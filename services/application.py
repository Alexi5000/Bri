"""Production application-service layer for Bri.

The Streamlit interface should present product workflows, not directly coordinate
SQLite rows, filesystem lifecycle, MCP HTTP calls, and agent execution. This
module provides a typed middle layer for those concerns so Bri behaves like a
full-stack product while retaining the Streamlit + FastAPI + SQLite architecture.
"""

from __future__ import annotations

import asyncio
import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

from services.mcp_client import (
    MCPClient,
    MCPHealth,
    MCPToolSummary,
    ProcessingStartResult,
    VideoProgress,
)
from storage import database
from storage.file_store import get_file_store
from storage.maintenance import (
    DatabaseBackupResult,
    DatabaseIntegrityReport,
    configure_sqlite_for_production,
    create_sqlite_backup,
    run_integrity_check,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class VideoSummary:
    """Presentation-ready view of a persisted video."""

    video_id: str
    filename: str
    file_path: str
    duration: float = 0.0
    processing_status: str = "unknown"
    thumbnail_path: str | None = None
    upload_timestamp: str | None = None

    @property
    def duration_label(self) -> str:
        if not self.duration or self.duration <= 0 or math.isnan(float(self.duration)):
            return "Pending analysis"
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def status_label(self) -> str:
        labels = {
            "pending": "Queued",
            "processing": "Processing",
            "complete": "Ready",
            "completed": "Ready",
            "error": "Needs attention",
        }
        return labels.get(self.processing_status, self.processing_status.title())


@dataclass(frozen=True)
class DashboardSnapshot:
    """Aggregated operational and product metrics for the Streamlit shell."""

    videos: list[VideoSummary]
    total_videos: int
    ready_videos: int
    processing_videos: int
    pending_videos: int
    error_videos: int
    conversations: int
    mcp_health: MCPHealth
    tools: list[MCPToolSummary] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds") + "Z"
    )


@dataclass(frozen=True)
class UploadResult:
    """Result of the production upload workflow."""

    ok: bool
    video: VideoSummary | None = None
    message: str = ""
    processing: ProcessingStartResult | None = None


@dataclass(frozen=True)
class ChatResult:
    """Result returned after a conversational exchange with Bri."""

    ok: bool
    message: str
    response: Any | None = None
    elapsed_ms: int = 0


@dataclass(frozen=True)
class ConversationMessage:
    """Presentation-ready conversation message for Streamlit chat surfaces."""

    role: str
    content: str
    timestamp: Any


@dataclass(frozen=True)
class PersistenceReadiness:
    """Middle-layer view of Bri's SQLite durability posture."""

    configured: bool
    integrity: DatabaseIntegrityReport
    production_settings: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.configured and self.integrity.ok


class BriApplicationService:
    """Facade for the Streamlit frontend and production workflow orchestration."""

    def __init__(self, mcp_client: MCPClient | None = None) -> None:
        self.mcp_client = mcp_client or MCPClient()
        self.file_store = get_file_store()

    def snapshot(self, *, include_tools: bool = True) -> DashboardSnapshot:
        """Return the current full-stack dashboard state."""

        videos = self.list_videos()
        conversations = self._count_conversations()
        mcp_health = self.mcp_client.health()
        tools: list[MCPToolSummary] = []
        if include_tools and mcp_health.online:
            try:
                tools = self.mcp_client.list_tools()
            except Exception as exc:
                logger.warning("Unable to load MCP tool catalog for dashboard: %s", exc)

        statuses = [video.processing_status for video in videos]
        return DashboardSnapshot(
            videos=videos,
            total_videos=len(videos),
            ready_videos=sum(status in {"complete", "completed"} for status in statuses),
            processing_videos=statuses.count("processing"),
            pending_videos=statuses.count("pending"),
            error_videos=statuses.count("error"),
            conversations=conversations,
            mcp_health=mcp_health,
            tools=tools,
        )

    def list_videos(self) -> list[VideoSummary]:
        """Return all uploaded videos as typed summaries."""

        rows = database.get_all_videos()
        return [self._row_to_video_summary(row) for row in rows]

    def get_video(self, video_id: str) -> VideoSummary | None:
        """Return a single video by id."""

        row = database.get_video(video_id)
        return self._row_to_video_summary(row) if row else None

    def upload_video(
        self, uploaded_file: BinaryIO | Any, *, start_processing: bool = True
    ) -> UploadResult:
        """Persist an uploaded video and optionally start MCP progressive processing."""

        if uploaded_file is None:
            return UploadResult(ok=False, message="No video file was provided.")

        filename = Path(str(getattr(uploaded_file, "name", "uploaded_video"))).name
        video_id = str(uuid.uuid4())
        try:
            file_size = int(getattr(uploaded_file, "size", 0) or 0)
            is_valid, validation_error = self.file_store.validate_video_file(filename, file_size)
            if not is_valid:
                return UploadResult(
                    ok=False, message=str(validation_error or "Unsupported video upload.")
                )
            saved_video_id, saved_path = self.file_store.save_uploaded_video(
                uploaded_file, filename, video_id
            )
            video_id = saved_video_id
            duration = self._safe_video_duration(saved_path)
            database.insert_video(
                video_id=video_id,
                filename=filename,
                file_path=saved_path,
                duration=duration,
            )
            video = self.get_video(video_id)
            processing_result: ProcessingStartResult | None = None
            if start_processing:
                try:
                    processing_result = self.mcp_client.start_progressive_processing(
                        video_id, saved_path
                    )
                    database.update_video_status(video_id, "processing")
                    video = self.get_video(video_id)
                except Exception as exc:
                    logger.warning("Video saved but MCP processing did not start: %s", exc)
                    return UploadResult(
                        ok=True,
                        video=video,
                        message="Video uploaded. MCP processing is offline, so the video is queued for later processing.",
                    )
            return UploadResult(
                ok=True,
                video=video,
                message="Video uploaded and processing workflow started."
                if processing_result
                else "Video uploaded.",
                processing=processing_result,
            )
        except Exception as exc:
            try:
                self.file_store.delete_video(video_id)
            except Exception:
                logger.debug("Unable to clean up failed upload %s", video_id, exc_info=True)
            logger.error("Video upload workflow failed: %s", exc, exc_info=True)
            return UploadResult(ok=False, message=f"Upload failed: {exc}")

    def start_processing(self, video_id: str) -> ProcessingStartResult:
        """Start or restart progressive processing for an existing video."""

        video = self.get_video(video_id)
        if not video:
            raise ValueError(f"Video not found: {video_id}")
        result = self.mcp_client.start_progressive_processing(video.video_id, video.file_path)
        database.update_video_status(video.video_id, "processing")
        return result

    def delete_video(self, video_id: str) -> bool:
        """Delete a video and its local persisted assets as one product operation."""

        if not self.get_video(video_id):
            raise ValueError(f"Video not found: {video_id}")
        file_deleted = self.file_store.delete_video(video_id)
        database.delete_video(video_id)
        return bool(file_deleted)

    def get_conversation_history(
        self, video_id: str, *, limit: int = 20
    ) -> list[ConversationMessage]:
        """Return chat history through the middle-layer boundary."""

        from services.memory import Memory

        messages = Memory().get_conversation_history(video_id, limit=limit)
        return [
            ConversationMessage(
                role=str(getattr(message, "role", "assistant")),
                content=str(getattr(message, "content", "")),
                timestamp=getattr(message, "timestamp", None),
            )
            for message in messages
        ]

    def get_processing_progress(self, video_id: str) -> VideoProgress:
        """Return current staged video processing progress through the MCP boundary."""

        if not self.get_video(video_id):
            raise ValueError(f"Video not found: {video_id}")
        return self.mcp_client.video_progress(video_id)

    def persistence_readiness(self) -> PersistenceReadiness:
        """Return SQLite durability and integrity readiness through the middle layer."""

        settings = configure_sqlite_for_production()
        integrity = run_integrity_check()
        return PersistenceReadiness(
            configured=True, integrity=integrity, production_settings=settings
        )

    def create_database_backup(self) -> DatabaseBackupResult:
        """Create an online SQLite backup through the middle-layer boundary."""

        return create_sqlite_backup()

    def send_message(
        self, video_id: str, message: str, *, timeout_seconds: float = 60.0
    ) -> ChatResult:
        """Run a conversational exchange through Bri's agent layer."""

        from services.agent import GroqAgent
        from services.error_handler import ErrorHandler

        clean_message = (message or "").strip()
        if not clean_message:
            return ChatResult(ok=False, message="Please enter a message.")
        if len(clean_message) > 5000:
            return ChatResult(
                ok=False, message="Message too long. Please keep it under 5,000 characters."
            )
        if not self.get_video(video_id):
            return ChatResult(ok=False, message="Select a valid video before chatting.")

        started = time.perf_counter()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            agent = GroqAgent()
            response = loop.run_until_complete(
                asyncio.wait_for(agent.chat(clean_message, video_id), timeout=timeout_seconds)
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            if response and hasattr(response, "message"):
                return ChatResult(
                    ok=True, message=str(response.message), response=response, elapsed_ms=elapsed_ms
                )
            return ChatResult(
                ok=False, message="Bri returned an invalid response. Please try again."
            )
        except asyncio.TimeoutError:
            return ChatResult(ok=False, message="Request timed out. Please try a simpler question.")
        except Exception as exc:
            logger.error("Conversation workflow failed: %s", exc, exc_info=True)
            return ChatResult(
                ok=False, message=ErrorHandler.format_error_for_user(exc, {"query": clean_message})
            )
        finally:
            loop.close()

    def _row_to_video_summary(self, row: Any) -> VideoSummary:
        data = dict(row) if not isinstance(row, dict) else row
        return VideoSummary(
            video_id=str(data.get("video_id", "")),
            filename=str(data.get("filename", "Untitled video")),
            file_path=str(data.get("file_path", "")),
            duration=float(data.get("duration") or 0.0),
            processing_status=str(data.get("processing_status") or "unknown"),
            thumbnail_path=data.get("thumbnail_path"),
            upload_timestamp=str(data.get("upload_timestamp"))
            if data.get("upload_timestamp") is not None
            else None,
        )

    def _count_conversations(self) -> int:
        try:
            db = database.get_database()
            rows = db.execute_query("SELECT COUNT(*) AS count FROM memory")
            return int(rows[0]["count"]) if rows else 0
        except Exception:
            return 0

    def _safe_video_duration(self, video_path: str) -> float:
        try:
            import cv2  # type: ignore

            capture = cv2.VideoCapture(video_path)
            if not capture.isOpened():
                return 0.0
            fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
            frames = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
            capture.release()
            if fps <= 0:
                return 0.0
            return float(frames / fps)
        except Exception as exc:
            logger.debug("Unable to determine duration for %s: %s", video_path, exc)
            return 0.0


def get_application_service() -> BriApplicationService:
    """Return a new lightweight application-service facade."""

    return BriApplicationService()


__all__ = [
    "BriApplicationService",
    "DashboardSnapshot",
    "VideoSummary",
    "UploadResult",
    "ChatResult",
    "PersistenceReadiness",
    "ConversationMessage",
    "get_application_service",
]
