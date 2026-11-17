---
name: quality-gate
description: Verify and control quality standards for code or analysis results. Use when checking code quality, validating compliance, or enforcing quality gates for project deliverables.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Quality Gate

Verify and control quality standards for code or analysis results, providing quality checks and validation to ensure all outputs meet predefined quality requirements.

## When to Use

Use when you need to:
- Check code quality for syntax, standards, complexity, and security issues
- Validate that analysis results meet quality criteria
- Enforce quality gates for project deliverables or code submissions
- Perform compliance checking against coding standards
- Generate quality reports and improvement recommendations

When NOT to use:
- When only basic file operations are needed without quality assessment
- When quality validation is not required for the task
- When simple pass/fail decisions are sufficient without detailed analysis

## Quick Start

```python
Skill("quality-gate", prompt="""
Perform quality check on code:
{
  "check_type": "code_quality",
  "target_path": "/path/to/code",
  "severity_level": "warning"
}
""")
```

## Instructions

1. Determine the quality check type needed:
   - code_quality: For code syntax, standards, and complexity checks
   - standard_compliance: For checking compliance with coding standards
   - quality_gate: For enforcing quality gates with pass/fail decisions
   - documentation_quality: For checking documentation quality

2. Specify the target and parameters:
   - Target path for files/directories to check
   - Quality rules or standards to apply
   - Severity level for issue reporting

3. Execute the quality check using appropriate tools and analysis techniques.

4. Generate quality report showing:
   - Issues found with severity levels
   - Quality score or compliance status
   - Recommendations for improvements

## Examples

Code quality check:
```python
Skill("quality-gate", prompt="""
Check code quality for potential issues:
{
  "check_type": "code_quality",
  "target_path": "/path/to/source/files",
  "quality_rules": {
    "max_line_length": 120,
    "max_function_complexity": 10,
    "require_docstrings": true
  },
  "severity_level": "warning"
}
""")
```

Enforce quality gate:
```python
Skill("quality-gate", prompt="""
Enforce quality gate for code submission:
{
  "check_type": "quality_gate",
  "target_artifacts": ["/path/to/code"],
  "gate_rules": {
    "max_critical_issues": 0,
    "max_error_issues": 5,
    "minimum_quality_score": 80
  },
  "fail_on_violation": true
}
""")
```

## BDD Scenario Checks (`scenario_spec` check_type)

`supported_check_types` now includes a fifth type, `scenario_spec`, implemented in
`main.py::_check_scenario_spec`. It does **not** re-implement Gherkin rules: it loads
`skills/gherkin-bdd/scripts/gherkin_gate.py` and maps its report into this skill's
`issues` / `gate_decision` schema.

```json
{
  "check_type": "scenario_spec",
  "target_path": "skills/gherkin-bdd/features/<module>"
}
```

- `check_result` = `pass` only when `errors == 0`; warnings are reported, never blocking.
- `quality_details.gate_decision.blocking_issues` lists `BDD-xxx file:line message`
  so the caller can block packaging without re-parsing the engine output.
- Mapping: engine `severity=error` → `error`, everything else → `warning`;
  `scenario_metrics` carries `features / scenarios / steps / errors / warnings`.
- Rules and 20 validation codes: `skills/gherkin-bdd/references/authoring-rules.md`.
- Generated artifacts (UAT / step stubs / matrix) are **not** test results; only an
  external runner (pytest-bdd / behave) produces G2 evidence.

CLI:

```bash
python3 skills/quality-gate/main.py '{"check_type":"scenario_spec","target_path":"skills/gherkin-bdd/features"}'
```

## Best Practices

- Define clear quality rules and standards before starting checks
- Use appropriate severity levels to prioritize issues
- Provide actionable recommendations for quality improvements
- Consider both code quality and compliance requirements
- Balance thoroughness with performance for large codebases

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit, Glob, Grep, Bash.

## Common Mistakes

❌ Don't skip quality checks for small changes - all code should meet quality standards
❌ Don't set overly strict rules that block legitimate development progress
❌ Don't ignore quality gates - address issues before proceeding