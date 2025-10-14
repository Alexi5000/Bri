"""Tool-related data models for video processing results."""

from pydantic import BaseModel, Field
from typing import List, Tuple


class Caption(BaseModel):
    """Image caption for a video frame."""
    frame_timestamp: float = Field(..., description="Timestamp of the captioned frame")
    text: str = Field(..., description="Caption text")
    confidence: float = Field(..., description="Caption confidence score")


class TranscriptSegment(BaseModel):
    """A segment of transcribed audio."""
    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence score")


class Transcript(BaseModel):
    """Complete video transcript."""
    segments: List[TranscriptSegment] = Field(default_factory=list, description="List of transcript segments")
    language: str = Field(..., description="Detected language")
    full_text: str = Field(..., description="Complete transcript text")


class DetectedObject(BaseModel):
    """A detected object in a frame."""
    class_name: str = Field(..., description="Object class name")
    confidence: float = Field(..., description="Detection confidence score")
    bbox: Tuple[int, int, int, int] = Field(..., description="Bounding box (x, y, width, height)")


class DetectionResult(BaseModel):
    """Object detection results for a frame."""
    frame_timestamp: float = Field(..., description="Frame timestamp in seconds")
    objects: List[DetectedObject] = Field(default_factory=list, description="List of detected objects")
