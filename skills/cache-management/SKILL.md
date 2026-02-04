---
name: cache-management
description: Manage various types of caching in the system including memory, file, and distributed caches. Use when storing, retrieving, or managing cached data, or handling cache strategies and performance optimization.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Cache Management

Manage various types of caching in the system including memory, file, and distributed caches to provide unified cache interfaces ensuring system performance and data consistency.

## When to Use

Use when you need to:
- Store data in cache with specific TTL (time-to-live) values
- Retrieve cached data by key
- Manage cache strategies (LRU, LFU, FIFO, etc.)
- Monitor cache performance metrics (hit rate, usage)
- Handle cache warming, clearing, or batch operations
- Implement cache consistency mechanisms

When NOT to use:
- When only simple file operations are needed without caching
- When temporary data doesn't require persistence
- When caching is not relevant to the current task

## Quick Start

```python
Skill("cache-management", prompt="""
Perform basic cache operation:
{
  "operation": "get",
  "key": "cache_key_name",
  "cache_type": "memory"
}
""")
```

## Instructions

1. Determine the cache operation needed:
   - get: To retrieve cached data by key
   - set: To store data in cache with optional TTL
   - delete: To remove specific cache entries
   - clear: To clear all or pattern-matched cache entries
   - stats: To get cache performance statistics
   - batch: To perform multiple cache operations

2. Specify the cache parameters:
   - Cache key for individual operations
   - Cache type (memory, file, redis, etc.)
   - Value and TTL for set operations
   - Cache strategy if needed

3. Execute the cache operation using appropriate tools and techniques.

4. Handle cache consistency and monitoring:
   - Track cache hit rates and performance
   - Validate cache data integrity
   - Handle cache warming or preloading

## Examples

Store data in cache:
```python
Skill("cache-management", prompt="""
Store analysis result in cache:
{
  "operation": "set",
  "key": "analysis_result_20251116",
  "value": {"data": "analysis_data"},
  "ttl": 3600,
  "cache_type": "memory"
}
""")
```

Get cached data:
```python
Skill("cache-management", prompt="""
Retrieve cached data:
{
  "operation": "get",
  "key": "analysis_result_20251116",
  "cache_type": "memory"
}
""")
```

## Best Practices

- Use appropriate TTL values to balance performance and data freshness
- Monitor cache hit rates to optimize cache efficiency
- Use batch operations for multiple cache entries to improve performance
- Implement cache warming for critical data that should be pre-loaded
- Apply appropriate cache strategies based on access patterns

## Requirements

No special dependencies required. Uses standard Claude tools: Read, Write, Edit, Glob, Grep, Bash.

## Common Mistakes

❌ Don't ignore cache expiration - always set appropriate TTL values
❌ Don't store sensitive data in cache without considering security implications
❌ Don't forget to handle cache miss scenarios gracefully