#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""仓库级工具脚本的厂商中立性守卫。

覆盖两类回归：
1. 定位逻辑不得只认某个厂商的容器目录（`.claude` / `.agents` / `skills` 均可）；
2. 脚本源码不得重新写死已废弃的模板名或单一厂商标记。

不依赖任何真实厂商目录；用 tempfile 构造最小容器结构。
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import finalize_documentation as fd
import update_capability_registry as ucr


class FinalizeDocVendorNeutralTest(unittest.TestCase):
    """交付模板定位：容器名任意，不得绑定 `.claude`。"""

    def _make_container(self, root, container):
        deliverables = root / container / "template-processor" / "templates" / "deliverables"
        deliverables.mkdir(parents=True, exist_ok=True)
        (deliverables / "FUNCTIONAL_DOC_SPEC.md").write_text("template", encoding="utf-8")
        return deliverables

    def test_find_deliverables_in_plain_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self._make_container(root, "skills")
            self.assertEqual(fd.find_deliverables_dir(root), expected)

    def test_find_deliverables_in_hidden_non_claude_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self._make_container(root, ".agents/skills")
            self.assertEqual(fd.find_deliverables_dir(root), expected)

    def test_find_deliverables_in_other_hidden_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self._make_container(root, ".workbuddy/skills")
            self.assertEqual(fd.find_deliverables_dir(root), expected)

    def test_missing_deliverables_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(fd.find_deliverables_dir(Path(tmp)))

    def test_no_dead_template_name(self):
        source = (SCRIPTS_DIR / "finalize_documentation.py").read_text(encoding="utf-8")
        self.assertNotIn("STRATEGIC_FUNCTIONAL_SPEC_V6.md", source)
        self.assertNotIn("GEMINI.md", source)


class UpdateRegistryVendorNeutralTest(unittest.TestCase):
    """旧注册表路径识别：按 agents/skills 目录段，不看容器名。"""

    def test_identifies_agents_segment(self):
        self.assertEqual(
            ucr._legacy_kind("/opt/proj/.claude/agents/foo/AGENT.md"), "agents")

    def test_identifies_skills_segment(self):
        self.assertEqual(
            ucr._legacy_kind("/opt/proj/.agents/skills/bar/SKILL.md"), "skills")

    def test_identifies_windows_paths(self):
        self.assertEqual(
            ucr._legacy_kind(r"D:\proj\.workbuddy\skills\baz\SKILL.md"), "skills")

    def test_unrelated_path_is_ignored(self):
        self.assertIsNone(ucr._legacy_kind("/opt/proj/docs/readme.md"))

    def test_no_single_vendor_marker(self):
        source = (SCRIPTS_DIR / "update_capability_registry.py").read_text(encoding="utf-8")
        self.assertNotIn('MARKER = "/.claude"', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
