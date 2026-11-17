---
name: intent-to-action-mapper
description: 意图到动作映射 - 把已判定的意图展开为可执行动作序列（动作、工具、资源、顺序、依赖与约束），并给出映射置信度
allowed-tools: [Read, Grep, Glob, Bash, Task]
---

# Intent to Action Mapper

把「要做什么」变成「按什么顺序、用什么工具、缺什么资源」。
本技能**不判断意图是否正确**——那是 `intent-understanding` / `enhanced-intent-understanding` 的职责。

## 何时使用

- 意图已判定（`mapping_ready=true`），需要生成执行计划。
- 需要把抽象诉求展开成有依赖关系的动作序列。
- 需要评估动作集所需的工具与资源是否齐备。

## 输入契约

```json
{
  "intent": "gap_analysis",
  "context": {
    "target_module": "account",
    "available_tools": ["Read", "Grep", "Bash"],
    "constraints": ["不得修改源码", "24 小时内出结论"]
  }
}
```

## 输出契约

```json
{
  "status": "success | partial | error",
  "intent": "gap_analysis",
  "action_plan": {
    "actions": [
      {
        "seq": 1,
        "action": "定位 Odoo 原生能力实现位置",
        "tools": ["Grep", "Read"],
        "inputs": ["target_module"],
        "outputs": ["evidence[]"],
        "depends_on": [],
        "parallelizable": true
      }
    ],
    "critical_path": [1, 3, 5]
  },
  "resource_allocation": {"required_tools": ["Grep", "Read"], "missing_tools": []},
  "constraints_check": [{"constraint": "不得修改源码", "satisfied": true, "note": "全部为只读动作"}],
  "mapping_confidence": 0.82,
  "fallback_plan": null
}
```

必填：`action_plan.actions[].depends_on`、`tools`、`outputs`；`constraints_check` 每条约束一项。

## 判据与纪律

- 动作必须**可判定完成**（有 `outputs`），不得出现「进一步分析」这类不可验收动作。
- `depends_on` 必须构成有向无环图；出现环则报 `status=error` 并列出环。
- 约束未满足时 `status=partial`，并在 `constraints_check` 写明冲突点，不得静默忽略。
- `mapping_confidence < 0.6` 时必须提供 `fallback_plan`。
- 缺工具时列入 `resource_allocation.missing_tools`，不得假设工具可用。

## 禁止事项

- 禁止在意图未判定时直接映射（输入必须含 `intent`）。
- 禁止生成修改 Odoo 核心源码的动作。
- 禁止把动作序列写成散文（必须是结构化条目）。
- 禁止用 `mapping_confidence` 作为方案优劣排名依据（FDE §7）。

## 失败与升级

| 情形 | 动作 |
|---|---|
| `intent` 缺失或为 `unclear` | 返回 `status=error`，要求先澄清意图 |
| 动作依赖成环 | `status=error`，列出环上动作 |
| 关键工具缺失 | `status=partial`，给 `fallback_plan` |
| 约束无法同时满足 | 列出冲突约束，交编排器决策 |

## 与其他技能的关系

- 上游：`enhanced-intent-understanding`（`mapping_ready=true`）。
- 下游：`capability-twin-orchestrator` 按 `action_plan` 调度子代理；
  `quality-gate` 可按 `outputs` 校验动作是否真正产出。
