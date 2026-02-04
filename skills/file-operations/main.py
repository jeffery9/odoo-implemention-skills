#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作Skill主执行文件
"""

import json
import time
import os
import shutil
import glob
from typing import Any, Dict, Optional, List
from pathlib import Path


class FileManager:
    """文件管理器主类"""

    def __init__(self):
        pass

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作"""
        start_time = time.time()

        operation = config.get('operation', 'read')
        file_path = config.get('file_path', '')

        try:
            if operation == 'read':
                return self._handle_read(config, start_time)
            elif operation == 'write':
                return self._handle_write(config, start_time)
            elif operation == 'copy':
                return self._handle_copy(config, start_time)
            elif operation == 'move':
                return self._handle_move(config, start_time)
            elif operation == 'delete':
                return self._handle_delete(config, start_time)
            elif operation == 'info':
                return self._handle_info(config, start_time)
            elif operation == 'list':
                return self._handle_list(config, start_time)
            elif operation == 'mkdir':
                return self._handle_mkdir(config, start_time)
            elif operation == 'search':
                return self._handle_search(config, start_time)
            elif operation == 'backup':
                return self._handle_backup(config, start_time)
            elif operation == 'restore':
                return self._handle_restore(config, start_time)
            else:
                return {
                    "metadata": {
                        "skill_name": "file-operations",
                        "operation": operation,
                        "execution_time": time.time() - start_time,
                        "status": "failed"
                    },
                    "error": f"Unsupported operation: {operation}"
                }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": operation,
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": str(e)
            }

    def _handle_read(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理读取操作"""
        file_path = config.get('file_path')
        encoding = config.get('encoding', 'utf-8')

        if not file_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "read",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "File path is required for read operation"
            }

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            file_stats = os.stat(file_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "read",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "file_path": file_path,
                    "content": content,
                    "size": file_stats.st_size,
                    "modified_time": time.ctime(file_stats.st_mtime)
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "read",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to read file: {str(e)}"
            }

    def _handle_write(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理写入操作"""
        file_path = config.get('file_path')
        content = config.get('content', '')
        encoding = config.get('encoding', 'utf-8')

        if not file_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "write",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "File path is required for write operation"
            }

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)

            file_stats = os.stat(file_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "write",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "file_path": file_path,
                    "size": file_stats.st_size,
                    "modified_time": time.ctime(file_stats.st_mtime)
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "write",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to write file: {str(e)}"
            }

    def _handle_copy(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理复制操作"""
        source_path = config.get('source_path')
        destination_path = config.get('destination_path')
        recursive = config.get('recursive', False)

        if not source_path or not destination_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "copy",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "Source and destination paths are required for copy operation"
            }

        try:
            if os.path.isdir(source_path) and recursive:
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "copy",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "source_path": source_path,
                    "destination_path": destination_path
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "copy",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to copy file: {str(e)}"
            }

    def _handle_move(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理移动操作"""
        source_path = config.get('source_path')
        destination_path = config.get('destination_path')

        if not source_path or not destination_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "move",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "Source and destination paths are required for move operation"
            }

        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.move(source_path, destination_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "move",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "source_path": source_path,
                    "destination_path": destination_path
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "move",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to move file: {str(e)}"
            }

    def _handle_delete(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理删除操作"""
        file_path = config.get('file_path')
        recursive = config.get('recursive', False)

        if not file_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "delete",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "File path is required for delete operation"
            }

        try:
            if os.path.isdir(file_path) and recursive:
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "delete",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "file_path": file_path
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "delete",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to delete file: {str(e)}"
            }

    def _handle_info(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理信息查询操作"""
        file_path = config.get('file_path')

        if not file_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "info",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "File path is required for info operation"
            }

        try:
            file_stats = os.stat(file_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "info",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "file_path": file_path,
                    "size": file_stats.st_size,
                    "modified_time": time.ctime(file_stats.st_mtime),
                    "created_time": time.ctime(file_stats.st_ctime),
                    "is_directory": os.path.isdir(file_path),
                    "is_file": os.path.isfile(file_path),
                    "permissions": oct(file_stats.st_mode)[-3:]
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "info",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to get file info: {str(e)}"
            }

    def _handle_list(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理目录列表操作"""
        directory_path = config.get('directory_path', '.')
        pattern = config.get('pattern', '*')

        try:
            search_path = os.path.join(directory_path, pattern)
            files = glob.glob(search_path)

            file_info_list = []
            for file_path in files:
                try:
                    file_stats = os.stat(file_path)
                    file_info_list.append({
                        "file_path": file_path,
                        "size": file_stats.st_size,
                        "modified_time": time.ctime(file_stats.st_mtime),
                        "is_directory": os.path.isdir(file_path),
                        "is_file": os.path.isfile(file_path)
                    })
                except Exception:
                    # 跳过无法获取信息的文件
                    file_info_list.append({
                        "file_path": file_path,
                        "size": 0,
                        "modified_time": "Unknown",
                        "is_directory": os.path.isdir(file_path),
                        "is_file": os.path.isfile(file_path)
                    })

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "list",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "results": {
                    "files": file_info_list,
                    "count": len(file_info_list)
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "list",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to list directory: {str(e)}"
            }

    def _handle_mkdir(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理创建目录操作"""
        directory_path = config.get('directory_path')
        parents = config.get('parents', False)

        if not directory_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "mkdir",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "Directory path is required for mkdir operation"
            }

        try:
            if parents:
                os.makedirs(directory_path, exist_ok=True)
            else:
                os.mkdir(directory_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "mkdir",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "directory_path": directory_path
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "mkdir",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to create directory: {str(e)}"
            }

    def _handle_search(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理文件搜索操作"""
        directory_path = config.get('directory_path', '.')
        pattern = config.get('pattern', '*')
        recursive = config.get('recursive', False)

        try:
            if recursive:
                files = []
                for root, _, filenames in os.walk(directory_path):
                    for filename in filenames:
                        if pattern == '*' or pattern in filename:
                            files.append(os.path.join(root, filename))
            else:
                search_path = os.path.join(directory_path, pattern)
                files = glob.glob(search_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "search",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "results": {
                    "files": files,
                    "count": len(files)
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "search",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to search files: {str(e)}"
            }

    def _handle_backup(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理备份操作"""
        file_path = config.get('file_path')
        backup_path = config.get('backup_path')

        if not file_path or not backup_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "backup",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "File path and backup path are required for backup operation"
            }

        try:
            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(file_path, backup_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "backup",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "file_path": file_path,
                    "backup_path": backup_path
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "backup",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to backup file: {str(e)}"
            }

    def _handle_restore(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理恢复操作"""
        backup_path = config.get('backup_path')
        restore_path = config.get('restore_path')

        if not backup_path or not restore_path:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "restore",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "Backup path and restore path are required for restore operation"
            }

        try:
            # 确保恢复目录存在
            os.makedirs(os.path.dirname(restore_path), exist_ok=True)
            shutil.copy2(backup_path, restore_path)

            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "restore",
                    "execution_time": time.time() - start_time,
                    "status": "success"
                },
                "file_data": {
                    "backup_path": backup_path,
                    "restore_path": restore_path
                }
            }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "file-operations",
                    "operation": "restore",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Failed to restore file: {str(e)}"
            }


def main(config: Dict[str, Any]) -> Dict[str, Any]:
    """主函数入口"""
    manager = FileManager()
    return manager.execute(config)


if __name__ == "__main__":
    # 测试代码
    test_config = {
        "operation": "write",
        "file_path": "/tmp/test_file.txt",
        "content": "Hello, File Operations Skill!",
        "encoding": "utf-8"
    }

    result = main(test_config)
    print(json.dumps(result, indent=2, ensure_ascii=False))