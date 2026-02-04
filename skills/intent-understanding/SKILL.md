---
name: intent-understanding
description: Translates natural language requests into structured Capability Twin 6+3+4+N workflows. Use to parse user queries like "Analyze inventory gaps" into executable agent plans.
---

# Intent Understanding

The "Intention OS" layer of the Capability Twin framework. It maps human goals to technical workflows.

## Core Capabilities
- **Analysis Mapping**: Convert "analyze", "compare", "audit" into framework steps.
- **Module Detection**: Identify Odoo modules (e.g., "sales" -> `sale`, "warehouse" -> `stock`).
- **Confidence Scoring**: Assess how certain the mapping is and request clarification if needed.

## Workflow Integration
This skill is automatically invoked by the Orchestrator to handle natural language inputs.

```python
Skill("intent-understanding", params={
    "user_input": "I need to understand how Odoo handles manufacturing costs and if it fits our agile model."
})
```

## Reference Material
- **Supported Categories**: Analysis types, focus areas, and detail levels. See [categories.md](references/categories.md).
- **Mapping Logic**: Implementation of Odoo-specific alias detection.

## Best Practices
- **Prefer Explicit**: If the user provides a module name, use it.
- **Clarification First**: If the request is too vague ("Analyze Odoo"), ask for a specific module or business goal.
- **Bi-directional Focus**: If the user mentions "gaps" or "requirements", prioritize `gap_analysis` workflow.
