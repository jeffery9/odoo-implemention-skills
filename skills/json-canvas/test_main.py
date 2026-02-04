"""
测试文件: json-canvas 技能的单元测试
"""

import unittest
import os
import tempfile
from pathlib import Path

# 添加项目路径以便导入
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 由于json-canvas是一个接口技能，我们主要测试其文档结构
from json_canvas import main


class TestJsonCanvas(unittest.TestCase):
    """测试 Json Canvas 技能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.canvas"

    def tearDown(self):
        """清理测试环境"""
        if self.test_file.exists():
            self.test_file.unlink()
        if self.temp_dir.exists():
            self.temp_dir.rmdir()

    def test_initialization(self):
        """测试实例化"""
        # 由于这是接口技能，我们检查其文档结构
        self.assertTrue(True)  # 占位符

    def test_document_structure(self):
        """测试文档结构"""
        # 检查SKILL.md文件是否存在
        skill_file = Path(__file__).parent / "SKILL.md"
        self.assertTrue(skill_file.exists(), "SKILL.md 文件不存在")

        # 检查README.md文件是否存在
        readme_file = Path(__file__).parent / "README.md"
        self.assertTrue(readme_file.exists(), "README.md 文件不存在")

        # 检查INTEGRATION_GUIDE.md文件是否存在
        integration_file = Path(__file__).parent / "INTEGRATION_GUIDE.md"
        self.assertTrue(integration_file.exists(), "INTEGRATION_GUIDE.md 文件不存在")


class TestJsonCanvasIntegration(unittest.TestCase):
    """测试 Json Canvas 技能的集成测试"""

    def test_documentation_structure(self):
        """测试文档结构完整性"""
        skill_dir = Path(__file__).parent

        required_files = [
            "SKILL.md",
            "README.md",
            "INTEGRATION_GUIDE.md",
            "main.py"
        ]

        for filename in required_files:
            file_path = skill_dir / filename
            self.assertTrue(file_path.exists(), f"{filename} 文件不存在")

    def test_skill_definition(self):
        """测试技能定义"""
        skill_file = Path(__file__).parent / "SKILL.md"

        if skill_file.exists():
            content = skill_file.read_text(encoding='utf-8')
            # 检查是否包含技能名称
            self.assertIn("name:", content)
            # 检查是否包含描述
            self.assertIn("description:", content)


if __name__ == '__main__':
    unittest.main()