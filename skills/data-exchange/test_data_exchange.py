#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Exchange Skill 测试文件
"""

import unittest
import json
import os
import tempfile
import csv
import yaml
from main import DataExchange


class TestDataExchange(unittest.TestCase):

    def setUp(self):
        """测试设置"""
        self.processor = DataExchange()
        self.test_dir = tempfile.mkdtemp()

    def test_supported_operations(self):
        """测试支持的操作类型"""
        expected_operations = [
            "import", "export", "convert", "validate"
        ]
        self.assertEqual(self.processor.supported_operations, expected_operations)

    def test_supported_formats(self):
        """测试支持的数据格式"""
        expected_formats = [
            "json", "xml", "csv", "yaml"
        ]
        self.assertEqual(self.processor.supported_formats, expected_formats)

    def test_json_import(self):
        """测试JSON数据导入"""
        # 创建测试JSON文件
        test_data = {"name": "test", "value": 123}
        json_path = os.path.join(self.test_dir, "test.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)

        config = {
            "operation": "import",
            "source_path": json_path
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("data_info", result)
        self.assertIn("parsed_data", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "data-exchange")
        self.assertEqual(metadata["operation"], "import")
        self.assertEqual(metadata["status"], "success")

        # 验证解析的数据
        parsed_data = result["parsed_data"]
        self.assertEqual(parsed_data, test_data)

    def test_csv_import(self):
        """测试CSV数据导入"""
        # 创建测试CSV文件
        csv_data = [
            ["name", "value"],
            ["test1", "123"],
            ["test2", "456"]
        ]
        csv_path = os.path.join(self.test_dir, "test.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        config = {
            "operation": "import",
            "source_path": csv_path
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("data_info", result)
        self.assertIn("parsed_data", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "data-exchange")
        self.assertEqual(metadata["operation"], "import")
        self.assertEqual(metadata["status"], "success")

        # 验证解析的数据
        parsed_data = result["parsed_data"]
        self.assertIsInstance(parsed_data, list)
        self.assertEqual(len(parsed_data), 2)
        self.assertEqual(parsed_data[0]["name"], "test1")
        self.assertEqual(parsed_data[0]["value"], "123")

    def test_data_export_json(self):
        """测试JSON数据导出"""
        test_data = {"name": "test", "value": 123}
        output_path = os.path.join(self.test_dir, "output.json")

        config = {
            "operation": "export",
            "data": test_data,
            "target_path": output_path,
            "export_format": "json"
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("data_info", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "data-exchange")
        self.assertEqual(metadata["operation"], "export")
        self.assertEqual(metadata["status"], "success")

        # 验证导出的文件
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        self.assertEqual(exported_data, test_data)

    def test_data_conversion(self):
        """测试数据转换"""
        # 创建测试JSON文件
        test_data = {"name": "test", "value": 123}
        json_path = os.path.join(self.test_dir, "test_convert.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)

        output_path = os.path.join(self.test_dir, "converted.csv")

        config = {
            "operation": "convert",
            "source_path": json_path,
            "target_format": "csv",
            "output_path": output_path
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("data_info", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "data-exchange")
        self.assertEqual(metadata["operation"], "convert")
        self.assertEqual(metadata["status"], "success")

        # 验证转换后的文件
        self.assertTrue(os.path.exists(output_path))

    def test_data_validation(self):
        """测试数据验证"""
        test_data = {"name": "test", "value": 123}
        validation_rules = {
            "required_fields": ["name", "value"],
            "field_types": {
                "value": "integer"
            }
        }

        config = {
            "operation": "validate",
            "data": test_data,
            "validation_rules": validation_rules
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("data_info", result)
        self.assertIn("validation_details", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "data-exchange")
        self.assertEqual(metadata["operation"], "validate")
        self.assertEqual(metadata["status"], "success")

        # 验证验证结果
        validation_details = result["validation_details"]
        self.assertTrue(validation_details["is_valid"])
        self.assertEqual(len(validation_details["errors"]), 0)

    def test_invalid_operation(self):
        """测试无效操作"""
        config = {
            "operation": "invalid_operation"
        }

        with self.assertRaises(ValueError):
            self.processor.execute(config)

    def test_missing_required_parameters(self):
        """测试缺少必需参数"""
        # 测试导入操作缺少必需参数
        config = {
            "operation": "import"
            # 缺少 source_path
        }

        with self.assertRaises(ValueError):
            self.processor.execute(config)

        # 测试导出操作缺少必需参数
        config = {
            "operation": "export"
            # 缺少 data 和 target_path
        }

        with self.assertRaises(ValueError):
            self.processor.execute(config)

    def test_format_detection(self):
        """测试格式检测"""
        # 测试JSON格式检测
        json_path = os.path.join(self.test_dir, "test_detect.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write('{"test": "data"}')

        detected_format = self.processor._detect_format(json_path)
        self.assertEqual(detected_format, "json")

        # 测试CSV格式检测
        csv_path = os.path.join(self.test_dir, "test_detect.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('name,value\ntest,123')

        detected_format = self.processor._detect_format(csv_path)
        self.assertEqual(detected_format, "csv")


if __name__ == "__main__":
    unittest.main()