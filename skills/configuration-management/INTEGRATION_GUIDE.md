# Configuration Management Skill 集成指南

## 概述

本文档提供了将配置管理技能集成到其他Skills中的详细指南。

## 在Skills中使用配置管理器

### 1. 基本集成

```python
from claude_code.skills import Skill

# 在Skill中获取配置
def initialize_skill(self):
    # 获取技能特定配置
    config_result = Skill("configuration-management", config={
        "operation": "get",
        "config_type": "skill",
        "config_id": self.__class__.__name__
    })

    if config_result.get("metadata", {}).get("status") == "success":
        self.config = config_result.get("config_data", {}).get("data", {})
    else:
        # 使用默认配置
        self.config = self._get_default_config()
```

### 2. 配置分层管理

```python
# 实现配置分层：项目配置 > 技能配置 > 系统默认配置
def get_effective_config(self, project_id):
    # 获取系统默认配置
    system_config = self._get_system_config()

    # 获取技能配置
    skill_config_result = Skill("configuration-management", config={
        "operation": "get",
        "config_type": "skill",
        "config_id": self.__class__.__name__
    })

    skill_config = {}
    if skill_config_result.get("metadata", {}).get("status") == "success":
        skill_config = skill_config_result.get("config_data", {}).get("data", {})

    # 获取项目配置
    project_config_result = Skill("configuration-management", config={
        "operation": "get",
        "config_type": "project",
        "config_id": project_id
    })

    project_config = {}
    if project_config_result.get("metadata", {}).get("status") == "success":
        project_config = project_config_result.get("config_data", {}).get("data", {})

    # 合并配置（项目配置优先级最高）
    effective_config = system_config.copy()
    effective_config.update(skill_config)
    effective_config.update(project_config)

    return effective_config
```

### 3. 动态配置更新

```python
# 监听配置变更
def on_config_change(self, config_type, config_id):
    """配置变更回调函数"""
    # 重新加载配置
    self.reload_configuration(config_type, config_id)

def reload_configuration(self, config_type, config_id):
    """重新加载配置"""
    config_result = Skill("configuration-management", config={
        "operation": "get",
        "config_type": config_type,
        "config_id": config_id
    })

    if config_result.get("metadata", {}).get("status") == "success":
        new_config = config_result.get("config_data", {}).get("data", {})
        self.config = new_config
        print(f"Configuration reloaded for {config_type}/{config_id}")
```

## 最佳实践

### 1. 配置组织原则

```python
# 推荐的配置分层结构
configuration_hierarchy = {
    "system_defaults": {
        "cache": {
            "default_ttl": 1800,
            "memory_max_size": 10000
        },
        "performance": {
            "max_concurrent_skills": 5,
            "timeout_threshold": 300
        }
    },
    "skill_defaults": {
        "technical-analyzer": {
            "analysis_depth": "detailed",
            "cache_ttl": 3600
        },
        "ecosystem-discovery": {
            "include_enterprise": True,
            "cache_enabled": True
        }
    },
    "project_overrides": {
        "stock_analysis_20251116": {
            "cache_ttl": 7200,
            "analysis_depth": "comprehensive"
        }
    }
}
```

### 2. 配置验证

```python
# 验证配置合法性
def validate_configuration(self, config_data, config_type):
    """验证配置数据"""
    validation_result = Skill("configuration-management", config={
        "operation": "validate",
        "config_type": config_type,
        "config_data": config_data
    })

    if validation_result.get("metadata", {}).get("status") == "validation_failed":
        errors = validation_result.get("results", {}).get("validation_errors", [])
        raise ValueError(f"Configuration validation failed: {errors}")

    return True
```

### 3. 配置版本管理

```python
# 使用配置版本控制
def get_config_with_version(self, config_type, config_id, version=None):
    """获取指定版本的配置"""
    config = Skill("configuration-management", config={
        "operation": "get",
        "config_type": config_type,
        "config_id": config_id,
        "version": version  # 如果不指定则获取最新版本
    })

    return config
```

## 错误处理

### 1. 配置缺失处理

```python
def get_config_with_fallback(self, config_type, config_id):
    """获取配置，支持降级处理"""
    try:
        result = Skill("configuration-management", config={
            "operation": "get",
            "config_type": config_type,
            "config_id": config_id
        })

        if result.get("metadata", {}).get("status") == "success":
            return result.get("config_data", {}).get("data", {})

    except Exception as e:
        print(f"Failed to get configuration: {e}")

    # 返回默认配置
    return self._get_default_config()
```

### 2. 配置验证失败处理

```python
def safe_config_update(self, config_type, config_id, new_config):
    """安全地更新配置"""
    # 先验证新配置
    try:
        validation_result = Skill("configuration-management", config={
            "operation": "validate",
            "config_type": config_type,
            "config_data": new_config
        })

        if validation_result.get("metadata", {}).get("status") == "validation_failed":
            errors = validation_result.get("results", {}).get("validation_errors", [])
            print(f"Configuration validation failed: {errors}")
            return False

        # 验证通过，执行更新
        update_result = Skill("configuration-management", config={
            "operation": "update",
            "config_type": config_type,
            "config_id": config_id,
            "config_data": new_config
        })

        return update_result.get("metadata", {}).get("status") == "success"

    except Exception as e:
        print(f"Failed to update configuration: {e}")
        return False
```

## 安全考虑

### 1. 敏感配置处理

```python
# 避免在日志中暴露敏感配置
def log_config_safely(self, config_data):
    """安全地记录配置信息"""
    sensitive_keys = ['password', 'api_key', 'secret', 'token']
    safe_config = config_data.copy()

    for key in sensitive_keys:
        if key in safe_config:
            safe_config[key] = "***REDACTED***"

    print(f"Configuration: {safe_config}")
```

### 2. 访问控制

```python
# 验证配置访问权限
def check_config_access(self, config_type, config_id, user_role):
    """检查配置访问权限"""
    # 实现基于角色的访问控制逻辑
    allowed_configs = {
        'admin': ['system', 'skill', 'project'],
        'developer': ['skill', 'project'],
        'analyst': ['project']
    }

    if config_type not in allowed_configs.get(user_role, []):
        raise PermissionError(f"User role {user_role} cannot access {config_type} configuration")
```

## 性能优化

### 1. 配置缓存

```python
# 缓存频繁访问的配置
class ConfigCache:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5分钟

    def get_cached_config(self, config_type, config_id):
        cache_key = f"{config_type}:{config_id}"
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['data']

        # 缓存未命中，从配置管理器获取
        result = Skill("configuration-management", config={
            "operation": "get",
            "config_type": config_type,
            "config_id": config_id
        })

        if result.get("metadata", {}).get("status") == "success":
            config_data = result.get("config_data", {}).get("data", {})
            self.cache[cache_key] = {
                'data': config_data,
                'timestamp': time.time()
            }
            return config_data

        return None
```

### 2. 批量配置操作

```python
# 批量获取多个配置
def get_multiple_configs(self, config_requests):
    """批量获取配置"""
    configs = {}
    for req in config_requests:
        config_type = req['config_type']
        config_id = req['config_id']

        result = Skill("configuration-management", config={
            "operation": "get",
            "config_type": config_type,
            "config_id": config_id
        })

        if result.get("metadata", {}).get("status") == "success":
            configs[f"{config_type}:{config_id}"] = result.get("config_data", {}).get("data", {})

    return configs
```