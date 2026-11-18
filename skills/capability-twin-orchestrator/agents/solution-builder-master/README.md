# Solution Builder Master Agent

## 概述

Solution Builder Master是Capability Twin 2.1框架中的高级编排器Agent，负责自动化构建、实施和管理Odoo解决方案。该Agent集成了现有的14个Domain Agents和13个Reusable Skills，提供端到端的解决方案构建能力，并内嵌自适应交付治理引擎。

## 核心功能

### 1. 解决方案自动化构建
- 基于需求自动构建Odoo解决方案
- 集成需求分析、技术分析、方案设计等全流程
- 生成完整的解决方案包和实施指导

### 2. 敏捷实施管理
- 管理解决方案的实施过程
- 支持敏捷迭代式的实施方式
- 提供实时的实施进度监控

### 3. 智能变更处理
- 处理解决方案的变更请求
- 分析变更影响和依赖关系
- 提供安全的变更实施和回滚机制

### 4. 项目管理协调
- 协调项目各阶段的执行
- 自动生成项目管理文档
- 支持风险管理与质量控制

## 架构设计

Solution Builder Master采用分层架构设计：

```
┌─────────────────────────────────────┐
│       Solution Builder Master       │
│     (高级编排层 - 统筹协调)          │
├─────────────────────────────────────┤
│        Domain Agents (14个)          │
│  - capability-twin-orchestrator     │
│  - ecosystem-discovery-agent        │
│  - technical-analysis-agent         │
│  - function-analysis-agent          │
│  - domain-analysis-agent            │
│  - business-process-agent           │
│  - comprehensive-analysis-agent     │
│  - industry-requirements-agent      │
│  - solution-architect-agent         │
│  - implementation-guide-agent       │
│  - capability-extractor-agent       │
│  - delivery-packager-agent          │
│  - trustworthiness-auditor-agent    │
│  - human-review-gatekeeper-agent    │
├─────────────────────────────────────┤
│       Reusable Skills (13个)         │
│  - generic-analyzer                 │
│  - relationship-analysis            │
│  - source-traceability              │
│  - knowledge-manager                │
│  - template-processor               │
│  - data-exchange                    │
│  - quality-gate                     │
│  - cache-management                 │
│  - configuration-management         │
│  - file-operations                  │
│  - autonomous-evolution             │
│  - workflow-orchestrator            │
│  - ecosystem-discovery              │
└─────────────────────────────────────┘
```

## 使用方法

### 基本调用
```python
Agent("solution-builder-master")
```

### 带参数调用
```python
Agent("solution-builder-master", prompt="""
执行解决方案构建：

需求描述: 增强项目管理功能，支持资源分配和进度跟踪
目标模块: project
实施环境: 生产环境
""")
```

## 工作流模式

### 1. 解决方案构建工作流
```
需求分析 → 生态发现 → 技术分析 → 方案设计 → 实施指导 → 能力萃取 → 成果包装 → 可信审计 → 人工复核
```

### 2. 敏捷实施工作流
```
实施准备 → 部署执行 → 进度监控 → 质量验证 → 知识积累 → 项目总结
```

### 3. 变更处理工作流
```
变更识别 → 影响分析 → 变更实施 → 结果验证 → 经验学习 → 知识更新
```

## 集成能力

Solution Builder Master与Capability Twin 2.1框架的其他组件紧密集成：

1. **Domain Agents**: 调用14个专业Domain Agents执行特定分析任务
2. **Reusable Skills**: 利用13个Reusable Skills提供基础设施支持
3. **知识中枢**: 与能力注册中心、映射知识库等知识组件交互
4. **增量学习**: 集成Autonomous Evolution Skill实现自学习优化

## 输出产物

### 1. 解决方案文档
- `solution_design.md` - 解决方案设计文档
- `implementation_guide.md` - 实施指导文档
- `technical_specification.md` - 技术规格文档
- `test_plan.md` - 测试计划文档

### 2. 实施文档
- `implementation_plan.md` - 实施计划文档
- `deployment_script.py` - 部署脚本
- `configuration_guide.md` - 配置指南
- `validation_report.md` - 验证报告

### 3. 项目管理文档
- `project_charter.md` - 项目章程
- `sprint_plan.md` - 迭代计划
- `risk_register.md` - 风险登记册
- `status_report.md` - 状态报告

### 4. 变更管理文档
- `change_request.md` - 变更请求
- `impact_analysis.md` - 影响分析
- `change_plan.md` - 变更计划
- `rollback_plan.md` - 回滚计划

## 最佳实践

### 1. 需求管理
- 尽可能详细地描述需求
- 明确区分功能需求和非功能需求
- 提供业务场景和用户故事
- 指定优先级和验收标准

### 2. 解决方案设计
- 优先考虑重用现有能力单元
- 合理划分定制开发范围
- 考虑系统的可扩展性和可维护性
- 确保设计方案的可行性和合理性

### 3. 实施管理
- 制定详细的实施计划
- 准备充分的测试环境
- 建立有效的监控机制
- 制定应急预案和回滚方案

### 4. 变更管理
- 及时识别和评估变更影响
- 充分测试变更内容
- 确保变更过程的可控性
- 完整记录变更历史

## 故障排除

### 常见问题

#### 1. Agent调用失败
**问题**: 无法调用某个Domain Agent
**解决方案**:
```bash
# 检查Agent是否存在
ls .claude/agents/[agent-name]/

# 检查Agent配置
cat .claude/agents/[agent-name]/AGENT.md
```

#### 2. Skill执行错误
**问题**: Skill执行返回错误
**解决方案**:
```bash
# 检查Skill配置
cat .claude/skills/[skill-name]/SKILL.md

# 查看Skill日志
# (根据具体环境查看日志文件)
```

## 性能优化

### 1. 智能调度
- 基于依赖关系和重要性调度Agent执行
- 动态分配计算资源
- 智能缓存中间结果
- 最大化并行执行效率

### 2. 质量控制
- 在关键节点验证结果质量
- 自动修复常见的质量问题
- 在资源受限时自动降级
- 优雅处理Agent执行失败

## 监控指标

### 执行指标
- **成功率**: 工作流执行成功率
- **响应时间**: 平均执行时间
- **资源利用率**: 计算资源利用率
- **错误率**: 执行错误率

### 质量指标
- **分析深度**: 分析结果的详细程度
- **一致性**: 不同Agent结果的一致性
- **完整性**: 分析结果的完整性
- **可信度**: 结果的可信度评分