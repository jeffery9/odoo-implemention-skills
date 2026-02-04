---
name: context-memory-manager
description: Manages the framework's memory layers (Working, Episodic, Semantic) based on OpenClaw practices. Use to persist facts, recall usage patterns, or snapshot run states.
---

# Context Memory Manager (OpenClaw Style)

Implements a tiered memory system to ensure consistent Odoo 19 delivery.

## Memory Layers
1. **Working Context**: Live variables in the orchestrator.
2. **Episodic Snapshot**: Historic run data in `kb/snapshots/*.jsonl`.
3. **Semantic Facts**: Persistent Odoo truths in `kb/long_term_facts.jsonl`.

## Core Operations
- **Remember**: Store an atomic fact or pattern.
- **Recall**: Fetch knowledge based on a query.
- **Snapshot**: Freeze the current state for error recovery or auditing.

## Usage Example
```python
Skill("context-memory-manager", params={
    "operation": "remember",
    "category": "pattern",
    "key": "mrp_consumption_warning",
    "value": "Uses _action_confirm to trigger stock check hooks",
    "metadata": {"module": "mrp", "version": "19.0"}
})
```

## Best Practices
- **Atomic Facts**: Don't store large blobs; store small, verifiable truths.
- **Metadata Tagging**: Always include the source module and Odoo version.
- **Recall Before Decide**: Always `recall` relevant patterns before starting a new `solution-architecture` task.
