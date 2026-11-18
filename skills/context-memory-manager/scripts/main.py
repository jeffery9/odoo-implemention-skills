#!/usr/bin/env python3
# -*- coding: utf-8 -*- 

"""
Enhanced Memory Manager based on OpenClaw practices using JSONL format.
Manages Short-term context, Episodic runs, and Long-term Semantic facts.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

VALID_CATEGORIES = ("fact", "pattern")


class MemoryManager:
    def __init__(self, kb_root: Path):
        self.kb_root = Path(kb_root)
        self.facts_path = self.kb_root / "long_term_facts.jsonl"
        self.patterns_path = self.kb_root / "usage_patterns.jsonl"
        self._init_storage()

    def storage_for(self, category: str) -> Path:
        """把 category 映射到具体 JSONL 文件。

        只接受 fact / pattern。历史上任何未知值都会静默落到 usage_patterns.jsonl，
        于是写错类别的记忆会「保存成功」但永远查不到——无声丢数据比报错更糟。
        """
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"未知的 category: {category!r}；只支持 {list(VALID_CATEGORIES)}"
            )
        return self.facts_path if category == "fact" else self.patterns_path

    def _init_storage(self):
        self.kb_root.mkdir(parents=True, exist_ok=True)
        # Ensure files exist
        for p in [self.facts_path, self.patterns_path]:
            if not p.exists():
                p.touch()

    def remember(self, category: str, key: str, value: Any, metadata: Optional[Dict] = None):
        """Append a persistent fact/pattern (Long-term) to JSONL."""
        storage_file = self.storage_for(category)
        if not key:
            raise ValueError("key 不能为空：它是 recall 的唯一索引")

        entry = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        with open(storage_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def recall(self, category: str, query: str = None) -> Dict:
        """Retrieve the latest state of memories from JSONL."""
        storage_file = self.storage_for(category)
        if not storage_file.exists():
            return {}

        memories = {}
        with open(storage_file, 'r', encoding='utf-8') as f:
            for lineno, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    key = entry["key"]
                except (json.JSONDecodeError, KeyError) as e:
                    # 明确指出坏行位置：整份记忆库因一行损坏而静默返回空，等于丢数据
                    raise ValueError(f"{storage_file}:{lineno} 不是合法的记忆记录: {e}") from e
                # Latest entry for a key wins
                memories[key] = {
                    "value": entry.get("value"),
                    "metadata": entry.get("metadata") or {},
                    "updated_at": entry.get("timestamp")
                }

        if not query:
            return memories

        return {k: v for k, v in memories.items() if query.lower() in k.lower()}

    def snapshot_run(self, run_id: str, context: Dict):
        """Save a snapshot of the current working memory (Episodic) as JSONL."""
        if not run_id:
            raise ValueError("run_id 不能为空：快照文件名由它决定")
        snapshot_dir = self.kb_root / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot_path = snapshot_dir / f"{run_id}.jsonl"
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(context, ensure_ascii=False) + "\n")
        return snapshot_path

def main():
    import sys
    if len(sys.argv) < 2:
        return

    try:
        params = json.loads(sys.argv[1])
        # 运行时数据属于用户工作区，与技能装在哪里无关。
        # 优先级：CAPABILITY_TWIN_WORKSPACE > 当前工作目录。
        # 不再用固定深度向上推导：npx skills 安装后深度会变，推导会落到错误目录。
        env_ws = os.environ.get("CAPABILITY_TWIN_WORKSPACE")
        project_root = Path(env_ws).expanduser().resolve() if env_ws else Path.cwd()
        manager = MemoryManager(project_root / "kb" / "mem")
        
        operation = params.get("operation")
        if operation == "remember":
            manager.remember(params.get("category", "fact"), params.get("key"), params.get("value"), params.get("metadata"))
            print(json.dumps({"status": "success", "operation": "remember"}))
        elif operation == "recall":
            results = manager.recall(params.get("category", "fact"), params.get("query"))
            print(json.dumps({"status": "success", "data": results, "operation": "recall"}))
        elif operation == "snapshot":
            manager.snapshot_run(params.get("run_id"), params.get("context"))
            print(json.dumps({"status": "success", "operation": "snapshot"}))
        else:
            # 拼错 operation 时保持沉默等于「成功但什么都没做」，调用方无从发现
            raise ValueError(
                f"未知的 operation: {operation!r}；只支持 remember / recall / snapshot"
            )
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()
