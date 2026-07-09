"""Response and query data models."""

from typing import Any

from pydantic import BaseModel, Field


class FrameWithContext(BaseModel):
    """Frame with associated context information."""
    frame_path: str = Field(..., description="Path to frame image")
    timestamp: float = Field(..., description="Timestamp in seconds")
    description: str | None = Field(None, description="Brief description of what's happening")


class AssistantMessageResponse(BaseModel):
    """Response from the assistant to the user."""
    message: str = Field(..., description="Response message text")
    frames: list[str] = Field(default_factory=list, description="List of frame image paths")
    timestamps: list[float] = Field(default_factory=list, description="List of relevant timestamps")
    suggestions: list[str] = Field(default_factory=list, description="Follow-up question suggestions")
    frame_contexts: list[FrameWithContext] | None = Field(
        None,
        description="Frames with their context (timestamp and description)"
    )


class UserQuery(BaseModel):
    """User query model."""
    video_id: str = Field(..., description="Video being queried")
    message: str = Field(..., description="User's query message")
    timestamp: float | None = Field(None, description="Optional timestamp reference")


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool via MCP server."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    video_id: str = Field(..., description="Video ID to process")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")


class ToolExecutionResponse(BaseModel):
    """Response from tool execution."""
    status: str = Field(..., description="Execution status: 'success' or 'error'")
    result: Any = Field(None, description="Tool execution result")
    cached: bool = Field(False, description="Whether result was retrieved from cache")
    execution_time: float = Field(..., description="Execution time in seconds")
