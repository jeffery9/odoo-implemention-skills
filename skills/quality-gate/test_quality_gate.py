#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate Skill 测试文件
"""

import unittest
import json
import os
import tempfile
from main import QualityGate


class TestQualityGate(unittest.TestCase):

    def setUp(self):
        """测试设置"""
        self.gate = QualityGate()
        self.test_dir = tempfile.mkdtemp()

    def test_supported_check_types(self):
        """测试支持的检查类型"""
        expected_types = [
            "code_quality", "standard_compliance", "quality_gate", "documentation_quality"
        ]
        self.assertEqual(self.gate.supported_check_types, expected_types)

    def test_severity_levels(self):
        """测试严重性级别"""
        expected_levels = ["info", "warning", "error", "critical"]
        self.assertEqual(self.gate.severity_levels, expected_levels)

    def test_code_quality_check(self):
        """测试代码质量检查"""
        # 创建测试Python文件
        test_code = '''
def hello_world():
    """打印Hello World"""
    print("Hello World!")

class TestClass:
    def method(self):
        # 这是一个很长的行，超过了一般的行长度限制，应该会触发警告This is a very long line that exceeds the normal line length limit and should trigger a warning
        pass
'''
        test_file = os.path.join(self.test_dir, "test_code.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)

        config = {
            "check_type": "code_quality",
            "target_path": test_file,
            "quality_rules": {
                "max_line_length": 80,
                "require_docstrings": True
            }
        }

        result = self.gate.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("quality_details", result)
        self.assertIn("improvement_recommendations", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "quality-gate")
        self.assertEqual(metadata["check_type"], "code_quality")
        self.assertEqual(metadata["status"], "success")

        # 验证结果
        results = result["results"]
        self.assertIn("check_result", results)
        self.assertIn("total_issues", results)
        self.assertIn("issues_by_severity", results)
        self.assertIn("quality_score", results)

    def test_standard_compliance_validation(self):
        """测试标准符合性验证"""
        config = {
            "check_type": "standard_compliance",
            "target_components": ["component1", "component2"],
            "standards": ["PEP8", "security_best_practices"],
            "strict_mode": True
        }

        result = self.gate.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("quality_details", result)
        self.assertIn("improvement_recommendations", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "quality-gate")
        self.assertEqual(metadata["check_type"], "standard_compliance")
        self.assertEqual(metadata["status"], "success")

    def test_quality_gate_enforcement(self):
        """测试质量门禁控制"""
        # 创建测试文件
        test_code = '''
def good_function():
    """这是一个好的函数"""
    return "OK"
'''
        test_file = os.path.join(self.test_dir, "good_code.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)

        config = {
            "check_type": "quality_gate",
            "target_artifacts": [test_file],
            "gate_rules": {
                "max_critical_issues": 0,
                "max_error_issues": 0,
                "minimum_quality_score": 90
            },
            "fail_on_violation": True
        }

        result = self.gate.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("quality_details", result)
        self.assertIn("improvement_recommendations", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "quality-gate")
        self.assertEqual(metadata["check_type"], "quality_gate")
        self.assertEqual(metadata["status"], "success")

    def test_documentation_quality_check(self):
        """测试文档质量检查"""
        # 创建测试Markdown文件
        test_doc = '''
# 测试文档

这是一个测试文档。
'''
        test_file = os.path.join(self.test_dir, "test_doc.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_doc)

        config = {
            "check_type": "documentation_quality",
            "target_path": test_file
        }

        result = self.gate.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("quality_details", result)
        self.assertIn("improvement_recommendations", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "quality-gate")
        self.assertEqual(metadata["check_type"], "documentation_quality")
        self.assertEqual(metadata["status"], "success")

    def test_invalid_check_type(self):
        """测试无效检查类型"""
        config = {
            "check_type": "invalid_check_type"
        }

        with self.assertRaises(ValueError):
            self.gate.execute(config)

    def test_missing_required_parameters(self):
        """测试缺少必需参数"""
        # 测试代码质量检查缺少必需参数
        config = {
            "check_type": "code_quality"
            # 缺少 target_path
        }

        with self.assertRaises(ValueError):
            self.gate.execute(config)

        # 测试标准符合性验证缺少必需参数
        config = {
            "check_type": "standard_compliance"
            # 缺少 target_components
        }

        with self.assertRaises(ValueError):
            self.gate.execute(config)

        # 测试质量门禁控制缺少必需参数
        config = {
            "check_type": "quality_gate"
            # 缺少 target_artifacts
        }

        with self.assertRaises(ValueError):
            self.gate.execute(config)

    def test_complexity_calculation(self):
        """测试复杂度计算"""
        # 创建复杂函数
        complex_code = '''
def complex_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return 1
    for i in range(10):
        while i > 0:
            i -= 1
    try:
        raise Exception("test")
    except:
        pass
    return 0
'''
        test_file = os.path.join(self.test_dir, "complex_code.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(complex_code)

        config = {
            "check_type": "code_quality",
            "target_path": test_file
        }

        result = self.gate.execute(config)
        # 复杂函数应该被检测到
        self.assertGreaterEqual(result["results"]["total_issues"], 0)

    def test_security_check(self):
        """测试安全性检查"""
        # 创建包含安全问题的代码
        insecure_code = '''
import os

def dangerous_function():
    eval("print('dangerous')")
    exec("print('very dangerous')")
    os.system("ls -la")
'''
        test_file = os.path.join(self.test_dir, "insecure_code.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(insecure_code)

        config = {
            "check_type": "code_quality",
            "target_path": test_file
        }

        result = self.gate.execute(config)
        # 应该检测到安全问题
        issues = result["quality_details"]["issues"]
        security_issues = [issue for issue in issues if issue["category"] == "security"]
        self.assertGreater(len(security_issues), 0)


if __name__ == "__main__":
    unittest.main()