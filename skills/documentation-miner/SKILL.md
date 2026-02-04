---
name: documentation-miner
description: Extracts official Odoo usage patterns from documentation. Use to find standard functional workflows (e.g., "MTO flow", "3-way matching") to enrich scenario solutions.
---

# Documentation Miner

Connects the framework to Odoo's official "Functional Bible" to ensure solutions follow standard patterns.

## Core Functions
1. **Pattern Search**: Find how Odoo intends for a specific feature to be used (e.g., "Advanced Route Management").
2. **Contextual Enrichment**: Fetch documentation snippets related to a target business scenario.
3. **Validation**: Verify if a proposed custom flow contradicts official Odoo best practices.

## Usage
Used by `solution-architect-agent` to ground designs in official reality.

```python
Skill("documentation-miner", params={
    "topic": "Consignment stock in Odoo 19",
    "search_depth": "deep"
})
```

## Best Practices
- **Prioritize Odoo 19**: Always look for version-specific changes.
- **Extract Workflows**: Don't just get text; extract step-by-step "Patterns".
- **Link to Code**: Combine with `source-traceability` to find where the doc meets the code.
