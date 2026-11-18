# -*- coding: utf-8 -*-
"""P0 可选契约钩子的回归测试：默认关闭、开启只追加只读字段、不阻断流程。"""

import importlib.util
import logging
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import main as ct_main                      # noqa: E402
import framework_paths as fp                # noqa: E402


class OdooContractHookTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.tmp = Path(tempfile.mkdtemp())

    def test_optional_skill_resolver_is_non_fatal_when_absent(self):
        # required=False 是核心：未安装扩展技能时必须返回 None 而非抛错
        self.assertTrue(hasattr(fp, "odoo_implementation_dir"))
        result = fp.odoo_implementation_dir(required=False)
        self.assertTrue(result is None or result.is_dir())

    def test_contract_check_defaults_to_off(self):
        orch = ct_main.CapabilityTwinOrchestratorSkill()
        self.assertIsNone(orch._odoo_contract_check({}))
        self.assertIsNone(orch._odoo_contract_check({"odoo_contract": {}}))

    def test_preflight_has_no_contract_field_when_disabled(self):
        orch = ct_main.CapabilityTwinOrchestratorSkill()
        orch.bdd_gate = ct_main.BDDGate(
            features_dir=str(self.tmp), output_dir=str(self.tmp / "out"), enabled=True)
        result = orch._bdd_preflight({"target_module": "account", "bdd": {"blocking": False}})
        self.assertNotIn("odoo_contract", result)
        self.assertIn("run", result)

    def test_preflight_appends_readonly_contract_field_when_enabled(self):
        orch = ct_main.CapabilityTwinOrchestratorSkill()
        orch.bdd_gate = ct_main.BDDGate(
            features_dir=str(self.tmp), output_dir=str(self.tmp / "out"), enabled=True)
        result = orch._bdd_preflight({
            "target_module": "account",
            "bdd": {"blocking": False},
            "odoo_contract": {"enabled": True},
        })
        self.assertIn("odoo_contract", result)
        contract = result["odoo_contract"]
        self.assertTrue(contract["enabled"])
        self.assertIn(contract["status"], ("pass", "unavailable", "error"))
        # 契约校验失败不得翻转门禁结论
        self.assertNotIn("blocked", contract)

    def test_contract_error_never_blocks_pipeline(self):
        # 传入无法加载的路径配置，helper 必须降级为 unavailable/error 且不抛异常
        orch = ct_main.CapabilityTwinOrchestratorSkill()
        result = orch._odoo_contract_check({
            "odoo_contract": {"enabled": True, "manifest_path": "/no/such/file"}
        })
        self.assertIn(result["status"], ("pass", "unavailable", "error"))
        self.assertFalse(result.get("blocked", False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
