# Context Memory Manager Skill

Tiered memory for the Capability Twin framework, backed by plain JSONL files under the
user workspace. No database, no vector store, no network dependency.

## Memory layers

| Layer | Where | Written by |
|---|---|---|
| Working | in-process orchestrator state | orchestrator |
| Episodic | `kb/mem/snapshots/<run_id>.jsonl` | `snapshot` |
| Semantic facts | `kb/mem/long_term_facts.jsonl` | `remember` (`category=fact`) |
| Usage patterns | `kb/mem/usage_patterns.jsonl` | `remember` (`category=pattern`) |

`kb/mem/` is resolved against `CAPABILITY_TWIN_WORKSPACE`, falling back to the current
working directory. Installing the skill elsewhere never redirects stored data.

## Operations

```python
Skill("context-memory-manager", params={
    "operation": "remember",
    "category": "pattern",          # fact | pattern
    "key": "mrp_consumption_warning",
    "value": "Uses _action_confirm to trigger stock check hooks",
    "metadata": {"module": "mrp", "version": "19.0"},
})
# -> {"status": "success", "operation": "remember"}

Skill("context-memory-manager", params={
    "operation": "recall",
    "category": "pattern",
    "query": "mrp",                 # optional key substring, case-insensitive
})
# -> {"status": "success", "data": {"mrp_consumption_warning": {...}}, ...}

Skill("context-memory-manager", params={
    "operation": "snapshot",
    "run_id": "cto_20261118_135348_5fdc1bf9",
    "context": {"step": 13},
})
# -> {"status": "success", "operation": "snapshot"}
```

## Semantics

- **Append-only.** `remember` adds one JSONL line; earlier writes are never rewritten, so
  history stays auditable. `recall` returns the **latest** entry per key.
- **Errors are loud.** Unknown `category` / `operation`, empty `key` / `run_id`, and
  corrupted JSONL lines (reported with file and line number) return
  `{"status": "error", "message": ...}`. A misspelled request must not look like success.
- **Small and atomic.** Store verifiable one-liners with source metadata, not document blobs.

## Tests

```bash
python3 -m pytest skills/context-memory-manager -q
```

The test file loads the implementation by path under a unique module name, because every
skill in this repository ships its own `scripts/main.py` and a bare `from main import ...`
would resolve to whichever skill happened to be imported first.
