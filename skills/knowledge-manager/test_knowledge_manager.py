#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Manager Skill 测试文件
"""

import unittest
import json
import os
import tempfile
import time
from main import KnowledgeManager


class TestKnowledgeManager(unittest.TestCase):

    def setUp(self):
        """测试设置"""
        self.manager = KnowledgeManager()

    def test_supported_operations(self):
        """测试支持的操作类型"""
        expected_operations = [
            "store", "retrieve", "update", "delete",
            "cache_management", "lifecycle_management"
        ]
        self.assertEqual(self.manager.supported_operations, expected_operations)

    def test_knowledge_storage(self):
        """测试知识存储"""
        config = {
            "operation": "store",
            "knowledge_key": "test_analysis",
            "knowledge_data": {"result": "test data", "score": 0.95},
            "ttl": 3600,
            "tags": ["test", "analysis"]
        }

        result = self.manager.execute(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("knowledge_items", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "knowledge-manager")
        self.assertEqual(metadata["operation"], "store")
        self.assertEqual(metadata["status"], "success")

        # 验证结果
        results = result["results"]
        self.assertIn("operation_result", results)
        self.assertIn("knowledge_id", results)
        self.assertEqual(results["affected_items"], 1)

        # 验证知识条目
        knowledge_items = result["knowledge_items"]
        self.assertEqual(len(knowledge_items), 1)
        self.assertEqual(knowledge_items[0]["key"], "test_analysis")
        self.assertEqual(knowledge_items[0]["data"], config["knowledge_data"])

    def test_knowledge_retrieval(self):
        """测试知识检索"""
        # 先存储一些知识
        store_config = {
            "operation": "store",
            "knowledge_key": "retrieval_test",
            "knowledge_data": {"test": "retrieval data"},
            "tags": ["retrieval", "test"]
        }
        self.manager.execute(store_config)

        # 然后检索
        retrieve_config = {
            "operation": "retrieve",
            "search_query": "retrieval test",
            "tags": ["retrieval"],
            "max_results": 5
        }

        result = self.manager.execute(retrieve_config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("knowledge_items", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "knowledge-manager")
        self.assertEqual(metadata["operation"], "retrieve")
        self.assertEqual(metadata["status"], "success")

        # 验证检索结果
        knowledge_items = result["knowledge_items"]
        self.assertGreater(len(knowledge_items), 0)
        self.assertEqual(knowledge_items[0]["key"], "retrieval_test")

    def test_knowledge_update(self):
        """测试知识更新"""
        # 先存储知识
        store_config = {
            "operation": "store",
            "knowledge_key": "update_test",
            "knowledge_data": {"version": 1, "data": "original"},
            "tags": ["update", "test"]
        }
        store_result = self.manager.execute(store_config)

        # 更新知识
        update_config = {
            "operation": "update",
            "knowledge_key": "update_test",
            "knowledge_data": {"version": 2, "data": "updated"},
            "tags": ["modified"]
        }

        result = self.manager.execute(update_config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)
        self.assertIn("knowledge_items", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "knowledge-manager")
        self.assertEqual(metadata["operation"], "update")
        self.assertEqual(metadata["status"], "success")

        # 验证更新结果
        results = result["results"]
        self.assertEqual(results["affected_items"], 1)

    def test_knowledge_deletion(self):
        """测试知识删除"""
        # 先存储知识
        store_config = {
            "operation": "store",
            "knowledge_key": "delete_test",
            "knowledge_data": {"data": "to be deleted"},
            "tags": ["delete", "test"]
        }
        self.manager.execute(store_config)

        # 删除知识
        delete_config = {
            "operation": "delete",
            "knowledge_key": "delete_test"
        }

        result = self.manager.execute(delete_config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "knowledge-manager")
        self.assertEqual(metadata["operation"], "delete")
        self.assertEqual(metadata["status"], "success")

        # 验证删除结果
        results = result["results"]
        self.assertEqual(results["affected_items"], 1)

    def test_cache_management(self):
        """测试缓存管理"""
        # 存储一些知识用于测试
        for i in range(3):
            config = {
                "operation": "store",
                "knowledge_key": f"cache_test_{i}",
                "knowledge_data": {"test": f"data_{i}"},
                "ttl": 3600
            }
            self.manager.execute(config)

        # 测试缓存统计
        stats_config = {
            "operation": "cache_management",
            "action": "stats"
        }

        result = self.manager.execute(stats_config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("results", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "knowledge-manager")
        self.assertEqual(metadata["operation"], "cache_management")
        self.assertEqual(metadata["status"], "success")

        # 验证统计结果
        results = result["results"]
        self.assertIn("cache_stats", results)
        cache_stats = results["cache_stats"]
        self.assertIn("total_items", cache_stats)
        self.assertGreaterEqual(cache_stats["total_items"], 3)

    def test_invalid_operation(self):
        """测试无效操作"""
        config = {
            "operation": "invalid_operation",
            "knowledge_key": "test"
        }

        with self.assertRaises(ValueError):
            self.manager.execute(config)

    def test_missing_required_parameters(self):
        """测试缺少必需参数"""
        # 测试存储操作缺少必需参数
        config = {
            "operation": "store"
            # 缺少 knowledge_key 和 knowledge_data
        }

        with self.assertRaises(ValueError):
            self.manager.execute(config)

    def test_knowledge_id_generation(self):
        """测试知识ID生成"""
        knowledge_key = "test_key"
        params = {"param1": "value1", "param2": "value2"}

        knowledge_id1 = self.manager._generate_knowledge_id(knowledge_key, params)
        knowledge_id2 = self.manager._generate_knowledge_id(knowledge_key, params)

        # 相同输入应该生成相同的ID
        self.assertEqual(knowledge_id1, knowledge_id2)

        # 不同输入应该生成不同的ID
        params2 = {"param1": "value1", "param2": "value3"}
        knowledge_id3 = self.manager._generate_knowledge_id(knowledge_key, params2)
        self.assertNotEqual(knowledge_id1, knowledge_id3)

    def test_data_serialization(self):
        """测试数据序列化和反序列化"""
        test_data = {
            "string": "test",
            "number": 42,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }

        serialized = self.manager._serialize_knowledge(test_data)
        deserialized = self.manager._deserialize_knowledge(serialized)

        self.assertEqual(test_data, deserialized)

    def test_data_hash_calculation(self):
        """测试数据摘要计算"""
        data1 = "test data"
        data2 = "test data"
        data3 = "different data"

        hash1 = self.manager._calculate_data_hash(data1)
        hash2 = self.manager._calculate_data_hash(data2)
        hash3 = self.manager._calculate_data_hash(data3)

        # 相同数据应该有相同哈希
        self.assertEqual(hash1, hash2)
        # 不同数据应该有不同哈希
        self.assertNotEqual(hash1, hash3)

    def test_search_query_parsing(self):
        """测试搜索查询解析"""
        query = "project management analysis"
        parsed = self.manager._parse_search_query(query)

        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 3)
        self.assertIn("project", parsed)
        self.assertIn("management", parsed)
        self.assertIn("analysis", parsed)

    def test_cache_cleanup(self):
        """测试缓存清理"""
        # 存储一些知识
        for i in range(5):
            config = {
                "operation": "store",
                "knowledge_key": f"cleanup_test_{i}",
                "knowledge_data": {"test": f"data_{i}"},
                "ttl": 3600
            }
            self.manager.execute(config)

        # 执行LRU清理
        cleanup_config = {
            "operation": "cache_management",
            "action": "cleanup",
            "strategy": "lru",
            "cleanup_count": 2
        }

        result = self.manager.execute(cleanup_config)

        # 验证清理结果
        results = result["results"]
        self.assertIn("cache_management_result", results)
        cleanup_result = results["cache_management_result"]
        self.assertEqual(cleanup_result["action"], "cleanup")
        self.assertEqual(cleanup_result["strategy"], "lru")


if __name__ == "__main__":
    unittest.main()