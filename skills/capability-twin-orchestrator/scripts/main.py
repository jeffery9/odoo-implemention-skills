#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Capability Twin Orchestrator Skill
Main process that coordinates sub-agents and skill execution as capability units
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import json
from pathlib import Path
import asyncio
import uuid
import re

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / ".claude/scripts"))

from capability_registry import CapabilityRegistry

# Import new modules
from config import CapabilityTwinConfig
from file_operations import SafeFileUpdater, validate_module_name
from errors import ErrorHandler, WorkflowError, ErrorSeverity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileTracker:
    """
    Helper class to manage file-based tracking following planning-with-files principles
    """

    def __init__(self, workflow_id: str, target_module: str, config: Optional[CapabilityTwinConfig] = None):
        self.config = config or CapabilityTwinConfig()
        self.workflow_id = workflow_id
        self.target_module = target_module

        # Use configurable output directory
        self.base_dir = self.config.get_output_path() / workflow_id
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Create the three core files as per planning-with-files principles
        self.task_plan_path = self.base_dir / "task_plan.md"
        self.notes_path = self.base_dir / "notes.md"
        self.analysis_report_path = self.base_dir / "capability_analysis_report.md"

        # Initialize files
        self._init_files()

    def _init_files(self):
        """Initialize the three core tracking files"""
        # Initialize task_plan.md
        task_plan_content = f"""# Capability Twin Workflow Task Plan: {self.target_module}

## Goal
Analyze the {self.target_module} module using the Capability Twin framework (6+3+4+N workflow)


## Phases
- [ ] Phase 1: Setup and initialization
- [ ] Phase 2: Supply-side analysis (Steps 1-6)
- [ ] Phase 3: Demand-side analysis (Steps 7-9)
- [ ] Phase 4: Capability extraction & quality assurance (Steps 10-13)
- [ ] Phase 5: Results aggregation and delivery

## Key Questions
1. What are the core capabilities of the {self.target_module} module?
2. How does it integrate with other modules?
3. What are the business processes it supports?
4. What improvements or customizations are needed?

## FDE Review Checklist
At the mounted checkpoints (Steps 2, 6, 7, 9, 10, 12, 13 and Customization Step 4),
run the 9-item checklist in skills/fde-methodology/SKILL.md section 5. Record per item:
pass / fail / n/a + evidence. No weighted score, no maturity grade, no auto-filled human judgement.
- [ ] FDE review recorded at checkpoints (attached to existing steps, not new phases)

## Decisions Made
- [Decision]: Using workflow ID {self.workflow_id} for tracking

## Errors Encountered
- [None yet]

## Status
**Currently in Phase 1** - Setting up workflow
"""
        self.task_plan_path.write_text(task_plan_content, encoding='utf-8')

        # Initialize notes.md
        notes_content = f"""# Notes: {self.target_module} Analysis

## Analysis of the {self.target_module} module using Capability Twin framework

### Initial Parameters
- Target module: {self.target_module}
- Workflow ID: {self.workflow_id}
- Timestamp: {datetime.now().isoformat()}

## Synthesized Findings

### Initial Observations
- Module name: {self.target_module}

"""
        self.notes_path.write_text(notes_content, encoding='utf-8')

        # Initialize capability_analysis_report.md
        report_content = f"""# Capability Twin Analysis Report: {self.target_module}

## Overview
Capability Twin analysis of the {self.target_module} module using the 6+3+4+N workflow framework.

- Workflow ID: {self.workflow_id}
- Analysis date: {datetime.now().isoformat()}

## Analysis Framework Applied
- 5-Layer Enterprise Architecture Analysis
- Standardized 6+3+4+N workflow
- Planning-with-files principles for persistent tracking

"""
        self.analysis_report_path.write_text(report_content, encoding='utf-8')

    def update_task_plan_status(self, new_status: str, phase: str = None):
        """Update the status section in task_plan.md"""
        def update_func(content: str) -> str:
            if phase:
                content = content.replace(f"**Currently in Phase 1** - Setting up workflow",
                                        f"**Currently in {phase}** - {new_status}")
            else:
                content = content.replace("## Status\n**Currently in Phase 1** - Setting up workflow",
                                        f"## Status\n**Currently in Phase 1** - {new_status}")
            return content

        SafeFileUpdater.safe_file_update(self.task_plan_path, update_func)

    def update_task_plan_phase(self, phase_number: int, status: str, description: str):
        """Update a specific phase in the task_plan.md"""
        def update_func(content: str) -> str:
            phase_marker = f"Phase {phase_number}:"
            if "[x]" in status or status.lower() in ["completed", "done"]:
                old_phase = f"- [ ] {phase_marker}"
                new_phase = f"- [x] {phase_marker} {description}"
            else:
                old_phase = f"- [x] {phase_marker}"
                new_phase = f"- [ ] {phase_marker} {description}"

            return content.replace(old_phase, new_phase)

        SafeFileUpdater.safe_file_update(self.task_plan_path, update_func)

    def add_notes(self, section: str, content: str):
        """Add content to the notes.md file"""
        def update_func(current_notes: str) -> str:
            new_content = f"\n### {section}\n{content}\n"
            return current_notes + new_content

        SafeFileUpdater.safe_file_update(self.notes_path, update_func)

    def add_to_analysis_report(self, section: str, content: str):
        """Add content to the capability_analysis_report.md"""
        def update_func(current_report: str) -> str:
            new_content = f"\n## {section}\n{content}\n"
            return current_report + new_content

        SafeFileUpdater.safe_file_update(self.analysis_report_path, update_func)

    def log_error(self, error_msg: str):
        """Log an error to the task_plan.md file"""
        def update_func(content: str) -> str:
            error_entry = f"- [{datetime.now().isoformat()}] {error_msg}"
            return content.replace("## Errors Encountered\n- [None yet]",
                                 f"## Errors Encountered\n{error_entry}")

        SafeFileUpdater.safe_file_update(self.task_plan_path, update_func)

    def read_task_plan(self):
        """Read the current task plan for attention refresh"""
        return self.task_plan_path.read_text(encoding='utf-8')

class CapabilityTwinOrchestratorSkill:
    """
    Main orchestrator skill that coordinates sub-agents and manages skill execution
    """

    def __init__(self, config: Optional[CapabilityTwinConfig] = None):
        self.config = config or CapabilityTwinConfig()
        self.capability_registry = CapabilityRegistry(self.config.get_registry_path())
        self.workflow_id = f"cto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.shared_context = {}
        self.subagent_results = {}
        self.workflow_history = []
        self.file_tracker = None  # Initialize file tracker to None, will be set later

    def execute_workflow(self, workflow_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the main workflow with sub-agent coordination
        """
        try:
            logger.info(f"Starting Capability Twin workflow: {workflow_params.get('workflow_type', 'unknown')}")

            # Validate target module name if validation is enabled
            target_module = workflow_params.get("target_module", "{target_module}")
            if self.config.validate_module_names and not validate_module_name(target_module, self.config.allowed_module_pattern):
                raise WorkflowError(
                    f"Invalid module name: {target_module}",
                    context={"module_name": target_module},
                    severity=ErrorSeverity.HIGH
                )

            # Initialize file tracker following planning-with-files principle
            self.file_tracker = FileTracker(self.workflow_id, target_module, self.config)

            # Initialize shared context
            self.shared_context = {
                "workflow_id": self.workflow_id,
                "target_module": target_module,
                "workflow_type": workflow_params.get("workflow_type", "full_analysis"),
                "detail_level": workflow_params.get("detail_level", "comprehensive"),
                "timestamp": datetime.now().isoformat(),
                "configuration": {
                    "output_format": workflow_params.get("output_format", "markdown"),
                    "language": "zh"
                },
                "shared_data": {
                    "target_module": target_module,
                    "analysis_scope": ["core", "extensions", "enterprise"]
                },
                "previous_results": {},
                "knowledge_base": {},
                "context_sharing": workflow_params.get("context_sharing", {})
            }

            # Log workflow start
            self.workflow_history.append({
                "type": "workflow_start",
                "workflow_id": self.workflow_id,
                "target_module": self.shared_context["target_module"],
                "workflow_type": self.shared_context["workflow_type"],
                "timestamp": datetime.now().isoformat()
            })

            # Update task plan file to reflect progress
            self.file_tracker.update_task_plan_phase(1, "completed", "Setup and initialization")
            self.file_tracker.update_task_plan_status("Moving to supply-side analysis", "Phase 2")

            # Execute based on workflow type
            workflow_type = workflow_params.get("workflow_type", "full_analysis")

            if workflow_type == "full_analysis":
                result = self.execute_full_analysis_workflow(workflow_params)
            elif workflow_type == "supply_side_analysis":
                result = self.execute_supply_side_analysis(workflow_params)
            elif workflow_type == "demand_side_analysis":
                result = self.execute_demand_side_analysis(workflow_params)
            elif workflow_type == "customization":
                result = self.execute_customization_workflow(workflow_params)
            else:
                result = self.execute_full_analysis_workflow(workflow_params)

            # Finalize workflow
            result["workflow_id"] = self.workflow_id
            result["final_shared_context"] = self.shared_context
            result["workflow_history"] = self.workflow_history

            logger.info(f"Completed Capability Twin workflow: {self.workflow_id}")
            return result

        except Exception as e:
            logger.error(f"Error executing Capability Twin workflow: {e}")
            # Log error to file tracker if it exists
            if self.file_tracker:
                self.file_tracker.log_error(f"Error executing workflow: {str(e)}")

            # Use error handler for consistent error formatting
            error_handler = ErrorHandler()
            error_handler.log_error(
                WorkflowError(str(e), context={"workflow_id": self.workflow_id}, severity=ErrorSeverity.HIGH),
                logger
            )

            return {
                "status": "error",
                "error": str(e),
                "workflow_id": self.workflow_id,
                "timestamp": datetime.now().isoformat()
            }

    def execute_supply_side_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute supply-side analysis with sub-agent coordination
        """
        logger.info(f"Executing supply-side analysis for {params.get('target_module', 'unknown')}")

        # Read task plan before proceeding (Read-Before-Decide pattern)
        if self.file_tracker:
            task_plan_content = self.file_tracker.read_task_plan()
            logger.info(f"Refreshed task plan for supply-side analysis of {params.get('target_module', 'unknown')}")

        # Define workflow steps as sub-agents
        workflow_steps = [
            {
                "step": 1,
                "name": "Ecosystem Discovery",
                "agent_type": "ecosystem-discovery-agent",
                "sub_goal": f"discover ecosystem dependencies for {params.get('target_module')}",
                "skills_granted": ["relationship-analysis", "source-traceability", "generic-analyzer"],
                "config": {
                    "target_module": params.get("target_module"),
                    "include_enterprise": True,
                    "analyze_dependencies": True,
                    "bidirectional_analysis": True,
                    "detail_level": params.get("detail_level", "comprehensive")
                }
            },
            {
                "step": 2,
                "name": "Technical Analysis",
                "agent_type": "technical-analysis-agent",
                "sub_goal": f"analyze technical implementation of {params.get('target_module')}",
                "skills_granted": ["source-traceability", "knowledge-manager", "relationship-analysis", "fde-methodology"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": "deep" if params.get("detail_level") == "comprehensive" else params.get("detail_level"),
                    "include_extensions": True,
                    "focus_areas": ["models", "workflows", "reports", "security"]
                }
            },
            {
                "step": 3,
                "name": "Function Analysis",
                "agent_type": "function-analysis-agent",
                "sub_goal": f"analyze functional capabilities of {params.get('target_module')}",
                "skills_granted": ["generic-analyzer", "knowledge-manager"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            },
            {
                "step": 4,
                "name": "Domain Analysis",
                "agent_type": "domain-analysis-agent",
                "sub_goal": f"analyze domain-specific aspects of {params.get('target_module')}",
                "skills_granted": ["generic-analyzer", "relationship-analysis"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            },
            {
                "step": 5,
                "name": "Business Process Analysis",
                "agent_type": "business-process-agent",
                "sub_goal": f"analyze business processes in {params.get('target_module')}",
                "skills_granted": ["business-process-agent", "relationship-analysis"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            },
            {
                "step": 6,
                "name": "Comprehensive Analysis",
                "agent_type": "comprehensive-analysis-agent",
                "sub_goal": f"synthesize comprehensive view of {params.get('target_module')}",
                "skills_granted": ["generic-analyzer", "knowledge-manager", "relationship-analysis", "fde-methodology"],
                "config": {
                    "target_module": params.get("target_module"),
                    "inputs": [
                        "ecosystem_discovery_report",
                        "technical_analysis_report",
                        "function_analysis_report",
                        "domain_analysis_report",
                        "business_process_analysis_report"
                    ],
                    "analysis_objective": "comprehensive_view",
                    "detail_level": params.get("detail_level")
                }
            }
        ]

        results = []
        for i, step in enumerate(workflow_steps):
            logger.info(f"Executing step {step['step']}: {step['name']}")

            # Update task plan with current step
            if self.file_tracker:
                self.file_tracker.update_task_plan_status(f"Executing {step['name']}", f"Phase 2 - Step {step['step']}")
                self.file_tracker.add_notes(f"Step {step['step']}: {step['name']}", f"Starting execution with goal: {step['sub_goal']}")

            # Execute sub-agent
            subagent_result = self.execute_subagent(
                agent_type=step["agent_type"],
                goal=step["sub_goal"],
                skills_granted=step["skills_granted"],
                config=step["config"]
            )

            # Store result
            self.subagent_results[step["name"]] = subagent_result
            results.append({
                "step": step["step"],
                "name": step["name"],
                "result": subagent_result
            })

            # Update shared context
            self._update_shared_context(step["name"], subagent_result)

            # Add to analysis report
            if self.file_tracker:
                self.file_tracker.add_to_analysis_report(
                    f"Step {step['step']}: {step['name']}",
                    f"Result: {json.dumps(subagent_result, default=str, ensure_ascii=False)[:500]}..."  # Truncate for readability
                )

        # Update task plan after completion
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(2, "completed", "Supply-side analysis (Steps 1-6)")
            self.file_tracker.update_task_plan_status("Moving to demand-side analysis", "Phase 3")

        return {
            "workflow_type": "supply_side_analysis",
            "steps_completed": len(workflow_steps),
            "results": results,
            "status": "completed"
        }

    def execute_demand_side_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute demand-side analysis with sub-agent coordination
        """
        logger.info(f"Executing demand-side analysis for {params.get('target_module', 'unknown')}")

        # Read task plan before proceeding (Read-Before-Decide pattern)
        if self.file_tracker:
            task_plan_content = self.file_tracker.read_task_plan()
            logger.info(f"Refreshed task plan for demand-side analysis of {params.get('target_module', 'unknown')}")

        workflow_steps = [
            {
                "step": 7,
                "name": "Industry Requirements Analysis",
                "agent_type": "industry-requirements-agent",
                "sub_goal": f"analyze industry requirements for {params.get('target_module')}",
                "skills_granted": ["generic-analyzer", "relationship-analysis", "fde-methodology"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            },
            {
                "step": 8,
                "name": "Solution Architecture",
                "agent_type": "solution-architect-agent",
                "sub_goal": f"define solution architecture for {params.get('target_module')}",
                "skills_granted": ["generic-analyzer", "relationship-analysis", "template-processor"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            },
            {
                "step": 9,
                "name": "Implementation Guide Analysis",
                "agent_type": "implementation-guide-agent",
                "sub_goal": f"create implementation guide for {params.get('target_module')}",
                "skills_granted": ["template-processor", "knowledge-manager", "data-exchange", "fde-methodology"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            }
        ]

        results = []
        for step in workflow_steps:
            logger.info(f"Executing step {step['step']}: {step['name']}")

            # Update task plan with current step
            if self.file_tracker:
                self.file_tracker.update_task_plan_status(f"Executing {step['name']}", f"Phase 3 - Step {step['step']}")
                self.file_tracker.add_notes(f"Step {step['step']}: {step['name']}", f"Starting execution with goal: {step['sub_goal']}")

            # Execute sub-agent
            subagent_result = self.execute_subagent(
                agent_type=step["agent_type"],
                goal=step["sub_goal"],
                skills_granted=step["skills_granted"],
                config=step["config"]
            )

            # Store result
            self.subagent_results[step["name"]] = subagent_result
            results.append({
                "step": step["step"],
                "name": step["name"],
                "result": subagent_result
            })

            # Update shared context
            self._update_shared_context(step["name"], subagent_result)

            # Add to analysis report
            if self.file_tracker:
                self.file_tracker.add_to_analysis_report(
                    f"Step {step['step']}: {step['name']}",
                    f"Result: {json.dumps(subagent_result, default=str, ensure_ascii=False)[:500]}..."  # Truncate for readability
                )

        # Update task plan after completion
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(3, "completed", "Demand-side analysis (Steps 7-9)")
            self.file_tracker.update_task_plan_status("Moving to capability extraction", "Phase 4")

        return {
            "workflow_type": "demand_side_analysis",
            "steps_completed": len(workflow_steps),
            "results": results,
            "status": "completed"
        }

    def execute_capability_extraction_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute capability extraction workflow with sub-agent coordination
        """
        logger.info(f"Executing capability extraction for {params.get('target_module', 'unknown')}")

        # Read task plan before proceeding (Read-Before-Decide pattern)
        if self.file_tracker:
            task_plan_content = self.file_tracker.read_task_plan()
            logger.info(f"Refreshed task plan for capability extraction of {params.get('target_module', 'unknown')}")

        workflow_steps = [
            {
                "step": 10,
                "name": "Capability Unit Extraction",
                "agent_type": "capability-extractor-agent",
                "sub_goal": f"extract capability units from {params.get('target_module')} analysis",
                "skills_granted": ["knowledge-manager", "data-exchange", "quality-gate", "fde-methodology"],
                "config": {
                    "target_module": params.get("target_module"),
                    "inputs": ["comprehensive_analysis_report"],
                    "extraction_scope": "full_spectrum",
                    "quality_requirements": ["source_verified", "well_documented"]
                }
            },
            {
                "step": 11,
                "name": "Delivery Packaging",
                "agent_type": "delivery-packager-agent",
                "sub_goal": f"package deliverables for {params.get('target_module')}",
                "skills_granted": ["template-processor", "data-exchange", "knowledge-manager"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            },
            {
                "step": 12,
                "name": "Trustworthiness Audit",
                "agent_type": "trustworthiness-auditor-agent",
                "sub_goal": f"audit trustworthiness of {params.get('target_module')} results",
                "skills_granted": ["quality-gate", "source-traceability", "knowledge-manager", "fde-methodology"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            },
            {
                "step": 13,
                "name": "Human Review Gatekeeper",
                "agent_type": "human-review-gatekeeper-agent",
                "sub_goal": f"perform human review of {params.get('target_module')} results",
                "skills_granted": ["quality-gate", "knowledge-manager", "fde-methodology"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            }
        ]

        results = []
        for step in workflow_steps:
            logger.info(f"Executing step {step['step']}: {step['name']}")

            # Update task plan with current step
            if self.file_tracker:
                self.file_tracker.update_task_plan_status(f"Executing {step['name']}", f"Phase 4 - Step {step['step']}")
                self.file_tracker.add_notes(f"Step {step['step']}: {step['name']}", f"Starting execution with goal: {step['sub_goal']}")

            # Execute sub-agent
            subagent_result = self.execute_subagent(
                agent_type=step["agent_type"],
                goal=step["sub_goal"],
                skills_granted=step["skills_granted"],
                config=step["config"]
            )

            # Store result
            self.subagent_results[step["name"]] = subagent_result
            results.append({
                "step": step["step"],
                "name": step["name"],
                "result": subagent_result
            })

            # Update shared context
            self._update_shared_context(step["name"], subagent_result)

            # Add to analysis report
            if self.file_tracker:
                self.file_tracker.add_to_analysis_report(
                    f"Step {step['step']}: {step['name']}",
                    f"Result: {json.dumps(subagent_result, default=str, ensure_ascii=False)[:500]}..."  # Truncate for readability
                )

        # Update task plan after completion
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(4, "completed", "Capability extraction & quality assurance (Steps 10-13)")
            self.file_tracker.update_task_plan_status("Moving to results aggregation", "Phase 5")

        return {
            "workflow_type": "capability_extraction_workflow",
            "steps_completed": len(workflow_steps),
            "results": results,
            "status": "completed"
        }

    def execute_customization_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute customization workflow with sub-agent coordination
        """
        logger.info(f"Executing customization workflow for {params.get('target_module', 'unknown')}")

        # Read task plan before proceeding (Read-Before-Decide pattern)
        if self.file_tracker:
            task_plan_content = self.file_tracker.read_task_plan()
            logger.info(f"Refreshed task plan for customization workflow of {params.get('target_module', 'unknown')}")

        workflow_steps = [
            {
                "step": 1,
                "name": "Capability Gap Identification",
                "agent_type": "capability-gap-identifier-agent",
                "sub_goal": f"identify capability gaps for requirement: {params.get('requirement', 'custom')}",
                "skills_granted": ["source-traceability", "relationship-analysis", "knowledge-manager"],
                "config": {
                    "requirement": params.get("requirement", "custom_requirement"),
                    "target_module": params.get("target_module")
                }
            },
            {
                "step": 2,
                "name": "Capability Specification Definition",
                "agent_type": "capability-specification-definer-agent",
                "sub_goal": f"define capability specifications for requirement: {params.get('requirement', 'custom')}",
                "skills_granted": ["knowledge-manager", "template-processor", "data-exchange"],
                "config": {
                    "requirement": params.get("requirement", "custom_requirement"),
                    "target_module": params.get("target_module")
                }
            },
            {
                "step": 3,
                "name": "Code Generation",
                "agent_type": "code-autogenerator-agent",
                "sub_goal": f"generate code for requirement: {params.get('requirement', 'custom')}",
                "skills_granted": ["file-operations", "template-processor", "data-exchange"],
                "config": {
                    "requirement": params.get("requirement", "custom_requirement"),
                    "target_module": params.get("target_module")
                }
            },
            {
                "step": 4,
                "name": "Quality Gate and Registration",
                "agent_type": "quality-gate-and-registration-agent",
                "sub_goal": f"perform quality checks and register capability for requirement: {params.get('requirement', 'custom')}",
                "skills_granted": ["quality-gate", "knowledge-manager", "data-exchange", "fde-methodology"],
                "config": {
                    "requirement": params.get("requirement", "custom_requirement"),
                    "target_module": params.get("target_module")
                }
            }
        ]

        results = []
        for step in workflow_steps:
            logger.info(f"Executing customization step {step['step']}: {step['name']}")

            # Update task plan with current step
            if self.file_tracker:
                self.file_tracker.update_task_plan_status(f"Executing {step['name']}", f"Customization - Step {step['step']}")
                self.file_tracker.add_notes(f"Step {step['step']}: {step['name']}", f"Starting execution with goal: {step['sub_goal']}")

            # Execute sub-agent
            subagent_result = self.execute_subagent(
                agent_type=step["agent_type"],
                goal=step["sub_goal"],
                skills_granted=step["skills_granted"],
                config=step["config"]
            )

            # Store result
            self.subagent_results[step["name"]] = subagent_result
            results.append({
                "step": step["step"],
                "name": step["name"],
                "result": subagent_result
            })

            # Update shared context
            self._update_shared_context(step["name"], subagent_result)

            # Add to analysis report
            if self.file_tracker:
                self.file_tracker.add_to_analysis_report(
                    f"Step {step['step']}: {step['name']}",
                    f"Result: {json.dumps(subagent_result, default=str, ensure_ascii=False)[:500]}..."  # Truncate for readability
                )

        # Update task plan after completion
        if self.file_tracker:
            self.file_tracker.update_task_plan_status("Customization workflow completed", "Phase 5")

        return {
            "workflow_type": "customization",
            "requirement": params.get("requirement", "custom_requirement"),
            "target_module": params.get("target_module"),
            "steps_completed": len(workflow_steps),
            "results": results,
            "status": "completed"
        }

    def execute_full_analysis_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full analysis workflow combining all phases
        """
        logger.info("Starting full Capability Twin analysis workflow...")

        # Execute supply-side analysis (steps 1-6)
        supply_results = self.execute_supply_side_analysis(params)

        # Execute demand-side analysis (steps 7-9)
        demand_results = self.execute_demand_side_analysis(params)

        # Execute capability extraction (steps 10-13)
        extraction_results = self.execute_capability_extraction_workflow(params)

        # Update task plan after completion
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(5, "completed", "Results aggregation and delivery")
            self.file_tracker.update_task_plan_status("Workflow completed", "Phase 5")
            self.file_tracker.add_to_analysis_report(
                "Complete Results Summary",
                f"Supply-side analysis results: {json.dumps(supply_results, default=str, ensure_ascii=False)[:300]}..."
            )
            self.file_tracker.add_to_analysis_report(
                "Complete Results Summary",
                f"Demand-side analysis results: {json.dumps(demand_results, default=str, ensure_ascii=False)[:300]}..."
            )
            self.file_tracker.add_to_analysis_report(
                "Complete Results Summary",
                f"Extraction results: {json.dumps(extraction_results, default=str, ensure_ascii=False)[:300]}..."
            )

        complete_results = {
            "workflow_type": "full_analysis",
            "target_module": params.get("target_module"),
            "detail_level": params.get("detail_level"),
            "timestamp": datetime.now().isoformat(),
            "supply_side_results": supply_results,
            "demand_side_results": demand_results,
            "extraction_results": extraction_results,
            "total_steps_completed": 13,
            "status": "completed",
            "subagent_results_summary": {name: self._summarize_result(result)
                                       for name, result in self.subagent_results.items()}
        }

        return complete_results

    def execute_subagent(self, agent_type: str, goal: str,
                        skills_granted: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a sub-agent with specified skills and configuration
        """
        try:
            # Prepare parameters for the sub-agent execution
            subagent_params = {
                "target_module": config.get("target_module", "{target_module}"),
                "goal": goal,
                "skills_granted": skills_granted,
                "config": config,
                "shared_context": self.shared_context,
                "workflow_id": self.workflow_id
            }

            # Validate target module name if validation is enabled
            target_module = config.get("target_module", "{target_module}")
            if (self.config.validate_module_names and
                target_module != "{target_module}" and
                not validate_module_name(target_module, self.config.allowed_module_pattern)):
                raise WorkflowError(
                    f"Invalid module name: {target_module}",
                    context={"module_name": target_module, "agent_type": agent_type},
                    severity=ErrorSeverity.HIGH
                )

            # Execute the agent through the capability registry
            result = self.capability_registry.execute_capability(agent_type, subagent_params)

            logger.info(f"Sub-agent {agent_type} executed successfully")
            return result

        except Exception as e:
            logger.error(f"Error executing sub-agent {agent_type}: {e}")
            # Log error to file tracker if it exists
            if self.file_tracker:
                self.file_tracker.log_error(f"Error executing sub-agent {agent_type}: {str(e)}")

            # Use error handler for consistent error formatting
            error_handler = ErrorHandler()
            error_handler.log_error(
                WorkflowError(str(e),
                             context={"agent_type": agent_type, "workflow_id": self.workflow_id},
                             severity=ErrorSeverity.HIGH),
                logger
            )

            return {
                "status": "error",
                "error": str(e),
                "agent_type": agent_type,
                "timestamp": datetime.now().isoformat()
            }

    def _update_shared_context(self, step_name: str, result: Dict[str, Any]) -> None:
        """
        Update the shared context with step results
        """
        try:
            # Store result reference
            self.shared_context["previous_results"][step_name] = {
                "result_reference": result.get("result_reference", ""),
                "timestamp": datetime.now().isoformat(),
                "agent_name": result.get("agent_type", ""),
                "status": result.get("status", "unknown")
            }

            # Store capability units if present
            if "capability_units" in result:
                self.shared_context["knowledge_base"]["capability_units"] = result["capability_units"]

            # Store extracted insights if present
            if "extracted_insights" in result:
                self.shared_context["knowledge_base"]["insights"] = result["extracted_insights"]

            # Log context update
            self.workflow_history.append({
                "type": "context_update",
                "step_name": step_name,
                "updated_at": datetime.now().isoformat()
            })

            # Add context update to file tracker if it exists
            if self.file_tracker:
                self.file_tracker.add_notes(
                    f"Context Update: {step_name}",
                    f"Updated shared context with results from {step_name}. Status: {result.get('status', 'unknown')}"
                )

        except Exception as e:
            logger.error(f"Error updating shared context for {step_name}: {e}")
            # Log error to file tracker if it exists
            if self.file_tracker:
                self.file_tracker.log_error(f"Error updating shared context for {step_name}: {str(e)}")

    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of a result for the overall workflow
        """
        return {
            "status": result.get("status", "unknown"),
            "has_capability_units": "capability_units" in result,
            "has_insights": "extracted_insights" in result,
            "timestamp": result.get("timestamp", datetime.now().isoformat())
        }

def execute_skill(skill_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the Capability Twin Orchestrator skill
    """
    try:
        logger.info("Executing Capability Twin Orchestrator skill")

        # Check if we need to perform intent analysis first
        # If the user provided a natural language request without structured parameters
        user_input = skill_params.get("user_input") or skill_params.get("request") or skill_params.get("query")

        if user_input:
            logger.info("Detected natural language request, performing intent analysis...")

            # First, analyze the user's intent using the intent-understanding skill
            intent_analysis_params = {
                "user_input": user_input,
                "context": {
                    "available_modules": skill_params.get("available_modules", ["sale", "stock", "account", "purchase", "mrp", "hr", "crm"]),
                    "workflow_preferences": skill_params.get("workflow_preferences", ["supply_side", "demand_side", "gap_analysis"])
                }
            }

            # Execute intent understanding skill
            intent_skill_result = None
            try:
                config = CapabilityTwinConfig()
                intent_skill_result = CapabilityRegistry(config.get_registry_path()).execute_capability("intent-understanding", intent_analysis_params)
            except Exception as e:
                logger.warning(f"Intent understanding skill failed: {e}, using original parameters")

            if intent_skill_result and intent_skill_result.get("status") == "success":
                logger.info(f"Intent analysis completed with confidence: {intent_skill_result.get('confidence', 0)}")

                # Extract intent information
                intent_info = intent_skill_result.get("intent_analysis", {})

                # Update skill_params with intent-derived values, but keep any explicitly provided values
                if intent_info.get("target_module"):
                    skill_params["target_module"] = skill_params.get("target_module") or intent_info.get("target_module")

                if intent_info.get("workflow_type"):
                    skill_params["workflow_type"] = skill_params.get("workflow_type") or intent_info.get("workflow_type")

                if intent_info.get("detail_level"):
                    skill_params["detail_level"] = skill_params.get("detail_level") or intent_info.get("detail_level")

                # Provide workflow configuration based on intent if not provided
                if not skill_params.get("sub_agents_config") and intent_info.get("analysis_focus"):
                    skill_params["sub_agents_config"] = intent_info.get("suggested_workflow", {}).get("sub_agents_config", [])

                logger.info(f"Updated parameters from intent analysis: target_module={skill_params.get('target_module')}, workflow_type={skill_params.get('workflow_type')}")

            # Check if intent analysis was inconclusive or low confidence
            clarification_needed = intent_skill_result.get("clarification_needed", []) if intent_skill_result else []
            if clarification_needed:
                logger.warning(f"Intent analysis requests clarification: {clarification_needed}")
                # Add clarification request to the result

        # Create configuration and orchestrator instance
        config = CapabilityTwinConfig()
        orchestrator = CapabilityTwinOrchestratorSkill(config=config)

        # Execute the workflow
        result = orchestrator.execute_workflow(skill_params)

        # Add any clarification requests if they exist
        if user_input and intent_skill_result and intent_skill_result.get("status") == "success":
            clarification_needed = intent_skill_result.get("clarification_needed", [])
            if clarification_needed:
                result["clarification_needed"] = clarification_needed
                result["intent_confidence"] = intent_skill_result.get("confidence", 0)
                result["intent_analysis"] = intent_skill_result.get("intent_analysis", {})

        logger.info("Capability Twin Orchestrator skill completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error executing Capability Twin Orchestrator skill: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Main function to test the Capability Twin Orchestrator skill"""
    print("Testing Capability Twin Orchestrator Skill...")

    # Example 1: Full analysis workflow
    print("\n1. Executing full analysis workflow:")
    full_analysis_params = {
        "target_module": "sale",
        "workflow_type": "full_analysis",
        "detail_level": "comprehensive",
        "output_format": "markdown",
        "sub_agents_config": [
            {
                "agent_type": "ecosystem-discovery-agent",
                "sub_goal": "discover ecosystem dependencies for sale module",
                "skills_granted": ["relationship-analysis", "source-traceability", "generic-analyzer"]
            },
            {
                "agent_type": "technical-analysis-agent",
                "sub_goal": "analyze technical implementation of sale models and workflows",
                "skills_granted": ["source-traceability", "knowledge-manager", "relationship-analysis"]
            },
            {
                "agent_type": "function-analysis-agent",
                "sub_goal": "analyze functional capabilities of sale module",
                "skills_granted": ["generic-analyzer", "knowledge-manager"]
            },
            {
                "agent_type": "capability-extractor-agent",
                "sub_goal": "extract capability units from analysis results",
                "skills_granted": ["knowledge-manager", "data-exchange", "quality-gate"]
            }
        ],
        "context_sharing": {
            "ecosystem_to_technical": ["dependencies", "integration_points"],
            "technical_to_function": ["models", "workflows", "data_structures"],
            "function_to_extraction": ["functions", "capabilities", "features"]
        }
    }

    result1 = execute_skill(full_analysis_params)
    print("Full analysis result (truncated):")
    print(json.dumps({
        "status": result1.get("status"),
        "workflow_type": result1.get("workflow_type"),
        "target_module": result1.get("target_module"),
        "total_steps_completed": result1.get("total_steps_completed"),
        "timestamp": result1.get("timestamp")
    }, ensure_ascii=False, indent=2))

    # Example 2: Customization workflow
    print("\n2. Executing customization workflow:")
    customization_params = {
        "target_module": "stock",
        "workflow_type": "customization",
        "requirement": "add negative inventory control",
        "sub_agents_config": [
            {
                "agent_type": "capability-gap-identifier-agent",
                "sub_goal": "identify capability gaps for negative inventory control",
                "skills_granted": ["source-traceability", "relationship-analysis"]
            },
            {
                "agent_type": "code-autogenerator-agent",
                "sub_goal": "generate code for negative inventory control feature",
                "skills_granted": ["file-operations", "template-processor", "data-exchange"]
            }
        ]
    }

    result2 = execute_skill(customization_params)
    print("Customization result (truncated):")
    print(json.dumps({
        "status": result2.get("status"),
        "workflow_type": result2.get("workflow_type"),
        "requirement": result2.get("requirement"),
        "steps_completed": result2.get("steps_completed"),
        "timestamp": result2.get("timestamp")
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()