# 知识资产交接清单 (Knowledge Asset Manifest)

## 1. 项目基本信息
- **项目名称**: {{project_name}}
- **交付日期**: {{delivery_date}}
- **Odoo 版本**: 19.0 ({{edition}})

---

## 2. 移交的知识资产 (Mined Assets)

### 2.1 持久化能力单元 (Capability Units)
*已存入 `kb/mem/long_term_facts.jsonl` 的核心单元：*
- **单元 ID**: {{unit_ids}}
- **核心模式**: {{mined_patterns}}

### 2.2 场景解决方案 (Scenario Solutions)
*每一个方案均基于官方 Pattern 并包含 Source Traceability 审计。*
1. [{{scenario_1_id}}] {{scenario_1_name}}
2. [{{scenario_2_id}}] {{scenario_2_name}}

---

## 3. 技术环境与源码参考
- **源码挖掘路径**: `{{odoo_source_path}}`
- **运行快照**: `kb/mem/snapshots/{{last_run_id}}.jsonl`

---

## 4. 价值三态与验收边界 (Value States & Boundary)
- **基线 (Baseline)**: {{value_baseline}}
- **目标 (Target)**: {{value_target}}
- **实测 (Measured)**: {{value_measured}}
- **测量来源**: {{value_measurement_source}}

> 交付验收 ≠ 价值实现。本节只记录可核验的价值三态与证据，不代替客户侧价值裁定
> （FDE 2.0 §5.5）；无基线时如实写「无基线」，不编造数字。

---

## 5. 接收确认
- **甲方接收人**: ________________
- **乙方交付人**: ________________

---
*Capability Twin 3.5 | Digital Asset Sovereignty*
