#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器Skill测试文件
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import main


def test_basic_config_operations():
    """测试基本配置操作"""
    print("测试基本配置操作...")

    # 测试设置配置
    config = {
        "operation": "set",
        "config_type": "skill",
        "config_id": "test-skill",
        "config_data": {
            "timeout": 30,
            "retries": 3,
            "cache_enabled": True
        }
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"设置配置失败: {result}"
    print("✓ 设置配置成功")

    # 测试获取配置
    config = {
        "operation": "get",
        "config_type": "skill",
        "config_id": "test-skill"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"获取配置失败: {result}"
    assert result["config_data"]["data"]["timeout"] == 30, f"配置值不匹配: {result}"
    print("✓ 获取配置成功")

    # 测试更新配置
    config = {
        "operation": "update",
        "config_type": "skill",
        "config_id": "test-skill",
        "config_data": {
            "timeout": 60  # 只更新timeout，其他保持不变
        }
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"更新配置失败: {result}"
    assert result["config_data"]["data"]["timeout"] == 60, f"更新后的配置值不匹配: {result}"
    assert result["config_data"]["data"]["retries"] == 3, f"未更新的配置值丢失: {result}"
    print("✓ 更新配置成功")


def test_config_validation():
    """测试配置验证"""
    print("测试配置验证...")

    # 设置一个技能配置
    config = {
        "operation": "set",
        "config_type": "skill",
        "config_id": "validation-test",
        "config_data": {
            "timeout": 30,
            "cache_enabled": True
        }
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"设置配置失败: {result}"

    # 验证配置
    config = {
        "operation": "validate",
        "config_type": "skill",
        "config_id": "validation-test"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"验证配置失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    print("✓ 配置验证成功")


def test_config_history():
    """测试配置历史"""
    print("测试配置历史...")

    # 设置配置
    config = {
        "operation": "set",
        "config_type": "project",
        "config_id": "history-test",
        "config_data": {"version": "1.0"}
    }

    result = main(config)

    # 更新配置
    config = {
        "operation": "update",
        "config_type": "project",
        "config_id": "history-test",
        "config_data": {"version": "1.1"}
    }

    result = main(config)

    # 获取历史记录
    config = {
        "operation": "history",
        "config_type": "project",
        "config_id": "history-test"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"获取历史失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    assert len(result["results"]["history"]) >= 2, f"历史记录数量不足: {result}"
    print("✓ 配置历史测试成功")


def test_config_deletion():
    """测试配置删除"""
    print("测试配置删除...")

    # 设置配置
    config = {
        "operation": "set",
        "config_type": "test",
        "config_id": "delete-test",
        "config_data": {"test": "data"}
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"设置配置失败: {result}"

    # 删除配置
    config = {
        "operation": "delete",
        "config_type": "test",
        "config_id": "delete-test"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"删除配置失败: {result}"

    # 尝试获取已删除的配置
    config = {
        "operation": "get",
        "config_type": "test",
        "config_id": "delete-test"
    }

    result = main(config)
    assert result["metadata"]["status"] == "not_found", f"应该找不到已删除的配置: {result}"
    print("✓ 配置删除测试成功")


def test_error_handling():
    """测试错误处理"""
    print("测试错误处理...")

    # 测试缺少必需参数
    config = {
        "operation": "get"
        # 缺少config_type和config_id
    }

    result = main(config)
    assert result["metadata"]["status"] == "failed", f"应该返回错误: {result}"
    print("✓ 错误处理测试成功")


def run_all_tests():
    """运行所有测试"""
    print("开始运行配置管理器测试...")
    print("=" * 50)

    try:
        test_basic_config_operations()
        test_config_validation()
        test_config_history()
        test_config_deletion()
        test_error_handling()

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