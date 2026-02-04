---
name: file-operations
description: Provide unified file operations including read, write, copy, move, and delete. Use when managing files and directories, or performing file system operations that require standardized approaches.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# File Operations

Provide unified file operations including read, write, copy, move, and delete to standardize file system operations across different components and avoid duplicate file handling logic.

## When to Use

Use when you need to:
- Read file contents with specific encoding
- Write data to files with proper encoding handling
- Copy, move, or delete files and directories
- Get file information (size, modification time, etc.)
- List directory contents or search for files by pattern
- Create directories or manage directory structures
- Perform file backup and restore operations
- Handle file operations with consistent error handling

When NOT to use:
- When standard Claude tools (Read, Write, Edit, etc.) are sufficient
- When only simple file operations are required
- When working with virtual files that don't exist on disk

## Quick Start

```python
Skill("file-operations", prompt="""
Perform basic file operation:
{
  "operation": "read",
  "file_path": "/path/to/file.txt",
  "encoding": "utf-8"
}
""")
```

## Instructions

1. Determine the file operation needed:
   - read: To read file contents
   - write: To write content to a file
   - copy: To copy files or directories
   - move: To move/rename files or directories
   - delete: To remove files or directories
   - info: To get file metadata
   - list: To list directory contents
   - mkdir: To create directories
   - search: To find files by pattern

2. Prepare the operation parameters:
   - Source and destination paths as needed
   - File content for write operations
   - Encoding specification if needed
   - Recursive flag for directory operations

3. Execute the file operation using appropriate tools (Read, Write, Edit, Bash).

4. Handle operation results and potential errors:
   - Check operation success/failure status
   - Process file data or metadata as needed
   - Handle access permissions or path errors

## Examples

Read file contents:
```python
Skill("file-operations", prompt="""
Read file with UTF-8 encoding:
{
  "operation": "read",
  "file_path": "/path/to/config.json",
  "encoding": "utf-8"
}
""")
```

Write file:
```python
Skill("file-operations", prompt="""
Write content to file:
{
  "operation": "write",
  "file_path": "/path/to/output.txt",
  "content": "Hello, World!",
  "encoding": "utf-8"
}
""")
```

Copy files:
```python
Skill("file-operations", prompt="""
Copy file from source to destination:
{
  "operation": "copy",
  "source_path": "/path/to/source.txt",
  "destination_path": "/path/to/dest.txt"
}
""")
```

## Best Practices

- Always specify encoding when working with text files
- Use appropriate error handling for file operations
- Check file permissions before attempting operations
- Use recursive flag for directory operations when needed
- Validate file paths to prevent security issues

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit, Glob, Grep, Bash.

## Common Mistakes

❌ Don't ignore file encoding - specify UTF-8 unless other encoding is required
❌ Don't forget to check file permissions before attempting operations
❌ Don't assume file operations always succeed - handle errors appropriately