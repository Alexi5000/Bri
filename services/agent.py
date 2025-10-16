"""Groq Agent for conversational video analysis."""

import httpx
import time
from typing import Optional, Dict, Any, List

from groq import Groq
from models.responses import AssistantMessageResponse
from services.memory import Memory
from services.router import ToolRouter, ToolPlan
from services.context import ContextBuilder
from services.media_utils import MediaUtils
from services.error_handler import ErrorHandler
from config import Config
from utils.logging_config import get_logger, get_performance_logger, get_api_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)
api_logger = get_api_logger(__name__)


class AgentError(Exception):
    """Custom exception for agent-related errors."""
    pass


class GroqAgent:
    """
    Groq-powered conversational agent for video analysis.
    
    Provides natural language understanding and response generation with:
    - Tool routing based on query analysis
    - Conversational memory for context awareness
    - Warm, supportive personality
    - Integration with video processing tools via MCP server
    """
    
    # System prompt defining BRI's personality
    SYSTEM_PROMPT = """You are BRI (Brianna), a warm, supportive, and knowledgeable video analysis assistant.

Your personality:
- Friendly and approachable, like chatting with a knowledgeable friend
- Supportive and encouraging, making users feel comfortable
- Clear and concise, avoiding unnecessary jargon
- Playful when appropriate, using light humor and emojis occasionally
- Empathetic and understanding of user needs

Your capabilities:
- Analyze video content including visual scenes, audio transcripts, and detected objects
- Answer questions about specific moments using timestamps
- Find and describe relevant scenes based on user queries
- **REMEMBER previous conversations** - You have access to conversation history and should reference it
- Maintain conversation context to handle follow-up questions naturally
- Provide helpful suggestions for further exploration
- **Work with partial data** - You can answer questions even while video is still processing

Handling partial data:
- If you only have frames: Describe what you can see visually, mention timestamps
- If you have captions: Provide richer visual descriptions and scene understanding
- If you have transcripts: Include what was said and audio context
- If you have objects: Mention detected items and their locations
- Be honest about what data you have and what's still processing

Communication style:
- Use conversational language, not robotic responses
- **Reference previous messages** when relevant to show you remember
- Include relevant timestamps when discussing specific moments
- Offer follow-up suggestions to help users explore the video
- When you don't have information, be honest and suggest alternatives
- Keep responses focused and helpful, avoiding unnecessary verbosity

IMPORTANT: When users ask about previous conversations, acknowledge that you remember them and reference specific details from the conversation history provided to you.

Remember: You're here to make video analysis feel natural and enjoyable!"""

    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        memory: Optional[Memory] = None,
        context_builder: Optional[ContextBuilder] = None
    ):
        """
        Initialize Groq Agent.
        
        Args:
            groq_api_key: Groq API key. Uses Config.GROQ_API_KEY if not provided.
            memory: Memory instance for conversation history. Creates new if not provided.
            context_builder: ContextBuilder instance. Creates new if not provided.
        """
        self.groq_api_key = groq_api_key or Config.GROQ_API_KEY
        if not self.groq_api_key:
            raise AgentError("Groq API key is required")
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=self.groq_api_key)
        
        # Initialize components
        self.memory = memory or Memory()
        self.context_builder = context_builder or ContextBuilder()
        self.router = ToolRouter()
        
        # MCP server configuration
        self.mcp_base_url = Config.get_mcp_server_url()
        
        logger.info("Groq Agent initialized")
    
    async def chat(
        self,
        message: str,
        video_id: str,
        image_base64: Optional[str] = None
    ) -> AssistantMessageResponse:
        """
        Main entry point for processing user messages.
        
        Args:
            message: User's message/query
            video_id: Video being discussed
            image_base64: Optional base64-encoded image for visual queries
            
        Returns:
            AssistantMessageResponse with message, frames, timestamps, and suggestions
            
        Raises:
            AgentError: If processing fails
        """
        start_time = time.time()
        try:
            logger.info(f"Processing message for video {video_id}: {message[:50]}...")
            
            # Check if video has existing context (already processed)
            has_video_context = self._check_video_context_exists(video_id)
            
            # Determine if tools are needed
            tool_type = self._should_use_tool(message, has_video_context)
            
            if tool_type:
                # Process with tools
                response_text, frames, timestamps, frame_contexts = await self._run_with_tool(
                    message,
                    video_id,
                    image_base64
                )
            else:
                # General conversational response
                response_text = await self._respond_general(message, video_id)
                frames = []
                timestamps = []
                frame_contexts = []
            
            # Generate follow-up suggestions
            suggestions = self._generate_suggestions(message, response_text, video_id)
            
            # Store interaction in memory
            self._add_memory_pair(video_id, message, response_text)
            
            execution_time = time.time() - start_time
            logger.info(f"Generated response with {len(frames)} frames and {len(timestamps)} timestamps")
            perf_logger.log_execution_time(
                "chat_processing",
                execution_time,
                success=True,
                video_id=video_id,
                used_tools=tool_type is not None,
                frames_count=len(frames)
            )
            
            # Convert frame_contexts to FrameWithContext objects
            from models.responses import FrameWithContext
            frame_context_objects = [
                FrameWithContext(**ctx) for ctx in frame_contexts
            ] if frame_contexts else None
            
            return AssistantMessageResponse(
                message=response_text,
                frames=frames,
                timestamps=timestamps,
                suggestions=suggestions,
                frame_contexts=frame_context_objects
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Chat processing failed: {e}", exc_info=True)
            perf_logger.log_execution_time(
                "chat_processing",
                execution_time,
                success=False,
                video_id=video_id,
                error=str(e)
            )
            # Return friendly error message using ErrorHandler
            error_message = ErrorHandler.format_error_for_user(
                e,
                context={'query': message}
            )
            return AssistantMessageResponse(
                message=error_message,
                frames=[],
                timestamps=[],
                suggestions=["Try asking about something else in the video"]
            )
    
    def _check_video_context_exists(self, video_id: str) -> bool:
        """
        Check if video has existing processed context.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if video has been processed, False otherwise
        """
        try:
            video_context = self.context_builder.build_video_context(video_id, include_conversation=False)
            # Check for any video data: frames, captions, transcripts, or objects
            return bool(video_context.frames or video_context.captions or video_context.transcript or video_context.objects)
        except Exception:
            return False
    
    def _get_processing_stage_info(self, video_id: str) -> Dict[str, Any]:
        """
        Get current processing stage and available data for a video.
        
        Returns information about what data is available and what's still processing.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with stage info:
            {
                'stage': 'extracting' | 'captioning' | 'transcribing' | 'complete',
                'has_frames': bool,
                'has_captions': bool,
                'has_transcripts': bool,
                'has_objects': bool,
                'message': str  # User-friendly message about current stage
            }
        """
        try:
            # Get video context to check what's available
            video_context = self.context_builder.build_video_context(video_id, include_conversation=False)
            
            has_frames = bool(video_context.frames)
            has_captions = bool(video_context.captions)
            has_transcripts = bool(video_context.transcript and video_context.transcript.segments)
            has_objects = bool(video_context.objects)
            
            # Determine stage based on available data
            if has_transcripts and has_objects:
                stage = 'complete'
                message = None
            elif has_captions:
                stage = 'transcribing'
                message = "🎤 Still transcribing audio and detecting objects... I can answer visual questions now!"
            elif has_frames:
                stage = 'captioning'
                message = "🔍 Still analyzing video content... I can describe what I see in the frames!"
            else:
                stage = 'extracting'
                message = "⏳ Still extracting frames from your video... Give me just a moment!"
            
            return {
                'stage': stage,
                'has_frames': has_frames,
                'has_captions': has_captions,
                'has_transcripts': has_transcripts,
                'has_objects': has_objects,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing stage info: {e}")
            return {
                'stage': 'unknown',
                'has_frames': False,
                'has_captions': False,
                'has_transcripts': False,
                'has_objects': False,
                'message': "⏳ Processing your video... This may take a moment!"
            }
    
    def _should_use_tool(self, message: str, has_video_context: bool) -> Optional[str]:
        """
        Determine if a tool is needed for the query.
        
        Args:
            message: User's message
            has_video_context: Whether video has existing processed context
            
        Returns:
            Tool type if needed ('video_analysis'), None for general conversation
        """
        message_lower = message.lower()
        
        # Check for general conversational patterns that don't need tools
        general_only_patterns = [
            'hello', 'hi ', 'hey ', 'thanks', 'thank you',
            'how are you', 'who are you'
        ]
        
        # If message is purely conversational and short, no tools needed
        is_general = False
        for pattern in general_only_patterns:
            if message_lower.startswith(pattern) or f" {pattern}" in message_lower:
                if len(message.split()) < 10:
                    is_general = True
                    break
        
        if is_general:
            return None
        
        # If video has context, ANY question about the video should use it
        # This ensures we leverage existing analysis for all queries
        if has_video_context:
            return 'video_analysis'
        
        # Check for queries that require video content analysis
        # These should trigger tool usage even if video hasn't been processed yet
        content_analysis_patterns = [
            'recommend', 'worth', 'good', 'quality', 'rating',
            'summary', 'summarize', 'overview', 'about',
            'purpose', 'message', 'theme', 'genre', 'category',
            'audience', 'educational', 'entertainment'
        ]
        
        for pattern in content_analysis_patterns:
            if pattern in message_lower:
                return 'video_analysis'
        
        # Check if query requires video analysis
        tool_plan = self.router.analyze_query(message)
        if tool_plan.tools_needed:
            return 'video_analysis'
        
        return None
    
    async def _run_with_tool(
        self,
        message: str,
        video_id: str,
        image_base64: Optional[str]
    ) -> tuple[str, List[str], List[float], List[Dict[str, Any]]]:
        """
        Execute tool-based query processing with stage-aware responses.
        
        ENHANCED: Now checks processing stage and provides appropriate responses
        based on available data (frames-only, captions, or full intelligence).
        
        Args:
            message: User's query
            video_id: Video identifier
            image_base64: Optional image data
            
        Returns:
            Tuple of (response_text, frame_paths, timestamps, frame_contexts)
        """
        # Check processing stage and available data
        stage_info = self._get_processing_stage_info(video_id)
        logger.info(f"Processing stage for video {video_id}: {stage_info['stage']}")
        
        # Analyze query to determine tools needed
        tool_plan = self.router.analyze_query(message)
        
        logger.info(f"Tool plan: {tool_plan.tools_needed}")
        
        # Gather context from tools (will use whatever data is available)
        context_data = await self._gather_tool_context(
            video_id,
            tool_plan
        )
        
        # Get conversation history for context
        conversation_context = self.memory.get_recent_context(video_id, max_messages=6)
        
        # Build prompt with context
        prompt = self._build_tool_prompt(
            message,
            context_data,
            conversation_context
        )
        
        # Generate response using Groq
        response_text = await self._generate_response(prompt)
        
        # Add processing notice if video is still being processed
        if stage_info['message']:
            response_text = f"{response_text}\n\n---\n\n💡 **Note:** {stage_info['message']}"
        
        # Extract and organize relevant moments with media
        frames, timestamps, frame_contexts = self._extract_relevant_moments(
            context_data,
            message,
            response_text
        )
        
        # Generate thumbnails for frames
        frame_thumbnails = self._generate_frame_thumbnails(frames)
        
        # Update frame contexts with thumbnail paths
        for i, context in enumerate(frame_contexts):
            if i < len(frame_thumbnails):
                context['frame_path'] = frame_thumbnails[i]
        
        # Enhance response with formatted timestamps
        response_text = self._format_timestamps_in_response(
            response_text,
            timestamps
        )
        
        return response_text, frame_thumbnails, timestamps, frame_contexts
    
    async def _gather_tool_context(
        self,
        video_id: str,
        tool_plan: ToolPlan
    ) -> Dict[str, Any]:
        """
        Gather context from video processing tools via MCP server.
        
        ENHANCED: Now checks database FIRST for ALL available data types before
        calling MCP tools. This ensures we use existing processed data.
        
        Args:
            video_id: Video identifier
            tool_plan: Tool execution plan
            
        Returns:
            Dictionary with context data from tools
        """
        context_data = {
            'frames': [],
            'timestamps': [],
            'captions': [],
            'transcripts': [],
            'objects': [],
            'errors': []  # Track tool errors for graceful degradation
        }
        
        # STEP 1: Check database for ALL available data types FIRST
        # This is the key enhancement - we prioritize existing data
        logger.info(f"Checking database for existing video context for {video_id}")
        try:
            video_context = self.context_builder.build_video_context(video_id, include_conversation=False)
            
            # Extract captions (HIGHEST PRIORITY)
            if video_context.captions:
                logger.info(f"Found {len(video_context.captions)} captions in database")
                for caption in video_context.captions:
                    context_data['captions'].append({
                        'timestamp': caption.frame_timestamp,
                        'text': caption.text,
                        'confidence': caption.confidence,
                        'frame_path': caption.frame_path if hasattr(caption, 'frame_path') else None
                    })
                    if caption.frame_timestamp not in context_data['timestamps']:
                        context_data['timestamps'].append(caption.frame_timestamp)
            
            # Extract transcripts (HIGH PRIORITY)
            if video_context.transcript and video_context.transcript.segments:
                logger.info(f"Found {len(video_context.transcript.segments)} transcript segments in database")
                for segment in video_context.transcript.segments:
                    context_data['transcripts'].append({
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment.text,
                        'confidence': segment.confidence if hasattr(segment, 'confidence') else 1.0
                    })
                    if segment.start not in context_data['timestamps']:
                        context_data['timestamps'].append(segment.start)
            
            # Extract objects (MEDIUM PRIORITY)
            if video_context.objects:
                logger.info(f"Found {len(video_context.objects)} object detections in database")
                for detection in video_context.objects:
                    context_data['objects'].append({
                        'timestamp': detection.frame_timestamp,
                        'objects': [
                            {
                                'class_name': obj.class_name,
                                'confidence': obj.confidence,
                                'bbox': obj.bbox if hasattr(obj, 'bbox') else None
                            }
                            for obj in detection.objects
                        ],
                        'frame_path': detection.frame_path if hasattr(detection, 'frame_path') else None
                    })
                    if detection.frame_timestamp not in context_data['timestamps']:
                        context_data['timestamps'].append(detection.frame_timestamp)
            
            # Extract frames (FALLBACK)
            if video_context.frames:
                logger.info(f"Found {len(video_context.frames)} frames in database")
                for frame in video_context.frames:
                    if frame.image_path and frame.image_path not in context_data['frames']:
                        context_data['frames'].append(frame.image_path)
                    if frame.timestamp not in context_data['timestamps']:
                        context_data['timestamps'].append(frame.timestamp)
            
            # If we have substantial data from database, we may not need to call MCP tools
            has_captions = len(context_data['captions']) > 0
            has_transcripts = len(context_data['transcripts']) > 0
            has_objects = len(context_data['objects']) > 0
            
            if has_captions or has_transcripts or has_objects:
                logger.info(
                    f"Using existing database context: "
                    f"{len(context_data['captions'])} captions, "
                    f"{len(context_data['transcripts'])} transcripts, "
                    f"{len(context_data['objects'])} objects"
                )
                # Sort timestamps for chronological order
                context_data['timestamps'].sort()
                return context_data
            else:
                logger.info("No processed data in database, will call MCP tools")
        
        except Exception as e:
            logger.warning(f"Failed to retrieve context from database: {e}")
            # Continue to MCP tools as fallback
        
        # STEP 2: If no data in database, call MCP tools (original behavior)
        failed_tools = []
        successful_tools = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Execute tools based on plan
                for tool_name in tool_plan.execution_order:
                    try:
                        # Map tool names to MCP tool names
                        mcp_tool_name = self._map_tool_name(tool_name)
                        
                        # Prepare request
                        request_data = {
                            "tool_name": mcp_tool_name,
                            "video_id": video_id,
                            "parameters": tool_plan.parameters
                        }
                        
                        # Execute tool via MCP server
                        response = await client.post(
                            f"{self.mcp_base_url}/tools/{mcp_tool_name}/execute",
                            json=request_data
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('status') == 'success':
                                # Process tool result
                                self._process_tool_result(
                                    tool_name,
                                    result.get('result'),
                                    context_data
                                )
                                successful_tools.append(tool_name)
                                logger.info(f"Tool {tool_name} executed successfully")
                            else:
                                logger.warning(f"Tool {tool_name} returned error: {result}")
                                failed_tools.append(tool_name)
                                # Generate friendly error message
                                error_msg = ErrorHandler.handle_tool_error(
                                    mcp_tool_name,
                                    Exception(result.get('error', 'Unknown error')),
                                    successful_tools
                                )
                                context_data['errors'].append(error_msg)
                        else:
                            logger.warning(f"Tool {tool_name} request failed: {response.status_code}")
                            failed_tools.append(tool_name)
                    
                    except Exception as e:
                        logger.error(f"Tool {tool_name} execution failed: {e}")
                        failed_tools.append(tool_name)
                        # Generate friendly error message
                        error_msg = ErrorHandler.handle_tool_error(
                            tool_name,
                            e,
                            successful_tools
                        )
                        context_data['errors'].append(error_msg)
                        # Continue with other tools (graceful degradation)
                        continue
        
        except Exception as e:
            logger.error(f"Failed to gather tool context: {e}")
            context_data['errors'].append(
                ErrorHandler.format_error_for_user(e, context={'processing': True})
            )
        
        # Sort timestamps for chronological order
        if context_data['timestamps']:
            context_data['timestamps'].sort()
        
        return context_data
    
    def _map_tool_name(self, tool_name: str) -> str:
        """Map router tool names to MCP tool names."""
        mapping = {
            'captions': 'caption_frames',
            'transcripts': 'transcribe_audio',
            'objects': 'detect_objects'
        }
        return mapping.get(tool_name, tool_name)
    
    def _process_tool_result(
        self,
        tool_name: str,
        result: Any,
        context_data: Dict[str, Any]
    ) -> None:
        """Process tool result and add to context data."""
        if tool_name == 'captions' and result:
            context_data['captions'] = result.get('captions', [])
            # Extract frames and timestamps
            for caption in result.get('captions', []):
                if 'frame_path' in caption:
                    context_data['frames'].append(caption['frame_path'])
                if 'timestamp' in caption:
                    context_data['timestamps'].append(caption['timestamp'])
        
        elif tool_name == 'transcripts' and result:
            context_data['transcripts'] = result.get('segments', [])
            # Extract timestamps from transcript
            for segment in result.get('segments', []):
                if 'start' in segment:
                    context_data['timestamps'].append(segment['start'])
        
        elif tool_name == 'objects' and result:
            context_data['objects'] = result.get('detections', [])
            # Extract frames and timestamps from detections
            for detection in result.get('detections', []):
                if 'frame_path' in detection:
                    context_data['frames'].append(detection['frame_path'])
                if 'timestamp' in detection:
                    context_data['timestamps'].append(detection['timestamp'])
    
    def _build_tool_prompt(
        self,
        message: str,
        context_data: Dict[str, Any],
        conversation_context: str
    ) -> str:
        """Build prompt with tool context for Groq.
        
        ENHANCED: Uses structured format with prioritized data:
        Visual > Audio > Objects > Frames
        Includes only relevant data for the specific query to reduce prompt size.
        Summarizes long contexts to stay within token limits.
        """
        prompt_parts = []
        
        # Add conversation history if available (summarize if too long)
        if conversation_context:
            # Limit conversation context to ~500 chars to save tokens
            if len(conversation_context) > 500:
                conversation_context = conversation_context[-500:]
                prompt_parts.append("Previous conversation (recent):")
            else:
                prompt_parts.append("Previous conversation:")
            prompt_parts.append(conversation_context)
            prompt_parts.append("")
        
        # Add video context in structured format
        prompt_parts.append("Video Context:")
        
        # Determine query type to include only relevant data
        message_lower = message.lower()
        is_visual_query = any(kw in message_lower for kw in ['see', 'look', 'show', 'describe', 'scene', 'visual', 'appear'])
        is_audio_query = any(kw in message_lower for kw in ['say', 'said', 'speak', 'talk', 'mention', 'audio', 'hear'])
        is_object_query = any(kw in message_lower for kw in ['find', 'locate', 'search', 'detect', 'person', 'car', 'dog', 'cat'])
        
        # Check if query has timestamp - if so, filter context to relevant time window
        timestamp_param = None
        if 'timestamp' in context_data.get('parameters', {}):
            timestamp_param = context_data['parameters']['timestamp']
        
        # Priority 1: Captions (most informative for visual queries)
        if context_data.get('captions'):
            captions = context_data['captions']
            
            # Filter by timestamp if specified
            if timestamp_param is not None:
                window = 10.0  # 10 second window
                captions = [
                    c for c in captions
                    if abs(c.get('timestamp', 0) - timestamp_param) <= window
                ]
            
            # Include more captions for visual queries, fewer for others
            max_captions = 10 if is_visual_query else 5
            
            if captions:
                prompt_parts.append(f"\nVisual: ({len(captions)} scenes analyzed)")
                for caption in captions[:max_captions]:
                    timestamp = caption.get('timestamp', 0)
                    text = caption.get('text', '')
                    # Truncate very long captions
                    if len(text) > 100:
                        text = text[:97] + "..."
                    prompt_parts.append(f"  [{timestamp:.1f}s] {text}")
                
                if len(captions) > max_captions:
                    prompt_parts.append(f"  ... and {len(captions) - max_captions} more scenes")
        
        # Priority 2: Transcripts (most informative for audio queries)
        if context_data.get('transcripts'):
            transcripts = context_data['transcripts']
            
            # Filter by timestamp if specified
            if timestamp_param is not None:
                window = 10.0
                transcripts = [
                    t for t in transcripts
                    if abs(t.get('start', 0) - timestamp_param) <= window
                ]
            
            # Include more transcript for audio queries, fewer for others
            max_segments = 10 if is_audio_query else 5
            
            if transcripts:
                prompt_parts.append(f"\nAudio: ({len(transcripts)} segments)")
                for segment in transcripts[:max_segments]:
                    start = segment.get('start', 0)
                    text = segment.get('text', '')
                    # Truncate very long segments
                    if len(text) > 150:
                        text = text[:147] + "..."
                    prompt_parts.append(f"  [{start:.1f}s] {text}")
                
                if len(transcripts) > max_segments:
                    prompt_parts.append(f"  ... and {len(transcripts) - max_segments} more segments")
        
        # Priority 3: Objects (most informative for object queries)
        if context_data.get('objects'):
            objects = context_data['objects']
            
            # Filter by timestamp if specified
            if timestamp_param is not None:
                window = 10.0
                objects = [
                    o for o in objects
                    if abs(o.get('timestamp', 0) - timestamp_param) <= window
                ]
            
            # Include more objects for object queries, fewer for others
            max_detections = 10 if is_object_query else 5
            
            if objects:
                prompt_parts.append(f"\nObjects: ({len(objects)} frames analyzed)")
                
                # Summarize objects by type
                object_summary = {}
                for detection in objects:
                    timestamp = detection.get('timestamp', 0)
                    objs = detection.get('objects', [])
                    for obj in objs:
                        obj_name = obj.get('class_name', '')
                        if obj_name not in object_summary:
                            object_summary[obj_name] = []
                        object_summary[obj_name].append(timestamp)
                
                # Show object summary
                for obj_name, timestamps in list(object_summary.items())[:max_detections]:
                    ts_list = [f"{ts:.1f}s" for ts in timestamps[:3]]
                    if len(timestamps) > 3:
                        ts_list.append(f"+{len(timestamps) - 3} more")
                    prompt_parts.append(f"  {obj_name}: {', '.join(ts_list)}")
        
        # Fallback: If no captions, mention frames are available
        if not context_data.get('captions') and context_data.get('frames'):
            prompt_parts.append(f"\nFrames: {len(context_data['frames'])} frames extracted")
            prompt_parts.append("  (Visual analysis not yet complete)")
        
        # Add user question
        prompt_parts.append(f"\nUser question: {message}")
        
        # Add instruction based on available data
        if context_data.get('captions') or context_data.get('transcripts') or context_data.get('objects'):
            prompt_parts.append("\nProvide a helpful, conversational response based on the video context above.")
            prompt_parts.append("Reference specific timestamps when relevant.")
        else:
            prompt_parts.append("\nThe video has been uploaded but detailed analysis is still in progress.")
            prompt_parts.append("Acknowledge what you know and offer to analyze specific aspects.")
        
        # Log prompt size for monitoring
        prompt = "\n".join(prompt_parts)
        logger.debug(f"Built prompt with {len(prompt)} characters, ~{len(prompt.split())} words")
        
        return prompt
    
    async def _respond_general(self, message: str, video_id: str) -> str:
        """
        Generate general conversational response without tools.
        
        Args:
            message: User's message
            video_id: Video identifier
            
        Returns:
            Response text
        """
        # Get conversation history for context
        conversation_context = self.memory.get_recent_context(video_id, max_messages=4)
        
        # Check if video has been processed (has existing context)
        video_context = None
        try:
            video_context = self.context_builder.build_video_context(video_id, include_conversation=False)
        except Exception as e:
            logger.debug(f"No video context available: {e}")
        
        # Build prompt
        prompt_parts = []
        
        if conversation_context:
            prompt_parts.append("Previous conversation:")
            prompt_parts.append(conversation_context)
            prompt_parts.append("")
        
        # Add video context summary if available
        has_any_context = video_context and (video_context.frames or video_context.captions or video_context.transcript or video_context.objects)
        
        if has_any_context:
            prompt_parts.append("Video context available:")
            
            if video_context.metadata:
                prompt_parts.append(f"  Duration: {video_context.metadata.duration:.1f}s")
            
            if video_context.frames:
                prompt_parts.append(f"  Video frames: {len(video_context.frames)} frames extracted")
            
            if video_context.captions:
                prompt_parts.append(f"  Visual analysis: {len(video_context.captions)} scenes analyzed")
                # Include a few sample captions
                for caption in video_context.captions[:3]:
                    prompt_parts.append(f"    [{caption.frame_timestamp:.1f}s] {caption.text}")
            
            if video_context.transcript and video_context.transcript.segments:
                prompt_parts.append(f"  Audio transcript: {len(video_context.transcript.segments)} segments")
                # Include a few sample segments
                for segment in video_context.transcript.segments[:3]:
                    prompt_parts.append(f"    [{segment.start:.1f}s] {segment.text}")
            
            if video_context.objects:
                prompt_parts.append(f"  Object detection: {len(video_context.objects)} frames analyzed")
            
            prompt_parts.append("")
        
        prompt_parts.append(f"User: {message}")
        
        if has_any_context:
            if video_context.captions or video_context.transcript or video_context.objects:
                prompt_parts.append("\nRespond based on the video context provided above. Be helpful and conversational.")
            else:
                # Has frames but no detailed analysis yet
                prompt_parts.append("\nThe video has been uploaded and frames extracted, but detailed analysis (captions/transcripts) is still in progress. Acknowledge what you know and offer to analyze specific aspects.")
        else:
            prompt_parts.append("\nThe video hasn't been analyzed yet. Respond in a friendly manner and suggest they ask questions that will trigger video analysis.")
        
        prompt = "\n".join(prompt_parts)
        
        # Generate response
        response = await self._generate_response(prompt)
        return response
    
    async def _generate_response(self, prompt: str) -> str:
        """
        Generate response using Groq API.
        
        Args:
            prompt: Prompt text
            
        Returns:
            Generated response text
        """
        start_time = time.time()
        try:
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.groq_client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=messages,
                temperature=Config.GROQ_TEMPERATURE,
                max_tokens=Config.GROQ_MAX_TOKENS
            )
            
            execution_time = time.time() - start_time
            api_logger.log_api_call(
                "Groq",
                f"/chat/completions (model: {Config.GROQ_MODEL})",
                method="POST",
                status_code=200,
                execution_time=execution_time
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Groq API call failed: {e}")
            api_logger.log_api_call(
                "Groq",
                f"/chat/completions (model: {Config.GROQ_MODEL})",
                method="POST",
                execution_time=execution_time,
                error=str(e)
            )
            # Use ErrorHandler for friendly API error messages
            friendly_message = ErrorHandler.handle_api_error(e)
            raise AgentError(friendly_message)
    
    def _add_memory_pair(
        self,
        video_id: str,
        user_message: str,
        assistant_message: str
    ) -> None:
        """
        Store user-assistant interaction in memory.
        
        Args:
            video_id: Video identifier
            user_message: User's message
            assistant_message: Assistant's response
        """
        try:
            self.memory.add_memory_pair(
                video_id,
                user_message,
                assistant_message
            )
            logger.debug(f"Stored memory pair for video {video_id}")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            # Don't fail the request if memory storage fails
    
    def _extract_relevant_moments(
        self,
        context_data: Dict[str, Any],
        query: str,
        response: str
    ) -> tuple[List[str], List[float], List[Dict[str, Any]]]:
        """
        Extract and organize relevant frames and timestamps from context.
        
        Presents multiple relevant moments in chronological order with their
        associated frames and descriptions.
        
        Args:
            context_data: Context data from tools
            query: User's query
            response: Generated response text
            
        Returns:
            Tuple of (frame_paths, timestamps, frame_contexts) sorted chronologically
        """
        # Collect all moments with their timestamps and frames
        moments = []  # List of (timestamp, frame_path, description) tuples
        
        # Extract from captions
        for caption in context_data.get('captions', []):
            timestamp = caption.get('timestamp', 0)
            frame_path = caption.get('frame_path', '')
            description = caption.get('text', '')
            
            if frame_path and timestamp is not None:
                moments.append((timestamp, frame_path, description))
        
        # Extract from object detections
        for detection in context_data.get('objects', []):
            timestamp = detection.get('timestamp', 0)
            frame_path = detection.get('frame_path', '')
            objects = detection.get('objects', [])
            
            if frame_path and timestamp is not None and objects:
                obj_names = [obj.get('class_name', '') for obj in objects]
                description = f"Objects: {', '.join(obj_names)}"
                moments.append((timestamp, frame_path, description))
        
        # Extract from transcripts (use nearby frames if available)
        for segment in context_data.get('transcripts', []):
            timestamp = segment.get('start', 0)
            # Find closest frame to this timestamp
            closest_frame = self._find_closest_frame(
                timestamp,
                context_data.get('frames', [])
            )
            if closest_frame:
                description = segment.get('text', '')
                moments.append((timestamp, closest_frame, description))
        
        # Remove duplicates and sort by timestamp
        unique_moments = {}
        for timestamp, frame_path, description in moments:
            # Use timestamp as key to avoid duplicate timestamps
            if timestamp not in unique_moments:
                unique_moments[timestamp] = (frame_path, description)
        
        # Sort by timestamp (chronological order)
        sorted_timestamps = sorted(unique_moments.keys())
        
        # Extract frames, timestamps, and contexts in chronological order
        frames = []
        timestamps = []
        frame_contexts = []
        
        for ts in sorted_timestamps:
            frame_path, description = unique_moments[ts]
            frames.append(frame_path)
            timestamps.append(ts)
            frame_contexts.append({
                'frame_path': frame_path,
                'timestamp': ts,
                'description': description
            })
        
        # Limit to top 10 most relevant moments to avoid overwhelming the user
        max_moments = 10
        if len(frames) > max_moments:
            frames = frames[:max_moments]
            timestamps = timestamps[:max_moments]
            frame_contexts = frame_contexts[:max_moments]
        
        logger.info(f"Extracted {len(frames)} relevant moments in chronological order")
        return frames, timestamps, frame_contexts
    
    def _find_closest_frame(
        self,
        timestamp: float,
        frames: List[str]
    ) -> Optional[str]:
        """
        Find the frame path closest to a given timestamp.
        
        Args:
            timestamp: Target timestamp
            frames: List of frame paths
            
        Returns:
            Closest frame path or None
        """
        if not frames:
            return None
        
        # For now, just return the first frame
        # In a full implementation, we'd parse timestamps from frame paths
        # or maintain a mapping of timestamps to frames
        return frames[0] if frames else None
    
    def _generate_frame_thumbnails(self, frames: List[str]) -> List[str]:
        """
        Generate thumbnails for frame images.
        
        Creates thumbnail versions of frames for efficient display in responses.
        Falls back to original frames if thumbnail generation fails.
        
        Args:
            frames: List of frame image paths
            
        Returns:
            List of thumbnail paths (or original paths if generation fails)
        """
        if not frames:
            return []
        
        try:
            # Generate thumbnails for all frames
            thumbnails = MediaUtils.batch_generate_thumbnails(
                frames,
                max_width=320,
                max_height=180,
                quality=85
            )
            logger.info(f"Generated {len(thumbnails)} thumbnails")
            return thumbnails
            
        except Exception as e:
            logger.warning(f"Failed to generate thumbnails, using original frames: {e}")
            # Fallback to original frames
            return frames
    
    def _format_timestamps_in_response(
        self,
        response: str,
        timestamps: List[float]
    ) -> str:
        """
        Format timestamps in the response text for better readability.
        
        Converts raw timestamps to human-readable format (MM:SS or HH:MM:SS)
        and ensures they're properly highlighted in the response.
        
        Args:
            response: Original response text
            timestamps: List of timestamps referenced
            
        Returns:
            Response with formatted timestamps
        """
        import re
        
        # Find all timestamp patterns in the response (e.g., "1:23", "0:45", "12.5s")
        # Pattern matches: "12.5s", "1:23", "01:23:45"
        timestamp_pattern = r'(\d+\.?\d*s|\d+:\d+(?::\d+)?)'
        
        def format_timestamp(seconds: float) -> str:
            """Convert seconds to MM:SS or HH:MM:SS format."""
            return MediaUtils.format_timestamp(seconds)
        
        # Replace timestamp patterns with formatted versions
        def replace_timestamp(match):
            ts_str = match.group(1)
            try:
                # Parse the timestamp
                if 's' in ts_str:
                    # Format: "12.5s"
                    seconds = float(ts_str.replace('s', ''))
                elif ':' in ts_str:
                    # Already formatted, keep as is
                    return ts_str
                else:
                    return ts_str
                
                # Format and return
                return format_timestamp(seconds)
            except Exception:
                return ts_str
        
        formatted_response = re.sub(timestamp_pattern, replace_timestamp, response)
        
        # If we have timestamps but they're not mentioned in the response,
        # add a helpful note at the end
        if timestamps and not re.search(timestamp_pattern, response):
            formatted_timestamps = [format_timestamp(ts) for ts in timestamps[:3]]
            if len(timestamps) > 3:
                timestamp_note = f"\n\nRelevant moments: {', '.join(formatted_timestamps)}, and {len(timestamps) - 3} more."
            else:
                timestamp_note = f"\n\nRelevant moments: {', '.join(formatted_timestamps)}."
            
            formatted_response += timestamp_note
        
        return formatted_response
    
    def _generate_suggestions(
        self,
        user_message: str,
        response: str,
        video_id: str
    ) -> List[str]:
        """
        Generate 1-3 relevant follow-up question suggestions.
        
        Analyzes the user's query and response to suggest:
        - Related aspects to explore
        - Deeper dives into mentioned topics
        - Proactive content discovery
        
        Requirements: 9.1, 9.2, 9.3, 9.4
        
        Args:
            user_message: User's original message
            response: Assistant's response
            video_id: Video identifier
            
        Returns:
            List of 1-3 suggested follow-up questions
        """
        suggestions = []
        
        message_lower = user_message.lower()
        response_lower = response.lower()
        
        # Determine query type and generate appropriate suggestions
        query_type = self._classify_query_type(message_lower)
        
        if query_type == 'visual_description':
            suggestions = self._suggest_visual_followups(message_lower, response_lower)
        
        elif query_type == 'audio_transcript':
            suggestions = self._suggest_audio_followups(message_lower, response_lower)
        
        elif query_type == 'object_search':
            suggestions = self._suggest_object_followups(message_lower, response_lower)
        
        elif query_type == 'timestamp_specific':
            suggestions = self._suggest_timestamp_followups(message_lower, response_lower)
        
        elif query_type == 'summary':
            suggestions = self._suggest_summary_followups(message_lower, response_lower)
        
        elif query_type == 'general':
            suggestions = self._suggest_general_followups(message_lower, response_lower)
        
        else:
            # Fallback to generic exploration suggestions
            suggestions = self._suggest_exploration_followups()
        
        # Add proactive content discovery suggestions if response mentions additional content
        proactive_suggestions = self._detect_additional_content(response_lower)
        if proactive_suggestions:
            suggestions.extend(proactive_suggestions)
        
        # Ensure we return 1-3 suggestions (requirement 9.1)
        # Prioritize diversity and relevance
        unique_suggestions = list(dict.fromkeys(suggestions))  # Remove duplicates while preserving order
        return unique_suggestions[:3]
    
    def _classify_query_type(self, message_lower: str) -> str:
        """
        Classify the type of query to generate appropriate suggestions.
        
        Args:
            message_lower: Lowercased user message
            
        Returns:
            Query type classification
        """
        # Summary queries (check first as they're more specific)
        if any(phrase in message_lower for phrase in [
            'summary', 'summarize', 'overview', 'main point', 'key', 'overall theme'
        ]):
            return 'summary'
        
        # Audio/transcript queries
        if any(phrase in message_lower for phrase in [
            'say', 'said', 'talk', 'speak', 'mention', 'discuss', 'audio', 'hear'
        ]):
            return 'audio_transcript'
        
        # Object search queries
        if any(phrase in message_lower for phrase in [
            'find', 'show me', 'where', 'locate', 'search', 'all the'
        ]):
            return 'object_search'
        
        # Timestamp-specific queries (check before visual as they're more specific)
        # But exclude phrases like "see" which are visual
        if any(phrase in message_lower for phrase in [
            'at ', 'timestamp', 'minute', 'second', ':'
        ]) and 'see' not in message_lower:
            return 'timestamp_specific'
        
        # Visual description queries
        if any(phrase in message_lower for phrase in [
            'describe', 'see', 'look', 'appear', 'scene', 'visual', 'happening', 'going on', 'shown'
        ]):
            return 'visual_description'
        
        # General conversational
        if any(phrase in message_lower for phrase in [
            'hello', 'hi', 'thanks', 'thank', 'help', 'can you'
        ]):
            return 'general'
        
        return 'unknown'
    
    def _suggest_visual_followups(self, message_lower: str, response_lower: str) -> List[str]:
        """Generate suggestions for visual description queries."""
        suggestions = []
        
        # Suggest deeper exploration
        suggestions.append("Can you describe a specific moment in more detail?")
        
        # Suggest related aspects
        if 'people' in response_lower or 'person' in response_lower:
            suggestions.append("What are the people doing in the video?")
        elif 'object' in response_lower:
            suggestions.append("What objects can you identify?")
        else:
            suggestions.append("What's the setting or environment like?")
        
        # Suggest temporal exploration
        suggestions.append("How does the scene change throughout the video?")
        
        return suggestions
    
    def _suggest_audio_followups(self, message_lower: str, response_lower: str) -> List[str]:
        """Generate suggestions for audio/transcript queries."""
        suggestions = []
        
        # Suggest content exploration
        suggestions.append("Can you summarize the main points discussed?")
        
        # Suggest related topics
        if 'topic' in response_lower or 'about' in response_lower:
            suggestions.append("What else was mentioned about this topic?")
        else:
            suggestions.append("What other topics are covered?")
        
        # Suggest context
        suggestions.append("What's the context around this conversation?")
        
        return suggestions
    
    def _suggest_object_followups(self, message_lower: str, response_lower: str) -> List[str]:
        """Generate suggestions for object search queries."""
        suggestions = []
        
        # Suggest similar searches
        suggestions.append("Are there any other similar moments?")
        
        # Suggest context
        suggestions.append("What's happening in those scenes?")
        
        # Suggest related objects
        if 'found' in response_lower or 'appears' in response_lower:
            suggestions.append("What else appears alongside it?")
        else:
            suggestions.append("Can you search for something else?")
        
        return suggestions
    
    def _suggest_timestamp_followups(self, message_lower: str, response_lower: str) -> List[str]:
        """Generate suggestions for timestamp-specific queries."""
        suggestions = []
        
        # Suggest before/after exploration
        suggestions.append("What happens right before this moment?")
        suggestions.append("What happens right after this?")
        
        # Suggest related moments
        suggestions.append("Are there other important moments like this?")
        
        return suggestions
    
    def _suggest_summary_followups(self, message_lower: str, response_lower: str) -> List[str]:
        """Generate suggestions for summary queries."""
        suggestions = []
        
        # Suggest specific exploration
        suggestions.append("Can you tell me more about a specific part?")
        
        # Suggest different aspects
        suggestions.append("What are the key visual elements?")
        suggestions.append("What's the main message or theme?")
        
        return suggestions
    
    def _suggest_general_followups(self, message_lower: str, response_lower: str) -> List[str]:
        """Generate suggestions for general conversational queries."""
        suggestions = []
        
        # Suggest getting started
        suggestions.append("What's this video about?")
        suggestions.append("Can you describe what you see?")
        suggestions.append("What's being said in the audio?")
        
        return suggestions
    
    def _suggest_exploration_followups(self) -> List[str]:
        """Generate generic exploration suggestions."""
        return [
            "What are the main highlights of this video?",
            "Can you describe a specific scene?",
            "What's the overall theme?"
        ]
    
    def _detect_additional_content(self, response_lower: str) -> List[str]:
        """
        Detect if response mentions additional content and suggest proactive exploration.
        
        Requirement 9.3: Proactively offer to share additional relevant content
        
        Args:
            response_lower: Lowercased response text
            
        Returns:
            List of proactive suggestions
        """
        suggestions = []
        
        # Detect mentions of additional content
        if 'also' in response_lower or 'additionally' in response_lower:
            suggestions.append("Tell me more about what else you found")
        
        if 'other' in response_lower and ('moment' in response_lower or 'scene' in response_lower):
            suggestions.append("Show me those other moments")
        
        if 'more' in response_lower or 'several' in response_lower or 'multiple' in response_lower:
            suggestions.append("Can you elaborate on that?")
        
        if 'beginning' in response_lower or 'start' in response_lower:
            suggestions.append("What happens later in the video?")
        
        if 'end' in response_lower or 'ending' in response_lower:
            suggestions.append("What led up to that?")
        
        # Detect specific content types mentioned
        if 'q&a' in response_lower or 'question' in response_lower:
            suggestions.append("Want me to summarize the Q&A session?")
        
        if 'interview' in response_lower:
            suggestions.append("What are the key points from the interview?")
        
        if 'demonstration' in response_lower or 'demo' in response_lower:
            suggestions.append("Can you walk me through the demonstration?")
        
        return suggestions
    
    def _handle_error(self, error: Exception) -> str:
        """
        Generate friendly error message.
        
        Args:
            error: Exception that occurred
            
        Returns:
            User-friendly error message
        """
        error_str = str(error).lower()
        
        if 'api' in error_str or 'groq' in error_str:
            return "I'm having trouble thinking right now. Give me a moment and try again! 🤔"
        
        elif 'timeout' in error_str:
            return "That's taking longer than expected. Mind trying again? ⏱️"
        
        elif 'connection' in error_str or 'network' in error_str:
            return "I'm having trouble connecting to my tools. Let's try that again! 🔌"
        
        else:
            return "Oops, something unexpected happened! Could you try rephrasing your question? 😅"
    
    def close(self) -> None:
        """Clean up resources."""
        if self.memory:
            self.memory.close()
        logger.info("Groq Agent closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
