#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册表集成回归测试。

锁定 `odoo-implementation` 已被 Capability Twin 的发现体系接纳：
它不能只在磁盘上存在、却不被内部注册表认识（那会成为无法被
execute_skill / 能力列举发现的孤岛）。

断言对象是 discover_capabilities.py 的既有输出，不引入新的发现机制。
"""

import json
import re
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
SKILLS_ROOT = SKILL_ROOT.parent
REGISTRY = SKILL_ROOT / "capability_registry.json"
ODOO_IMPL_DIR = SKILLS_ROOT / "odoo-implementation"


def _load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _frontmatter_value(field: str) -> str:
    """从 SKILL.md frontmatter 读取单值字段；不引入 YAML 依赖。"""
    text = (ODOO_IMPL_DIR / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(field)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        raise AssertionError(f"SKILL.md frontmatter 缺少字段 {field}")
    return match.group(1).strip().strip("\"'")


class RegistryIntegrationTests(unittest.TestCase):
    """odoo-implementation 在注册表中的登记状态。"""

    @classmethod
    def setUpClass(cls):
        cls.registry = _load_registry()
        cls.skills = cls.registry.get("skills", {})

    def test_01_skill_is_registered(self):
        """新技能包必须出现在 skills 节点，否则 CT 无从发现它。"""
        self.assertIn("odoo-implementation", self.skills,
                      "odoo-implementation 未登记：请运行 discover_capabilities.py")

    def test_02_registry_points_to_real_files(self):
        """注册表里的 path/file 必须解析到真实存在的技能文件。"""
        entry = self.skills["odoo-implementation"]
        skill_dir = SKILLS_ROOT / entry["path"]
        skill_file = SKILLS_ROOT / entry["file"]
        self.assertTrue(skill_dir.is_dir(), f"path 不存在：{skill_dir}")
        self.assertTrue(skill_file.is_file(), f"file 不存在：{skill_file}")
        self.assertEqual(skill_file.name, "SKILL.md")

    def test_03_skills_used_references_are_closed(self):
        """声明的技能依赖必须都已在注册表，引用不能悬空。"""
        entry = self.skills["odoo-implementation"]
        for used in entry.get("skills_used", []):
            self.assertIn(used, self.skills,
                          f"skills_used 引用了未登记的技能：{used}")

    def test_04_registered_entry_matches_frontmatter(self):
        """登记元数据来自 SKILL.md frontmatter，不得与之漂移。

        版本必须从 SKILL.md 动态读取：曾把 0.1.0 硬编码进断言，导致
        SKILL.md 升至 0.4.0 而注册表仍停在 0.1.0 时测试依然全绿（假绿）。
        """
        entry = self.skills["odoo-implementation"]
        self.assertEqual(entry["version"], _frontmatter_value("version"),
                         "注册表版本与 SKILL.md frontmatter 漂移：请重跑 discover_capabilities.py")
        self.assertEqual(entry["allowed_tools"],
                         ["Read", "Write", "Edit", "Glob", "Grep", "Bash"])

    def test_05_registry_keeps_capabilities_empty(self):
        """保持 CT 原架构：不借集成之名填充 capabilities 空节点。"""
        self.assertEqual(self.registry.get("capabilities", {}), {},
                         "capabilities 应为空——五层能力链/能力登记不在本次范围")


if __name__ == "__main__":
    unittest.main()
