---
name: json-canvas
description: Create and edit JSON Canvas files (.canvas) with nodes, edges, groups, and connections. Use when working with .canvas files, creating visual canvases, mind maps, flowcharts, or when the user mentions Canvas files in Obsidian.
allowed-tools: [Read, Write, Edit]
---
# JSON Canvas

Create and edit JSON Canvas files (.canvas) with nodes, edges, groups, and connections.

## When to Use

Use when you need to:
- Create visual representations of complex systems
- Map relationships between components
- Design architecture diagrams
- Create mind maps and flowcharts
- Work with Canvas files in Obsidian

When NOT to use:
- When only text-based documentation is needed
- When visual representation is not helpful
- When simple lists or tables are more appropriate

## Quick Start

```python
Skill("json-canvas", prompt="""
Create a canvas with nodes and edges:
{
  "nodes": [
    {"id": "1", "label": "Start", "x": 100, "y": 100},
    {"id": "2", "label": "Process", "x": 250, "y": 100}
  ],
  "edges": [
    {"from": "1", "to": "2"}
  ]
}
""")
```

## Instructions

1. Define the nodes you want to include in the canvas
2. Specify the connections between nodes
3. Set positioning and styling options
4. Execute the skill with appropriate configuration

## Examples

Create a simple flowchart:
```python
Skill("json-canvas", prompt="""
Create a flowchart for data processing:
{
  "nodes": [
    {"id": "input", "label": "Data Input", "x": 50, "y": 100},
    {"id": "process", "label": "Data Processing", "x": 200, "y": 100},
    {"id": "output", "label": "Data Output", "x": 350, "y": 100}
  ],
  "edges": [
    {"from": "input", "to": "process"},
    {"from": "process", "to": "output"}
  ]
}
""")
```

Create a network diagram:
```python
Skill("json-canvas", prompt="""
Create a network architecture diagram:
{
  "nodes": [
    {"id": "client", "label": "Client", "x": 50, "y": 50},
    {"id": "server", "label": "Web Server", "x": 200, "y": 50},
    {"id": "db", "label": "Database", "x": 350, "y": 50}
  ],
  "edges": [
    {"from": "client", "to": "server"},
    {"from": "server", "to": "db"}
  ]
}
""")
```

## Best Practices

- Use consistent node styling for related components
- Position nodes logically to show relationships
- Use appropriate colors to differentiate between types
- Keep diagrams simple and focused

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit.

## Common Mistakes

❌ Don't create overly complex diagrams - simplify where possible
❌ Don't ignore connections - every edge should represent a meaningful relationship
❌ Don't mix different diagram types in the same canvas