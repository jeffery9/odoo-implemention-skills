# 用户验收测试 (UAT) 脚本：{{scenario_name}}

> 本脚本由 `.feature` **派生**，禁止手工编辑步骤；任何修改请回到规格文件后重新生成。

- **来源规格**: `{{gherkin_feature_path}}`
- **场景编号**: {{scenario_id}}
- **生成命令**: `python3 skills/gherkin-bdd/scripts/gherkin_gate.py uat <features_dir> -o <output_dir>`
- **生成结果**: `{{generated_uat_path}}`
- **规格门禁报告**: `{{gated_report_path}}`

---

## 1. 测试用例基本信息
- **用例编号**: UAT-{{scenario_id}}-01
- **测试场景**: {{scenario_description}}
- **前置条件**: {{test_prerequisites}}（背景步骤由规格文件提供，不在本表重复维护）
- **质量门归属**: {{gate_level}}（G2 工程完成 / G3 业务验收）

---

## 2. 测试步骤与预期结果

<!-- 由 gherkin_gate.py uat 生成的表格整块注入；不要在此手工另写一套步骤 -->

{{generated_uat_table}}

---

## 3. 验收确认
- **验收人**: ________________
- **验收日期**: 202X-XX-XX
- **遗留问题 (Issues)**:
  - 无（如有遗留问题，由验收人在签字前追加，并注明责任方与关闭日期）

---

## 4. 边界声明

> **交付验收 ≠ 价值实现**：本脚本通过仅代表该场景的交付验收（G3）或工程完成（G2），
> 不代表客户已获得预期业务改善。价值三态（基线 / 目标 / 实测）另按 FDE 2.0 §5.3–5.5 记录，
> 价值裁定独立于交付方。

---
*Capability Twin 3.5 | Quality Assurance & Sign-off | Gherkin BDD derived*
