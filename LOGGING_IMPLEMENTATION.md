# BRI Video Agent - Comprehensive Logging Implementation

## 🎯 Goal
Implement production-grade logging for full observability without external alerting services.

---

## 📊 Logging Architecture

### Log Levels Strategy

```
DEBUG    → Development only (verbose details)
INFO     → Normal operations (processing started/completed)
WARNING  → Potential issues (slow queries, cache misses)
ERROR    → Recoverable errors (tool failures, validation errors)
CRITICAL → System failures (database down, out of memory)
```

### Log Categories

1. **Application Logs** - General app behavior
2. **Performance Logs** - Timing and metrics
3. **API Logs** - HTTP requests/responses
4. **Database Logs** - Query execution
5. **Pipeline Logs** - Video processing stages
6. **Audit Logs** - Data mutations
7. **Error Logs** - Exceptions and failures

---

## 🔧 Implementation

### 1. Enhanced Logging Configuration

**File: `utils/logging_config.py`** (UPDATE EXISTING)

```python
"""Enhanced logging configuration for BRI video agent."""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from config import Config


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""
    
    def __init__(self):
        super().__init__()
        self.context = {}
    
    def filter(self, record):
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True
    
    def set_context(self, **kwargs):
        """Set context for subsequent logs."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context."""
        self.context.clear()


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context if available
        if hasattr(record, 'video_id'):
            log_data['video_id'] = record.video_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"bri.performance.{name}")
    
    def log_execution_time(
        self,
        operation: str,
        execution_time: float,
        success: bool = True,
        **kwargs
    ):
        """Log operation execution time."""
        log_data = {
            "operation": operation,
            "execution_time": execution_time,
            "success": success,
            **kwargs
        }
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"{operation} completed in {execution_time:.2f}s",
            extra=log_data
        )
    
    def log_cache_hit(self, key: str, hit: bool):
        """Log cache hit/miss."""
        self.logger.info(
            f"Cache {'HIT' if hit else 'MISS'}: {key}",
            extra={"cache_key": key, "cache_hit": hit}
        )


class AuditLogger:
    """Logger for audit trail."""
    
    def __init__(self):
        self.logger = logging.getLogger("bri.audit")
    
    def log_data_mutation(
        self,
        operation: str,
        table: str,
        record_id: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log data mutation."""
        log_data = {
            "operation": operation,
            "table": table,
            "record_id": record_id,
            **kwargs
        }
        
        if data:
            log_data["data"] = data
        
        self.logger.info(
            f"{operation} on {table}: {record_id}",
            extra=log_data
        )


class PipelineLogger:
    """Logger for video processing pipeline."""
    
    def __init__(self):
        self.logger = logging.getLogger("bri.pipeline")
    
    def log_stage_start(self, video_id: str, stage: str):
        """Log pipeline stage start."""
        self.logger.info(
            f"Pipeline stage started: {stage}",
            extra={"video_id": video_id, "stage": stage, "event": "stage_start"}
        )
    
    def log_stage_complete(
        self,
        video_id: str,
        stage: str,
        duration: float,
        result_count: int
    ):
        """Log pipeline stage completion."""
        self.logger.info(
            f"Pipeline stage completed: {stage} ({result_count} results in {duration:.2f}s)",
            extra={
                "video_id": video_id,
                "stage": stage,
                "duration": duration,
                "result_count": result_count,
                "event": "stage_complete"
            }
        )
    
    def log_stage_error(self, video_id: str, stage: str, error: str):
        """Log pipeline stage error."""
        self.logger.error(
            f"Pipeline stage failed: {stage} - {error}",
            extra={"video_id": video_id, "stage": stage, "error": error, "event": "stage_error"}
        )


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    json_format: bool = False,
    enable_rotation: bool = True
):
    """Setup comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        json_format: Use JSON format for logs
        enable_rotation: Enable log rotation
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(name)-20s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_rotation:
        # Main application log (rotating)
        app_handler = logging.handlers.TimedRotatingFileHandler(
            log_path / "bri_app.log",
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        
        # Error log (rotating)
        error_handler = logging.handlers.TimedRotatingFileHandler(
            log_path / "bri_error.log",
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Performance log (rotating)
        perf_handler = logging.handlers.TimedRotatingFileHandler(
            log_path / "bri_performance.log",
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.addFilter(logging.Filter('bri.performance'))
        
        # Audit log (rotating)
        audit_handler = logging.handlers.TimedRotatingFileHandler(
            log_path / "bri_audit.log",
            when='midnight',
            interval=1,
            backupCount=90,  # Keep audit logs longer
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.addFilter(logging.Filter('bri.audit'))
        
        # Pipeline log (rotating)
        pipeline_handler = logging.handlers.TimedRotatingFileHandler(
            log_path / "bri_pipeline.log",
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        pipeline_handler.setLevel(logging.INFO)
        pipeline_handler.addFilter(logging.Filter('bri.pipeline'))
    else:
        # Simple file handlers (no rotation)
        app_handler = logging.FileHandler(log_path / "bri_app.log", encoding='utf-8')
        error_handler = logging.FileHandler(log_path / "bri_error.log", encoding='utf-8')
        perf_handler = logging.FileHandler(log_path / "bri_performance.log", encoding='utf-8')
        audit_handler = logging.FileHandler(log_path / "bri_audit.log", encoding='utf-8')
        pipeline_handler = logging.FileHandler(log_path / "bri_pipeline.log", encoding='utf-8')
    
    # Set formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)-8s - %(name)-20s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    for handler in [app_handler, error_handler, perf_handler, audit_handler, pipeline_handler]:
        handler.setFormatter(formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(perf_handler)
    root_logger.addHandler(audit_handler)
    root_logger.addHandler(pipeline_handler)
    
    # Log startup
    logging.info("="*80)
    logging.info("BRI Video Agent - Logging initialized")
    logging.info(f"Log level: {log_level}")
    logging.info(f"Log directory: {log_path.absolute()}")
    logging.info(f"JSON format: {json_format}")
    logging.info(f"Log rotation: {enable_rotation}")
    logging.info("="*80)


def get_logger(name: str) -> logging.Logger:
    """Get logger for module."""
    return logging.getLogger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get performance logger."""
    return PerformanceLogger(name)


def get_audit_logger() -> AuditLogger:
    """Get audit logger."""
    return AuditLogger()


def get_pipeline_logger() -> PipelineLogger:
    """Get pipeline logger."""
    return PipelineLogger()


# Context manager for request logging
class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.filter = ContextFilter()
    
    def __enter__(self):
        self.filter.set_context(**self.context)
        logging.getLogger().addFilter(self.filter)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.getLogger().removeFilter(self.filter)
        self.filter.clear_context()
```

---

## 📝 Usage Examples

### 1. Basic Logging

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

logger.debug("Detailed debug information")
logger.info("Normal operation")
logger.warning("Something unusual happened")
logger.error("An error occurred")
logger.critical("System failure!")
```

### 2. Performance Logging

```python
from utils.logging_config import get_performance_logger
import time

perf_logger = get_performance_logger(__name__)

start = time.time()
# ... do work ...
duration = time.time() - start

perf_logger.log_execution_time(
    "video_processing",
    duration,
    success=True,
    video_id="abc123",
    frames_processed=87
)
```

### 3. Audit Logging

```python
from utils.logging_config import get_audit_logger

audit_logger = get_audit_logger()

audit_logger.log_data_mutation(
    operation="INSERT",
    table="video_context",
    record_id="caption_123",
    video_id="abc123",
    context_type="caption"
)
```

### 4. Pipeline Logging

```python
from utils.logging_config import get_pipeline_logger
import time

pipeline_logger = get_pipeline_logger()

# Stage start
pipeline_logger.log_stage_start("abc123", "frame_extraction")

start = time.time()
# ... extract frames ...
duration = time.time() - start

# Stage complete
pipeline_logger.log_stage_complete("abc123", "frame_extraction", duration, 87)

# Or stage error
try:
    # ... process ...
    pass
except Exception as e:
    pipeline_logger.log_stage_error("abc123", "frame_extraction", str(e))
```

### 5. Context Logging

```python
from utils.logging_config import LogContext, get_logger

logger = get_logger(__name__)

with LogContext(video_id="abc123", request_id="req_456"):
    logger.info("Processing video")  # Includes video_id and request_id
    logger.info("Extracting frames")  # Also includes context
```

---

## 📊 Log Analysis Scripts

### 1. Error Summary

**File: `scripts/analyze_errors.py`**

```python
"""Analyze error logs."""

import json
from collections import Counter
from pathlib import Path

def analyze_errors(log_file="logs/bri_error.log"):
    """Analyze error patterns."""
    errors = []
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                errors.append(log.get('message', ''))
            except:
                # Plain text log
                if 'ERROR' in line:
                    errors.append(line.split(' - ')[-1].strip())
    
    # Count error types
    error_counts = Counter(errors)
    
    print("Top 10 Errors:")
    print("="*80)
    for error, count in error_counts.most_common(10):
        print(f"{count:4d}x  {error[:70]}")

if __name__ == "__main__":
    analyze_errors()
```

### 2. Performance Report

**File: `scripts/performance_report.py`**

```python
"""Generate performance report from logs."""

import json
from collections import defaultdict
from pathlib import Path

def performance_report(log_file="logs/bri_performance.log"):
    """Generate performance report."""
    operations = defaultdict(list)
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                if 'operation' in log and 'execution_time' in log:
                    operations[log['operation']].append(log['execution_time'])
            except:
                pass
    
    print("Performance Report:")
    print("="*80)
    print(f"{'Operation':<30} {'Count':>8} {'Avg':>10} {'Min':>10} {'Max':>10}")
    print("-"*80)
    
    for op, times in sorted(operations.items()):
        count = len(times)
        avg = sum(times) / count
        min_time = min(times)
        max_time = max(times)
        print(f"{op:<30} {count:>8} {avg:>10.2f}s {min_time:>10.2f}s {max_time:>10.2f}s")

if __name__ == "__main__":
    performance_report()
```

### 3. Pipeline Status

**File: `scripts/pipeline_status.py`**

```python
"""Check pipeline processing status."""

import json
from collections import defaultdict
from pathlib import Path

def pipeline_status(log_file="logs/bri_pipeline.log"):
    """Check pipeline status."""
    videos = defaultdict(lambda: {"stages": {}, "errors": []})
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                if 'video_id' not in log:
                    continue
                
                video_id = log['video_id']
                stage = log.get('stage', 'unknown')
                event = log.get('event', 'unknown')
                
                if event == 'stage_complete':
                    videos[video_id]['stages'][stage] = 'complete'
                elif event == 'stage_error':
                    videos[video_id]['stages'][stage] = 'error'
                    videos[video_id]['errors'].append(log.get('error', 'Unknown'))
            except:
                pass
    
    print("Pipeline Status:")
    print("="*80)
    
    for video_id, data in videos.items():
        print(f"\nVideo: {video_id}")
        print(f"  Stages: {data['stages']}")
        if data['errors']:
            print(f"  Errors: {data['errors']}")

if __name__ == "__main__":
    pipeline_status()
```

---

## 🎯 Integration Points

### Update MCP Server

**File: `mcp_server/main.py`**

```python
from utils.logging_config import (
    get_logger,
    get_performance_logger,
    get_audit_logger,
    get_pipeline_logger,
    LogContext
)

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)
audit_logger = get_audit_logger()
pipeline_logger = get_pipeline_logger()

@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """Execute tool with comprehensive logging."""
    
    with LogContext(video_id=request.video_id, tool_name=tool_name):
        logger.info(f"Executing tool: {tool_name}")
        
        start_time = time.time()
        
        try:
            # Execute tool
            result = await tool.execute(...)
            
            # Log success
            duration = time.time() - start_time
            perf_logger.log_execution_time(
                f"tool_{tool_name}",
                duration,
                success=True,
                video_id=request.video_id
            )
            
            # Log audit trail
            audit_logger.log_data_mutation(
                "INSERT",
                "video_context",
                f"{tool_name}_{request.video_id}",
                video_id=request.video_id,
                tool=tool_name
            )
            
            logger.info(f"Tool {tool_name} completed successfully")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
            
            perf_logger.log_execution_time(
                f"tool_{tool_name}",
                duration,
                success=False,
                video_id=request.video_id,
                error=str(e)
            )
            
            raise
```

---

## 📈 Log Monitoring Dashboard (Simple)

**File: `scripts/log_dashboard.py`**

```python
"""Simple log monitoring dashboard."""

import time
from pathlib import Path
from collections import deque

def tail_logs(log_file="logs/bri_app.log", lines=50):
    """Tail log file like 'tail -f'."""
    
    print(f"Monitoring: {log_file}")
    print("="*80)
    
    # Read last N lines
    with open(log_file) as f:
        recent = deque(f, maxlen=lines)
        for line in recent:
            print(line.rstrip())
    
    # Follow new lines
    with open(log_file) as f:
        f.seek(0, 2)  # Go to end
        while True:
            line = f.readline()
            if line:
                print(line.rstrip())
            else:
                time.sleep(0.1)

if __name__ == "__main__":
    import sys
    log_file = sys.argv[1] if len(sys.argv) > 1 else "logs/bri_app.log"
    tail_logs(log_file)
```

---

## ✅ Verification Checklist

After implementing comprehensive logging:

- [ ] All log files created in `logs/` directory
- [ ] Logs rotate daily
- [ ] Error logs separate from info logs
- [ ] Performance metrics logged
- [ ] Audit trail for data mutations
- [ ] Pipeline stages logged
- [ ] Context (video_id) in all relevant logs
- [ ] Analysis scripts work
- [ ] Can tail logs in real-time
- [ ] 30-day retention working

---

## 🚀 Quick Commands

```bash
# Tail application logs
python scripts/log_dashboard.py logs/bri_app.log

# Analyze errors
python scripts/analyze_errors.py

# Performance report
python scripts/performance_report.py

# Pipeline status
python scripts/pipeline_status.py

# View specific log
tail -f logs/bri_pipeline.log

# Search logs
grep "ERROR" logs/bri_app.log

# Count errors today
grep "$(date +%Y-%m-%d)" logs/bri_error.log | wc -l
```

---

**This comprehensive logging system provides full observability without external services.**
