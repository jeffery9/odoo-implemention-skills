#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys
from pathlib import Path

def main():
    try:
        # 获取 Agent 自身的指令集
        agent_dir = Path(__file__).resolve().parent
        instruction_file = agent_dir / "AGENT.md"
        instructions = instruction_file.read_text(encoding='utf-8') if instruction_file.exists() else "No instructions found."

        # 返回指令和执行状态，标记为“等待语义解读”
        print(json.dumps({
            "status": "semantic_wait",
            "agent_name": agent_dir.name,
            "instructions": instructions,
            "message": "I/O performed. Logic instructions exported to shared context."
        }, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()
