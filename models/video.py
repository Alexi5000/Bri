"""Video-related data models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VideoMetadata(BaseModel):
    """Metadata about a video file."""
    duration: float = Field(..., description="Video duration in seconds")
    fps: float = Field(..., description="Frames per second")
    width: int = Field(..., description="Video width in pixels")
    height: int = Field(..., description="Video height in pixels")
    codec: str = Field(..., description="Video codec")
    file_size: int = Field(..., description="File size in bytes")


class Video(BaseModel):
    """Video record model."""
    video_id: str = Field(..., description="Unique video identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to video file")
    duration: float = Field(..., description="Video duration in seconds")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    processing_status: str = Field(default="pending", description="Processing status: pending, processing, complete, error")
    thumbnail_path: Optional[str] = Field(None, description="Path to thumbnail image")


class Frame(BaseModel):
    """Extracted video frame."""
    timestamp: float = Field(..., description="Frame timestamp in seconds")
    image_path: str = Field(..., description="Path to frame image file")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image data")
    frame_number: int = Field(..., description="Frame number in video")
