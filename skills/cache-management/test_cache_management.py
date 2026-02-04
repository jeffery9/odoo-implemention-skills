#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器Skill测试文件
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import main


def test_memory_cache_operations():
    """测试内存缓存操作"""
    print("测试内存缓存操作...")

    # 测试设置缓存
    config = {
        "operation": "set",
        "key": "test_key",
        "value": {"data": "test_value", "number": 42},
        "ttl": 60,
        "cache_type": "memory"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"设置缓存失败: {result}"
    print("✓ 设置缓存成功")

    # 测试获取缓存
    config = {
        "operation": "get",
        "key": "test_key",
        "cache_type": "memory"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"获取缓存失败: {result}"
    assert result["cache_data"]["value"]["data"] == "test_value", f"缓存值不匹配: {result}"
    print("✓ 获取缓存成功")

    # 测试删除缓存
    config = {
        "operation": "delete",
        "key": "test_key",
        "cache_type": "memory"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"删除缓存失败: {result}"
    print("✓ 删除缓存成功")

    # 测试获取已删除的缓存
    config = {
        "operation": "get",
        "key": "test_key",
        "cache_type": "memory"
    }

    result = main(config)
    assert result["metadata"]["status"] == "not_found", f"应该找不到已删除的缓存: {result}"
    print("✓ 缓存删除验证成功")


def test_file_cache_operations():
    """测试文件缓存操作"""
    print("测试文件缓存操作...")

    # 测试设置缓存
    config = {
        "operation": "set",
        "key": "file_test_key",
        "value": {"file_data": "test_content", "timestamp": "2025-01-01"},
        "ttl": 60,
        "cache_type": "file"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"设置文件缓存失败: {result}"
    print("✓ 设置文件缓存成功")

    # 测试获取缓存
    config = {
        "operation": "get",
        "key": "file_test_key",
        "cache_type": "file"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"获取文件缓存失败: {result}"
    assert result["cache_data"]["value"]["file_data"] == "test_content", f"文件缓存值不匹配: {result}"
    print("✓ 获取文件缓存成功")


def test_cache_stats():
    """测试缓存统计"""
    print("测试缓存统计...")

    # 清空缓存
    config = {
        "operation": "clear",
        "cache_type": "memory"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"清空缓存失败: {result}"

    # 获取统计信息
    config = {
        "operation": "stats",
        "cache_type": "memory"
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"获取统计信息失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    print("✓ 缓存统计测试成功")


def test_batch_operations():
    """测试批量操作"""
    print("测试批量操作...")

    # 批量操作
    config = {
        "operation": "batch",
        "actions": [
            {
                "operation": "set",
                "key": "batch_key_1",
                "value": "batch_value_1",
                "ttl": 60,
                "cache_type": "memory"
            },
            {
                "operation": "set",
                "key": "batch_key_2",
                "value": "batch_value_2",
                "ttl": 60,
                "cache_type": "memory"
            }
        ]
    }

    result = main(config)
    assert result["metadata"]["status"] == "success", f"批量操作失败: {result}"
    assert "results" in result, f"结果中缺少results字段: {result}"
    print("✓ 批量操作测试成功")


def test_error_handling():
    """测试错误处理"""
    print("测试错误处理...")

    # 测试缺少必需参数
    config = {
        "operation": "get"
        # 缺少key参数
    }

    result = main(config)
    assert result["metadata"]["status"] == "failed", f"应该返回错误: {result}"
    print("✓ 错误处理测试成功")


def run_all_tests():
    """运行所有测试"""
    print("开始运行缓存管理器测试...")
    print("=" * 50)

    try:
        test_memory_cache_operations()
        test_file_cache_operations()
        test_cache_stats()
        test_batch_operations()
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