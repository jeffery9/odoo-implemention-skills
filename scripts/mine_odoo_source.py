#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Capability Twin 3.5 - High-Value Knowledge Crawler (Parallel Mesh Edition)
Continuous mining with 'Human Insight' focus, thread-safe logging, and parallel execution.
"""

import sys, os, json, logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 按本文件定位框架：不假设仓库目录名、不依赖 CWD。
# 早期版本以上级目录为锚点、并把仓库目录名直接拼进路径，换目录名或改用 worktree 即失效。
REPO_ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATOR_SCRIPTS = REPO_ROOT / "skills" / "capability-twin-orchestrator" / "scripts"
sys.path.insert(0, str(ORCHESTRATOR_SCRIPTS))

try:
    import framework_paths
    from config import CapabilityTwinConfig
    from main import execute_skill
except ImportError as exc:
    print(f"Error: Framework components not found under {ORCHESTRATOR_SCRIPTS} ({exc}).")
    sys.exit(1)


def odoo_source_path() -> Path:
    """Odoo 源码根目录。只认 ODOO_SOURCE_PATH，不提供任何写死的默认值。"""
    raw = (os.environ.get("ODOO_SOURCE_PATH") or "").strip()
    if not raw:
        raise SystemExit(
            "ODOO_SOURCE_PATH 未设置：请指向 Odoo 源码根目录"
            "（该目录下应包含 odoo/addons 或 addons）。"
        )
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"ODOO_SOURCE_PATH 指向的目录不存在: {path}")
    return path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContinuousMiner:
    def __init__(self):
        self.config = CapabilityTwinConfig()
        # 记忆写入用户工作区（CAPABILITY_TWIN_WORKSPACE 或 CWD），与技能安装位置无关
        self.kb_mem = framework_paths.workspace_root() / "kb" / "mem"
        self.status_file = self.kb_mem / "mining_status.jsonl"
        self.source_path = odoo_source_path()
        self.lock = threading.Lock()

    def get_mined_set(self):
        """Thread-safe read set of already successfully mined modules."""
        mined = set()
        with self.lock:
            if self.status_file.exists():
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            if entry.get("status") == "completed":
                                mined.add(entry.get("module"))
        return mined

    def mark_status(self, module, status):
        """Thread-safe append status to status log."""
        with self.lock:
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.status_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"module": module, "status": status, "ts": datetime.now().isoformat()}) + "\n")

    def _mine_module(self, module):
        """Task executor for mining a single Odoo module."""
        logger.info(f"🚀 Starting High-Insight Parallel Mining: {module}")
        
        # Trigger 6+3.5+4+N Workflow
        params = {
            "target_module": module,
            "workflow_type": "full_analysis",
            "detail_level": "comprehensive",
            "instruction_focus": "HUMAN_INSIGHT_FIRST" # Focus on industrial & financial compliance
        }
        
        try:
            result = execute_skill(params)
            if result and result.get("status") == "completed":
                self.mark_status(module, "completed")
                logger.info(f"✅ Successfully mined {module}. Insight stored in kb/mem/.")
                return module, "completed"
            else:
                self.mark_status(module, "failed")
                logger.warning(f"⚠️ Mining failed for {module}")
                return module, "failed"
        except Exception as e:
            logger.error(f"❌ Exception occurred during mining of {module}: {e}")
            self.mark_status(module, "error")
            return module, "error"

    def run(self, limit=5, max_workers=4):
        mined_set = self.get_mined_set()
        
        # 1. Discover all modules
        all_modules = []
        for p in [self.source_path / "addons", self.source_path / "odoo/addons"]:
            if p.exists():
                all_modules.extend([d.name for d in p.iterdir() if d.is_dir() and (d / "__manifest__.py").exists()])
        
        # 2. Priority Sort (Business Core first)
        priority_prefixes = ['stock', 'mrp', 'sale', 'purchase', 'account', 'product']
        all_modules.sort(key=lambda x: (not any(x.startswith(p) for p in priority_prefixes), x))

        # Filter modules that need mining
        modules_to_mine = [m for m in all_modules if m not in mined_set][:limit]
        
        if not modules_to_mine:
            logger.info("🎉 All discovered Odoo modules are already mined and up-to-date!")
            return

        logger.info(f"🌐 Initiating Parallel Agentic Mesh mining for {len(modules_to_mine)} modules with {max_workers} threads...")

        # 3. Parallel Execution via ThreadPoolExecutor
        completed_count = 0
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AgentMesh") as executor:
            future_to_module = {executor.submit(self._mine_module, m): m for m in modules_to_mine}
            for future in as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    mod, status = future.result()
                    if status == "completed":
                        completed_count += 1
                except Exception as exc:
                    logger.error(f"❌ Thread execution for {module} generated an exception: {exc}")

        logger.info(f"📊 Parallel mining session concluded: {completed_count}/{len(modules_to_mine)} modules successfully completed.")

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    ContinuousMiner().run(limit=limit, max_workers=workers)
