# JSON Canvas Integration Guide

This guide explains how to integrate the JSON Canvas skill into your Claude Code workflow.

## Prerequisites

- Claude Code framework
- Basic understanding of Canvas file structure
- Access to the `json-canvas` skill

## Integration Options

### 1. Direct Skill Usage

The JSON Canvas skill can be invoked directly:

```python
result = Skill("json-canvas", config={
    "nodes": [
        {"id": "1", "label": "Start", "x": 100, "y": 100},
        {"id": "2", "label": "Process", "x": 250, "y": 100}
    ],
    "edges": [
        {"from": "1", "to": "2"}
    ]
})
```

### 2. Through Workflow Agents

The skill can be used by workflow agents that need to create or modify visual representations of systems.

### 3. As Part of Multi-Skill Workflows

The skill can be chained with other skills for complex operations:

1. First use the `relationship-analysis` to identify components
2. Then use `json-canvas` to create visual representations of the relationships

## Configuration Options

### Canvas Structure

- `nodes`: Array of node objects with id, label, and position
- `edges`: Array of edge objects with from and to connections
- `groups`: Optional grouping information for organizing related elements

### Styling Options

- `node_style`: Default styling for nodes
- `edge_style`: Default styling for edges
- `layout`: Layout algorithm to use (auto, manual)

## Error Handling

The skill provides error handling for:
- Invalid node or edge definitions
- Missing required parameters
- Malformed JSON structure

## Performance Considerations

- For large diagrams, consider chunking the data
- Use caching for frequently accessed diagrams
- Batch operations when possible

## Testing Integration

To test this integration:

1. Run the skill with sample parameters
2. Verify the output format meets requirements
3. Check that all connections are properly defined
4. Validate JSON structure correctness

## Troubleshooting

Common issues and solutions:
- Structure errors: Check the JSON format for valid syntax
- Connection issues: Verify all from/to references are valid node IDs
- Integration problems: Verify skill availability in the framework