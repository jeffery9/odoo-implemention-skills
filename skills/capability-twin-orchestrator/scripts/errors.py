#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Error handling module for Capability Twin framework
"""

from typing import Dict, Any, Optional
from enum import Enum
import logging


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CapabilityTwinError(Exception):
    """Base exception for Capability Twin framework"""

    def __init__(self,
                 message: str,
                 context: Optional[Dict[str, Any]] = None,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.severity = severity

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization"""
        return {
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "type": self.__class__.__name__
        }


class WorkflowError(CapabilityTwinError):
    """Error in workflow execution"""
    pass


class ConfigurationError(CapabilityTwinError):
    """Error in configuration"""
    pass


class FileOperationError(CapabilityTwinError):
    """Error in file operations"""
    pass


class CapabilityRegistryError(CapabilityTwinError):
    """Error in capability registry operations"""
    pass


class ErrorHandler:
    """Centralized error handler for the framework"""

    @staticmethod
    def log_error(error: CapabilityTwinError, logger: logging.Logger) -> None:
        """Log error with appropriate level based on severity"""
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error.message}", extra=error.context)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error.message}", extra=error.context)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error.message}", extra=error.context)
        else:
            logger.info(f"Low severity error: {error.message}", extra=error.context)

    @staticmethod
    def handle_workflow_step_error(step_name: str,
                                  error: Exception,
                                  allow_partial_completion: bool = True) -> Dict[str, Any]:
        """
        Handle errors in workflow steps

        Args:
            step_name: Name of the step that failed
            error: The error that occurred
            allow_partial_completion: Whether to continue workflow after error

        Returns:
            Error result dictionary
        """
        error_result = {
            "step": step_name,
            "status": "error",
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "allow_partial_completion": allow_partial_completion
        }

        if allow_partial_completion:
            error_result["result"] = f"Step {step_name} failed but workflow can continue"
        else:
            error_result["result"] = f"Step {step_name} failed and workflow cannot continue"

        return error_result