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
        target_module = params.get("target_module") or params.get("config", {}).get("target_module")
        source_root_str = os.environ.get("ODOO_SOURCE_PATH")
        
        if not source_root_str:
            payload = {"status": "error", "message": "ODOO_SOURCE_PATH environment variable not set"}
            payload.update(_ontology_binding(params))
            print(json.dumps(payload, ensure_ascii=False))
            return
        
        source_root = Path(source_root_str)
        # 分片是运行时产物，写用户工作区；不能写进技能包（安装态为只读副本）
        project_root = framework_paths.workspace_root()
        # 按模块分目录，避免与其它模块的分片互相覆盖/误删
        shard_dir = project_root / "kb/shards" / target_module
        shard_dir.mkdir(parents=True, exist_ok=True)
        
        # 只清理本模块的旧分片（保持幂等，不影响其它模块）
        for f in shard_dir.glob("*.json"): f.unlink()

        shards = []
        current_shard_data = {}
        current_size = 0
        shard_index = 1
        
        # 全域扫描目录
        search_dirs = ["models", "wizard", "report", "views", "tests"]
        
        module_path = next((p for p in [source_root/"addons"/target_module, source_root/"odoo"/"addons"/target_module] if p.exists()), None)
        if not module_path:
            payload = {"status": "error", "message": f"Module {target_module} not found"}
            payload.update(_ontology_binding(params))
            print(json.dumps(payload, ensure_ascii=False))
            return

        # 递归抓取所有代码与配置证据
        all_files = []
        for sdir in search_dirs:
            p = module_path / sdir
            if p.exists():
                all_files.extend(list(p.rglob("*.py")) + list(p.rglob("*.xml")))

        for f_path in all_files:
            try:
                rel_path = f_path.relative_to(module_path)
                content = f_path.read_text(encoding='utf-8', errors='ignore')
                current_shard_data[str(rel_path)] = content
                current_size += len(content)
                
                # 分片阈值 40KB (最佳上下文密度)
                if current_size > 40000:
                    s_file = shard_dir / f"shard_{shard_index}.json"
                    s_file.write_text(json.dumps(current_shard_data), encoding='utf-8')
                    shards.append(str(s_file))
                    current_shard_data = {}
                    current_size = 0
                    shard_index += 1
            except: continue

        if current_shard_data:
            s_file = shard_dir / f"shard_{shard_index}.json"
            s_file.write_text(json.dumps(current_shard_data), encoding='utf-8')
            shards.append(str(s_file))

        payload = {
            "status": "success",
            "shards": shards,
            "total_files": len(all_files),
            "instruction": "LLM: ALL physical evidence is sharded. You must digest every shard to maintain the no-loss mandate."
        }
        payload.update(_ontology_binding(params))
        print(json.dumps(payload, ensure_ascii=False))

    except Exception as e:
        payload = {"status": "error", "message": str(e)}
        payload.update(_ontology_binding(params))
        print(json.dumps(payload, ensure_ascii=False))

if __name__ == "__main__":
    main()