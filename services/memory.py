"""Memory Manager for conversation history storage and retrieval."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional
from models.memory import MemoryRecord
from storage.database import Database, DatabaseError
from config import Config

logger = logging.getLogger(__name__)


class MemoryError(Exception):
    """Custom exception for memory-related errors."""
    pass


class Memory:
    """Memory Manager for storing and retrieving conversation history.
    
    Manages conversation history in SQLite database with support for:
    - Inserting new conversation turns
    - Retrieving conversation history with limits
    - Resetting (wiping) conversation history per video
    - Performance-optimized queries with indexing
    """
    
    def __init__(self, db: Optional[Database] = None):
        """Initialize Memory Manager.
        
        Args:
            db: Database instance. Creates new instance if not provided.
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("Memory Manager initialized")
    
    def insert(self, memory_record: MemoryRecord) -> None:
        """Store a conversation turn in memory.
        
        Args:
            memory_record: MemoryRecord containing message details
            
        Raises:
            MemoryError: If insertion fails
            
        Example:
            memory.insert(MemoryRecord(
                message_id="msg_123",
                video_id="vid_456",
                role="user",
                content="What's happening in this video?"
            ))
        """
        try:
            query = """
                INSERT INTO memory (message_id, video_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """
            parameters = (
                memory_record.message_id,
                memory_record.video_id,
                memory_record.role,
                memory_record.content,
                memory_record.timestamp.isoformat()
            )
            
            self.db.execute_update(query, parameters)
            logger.debug(f"Inserted memory record: {memory_record.message_id} for video {memory_record.video_id}")
            
        except DatabaseError as e:
            logger.error(f"Failed to insert memory record: {e}")
            raise MemoryError(f"Failed to store conversation turn: {e}")
    
    def get_conversation_history(
        self,
        video_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[MemoryRecord]:
        """Retrieve conversation history for a video with pagination support.
        
        Args:
            video_id: Video identifier
            limit: Maximum number of messages to retrieve (most recent first).
                   Uses Config.MAX_CONVERSATION_HISTORY if not provided.
            offset: Number of messages to skip (for pagination)
            
        Returns:
            List of MemoryRecord objects in chronological order (oldest first)
            
        Raises:
            MemoryError: If retrieval fails
            
        Example:
            # Get first page (most recent 10 messages)
            history = memory.get_conversation_history("vid_456", limit=10)
            
            # Get second page (next 10 messages)
            history_page2 = memory.get_conversation_history("vid_456", limit=10, offset=10)
        """
        try:
            if limit is None:
                limit = Config.MAX_CONVERSATION_HISTORY
            
            # Query retrieves most recent messages with pagination support
            # Uses index on (video_id, timestamp DESC) for performance
            query = """
                SELECT message_id, video_id, role, content, timestamp
                FROM memory
                WHERE video_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            parameters = (video_id, limit, offset)
            
            rows = self.db.execute_query(query, parameters)
            
            # Convert rows to MemoryRecord objects and reverse to chronological order
            memory_records = []
            for row in reversed(rows):
                memory_records.append(MemoryRecord(
                    message_id=row['message_id'],
                    video_id=row['video_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                ))
            
            logger.debug(f"Retrieved {len(memory_records)} memory records for video {video_id} (offset: {offset})")
            return memory_records
            
        except DatabaseError as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            raise MemoryError(f"Failed to retrieve conversation history: {e}")
    
    def get_by_message_id(self, message_id: str) -> Optional[MemoryRecord]:
        """Retrieve a specific message by ID.
        
        Args:
            message_id: Unique message identifier
            
        Returns:
            MemoryRecord if found, None otherwise
            
        Raises:
            MemoryError: If retrieval fails
        """
        try:
            query = """
                SELECT message_id, video_id, role, content, timestamp
                FROM memory
                WHERE message_id = ?
            """
            parameters = (message_id,)
            
            rows = self.db.execute_query(query, parameters)
            
            if not rows:
                return None
            
            row = rows[0]
            return MemoryRecord(
                message_id=row['message_id'],
                video_id=row['video_id'],
                role=row['role'],
                content=row['content'],
                timestamp=datetime.fromisoformat(row['timestamp'])
            )
            
        except DatabaseError as e:
            logger.error(f"Failed to retrieve message {message_id}: {e}")
            raise MemoryError(f"Failed to retrieve message: {e}")
    
    def reset_memory(self, video_id: str) -> int:
        """Clear all conversation history for a video (memory wipe).
        
        Args:
            video_id: Video identifier
            
        Returns:
            Number of deleted records
            
        Raises:
            MemoryError: If deletion fails
            
        Example:
            deleted_count = memory.reset_memory("vid_456")
            print(f"Deleted {deleted_count} messages")
        """
        try:
            query = """
                DELETE FROM memory
                WHERE video_id = ?
            """
            parameters = (video_id,)
            
            deleted_count = self.db.execute_update(query, parameters)
            logger.info(f"Reset memory for video {video_id}: deleted {deleted_count} records")
            return deleted_count
            
        except DatabaseError as e:
            logger.error(f"Failed to reset memory for video {video_id}: {e}")
            raise MemoryError(f"Failed to reset conversation history: {e}")
    
    def count_messages(self, video_id: str) -> int:
        """Count total messages for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Number of messages
            
        Raises:
            MemoryError: If count fails
        """
        try:
            query = """
                SELECT COUNT(*) as count
                FROM memory
                WHERE video_id = ?
            """
            parameters = (video_id,)
            
            rows = self.db.execute_query(query, parameters)
            return rows[0]['count'] if rows else 0
            
        except DatabaseError as e:
            logger.error(f"Failed to count messages for video {video_id}: {e}")
            raise MemoryError(f"Failed to count messages: {e}")
    
    def add_memory_pair(
        self,
        video_id: str,
        user_message: str,
        assistant_message: str
    ) -> tuple[str, str]:
        """Convenience method to add a user-assistant message pair.
        
        Args:
            video_id: Video identifier
            user_message: User's message content
            assistant_message: Assistant's response content
            
        Returns:
            Tuple of (user_message_id, assistant_message_id)
            
        Raises:
            MemoryError: If insertion fails
            
        Example:
            user_id, assistant_id = memory.add_memory_pair(
                "vid_456",
                "What's happening at 1:30?",
                "At 1:30, there's a person walking a dog in the park."
            )
        """
        try:
            user_id = f"msg_{uuid.uuid4().hex[:16]}"
            assistant_id = f"msg_{uuid.uuid4().hex[:16]}"
            
            # Insert user message
            self.insert(MemoryRecord(
                message_id=user_id,
                video_id=video_id,
                role="user",
                content=user_message,
                timestamp=datetime.now()
            ))
            
            # Insert assistant message
            self.insert(MemoryRecord(
                message_id=assistant_id,
                video_id=video_id,
                role="assistant",
                content=assistant_message,
                timestamp=datetime.now()
            ))
            
            logger.debug(f"Added memory pair for video {video_id}")
            return user_id, assistant_id
            
        except MemoryError as e:
            logger.error(f"Failed to add memory pair: {e}")
            raise
    
    def get_recent_context(
        self,
        video_id: str,
        max_messages: int = 6
    ) -> str:
        """Get recent conversation history formatted as context string.
        
        Args:
            video_id: Video identifier
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation history string
            
        Example:
            context = memory.get_recent_context("vid_456", max_messages=4)
            # Returns: "User: What's in the video?\nAssistant: I see a park scene..."
        """
        try:
            history = self.get_conversation_history(video_id, limit=max_messages)
            
            if not history:
                return ""
            
            context_lines = []
            for record in history:
                role_label = "User" if record.role == "user" else "Assistant"
                context_lines.append(f"{role_label}: {record.content}")
            
            return "\n".join(context_lines)
            
        except MemoryError as e:
            logger.warning(f"Failed to get recent context: {e}")
            return ""
    
    def close(self) -> None:
        """Close database connection."""
        if self.db:
            self.db.close()
            logger.info("Memory Manager closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
