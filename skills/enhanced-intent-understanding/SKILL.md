---
name: enhanced-intent-understanding
description: 增强意图理解 - 在基础意图识别之上叠加情绪信号、上下文与历史对齐，输出意图类别、置信度分解与澄清问题，用于判断「能否开工」
allowed-tools: [Read, Grep, Glob, Bash]
---

# Enhanced Intent Understanding

`intent-understanding` 的增强版：不只给意图类别，还给**置信度是怎么算出来的**，以及缺什么才能判定。

## 何时使用

- 用户表述含混、情绪化或前后不一致，需要先判断「能不能开工」。
- 需要解释「为什么判成这个意图」，而不只是一个标签。
- 需要跨会话沿用用户偏好（`ContextMemorySystem`）。

若只需基础意图分类且表述清晰，直接用 `intent-understanding`，不必引入本技能。

## 核心能力

| 能力 | 说明 | 入口 |
|---|---|---|
| 意图识别 | 关键词 + 模式匹配，输出意图类别 | `analyze_intent(text, context)` |
| 情绪识别 | 从文本判断焦虑/急迫/犹豫等信号 | `_recognize_emotion` |
| 置信度分解 | 意图强度 / 上下文充分度 / 情绪一致性 / 与历史意图对齐 四项加权 | `_calculate_confidence` |
| 上下文记忆 | 存储与检索上下文、更新用户偏好 | `ContextMemorySystem` |

## 输入契约

```json
{
  "input_text": "客户原话，不得预改写",
  "context": {"available_modules": ["sale"], "workflow_preferences": ["supply_side"], "user_id": "u-001"},
  "original_intent": {"intent": "上一轮的意图判定，用于一致性对齐，可选"}
}
```

## 输出契约

```json
{
  "status": "success | partial | error",
  "intent": "full_analysis | supply_side | demand_side | gap_analysis | customization | unclear",
  "confidence": 0.78,
  "confidence_breakdown": {
    "intent_strength": 0.8,
    "context_sufficiency": 0.7,
    "emotion_alignment": 0.9,
    "history_alignment": 0.7
  },
  "emotion": "urgent | anxious | neutral | null",
  "clarifications_needed": ["缺目标模块：是 sale 还是 stock？"],
  "mapping_ready": true
}
```

必填：`intent`、`confidence`、`confidence_breakdown`、`clarifications_needed`。

## 判据与纪律

- `confidence < 0.6` 或 `clarifications_needed` 非空时，`mapping_ready` 必须为 `false`，
  不得直接进入 `intent-to-action-mapper`。
- `confidence_breakdown` 四项必须与实际计算一致，不得倒推编造。
- 情绪只作为**置信度修正项**，不得单独决定意图。
- 识别不出时输出 `intent=unclear`，不得默认成 `full_analysis`。

## 禁止事项

- 禁止改写用户原话后再判定（保留 `input_text` 原文）。
- 禁止在 `clarifications_needed` 非空时宣称可执行。
- 禁止把置信度当作质量评分对外发布（FDE §7：不做总分）。
- 禁止跨用户混用上下文记忆。

## 与其他技能的关系

- 上游：可由 `intent-understanding` 的初步结果作为 `original_intent` 输入。
- 下游：`mapping_ready=true` → `intent-to-action-mapper`；否则回到用户澄清。
