# Quality Gate Skill

## 概述

Quality Gate Skill 是一个专业的质量门禁技能，负责验证和控制代码或分析结果的质量标准，确保所有输出符合预定义的质量要求。

## 功能特性

- **代码质量检查**: 语法、规范、复杂度和安全性检查
- **标准符合性验证**: 验证是否符合编码标准和最佳实践
- **质量门禁控制**: 执行质量门禁策略，控制制品发布
- **文档质量检查**: 检查文档的质量和完整性

## 使用方法

### 在代理中调用

```python
# 代码质量检查
result = Skill("quality-gate", config={
    "check_type": "code_quality",
    "target_path": "/path/to/source/code",
    "quality_rules": {
        "max_line_length": 120,
        "require_docstrings": true
    }
})

# 标准符合性验证
result = Skill("quality-gate", config={
    "check_type": "standard_compliance",
    "target_components": ["module1", "module2"],
    "standards": ["PEP8", "security_best_practices"]
})

# 质量门禁控制
result = Skill("quality-gate", config={
    "check_type": "quality_gate",
    "target_artifacts": ["/path/to/artifact1"],
    "gate_rules": {
        "max_critical_issues": 0,
        "minimum_quality_score": 80
    }
})
```

## 支持的检查类型

1. **code_quality**: 代码质量检查
2. **standard_compliance**: 标准符合性验证
3. **quality_gate**: 质量门禁控制
4. **documentation_quality**: 文档质量检查

## 输出格式

技能返回标准化的JSON格式输出，包含：
- 操作元数据
- 结果信息
- 质量详情
- 改进建议
- 性能指标

## 维护

技能由技能维护团队负责维护和更新。