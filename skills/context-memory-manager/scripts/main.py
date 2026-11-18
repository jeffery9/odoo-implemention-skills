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

class MemoryManager:
    def __init__(self, kb_root: Path):
        self.kb_root = kb_root
        self.facts_path = kb_root / "long_term_facts.jsonl"
        self.patterns_path = kb_root / "usage_patterns.jsonl"
        self._init_storage()

    def _init_storage(self):
        self.kb_root.mkdir(parents=True, exist_ok=True)
        # Ensure files exist
        for p in [self.facts_path, self.patterns_path]:
            if not p.exists():
                p.touch()

    def remember(self, category: str, key: str, value: Any, metadata: Optional[Dict] = None):
        """Append a persistent fact/pattern (Long-term) to JSONL."""
        storage_file = self.facts_path if category == "fact" else self.patterns_path
        
        entry = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        with open(storage_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def recall(self, category: str, query: str = None) -> Dict:
        """Retrieve the latest state of memories from JSONL."""
        storage_file = self.facts_path if category == "fact" else self.patterns_path
        if not storage_file.exists():
            return {}

        memories = {}
        with open(storage_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    # Latest entry for a key wins
                    memories[entry["key"]] = {
                        "value": entry["value"],
                        "metadata": entry["metadata"],
                        "updated_at": entry["timestamp"]
                    }
        
        if not query:
            return memories
            
        return {k: v for k, v in memories.items() if query.lower() in k.lower()}

    def snapshot_run(self, run_id: str, context: Dict):
        """Save a snapshot of the current working memory (Episodic) as JSONL."""
        snapshot_dir = self.kb_root / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        
        snapshot_path = snapshot_dir / f"{run_id}.jsonl"
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(context, ensure_ascii=False) + "\n")

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
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()
