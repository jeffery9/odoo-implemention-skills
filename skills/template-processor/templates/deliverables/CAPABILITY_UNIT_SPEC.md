# 能力单元规范：{{unit_id}}

## 1. 业务价值洞察 (Human-Centric Insight)
- **核心意图**: {{business_intent}}
- **使用场景 (维度1)**: {{usage_scenario}}
- **使用方式与流程节点 (维度2)**: {{usage_method}}
- **老板价值**: {{value_to_owner}}
- **顾问心得**: {{consultant_tip}}

---

## 2. 三流深度解析 (3-Flows Alignment)
- **信息流 (Information Flow)**: *[描述单据链条，如：销售订单 → 制造订单 → 工单的指令流转及状态同步]*
- **物流/实流 (Logistics Flow)**: *[描述物理移动，如：原材料从原材料仓到生产线，再到产成品仓的物理轨迹]*
- **资金流/价值流 (Value Flow)**: *[描述会计影响，如：在制品的成本累计、完工后的入库成本结转及差异分摊]*

---

## 3. 操作与控制要求 (Ops & Control)
- **权限组要求 (维度3)**: {{permission_groups}}
- **必需配置项**: {{required_configurations}}

---

## 4. 物理证据与技术代差 (Evidence & V19 Diff)
- **Odoo 19 差异化代差 (维度4)**: {{v19_diff}}
- **核心模型 (POI)**: {{main_model}}
- **验证场景 (Test POI)**: `{{test_scenario_feature}}`（场景编号：{{scenario_ids}}）
- **场景规格门禁**: `{{gated_report_path}}`（`error=0` 为通过）

> 场景正文以 `.feature` 为唯一事实源，本规范只引用路径与编号，不复制步骤；
> 追溯矩阵由 `gherkin_gate.py matrix` 生成，能力单元与场景为 1:N 绑定。

---

## 5. 复用与集成指南
- **集成切入点 (Hooks)**: `{{method_hook_point}}`
- **复用提示**: {{reusability_notes}}

---
*Persisted in Capability Twin Memory (JSONL) | 100% Traceable*
