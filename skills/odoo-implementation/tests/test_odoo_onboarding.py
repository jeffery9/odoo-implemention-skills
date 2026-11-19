#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""onboarding 编排器测试：全部离线，注入假 executor_run，绝不连真实 Odoo。"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))
import odoo_onboarding as O  # noqa: E402

TEMPLATES = SKILL_DIR / "templates" / "project"
CORE = "core-services-actions.template.json"
BASE = "base-data-actions.template.json"
SEED = "seed-actions.template.json"
FULL_ENV = {v: "x" for v in ("ODOO_URL", "ODOO_DB", "ODOO_USER",
                             "ODOO_PASSWORD", "ODOO_API_KEY")}


def write_profile(directory, data):
    path = Path(directory) / "profile.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


def good_profile(**overrides):
    data = {
        "project": "demo",
        "odoo_version": "19.0",
        "channel": "json2",
        "phases": [
            {"seed_id": "SEED-001", "plan": CORE},
            {"seed_id": "SEED-004", "plan": BASE},
            {"seed_id": "SEED-009", "plan": SEED},
        ],
    }
    data.update(overrides)
    return data


def pass_report():
    return {"status": "pass", "executed_count": 1,
            "skipped_actions": [], "issues": []}


class TestProfileLoading(unittest.TestCase):
    def test_01_credential_field_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            profile = good_profile()
            profile["ODOO_PASSWORD"] = "leaked"
            with self.assertRaises(O.OnboardingError):
                O.load_profile(write_profile(d, profile))

    def test_02_nested_credential_field_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            profile = good_profile()
            profile["phases"][0]["api_key"] = "leaked"
            with self.assertRaises(O.OnboardingError):
                O.load_profile(write_profile(d, profile))

    def test_03_missing_file(self):
        with self.assertRaises(O.OnboardingError):
            O.load_profile("/nonexistent/onboarding-profile.json")

    def test_04_corrupt_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(O.OnboardingError):
                O.load_profile(str(path))

    def test_05_valid_profile_loads(self):
        with tempfile.TemporaryDirectory() as d:
            data = O.load_profile(write_profile(d, good_profile()))
            self.assertEqual(data["odoo_version"], "19.0")


class TestProfileValidation(unittest.TestCase):
    def test_06_unknown_seed_rejected(self):
        issues = O.validate_profile(good_profile(phases=[
            {"seed_id": "SEED-999", "plan": SEED}]))
        self.assertTrue(any(i["code"] == "CT-003" for i in issues))

    def test_07_duplicate_seed_rejected(self):
        issues = O.validate_profile(good_profile(phases=[
            {"seed_id": "SEED-009", "plan": SEED},
            {"seed_id": "SEED-009", "plan": SEED}]))
        self.assertTrue(any("重复" in i["message"] for i in issues))

    def test_08_invalid_version_and_channel(self):
        issues = O.validate_profile(good_profile(odoo_version="20.0", channel="rpc"))
        codes = {i["code"] for i in issues}
        self.assertIn("CT-003", codes)

    def test_09_empty_phases_rejected(self):
        issues = O.validate_profile(good_profile(phases=[]))
        self.assertTrue(any(i["severity"] == "error" for i in issues))

    def test_10_dependency_order(self):
        # 乱序声明 → 依赖顺序：001（模块安装）先行、004（基础数据）先于 009（主数据）
        ordered = O.order_phases(good_profile(phases=[
            {"seed_id": "SEED-009", "plan": SEED},
            {"seed_id": "SEED-004", "plan": BASE},
            {"seed_id": "SEED-001", "plan": CORE},
        ])["phases"])
        self.assertEqual([p["seed_id"] for p in ordered],
                         ["SEED-001", "SEED-004", "SEED-009"])


class TestCheck(unittest.TestCase):
    def test_11_check_clean_profile_pass_with_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            # 复制模板到临时目录，使相对路径可解析
            for name in (CORE, BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            profile = good_profile()
            path = write_profile(d, profile)
            data = O.load_profile(path)
            report = O.check(data, path, env=FULL_ENV)
            self.assertEqual(report["status"], "pass")
            self.assertEqual([p["seed_id"] for p in report["phases"]],
                             ["SEED-001", "SEED-004", "SEED-009"])

    def test_12_check_missing_credentials_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            for name in (CORE, BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            path = write_profile(d, good_profile())
            report = O.check(O.load_profile(path), path, env={})
            self.assertEqual(report["status"], "blocked")
            self.assertTrue(all(p["status"] == "blocked" for p in report["phases"]))

    def test_13_check_missing_plan_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_profile(d, good_profile(phases=[
                {"seed_id": "SEED-012", "plan": "plans/missing.json"}]))
            report = O.check(O.load_profile(path), path, env=FULL_ENV)
            self.assertEqual(report["status"], "error")
            self.assertEqual(report["phases"][0]["issues"][0]["code"], "CT-000")


class TestRun(unittest.TestCase):
    def test_14_dry_run_default_no_credentials_needed(self):
        with tempfile.TemporaryDirectory() as d:
            for name in (CORE, BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            path = write_profile(d, good_profile())
            report = O.run_onboarding(O.load_profile(path), path, apply=False, env={})
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["mode"], "dry_run")
            self.assertTrue(all(p["status"] == "pass" for p in report["phases"]))

    def test_15_apply_delegates_each_phase(self):
        calls = []
        def fake(plan, **kw):
            calls.append(kw)
            return pass_report()
        with tempfile.TemporaryDirectory() as d:
            for name in (CORE, BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            path = write_profile(d, good_profile())
            report = O.run_onboarding(O.load_profile(path), path, apply=True,
                                      env=FULL_ENV, executor_run=fake)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["mode"], "apply")
        self.assertEqual(len(calls), 3)  # 每阶段恰好委派一次
        self.assertTrue(all(c["apply"] is True for c in calls))

    def test_16_chain_fail_closed_stops_later_phases(self):
        seen = []
        def fake(plan, **kw):
            seed_name = str(plan.get("seed_name", ""))
            seen.append("base" if "基础数据" in seed_name else "other")
            if "基础数据" in seed_name:  # SEED-004 阶段 blocked
                return {"status": "blocked", "executed_count": 0,
                        "skipped_actions": [],
                        "issues": [{"code": "CT-007", "severity": "blocked", "message": "x"}]}
            return pass_report()
        with tempfile.TemporaryDirectory() as d:
            for name in (CORE, BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            path = write_profile(d, good_profile())
            report = O.run_onboarding(O.load_profile(path), path, apply=True,
                                      env=FULL_ENV, executor_run=fake)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["stopped_at"], "SEED-004")
        statuses = [(p["seed_id"], p["status"]) for p in report["phases"]]
        self.assertEqual(statuses, [("SEED-001", "pass"), ("SEED-004", "blocked"),
                                    ("SEED-009", "not_run")])
        self.assertEqual(seen, ["other", "base"])  # SEED-009 未委派

    def test_17_profile_error_zero_dispatch(self):
        calls = []
        def fake(plan, **kw):
            calls.append(1)
            return pass_report()
        with tempfile.TemporaryDirectory() as d:
            path = write_profile(d, good_profile(odoo_version="20.0"))
            report = O.run_onboarding(O.load_profile(path), path, apply=False,
                                      env=FULL_ENV, executor_run=fake)
        self.assertEqual(report["status"], "error")
        self.assertEqual(calls, [])

    def test_18_version_missing_fail_closed_at_profile_layer(self):
        """onboarding 在项目级强制版本：缺版本即 CT-003 error、零委派。

        这是与单动作执行器的有意分层差异——执行器允许 odoo_version 缺省（仅当
        动作带版本标注时才 CT-003），但项目接入编排要求先明确目标版本，属
        "快速无误"的项目级门禁。
        """
        calls = []
        def fake(plan, **kw):
            calls.append(1)
            return pass_report()
        with tempfile.TemporaryDirectory() as d:
            for name in (BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            profile = good_profile(odoo_version=None, phases=[
                {"seed_id": "SEED-004", "plan": BASE},
                {"seed_id": "SEED-009", "plan": SEED},
            ])
            path = write_profile(d, profile)
            report = O.run_onboarding(O.load_profile(path), path, apply=False,
                                      env={}, executor_run=fake)
        self.assertEqual(report["status"], "error")
        codes = {i["code"] for i in report["issues"]}
        self.assertIn("CT-003", codes)
        self.assertEqual(calls, [])  # 版本门禁先于任何委派
        self.assertEqual(report["phases"], [])


class TestCLI(unittest.TestCase):
    def test_19_cli_credential_arg_error_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            profile = good_profile()
            profile["password"] = "leaked"
            path = write_profile(d, profile)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "odoo_onboarding.py"),
                 "check", "--profile", path],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "error")

    def test_20_cli_dry_run_exit_0(self):
        with tempfile.TemporaryDirectory() as d:
            for name in (CORE, BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            path = write_profile(d, good_profile())
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "odoo_onboarding.py"),
                 "run", "--profile", path],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["mode"], "dry_run")

    def test_21_cli_check_missing_creds_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            for name in (CORE, BASE, SEED):
                (Path(d) / name).write_text((TEMPLATES / name).read_text(encoding="utf-8"),
                                            encoding="utf-8")
            path = write_profile(d, good_profile())
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "odoo_onboarding.py"),
                 "check", "--profile", path],
                capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
