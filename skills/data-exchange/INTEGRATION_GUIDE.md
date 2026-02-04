# Data Exchange Skill 集成指南

## 概述

本文档提供了将Data Exchange Skill集成到Claude Code代理中的详细指南。

## 在代理中使用

### 1. 基本集成

```python
from claude_code.skills import Skill

# 在代理的执行逻辑中调用数据导入
skill_result = Skill("data-exchange", config={
    "operation": "import",
    "source_path": "/path/to/data.json",
    "validation_rules": {
        "required_fields": ["id", "name"],
        "field_types": {
            "id": "integer",
            "name": "string"
        }
    }
})

# 处理技能返回的结果
parsed_data = skill_result["parsed_data"]
validation_result = skill_result["data_info"]["validation_result"]
```

### 2. 数据导出集成

```python
# 在代理中导出分析结果
analysis_results = [
    {"module": "base", "dependencies": 5, "complexity": "low"},
    {"module": "web", "dependencies": 12, "complexity": "medium"},
    {"module": "account", "dependencies": 8, "complexity": "high"}
]

skill_result = Skill("data-exchange", config={
    "operation": "export",
    "data": analysis_results,
    "target_path": "/path/to/analysis_report.csv",
    "export_format": "csv",
    "include_headers": True
})

# 检查导出结果
if skill_result["metadata"]["status"] == "success":
    print(f"分析报告已导出到: {skill_result['data_info']['target_path']}")
```

### 3. 数据转换集成

```python
# 在代理中转换数据格式
skill_result = Skill("data-exchange", config={
    "operation": "convert",
    "source_path": "/path/to/config.json",
    "target_format": "yaml",
    "output_path": "/path/to/config.yaml"
})

# 获取转换结果
converted_data = skill_result["converted_data"]
```

## 常见应用场景

### 1. 配置文件处理

```python
# 导入配置文件
Skill("data-exchange", config={
    "operation": "import",
    "source_path": "config/app_settings.json",
    "validation_rules": {
        "required_fields": ["database", "redis", "api"],
        "field_types": {
            "database.port": "integer",
            "redis.host": "string",
            "api.timeout": "integer"
        }
    }
})
```

### 2. 分析结果导出

```python
# 导出技术分析结果
Skill("data-exchange", config={
    "operation": "export",
    "data": technical_analysis_results,
    "target_path": "reports/technical_analysis_20251116.csv",
    "export_format": "csv",
    "include_headers": True
})
```

### 3. 数据格式标准化

```python
# 转换不同格式的配置文件到统一格式
Skill("data-exchange", config={
    "operation": "convert",
    "source_path": "configs/legacy_config.xml",
    "target_format": "json",
    "output_path": "configs/modern_config.json"
})
```

## 错误处理

### 1. 处理导入错误

```python
try:
    result = Skill("data-exchange", config={
        "operation": "import",
        "source_path": "/path/to/data.json"
    })

    if result["metadata"]["status"] == "success":
        parsed_data = result["parsed_data"]
        print("数据导入成功")
    else:
        validation_result = result["data_info"]["validation_result"]
        print(f"数据导入失败: {validation_result['errors']}")

except Exception as e:
    print(f"执行技能时发生错误: {str(e)}")
```

### 2. 处理导出错误

```python
result = Skill("data-exchange", config={
    "operation": "export",
    "data": export_data,
    "target_path": "/path/to/output.csv",
    "export_format": "csv"
})

if result["metadata"]["status"] != "success":
    validation_result = result["data_info"]["validation_result"]
    print("导出失败:")
    for error in validation_result["errors"]:
        print(f"  - {error}")
```

## 性能优化建议

### 1. 批量处理

```python
# 批量处理多个数据文件
data_files = [
    {"path": "data1.json", "output": "output1.csv"},
    {"path": "data2.json", "output": "output2.csv"},
    {"path": "data3.json", "output": "output3.csv"}
]

for data_file in data_files:
    Skill("data-exchange", config={
        "operation": "convert",
        "source_path": data_file["path"],
        "target_format": "csv",
        "output_path": data_file["output"]
    })
```

### 2. 流式处理大文件

```python
# 对于大文件，可以分批处理
Skill("data-exchange", config={
    "operation": "import",
    "source_path": "/path/to/large_data.csv",
    "batch_size": 1000  # 如果支持的话
})
```

## 最佳实践

### 1. 数据验证
- 始终验证导入的数据
- 定义清晰的验证规则
- 提供友好的错误信息

### 2. 文件路径安全
- 验证文件路径安全性
- 防止路径遍历攻击
- 限制文件访问权限

### 3. 格式兼容性
- 处理不同格式的特殊要求
- 提供格式转换映射
- 支持自定义格式处理

## API参考

### 支持的操作类型

| 操作 | 描述 | 必需参数 |
|------|------|----------|
| import | 导入数据 | source_path |
| export | 导出数据 | data, target_path |
| convert | 转换数据 | source_path, target_format |
| validate | 验证数据 | data |

### 配置参数

| 参数 | 类型 | 描述 |
|------|------|------|
| operation | string | 操作类型 |
| source_path | string | 源文件路径 |
| target_path | string | 目标文件路径 |
| data | any | 待导出的数据 |
| export_format | string | 导出格式 |
| target_format | string | 目标格式 |
| validation_rules | dict | 验证规则 |
| include_headers | boolean | 是否包含表头 |
| encoding | string | 文件编码 |

## 故障排除

### 1. 数据解析失败
- 检查文件格式是否正确
- 验证文件编码是否匹配
- 确认数据结构是否符合预期

### 2. 文件访问错误
- 检查文件路径是否正确
- 验证文件权限是否足够
- 确认磁盘空间是否充足

### 3. 格式转换问题
- 检查源格式是否支持
- 验证目标格式是否支持
- 确认数据结构是否兼容

## 性能监控

```python
# 监控数据处理性能
result = Skill("data-exchange", config={
    "operation": "import",
    "source_path": "/path/to/large_data.json"
})

performance = result["results"]["performance_metrics"]
print(f"处理时间: {performance['execution_time_ms']}ms")
print(f"内存使用: {performance['memory_usage_mb']}MB")
print(f"处理速率: {performance['processing_rate']} items/s")
```