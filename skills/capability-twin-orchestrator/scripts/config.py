#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration module for Capability Twin framework
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# 路径锚定到本文件，避免依赖进程工作目录（CWD）。
# config.py 位于 <repo>/skills/capability-twin-orchestrator/scripts/
_SKILL_ROOT = Path(__file__).resolve().parents[1]
_FRAMEWORK_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class CapabilityTwinConfig:
    """
    Configuration for the Capability Twin framework
    """
    # Registry configuration（默认指向仓内真实注册表，不随 CWD 漂移）
    registry_path: str = str(_SKILL_ROOT / "capability_registry.json")

    # File tracking configuration（默认落在框架根目录，避免污染调用方 CWD）
    output_directory: str = str(_FRAMEWORK_ROOT / "capability_twin_runs")
    file_tracking_enabled: bool = True

    # Performance configuration
    max_concurrent_agents: int = 1  # For now, keeping it sync until async is implemented
    result_truncation_limit: int = 500  # Characters to truncate results

    # Error handling configuration
    allow_partial_completion: bool = True  # Continue workflow even if some steps fail
    enable_backup_files: bool = True

    # Security configuration
    validate_module_names: bool = True
    allowed_module_pattern: str = r'^[a-zA-Z_][a-zA-Z0-9_]*$'

    def get_output_path(self) -> Path:
        """Get the base output directory path"""
        return Path(self.output_directory)

    def get_registry_path(self) -> Path:
        """Get the registry file path"""
        return Path(self.registry_path)