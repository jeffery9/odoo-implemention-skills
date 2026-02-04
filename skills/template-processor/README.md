# Template Processor Skill

## 概述

Template Processor Skill 是一个专业的模板处理技能，负责处理各种模板格式，支持渲染、验证、转换和管理功能。

## 功能特性

- **模板渲染**: 支持多种模板引擎的渲染功能
- **模板验证**: 提供语法和变量完整性验证
- **模板转换**: 支持不同模板格式间的转换
- **模板管理**: 提供缓存和版本管理功能

## 安装依赖

```bash
pip install jinja2 pystache pybars3
```

## 使用方法

### 在代理中调用

```python
# 模板渲染
result = Skill("template-processor", config={
    "operation": "render",
    "template_path": "/path/to/template.jinja2",
    "context_data": {"name": "World", "title": "Hello"},
    "output_path": "/path/to/output.html",
    "template_engine": "jinja2"
})

# 模板验证
result = Skill("template-processor", config={
    "operation": "validate",
    "template_path": "/path/to/template.jinja2",
    "required_variables": ["name", "title"],
    "template_engine": "jinja2"
})

# 模板转换
result = Skill("template-processor", config={
    "operation": "convert",
    "source_template_path": "/path/to/template.jinja2",
    "target_format": "mustache",
    "output_path": "/path/to/template.mustache"
})
```

## 支持的操作

1. **render**: 渲染模板
2. **validate**: 验证模板
3. **convert**: 转换模板
4. **manage**: 管理模板

## 支持的模板引擎

- Jinja2
- Mustache
- Handlebars

## 输出格式

技能返回标准化的JSON格式输出，包含：
- 操作元数据
- 结果信息
- 模板数据
- 性能指标

## 维护

技能由技能维护团队负责维护和更新。