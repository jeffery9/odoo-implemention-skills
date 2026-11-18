# Source Traceability Skill Usage Guide

This guide provides detailed information on how to use the Source Traceability skill effectively.

## Basic Usage

The Source Traceability skill is designed to verify source code traceability of analysis results, ensuring all technical claims can be traced to specific source code.

### Simple Source Validation

```python
result = Skill("source-traceability", config={
    "verification_type": "reference_validation",
    "target_references": references
})
```

### Advanced Usage

For more complex validation, you can specify additional parameters:

```python
import os

result = Skill("source-traceability", config={
    "verification_type": "consistency_check",
    "target_references": references,
    "source_path": os.environ["ODOO_SOURCE_PATH"],   # 不写死本机路径
    "validation_depth": "comprehensive"
})
```

## Verification Types

### 1. Reference Validation

Validates that references in analysis results can be traced to source code:
- Method call locations
- Data structure definitions
- Configuration references
- External service calls

### 2. Consistency Checking

Ensures consistency between analysis results and source code:
- Code-to-documentation alignment
- Cross-reference validation
- Metadata consistency
- Annotation accuracy

### 3. Traceability Assessment

Evaluates the overall traceability of analysis results:
- Completeness of source references
- Quality of traceability links
- Depth of source code coverage
- Confidence scores for traceability

## Best Practices

1. Always validate your analysis results against source code
2. Maintain clear traceability links between findings and evidence
3. Document any gaps in traceability
4. Use appropriate tools (Grep for code references, Read for source validation)
5. Regularly audit traceability links for accuracy

## Common Use Cases

### Technical Analysis Verification
- Verify that technical claims are supported by evidence
- Validate architectural decisions against source code
- Confirm business logic implementation
- Check compliance with standards

### Quality Control
- Ensure analysis results are accurate
- Verify that all claims have source support
- Document any discrepancies found
- Provide confidence scores for findings

### Audit and Compliance
- Support compliance audits
- Provide evidence for regulatory requirements
- Document technical decisions
- Maintain audit trails

## Error Handling

The skill provides detailed error messages for:
- Invalid verification types
- Missing reference parameters
- Source code accessibility issues
- Validation failures

## Performance Considerations

- For large codebases, consider limiting the scope to specific modules
- Use caching when running similar validations multiple times
- Batch multiple validation requests when possible
- Focus on high-priority areas first