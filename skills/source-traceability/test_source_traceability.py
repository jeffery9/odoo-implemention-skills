#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Source Traceability Skill 测试文件
"""

import unittest
import json
import os
import tempfile
from main import SourceTraceabilityAnalyzer


class TestSourceTraceabilityAnalyzer(unittest.TestCase):

    def setUp(self):
        """测试设置"""
        self.analyzer = SourceTraceabilityAnalyzer()
        self.test_dir = tempfile.mkdtemp()

    def test_supported_verification_types(self):
        """测试支持的验证类型"""
        expected_types = [
            "reference_validation",
            "consistency_check",
            "traceability_assessment",
            "trustworthiness_assessment"
        ]
        self.assertEqual(self.analyzer.supported_verification_types, expected_types)

    def test_reference_validation_real(self):
        """测试引用验证真实逻辑"""
        # 创建临时测试文件
        test_file_name = "test_module.py"
        test_file = os.path.join(self.test_dir, test_file_name)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# 测试文件\nprint('Hello World')\nclass TestClass:\n    def test_function(self):\n        pass\n")

        config = {
            "verification_type": "reference_validation",
            "target_references": [
                {
                    "file_path": test_file_name,  # 使用相对路径
                    "line_numbers": [2, 2],
                    "expected_content": "Hello World"
                }
            ],
            "source_root": self.test_dir
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("verification_results", result)
        self.assertIn("traceability_metrics", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "source-traceability")
        self.assertEqual(metadata["verification_type"], "reference_validation")

        # 验证验证结果
        verification_results = result["verification_results"]
        self.assertIsInstance(verification_results, list)
        self.assertGreater(len(verification_results), 0)
        self.assertEqual(verification_results[0]["validation_status"], "valid")

    def test_consistency_check_real(self):
        """测试一致性检查真实逻辑"""
        # 创建临时测试文件
        test_file_name = "test_module.py"
        test_file = os.path.join(self.test_dir, test_file_name)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# 测试文件\nprint('Hello World')\n")

        config = {
            "verification_type": "consistency_check",
            "target_components": [
                {
                    "id": "test_component",
                    "references": [
                        {
                            "file_path": test_file_name,  # 使用相对路径
                            "line_numbers": [2, 2],
                            "expected_content": "Hello World"
                        }
                    ]
                }
            ],
            "source_root": self.test_dir
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("consistency_results", result)

        # 验证一致性检查结果
        consistency_results = result["consistency_results"]
        self.assertIsInstance(consistency_results, list)
        self.assertGreater(len(consistency_results), 0)
        self.assertIn("consistency_score", consistency_results[0])

    def test_traceability_assessment_real(self):
        """测试可追溯性评估真实逻辑"""
        # 创建临时测试文件
        test_file_name = "test_module.py"
        test_file = os.path.join(self.test_dir, test_file_name)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# 测试文件\nprint('Hello World')\n")

        config = {
            "verification_type": "traceability_assessment",
            "target_components": [
                {
                    "id": "test_component",
                    "references": [
                        {
                            "file_path": test_file_name,  # 使用相对路径
                            "line_numbers": [2, 2],
                            "expected_content": "Hello World"
                        }
                    ]
                }
            ],
            "source_root": self.test_dir
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("traceability_scores", result)

        # 验证可追溯性分数
        traceability_scores = result["traceability_scores"]
        self.assertIsInstance(traceability_scores, dict)
        self.assertIn("test_component", traceability_scores)

    def test_trustworthiness_assessment_real(self):
        """测试可信度评估真实逻辑"""
        # 创建临时测试文件
        test_file_name = "test_module.py"
        test_file = os.path.join(self.test_dir, test_file_name)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# 测试文件\nprint('Hello World')\nclass TestClass:\n    def test_function(self):\n        pass\n")

        config = {
            "verification_type": "trustworthiness_assessment",
            "target_components": [
                {
                    "id": "test_component",
                    "references": [
                        {
                            "file_path": test_file_name,  # 使用相对路径
                            "line_numbers": [2, 2],
                            "expected_content": "Hello World",
                            "expected_class": "TestClass",
                            "expected_function": "test_function"
                        }
                    ]
                }
            ],
            "assessment_criteria": ["completeness", "accuracy", "consistency"],
            "source_root": self.test_dir
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("trustworthiness_assessment", result)
        self.assertIn("improvement_recommendations", result)

        # 验证可信度评估结构
        trust_assessment = result["trustworthiness_assessment"]
        self.assertIn("component_scores", trust_assessment)
        self.assertIn("overall_score", trust_assessment)
        self.assertIn("confidence_level", trust_assessment)

    def test_invalid_verification_type(self):
        """测试无效验证类型"""
        config = {
            "verification_type": "invalid_type",
            "target_references": []
        }

        with self.assertRaises(ValueError):
            self.analyzer.analyze(config)

    def test_file_not_found_validation_real(self):
        """测试文件未找到的验证"""
        config = {
            "verification_type": "reference_validation",
            "target_references": [
                {
                    "file_path": "nonexistent/file.py",
                    "line_numbers": [1, 1]
                }
            ],
            "source_root": self.test_dir
        }

        result = self.analyzer.analyze(config)
        verification_results = result["verification_results"]

        self.assertEqual(len(verification_results), 1)
        self.assertEqual(verification_results[0]["validation_status"], "invalid")
        self.assertIn("File not found", verification_results[0]["validation_details"])

    def test_content_mismatch_validation_real(self):
        """测试内容不匹配的验证"""
        # 创建临时测试文件
        test_file_name = "test_module.py"
        test_file = os.path.join(self.test_dir, test_file_name)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("print('Hello World')\n")

        config = {
            "verification_type": "reference_validation",
            "target_references": [
                {
                    "file_path": test_file_name,  # 使用相对路径
                    "line_numbers": [1, 1],
                    "expected_content": "Goodbye World"
                }
            ],
            "source_root": self.test_dir
        }

        result = self.analyzer.analyze(config)
        verification_results = result["verification_results"]

        self.assertEqual(len(verification_results), 1)
        self.assertEqual(verification_results[0]["validation_status"], "inconsistent")
        self.assertIn("Content", verification_results[0]["validation_details"])

    def test_class_function_detection_real(self):
        """测试类和函数检测真实逻辑"""
        # 创建临时测试文件
        test_file_name = "test_module.py"
        test_file = os.path.join(self.test_dir, test_file_name)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("class TestClass:\n    def test_function(self):\n        pass\n")

        # 测试类查找
        class_found = self.analyzer._find_class_in_file(test_file, "TestClass")
        self.assertTrue(class_found)

        # 测试函数查找
        function_found = self.analyzer._find_function_in_file(test_file, "test_function")
        self.assertTrue(function_found)

        # 测试不存在的类
        class_not_found = self.analyzer._find_class_in_file(test_file, "NonExistentClass")
        self.assertFalse(class_not_found)

    def test_confidence_level_determination_real(self):
        """测试置信度等级确定"""
        self.assertEqual(self.analyzer._determine_confidence_level(0.95), "high")
        self.assertEqual(self.analyzer._determine_confidence_level(0.80), "medium")
        self.assertEqual(self.analyzer._determine_confidence_level(0.60), "low")

    def test_recommendation_generation_real(self):
        """测试改进建议生成真实逻辑"""
        component = {
            "id": "test_component",
            "references": [
                {
                    "file_path": "test/file.py",
                    "line_numbers": [1, 1],
                    "expected_content": "test"
                }
            ]
        }

        scores = {
            "completeness": 0.5,
            "accuracy": 0.5,
            "consistency": 0.5,
            "overall": 0.5
        }

        recommendations = self.analyzer._generate_recommendations_real(component, scores)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    def test_trustworthiness_calculation_real(self):
        """测试可信度计算真实逻辑"""
        component = {
            "id": "test_component",
            "references": [
                {
                    "file_path": "test/file.py",
                    "line_numbers": [1, 1],
                    "expected_content": "test",
                    "expected_class": "TestClass",
                    "expected_function": "test_function"
                }
            ]
        }

        criteria = ["completeness", "accuracy", "consistency"]
        scores = self.analyzer._calculate_trustworthiness_scores_real(component, criteria)

        self.assertIsInstance(scores, dict)
        self.assertIn("completeness", scores)
        self.assertIn("accuracy", scores)
        self.assertIn("consistency", scores)
        self.assertIn("overall", scores)
        self.assertIn("confidence_level", scores)

    def tearDown(self):
        """测试清理"""
        # 清理临时文件
        for filename in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, filename))
        os.rmdir(self.test_dir)


if __name__ == "__main__":
    unittest.main()