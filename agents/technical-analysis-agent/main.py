#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys
from pathlib import Path

def main():
    if len(sys.argv) < 2: return
    try:
        params = json.loads(sys.argv[1])
        target_module = params.get("target_module") or params.get("config", {}).get("target_module")
        source_root_str = os.environ.get("ODOO_SOURCE_PATH")
        
        if not source_root_str:
            print(json.dumps({"status": "error", "message": "ODOO_SOURCE_PATH environment variable not set"}))
            return
        
        source_root = Path(source_root_str)
        project_root = Path(__file__).resolve().parents[3]
        shard_dir = project_root / "kb/shards"
        shard_dir.mkdir(parents=True, exist_ok=True)
        
        # 物理清理旧分片
        for f in shard_dir.glob("*.json"): f.unlink()

        shards = []
        current_shard_data = {}
        current_size = 0
        shard_index = 1
        
        # 全域扫描目录
        search_dirs = ["models", "wizard", "report", "views", "tests"]
        
        module_path = next((p for p in [source_root/"addons"/target_module, source_root/"odoo"/"addons"/target_module] if p.exists()), None)
        if not module_path:
            print(json.dumps({"status": "error", "message": f"Module {target_module} not found"}))
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

        print(json.dumps({
            "status": "success",
            "shards": shards,
            "total_files": len(all_files),
            "instruction": "LLM: ALL physical evidence is sharded. You must digest every shard to maintain the no-loss mandate."
        }, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()