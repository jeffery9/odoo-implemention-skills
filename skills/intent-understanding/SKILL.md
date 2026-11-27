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

## Boundary with the other intent skills
This is the **entry point** for intent parsing: it classifies the request and maps it to a
`6+3+4+N` workflow. It does not compute evidence-backed confidence, nor does it map a
confirmed intent to capability actions.

- `enhanced-intent-understanding`: use only when the classification needs an explicit
  confidence derivation and a `mapping_ready` verdict.
- `intent-to-action-mapper`: use only after `mapping_ready=true`; it maps a confirmed
  intent to capabilities and never re-judges the intent itself.

The three skills form a one-way chain; do not call the downstream skills from this entry
point without the upstream verdict.

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

## Dependencies & Installation
Requires the sibling `capability-twin-orchestrator` skill (ability registry and shared modules).
Install the suite rather than this skill alone:

```bash
npx skills add <owner>/<repo> --all
```

If the sibling is absent, import fails immediately with the exact install command — no silent degradation.

## Best Practices
- **Prefer Explicit**: If the user provides a module name, use it.
- **Clarification First**: If the request is too vague ("Analyze Odoo"), ask for a specific module or business goal.
- **Bi-directional Focus**: If the user mentions "gaps" or "requirements", prioritize `gap_analysis` workflow.
