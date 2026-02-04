---
name: source-traceability
description: Verifies that analysis conclusions are directly traceable to Odoo 19 source code. Use to audit technical claims or find the physical location of a business capability in the codebase.
---

# Source Traceability

Ensures that every functional "Capability" is backed by actual Odoo 19 code.

## Key Functions
1. **Source Mapping**: Connect business concepts to specific file paths (models, views, etc.).
2. **Audit Trail**: Provide code snippets or line references for technical claims.
3. **Pattern Verification**: Confirm if a suggested usage pattern exists in the Odoo standard.

## Usage
Provide a capability ID or function name to trace its origin.

```python
Skill("source-traceability", params={
    "target_module": "project",
    "capability_id": "task_dependency_management"
})
```
