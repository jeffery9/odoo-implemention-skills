#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Intent to Action Mapper Skill
Tests functionality and integration capabilities
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".claude" / "skills"))

def test_intent_to_action_mapper():
    """Test the intent to action mapper skill"""
    try:
        # Import the intent to action mapper
        sys.path.insert(0, str(Path(__file__).parent))
        from main import IntentToActionMapper

        # Initialize the skill
        skill = IntentToActionMapper()

        # Test cases
        test_cases = [
            {
                "intent": "analyze_request",
                "expected_actions": ["search_module_files", "parse_module_code", "identify_dependencies"],
                "description": "Analyze module request"
            },
            {
                "intent": "explanation_request",
                "expected_actions": ["search_documentation", "find_examples", "create_explanation"],
                "description": "Explain feature request"
            },
            {
                "intent": "problem_solving_request",
                "expected_actions": ["identify_problem", "search_solutions", "evaluate_options"],
                "description": "Problem solving request"
            },
            {
                "intent": "help_request",
                "expected_actions": ["assess_need", "find_adequate_help", "provide_assistance"],
                "description": "Help request"
            }
        ]

        print("Testing Intent to Action Mapper Skill")
        print("=" * 50)

        all_passed = True
        passed_tests = 0
        total_tests = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['description']}")
            print(f"  Intent: {test_case['intent']}")

            # Map intent to actions
            result = skill.map_intent_to_actions(test_case['intent'])

            # Check if the result has the expected structure
            has_action_plan = 'action_plan' in result
            has_resource_allocation = 'resource_allocation' in result
            has_execution_sequence = 'execution_sequence' in result
            has_estimated_time = 'estimated_time' in result
            has_confidence = 'confidence' in result

            print(f"  Has action plan: {'✓' if has_action_plan else '✗'}")
            print(f"  Has resource allocation: {'✓' if has_resource_allocation else '✗'}")
            print(f"  Has execution sequence: {'✓' if has_execution_sequence else '✗'}")
            print(f"  Has estimated time: {'✓' if has_estimated_time else '✗'}")
            print(f"  Has confidence: {'✓' if has_confidence else '✗'}")

            # Check if confidence is reasonable
            confidence = result.get('confidence', 0)
            confidence_reasonable = 0.0 <= confidence <= 1.0
            print(f"  Confidence reasonable: {'✓' if confidence_reasonable else '✗'} ({confidence:.2f})")

            # Check if we have the expected actions
            actions = result.get('action_plan', {}).get('actions', [])
            expected_actions = test_case['expected_actions']
            has_expected_actions = all(action in actions for action in expected_actions[:3])  # Check first 3 actions
            print(f"  Has expected actions: {'✓' if has_expected_actions else '✗'}")

            # Overall test result
            test_passed = (
                has_action_plan and
                has_resource_allocation and
                has_execution_sequence and
                has_estimated_time and
                has_confidence and
                confidence_reasonable and
                has_expected_actions
            )

            if test_passed:
                print("  ✓ PASS")
                passed_tests += 1
            else:
                print("  ✗ FAIL")
                all_passed = False

        print(f"\n{'='*50}")
        print(f"Test Results: {passed_tests}/{total_tests} tests passed")
        print(f"Overall Result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

        return all_passed

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_enhanced_intent():
    """Test integration with Enhanced Intent Understanding skill"""
    try:
        # Import both skills
        sys.path.insert(0, str(Path(__file__).parent))
        from main import IntentToActionMapper

        # Initialize the skills
        action_mapper = IntentToActionMapper()

        # Test integration with context
        print("\nTesting Integration with Enhanced Intent Understanding...")
        print("=" * 60)

        # Test with context from enhanced intent understanding
        context = {
            'user_id': 'integration_test_user',
            'session_id': 'integration_session_001',
            'intent': 'analyze_request',
            'emotion': 'neutral',
            'confidence': 0.85
        }

        print("Testing with context-based intent mapping...")
        result = action_mapper.map_intent_to_actions('analyze_request', context)

        # Check if all required fields are present
        required_fields = ['action_plan', 'resource_allocation', 'execution_sequence', 'estimated_time', 'confidence']
        all_fields_present = all(field in result for field in required_fields)

        print(f"  All required fields present: {'✓' if all_fields_present else '✗'}")

        # Check if action plan has context information
        action_plan = result.get('action_plan', {})
        has_context_info = 'intent' in action_plan and action_plan['intent'] == 'analyze_request'
        print(f"  Action plan has correct intent: {'✓' if has_context_info else '✗'}")

        # Check if execution sequence has appropriate steps
        execution_sequence = result.get('execution_sequence', [])
        has_execution_steps = len(execution_sequence) > 0
        print(f"  Execution sequence has steps: {'✓' if has_execution_steps else '✗'}")

        # Check confidence with context
        confidence = result.get('confidence', 0)
        confidence_with_context = confidence >= 0.5
        print(f"  Confidence with context >= 0.5: {'✓' if confidence_with_context else '✗'} ({confidence:.2f})")

        integration_passed = (
            all_fields_present and
            has_context_info and
            has_execution_steps and
            confidence_with_context
        )

        print(f"  Integration test: {'✓ PASSED' if integration_passed else '✗ FAILED'}")

        return integration_passed

    except Exception as e:
        print(f"Error during integration testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_update_templates():
    """Test updating action templates"""
    try:
        # Import the intent to action mapper
        sys.path.insert(0, str(Path(__file__).parent))
        from main import IntentToActionMapper

        # Initialize the skill
        skill = IntentToActionMapper()

        # Test updating templates
        print("\nTesting Template Updates...")
        print("=" * 30)

        # Get original templates
        original_templates = skill.action_templates.copy()

        # Add new template
        new_templates = {
            'new_intent': {
                'description': 'New intent for testing',
                'actions': ['action1', 'action2'],
                'required_resources': ['resource1'],
                'execution_plan': 'sequential'
            }
        }

        update_result = skill.update_action_templates(new_templates)
        print(f"  Template update: {'✓ SUCCESS' if update_result else '✗ FAILED'}")

        # Check if template was added
        has_new_template = 'new_intent' in skill.action_templates
        print(f"  New template added: {'✓' if has_new_template else '✗ FAILED'}")

        # Test mapping with new template
        if has_new_template:
            result = skill.map_intent_to_actions('new_intent')
            has_action_plan = 'action_plan' in result
            print(f"  New template mapping: {'✓ SUCCESS' if has_action_plan else '✗ FAILED'}")

        return update_result and has_new_template and has_action_plan

    except Exception as e:
        print(f"Error during template update testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Intent to Action Mapper Skill Integration Tests")
    print("=" * 60)

    # Test intent to action mapper functionality
    mapper_test_result = test_intent_to_action_mapper()

    # Test integration with enhanced intent understanding
    integration_test_result = test_integration_with_enhanced_intent()

    # Test template updates
    template_test_result = test_update_templates()

    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Mapper Tests: {'✓ PASSED' if mapper_test_result else '✗ FAILED'}")
    print(f"Integration Tests: {'✓ PASSED' if integration_test_result else '✗ FAILED'}")
    print(f"Template Tests: {'✓ PASSED' if template_test_result else '✗ FAILED'}")

    overall_result = mapper_test_result and integration_test_result and template_test_result
    print(f"Overall Result: {'✓ ALL TESTS PASSED' if overall_result else '✗ SOME TESTS FAILED'}")

    return overall_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)