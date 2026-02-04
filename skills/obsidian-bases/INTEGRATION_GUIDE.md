# Obsidian Bases Integration Guide

This guide explains how to integrate the Obsidian Bases skill into your Claude Code workflow.

## Prerequisites

- Claude Code framework
- Basic understanding of Obsidian Bases structure
- Access to the `obsidian-bases` skill

## Integration Options

### 1. Direct Skill Usage

The Obsidian Bases skill can be invoked directly:

```python
result = Skill("obsidian-bases", config={
    "views": [
        {"name": "Table View", "type": "table"}
    ],
    "filters": [
        {"field": "status", "operator": "=", "value": "todo"}
    ],
    "formulas": [
        {"name": "total_cost", "expression": "cost * quantity"}
    ]
})
```

### 2. Through Workflow Agents

The skill can be used by workflow agents that need to create or modify database-like views of notes.

### 3. As Part of Multi-Skill Workflows

The skill can be chained with other skills for complex operations:

1. First use the `knowledge-manager` to retrieve existing knowledge
2. Then use `obsidian-bases` to create structured views of the data

## Configuration Options

### Views

- `views`: Array of view definitions with name and type
- Supported types: table, card, calendar, gantt, kanban

### Filters

- `filters`: Array of filter conditions
- Each filter has field, operator, and value properties

### Formulas

- `formulas`: Array of formula definitions
- Each formula has name and expression properties

## Error Handling

The skill provides error handling for:
- Invalid view definitions
- Malformed filter expressions
- Syntax errors in formulas
- Missing required parameters

## Performance Considerations

- For large datasets, consider filtering early in the process
- Use caching for frequently accessed bases
- Batch operations when possible

## Testing Integration

To test this integration:

1. Run the skill with sample parameters
2. Verify the output format meets requirements
3. Check that all views are properly defined
4. Validate formula syntax correctness

## Troubleshooting

Common issues and solutions:
- Syntax errors: Check the formula expressions for valid syntax
- View issues: Verify all view types are supported
- Integration problems: Verify skill availability in the framework