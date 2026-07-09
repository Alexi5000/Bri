# BRI Logging and Monitoring Guide

## Overview

BRI includes a comprehensive logging and monitoring system that tracks application behavior, performance metrics, API calls, and errors. The system provides structured logging with multiple log levels, automatic log rotation, and specialized loggers for different concerns.

## Features

- **Structured Logging**: Consistent log format with timestamps, levels, and context
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Automatic rotation when files reach 10MB (keeps 5 backup files)
- **Specialized Loggers**: 
  - Performance metrics (execution times, cache hit rates)
  - API call tracking (Groq, MCP server)
  - Error tracking with stack traces
- **Flexible Output**: Human-readable or JSON format
- **Separate Log Files**: General, errors-only, and performance logs

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs                      # Directory for log files
LOG_ROTATION_ENABLED=true         # Enable automatic log rotation
LOG_JSON_FORMAT=false             # Output logs as JSON (useful for log aggregation)
```

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems (verbose)
- **INFO**: General informational messages about application flow
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for failures that don't stop the application
- **CRITICAL**: Critical errors that may cause application failure

## Log Files

The logging system creates three main log files in the `logs/` directory:

### 1. `bri.log` - General Application Log
Contains all log messages at the configured level and above.

**Example entries:**
```
2025-10-15 14:23:45 - INFO     - services.agent      - Processing message for video vid_123: What's happening...
2025-10-15 14:23:46 - INFO     - mcp_server.main     - Tool 'caption_frames' executed successfully in 0.52s
```

### 2. `bri_errors.log` - Errors Only
Contains only ERROR and CRITICAL level messages for quick error review.

**Example entries:**
```
2025-10-15 14:25:10 - ERROR    - services.agent      - Groq API call failed: Connection timeout
2025-10-15 14:25:10 - ERROR    - mcp_server.main     - Tool execution failed: Model not loaded
```

### 3. `bri_performance.log` - Performance Metrics
Contains performance-related logs including execution times and cache statistics.

**Example entries:**
```
2025-10-15 14:23:46 - INFO     - bri.performance.mcp_server.main - tool_caption_frames completed in 0.523s - SUCCESS
2025-10-15 14:23:47 - DEBUG    - bri.performance.mcp_server.cache - Cache HIT: bri:tool:captions:vid_123:abc
```

## Usage

### Basic Logging

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")

# Log exceptions with stack trace
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
```

### Performance Logging

```python
from utils.logging_config import get_performance_logger
import time

perf_logger = get_performance_logger(__name__)

# Log execution time
start_time = time.time()
result = process_video()
execution_time = time.time() - start_time

perf_logger.log_execution_time(
    "video_processing",
    execution_time,
    success=True,
    video_id="vid_123",
    frames_extracted=50
)

# Log cache hit/miss
perf_logger.log_cache_hit("bri:tool:captions:vid_123", hit=True)
```

### API Call Logging

```python
from utils.logging_config import get_api_logger
import time

api_logger = get_api_logger(__name__)

# Log successful API call
start_time = time.time()
response = groq_client.chat.completions.create(...)
execution_time = time.time() - start_time

api_logger.log_api_call(
    "Groq",
    "/chat/completions",
    method="POST",
    status_code=200,
    execution_time=execution_time
)

# Log failed API call
api_logger.log_api_call(
    "MCP",
    "/tools/caption_frames/execute",
    method="POST",
    execution_time=1.234,
    error="Connection timeout"
)
```

## Log Rotation

Log rotation is enabled by default and configured as follows:

- **Max File Size**: 10 MB per log file
- **Backup Count**: 5 backup files kept
- **Naming**: Rotated files are named `bri.log.1`, `bri.log.2`, etc.

When a log file reaches 10MB:
1. Current file is renamed to `.1`
2. Previous `.1` becomes `.2`, etc.
3. Oldest backup (`.5`) is deleted
4. New log file is created

To disable rotation, set `LOG_ROTATION_ENABLED=false` in `.env`.

## Monitoring

### View Live Logs

```bash
# Watch general log
tail -f logs/bri.log

# Watch errors only
tail -f logs/bri_errors.log

# Watch performance metrics
tail -f logs/bri_performance.log

# Filter for specific component
tail -f logs/bri.log | grep "services.agent"
```

### Search Logs

```bash
# Find all errors
grep "ERROR" logs/bri.log

# Find specific video processing
grep "vid_123" logs/bri.log

# Find slow operations (>1 second)
grep -E "completed in [1-9]\.[0-9]+s" logs/bri_performance.log
```

### Analyze Cache Performance

```bash
# Count cache hits vs misses
grep "Cache HIT" logs/bri_performance.log | wc -l
grep "Cache MISS" logs/bri_performance.log | wc -l

# Calculate hit rate
python -c "
hits = $(grep 'Cache HIT' logs/bri_performance.log | wc -l)
misses = $(grep 'Cache MISS' logs/bri_performance.log | wc -l)
total = hits + misses
rate = (hits / total * 100) if total > 0 else 0
print(f'Cache hit rate: {rate:.1f}%')
"
```

## Testing

Run the logging test suite to verify the system is working:

```bash
python scripts/test_logging.py
```

This will:
- Test all log levels
- Generate performance metrics
- Log API calls
- Test cache hit rate tracking
- Display log file summary

## Best Practices

### 1. Use Appropriate Log Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"Processing frame {frame_num} with params: {params}")

# INFO: General flow information
logger.info(f"Video {video_id} processing started")

# WARNING: Unexpected but handled situations
logger.warning(f"Cache unavailable, falling back to direct processing")

# ERROR: Errors that don't stop the application
logger.error(f"Failed to process frame {frame_num}", exc_info=True)

# CRITICAL: Severe errors that may stop the application
logger.critical(f"Database connection lost, cannot continue")
```

### 2. Include Context

Always include relevant context in log messages:

```python
# Good: Includes context
logger.info(f"Tool '{tool_name}' executed for video {video_id} in {time:.2f}s")

# Bad: Missing context
logger.info("Tool executed")
```

### 3. Log Performance Metrics

Track execution times for operations that may be slow:

```python
start_time = time.time()
result = expensive_operation()
execution_time = time.time() - start_time

perf_logger.log_execution_time(
    "expensive_operation",
    execution_time,
    success=True,
    **additional_context
)
```

### 4. Don't Log Sensitive Data

Never log sensitive information:

```python
# Bad: Logs API key
logger.info(f"Using API key: {api_key}")

# Good: Logs that key is set
logger.info("API key configured")
```

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration:
   ```bash
   echo $LOG_LEVEL
   ```

2. Verify log directory exists and is writable:
   ```bash
   ls -la logs/
   ```

3. Check if logging is initialized:
   ```python
   from utils.logging_config import setup_logging
   setup_logging()  # Call this early in your application
   ```

### Log Files Too Large

1. Enable log rotation if disabled:
   ```bash
   LOG_ROTATION_ENABLED=true
   ```

2. Reduce log level to reduce verbosity:
   ```bash
   LOG_LEVEL=WARNING  # Only warnings and errors
   ```

3. Manually clean old logs:
   ```bash
   rm logs/bri.log.*  # Remove rotated backups
   ```

### Performance Impact

Logging has minimal performance impact, but if needed:

1. Increase log level to reduce I/O:
   ```bash
   LOG_LEVEL=WARNING
   ```

2. Disable performance logging in production:
   ```python
   # Only log performance in development
   if Config.DEBUG:
       perf_logger.log_execution_time(...)
   ```

## Integration with Monitoring Tools

### JSON Format for Log Aggregation

Enable JSON format for integration with log aggregation tools (ELK, Splunk, etc.):

```bash
LOG_JSON_FORMAT=true
```

JSON log example:
```json
{
  "timestamp": "2025-10-15T14:23:45.123456",
  "level": "INFO",
  "logger": "services.agent",
  "message": "Processing message for video vid_123",
  "module": "agent",
  "function": "chat",
  "line": 123,
  "video_id": "vid_123",
  "execution_time": 0.523
}
```

### Metrics Export

Performance logs can be parsed and exported to monitoring systems:

```python
# Example: Export metrics to Prometheus
from prometheus_client import Counter, Histogram

tool_execution_time = Histogram('tool_execution_seconds', 'Tool execution time')
cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')
```

## Summary

The BRI logging system provides comprehensive monitoring capabilities:

- ✅ Structured logging with multiple levels
- ✅ Automatic log rotation
- ✅ Performance metrics tracking
- ✅ API call logging
- ✅ Cache hit rate monitoring
- ✅ Separate error logs
- ✅ Flexible output formats

For questions or issues, check the logs first - they contain detailed information about what's happening in the application.
