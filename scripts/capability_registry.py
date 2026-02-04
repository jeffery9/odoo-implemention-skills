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

    def __init__(self, registry_path: Path):
        """
        Initialize the capability registry
        """
        self.registry_path = Path(registry_path)
        self.capabilities = {}

        # Load existing registry or create new one
        self._load_registry()

    def _load_registry(self):
        """
        Load the capability registry from file
        """
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.capabilities = json.load(f)
                logger.info(f"Loaded capability registry from {self.registry_path}")
            except Exception as e:
                logger.error(f"Error loading capability registry: {e}")
                self.capabilities = {}
        else:
            # Create default registry structure
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

        capability_path = Path(capability.get("path", ""))
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
            return {
                "status": "pending_instruction",
                "capability_type": "prompt_agent",
                "instruction_file": str(agent_md),
                "target_module": params.get("target_module"),
                "goal": params.get("goal"),
                "timestamp": self._get_timestamp()
            }

        return {
            "status": "executed",
            "capability_name": name,
            "capability_type": capability.get("type", "unknown"),
            "parameters": params,
            "result": f"Executed {name} (Metadata only)",
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
    registry = CapabilityRegistry(Path("test_registry.json"))

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