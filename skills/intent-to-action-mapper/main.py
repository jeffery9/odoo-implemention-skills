#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intent to Action Mapper Skill
Converts user intents into specific actions and execution plans
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".claude" / "skills"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentToActionMapper:
    """Intent to Action Mapper for converting user intents into specific actions"""

    def __init__(self):
        """Initialize the intent to action mapper"""
        # Action templates for different intent types
        self.action_templates = self._initialize_action_templates()

        # Resource constraints
        self.resource_constraints = {
            'max_execution_time': 300,  # 5 minutes
            'max_memory_usage': '2GB',
            'max_cpu_usage': '80%',
            'concurrent_tasks': 5
        }

        # Decision history tracking
        self.decision_history = []

    def _initialize_action_templates(self) -> Dict[str, Any]:
        """Initialize action templates for different intent types"""
        return {
            'analyze_request': {
                'description': 'Analyze a specific module or feature',
                'actions': [
                    'search_module_files',
                    'parse_module_code',
                    'identify_dependencies',
                    'generate_analysis_report'
                ],
                'required_resources': ['code_analysis_tools', 'memory'],
                'execution_plan': 'sequential'
            },
            'explanation_request': {
                'description': 'Explain a specific concept or feature',
                'actions': [
                    'search_documentation',
                    'find_examples',
                    'create_explanation',
                    'format_output'
                ],
                'required_resources': ['knowledge_base', 'text_processing'],
                'execution_plan': 'sequential'
            },
            'creation_request': {
                'description': 'Create new content or configuration',
                'actions': [
                    'validate_requirements',
                    'create_draft',
                    'apply_templates',
                    'review_content'
                ],
                'required_resources': ['content_creation_tools', 'validation'],
                'execution_plan': 'sequential'
            },
            'problem_solving_request': {
                'description': 'Solve a specific problem or issue',
                'actions': [
                    'identify_problem',
                    'search_solutions',
                    'evaluate_options',
                    'implement_solution'
                ],
                'required_resources': ['problem_solving_tools', 'knowledge_base'],
                'execution_plan': 'iterative'
            },
            'help_request': {
                'description': 'Provide general help and assistance',
                'actions': [
                    'assess_need',
                    'find_adequate_help',
                    'provide_assistance',
                    'verify_understanding'
                ],
                'required_resources': ['help_resources', 'communication'],
                'execution_plan': 'iterative'
            },
            'information_request': {
                'description': 'Provide specific information or data',
                'actions': [
                    'search_data_sources',
                    'validate_accuracy',
                    'format_information',
                    'present_results'
                ],
                'required_resources': ['data_sources', 'validation_tools'],
                'execution_plan': 'sequential'
            },
            'general_request': {
                'description': 'Handle general requests',
                'actions': [
                    'analyze_request',
                    'determine_action',
                    'execute_action',
                    'verify_result'
                ],
                'required_resources': ['general_tools'],
                'execution_plan': 'sequential'
            }
        }

    def map_intent_to_actions(self, intent: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Map user intent to specific actions and execution plan

        Args:
            intent: The recognized intent
            context: Optional context information

        Returns:
            Dict containing:
            - action_plan: Detailed action plan
            - resource_allocation: Resource allocation plan
            - execution_sequence: Execution sequence
            - estimated_time: Estimated execution time
            - confidence: Confidence in the mapping
        """
        try:
            # Get action template for the intent
            action_template = self._get_action_template(intent)

            if not action_template:
                # Fallback to general template
                action_template = self._get_action_template('general_request')

            # Generate action plan
            action_plan = self._generate_action_plan(intent, action_template, context)

            # Allocate resources
            resource_allocation = self._allocate_resources(action_plan, action_template)

            # Generate execution sequence
            execution_sequence = self._generate_execution_sequence(action_plan, resource_allocation, intent)

            # Estimate execution time
            estimated_time = self._estimate_execution_time(action_plan, resource_allocation)

            # Calculate confidence
            confidence = self._calculate_mapping_confidence(intent, action_plan, context)

            return {
                'action_plan': action_plan,
                'resource_allocation': resource_allocation,
                'execution_sequence': execution_sequence,
                'estimated_time': estimated_time,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Error mapping intent to actions: {e}")
            # Fallback to basic mapping
            return self._fallback_mapping(intent, context)

    def _get_action_template(self, intent: str) -> Optional[Dict]:
        """Get action template for a specific intent"""
        return self.action_templates.get(intent)

    def _generate_action_plan(self, intent: str, template: Dict, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate detailed action plan based on intent and template"""
        try:
            # Basic action plan structure
            action_plan = {
                'intent': intent,
                'description': template.get('description', f'Action plan for {intent}'),
                'actions': [],
                'prerequisites': [],
                'postconditions': [],
                'constraints': [],
                'resources_needed': template.get('required_resources', [])
            }

            # Add actions from template
            if 'actions' in template:
                action_plan['actions'] = template['actions']

            # Add context-specific actions
            if context and isinstance(context, dict):
                # Add actions based on context
                if 'previous_actions' in context:
                    action_plan['prerequisites'].extend(context['previous_actions'])

                # Add postconditions based on context
                if 'expected_outcome' in context:
                    action_plan['postconditions'].append(context['expected_outcome'])

            # Add custom actions based on intent
            custom_actions = self._get_custom_actions(intent)
            if custom_actions:
                action_plan['actions'].extend(custom_actions)

            return action_plan

        except Exception as e:
            logger.error(f"Error generating action plan: {e}")
            return {
                'intent': intent,
                'actions': ['fallback_action'],
                'prerequisites': [],
                'postconditions': [],
                'constraints': [],
                'resources_needed': ['default_resources']
            }

    def _get_custom_actions(self, intent: str) -> List[str]:
        """Get custom actions based on intent"""
        custom_actions = {
            'analyze_request': [
                'identify_module_files',
                'parse_module_code',
                'search_dependencies',
                'generate_analysis_report'
            ],
            'explanation_request': [
                'find_documentation',
                'search_examples',
                'create_explanation',
                'format_output'
            ],
            'problem_solving_request': [
                'identify_problem',
                'search_solutions',
                'validate_solution',
                'implement_fix'
            ]
        }

        return custom_actions.get(intent, [])

    def _allocate_resources(self, action_plan: Dict, template: Dict) -> Dict[str, Any]:
        """Allocate resources for action execution"""
        try:
            # Resource allocation strategy
            resource_allocation = {
                'tool_requirements': [],
                'memory_requirements': 'normal',
                'cpu_requirements': 'normal',
                'time_requirements': 'normal',
                'user_interactions': [],
                'dependencies': []
            }

            # Add tools based on actions
            for action in action_plan.get('actions', []):
                tools = self._get_tools_for_action(action)
                resource_allocation['tool_requirements'].extend(tools)

            # Add context-specific resources
            if 'context' in action_plan:
                # Add resources based on context
                pass

            return resource_allocation

        except Exception as e:
            logger.error(f"Error allocating resources: {e}")
            return {
                'tool_requirements': ['basic_tools'],
                'memory_requirements': 'normal',
                'cpu_requirements': 'normal',
                'time_requirements': 'normal',
                'user_interactions': [],
                'dependencies': []
            }

    def _get_tools_for_action(self, action: str) -> List[str]:
        """Get required tools for an action"""
        action_tools = {
            'search_module_files': ['file_search', 'code_analysis'],
            'parse_module_code': ['code_parser', 'syntax_analyzer'],
            'identify_dependencies': ['dependency_analyzer', 'graph_builder'],
            'generate_analysis_report': ['report_generator', 'format_converter'],
            'search_documentation': ['documentation_search', 'content_fetcher'],
            'find_examples': ['example_finder', 'content_matcher'],
            'create_explanation': ['explanation_generator', 'content_formatter'],
            'validate_requirements': ['validation_engine', 'rule_checker'],
            'create_draft': ['content_creator', 'template_engine'],
            'apply_templates': ['template_applier', 'style_formatter'],
            'review_content': ['review_engine', 'quality_checker'],
            'identify_problem': ['problem_analyzer', 'issue_detector'],
            'search_solutions': ['solution_finder', 'knowledge_search'],
            'evaluate_options': ['evaluator', 'comparator'],
            'implement_solution': ['implementation_engine', 'code_generator'],
            'assess_need': ['assess_engine', 'requirement_analyzer'],
            'find_adequate_help': ['help_finder', 'resource_locator'],
            'provide_assistance': ['assistant', 'communication_tool'],
            'verify_understanding': ['verifier', 'feedback_collector'],
            'search_data_sources': ['data_searcher', 'data_fetcher'],
            'validate_accuracy': ['validator', 'accuracy_checker'],
            'format_information': ['formatter', 'output_formatter'],
            'present_results': ['presenter', 'result_displayer']
        }

        return action_tools.get(action, ['general_tool'])

    def _generate_execution_sequence(self, action_plan: Dict, resource_allocation: Dict, intent: str) -> List[Dict]:
        """Generate detailed execution sequence"""
        try:
            execution_sequence = []

            # Add initialization step
            execution_sequence.append({
                'step': 1,
                'action': 'initialize_execution',
                'description': 'Initialize execution environment',
                'resources': ['execution_environment'],
                'estimated_time': '5s'
            })

            # Add prerequisite steps
            for i, prerequisite in enumerate(action_plan.get('prerequisites', []), 2):
                execution_sequence.append({
                    'step': i,
                    'action': prerequisite,
                    'description': f'Execute prerequisite: {prerequisite}',
                    'resources': resource_allocation.get('tool_requirements', []),
                    'estimated_time': '10s'
                })

            # Add main action steps
            actions = action_plan.get('actions', [])
            for i, action in enumerate(actions, len(execution_sequence) + 2):
                execution_sequence.append({
                    'step': i,
                    'action': action,
                    'description': f'Execute action: {action}',
                    'resources': [tool for tool in resource_allocation.get('tool_requirements', []) if self._is_action_tool(tool, action)],
                    'estimated_time': '30s'
                })

            # Add postcondition steps
            for i, postcondition in enumerate(action_plan.get('postconditions', []), len(execution_sequence) + 2):
                execution_sequence.append({
                    'step': i,
                    'action': 'verify_postcondition',
                    'description': f'Verify postcondition: {postcondition}',
                    'resources': ['verification_tool'],
                    'estimated_time': '5s'
                })

            return execution_sequence

        except Exception as e:
            logger.error(f"Error generating execution sequence: {e}")
            # Fallback to simple sequence
            return [{
                'step': 1,
                'action': 'execute_action',
                'description': 'Execute intent action',
                'resources': ['default_resources'],
                'estimated_time': '60s'
            }]

    def _is_action_tool(self, tool: str, action: str) -> bool:
        """Check if a tool is relevant for an action"""
        # Simplified check - in a real implementation, this would be more sophisticated
        return True

    def _estimate_execution_time(self, action_plan: Dict, resource_allocation: Dict) -> str:
        """Estimate execution time for the action plan"""
        try:
            # Base time calculation
            base_time = 10  # 10 seconds base time

            # Add time for each action
            actions = action_plan.get('actions', [])
            action_time = len(actions) * 30  # 30 seconds per action

            # Add time for prerequisites
            prerequisites = action_plan.get('prerequisites', [])
            prerequisite_time = len(prerequisites) * 10  # 10 seconds per prerequisite

            # Add time for postconditions
            postconditions = action_plan.get('postconditions', [])
            postcondition_time = len(postconditions) * 5  # 5 seconds per postcondition

            # Total estimated time
            total_time = base_time + action_time + prerequisite_time + postcondition_time

            # Add resource constraints impact
            if 'high_cpu' in resource_allocation.get('cpu_requirements', ''):
                total_time *= 1.2  # 20% more time for high CPU usage
            if 'high_memory' in resource_allocation.get('memory_requirements', ''):
                total_time *= 1.1  # 10% more time for high memory usage

            # Format time
            if total_time < 60:
                return f"{total_time}s"
            elif total_time < 3600:
                return f"{total_time//60}m {total_time%60}s"
            else:
                return f"{total_time//3600}h {(total_time%3600)//60}m {(total_time%60)}s"

        except Exception as e:
            logger.error(f"Error estimating execution time: {e}")
            return "unknown"

    def _calculate_mapping_confidence(self, intent: str, action_plan: Dict, context: Optional[Dict]) -> float:
        """Calculate confidence in the intent-to-action mapping"""
        try:
            confidence_factors = []

            # Factor 1: Intent recognition confidence
            confidence_factors.append(0.8 if intent != 'unknown' else 0.3)

            # Factor 2: Action plan completeness
            actions = action_plan.get('actions', [])
            confidence_factors.append(min(1.0, len(actions) / 10.0))  # Normalize to 0-1

            # Factor 3: Resource availability
            resource_count = len(action_plan.get('resources_needed', []))
            confidence_factors.append(min(1.0, resource_count / 10.0))

            # Factor 4: Context availability
            if context and isinstance(context, dict):
                context_keys = len(context.keys())
                confidence_factors.append(min(1.0, context_keys / 20.0))
            else:
                confidence_factors.append(0.5)

            # Calculate weighted average
            if confidence_factors:
                confidence = sum(confidence_factors) / len(confidence_factors)
            else:
                confidence = 0.5

            # Ensure confidence is between 0 and 1
            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error(f"Error calculating mapping confidence: {e}")
            return 0.5

    def _fallback_mapping(self, intent: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Fallback mapping when primary mapping fails"""
        return {
            'action_plan': {
                'intent': intent,
                'description': f'Fallback action plan for {intent}',
                'actions': ['general_action'],
                'prerequisites': [],
                'postconditions': [],
                'constraints': [],
                'resources_needed': ['default_resources']
            },
            'resource_allocation': {
                'tool_requirements': ['general_tools'],
                'memory_requirements': 'normal',
                'cpu_requirements': 'normal',
                'time_requirements': 'normal',
                'user_interactions': [],
                'dependencies': []
            },
            'execution_sequence': [{
                'step': 1,
                'action': 'execute_general_action',
                'description': 'Execute general action',
                'resources': ['default_resources'],
                'estimated_time': '60s'
            }],
            'estimated_time': "60s",
            'confidence': 0.3
        }

    def update_action_templates(self, new_templates: Dict[str, Any]) -> bool:
        """Update action templates"""
        try:
            self.action_templates.update(new_templates)
            return True
        except Exception as e:
            logger.error(f"Error updating action templates: {e}")
            return False

    def get_execution_history(self) -> List[Dict]:
        """Get execution history"""
        return self.decision_history.copy()

    def clear_execution_history(self) -> bool:
        """Clear execution history"""
        try:
            self.decision_history.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing execution history: {e}")
            return False


def main():
    """Main execution function for testing the intent to action mapper"""
    print("Intent to Action Mapper Skill")
    print("=" * 40)

    # Initialize the skill
    skill = IntentToActionMapper()

    # Test with sample intents
    test_intents = [
        "analyze_request",
        "explanation_request",
        "problem_solving_request",
        "creation_request",
        "help_request",
        "information_request"
    ]

    print("Testing intent to action mapping capabilities:")
    print()

    for i, intent in enumerate(test_intents, 1):
        print(f"Test {i}: Intent '{intent}'")

        # Map intent to actions
        result = skill.map_intent_to_actions(intent)

        print(f"  Action Plan: {result.get('action_plan', {}).get('description', 'N/A')}")
        print(f"  Actions: {result.get('action_plan', {}).get('actions', [])[:3]}...")  # Show first 3 actions
        print(f"  Estimated Time: {result.get('estimated_time', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        print()

    print("Intent to Action Mapper Skill test completed.")
    print()

    # Test with custom context
    print("Testing with custom context:")
    context = {
        'previous_actions': ['identify_module'],
        'expected_outcome': 'generate_report',
        'module_type': 'sale'
    }

    result = skill.map_intent_to_actions("analyze_request", context)
    print(f"  With context - Actions: {result.get('action_plan', {}).get('actions', [])}")
    print(f"  With context - Confidence: {result.get('confidence', 0):.2f}")


if __name__ == "__main__":
    main()