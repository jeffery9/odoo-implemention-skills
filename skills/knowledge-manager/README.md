# Knowledge Manager Skill

## 概述

Knowledge Manager Skill 是一个专业的知识管理技能，负责管理分析过程中产生的知识，提供缓存、检索、存储和知识库管理功能。

## 功能特性

- **知识存储**: 支持结构化知识的持久化存储
- **知识检索**: 基于关键词的智能检索功能
- **缓存管理**: 智能缓存策略避免重复计算
- **生命周期管理**: 知识条目的创建、更新、删除管理

## 使用方法

### 在代理中调用

```python
# 存储知识
result = Skill("knowledge-manager", config={
    "operation": "store",
    "knowledge_key": "analysis_result_20251116",
    "knowledge_data": analysis_data,
    "ttl": 86400,
    "tags": ["technical_analysis", "project"]
})

# 检索知识
result = Skill("knowledge-manager", config={
    "operation": "retrieve",
    "search_query": "project technical analysis",
    "tags": ["technical_analysis"],
    "max_results": 5
})

# 缓存管理
result = Skill("knowledge-manager", config={
    "operation": "cache_management",
    "action": "cleanup",
    "strategy": "lru"
})
```

## 支持的操作

1. **store**: 存储知识
2. **retrieve**: 检索知识
3. **update**: 更新知识
4. **delete**: 删除知识
5. **cache_management**: 缓存管理
6. **lifecycle_management**: 生命周期管理

## 输出格式

技能返回标准化的JSON格式输出，包含：
- 操作元数据
- 结果信息
- 知识条目列表
- 性能指标

## 维护

技能由技能维护团队负责维护和更新。