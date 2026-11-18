#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""种子执行器测试：全部离线，注入假 transport/runner，绝不连真实 Odoo。"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import odoo_seed_executor as E  # noqa: E402

# execute_action 接收内部键名（url/db/user/password），先经 load_credentials 规范化
FULL_ENV = E.load_credentials({v: "x" for v in E.CREDENTIAL_ENV.values()})


class FakeCommon:
    def __init__(self, uid=1):
        self.uid = uid

    def authenticate(self, *args):
        return self.uid


class FakeModels:
    def __init__(self, fail_times=0):
        self.calls = []
        self.fail_times = fail_times

    def execute_kw(self, *args):
        self.calls.append(args)
        if len(self.calls) <= self.fail_times:
            raise RuntimeError("transient")
        return {"ok": True}


class FakeProc:
    def __init__(self, code=0, stdout="ok", stderr=""):
        self.returncode = code
        self.stdout = stdout
        self.stderr = stderr


def plan(actions, seed="SEED-TEST"):
    return {"seed_id": seed, "actions": actions}


class ExecutorTests(unittest.TestCase):
    def test_01_dry_run_does_not_touch_transport(self):
        models = FakeModels()
        transport = FakeCommon()
        # 即使注入会抛异常的 transport，dry-run 也不应调用
        report = E.run(plan([{"method": "create", "model": "res.partner",
                              "idempotency_key": "k", "args": []}]),
                       "rpc", apply=False, env=FULL_ENV,
                       transport=transport, runner=None)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["mode"], "dry_run")
        self.assertEqual(report["results"][0]["status"], "dry_run")
        self.assertEqual(models.calls, [])

    def test_02_missing_credentials_blocked_on_apply(self):
        report = E.run(plan([{"method": "search", "model": "res.partner"}]),
                       "rpc", apply=True, env={})
        self.assertEqual(report["status"], "blocked")
        codes = {i["code"] for i in report["issues"]}
        self.assertIn("CT-006", codes)

    def test_03_missing_credentials_ok_on_dry_run(self):
        report = E.run(plan([{"method": "search", "model": "res.partner"}]),
                       "rpc", apply=False, env={})
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["issues"], [])

    def test_04_write_without_idempotency_blocked(self):
        report = E.run(plan([{"method": "write", "model": "res.partner", "args": []}]),
                       "rpc", apply=True, env=FULL_ENV)
        self.assertEqual(report["status"], "blocked")
        codes = {i["code"] for i in report["issues"]}
        self.assertIn("CT-007", codes)

    def test_05_read_retries_then_succeeds(self):
        # 注入的 object 代理无 authenticate：视为已认证连接，跳过认证直接调用
        models = FakeModels(fail_times=1)
        action = {"method": "search", "model": "res.partner", "args": []}
        result = E.execute_action(FULL_ENV, action, "rpc", dry_run=False,
                                  transport=models)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["attempts"], 2)

    def test_06_credential_error_not_retried(self):
        class Denied(FakeCommon):
            def authenticate(self, *args):
                return 0

        result = E.execute_action(FULL_ENV, {"method": "search", "model": "x"},
                                  "rpc", dry_run=False, transport=Denied())
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["category"], "credential_missing")
        self.assertNotIn("attempts", result)

    def test_07_shell_channel_reachable(self):
        calls = []

        def runner(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return FakeProc(stdout="done")

        action = {"method": "search", "model": "res.partner",
                  "shell_code": "print(1)"}
        result = E.execute_action(FULL_ENV, action, "shell", dry_run=False,
                                  runner=runner)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["result"], "done")
        self.assertTrue(calls)
        self.assertIn("ODOO_PASSWORD", calls[0][1]["env"])

    def test_08_shell_code_required(self):
        with self.assertRaises(E.ExecutorError):
            E.execute_action(FULL_ENV, {"method": "search", "model": "x"},
                             "shell", dry_run=False,
                             runner=lambda *a, **k: FakeProc())

    def test_09_cli_exit_codes(self):
        script = str(SKILL_DIR / "scripts" / "odoo_seed_executor.py")
        p = subprocess.run([sys.executable, script],
                           input=json.dumps(plan([{"method": "write", "model": "x"}])),
                           text=True, capture_output=True)
        self.assertEqual(p.returncode, 1)  # 缺幂等键 → blocked → exit 1
        report = json.loads(p.stdout)
        self.assertEqual(report["status"], "blocked")

    def test_10_report_is_json_serializable(self):
        report = E.run(plan([]), "rpc", apply=False, env={})
        json.dumps(report, ensure_ascii=False)  # 不抛即通过

    @staticmethod
    def _base_template():
        path = SKILL_DIR / "templates" / "project" / "base-data-actions.template.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_11_base_data_template_is_safe_and_complete(self):
        """基础数据族模板：5 类种子全覆盖、写操作全带幂等键与 shell_code。"""
        data = self._base_template()
        seed_ids = {a["seed_id"] for a in data["actions"]}
        self.assertEqual(seed_ids, {"SEED-006", "SEED-007", "SEED-008",
                                    "SEED-009", "SEED-010"})
        for action in data["actions"]:
            self.assertTrue(action.get("idempotency_key"),
                            f"写操作缺幂等键：{action}")
            self.assertTrue(action.get("shell_code"),
                            f"缺 shell_code：{action}")

    def test_12_version_required_when_actions_are_version_scoped(self):
        """含版本敏感动作却未指定版本 → fail-closed（CT-003 error，零执行）。"""
        report = E.run(self._base_template(), "rpc", apply=False, env={})
        self.assertEqual(report["status"], "error")
        self.assertIn("CT-003", {i["code"] for i in report["issues"]})
        self.assertEqual(report["executed_count"], 0)

    def test_13_version_filter_18_vs_19(self):
        """18.0 跳过 19 专属 UoM 动作；19.0 跳过两条 17/18 专属 UoM 动作。"""
        data = self._base_template()
        r18 = E.run(data, "rpc", apply=False, env={}, odoo_version="18.0")
        self.assertEqual(r18["status"], "pass")
        self.assertEqual(r18["odoo_version"], "18.0")
        self.assertEqual(r18["executed_count"], 6)
        self.assertEqual(len(r18["skipped_actions"]), 1)
        self.assertIn("19.0", r18["skipped_actions"][0]["odoo_versions"])

        r19 = E.run(data, "rpc", apply=False, env={}, odoo_version="19.0")
        self.assertEqual(r19["status"], "pass")
        self.assertEqual(r19["odoo_version"], "19.0")
        self.assertEqual(r19["executed_count"], 5)
        self.assertEqual(len(r19["skipped_actions"]), 2)
        # 19 的建议通道是 json2，用 rpc 应带 warning 但仍放行
        self.assertTrue(any(i["severity"] == "warning" for i in r19["issues"]))

    def test_14_json2_channel_and_credentials(self):
        """JSON-2 仅 19 可用、凭据用 API key；请求体为命名参数。"""
        report17 = E.run(plan([{"method": "search", "model": "x"}]), "json2",
                         apply=False, env=FULL_ENV, odoo_version="17.0")
        self.assertEqual(report17["status"], "error")
        self.assertIn("CT-003", {i["code"] for i in report17["issues"]})

        env19 = E.load_credentials({"ODOO_URL": "https://x", "ODOO_DB": "d",
                                    "ODOO_API_KEY": "k"})
        self.assertEqual(E.validate_credentials(env19, "json2"), [])
        self.assertTrue(E.validate_credentials(env19, "rpc"))  # 缺 user/password

        payload = E._json2_payload({"method": "write", "model": "x",
                                    "args": [[1], {"name": "n"}]})
        self.assertEqual(payload, {"ids": [1], "vals": {"name": "n"}})

        calls = []
        def transport(endpoint, body, creds):
            calls.append((endpoint, body, creds))
            return {"result": [1]}
        action = {"method": "search", "model": "res.partner", "args": [[[]]]}
        result = E.execute_action(env19, action, "json2", dry_run=False,
                                  transport=transport)
        self.assertEqual(result["status"], "ok")
        self.assertIn("/json/2/res.partner/search", calls[0][0])
        self.assertEqual(calls[0][2]["api_key"], "k")
        self.assertEqual(calls[0][2]["password"], "")  # JSON-2 不用密码

    def test_15_normalize_version_rejects_unknown(self):
        self.assertEqual(E.normalize_version("18"), "18.0")
        self.assertEqual(E.normalize_version("19.0"), "19.0")
        self.assertIsNone(E.normalize_version("20.0"))
        with self.assertRaises(E.ExecutorError):
            E.run(plan([]), "rpc", apply=False, odoo_version="20.0")


if __name__ == "__main__":
    unittest.main()
