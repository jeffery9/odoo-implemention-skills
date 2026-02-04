#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Manager Skill 主执行文件 - 使用 JSONL 格式
"""

import json
import os
import time
import hashlib
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


class KnowledgeManager:
    """知识管理器主类"""

    def __init__(self, base_dir: Optional[str] = None):
        self.supported_operations = [
            "store", "retrieve", "update", "delete",
            "cache_management", "lifecycle_management"
        ]
        
        # Use provided base_dir or default to project-relative 'kb/mem'
        if base_dir:
            self.cache_dir = Path(base_dir)
        else:
            # Try to find project root or use current directory/kb/mem
            self.cache_dir = Path(os.getcwd()) / "kb" / "mem"
            
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "knowledge_index.jsonl"
        self._load_index()

    def _load_index(self):
        """加载知识索引 (JSONL 格式)"""
        self.knowledge_index = {}
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            # 假设 JSONL 的每一行是一个包含 id 的 metadata 对象
                            if "id" in entry:
                                self.knowledge_index[entry["id"]] = entry
            except Exception:
                pass

    def _save_index(self):
        """保存知识索引 (重写为 JSONL)"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                for metadata in self.knowledge_index.values():
                    f.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _generate_knowledge_id(self, knowledge_key: str, params: Dict) -> str:
        """生成知识标识符"""
        key_data = f"{knowledge_key}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _serialize_knowledge(self, knowledge_data: Any) -> Any:
        """返回原始数据，由存储层处理序列化"""
        return knowledge_data

    def _deserialize_knowledge(self, serialized_data: Any) -> Any:
        """反序列化知识数据"""
        if isinstance(serialized_data, str):
            try:
                return json.loads(serialized_data)
            except Exception:
                return serialized_data
        return serialized_data

    def _calculate_data_hash(self, data: Any) -> str:
        """计算数据摘要"""
        s = data if isinstance(data, str) else json.dumps(data, sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()

    def _persist_knowledge(self, knowledge_id: str, data: Any, metadata: Dict) -> bool:
        """持久化存储知识 (JSONL 格式)"""
        try:
            # 1. 存储独立的 .jsonl 文件
            knowledge_file = self.cache_dir / f"{knowledge_id}.jsonl"
            content = {"data": data, "metadata": metadata}
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(content, ensure_ascii=False) + "\n")

            # 2. 如果包含“人话”洞察，同步追加到全局长效事实库
            tags = metadata.get("tags", [])
            if "human_insight" in tags:
                wisdom_file = self.cache_dir / "business_wisdom.jsonl"
                wisdom_entry = {
                    "module": metadata.get("module"),
                    "insight": data.get("human_insight", {}).get("business_intent", "Unknown Capability"),
                    "value": data.get("human_insight", {}).get("value_to_owner", ""),
                    "id": knowledge_id,
                    "ts": datetime.now().isoformat()
                }
                with open(wisdom_file, 'a', encoding='utf-8') as wf:
                    wf.write(json.dumps(wisdom_entry, ensure_ascii=False) + "\n")
            
            if any(t in tags for t in ["human_insight", "capability_unit"]):
                global_facts = self.cache_dir / "long_term_facts.jsonl"
                global_entry = {
                    "key": metadata.get("key"),
                    "value": data,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat()
                }
                with open(global_facts, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(global_entry, ensure_ascii=False) + "\n")

            # 更新索引
            self.knowledge_index[knowledge_id] = metadata
            self._save_index()
            return True
        except Exception:
            return False

    def _load_knowledge(self, knowledge_id: str) -> Any:
        """加载知识数据"""
        try:
            knowledge_file = self.cache_dir / f"{knowledge_id}.jsonl"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    line = f.readline()
                    if line:
                        content = json.loads(line)
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
        return [word.strip() for word in search_query.split() if word.strip()]

    def _query_index(self, parsed_query: List[str], params: Dict) -> List[Dict]:
        """查询索引"""
        candidates = []
        tags_filter = params.get("tags", [])

        for knowledge_id, metadata in self.knowledge_index.items():
            if tags_filter:
                knowledge_tags = metadata.get("tags", [])
                if not any(tag in knowledge_tags for tag in tags_filter):
                    continue

            created_at = metadata.get("created_at")
            ttl = metadata.get("ttl", 86400)
            if created_at:
                try:
                    created_timestamp = time.mktime(datetime.fromisoformat(created_at).timetuple())
                    if time.time() > created_timestamp + ttl:
                        continue
                except Exception:
                    pass

            score = 0
            knowledge_key = metadata.get("key", "")
            knowledge_tags = metadata.get("tags", [])

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
        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def _list_cache_items(self) -> List[Dict]:
        """列出所有缓存条目"""
        return [{"id": k, "metadata": v} for k, v in self.knowledge_index.items()]

    def _remove_cache_item(self, knowledge_id: str) -> bool:
        """删除缓存条目"""
        try:
            knowledge_file = self.cache_dir / f"{knowledge_id}.jsonl"
            if knowledge_file.exists():
                knowledge_file.unlink()

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
            sorted_items = sorted(
                all_items,
                key=lambda x: x["metadata"].get("last_accessed", 0)
            )
            items_to_remove = sorted_items[:params.get("cleanup_count", 100)]
        elif strategy == "expired":
            current_time = time.time()
            items_to_remove = [
                item for item in all_items
                if item["metadata"].get("created_at") and
                   time.mktime(datetime.fromisoformat(item["metadata"]["created_at"]).timetuple()) +
                   item["metadata"].get("ttl", 86400) < current_time
            ]

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

    def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识管理操作"""
        operation = config.get("operation", "retrieve")
        base_dir = config.get("base_dir")

        if base_dir:
            self.__init__(base_dir=base_dir)

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

        knowledge_id = self._generate_knowledge_id(knowledge_key, config)
        serialized_data = self._serialize_knowledge(knowledge_data)

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

        storage_result = self._persist_knowledge(knowledge_id, serialized_data, metadata)

        return {
            "metadata": {
                "skill_name": "knowledge-manager",
                "operation": "store",
                "status": "success" if storage_result else "failed"
            },
            "results": {
                "knowledge_id": knowledge_id,
                "affected_items": 1 if storage_result else 0
            }
        }

    def _retrieve_knowledge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """检索知识"""
        search_query = config.get("search_query", "")
        tags = config.get("tags", [])
        max_results = config.get("max_results", 10)

        parsed_query = self._parse_search_query(search_query)
        candidates = self._query_index(parsed_query, {"tags": tags})
        ranked_results = self._rank_results(candidates, parsed_query)

        knowledge_items = []
        for item in ranked_results[:max_results]:
            knowledge_data = self._load_knowledge(item["id"])
            if knowledge_data is not None:
                self._update_access_count(item["id"])
                knowledge_items.append({
                    "key": item["key"],
                    "data": knowledge_data,
                    "metadata": item["metadata"],
                    "relevance_score": item["score"]
                })

        return {
            "metadata": {"skill_name": "knowledge-manager", "operation": "retrieve", "status": "success"},
            "knowledge_items": knowledge_items
        }

    def _update_knowledge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """更新知识"""
        knowledge_key = config.get("knowledge_key")
        knowledge_data = config.get("knowledge_data")
        
        existing_items = [item for item in self._list_cache_items() if item["metadata"].get("key") == knowledge_key]
        if not existing_items:
            raise ValueError(f"未找到知识条目: {knowledge_key}")

        existing_item = existing_items[0]
        knowledge_id = existing_item["id"]
        serialized_data = self._serialize_knowledge(knowledge_data)

        metadata = existing_item["metadata"].copy()
        metadata["updated_at"] = datetime.now().isoformat()
        metadata["size_bytes"] = len(serialized_data)
        metadata["hash"] = self._calculate_data_hash(serialized_data)

        update_result = self._persist_knowledge(knowledge_id, serialized_data, metadata)
        return {"metadata": {"skill_name": "knowledge-manager", "operation": "update", "status": "success" if update_result else "failed"}, "results": {"knowledge_id": knowledge_id}}

    def _delete_knowledge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """删除知识"""
        knowledge_key = config.get("knowledge_key")
        items_to_delete = [item for item in self._list_cache_items() if item["metadata"].get("key") == knowledge_key]
        deleted_count = 0
        for item in items_to_delete:
            if self._remove_cache_item(item["id"]):
                deleted_count += 1
        return {"metadata": {"skill_name": "knowledge-manager", "operation": "delete", "status": "success"}, "results": {"affected_items": deleted_count}}

    def _manage_cache(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """管理缓存"""
        action = config.get("action", "stats")
        if action == "stats":
            return {"metadata": {"skill_name": "knowledge-manager", "status": "success"}, "results": {"total_items": len(self.knowledge_index)}}
        else:
            cleanup_result = self._cleanup_cache(config.get("strategy", "lru"), config)
            return {"metadata": {"skill_name": "knowledge-manager", "status": "success"}, "results": cleanup_result}

    def _manage_lifecycle(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """管理知识生命周期"""
        cleanup_result = self._cleanup_cache("expired", {})
        return {"metadata": {"skill_name": "knowledge-manager", "status": "success"}, "results": cleanup_result}


def main():
    """主函数"""
    import sys
    if len(sys.argv) < 2:
        sys.exit(1)
    try:
        config = json.loads(sys.argv[1])
        manager = KnowledgeManager(base_dir=config.get("base_dir"))
        result = manager.execute(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"status": "failed", "error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
