#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Capability Registry module for Capability Twin framework
Manages the registration, discovery, and execution of capability units (agents and skills)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """
    Registry for managing capability units (agents, skills, and other executable components)
    """

    def __init__(self, registry_path: Path, create_if_missing: bool = False):
        """
        Initialize the capability registry

        Args:
            registry_path: 注册表文件路径
            create_if_missing: 仅当显式要求时才允许创建空注册表。
                默认 False —— 文件缺失应视为配置错误并抛错，
                避免「在错误目录启动 → 静默生成空表 → 所有能力查不到」的假绿。
        """
        self.registry_path = Path(registry_path)
        self.create_if_missing = create_if_missing
        self.capabilities = {}

        # 注册表中的路径以「技能容器根」为基准（形如 `<skill>/agents/xxx` 或 `<skill>`），
        # 容器在仓库布局下是 `skills/`，在安装布局下是 `.claude/skills/`，
        # 因此这里锚定到注册表所在技能目录的父目录，而不是固定深度的仓库根。
        try:
            self.base_dir = self.registry_path.resolve().parents[1]
        except (IndexError, OSError):
            self.base_dir = Path(__file__).resolve().parents[2]

        # Load existing registry or create new one
        self._load_registry()

    def _resolve_path(self, raw_path: str) -> Path:
        """把注册表中的路径解析为绝对路径（兼容历史绝对路径与相对路径）"""
        p = Path(raw_path)
        return p if p.is_absolute() else (self.base_dir / p)

    def _load_registry(self):
        """
        Load the capability registry from file
        """
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.capabilities = json.load(f)
                logger.info(f"Loaded capability registry from {self.registry_path}")
                return
            except Exception as e:
                logger.error(f"Error loading capability registry: {e}")
                self.capabilities = {}
                return

        if not self.create_if_missing:
            raise FileNotFoundError(
                f"Capability registry not found: {self.registry_path}. "
                "运行 discover_capabilities.py 重建注册表，或显式传入 create_if_missing=True。"
            )

        # Create default registry structure (explicit opt-in only)
        self.capabilities = {
            "agents": {},
            "skills": {},
            "capabilities": {}
        }
        self._save_registry()
        logger.info(f"Created new capability registry at {self.registry_path}")

    def _save_registry(self):
        """
        Save the capability registry to file
        """
        try:
            # Ensure parent directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.capabilities, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved capability registry to {self.registry_path}")
        except Exception as e:
            logger.error(f"Error saving capability registry: {e}")
            raise

    def register_capability(self, capability_type: str, name: str, metadata: Dict[str, Any]):
        """
        Register a new capability
        """
        if capability_type not in self.capabilities:
            self.capabilities[capability_type] = {}

        self.capabilities[capability_type][name] = {
            **metadata,
            "registered_at": self._get_timestamp(),
            "capability_id": f"{capability_type}:{name}"
        }

        self._save_registry()
        logger.info(f"Registered {capability_type} capability: {name}")

    def get_capability(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a capability by name from any category
        """
        for category, capabilities in self.capabilities.items():
            if name in capabilities:
                return capabilities[name]

        logger.warning(f"Capability not found: {name}")
        return None

    def list_capabilities(self, capability_type: Optional[str] = None) -> Dict[str, Any]:
        """
        List all capabilities, optionally filtered by type
        """
        if capability_type:
            return self.capabilities.get(capability_type, {})
        else:
            return self.capabilities

    def execute_capability(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a capability with given parameters.
        Tries to find a Python entry point (main.py) or returns a structured instruction for the orchestrator.
        """
        capability = self.get_capability(name)

        if not capability:
            logger.warning(f"Capability {name} not found in registry.")
            return {
                "status": "error",
                "message": f"Capability {name} not found",
                "timestamp": self._get_timestamp()
            }

        capability_path = self._resolve_path(capability.get("path", ""))
        main_py = capability_path / "main.py"
        if not main_py.exists():
            main_py = capability_path / "scripts" / "main.py"

        # If it's a Python-based skill/agent, we can execute it
        if main_py.exists():
            try:
                import subprocess
                import sys

                logger.info(f"Executing Python capability: {name} at {main_py}")
                
                # Prepare environment with necessary paths
                env = os.environ.copy()
                scripts_dir = str(Path(__file__).parent.absolute())
                if 'PYTHONPATH' in env:
                    env['PYTHONPATH'] = f"{scripts_dir}{os.pathsep}{env['PYTHONPATH']}"
                else:
                    env['PYTHONPATH'] = scripts_dir

                # Execute as a subprocess to ensure isolation
                cmd = [sys.executable, str(main_py), json.dumps(params)]
                result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)

                if result.returncode == 0:
                    logger.info(f"Capability {name} stdout: {result.stdout}")
                    try:
                        return json.loads(result.stdout)
                    except json.JSONDecodeError:
                        return {
                            "status": "success",
                            "raw_output": result.stdout,
                            "timestamp": self._get_timestamp()
                        }
                else:
                    logger.error(f"Capability {name} failed with returncode {result.returncode}")
                    logger.error(f"Capability {name} stderr: {result.stderr}")
                    return {
                        "status": "error",
                        "error": result.stderr or "Unknown error during execution",
                        "returncode": result.returncode,
                        "timestamp": self._get_timestamp()
                    }
            except Exception as e:
                logger.error(f"Failed to execute Python capability {name}: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": self._get_timestamp()
                }

        # If it's a Prompt-based Agent (only AGENT.md exists)
        agent_md = capability_path / "AGENT.md"
        if agent_md.exists():
            granted = list(params.get("skills_granted", []) or [])
            unknown = [s for s in granted if s not in self.capabilities.get("skills", {})]
            if unknown:
                logger.warning(
                    f"{name}: skills_granted 含未注册或非技能条目 {unknown}（已透传，但调用方应修正路由表）"
                )
            return {
                "status": "pending_instruction",
                "capability_type": "prompt_agent",
                "instruction_file": str(agent_md),
                "target_module": params.get("target_module"),
                "goal": params.get("goal"),
                # 技能授予必须透传，否则被授予的技能（含 FDE 检查点）永远到不了执行者
                "skills_granted": granted,
                "unknown_skills": unknown,
                "shared_context_keys": sorted((params.get("shared_context") or {}).keys()),
                "workflow_id": params.get("workflow_id"),
                "execution_contract": (
                    "执行前先加载 skills_granted 中每个技能的 SKILL.md 并遵守其约束；"
                    "仅在产出物满足这些技能的检查清单后才可声明本步骤成功；"
                    "无法完成时报 error 并写明缺失的输入或证据，不得返回成功空结果。"
                ),
                "timestamp": self._get_timestamp()
            }

        # 既无 Python 入口也无 AGENT.md：不能假装执行过
        return {
            "status": "unsupported",
            "capability_name": name,
            "capability_type": capability.get("type", "unknown"),
            "parameters": params,
            "error": f"{name} 既无 main.py 也无 AGENT.md，无法执行",
            "timestamp": self._get_timestamp(),
            "workflow_id": params.get("workflow_id", "unknown")
        }

    def _get_timestamp(self) -> str:
        """
        Get current timestamp as string
        """
        from datetime import datetime
        return datetime.now().isoformat()


# Example usage and testing
if __name__ == "__main__":
    # Test the capability registry
    registry = CapabilityRegistry(Path("test_registry.json"), create_if_missing=True)

    # Register some example capabilities
    registry.register_capability("agents", "ecosystem-discovery-agent", {
        "description": "Discovers ecosystem dependencies for a module",
        "type": "agent",
        "version": "1.0.0"
    })

    registry.register_capability("agents", "technical-analysis-agent", {
        "description": "Analyzes technical implementation of a module",
        "type": "agent",
        "version": "1.0.0"
    })

    # Test capability execution
    result = registry.execute_capability("ecosystem-discovery-agent", {
        "target_module": "sale",
        "goal": "discover ecosystem dependencies"
    })

    print("Execution result:", result)

    # List all capabilities
    all_capabilities = registry.list_capabilities()
    print("All capabilities:", json.dumps(all_capabilities, indent=2))