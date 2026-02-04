---
name: autonomous-evolution
description: Enables self-learning and knowledge accumulation for the Capability Twin framework. Use to optimize capability models based on new Odoo 19 discoveries or user feedback.
---

# Autonomous Evolution

Drives the continuous improvement of the research platform by learning from executed workflows and mined code patterns.

## Core Capabilities
- **Learn**: Update models based on new analysis results.
- **Extract Knowledge**: Identify patterns from mined Odoo source code.
- **Optimize**: Suggest improvements for existing "Capability Units".
- **Relational Analysis**: Map how capabilities evolve and depend on each other.

## Usage Guide
This skill is often called by the `capability-extractor-agent` to refine results.

```python
Skill("autonomous-evolution", params={
    "operation": "extract_knowledge",
    "data": mined_source_patterns,
    "knowledge_type": "implementation_patterns"
})
```

## Detailed Models
- **Capability Dimensions**: Structural, Behavioral, Rules, and Constraints. See [dimensions.md](references/dimensions.md).
- **Evolution Strategies**: Fast, Balanced, Conservative.

## Resources
- **Scripts**: Implementation of learning algorithms.
