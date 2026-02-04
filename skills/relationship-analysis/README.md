# Relationship Analysis Skill

## 概述

Relationship Analysis Skill 是一个通用的组件关系分析技能，用于分析模块、组件和能力单元之间的各种关系。

## 功能特性

- 依赖关系分析
- 关联关系识别
- 层次关系映射
- 网络分析和关键节点识别

## 使用方法

### 在代理中调用

```python
# 基础依赖分析
result = Skill("relationship-analysis", config={
    "analysis_type": "dependency_analysis",
    "scope": "project",
    "direction": "bidirectional"
})

# 网络分析
result = Skill("relationship-analysis", config={
    "analysis_type": "network_analysis",
    "scope": ["module1", "module2", "module3"],
    "metrics": ["centrality", "betweenness"]
})
```

## 输出格式

技能返回标准化的JSON格式输出，包含：
- 关系列表
- 网络指标
- 分析摘要
- 关键节点识别

## 集成说明

该技能可被以下代理使用：
- ecosystem-discovery-agent
- comprehensive-analysis-agent
- capability-extractor-agent
- technical-analysis-agent

## 维护

技能由技能维护团队负责维护和更新。