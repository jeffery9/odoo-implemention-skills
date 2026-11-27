#!/usr/bin/env python3
"""Odoo 项目 onboarding 编排器。

职责边界：本脚本是**编排层**，不实现任何 RPC / JSON-2 / shell 调用，也不读取凭据值。
它读取一份项目 profile（目标版本、通道、启用的种子能力阶段及各自的动作计划路径），
按 SKILL.md §6.3 依赖顺序排序，逐阶段委派 odoo_seed_executor.run() 执行；任一阶段
error/blocked 即停止后续阶段（链式 fail-closed）。

两个子命令：
  check  静态接入检查（不连 Odoo、不执行动作）：版本/通道、seed 白名单、幂等键、
         版本注解、凭据齐备性。用于 onboarding 前的就绪判定。
  run    逐阶段执行；默认 dry-run，--apply 才真实写入。

退出码：0 = 无阻断；1 = error/blocked；2 = 工具/入参错误。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 同目录复用执行器：校验函数与执行入口均来自唯一出口，不重复实现。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import odoo_seed_executor as executor  # noqa: E402

# 能力白名单：与 SKILL.md §6.1 能力索引（SEED-001~013）一致。
SUPPORTED_SEEDS = frozenset({f"SEED-{i:03d}" for i in range(1, 14)})

# 默认依赖顺序（SKILL.md §6.3）：
#   SEED-001 模块安装先行 → 核心服务族 → 基础数据族 → 汇率（依赖币种）
#   → 主数据/组织/编号 → 会计模块 → 期初余额（依赖会计）。
# 排序只为确定性，不替代项目侧对业务前置的判断；约束见 README/version-compatibility。
DEPENDENCY_ORDER = (
    "SEED-001", "SEED-002", "SEED-003",
    "SEED-004", "SEED-005", "SEED-006", "SEED-007", "SEED-008",
    "SEED-009", "SEED-010", "SEED-011",
    "SEED-012", "SEED-013",
)

# profile 中禁止出现的凭据类键（凭据只从环境变量读取）。
FORBIDDEN_KEY_FRAGMENTS = ("credential", "password", "api_key", "apikey",
                           "token", "secret")


class OnboardingError(Exception):
    """profile 读取/结构错误，对应退出码 2。"""


def _issue(code: str, category: str, severity: str, message: str,
           phase: Optional[str] = None) -> Dict[str, str]:
    item = {"code": code, "category": category, "severity": severity,
            "message": message}
    if phase:
        item["phase"] = phase
    return item


def _scan_forbidden_keys(node: Any, path: str = "$") -> List[str]:
    """递归扫描 profile 中的凭据类键名，返回命中的路径。"""
    hits: List[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}"
            if any(fragment in str(key).lower() for fragment in FORBIDDEN_KEY_FRAGMENTS):
                hits.append(here)
            hits.extend(_scan_forbidden_keys(value, here))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            hits.extend(_scan_forbidden_keys(value, f"{path}[{index}]"))
    return hits


def load_profile(path: str) -> Dict[str, Any]:
    """读取并做结构性校验；失败即 OnboardingError（退出码 2）。"""
    p = Path(path)
    if not p.is_file():
        raise OnboardingError(f"onboarding profile 文件不存在：{p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OnboardingError(f"onboarding profile JSON 损坏：{p}:{exc.lineno}: {exc.msg}")
    if not isinstance(data, dict):
        raise OnboardingError("onboarding profile 必须是 JSON 对象")
    if not isinstance(data.get("phases", []), list):
        raise OnboardingError("onboarding profile.phases 必须是数组")

    forbidden = _scan_forbidden_keys(data)
    if forbidden:
        raise OnboardingError(
            "onboarding profile 禁止包含凭据类字段（凭据只从环境变量读取）："
            + ", ".join(forbidden))
    return data


def validate_profile(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """校验 profile 的版本/通道/阶段字段，返回 issue 列表。"""
    issues: List[Dict[str, str]] = []
    version_raw = profile.get("odoo_version")
    version = executor.normalize_version(version_raw)
    if version is None:
        issues.append(_issue(
            "CT-003", "contract_violation", "error",
            f"odoo_version={version_raw!r} 无效；可选：{', '.join(executor.SUPPORTED_VERSIONS)}"))
    channel = profile.get("channel")
    if channel not in executor.CHANNEL_CREDENTIALS:
        issues.append(_issue(
            "CT-003", "contract_violation", "error",
            f"channel={channel!r} 无效；可选：{', '.join(executor.CHANNEL_CREDENTIALS)}"))
    if version and channel:
        issues.extend(executor.validate_channel_version(channel, version))

    phases = profile.get("phases", [])
    if not phases:
        issues.append(_issue("CT-001", "input_validation", "error",
                             "phases 不能为空；至少声明一个种子能力阶段"))
    seen = set()
    for index, phase in enumerate(phases):
        label = f"phases[{index}]"
        if not isinstance(phase, dict):
            issues.append(_issue("CT-003", "contract_violation", "error",
                                 f"{label} 不是对象", phase=label))
            continue
        seed = str(phase.get("seed_id", "")).strip()
        if seed not in SUPPORTED_SEEDS:
            issues.append(_issue(
                "CT-003", "contract_violation", "error",
                f"{label} 的 seed_id={seed!r} 不在 SEED-001~013 白名单", phase=seed or label))
        elif seed in seen:
            issues.append(_issue(
                "CT-003", "contract_violation", "error",
                f"{label} 的 seed_id={seed} 重复；同一能力不得出现两次", phase=seed))
        else:
            seen.add(seed)
        plan = phase.get("plan")
        if not isinstance(plan, str) or not plan.strip():
            issues.append(_issue("CT-001", "input_validation", "error",
                                 f"{label} 缺少有效的 plan 路径", phase=seed or label))
    return issues


def order_phases(phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按依赖顺序稳定排序；未知 seed 排在末尾（其合法性已由 validate_profile 判定）。"""
    rank = {seed: index for index, seed in enumerate(DEPENDENCY_ORDER)}
    return sorted(phases, key=lambda phase: rank.get(str(phase.get("seed_id", "")), len(rank)))


def _resolve_plan(profile_path: str, plan_ref: str) -> Path:
    """plan 路径相对 profile 所在目录解析；绝对路径直接使用。"""
    ref = Path(plan_ref)
    if ref.is_absolute():
        return ref
    return Path(profile_path).resolve().parent / ref


def check(profile: Dict[str, Any], profile_path: str,
          env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """静态接入检查：不连 Odoo、不执行动作；汇总所有阶段的契约与凭据就绪状态。"""
    issues = validate_profile(profile)
    version = executor.normalize_version(profile.get("odoo_version"))
    channel = profile.get("channel", "rpc")
    phases = order_phases(profile.get("phases", []))
    phase_reports: List[Dict[str, Any]] = []
    creds = executor.load_credentials(env)

    for phase in phases:
        seed = str(phase.get("seed_id", ""))
        plan_ref = phase.get("plan", "")
        if issues and any(i.get("phase") == seed and i["severity"] == "error"
                          for i in issues):
            phase_reports.append({"seed_id": seed, "status": "error",
                                  "issues": [i for i in issues if i.get("phase") == seed]})
            continue
        plan_path = _resolve_plan(profile_path, plan_ref) if isinstance(plan_ref, str) else None
        if plan_path is None or not plan_path.is_file():
            phase_reports.append({"seed_id": seed, "status": "error", "plan": plan_ref,
                                  "issues": [_issue("CT-000", "tool_error", "error",
                                                    f"动作计划文件不存在：{plan_ref}",
                                                    phase=seed)]})
            continue
        try:
            plan = executor.load_plan(str(plan_path))
        except executor.ExecutorError as exc:
            phase_reports.append({"seed_id": seed, "status": "error", "plan": plan_ref,
                                  "issues": [_issue("CT-000", "tool_error", "error",
                                                    str(exc), phase=seed)]})
            continue
        phase_issues = executor.validate_actions(plan.get("actions", []))
        phase_issues.extend(executor.validate_version_annotations(
            plan.get("actions", []), version))
        if channel in executor.CHANNEL_CREDENTIALS:
            phase_issues.extend(executor.validate_credentials(creds, channel))
        phase_status = "error" if any(i["severity"] == "error" for i in phase_issues) else (
            "blocked" if any(i["severity"] == "blocked" for i in phase_issues) else "pass")
        phase_reports.append({"seed_id": seed, "plan": plan_ref, "status": phase_status,
                              "action_count": len(plan.get("actions", [])),
                              "issues": phase_issues})

    global_errors = [i for i in issues if not i.get("phase")]
    status = "error" if (any(i["severity"] == "error" for i in global_errors)
                         or any(p["status"] == "error" for p in phase_reports)) else (
        "blocked" if any(p["status"] == "blocked" for p in phase_reports) else "pass")
    return {
        "status": status,
        "mode": "check",
        "project": profile.get("project"),
        "odoo_version": version,
        "channel": channel,
        "phase_count": len(phases),
        "issues": global_errors,
        "phases": phase_reports,
        "timestamp": datetime.now().isoformat(),
    }


def run_onboarding(profile: Dict[str, Any], profile_path: str, apply: bool,
                   env: Optional[Dict[str, str]] = None,
                   executor_run: Callable = executor.run,
                   transport: Optional[Any] = None,
                   runner: Optional[Any] = None,
                   ledger_path: Optional[str] = executor.DEFAULT_LEDGER_PATH) -> Dict[str, Any]:
    """逐阶段执行：默认 dry-run；--apply 才真实写入；阶段失败即停（链式 fail-closed）。"""
    issues = validate_profile(profile)
    version = executor.normalize_version(profile.get("odoo_version"))
    channel = profile.get("channel", "rpc")
    phases = order_phases(profile.get("phases", []))

    if any(i["severity"] == "error" for i in issues):
        return {"status": "error", "mode": "apply" if apply else "dry_run",
                "project": profile.get("project"), "odoo_version": version,
                "channel": channel, "phase_count": len(phases),
                "completed_phases": [], "stopped_at": None, "issues": issues,
                "phases": [], "timestamp": datetime.now().isoformat()}

    phase_reports: List[Dict[str, Any]] = []
    stopped_at: Optional[str] = None
    for phase in phases:
        seed = str(phase.get("seed_id", ""))
        plan_ref = str(phase.get("plan", ""))
        if stopped_at is not None:
            phase_reports.append({"seed_id": seed, "status": "not_run",
                                  "reason": f"blocked_by_previous_phase:{stopped_at}"})
            continue
        plan_path = _resolve_plan(profile_path, plan_ref)
        if not plan_path.is_file():
            stopped_at = seed
            phase_reports.append({"seed_id": seed, "status": "error", "plan": plan_ref,
                                  "issues": [_issue("CT-000", "tool_error", "error",
                                                    f"动作计划文件不存在：{plan_ref}",
                                                    phase=seed)]})
            continue
        try:
            plan = executor.load_plan(str(plan_path))
            report = executor_run(plan, channel=channel, apply=apply, env=env,
                                  transport=transport, runner=runner,
                                  odoo_version=profile.get("odoo_version"),
                                  ledger_path=ledger_path)
        except executor.ExecutorError as exc:
            stopped_at = seed
            phase_reports.append({"seed_id": seed, "status": "error", "plan": plan_ref,
                                  "issues": [_issue("CT-000", "tool_error", "error",
                                                    str(exc), phase=seed)]})
            continue
        phase_reports.append({"seed_id": seed, "plan": plan_ref,
                              "status": report.get("status", "error"),
                              "executed_count": report.get("executed_count", 0),
                              "skipped_actions": report.get("skipped_actions", []),
                              "issues": report.get("issues", [])})
        if report.get("status") in {"error", "blocked"}:
            stopped_at = seed

    statuses = [p["status"] for p in phase_reports]
    status = "error" if "error" in statuses else ("blocked" if "blocked" in statuses else "pass")
    completed = [p["seed_id"] for p in phase_reports if p["status"] == "pass"]
    return {
        "status": status,
        "mode": "apply" if apply else "dry_run",
        "project": profile.get("project"),
        "odoo_version": version,
        "channel": channel,
        "phase_count": len(phases),
        "completed_phases": completed,
        "stopped_at": stopped_at,
        "issues": issues,
        "phases": phase_reports,
        "timestamp": datetime.now().isoformat(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Odoo 项目 onboarding 编排器（按依赖顺序逐阶段委派单一执行出口）")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("check", "静态接入检查（不连 Odoo、不执行动作）"),
                            ("run", "逐阶段执行（默认 dry-run，--apply 才写入）")):
        child = sub.add_parser(name, help=help_text)
        child.add_argument("--profile", required=True, help="onboarding profile JSON 路径")
        if name == "run":
            child.add_argument("--apply", action="store_true",
                               help="真实执行；不加则只做 dry-run（默认且安全）")
            child.add_argument("--ledger-path", default=executor.DEFAULT_LEDGER_PATH,
                               help=f"幂等账本路径（默认 {executor.DEFAULT_LEDGER_PATH}）")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = load_profile(args.profile)
    except OnboardingError as exc:
        print(json.dumps({"status": "error", "issues": [_issue(
            "CT-000", "tool_error", "error", str(exc))]}, ensure_ascii=False, indent=2))
        return 2
    if args.command == "check":
        report = check(profile, args.profile)
    else:
        report = run_onboarding(profile, args.profile, apply=args.apply,
                                ledger_path=args.ledger_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] in {"blocked", "error"} else 0


if __name__ == "__main__":
    sys.exit(main())
