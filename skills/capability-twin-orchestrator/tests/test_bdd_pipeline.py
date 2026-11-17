#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gherkin BDD 与流水线集成的回归测试。

覆盖的是「门禁能不能真的拦住东西」，而不只是「正常时能跑通」：
- 模块无规格时回落到基线，但**不得**冒充模块级通过；
- 规格违规时 preflight 与 Step 10→11 都必须阻断；
- 交付包不得把别的模块的场景渲染进本模块文档；
- 质量门 `scenario_spec` 与独立命令使用同一套判定。
"""

import importlib.util
import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "capability-twin-orchestrator" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "scripts"))

import main as ct_main                      # noqa: E402
from config import CapabilityTwinConfig     # noqa: E402
from bdd_gate import BDDGate                # noqa: E402

GOOD_FEATURE = """# language: zh-CN
@ct-module=stock
@ct-source=addons/stock/models/stock_picking.py:L642
功能: 库存调拨完成后的可用量变化

  @ct-id=SCN-STK-901 @ct-unit=CU-STK-001 @ct-gate=G2 @ct-priority=P0
  场景: 调拨完成时源库位可用量减少
    假如 库位「WH/Stock」中商品「A」的可用量为 20 件
    当 完成一次从「WH/Stock」到「WH/Output」的调拨，数量 5 件
    那么 库位「WH/Stock」中商品「A」的可用量变为 15 件
    而且 库位「WH/Output」中商品「A」的可用量增加 5 件
"""

BAD_FEATURE = """# language: zh-CN
@ct-module=stock
功能: 缺少标签与断言的坏规格

  场景: 只有前置条件
    假如 库位「WH/Stock」中商品「A」的可用量为 20 件
"""


def _write_feature(root: Path, module: str, name: str, text: str) -> Path:
    target = root / module / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _load_quality_gate():
    path = ROOT / "skills" / "quality-gate" / "main.py"
    spec = importlib.util.spec_from_file_location("ct_quality_gate", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("ct_quality_gate", module)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BDDGateUnitTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_pass_in_module_scope_derives_artifacts(self):
        feats = self.tmp / "features"
        _write_feature(feats, "stock", "good.feature", GOOD_FEATURE)
        gate = BDDGate(features_dir=str(feats), output_dir=str(self.tmp / "out"))
        run = gate.run(module="stock", derive=True)

        self.assertEqual(run["status"], "pass")
        self.assertEqual(run["scope"], "module:stock")
        self.assertTrue(run["satisfies_module"])
        self.assertEqual(run["scenarios"], 1)
        for key in ("uat_files", "steps_files", "matrix"):
            self.assertTrue(run["derived"].get(key), f"缺少派生产物: {key}")
        self.assertTrue((ROOT / run["report_path"]).is_file())

    def test_baseline_pass_does_not_satisfy_module(self):
        feats = self.tmp / "features"
        _write_feature(feats, "stock", "good.feature", GOOD_FEATURE)
        gate = BDDGate(features_dir=str(feats), output_dir=str(self.tmp / "out"))
        run = gate.run(module="hr", derive=False)

        self.assertEqual(run["status"], "pass")
        self.assertEqual(run["scope"], "baseline")
        self.assertFalse(run["satisfies_module"])
        self.assertIn("未满足模块级验收", BDDGate.summary_line(run))

    def test_invalid_spec_fails_and_derives_nothing(self):
        feats = self.tmp / "features"
        _write_feature(feats, "stock", "bad.feature", BAD_FEATURE)
        gate = BDDGate(features_dir=str(feats), output_dir=str(self.tmp / "out"))
        run = gate.run(module="stock", derive=True)

        self.assertEqual(run["status"], "fail")
        self.assertTrue(run["blocking"])
        self.assertFalse(run["satisfies_module"])
        self.assertTrue(run["blocking_issues"])
        self.assertEqual(run["derived"], {})

    def test_deliverable_context_does_not_leak_other_modules(self):
        feats = self.tmp / "features"
        _write_feature(feats, "stock", "good.feature", GOOD_FEATURE)
        gate = BDDGate(features_dir=str(feats), output_dir=str(self.tmp / "out"))
        run = gate.run(module="hr", derive=False)
        ctx = gate.deliverable_context(module="hr", run=run)

        self.assertIn("尚未建立场景规格", ctx["scenario_ids"])
        self.assertNotIn("SCN-STK-901", ctx["gherkin_feature"])


class PipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = CapabilityTwinConfig(output_directory=str(self.tmp / "runs"))

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_preflight_blocks_on_invalid_spec(self):
        feats = self.tmp / "features"
        _write_feature(feats, "stock", "bad.feature", BAD_FEATURE)

        orch = ct_main.CapabilityTwinOrchestratorSkill(config=self.cfg)
        result = orch.execute_workflow({
            "target_module": "stock",
            "workflow_type": "full_analysis",
            "bdd": {"features_dir": str(feats), "output_dir": str(self.tmp / "bdd")},
        })

        self.assertEqual(result["status"], "blocked")
        self.assertIn("preflight", result["blocked_at"])
        self.assertNotIn("supply_side_results", result)   # 分析阶段根本没启动
        self.assertTrue(result["gate"]["blocking_issues"])

        plan = (self.tmp / "runs" / orch.workflow_id / "task_plan.md").read_text(encoding="utf-8")
        self.assertIn("Blocked by BDD spec gate", plan)
        self.assertIn("- [ ] L1 Gherkin spec gate passed", plan)

    def test_pass_path_records_gate_in_task_plan(self):
        orch = ct_main.CapabilityTwinOrchestratorSkill(config=self.cfg)
        result = orch.execute_workflow({
            "target_module": "account",
            "workflow_type": "supply_side_analysis",
            "bdd": {"output_dir": str(self.tmp / "bdd")},
        })
        self.assertNotEqual(result["status"], "blocked")
        self.assertEqual(result["bdd_gate"]["status"], "pass")

        plan = (self.tmp / "runs" / orch.workflow_id / "task_plan.md").read_text(encoding="utf-8")
        self.assertIn("- [x] L1 Gherkin spec gate passed", plan)

    def test_extraction_gate_stops_before_packaging(self):
        feats = self.tmp / "features"
        _write_feature(feats, "stock", "bad.feature", BAD_FEATURE)

        orch = ct_main.CapabilityTwinOrchestratorSkill(config=self.cfg)
        result = orch.execute_capability_extraction_workflow({
            "target_module": "stock",
            "bdd": {"features_dir": str(feats), "output_dir": str(self.tmp / "bdd")},
        })

        self.assertEqual(result["status"], "blocked")
        steps = [item.get("step") for item in result["results"]]
        self.assertIn(10, steps)
        self.assertIsNone(steps[-1])          # 门禁条目挂在 Step 10 之后
        self.assertNotIn(11, steps)           # 打包从未执行
        self.assertTrue(result["gate"]["blocking_issues"])


class BundleRenderingTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = CapabilityTwinConfig(output_directory=str(self.tmp / "runs"))

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_module_without_spec_skips_scenario_templates(self):
        orch = ct_main.CapabilityTwinOrchestratorSkill(config=self.cfg)
        out = self.tmp / "developer"
        result = orch.render_deliverables_bundle({
            "bundle_type": "developer",
            "target_module": "hr",           # 仓内没有 features/hr
            "output_directory": str(out),
            "bdd": {"output_dir": str(self.tmp / "bdd")},
        })

        self.assertIn("SCENARIO_SOLUTION", result["blocked_templates"])
        self.assertFalse((out / "SCENARIO_SOLUTION.md").exists())
        self.assertFalse(result["scenario_binding"]["satisfies_module"])
        self.assertTrue((out / "CAPABILITY_UNIT_SPEC.md").exists())

    def test_spec_drives_context_and_overrides_manual_input(self):
        orch = ct_main.CapabilityTwinOrchestratorSkill(config=self.cfg)
        out = self.tmp / "consultant"
        result = orch.render_deliverables_bundle({
            "bundle_type": "consultant",
            "target_module": "account",
            "output_directory": str(out),
            "context_data": {"scenario_name": "人工旧标题"},
            "bdd": {"output_dir": str(self.tmp / "bdd")},
        })

        self.assertEqual(result["status"], "success")
        self.assertIn("scenario_name", result["context_overrides"])

        uat = (out / "CONSULTANT_UAT_SCRIPT.md").read_text(encoding="utf-8")
        self.assertIn("SCN-ACC-001", uat)
        self.assertNotIn("人工旧标题", uat)
        self.assertNotIn("{{", uat)           # 场景字段已全部由规格派生


class QualityGateIntegrationTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_scenario_spec_check_shares_verdict(self):
        qg = _load_quality_gate()
        gate = qg.QualityGate()

        ok = gate.execute({"check_type": "scenario_spec",
                           "target_path": str(ROOT / "skills/gherkin-bdd/features")})
        self.assertEqual(ok["results"]["check_result"], "pass")
        self.assertEqual(ok["results"]["scenario_metrics"]["errors"], 0)

        feats = self.tmp / "features"
        _write_feature(feats, "stock", "bad.feature", BAD_FEATURE)
        bad = gate.execute({"check_type": "scenario_spec", "target_path": str(feats)})
        self.assertEqual(bad["results"]["check_result"], "fail")
        self.assertTrue(bad["quality_details"]["gate_decision"]["blocking_issues"])
        self.assertFalse(bad["quality_details"]["gate_decision"]["passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
