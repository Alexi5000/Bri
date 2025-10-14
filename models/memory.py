"""Memory and conversation-related data models."""

from pydantic import BaseModel, Field
from datetime import datetime


class MemoryRecord(BaseModel):
    """A single conversation turn stored in memory."""
    message_id: str = Field(..., description="Unique message identifier")
    video_id: str = Field(..., description="Associated video ID")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
