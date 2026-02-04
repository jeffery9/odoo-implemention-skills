---
name: capability-twin-orchestrator
description: Orchestrates Odoo 19 functional analysis using the Capability Twin 6+3+4+N framework. Use for comprehensive module analysis, gap identification, and solution design.
---

# Capability Twin Orchestrator

The central brain for Odoo 19 native functional research. It coordinates specialized agents to transform customer intents into delivered solutions.

## Core Framework
- **Workflow**: Standardized 6+3+4+N analysis process. See [workflows.md](references/workflows.md).
- **Architecture**: 5-Layer Enterprise Architecture (Industry to Code). See [architecture.md](references/architecture.md).

## Usage Guide
This skill analyzes natural language or structured JSON to run workflows.

### 1. Intent OS Recognition
Simply describe what you want to achieve:
- "Analyze Odoo's manufacturing module for a pharma company."
- "Compare our legacy CRM requirements with Odoo 19 native CRM."

### 2. Standard Structured Invocation
```python
Skill("capability-twin-orchestrator", params={
    "target_module": "sale",
    "workflow_type": "full_analysis", # full, supply_side, demand_side, gap
    "detail_level": "comprehensive"
})
```

## Best Practices
- **Supply-Side First**: Always understand what Odoo does natively before proposing customization.
- **Traceability**: All findings must trace back to Odoo source code (via `technical-analysis-agent`).
- **Knowledge Persistence**: Results are stored in the `kb/` directory for future reuse.

## Resources
- **Scripts**: [main.py](scripts/main.py) (Orchestration logic)
- **Registry**: [capability_registry.json](capability_registry.json)
