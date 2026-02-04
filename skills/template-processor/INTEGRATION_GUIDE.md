# Template Processor Skill 集成指南

## 概述

本文档提供了将Template Processor Skill集成到Claude Code代理中的详细指南。

## 在代理中使用

### 1. 基本集成

```python
from claude_code.skills import Skill

# 在代理的执行逻辑中调用
skill_result = Skill("template-processor", config={
    "operation": "render",
    "template_path": "/path/to/template.jinja2",
    "context_data": {
        "project_name": "MyProject",
        "version": "1.0.0",
        "author": "Developer"
    },
    "output_path": "/path/to/output.md",
    "template_engine": "jinja2"
})

# 处理技能返回的结果
rendered_content = skill_result["template_data"]["rendered_content"]
validation_result = skill_result["template_data"]["validation_result"]
```

### 2. 模板验证集成

```python
# 在代理中验证模板
skill_result = Skill("template-processor", config={
    "operation": "validate",
    "template_path": "/path/to/template.jinja2",
    "required_variables": ["project_name", "version", "author"],
    "template_engine": "jinja2"
})

# 检查验证结果
validation_result = skill_result["results"]["validation_result"]
if not validation_result["is_valid"]:
    # 处理验证错误
    syntax_errors = validation_result["syntax_errors"]
    missing_variables = validation_result["missing_variables"]
```

### 3. 模板转换集成

```python
# 在代理中转换模板格式
skill_result = Skill("template-processor", config={
    "operation": "convert",
    "source_template_path": "/path/to/template.jinja2",
    "target_format": "mustache",
    "output_path": "/path/to/converted_template.mustache"
})

# 获取转换结果
converted_content = skill_result["template_data"]["converted_content"]
```

## 常见应用场景

### 1. 生成配置文件

```python
# 生成应用配置文件
Skill("template-processor", config={
    "operation": "render",
    "template_path": "templates/app_config.yaml.j2",
    "context_data": {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "myapp"
        },
        "redis": {
            "host": "localhost",
            "port": 6379
        }
    },
    "output_path": "config/app_config.yaml",
    "template_engine": "jinja2"
})
```

### 2. 生成文档

```python
# 生成项目文档
Skill("template-processor", config={
    "operation": "render",
    "template_path": "templates/README.md.j2",
    "context_data": {
        "project_name": "My Awesome Project",
        "description": "A project that does amazing things",
        "version": "1.0.0",
        "dependencies": ["python>=3.8", "flask>=2.0.0"]
    },
    "output_path": "README.md",
    "template_engine": "jinja2"
})
```

### 3. 验证模板完整性

```python
# 在部署前验证配置模板
Skill("template-processor", config={
    "operation": "validate",
    "template_path": "templates/deployment.yaml.j2",
    "required_variables": [
        "app_name",
        "image_tag",
        "replicas",
        "ports"
    ],
    "template_engine": "jinja2"
})
```

## 错误处理

### 1. 处理模板渲染错误

```python
try:
    result = Skill("template-processor", config={
        "operation": "render",
        "template_path": "/path/to/template.jinja2",
        "context_data": {"name": "World"}
    })

    if result["metadata"]["status"] == "success":
        print("模板渲染成功")
        rendered_content = result["template_data"]["rendered_content"]
    else:
        print(f"模板渲染失败: {result['error_details']}")

except Exception as e:
    print(f"执行技能时发生错误: {str(e)}")
```

### 2. 处理验证错误

```python
result = Skill("template-processor", config={
    "operation": "validate",
    "template_path": "/path/to/template.jinja2"
})

validation_result = result["results"]["validation_result"]
if not validation_result["is_valid"]:
    if validation_result["syntax_errors"]:
        print("语法错误:")
        for error in validation_result["syntax_errors"]:
            print(f"  - {error}")

    if validation_result["missing_variables"]:
        print("缺少必需变量:")
        for var in validation_result["missing_variables"]:
            print(f"  - {var}")
```

## 性能优化建议

### 1. 使用缓存

```python
# 对于频繁渲染的模板启用缓存
Skill("template-processor", config={
    "operation": "render",
    "template_path": "/path/to/frequently_used_template.jinja2",
    "context_data": template_variables,
    "cache_enabled": True
})
```

### 2. 批量处理

```python
# 批量处理多个模板
templates = [
    {"path": "template1.jinja2", "output": "output1.txt"},
    {"path": "template2.jinja2", "output": "output2.txt"},
    {"path": "template3.jinja2", "output": "output3.txt"}
]

for template_info in templates:
    Skill("template-processor", config={
        "operation": "render",
        "template_path": template_info["path"],
        "context_data": template_variables,
        "output_path": template_info["output"]
    })
```

## 最佳实践

### 1. 模板设计
- 使用明确的变量命名
- 提供默认值处理
- 避免复杂的逻辑嵌套

### 2. 错误处理
- 始终验证模板渲染结果
- 提供清晰的错误信息
- 实现优雅的降级机制

### 3. 安全性
- 验证模板内容安全性
- 限制文件系统访问权限
- 避免执行用户输入的模板

## API参考

### 支持的操作类型

| 操作 | 描述 | 必需参数 |
|------|------|----------|
| render | 渲染模板 | template_path |
| validate | 验证模板 | template_path |
| convert | 转换模板 | source_template_path, target_format |
| manage | 管理模板 | action |

### 配置参数

| 参数 | 类型 | 描述 |
|------|------|------|
| operation | string | 操作类型 |
| template_path | string | 模板文件路径 |
| context_data | dict | 渲染上下文数据 |
| output_path | string | 输出文件路径 |
| template_engine | string | 模板引擎类型 |
| required_variables | list | 必需的变量列表 |
| target_format | string | 目标模板格式 |
| cache_enabled | boolean | 是否启用缓存 |

## 故障排除

### 1. 模板渲染失败
- 检查模板文件路径是否正确
- 验证模板语法是否正确
- 确认上下文数据格式是否正确

### 2. 模板引擎不可用
- 确保已安装相应的模板引擎包
- 检查Python环境是否正确配置
- 验证包版本是否兼容

### 3. 缓存问题
- 检查缓存目录权限
- 清理过期的缓存文件
- 重启服务以清除内存缓存