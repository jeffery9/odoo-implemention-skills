#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration script to move legacy Capability Twin knowledge into the new JSONL memory system.
"""

import json
import os
from pathlib import Path
from datetime import datetime

# 历史资产位于仓库根，脚本统一收口在 scripts/ 下，故回退一级到仓库根。
# 用 parent（脚本自身目录）会错误指向 scripts/，worktree 下还会指到框架之外。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_MEM_DIR = PROJECT_ROOT / "kb" / "mem"
FACTS_FILE = KB_MEM_DIR / "long_term_facts.jsonl"
PATTERNS_FILE = KB_MEM_DIR / "usage_patterns.jsonl"

def append_to_jsonl(file_path, key, value, metadata):
    entry = {
        "key": key,
        "value": value,
        "metadata": metadata,
        "timestamp": datetime.now().isoformat(),
        "migration_source": "legacy_v2"
    }
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def migrate_capability_units_project():
    legacy_file = PROJECT_ROOT / "capability_units_project.json"
    if not legacy_file.exists():
        print("Legacy capability_units_project.json not found.")
        return

    print(f"Migrating {legacy_file}...")
    try:
        with open(legacy_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        units = data.get("capability_units", [])
        for unit in units:
            unit_id = unit.get("id")
            module = unit.get("metadata", {}).get("module", data.get("module", "unknown"))
            append_to_jsonl(FACTS_FILE, unit_id, unit, {"module": module, "type": "capability_unit"})
        print(f"  Successfully migrated {len(units)} units from project file.")
    except Exception as e:
        print(f"  Error migrating project file: {e}")

def migrate_module_specific_kb():
    modules_dir = PROJECT_ROOT / "kb" / "modules"
    if not modules_dir.exists():
        return

    print("Scanning kb/modules/ for legacy results...")
    for module_dir in modules_dir.iterdir():
        if module_dir.is_dir():
            module_name = module_dir.name
            
            # 1. Migrate capability_units.json
            cap_file = module_dir / "capability_units.json"
            if cap_file.exists():
                try:
                    with open(cap_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Could be a list or a dict with a list
                        units = data if isinstance(data, list) else data.get("capability_units", [])
                        for unit in units:
                            unit_id = unit.get("id", f"{module_name}_{datetime.now().timestamp()}")
                            append_to_jsonl(FACTS_FILE, unit_id, unit, {"module": module_name, "type": "capability_unit"})
                    print(f"  Migrated capability units for {module_name}")
                except Exception as e:
                    print(f"  Error in {cap_file}: {e}")

            # 2. Migrate technical_analysis.json as usage patterns
            tech_file = module_dir / "technical_analysis.json"
            if tech_file.exists():
                try:
                    with open(tech_file, 'r', encoding='utf-8') as f:
                        tech_data = json.load(f)
                        append_to_jsonl(PATTERNS_FILE, f"{module_name}_technical_patterns", tech_data, {"module": module_name, "type": "technical_patterns"})
                    print(f"  Migrated technical patterns for {module_name}")
                except Exception as e:
                    print(f"  Error in {tech_file}: {e}")

def main():
    KB_MEM_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Starting Legacy Knowledge Migration to kb/mem/...")
    migrate_capability_units_project()
    migrate_module_specific_kb()
    print("Migration Complete.")

if __name__ == "__main__":
    main()
