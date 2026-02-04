# Cache Management Skill 集成指南

## 概述

本文档提供了将缓存管理技能集成到其他Skills中的详细指南。

## 在Skills中使用缓存管理器

### 1. 基本集成

```python
from claude_code.skills import Skill

# 在Skill中缓存分析结果
def perform_analysis(self, module_name):
    # 构造缓存键
    cache_key = f"analysis_{module_name}_{self.detail_level}"

    # 尝试从缓存获取结果
    cache_result = Skill("cache-management", config={
        "operation": "get",
        "key": cache_key,
        "cache_type": "memory"
    })

    if cache_result.get("metadata", {}).get("status") == "success" and "cache_data" in cache_result:
        return cache_result["cache_data"]["value"]

    # 执行实际分析
    result = self._execute_analysis(module_name)

    # 将结果存入缓存
    Skill("cache-management", config={
        "operation": "set",
        "key": cache_key,
        "value": result,
        "ttl": 3600,  # 1小时过期
        "cache_type": "memory"
    })

    return result
```

### 2. 批量缓存操作

```python
# 批量缓存多个分析结果
def cache_multiple_results(self, results_dict):
    actions = []
    for key, value in results_dict.items():
        actions.append({
            "operation": "set",
            "key": f"analysis_{key}",
            "value": value,
            "ttl": 3600,
            "cache_type": "memory"
        })

    Skill("cache-management", config={
        "operation": "batch",
        "actions": actions
    })
```

### 3. 缓存监控

```python
# 监控缓存性能
def monitor_cache_performance(self):
    stats_result = Skill("cache-management", config={
        "operation": "stats",
        "cache_type": "memory"
    })

    if stats_result.get("metadata", {}).get("status") == "success":
        stats = stats_result.get("results", {}).get("cache_stats", {})
        hit_rate = stats.get("hit_rate", 0)

        if hit_rate < 0.8:  # 缓存命中率低于80%
            print("Warning: Cache hit rate is low")
```

## 最佳实践

### 1. 缓存键命名规范

```python
# 推荐的缓存键格式
cache_keys = {
    'analysis_result': f"analysis:{module}:{timestamp}",
    'ecosystem_data': f"ecosystem:{module}:{scope}",
    'template_output': f"template:{template_id}:{parameters_hash}"
}
```

### 2. 缓存策略选择

- **内存缓存**: 适用于小数据、高频访问
- **文件缓存**: 适用于大数据、中频访问

### 3. TTL设置策略

```python
# 根据数据类型设置不同的TTL
ttl_config = {
    'analysis_results': 3600,      # 1小时
    'ecosystem_data': 7200,        # 2小时
    'configuration': 86400,        # 24小时
    'real_time_data': 300          # 5分钟
}
```

## 错误处理

### 1. 缓存失效降级

```python
def get_with_fallback(self, key):
    try:
        # 尝试从缓存获取
        result = Skill("cache-management", config={
            "operation": "get",
            "key": key
        })

        if result.get("metadata", {}).get("status") == "success":
            return result.get("cache_data", {}).get("value")
    except Exception as e:
        # 缓存访问失败，记录日志但不中断流程
        print(f"Cache access failed: {e}")

    # 直接执行操作
    return self.perform_direct_operation()
```

### 2. 性能监控

```python
import time

def perform_cached_operation(self, key, operation):
    start_time = time.time()

    result = Skill("cache-management", config={
        "operation": "get",
        "key": key
    })

    execution_time = time.time() - start_time

    # 记录性能指标
    if execution_time > 1.0:  # 超过1秒
        print(f"Warning: Cache operation took {execution_time} seconds")
```

## 安全考虑

### 1. 敏感数据处理

```python
# 避免缓存敏感数据
sensitive_keys = ['password', 'api_key', 'secret']

def is_safe_to_cache(self, data):
    """检查数据是否安全可缓存"""
    if isinstance(data, dict):
        for key in data.keys():
            if key in sensitive_keys:
                return False
    return True
```

### 2. 访问控制

```python
# 在缓存操作前验证权限
def validate_cache_access(self, operation, key):
    """验证缓存访问权限"""
    # 实现访问控制逻辑
    pass
```

## 性能优化

### 1. 缓存预热

```python
# 在应用启动时预热常用缓存
def warmup_cache(self):
    Skill("cache-management", config={
        "operation": "warmup",
        "pattern": "frequently_used_*"
    })
```

### 2. 缓存清理

```python
# 定期清理过期缓存
def cleanup_cache(self):
    Skill("cache-management", config={
        "operation": "clear",
        "pattern": "expired_*"
    })
```