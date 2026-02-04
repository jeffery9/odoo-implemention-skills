#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作Skill测试文件
"""

import sys
import os
import json
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import main


def test_file_read_write():
    """测试文件读写操作"""
    print("测试文件读写操作...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test.txt")

    try:
        # 测试写入文件
        config = {
            "operation": "write",
            "file_path": test_file,
            "content": "Hello, World!\nThis is a test file.",
            "encoding": "utf-8"
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"写入文件失败: {result}"
        print("✓ 写入文件成功")

        # 测试读取文件
        config = {
            "operation": "read",
            "file_path": test_file,
            "encoding": "utf-8"
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"读取文件失败: {result}"
        assert "Hello, World!" in result["file_data"]["content"], f"文件内容不匹配: {result}"
        print("✓ 读取文件成功")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_file_copy_move():
    """测试文件复制移动操作"""
    print("测试文件复制移动操作...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    source_file = os.path.join(temp_dir, "source.txt")
    dest_file = os.path.join(temp_dir, "dest.txt")
    moved_file = os.path.join(temp_dir, "moved.txt")

    try:
        # 创建源文件
        with open(source_file, 'w') as f:
            f.write("Test content for copy/move")

        # 测试复制文件
        config = {
            "operation": "copy",
            "source_path": source_file,
            "destination_path": dest_file
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"复制文件失败: {result}"
        assert os.path.exists(dest_file), "复制的文件不存在"
        print("✓ 复制文件成功")

        # 测试移动文件
        config = {
            "operation": "move",
            "source_path": source_file,
            "destination_path": moved_file
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"移动文件失败: {result}"
        assert not os.path.exists(source_file), "源文件未被删除"
        assert os.path.exists(moved_file), "移动的文件不存在"
        print("✓ 移动文件成功")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_file_delete():
    """测试文件删除操作"""
    print("测试文件删除操作...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test_delete.txt")

    try:
        # 创建测试文件
        with open(test_file, 'w') as f:
            f.write("Test content for deletion")

        # 测试删除文件
        config = {
            "operation": "delete",
            "file_path": test_file
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"删除文件失败: {result}"
        assert not os.path.exists(test_file), "文件未被删除"
        print("✓ 删除文件成功")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_file_info():
    """测试文件信息查询操作"""
    print("测试文件信息查询操作...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test_info.txt")

    try:
        # 创建测试文件
        with open(test_file, 'w') as f:
            f.write("Test content for info")

        # 测试获取文件信息
        config = {
            "operation": "info",
            "file_path": test_file
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"获取文件信息失败: {result}"
        assert "file_data" in result, f"结果中缺少file_data字段: {result}"
        assert result["file_data"]["size"] > 0, f"文件大小不正确: {result}"
        print("✓ 获取文件信息成功")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_directory_operations():
    """测试目录操作"""
    print("测试目录操作...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    test_dir = os.path.join(temp_dir, "test_dir")
    sub_dir = os.path.join(test_dir, "sub_dir")

    try:
        # 测试创建目录
        config = {
            "operation": "mkdir",
            "directory_path": test_dir
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"创建目录失败: {result}"
        assert os.path.exists(test_dir), "目录未创建"
        print("✓ 创建目录成功")

        # 测试递归创建目录
        config = {
            "operation": "mkdir",
            "directory_path": sub_dir,
            "parents": True
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"递归创建目录失败: {result}"
        assert os.path.exists(sub_dir), "递归目录未创建"
        print("✓ 递归创建目录成功")

        # 测试列出目录内容
        config = {
            "operation": "list",
            "directory_path": test_dir
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"列出目录内容失败: {result}"
        assert "results" in result, f"结果中缺少results字段: {result}"
        print("✓ 列出目录内容成功")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_file_search():
    """测试文件搜索操作"""
    print("测试文件搜索操作...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    test_file1 = os.path.join(temp_dir, "search_test1.txt")
    test_file2 = os.path.join(temp_dir, "search_test2.txt")
    test_file3 = os.path.join(temp_dir, "other_file.txt")

    try:
        # 创建测试文件
        for file_path in [test_file1, test_file2, test_file3]:
            with open(file_path, 'w') as f:
                f.write(f"Content of {os.path.basename(file_path)}")

        # 测试搜索文件
        config = {
            "operation": "search",
            "directory_path": temp_dir,
            "pattern": "*test*.txt"
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"搜索文件失败: {result}"
        assert "results" in result, f"结果中缺少results字段: {result}"
        assert result["results"]["count"] >= 2, f"搜索结果数量不正确: {result}"
        print("✓ 搜索文件成功")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_backup_restore():
    """测试备份恢复操作"""
    print("测试备份恢复操作...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test_backup.txt")
    backup_file = os.path.join(temp_dir, "backup.txt")

    try:
        # 创建测试文件
        with open(test_file, 'w') as f:
            f.write("Original content")

        # 测试备份文件
        config = {
            "operation": "backup",
            "file_path": test_file,
            "backup_path": backup_file
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"备份文件失败: {result}"
        assert os.path.exists(backup_file), "备份文件未创建"
        print("✓ 备份文件成功")

        # 修改原文件
        with open(test_file, 'w') as f:
            f.write("Modified content")

        # 测试恢复文件
        config = {
            "operation": "restore",
            "backup_path": backup_file,
            "restore_path": test_file
        }

        result = main(config)
        assert result["metadata"]["status"] == "success", f"恢复文件失败: {result}"

        # 验证恢复的内容
        with open(test_file, 'r') as f:
            content = f.read()
        assert content == "Original content", f"恢复的内容不正确: {content}"
        print("✓ 恢复文件成功")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_error_handling():
    """测试错误处理"""
    print("测试错误处理...")

    # 测试读取不存在的文件
    config = {
        "operation": "read",
        "file_path": "/nonexistent/file.txt"
    }

    result = main(config)
    assert result["metadata"]["status"] == "failed", f"应该返回错误: {result}"
    print("✓ 错误处理测试成功")


def run_all_tests():
    """运行所有测试"""
    print("开始运行文件操作Skill测试...")
    print("=" * 50)

    try:
        test_file_read_write()
        test_file_copy_move()
        test_file_delete()
        test_file_info()
        test_directory_operations()
        test_file_search()
        test_backup_restore()
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