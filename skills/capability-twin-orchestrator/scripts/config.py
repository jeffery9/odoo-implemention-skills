#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration module for Capability Twin framework
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CapabilityTwinConfig:
    """
    Configuration for the Capability Twin framework
    """
    # Using script location as anchor to find project root
    _project_root: Path = Path(__file__).parent.parent.parent.parent.parent.absolute()

    # Registry configuration
    registry_path: str = str(_project_root / "CAPABILITY_TWIN/skills/capability-twin-orchestrator/capability_registry.json")

    # Odoo Source Code Path (Crucial for knowledge mining)
    odoo_source_path: str = os.getenv("ODOO_SOURCE_PATH", "/Users/jeffery/_project/topdon/EUx/odoo-19.0")

    # Knowledge Base Path (Persistent storage)
    knowledge_base_path: str = "kb/mem"

    # Artifacts and Deliverables (Outside the framework directory)
    solutions_directory: str = "Complete_Solution"
    deliverables_directory: str = "Deliverables_Package"
    runs_directory: str = "capability_twin_runs"

    # File tracking configuration
    file_tracking_enabled: bool = True

    # Performance configuration
    max_concurrent_agents: int = 1
    result_truncation_limit: int = 2000  # Increased for more detail

    # Error handling configuration
    allow_partial_completion: bool = True
    enable_backup_files: bool = True

    # Security configuration
    validate_module_names: bool = True
    allowed_module_pattern: str = r'^[a-zA-Z_][a-zA-Z0-9_]*$'

    def get_output_path(self) -> Path:
        """Get the base output directory (capability_twin_runs) in project root"""
        path = self._project_root / self.runs_directory
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_registry_path(self) -> Path:
        """Get the registry file path"""
        return Path(self.registry_path)

    def get_odoo_source_path(self) -> Path:
        """Get the Odoo source code path"""
        return Path(self.odoo_source_path)

    def get_kb_path(self) -> Path:
        """Get the knowledge base path in project root"""
        path = self._project_root / self.knowledge_base_path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_solutions_path(self) -> Path:
        """Get the Complete_Solution directory path in project root"""
        path = self._project_root / self.solutions_directory
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_deliverables_path(self) -> Path:
        """Get the Deliverables_Package directory path in project root"""
        path = self._project_root / self.deliverables_directory
        path.mkdir(parents=True, exist_ok=True)
        return path
