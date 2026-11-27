#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys
from pathlib import Path

# 框架路径中枢随 orchestrator 分发：本文件位于 <orchestrator>/agents/<agent>/main.py
_scripts = Path(__file__).resolve().parents[2] / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
import framework_paths

def _ontology_binding(params):
    shared = params.get("shared_context") if isinstance(params.get("shared_context"), dict) else {}
    return {
        "ontology_context": params.get("ontology_context") or shared.get("ontology"),
        "ontology_contract": params.get("ontology_contract"),
    }

def main():
    if len(sys.argv) < 2: return
    params = {}
    try:
        params = json.loads(sys.argv[1])
        target = params.get("target_module") or params.get("config", {}).get("target_module")
        # 直接获取 LLM 产出的完整 Markdown 内容
        full_markdown_content = params.get("full_markdown_content") or params.get("config", {}).get("full_markdown_content")
        
        if not full_markdown_content:
            payload = {"status": "error", "message": "No content provided by LLM brain."}
            payload.update(_ontology_binding(params))
            print(json.dumps(payload, ensure_ascii=False))
            return

        # 纯 I/O 职责：物理落地到用户工作区，而非技能包所在目录
        project_root = framework_paths.workspace_root()
        output_path = project_root / f"docs/functional/{target}_v19_functional.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_path.write_text(full_markdown_content, encoding='utf-8')

        payload = {
            "status": "success",
            "message": f"I/O successfully performed. Masterpiece written to {output_path.name}"
        }
        payload.update(_ontology_binding(params))
        print(json.dumps(payload, ensure_ascii=False))

    except Exception as e:
        payload = {"status": "error", "message": str(e)}
        payload.update(_ontology_binding(params))
        print(json.dumps(payload, ensure_ascii=False))

if __name__ == "__main__":
    main()
