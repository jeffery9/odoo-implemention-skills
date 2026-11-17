# Capability Twin Workflow: 6+3+4+N

This reference documents the standardized multi-phase workflow for Odoo 19 functional analysis.

## Supply-Side Analysis (6 Steps)
Analyze what Odoo *already has*.
1. **Ecosystem Discovery**: Map module dependencies and integration points.
2. **Technical Analysis**: Source code deep-dive (models, workflows, logic).
3. **Function Analysis**: Map code to functional capabilities.
4. **Domain Analysis**: Industry-standard domain logic (Sales, Stock, etc.).
5. **Business Process Analysis**: End-to-end value chain mapping.
6. **Comprehensive Analysis**: Synthesize all supply-side findings.

## Demand-Side Response (3 Steps)
Analyze what the *customer needs*.
7. **Industry Requirements**: Align findings with industry-specific standards.
8. **Solution Architecture**: Design the target technical/functional architecture.
9. **Implementation Guide**: Actionable configuration and implementation steps.

## Gap Analysis (Bi-directional)
*Phase 3.5: Align Supply and Demand to identify gaps.*

## Extraction & Quality Assurance (4 Steps)
Refine and verify results.
10. **Capability Extraction**: Structure findings into reusable "Capability Units".
11. **Delivery Packaging**: Format results for specific stakeholders.
12. **Trustworthiness Audit**: Verify source code traceability.
13. **Human Review**: Final manual validation gate.

## Customization (N Steps)
Iterative development of custom features based on identified Gaps.

## FDE 2.0 Checkpoints (attached, not new phases)

The `fde-methodology` skill is granted at the review and quality-gate steps below.
These are **attached checkpoints, not extra phases**: step numbers, step names and the
`6+3+4+N` structure stay unchanged. At each checkpoint run the 9-item checklist in
`skills/fde-methodology/SKILL.md` §5 and record `pass / fail / n/a + evidence`.

| Pipeline | Mounted steps | Checklist items (§5) | Focus |
|---|---|---|---|
| Supply-Side (6) | 2, 6 | 3, 9 | Source traceability; no second set of facts when synthesizing |
| Demand-Side (3) | 7, 9 | 1, 2 | Problem before solution; falsifiable value with baseline / target / measured |
| Gap Analysis (3.5) | — | 2, 3 | Review lens only; no stage enum, no state field |
| Extraction & QA (4) | 10, 12, 13 | 3, 4, 8 | Evidence over status; dual quality separation; reuse keeps context |
| Customization (N) | 4 | 8, 9 | Reuse metadata; no parallel registry |

Discipline: no weighted score, no maturity grade, no auto-filled human judgement,
no new value-stream stage enum. Output contract and anti-patterns live in
`skills/fde-methodology/SKILL.md` §6–§7; the runtime `task_plan.md` only references
that checklist, it does not duplicate it.
