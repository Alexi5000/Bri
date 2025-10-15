"""Tool registry for dynamic tool discovery and management."""

import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from tools.frame_extractor import FrameExtractor
from tools.image_captioner import ImageCaptioner
from tools.audio_transcriber import AudioTranscriber
from tools.object_detector import ObjectDetector
from storage.database import get_database
from config import Config

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Abstract base class for MCP tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON Schema for tool parameters."""
        pass
    
    @abstractmethod
    async def execute(self, video_id: str, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters."""
        pass


class FrameExtractionTool(Tool):
    """Tool for extracting frames from videos."""
    
    def __init__(self):
        self.extractor = FrameExtractor()
    
    @property
    def name(self) -> str:
        return "extract_frames"
    
    @property
    def description(self) -> str:
        return "Extract frames from video at regular intervals or specific timestamps"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "interval_seconds": {
                    "type": "number",
                    "description": "Interval between frames in seconds",
                    "default": Config.FRAME_EXTRACTION_INTERVAL
                },
                "max_frames": {
                    "type": "integer",
                    "description": "Maximum number of frames to extract",
                    "default": Config.MAX_FRAMES_PER_VIDEO
                },
                "timestamp": {
                    "type": "number",
                    "description": "Extract single frame at specific timestamp (optional)"
                }
            }
        }
    
    async def execute(self, video_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract frames from video."""
        try:
            # Get video path from database
            video_path = self._get_video_path(video_id)
            
            # Check if extracting single frame or multiple
            if "timestamp" in parameters and parameters["timestamp"] is not None:
                # Extract single frame at timestamp
                frame = self.extractor.extract_frame_at_timestamp(
                    video_path,
                    video_id,
                    parameters["timestamp"]
                )
                return {
                    "frames": [frame.dict()],
                    "count": 1
                }
            else:
                # Extract multiple frames
                interval = parameters.get("interval_seconds", Config.FRAME_EXTRACTION_INTERVAL)
                max_frames = parameters.get("max_frames", Config.MAX_FRAMES_PER_VIDEO)
                
                frames = self.extractor.extract_frames(
                    video_path,
                    video_id,
                    interval_seconds=interval,
                    max_frames=max_frames
                )
                
                return {
                    "frames": [frame.dict() for frame in frames],
                    "count": len(frames)
                }
        except Exception as e:
            logger.error(f"Frame extraction failed: {str(e)}")
            raise
    
    def _get_video_path(self, video_id: str) -> str:
        """Get video file path from database."""
        db = get_database()
        result = db.execute_query(
            "SELECT file_path FROM videos WHERE video_id = ?",
            (video_id,)
        )
        if not result:
            raise ValueError(f"Video not found: {video_id}")
        return result[0]["file_path"]


class ImageCaptioningTool(Tool):
    """Tool for generating captions for video frames."""
    
    def __init__(self):
        self.captioner = ImageCaptioner()
    
    @property
    def name(self) -> str:
        return "caption_frames"
    
    @property
    def description(self) -> str:
        return "Generate natural language captions for video frames using BLIP"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "frame_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of frame image paths to caption"
                },
                "timestamps": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of timestamps corresponding to frames"
                }
            },
            "required": ["frame_paths", "timestamps"]
        }
    
    async def execute(self, video_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate captions for frames."""
        try:
            # If no frame paths provided, get all frames for video
            if "frame_paths" not in parameters or not parameters["frame_paths"]:
                frames = self._get_video_frames(video_id)
                frame_paths = [f["image_path"] for f in frames]
                timestamps = [f["timestamp"] for f in frames]
            else:
                frame_paths = parameters["frame_paths"]
                timestamps = parameters["timestamps"]
            
            # Generate captions
            captions = self.captioner.caption_frames_batch(frame_paths, timestamps)
            
            return {
                "captions": [caption.dict() for caption in captions],
                "count": len(captions)
            }
        except Exception as e:
            logger.error(f"Image captioning failed: {str(e)}")
            raise
    
    def _get_video_frames(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all frames for a video from database."""
        db = get_database()
        results = db.execute_query(
            """SELECT data FROM video_context 
               WHERE video_id = ? AND context_type = 'frame'
               ORDER BY timestamp""",
            (video_id,)
        )
        
        if not results:
            # Try to extract frames first
            logger.info(f"No frames found for video {video_id}, extracting...")
            extractor_tool = FrameExtractionTool()
            import asyncio
            result = asyncio.run(extractor_tool.execute(video_id, {}))
            return result["frames"]
        
        import json
        return [json.loads(row["data"]) for row in results]


class AudioTranscriptionTool(Tool):
    """Tool for transcribing audio from videos."""
    
    def __init__(self):
        self.transcriber = AudioTranscriber()
    
    @property
    def name(self) -> str:
        return "transcribe_audio"
    
    @property
    def description(self) -> str:
        return "Transcribe audio from video using Whisper with timestamps"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "Language code (e.g., 'en', 'es'). Auto-detected if not provided"
                },
                "start_time": {
                    "type": "number",
                    "description": "Start time for segment transcription (optional)"
                },
                "end_time": {
                    "type": "number",
                    "description": "End time for segment transcription (optional)"
                }
            }
        }
    
    async def execute(self, video_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe video audio."""
        try:
            # Get video path from database
            video_path = self._get_video_path(video_id)
            language = parameters.get("language")
            
            # Check if transcribing segment or full video
            if "start_time" in parameters and "end_time" in parameters:
                # Transcribe segment
                segment = self.transcriber.transcribe_segment(
                    video_path,
                    parameters["start_time"],
                    parameters["end_time"],
                    language
                )
                return {
                    "segment": segment.dict(),
                    "type": "segment"
                }
            else:
                # Transcribe full video
                transcript = self.transcriber.transcribe_video(video_path, language)
                return {
                    "transcript": transcript.dict(),
                    "type": "full"
                }
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            raise
    
    def _get_video_path(self, video_id: str) -> str:
        """Get video file path from database."""
        db = get_database()
        result = db.execute_query(
            "SELECT file_path FROM videos WHERE video_id = ?",
            (video_id,)
        )
        if not result:
            raise ValueError(f"Video not found: {video_id}")
        return result[0]["file_path"]


class ObjectDetectionTool(Tool):
    """Tool for detecting objects in video frames."""
    
    def __init__(self):
        self.detector = ObjectDetector()
    
    @property
    def name(self) -> str:
        return "detect_objects"
    
    @property
    def description(self) -> str:
        return "Detect objects in video frames using YOLOv8"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "frame_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of frame image paths to analyze"
                },
                "timestamps": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of timestamps corresponding to frames"
                },
                "confidence_threshold": {
                    "type": "number",
                    "description": "Minimum confidence score for detections (0-1)",
                    "default": 0.25
                },
                "object_class": {
                    "type": "string",
                    "description": "Specific object class to search for (optional)"
                }
            }
        }
    
    async def execute(self, video_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects in frames."""
        try:
            # If no frame paths provided, get all frames for video
            if "frame_paths" not in parameters or not parameters["frame_paths"]:
                frames = self._get_video_frames(video_id)
                frame_paths = [f["image_path"] for f in frames]
                timestamps = [f["timestamp"] for f in frames]
            else:
                frame_paths = parameters["frame_paths"]
                timestamps = parameters["timestamps"]
            
            confidence_threshold = parameters.get("confidence_threshold", 0.25)
            object_class = parameters.get("object_class")
            
            # Detect objects
            if object_class:
                # Search for specific object
                detections = self.detector.search_for_object(
                    frame_paths,
                    timestamps,
                    object_class,
                    confidence_threshold
                )
            else:
                # Detect all objects
                detections = self.detector.detect_objects_in_frames(
                    frame_paths,
                    timestamps,
                    confidence_threshold
                )
            
            return {
                "detections": [detection.dict() for detection in detections],
                "count": len(detections)
            }
        except Exception as e:
            logger.error(f"Object detection failed: {str(e)}")
            raise
    
    def _get_video_frames(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all frames for a video from database."""
        db = get_database()
        results = db.execute_query(
            """SELECT data FROM video_context 
               WHERE video_id = ? AND context_type = 'frame'
               ORDER BY timestamp""",
            (video_id,)
        )
        
        if not results:
            # Try to extract frames first
            logger.info(f"No frames found for video {video_id}, extracting...")
            extractor_tool = FrameExtractionTool()
            import asyncio
            result = asyncio.run(extractor_tool.execute(video_id, {}))
            return result["frames"]
        
        import json
        return [json.loads(row["data"]) for row in results]


class ToolRegistry:
    """Registry for managing and discovering video processing tools."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        logger.info("Tool registry initialized")
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a new tool.
        
        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Retrieve tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools with their definitions.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": tool.name,
                "type": "function",
                "description": tool.description,
                "parameters": tool.parameters_schema
            }
            for tool in self.tools.values()
        ]
    
    def register_all_tools(self) -> None:
        """Register all available video processing tools."""
        try:
            # Register frame extraction tool
            self.register_tool(FrameExtractionTool())
            
            # Register image captioning tool
            self.register_tool(ImageCaptioningTool())
            
            # Register audio transcription tool
            self.register_tool(AudioTranscriptionTool())
            
            # Register object detection tool
            self.register_tool(ObjectDetectionTool())
            
            logger.info(f"Successfully registered {len(self.tools)} tools")
        except Exception as e:
            logger.error(f"Failed to register tools: {str(e)}")
            raise
