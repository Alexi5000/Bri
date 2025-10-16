"""Context Builder for aggregating video processing results."""

import logging
import json
from typing import List, Optional
from dataclasses import dataclass
from models.video import VideoMetadata, Frame
from models.memory import MemoryRecord
from models.tools import Caption, Transcript, TranscriptSegment, DetectionResult, DetectedObject
from storage.database import Database

# Import semantic search service (optional)
try:
    from services.semantic_search import get_semantic_search_service
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

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
    
    def __init__(self, db: Optional[Database] = None, enable_semantic_search: bool = True):
        """Initialize Context Builder.
        
        Args:
            db: Database instance. Creates new instance if not provided.
            enable_semantic_search: Whether to enable semantic search (requires chromadb + sentence-transformers)
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        
        # Initialize semantic search if available and enabled
        self.semantic_search = None
        if enable_semantic_search and SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.semantic_search = get_semantic_search_service()
                if self.semantic_search.is_enabled():
                    logger.info("Context Builder initialized with semantic search enabled")
                else:
                    logger.info("Context Builder initialized (semantic search unavailable)")
            except Exception as e:
                logger.warning(f"Failed to initialize semantic search: {e}")
                self.semantic_search = None
        else:
            logger.info("Context Builder initialized (semantic search disabled)")
    
    def build_video_context(
        self,
        video_id: str,
        include_conversation: bool = True
    ) -> VideoContext:
        """Compile all available data for a video.
        
        ENHANCED: Now checks database for ALL available data types and builds
        rich context even with partial data. Prioritizes: captions > transcripts > objects > frames
        
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
            logger.debug(f"Building comprehensive context for video {video_id}")
            
            # Retrieve ALL data types from database
            # Priority order: captions > transcripts > objects > frames
            
            # 1. Retrieve metadata (always try first for video info)
            metadata = self._get_video_metadata(video_id)
            
            # 2. Retrieve captions (HIGHEST PRIORITY - most informative)
            captions = self._get_captions(video_id)
            
            # 3. Retrieve transcript (HIGH PRIORITY - audio content)
            transcript = self._get_transcript(video_id)
            
            # 4. Retrieve object detections (MEDIUM PRIORITY - specific objects)
            objects = self._get_object_detections(video_id)
            
            # 5. Retrieve frames (FALLBACK - raw visual data)
            frames = self._get_frames(video_id)
            
            # 6. Retrieve conversation history if requested
            conversation_history = []
            if include_conversation:
                conversation_history = self._get_conversation_history(video_id)
            
            # Build context with all available data
            context = VideoContext(
                video_id=video_id,
                metadata=metadata,
                frames=frames,
                captions=captions,
                transcript=transcript,
                objects=objects,
                conversation_history=conversation_history
            )
            
            # Log comprehensive data availability
            data_summary = []
            if metadata:
                data_summary.append(f"metadata (duration: {metadata.duration:.1f}s)")
            if captions:
                data_summary.append(f"{len(captions)} captions")
            if transcript and transcript.segments:
                data_summary.append(f"{len(transcript.segments)} transcript segments")
            if objects:
                data_summary.append(f"{len(objects)} object detections")
            if frames:
                data_summary.append(f"{len(frames)} frames")
            
            if data_summary:
                logger.info(f"Built context for video {video_id}: {', '.join(data_summary)}")
            else:
                logger.warning(f"No processed data found for video {video_id}")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build context for video {video_id}: {e}")
            raise ContextError(f"Failed to build video context: {e}")

    def build_rich_context_description(
        self,
        video_id: str,
        max_items: int = 10
    ) -> str:
        """Build a rich text description of video context even with partial data.
        
        Prioritizes: captions > transcripts > objects > frames
        Provides fallback descriptions when higher-priority data is unavailable.
        
        Args:
            video_id: Video identifier
            max_items: Maximum number of items to include per data type
            
        Returns:
            Rich text description of available video context
        """
        try:
            context = self.build_video_context(video_id, include_conversation=False)
            description_parts = []
            
            # Add metadata summary
            if context.metadata:
                description_parts.append(
                    f"Video duration: {context.metadata.duration:.1f}s "
                    f"({context.metadata.width}x{context.metadata.height})"
                )
            
            # Priority 1: Captions (most informative)
            if context.captions:
                description_parts.append(f"\nVisual Analysis ({len(context.captions)} scenes):")
                for caption in context.captions[:max_items]:
                    description_parts.append(
                        f"  [{self._format_timestamp(caption.frame_timestamp)}] {caption.text}"
                    )
                if len(context.captions) > max_items:
                    description_parts.append(f"  ... and {len(context.captions) - max_items} more scenes")
            
            # Priority 2: Transcripts (audio content)
            if context.transcript and context.transcript.segments:
                description_parts.append(f"\nAudio Transcript ({len(context.transcript.segments)} segments):")
                for segment in context.transcript.segments[:max_items]:
                    description_parts.append(
                        f"  [{self._format_timestamp(segment.start)}] {segment.text}"
                    )
                if len(context.transcript.segments) > max_items:
                    description_parts.append(f"  ... and {len(context.transcript.segments) - max_items} more segments")
            
            # Priority 3: Objects (specific detections)
            if context.objects:
                description_parts.append(f"\nDetected Objects ({len(context.objects)} frames analyzed):")
                object_summary = {}
                for detection in context.objects:
                    for obj in detection.objects:
                        obj_name = obj.class_name
                        if obj_name not in object_summary:
                            object_summary[obj_name] = []
                        object_summary[obj_name].append(detection.frame_timestamp)
                
                for obj_name, timestamps in list(object_summary.items())[:max_items]:
                    ts_str = ", ".join([self._format_timestamp(ts) for ts in timestamps[:3]])
                    if len(timestamps) > 3:
                        ts_str += f" (+{len(timestamps) - 3} more)"
                    description_parts.append(f"  {obj_name}: {ts_str}")
            
            # Priority 4: Frames (fallback - describe by timestamp)
            if context.frames and not context.captions:
                description_parts.append(f"\nExtracted Frames ({len(context.frames)} frames):")
                description_parts.append("  Frames available at:")
                timestamps = [self._format_timestamp(f.timestamp) for f in context.frames[:max_items]]
                description_parts.append(f"  {', '.join(timestamps)}")
                if len(context.frames) > max_items:
                    description_parts.append(f"  ... and {len(context.frames) - max_items} more frames")
            
            if not description_parts:
                return "No processed data available for this video yet."
            
            return "\n".join(description_parts)
            
        except Exception as e:
            logger.error(f"Failed to build rich context description: {e}")
            return "Unable to retrieve video context."
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp as MM:SS or HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def search_captions(
        self,
        video_id: str,
        query: str,
        top_k: int = 5,
        use_semantic: bool = True
    ) -> List[Caption]:
        """Find relevant captions using text similarity.
        
        ENHANCED: Improved keyword matching with:
        - Stemming/lemmatization for better word matching
        - Multiple relevance scoring factors
        - Ranked results by relevance score
        - Optional semantic search with embeddings (if available)
        - Hybrid search combining keyword + semantic matching
        
        Args:
            video_id: Video identifier
            query: Search query text
            top_k: Maximum number of results to return
            use_semantic: Whether to use semantic search (if available)
            
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
            
            # Normalize and process query
            query_lower = query.lower()
            query_words = self._tokenize_and_stem(query_lower)
            
            # Score captions based on multiple relevance factors
            scored_captions = []
            for caption in all_captions:
                caption_lower = caption.text.lower()
                caption_words = self._tokenize_and_stem(caption_lower)
                
                # Calculate relevance score with multiple factors
                score = 0.0
                
                # Factor 1: Exact phrase match (highest priority - 100 points)
                if query_lower in caption_lower:
                    score += 100.0
                
                # Factor 2: Stemmed word overlap (50 points max)
                if query_words:
                    overlap = len(query_words.intersection(caption_words))
                    word_overlap_score = (overlap / len(query_words)) * 50.0
                    score += word_overlap_score
                
                # Factor 3: Partial word matches (25 points max)
                partial_matches = 0
                for q_word in query_lower.split():
                    if len(q_word) > 3:  # Only check words longer than 3 chars
                        for c_word in caption_lower.split():
                            if q_word in c_word or c_word in q_word:
                                partial_matches += 1
                                break
                if query_lower.split():
                    partial_score = (partial_matches / len(query_lower.split())) * 25.0
                    score += partial_score
                
                # Factor 4: Synonym/related word matching (10 points max)
                synonym_score = self._calculate_synonym_score(query_lower, caption_lower)
                score += synonym_score
                
                # Boost score by caption confidence (multiply by 0.5 to 1.0)
                confidence_multiplier = 0.5 + (caption.confidence * 0.5)
                score *= confidence_multiplier
                
                scored_captions.append((score, caption))
            
            # Sort by score (descending)
            scored_captions.sort(key=lambda x: x[0], reverse=True)
            keyword_results = [(score, caption) for score, caption in scored_captions if score > 0]
            
            # If semantic search is available and enabled, perform hybrid search
            if use_semantic and self.semantic_search and self.semantic_search.is_enabled():
                try:
                    # Convert keyword results to format expected by hybrid search
                    kw_results_dict = [
                        {
                            'text': caption.text,
                            'score': score,
                            'caption': caption
                        }
                        for score, caption in keyword_results
                    ]
                    
                    # Perform hybrid search
                    hybrid_results = self.semantic_search.hybrid_search(
                        query=query,
                        keyword_results=kw_results_dict,
                        video_id=video_id,
                        top_k=top_k,
                        semantic_weight=0.7  # 70% semantic, 30% keyword
                    )
                    
                    # Extract captions from hybrid results
                    results = []
                    for result in hybrid_results:
                        if 'caption' in result:
                            results.append(result['caption'])
                        else:
                            # Semantic-only result, find matching caption
                            for _, caption in keyword_results:
                                if caption.text == result['text']:
                                    results.append(caption)
                                    break
                    
                    logger.info(
                        f"Hybrid search found {len(results)} captions for query: {query} "
                        f"(keyword: {len(keyword_results)}, semantic: enabled)"
                    )
                    return results[:top_k]
                    
                except Exception as e:
                    logger.warning(f"Hybrid search failed, falling back to keyword search: {e}")
            
            # Fallback to keyword-only results
            results = [caption for score, caption in keyword_results[:top_k]]
            
            logger.info(
                f"Keyword search found {len(results)} captions for query: {query} "
                f"(top score: {keyword_results[0][0]:.1f})" if keyword_results else ""
            )
            return results
            
        except Exception as e:
            logger.error(f"Failed to search captions: {e}")
            raise ContextError(f"Failed to search captions: {e}")
    
    def _tokenize_and_stem(self, text: str) -> set:
        """Tokenize and apply simple stemming to text.
        
        Uses basic suffix removal for stemming (simplified Porter stemmer).
        
        Args:
            text: Input text
            
        Returns:
            Set of stemmed tokens
        """
        # Remove punctuation and split
        import string
        text = text.translate(str.maketrans('', '', string.punctuation))
        words = text.lower().split()
        
        # Apply simple stemming (remove common suffixes)
        stemmed = set()
        for word in words:
            # Skip very short words
            if len(word) <= 2:
                stemmed.add(word)
                continue
            
            # Remove common suffixes
            if word.endswith('ing'):
                stemmed.add(word[:-3])
            elif word.endswith('ed'):
                stemmed.add(word[:-2])
            elif word.endswith('s') and not word.endswith('ss'):
                stemmed.add(word[:-1])
            elif word.endswith('ly'):
                stemmed.add(word[:-2])
            else:
                stemmed.add(word)
        
        return stemmed
    
    def _calculate_synonym_score(self, query: str, caption: str) -> float:
        """Calculate score based on synonym/related word matching.
        
        Uses a simple synonym dictionary for common visual terms.
        
        Args:
            query: Query text
            caption: Caption text
            
        Returns:
            Synonym match score (0-10)
        """
        # Simple synonym dictionary for common visual terms
        synonyms = {
            'person': ['man', 'woman', 'people', 'human', 'individual'],
            'car': ['vehicle', 'automobile', 'truck', 'van'],
            'dog': ['puppy', 'canine', 'pet'],
            'cat': ['kitten', 'feline', 'pet'],
            'walk': ['walking', 'stroll', 'move', 'moving'],
            'run': ['running', 'jog', 'jogging', 'sprint'],
            'sit': ['sitting', 'seated', 'rest'],
            'stand': ['standing', 'upright'],
            'talk': ['talking', 'speak', 'speaking', 'conversation'],
            'eat': ['eating', 'consume', 'meal'],
            'drink': ['drinking', 'beverage'],
            'hold': ['holding', 'carry', 'carrying', 'grip'],
            'wear': ['wearing', 'dressed', 'clothing'],
            'look': ['looking', 'gaze', 'watch', 'watching'],
        }
        
        score = 0.0
        query_words = query.lower().split()
        caption_lower = caption.lower()
        
        for word in query_words:
            if word in synonyms:
                # Check if any synonym appears in caption
                for synonym in synonyms[word]:
                    if synonym in caption_lower:
                        score += 2.0  # 2 points per synonym match
                        break
        
        return min(score, 10.0)  # Cap at 10 points
    
    def search_transcripts(
        self,
        video_id: str,
        query: str,
        top_k: int = 10
    ) -> List[TranscriptSegment]:
        """Search transcript for keywords.
        
        ENHANCED: Improved keyword matching with relevance scoring and ranking.
        
        Args:
            video_id: Video identifier
            query: Search query text (keywords)
            top_k: Maximum number of results to return
            
        Returns:
            List of TranscriptSegment objects ranked by relevance
            
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
            
            # Normalize and process query
            query_lower = query.lower()
            query_words = self._tokenize_and_stem(query_lower)
            
            # Score segments based on relevance
            scored_segments = []
            for segment in transcript.segments:
                segment_lower = segment.text.lower()
                segment_words = self._tokenize_and_stem(segment_lower)
                
                score = 0.0
                
                # Factor 1: Exact phrase match (100 points)
                if query_lower in segment_lower:
                    score += 100.0
                
                # Factor 2: Stemmed word overlap (50 points max)
                if query_words:
                    overlap = len(query_words.intersection(segment_words))
                    word_overlap_score = (overlap / len(query_words)) * 50.0
                    score += word_overlap_score
                
                # Factor 3: Partial word matches (25 points max)
                partial_matches = 0
                for q_word in query_lower.split():
                    if len(q_word) > 3:
                        for s_word in segment_lower.split():
                            if q_word in s_word or s_word in q_word:
                                partial_matches += 1
                                break
                if query_lower.split():
                    partial_score = (partial_matches / len(query_lower.split())) * 25.0
                    score += partial_score
                
                # Boost by confidence if available
                if hasattr(segment, 'confidence'):
                    confidence_multiplier = 0.5 + (segment.confidence * 0.5)
                    score *= confidence_multiplier
                
                if score > 0:
                    scored_segments.append((score, segment))
            
            # Sort by score (descending) and return top_k
            scored_segments.sort(key=lambda x: x[0], reverse=True)
            matching_segments = [segment for score, segment in scored_segments[:top_k]]
            
            logger.info(
                f"Found {len(matching_segments)} transcript segments for query: {query} "
                f"(top score: {scored_segments[0][0]:.1f})" if scored_segments else ""
            )
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

    # Private helper methods for data retrieval
    
    def _get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """Retrieve video metadata from database.
        
        Args:
            video_id: Video identifier
            
        Returns:
            VideoMetadata if found, None otherwise
        """
        try:
            query = """
                SELECT data
                FROM video_context
                WHERE video_id = ? AND context_type = 'metadata'
                ORDER BY created_at DESC
                LIMIT 1
            """
            rows = self.db.execute_query(query, (video_id,))
            
            if not rows:
                return None
            
            data = json.loads(rows[0]['data'])
            return VideoMetadata(**data)
            
        except Exception as e:
            logger.warning(f"Failed to retrieve metadata for video {video_id}: {e}")
            return None
    
    def _get_frames(self, video_id: str) -> List[Frame]:
        """Retrieve all frames for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List of Frame objects
        """
        try:
            query = """
                SELECT data, timestamp
                FROM video_context
                WHERE video_id = ? AND context_type = 'frame'
                ORDER BY timestamp ASC
            """
            rows = self.db.execute_query(query, (video_id,))
            
            frames = []
            for row in rows:
                data = json.loads(row['data'])
                frames.append(Frame(**data))
            
            return frames
            
        except Exception as e:
            logger.warning(f"Failed to retrieve frames for video {video_id}: {e}")
            return []
    
    def _get_captions(self, video_id: str) -> List[Caption]:
        """Retrieve all captions for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List of Caption objects
        """
        try:
            query = """
                SELECT data, timestamp
                FROM video_context
                WHERE video_id = ? AND context_type = 'caption'
                ORDER BY timestamp ASC
            """
            rows = self.db.execute_query(query, (video_id,))
            
            captions = []
            for row in rows:
                data = json.loads(row['data'])
                captions.append(Caption(**data))
            
            return captions
            
        except Exception as e:
            logger.warning(f"Failed to retrieve captions for video {video_id}: {e}")
            return []
    
    def _get_transcript(self, video_id: str) -> Optional[Transcript]:
        """Retrieve transcript for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Transcript if found, None otherwise
        """
        try:
            query = """
                SELECT data
                FROM video_context
                WHERE video_id = ? AND context_type = 'transcript'
                ORDER BY created_at DESC
                LIMIT 1
            """
            rows = self.db.execute_query(query, (video_id,))
            
            if not rows:
                return None
            
            data = json.loads(rows[0]['data'])
            return Transcript(**data)
            
        except Exception as e:
            logger.warning(f"Failed to retrieve transcript for video {video_id}: {e}")
            return None
    
    def _get_object_detections(self, video_id: str) -> List[DetectionResult]:
        """Retrieve all object detections for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List of DetectionResult objects
        """
        try:
            query = """
                SELECT data, timestamp
                FROM video_context
                WHERE video_id = ? AND context_type = 'object'
                ORDER BY timestamp ASC
            """
            rows = self.db.execute_query(query, (video_id,))
            
            detections = []
            for row in rows:
                data = json.loads(row['data'])
                detections.append(DetectionResult(**data))
            
            return detections
            
        except Exception as e:
            logger.warning(f"Failed to retrieve object detections for video {video_id}: {e}")
            return []
    
    def _get_conversation_history(self, video_id: str) -> List[MemoryRecord]:
        """Retrieve conversation history for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List of MemoryRecord objects
        """
        try:
            from services.memory import Memory
            memory = Memory(self.db)
            return memory.get_conversation_history(video_id)
            
        except Exception as e:
            logger.warning(f"Failed to retrieve conversation history for video {video_id}: {e}")
            return []
    
    def _get_transcript_segment_at_timestamp(
        self,
        video_id: str,
        timestamp: float
    ) -> Optional[TranscriptSegment]:
        """Get the transcript segment at a specific timestamp.
        
        Args:
            video_id: Video identifier
            timestamp: Target timestamp in seconds
            
        Returns:
            TranscriptSegment if found, None otherwise
        """
        try:
            transcript = self._get_transcript(video_id)
            
            if not transcript or not transcript.segments:
                return None
            
            # Find segment containing the timestamp
            for segment in transcript.segments:
                if segment.start <= timestamp <= segment.end:
                    return segment
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get transcript segment at {timestamp}s: {e}")
            return None
    
    def index_video_for_semantic_search(self, video_id: str) -> bool:
        """Index video captions and transcripts for semantic search.
        
        This should be called after video processing is complete to enable
        semantic search capabilities.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if indexing successful, False otherwise
        """
        if not self.semantic_search or not self.semantic_search.is_enabled():
            logger.info("Semantic search not available, skipping indexing")
            return False
        
        try:
            logger.info(f"Indexing video {video_id} for semantic search")
            
            # Index captions
            captions = self._get_captions(video_id)
            if captions:
                caption_dicts = [
                    {
                        'text': cap.text,
                        'frame_timestamp': cap.frame_timestamp,
                        'confidence': cap.confidence
                    }
                    for cap in captions
                ]
                self.semantic_search.index_captions(video_id, caption_dicts)
                logger.info(f"Indexed {len(captions)} captions")
            
            # Index transcript segments
            transcript = self._get_transcript(video_id)
            if transcript and transcript.segments:
                segment_dicts = [
                    {
                        'text': seg.text,
                        'start': seg.start,
                        'end': seg.end,
                        'confidence': seg.confidence if hasattr(seg, 'confidence') else 1.0
                    }
                    for seg in transcript.segments
                ]
                self.semantic_search.index_transcripts(video_id, segment_dicts)
                logger.info(f"Indexed {len(transcript.segments)} transcript segments")
            
            logger.info(f"Successfully indexed video {video_id} for semantic search")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index video for semantic search: {e}")
            return False
    
    def search_captions_semantic(
        self,
        video_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Caption]:
        """Search captions using pure semantic similarity (no keyword matching).
        
        Args:
            video_id: Video identifier
            query: Search query text
            top_k: Maximum number of results to return
            min_score: Minimum similarity score threshold (0-1)
            
        Returns:
            List of Caption objects sorted by semantic similarity
        """
        if not self.semantic_search or not self.semantic_search.is_enabled():
            logger.warning("Semantic search not available, falling back to keyword search")
            return self.search_captions(video_id, query, top_k, use_semantic=False)
        
        try:
            # Perform semantic search
            results = self.semantic_search.search(
                query=query,
                video_id=video_id,
                content_type="caption",
                top_k=top_k,
                min_score=min_score
            )
            
            if not results:
                logger.info(f"No semantic results found for query: {query}")
                return []
            
            # Convert semantic results back to Caption objects
            all_captions = self._get_captions(video_id)
            caption_map = {cap.text: cap for cap in all_captions}
            
            matched_captions = []
            for result in results:
                if result.text in caption_map:
                    matched_captions.append(caption_map[result.text])
            
            logger.info(f"Semantic search found {len(matched_captions)} captions for query: {query}")
            return matched_captions
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def get_semantic_search_stats(self) -> dict:
        """Get statistics about semantic search indexing.
        
        Returns:
            Dictionary with stats or empty dict if not available
        """
        if not self.semantic_search:
            return {"enabled": False}
        return self.semantic_search.get_stats()
    
    def close(self) -> None:
        """Close database connection and semantic search service."""
        if self.db:
            self.db.close()
        if self.semantic_search:
            self.semantic_search.close()
        logger.info("Context Builder closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
