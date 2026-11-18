---
name: capability-twin-orchestrator
description: Orchestrates Odoo 19 functional analysis using the Capability Twin 6+3+4+N framework. Use for comprehensive module analysis, gap identification, and solution design.
---

# Capability Twin Orchestrator

The central brain for Odoo 19 native functional research. It coordinates specialized agents to transform customer intents into delivered solutions.

## Core Framework
- **Workflow**: Standardized 6+3+4+N analysis process. See [workflows.md](references/workflows.md).
- **Architecture**: 5-Layer Enterprise Architecture (Industry to Code). See [architecture.md](references/architecture.md).
- **FDE Checkpoints**: The 9-item FDE review checklist is attached to existing steps in all four pipelines (Steps 2, 6, 7, 9, 10, 12, 13 and Customization Step 4). See [workflows.md](references/workflows.md) § "FDE 2.0 Checkpoints"; these are checkpoints, not new phases.
- **BDD Spec Gate**: Business scenarios live in `skills/gherkin-bdd/features/*.feature` (single source of truth). The orchestrator enforces it at three boundaries — preflight, Step 10→11, and bundle rendering — via [bdd_gate.py](scripts/bdd_gate.py). A failing spec stops the pipeline (`status: blocked`) instead of packaging unvalidated deliverables.

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
    "detail_level": "comprehensive",
    "bdd": {                          # optional; these are the defaults
        "enabled": True,
        "blocking": True,
        "features_dir": "skills/gherkin-bdd/features",
        "output_dir": "capability_twin_runs/bdd"
    }
})
```

### 3. BDD Gate Semantics
| Field | Meaning |
|---|---|
| `status` | `pass` / `fail` / `missing` / `disabled`; workflow-level `blocked` when a gate stops the run |
| `satisfies_module` | `true` only when this module's own `.feature` passed; a repo-wide baseline pass is **not** a module sign-off |
| `derived` | UAT / step stubs / traceability matrix generated from the validated spec |
| `blocked_at` | Which mounted gate stopped the run (`G2 preflight` or `G2, Step 10→11`) |
| `blocked_templates` | Scenario-dependent deliverables skipped during packaging |

`bdd.blocking=false` is for drafts only: it records the failure but lets analysis continue.
Never use it to claim G2/G3 completion.

## Best Practices
- **Supply-Side First**: Always understand what Odoo does natively before proposing customization.
- **Traceability**: All findings must trace back to Odoo source code (via `technical-analysis-agent`).
- **Knowledge Persistence**: Results are stored in the `kb/` directory for future reuse.
- **FDE Discipline**: At mounted checkpoints record pass / fail / n/a + evidence; never equate "delivered" with "value realized", and never add a weighted score or maturity grade (`fde-methodology`).

## Dependencies & Installation

This skill is not standalone. Install the whole suite so sibling skills resolve:

```bash
npx skills add <owner>/<repo> --all      # recommended
npx skills add <owner>/<repo> --skill capability-twin-orchestrator  # will fail loudly without the rest
```

Required siblings: `gherkin-bdd` (spec gate engine + `.feature`), `template-processor`
(16 deliverable templates), `quality-gate` (gate checks). Missing dependencies raise
`SkillNotFound` with the exact install command — there is no silent fallback.

Path resolution is centralised in [framework_paths.py](scripts/framework_paths.py) and works in
both layouts: repository (`<repo>/skills/<skill>/`) and installed (`<project>/.claude/skills/<skill>/`).
Runtime artifacts always go to the workspace (`CAPABILITY_TWIN_WORKSPACE` or CWD), never into the skill tree.

## Resources
- **Scripts**: [main.py](scripts/main.py) (Orchestration logic), [bdd_gate.py](scripts/bdd_gate.py) (Gherkin spec gate adapter), [framework_paths.py](scripts/framework_paths.py) (path resolution)
- **Agents**: [agents/](agents/) (18 prompt agents, shipped inside this skill)
- **Registry**: [capability_registry.json](capability_registry.json)
- **Methodology**: [fde-methodology/SKILL.md](../fde-methodology/SKILL.md) (9-item review checklist, output contract, anti-patterns)
- **Scenario spec**: [gherkin-bdd/SKILL.md](../gherkin-bdd/SKILL.md) (single source of truth, validation codes, step stubs)
