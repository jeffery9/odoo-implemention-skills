# Intent Understanding Skill

Advanced intent recognition and interpretation skill that processes user inputs to understand their underlying intentions and map them to appropriate Capability Twin workflows. This skill analyzes text, parameters, and context to determine the most suitable analysis workflow type.

## Overview

The Intent Understanding skill provides sophisticated natural language processing capabilities to interpret user requests and map them to the appropriate Capability Twin workflow. It serves as an intelligent intermediary that converts natural language requests into structured workflow parameters.

### Key Features

- **Natural Language Processing**: Understands user requests in natural language
- **Intent Classification**: Maps requests to appropriate workflow types (full_analysis, supply_side_analysis, etc.)
- **Module Detection**: Identifies target modules from user input with aliases support
- **Context Awareness**: Considers available modules and user preferences
- **Confidence Scoring**: Provides confidence levels for intent interpretations
- **Clarification Requests**: Identifies when additional information is needed

## Architecture

```
User Input (Natural Language)
        ↓
Intent Understanding Skill
        ↓
Structured Workflow Parameters
        ↓
Capability Twin Orchestrator
```

## Usage

### Basic Usage

```python
import sys
from pathlib import Path

# Add skill directory to path
skill_dir = Path("./.claude/skills/intent-understanding")
sys.path.append(str(skill_dir))

from main import execute_skill

params = {
    "user_input": "Analyze the sales module to understand its capabilities and identify gaps",
    "context": {
        "available_modules": ["sale", "stock", "account"],
        "workflow_preferences": ["supply_side", "demand_side", "gap_analysis"]
    }
}

result = execute_skill(params)
# Result contains intent analysis, confidence scores, and suggested workflow
```

### Example Requests

| User Input | Interpreted Intent |
|------------|-------------------|
| "Analyze the inventory module comprehensively" | `workflow_type`: full_analysis, `target_module`: stock |
| "Technical analysis of accounting module" | `workflow_type`: supply_side_analysis, `analysis_focus`: technical |
| "Extract capabilities from sales analysis" | `workflow_type`: capability_extraction, `target_module`: sale |

## Integration Points

### With Capability Twin Orchestrator

The intent-understanding skill can be integrated with the capability-twin-orchestrator to enable natural language interaction:

```python
# First analyze intent
intent_result = execute_skill(intent_params)

# Then use the suggested workflow
if intent_result['status'] == 'success':
    suggested_workflow = intent_result['suggested_workflow']

    # Execute the actual analysis
    # Note: Import via path-based dynamic loading or sys.path adjustment for hyphenated directories
    # from capability_twin_orchestrator.main import execute_skill as execute_cto
    # ... setup and execute ...
```

### With External Systems

The skill can be used with any system that needs to interpret user intent for Capability Twin workflows.

## Configuration

### Context Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `available_modules` | List[str] | List of available modules for target identification |
| `workflow_preferences` | List[str] | User preferences for workflow types |
| `default_detail_level` | str | Default detail level if not specified ("basic", "medium", "comprehensive") |

## Output Format

The skill returns a structured interpretation of user intent:

```json
{
  "status": "success",
  "confidence": 0.85,
  "intent_analysis": {
    "workflow_type": "full_analysis",
    "target_module": "sale",
    "analysis_focus": ["supply_side", "demand_side", "gap_analysis"],
    "detail_level": "comprehensive"
  },
  "intent_confidence": {
    "workflow_type": 0.9,
    "target_module": 0.85,
    "analysis_focus": 0.8,
    "detail_level": 0.75
  },
  "keywords_identified": ["analyze", "sales", "capabilities", "gaps", "requirements"],
  "clarification_needed": [],
  "suggested_workflow": {
    "workflow_type": "full_analysis",
    "target_module": "sale",
    "detail_level": "comprehensive",
    "sub_agents_config": [...]
  }
}
```

## Best Practices

1. **Provide Context**: Always include relevant context like available modules
2. **Use Specific Terminology**: More specific input yields higher confidence results
3. **Handle Clarifications**: Act on the `clarification_needed` field when confidence is low
4. **Validate Results**: Always check the `confidence` score before proceeding

## Testing

Run the test suite:

```bash
python3 .claude/skills/intent-understanding/test_intent_understanding.py unittest
```

Or run example tests:

```bash
python3 .claude/skills/intent-understanding/test_intent_understanding.py
```

## Integration with 5-Layer Framework

The intent understanding skill maps user requests to the 5-layer enterprise architecture framework:

- **Layer 1**: Industry Requirements → demand_side_analysis, requirements_analysis
- **Layer 2**: End-to-End Business Process → business_process_analysis
- **Layer 3**: Domain Business Process → domain_analysis
- **Layer 4**: Function/Capability → function_analysis, capability_extraction
- **Layer 5**: Solution → solution_architecture, customization

## Integration with 6+3+4+N Workflow

The skill identifies which steps of the 6+3+4+N workflow to execute:

- **Steps 1-6**: Supply-side analysis (ecosystem, technical, function, domain, business process, comprehensive)
- **Steps 7-9**: Demand-side analysis (industry requirements, solution architecture, implementation guide)
- **Steps 10-13**: Capability extraction (extraction, packaging, audit, review)
- **N Steps**: Customization (gap identification, specification, code generation)

## Performance

The skill is designed to be fast and efficient, with typical response times under 100ms for intent analysis. Accuracy depends on the clarity of the user input, with confidence scores providing an indication of interpretation quality.