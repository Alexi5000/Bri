"""Standardized API response models."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResponseMetadata(BaseModel):
    """Metadata included in all API responses."""

    request_id: str = Field(..., description="Unique request identifier for tracing")
    timestamp: str = Field(..., description="ISO 8601 timestamp of response")
    version: str = Field(default="1.0.0", description="API version")
    execution_time: float = Field(..., description="Execution time in seconds")


class StandardResponse(BaseModel):
    """Standard response wrapper for all API endpoints."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Any | None = Field(None, description="Response data")
    error: dict[str, Any] | None = Field(None, description="Error information if failed")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class PaginatedResponse(BaseModel):
    """Paginated response for list endpoints."""

    success: bool = Field(True, description="Whether the request was successful")
    data: list[Any] = Field(..., description="List of items")
    pagination: dict[str, Any] = Field(..., description="Pagination information")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    suggestion: str | None = Field(None, description="Suggested action to resolve error")


def create_standard_response(
    data: Any = None,
    error: ErrorDetail | None = None,
    execution_time: float | None = None,
    request_id: str | None = None,
) -> StandardResponse:
    """
    Create a standardized API response.

    Args:
        data: Response data
        error: Error information if failed
        execution_time: Execution time in seconds
        request_id: Request identifier for tracing

    Returns:
        Standardized response object
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    if execution_time is None:
        execution_time = 0.0

    metadata = ResponseMetadata(
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0",
        execution_time=execution_time,
    )

    return StandardResponse(
        success=error is None, data=data, error=error.dict() if error else None, metadata=metadata
    )


def create_paginated_response(
    items: list[Any],
    page: int,
    page_size: int,
    total_items: int,
    execution_time: float | None = None,
    request_id: str | None = None,
) -> PaginatedResponse:
    """
    Create a paginated API response.

    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_items: Total number of items across all pages
        execution_time: Execution time in seconds
        request_id: Request identifier for tracing

    Returns:
        Paginated response object
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    if execution_time is None:
        execution_time = 0.0

    total_pages = (total_items + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1

    metadata = ResponseMetadata(
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0",
        execution_time=execution_time,
    )

    pagination = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }

    return PaginatedResponse(success=True, data=items, pagination=pagination, metadata=metadata)


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status: healthy, degraded, unhealthy")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    checks: dict[str, Any] = Field(..., description="Individual component health checks")


class ToolListResponse(BaseModel):
    """Response for listing available tools."""

    success: bool = Field(True, description="Whether the request was successful")
    data: dict[str, Any] = Field(..., description="Tools data")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class ToolExecutionResponseV1(BaseModel):
    """Standardized tool execution response."""

    success: bool = Field(..., description="Whether execution was successful")
    data: dict[str, Any] = Field(..., description="Execution result data")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class VideoProcessingResponse(BaseModel):
    """Response for video processing operations."""

    success: bool = Field(..., description="Whether processing was successful")
    data: dict[str, Any] = Field(..., description="Processing results")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class VideoStatusResponse(BaseModel):
    """Response for video status check."""

    success: bool = Field(True, description="Whether the request was successful")
    data: dict[str, Any] = Field(..., description="Video status data")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class QueueStatusResponse(BaseModel):
    """Response for queue status."""

    success: bool = Field(True, description="Whether the request was successful")
    data: dict[str, Any] = Field(..., description="Queue status data")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class CacheStatsResponse(BaseModel):
    """Response for cache statistics."""

    success: bool = Field(True, description="Whether the request was successful")
    data: dict[str, Any] = Field(..., description="Cache statistics")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class CacheClearResponse(BaseModel):
    """Response for cache clear operations."""

    success: bool = Field(True, description="Whether operation was successful")
    data: dict[str, Any] = Field(..., description="Clear operation results")
    metadata: ResponseMetadata = Field(..., description="Response metadata")
