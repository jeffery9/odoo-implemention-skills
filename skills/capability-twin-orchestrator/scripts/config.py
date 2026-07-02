#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration module for Capability Twin framework
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CapabilityTwinConfig:
    """
    Configuration for the Capability Twin framework
    """
    # Registry configuration
    registry_path: str = "capability_registry.json"

    # File tracking configuration
    output_directory: str = "capability_twin_runs"
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