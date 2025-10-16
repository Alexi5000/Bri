"""Custom middleware for API request/response handling."""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        """
        Add request ID to request state and response headers.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with request ID header
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state for access in handlers
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown"
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Calculate execution time
        execution_time = time.time() - request.state.start_time
        response.headers["X-Execution-Time"] = f"{execution_time:.3f}s"
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "execution_time": execution_time
            }
        )
        
        return response


class ResponseStandardizationMiddleware(BaseHTTPMiddleware):
    """Middleware to standardize API responses."""
    
    async def dispatch(self, request: Request, call_next):
        """
        Standardize response format.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Standardized response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Handle unexpected errors with standardized format
            logger.error(
                f"Unhandled exception in request: {str(e)}",
                exc_info=True,
                extra={
                    "request_id": getattr(request.state, "request_id", "unknown"),
                    "method": request.method,
                    "path": request.url.path
                }
            )
            
            execution_time = time.time() - getattr(request.state, "start_time", time.time())
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            
            error_response = {
                "success": False,
                "data": None,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"error": str(e)}
                },
                "metadata": {
                    "request_id": request_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "version": "1.0.0",
                    "execution_time": execution_time
                }
            }
            
            return JSONResponse(
                status_code=500,
                content=error_response,
                headers={
                    "X-Request-ID": request_id,
                    "X-Execution-Time": f"{execution_time:.3f}s"
                }
            )


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def get_execution_time(request: Request) -> float:
    """
    Get execution time for current request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Execution time in seconds
    """
    start_time = getattr(request.state, "start_time", time.time())
    return time.time() - start_time
