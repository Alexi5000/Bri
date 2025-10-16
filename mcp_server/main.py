"""FastAPI MCP Server for BRI video processing tools."""

import time
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.responses import ToolExecutionResponse
from mcp_server.registry import ToolRegistry
from mcp_server.cache import CacheManager
from mcp_server.validation import (
    ValidatedToolExecutionRequest,
    ValidatedProcessVideoRequest,
    ValidatedProgressiveProcessRequest,
    VideoIdValidator,
    RequestSizeValidator,
    check_rate_limit,
    tool_execution_limiter,
    video_processing_limiter,
    general_limiter
)
from mcp_server.middleware import (
    RequestIDMiddleware,
    ResponseStandardizationMiddleware,
    get_request_id,
    get_execution_time
)
from mcp_server.circuit_breaker import (
    database_breaker,
    cache_breaker,
    tool_execution_breaker,
    CircuitBreakerOpenError,
    retry_with_backoff
)
from mcp_server.versioning import (
    get_api_version,
    version_header,
    get_version_info,
    APIVersion
)
from mcp_server.response_models import (
    create_standard_response,
    create_paginated_response,
    ErrorDetail,
    HealthCheckResponse,
    ToolListResponse,
    ToolExecutionResponseV1,
    VideoProcessingResponse,
    VideoStatusResponse,
    QueueStatusResponse,
    CacheStatsResponse,
    CacheClearResponse,
    ResponseMetadata
)
from config import Config
from utils.logging_config import setup_logging, get_logger, get_performance_logger

# Setup logging
setup_logging(
    log_level=Config.LOG_LEVEL,
    log_dir=Config.LOG_DIR,
    json_format=Config.LOG_JSON_FORMAT,
    enable_rotation=Config.LOG_ROTATION_ENABLED
)

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BRI MCP Server",
    description="Model Context Protocol server for video processing tools",
    version="1.0.0"
)

# Add custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(ResponseStandardizationMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tool registry and cache
tool_registry = ToolRegistry()
cache_manager = CacheManager()


@app.on_event("startup")
async def startup_event():
    """Initialize server components on startup."""
    logger.info("Starting BRI MCP Server...")
    
    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Ensure directories exist
    Config.ensure_directories()
    logger.info("Required directories verified")
    
    # Register all available tools
    tool_registry.register_all_tools()
    
    logger.info(f"Registered {len(tool_registry.list_tools())} tools")
    
    # Start processing queue workers
    try:
        from services.processing_queue import start_queue_workers
        await start_queue_workers()
        logger.info("Processing queue workers started")
    except Exception as e:
        logger.error(f"Failed to start queue workers: {e}")
    
    logger.info(f"Server running on {Config.get_mcp_server_url()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("Shutting down BRI MCP Server...")
    
    # Shutdown processing queue gracefully
    try:
        from services.processing_queue import shutdown_queue
        await shutdown_queue()
        logger.info("Processing queue shutdown complete")
    except Exception as e:
        logger.error(f"Error during queue shutdown: {e}")
    
    cache_manager.close()


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "BRI MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools_available": len(tool_registry.list_tools()),
        "api_versioning": get_version_info()
    }


@app.get("/version")
async def get_version():
    """Get API version information."""
    return get_version_info()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint with detailed component status."""
    import datetime
    
    # Check database connectivity
    db_healthy = True
    db_circuit_state = database_breaker.get_state()
    try:
        from storage.database import get_database
        db = get_database()
        db.execute_query("SELECT 1")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
    
    # Check cache connectivity
    cache_healthy = Config.REDIS_ENABLED
    cache_circuit_state = cache_breaker.get_state()
    if cache_healthy:
        try:
            cache_manager.get("health_check")
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            cache_healthy = False
    
    # Get circuit breaker states
    tool_circuit_state = tool_execution_breaker.get_state()
    
    # Determine overall status
    if db_healthy and (cache_healthy or not Config.REDIS_ENABLED):
        overall_status = "healthy"
    elif db_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return HealthCheckResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        checks={
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "circuit_breaker": db_circuit_state
            },
            "cache": {
                "status": "healthy" if cache_healthy else ("disabled" if not Config.REDIS_ENABLED else "unhealthy"),
                "enabled": Config.REDIS_ENABLED,
                "circuit_breaker": cache_circuit_state
            },
            "tools": {
                "status": "healthy",
                "count": len(tool_registry.list_tools()),
                "circuit_breaker": tool_circuit_state
            }
        }
    )


@app.get("/tools", response_model=ToolListResponse)
@app.get("/v1/tools", response_model=ToolListResponse)
async def list_tools(request: Request, version: APIVersion = get_api_version):
    """
    List all available tools with their schemas.
    
    Supports versioned endpoint: /v1/tools
    
    Returns:
        Standardized response with list of tool definitions
    """
    # Rate limiting
    await check_rate_limit(request, general_limiter)
    
    try:
        tools = tool_registry.list_tools()
        logger.info(f"Listed {len(tools)} available tools (API v{version.value})")
        
        response = ToolListResponse(
            success=True,
            data={"tools": tools, "count": len(tools)},
            metadata=ResponseMetadata(
                request_id=get_request_id(request),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                version=version.value,
                execution_time=get_execution_time(request)
            )
        )
        
        # Add version headers
        return response
        
    except Exception as e:
        logger.error(f"Failed to list tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@app.post("/tools/{tool_name}/execute")
@app.post("/v1/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    exec_request: ValidatedToolExecutionRequest,
    request: Request,
    version: APIVersion = get_api_version
):
    """
    Execute a specific tool with provided parameters and timeout handling.
    
    Args:
        tool_name: Name of the tool to execute
        exec_request: Tool execution request with video_id and parameters
        request: FastAPI request object
        
    Returns:
        Tool execution response with result, status, and metadata
    """
    import asyncio
    
    # Rate limiting
    await check_rate_limit(request, tool_execution_limiter)
    
    # Request size validation
    await RequestSizeValidator.validate_request_size(request)
    
    # Validate parameters size
    RequestSizeValidator.validate_parameters(exec_request.parameters)
    
    # Validate video exists
    VideoIdValidator.validate_or_raise(exec_request.video_id)
    
    start_time = time.time()
    timeout_seconds = Config.TOOL_EXECUTION_TIMEOUT
    
    try:
        # Validate tool exists
        tool = tool_registry.get_tool(tool_name)
        if tool is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
            )
        
        # Check cache first
        cache_key = cache_manager.generate_cache_key(
            tool_name,
            exec_request.video_id,
            exec_request.parameters
        )
        
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            execution_time = time.time() - start_time
            logger.info(f"Cache hit for {tool_name} on video {exec_request.video_id}")
            perf_logger.log_cache_hit(cache_key, hit=True)
            return ToolExecutionResponseV1(
                success=True,
                data={
                    "status": "success",
                    "result": cached_result,
                    "cached": True,
                    "tool_name": tool_name,
                    "video_id": exec_request.video_id
                },
                metadata=ResponseMetadata(
                    request_id=get_request_id(request),
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    version="1.0.0",
                    execution_time=execution_time
                )
            )
        
        # Execute tool with timeout
        logger.info(f"Executing tool '{tool_name}' for video {exec_request.video_id} (timeout: {timeout_seconds}s)")
        perf_logger.log_cache_hit(cache_key, hit=False)
        
        try:
            result = await asyncio.wait_for(
                tool.execute(exec_request.video_id, exec_request.parameters),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.error(f"Tool '{tool_name}' execution timed out after {timeout_seconds}s")
            perf_logger.log_execution_time(
                f"tool_{tool_name}",
                execution_time,
                success=False,
                video_id=exec_request.video_id,
                error="timeout"
            )
            return ToolExecutionResponseV1(
                success=False,
                data={
                    "status": "error",
                    "error": f"Tool execution timed out after {timeout_seconds} seconds",
                    "cached": False,
                    "tool_name": tool_name,
                    "video_id": exec_request.video_id
                },
                metadata=ResponseMetadata(
                    request_id=get_request_id(request),
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    version="1.0.0",
                    execution_time=execution_time
                )
            )
        
        # Cache the result
        cache_manager.set(cache_key, result)
        
        # Store result in database for later retrieval
        logger.info(f"Storing {tool_name} results in database for video {exec_request.video_id}...")
        _store_tool_result_in_db(exec_request.video_id, tool_name, result)
        logger.info(f"✓ Database storage confirmed for {tool_name}")
        
        execution_time = time.time() - start_time
        logger.info(
            f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s"
        )
        perf_logger.log_execution_time(
            f"tool_{tool_name}",
            execution_time,
            success=True,
            video_id=exec_request.video_id,
            cached=False
        )
        
        return ToolExecutionResponseV1(
            success=True,
            data={
                "status": "success",
                "result": result,
                "cached": False,
                "tool_name": tool_name,
                "video_id": exec_request.video_id
            },
            metadata=ResponseMetadata(
                request_id=get_request_id(request),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                version="1.0.0",
                execution_time=execution_time
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Tool execution failed: {str(e)}")
        return ToolExecutionResponseV1(
            success=False,
            data={
                "status": "error",
                "error": str(e),
                "cached": False,
                "tool_name": tool_name,
                "video_id": exec_request.video_id
            },
            metadata=ResponseMetadata(
                request_id=get_request_id(request),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                version="1.0.0",
                execution_time=execution_time
            )
        )


@app.post("/videos/{video_id}/process")
@app.post("/v1/videos/{video_id}/process")
async def process_video(
    video_id: str,
    process_request: ValidatedProcessVideoRequest,
    request: Request,
    version: APIVersion = get_api_version
):
    """
    Process a video with multiple tools in batch with parallel execution.
    
    Args:
        video_id: Video identifier
        process_request: Processing request with optional tools list
        request: FastAPI request object
        
    Returns:
        Processing status and results from all tools
    """
    import asyncio
    
    # Rate limiting
    await check_rate_limit(request, video_processing_limiter)
    
    # Request size validation
    await RequestSizeValidator.validate_request_size(request)
    
    # Validate video exists
    VideoIdValidator.validate_or_raise(video_id)
    
    start_time = time.time()
    
    try:
        # Default to all tools if not specified
        tools = process_request.tools
        if tools is None:
            tools = [tool["name"] for tool in tool_registry.list_tools()]
        
        logger.info(f"Processing video {video_id} with tools: {tools} (parallel execution)")
        
        # Create tasks for parallel execution
        tasks = []
        tool_names = []
        
        for tool_name in tools:
            tool = tool_registry.get_tool(tool_name)
            if tool is None:
                logger.warning(f"Tool '{tool_name}' not found, skipping")
                continue
            
            # Check cache first
            cache_key = cache_manager.generate_cache_key(
                tool_name,
                video_id,
                {}
            )
            
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {tool_name}")
                # Skip creating task for cached results
                continue
            
            # Create async task for tool execution
            tasks.append(_execute_tool_with_cache(tool, tool_name, video_id, cache_key))
            tool_names.append(tool_name)
        
        # Execute all tools in parallel
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            task_results = []
        
        # Process results
        results = {}
        errors = {}
        
        # Add cached results
        for tool_name in tools:
            cache_key = cache_manager.generate_cache_key(tool_name, video_id, {})
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None and tool_name not in tool_names:
                results[tool_name] = {
                    "result": cached_result,
                    "cached": True
                }
        
        # Add parallel execution results
        for tool_name, result in zip(tool_names, task_results):
            if isinstance(result, Exception):
                logger.error(f"Tool '{tool_name}' failed: {str(result)}")
                errors[tool_name] = str(result)
            else:
                results[tool_name] = {
                    "result": result,
                    "cached": False
                }
                logger.info(f"Tool '{tool_name}' completed successfully")
        
        execution_time = time.time() - start_time
        
        logger.info(
            f"Video processing complete: {len(results)} succeeded, "
            f"{len(errors)} failed in {execution_time:.2f}s (parallel)"
        )
        perf_logger.log_execution_time(
            "video_processing",
            execution_time,
            success=len(errors) == 0,
            video_id=video_id,
            tools_succeeded=len(results),
            tools_failed=len(errors)
        )
        
        return VideoProcessingResponse(
            success=len(errors) == 0,
            data={
                "status": "complete" if not errors else "partial",
                "video_id": video_id,
                "results": results,
                "errors": errors if errors else None,
                "parallel_execution": True,
                "tools_succeeded": len(results),
                "tools_failed": len(errors)
            },
            metadata=ResponseMetadata(
                request_id=get_request_id(request),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                version="1.0.0",
                execution_time=execution_time
            )
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Video processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing failed: {str(e)}"
        )


async def _execute_tool_with_cache(tool, tool_name: str, video_id: str, cache_key: str):
    """Execute a tool and cache the result.
    
    Args:
        tool: Tool instance to execute
        tool_name: Name of the tool
        video_id: Video identifier
        cache_key: Cache key for storing result
        
    Returns:
        Tool execution result
        
    Raises:
        Exception: If tool execution fails
    """
    try:
        result = await tool.execute(video_id, {})
        
        # Cache the result
        cache_manager.set(cache_key, result)
        logger.debug(f"Cached {tool_name} results for video {video_id}")
        
        # Store result in database for later retrieval
        logger.info(f"Storing {tool_name} results in database for video {video_id}...")
        _store_tool_result_in_db(video_id, tool_name, result)
        logger.info(f"✓ Database storage confirmed for {tool_name}")
        
        return result
    except Exception as e:
        logger.error(f"Tool '{tool_name}' execution failed: {str(e)}")
        raise


def _store_tool_result_in_db(video_id: str, tool_name: str, result: dict):
    """Store tool result in database for later retrieval by the agent.
    
    Uses VideoProcessingService for centralized storage with:
    - Transaction support
    - Validation after INSERT
    - Retry logic with exponential backoff
    - Comprehensive logging
    """
    try:
        from services.video_processing_service import get_video_processing_service
        
        service = get_video_processing_service()
        
        # Store results with transaction support and validation
        counts = service.store_tool_results(video_id, tool_name, result)
        
        # Log detailed metrics
        for data_type, count in counts.items():
            logger.info(f"✓ Stored {count} {data_type} for video {video_id}")
        
    except Exception as e:
        logger.error(f"Failed to store tool result in database: {e}", exc_info=True)


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics.
    
    Returns:
        Cache statistics including total keys and memory usage
    """
    try:
        stats = cache_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@app.delete("/cache/videos/{video_id}")
async def clear_video_cache(video_id: str):
    """
    Clear all cached results for a specific video.
    
    Args:
        video_id: Video identifier
        
    Returns:
        Number of cache entries deleted
    """
    try:
        deleted = cache_manager.clear_video_cache(video_id)
        logger.info(f"Cleared {deleted} cache entries for video {video_id}")
        return {
            "status": "success",
            "video_id": video_id,
            "deleted_count": deleted
        }
    except Exception as e:
        logger.error(f"Failed to clear video cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear video cache: {str(e)}"
        )


@app.delete("/cache")
async def clear_all_cache():
    """
    Clear all BRI cache entries.
    
    Returns:
        Success status
    """
    try:
        success = cache_manager.clear_all()
        if success:
            logger.info("Cleared all cache entries")
            return {"status": "success", "message": "All cache entries cleared"}
        else:
            return {"status": "skipped", "message": "Cache not enabled"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@app.get("/videos/{video_id}/status")
async def get_video_data_status(video_id: str, request: Request):
    """
    Get data completeness status for a video.
    
    Shows detailed information about what data has been processed and stored:
    - Frames extracted
    - Captions generated
    - Transcripts created
    - Objects detected
    
    Args:
        video_id: Video identifier
        request: FastAPI request object
        
    Returns:
        Detailed status report with counts for each data type
        
    Example Response:
        {
            "video_id": "vid_123",
            "complete": true,
            "frames": {"count": 10, "present": true},
            "captions": {"count": 10, "present": true},
            "transcripts": {"count": 5, "present": true},
            "objects": {"count": 10, "present": true},
            "missing": []
        }
    """
    # Rate limiting
    await check_rate_limit(request, general_limiter)
    
    # Validate video exists
    VideoIdValidator.validate_or_raise(video_id)
    
    try:
        from services.video_processing_service import get_video_processing_service
        
        service = get_video_processing_service()
        status_report = service.verify_video_data_completeness(video_id)
        
        logger.info(
            f"Video {video_id} status: complete={status_report['complete']}, "
            f"missing={status_report['missing']}"
        )
        
        return status_report
        
    except Exception as e:
        logger.error(f"Failed to get video status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video status: {str(e)}"
        )


@app.post("/videos/{video_id}/process-progressive")
async def process_video_progressive(
    video_id: str,
    prog_request: ValidatedProgressiveProcessRequest,
    http_request: Request,
    priority: str = "normal"  # "high", "normal", "low"
):
    """
    Process a video progressively through 3 stages using job queue.
    
    Stages:
    1. EXTRACTING (Fast - 10s): Extract frames → User can start chatting
    2. CAPTIONING (Medium - 60s): Generate captions → Richer responses
    3. TRANSCRIBING (Slow - 120s): Full transcription + objects → Complete intelligence
    
    This endpoint returns immediately and processing continues in background queue.
    Use GET /videos/{video_id}/progress to check status.
    
    Args:
        video_id: Video identifier
        prog_request: Request with video_path
        http_request: FastAPI request object
        priority: Job priority ("high", "normal", "low")
        
    Returns:
        Immediate response with processing queued confirmation
    """
    # Rate limiting
    await check_rate_limit(http_request, video_processing_limiter)
    
    # Request size validation
    await RequestSizeValidator.validate_request_size(http_request)
    
    # Validate video exists
    VideoIdValidator.validate_or_raise(video_id)
    
    try:
        from services.processing_queue import get_processing_queue, JobPriority
        
        queue = get_processing_queue()
        
        # Map priority string to enum
        priority_map = {
            "high": JobPriority.HIGH,
            "normal": JobPriority.NORMAL,
            "low": JobPriority.LOW
        }
        job_priority = priority_map.get(priority.lower(), JobPriority.NORMAL)
        
        # Add job to queue
        job = await queue.add_job(
            video_id=video_id,
            video_path=prog_request.video_path,
            priority=job_priority
        )
        
        logger.info(
            f"Added video {video_id} to processing queue "
            f"(priority: {priority}, status: {job.status})"
        )
        
        # Get queue status
        queue_status = queue.get_status()
        
        return {
            "status": "queued" if job.status == 'queued' else "processing",
            "video_id": video_id,
            "message": f"Video added to processing queue with {priority} priority",
            "queue_position": len([j for j in queue.queue if j.priority <= job.priority]),
            "queue_size": queue_status['queued_jobs'],
            "active_jobs": queue_status['active_jobs'],
            "stages": [
                "Stage 1: Extracting frames (10s)",
                "Stage 2: Generating captions (60s)",
                "Stage 3: Transcription + objects (120s)"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to queue progressive processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue processing: {str(e)}"
        )


@app.get("/videos/{video_id}/progress")
async def get_processing_progress(video_id: str, request: Request):
    """
    Get current processing progress for a video.
    
    Args:
        video_id: Video identifier
        request: FastAPI request object
        
    Returns:
        Current processing progress or None if not processing
        
    Example Response:
        {
            "video_id": "vid_123",
            "stage": "captioning",
            "progress_percent": 45.0,
            "message": "Analyzing video content... 🔍",
            "frames_extracted": 10,
            "captions_generated": 5,
            "transcript_segments": 0,
            "objects_detected": 0
        }
    """
    # Rate limiting
    await check_rate_limit(request, general_limiter)
    
    # Validate video exists
    VideoIdValidator.validate_or_raise(video_id)
    
    try:
        from services.progressive_processor import get_progressive_processor
        
        processor = get_progressive_processor()
        progress = processor.get_progress(video_id)
        
        if progress is None:
            return {
                "video_id": video_id,
                "processing": False,
                "message": "No active processing for this video"
            }
        
        return {
            "video_id": progress.video_id,
            "processing": True,
            "stage": progress.stage.value,
            "progress_percent": progress.progress_percent,
            "message": progress.message,
            "frames_extracted": progress.frames_extracted,
            "captions_generated": progress.captions_generated,
            "transcript_segments": progress.transcript_segments,
            "objects_detected": progress.objects_detected
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )


@app.get("/circuit-breakers")
async def get_circuit_breaker_status(request: Request):
    """
    Get status of all circuit breakers.
    
    Returns:
        Status of all circuit breakers in the system
    """
    # Rate limiting
    await check_rate_limit(request, general_limiter)
    
    return create_standard_response(
        data={
            "circuit_breakers": {
                "database": database_breaker.get_state(),
                "cache": cache_breaker.get_state(),
                "tool_execution": tool_execution_breaker.get_state()
            }
        },
        execution_time=get_execution_time(request),
        request_id=get_request_id(request)
    )


@app.post("/circuit-breakers/{breaker_name}/reset")
async def reset_circuit_breaker(breaker_name: str, request: Request):
    """
    Manually reset a circuit breaker.
    
    Args:
        breaker_name: Name of circuit breaker to reset
        request: FastAPI request object
        
    Returns:
        Success status
    """
    # Rate limiting
    await check_rate_limit(request, general_limiter)
    
    breakers = {
        "database": database_breaker,
        "cache": cache_breaker,
        "tool_execution": tool_execution_breaker
    }
    
    if breaker_name not in breakers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Circuit breaker '{breaker_name}' not found"
        )
    
    breaker = breakers[breaker_name]
    breaker.reset()
    
    logger.info(f"Circuit breaker '{breaker_name}' reset via API")
    
    return create_standard_response(
        data={
            "message": f"Circuit breaker '{breaker_name}' reset successfully",
            "state": breaker.get_state()
        },
        execution_time=get_execution_time(request),
        request_id=get_request_id(request)
    )


@app.get("/queue/status")
async def get_queue_status():
    """
    Get processing queue status.
    
    Returns:
        Queue statistics including active jobs, queued jobs, and completed jobs
    """
    try:
        from services.processing_queue import get_processing_queue
        
        queue = get_processing_queue()
        status = queue.get_status()
        
        return {
            "status": "running",
            "active_jobs": status['active_jobs'],
            "queued_jobs": status['queued_jobs'],
            "completed_jobs": status['completed_jobs'],
            "workers": status['workers'],
            "shutdown_requested": status['shutdown_requested']
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        )


@app.get("/queue/job/{video_id}")
async def get_job_status(video_id: str):
    """
    Get status of a specific processing job.
    
    Args:
        video_id: Video identifier
        
    Returns:
        Job status or 404 if not found
    """
    try:
        from services.processing_queue import get_processing_queue
        
        queue = get_processing_queue()
        job_status = queue.get_job_status(video_id)
        
        if job_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No job found for video {video_id}"
            )
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


async def _run_progressive_processing(video_id: str, video_path: str):
    """
    Run progressive processing in background.
    
    Args:
        video_id: Video identifier
        video_path: Path to video file
    """
    try:
        from services.progressive_processor import get_progressive_processor
        
        processor = get_progressive_processor()
        await processor.process_video_progressive(video_id, video_path)
        
        logger.info(f"Progressive processing completed for video {video_id}")
        
    except Exception as e:
        logger.error(f"Progressive processing failed for video {video_id}: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "detail": "An unexpected error occurred",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=Config.MCP_SERVER_HOST,
        port=Config.MCP_SERVER_PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    )
