#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Capability Twin 3.5 - High-Value Knowledge Crawler
Continuous mining with 'Human Insight' focus and skip logic.
"""

import sys, os, json, logging
from pathlib import Path
from datetime import datetime

# Standard framework paths
PROJECT_ROOT = Path("/Users/jeffery/odoo19-study")
sys.path.append(str(PROJECT_ROOT / "CAPABILITY_TWIN/scripts"))
sys.path.append(str(PROJECT_ROOT / "CAPABILITY_TWIN/skills/capability-twin-orchestrator/scripts"))

try:
    from config import CapabilityTwinConfig
    from main import execute_skill
except ImportError:
    print("Error: Framework components not found.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContinuousMiner:
    def __init__(self):
        self.config = CapabilityTwinConfig()
        self.kb_mem = self.config.get_kb_path()
        self.status_file = self.kb_mem / "mining_status.jsonl"
        self.source_path = self.config.get_odoo_source_path()

    def get_mined_set(self):
        """Read set of already successfully mined modules."""
        mined = set()
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry.get("status") == "completed":
                            mined.add(entry.get("module"))
        return mined

    def mark_status(self, module, status):
        with open(self.status_file, 'a') as f:
            f.write(json.dumps({"module": module, "status": status, "ts": datetime.now().isoformat()}) + "\n")

    def run(self, limit=10):
        mined_set = self.get_mined_set()
        
        # 1. Discover all modules
        all_modules = []
        for p in [self.source_path / "addons", self.source_path / "odoo/addons"]:
            if p.exists():
                all_modules.extend([d.name for d in p.iterdir() if d.is_dir() and (d / "__manifest__.py").exists()])
        
        # 2. Priority Sort (Business Core first)
        priority_prefixes = ['stock', 'mrp', 'sale', 'purchase', 'account', 'product']
        all_modules.sort(key=lambda x: (not any(x.startswith(p) for p in priority_prefixes), x))

        count = 0
        for module in all_modules:
            if count >= limit: break
            if module in mined_set: continue

            logger.info(f"🚀 Starting High-Insight Mining: {module}")
            
            # Trigger 6+3.5+4+N Workflow
            params = {
                "target_module": module,
                "workflow_type": "full_analysis",
                "detail_level": "comprehensive",
                "instruction_focus": "HUMAN_INSIGHT_FIRST" # Tell Agents to focus on business value
            }
            
            try:
                result = execute_skill(params)
                if result.get("status") == "completed":
                    self.mark_status(module, "completed")
                    logger.info(f"✅ Mined {module}. Insight stored in kb/mem/.")
                    count += 1
                else:
                    self.mark_status(module, "failed")
            except Exception as e:
                logger.error(f"❌ Error mining {module}: {e}")
                self.mark_status(module, "error")

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    ContinuousMiner().run(limit=limit)