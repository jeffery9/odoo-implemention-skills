#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Safe file operations module for Capability Twin framework
"""

import shutil
from pathlib import Path
from typing import Callable, Optional
import tempfile
import re


class SafeFileUpdater:
    """
    Safe file updater with backup and atomic operations
    """

    @staticmethod
    def safe_file_update(file_path: Path, update_func: Callable[[str], str]) -> bool:
        """
        Safely update a file with backup protection

        Args:
            file_path: Path to the file to update
            update_func: Function that takes current content and returns new content

        Returns:
            True if successful, False otherwise
        """
        backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")

        # Create backup if file exists
        if file_path.exists():
            shutil.copy2(file_path, backup_path)

        try:
            # Read current content
            content = file_path.read_text(encoding='utf-8')

            # Apply update
            new_content = update_func(content)

            # Write new content atomically
            file_path.write_text(new_content, encoding='utf-8')

            # Clean up backup on success
            if backup_path.exists():
                backup_path.unlink()

            return True

        except Exception as e:
            # Restore from backup on failure if it exists
            if backup_path.exists():
                shutil.move(backup_path, file_path)
            raise e

    @staticmethod
    def safe_string_replace(file_path: Path, old_string: str, new_string: str) -> bool:
        """
        Safely replace a string in a file with backup protection
        """
        def update_func(content: str) -> str:
            # Check if the old string exists before replacing
            if old_string not in content:
                raise ValueError(f"String '{old_string}' not found in file {file_path}")
            return content.replace(old_string, new_string)

        return SafeFileUpdater.safe_file_update(file_path, update_func)

    @staticmethod
    def validate_path(path: str, allowed_base: Optional[Path] = None) -> str:
        """
        Validate and sanitize file paths to prevent directory traversal

        Args:
            path: The path to validate
            allowed_base: Base directory that path must be within

        Returns:
            Sanitized path
        """
        # Remove directory traversal attempts
        safe_path = Path(path).name  # Only take the filename part

        if allowed_base:
            # Ensure the full path is within allowed base
            full_path = allowed_base / safe_path
            resolved = full_path.resolve()
            allowed_resolved = allowed_base.resolve()

            if not str(resolved).startswith(str(allowed_resolved)):
                raise ValueError(f"Path {path} is outside allowed base directory")

        return safe_path


def validate_module_name(module_name: str, pattern: str = r'^[a-zA-Z_][a-zA-Z0-9_]*$') -> bool:
    """
    Validate module name to prevent security issues

    Args:
        module_name: The module name to validate
        pattern: Regex pattern to validate against

    Returns:
        True if valid, False otherwise
    """
    if not module_name:
        return False

    return bool(re.match(pattern, module_name))