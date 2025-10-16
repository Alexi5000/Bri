"""API request validation and rate limiting."""

import time
from typing import Dict, Optional, Any, List
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field, validator
from storage.database import get_database
from utils.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API endpoints."""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per client
            burst_size: Maximum burst size (tokens in bucket)
        """
        self.rate = requests_per_minute / 60.0  # Requests per second
        self.burst_size = burst_size
        self.buckets: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"tokens": burst_size, "last_update": time.time()}
        )
        self.lock = Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: Client identifier (IP address or API key)
            
        Returns:
            True if request is allowed, False otherwise
        """
        with self.lock:
            now = time.time()
            bucket = self.buckets[client_id]
            
            # Refill tokens based on time elapsed
            time_elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(
                self.burst_size,
                bucket["tokens"] + time_elapsed * self.rate
            )
            bucket["last_update"] = now
            
            # Check if we have tokens available
            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                return True
            
            return False
    
    def get_retry_after(self, client_id: str) -> int:
        """
        Get seconds until next request is allowed.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Seconds to wait before retry
        """
        with self.lock:
            bucket = self.buckets[client_id]
            tokens_needed = 1.0 - bucket["tokens"]
            return int(tokens_needed / self.rate) + 1


class VideoIdValidator:
    """Validator for video_id existence in database."""
    
    @staticmethod
    def validate_video_exists(video_id: str) -> bool:
        """
        Check if video exists in database.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if video exists, False otherwise
        """
        try:
            db = get_database()
            result = db.execute_query(
                "SELECT video_id FROM videos WHERE video_id = ?",
                (video_id,)
            )
            return len(result) > 0
        except Exception as e:
            logger.error(f"Failed to validate video_id: {e}")
            return False
    
    @staticmethod
    def validate_or_raise(video_id: str) -> None:
        """
        Validate video exists or raise HTTPException.
        
        Args:
            video_id: Video identifier
            
        Raises:
            HTTPException: If video not found
        """
        if not VideoIdValidator.validate_video_exists(video_id):
            logger.warning(f"Video not found: {video_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video '{video_id}' not found"
            )


class RequestSizeValidator:
    """Validator for request payload sizes."""
    
    # Size limits in bytes
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_TOOL_PARAMS_SIZE = 1 * 1024 * 1024  # 1 MB
    MAX_ARRAY_LENGTH = 1000  # Maximum array items
    
    @staticmethod
    async def validate_request_size(request: Request) -> None:
        """
        Validate request body size.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If request is too large
        """
        content_length = request.headers.get("content-length")
        
        if content_length:
            content_length = int(content_length)
            if content_length > RequestSizeValidator.MAX_REQUEST_SIZE:
                logger.warning(
                    f"Request too large: {content_length} bytes "
                    f"(max: {RequestSizeValidator.MAX_REQUEST_SIZE})"
                )
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request body too large. Maximum size: {RequestSizeValidator.MAX_REQUEST_SIZE} bytes"
                )
    
    @staticmethod
    def validate_parameters(parameters: Dict[str, Any]) -> None:
        """
        Validate tool parameters size and structure.
        
        Args:
            parameters: Tool parameters dictionary
            
        Raises:
            HTTPException: If parameters are invalid
        """
        import json
        
        # Check serialized size
        try:
            params_json = json.dumps(parameters)
            params_size = len(params_json.encode('utf-8'))
            
            if params_size > RequestSizeValidator.MAX_TOOL_PARAMS_SIZE:
                logger.warning(f"Parameters too large: {params_size} bytes")
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Parameters too large. Maximum size: {RequestSizeValidator.MAX_TOOL_PARAMS_SIZE} bytes"
                )
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid parameters: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parameters format"
            )
        
        # Check array lengths
        for key, value in parameters.items():
            if isinstance(value, list):
                if len(value) > RequestSizeValidator.MAX_ARRAY_LENGTH:
                    logger.warning(f"Array '{key}' too long: {len(value)} items")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Array '{key}' exceeds maximum length of {RequestSizeValidator.MAX_ARRAY_LENGTH}"
                    )


class ValidatedToolExecutionRequest(BaseModel):
    """Validated tool execution request with constraints."""
    
    video_id: str = Field(..., min_length=1, max_length=255, description="Video identifier")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    
    @validator('video_id')
    def validate_video_id_format(cls, v):
        """Validate video_id format."""
        if not v or not v.strip():
            raise ValueError("video_id cannot be empty")
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', '..', '<', '>', '|', '*', '?']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f"video_id contains invalid character: {char}")
        
        return v.strip()
    
    @validator('parameters')
    def validate_parameters_structure(cls, v):
        """Validate parameters structure."""
        if not isinstance(v, dict):
            raise ValueError("parameters must be a dictionary")
        
        # Validate parameter values
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("parameter keys must be strings")
            
            # Check for reasonable nesting depth
            if isinstance(value, (dict, list)):
                cls._check_nesting_depth(value, max_depth=5)
        
        return v
    
    @staticmethod
    def _check_nesting_depth(obj: Any, max_depth: int, current_depth: int = 0):
        """Check nesting depth of nested structures."""
        if current_depth > max_depth:
            raise ValueError(f"parameters nesting exceeds maximum depth of {max_depth}")
        
        if isinstance(obj, dict):
            for value in obj.values():
                ValidatedToolExecutionRequest._check_nesting_depth(
                    value, max_depth, current_depth + 1
                )
        elif isinstance(obj, list):
            for item in obj:
                ValidatedToolExecutionRequest._check_nesting_depth(
                    item, max_depth, current_depth + 1
                )


class ValidatedProcessVideoRequest(BaseModel):
    """Validated video processing request."""
    
    tools: Optional[List[str]] = Field(None, description="List of tool names to execute")
    
    @validator('tools')
    def validate_tools_list(cls, v):
        """Validate tools list."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("tools must be a list")
            
            if len(v) > 10:
                raise ValueError("Maximum 10 tools can be specified")
            
            # Check for duplicates
            if len(v) != len(set(v)):
                raise ValueError("Duplicate tool names not allowed")
            
            # Validate tool names
            valid_tools = {'extract_frames', 'caption_frames', 'transcribe_audio', 'detect_objects'}
            for tool in v:
                if not isinstance(tool, str):
                    raise ValueError("Tool names must be strings")
                if tool not in valid_tools:
                    raise ValueError(f"Invalid tool name: {tool}")
        
        return v


class ValidatedProgressiveProcessRequest(BaseModel):
    """Validated progressive processing request."""
    
    video_path: str = Field(..., min_length=1, max_length=1024, description="Path to video file")
    
    @validator('video_path')
    def validate_video_path(cls, v):
        """Validate video path format."""
        if not v or not v.strip():
            raise ValueError("video_path cannot be empty")
        
        # Check for path traversal attempts
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid video_path: path traversal not allowed")
        
        # Check file extension
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        if not any(v.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Invalid video format. Supported: {', '.join(valid_extensions)}")
        
        return v.strip()


# Global rate limiters for different endpoint types
tool_execution_limiter = RateLimiter(requests_per_minute=120, burst_size=20)
video_processing_limiter = RateLimiter(requests_per_minute=30, burst_size=5)
general_limiter = RateLimiter(requests_per_minute=300, burst_size=50)


async def check_rate_limit(request: Request, limiter: RateLimiter) -> None:
    """
    Check rate limit for request.
    
    Args:
        request: FastAPI request object
        limiter: Rate limiter instance
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Use client IP as identifier
    client_id = request.client.host if request.client else "unknown"
    
    if not limiter.is_allowed(client_id):
        retry_after = limiter.get_retry_after(client_id)
        logger.warning(f"Rate limit exceeded for client {client_id}")
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )
