# -*- coding: utf-8 -*-
"""契约校验器自测：既有技能不误伤、四类负例必须失败、schema 与脚本不漂移。"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SKILL_DIR = TEST_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
REPO_ROOT = SKILL_DIR.parent.parent
VALIDATOR = SCRIPTS_DIR / "validate_odoo_manifest.py"


def _load_validator():
    """按唯一模块名加载，避免与其他技能的 main.py 撞车。"""
    name = "ct_odoo_validate_manifest"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V = _load_validator()


def _manifest(extra: str) -> str:
    return f"---\nname: probe\ndescription: probe\nversion: 0.1.0\n{extra}\n---\n# probe\n"


class ParseFrontmatterTests(unittest.TestCase):
    def test_inline_arrays(self):
        text = _manifest('ct_odoo_versions: ["17.0", "18.0", "19.0"]')
        manifest, lines = V.parse_frontmatter(text)
        self.assertEqual(manifest["ct_odoo_versions"], ["17.0", "18.0", "19.0"])
        self.assertGreater(lines["ct_odoo_versions"], 0)

    def test_missing_frontmatter_is_tool_error(self):
        with self.assertRaises(V.ToolError):
            V.parse_frontmatter("# no frontmatter\n")

    def test_line_numbers_are_recorded(self):
        text = _manifest("ct_layer: broken")
        _, lines = V.parse_frontmatter(text)
        self.assertEqual(lines["ct_layer"], 5)


class ValidationTests(unittest.TestCase):
    def test_no_ct_fields_is_skipped_not_error(self):
        text = "---\nname: legacy\ndescription: legacy\n---\n# legacy\n"
        issues, status = V.validate_manifest(V.parse_frontmatter(text)[0], file="legacy.md")
        self.assertEqual(status, "skipped")
        self.assertEqual(issues, [])

    def test_four_negative_classes_all_error(self):
        cases = {
            "unknown_field": "ct_layer: shared\nct_bogus: yes",
            "bad_layer": "ct_layer: superlayer",
            "bad_version": 'ct_layer: core\nct_odoo_versions: [">=19.0"]',
            "layer_conflict": "ct_layer: shared\nct_module: account",
        }
        for name, extra in cases.items():
            with self.subTest(case=name):
                issues, status = V.validate_manifest(
                    V.parse_frontmatter(_manifest(extra))[0], file=f"{name}.md")
                self.assertEqual(status, "validated")
                self.assertTrue(any(i["severity"] == "error" for i in issues), name)

    def test_module_without_ct_module_errors(self):
        issues, _ = V.validate_manifest(
            V.parse_frontmatter(_manifest("ct_layer: module"))[0], file="m.md")
        self.assertTrue(any(i["code"] == "CT-001" for i in issues))

    def test_valid_manifest_passes(self):
        extra = 'ct_layer: module\nct_module: account\nct_odoo_versions: ["19.0"]\nct_scenario_refs: [SCN-ACC-001]\nct_state_outputs: [project-state]'
        issues, status = V.validate_manifest(
            V.parse_frontmatter(_manifest(extra))[0], file="valid.md")
        self.assertEqual(status, "validated")
        self.assertEqual([i for i in issues if i["severity"] == "error"], [])

    def test_scenario_ref_unreachable_errors(self):
        extra = "ct_layer: core\nct_scenario_refs: [SCN-NOT-EXIST]"
        issues, _ = V.validate_manifest(
            V.parse_frontmatter(_manifest(extra))[0], file="ref.md",
            features_dir=V.DEFAULT_FEATURES_DIR)
        self.assertTrue(any(i["code"] == "CT-004" for i in issues))


class SchemaSyncTests(unittest.TestCase):
    def test_field_sets_match_schema(self):
        schema = json.loads((SKILL_DIR / "schemas" / "odoo-implementation.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["properties"]), set(V.ALLOWED_FIELDS))
        layer_prop = schema["properties"]["ct_layer"]
        self.assertEqual(set(layer_prop["enum"]), set(V.VALID_LAYERS))
        self.assertEqual(schema["properties"]["ct_module"]["pattern"], V.MODULE_PATTERN.pattern)
        self.assertEqual(schema["properties"]["ct_odoo_versions"]["items"]["pattern"], V.VERSION_PATTERN.pattern)
        self.assertFalse(schema["additionalProperties"])

    def test_schema_if_then_requires_ct_module_for_module_layer(self):
        schema = json.loads((SKILL_DIR / "schemas" / "odoo-implementation.schema.json").read_text(encoding="utf-8"))
        rule = schema["allOf"][0]
        self.assertEqual(rule["if"]["properties"]["ct_layer"]["const"], "module")
        self.assertEqual(rule["then"]["required"], ["ct_module"])


class RealTreeTests(unittest.TestCase):
    def test_existing_skills_all_skipped(self):
        report = V.run(REPO_ROOT / "skills")
        self.assertEqual(report["status"], "pass")
        # 技能数由目录推导，归档离群技能后不再写死 21（A 级验收线 §6）。
        skill_cards = list((REPO_ROOT / "skills").rglob("SKILL.md"))
        self.assertGreater(len(skill_cards), 0)
        self.assertEqual(report["manifest_skipped"], len(skill_cards))
        self.assertEqual(report["manifest_checked"], 1)
        self.assertEqual(report["issues"], [])

    def test_cli_exit_codes(self):
        self.assertEqual(subprocess.run([sys.executable, str(VALIDATOR), str(SKILL_DIR / "SKILL.md")],
                                        capture_output=True).returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.md"
            bad.write_text(_manifest("ct_layer: nope"), encoding="utf-8")
            self.assertEqual(subprocess.run([sys.executable, str(VALIDATOR), str(bad)],
                                            capture_output=True).returncode, 1)
        self.assertEqual(subprocess.run([sys.executable, str(VALIDATOR), "/no/such/path"],
                                        capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
