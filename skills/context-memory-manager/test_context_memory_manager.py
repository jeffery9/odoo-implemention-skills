#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Context Memory Manager Skill
Tests integration with Enhanced Intent Understanding skill
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".claude" / "skills"))

def test_context_memory_manager():
    """Test the context memory manager skill"""
    try:
        # Import the context memory manager
        sys.path.insert(0, str(Path(__file__).parent))
        from main import ContextMemoryManager

        # Initialize the skill
        skill = ContextMemoryManager()

        # Test cases
        test_cases = [
            {
                "user_id": "test_user_001",
                "session_id": "session_001",
                "context_type": "intent_analysis",
                "data": {
                    "previous_intent": "analyze_request",
                    "previous_context": "analyzing_odoo_modules",
                    "confidence": 0.85
                }
            },
            {
                "user_id": "test_user_002",
                "session_id": "session_002",
                "context_type": "knowledge_acquisition",
                "data": {
                    "previous_intent": "explanation_request",
                    "previous_context": "understanding_features",
                    "emotion": "positive"
                },
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "analysis_depth": "comprehensive"
                }
            }
        ]

        print("Testing Context Memory Manager Skill")
        print("=" * 50)

        # Test storing context
        all_stores_passed = True
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nStore Test {i}: {test_case['user_id']}")

            store_result = skill.store_context(test_case)
            print(f"  Store result: {'✓ SUCCESS' if store_result else '✗ FAILED'}")

            if not store_result:
                all_stores_passed = False

        # Test retrieving context
        print("\nRetrieving context data...")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nRetrieve Test {i}: {test_case['user_id']}")

            # Retrieve session context
            session_context = skill.retrieve_context('session_context')
            print(f"  Session context: {'✓ SUCCESS' if session_context else '✗ FAILED'}")

            # Retrieve user preferences
            user_prefs = skill.retrieve_context('user_preferences', test_case['user_id'])
            print(f"  User preferences: {'✓ SUCCESS' if user_prefs else '✗ FAILED'}")

        # Test updating preferences
        print("\nUpdating user preferences...")
        preferences_updates = {
            "test_user_001": {"module_focus": "sale", "analysis_depth": "comprehensive"},
            "test_user_002": {"theme": "light", "language": "zh"}
        }

        all_updates_passed = True
        for user_id, prefs in preferences_updates.items():
            update_result = skill.update_preferences(user_id, prefs)
            print(f"  Update {user_id}: {'✓ SUCCESS' if update_result else '✗ FAILED'}")

            if not update_result:
                all_updates_passed = False

        # Test getting user context summary
        print("\nGetting user context summaries...")
        all_summaries_passed = True
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nSummary Test {i}: {test_case['user_id']}")

            summary = skill.get_user_context_summary(test_case['user_id'])
            print(f"  Summary: {'✓ SUCCESS' if summary else '✗ FAILED'}")
            print(f"    - User ID: {summary.get('user_id', 'N/A')}")
            print(f"    - Preferences: {summary.get('preferences', {})}")
            print(f"    - Interaction count: {summary.get('interaction_count', 0)}")

            if not summary:
                all_summaries_passed = False

        # Test clearing context
        print("\nClearing context...")
        clear_result = skill.clear_context(user_id='test_user_001')
        print(f"  Clear test_user_001: {'✓ SUCCESS' if clear_result else '✗ FAILED'}")

        return all_stores_passed and all_updates_passed and all_summaries_passed and clear_result

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
        from main import ContextMemoryManager

        # Initialize the skills
        context_manager = ContextMemoryManager()

        # Test context storage and retrieval
        print("\nTesting Integration with Enhanced Intent Understanding...")
        print("=" * 60)

        # Test storing intent analysis context
        intent_context = {
            'user_id': 'intent_test_user',
            'session_id': 'intent_session_001',
            'interaction_id': 'intent_interaction_001',
            'context_type': 'intent_analysis',
            'data': {
                'intent': 'analyze_request',
                'confidence': 0.75,
                'emotion': 'neutral',
                'original_intent': 'analyze_request'
            },
            'preferences': {
                'theme': 'dark',
                'analysis_type': 'detailed'
            }
        }

        print("Storing intent analysis context...")
        store_result = context_manager.store_context(intent_context)
        print(f"  Store result: {'✓ SUCCESS' if store_result else '✗ FAILED'}")

        # Verify context was stored
        if store_result:
            print("Verifying stored context...")
            session_context = context_manager.retrieve_context('session_context')
            user_prefs = context_manager.retrieve_context('user_preferences', 'intent_test_user')
            print(f"  Session context: {'✓ SUCCESS' if session_context else '✗ FAILED'}")
            print(f"  User preferences: {'✓ SUCCESS' if user_prefs else '✗ FAILED'}")

        # Test updating intent preferences
        print("Updating intent preferences...")
        updated_prefs = {'theme': 'light', 'analysis_type': 'comprehensive', 'module_focus': 'sale'}
        update_result = context_manager.update_preferences('intent_test_user', updated_prefs)
        print(f"  Update result: {'✓ SUCCESS' if update_result else '✗ FAILED'}")

        # Test getting intent context summary
        print("Getting intent context summary...")
        summary = context_manager.get_user_context_summary('intent_test_user')
        print(f"  Summary: {'✓ SUCCESS' if summary else '✗ FAILED'}")
        print(f"    - User ID: {summary.get('user_id', 'N/A')}")
        print(f"    - Preferences: {summary.get('preferences', {})}")

        return store_result and update_result and summary

    except Exception as e:
        print(f"Error during integration testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Context Memory Manager Skill Integration Tests")
    print("=" * 60)

    # Test context memory manager functionality
    manager_test_result = test_context_memory_manager()

    # Test integration with enhanced intent understanding
    integration_test_result = test_integration_with_enhanced_intent()

    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Context Manager Tests: {'✓ PASSED' if manager_test_result else '✗ FAILED'}")
    print(f"Integration Tests: {'✓ PASSED' if integration_test_result else '✗ FAILED'}")

    overall_result = manager_test_result and integration_test_result
    print(f"Overall Result: {'✓ ALL TESTS PASSED' if overall_result else '✗ SOME TESTS FAILED'}")

    return overall_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)