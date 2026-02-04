---
name: relationship-analysis
description: Analyze relationships and dependencies between components, modules, or system elements. Use when mapping dependencies, identifying integration points, or understanding system architecture.
allowed-tools: [Read, Grep, Glob, Bash]
---

# Relationship Analysis

Analyze relationships and dependencies between components, modules, or system elements to understand system architecture and integration points.

## When to Use

Use when you need to:
- Analyze module dependencies in a codebase
- Map relationships between system components
- Identify integration points and data flows
- Understand system architecture and connections
- Find potential bottlenecks or critical nodes in a system

When NOT to use:
- When only simple file reading is required (use Read tool directly)
- When you need to analyze only a single component in isolation
- When performing basic debugging without relationship mapping

## Quick Start

```python
Skill("relationship-analysis", prompt="""
Analyze relationships between components:
{
  "analysis_type": "dependency_analysis",
  "scope": "target_module",
  "direction": "bidirectional"
}
""")
```

## Instructions

1. Determine the analysis type needed:
   - dependency_analysis: For module/dependency relationships
   - relationship_mapping: For business entity connections
   - network_analysis: For network metrics and key nodes
   - hierarchy_mapping: For hierarchical structure analysis

2. Identify the scope of analysis:
   - Single component or module
   - Group of related components
   - Full system or subsystem

3. Execute the relationship analysis using appropriate tools (Read, Grep, Glob) to discover connections, dependencies, and relationships.

4. Generate structured output showing:
   - Relationships identified
   - Direction of dependencies
   - Criticality assessment
   - Visual representation if needed

## Examples

Analyze module dependencies:
```python
Skill("relationship-analysis", prompt="""
Analyze dependencies for the 'accounting' module in Odoo:
{
  "analysis_type": "dependency_analysis",
  "scope": "accounting",
  "direction": "bidirectional",
  "include_enterprise": false
}
""")
```

Map integration points:
```python
Skill("relationship-analysis", prompt="""
Map integration points between modules A, B, and C:
{
  "analysis_type": "relationship_mapping",
  "scope": ["module_a", "module_b", "module_c"]
}
""")
```

## Best Practices

- Start with a narrow scope and expand as needed
- Document both direct and reverse dependencies
- Note the criticality and impact of each relationship
- Use appropriate tools (Grep for code relationships, Read for configuration files)
- Create visual representations for complex relationship networks

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Grep, Glob, Bash.

## Common Mistakes

❌ Don't analyze the entire codebase at once - start with a specific scope
❌ Don't ignore reverse dependencies - consider bidirectional relationships
❌ Don't forget to document the criticality and impact of relationships