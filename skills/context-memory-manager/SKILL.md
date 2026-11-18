---
name: context-memory-manager
description: Manages the framework's memory layers (Working, Episodic, Semantic) based on OpenClaw practices. Use to persist facts, recall usage patterns, or snapshot run states.
---

# Context Memory Manager (OpenClaw Style)

Implements a tiered memory system to ensure consistent Odoo 19 delivery.

## Memory Layers
1. **Working Context**: Live variables in the orchestrator.
2. **Episodic Snapshot**: Historic run data in `kb/mem/snapshots/*.jsonl`.
3. **Semantic Facts**: Persistent Odoo truths in `kb/mem/long_term_facts.jsonl`
   (usage patterns go to `kb/mem/usage_patterns.jsonl`).

All paths are relative to the **user workspace** (`CAPABILITY_TWIN_WORKSPACE`, or the
current working directory when unset) — never to the directory the skill was installed in.

## Core Operations
- **Remember** (`category=fact|pattern`): append one JSONL line. Append-only, so history
  is auditable; `recall` returns the latest write per key.
- **Recall**: fetch knowledge by optional key substring (case-insensitive).
- **Snapshot** (`run_id`, `context`): freeze the current state for error recovery or auditing.

## Failure Behaviour
Errors are reported as `{"status": "error", "message": ...}` instead of being swallowed:
an unknown `category` or `operation`, an empty `key` / `run_id`, and a corrupted JSONL line
(with file and line number) all fail loudly. Silent success on a bad request loses data.

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
