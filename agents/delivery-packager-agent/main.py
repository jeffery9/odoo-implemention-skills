#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys
from pathlib import Path

def main():
    if len(sys.argv) < 2: return
    try:
        params = json.loads(sys.argv[1])
        target = params.get("target_module") or params.get("config", {}).get("target_module")
        # 直接获取 LLM 产出的完整 Markdown 内容
        full_markdown_content = params.get("full_markdown_content") or params.get("config", {}).get("full_markdown_content")
        
        if not full_markdown_content:
            print(json.dumps({"status": "error", "message": "No content provided by LLM brain."}))
            return

        # 纯 I/O 职责：物理落地
        project_root = Path(__file__).resolve().parents[2]
        output_path = project_root / f"docs/functional/{target}_v19_functional.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_path.write_text(full_markdown_content, encoding='utf-8')

        print(json.dumps({
            "status": "success", 
            "message": f"I/O successfully performed. Masterpiece written to {output_path.name}"
        }, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()
