#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration module for Capability Twin framework
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import framework_paths

# 路径锚定到本文件，避免依赖进程工作目录（CWD）。
# 结构不变量为 `<容器>/<技能>/scripts/`，容器可能是仓库根的 skills/，
# 也可能是安装后的 .claude/skills/ —— 两种布局由 framework_paths 统一推导。
_SKILL_ROOT = framework_paths.SKILL_ROOT
_FRAMEWORK_ROOT = framework_paths.FRAMEWORK_ROOT


@dataclass
class CapabilityTwinConfig:
    """
    Configuration for the Capability Twin framework
    """
    # Registry configuration（默认指向仓内真实注册表，不随 CWD 漂移）
    registry_path: str = str(_SKILL_ROOT / "capability_registry.json")

    # File tracking configuration（产物恒写用户工作区，不污染技能包）
    # 用 default_factory 而非直接赋值：产物目录依赖 CWD，
    # 写成类属性会在导入时冻结，调用方 chdir 后仍写回导入位置。
    output_directory: str = field(default_factory=lambda: str(framework_paths.default_run_dir()))
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