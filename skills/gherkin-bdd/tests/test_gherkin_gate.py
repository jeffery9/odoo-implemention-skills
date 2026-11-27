#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gherkin-bdd 能力单元自测。

与框架既有测试一致，使用 unittest + 纯标准库，不引入 pytest-bdd / behave 依赖。
重点验证「违规一定被测出」（不假绿），而不只验证正例能过。
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import gherkin_gate as gg  # noqa: E402

GOOD = """# language: zh-CN
@ct-module=account
@ct-source=addons/account/models/account_move.py:L128
功能: 发出商品的收入与成本配比
  作为 财务负责人
  我希望 发货未开票时收入暂不确认
  以便 符合中国企业会计准则的配比要求

  背景:
    假如 账套「华东公司」已启用中国企业会计科目表

  @ct-id=SCN-ACC-001 @ct-unit=CU-ACC-014 @ct-gate=G2
  场景: 发货未开票时确认发出商品
    假如 销售订单「SO-001」已确认，商品「A」的可用量为 10 件
    当 仓库按销售订单发货，发出商品「A」10 件且尚未开票
    那么 该批商品计入「发出商品」10 件
    而且 当期主营业务收入不含该批商品金额 1200 元
"""


class GherkinGateTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _features(self, text: str, module: str = "account",
                  filename: str = "sample.feature") -> Path:
        target = self.root / "features" / module / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return self.root / "features"

    def _codes(self, text: str, module: str = "account", **kwargs):
        report = gg.validate(self._features(text, module=module), **kwargs)
        return report, {i["code"] for i in report["issues"]}

    # ---------- 正例 ----------

    def test_good_feature_passes_without_noise(self):
        report, codes = self._codes(GOOD)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["warnings"], 0)
        self.assertEqual(report["scenarios"], 1)
        self.assertEqual(codes, set())

    def test_shipped_examples_are_clean(self):
        report = gg.validate(SKILL_DIR / "features")
        self.assertEqual(report["status"], "pass")
        # 数字由目录内容推导，避免新增场景后测试假绿/假红（A 级验收线 §6）。
        expected_features = len(list((SKILL_DIR / "features").rglob("*.feature")))
        self.assertEqual(report["features"], expected_features)
        self.assertGreaterEqual(report["scenarios"], expected_features)
        self.assertEqual(report["errors"], 0)

    def test_feature_level_tags_are_inherited_and_overridden(self):
        text = GOOD.replace(
            "@ct-id=SCN-ACC-001 @ct-unit=CU-ACC-014 @ct-gate=G2",
            "@ct-id=SCN-ACC-001 @ct-unit=CU-ACC-014 @ct-gate=G3")
        report = gg.validate(self._features(text))
        index = report["scenario_index"][0]
        self.assertEqual(index["module"], "account")     # 继承功能级
        self.assertEqual(index["source"], "addons/account/models/account_move.py:L128")
        self.assertEqual(index["gate"], "G3")           # 场景级覆盖

    def test_warning_only_still_passes(self):
        text = GOOD.replace("@ct-module=account", "@ct-module=stock")
        report, codes = self._codes(text)
        self.assertEqual(report["status"], "pass")
        self.assertIn("BDD-014", codes)
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["warnings"], 1)

    # ---------- 反例：每条规则都要能被测出 ----------

    def test_bdd_001_missing_language(self):
        _, codes = self._codes(GOOD.replace("# language: zh-CN\n", "", 1))
        self.assertIn("BDD-001", codes)

    def test_bdd_002_english_keywords(self):
        text = GOOD.replace("功能:", "Feature:").replace("场景:", "Scenario:")
        text = text.replace("背景:", "Background:")
        text = (text.replace("假如 ", "Given ").replace("当 ", "When ")
                    .replace("那么 ", "Then ").replace("而且 ", "And "))
        report, codes = self._codes(text)
        self.assertIn("BDD-002", codes)
        self.assertEqual(report["status"], "fail")
        relaxed, _ = self._codes(text, allow_en=True)
        self.assertEqual(relaxed["status"], "pass")   # 迁移期降级为 warning

    def test_bdd_003_missing_required_tags(self):
        text = GOOD.replace(" @ct-unit=CU-ACC-014 @ct-gate=G2", "")
        _, codes = self._codes(text)
        self.assertIn("BDD-003", codes)

    def test_bdd_004_duplicate_scenario_id(self):
        extra = GOOD.split("  场景:")[1]
        text = GOOD + "\n  @ct-id=SCN-ACC-001 @ct-unit=CU-ACC-014 @ct-gate=G2\n  场景:" + extra.replace(
            " 发货未开票时确认发出商品", " 重复编号场景", 1)
        _, codes = self._codes(text)
        self.assertIn("BDD-004", codes)

    def test_bdd_005_missing_when(self):
        text = GOOD.replace("    当 仓库按销售订单发货，发出商品「A」10 件且尚未开票\n", "")
        _, codes = self._codes(text)
        self.assertIn("BDD-005", codes)

    def test_bdd_006_step_order(self):
        text = GOOD.replace(
            "    那么 该批商品计入「发出商品」10 件\n",
            "    那么 该批商品计入「发出商品」10 件\n    当 财务对该销售订单开票，发票金额 1200 元\n")
        _, codes = self._codes(text)
        self.assertIn("BDD-006", codes)
        self.assertIn("BDD-012", codes)

    def test_bdd_007_banned_alias_and_model_name(self):
        alias, codes = self._codes(GOOD.replace("销售订单", "客户订单"))
        self.assertIn("BDD-007", codes)
        self.assertEqual(alias["status"], "fail")
        model, codes2 = self._codes(GOOD.replace("账套「华东公司」", "account.move 记录"))
        self.assertIn("BDD-007", codes2)

    def test_bdd_008_placeholder_mismatch(self):
        text = GOOD.replace(
            "  场景: 发货未开票时确认发出商品",
            "  场景大纲: 发货未开票时确认发出商品")
        text = text.replace("商品「A」的可用量为 10 件", "商品「A」的可用量为 <可用量> 件")
        text += "\n    例子:\n      | 发货数量 |\n      | 10       |\n"
        _, codes = self._codes(text)
        self.assertIn("BDD-008", codes)

    def test_bdd_009_examples_bad_rows(self):
        text = GOOD.replace(
            "  场景: 发货未开票时确认发出商品",
            "  场景大纲: 发货未开票时确认发出商品")
        text = text.replace("商品「A」的可用量为 10 件", "商品「A」的可用量为 <可用量> 件")
        text += "\n    例子:\n      | 可用量 |\n      | 10 | 20 |\n"
        _, codes = self._codes(text)
        self.assertIn("BDD-009", codes)

    def test_bdd_010_hash_in_tag_line(self):
        _, codes = self._codes(GOOD.replace("@ct-id=SCN-ACC-001", "@ct-id=SCN#1"))
        self.assertIn("BDD-010", codes)

    def test_bdd_011_feature_without_scenario(self):
        text = GOOD.split("  @ct-id=")[0]
        _, codes = self._codes(text)
        self.assertIn("BDD-011", codes)

    def test_bdd_013_bad_id_format(self):
        _, codes = self._codes(GOOD.replace("SCN-ACC-001", "SCN-1"))
        self.assertIn("BDD-013", codes)

    def test_bdd_014_module_dir_mismatch(self):
        _, codes = self._codes(GOOD, module="stock")
        self.assertIn("BDD-014", codes)

    def test_bdd_018_unparsable_line(self):
        text = GOOD.replace(
            "    那么 该批商品计入「发出商品」10 件",
            "    这一行既不是步骤也不是数据表\n    那么 该批商品计入「发出商品」10 件")
        _, codes = self._codes(text)
        self.assertIn("BDD-018", codes)

    def test_bdd_020_no_feature_files(self):
        empty = self.root / "features" / "account"
        empty.mkdir(parents=True, exist_ok=True)
        report = gg.validate(self.root / "features")
        self.assertEqual(report["status"], "fail")
        self.assertIn("BDD-020", {i["code"] for i in report["issues"]})

    # ---------- 生成器 ----------

    def test_generate_uat_steps_and_matrix(self):
        root = self._features(GOOD)
        report = gg.validate(root)
        features = report["_features"]
        out = self.root / "out"

        uat = gg.generate_uat(features, out / "uat")
        self.assertEqual(len(uat), 1)
        content = (out / "uat" / Path(uat[0]).name).read_text(encoding="utf-8")
        self.assertIn("SCN-ACC-001", content)
        self.assertIn("预期结果", content)
        self.assertIn("价值实现", content)   # FDE 边界声明

        steps = gg.generate_steps(features, out / "steps")
        self.assertEqual(len(steps), 1)
        code = (out / "steps" / Path(steps[0]).name).read_text(encoding="utf-8")
        compile(code, steps[0], "exec")      # 生成代码必须语法合法
        self.assertIn("NotImplementedError", code)
        self.assertIn("pytest_bdd", code)

        behave = gg.generate_steps(features, out / "behave", style="behave")
        behave_code = (out / "behave" / Path(behave[0]).name).read_text(encoding="utf-8")
        compile(behave_code, behave[0], "exec")
        self.assertIn("from behave import", behave_code)

        matrix_path = out / "matrix.json"
        gg.generate_matrix(features, matrix_path)
        payload = json.loads(matrix_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["scenarios"][0]["id"], "SCN-ACC-001")
        self.assertIn("CU-ACC-014", payload["by_unit"])

    def test_parameterized_steps_produce_parse_expressions(self):
        text = GOOD.replace(
            "  场景: 发货未开票时确认发出商品",
            "  场景大纲: 发货未开票时确认发出商品")
        text = text.replace("商品「A」的可用量为 10 件", "商品「A」的可用量为 <可用量> 件")
        text += "\n    例子:\n      | 可用量 |\n      | 10     |\n"
        root = self._features(text)
        self.assertEqual(gg.validate(root)["status"], "pass")
        out = self.root / "out"
        written = gg.generate_steps(gg.validate(root)["_features"], out)
        code = (out / Path(written[0]).name).read_text(encoding="utf-8")
        compile(code, written[0], "exec")
        self.assertIn("{可用量}", code)
        self.assertIn("可用量)", code)

    # ---------- CLI 契约 ----------

    def test_cli_exit_codes_and_blocked_generation(self):
        good = self._features(GOOD)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gg.main(["validate", str(good)]), 0)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gg.main(["uat", str(good), "-o", str(self.root / "uat")]), 0)
        self.assertTrue((self.root / "uat").is_dir())

        self._features(GOOD.replace("# language: zh-CN\n", "", 1),
                       module="stock", filename="bad.feature")
        bad_file = self.root / "features" / "stock" / "bad.feature"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gg.main(["validate", str(good)]), 1)
        blocked_out = self.root / "blocked"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gg.main(["uat", str(bad_file), "-o", str(blocked_out)]), 1)
        self.assertFalse(blocked_out.exists())   # 规格不合格时拒绝派生交付物
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gg.main(["uat", str(bad_file), "-o", str(blocked_out), "--force"]), 0)
        self.assertTrue(blocked_out.exists())

    def test_cli_missing_path_returns_tool_error(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(gg.main(["validate", str(self.root / "nope")]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
