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
    },
    "ontology": {                     # optional; enabled by default
        "enabled": True,
        "hops": 1,                    # subgraph expansion depth
        "max_nodes": 40,              # bounded context, not the whole graph
        "carrier": None               # python | view | owl
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

### 4. Step Evidence Contract (A-level)
A delegated step is **not** complete just because its status says `success`. Every step
returns `evidence_contract` and stays `delegated` until evidence is submitted and validated:

```python
execute_skill({
    "operation": "submit_step_evidence",
    "workflow_id": "<from workflow result>",
    "step": 2,
    "evidence": {
        "workflow_id": "<same workflow_id>",
        "step": 2,
        "artifacts": [{"path": "capability_twin_runs/.../report.md",
                       "kind": "report",
                       "anchor": "addons/account/models/account_move.py:L128"}],
        "fde_records": [{"item": i, "result": "pass|fail|n/a", "evidence": "..."}
                        for i in range(1, 10)],
        "ontology_consumption": {
            "fingerprint": "<ontology_contract.fingerprint>",
            "mode": "used",
            "node_ids": ["<allowed_node_id>"],
            "anchors": ["<allowed source_anchor>"],
            "statement": "本体子图中的哪条框架级关系支撑了本步骤结论"
        },
    },
})
```

The workflow result carries `step_registry` (path under `capability_twin_runs/<workflow_id>/`)
and `evidence_submission_hint`. Step registration is persisted at workflow finalization and
restored by `workflow_id` on a new instance — the host does **not** need to keep the original
process alive. `operation=workflow_outcome` with the same `workflow_id` re-reads the current
outcome. A missing, corrupt or out-of-bounds registry fails closed: no empty registry is
created, and the step stays `delegated`.

`evidence_gate` checks artifact existence, non-empty files, traceability anchors, the
9-item FDE checklist and `ontology_consumption`. Only a `pass` report promotes the step
to `success` and fills `fde_checkpoint.recorded=true`; any `fail` item blocks promotion.
`status=completed` is returned only when all steps are evidence-validated.
`workflow_outcome.ontology_consumption` reports required / validated / pending steps and
the per-mode counts, so "the ontology was reachable" can never be confused with
"agents actually used it".

## 5. Ontology Context Layer (read-only)

The orchestrator attaches an **anchored semantic subgraph** to `shared_context["ontology"]`
during preflight, before any sub-agent runs. Every sub-agent therefore reasons from the same
bounded view of the Odoo application (models, fields, views, actions, menus, groups, rules,
ACLs and Python/View/OWL logic) instead of rediscovering it from scattered sources.

| Field | Meaning |
|---|---|
| `status` | `ok` / `open-question` / `unavailable` / `disabled`; never silently empty |
| `subgraph.nodes` | Nodes with physical `source_anchor`; truncated to `ontology.max_nodes` |
| `subgraph.edges` | Only edges whose both endpoints survive truncation |
| `anchors` | Sorted `file:line` / `file:record:xmlid` anchors for citation |
| `open_questions` | Unresolved bindings or "ontology not built"; never fabricated |
| `consumption` | `read-only reasoning context; not step evidence` |
| `ontology_contract` | Step-level binding: `fingerprint`, `allowed_modes`, `allowed_node_ids`, `allowed_anchors` |

Rules:

- The ontology is a **derived projection** (`ontology/`), not a second source of truth.
  It does not fill `capabilities: {}` and does not replace `.feature` or source anchors.
- No manifest or no query script ⇒ `status=unavailable` + `open-question`. An unbuilt
  ontology is **not** an empty green graph.
- Explicit `ontology.enabled=false` is the only way to disable it; drafts must say so.
- The subgraph itself is reasoning input only: it never replaces a step artifact, source
  anchor, FDE record or `.feature` spec, and its `status` never changes workflow `status`.
- Its **usage record** is mandatory. Every delegated step receives `ontology_contract`
  and must return `ontology_consumption` bound to that contract's fingerprint:
  `mode=used` cites in-subgraph `node_ids` + `source_anchors` plus a concrete `statement`;
  `mode=not_applicable` requires a specific `reason`; `open-question` / `unavailable` /
  `disabled` must be reported honestly. Missing, stale or fabricated records fail the
  evidence gate and keep the step `delegated`.

The result carries `ontology_context` (a small fingerprint) and
`workflow_outcome.ontology_consumption` (closure counts); the full subgraph stays in
`final_shared_context["ontology"]`.

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
- **Scripts**: [main.py](scripts/main.py) (Orchestration logic), [evidence_gate.py](scripts/evidence_gate.py) (step evidence contract + validation), [bdd_gate.py](scripts/bdd_gate.py) (Gherkin spec gate adapter), [ontology_context.py](scripts/ontology_context.py) (bounded ontology subgraph adapter), [framework_paths.py](scripts/framework_paths.py) (path resolution)
- **Ontology**: `ontology/` at framework root is a generated, do-not-edit projection; query it with `python scripts/ontology_lookup.py --module <module>`
- **Agents**: [agents/](agents/) (18 prompt agents, shipped inside this skill)
- **Registry**: [capability_registry.json](capability_registry.json)
- **Methodology**: [fde-methodology/SKILL.md](../fde-methodology/SKILL.md) (9-item review checklist, output contract, anti-patterns)
- **Scenario spec**: [gherkin-bdd/SKILL.md](../gherkin-bdd/SKILL.md) (single source of truth, validation codes, step stubs)
