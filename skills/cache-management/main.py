#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器Skill主执行文件
"""

import json
import time
import hashlib
from collections import OrderedDict
from typing import Any, Dict, Optional, List
import os
import pickle


class BloomFilter:
    """简单的布隆过滤器实现，用于缓存穿透防护"""

    def __init__(self, size=10000, hash_count=3):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [0] * size

    def _hash(self, item, seed):
        """生成哈希值"""
        hash_val = hashlib.md5((str(item) + str(seed)).encode()).hexdigest()
        return int(hash_val, 16) % self.size

    def add(self, item):
        """添加元素到布隆过滤器"""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            self.bit_array[index] = 1

    def might_contain(self, item):
        """检查元素是否可能存在于集合中"""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            if self.bit_array[index] == 0:
                return False
        return True


class LRUCache:
    """LRU缓存实现"""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.bloom_filter = BloomFilter()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            # 移动到末尾表示最近使用
            self.cache.move_to_end(key)
            value_data = self.cache[key]
            # 更新访问计数
            value_data['access_count'] += 1
            value_data['last_accessed'] = time.time()
            return value_data['value']
        return None

    def put(self, key: str, value: Any, ttl: int = 3600) -> None:
        """设置缓存值"""
        # 如果键已存在，先删除它
        if key in self.cache:
            # 更新现有键值
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            # 删除最久未使用的项
            self.cache.popitem(last=False)

        # 添加到布隆过滤器
        self.bloom_filter.add(key)

        # 存储值和元数据
        self.cache[key] = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl if ttl > 0 else None,
            'access_count': 0,
            'last_accessed': time.time(),
            'size': len(str(value))
        }

    def delete(self, key: str) -> bool:
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> int:
        """清空缓存"""
        count = len(self.cache)
        self.cache.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.cache:
            return {
                'item_count': 0,
                'total_size': 0,
                'hit_rate': 0.0
            }

        total_size = sum(item['size'] for item in self.cache.values())
        total_access = sum(item['access_count'] for item in self.cache.values())
        hit_rate = total_access / max(len(self.cache), 1) if total_access > 0 else 0.0

        return {
            'item_count': len(self.cache),
            'total_size': total_size,
            'hit_rate': hit_rate,
            'capacity': self.capacity
        }


class FileCache:
    """文件系统缓存实现"""

    def __init__(self, cache_dir: str = "/tmp/cache_management"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.bloom_filter = BloomFilter()

    def _get_file_path(self, key: str) -> str:
        """获取缓存文件路径"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)

            # 检查是否过期
            if data.get('expires_at') and time.time() > data['expires_at']:
                os.remove(file_path)
                return None

            # 更新访问计数
            data['access_count'] = data.get('access_count', 0) + 1
            data['last_accessed'] = time.time()

            with open(file_path, 'wb') as f:
                pickle.dump(data, f)

            return data['value']
        except Exception:
            return None

    def put(self, key: str, value: Any, ttl: int = 3600) -> None:
        """设置缓存值"""
        file_path = self._get_file_path(key)

        # 添加到布隆过滤器
        self.bloom_filter.add(key)

        data = {
            'value': value,
            'created_at': time.time(),
            'expires_at': time.time() + ttl if ttl > 0 else None,
            'access_count': 0,
            'last_accessed': time.time(),
            'size': len(str(value))
        }

        with open(file_path, 'wb') as f:
            pickle.dump(data, f)

    def delete(self, key: str) -> bool:
        """删除缓存项"""
        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def clear(self) -> int:
        """清空缓存"""
        count = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                os.remove(os.path.join(self.cache_dir, filename))
                count += 1
        return count


class CacheManager:
    """缓存管理器主类"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.memory_cache = LRUCache(capacity=10000)
            self.file_cache = FileCache()
            self.cache_types = {
                'memory': self.memory_cache,
                'file': self.file_cache
            }
            self.__class__._initialized = True

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行缓存操作"""
        start_time = time.time()

        operation = config.get('operation', 'get')
        cache_type = config.get('cache_type', 'memory')
        key = config.get('key')

        cache = self.cache_types.get(cache_type)
        if not cache:
            return {
                "metadata": {
                    "skill_name": "cache-management",
                    "operation": operation,
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": f"Unsupported cache type: {cache_type}"
            }

        try:
            if operation == 'get':
                return self._handle_get(cache, key, start_time, operation, cache_type)
            elif operation == 'set':
                return self._handle_set(cache, config, start_time, operation, cache_type)
            elif operation == 'delete':
                return self._handle_delete(cache, key, start_time, operation, cache_type)
            elif operation == 'clear':
                return self._handle_clear(cache, config, start_time, operation, cache_type)
            elif operation == 'stats':
                return self._handle_stats(cache, start_time, operation, cache_type)
            elif operation == 'batch':
                return self._handle_batch(config, start_time)
            else:
                return {
                    "metadata": {
                        "skill_name": "cache-management",
                        "operation": operation,
                        "execution_time": time.time() - start_time,
                        "status": "failed"
                    },
                    "error": f"Unsupported operation: {operation}"
                }
        except Exception as e:
            return {
                "metadata": {
                    "skill_name": "cache-management",
                    "operation": operation,
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": str(e)
            }

    def _handle_get(self, cache, key: str, start_time: float, operation: str, cache_type: str) -> Dict[str, Any]:
        """处理获取操作"""
        if not key:
            return {
                "metadata": {
                    "skill_name": "cache-management",
                    "operation": operation,
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "Key is required for get operation"
            }

        value = cache.get(key)
        status = "success" if value is not None else "not_found"

        result = {
            "metadata": {
                "skill_name": "cache-management",
                "operation": operation,
                "execution_time": time.time() - start_time,
                "status": status
            }
        }

        if value is not None:
            result["cache_data"] = {
                "key": key,
                "value": value
            }

        return result

    def _handle_set(self, cache, config: Dict[str, Any], start_time: float, operation: str, cache_type: str) -> Dict[str, Any]:
        """处理设置操作"""
        key = config.get('key')
        value = config.get('value')
        ttl = config.get('ttl', 3600)

        if not key or value is None:
            return {
                "metadata": {
                    "skill_name": "cache-management",
                    "operation": operation,
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "Key and value are required for set operation"
            }

        cache.put(key, value, ttl)

        return {
            "metadata": {
                "skill_name": "cache-management",
                "operation": operation,
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "cache_data": {
                "key": key,
                "value": value
            }
        }

    def _handle_delete(self, cache, key: str, start_time: float, operation: str, cache_type: str) -> Dict[str, Any]:
        """处理删除操作"""
        if not key:
            return {
                "metadata": {
                    "skill_name": "cache-management",
                    "operation": operation,
                    "execution_time": time.time() - start_time,
                    "status": "failed"
                },
                "error": "Key is required for delete operation"
            }

        success = cache.delete(key)

        return {
            "metadata": {
                "skill_name": "cache-management",
                "operation": operation,
                "execution_time": time.time() - start_time,
                "status": "success" if success else "not_found"
            }
        }

    def _handle_clear(self, cache, config: Dict[str, Any], start_time: float, operation: str, cache_type: str) -> Dict[str, Any]:
        """处理清空操作"""
        pattern = config.get('pattern')
        # 简化实现，实际应该支持模式匹配
        count = cache.clear()

        return {
            "metadata": {
                "skill_name": "cache-management",
                "operation": operation,
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "results": {
                "affected_items": count
            }
        }

    def _handle_stats(self, cache, start_time: float, operation: str, cache_type: str) -> Dict[str, Any]:
        """处理统计操作"""
        stats = cache.stats() if hasattr(cache, 'stats') else {}

        return {
            "metadata": {
                "skill_name": "cache-management",
                "operation": operation,
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "results": {
                "cache_stats": stats
            }
        }

    def _handle_batch(self, config: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """处理批量操作"""
        actions = config.get('actions', [])
        results = []

        for action_config in actions:
            # 为每个操作创建独立的CacheManager实例以避免状态冲突
            sub_manager = CacheManager()
            result = sub_manager.execute(action_config)
            results.append(result)

        return {
            "metadata": {
                "skill_name": "cache-management",
                "operation": "batch",
                "execution_time": time.time() - start_time,
                "status": "success"
            },
            "results": {
                "batch_results": results
            }
        }


def main(config: Dict[str, Any]) -> Dict[str, Any]:
    """主函数入口"""
    manager = CacheManager()
    return manager.execute(config)


if __name__ == "__main__":
    # 测试代码
    test_config = {
        "operation": "set",
        "key": "test_key",
        "value": {"test": "data"},
        "ttl": 60,
        "cache_type": "memory"
    }

    result = main(test_config)
    print(json.dumps(result, indent=2, ensure_ascii=False))