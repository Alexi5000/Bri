"""FastAPI MCP Server for BRI video processing tools."""

import logging
import time
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.responses import ToolExecutionRequest, ToolExecutionResponse
from mcp_server.registry import ToolRegistry
from mcp_server.cache import CacheManager
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BRI MCP Server",
    description="Model Context Protocol server for video processing tools",
    version="1.0.0"
)

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
    logger.info(f"Server running on {Config.get_mcp_server_url()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("Shutting down BRI MCP Server...")
    cache_manager.close()


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "BRI MCP Server",
        "version": "1.0.0",
        "status": "running",
        "tools_available": len(tool_registry.list_tools())
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cache_enabled": Config.REDIS_ENABLED,
        "tools_registered": len(tool_registry.list_tools())
    }


@app.get("/tools")
async def list_tools():
    """
    List all available tools with their schemas.
    
    Returns:
        List of tool definitions with names, descriptions, and parameter schemas
    """
    try:
        tools = tool_registry.list_tools()
        logger.info(f"Listed {len(tools)} available tools")
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Failed to list tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """
    Execute a specific tool with provided parameters and timeout handling.
    
    Args:
        tool_name: Name of the tool to execute
        request: Tool execution request with video_id and parameters
        
    Returns:
        Tool execution response with result, status, and metadata
    """
    import asyncio
    
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
            request.video_id,
            request.parameters
        )
        
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            execution_time = time.time() - start_time
            logger.info(f"Cache hit for {tool_name} on video {request.video_id}")
            return ToolExecutionResponse(
                status="success",
                result=cached_result,
                cached=True,
                execution_time=execution_time
            )
        
        # Execute tool with timeout
        logger.info(f"Executing tool '{tool_name}' for video {request.video_id} (timeout: {timeout_seconds}s)")
        
        try:
            result = await asyncio.wait_for(
                tool.execute(request.video_id, request.parameters),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.error(f"Tool '{tool_name}' execution timed out after {timeout_seconds}s")
            return ToolExecutionResponse(
                status="error",
                result={"error": f"Tool execution timed out after {timeout_seconds} seconds"},
                cached=False,
                execution_time=execution_time
            )
        
        # Cache the result
        cache_manager.set(cache_key, result)
        
        execution_time = time.time() - start_time
        logger.info(
            f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s"
        )
        
        return ToolExecutionResponse(
            status="success",
            result=result,
            cached=False,
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Tool execution failed: {str(e)}")
        return ToolExecutionResponse(
            status="error",
            result={"error": str(e)},
            cached=False,
            execution_time=execution_time
        )


class ProcessVideoRequest(BaseModel):
    """Request model for batch video processing."""
    tools: Optional[list] = None


@app.post("/videos/{video_id}/process")
async def process_video(
    video_id: str,
    request: ProcessVideoRequest = ProcessVideoRequest()
):
    """
    Process a video with multiple tools in batch with parallel execution.
    
    Args:
        video_id: Video identifier
        tools: Optional list of tool names to run. If None, runs all tools.
        
    Returns:
        Processing status and results from all tools
    """
    import asyncio
    
    start_time = time.time()
    
    try:
        # Default to all tools if not specified
        tools = request.tools
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
        
        response = {
            "status": "complete" if not errors else "partial",
            "video_id": video_id,
            "results": results,
            "errors": errors if errors else None,
            "execution_time": execution_time,
            "parallel_execution": True
        }
        
        logger.info(
            f"Video processing complete: {len(results)} succeeded, "
            f"{len(errors)} failed in {execution_time:.2f}s (parallel)"
        )
        
        return response
        
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
        return result
    except Exception as e:
        logger.error(f"Tool '{tool_name}' execution failed: {str(e)}")
        raise


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
