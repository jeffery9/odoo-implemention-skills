#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主演化Skill测试文件
"""

import sys
import os
import json
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 本技能实现位于 scripts/，需显式加入导入路径，否则 pytest 收集阶段报 No module named 'main'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + os.sep + "scripts")

from main import main


def test_incremental_learning():
    """测试增量学习功能"""
    print("测试增量学习功能...")

    # 测试学习操作
    config = {
        "operation": "learn",
        "data": {"metric1": 0.85, "metric2": 0.75, "timestamp": time.time()},
        "model_id": "test_model_001",
        "strategy": "balanced"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"增量学习失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    print("✓ 增量学习功能测试成功")


def test_knowledge_extraction():
    """测试知识提取功能"""
    print("测试知识提取功能...")

    # 测试知识提取操作
    config = {
        "operation": "extract_knowledge",
        "data": [
            {"id": "cap_001", "name": "Cache Management", "complexity": 0.6, "importance": 0.8},
            {"id": "cap_002", "name": "Configuration Management", "complexity": 0.7, "importance": 0.9}
        ],
        "knowledge_type": "capability_patterns"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"知识提取失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    assert result["results"]["count"] >= 2, f"提取的知识项数量不正确: {result}"
    print("✓ 知识提取功能测试成功")


def test_model_optimization():
    """测试模型优化功能"""
    print("测试模型优化功能...")

    # 测试模型优化操作
    config = {
        "operation": "optimize_model",
        "model_data": {
            "performance_metrics": {
                "accuracy": 0.85,
                "latency": 0.25
            }
        },
        "optimization_goal": "performance"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"模型优化失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    assert result["results"]["optimized"] == True, f"模型未被优化: {result}"
    print("✓ 模型优化功能测试成功")


def test_intelligent_recommendations():
    """测试智能推荐功能"""
    print("测试智能推荐功能...")

    # 测试生成推荐操作
    config = {
        "operation": "generate_recommendations",
        "user_context": {
            "expertise_level": "intermediate",
            "preferences": ["performance", "reliability"]
        },
        "current_capabilities": [
            {"id": "cap_001", "name": "Cache Management", "complexity": 0.6, "importance": 0.8},
            {"id": "cap_002", "name": "Configuration Management", "complexity": 0.7, "importance": 0.9}
        ]
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"生成推荐失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    print("✓ 智能推荐功能测试成功")


def test_optimization_planning():
    """测试优化路径规划功能"""
    print("测试优化路径规划功能...")

    # 测试规划优化操作
    config = {
        "operation": "plan_optimization",
        "opportunity": {
            "type": "performance_improvement",
            "target_capability": "Cache Management"
        },
        "current_capabilities": [
            {"id": "cap_001", "name": "Cache Management", "complexity": 0.6, "importance": 0.8}
        ],
        "user_profile": {
            "experience_level": "intermediate",
            "available_time": "2 weeks"
        }
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"规划优化失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    assert "steps" in result["results"], f"结果中缺少步骤信息: {result}"
    print("✓ 优化路径规划功能测试成功")


def test_evolution_evaluation():
    """测试演化评估功能"""
    print("测试演化评估功能...")

    # 测试演化评估操作
    config = {
        "operation": "evaluate_evolution",
        "evaluation_data": {
            "metrics_history": [
                {"accuracy": 0.80, "timestamp": time.time() - 3600},
                {"accuracy": 0.85, "timestamp": time.time()}
            ]
        }
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"演化评估失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    print("✓ 演化评估功能测试成功")


def test_error_handling():
    """测试错误处理"""
    print("测试错误处理...")

    # 测试缺少必需参数
    config = {
        "operation": "learn"
        # 缺少data参数
    }

    result = main(config)
    assert result["metadata"]["status"] == "failed", f"应该返回错误: {result}"
    print("✓ 错误处理测试成功")


def test_capability_model_extraction():
    """测试能力模型提取功能"""
    print("测试能力模型提取功能...")

    # 测试能力模型提取操作
    config = {
        "operation": "extract_capability_model",
        "capability_data": {
            "id": "cap_001",
            "name": "Cache Management",
            "namespace": "infrastructure",
            "functionality": "提供缓存管理功能",
            "dependencies": ["file-operations"],
            "performance_metrics": {
                "response_time": "0.1s",
                "throughput": "1000 req/s"
            }
        }
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"能力模型提取失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    assert "capability_model" in result["results"], f"结果中缺少能力模型: {result}"
    print("✓ 能力模型提取功能测试成功")


def test_capability_relationships_analysis():
    """测试能力关系分析功能"""
    print("测试能力关系分析功能...")

    # 测试能力关系分析操作
    config = {
        "operation": "analyze_capability_relationships",
        "capabilities": [
            {
                "id": "cap_001",
                "name": "Cache Management",
                "dependencies": ["file-operations"],
                "collaborators": ["configuration-management"]
            },
            {
                "id": "cap_002",
                "name": "Configuration Management",
                "dependencies": ["file-operations"],
                "collaborators": ["cache-management"]
            }
        ]
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"能力关系分析失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    assert "total_relationships" in result["results"], f"结果中缺少关系统计: {result}"
    print("✓ 能力关系分析功能测试成功")


def run_all_tests():
    """运行所有测试"""
    print("开始运行自主演化Skill测试...")
    print("=" * 50)

    try:
        test_incremental_learning()
        test_knowledge_extraction()
        test_model_optimization()
        test_intelligent_recommendations()
        test_optimization_planning()
        test_evolution_evaluation()
        test_error_handling()
        test_capability_model_extraction()
        test_capability_relationships_analysis()

        print("=" * 50)
        print("所有测试通过! ✓")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)