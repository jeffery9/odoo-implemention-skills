# Scenario Solution：{{scenario_name}}

> **业务场景唯一事实源**：`{{gherkin_feature_path}}`（覆盖场景：{{scenario_ids}}）
> 本文件只描述方案、约束与验证安排，**不复制场景步骤**；验收条件以 `.feature` 为准。

## 1. 业务场景描述 (Scenario Context)
*通过“人、事、地、物、时”五维度描述该具体场景；完整前置、动作与期望结果见 Gherkin 规格。*

- **目标角色**: {{target_role}}
- **触发条件**: {{trigger_event}}
- **期望结果**: {{desired_outcome}}

---

## 2. 可执行场景规格 (Executable Specification)

```gherkin
{{gherkin_feature}}
```

- **规格路径**: `{{gherkin_feature_path}}`
- **场景编号**: {{scenario_ids}}
- **统一语言**: 术语以 `skills/gherkin-bdd/references/ubiquitous-language.md` 为准
- **门禁结果**: `{{gated_report_path}}`（以 `error=0` 为通过，warning 只记录不阻断）

---

## 3. 解决方案架构 (Solution Architecture)
*本方案遵循 Odoo 19 官方使用模式构建。*

### 3.1 模式引用 (Official Pattern)
- **引用文档**: {{doc_link}}
- **核心逻辑**: {{pattern_logic_summary}}

### 3.2 技术实现方案
- **涉及模型**: {{models_to_modify}}
- **核心逻辑注入 (The Hook)**:
  - `{{method_hook}}`: *[描述该方法的具体逻辑重写或扩展方式]*
- **UI/UX 调整**: *[描述在该场景下对 View 的优化]*

---

## 4. 约束与边界 (Constraints)
- **数据前提**: {{prerequisites}}
- **负面限制**: *[明确本方案不适用的场景]*

---

## 5. 验证计划 (Validation Plan)

| 层级 | 方式 | 判据 / 产物 |
|---|---|---|
| L1 规格门禁 | `gherkin_gate.py validate` | `{{gated_report_path}}` 中 `error=0` |
| L2 场景自动化 | 由 `steps` 派生的步骤定义 + pytest-bdd / behave | 执行结果全绿（G2 证据） |
| G3 人工验收 | 由 `uat` 派生的验收脚本 | 业务方签字，独立于自动化结果 |

- **关键测试案例**: 见规格文件中的场景编号 {{scenario_ids}}
- **G3 裁定人**: {{business_acceptance_owner}}

> **边界声明**：本方案的通过标准分为「工程完成（G2）」与「业务验收（G3）」两轨；
> 二者均不等于价值实现，价值三态（基线 / 目标 / 实测）另按 FDE 2.0 §5.3–5.5 记录。

---
*Capability Twin Modular Component | Scenario Architect*
