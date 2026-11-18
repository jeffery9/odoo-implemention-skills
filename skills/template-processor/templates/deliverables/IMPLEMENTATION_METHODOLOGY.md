# 实施方法论：Capability Twin 模式驱动交付体系

## 1. 核心方法论概述
*本项目采用基于 Odoo 19 源码采矿的 6+3+4+N 实施方法论。核心理念是：先挖掘、再对标、后集成。*

- **方法论名称**: Capability Twin 3.5 Pattern-Driven Methodology
- **交付特色**: [源码原生 / 场景化集成 / 100% 溯源 / 持续演化]

---

## 2. 实施阶段划分 (Project Phases)

### Phase 1: 意图对齐与业务建模
- **核心活动**: 使用 Intent OS 拆解客户痛点，定义《项目使命与业务价值》。
- **交付物**: `PURPOSE_AND_STRATEGY.md`

### Phase 2: 源码采矿与双向对标
- **核心活动**: 启动 Capability Twin 引擎，挖掘 Odoo 19 源码模式，执行物理级 Gap 分析。
- **交付物**: `GAP_ANALYSIS_REPORT.md`

### Phase 3: 场景化方案设计
- **核心活动**: 将项目拆解为多个自包含的 Scenario，基于官方 Pattern 构建方案积木。
- **交付物**: `SCENARIO_SOLUTION.md` (多份)

### Phase 4: 敏捷构建与质量门禁
- **核心活动**: 自动化生成代码，执行 Source Traceability 审计，通过 UAT 签字。
- **交付物**: `CONSULTANT_CONF_GUIDE.md`, `UAT_SCRIPT.md`

### Phase 5: 知识沉淀与系统上线
- **核心活动**: 将本次交付的场景方案沉淀至 `kb/mem`，完成全员培训。
- **交付物**: `PROJECT_SOLUTION.md`

---

## 3. 项目治理与质量保证 (Governance)
- **源码追溯机制**: 每一项配置和开发必须绑定物理代码位置。
- **变更控制流程**: 严禁在没有 Gap 报告支持的情况下进行私自定制。
- **沟通机制**: {{communication_plan}}

---

## 4. 风险预警体系
| 风险类别 | 触发条件 | 应对策略 |
| :--- | :--- | :--- |
| **功能幻觉** | 未经源码验证的方案建议 | 激活 `source-traceability` 技能强制审计 |
| **架构冲突** | 自定义逻辑破坏 Odoo 升级路径 | 强制使用官方 Hook 模式重构 |

---
*Capability Twin 3.5 | Delivery Excellence Standard*
