"""
Progressive video processing service.

This module owns Bri's staged video-intelligence execution boundary. It is
intentionally focused on orchestration only: stage sequencing, progress state,
callbacks, duplicate-job protection, and database status updates. Tool behavior
lives in MCP tool implementations, queue behavior lives in ``processing_queue``,
and UI polling goes through the application middle layer.
"""

from __future__ import annotations

import asyncio
import copy
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from storage.database import Database
from utils.logging_config import get_logger

logger = get_logger(__name__)


ProgressCallback = Callable[["ProcessingProgress"], None]


class ProcessingStage(Enum):
    """Ordered stages in Bri's progressive video workflow."""

    PENDING = "pending"
    EXTRACTING = "extracting"
    CAPTIONING = "captioning"
    TRANSCRIBING = "transcribing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass(frozen=True)
class ProcessingProgress:
    """Immutable processing progress snapshot for a single video."""

    video_id: str
    stage: ProcessingStage
    progress_percent: float
    message: str
    stage_start_time: float
    total_start_time: float
    frames_extracted: int = 0
    captions_generated: int = 0
    transcript_segments: int = 0
    objects_detected: int = 0

    def with_updates(self, **updates: Any) -> ProcessingProgress:
        """Return a new progress snapshot with the supplied updates."""

        return replace(self, **updates)


class DuplicateProcessingJobError(RuntimeError):
    """Raised when a second processor attempts to run the same video."""


class ProgressiveProcessor:
    """
    Coordinate staged video processing with race-safe progress tracking.

    The processor intentionally avoids exposing mutable progress objects. All
    stored progress is an immutable dataclass snapshot, and callers receive a
    defensive copy. A per-video async lock prevents duplicate tool execution for
    the same video, while a small threading lock protects synchronous readers
    such as FastAPI status endpoints and Streamlit middle-layer polling.
    """

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()

        self._state_lock = threading.RLock()
        self._job_locks_guard = asyncio.Lock()
        self._job_locks: dict[str, asyncio.Lock] = {}
        self.active_jobs: dict[str, ProcessingProgress] = {}
        self.progress_callbacks: dict[str, ProgressCallback] = {}

        logger.info("Progressive Processor initialized")

    async def process_video_progressive(
        self,
        video_id: str,
        video_path: str,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Process a video through the progressive intelligence stages."""

        job_lock = await self._reserve_video_job(video_id)
        try:
            return await self._run_progressive_job(video_id, video_path, progress_callback)
        finally:
            self._cleanup_video_job(video_id)
            job_lock.release()
            async with self._job_locks_guard:
                if not job_lock.locked():
                    self._job_locks.pop(video_id, None)

    async def _reserve_video_job(self, video_id: str) -> asyncio.Lock:
        """Acquire the per-video lock or reject duplicate processing."""

        async with self._job_locks_guard:
            job_lock = self._job_locks.setdefault(video_id, asyncio.Lock())
            if job_lock.locked():
                raise DuplicateProcessingJobError(f"Video {video_id} is already processing")
            await job_lock.acquire()
            return job_lock

    async def _run_progressive_job(
        self,
        video_id: str,
        video_path: str,
        progress_callback: ProgressCallback | None,
    ) -> dict[str, Any]:
        """Execute the staged workflow after duplicate-job protection is acquired."""

        logger.info("Starting progressive processing for video %s", video_id)
        now = time.time()
        progress = ProcessingProgress(
            video_id=video_id,
            stage=ProcessingStage.EXTRACTING,
            progress_percent=0.0,
            message="Starting video processing...",
            stage_start_time=now,
            total_start_time=now,
        )

        if progress_callback:
            with self._state_lock:
                self.progress_callbacks[video_id] = progress_callback
        self._update_progress(progress)

        try:
            progress = await self._stage_1_extract_frames(video_id, video_path, progress)
            progress = await self._stage_2_generate_captions(video_id, progress)
            progress = await self._stage_3_full_processing(video_id, video_path, progress)

            progress = progress.with_updates(
                stage=ProcessingStage.COMPLETE,
                progress_percent=100.0,
                message="Processing complete!",
            )
            self._update_progress(progress)
            self._update_video_status(video_id, "complete")

            total_time = time.time() - progress.total_start_time
            logger.info(
                "Progressive processing complete for video %s in %.1fs",
                video_id,
                total_time,
            )
            return {
                "status": "complete",
                "video_id": video_id,
                "total_time": total_time,
                "frames": progress.frames_extracted,
                "captions": progress.captions_generated,
                "transcripts": progress.transcript_segments,
                "objects": progress.objects_detected,
            }
        except Exception as exc:
            logger.error("Progressive processing failed for video %s: %s", video_id, exc)
            failed = progress.with_updates(
                stage=ProcessingStage.ERROR,
                message=f"Processing failed: {exc}",
            )
            self._update_progress(failed)
            self._update_video_status(video_id, "error")
            raise

    async def _stage_1_extract_frames(
        self,
        video_id: str,
        video_path: str,
        progress: ProcessingProgress,
    ) -> ProcessingProgress:
        """Extract representative frames so the user can start chatting quickly."""

        logger.info("Stage 1: Extracting frames for video %s", video_id)
        progress = progress.with_updates(
            stage=ProcessingStage.EXTRACTING,
            progress_percent=10.0,
            message="Extracting frames from video...",
            stage_start_time=time.time(),
        )
        self._update_progress(progress)
        self._update_video_status(video_id, "extracting")

        from mcp_server.registry import ToolRegistry

        frame_tool = self._get_registered_tool(ToolRegistry, "extract_frames")
        result = await frame_tool.execute(video_id, {})
        self._store_results(video_id, "extract_frames", result)
        frames_count = len(result.get("frames", []))

        progress = progress.with_updates(
            frames_extracted=frames_count,
            progress_percent=33.0,
            message=f"Extracted {frames_count} frames. Ready to chat.",
        )
        self._update_progress(progress)
        logger.info(
            "Stage 1 complete: %s frames extracted in %.1fs",
            frames_count,
            time.time() - progress.stage_start_time,
        )
        return progress

    async def _stage_2_generate_captions(
        self,
        video_id: str,
        progress: ProcessingProgress,
    ) -> ProcessingProgress:
        """Generate frame captions for content-aware conversations."""

        logger.info("Stage 2: Generating captions for video %s", video_id)
        progress = progress.with_updates(
            stage=ProcessingStage.CAPTIONING,
            progress_percent=40.0,
            message="Analyzing video content...",
            stage_start_time=time.time(),
        )
        self._update_progress(progress)
        self._update_video_status(video_id, "captioning")

        from mcp_server.registry import ToolRegistry

        caption_tool = self._get_registered_tool(ToolRegistry, "caption_frames")
        result = await caption_tool.execute(video_id, {})
        self._store_results(video_id, "caption_frames", result)
        captions_count = len(result.get("captions", []))

        progress = progress.with_updates(
            captions_generated=captions_count,
            progress_percent=66.0,
            message=f"Generated {captions_count} captions. Understanding deepens.",
        )
        self._update_progress(progress)
        logger.info(
            "Stage 2 complete: %s captions generated in %.1fs",
            captions_count,
            time.time() - progress.stage_start_time,
        )
        return progress

    async def _stage_3_full_processing(
        self,
        video_id: str,
        video_path: str,
        progress: ProcessingProgress,
    ) -> ProcessingProgress:
        """Run slower enrichment tools without failing the completed core workflow."""

        logger.info("Stage 3: Full processing for video %s", video_id)
        progress = progress.with_updates(
            stage=ProcessingStage.TRANSCRIBING,
            progress_percent=70.0,
            message="Transcribing audio and detecting objects...",
            stage_start_time=time.time(),
        )
        self._update_progress(progress)
        self._update_video_status(video_id, "transcribing")

        from mcp_server.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register_all_tools()
        tasks = []

        transcript_tool = registry.get_tool("transcribe_audio")
        if transcript_tool:
            tasks.append(self._run_transcription(transcript_tool, video_id))

        object_tool = registry.get_tool("detect_objects")
        if object_tool:
            tasks.append(self._run_object_detection(object_tool, video_id))

        results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
        transcript_segments = progress.transcript_segments
        objects_detected = progress.objects_detected

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Optional stage-3 enrichment failed: %s", result)
                continue
            if result[0] == "transcript_segments":
                transcript_segments = result[1]
            if result[0] == "objects_detected":
                objects_detected = result[1]

        progress = progress.with_updates(
            transcript_segments=transcript_segments,
            objects_detected=objects_detected,
            progress_percent=95.0,
            message="Finalizing video intelligence...",
        )
        self._update_progress(progress)
        logger.info(
            "Stage 3 complete: transcripts=%s, objects=%s in %.1fs",
            progress.transcript_segments,
            progress.objects_detected,
            time.time() - progress.stage_start_time,
        )
        return progress

    @staticmethod
    def _get_registered_tool(registry_class: Any, tool_name: str) -> Any:
        """Create a registry, register production tools, and return one tool."""

        registry = registry_class()
        registry.register_all_tools()
        tool = registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"{tool_name} tool not available")
        return tool

    async def _run_transcription(self, tool: Any, video_id: str) -> tuple[str, int]:
        """Run transcription and return a normalized count tuple."""

        result = await tool.execute(video_id, {})
        self._store_results(video_id, "transcribe_audio", result)
        segments_count = len(result.get("segments", []))
        logger.info("Transcription complete: %s segments", segments_count)
        return "transcript_segments", segments_count

    async def _run_object_detection(self, tool: Any, video_id: str) -> tuple[str, int]:
        """Run object detection and return a normalized count tuple."""

        result = await tool.execute(video_id, {})
        self._store_results(video_id, "detect_objects", result)
        detections_count = len(result.get("detections", []))
        logger.info("Object detection complete: %s detections", detections_count)
        return "objects_detected", detections_count

    def _store_results(self, video_id: str, tool_name: str, result: dict[str, Any]) -> None:
        """Persist tool outputs to the video processing service.

        Failures here are logged but never raised: the pipeline's primary job
        is to keep the user-visible progress stream alive, so a DB write glitch
        must not abort the rest of the run.
        """

        try:
            from services.video_processing_service import get_video_processing_service

            service = get_video_processing_service()
            counts = service.store_tool_results(video_id, tool_name, result)

            for data_type, count in counts.items():
                logger.info(
                    "Stored %s %s for video %s",
                    count,
                    data_type,
                    video_id,
                )
        except Exception as exc:
            logger.error("Failed to store %s results: %s", tool_name, exc)

    def _update_progress(self, progress: ProcessingProgress) -> None:
        """Store progress atomically and notify the callback with a snapshot."""

        callback: ProgressCallback | None
        with self._state_lock:
            self.active_jobs[progress.video_id] = progress
            callback = self.progress_callbacks.get(progress.video_id)

        if callback:
            try:
                callback(copy.copy(progress))
            except Exception as exc:
                logger.error("Progress callback failed: %s", exc)

        logger.info(
            "Video %s: %s - %.0f%% - %s",
            progress.video_id,
            progress.stage.value,
            progress.progress_percent,
            progress.message,
        )

    def _update_video_status(self, video_id: str, status: str) -> None:
        """Update video processing status through the configured database."""

        try:
            self.db.execute_update(
                """
                UPDATE videos
                SET processing_status = ?
                WHERE video_id = ?
                """,
                (status, video_id),
            )
            logger.debug("Updated video %s status to: %s", video_id, status)
        except Exception as exc:
            logger.error("Failed to update video status: %s", exc)

    def _cleanup_video_job(self, video_id: str) -> None:
        """Remove in-memory state for a completed or failed job."""

        with self._state_lock:
            self.active_jobs.pop(video_id, None)
            self.progress_callbacks.pop(video_id, None)

    def get_progress(self, video_id: str) -> ProcessingProgress | None:
        """Return a defensive snapshot of current video progress."""

        with self._state_lock:
            progress = self.active_jobs.get(video_id)
            return copy.copy(progress) if progress else None

    def is_processing(self, video_id: str) -> bool:
        """Return whether a video currently has active processing state."""

        with self._state_lock:
            return video_id in self.active_jobs


_processor_instance: ProgressiveProcessor | None = None
_processor_instance_lock = threading.Lock()


def get_progressive_processor() -> ProgressiveProcessor:
    """Get or create the process-local progressive processor singleton."""

    global _processor_instance
    with _processor_instance_lock:
        if _processor_instance is None:
            _processor_instance = ProgressiveProcessor()
        return _processor_instance
