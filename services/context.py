"""Context Builder for aggregating video processing results."""

import logging
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from models.video import Video, VideoMetadata, Frame
from models.memory import MemoryRecord
from models.tools import Caption, Transcript, TranscriptSegment, DetectionResult, DetectedObject
from storage.database import Database, DatabaseError

logger = logging.getLogger(__name__)


class ContextError(Exception):
    """Custom exception for context-related errors."""
    pass


@dataclass
class VideoContext:
    """Aggregated context for a video including all processed data."""
    video_id: str
    metadata: Optional[VideoMetadata]
    frames: List[Frame]
    captions: List[Caption]
    transcript: Optional[Transcript]
    objects: List[DetectionResult]
    conversation_history: List[MemoryRecord]


@dataclass
class TimestampContext:
    """Context around a specific timestamp in a video."""
    timestamp: float
    nearby_frames: List[Frame]
    captions: List[Caption]
    transcript_segment: Optional[TranscriptSegment]
    detected_objects: List[DetectedObject]


class ContextBuilder:
    """Context Builder for aggregating and searching video processing results.
    
    Provides methods to:
    - Compile all available data for a video
    - Search captions using text similarity
    - Search transcripts for keywords
    - Find frames containing specific objects
    - Retrieve context around specific timestamps
    """
    
    def __init__(self, db: Optional[Database] = None):
        """Initialize Context Builder.
        
        Args:
            db: Database instance. Creates new instance if not provided.
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("Context Builder initialized")
    
    def build_video_context(
        self,
        video_id: str,
        include_conversation: bool = True
    ) -> VideoContext:
        """Compile all available data for a video.
        
        Args:
            video_id: Video identifier
            include_conversation: Whether to include conversation history
            
        Returns:
            VideoContext with all aggregated data
            
        Raises:
            ContextError: If data retrieval fails
            
        Example:
            context = builder.build_video_context("vid_456")
            print(f"Found {len(context.frames)} frames")
            print(f"Found {len(context.captions)} captions")
        """
        try:
            logger.debug(f"Building context for video {video_id}")
            
            # Retrieve metadata
            metadata = self._get_video_metadata(video_id)
            
            # Retrieve frames
            frames = self._get_frames(video_id)
            
            # Retrieve captions
            captions = self._get_captions(video_id)
            
            # Retrieve transcript
            transcript = self._get_transcript(video_id)
            
            # Retrieve object detections
            objects = self._get_object_detections(video_id)
            
            # Retrieve conversation history if requested
            conversation_history = []
            if include_conversation:
                conversation_history = self._get_conversation_history(video_id)
            
            context = VideoContext(
                video_id=video_id,
                metadata=metadata,
                frames=frames,
                captions=captions,
                transcript=transcript,
                objects=objects,
                conversation_history=conversation_history
            )
            
            logger.info(
                f"Built context for video {video_id}: "
                f"{len(frames)} frames, {len(captions)} captions, "
                f"{len(objects)} detection results"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build context for video {video_id}: {e}")
            raise ContextError(f"Failed to build video context: {e}")

    def search_captions(
        self,
        video_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Caption]:
        """Find relevant captions using text similarity.
        
        Uses simple keyword matching for text similarity.
        For production, consider using embeddings and vector similarity.
        
        Args:
            video_id: Video identifier
            query: Search query text
            top_k: Maximum number of results to return
            
        Returns:
            List of Caption objects sorted by relevance
            
        Raises:
            ContextError: If search fails
            
        Example:
            captions = builder.search_captions("vid_456", "person walking", top_k=3)
            for caption in captions:
                print(f"{caption.frame_timestamp}s: {caption.text}")
        """
        try:
            logger.debug(f"Searching captions for video {video_id} with query: {query}")
            
            # Get all captions for the video
            all_captions = self._get_captions(video_id)
            
            if not all_captions:
                logger.warning(f"No captions found for video {video_id}")
                return []
            
            # Normalize query for matching
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            # Score captions based on keyword overlap
            scored_captions = []
            for caption in all_captions:
                caption_lower = caption.text.lower()
                caption_words = set(caption_lower.split())
                
                # Calculate simple relevance score
                # 1. Exact phrase match (highest priority)
                if query_lower in caption_lower:
                    score = 100.0
                # 2. Word overlap
                else:
                    overlap = len(query_words.intersection(caption_words))
                    score = (overlap / len(query_words)) * 50.0 if query_words else 0.0
                
                # Boost score by caption confidence
                score *= caption.confidence
                
                scored_captions.append((score, caption))
            
            # Sort by score (descending) and return top_k
            scored_captions.sort(key=lambda x: x[0], reverse=True)
            results = [caption for score, caption in scored_captions[:top_k] if score > 0]
            
            logger.info(f"Found {len(results)} relevant captions for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search captions: {e}")
            raise ContextError(f"Failed to search captions: {e}")
    
    def search_transcripts(
        self,
        video_id: str,
        query: str
    ) -> List[TranscriptSegment]:
        """Search transcript for keywords.
        
        Args:
            video_id: Video identifier
            query: Search query text (keywords)
            
        Returns:
            List of TranscriptSegment objects containing the query
            
        Raises:
            ContextError: If search fails
            
        Example:
            segments = builder.search_transcripts("vid_456", "hello world")
            for segment in segments:
                print(f"{segment.start}s-{segment.end}s: {segment.text}")
        """
        try:
            logger.debug(f"Searching transcripts for video {video_id} with query: {query}")
            
            # Get transcript for the video
            transcript = self._get_transcript(video_id)
            
            if not transcript or not transcript.segments:
                logger.warning(f"No transcript found for video {video_id}")
                return []
            
            # Normalize query for matching
            query_lower = query.lower()
            
            # Find segments containing the query
            matching_segments = []
            for segment in transcript.segments:
                if query_lower in segment.text.lower():
                    matching_segments.append(segment)
            
            logger.info(f"Found {len(matching_segments)} transcript segments for query: {query}")
            return matching_segments
            
        except Exception as e:
            logger.error(f"Failed to search transcripts: {e}")
            raise ContextError(f"Failed to search transcripts: {e}")
    
    def get_frames_with_object(
        self,
        video_id: str,
        object_class: str
    ) -> List[Frame]:
        """Find frames containing a specific object.
        
        Args:
            video_id: Video identifier
            object_class: Object class name to search for (e.g., "person", "car", "dog")
            
        Returns:
            List of Frame objects containing the specified object
            
        Raises:
            ContextError: If search fails
            
        Example:
            frames = builder.get_frames_with_object("vid_456", "dog")
            print(f"Found dog in {len(frames)} frames")
        """
        try:
            logger.debug(f"Searching for object '{object_class}' in video {video_id}")
            
            # Get all object detections for the video
            detections = self._get_object_detections(video_id)
            
            if not detections:
                logger.warning(f"No object detections found for video {video_id}")
                return []
            
            # Normalize object class for matching
            object_class_lower = object_class.lower()
            
            # Find timestamps where the object appears
            matching_timestamps = set()
            for detection in detections:
                for obj in detection.objects:
                    if object_class_lower in obj.class_name.lower():
                        matching_timestamps.add(detection.frame_timestamp)
            
            if not matching_timestamps:
                logger.info(f"Object '{object_class}' not found in video {video_id}")
                return []
            
            # Get frames at those timestamps
            all_frames = self._get_frames(video_id)
            matching_frames = [
                frame for frame in all_frames
                if frame.timestamp in matching_timestamps
            ]
            
            logger.info(f"Found object '{object_class}' in {len(matching_frames)} frames")
            return matching_frames
            
        except Exception as e:
            logger.error(f"Failed to search for object: {e}")
            raise ContextError(f"Failed to search for object: {e}")
    
    def get_context_at_timestamp(
        self,
        video_id: str,
        timestamp: float,
        window: float = 5.0
    ) -> TimestampContext:
        """Get all context around a specific timestamp.
        
        Args:
            video_id: Video identifier
            timestamp: Target timestamp in seconds
            window: Time window in seconds (context will span ±window around timestamp)
            
        Returns:
            TimestampContext with all relevant data
            
        Raises:
            ContextError: If retrieval fails
            
        Example:
            context = builder.get_context_at_timestamp("vid_456", 30.5, window=3.0)
            print(f"Found {len(context.nearby_frames)} frames near 30.5s")
        """
        try:
            logger.debug(f"Getting context at timestamp {timestamp}s for video {video_id}")
            
            start_time = max(0, timestamp - window)
            end_time = timestamp + window
            
            # Get frames within the window
            all_frames = self._get_frames(video_id)
            nearby_frames = [
                frame for frame in all_frames
                if start_time <= frame.timestamp <= end_time
            ]
            
            # Get captions within the window
            all_captions = self._get_captions(video_id)
            nearby_captions = [
                caption for caption in all_captions
                if start_time <= caption.frame_timestamp <= end_time
            ]
            
            # Get transcript segment at timestamp
            transcript_segment = self._get_transcript_segment_at_timestamp(
                video_id, timestamp
            )
            
            # Get detected objects within the window
            all_detections = self._get_object_detections(video_id)
            detected_objects = []
            for detection in all_detections:
                if start_time <= detection.frame_timestamp <= end_time:
                    detected_objects.extend(detection.objects)
            
            context = TimestampContext(
                timestamp=timestamp,
                nearby_frames=nearby_frames,
                captions=nearby_captions,
                transcript_segment=transcript_segment,
                detected_objects=detected_objects
            )
            
            logger.info(
                f"Built timestamp context at {timestamp}s: "
                f"{len(nearby_frames)} frames, {len(nearby_captions)} captions, "
                f"{len(detected_objects)} objects"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context at timestamp: {e}")
            raise ContextError(f"Failed to get timestamp context: {e}")
