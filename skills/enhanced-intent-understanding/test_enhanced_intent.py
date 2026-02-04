#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Enhanced Intent Understanding Skill
Tests integration with Capability Twin framework
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".claude" / "skills"))

def test_enhanced_intent_understanding():
    """Test the enhanced intent understanding skill"""
    try:
        # Import the enhanced skill
        sys.path.insert(0, str(Path(__file__).parent))
        from main import EnhancedIntentUnderstandingSkill

        # Initialize the skill
        skill = EnhancedIntentUnderstandingSkill()

        # Test cases
        test_cases = [
            {
                "input": "Can you analyze the sales module for me?",
                "expected_intent": "analyze_request"
            },
            {
                "input": "I need help understanding how inventory works",
                "expected_intent": "explanation_request"
            },
            {
                "input": "Could you explain the accounting features?",
                "expected_intent": "explanation_request"
            },
            {
                "input": "That's great! Now can you show me how to fix the issue?",
                "expected_intent": "problem_solving_request"
            }
        ]

        print("Testing Enhanced Intent Understanding Skill")
        print("=" * 50)

        all_passed = True
        passed_tests = 0
        total_tests = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['input']}")

            # Analyze intent
            result = skill.analyze_intent(test_case['input'])

            intent = result.get('intent', 'unknown')
            confidence = result.get('confidence', 0)
            emotion = result.get('emotion', 'neutral')

            print(f"  Recognized intent: {intent}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Emotion: {emotion}")

            # Check if intent matches expectation
            if intent == test_case['expected_intent']:
                print("  ✓ PASS")
                passed_tests += 1
            else:
                print(f"  ✗ FAIL - Expected: {test_case['expected_intent']}")
                all_passed = False

        print(f"\n{'='*50}")
        print(f"Test Results: {passed_tests}/{total_tests} tests passed")
        print(f"Overall Result: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

        # Test context management
        print("\nTesting Context Management...")
        context_data = {
            'user_id': 'test_user_001',
            'session_id': 'session_001',
            'context_type': 'intent_analysis'
        }

        store_result = skill.store_context(context_data)
        print(f"  Context storage: {'✓ SUCCESS' if store_result else '✗ FAILED'}")

        # Test retrieval
        retrieved_context = skill.retrieve_context('short_term')
        print(f"  Context retrieval: {'✓ SUCCESS' if retrieved_context else '✗ FAILED'}")

        # Test preferences update
        preferences = {'theme': 'dark', 'language': 'en'}
        pref_result = skill.update_preferences('test_user_001', preferences)
        print(f"  Preferences update: {'✓ SUCCESS' if pref_result else '✗ FAILED'}")

        return all_passed and store_result and retrieved_context and pref_result

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_capability_twin():
    """Test integration with Capability Twin framework"""
    try:
        # Import the enhanced skill
        sys.path.insert(0, str(Path(__file__).parent))
        from main import EnhancedIntentUnderstandingSkill

        # Initialize the skill
        skill = EnhancedIntentUnderstandingSkill()

        # Test context memory system
        print("\nTesting Context Memory System...")
        context_memory = skill.context_memory

        # Test storing context
        test_context = {
            'user_id': 'integration_test_user',
            'session_id': 'integration_session_001',
            'interaction_id': 'interaction_001',
            'context_data': {
                'previous_intent': 'analyze_request',
                'previous_context': 'analyzing_odoo_modules'
            }
        }

        store_result = context_memory.store_context(test_context)
        print(f"  Context storage: {'✓ SUCCESS' if store_result else '✗ FAILED'}")

        # Test retrieving context
        retrieved_context = context_memory.retrieve_context('short_term')
        print(f"  Context retrieval: {'✓ SUCCESS' if retrieved_context else '✗ FAILED'}")

        # Test updating preferences
        preferences = {'module_focus': 'sale', 'analysis_depth': 'comprehensive'}
        pref_result = context_memory.update_preferences('integration_test_user', preferences)
        print(f"  Preferences update: {'✓ SUCCESS' if pref_result else '✗ FAILED'}")

        # Test retrieving preferences
        user_preferences = context_memory.retrieve_context('user_preferences', 'integration_test_user')
        print(f"  Preferences retrieval: {'✓ SUCCESS' if user_preferences else '✗ FAILED'}")

        return store_result and retrieved_context and pref_result and user_preferences

    except Exception as e:
        print(f"Error during integration testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Enhanced Intent Understanding Skill Integration Tests")
    print("=" * 60)

    # Test enhanced skill functionality
    enhanced_test_result = test_enhanced_intent_understanding()

    # Test integration with Capability Twin
    integration_test_result = test_integration_with_capability_twin()

    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Enhanced Skill Tests: {'✓ PASSED' if enhanced_test_result else '✗ FAILED'}")
    print(f"Integration Tests: {'✓ PASSED' if integration_test_result else '✗ FAILED'}")

    overall_result = enhanced_test_result and integration_test_result
    print(f"Overall Result: {'✓ ALL TESTS PASSED' if overall_result else '✗ SOME TESTS FAILED'}")

    return overall_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)