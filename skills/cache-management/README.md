# Cache Management Skill

## 概述

缓存管理技能是专门用于管理系统内各种类型缓存的通用技能，支持内存级缓存、持久化缓存和分布式缓存。该技能提供统一的缓存接口，确保系统性能和数据一致性。

## 核心功能

1. **多级缓存管理** - 支持内存、文件系统等多种缓存类型
2. **缓存策略控制** - 实现LRU、LFU等缓存淘汰策略
3. **缓存监控与统计** - 实时监控缓存性能指标
4. **缓存一致性保证** - 处理缓存穿透、雪崩等问题

## 使用方法

### 基本调用
```python
result = Skill("cache-management", config={
    "operation": "get",
    "key": "my_cache_key",
    "cache_type": "memory"
})
```

### 设置缓存
```python
result = Skill("cache-management", config={
    "operation": "set",
    "key": "my_cache_key",
    "value": {"data": "my_data"},
    "ttl": 3600,
    "cache_type": "memory"
})
```

### 批量操作
```python
result = Skill("cache-management", config={
    "operation": "batch",
    "actions": [
        {"operation": "set", "key": "key1", "value": "value1"},
        {"operation": "get", "key": "key2"}
    ]
})
```

## 支持的操作类型

- `get` - 获取缓存值
- `set` - 设置缓存值
- `delete` - 删除缓存项
- `clear` - 清空缓存
- `stats` - 获取缓存统计信息
- `batch` - 批量操作

## 支持的缓存类型

- `memory` - 内存缓存（LRU策略）
- `file` - 文件系统缓存

## 配置参数

### 必需参数
- `operation` - 操作类型

### 可选参数
- `key` - 缓存键
- `value` - 缓存值
- `cache_type` - 缓存类型（默认：memory）
- `ttl` - 过期时间（秒，默认：3600）
- `actions` - 批量操作列表

## 输出格式

```json
{
  "metadata": {
    "skill_name": "cache-management",
    "operation": "get",
    "execution_time": 0.001,
    "status": "success"
  },
  "cache_data": {
    "key": "my_cache_key",
    "value": "cached_value"
  }
}
```