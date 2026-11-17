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
from bdd_gate import BDDGate, SCENARIO_DEPENDENT_TEMPLATES

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

## BDD Spec Gate (attached to G2, not a new phase)
Business scenarios are authored in skills/gherkin-bdd/features/*.feature (single source of truth).
- [ ] L1 Gherkin spec gate passed (error=0)
- [ ] Derived UAT / step stubs / traceability matrix generated from the validated spec
- [ ] G3 sign-off uses the derived UAT script, not hand-written steps

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
            target_phase = phase or "Phase 1"
            line = f"**Currently in {target_phase}** - {new_status}"
            # 用整行替换而不是匹配初始文案：状态行被改过一次后，
            # 原来的 replace 锚点就消失了，后续更新会静默失效（例如门禁阻断状态写不进去）。
            pattern = re.compile(r"\*\*Currently in [^*]+\*\* - [^\n]*")
            if pattern.search(content):
                return pattern.sub(line, content, count=1)
            return content.replace("## Status", f"## Status\n{line}", 1)

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

    def update_bdd_gate(self, passed: bool, detail: str, artifact: str = ""):
        """
        把规格门禁结果写回 task_plan.md。

        门禁状态必须落在计划文件里，而不是只存在于返回值中 ——
        否则中断后重跑的人无法判断上一次到底过没过。
        """
        def update_func(content: str) -> str:
            mark = "x" if passed else " "
            line = f"- [{mark}] L1 Gherkin spec gate passed (error=0) — {detail}"
            if artifact:
                line += f" | artifact: {artifact}"
            pattern = re.compile(r"- \[[ x]\] L1 Gherkin spec gate passed[^\n]*")
            if pattern.search(content):
                return pattern.sub(line, content, count=1)
            return content.replace("## Decisions Made", f"{line}\n\n## Decisions Made")

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
        # 规格门禁：由 preflight 实例化，后续步骤复用同一次判定结果
        self.bdd_gate: Optional[BDDGate] = None
        self.bdd_run: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Gherkin BDD 规格门禁
    # 挂载在既有流程边界（preflight / Step 10→11 / Step 13），不新增阶段编号。
    # ------------------------------------------------------------------
    def _make_bdd_gate(self, params: Dict[str, Any]) -> BDDGate:
        raw = params.get("bdd")
        cfg: Dict[str, Any] = raw if isinstance(raw, dict) else {}
        self.bdd_gate = BDDGate(
            features_dir=cfg.get("features_dir"),
            output_dir=cfg.get("output_dir"),
            enabled=bool(cfg.get("enabled", True)),
        )
        return self.bdd_gate

    def _bdd_preflight(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        流程启动前的规格门禁（G2 前置条件）。

        - `fail`（有规格但违规）默认阻断整条流水线；
        - `missing`（该模块尚无 `.feature`）不阻断分析，但会阻止场景类交付物打包。
        """
        raw = params.get("bdd")
        cfg: Dict[str, Any] = raw if isinstance(raw, dict) else {}
        gate = self.bdd_gate or self._make_bdd_gate(params)

        run = gate.run(module=params.get("target_module"),
                       stage="G2-preflight", derive=False)
        self.bdd_run = run

        blocking = bool(cfg.get("blocking", True))
        blocked = blocking and run.get("status") == "fail"

        if self.file_tracker:
            self.file_tracker.update_bdd_gate(
                passed=bool(run.get("satisfies_module")),
                detail=BDDGate.summary_line(run),
                artifact=run.get("report_path") or "",
            )
            self.file_tracker.add_notes(
                "BDD Spec Gate (preflight)",
                f"status={run.get('status')} scope={run.get('scope')} "
                f"features_dir={run.get('features_dir')} "
                f"report={run.get('report_path')}",
            )
            if blocked:
                codes = ", ".join(i.get("code", "") for i in run.get("blocking_issues", [])[:5])
                self.file_tracker.log_error(
                    f"BDD spec gate blocked the pipeline at G2 preflight ({codes})")

        logger.info(f"BDD spec gate preflight: {BDDGate.summary_line(run)}")
        return {"run": run, "blocked": blocked, "blocking": blocking}

    def _bdd_gate_stage(self, params: Dict[str, Any], stage: str,
                        derive: bool = False,
                        unit_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """在既有步骤边界复用同一门禁引擎，避免多套判定口径。"""
        gate = self.bdd_gate or self._make_bdd_gate(params)
        run = gate.run(module=params.get("target_module"), stage=stage,
                       derive=derive, unit_ids=unit_ids)
        self.bdd_run = run
        if self.file_tracker:
            self.file_tracker.update_bdd_gate(
                passed=bool(run.get("satisfies_module")),
                detail=f"[{stage}] " + BDDGate.summary_line(run),
                artifact=run.get("report_path") or "",
            )
        return run

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

            # ---- Gherkin BDD 规格门禁：G2 前置，失败即阻断（不进入分析阶段）----
            preflight = self._bdd_preflight(workflow_params)
            self.shared_context["bdd_gate"] = {
                "status": preflight["run"].get("status"),
                "scope": preflight["run"].get("scope"),
                "features_dir": preflight["run"].get("features_dir"),
                "report_path": preflight["run"].get("report_path"),
            }
            if preflight["blocked"]:
                self.file_tracker.update_task_plan_status(
                    "Blocked by BDD spec gate", "Phase 2")
                logger.error("Workflow blocked by BDD spec gate before analysis")
                return {
                    "workflow_id": self.workflow_id,
                    "status": "blocked",
                    "blocked_at": "BDD Spec Gate (G2 preflight)",
                    "gate": preflight["run"],
                    "target_module": target_module,
                    "workflow_type": workflow_params.get("workflow_type", "full_analysis"),
                    "next_action": "修正 .feature 规格后重跑；或在入参显式设置 bdd.blocking=false 仅作草稿分析",
                    "timestamp": datetime.now().isoformat(),
                    "workflow_history": self.workflow_history,
                }

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
            result.setdefault("bdd_gate", self.shared_context.get("bdd_gate", {}))

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
                "skills_granted": ["relationship-analysis", "source-traceability", "knowledge-manager"],
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
                "skills_granted": ["source-traceability", "relationship-analysis", "knowledge-manager", "fde-methodology"],
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
                "skills_granted": ["generic-analyzer", "source-traceability", "knowledge-manager"],
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
                "skills_granted": ["generic-analyzer", "relationship-analysis", "knowledge-manager"],
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
                "skills_granted": ["documentation-miner", "relationship-analysis", "generic-analyzer", "knowledge-manager"],
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
                "skills_granted": ["source-traceability", "generic-analyzer", "quality-gate", "fde-methodology"],
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

        # 按子步骤真实状态结算，失败/待执行不标记为完成
        outcome = self._workflow_outcome(results)
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(
                2, "completed" if outcome["status"] == "completed" else "in_progress",
                f"Supply-side analysis (Steps 1-6) — {outcome['status']}")
            self.file_tracker.update_task_plan_status("Moving to demand-side analysis", "Phase 3")

        return {
            "workflow_type": "supply_side_analysis",
            **outcome,
            "results": results,
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
                "skills_granted": ["documentation-miner", "generic-analyzer", "knowledge-manager", "fde-methodology"],
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
                "skills_granted": ["documentation-miner", "relationship-analysis", "template-processor", "gherkin-bdd"],
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
                "skills_granted": ["documentation-miner", "template-processor", "data-exchange", "fde-methodology", "gherkin-bdd"],
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

        outcome = self._workflow_outcome(results)
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(
                3, "completed" if outcome["status"] == "completed" else "in_progress",
                f"Demand-side analysis (Steps 7-9) — {outcome['status']}")
            self.file_tracker.update_task_plan_status("Moving to capability extraction", "Phase 4")

        return {
            "workflow_type": "demand_side_analysis",
            **outcome,
            "results": results,
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
                "skills_granted": ["generic-analyzer", "source-traceability", "knowledge-manager", "quality-gate", "fde-methodology", "gherkin-bdd"],
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
                "skills_granted": ["template-processor", "file-operations", "data-exchange"],
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
                "skills_granted": ["source-traceability", "quality-gate", "knowledge-manager", "fde-methodology", "gherkin-bdd"],
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
                "skills_granted": ["quality-gate", "knowledge-manager", "fde-methodology", "gherkin-bdd"],
                "config": {
                    "target_module": params.get("target_module"),
                    "analysis_depth": params.get("detail_level")
                }
            }
        ]

        results = []
        gate_run: Dict[str, Any] = {}
        for step in workflow_steps:
            logger.info(f"Executing step {step['step']}: {step['name']}")

            # 打包步骤直接消费已通过门禁的规格产物，不另造一套场景描述
            if step["step"] == 11 and gate_run:
                step["config"]["bdd_artifacts"] = gate_run.get("derived", {})
                step["config"]["bdd_gate_report"] = gate_run.get("report_path")
                step["config"]["scenario_deliverables_blocked"] = not gate_run.get("satisfies_module")

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

            # ---- 挂载点：Step 10 → Step 11 ----
            # 能力单元抽取完成后立即做 G2 规格门禁，通过才允许派生 UAT / 步骤桩 / 矩阵。
            # 失败即中止，避免把不合格规格包装成交付物（门禁必须能真正拦住东西）。
            if step["step"] == 10:
                unit_ids = self._extract_unit_ids(subagent_result)
                gate_run = self._bdd_gate_stage(params, stage="G2", derive=True,
                                                unit_ids=unit_ids)
                results.append({
                    "step": None,
                    "name": "BDD Spec Gate (mounted at Step 10→11, not a new phase)",
                    "result": gate_run,
                })
                self.subagent_results["BDD Spec Gate"] = gate_run
                self.shared_context["bdd_gate"] = {
                    "status": gate_run.get("status"),
                    "scope": gate_run.get("scope"),
                    "report_path": gate_run.get("report_path"),
                    "derived": gate_run.get("derived", {}),
                }
                if self.file_tracker:
                    self.file_tracker.add_notes(
                        "BDD Spec Gate (Step 10→11)",
                        f"{BDDGate.summary_line(gate_run)}; "
                        f"units_without_scenario={gate_run.get('coverage', {}).get('units_without_scenario', [])}")
                    self.file_tracker.add_to_analysis_report(
                        "BDD Spec Gate (G2)",
                        json.dumps({k: gate_run.get(k) for k in
                                    ("status", "scope", "features", "scenarios",
                                     "errors", "warnings", "coverage", "derived")},
                                   ensure_ascii=False, default=str))

                if gate_run.get("status") == "fail":
                    codes = ", ".join(i.get("code", "")
                                      for i in gate_run.get("blocking_issues", [])[:5])
                    if self.file_tracker:
                        self.file_tracker.log_error(
                            f"BDD spec gate failed at Step 10→11 ({codes}); packaging aborted")
                    outcome = self._workflow_outcome(results)
                    return {
                        "workflow_type": "capability_extraction_workflow",
                        "status": "blocked",
                        "blocked_at": "BDD Spec Gate (G2, Step 10→11)",
                        "gate": gate_run,
                        **{k: v for k, v in outcome.items() if k != "status"},
                        "results": results,
                    }

                if not gate_run.get("satisfies_module") and self.file_tracker:
                    # 无本模块规格：分析可以继续，但 G2 场景证据不成立，必须在计划里留痕
                    self.file_tracker.add_notes(
                        "BDD Spec Gate (Step 10→11) — module spec absent",
                        f"scope={gate_run.get('scope')}；场景类交付物（UAT / Scenario Solution）"
                        f"在打包阶段会被跳过，直至 skills/gherkin-bdd/features/"
                        f"{params.get('target_module')}/ 下补齐 .feature")

        outcome = self._workflow_outcome(results)
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(
                4, "completed" if outcome["status"] == "completed" else "in_progress",
                f"Capability extraction & quality assurance (Steps 10-13) — {outcome['status']}")
            self.file_tracker.update_task_plan_status("Moving to results aggregation", "Phase 5")

        return {
            "workflow_type": "capability_extraction_workflow",
            **outcome,
            "results": results,
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
                "skills_granted": ["template-processor", "generic-analyzer", "knowledge-manager"],
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
                "skills_granted": ["file-operations", "template-processor", "source-traceability", "quality-gate"],
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
                "skills_granted": ["quality-gate", "knowledge-manager", "data-exchange", "fde-methodology", "gherkin-bdd"],
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

            # ---- 挂载点：N 步客制化 第 4 步（质量门与注册）----
            # 交付前必须确认该模块的场景规格仍然成立，否则注册的是未经场景验证的能力。
            if step["step"] == 4:
                gate_run = self._bdd_gate_stage(params, stage="G2-customization", derive=True)
                results.append({
                    "step": None,
                    "name": "BDD Spec Gate (mounted at Customization Step 4, not a new phase)",
                    "result": gate_run,
                })
                self.subagent_results["BDD Spec Gate"] = gate_run
                step["config"]["bdd_artifacts"] = gate_run.get("derived", {})
                step["config"]["bdd_gate_report"] = gate_run.get("report_path")
                if gate_run.get("status") == "fail":
                    codes = ", ".join(i.get("code", "")
                                      for i in gate_run.get("blocking_issues", [])[:5])
                    if self.file_tracker:
                        self.file_tracker.log_error(
                            f"BDD spec gate failed at Customization Step 4 ({codes}); registration aborted")
                    outcome = self._workflow_outcome(results)
                    return {
                        "workflow_type": "customization",
                        "requirement": params.get("requirement", "custom_requirement"),
                        "target_module": params.get("target_module"),
                        "status": "blocked",
                        "blocked_at": "BDD Spec Gate (G2, Customization Step 4)",
                        "gate": gate_run,
                        **{k: v for k, v in outcome.items() if k != "status"},
                        "results": results,
                    }

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

        outcome = self._workflow_outcome(results)
        if self.file_tracker:
            self.file_tracker.update_task_plan_status(
                f"Customization workflow — {outcome['status']}", "Phase 5")

        return {
            "workflow_type": "customization",
            "requirement": params.get("requirement", "custom_requirement"),
            "target_module": params.get("target_module"),
            **outcome,
            "results": results,
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

        # 汇总三段子工作流的真实状态，不按固定 13 步宣称完成
        phases = [supply_results, demand_results, extraction_results]
        agg = {
            "steps_total": sum(p.get("steps_total", 0) for p in phases),
            "steps_completed": sum(p.get("steps_completed", 0) for p in phases),
            "steps_delegated": sum(p.get("steps_delegated", 0) for p in phases),
            "steps_failed": sum(p.get("steps_failed", 0) for p in phases),
        }
        agg["requires_semantic_execution"] = agg["steps_delegated"] > 0
        phase_statuses = [p.get("status") for p in phases]
        if "blocked" in phase_statuses:
            # 门禁拦截优先于完成度汇总：被 G2 规格门禁挡住时不能报 partial/completed
            agg["status"] = "blocked"
            agg["blocked_at"] = next((p.get("blocked_at") for p in phases
                                      if p.get("status") == "blocked"), "BDD Spec Gate")
        elif all(s == "completed" for s in phase_statuses):
            agg["status"] = "completed"
        elif all(s == "failed" for s in phase_statuses):
            agg["status"] = "failed"
        else:
            agg["status"] = "partial"

        # Update task plan after completion
        if self.file_tracker:
            self.file_tracker.update_task_plan_phase(
                5, "completed" if agg["status"] == "completed" else "in_progress",
                f"Results aggregation and delivery — {agg['status']}")
            self.file_tracker.update_task_plan_status(
                f"Workflow {agg['status']}", "Phase 5")
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
            **agg,
            "subagent_results_summary": {name: self._summarize_result(result)
                                       for name, result in self.subagent_results.items()}
        }

        return complete_results

    # 交付包 → 模板映射（templates/deliverables/ 下 16 份模板的完整覆盖）
    BUNDLE_TEMPLATES = {
        "strategy":    ["PURPOSE_AND_STRATEGY", "PROJECT_SOLUTION", "STATEMENT_OF_WORK"],
        "consultant":  ["CONSULTANT_CONF_GUIDE", "CONSULTANT_UAT_SCRIPT",
                        "CONSULTANT_DISCOVERY_NOTE", "IMPLEMENTATION_METHODOLOGY"],
        "developer":   ["CAPABILITY_ANALYSIS_REPORT", "GAP_ANALYSIS_REPORT", "SOLUTION_SPECIFICATION",
                        "CAPABILITY_UNIT_SPEC", "SCENARIO_SOLUTION", "FUNCTIONAL_DOC_SPEC"],
        "handover":    ["HANDOVER_MANIFEST", "EVOLUTION_GUIDE", "BEST_PRACTICES_REPORT"],
    }
    BUNDLE_ALIASES = {
        "handover_package": "handover", "asset": "handover", "资产移交包": "handover",
        "战略包": "strategy", "顾问包": "consultant", "研发技术包": "developer",
    }

    def render_deliverables_bundle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染角色化交付包。

        这是 README §6 记录的 `operation: render_deliverables_bundle` 的实际实现：
        按 bundle_type 选取模板集合，逐份调用 template-processor 落盘。
        以「文件是否真的生成」判定成功，不以返回值声称成功。

        接入 Gherkin BDD 后的行为：
        - 渲染前先跑规格门禁（`skills/gherkin-bdd`，只读复用，不复制规则）；
        - 场景变量（`scenario_ids` / `gherkin_feature` / `generated_uat_table` 等）
          由 `.feature` 机械派生，人工传入的同名字段不得覆盖（唯一事实源）；
        - 门禁未通过时跳过 `SCENARIO_SOLUTION` / `CONSULTANT_UAT_SCRIPT`，
          宁可少交付两份文件，也不产出与规格脱钩的验收步骤。
        """
        bundle_type = params.get("bundle_type", "handover_package")
        key = self.BUNDLE_ALIASES.get(bundle_type, bundle_type)
        templates = self.BUNDLE_TEMPLATES.get(key)
        if not templates:
            return {
                "status": "error",
                "error": f"未知 bundle_type: {bundle_type}",
                "supported": sorted(self.BUNDLE_TEMPLATES),
                "aliases": sorted(self.BUNDLE_ALIASES),
            }

        context = dict(params.get("context_data", {}) or {})
        target_module = params.get("target_module") or context.get("target_module")

        # ---- Gherkin BDD 门禁：场景类交付物必须由已通过的规格派生 ----
        gate = self.bdd_gate or self._make_bdd_gate(params)
        run = gate.run(module=target_module, stage="G3-derive", derive=True)
        self.bdd_run = run

        allow_invalid = params.get("allow_invalid_scenarios") is True
        # 只有「该模块自己的规格通过」才允许产出场景类交付物；
        # 全仓基线通过不能替该模块背书（否则会渲染出别的模块的场景）。
        gate_blocked = (not run.get("satisfies_module")) and not allow_invalid

        derived_ctx = gate.deliverable_context(module=target_module, run=run)
        # 派生字段优先：`.feature` 是唯一事实源，人工传入的同名字段不得覆盖
        overridden = []
        for k, v in derived_ctx.items():
            if k in context and context[k] not in (None, "", v):
                overridden.append(k)
            context[k] = v

        blocked_templates: List[str] = []
        if gate_blocked:
            blocked_templates = [t for t in templates
                                 if t in SCENARIO_DEPENDENT_TEMPLATES]
            templates = [t for t in templates if t not in blocked_templates]

        out_dir = Path(params.get("output_directory")
                       or (self.config.get_output_path() / "deliverables" / key))
        out_dir.mkdir(parents=True, exist_ok=True)

        rendered, failed = [], []
        for name in templates:
            target = out_dir / f"{name}.md"
            self.capability_registry.execute_capability("template-processor", {
                "operation": "render_deliverable",
                "template_name": name,
                "context_data": context,
                "output_path": str(target),
                "template_engine": params.get("template_engine", "simple"),
            })
            if target.is_file() and target.stat().st_size > 0:
                rendered.append({"template": name, "path": str(target)})
            else:
                failed.append({"template": name, "reason": "未生成输出文件"})

        if rendered and (failed or blocked_templates):
            status = "partial"
        elif rendered:
            status = "success"
        elif blocked_templates and not failed:
            status = "blocked"
        else:
            status = "failed"

        return {
            "workflow_type": "render_deliverables_bundle",
            "bundle_type": key,
            "output_directory": str(out_dir),
            "status": status,
            "steps_total": len(templates) + len(blocked_templates),
            "steps_completed": len(rendered),
            "steps_failed": len(failed),
            "rendered": rendered,
            "failed": failed,
            "blocked_templates": blocked_templates,
            "scenario_binding": {
                "source": "skills/gherkin-bdd/features",
                "status": run.get("status"),
                "scope": run.get("scope"),
                "satisfies_module": run.get("satisfies_module"),
                "features": run.get("features"),
                "scenarios": run.get("scenarios"),
                "report_path": run.get("report_path"),
            },
            "gate": run,
            "context_overrides": overridden,
            "timestamp": datetime.now().isoformat(),
        }

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

            # 无论走哪条执行路径（prompt / stub / subprocess），结果都必须携带被授予的技能，
            # 否则下游无法判断本步骤受哪些约束、是否挂了 FDE 检查点。
            if isinstance(result, dict):
                result.setdefault("skills_granted", list(skills_granted))
                if "fde-methodology" in skills_granted:
                    result["fde_checkpoint"] = {
                        "required": True,
                        "checklist": "skills/fde-methodology/SKILL.md §5（9 条）",
                        "record_format": "逐条 pass / fail / n/a + 证据",
                        # 由执行者在实际复核后置为 True 并附证据；框架不代填
                        "recorded": False,
                    }

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
            # Store result reference（setdefault：允许直接调用单个工作流方法）
            self.shared_context.setdefault("previous_results", {})[step_name] = {
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

    @staticmethod
    def _extract_unit_ids(result: Dict[str, Any]) -> List[str]:
        """从 Step 10 结果中收集能力单元编号，用于检查「单元是否被场景覆盖」。"""
        ids: List[str] = []
        for key in ("capability_units", "units"):
            for item in (result.get(key) or []):
                if isinstance(item, dict):
                    uid = item.get("id") or item.get("unit_id")
                else:
                    uid = item
                if isinstance(uid, str) and uid.strip():
                    ids.append(uid.strip())
        return ids

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

    # 子步骤状态归一化：只有 success 才算「本步骤已完成」。
    # delegated 表示指令已下发、等待语义执行（prompt agent 的正常工作方式），
    # 它不等于完成；failed 表示执行失败或无可用入口。
    DELEGATED_STATUSES = {"pending_instruction", "semantic_wait", "delegated"}
    FAILED_STATUSES = {"error", "failed", "unsupported"}

    def _normalize_step_status(self, status: str) -> str:
        """把子代理返回的多种状态归一到 success / delegated / failed 三态"""
        s = (status or "unknown").lower()
        if s in self.DELEGATED_STATUSES:
            return "delegated"
        if s in self.FAILED_STATUSES:
            return "failed"
        if s in ("success", "completed", "ok"):
            return "success"
        return "failed"

    def _workflow_outcome(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        按子步骤真实状态汇总工作流结论。

        规则（避免「全部失败仍报 completed」）：
        - 全部 success            → completed
        - 有失败且有成功/委派      → partial
        - 无 success 但有委派      → delegated（等待语义执行，未完成）
        - 全部失败                 → failed
        """
        counts = {"success": 0, "delegated": 0, "failed": 0}
        for item in results:
            counts[self._normalize_step_status((item.get("result") or {}).get("status", ""))] += 1

        total = len(results)
        if total and counts["success"] == total:
            status = "completed"
        elif counts["failed"] == total or total == 0:
            status = "failed"
        elif counts["failed"] > 0:
            status = "partial"
        else:
            status = "delegated"

        return {
            "status": status,
            "steps_total": total,
            "steps_completed": counts["success"],
            "steps_delegated": counts["delegated"],
            "steps_failed": counts["failed"],
            "requires_semantic_execution": counts["delegated"] > 0,
        }

def execute_skill(skill_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the Capability Twin Orchestrator skill
    """
    try:
        logger.info("Executing Capability Twin Orchestrator skill")

        # 交付包渲染入口（README §6 记录的 operation）。
        # 早期版本忽略 operation，导致该命令静默落到 full_analysis；此处显式分流。
        if skill_params.get("operation") in ("render_deliverables_bundle", "render_deliverable"):
            banner = CapabilityTwinOrchestratorSkill(config=CapabilityTwinConfig())
            return banner.render_deliverables_bundle(skill_params)

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
                "skills_granted": ["relationship-analysis", "source-traceability", "knowledge-manager"]
            },
            {
                "agent_type": "technical-analysis-agent",
                "sub_goal": "analyze technical implementation of sale models and workflows",
                "skills_granted": ["source-traceability", "relationship-analysis", "knowledge-manager", "fde-methodology"]
            },
            {
                "agent_type": "function-analysis-agent",
                "sub_goal": "analyze functional capabilities of sale module",
                "skills_granted": ["generic-analyzer", "source-traceability", "knowledge-manager"]
            },
            {
                "agent_type": "capability-extractor-agent",
                "sub_goal": "extract capability units from analysis results",
                "skills_granted": ["generic-analyzer", "source-traceability", "knowledge-manager", "quality-gate", "fde-methodology"]
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
                "skills_granted": ["source-traceability", "relationship-analysis", "knowledge-manager"]
            },
            {
                "agent_type": "code-autogenerator-agent",
                "sub_goal": "generate code for negative inventory control feature",
                "skills_granted": ["file-operations", "template-processor", "source-traceability", "quality-gate"]
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