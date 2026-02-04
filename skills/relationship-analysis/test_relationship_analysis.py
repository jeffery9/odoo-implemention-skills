#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relationship Analysis Skill 测试文件
"""

import unittest
import json
import os
import tempfile
from main import RelationshipAnalyzer


class TestRelationshipAnalyzer(unittest.TestCase):

    def setUp(self):
        """测试设置"""
        self.analyzer = RelationshipAnalyzer()

    def test_supported_analysis_types(self):
        """测试支持的分析类型"""
        expected_types = [
            "dependency_analysis",
            "relationship_mapping",
            "network_analysis",
            "hierarchy_mapping"
        ]
        self.assertEqual(self.analyzer.supported_analysis_types, expected_types)

    def test_dependency_analysis_with_real_logic(self):
        """测试依赖分析真实逻辑"""
        config = {
            "analysis_type": "dependency_analysis",
            "scope": "base",  # 使用一个真实存在的模块名
            "direction": "unidirectional"
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("dependencies", result)
        self.assertIn("importance_scores", result)
        self.assertIn("network", result)

        # 验证元数据
        metadata = result["metadata"]
        self.assertEqual(metadata["skill_name"], "relationship-analysis")
        self.assertEqual(metadata["analysis_type"], "dependency_analysis")

        # 验证依赖关系结构
        dependencies = result["dependencies"]
        self.assertIsInstance(dependencies, list)

        # 验证网络结构
        network = result["network"]
        self.assertIn("nodes", network)
        self.assertIn("edges", network)
        self.assertIsInstance(network["nodes"], list)
        self.assertIsInstance(network["edges"], list)

    def test_network_analysis_with_real_logic(self):
        """测试网络分析真实逻辑"""
        config = {
            "analysis_type": "network_analysis",
            "scope": ["base", "web"],  # 使用真实模块名
            "metrics": ["centrality"]
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("relationships", result)
        self.assertIn("network_metrics", result)

        # 验证网络指标
        network_metrics = result["network_metrics"]
        self.assertIn("nodes_count", network_metrics)
        self.assertIn("edges_count", network_metrics)
        self.assertIn("centrality_scores", network_metrics)
        self.assertIn("key_nodes", network_metrics)

        # 验证中心性计算结果
        centrality_scores = network_metrics["centrality_scores"]
        self.assertIsInstance(centrality_scores, dict)

    def test_relationship_mapping_with_real_logic(self):
        """测试关系映射真实逻辑"""
        config = {
            "analysis_type": "relationship_mapping",
            "scope": ["base", "web"]
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("relationships", result)
        self.assertIsInstance(result["relationships"], list)

    def test_hierarchy_mapping_with_real_logic(self):
        """测试层次映射真实逻辑"""
        config = {
            "analysis_type": "hierarchy_mapping",
            "scope": "base"
        }

        result = self.analyzer.analyze(config)

        # 验证返回结果结构
        self.assertIn("metadata", result)
        self.assertIn("hierarchy", result)
        hierarchy = result["hierarchy"]
        self.assertIn("root", hierarchy)
        self.assertIn("levels", hierarchy)
        self.assertIsInstance(hierarchy["levels"], list)

    def test_invalid_analysis_type(self):
        """测试无效分析类型"""
        config = {
            "analysis_type": "invalid_type",
            "scope": "base"
        }

        with self.assertRaises(ValueError):
            self.analyzer.analyze(config)

    def test_dependency_calculation_real(self):
        """测试真实依赖计算"""
        # 模拟依赖数据
        dependencies = [{"module": "base"}, {"module": "web"}]
        reverse_dependencies = [{"module": "project"}]

        importance_scores = self.analyzer._calculate_dependency_importance(dependencies, reverse_dependencies)
        self.assertIsInstance(importance_scores, dict)
        # 验证所有模块都有得分
        for dep in dependencies:
            self.assertIn(dep["module"], importance_scores)
        for dep in reverse_dependencies:
            self.assertIn(dep["module"], importance_scores)

    def test_network_building_real(self):
        """测试真实网络构建"""
        dependencies = [{"module": "base", "type": "technical"}]
        reverse_dependencies = [{"module": "project", "dependency_type": "extension"}]

        network = self.analyzer._build_dependency_network(dependencies, reverse_dependencies)
        self.assertIn("nodes", network)
        self.assertIn("edges", network)
        self.assertGreater(len(network["nodes"]), 0)
        self.assertGreater(len(network["edges"]), 0)

        # 验证节点包含目标模块和依赖模块
        nodes = set(network["nodes"])
        self.assertIn("target_module", nodes)
        self.assertIn("base", nodes)
        self.assertIn("project", nodes)

    def test_centrality_calculation_real(self):
        """测试真实中心性计算"""
        graph = {
            "nodes": ["node1", "node2", "node3"],
            "edges": [
                {"source": "node1", "target": "node2", "weight": 1.0},
                {"source": "node2", "target": "node3", "weight": 1.0}
            ]
        }

        centrality = self.analyzer._calculate_centrality_real(graph)
        self.assertIsInstance(centrality, dict)
        for node in graph["nodes"]:
            self.assertIn(node, centrality)
            self.assertIsInstance(centrality[node], float)
            self.assertGreaterEqual(centrality[node], 0.0)
            self.assertLessEqual(centrality[node], 1.0)

    def test_key_node_identification_real(self):
        """测试真实关键节点识别"""
        centrality = {"node1": 0.8, "node2": 0.4, "node3": 0.9, "node4": 0.2}
        key_nodes = self.analyzer._identify_key_nodes_real(centrality)
        self.assertIsInstance(key_nodes, list)
        # 验证返回了节点
        self.assertGreater(len(key_nodes), 0)

    def test_module_dependencies_real(self):
        """测试真实模块依赖获取"""
        # 测试不存在的模块应该返回空列表而不是报错
        dependencies = self.analyzer._get_module_dependencies("nonexistent_module")
        self.assertIsInstance(dependencies, list)

    def test_module_hierarchy_real(self):
        """测试真实模块层次结构获取"""
        # 测试单个模块
        hierarchy = self.analyzer._get_module_hierarchy("base")
        self.assertIsInstance(hierarchy, dict)
        self.assertIn("root", hierarchy)
        self.assertIn("levels", hierarchy)
        self.assertIsInstance(hierarchy["levels"], list)

        # 测试多个模块
        hierarchy = self.analyzer._get_module_hierarchy(["base", "web"])
        self.assertIsInstance(hierarchy, dict)
        self.assertIn("levels", hierarchy)
        self.assertGreater(len(hierarchy["levels"]), 0)


if __name__ == "__main__":
    unittest.main()