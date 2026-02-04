---
name: configuration-management
description: Manage system configuration information at multiple levels (system, skill, project). Use when retrieving, updating, or validating configuration settings, or managing configuration versions and compliance.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Configuration Management

Manage system configuration information at multiple levels (system, skill, project) to provide unified configuration management interface ensuring system consistency and maintainability.

## When to Use

Use when you need to:
- Retrieve configuration settings for a specific skill, project, or system component
- Update configuration parameters and settings
- Validate configuration compliance and correctness
- Manage configuration versions and history
- Handle configuration merging and conflict resolution

When NOT to use:
- When only simple file read/write operations are needed
- When configuration management is not required for the task
- When working with temporary or one-time settings

## Quick Start

```python
Skill("configuration-management", prompt="""
Get configuration settings:
{
  "operation": "get",
  "config_type": "skill",
  "config_id": "my-skill-name"
}
""")
```

## Instructions

1. Determine the configuration operation needed:
   - get: To retrieve configuration settings
   - update: To update configuration parameters
   - validate: To check configuration validity
   - history: To get configuration version history
   - delete: To remove configuration settings

2. Specify the configuration parameters:
   - Configuration type (system, skill, project, workflow)
   - Configuration ID or identifier
   - Configuration data (for updates)

3. Execute the configuration operation using appropriate tools (Read, Write, Edit) to manage configuration files.

4. Handle validation and version control as needed:
   - Verify configuration schema compliance
   - Track configuration changes
   - Merge configurations properly

## Examples

Retrieve configuration:
```python
Skill("configuration-management", prompt="""
Get skill configuration:
{
  "operation": "get",
  "config_type": "skill",
  "config_id": "technical-analyzer",
  "output_format": "json"
}
""")
```

Update configuration:
```python
Skill("configuration-management", prompt="""
Update project configuration:
{
  "operation": "update",
  "config_type": "project",
  "config_id": "analysis-project-2025",
  "config_data": {
    "analysis_depth": "comprehensive",
    "cache_strategy": "aggressive"
  },
  "validate": true
}
""")
```

## Best Practices

- Separate configuration types by level (system, skill, project)
- Use clear naming conventions for configuration identifiers
- Validate configuration data before applying changes
- Track configuration versions and maintain history
- Document configuration parameters for clarity

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit, Glob, Grep, Bash.

## Common Mistakes

❌ Don't ignore configuration validation - always check schema compliance
❌ Don't update configurations without proper backup/rollback strategy
❌ Don't mix configuration types - keep system, skill, and project configs separate