# Data Exchange Skill

## 概述

Data Exchange Skill 是一个专业的数据交换技能，负责处理各种数据格式的导入导出和转换，支持JSON、XML、CSV、YAML等格式。

## 功能特性

- **数据导入**: 支持多种数据格式的导入和解析
- **数据导出**: 支持多种数据格式的导出和格式化
- **数据转换**: 支持不同数据格式间的转换
- **数据验证**: 提供数据完整性验证和类型检查

## 安装依赖

```bash
pip install pyyaml
```

## 使用方法

### 在代理中调用

```python
# 数据导入
result = Skill("data-exchange", config={
    "operation": "import",
    "source_path": "/path/to/data.json",
    "validation_rules": {
        "required_fields": ["name", "value"],
        "field_types": {
            "value": "integer"
        }
    }
})

# 数据导出
result = Skill("data-exchange", config={
    "operation": "export",
    "data": {"name": "test", "value": 123},
    "target_path": "/path/to/output.csv",
    "export_format": "csv"
})

# 数据转换
result = Skill("data-exchange", config={
    "operation": "convert",
    "source_path": "/path/to/data.json",
    "target_format": "csv",
    "output_path": "/path/to/converted.csv"
})
```

## 支持的操作

1. **import**: 导入数据
2. **export**: 导出数据
3. **convert**: 转换数据
4. **validate**: 验证数据

## 支持的数据格式

- JSON
- XML
- CSV
- YAML

## 输出格式

技能返回标准化的JSON格式输出，包含：
- 操作元数据
- 结果信息
- 数据信息
- 性能指标

## 维护

技能由技能维护团队负责维护和更新。