#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
种子能力执行器 —— Odoo 初始化动作的**单一出口**，带版本感知。

版本约束（见 references/version-compatibility.md）：
- Odoo 17.0 / 18.0：对外 API 为 XML-RPC（channel=rpc）；
- Odoo 19.0：XML-RPC/JSON-RPC 已 deprecated，推荐 JSON-2（channel=json2，bearer API key）；
- shell 通道跨版本通用，但 shell_code 必须按目标版本的模型/字段编写。

设计要点（与 error-taxonomy.md 的失败分类严格对齐）：
1. 零依赖：仅用 Python 标准库（xmlrpc.client / urllib.request / subprocess）。
2. 默认 dry-run：不传 --apply 时只打印将执行的动作，绝不产生外部写操作。
3. fail-closed：缺凭据 → CT-006 blocked；写操作无幂等键 → CT-007 blocked；
   动作声明 odoo_versions 却未指定版本 → CT-003 error；通道与版本不兼容 → CT-003 error；
   幂等账本损坏 → CT-011 error。blocked/error 级别不得由自动化自行解除。
4. 动作级版本过滤：声明 odoo_versions 的动作只在匹配版本执行，不匹配则跳过并计入
   skipped_actions；未声明者视为通用动作。
5. 写操作不自动重试；只读操作失败最多重试 2 次，退避递增。
6. 凭据只从环境变量读取，绝不写入动作计划、日志或报告。
7. 报告为 JSON，与 validate_odoo_manifest.py / gherkin_gate.py 字段风格一致。
8. 执行器不内置任何种子能力的业务动作；业务语义由 templates/project/ 下的计划声明。
9. --apply 使用幂等账本（默认 artifacts/idempotency_ledger.json）：成功写入才记账，
   重放同一「计划 ID + 动作序号 + 幂等键」即 skipped；账本损坏直接 error，不得降级为空账本。

退出码：0 = 无阻断；1 = 存在 error/blocked；2 = 工具/入参错误。
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import xmlrpc.client
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SUPPORTED_VERSIONS = ("17.0", "18.0", "19.0")

# 幂等账本：运行产物，默认落在用户工作区的 artifacts/，不随技能包分发。
DEFAULT_LEDGER_PATH = "artifacts/idempotency_ledger.json"
LEDGER_SCHEMA_VERSION = 1

# 凭据环境变量名——只认环境变量，不提供默认值（缺即 blocked）
CREDENTIAL_ENV = {
    "url": "ODOO_URL",
    "db": "ODOO_DB",
    "user": "ODOO_USER",
    "password": "ODOO_PASSWORD",
    "api_key": "ODOO_API_KEY",  # Odoo 19+ JSON-2 的 bearer key（14.0+ 亦可用于 XML-RPC）
}

# 各通道实际需要的凭据；rpc 亦可用 api_key 代替 password，但最小集仍为 user/password
CHANNEL_CREDENTIALS = {
    "rpc": ("url", "db", "user", "password"),
    "json2": ("url", "db", "api_key"),
    "shell": ("url", "db", "user", "password"),
}

# 写操作白名单：标准 CRUD + 三类核心服务动作（模块安装/配置参数/数据导入）。
# 核心服务动作虽非 CRUD，但都改变数据库状态，必须与写操作一样强制幂等键。
WRITE_METHODS = frozenset({
    "create", "write", "unlink", "copy", "import_data",
    "button_immediate_install",  # SEED-001 模块安装（ir.module.module，记录集方法）
    "set_param",                 # SEED-002 配置参数（ir.config_parameter，模型级方法）
})
READ_METHODS = frozenset({"search", "search_read", "read", "search_count"})
RETRYABLE_READ = 2  # 只读失败最多重试 2 次（error-taxonomy.md 重试禁令）


class ExecutorError(Exception):
    """工具/入参错误，对应退出码 2。"""


def _issue(code: str, category: str, severity: str, message: str) -> Dict[str, str]:
    return {"code": code, "category": category, "severity": severity, "message": message}


def load_credentials(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """从环境变量读取凭据；不返回任何默认值。"""
    source = env if env is not None else os.environ
    return {key: source.get(var, "") for key, var in CREDENTIAL_ENV.items()}


def validate_credentials(creds: Dict[str, str], channel: str = "rpc") -> List[Dict[str, str]]:
    """按通道校验必需凭据；缺任一即产生 CT-006 blocked。"""
    required = CHANNEL_CREDENTIALS.get(channel, CHANNEL_CREDENTIALS["rpc"])
    missing = [CREDENTIAL_ENV[key] for key in required if not creds.get(key)]
    if not missing:
        return []
    return [_issue(
        "CT-006", "credential_missing", "blocked",
        f"通道 {channel} 缺少凭据环境变量：{', '.join(missing)}",
    )]


def validate_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """校验动作计划：写操作必须有幂等键；未知方法视为契约违规。"""
    issues: List[Dict[str, str]] = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            issues.append(_issue("CT-003", "contract_violation", "error",
                                 f"actions[{index}] 不是对象"))
            continue
        method = str(action.get("method", "")).strip()
        if not method:
            issues.append(_issue("CT-001", "input_validation", "error",
                                 f"actions[{index}] 缺少 method"))
            continue
        if method in WRITE_METHODS and not action.get("idempotency_key"):
            issues.append(_issue(
                "CT-007", "idempotency_absent", "blocked",
                f"actions[{index}] 是写操作（{method}）但无幂等键 idempotency_key；"
                "按 error-taxonomy.md 不得执行，也不得重试",
            ))
        if method not in WRITE_METHODS and method not in READ_METHODS:
            issues.append(_issue("CT-003", "contract_violation", "error",
                                 f"actions[{index}] 的 method={method!r} 不在允许集合"))
    return issues


def normalize_version(value: Optional[str]) -> Optional[str]:
    """把 '18' / '18.0' 归一为 '18.0'；非法值返回 None。"""
    if not value:
        return None
    text = str(value).strip()
    if text.isdigit():
        text = f"{text}.0"
    return text if text in SUPPORTED_VERSIONS else None


def validate_channel_version(channel: str, version: Optional[str]) -> List[Dict[str, str]]:
    """通道与版本兼容性检查；JSON-2 仅 19.0 可用，19.0 + rpc 给出 deprecated 警告。"""
    issues: List[Dict[str, str]] = []
    if version is None:
        return issues
    if channel == "json2" and version != "19.0":
        issues.append(_issue(
            "CT-003", "contract_violation", "error",
            f"channel=json2 仅适用于 Odoo 19.0，当前版本 {version} 不支持；"
            "17.0/18.0 请使用 channel=rpc",
        ))
    if channel == "rpc" and version == "19.0":
        issues.append(_issue(
            "CT-003", "contract_violation", "warning",
            "Odoo 19.0 起 XML-RPC 已 deprecated（计划 22.0 移除）；建议改用 channel=json2",
        ))
    return issues


def action_applies(action: Dict[str, Any], version: Optional[str]) -> Optional[bool]:
    """动作是否适用于目标版本：True/False；未指定版本而动作带版本约束时返回 None。"""
    versions = action.get("odoo_versions")
    if not versions:
        return True
    if version is None:
        return None
    return version in [normalize_version(v) or str(v) for v in versions]


def validate_version_annotations(actions: List[Dict[str, Any]],
                                 version: Optional[str]) -> List[Dict[str, str]]:
    """fail-closed：动作声明了 odoo_versions 却未指定目标版本，判为契约错误。"""
    if version is not None:
        return []
    for index, action in enumerate(actions):
        if isinstance(action, dict) and action.get("odoo_versions"):
            return [_issue(
                "CT-003", "contract_violation", "error",
                f"actions[{index}] 声明了 odoo_versions，但未提供 --odoo-version；"
                "版本相关动作必须显式指定目标版本",
            )]
    return []


def load_plan(path: Optional[str]) -> Dict[str, Any]:
    """读取动作计划 JSON：显式路径、stdin，或空计划。"""
    if path:
        p = Path(path)
        if not p.is_file():
            raise ExecutorError(f"动作计划文件不存在：{p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ExecutorError(f"动作计划 JSON 损坏：{p}:{exc.lineno}: {exc.msg}")
    elif not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if not raw:
            data = {"actions": []}
        else:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ExecutorError(f"stdin 动作计划 JSON 损坏：{exc.lineno}: {exc.msg}")
    else:
        data = {"actions": []}

    if not isinstance(data, dict) or not isinstance(data.get("actions", []), list):
        raise ExecutorError("动作计划必须是含 actions 数组的对象")
    return data


def _ledger_key(plan_id: str, index: int, action: Dict[str, Any]) -> str:
    """Stable key: plan ID + action index + declared idempotency key."""
    return f"{plan_id}:{index}:{action.get('idempotency_key')}"


def load_ledger(path: Optional[str]) -> Dict[str, Any]:
    """Load the idempotency ledger; a corrupt ledger must fail closed."""
    if not path:
        return {"schema": LEDGER_SCHEMA_VERSION, "entries": {}}
    ledger_file = Path(path)
    if not ledger_file.exists():
        return {"schema": LEDGER_SCHEMA_VERSION, "entries": {}}
    try:
        data = json.loads(ledger_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExecutorError(f"幂等账本损坏，禁止执行写操作：{ledger_file} ({exc})")
    if (not isinstance(data, dict)
            or data.get("schema") != LEDGER_SCHEMA_VERSION
            or not isinstance(data.get("entries"), dict)):
        raise ExecutorError(f"幂等账本结构非法，禁止执行写操作：{ledger_file}")
    return data


def save_ledger(path: str, ledger: Dict[str, Any]) -> None:
    """Atomically persist the ledger so a crash cannot leave a half-written file."""
    ledger_file = Path(path)
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = ledger_file.with_suffix(ledger_file.suffix + ".tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ledger_file)


def render_action(action: Dict[str, Any], index: int) -> str:
    """把动作渲染为可读的单行描述（不含凭据）。"""
    method = action.get("method", "?")
    model = action.get("model", "?")
    key = action.get("idempotency_key")
    suffix = f" idempotency_key={key}" if key else ""
    versions = action.get("odoo_versions")
    ver = f" odoo_versions={','.join(versions)}" if versions else ""
    return f"  [{index}] {method} {model}{suffix}{ver}"


def _rpc_execute(creds: Dict[str, str], action: Dict[str, Any],
                 transport: Optional[Any] = None) -> Any:
    """Odoo 17/18 的 XML-RPC 通道（19 仍可用但 deprecated）。

    transport 可注入以便离线测试，语义如下：
    - 未提供：分别连 /xmlrpc/2/common 与 /xmlrpc/2/object，走真实认证；
    - 提供且带 authenticate：同一对象承担认证与调用（假代理需实现两者）；
    - 提供但不带 authenticate：视为已认证的 object 代理，跳过认证。
    """
    uid = None
    if transport is None:
        common = xmlrpc.client.ServerProxy(f"{creds['url']}/xmlrpc/2/common")
        models = xmlrpc.client.ServerProxy(f"{creds['url']}/xmlrpc/2/object")
    else:
        common = transport if hasattr(transport, "authenticate") else None
        models = transport
    if common is not None:
        uid = common.authenticate(creds["db"], creds["user"], creds["password"], {})
        if not uid:
            raise PermissionError("Odoo 认证失败（凭据错误或用户无权限）")
    args = action.get("args", [])
    kwargs = action.get("kwargs", {})
    return models.execute_kw(creds["db"], uid, creds["password"],
                             action["model"], action["method"], args, kwargs)


def _json2_payload(action: Dict[str, Any]) -> Dict[str, Any]:
    """把通用的 args/kwargs 动作映射为 JSON-2 的命名参数请求体。"""
    method = action.get("method", "")
    args = action.get("args", [])
    kwargs = action.get("kwargs", {})
    if method == "create":
        return {"vals": args[0] if args else kwargs.get("vals", {})}
    # 核心服务动作（SEED-001~003）：JSON-2 请求体为扁平对象，方法参数作顶层 key。
    # args 的位置约定与 XML-RPC execute_kw 保持一致，在此转换为命名参数。
    if method == "button_immediate_install":
        # 记录集方法：模块记录 ID 列表作 ids 字段
        return {"ids": args[0] if args else kwargs.get("ids", [])}
    if method == "set_param":
        # 模型级方法：set_param(key, value, group=None)
        payload: Dict[str, Any] = {
            "key": args[0] if args else kwargs.get("key", ""),
            "value": args[1] if len(args) > 1 else kwargs.get("value", ""),
        }
        if "group" in kwargs:
            payload["group"] = kwargs["group"]
        return payload
    if method == "import_data":
        # 模型级方法：import_data(fields, rows, mode=...)
        payload = {
            "fields": args[0] if args else kwargs.get("fields", []),
            "rows": args[1] if len(args) > 1 else kwargs.get("rows", []),
        }
        if len(args) > 2:
            payload["mode"] = args[2]
        for key in ("mode", "current_company_id", "dryrun"):
            if key in kwargs:
                payload[key] = kwargs[key]
        return payload
    if method in {"write", "unlink", "read"}:
        payload = {"ids": args[0] if args else kwargs.get("ids", [])}
        if method == "write":
            payload["vals"] = args[1] if len(args) > 1 else kwargs.get("vals", {})
        if method == "read" and kwargs.get("fields"):
            payload["fields"] = kwargs["fields"]
        return payload
    if method in READ_METHODS:
        payload = {"domain": args[0] if args else kwargs.get("domain", [])}
        for key in ("fields", "limit", "offset", "order"):
            if key in kwargs:
                payload[key] = kwargs[key]
        return payload
    return dict(kwargs)  # 兜底：命名参数直传


def _json2_execute(creds: Dict[str, str], action: Dict[str, Any],
                   transport: Optional[Any] = None) -> Any:
    """Odoo 19+ 的 JSON-2 通道：POST /json/2/<model>/<method>，bearer API key。

    transport 可注入（接收 endpoint/payload/creds 并返回结果对象）以便离线测试。
    """
    endpoint = (f"{creds['url'].rstrip('/')}/json/2/"
                f"{action['model']}/{action['method']}")
    payload = _json2_payload(action)
    if transport is not None:
        response = transport(endpoint, payload, creds)
    else:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"bearer {creds['api_key']}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=120) as resp:
            response = json.loads(resp.read().decode("utf-8") or "{}")
    if isinstance(response, dict) and response.get("error"):
        raise RuntimeError(f"JSON-2 返回错误：{response['error']}")
    if isinstance(response, dict):
        return response.get("result")
    return response


def _shell_execute(creds: Dict[str, str], action: Dict[str, Any],
                   runner: Optional[Any] = None) -> Any:
    """经 odoo shell 执行单个动作；代码通过 stdin 注入，凭据走环境变量。"""
    code = str(action.get("shell_code", "")).strip()
    if not code:
        raise ExecutorError(f"动作 {action.get('method')!r} 未提供 shell_code")
    cmd = ["odoo", "shell", "-d", creds["db"],
           "--db_host", creds.get("host", "localhost"),
           "--db_user", creds["user"], "--db_password", creds["password"],
           "--no-http"]
    env = dict(os.environ)
    env.update({
        "ODOO_URL": creds["url"], "ODOO_DB": creds["db"],
        "ODOO_USER": creds["user"], "ODOO_PASSWORD": creds["password"],
    })
    invoke = runner or subprocess.run
    proc = invoke(cmd, input=code, text=True, capture_output=True, env=env, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"odoo shell 退出码 {proc.returncode}: {proc.stderr[:400]}")
    return proc.stdout.strip()


def execute_action(creds: Dict[str, str], action: Dict[str, Any],
                   channel: str, dry_run: bool,
                   transport: Optional[Any] = None,
                   runner: Optional[Any] = None) -> Dict[str, Any]:
    """执行单个动作；dry_run 时不产生任何外部调用。"""
    method = action.get("method", "")
    if dry_run:
        return {"method": method, "status": "dry_run", "result": None}

    attempts = RETRYABLE_READ if method in READ_METHODS else 1
    last_error = ""
    for attempt in range(attempts):
        try:
            if channel == "rpc":
                result = _rpc_execute(creds, action, transport=transport)
            elif channel == "json2":
                result = _json2_execute(creds, action, transport=transport)
            else:
                result = _shell_execute(creds, action, runner=runner)
            return {"method": method, "status": "ok", "result": result,
                    "attempts": attempt + 1}
        except PermissionError as exc:
            # 凭据类错误：只允许刷新凭据重试 1 次；这里不循环刷新，直接返回
            return {"method": method, "status": "error", "error": str(exc),
                    "category": "credential_missing"}
        except ExecutorError:
            # 入参/工具错误属于 exit 2 范畴，不重试、不伪装成外部失败
            raise
        except Exception as exc:  # noqa: BLE001 - 统一上报，不吞异常
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt + 1 < attempts:
                time.sleep(0.1 * (attempt + 1))  # 退避递增
    return {"method": method, "status": "error", "error": last_error,
            "category": "external_failure"}


def run(plan: Dict[str, Any], channel: str, apply: bool,
        env: Optional[Dict[str, str]] = None,
        transport: Optional[Any] = None,
        runner: Optional[Any] = None,
        odoo_version: Optional[str] = None,
        ledger_path: Optional[str] = None) -> Dict[str, Any]:
    """主入口：版本/契约校验 → 动作过滤 → （可选）执行 → 汇总报告。"""
    version = normalize_version(odoo_version) if odoo_version else None
    if odoo_version and version is None:
        raise ExecutorError(f"不支持的 Odoo 版本 {odoo_version!r}；"
                            f"可选：{', '.join(SUPPORTED_VERSIONS)}")
    if channel not in CHANNEL_CREDENTIALS:
        raise ExecutorError(f"不支持的通道 {channel!r}；"
                            f"可选：{', '.join(CHANNEL_CREDENTIALS)}")

    actions = plan.get("actions", [])
    issues = validate_actions(actions)
    issues.extend(validate_channel_version(channel, version))
    issues.extend(validate_version_annotations(actions, version))
    creds = load_credentials(env)
    credential_issues = validate_credentials(creds, channel)
    # dry-run 不需要真实连接，凭据缺失不作为阻断；--apply 才 fail-closed
    if apply:
        issues.extend(credential_issues)

    # 幂等账本只在 --apply 时读写；损坏即 fail-closed（不降级为空账本）。
    ledger: Dict[str, Any] = {"schema": LEDGER_SCHEMA_VERSION, "entries": {}}
    ledger_loaded = False
    if apply and ledger_path:
        try:
            ledger = load_ledger(ledger_path)
            ledger_loaded = True
        except ExecutorError as exc:
            issues.append(_issue("CT-011", "idempotency_ledger_corrupt", "error", str(exc)))

    plan_id = str(plan.get("plan_id") or plan.get("seed_id") or "default")
    results: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    replayed: List[Dict[str, Any]] = []
    recorded: List[Dict[str, Any]] = []
    if not any(i["severity"] in {"error", "blocked"} for i in issues):
        for index, action in enumerate(actions):
            applies = action_applies(action, version)
            if applies is False:
                skipped.append({"index": index, "method": action.get("method"),
                                "odoo_versions": action.get("odoo_versions"),
                                "reason": "version_mismatch"})
                continue
            key = None
            if apply and ledger_loaded and ledger_path and action.get("method") in WRITE_METHODS:
                key = _ledger_key(plan_id, index, action)
                if key in ledger["entries"]:
                    replayed.append({"index": index, "key": key,
                                     "method": action.get("method")})
                    skipped.append({"index": index, "method": action.get("method"),
                                    "reason": "idempotent_replay", "key": key})
                    continue
            outcome = execute_action(creds, action, channel, dry_run=not apply,
                                     transport=transport, runner=runner)
            if key and outcome.get("status") == "ok":
                ledger["entries"][key] = {
                    "plan_id": plan_id,
                    "index": index,
                    "method": action.get("method"),
                    "idempotency_key": action.get("idempotency_key"),
                    "recorded_at": datetime.now().isoformat(),
                }
                recorded.append({"index": index, "key": key,
                                 "method": action.get("method")})
            results.append(outcome)
        if ledger_loaded and ledger_path and recorded:
            save_ledger(ledger_path, ledger)

    blocked = any(i["severity"] == "blocked" for i in issues)
    errored = any(i["severity"] == "error" for i in issues) or any(
        r.get("status") == "error" for r in results)
    status = "blocked" if blocked else ("error" if errored else "pass")
    return {
        "status": status,
        "channel": channel,
        "odoo_version": version,
        "mode": "apply" if apply else "dry_run",
        "action_count": len(actions),
        "executed_count": len(results),
        "skipped_actions": skipped,
        "issues": issues,
        "results": results,
        "idempotency": {
            "ledger": ledger_path if apply else None,
            "enabled": bool(apply and ledger_path),
            "replayed": replayed,
            "recorded": recorded,
        },
        "timestamp": datetime.now().isoformat(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Odoo 种子能力执行器（RPC / JSON-2 / shell 单一出口，版本感知）")
    parser.add_argument("--channel", choices=tuple(CHANNEL_CREDENTIALS), default="rpc",
                        help="rpc=XML-RPC(17/18)，json2=JSON-2(19)，shell=odoo shell(通用)")
    parser.add_argument("--odoo-version", choices=SUPPORTED_VERSIONS,
                        help="目标 Odoo 大版本；动作含 odoo_versions 时必填")
    parser.add_argument("--apply", action="store_true",
                        help="真实执行；不加则只做 dry-run（默认且安全）")
    parser.add_argument("--plan", help="动作计划 JSON 路径；缺省时读 stdin")
    parser.add_argument(
        "--ledger-path", default=DEFAULT_LEDGER_PATH,
        help=f"幂等账本路径（运行产物，默认 {DEFAULT_LEDGER_PATH}）；仅 --apply 时读写")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        plan = load_plan(args.plan)
        report = run(plan, channel=args.channel, apply=args.apply,
                     odoo_version=args.odoo_version,
                     ledger_path=args.ledger_path)
    except ExecutorError as exc:
        print(json.dumps({"status": "error", "issues": [_issue(
            "CT-000", "tool_error", "error", str(exc))]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] in {"blocked", "error"} else 0


if __name__ == "__main__":
    sys.exit(main())
