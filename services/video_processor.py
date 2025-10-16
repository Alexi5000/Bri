"""
Video Processing Workflow Manager for BRI
Handles batch video processing with MCP server integration
"""

import logging
import requests
import time
from typing import Dict, Any, Optional, Callable
from config import Config
from storage.database import update_video_status

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Custom exception for video processing errors."""
    pass


class VideoProcessor:
    """
    Manages video processing workflow with MCP server.
    
    Handles:
    - Triggering batch processing on MCP server
    - Tracking processing progress
    - Updating database status
    - Providing friendly status messages
    """
    
    def __init__(self, mcp_server_url: Optional[str] = None):
        """
        Initialize video processor.
        
        Args:
            mcp_server_url: MCP server URL. Uses Config if not provided.
        """
        self.mcp_server_url = mcp_server_url or Config.get_mcp_server_url()
        self.processing_steps = [
            "extract_frames",
            "caption_frames",
            "transcribe_audio",
            "detect_objects"
        ]
        
    def get_friendly_step_name(self, step: str) -> str:
        """
        Convert technical step name to friendly display name.
        
        Args:
            step: Technical step name
            
        Returns:
            Friendly step name with emoji
        """
        step_names = {
            "extract_frames": "🎞️ Extracting key frames",
            "caption_frames": "🖼️ Describing scenes",
            "transcribe_audio": "🎤 Transcribing audio",
            "detect_objects": "🔍 Detecting objects"
        }
        return step_names.get(step, f"Processing {step}")
    
    def get_processing_message(self, step: str, progress: float) -> str:
        """
        Generate friendly processing message for current step.
        
        Args:
            step: Current processing step
            progress: Progress percentage (0-100)
            
        Returns:
            Friendly status message
        """
        messages = {
            "extract_frames": [
                "Taking snapshots of your video... 📸",
                "Capturing the best moments... ✨",
                "Almost done with frame extraction! 🎬"
            ],
            "caption_frames": [
                "Looking at what's happening in each scene... 👀",
                "Understanding the visual content... 🖼️",
                "Nearly finished describing everything! 💭"
            ],
            "transcribe_audio": [
                "Listening to the audio... 🎧",
                "Writing down what I hear... ✍️",
                "Almost done with transcription! 🎤"
            ],
            "detect_objects": [
                "Spotting interesting things in your video... 🔍",
                "Identifying objects and people... 👥",
                "Finishing up object detection! ✅"
            ]
        }
        
        step_messages = messages.get(step, ["Processing..."])
        
        # Select message based on progress
        if progress < 33:
            return step_messages[0]
        elif progress < 66:
            return step_messages[1] if len(step_messages) > 1 else step_messages[0]
        else:
            return step_messages[-1]
    
    async def process_video(
        self,
        video_id: str,
        progress_callback: Optional[Callable[[str, float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process video with all available tools.
        
        Args:
            video_id: Video identifier
            progress_callback: Optional callback for progress updates
                              Signature: callback(step_name, progress, message)
        
        Returns:
            Processing results dictionary
            
        Raises:
            VideoProcessingError: If processing fails
        """
        try:
            # Update status to processing
            update_video_status(video_id, "processing")
            logger.info(f"Starting video processing for {video_id}")
            
            # Trigger batch processing on MCP server
            url = f"{self.mcp_server_url}/videos/{video_id}/process"
            
            # Report initial status
            if progress_callback:
                progress_callback(
                    "Starting",
                    0,
                    "🚀 Getting ready to analyze your video..."
                )
            
            # Make request to MCP server
            response = requests.post(
                url,
                json={"tools": self.processing_steps},
                timeout=300  # 5 minute timeout for processing
            )
            
            if response.status_code != 200:
                raise VideoProcessingError(
                    f"MCP server returned status {response.status_code}: {response.text}"
                )
            
            result = response.json()
            
            # Simulate progress updates for each step
            # In a real implementation, this would poll the server for progress
            total_steps = len(self.processing_steps)
            for i, step in enumerate(self.processing_steps):
                progress = ((i + 1) / total_steps) * 100
                
                if progress_callback:
                    friendly_name = self.get_friendly_step_name(step)
                    message = self.get_processing_message(step, progress)
                    progress_callback(friendly_name, progress, message)
                
                # Small delay to show progress (remove in production with real polling)
                time.sleep(0.5)
            
            # Check if processing was successful
            if result.get("status") == "complete":
                update_video_status(video_id, "complete")
                logger.info(f"Video processing completed successfully for {video_id}")
                
                # Index for semantic search (if available)
                try:
                    from services.embedding_pipeline import get_embedding_pipeline
                    pipeline = get_embedding_pipeline()
                    if pipeline.is_enabled():
                        logger.info(f"Indexing video {video_id} for semantic search")
                        
                        # Fetch caption and transcript data
                        from services.context import ContextBuilder
                        context_builder = ContextBuilder()
                        
                        captions = context_builder._get_captions(video_id)
                        transcript = context_builder._get_transcript(video_id)
                        
                        caption_dicts = [
                            {
                                'text': cap.text,
                                'frame_timestamp': cap.frame_timestamp,
                                'confidence': cap.confidence
                            }
                            for cap in captions
                        ] if captions else []
                        
                        segment_dicts = [
                            {
                                'text': seg.text,
                                'start': seg.start,
                                'end': seg.end,
                                'confidence': seg.confidence if hasattr(seg, 'confidence') else 1.0
                            }
                            for seg in transcript.segments
                        ] if transcript and transcript.segments else []
                        
                        pipeline.process_video(video_id, caption_dicts, segment_dicts)
                        logger.info(f"Semantic search indexing complete for {video_id}")
                except Exception as e:
                    logger.warning(f"Failed to index video for semantic search: {e}")
                    # Don't fail the whole process if semantic indexing fails
                
                if progress_callback:
                    progress_callback(
                        "Complete",
                        100,
                        "✨ All set! I'm ready to answer your questions!"
                    )
                
                return result
            
            elif result.get("status") == "partial":
                # Some tools succeeded, some failed
                update_video_status(video_id, "complete")
                logger.warning(
                    f"Video processing partially completed for {video_id}: "
                    f"{result.get('errors')}"
                )
                
                if progress_callback:
                    progress_callback(
                        "Complete",
                        100,
                        "✅ Done! Some features may be limited, but I'm ready to help!"
                    )
                
                return result
            
            else:
                # Processing failed
                update_video_status(video_id, "error")
                raise VideoProcessingError(
                    f"Processing failed with status: {result.get('status')}"
                )
        
        except requests.exceptions.Timeout:
            update_video_status(video_id, "error")
            logger.error(f"Video processing timed out for {video_id}")
            raise VideoProcessingError(
                "Processing took too long. Please try with a shorter video."
            )
        
        except requests.exceptions.ConnectionError:
            update_video_status(video_id, "error")
            logger.error(f"Could not connect to MCP server for {video_id}")
            raise VideoProcessingError(
                "Could not connect to processing server. Please ensure it's running."
            )
        
        except Exception as e:
            update_video_status(video_id, "error")
            logger.error(f"Video processing failed for {video_id}: {e}")
            raise VideoProcessingError(f"Processing failed: {str(e)}")
    
    def get_processing_status(self, video_id: str) -> Dict[str, Any]:
        """
        Get current processing status for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Status dictionary with current state
        """
        from storage.database import get_video
        
        video = get_video(video_id)
        if not video:
            return {
                "status": "not_found",
                "message": "Video not found"
            }
        
        status = video["processing_status"]
        
        status_messages = {
            "pending": "⏳ Waiting to start processing...",
            "processing": "🔄 Processing your video...",
            "complete": "✅ Ready to chat!",
            "error": "❌ Processing encountered an issue"
        }
        
        return {
            "status": status,
            "message": status_messages.get(status, "Unknown status"),
            "video_id": video_id
        }
    
    def check_mcp_server_health(self) -> bool:
        """
        Check if MCP server is available.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.mcp_server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"MCP server health check failed: {e}")
            return False


def get_video_processor() -> VideoProcessor:
    """
    Get or create global video processor instance.
    
    Returns:
        VideoProcessor instance
    """
    return VideoProcessor()
