#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Manager Skill 主执行文件
"""

import json
import os
import time
import hashlib
import tempfile
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime


def _ensure_dir(path: Path) -> Path:
    """
    确保目录存在。

    兼容不完全实现 exist_ok 的受限运行时（沙箱 / 自定义 shim 会抛 FileExistsError）；
    若目标确实不是目录，仍如实抛错，避免掩盖真实故障。
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        if not path.is_dir():
            raise
    return path


class KnowledgeManager:
    """知识管理器主类"""

    def __init__(self):
        self.supported_operations = [
            "store", "retrieve", "update", "delete",
            "cache_management", "lifecycle_management"
        ]
        self.cache_dir = Path(tempfile.gettempdir()) / "knowledge_base"
        _ensure_dir(self.cache_dir)
        self.index_file = self.cache_dir / "knowledge_index.json"
        self._load_index()

    def _load_index(self):
        """加载知识索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.knowledge_index = json.load(f)
            except Exception:
                self.knowledge_index = {}
        else:
            self.knowledge_index = {}

    def _save_index(self):
        """保存知识索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass  # 忽略索引保存错误

    def _generate_knowledge_id(self, knowledge_key: str, params: Dict) -> str:
        """生成知识标识符"""
        key_data = f"{knowledge_key}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _serialize_knowledge(self, knowledge_data: Any) -> str:
        """序列化知识数据"""
        if isinstance(knowledge_data, str):
            return knowledge_data
        return json.dumps(knowledge_data, ensure_ascii=False)

    def _deserialize_knowledge(self, serialized_data: str) -> Any:
        """反序列化知识数据"""
        try:
            return json.loads(serialized_data)
        except Exception:
            return serialized_data

    def _calculate_data_hash(self, data: str) -> str:
        """计算数据摘要"""
        return hashlib.sha256(data.encode()).hexdigest()

    def _persist_knowledge(self, knowledge_id: str, serialized_data: str, metadata: Dict) -> bool:
        """持久化存储知识"""
        try:
            # 存储知识数据
            knowledge_file = self.cache_dir / f"{knowledge_id}.json"
            knowledge_content = {
                "data": serialized_data,
                "metadata": metadata
            }
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_content, f, ensure_ascii=False, indent=2)

            # 更新索引
            self.knowledge_index[knowledge_id] = metadata
            self._save_index()

            return True
        except Exception as e:
            return False

    def _load_knowledge(self, knowledge_id: str) -> Any:
        """加载知识数据"""
        try:
            knowledge_file = self.cache_dir / f"{knowledge_id}.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                return self._deserialize_knowledge(content["data"])
            return None
        except Exception:
            return None

    def _update_index(self, knowledge_id: str, metadata: Dict):
        """更新索引"""
        self.knowledge_index[knowledge_id] = metadata
        self._save_index()

    def _update_access_count(self, knowledge_id: str):
        """更新访问计数"""
        if knowledge_id in self.knowledge_index:
            self.knowledge_index[knowledge_id]["access_count"] = \
                self.knowledge_index[knowledge_id].get("access_count", 0) + 1
            self.knowledge_index[knowledge_id]["last_accessed"] = time.time()
            self._save_index()

    def _parse_search_query(self, search_query: str) -> List[str]:
        """解析搜索查询"""
        # 简单的关键词分割
        return [word.strip() for word in search_query.split() if word.strip()]

    def _query_index(self, parsed_query: List[str], params: Dict) -> List[Dict]:
        """查询索引"""
        candidates = []
        tags_filter = params.get("tags", [])

        for knowledge_id, metadata in self.knowledge_index.items():
            # 检查标签过滤
            if tags_filter:
                knowledge_tags = metadata.get("tags", [])
                if not any(tag in knowledge_tags for tag in tags_filter):
                    continue

            # 检查过期时间
            created_at = metadata.get("created_at")
            ttl = metadata.get("ttl", 86400)
            if created_at:
                created_timestamp = time.mktime(datetime.fromisoformat(created_at).timetuple())
                if time.time() > created_timestamp + ttl:
                    continue  # 已过期，跳过

            # 计算相关性评分
            score = 0
            knowledge_key = metadata.get("key", "")
            knowledge_tags = metadata.get("tags", [])

            # 关键词匹配评分
            for query_word in parsed_query:
                if query_word.lower() in knowledge_key.lower():
                    score += 2
                for tag in knowledge_tags:
                    if query_word.lower() in tag.lower():
                        score += 1

            candidates.append({
                "id": knowledge_id,
                "key": knowledge_key,
                "metadata": metadata,
                "score": score
            })

        return candidates

    def _rank_results(self, candidates: List[Dict], parsed_query: List[str]) -> List[Dict]:
        """对结果进行排序"""
        # 按相关性评分排序
        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def _list_cache_items(self) -> List[Dict]:
        """列出所有缓存条目"""
        items = []
        for knowledge_id, metadata in self.knowledge_index.items():
            items.append({
                "id": knowledge_id,
                "metadata": metadata
            })
        return items

    def _remove_cache_item(self, knowledge_id: str) -> bool:
        """删除缓存条目"""
        try:
            # 删除知识文件
            knowledge_file = self.cache_dir / f"{knowledge_id}.json"
            if knowledge_file.exists():
                knowledge_file.unlink()

            # 从索引中移除
            if knowledge_id in self.knowledge_index:
                del self.knowledge_index[knowledge_id]
                self._save_index()

            return True
        except Exception:
            return False

    def _cleanup_cache(self, strategy: str, params: Dict) -> Dict:
        """清理缓存"""
        all_items = self._list_cache_items()
        items_to_remove = []

        if strategy == "lru":
            # 按最后访问时间排序，删除最久未访问的
            sorted_items = sorted(
                all_items,
                key=lambda x: x["metadata"].get("last_accessed", x["metadata"].get("created_at", 0))
            )
            items_to_remove = sorted_items[:params.get("cleanup_count", 100)]
        elif strategy == "expired":
            # 删除已过期的条目
            current_time = time.time()
            items_to_remove = [
                item for item in all_items
                if item["metadata"].get("created_at") and
                   time.mktime(datetime.fromisoformat(item["metadata"]["created_at"]).timetuple()) +
                   item["metadata"].get("ttl", 86400) < current_time
            ]
        elif strategy == "size_based":
            # 基于大小清理
            total_size = sum(item["metadata"].get("size_bytes", 0) for item in all_items)
            max_size = params.get("max_size_mb", 1024) * 1024 * 1024
            if total_size > max_size:
                # 删除最少访问的条目
                sorted_items = sorted(all_items, key=lambda x: x["metadata"].get("access_count", 0))
                items_to_remove = sorted_items[:int(len(sorted_items) * 0.1)]  # 删除10%

        # 执行删除
        removed_count = 0
        space_freed = 0
        for item in items_to_remove:
            if self._remove_cache_item(item["id"]):
                removed_count += 1
                space_freed += item["metadata"].get("size_bytes", 0)

        return {
            "action": "cleanup",
            "strategy": strategy,
            "items_removed": removed_count,
            "space_freed_mb": space_freed / (1024 * 1024)
        }

    def _cache_statistics(self) -> Dict:
        """缓存统计信息"""
        all_items = self._list_cache_items()
        total_items = len(all_items)
        total_size = sum(item["metadata"].get("size_bytes", 0) for item in all_items)
        total_accesses = sum(item["metadata"].get("access_count", 0) for item in all_items)

        # 计算平均访问次数
        avg_accesses = total_accesses / total_items if total_items > 0 else 0

        # 找到最常访问的条目
        if all_items:
            most_accessed = max(all_items, key=lambda x: x["metadata"].get("access_count", 0))
            least_accessed = min(all_items, key=lambda x: x["metadata"].get("access_count", 0))
        else:
            most_accessed = least_accessed = None

        return {
            "total_items": total_items,
            "total_size_mb": total_size / (1024 * 1024),
            "total_accesses": total_accesses,
            "average_accesses_per_item": avg_accesses,
            "most_accessed_item": most_accessed["metadata"]["key"] if most_accessed else None,
            "least_accessed_item": least_accessed["metadata"]["key"] if least_accessed else None
        }

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行知识管理操作

        Args:
            config: 操作配置

        Returns:
            操作结果
        """
        operation = config.get("operation", "retrieve")

        if operation not in self.supported_operations:
            raise ValueError(f"不支持的操作类型: {operation}")

        if operation == "store":
            return self._store_knowledge(config)
        elif operation == "retrieve":
            return self._retrieve_knowledge(config)
        elif operation == "update":
            return self._update_knowledge(config)
        elif operation == "delete":
            return self._delete_knowledge(config)
        elif operation == "cache_management":
            return self._manage_cache(config)
        elif operation == "lifecycle_management":
            return self._manage_lifecycle(config)

    def _store_knowledge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """存储知识"""
        knowledge_key = config.get("knowledge_key")
        knowledge_data = config.get("knowledge_data")
        ttl = config.get("ttl", 86400)
        tags = config.get("tags", [])

        if not knowledge_key or knowledge_data is None:
            raise ValueError("缺少必需的参数: knowledge_key 或 knowledge_data")

        # 生成知识标识符
        knowledge_id = self._generate_knowledge_id(knowledge_key, config)

        # 序列化知识数据
        serialized_data = self._serialize_knowledge(knowledge_data)

        # 创建元数据
        metadata = {
            "id": knowledge_id,
            "key": knowledge_key,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_accessed": time.time(),
            "tags": tags,
            "ttl": ttl,
            "access_count": 0,
            "size_bytes": len(serialized_data),
            "hash": self._calculate_data_hash(serialized_data)
        }
        # KB 回流消费点（FDE §11 / A-3）：只有带人工确认与来源锚点的候选，
        # 才能被消费方以 approved_only=true 检索并采用；框架不自动代填这两项。
        for field in ("approved_by", "source_anchor"):
            if config.get(field):
                metadata[field] = str(config[field])

        # 存储知识
        storage_result = self._persist_knowledge(knowledge_id, serialized_data, metadata)

        return {
            "metadata": {
                "skill_name": "knowledge-manager",
                "operation": "store",
                "execution_time": datetime.now().isoformat(),
                "status": "success" if storage_result else "failed"
            },
            "results": {
                "operation_result": "知识存储成功" if storage_result else "知识存储失败",
                "knowledge_id": knowledge_id,
                "affected_items": 1 if storage_result else 0,
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": len(serialized_data) / (1024 * 1024)
                }
            },
            "knowledge_items": [{
                "key": knowledge_key,
                "data": knowledge_data,
                "metadata": metadata
            }]
        }

    def _retrieve_knowledge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """检索知识"""
        search_query = config.get("search_query", "")
        tags = config.get("tags", [])
        max_results = config.get("max_results", 10)

        # 解析搜索查询
        parsed_query = self._parse_search_query(search_query)

        # 查询索引获取候选条目
        candidates = self._query_index(parsed_query, {"tags": tags})

        # KB 回流消费点：approved_only=true 时只消费带人工确认与来源锚点的候选。
        # 这是「消费方主动采用才落库」的入口；不传则保持既有检索语义。
        approved_only = bool(config.get("approved_only", False))
        rejected_candidates = 0
        if approved_only:
            before = len(candidates)
            candidates = [
                c for c in candidates
                if (c.get("metadata", {}).get("approved_by")
                    and c.get("metadata", {}).get("source_anchor"))
            ]
            rejected_candidates = before - len(candidates)

        # 计算相关性评分
        ranked_results = self._rank_results(candidates, parsed_query)

        # 加载知识数据
        knowledge_items = []
        for item in ranked_results[:max_results]:
            knowledge_data = self._load_knowledge(item["id"])
            if knowledge_data is not None:
                # 更新访问计数
                self._update_access_count(item["id"])
                knowledge_items.append({
                    "key": item["key"],
                    "data": knowledge_data,
                    "metadata": item["metadata"],
                    "relevance_score": item["score"]
                })

        return {
            "metadata": {
                "skill_name": "knowledge-manager",
                "operation": "retrieve",
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "operation_result": f"检索到 {len(knowledge_items)} 个知识条目",
                "affected_items": len(knowledge_items),
                "performance_metrics": {
                    "execution_time_ms": 0,  # 简化处理
                    "memory_usage_mb": sum(item["metadata"].get("size_bytes", 0) for item in knowledge_items) / (1024 * 1024)
                },
                "retrieval_stats": {
                    "candidates_evaluated": len(candidates),
                    "results_returned": len(knowledge_items),
                    "total_found": len(ranked_results),
                    "approved_only": approved_only,
                    "rejected_unapproved": rejected_candidates
                }
            },
            "knowledge_items": knowledge_items
        }

    def _update_knowledge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """更新知识"""
        knowledge_key = config.get("knowledge_key")
        knowledge_data = config.get("knowledge_data")
        tags = config.get("tags", [])

        if not knowledge_key or knowledge_data is None:
            raise ValueError("缺少必需的参数: knowledge_key 或 knowledge_data")

        # 查找现有的知识条目
        existing_items = [
            item for item in self._list_cache_items()
            if item["metadata"].get("key") == knowledge_key
        ]

        if not existing_items:
            raise ValueError(f"未找到知识条目: {knowledge_key}")

        # 更新第一个匹配的条目
        existing_item = existing_items[0]
        knowledge_id = existing_item["id"]

        # 序列化新数据
        serialized_data = self._serialize_knowledge(knowledge_data)

        # 更新元数据
        metadata = existing_item["metadata"].copy()
        metadata["updated_at"] = datetime.now().isoformat()
        metadata["size_bytes"] = len(serialized_data)
        metadata["hash"] = self._calculate_data_hash(serialized_data)
        if tags:
            metadata["tags"] = list(set(metadata.get("tags", []) + tags))  # 合并标签并去重

        # 存储更新后的知识
        update_result = self._persist_knowledge(knowledge_id, serialized_data, metadata)

        return {
            "metadata": {
                "skill_name": "knowledge-manager",
                "operation": "update",
                "execution_time": datetime.now().isoformat(),
                "status": "success" if update_result else "failed"
            },
            "results": {
                "operation_result": "知识更新成功" if update_result else "知识更新失败",
                "knowledge_id": knowledge_id,
                "affected_items": 1 if update_result else 0,
                "performance_metrics": {
                    "execution_time_ms": 0,
                    "memory_usage_mb": len(serialized_data) / (1024 * 1024)
                }
            },
            "knowledge_items": [{
                "key": knowledge_key,
                "data": knowledge_data,
                "metadata": metadata
            }]
        }

    def _delete_knowledge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """删除知识"""
        knowledge_key = config.get("knowledge_key")

        if not knowledge_key:
            raise ValueError("缺少必需的参数: knowledge_key")

        # 查找要删除的知识条目
        items_to_delete = [
            item for item in self._list_cache_items()
            if item["metadata"].get("key") == knowledge_key
        ]

        deleted_count = 0
        for item in items_to_delete:
            if self._remove_cache_item(item["id"]):
                deleted_count += 1

        return {
            "metadata": {
                "skill_name": "knowledge-manager",
                "operation": "delete",
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "operation_result": f"成功删除 {deleted_count} 个知识条目",
                "affected_items": deleted_count,
                "performance_metrics": {
                    "execution_time_ms": 0,
                    "memory_usage_mb": 0
                }
            },
            "knowledge_items": []
        }

    def _manage_cache(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """管理缓存"""
        action = config.get("action", "stats")
        strategy = config.get("strategy", "lru")

        if action == "stats":
            stats = self._cache_statistics()
            result = {
                "metadata": {
                    "skill_name": "knowledge-manager",
                    "operation": "cache_management",
                    "execution_time": datetime.now().isoformat(),
                    "status": "success"
                },
                "results": {
                    "operation_result": "缓存统计完成",
                    "cache_stats": stats,
                    "performance_metrics": {
                        "execution_time_ms": 0,
                        "memory_usage_mb": stats.get("total_size_mb", 0)
                    }
                },
                "knowledge_items": []
            }
        else:
            cleanup_result = self._cleanup_cache(strategy, config)
            result = {
                "metadata": {
                    "skill_name": "knowledge-manager",
                    "operation": "cache_management",
                    "execution_time": datetime.now().isoformat(),
                    "status": "success"
                },
                "results": {
                    "operation_result": f"缓存管理完成: {cleanup_result['action']}",
                    "cache_management_result": cleanup_result,
                    "performance_metrics": {
                        "execution_time_ms": 0,
                        "memory_usage_mb": cleanup_result.get("space_freed_mb", 0)
                    }
                },
                "knowledge_items": []
            }

        return result

    def _manage_lifecycle(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """管理知识生命周期"""
        # 简化的生命周期管理，主要是清理过期条目
        cleanup_result = self._cleanup_cache("expired", {})

        return {
            "metadata": {
                "skill_name": "knowledge-manager",
                "operation": "lifecycle_management",
                "execution_time": datetime.now().isoformat(),
                "status": "success"
            },
            "results": {
                "operation_result": "生命周期管理完成",
                "lifecycle_result": cleanup_result,
                "performance_metrics": {
                    "execution_time_ms": 0,
                    "memory_usage_mb": cleanup_result.get("space_freed_mb", 0)
                }
            },
            "knowledge_items": []
        }


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <config_json>")
        sys.exit(1)

    try:
        config = json.loads(sys.argv[1])
        manager = KnowledgeManager()
        result = manager.execute(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {
            "metadata": {
                "skill_name": "knowledge-manager",
                "status": "failed",
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            },
            "error_details": f"执行知识管理操作时发生错误: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()