"""Structured logging configuration for BRI application.

Provides centralized logging setup with:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- Structured log formatting with timestamps
- Log rotation policy
- Performance metrics logging
- Cache hit rate tracking
- API call logging
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json
import threading
from contextvars import ContextVar

from config import Config

# Context variables for request-scoped logging
_log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output option."""
    
    def __init__(self, json_format: bool = False):
        """Initialize formatter.
        
        Args:
            json_format: If True, output logs as JSON. Otherwise use human-readable format.
        """
        self.json_format = json_format
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        if self.json_format:
            return self._format_json(record)
        else:
            return self._format_human_readable(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context variables (video_id, request_id, user_id, etc.)
        context = _log_context.get()
        if context:
            log_data.update(context)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)
    
    def _format_human_readable(self, record: logging.LogRecord) -> str:
        """Format log record in human-readable format."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Color codes for different log levels (if terminal supports it)
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m'  # Magenta
        }
        reset = '\033[0m'
        
        # Use colors only if outputting to terminal
        use_colors = hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()
        
        if use_colors:
            level_color = colors.get(record.levelname, '')
            level_str = f"{level_color}{record.levelname:8s}{reset}"
        else:
            level_str = f"{record.levelname:8s}"
        
        base_msg = f"{timestamp} - {level_str} - {record.name:20s} - {record.getMessage()}"
        
        # Add context information if present
        context = _log_context.get()
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            base_msg += f" [{context_str}]"
        
        # Add exception info if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg


class PerformanceLogger:
    """Logger for performance metrics and timing information."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize performance logger.
        
        Args:
            logger: Base logger to use
        """
        self.logger = logger
    
    def log_execution_time(
        self,
        operation: str,
        execution_time: float,
        success: bool = True,
        **kwargs
    ) -> None:
        """Log execution time for an operation.
        
        Args:
            operation: Name of the operation
            execution_time: Time taken in seconds
            success: Whether operation succeeded
            **kwargs: Additional context fields
        """
        status = "SUCCESS" if success else "FAILED"
        extra_fields = {
            'operation': operation,
            'execution_time': execution_time,
            'status': status,
            **kwargs
        }
        
        log_record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "(performance)",
            0,
            f"{operation} completed in {execution_time:.3f}s - {status}",
            (),
            None
        )
        log_record.extra_fields = extra_fields
        self.logger.handle(log_record)
    
    def log_cache_hit(self, cache_key: str, hit: bool) -> None:
        """Log cache hit/miss.
        
        Args:
            cache_key: Cache key accessed
            hit: True if cache hit, False if miss
        """
        status = "HIT" if hit else "MISS"
        extra_fields = {
            'cache_key': cache_key,
            'cache_status': status
        }
        
        log_record = self.logger.makeRecord(
            self.logger.name,
            logging.DEBUG,
            "(cache)",
            0,
            f"Cache {status}: {cache_key}",
            (),
            None
        )
        log_record.extra_fields = extra_fields
        self.logger.handle(log_record)


class APILogger:
    """Logger for API calls and responses."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize API logger.
        
        Args:
            logger: Base logger to use
        """
        self.logger = logger
    
    def log_api_call(
        self,
        api_name: str,
        endpoint: str,
        method: str = "POST",
        status_code: Optional[int] = None,
        execution_time: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Log API call details.
        
        Args:
            api_name: Name of the API (e.g., "Groq", "MCP")
            endpoint: API endpoint called
            method: HTTP method
            status_code: Response status code
            execution_time: Time taken in seconds
            error: Error message if call failed
        """
        extra_fields = {
            'api_name': api_name,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'execution_time': execution_time
        }
        
        if error:
            level = logging.ERROR
            message = f"{api_name} API call failed: {endpoint} - {error}"
            extra_fields['error'] = error
        else:
            level = logging.INFO
            time_str = f" ({execution_time:.3f}s)" if execution_time else ""
            message = f"{api_name} API call: {method} {endpoint}{time_str}"
        
        log_record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(api)",
            0,
            message,
            (),
            None
        )
        log_record.extra_fields = extra_fields
        self.logger.handle(log_record)


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    json_format: bool = False,
    enable_rotation: bool = True
) -> None:
    """Setup application-wide logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR). Uses Config.LOG_LEVEL if not provided.
        log_dir: Directory for log files. Uses Config.LOG_DIR if not provided.
        json_format: If True, output logs as JSON
        enable_rotation: If True, enable log rotation
    """
    # Get configuration
    log_level = log_level or Config.LOG_LEVEL
    log_dir = log_dir or Config.LOG_DIR
    
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    formatter = StructuredFormatter(json_format=json_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (always human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(StructuredFormatter(json_format=False))
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    general_log_file = os.path.join(log_dir, 'bri.log')
    if enable_rotation:
        # Time-based rotating file handler: Daily rotation, keep 30 days
        file_handler = logging.handlers.TimedRotatingFileHandler(
            general_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 30-day retention
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler(general_log_file, encoding='utf-8')
    
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # File handler for errors only
    error_log_file = os.path.join(log_dir, 'bri_errors.log')
    if enable_rotation:
        error_handler = logging.handlers.TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 30-day retention
            encoding='utf-8'
        )
    else:
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # File handler for performance metrics
    perf_log_file = os.path.join(log_dir, 'bri_performance.log')
    if enable_rotation:
        perf_handler = logging.handlers.TimedRotatingFileHandler(
            perf_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 30-day retention
            encoding='utf-8'
        )
    else:
        perf_handler = logging.FileHandler(perf_log_file, encoding='utf-8')
    
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(formatter)
    
    # Add performance handler to specific loggers
    perf_logger = logging.getLogger('bri.performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)
    
    # File handler for audit logs
    audit_log_file = os.path.join(log_dir, 'bri_audit.log')
    if enable_rotation:
        audit_handler = logging.handlers.TimedRotatingFileHandler(
            audit_log_file,
            when='midnight',
            interval=1,
            backupCount=90,  # Keep audit logs for 90 days (compliance)
            encoding='utf-8'
        )
    else:
        audit_handler = logging.FileHandler(audit_log_file, encoding='utf-8')
    
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(formatter)
    
    # Add audit handler to audit loggers
    audit_logger = logging.getLogger('bri.audit')
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    
    # File handler for pipeline logs
    pipeline_log_file = os.path.join(log_dir, 'bri_pipeline.log')
    if enable_rotation:
        pipeline_handler = logging.handlers.TimedRotatingFileHandler(
            pipeline_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 30-day retention
            encoding='utf-8'
        )
    else:
        pipeline_handler = logging.FileHandler(pipeline_log_file, encoding='utf-8')
    
    pipeline_handler.setLevel(logging.INFO)
    pipeline_handler.setFormatter(formatter)
    
    # Add pipeline handler to pipeline loggers
    pipeline_logger = logging.getLogger('bri.pipeline')
    pipeline_logger.addHandler(pipeline_handler)
    pipeline_logger.setLevel(logging.INFO)
    
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    
    root_logger.info(f"Logging initialized: level={log_level}, dir={log_dir}, rotation={enable_rotation}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        PerformanceLogger instance
    """
    logger = logging.getLogger(f'bri.performance.{name}')
    return PerformanceLogger(logger)


def get_api_logger(name: str) -> APILogger:
    """Get an API logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        APILogger instance
    """
    logger = logging.getLogger(f'bri.api.{name}')
    return APILogger(logger)


class LogContext:
    """Context manager for adding contextual information to logs.
    
    Usage:
        with LogContext(video_id="vid_123", request_id="req_456"):
            logger.info("Processing video")  # Includes video_id and request_id
    """
    
    def __init__(self, **kwargs):
        """Initialize log context.
        
        Args:
            **kwargs: Context key-value pairs (e.g., video_id, request_id, user_id)
        """
        self.context = kwargs
        self.token = None
    
    def __enter__(self):
        """Enter context and set context variables."""
        current_context = _log_context.get().copy()
        current_context.update(self.context)
        self.token = _log_context.set(current_context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous context."""
        if self.token:
            _log_context.reset(self.token)


class AuditLogger:
    """Logger for audit trail of data mutations."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize audit logger.
        
        Args:
            logger: Base logger to use
        """
        self.logger = logger
    
    def log_data_mutation(
        self,
        operation: str,  # 'INSERT', 'UPDATE', 'DELETE'
        table: str,
        record_id: str,
        changes: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log data mutation for audit trail.
        
        Args:
            operation: Type of operation (INSERT, UPDATE, DELETE)
            table: Database table name
            record_id: ID of the affected record
            changes: Dictionary of changed fields (for UPDATE)
            user_id: ID of user performing the operation
            **kwargs: Additional context
        """
        extra_fields = {
            'audit_operation': operation,
            'audit_table': table,
            'audit_record_id': record_id,
            'audit_user_id': user_id,
            **kwargs
        }
        
        if changes:
            extra_fields['audit_changes'] = changes
        
        message = f"AUDIT: {operation} on {table} (record_id={record_id})"
        if user_id:
            message += f" by user {user_id}"
        
        log_record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "(audit)",
            0,
            message,
            (),
            None
        )
        log_record.extra_fields = extra_fields
        self.logger.handle(log_record)


class PipelineLogger:
    """Logger for data pipeline stages."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize pipeline logger.
        
        Args:
            logger: Base logger to use
        """
        self.logger = logger
    
    def log_stage(
        self,
        stage: str,  # 'extract', 'caption', 'transcribe', 'detect'
        video_id: str,
        status: str,  # 'started', 'completed', 'failed'
        execution_time: Optional[float] = None,
        items_processed: Optional[int] = None,
        error: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log pipeline stage execution.
        
        Args:
            stage: Pipeline stage name
            video_id: Video being processed
            status: Stage status
            execution_time: Time taken in seconds
            items_processed: Number of items processed (frames, segments, etc.)
            error: Error message if failed
            **kwargs: Additional context
        """
        extra_fields = {
            'pipeline_stage': stage,
            'video_id': video_id,
            'pipeline_status': status,
            **kwargs
        }
        
        if execution_time is not None:
            extra_fields['execution_time'] = execution_time
        
        if items_processed is not None:
            extra_fields['items_processed'] = items_processed
        
        if error:
            extra_fields['error'] = error
        
        level = logging.ERROR if status == 'failed' else logging.INFO
        
        message = f"Pipeline {stage} {status} for video {video_id}"
        if execution_time:
            message += f" in {execution_time:.2f}s"
        if items_processed:
            message += f" ({items_processed} items)"
        if error:
            message += f" - {error}"
        
        log_record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(pipeline)",
            0,
            message,
            (),
            None
        )
        log_record.extra_fields = extra_fields
        self.logger.handle(log_record)


def get_audit_logger(name: str) -> AuditLogger:
    """Get an audit logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        AuditLogger instance
    """
    logger = logging.getLogger(f'bri.audit.{name}')
    return AuditLogger(logger)


def get_pipeline_logger(name: str) -> PipelineLogger:
    """Get a pipeline logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        PipelineLogger instance
    """
    logger = logging.getLogger(f'bri.pipeline.{name}')
    return PipelineLogger(logger)
