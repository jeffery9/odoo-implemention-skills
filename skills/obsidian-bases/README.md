---
name: obsidian-bases
description: Create and edit Obsidian Bases (.base files) with views, filters, formulas, and summaries. Use when working with .base files, creating database-like views of notes, or when the user mentions Bases, table views, filters, or formulas in Obsidian.
allowed-tools: [Read, Write, Edit]
---
# Obsidian Bases

Create and edit Obsidian Bases (.base files) with views, filters, formulas, and summaries.

## When to Use

Use when you need to:
- Create database-like views of your notes
- Define filters and formulas for note processing
- Build summary views of your knowledge base
- Work with Bases files in Obsidian
- Create structured data views from markdown notes

When NOT to use:
- When working with simple markdown files
- When no data transformation is needed
- When basic note-taking is sufficient

## Quick Start

```python
Skill("obsidian-bases", prompt="""
Create a base with views and formulas:
{
  "views": [
    {"name": "Table View", "type": "table"}
  ],
  "filters": [
    {"field": "status", "operator": "=", "value": "todo"}
  ],
  "formulas": [
    {"name": "total_cost", "expression": "cost * quantity"}
  ]
}
""")
```

## Instructions

1. Define the views you want to include in the base
2. Specify the filters and formulas
3. Set field mappings and data processing rules
4. Execute the skill with appropriate configuration

## Examples

Create a project tracking base:
```python
Skill("obsidian-bases", prompt="""
Create a project tracking base:
{
  "views": [
    {"name": "Table View", "type": "table"},
    {"name": "Gantt View", "type": "gantt"}
  ],
  "filters": [
    {"field": "project", "operator": "=", "value": "Odoo Implementation"},
    {"field": "status", "operator": "!=", "value": "completed"}
  ],
  "formulas": [
    {"name": "progress", "expression": "completed_tasks / total_tasks * 100"}
  ]
}
""")
```

Create a knowledge base summary:
```python
Skill("obsidian-bases", prompt="""
Create a knowledge base summary base:
{
  "views": [
    {"name": "Cards View", "type": "cards"}
  ],
  "filters": [
    {"field": "tags", "operator": "contains", "value": "documentation"}
  ],
  "formulas": [
    {"name": "word_count", "expression": "length(content)"}
  ]
}
""")
```

## Best Practices

- Use consistent naming conventions for fields and formulas
- Keep filters and formulas simple but effective
- Use appropriate view types for different data types
- Test formulas with sample data before production use

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit.

## Common Mistakes

❌ Don't create overly complex formulas - simplify where possible
❌ Don't forget to test filters - verify they return expected results
❌ Don't mix incompatible view types in the same base