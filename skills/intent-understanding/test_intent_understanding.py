#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for Intent Understanding Skill
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

# Add project paths
skill_dir = Path(__file__).parent.resolve()
project_root = skill_dir.parent.parent.parent
scripts_dir = project_root / ".claude" / "scripts"

sys.path.append(str(project_root))
sys.path.append(str(scripts_dir))
sys.path.append(str(skill_dir))

from main import IntentUnderstandingSkill


class TestIntentUnderstandingSkill(unittest.TestCase):
    """
    Test suite for IntentUnderstandingSkill
    """

    def setUp(self):
        """Set up test fixtures"""
        self.intent_skill = IntentUnderstandingSkill()

    def test_workflow_type_identification(self):
        """Test identification of different workflow types"""
        # Test full analysis
        result = self.intent_skill._identify_workflow_type("perform a complete analysis")
        self.assertEqual(result, "full_analysis")

        # Test supply side analysis
        result = self.intent_skill._identify_workflow_type("analyze the technical implementation")
        self.assertEqual(result, "supply_side_analysis")

        # Test demand side analysis
        result = self.intent_skill._identify_workflow_type("analyze requirements and gaps")
        self.assertEqual(result, "demand_side_analysis")

        # Test capability extraction
        result = self.intent_skill._identify_workflow_type("extract capability units")
        self.assertEqual(result, "capability_extraction")

        # Test customization
        result = self.intent_skill._identify_workflow_type("need to customize the module")
        self.assertEqual(result, "customization")

    def test_target_module_identification(self):
        """Test identification of target modules"""
        # Test sales module identification
        result = self.intent_skill._identify_target_module("analyze the sales module", {})
        self.assertEqual(result, "sale")

        # Test inventory/stock module identification
        result = self.intent_skill._identify_target_module("analyze the inventory management", {})
        self.assertEqual(result, "stock")

        # Test accounting module identification
        result = self.intent_skill._identify_target_module("analyze the accounting module", {})
        self.assertEqual(result, "account")

        # Test with context
        context = {"available_modules": ["sale", "stock", "account"]}
        result = self.intent_skill._identify_target_module("check the stock module", context)
        self.assertEqual(result, "stock")

        # Test ambiguous input
        result = self.intent_skill._identify_target_module("analyze something", {})
        self.assertIsNone(result)

    def test_analysis_focus_identification(self):
        """Test identification of analysis focus areas"""
        # Test supply side focus
        result = self.intent_skill._identify_analysis_focus("analyze the technical implementation of the system")
        self.assertIn("supply_side", result)

        # Test demand side focus
        result = self.intent_skill._identify_analysis_focus("analyze requirements and business needs")
        self.assertIn("demand_side", result)

        # Test gap analysis focus
        result = self.intent_skill._identify_analysis_focus("identify gaps between current system and requirements")
        self.assertIn("gap_analysis", result)

        # Test capability extraction focus
        result = self.intent_skill._identify_analysis_focus("extract capability units for delivery")
        self.assertIn("capability_extraction", result)

    def test_detail_level_identification(self):
        """Test identification of detail levels"""
        # Test comprehensive level
        result = self.intent_skill._identify_detail_level("perform a comprehensive and detailed analysis")
        self.assertEqual(result, "comprehensive")

        # Test basic level
        result = self.intent_skill._identify_detail_level("provide a basic overview")
        self.assertEqual(result, "basic")

        # Test medium level
        result = self.intent_skill._identify_detail_level("analyze it normally")
        self.assertEqual(result, "medium")

    def test_confidence_calculation(self):
        """Test confidence calculation"""
        intent_analysis = {
            "workflow_type": "full_analysis",
            "target_module": "sale",
            "analysis_focus": ["supply_side", "demand_side"],
            "detail_level": "comprehensive"
        }

        confidence = self.intent_skill._calculate_confidence(intent_analysis)
        self.assertGreater(confidence, 0.7)  # Should be high when all elements identified

        # Test with missing target module (should reduce confidence)
        intent_analysis["target_module"] = None
        confidence = self.intent_skill._calculate_confidence(intent_analysis)
        self.assertLess(confidence, 1.0)  # Should be reduced when element is missing

    def test_clarification_determination(self):
        """Test determination of needed clarifications"""
        # Test when target module is None
        intent_analysis = {
            "target_module": None,
            "workflow_type": "full_analysis",
            "analysis_focus": ["supply_side", "demand_side", "gap_analysis"]
        }
        clarifications = self.intent_skill._determine_clarifications(intent_analysis)
        self.assertIn("specific_module", clarifications)

        # Test when default analysis focus is used
        clarifications = self.intent_skill._determine_clarifications({
            "target_module": "sale",
            "workflow_type": "full_analysis",
            "analysis_focus": ["supply_side", "demand_side", "gap_analysis"]  # These are defaults
        })
        self.assertIn("analysis_focus", clarifications)

    def test_intent_analysis_full_process(self):
        """Test the complete intent analysis process"""
        user_input = "Please analyze the sales module in detail to understand its capabilities and identify gaps"
        context = {"available_modules": ["sale", "stock", "account"]}

        params = {
            "user_input": user_input,
            "context": context
        }

        intent_analysis = self.intent_skill._perform_intent_analysis(user_input, context)

        # Check that analysis was performed
        self.assertIsNotNone(intent_analysis["workflow_type"])
        self.assertIn(intent_analysis["workflow_type"], self.intent_skill.workflow_keywords.keys())
        self.assertIsNotNone(intent_analysis["analysis_focus"])
        self.assertIsNotNone(intent_analysis["detail_level"])


def test_intent_understanding_main():
    """Test function that runs example scenarios"""
    print("Running Intent Understanding Skill tests...")

    # Create an instance
    skill = IntentUnderstandingSkill()

    # Test case 1: Full analysis request
    print("\n1. Testing comprehensive analysis request:")
    test_params1 = {
        "user_input": "Please perform a complete analysis of the inventory module to understand its capabilities and identify gaps with our requirements",
        "context": {
            "available_modules": ["stock", "sale", "account"],
            "workflow_preferences": ["supply_side", "demand_side", "gap_analysis"]
        }
    }

    result1 = skill.analyze_intent(test_params1)
    print(f"   Confidence: {result1['confidence']:.2f}")
    print(f"   Workflow: {result1['intent_analysis']['workflow_type']}")
    print(f"   Module: {result1['intent_analysis']['target_module']}")

    # Test case 2: Technical analysis
    print("\n2. Testing technical analysis request:")
    test_params2 = {
        "user_input": "Analyze the technical implementation of the accounting module",
        "context": {
            "available_modules": ["account", "stock"],
            "workflow_preferences": ["technical_analysis"]
        }
    }

    result2 = skill.analyze_intent(test_params2)
    print(f"   Confidence: {result2['confidence']:.2f}")
    print(f"   Focus: {result2['intent_analysis']['analysis_focus']}")

    # Test case 3: Ambiguous request
    print("\n3. Testing ambiguous request:")
    test_params3 = {
        "user_input": "Analyze the module",
        "context": {
            "available_modules": ["sale", "stock"],
            "workflow_preferences": ["full_analysis"]
        }
    }

    result3 = skill.analyze_intent(test_params3)
    print(f"   Confidence: {result3['confidence']:.2f}")
    print(f"   Clarifications needed: {result3['clarification_needed']}")

    print("\nIntent Understanding Skill test examples completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'unittest':
        # Run unit tests
        unittest.main()
    else:
        # Run example tests
        test_intent_understanding_main()