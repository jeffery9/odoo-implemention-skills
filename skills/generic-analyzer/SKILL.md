---
name: generic-analyzer
description: Generic analyzer for performing various types of analysis (technical, ecosystem, domain, business process, etc.) using parameterized templates. Use when conducting multi-level analysis of code, systems, or business processes across different domains.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Generic Analyzer

Generic analyzer for performing various types of analysis (technical, ecosystem, domain, business process, etc.) using parameterized templates to provide flexible analysis capabilities across different domains and contexts.

## When to Use

Use when you need to:
- Perform technical analysis of code modules, systems, or components
- Conduct ecosystem discovery to identify module dependencies and extensions
- Analyze domain-specific business processes and workflows
- Execute comprehensive multi-level analysis (function, domain, business process)
- Perform template compliance checks against predefined standards
- Analyze industry requirements and solution architecture
- Generate implementation guides from analysis results
- Apply different analysis templates with parameterized configurations

When NOT to use:
- When simple, direct analysis without templates is sufficient
- When a more specific, dedicated skill is available for the task
- When parameterized analysis is not needed

## Quick Start

```python
Skill("generic-analyzer", prompt="""
Perform technical analysis of a module:
{
  "template": "technical_analysis",
  "scope": "target_module",
  "analysis_depth": "detailed"
}
""")
```

## Instructions

1. Determine the analysis template needed:
   - ecosystem_discovery: For module dependency and extension analysis
   - technical_analysis: For code and system technical analysis
   - function_analysis: For functional capability analysis
   - domain_analysis: For domain-specific business process analysis
   - business_process_analysis: For end-to-end business process analysis
   - comprehensive_analysis: For integrated multi-level analysis
   - template_compliance: For compliance verification
   - industry_requirements: For industry-specific requirements analysis
   - solution_architecture: For solution design analysis
   - implementation_guide: For implementation planning

2. Prepare the analysis configuration:
   - Template name and scope
   - Analysis depth (basic, detailed, comprehensive)
   - Input references for multi-step analysis
   - Template-specific parameters

3. Execute the analysis using the generic analyzer with appropriate configuration.

4. Process and validate the results:
   - Check quality scores and validation results
   - Verify extracted insights and capability units
   - Review recommendations and findings

## Examples

Ecosystem discovery:
```python
Skill("generic-analyzer", prompt="""
Discover module ecosystem:
{
  "template": "ecosystem_discovery",
  "scope": "stock",
  "discovery_type": "module_extensions",
  "bidirectional_analysis": true
}
""")
```

Technical analysis:
```python
Skill("generic-analyzer", prompt="""
Perform detailed technical analysis:
{
  "template": "technical_analysis",
  "scope": "mrp",
  "analysis_depth": "detailed",
  "focus_areas": ["models", "workflows", "reports"]
}
""")
```

## Best Practices

- Use appropriate analysis depth based on requirements (basic, detailed, comprehensive)
- Leverage input chaining for multi-step analysis workflows
- Validate results using quality checks and compliance verification
- Use caching to avoid redundant analysis when possible
- Apply parameterized configurations for consistent execution

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit, Glob, Grep, Bash.

## Common Mistakes

❌ Don't forget to specify analysis scope - all templates require a scope parameter
❌ Don't ignore quality scores - validate results before proceeding with downstream tasks
❌ Don't skip template selection - use the most appropriate template for your analysis type