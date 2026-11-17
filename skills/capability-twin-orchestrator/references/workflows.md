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

## Business Scenario Contract (Gherkin BDD, attached not new phases)

业务场景统一用 `zh-CN` Gherkin 描述，规格位于 `skills/gherkin-bdd/features/`。
`.feature` 是唯一事实源；UAT 脚本、追溯矩阵、步骤定义全部由 `gherkin_gate.py` 派生，
模板与交付物不复制场景正文。以下同样是**挂载点，不新增阶段、不改 `6+3+4+N` 编号**。

这些挂载点不只是文档约定，运行时由 `scripts/bdd_gate.py` 在下列位置真实调用：

| Pipeline | Mounted steps | Runtime hook | Action | Pass criterion |
|---|---|---|---|---|
| All workflows | preflight（Phase 1 之后、Phase 2 之前） | `execute_workflow` → `_bdd_preflight` | 校验本模块 `.feature`，`fail` 直接阻断整条流水线 | `status=pass` 且 `satisfies_module=true` |
| Demand-Side (3) | 8, 9 | `skills_granted += gherkin-bdd` | 用场景写可验收条件，标注 G2 / G3 | `validate` 退出码 0 |
| Extraction & QA (4) | 10 → 11 | `_bdd_gate_stage(stage="G2", derive=True)` | 补 `@ct-unit`；通过后派生 UAT / 步骤桩 / 矩阵并交给打包步骤 | `error=0`；失败即中止，不进入打包 |
| Extraction & QA (4) | 11 | `config["bdd_artifacts"]` | 打包消费已通过门禁的派生件，不另写场景 | UAT 与规格同源 |
| Extraction & QA (4) | 12 | `skills_granted += gherkin-bdd` | 核对 `@ct-source` 证据与门禁报告 | `error=0` |
| Extraction & QA (4) | 13 | `skills_granted += gherkin-bdd` | 业务方按派生 UAT 签字 | G3 人工裁定 |
| Delivery packaging | `render_deliverables_bundle` | 同引擎，`stage="G3-derive"` | 场景变量由规格派生；未通过则跳过 `SCENARIO_SOLUTION` / `CONSULTANT_UAT_SCRIPT` | `satisfies_module=true`，否则模板计入 `blocked_templates` |
| Customization (N) | 4 | `_bdd_gate_stage(stage="G2-customization")` + 外部 runner | 注册前复核规格仍成立；`pytest-bdd` / `behave` 执行场景 | `error=0` 且执行全绿，构成 G2 证据 |

Discipline:
- `validate` 存在 `error` 时拒绝派生 UAT / 步骤桩 / 矩阵；`--force` 仅限草稿期。
- **回落不算通过**：模块无 `.feature` 时门禁回落到全仓基线，`satisfies_module=false`。
  基线通过只用于发现仓库级回归，不能替该模块背书，也不能渲染该模块的场景类交付物。
- 门禁失败即中止（fail-fast），不允许「先打包、后补规格」。
- 生成物不等于测试通过；未实现的步骤必须显式失败。
- 自动化通过 = G2；交付验收 ≠ 价值实现（FDE 2.0 §5.5）。
- 运行时不改写任何 `SKILL.md` / `AGENT.md`，指令变更由人评审后合入。

Runtime contract（返回给调用方的字段）:

```json
{
  "status": "pass | fail | missing | disabled | blocked",
  "satisfies_module": true,
  "scope": "module:account | baseline | explicit",
  "errors": 0, "warnings": 0,
  "coverage": {"by_module": {}, "by_gate": {}, "by_unit": {}, "scenarios_without_unit": []},
  "derived": {"uat_dir": "", "steps_dir": "", "matrix": ""},
  "report_path": "capability_twin_runs/bdd/<module>/gherkin_gate.json"
}
```

调用方可显式关闭或放开（仅草稿场景）：

```python
{"target_module": "mrp", "bdd": {"enabled": True, "blocking": False,
                                 "features_dir": "skills/gherkin-bdd/features",
                                 "output_dir": "capability_twin_runs/bdd"}}
```

