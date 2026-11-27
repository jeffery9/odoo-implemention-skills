# 实施配置手册：{{scenario_name}}

## 1. 场景配置目标 (Configuration Goal)
*本手册指导顾问如何在 Odoo 19 中通过标准配置实现 {{scenario_name}}。*

- **业务价值**: {{business_value}}
- **涉及应用**: {{odoo_apps}}

---

## 2. 关键配置步骤 (Step-by-Step Setup)

### 2.1 基础参数设置
1. 进入 **{{app_name}} > 配置 > 设置**。
2. 勾选 **{{setting_name}}** 选项。
3. *[顾问提示]: {{setup_tip_1}}*

### 2.2 主数据准备
- **产品配置**: 确保 {{product_category}} 下的产品启用了 {{tracking_method}}。
- **路线/库位**: 配置名为 "{{route_name}}" 的推送路线。

### 2.3 业务规则引擎 (Rules)
- **自动化动作**: 创建一个名为 "{{action_name}}" 的自动化动作，触发条件为 {{trigger_condition}}。

---

## 3. 官方 Pattern 最佳实践
*基于 Odoo 19 官方建议的配置模式：*
- **模式名称**: {{official_pattern_name}}
- **配置要点**: {{pattern_conf_points}}

---

## 4. 常见陷阱与排产 (Pitfalls & Troubleshooting)
- ⚠️ **风险 A**: {{pitfall_a}}
- ⚠️ **风险 B**: {{pitfall_b}}

---

## 5. 证据与溯源 (Evidence & Traceability)
- **结论依据**: {{evidence_basis}}
- **源码/材料锚点**: {{source_anchor}}
- **验收记录**: {{acceptance_record}}

---
*Capability Twin 3.5 | Implementation Specialist Tool*
