# Gherkin BDD 接入指南

本文说明 `gherkin-bdd` 如何挂到既有 Capability Twin 3.5 框架上，以及如何在流水线、质量门与 CI 中真实执行。

## 1. 与框架的关系

| 维度 | 结论 |
|---|---|
| 生命周期 | **挂载点**，不新增阶段、不修改 `6+3+4+N` 的步骤编号与名称 |
| 事实源 | `.feature` 是业务场景唯一事实源；16 份交付模板只引用路径或派生结果 |
| 运行时 | 编排器通过 `scripts/bdd_gate.py` 在 preflight、Step 10→11、交付打包三处**真实调用**门禁 |
| 质量门 | `quality-gate` 新增 `scenario_spec` 检查类型，内部委托同一引擎，不复制规则 |
| FDE 对齐 | 交付验收（G3）与价值实现分轨；价值三态另记（§5.3–5.5） |
| 指令变更 | 运行时不改写任何 `SKILL.md` / `AGENT.md`，变更由人评审后合入 |

## 2. 流水线挂载点（运行时行为）

| 既有步骤 | 运行时 hook | 行为 | 产物 / 判据 |
|---|---|---|---|
| Phase 1 → 2 之间 | `execute_workflow` → `_bdd_preflight` | 校验本模块 `.feature`；`fail` 直接返回 `blocked` | `status=pass` 且 `satisfies_module=true` |
| 8 方案架构 | `skills_granted += gherkin-bdd` | 用 Gherkin 写目标业务场景，作为可验收条件 | `.feature` 初稿 |
| 9 实施指南 | 同上 | 场景与实施步骤一一对应，标注 G2 / G3 | 场景清单 |
| 10 能力单元提取 | 同上 | 补 `@ct-unit`，建立能力单元 → 场景 1:N 绑定 | 能力单元规范引用路径 |
| 10 → 11 | `_bdd_gate_stage("G2", derive=True)` | 校验 + 派生 UAT / 步骤桩 / 矩阵；`fail` 立即中止 | `error=0`，`derived.*` 路径 |
| 11 交付打包 | `config["bdd_artifacts"]` | 打包消费已通过门禁的派生件，不另写场景 | UAT 与规格同源 |
| 12 可信性审计 | `skills_granted += gherkin-bdd` | 核对 `@ct-source` 证据可达 | gate JSON 报告 |
| 13 人工复核 | 同上 | 业务方按派生 UAT 签字，G3 由人裁定 | 验收记录 |
| 交付包渲染 | `render_deliverables_bundle` | 场景变量由规格派生；门禁不满足则跳过场景类模板 | `scenario_binding` / `blocked_templates` |
| N 步客制化 第 4 步 | 外部 runner | `pytest-bdd` / `behave` 执行场景，结果回写 G2 | 自动化执行日志 |

`skills/capability-twin-orchestrator/references/workflows.md` 已登记以上挂载点；
FDE 2.0 的 9 项检查点表保持不变。

**回落不算通过**：模块没有 `.feature` 时门禁回落到全仓基线，`satisfies_module=false`。
基线通过只用于发现仓库级回归，不能替该模块背书，也不能渲染该模块的场景类交付物。

## 3. 交付模板改造

三份模板已改为引用 `.feature`，不再维护自然语言副本：

| 模板 | 变量 | 含义 |
|---|---|---|
| `SCENARIO_SOLUTION.md` | `gherkin_feature_path` | 规格路径（唯一事实源） |
| | `gherkin_feature` | Gherkin 正文（超出 6000 字符截断并注明） |
| | `scenario_ids` | 本方案覆盖的场景编号列表 |
| `CONSULTANT_UAT_SCRIPT.md` | `gherkin_feature_path` | 规格路径 |
| | `generated_uat_table` | 由 `scenario_index` 派生的用例表 |
| | `generated_uat_path` / `gated_report_path` | 派生件与门禁报告路径 |
| `CAPABILITY_UNIT_SPEC.md` | `test_scenario_feature` | 场景对应的 `.feature` 路径与编号 |

这些变量现在由 `render_deliverables_bundle` 自动注入（`BDDGate.deliverable_context`）：

- **派生字段优先**：人工传入的 `scenario_name`、`scenario_ids` 等会被规格值覆盖，
  覆盖项记录在 `context_overrides`，避免「模板说 A、规格写 B」。
- **不代填人类判断**：验收人、遗留问题、业务价值等字段一律不自动编造。
- 未通过门禁时跳过 `SCENARIO_SOLUTION` / `CONSULTANT_UAT_SCRIPT`，
  返回 `blocked_templates`；需要草稿可用 `allow_invalid_scenarios=true` 显式放行。

示例（无需再手填场景字段）：

```python
Skill("capability-twin-orchestrator", params={
    "operation": "render_deliverables_bundle",
    "bundle_type": "consultant",
    "target_module": "account",
    "context_data": {"business_acceptance_owner": "财务负责人"},
    "bdd": {"enabled": True, "blocking": True}
})
```

## 4. 质量门与 CI

### 4.1 规格门禁（L1，零依赖，本轮已实测）

两种等价入口：

```bash
# 独立命令
python3 skills/gherkin-bdd/scripts/gherkin_gate.py validate skills/gherkin-bdd/features

# 作为 quality-gate 的检查类型
python3 skills/quality-gate/main.py \
  '{"check_type":"scenario_spec","target_path":"skills/gherkin-bdd/features"}'
```

- 退出码 `0`：`error=0`；`1`：存在 `error`；`2`：入参/路径错误。
- `quality-gate` 复用同一引擎，把结果映射为 `issues` / `gate_decision.blocking_issues`，
  不设加权分数、不产生第二套判定。
- `uat` / `steps` / `matrix` 会先跑校验；规格不合格时**拒绝生成**（草稿可用 `--force`，CI 禁用）。

### 4.2 场景执行（L2，需外部 runner）

`pytest-bdd` / `behave` 不是本仓库依赖，本轮环境未安装，因此 **L2 未在本轮实测**。
接入方式见 `steps/README.md`。G2 证据只认外部 runner 的执行结果，不认「步骤桩已生成」。

### 4.3 CI 片段

```yaml
- name: BDD 规格门禁
  run: |
    python3 skills/gherkin-bdd/scripts/gherkin_gate.py validate skills/gherkin-bdd/features
    python3 skills/gherkin-bdd/scripts/gherkin_gate.py uat skills/gherkin-bdd/features \
      -o capability_twin_runs/uat
    python3 skills/gherkin-bdd/scripts/gherkin_gate.py matrix skills/gherkin-bdd/features \
      -o capability_twin_runs/scenario_matrix.json
- name: 能力单元与流水线接入自测
  run: |
    python3 skills/gherkin-bdd/tests/test_gherkin_gate.py
    python3 skills/capability-twin-orchestrator/tests/test_bdd_pipeline.py
- name: 场景自动化（可选，需安装 pytest-bdd）
  run: |
    python3 skills/gherkin-bdd/scripts/gherkin_gate.py steps skills/gherkin-bdd/features \
      -o capability_twin_runs/steps
    pytest capability_twin_runs/steps -q
```

最后一步在步骤桩未实现时会**显式失败**，这符合「不假绿」纪律：
先把场景写成规格，再逐步实现步骤，直到全绿，才构成 G2 证据。

## 5. 迁移路径（已有自然语言场景）

1. 从 `SCENARIO_SOLUTION` / `CONSULTANT_UAT_SCRIPT` 中抽取「前置 / 动作 / 期望」三步。
2. 按词表把技术表述替换为标准业务词；补齐 4 个必填标签与唯一 `@ct-id`。
3. 运行 `validate --allow-en` 检查迁移期残留（英文关键字降级为 warning）。
4. 用 `uat` 生成新 UAT，人工比对旧用例覆盖度，差异写入遗留问题。
5. 移除模板中的自然语言副本，只保留规格路径引用。

## 6. 边界声明

- 不把 Gherkin 场景当成需求文档的全部：业务价值、约束、方案架构仍在对应交付模板中。
- 不为通过校验而放宽规则：`--allow-en` 与 `--force` 仅限迁移期 / 草稿期。
- 不把 G3 人工裁定自动化；不把 UAT 签字等同于价值实现。
- 门禁只做**判定与派生**，不改写规格、不修改被测代码、不向交付物写入无依据结论。

## 7. 本轮验证记录

| 项 | 结果 |
|---|---|
| 示例规格校验 | 2 features / 5 scenarios / 21 steps，errors=0，warnings=0，退出码 0 |
| 能力单元自测 | 23 / 23 通过（含 15 条规则的违规检出、生成器语法编译、CLI 退出码、拒绝派生） |
| 生成链路 | UAT ×2、pytest-bdd 步骤桩 ×2、behave 步骤桩 ×2、追溯矩阵 ×1 |
| 外部 runner | 未安装，L2 执行未在本轮实测（已显式声明，不计入通过项） |
| 注册表 | 新增 `gherkin-bdd` 后重建 `capability_registry.json` |
