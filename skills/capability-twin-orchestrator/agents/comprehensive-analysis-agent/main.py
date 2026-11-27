#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys
from pathlib import Path

def _ontology_binding(params):
    shared = params.get("shared_context") if isinstance(params.get("shared_context"), dict) else {}
    return {
        "ontology_context": params.get("ontology_context") or shared.get("ontology"),
        "ontology_contract": params.get("ontology_contract"),
    }

def main():
    params = {}
    if len(sys.argv) >= 2:
        try:
            params = json.loads(sys.argv[1])
        except (TypeError, json.JSONDecodeError):
            params = {}
    if not isinstance(params, dict):
        params = {}
    try:
        # 获取 Agent 自身的指令集
        agent_dir = Path(__file__).resolve().parent
        instruction_file = agent_dir / "AGENT.md"
        instructions = instruction_file.read_text(encoding='utf-8') if instruction_file.exists() else "No instructions found."

        # 返回指令和执行状态，标记为“等待语义解读”
        payload = {
            "status": "semantic_wait",
            "agent_name": agent_dir.name,
            "instructions": instructions,
            "message": "I/O performed. Logic instructions exported to shared context."
        }
        payload.update(_ontology_binding(params))
        print(json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        payload = {"status": "error", "message": str(e)}
        payload.update(_ontology_binding(params))
        print(json.dumps(payload, ensure_ascii=False))

if __name__ == "__main__":
    main()
