---
name: knowledge-manager
description: Manages persistent knowledge units for the Capability Twin framework. Use to store, retrieve, or query analysis results, capability units, and business logic patterns.
---

# Knowledge Manager

Handles the lifecycle of technical and functional knowledge within the Odoo 19 research ecosystem.

## Core Operations
- **Store**: Save capability units or analysis findings.
- **Retrieve**: Query existing knowledge based on tags or module names.
- **Cache**: Optimize repeated lookups.

## Usage
Knowledge is stored in the project's `kb/` directory by default.

```python
Skill("knowledge-manager", params={
    "operation": "retrieve",
    "search_query": "negative inventory control",
    "tags": ["stock", "pattern"]
})
```

## Resources
- **Script**: [main.py](scripts/main.py)
- **Base Dir**: Persistent `kb/` directory for long-term knowledge accumulation.
