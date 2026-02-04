---
name: data-exchange
description: Handle import, export, and conversion of various data formats (JSON, XML, CSV, YAML, etc.). Use when processing data files, converting formats, or managing data exchange between systems.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Data Exchange

Handle import, export, and conversion of various data formats (JSON, XML, CSV, YAML, etc.) to facilitate data exchange between different systems and formats.

## When to Use

Use when you need to:
- Import data from files in various formats (JSON, XML, CSV, YAML)
- Export data to specific file formats
- Convert data from one format to another
- Validate data integrity and format compliance
- Process configuration files or data exports

When NOT to use:
- When working with in-memory data structures only
- When simple file read/write operations are sufficient
- When data processing doesn't require format conversion

## Quick Start

```python
Skill("data-exchange", prompt="""
Convert data from one format to another:
{
  "operation": "convert",
  "source_path": "/path/to/input.json",
  "target_format": "csv",
  "output_path": "/path/to/output.csv"
}
""")
```

## Instructions

1. Determine the operation type needed:
   - import: To read and parse data from a file
   - export: To write data to a file in a specific format
   - convert: To transform data from one format to another
   - validate: To check data integrity and format compliance

2. Prepare the operation parameters:
   - Source and target file paths
   - Source and target data formats
   - Any validation rules or formatting options

3. Execute the data operation using appropriate tools (Read for import, Write for export).

4. Handle validation and error reporting:
   - Check for parsing errors
   - Validate data structure if needed
   - Report any issues found

## Examples

Import data from a file:
```python
Skill("data-exchange", prompt="""
Import data from JSON file:
{
  "operation": "import",
  "source_path": "/path/to/data.json",
  "validation_rules": {
    "required_fields": ["id", "name"]
  }
}
""")
```

Export data to CSV:
```python
Skill("data-exchange", prompt="""
Export data to CSV format:
{
  "operation": "export",
  "data": [{"id": 1, "name": "example"}],
  "target_path": "/path/to/output.csv",
  "export_format": "csv",
  "include_headers": true
}
""")
```

Convert between formats:
```python
Skill("data-exchange", prompt="""
Convert from JSON to YAML:
{
  "operation": "convert",
  "source_path": "/path/to/input.json",
  "source_format": "json",
  "target_format": "yaml",
  "output_path": "/path/to/output.yaml"
}
""")
```

## Best Practices

- Use appropriate validation rules to ensure data integrity
- Check file existence and permissions before operations
- Handle large files with streaming when possible
- Include headers in CSV exports for better readability
- Verify successful file operations after completion

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit, Glob, Grep, Bash.

## Common Mistakes

❌ Don't forget to validate file paths - always check they're safe and accessible
❌ Don't ignore encoding issues - specify UTF-8 when needed
❌ Don't skip data validation - verify data structure when processing