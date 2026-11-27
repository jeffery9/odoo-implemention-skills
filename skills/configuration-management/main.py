#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器Skill主执行文件
"""

import json
import time
import os
import yaml
from typing import Any, Dict, Optional, List
from datetime import datetime
import hashlib


class ConfigVersionManager:
    """配置版本管理器"""

    def __init__(self, storage_dir: str = "/tmp/config_versions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save_version(self, config_type: str, config_id: str, config_data: Dict[str, Any], author: str = "system") -> str:
        """保存配置版本"""
        version = self._generate_version()
        # 毫秒时间戳可能在同一毫秒内碰撞；若目标文件已存在，递增版本号，
        # 保证连续写入产生独立的历史记录，而不是互相覆盖成一条。
        version_file = self._get_version_file_path(config_type, config_id, version)
        while os.path.exists(version_file):
            version = f"v{int(version[1:]) + 1}"
            version_file = self._get_version_file_path(config_type, config_id, version)
        version_data = {
            'config_data': config_data,
            'metadata': {
                'version': version,
                'timestamp': datetime.now().isoformat(),
                'author': author,
                'config_type': config_type,
                'config_id': config_id
            }
        }

        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)

        return version

    def get_version(self, config_type: str, config_id: str, version: str) -> Optional[Dict[str, Any]]:
        """获取指定版本的配置"""
        version_file = self._get_version_file_path(config_type, config_id, version)
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def get_history(self, config_type: str, config_id: str) -> List[Dict[str, Any]]:
        """获取配置变更历史"""
        history = []
        config_dir = os.path.join(self.storage_dir, config_type, config_id)

        if os.path.exists(config_dir):
            for filename in os.listdir(config_dir):
                if filename.endswith('.json'):
                    version_file = os.path.join(config_dir, filename)
                    with open(version_file, 'r', encoding='utf-8') as f:
                        version_data = json.load(f)
                        history.append(version_data['metadata'])

        # 按时间排序
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        return history

    def _generate_version(self) -> str:
        """生成版本号"""
        timestamp = int(time.time() * 1000)
        return f"v{timestamp}"

    def _get_version_file_path(self, config_type: str, config_id: str, version: str) -> str:
        """获取版本文件路径"""
        config_dir = os.path.join(self.storage_dir, config_type, config_id)
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, f"{version}.json")


class ConfigurationManager:
    """配置管理器主类"""

    def __init__(self):
        self.storage_dir = "/tmp/configuration_management"
        os.makedirs(self.storage_dir, exist_ok=True)
        self.version_manager = ConfigVersionManager()

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行配置操作"""
        start_time = time.time()

        operation = config.get('operation', 'get')
        config_type = config.get('config_type')
        config_id = config.get('config_id')

        try:
            if operation == 'get':
                return self._handle_get(config, start_time)
            elif operation == 'set':
                return self._handle_set(config, start_time)
            elif operation == 'update':
                return self._handle_update(config, start_time)
            elif operation == 'delete':
                return self._handle_delete(config, start_time)
            elif operation == 'validate':
                return self._handle_validate(config, start_time)
            elif operation == 'history':
                return self._handle_history(config, start_time)
            else:
                return {
                    "metadata": {
                        "skill_name": "configuration-management",
                        "operation": operation,
                        "execution_time": time.time() - start_time,
                        "status": "failed"
                    },
                    "error": f"Unsupported operation: {operation}"
                }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": operation,
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": str(e)
            }

    def _handle_get(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理获取配置操作"""
        config_type = config.get('config_type')
        config_id = config.get('config_id')
        version = config.get('version')

        if not config_type or not config_id:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": "get",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "config_type and config_id are required"
            }

        # 获取配置数据
        config_data = self._load_config(config_type, config_id, version)

        if config_data is None:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": "get",
                    "config_type": config_type,
                    "config_id": config_id,
                    "execution_time": time.time() - start_time,
                    "status": "not_found"
                }
            }

        return {
            "metadata": {
                "skill_name": "configuration-management",
                "operation": "get",
                "config_type": config_type,
                "config_id": config_id,
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "config_data": {
                "config_id": config_id,
                "config_type": config_type,
                "data": config_data
            }
        }

    def _handle_set(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理设置配置操作"""
        config_type = config.get('config_type')
        config_id = config.get('config_id')
        config_data = config.get('config_data')

        if not config_type or not config_id or config_data is None:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": "set",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "config_type, config_id, and config_data are required"
            }

        # 保存配置数据
        self._save_config(config_type, config_id, config_data)

        # 保存版本
        version = self.version_manager.save_version(config_type, config_id, config_data)

        return {
            "metadata": {
                "skill_name": "configuration-management",
                "operation": "set",
                "config_type": config_type,
                "config_id": config_id,
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "config_data": {
                "config_id": config_id,
                "config_type": config_type,
                "data": config_data,
                "metadata": {
                    "version": version,
                    "created_at": datetime.now().isoformat()
                }
            }
        }

    def _handle_update(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理更新配置操作"""
        config_type = config.get('config_type')
        config_id = config.get('config_id')
        config_data = config.get('config_data')

        if not config_type or not config_id or config_data is None:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": "update",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "config_type, config_id, and config_data are required"
            }

        # 获取现有配置
        existing_config = self._load_config(config_type, config_id) or {}

        # 合并配置
        updated_config = self._merge_configurations(existing_config, config_data)

        # 保存更新后的配置
        self._save_config(config_type, config_id, updated_config)

        # 保存版本
        version = self.version_manager.save_version(config_type, config_id, updated_config)

        return {
            "metadata": {
                "skill_name": "configuration-management",
                "operation": "update",
                "config_type": config_type,
                "config_id": config_id,
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "config_data": {
                "config_id": config_id,
                "config_type": config_type,
                "data": updated_config,
                "metadata": {
                    "version": version,
                    "updated_at": datetime.now().isoformat()
                }
            }
        }

    def _handle_delete(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理删除配置操作"""
        config_type = config.get('config_type')
        config_id = config.get('config_id')

        if not config_type or not config_id:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": "delete",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "config_type and config_id are required"
            }

        # 删除配置文件
        config_file = self._get_config_file_path(config_type, config_id)
        if os.path.exists(config_file):
            os.remove(config_file)
            success = True
        else:
            success = False

        return {
            "metadata": {
                "skill_name": "configuration-management",
                "operation": "delete",
                "config_type": config_type,
                "config_id": config_id,
                "execution_time": time.time() - start_time,
                "status": "success" if success else "not_found"
            }
        }

    def _handle_validate(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理验证配置操作"""
        config_type = config.get('config_type')
        config_id = config.get('config_id')
        config_data = config.get('config_data')

        if not config_type or not config_id:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": "validate",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "config_type and config_id are required"
            }

        # 如果没有提供config_data，则加载现有配置
        if config_data is None:
            config_data = self._load_config(config_type, config_id)
            if config_data is None:
                return {
                    "metadata": {
                        "skill_name": "configuration-management",
                        "operation": "validate",
                        "config_type": config_type,
                        "config_id": config_id,
                        "execution_time": time.time() - start_time,
                        "status": "not_found"
                    }
                }

        # 执行验证（简化实现，实际应该有具体的验证逻辑）
        errors = self._validate_config(config_data, config_type)

        return {
            "metadata": {
                "skill_name": "configuration-management",
                "operation": "validate",
                "config_type": config_type,
                "config_id": config_id,
                "execution_time": time.time() - start_time,
                "status": "success" if not errors else "validation_failed"
            },
            "results": {
                "validation_errors": errors
            },
            "config_data": {
                "config_id": config_id,
                "config_type": config_type,
                "data": config_data
            }
        }

    def _handle_history(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理获取配置历史操作"""
        config_type = config.get('config_type')
        config_id = config.get('config_id')

        if not config_type or not config_id:
            return {
                "metadata": {
                    "skill_name": "configuration-management",
                    "operation": "history",
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "config_type and config_id are required"
            }

        # 获取历史记录
        history = self.version_manager.get_history(config_type, config_id)

        return {
            "metadata": {
                "skill_name": "configuration-management",
                "operation": "history",
                "config_type": config_type,
                "config_id": config_id,
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "results": {
                "history": history
            }
        }

    def _load_config(self, config_type: str, config_id: str, version: str = None) -> Optional[Dict[str, Any]]:
        """加载配置数据"""
        if version:
            version_data = self.version_manager.get_version(config_type, config_id, version)
            return version_data['config_data'] if version_data else None

        config_file = self._get_config_file_path(config_type, config_id)
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _save_config(self, config_type: str, config_id: str, config_data: Dict[str, Any]) -> None:
        """保存配置数据"""
        config_file = self._get_config_file_path(config_type, config_id)
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def _get_config_file_path(self, config_type: str, config_id: str) -> str:
        """获取配置文件路径"""
        return os.path.join(self.storage_dir, config_type, f"{config_id}.json")

    def _merge_configurations(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置，override_config优先级更高"""
        merged = base_config.copy()
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configurations(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _validate_config(self, config_data: Dict[str, Any], config_type: str) -> List[str]:
        """验证配置数据（简化实现）"""
        errors = []

        # 基本验证
        if not isinstance(config_data, dict):
            errors.append("Configuration data must be a dictionary")
            return errors

        # 根据配置类型进行特定验证（示例）
        if config_type == "skill":
            if "timeout" in config_data and not isinstance(config_data["timeout"], int):
                errors.append("timeout must be an integer")
            if "cache_enabled" in config_data and not isinstance(config_data["cache_enabled"], bool):
                errors.append("cache_enabled must be a boolean")

        return errors


def main(config: Dict[str, Any]) -> Dict[str, Any]:
    """主函数入口"""
    manager = ConfigurationManager()
    return manager.execute(config)


if __name__ == "__main__":
    # 测试代码
    test_config = {
        "operation": "set",
        "config_type": "skill",
        "config_id": "test-skill",
        "config_data": {"timeout": 30, "retries": 3}
    }

    result = main(test_config)
    print(json.dumps(result, indent=2, ensure_ascii=False))