"""Error Handler for friendly error messages and graceful degradation."""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur in the system."""
    TOOL_ERROR = "tool_error"
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorHandler:
    """
    Handles errors with friendly, playful messages and suggests fallback approaches.
    
    Provides graceful degradation when tools are unavailable and maintains
    BRI's warm, supportive personality even when things go wrong.
    
    Requirements: 3.8, 4.7, 6.4, 10.1, 10.2, 10.3, 10.4, 10.5
    """
    
    # Friendly error messages for different scenarios
    TOOL_ERROR_MESSAGES = {
        'frame_extractor': "I had trouble extracting frames, but I can still help with the audio!",
        'image_captioner': "The visual descriptions are being a bit shy right now, but I can tell you what was said!",
        'audio_transcriber': "The audio was a bit tricky, but I can describe what I see in the video!",
        'object_detector': "I couldn't spot specific objects this time, but I can tell you what's happening overall!",
        'caption_frames': "I had trouble describing the scenes, but I can help with the audio content!",
        'transcribe_audio': "The audio transcription is taking a break, but I can describe what's visible!",
        'detect_objects': "Object detection is being camera-shy, but I can still describe the scenes!",
    }
    
    API_ERROR_MESSAGES = {
        'rate_limit': "I'm thinking a bit too hard right now! Give me a moment and try again.",
        'timeout': "That took longer than expected. Let's try something simpler!",
        'authentication': "I'm having trouble connecting to my brain. Check the API key configuration!",
        'unavailable': "I'm having trouble thinking right now. Give me a moment and try again!",
        'invalid_request': "Hmm, I didn't quite understand that request. Could you rephrase it?",
    }
    
    GENERAL_ERROR_MESSAGES = [
        "Oops! Something unexpected happened. Let's try that again!",
        "I hit a little snag there. Mind giving it another shot?",
        "That didn't go as planned. Let's try a different approach!",
        "I'm having a moment here. Could you try asking in a different way?",
    ]
    
    @staticmethod
    def handle_tool_error(
        tool_name: str,
        error: Exception,
        available_tools: Optional[List[str]] = None
    ) -> str:
        """
        Generate friendly error message for tool-specific failures.
        
        Provides context-aware messages that maintain BRI's personality
        and suggest alternative approaches when a tool fails.
        
        Args:
            tool_name: Name of the tool that failed
            error: The exception that occurred
            available_tools: List of tools that are still available
            
        Returns:
            Friendly error message with suggestions
            
        Requirement: 10.1, 10.2
        """
        logger.warning(f"Tool '{tool_name}' failed: {error}")
        
        # Get base error message for this tool
        base_message = ErrorHandler.TOOL_ERROR_MESSAGES.get(
            tool_name,
            f"I had trouble with {tool_name}, but I'll do my best with what I have!"
        )
        
        # Add fallback suggestions if other tools are available
        if available_tools:
            fallback_msg = ErrorHandler._suggest_tool_fallback(
                tool_name,
                available_tools
            )
            if fallback_msg:
                base_message += f" {fallback_msg}"
        
        return base_message
    
    @staticmethod
    def handle_api_error(error: Exception) -> str:
        """
        Handle Groq API errors gracefully with friendly messages.
        
        Detects specific API error types and provides appropriate
        user-friendly messages with actionable suggestions.
        
        Args:
            error: The API exception that occurred
            
        Returns:
            Friendly error message
            
        Requirement: 10.1, 10.5
        """
        error_str = str(error).lower()
        
        # Detect specific error types
        if 'rate limit' in error_str or '429' in error_str:
            return ErrorHandler.API_ERROR_MESSAGES['rate_limit']
        
        elif 'timeout' in error_str or 'timed out' in error_str:
            return ErrorHandler.API_ERROR_MESSAGES['timeout']
        
        elif 'authentication' in error_str or 'unauthorized' in error_str or '401' in error_str:
            return ErrorHandler.API_ERROR_MESSAGES['authentication']
        
        elif 'unavailable' in error_str or '503' in error_str or '502' in error_str:
            return ErrorHandler.API_ERROR_MESSAGES['unavailable']
        
        elif 'invalid' in error_str or '400' in error_str:
            return ErrorHandler.API_ERROR_MESSAGES['invalid_request']
        
        else:
            # Generic API error
            return "I'm having trouble thinking right now. Let's try again in a moment!"
    
    @staticmethod
    def suggest_fallback(
        original_query: str,
        available_data: List[str],
        failed_tools: Optional[List[str]] = None
    ) -> str:
        """
        Suggest alternative approaches when primary method fails.
        
        Analyzes what data is available and suggests how the user
        can still get useful information despite tool failures.
        
        Args:
            original_query: The user's original query
            available_data: List of data types still available (e.g., ['captions', 'transcripts'])
            failed_tools: List of tools that failed
            
        Returns:
            Suggestion for alternative approach
            
        Requirement: 10.3
        """
        if not available_data:
            return "I don't have much data to work with right now. Try uploading the video again or asking a general question!"
        
        query_lower = original_query.lower()
        suggestions = []
        
        # Suggest based on what's available
        if 'captions' in available_data:
            if 'audio' in query_lower or 'say' in query_lower or 'said' in query_lower:
                suggestions.append("I can describe what's visible in the video instead!")
            else:
                suggestions.append("I can describe the visual scenes for you!")
        
        if 'transcripts' in available_data:
            if 'see' in query_lower or 'look' in query_lower or 'visual' in query_lower:
                suggestions.append("I can tell you what was said instead!")
            else:
                suggestions.append("I can share what was said in the audio!")
        
        if 'objects' in available_data:
            suggestions.append("I can tell you about objects I detected!")
        
        # Build friendly suggestion message
        if len(suggestions) == 1:
            return suggestions[0]
        elif len(suggestions) > 1:
            return f"{suggestions[0]} Or, {suggestions[1].lower()}"
        else:
            return "Let me know what else you'd like to know about the video!"
    
    @staticmethod
    def handle_graceful_degradation(
        requested_tools: List[str],
        available_tools: List[str],
        query: str
    ) -> Dict[str, Any]:
        """
        Implement graceful degradation when tools are unavailable.
        
        Determines which tools can still be used and provides a plan
        for answering the query with limited capabilities.
        
        Args:
            requested_tools: Tools that were requested for the query
            available_tools: Tools that are actually available
            query: User's query
            
        Returns:
            Dictionary with degradation plan and user message
            
        Requirement: 10.4, 10.5
        """
        unavailable_tools = [t for t in requested_tools if t not in available_tools]
        usable_tools = [t for t in requested_tools if t in available_tools]
        
        # Build user-facing message
        if not usable_tools:
            message = "My tools are taking a break right now. I can still chat about what we've already found!"
            can_proceed = False
        else:
            # Generate friendly message about degraded service
            if len(unavailable_tools) == 1:
                tool_name = unavailable_tools[0]
                message = ErrorHandler.TOOL_ERROR_MESSAGES.get(
                    tool_name,
                    f"I'm having trouble with {tool_name}, but I'll work with what I have!"
                )
            else:
                message = "Some of my tools are being temperamental, but I'll do my best with what's working!"
            
            can_proceed = True
        
        return {
            'can_proceed': can_proceed,
            'usable_tools': usable_tools,
            'unavailable_tools': unavailable_tools,
            'message': message,
            'fallback_suggestion': ErrorHandler.suggest_fallback(
                query,
                usable_tools,
                unavailable_tools
            ) if usable_tools else None
        }
    
    @staticmethod
    def handle_video_upload_error(error: Exception, filename: str) -> str:
        """
        Handle video upload errors with friendly messages.
        
        Args:
            error: The exception that occurred
            filename: Name of the file being uploaded
            
        Returns:
            Friendly error message
            
        Requirement: 10.1, 10.2
        """
        error_str = str(error).lower()
        
        # Check for specific upload error types
        if 'format' in error_str or 'codec' in error_str:
            return "Oops! I can only work with MP4, AVI, MOV, or MKV files. Want to try another format?"
        
        elif 'size' in error_str or 'too large' in error_str:
            return "This video is a bit too big for me right now. Can you try one under 500MB?"
        
        elif 'permission' in error_str or 'access' in error_str:
            return "I don't have permission to access that file. Could you check the file permissions?"
        
        elif 'not found' in error_str or 'no such file' in error_str:
            return "Hmm, I can't find that file. Did it move somewhere?"
        
        else:
            return "Hmm, something went wrong with the upload. Mind giving it another shot?"
    
    @staticmethod
    def handle_processing_error(
        video_id: str,
        error: Exception,
        completed_steps: Optional[List[str]] = None
    ) -> str:
        """
        Handle video processing errors with context about what succeeded.
        
        Args:
            video_id: Video identifier
            error: The exception that occurred
            completed_steps: List of processing steps that completed successfully
            
        Returns:
            Friendly error message with context
            
        Requirement: 10.1, 10.2
        """
        error_str = str(error).lower()
        
        base_message = "I ran into a hiccup while processing your video."
        
        # Add context about what succeeded
        if completed_steps:
            if len(completed_steps) == 1:
                base_message += f" I did manage to complete {completed_steps[0]}, though!"
            else:
                steps_str = ", ".join(completed_steps[:-1]) + f" and {completed_steps[-1]}"
                base_message += f" I did manage to complete {steps_str}, though!"
        
        # Add specific guidance based on error type
        if 'memory' in error_str or 'out of memory' in error_str:
            base_message += " The video might be too large. Try a shorter clip?"
        elif 'timeout' in error_str:
            base_message += " It's taking longer than expected. Want to try again?"
        else:
            base_message += " Let's give it another try!"
        
        return base_message
    
    @staticmethod
    def handle_query_error(query: str, error: Exception) -> str:
        """
        Handle query processing errors with helpful suggestions.
        
        Args:
            query: The user's query that failed
            error: The exception that occurred
            
        Returns:
            Friendly error message with suggestions
            
        Requirement: 10.1, 10.3
        """
        error_str = str(error).lower()
        
        # Check for specific query error types
        if 'timestamp' in error_str or 'out of range' in error_str:
            return "That timestamp is beyond the video length. Could you try a different time?"
        
        elif 'not found' in error_str or 'no results' in error_str:
            return "I couldn't find that in the video. Want to try asking about something else?"
        
        elif 'ambiguous' in error_str or 'unclear' in error_str:
            return "I'm not quite sure what you're looking for. Could you be more specific?"
        
        else:
            return "I had trouble understanding that question. Could you rephrase it?"
    
    @staticmethod
    def _suggest_tool_fallback(
        failed_tool: str,
        available_tools: List[str]
    ) -> Optional[str]:
        """
        Suggest alternative tools when one fails.
        
        Args:
            failed_tool: Tool that failed
            available_tools: Tools still available
            
        Returns:
            Suggestion message or None
        """
        # Map tools to their alternatives
        fallback_map = {
            'caption_frames': ['transcribe_audio', 'detect_objects'],
            'image_captioner': ['transcribe_audio', 'detect_objects'],
            'transcribe_audio': ['caption_frames', 'detect_objects'],
            'audio_transcriber': ['caption_frames', 'detect_objects'],
            'detect_objects': ['caption_frames', 'transcribe_audio'],
            'object_detector': ['caption_frames', 'transcribe_audio'],
        }
        
        alternatives = fallback_map.get(failed_tool, [])
        available_alternatives = [t for t in alternatives if t in available_tools]
        
        if not available_alternatives:
            return None
        
        # Generate friendly suggestion
        if 'caption' in available_alternatives[0] or 'image' in available_alternatives[0]:
            return "I can still describe what's visible!"
        elif 'transcribe' in available_alternatives[0] or 'audio' in available_alternatives[0]:
            return "I can still tell you what was said!"
        elif 'object' in available_alternatives[0] or 'detect' in available_alternatives[0]:
            return "I can still identify objects in the scenes!"
        
        return None
    
    @staticmethod
    def get_generic_error_message() -> str:
        """
        Get a generic friendly error message.
        
        Returns:
            Random friendly error message
        """
        import random
        return random.choice(ErrorHandler.GENERAL_ERROR_MESSAGES)
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorType:
        """
        Classify an error into a specific type.
        
        Args:
            error: The exception to classify
            
        Returns:
            ErrorType classification
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Check for API errors
        if 'api' in error_str or 'groq' in error_str or 'rate limit' in error_str:
            return ErrorType.API_ERROR
        
        # Check for network errors
        if 'connection' in error_str or 'network' in error_str or 'timeout' in error_str:
            return ErrorType.NETWORK_ERROR
        
        # Check for validation errors
        if 'validation' in error_str or 'invalid' in error_str or 'valueerror' in error_type_name:
            return ErrorType.VALIDATION_ERROR
        
        # Check for processing errors
        if 'processing' in error_str or 'decode' in error_str or 'encode' in error_str:
            return ErrorType.PROCESSING_ERROR
        
        # Check for tool errors
        if 'tool' in error_str or 'extractor' in error_str or 'detector' in error_str:
            return ErrorType.TOOL_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    @staticmethod
    def format_error_for_user(
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format any error into a user-friendly message.
        
        Main entry point for error handling that routes to specific
        handlers based on error type and context.
        
        Args:
            error: The exception that occurred
            context: Optional context about where/how the error occurred
            
        Returns:
            Friendly error message
            
        Requirement: 10.1, 10.2
        """
        context = context or {}
        error_type = ErrorHandler.classify_error(error)
        
        # Route to specific handler based on error type and context
        if context.get('tool_name'):
            return ErrorHandler.handle_tool_error(
                context['tool_name'],
                error,
                context.get('available_tools')
            )
        
        elif error_type == ErrorType.API_ERROR:
            return ErrorHandler.handle_api_error(error)
        
        elif context.get('upload'):
            return ErrorHandler.handle_video_upload_error(
                error,
                context.get('filename', 'video')
            )
        
        elif context.get('processing'):
            return ErrorHandler.handle_processing_error(
                context.get('video_id', ''),
                error,
                context.get('completed_steps')
            )
        
        elif context.get('query'):
            return ErrorHandler.handle_query_error(
                context.get('query', ''),
                error
            )
        
        else:
            return ErrorHandler.get_generic_error_message()
