"""
Progressive Video Processing Service
Implements staged processing workflow for faster user interaction
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from utils.logging_config import get_logger
from storage.database import Database

logger = get_logger(__name__)


class ProcessingStage(Enum):
    """Video processing stages."""
    PENDING = 'pending'
    EXTRACTING = 'extracting'  # Stage 1: Extract frames only (10s)
    CAPTIONING = 'captioning'  # Stage 2: Generate captions (60s)
    TRANSCRIBING = 'transcribing'  # Stage 3: Full transcription + objects (120s)
    COMPLETE = 'complete'
    ERROR = 'error'


@dataclass
class ProcessingProgress:
    """Processing progress information."""
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


class ProgressiveProcessor:
    """
    Manages progressive video processing with staged workflow.
    
    Stages:
    1. EXTRACTING (Fast - 10s): Extract frames only → User can start chatting
    2. CAPTIONING (Medium - 60s): Generate captions for key frames
    3. TRANSCRIBING (Slow - 120s): Full transcription + object detection
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize Progressive Processor.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        
        # Track active processing jobs
        self.active_jobs: Dict[str, ProcessingProgress] = {}
        
        # Progress callbacks
        self.progress_callbacks: Dict[str, Callable] = {}
        
        logger.info("Progressive Processor initialized")
    
    async def process_video_progressive(
        self,
        video_id: str,
        video_path: str,
        progress_callback: Optional[Callable[[ProcessingProgress], None]] = None
    ) -> Dict[str, Any]:
        """
        Process video progressively through 3 stages.
        
        Args:
            video_id: Video identifier
            video_path: Path to video file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Final processing results
        """
        logger.info(f"Starting progressive processing for video {video_id}")
        
        # Initialize progress tracking
        progress = ProcessingProgress(
            video_id=video_id,
            stage=ProcessingStage.EXTRACTING,
            progress_percent=0.0,
            message="Starting video processing...",
            stage_start_time=time.time(),
            total_start_time=time.time()
        )
        
        self.active_jobs[video_id] = progress
        if progress_callback:
            self.progress_callbacks[video_id] = progress_callback
        
        try:
            # Stage 1: Extract frames (Fast - 10s)
            await self._stage_1_extract_frames(video_id, video_path, progress)
            
            # Stage 2: Generate captions (Medium - 60s)
            await self._stage_2_generate_captions(video_id, progress)
            
            # Stage 3: Transcription + Objects (Slow - 120s)
            await self._stage_3_full_processing(video_id, video_path, progress)
            
            # Mark as complete
            progress.stage = ProcessingStage.COMPLETE
            progress.progress_percent = 100.0
            progress.message = "Processing complete! 🎉"
            self._update_progress(progress)
            
            # Update database status
            self._update_video_status(video_id, 'complete')
            
            total_time = time.time() - progress.total_start_time
            logger.info(
                f"Progressive processing complete for video {video_id} "
                f"in {total_time:.1f}s"
            )
            
            return {
                'status': 'complete',
                'video_id': video_id,
                'total_time': total_time,
                'frames': progress.frames_extracted,
                'captions': progress.captions_generated,
                'transcripts': progress.transcript_segments,
                'objects': progress.objects_detected
            }
            
        except Exception as e:
            logger.error(f"Progressive processing failed for video {video_id}: {e}")
            progress.stage = ProcessingStage.ERROR
            progress.message = f"Processing failed: {str(e)}"
            self._update_progress(progress)
            self._update_video_status(video_id, 'error')
            raise
        
        finally:
            # Cleanup
            if video_id in self.active_jobs:
                del self.active_jobs[video_id]
            if video_id in self.progress_callbacks:
                del self.progress_callbacks[video_id]
    
    async def _stage_1_extract_frames(
        self,
        video_id: str,
        video_path: str,
        progress: ProcessingProgress
    ) -> None:
        """
        Stage 1: Extract frames only (Fast - target 10s).
        
        After this stage, user can start chatting with frame-based responses.
        """
        logger.info(f"Stage 1: Extracting frames for video {video_id}")
        
        progress.stage = ProcessingStage.EXTRACTING
        progress.progress_percent = 10.0
        progress.message = "Extracting frames from video... 🎬"
        progress.stage_start_time = time.time()
        self._update_progress(progress)
        self._update_video_status(video_id, 'extracting')
        
        try:
            # Import here to avoid circular dependencies
            from mcp_server.registry import ToolRegistry
            
            registry = ToolRegistry()
            registry.register_all_tools()
            
            # Get frame extractor tool
            frame_tool = registry.get_tool('extract_frames')
            if not frame_tool:
                raise ValueError("Frame extraction tool not available")
            
            # Execute frame extraction
            result = await frame_tool.execute(video_id, {})
            
            # Update progress
            frames_count = len(result.get('frames', []))
            progress.frames_extracted = frames_count
            progress.progress_percent = 33.0
            progress.message = f"Extracted {frames_count} frames! Ready to chat! 💬"
            self._update_progress(progress)
            
            stage_time = time.time() - progress.stage_start_time
            logger.info(
                f"Stage 1 complete: {frames_count} frames extracted "
                f"in {stage_time:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Stage 1 failed: {e}")
            raise
    
    async def _stage_2_generate_captions(
        self,
        video_id: str,
        progress: ProcessingProgress
    ) -> None:
        """
        Stage 2: Generate captions for key frames (Medium - target 60s).
        
        After this stage, agent can provide richer, content-aware responses.
        """
        logger.info(f"Stage 2: Generating captions for video {video_id}")
        
        progress.stage = ProcessingStage.CAPTIONING
        progress.progress_percent = 40.0
        progress.message = "Analyzing video content... 🔍"
        progress.stage_start_time = time.time()
        self._update_progress(progress)
        self._update_video_status(video_id, 'captioning')
        
        try:
            from mcp_server.registry import ToolRegistry
            
            registry = ToolRegistry()
            registry.register_all_tools()
            
            # Get caption tool
            caption_tool = registry.get_tool('caption_frames')
            if not caption_tool:
                raise ValueError("Caption tool not available")
            
            # Execute captioning
            result = await caption_tool.execute(video_id, {})
            
            # Update progress
            captions_count = len(result.get('captions', []))
            progress.captions_generated = captions_count
            progress.progress_percent = 66.0
            progress.message = f"Generated {captions_count} captions! Understanding deepens! 🧠"
            self._update_progress(progress)
            
            stage_time = time.time() - progress.stage_start_time
            logger.info(
                f"Stage 2 complete: {captions_count} captions generated "
                f"in {stage_time:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Stage 2 failed: {e}")
            raise
    
    async def _stage_3_full_processing(
        self,
        video_id: str,
        video_path: str,
        progress: ProcessingProgress
    ) -> None:
        """
        Stage 3: Full transcription + object detection (Slow - target 120s).
        
        After this stage, agent has complete intelligence with all data.
        """
        logger.info(f"Stage 3: Full processing for video {video_id}")
        
        progress.stage = ProcessingStage.TRANSCRIBING
        progress.progress_percent = 70.0
        progress.message = "Transcribing audio and detecting objects... 🎤🔍"
        progress.stage_start_time = time.time()
        self._update_progress(progress)
        self._update_video_status(video_id, 'transcribing')
        
        try:
            from mcp_server.registry import ToolRegistry
            
            registry = ToolRegistry()
            registry.register_all_tools()
            
            # Get tools
            transcript_tool = registry.get_tool('transcribe_audio')
            object_tool = registry.get_tool('detect_objects')
            
            # Run transcription and object detection in parallel
            tasks = []
            
            if transcript_tool:
                tasks.append(self._run_transcription(transcript_tool, video_id, progress))
            
            if object_tool:
                tasks.append(self._run_object_detection(object_tool, video_id, progress))
            
            # Wait for both to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            progress.progress_percent = 95.0
            progress.message = "Finalizing... Almost there! ✨"
            self._update_progress(progress)
            
            stage_time = time.time() - progress.stage_start_time
            logger.info(
                f"Stage 3 complete: transcripts={progress.transcript_segments}, "
                f"objects={progress.objects_detected} in {stage_time:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Stage 3 failed: {e}")
            # Don't raise - partial completion is acceptable
            logger.warning("Continuing despite Stage 3 errors")
    
    async def _run_transcription(self, tool, video_id: str, progress: ProcessingProgress):
        """Run transcription and update progress."""
        try:
            result = await tool.execute(video_id, {})
            segments_count = len(result.get('segments', []))
            progress.transcript_segments = segments_count
            logger.info(f"Transcription complete: {segments_count} segments")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
    
    async def _run_object_detection(self, tool, video_id: str, progress: ProcessingProgress):
        """Run object detection and update progress."""
        try:
            result = await tool.execute(video_id, {})
            detections_count = len(result.get('detections', []))
            progress.objects_detected = detections_count
            logger.info(f"Object detection complete: {detections_count} detections")
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
    
    def _update_progress(self, progress: ProcessingProgress) -> None:
        """
        Update progress and notify callback.
        
        Args:
            progress: Current progress state
        """
        # Store in active jobs
        self.active_jobs[progress.video_id] = progress
        
        # Call progress callback if registered
        callback = self.progress_callbacks.get(progress.video_id)
        if callback:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
        
        # Log progress
        logger.info(
            f"Video {progress.video_id}: {progress.stage.value} - "
            f"{progress.progress_percent:.0f}% - {progress.message}"
        )
    
    def _update_video_status(self, video_id: str, status: str) -> None:
        """
        Update video processing status in database.
        
        Args:
            video_id: Video identifier
            status: New status
        """
        try:
            query = """
                UPDATE videos
                SET processing_status = ?
                WHERE video_id = ?
            """
            self.db.execute_update(query, (status, video_id))
            logger.debug(f"Updated video {video_id} status to: {status}")
        except Exception as e:
            logger.error(f"Failed to update video status: {e}")
    
    def get_progress(self, video_id: str) -> Optional[ProcessingProgress]:
        """
        Get current processing progress for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            ProcessingProgress or None if not processing
        """
        return self.active_jobs.get(video_id)
    
    def is_processing(self, video_id: str) -> bool:
        """
        Check if a video is currently being processed.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if processing, False otherwise
        """
        return video_id in self.active_jobs


# Global processor instance
_processor_instance: Optional[ProgressiveProcessor] = None


def get_progressive_processor() -> ProgressiveProcessor:
    """
    Get or create global progressive processor instance.
    
    Returns:
        ProgressiveProcessor instance
    """
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = ProgressiveProcessor()
    return _processor_instance
