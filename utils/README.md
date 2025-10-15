# BRI Utilities

This directory contains utility modules for the BRI application.

## Logging Configuration (`logging_config.py`)

Comprehensive logging and monitoring system for BRI.

### Features

- **Structured Logging**: Consistent format with timestamps and context
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Automatic rotation at 10MB (keeps 5 backups)
- **Specialized Loggers**:
  - `PerformanceLogger`: Track execution times and cache hit rates
  - `APILogger`: Log API calls and responses
- **Flexible Output**: Human-readable or JSON format
- **Separate Log Files**: General, errors-only, and performance logs

### Quick Start

```python
from utils.logging_config import setup_logging, get_logger

# Initialize logging (call once at application startup)
setup_logging()

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("Application started")
logger.error("Something went wrong", exc_info=True)
```

### Performance Logging

```python
from utils.logging_config import get_performance_logger
import time

perf_logger = get_performance_logger(__name__)

# Log execution time
start = time.time()
result = expensive_operation()
perf_logger.log_execution_time(
    "expensive_operation",
    time.time() - start,
    success=True,
    video_id="vid_123"
)

# Log cache hit/miss
perf_logger.log_cache_hit("cache_key", hit=True)
```

### API Logging

```python
from utils.logging_config import get_api_logger

api_logger = get_api_logger(__name__)

# Log API call
api_logger.log_api_call(
    "Groq",
    "/chat/completions",
    method="POST",
    status_code=200,
    execution_time=0.523
)
```

### Configuration

Set these environment variables in `.env`:

```bash
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs                      # Directory for log files
LOG_ROTATION_ENABLED=true         # Enable automatic log rotation
LOG_JSON_FORMAT=false             # Output logs as JSON
```

### Log Files

- `logs/bri.log` - All log messages
- `logs/bri_errors.log` - Errors only
- `logs/bri_performance.log` - Performance metrics

### Testing

Run the test suite to verify logging is working:

```bash
python scripts/test_logging.py
```

### Documentation

See `docs/logging_guide.md` for comprehensive documentation.
