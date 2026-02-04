# Quality Gate Skill 集成指南

## 概述

本文档提供了将Quality Gate Skill集成到Claude Code代理中的详细指南。

## 在代理中使用

### 1. 基本集成

```python
from claude_code.skills import Skill

# 在代理的执行逻辑中调用代码质量检查
skill_result = Skill("quality-gate", config={
    "check_type": "code_quality",
    "target_path": "/path/to/source/code",
    "quality_rules": {
        "max_line_length": 120,
        "require_docstrings": True,
        "max_function_complexity": 10
    },
    "severity_level": "warning"
})

# 处理技能返回的结果
quality_score = skill_result["results"]["quality_score"]
issues = skill_result["quality_details"]["issues"]
recommendations = skill_result["improvement_recommendations"]
```

### 2. 标准符合性验证集成

```python
# 在代理中验证标准符合性
skill_result = Skill("quality-gate", config={
    "check_type": "standard_compliance",
    "target_components": ["module1", "module2", "module3"],
    "standards": ["PEP8", "security_best_practices", "performance_guidelines"],
    "strict_mode": True
})

# 检查符合性结果
compliance_status = skill_result["quality_details"]["compliance_status"]
if not compliance_status["compliant"]:
    non_compliant_items = compliance_status["non_compliant_items"]
    # 处理不符合项
```

### 3. 质量门禁控制集成

```python
# 在代理中执行质量门禁控制
skill_result = Skill("quality-gate", config={
    "check_type": "quality_gate",
    "target_artifacts": ["/path/to/artifact1", "/path/to/artifact2"],
    "gate_rules": {
        "max_critical_issues": 0,
        "max_error_issues": 5,
        "minimum_quality_score": 80
    },
    "fail_on_violation": True
})

# 检查门禁决策
gate_decision = skill_result["quality_details"]["gate_decision"]
if not gate_decision["passed"]:
    blocking_issues = gate_decision["blocking_issues"]
    # 阻止继续执行
```

## 常见应用场景

### 1. 代码审查

```python
# 在代码审查流程中使用质量门禁
Skill("quality-gate", config={
    "check_type": "code_quality",
    "target_path": "/path/to/pull/request/files",
    "quality_rules": {
        "max_line_length": 100,
        "require_docstrings": True,
        "forbidden_patterns": ["TODO:", "FIXME:"]
    },
    "severity_level": "warning"
})
```

### 2. 持续集成

```python
# 在CI流程中执行质量检查
Skill("quality-gate", config={
    "check_type": "quality_gate",
    "target_artifacts": ["/path/to/build/artifacts"],
    "gate_rules": {
        "max_critical_issues": 0,
        "max_error_issues": 10,
        "minimum_quality_score": 75
    },
    "fail_on_violation": True
})
```

### 3. 发布前检查

```python
# 在发布前执行全面质量检查
Skill("quality-gate", config={
    "check_type": "standard_compliance",
    "target_components": ["all_modules"],
    "standards": ["coding_standards", "security_guidelines", "performance_benchmarks"],
    "strict_mode": True
})
```

## 错误处理

### 1. 处理质量检查失败

```python
try:
    result = Skill("quality-gate", config={
        "check_type": "code_quality",
        "target_path": "/path/to/code"
    })

    if result["metadata"]["status"] == "success":
        quality_score = result["results"]["quality_score"]
        if quality_score < 80:
            print(f"质量评分较低: {quality_score}")
            # 提供改进建议
            recommendations = result["improvement_recommendations"]
            for rec in recommendations:
                print(f"建议: {rec['recommendation']}")
    else:
        print(f"质量检查失败: {result['error_details']}")

except Exception as e:
    print(f"执行技能时发生错误: {str(e)}")
```

### 2. 处理门禁违规

```python
result = Skill("quality-gate", config={
    "check_type": "quality_gate",
    "target_artifacts": ["/path/to/artifacts"],
    "gate_rules": {"max_critical_issues": 0}
})

gate_decision = result["quality_details"]["gate_decision"]
if not gate_decision["passed"]:
    print("质量门禁未通过:")
    for issue in gate_decision["blocking_issues"]:
        print(f"  - {issue}")
    # 阻止继续执行
```

## 性能优化建议

### 1. 增量检查

```python
# 只检查变更的文件
Skill("quality-gate", config={
    "check_type": "code_quality",
    "target_path": "/path/to/changed/files",
    "quality_rules": {
        "incremental_check": True  # 如果支持的话
    }
})
```

### 2. 并行处理

```python
# 并行检查多个组件
components = ["component1", "component2", "component3"]
for component in components:
    Skill("quality-gate", config={
        "check_type": "code_quality",
        "target_path": f"/path/to/{component}",
        "concurrent_processing": True  # 如果支持的话
    })
```

## 最佳实践

### 1. 质量标准定义
- 定义清晰、可衡量的质量标准
- 根据项目需求调整质量规则
- 定期评审和更新质量标准

### 2. 渐进式改进
- 从宽松的质量门禁开始
- 逐步提高质量要求
- 提供具体的改进建议

### 3. 集成策略
- 在开发流程的关键节点集成质量检查
- 提供实时反馈给开发者
- 自动化质量检查流程

## API参考

### 支持的检查类型

| 检查类型 | 描述 | 必需参数 |
|---------|------|---------|
| code_quality | 代码质量检查 | target_path |
| standard_compliance | 标准符合性验证 | target_components |
| quality_gate | 质量门禁控制 | target_artifacts |
| documentation_quality | 文档质量检查 | target_path |

### 配置参数

| 参数 | 类型 | 描述 |
|------|------|------|
| check_type | string | 检查类型 |
| target_path | string | 目标文件或目录路径 |
| target_components | list | 目标组件列表 |
| target_artifacts | list | 目标制品列表 |
| quality_rules | dict | 质量规则定义 |
| standards | list | 标准列表 |
| gate_rules | dict | 门禁规则 |
| severity_level | string | 严重性级别 |
| strict_mode | boolean | 严格模式 |
| fail_on_violation | boolean | 违规时是否失败 |

## 故障排除

### 1. 质量检查无结果
- 检查目标路径是否正确
- 验证文件是否可访问
- 确认质量规则是否合理

### 2. 门禁决策不明确
- 检查门禁规则是否定义清楚
- 验证制品路径是否正确
- 确认违规处理策略是否合适

### 3. 性能问题
- 检查是否在处理大量文件
- 考虑使用增量检查
- 优化质量规则复杂度

## 质量报告

```python
# 生成详细的质量报告
result = Skill("quality-gate", config={
    "check_type": "code_quality",
    "target_path": "/path/to/code",
    "generate_report": True,  # 如果支持的话
    "report_format": "html"   # 如果支持的话
})

# 获取报告信息
if "report_path" in result:
    print(f"质量报告已生成: {result['report_path']}")
```