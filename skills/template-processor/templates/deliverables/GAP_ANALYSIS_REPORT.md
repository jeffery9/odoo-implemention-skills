# Capability Twin：业务需求差距与模式对标报告

## 1. 交付目标 (Target Alignment)
*对比客户意图与 Odoo 19 物理实现的对标结论。*

- **客户意图 (Intent)**: {{user_intent}}
- **对标模块**: {{target_module}}
- **原生覆盖率**: {{coverage_percentage}}%

---

## 2. 模式对标矩阵 (Pattern Matching Matrix)

| 业务需求场景 | Odoo 官方 Pattern | 匹配状态 | 详细说明 |
| :--- | :--- | :--- | :--- |
| {{requirement_1}} | {{official_pattern_1}} | [✅/⚠️/❌] | {{matching_details_1}} |
| {{requirement_2}} | {{official_pattern_2}} | [✅/⚠️/❌] | {{matching_details_2}} |

**状态定义**:
- ✅ **原生匹配**: 直接通过配置即可实现。
- ⚠️ **配置缺口**: 需要通过 Studio 或 Automated Actions 进行轻量级增强。
- ❌ **研发缺口**: Odoo 官方目前无此逻辑模式，必须定制开发。

---

## 3. 核心 Gap 深度解析
*针对标记为 ❌ 的研发缺口，提供源码级的技术解释。*

### 3.1 Gap: {{gap_title}}
- **需求痛点**: {{gap_pain_point}}
- **原生局限性**: *[引用 Odoo 19 源码中的具体缺失点]*
- **冲突评估**: *[描述自定义该逻辑是否会破坏 Odoo 的官方升级路径]*

---

## 4. 差距桥接策略 (Bridging Strategy)
- **推荐方案**: {{recommended_approach}}
- **实施成本估算**: [低/中/高]
- **维护性评估**: {{maintenance_impact}}

---
*Capability Twin 3.5 | Gap Analyzer Agent*
