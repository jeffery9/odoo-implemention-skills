# Source Traceability Skill

## 概述

Source Traceability Skill 是一个通用的源码追溯技能，用于验证分析结论的源码可追溯性和一致性。

## 功能特性

- 源码引用验证
- 一致性检查
- 可追溯性评估
- 可信度评分

## 使用方法

### 在代理中调用

```python
# 基础源码验证
result = Skill("source-traceability", config={
    "verification_type": "reference_validation",
    "target_references": ["reference_list"],
    "source_root": "/path/to/source"
})

# 可信度评估
result = Skill("source-traceability", config={
    "verification_type": "trustworthiness_assessment",
    "target_components": ["component_list"],
    "assessment_criteria": ["completeness", "accuracy", "consistency"]
})
```

## 输出格式

技能返回标准化的JSON格式输出，包含：
- 验证结果列表
- 追溯性指标
- 可信度评估
- 改进建议

## 集成说明

该技能可被以下代理使用：
- technical-analysis-agent
- trustworthiness-auditor-agent
- capability-extractor-agent
- comprehensive-analysis-agent

## 维护

技能由技能维护团队负责维护和更新。