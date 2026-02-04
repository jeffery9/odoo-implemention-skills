#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys, time, logging, subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("capability-twin-orchestrator")

class CapabilityTwinOrchestrator:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.shared_context = {
            "workflow_id": f"cto_{time.strftime('%Y%m%d_%H%M%S')}",
            "matured_knowledge": [], # 滑动窗口积累的智慧
            "results": []
        }

    def execute_subagent(self, agent_type, goal, config):
        agent_path = self.project_root / f"CAPABILITY_TWIN/agents/{agent_type}/main.py"
        input_data = json.dumps({
            "goal": goal, 
            "config": config, 
            "shared_context": self.shared_context
        })
        result = subprocess.run([sys.executable, str(agent_path), input_data], capture_output=True, text=True)
        try:
            return json.loads(result.stdout)
        except:
            return {"status": "error", "message": result.stderr}

    def run_full_audit(self, target_module):
        logger.info(f"🚀 Starting v18.0 Full Evidence Audit: {target_module}")
        
        # 1. 物理分片搬运
        tech_res = self.execute_subagent("technical-analysis-agent", "Ingest all evidence", {"target_module": target_module})
        shards = tech_res.get("shards", [])
        
        # 2. 滑动窗口采矿循环
        for i, shard_path in enumerate(shards):
            logger.info(f"🧠 Digging Shard {i+1}/{len(shards)}...")
            # 物理模拟：每一轮 LLM 消化分片产生 Facts
            # 在实际工程中，这里会由 LLM 驱动分片读取
            # 我们将分片路径存入 context，由 LLM 最终阶段全量读取
            self.shared_context["matured_knowledge"].append({
                "shard": shard_path,
                "status": "ingested"
            })

        # 3. 终极合成 (Master Synthesis)
        # 此步骤将引导 LLM 读取 accumulated shards 产出 600行+ 的内容
        logger.info("🎬 Evidence pipeline complete. Ready for LLM Synthesis.")
        return {"status": "success", "snapshot_id": self.shared_context["workflow_id"]}

def execute_skill(params):
    orchestrator = CapabilityTwinOrchestrator()
    return orchestrator.run_full_audit(params.get("target_module"))