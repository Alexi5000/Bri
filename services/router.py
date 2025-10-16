"""Tool Router for query analysis and tool selection."""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolPlan:
    """Represents an execution plan for processing a query."""
    tools_needed: List[str] = field(default_factory=list)  # e.g., ['captions', 'objects']
    execution_order: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


class ToolRouter:
    """
    Analyzes user queries to determine which video processing tools are needed
    and coordinates their execution.
    """
    
    # Keywords for different tool types
    CAPTION_KEYWORDS = [
        'what', 'describe', 'scene', 'happening', 'show', 'see', 'visual',
        'look', 'appear', 'display', 'picture', 'image', 'view'
    ]
    
    TRANSCRIPT_KEYWORDS = [
        'say', 'said', 'speak', 'talk', 'mention', 'audio', 'sound',
        'voice', 'word', 'conversation', 'dialogue', 'discuss', 'tell'
    ]
    
    OBJECT_KEYWORDS = [
        'find', 'locate', 'search', 'detect', 'spot', 'identify',
        'person', 'people', 'car', 'dog', 'cat', 'object', 'thing',
        'all the', 'every', 'count', 'how many'
    ]
    
    # Timestamp patterns
    TIMESTAMP_PATTERNS = [
        r'(\d+):(\d+):(\d+)',  # HH:MM:SS
        r'(\d+):(\d+)',         # MM:SS
        r'at\s+(\d+)\s*(?:seconds?|secs?|s)',  # at X seconds
        r'at\s+(\d+)\s*(?:minutes?|mins?|m)',  # at X minutes
        r'(\d+)\s*(?:seconds?|secs?|s)',       # X seconds
        r'(\d+)\s*(?:minutes?|mins?|m)',       # X minutes
    ]
    
    def __init__(self):
        """Initialize the Tool Router."""
        pass
    
    def analyze_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolPlan:
        """
        Determine which tools to use and in what order based on query content.
        
        ENHANCED: Implements smart query routing:
        - Visual questions → Use captions + objects
        - Audio questions → Use transcripts
        - Temporal questions → Use all data with timestamp filtering
        - General questions → Use comprehensive context
        
        Args:
            query: User's query string
            context: Optional conversation context
            
        Returns:
            ToolPlan with tools needed, execution order, and parameters
        """
        query_lower = query.lower()
        tools_needed = []
        parameters = {}
        
        # Classify query type for smart routing
        query_type = self._classify_query_type(query_lower)
        parameters['query_type'] = query_type
        
        # Extract timestamp if present (affects routing)
        timestamp = self.extract_timestamp(query)
        if timestamp is not None:
            parameters['timestamp'] = timestamp
            parameters['temporal_query'] = True
        
        # Smart routing based on query type
        if query_type == 'visual':
            # Visual questions → Use captions + objects
            tools_needed.append('captions')
            tools_needed.append('objects')
            logger.debug("Visual query detected: using captions + objects")
        
        elif query_type == 'audio':
            # Audio questions → Use transcripts
            tools_needed.append('transcripts')
            logger.debug("Audio query detected: using transcripts")
        
        elif query_type == 'temporal':
            # Temporal questions → Use all data with timestamp filtering
            tools_needed.extend(['captions', 'transcripts', 'objects'])
            logger.debug("Temporal query detected: using all data with timestamp filtering")
        
        elif query_type == 'object_search':
            # Object search → Use objects + captions for context
            tools_needed.append('objects')
            tools_needed.append('captions')
            # Try to extract object name from query
            object_name = self._extract_object_name(query_lower)
            if object_name:
                parameters['object_name'] = object_name
            logger.debug(f"Object search query detected: looking for '{object_name}'")
        
        elif query_type == 'general':
            # General questions → Use comprehensive context
            tools_needed.extend(['captions', 'transcripts', 'objects'])
            logger.debug("General query detected: using comprehensive context")
        
        else:
            # Fallback: use original logic
            if self.requires_captions(query):
                tools_needed.append('captions')
            if self.requires_transcripts(query):
                tools_needed.append('transcripts')
            if self.requires_objects(query):
                tools_needed.append('objects')
                object_name = self._extract_object_name(query_lower)
                if object_name:
                    parameters['object_name'] = object_name
        
        # Remove duplicates while preserving order
        tools_needed = list(dict.fromkeys(tools_needed))
        
        # Determine execution order
        execution_order = self._optimize_execution_order(
            tools_needed,
            parameters
        )
        
        return ToolPlan(
            tools_needed=tools_needed,
            execution_order=execution_order,
            parameters=parameters
        )
    
    def _classify_query_type(self, query_lower: str) -> str:
        """
        Classify query type for smart routing.
        
        Args:
            query_lower: Lowercased query string
            
        Returns:
            Query type: 'visual', 'audio', 'temporal', 'object_search', 'general'
        """
        # Temporal queries (highest priority - most specific)
        if any(pattern in query_lower for pattern in [
            'at ', ':', 'timestamp', 'minute', 'second', 'beginning', 'start', 'end'
        ]):
            # Check if it's a temporal query (not just "see at")
            if self.extract_timestamp(query_lower) is not None:
                return 'temporal'
        
        # Audio queries
        if any(kw in query_lower for kw in self.TRANSCRIPT_KEYWORDS):
            return 'audio'
        
        # Object search queries
        if any(kw in query_lower for kw in ['find', 'locate', 'search', 'show me all', 'how many']):
            # Check if looking for specific objects
            if self._extract_object_name(query_lower):
                return 'object_search'
        
        # Visual queries
        if any(kw in query_lower for kw in self.CAPTION_KEYWORDS):
            return 'visual'
        
        # General queries (summary, overview, etc.)
        if any(kw in query_lower for kw in ['summary', 'summarize', 'overview', 'about', 'what is', 'tell me']):
            return 'general'
        
        # Default to general
        return 'general'
    
    def requires_captions(self, query: str) -> bool:
        """
        Check if query needs image captions.
        
        Args:
            query: User's query string
            
        Returns:
            True if captions are needed
        """
        query_lower = query.lower()
        
        # Check for caption-related keywords
        for keyword in self.CAPTION_KEYWORDS:
            if keyword in query_lower:
                return True
        
        # Check for visual description requests
        if any(phrase in query_lower for phrase in [
            'what is', 'what are', 'what\'s', 'describe',
            'show me', 'can you see', 'is there'
        ]):
            # If not explicitly about audio, assume visual
            if not self.requires_transcripts(query):
                return True
        
        return False
    
    def requires_transcripts(self, query: str) -> bool:
        """
        Check if query needs audio transcripts.
        
        Args:
            query: User's query string
            
        Returns:
            True if transcripts are needed
        """
        query_lower = query.lower()
        
        # Check for transcript-related keywords
        for keyword in self.TRANSCRIPT_KEYWORDS:
            if keyword in query_lower:
                return True
        
        return False
    
    def requires_objects(self, query: str) -> bool:
        """
        Check if query needs object detection.
        
        Args:
            query: User's query string
            
        Returns:
            True if object detection is needed
        """
        query_lower = query.lower()
        
        # Check for object-related keywords
        for keyword in self.OBJECT_KEYWORDS:
            if keyword in query_lower:
                return True
        
        # Check for counting or finding specific items
        if any(phrase in query_lower for phrase in [
            'how many', 'count', 'find all', 'show all',
            'every time', 'all the'
        ]):
            return True
        
        return False
    
    def extract_timestamp(self, query: str) -> Optional[float]:
        """
        Extract timestamp from query if present.
        
        Args:
            query: User's query string
            
        Returns:
            Timestamp in seconds, or None if not found
        """
        query_lower = query.lower()
        
        # Try each timestamp pattern
        for pattern in self.TIMESTAMP_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                groups = match.groups()
                
                # Handle HH:MM:SS format
                if len(groups) == 3:
                    hours, minutes, seconds = map(int, groups)
                    return hours * 3600 + minutes * 60 + seconds
                
                # Handle MM:SS format
                elif len(groups) == 2 and ':' in match.group(0):
                    minutes, seconds = map(int, groups)
                    return minutes * 60 + seconds
                
                # Handle "at X seconds/minutes" format
                elif len(groups) == 1:
                    value = int(groups[0])
                    if 'minute' in match.group(0) or 'm' in match.group(0):
                        return value * 60
                    else:
                        return float(value)
        
        # Check for relative time references
        if 'beginning' in query_lower or 'start' in query_lower:
            return 0.0
        
        return None
    
    def _extract_object_name(self, query_lower: str) -> Optional[str]:
        """
        Extract object name from query for object detection.
        
        Args:
            query_lower: Lowercased query string
            
        Returns:
            Object name if found, None otherwise
        """
        # Common object patterns - ordered by specificity
        # Use more specific patterns that skip filler words
        object_patterns = [
            r'(?:how many|count)\s+(\w+)',
            r'(?:is there|are there)\s+(?:a|an|any)\s+(\w+)',
            r'scenes?\s+with\s+(?:a|an|the)?\s*(\w+)',
            r'(?:show|find)\s+me\s+all\s+(?:the\s+)?(\w+)',  # "show me all the dogs"
            r'(?:show|find)\s+all\s+(?:the\s+)?(\w+)',       # "show all the dogs"
            r'(?:find|locate|detect)\s+(?:the\s+)?(\w+)',    # "find the car"
        ]
        
        for pattern in object_patterns:
            match = re.search(pattern, query_lower)
            if match:
                object_name = match.group(1)
                # Filter out common words that aren't objects
                stop_words = ['the', 'a', 'an', 'this', 'that', 'these', 'those', 
                             'me', 'all', 'some', 'any', 'every', 'each', 'video']
                if object_name not in stop_words:
                    return object_name
        
        return None
    
    def _optimize_execution_order(
        self,
        tools_needed: List[str],
        parameters: Dict[str, Any]
    ) -> List[str]:
        """
        Optimize tool execution order based on dependencies and efficiency.
        
        Args:
            tools_needed: List of tools that need to be executed
            parameters: Query parameters
            
        Returns:
            Optimized execution order
        """
        if not tools_needed:
            return []
        
        # If timestamp is specified, prioritize temporal context
        if parameters.get('temporal_query'):
            # For temporal queries, get transcripts first (fastest),
            # then captions, then objects
            order = []
            if 'transcripts' in tools_needed:
                order.append('transcripts')
            if 'captions' in tools_needed:
                order.append('captions')
            if 'objects' in tools_needed:
                order.append('objects')
            return order
        
        # Default order: transcripts (fastest) -> captions -> objects (slowest)
        # This allows for early results while heavier processing continues
        order = []
        if 'transcripts' in tools_needed:
            order.append('transcripts')
        if 'captions' in tools_needed:
            order.append('captions')
        if 'objects' in tools_needed:
            order.append('objects')
        
        return order
