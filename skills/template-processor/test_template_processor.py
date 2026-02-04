#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template Processor Skill 测试文件
"""

import unittest
import json
import os
import tempfile
import time
from main import TemplateProcessor


class TestTemplateProcessor(unittest.TestCase):

    def setUp(self):
        """测试设置"""
        self.processor = TemplateProcessor()
        self.test_dir = tempfile.mkdtemp()

    def test_supported_operations(self):
        """测试支持的操作类型"""
        expected_operations = [
            "render", "validate", "convert", "manage"
        ]
        self.assertEqual(self.processor.supported_operations, expected_operations)

    def test_template_rendering_jinja2(self):
        """测试Jinja2模板渲染"""
        # 创建测试模板
        template_content = "Hello {{name}}!"
        template_path = os.path.join(self.test_dir, "test.jinja2")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        config = {
            "operation": "render",
            "template_path": template_path,
            "context_data": {"name": "World"},
            "template_engine": "jinja2"
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("template_data", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "template-processor")
        self.assertEqual(metadata["operation"], "render")
        self.assertEqual(metadata["status"], "success")

        # 验证结果
        template_data = result["template_data"]
        self.assertEqual(template_data["rendered_content"], "Hello World!")

    def test_template_validation(self):
        """测试模板验证"""
        # 创建测试模板
        template_content = "Hello {{name}}!"
        template_path = os.path.join(self.test_dir, "test_validate.jinja2")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        config = {
            "operation": "validate",
            "template_path": template_path,
            "template_engine": "jinja2"
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("template_data", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "template-processor")
        self.assertEqual(metadata["operation"], "validate")
        self.assertEqual(metadata["status"], "success")

        # 验证验证结果
        results = result["results"]
        validation_result = results["validation_result"]
        self.assertTrue(validation_result["is_valid"])

    def test_template_conversion(self):
        """测试模板转换"""
        # 创建测试模板
        template_content = "Hello {{name}}!"
        template_path = os.path.join(self.test_dir, "test_convert.jinja2")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        config = {
            "operation": "convert",
            "source_template_path": template_path,
            "target_format": "mustache"
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("template_data", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "template-processor")
        self.assertEqual(metadata["operation"], "convert")
        self.assertEqual(metadata["status"], "success")

        # 验证转换结果
        template_data = result["template_data"]
        self.assertIn("converted_content", template_data)

    def test_template_management(self):
        """测试模板管理"""
        config = {
            "operation": "manage",
            "action": "list"
        }

        result = self.processor.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("template_data", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "template-processor")
        self.assertEqual(metadata["operation"], "manage")
        self.assertEqual(metadata["status"], "success")

    def test_invalid_operation(self):
        """测试无效操作"""
        config = {
            "operation": "invalid_operation"
        }

        with self.assertRaises(ValueError):
            self.processor.execute(config)

    def test_missing_required_parameters(self):
        """测试缺少必需参数"""
        # 测试渲染操作缺少必需参数
        config = {
            "operation": "render"
            # 缺少 template_path
        }

        with self.assertRaises(ValueError):
            self.processor.execute(config)

    def test_template_caching(self):
        """测试模板缓存"""
        # 创建测试模板
        template_content = "Hello {{name}}!"
        template_path = os.path.join(self.test_dir, "test_cache.jinja2")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        config = {
            "operation": "render",
            "template_path": template_path,
            "context_data": {"name": "World"},
            "template_engine": "jinja2",
            "cache_enabled": True
        }

        result = self.processor.execute(config)

        # 验证缓存键存在
        template_data = result["template_data"]
        self.assertIn("cache_key", template_data)
        self.assertIsNotNone(template_data["cache_key"])

    def test_template_engine_selection(self):
        """测试模板引擎选择"""
        # 测试Jinja2引擎
        jinja2_engine = self.processor._get_template_engine("jinja2")
        self.assertIsNotNone(jinja2_engine)

        # 测试Mustache引擎
        mustache_engine = self.processor._get_template_engine("mustache")
        self.assertIsNotNone(mustache_engine)

        # 测试Handlebars引擎
        handlebars_engine = self.processor._get_template_engine("handlebars")
        self.assertIsNotNone(handlebars_engine)

        # 测试不支持的引擎
        with self.assertRaises(ValueError):
            self.processor._get_template_engine("unsupported_engine")


if __name__ == "__main__":
    unittest.main()