#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Intent Understanding Skill
Advanced intent recognition and interpretation for Capability Twin workflows
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import re
from pathlib import Path
import uuid

# 技能容器根：仓库布局下是 skills/，npx skills 安装后是 .claude/skills/。
# 只按本文件深度推导，不依赖 CWD，也不依赖仓库根。
_skills_root = Path(__file__).resolve().parents[1]
_orchestrator = _skills_root / "capability-twin-orchestrator"
if not _orchestrator.is_dir():
    raise ImportError(
        f"本技能依赖 `capability-twin-orchestrator`，但在 `{_skills_root}` 下未找到。"
        "请整套安装：npx skills add <owner>/<repo> --all；"
        "或补装：npx skills add <owner>/<repo> --skill capability-twin-orchestrator"
    )
sys.path.insert(0, str(_orchestrator / "scripts"))

from capability_registry import CapabilityRegistry

_REGISTRY_PATH = _orchestrator / "capability_registry.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentUnderstandingSkill:
    """
    Advanced intent recognition and interpretation skill that processes user inputs
    to understand their underlying intentions and map them to appropriate Capability
    Twin workflows.
    """

    def __init__(self):
        self.skill_id = f"intent-understanding-{str(uuid.uuid4())[:8]}"
        self.capability_registry = CapabilityRegistry(_REGISTRY_PATH)

        # Define keyword mappings for different intent categories
        self.workflow_keywords = {
            "full_analysis": ["complete", "comprehensive", "full", "thorough", "overall", "entire", "all aspects", "holistic"],
            "supply_side_analysis": ["supply", "supply-side", "current", "existing", "technical", "implementation", "how it works", "system", "architecture"],
            "demand_side_analysis": ["demand", "demand-side", "requirements", "needs", "needs analysis", "requirements analysis", "gap analysis", "gap"],
            "capability_extraction": ["extract", "extract capability", "capability unit", "capability", "unit", "package", "delivery", "capability extraction"],
            "customization": ["custom", "customize", "customization", "extension", "extend", "enhance", "modify", "improve", "solution", "development"]
        }

        self.detail_level_keywords = {
            "basic": ["basic", "high-level", "overview", "summary", "brief"],
            "medium": ["medium", "moderate", "standard", "normal", "regular"],
            "comprehensive": ["comprehensive", "detailed", "deep", "thorough", "extensive", "complete", "in-depth", "full detail"]
        }

        self.module_aliases = {
            "sale": ["sales", "order", "quotation", "quote", "sales order", "sale order"],
            "stock": ["inventory", "warehousing", "warehouse", "inventory management", "stock management", "inventory control"],
            "account": ["accounting", "finance", "financial", "general ledger", "gl", "chart of accounts"],
            "purchase": ["procurement", "buying", "procure", "supplier", "vendors", "purchasing"],
            "mrp": ["manufacturing", "production", "manufacture", "work order", "bom", "bill of materials"],
            "hr": ["human resource", "employee", "personnel", "staff", "human resources", "payroll"],
            "crm": ["customer", "partner", "lead", "opportunity", "opportunity management", "customer management"]
        }

    def analyzeIntent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user input to understand underlying intentions
        """
        try:
            logger.info(f"Analyzing intent for input: {params.get('user_input', 'no input provided')}")

            user_input = params.get('user_input', '')
            context = params.get('context', {})

            # Perform intent analysis
            intent_analysis = self.performIntentAnalysis(user_input, context)

            # Calculate overall confidence
            confidence = self.calculateConfidence(intent_analysis)

            # Generate suggested workflow based on intent
            suggested_workflow = self.generateSuggestedWorkflow(intent_analysis, context)

            result = {
                "status": "success",
                "skill_id": self.skill_id,
                "timestamp": datetime.now().isoformat(),
                "confidence": confidence,
                "intent_analysis": intent_analysis,
                "intent_confidence": self.calculateIndividualConfidences(intent_analysis),
                "keywords_identified": self.extractKeywords(user_input),
                "clarification_needed": self.determineClarifications(intent_analysis),
                "suggested_workflow": suggested_workflow
            }

            logger.info(f"Intent analysis completed with confidence: {confidence}")
            return result

        except Exception as e:
            logger.error(f"Error in intent analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill_id": self.skill_id,
                "timestamp": datetime.now().isoformat()
            }

    def performIntentAnalysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the actual intent analysis on user input
        """
        user_input_lower = user_input.lower()

        # Identify workflow type intent
        workflow_type = self.identifyWorkflowType(user_input_lower)

        # Identify target module
        target_module = self.identifyTargetModule(user_input_lower, context)

        # Identify analysis focus
        analysis_focus = self.identifyAnalysisFocus(user_input_lower)

        # Identify detail level
        detail_level = self.identifyDetailLevel(user_input_lower)

        return {
            "workflow_type": workflow_type,
            "target_module": target_module,
            "analysis_focus": analysis_focus,
            "detail_level": detail_level
        }

    def identifyWorkflowType(self, user_input: str) -> str:
        """
        Identify the intended workflow type from user input
        """
        for workflow_type, keywords in self.workflow_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    return workflow_type

        # Default to full_analysis if no clear indication
        return "full_analysis"

    def identifyTargetModule(self, user_input: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Identify the target module from user input
        """
        # First, check if a specific module is mentioned
        # Check in context if provided
        available_modules = context.get('available_modules', [])

        # Check user input for module names and their aliases
        for module, aliases in self.module_aliases.items():
            if module in user_input or any(alias in user_input for alias in aliases):
                # Verify module exists in context if available
                if available_modules and module in available_modules:
                    return module
                elif not available_modules:  # If no context provided, return the identified module
                    return module

        # If no module clearly identified in aliases, check available_modules in context
        for module in available_modules:
            if module in user_input:
                return module

        return None  # Return None if uncertain

    def identifyAnalysisFocus(self, user_input: str) -> List[str]:
        """
        Identify the focus areas for analysis
        """
        focus_areas = []

        # Check for various analysis types in the input
        if any(word in user_input for word in ["supply", "supply-side", "technical", "implementation", "how it works"]):
            focus_areas.append("supply_side")

        if any(word in user_input for word in ["demand", "demand-side", "requirements", "needs", "gap"]):
            focus_areas.append("demand_side")

        if any(word in user_input for word in ["capability", "extract", "unit", "package", "delivery"]):
            focus_areas.append("capability_extraction")

        if any(word in user_input for word in ["gaps", "gap analysis", "requirements", "needs analysis"]):
            focus_areas.append("gap_analysis")

        if any(word in user_input for word in ["function", "functional", "feature", "capabilities"]):
            focus_areas.append("function_analysis")

        if any(word in user_input for word in ["business", "process", "workflow", "business process"]):
            focus_areas.append("business_process")

        # If no specific focus identified, assume comprehensive
        if not focus_areas:
            focus_areas = ["supply_side", "demand_side", "gap_analysis"]

        return focus_areas

    def identifyDetailLevel(self, user_input: str) -> str:
        """
        Identify the required detail level
        """
        for detail_level, keywords in self.detail_level_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    return detail_level

        # Default to comprehensive if detailed analysis requested, otherwise medium
        if any(word in user_input for word in ["detailed", "deep", "thorough", "extensive", "in-depth", "complete"]):
            return "comprehensive"
        else:
            return "medium"

    def calculateConfidence(self, intent_analysis: Dict[str, Any]) -> float:
        """
        Calculate overall confidence in intent interpretation
        """
        # Calculate confidence based on how many elements were clearly identified
        confidence_score = 0.0
        total_elements = len(intent_analysis)
        identified_elements = 0

        for key, value in intent_analysis.items():
            if value is not None and value != [] and value != "":
                if isinstance(value, list):
                    if len(value) > 0:
                        identified_elements += 1
                else:
                    identified_elements += 1

        # Calculate base confidence
        if total_elements > 0:
            confidence_score = identified_elements / total_elements

        # Adjust for specific conditions
        if intent_analysis.get('target_module') is None:
            confidence_score *= 0.7  # Lower confidence if no target module identified
        if intent_analysis.get('workflow_type') == 'full_analysis' and identified_elements < 3:
            confidence_score *= 0.8  # Lower confidence for default full_analysis when other elements unclear

        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence_score))

    def calculateIndividualConfidences(self, intent_analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate individual confidence scores for each intent element
        """
        confidences = {}

        for key, value in intent_analysis.items():
            if value is None or (isinstance(value, (str, list)) and not value):
                confidences[key] = 0.1  # Very low confidence if not identified
            else:
                if key == 'target_module':
                    # Lower confidence for target_module if it's just a guess
                    confidences[key] = 0.7 if value else 0.1
                else:
                    confidences[key] = 0.9  # High confidence if identified
                    if key == 'detail_level' and value == 'medium':
                        confidences[key] = 0.6  # Medium confidence for default medium level

        return confidences

    def extractKeywords(self, user_input: str) -> List[str]:
        """
        Extract relevant keywords from user input
        """
        # Find all words that might be relevant to intent
        words = re.findall(r'\b\w+\b', user_input.lower())

        # Filter for potentially meaningful words
        meaningful_keywords = []
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }

        for word in words:
            if len(word) > 2 and word not in common_words:
                if word not in meaningful_keywords:
                    meaningful_keywords.append(word)

        return meaningful_keywords[:20]  # Return top 20 keywords

    def determineClarifications(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """
        Determine what clarifications are needed based on intent analysis
        """
        clarifications = []

        if intent_analysis.get('target_module') is None:
            clarifications.append("specific_module")

        if intent_analysis.get('workflow_type') == 'full_analysis' and intent_analysis.get('analysis_focus') == ["supply_side", "demand_side", "gap_analysis"]:
            # This suggests default values were used, so clarify intent
            clarifications.append("analysis_focus")

        if intent_analysis.get('detail_level') == 'medium':
            # Medium is often a default, so ask for clarification if precision is needed
            if any(kw in ['detailed', 'thorough', 'comprehensive', 'basic', 'overview'] for kw in intent_analysis.get('analysis_focus', [])):
                pass  # If these were identified, no clarification needed
            else:
                clarifications.append("detail_level")

        return clarifications

    def generateSuggestedWorkflow(self, intent_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a suggested workflow based on intent analysis
        """
        suggested_workflow = {
            "workflow_type": intent_analysis.get('workflow_type', 'full_analysis'),
            "target_module": intent_analysis.get('target_module', '{target_module}'),
            "detail_level": intent_analysis.get('detail_level', 'comprehensive'),
            "sub_agents_config": []
        }

        # Add appropriate sub-agent configurations based on analysis focus
        focus_areas = intent_analysis.get('analysis_focus', [])

        if 'supply_side' in focus_areas or 'supply_side_analysis' in intent_analysis.get('workflow_type', ''):
            suggested_workflow["sub_agents_config"].append({
                "agent_type": "ecosystem-discovery-agent",
                "sub_goal": f"discover ecosystem dependencies for {suggested_workflow['target_module']} module",
                "skills_granted": ["relationship-analysis", "source-traceability", "generic-analyzer"]
            })
            suggested_workflow["sub_agents_config"].append({
                "agent_type": "technical-analysis-agent",
                "sub_goal": f"analyze technical implementation of {suggested_workflow['target_module']} models and workflows",
                "skills_granted": ["source-traceability", "knowledge-manager", "relationship-analysis"]
            })

        if 'demand_side' in focus_areas or 'demand_side_analysis' in intent_analysis.get('workflow_type', ''):
            suggested_workflow["sub_agents_config"].append({
                "agent_type": "industry-requirements-agent",
                "sub_goal": f"analyze industry requirements for {suggested_workflow['target_module']} module",
                "skills_granted": ["relationship-analysis", "source-traceability", "generic-analyzer"]
            })
            suggested_workflow["sub_agents_config"].append({
                "agent_type": "solution-architect-agent",
                "sub_goal": f"define solution architecture for {suggested_workflow['target_module']} requirements",
                "skills_granted": ["knowledge-manager", "generic-analyzer", "relationship-analysis"]
            })

        if 'capability_extraction' in focus_areas or 'capability_extraction' in intent_analysis.get('workflow_type', ''):
            suggested_workflow["sub_agents_config"].append({
                "agent_type": "capability-extractor-agent",
                "sub_goal": f"extract capability units from {suggested_workflow['target_module']} analysis results",
                "skills_granted": ["knowledge-manager", "data-exchange", "quality-gate"]
            })

        if 'gap_analysis' in focus_areas:
            suggested_workflow["sub_agents_config"].append({
                "agent_type": "capability-gap-identifier-agent",
                "sub_goal": f"identify capability gaps for {suggested_workflow['target_module']} requirements",
                "skills_granted": ["source-traceability", "relationship-analysis", "knowledge-manager"]
            })

        return suggested_workflow


def execute_skill(skill_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the Intent Understanding skill
    """
    try:
        logger.info("Executing Intent Understanding skill")

        # Create intent understanding instance
        intent_skill = IntentUnderstandingSkill()

        # Analyze the provided intent
        result = intent_skill.analyzeIntent(skill_params)

        logger.info("Intent Understanding skill completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error executing Intent Understanding skill: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# --- 命名兼容层 -----------------------------------------------------------
# 历史实现使用 camelCase，测试与外部调用方使用 snake_case。显式登记别名，
# 避免两套命名继续分叉；新增方法应直接写 snake_case。
_SNAKE_ALIASES = {
    "_perform_intent_analysis": "performIntentAnalysis",
    "_identify_workflow_type": "identifyWorkflowType",
    "_identify_target_module": "identifyTargetModule",
    "_identify_analysis_focus": "identifyAnalysisFocus",
    "_identify_detail_level": "identifyDetailLevel",
    "_calculate_confidence": "calculateConfidence",
    "_determine_clarifications": "determineClarifications",
    "perform_intent_analysis": "performIntentAnalysis",
    "identify_workflow_type": "identifyWorkflowType",
    "identify_target_module": "identifyTargetModule",
    "identify_analysis_focus": "identifyAnalysisFocus",
    "identify_detail_level": "identifyDetailLevel",
    "calculate_confidence": "calculateConfidence",
    "determine_clarifications": "determineClarifications",
    "analyze_intent": "analyzeIntent",
    "generate_suggested_workflow": "generateSuggestedWorkflow",
    "extract_keywords": "extractKeywords",
}
for _snake, _camel in _SNAKE_ALIASES.items():
    if not hasattr(IntentUnderstandingSkill, _snake):
        setattr(IntentUnderstandingSkill, _snake, getattr(IntentUnderstandingSkill, _camel))


def main():
    """Main function to test the Intent Understanding skill"""
    print("Testing Intent Understanding Skill...")

    # Example 1: Comprehensive analysis request
    print("\n1. Analyzing comprehensive analysis request:")
    analysis_request = {
        "user_input": "Please perform a complete analysis of the inventory module to understand its current capabilities and identify any gaps with our business requirements.",
        "context": {
            "available_modules": ["stock", "sale", "account", "purchase"],
            "workflow_preferences": ["supply_side", "demand_side", "gap_analysis"]
        }
    }

    result1 = execute_skill(analysis_request)
    print(f"Confidence: {result1.get('confidence', 0):.2f}")
    print(f"Workflow Type: {result1.get('intent_analysis', {}).get('workflow_type')}")
    print(f"Target Module: {result1.get('intent_analysis', {}).get('target_module')}")
    print(f"Clarifications Needed: {result1.get('clarification_needed', [])}")

    # Example 2: Technical analysis request
    print("\n2. Analyzing technical analysis request:")
    tech_request = {
        "user_input": "I need to understand the technical implementation of the accounting module, especially the models and workflows.",
        "context": {
            "available_modules": ["account", "stock", "sale"],
            "workflow_preferences": ["technical_analysis"]
        }
    }

    result2 = execute_skill(tech_request)
    print(f"Confidence: {result2.get('confidence', 0):.2f}")
    print(f"Workflow Type: {result2.get('intent_analysis', {}).get('workflow_type')}")
    print(f"Target Module: {result2.get('intent_analysis', {}).get('target_module')}")
    print(f"Analysis Focus: {result2.get('intent_analysis', {}).get('analysis_focus')}")

    # Example 3: Ambiguous request
    print("\n3. Analyzing ambiguous request:")
    ambiguous_request = {
        "user_input": "Analyze the module for our business.",
        "context": {
            "available_modules": ["sale", "stock", "account"],
            "workflow_preferences": ["full_analysis"]
        }
    }

    result3 = execute_skill(ambiguous_request)
    print(f"Confidence: {result3.get('confidence', 0):.2f}")
    print(f"Clarifications Needed: {result3.get('clarification_needed', [])}")
    print(f"Target Module: {result3.get('intent_analysis', {}).get('target_module')}")


if __name__ == "__main__":
    main()