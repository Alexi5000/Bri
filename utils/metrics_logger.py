"""Operational metrics logging for BRI.

Logs detailed metrics for:
- Database operations
- API calls
- Pipeline stages
- Resource usage
- Cache performance
- Model inference times
"""

import logging
import time
import psutil
import os
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps

from utils.logging_config import get_logger, get_performance_logger, LogContext

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class MetricsLogger:
    """Centralized metrics logging for operational monitoring."""
    
    @staticmethod
    def log_database_query(
        query_type: str,
        table: str,
        execution_time: float,
        rows_affected: Optional[int] = None,
        video_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log database query metrics.
        
        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            execution_time: Query execution time in seconds
            rows_affected: Number of rows affected
            video_id: Video ID for context
            success: Whether query succeeded
            error: Error message if failed
        """
        with LogContext(video_id=video_id):
            extra_fields = {
                'metric_type': 'database',
                'query_type': query_type,
                'table': table,
                'execution_time': execution_time,
                'rows_affected': rows_affected,
                'success': success
            }
            
            if error:
                extra_fields['error'] = error
            
            level = logging.ERROR if not success else logging.INFO
            message = f"DB {query_type} on {table}: {execution_time:.3f}s"
            
            if rows_affected is not None:
                message += f" ({rows_affected} rows)"
            
            if error:
                message += f" - ERROR: {error}"
            
            log_record = logger.makeRecord(
                logger.name,
                level,
                "(metrics)",
                0,
                message,
                (),
                None
            )
            log_record.extra_fields = extra_fields
            logger.handle(log_record)
    
    @staticmethod
    def log_api_call(
        api_name: str,
        endpoint: str,
        method: str,
        status_code: Optional[int],
        execution_time: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        video_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log API call metrics.
        
        Args:
            api_name: API name (Groq, MCP, etc.)
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            execution_time: Request execution time
            request_size: Request payload size in bytes
            response_size: Response payload size in bytes
            video_id: Video ID for context
            error: Error message if failed
        """
        with LogContext(video_id=video_id):
            extra_fields = {
                'metric_type': 'api',
                'api_name': api_name,
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'execution_time': execution_time,
                'request_size_bytes': request_size,
                'response_size_bytes': response_size
            }
            
            if error:
                extra_fields['error'] = error
            
            success = status_code and 200 <= status_code < 300
            level = logging.ERROR if not success else logging.INFO
            
            message = f"API {api_name} {method} {endpoint}: {execution_time:.3f}s"
            
            if status_code:
                message += f" [{status_code}]"
            
            if request_size:
                message += f" (req: {request_size} bytes)"
            
            if response_size:
                message += f" (resp: {response_size} bytes)"
            
            if error:
                message += f" - ERROR: {error}"
            
            log_record = logger.makeRecord(
                logger.name,
                level,
                "(metrics)",
                0,
                message,
                (),
                None
            )
            log_record.extra_fields = extra_fields
            logger.handle(log_record)
    
    @staticmethod
    def log_pipeline_stage(
        stage: str,
        video_id: str,
        status: str,
        execution_time: float,
        items_processed: Optional[int] = None,
        success_rate: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Log pipeline stage metrics.
        
        Args:
            stage: Pipeline stage (extract, caption, transcribe, detect)
            video_id: Video ID
            status: Stage status (started, completed, failed)
            execution_time: Stage execution time
            items_processed: Number of items processed
            success_rate: Success rate (0-1)
            error: Error message if failed
        """
        with LogContext(video_id=video_id):
            extra_fields = {
                'metric_type': 'pipeline',
                'pipeline_stage': stage,
                'video_id': video_id,
                'status': status,
                'execution_time': execution_time,
                'items_processed': items_processed,
                'success_rate': success_rate
            }
            
            if error:
                extra_fields['error'] = error
            
            level = logging.ERROR if status == 'failed' else logging.INFO
            
            message = f"Pipeline {stage} {status} for {video_id}: {execution_time:.2f}s"
            
            if items_processed:
                message += f" ({items_processed} items)"
            
            if success_rate is not None:
                message += f" (success: {success_rate*100:.1f}%)"
            
            if error:
                message += f" - ERROR: {error}"
            
            log_record = logger.makeRecord(
                logger.name,
                level,
                "(metrics)",
                0,
                message,
                (),
                None
            )
            log_record.extra_fields = extra_fields
            logger.handle(log_record)
    
    @staticmethod
    def log_resource_usage(
        component: str,
        video_id: Optional[str] = None
    ):
        """Log current resource usage.
        
        Args:
            component: Component name
            video_id: Video ID for context
        """
        try:
            process = psutil.Process(os.getpid())
            
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Disk usage
            disk_usage = psutil.disk_usage('.')
            disk_percent = disk_usage.percent
            
            with LogContext(video_id=video_id):
                extra_fields = {
                    'metric_type': 'resource',
                    'component': component,
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'disk_percent': disk_percent
                }
                
                message = (
                    f"Resources [{component}]: "
                    f"CPU={cpu_percent:.1f}%, "
                    f"Memory={memory_mb:.1f}MB, "
                    f"Disk={disk_percent:.1f}%"
                )
                
                log_record = logger.makeRecord(
                    logger.name,
                    logging.INFO,
                    "(metrics)",
                    0,
                    message,
                    (),
                    None
                )
                log_record.extra_fields = extra_fields
                logger.handle(log_record)
                
        except Exception as e:
            logger.error(f"Failed to log resource usage: {e}")
    
    @staticmethod
    def log_cache_operation(
        operation: str,
        cache_key: str,
        hit: bool,
        cache_size: Optional[int] = None,
        video_id: Optional[str] = None
    ):
        """Log cache operation metrics.
        
        Args:
            operation: Operation type (get, set, delete)
            cache_key: Cache key
            hit: Whether cache hit occurred (for get operations)
            cache_size: Size of cached data in bytes
            video_id: Video ID for context
        """
        with LogContext(video_id=video_id):
            extra_fields = {
                'metric_type': 'cache',
                'operation': operation,
                'cache_key': cache_key,
                'cache_hit': hit,
                'cache_size_bytes': cache_size
            }
            
            status = "HIT" if hit else "MISS"
            message = f"Cache {operation.upper()} {status}: {cache_key}"
            
            if cache_size:
                message += f" ({cache_size} bytes)"
            
            log_record = logger.makeRecord(
                logger.name,
                logging.DEBUG,
                "(metrics)",
                0,
                message,
                (),
                None
            )
            log_record.extra_fields = extra_fields
            logger.handle(log_record)
    
    @staticmethod
    def log_model_inference(
        model_name: str,
        operation: str,
        execution_time: float,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
        video_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log model inference metrics.
        
        Args:
            model_name: Model name (BLIP, Whisper, YOLO)
            operation: Operation type (caption, transcribe, detect)
            execution_time: Inference time in seconds
            input_size: Input size (frames, audio length, etc.)
            output_size: Output size (captions, segments, detections)
            video_id: Video ID for context
            success: Whether inference succeeded
            error: Error message if failed
        """
        with LogContext(video_id=video_id):
            extra_fields = {
                'metric_type': 'model_inference',
                'model_name': model_name,
                'operation': operation,
                'execution_time': execution_time,
                'input_size': input_size,
                'output_size': output_size,
                'success': success
            }
            
            if error:
                extra_fields['error'] = error
            
            level = logging.ERROR if not success else logging.INFO
            
            message = f"Model {model_name} {operation}: {execution_time:.3f}s"
            
            if input_size:
                message += f" (input: {input_size})"
            
            if output_size:
                message += f" (output: {output_size})"
            
            if error:
                message += f" - ERROR: {error}"
            
            log_record = logger.makeRecord(
                logger.name,
                level,
                "(metrics)",
                0,
                message,
                (),
                None
            )
            log_record.extra_fields = extra_fields
            logger.handle(log_record)


def track_database_query(query_type: str, table: str):
    """Decorator to track database query metrics.
    
    Args:
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            rows_affected = None
            success = True
            
            try:
                result = func(*args, **kwargs)
                
                # Try to get rows affected from result
                if hasattr(result, 'rowcount'):
                    rows_affected = result.rowcount
                elif isinstance(result, (list, tuple)):
                    rows_affected = len(result)
                
                return result
                
            except Exception as e:
                success = False
                error = str(e)
                raise
                
            finally:
                execution_time = time.time() - start_time
                
                # Extract video_id from kwargs if present
                video_id = kwargs.get('video_id')
                
                MetricsLogger.log_database_query(
                    query_type=query_type,
                    table=table,
                    execution_time=execution_time,
                    rows_affected=rows_affected,
                    video_id=video_id,
                    success=success,
                    error=error
                )
        
        return wrapper
    return decorator


def track_api_call(api_name: str, endpoint: str, method: str = "POST"):
    """Decorator to track API call metrics.
    
    Args:
        api_name: API name
        endpoint: API endpoint
        method: HTTP method
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status_code = None
            
            try:
                result = await func(*args, **kwargs)
                status_code = 200
                return result
                
            except Exception as e:
                error = str(e)
                status_code = 500
                raise
                
            finally:
                execution_time = time.time() - start_time
                video_id = kwargs.get('video_id')
                
                MetricsLogger.log_api_call(
                    api_name=api_name,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    execution_time=execution_time,
                    video_id=video_id,
                    error=error
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status_code = None
            
            try:
                result = func(*args, **kwargs)
                status_code = 200
                return result
                
            except Exception as e:
                error = str(e)
                status_code = 500
                raise
                
            finally:
                execution_time = time.time() - start_time
                video_id = kwargs.get('video_id')
                
                MetricsLogger.log_api_call(
                    api_name=api_name,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    execution_time=execution_time,
                    video_id=video_id,
                    error=error
                )
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_model_inference(model_name: str, operation: str):
    """Decorator to track model inference metrics.
    
    Args:
        model_name: Model name
        operation: Operation type
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            success = True
            output_size = None
            
            try:
                result = func(*args, **kwargs)
                
                # Try to get output size
                if isinstance(result, (list, tuple)):
                    output_size = len(result)
                
                return result
                
            except Exception as e:
                success = False
                error = str(e)
                raise
                
            finally:
                execution_time = time.time() - start_time
                video_id = kwargs.get('video_id')
                
                MetricsLogger.log_model_inference(
                    model_name=model_name,
                    operation=operation,
                    execution_time=execution_time,
                    output_size=output_size,
                    video_id=video_id,
                    success=success,
                    error=error
                )
        
        return wrapper
    return decorator
