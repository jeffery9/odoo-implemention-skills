---
name: template-processor
description: Process various template formats, supporting rendering, validation, and conversion. Use when working with template files that need to be processed with context data, validated, or converted between formats.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Template Processor

Process various template formats, supporting rendering, validation, and conversion to handle templates that need to be processed with context data, validated, or converted between different formats.

## When to Use

Use when you need to:
- Render templates with specific context data (variables, configurations)
- Validate template syntax and required variables before use
- Convert templates between different formats (Jinja2, Mustache, etc.)
- Process configuration file templates with dynamic content
- Apply template transformations to generate documents or code
- Verify template integrity and formatting compliance

When NOT to use:
- When simple text replacement is sufficient (use string operations)
- When working with static content that doesn't require templating
- When processing files without variables or dynamic content

## Quick Start

```python
# 渲染标准交付包报告
Skill("template-processor", params={
  "operation": "render_deliverable",
  "template_name": "CAPABILITY_ANALYSIS_REPORT",
  "context_data": {"target_module": "sale", "native_score": 85}
})
```

## Standard Deliverable Templates
The following templates are available via `render_deliverable`:
- **PURPOSE_AND_STRATEGY**: Project mission and strategic goals.
- **STATEMENT_OF_WORK**: Project scope, milestones, and SOW terms.
- **GAP_ANALYSIS_REPORT**: Supply vs. Demand bi-directional alignment.
- **SOLUTION_SPECIFICATION**: High-level technical and functional blueprint.
- **IMPLEMENTATION_METHODOLOGY**: Project lifecycle and quality standards.
- **SCENARIO_SOLUTION**: Modular scenario-based solution积木.
- **CONSULTANT_CONF_GUIDE**: Step-by-step Odoo 19 configuration guide.
- **CONSULTANT_UAT_SCRIPT**: User acceptance test cases and sign-off.
- **CONSULTANT_DISCOVERY_NOTE**: Raw interview and discovery records.
- **CAPABILITY_ANALYSIS_REPORT**: Deep-dive Odoo 19 source pattern report.
- **CAPABILITY_UNIT_SPEC**: Atomic capability unit definition for KB.

## Instructions

1. Determine the template operation needed:
   - render: To render template with specific path
   - render_deliverable: To render a standard Capability Twin deliverable (from `templates/deliverables/` inside this skill)
   - validate: To validate template syntax and required variables
   - convert: To convert between template formats
   - manage: To manage template lifecycle operations

2. Prepare the template parameters:
   - Template file path
   - Context data for rendering (as dictionary)
   - Target format for conversion
   - Template engine type if specified

3. Execute the template operation using appropriate tools and techniques.

4. Handle validation and error checking:
   - Verify template syntax before rendering
   - Check for missing required variables
   - Validate rendered output format

## Examples

Render template with context:
```python
Skill("template-processor", prompt="""
Render configuration template:
{
  "operation": "render",
  "template_path": "/path/to/config.template",
  "context_data": {
    "database_host": "localhost",
    "database_port": 5432,
    "app_name": "myapp"
  },
  "output_path": "/path/to/config.ini",
  "template_engine": "jinja2"
}
""")
```

Validate template:
```python
Skill("template-processor", prompt="""
Validate template syntax and variables:
{
  "operation": "validate",
  "template_path": "/path/to/template.html",
  "required_variables": ["title", "content", "author"],
  "template_engine": "jinja2"
}
""")
```

## Best Practices

- Always validate templates before rendering to avoid runtime errors
- Use appropriate template engines for specific use cases
- Verify that required variables are provided in context data
- Sanitize input data to prevent template injection attacks
- Consider performance implications for large template sets

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit, Glob, Grep, Bash.

## Common Mistakes

❌ Don't render templates without validating syntax first
❌ Don't ignore missing required variables - always check context data
❌ Don't use templates with untrusted input without proper sanitization