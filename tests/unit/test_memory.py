"""Unit tests for Memory Manager."""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from models.memory import MemoryRecord
from services.memory import Memory, MemoryError
from storage.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database with schema
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create memory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            message_id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Create videos table (for foreign key reference)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration REAL,
            upload_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            processing_status TEXT DEFAULT 'pending'
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def memory(temp_db):
    """Create Memory instance with temporary database."""
    db = Database(db_path=temp_db)
    mem = Memory(db=db)
    yield mem
    mem.close()


@pytest.fixture
def sample_memory_record():
    """Create a sample memory record for testing."""
    return MemoryRecord(
        message_id="msg_test_001",
        video_id="vid_test_001",
        role="user",
        content="What's happening in this video?",
        timestamp=datetime.now()
    )


class TestMemoryInsert:
    """Tests for Memory.insert() method."""
    
    def test_insert_user_message(self, memory, sample_memory_record):
        """Test inserting a user message."""
        memory.insert(sample_memory_record)
        
        # Verify insertion
        retrieved = memory.get_by_message_id(sample_memory_record.message_id)
        assert retrieved is not None
        assert retrieved.message_id == sample_memory_record.message_id
        assert retrieved.video_id == sample_memory_record.video_id
        assert retrieved.role == sample_memory_record.role
        assert retrieved.content == sample_memory_record.content
    
    def test_insert_assistant_message(self, memory):
        """Test inserting an assistant message."""
        record = MemoryRecord(
            message_id="msg_test_002",
            video_id="vid_test_001",
            role="assistant",
            content="I can see a person walking in the park.",
            timestamp=datetime.now()
        )
        
        memory.insert(record)
        
        # Verify insertion
        retrieved = memory.get_by_message_id(record.message_id)
        assert retrieved is not None
        assert retrieved.role == "assistant"
        assert retrieved.content == record.content
    
    def test_insert_multiple_messages(self, memory):
        """Test inserting multiple messages."""
        records = [
            MemoryRecord(
                message_id=f"msg_test_{i:03d}",
                video_id="vid_test_001",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            for i in range(5)
        ]
        
        for record in records:
            memory.insert(record)
        
        # Verify all inserted
        count = memory.count_messages("vid_test_001")
        assert count == 5
    
    def test_insert_duplicate_message_id_fails(self, memory, sample_memory_record):
        """Test that inserting duplicate message_id raises error."""
        memory.insert(sample_memory_record)
        
        # Try to insert again with same message_id
        with pytest.raises(MemoryError):
            memory.insert(sample_memory_record)


class TestMemoryRetrieval:
    """Tests for Memory.get_conversation_history() method."""
    
    def test_retrieve_empty_history(self, memory):
        """Test retrieving history for video with no messages."""
        history = memory.get_conversation_history("vid_nonexistent")
        assert history == []
    
    def test_retrieve_conversation_history(self, memory):
        """Test retrieving conversation history in chronological order."""
        # Insert messages with different timestamps
        records = [
            MemoryRecord(
                message_id=f"msg_{i}",
                video_id="vid_001",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            for i in range(5)
        ]
        
        for record in records:
            memory.insert(record)
        
        # Retrieve history
        history = memory.get_conversation_history("vid_001")
        
        # Verify chronological order (oldest first)
        assert len(history) == 5
        for i, record in enumerate(history):
            assert record.message_id == f"msg_{i}"
            assert record.content == f"Message {i}"
    
    def test_retrieve_with_limit(self, memory):
        """Test retrieving conversation history with limit."""
        # Insert 10 messages
        for i in range(10):
            memory.insert(MemoryRecord(
                message_id=f"msg_{i}",
                video_id="vid_001",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now() + timedelta(seconds=i)
            ))
        
        # Retrieve with limit of 5 (should get most recent 5)
        history = memory.get_conversation_history("vid_001", limit=5)
        
        assert len(history) == 5
        # Should get messages 5-9 (most recent) in chronological order
        assert history[0].message_id == "msg_5"
        assert history[-1].message_id == "msg_9"
    
    def test_retrieve_with_offset(self, memory):
        """Test retrieving conversation history with pagination."""
        # Insert 10 messages
        for i in range(10):
            memory.insert(MemoryRecord(
                message_id=f"msg_{i}",
                video_id="vid_001",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now() + timedelta(seconds=i)
            ))
        
        # Get first page (most recent 5)
        page1 = memory.get_conversation_history("vid_001", limit=5, offset=0)
        assert len(page1) == 5
        assert page1[0].message_id == "msg_5"
        
        # Get second page (next 5)
        page2 = memory.get_conversation_history("vid_001", limit=5, offset=5)
        assert len(page2) == 5
        assert page2[0].message_id == "msg_0"
    
    def test_retrieve_separate_video_contexts(self, memory):
        """Test that conversation histories are separate per video."""
        # Insert messages for video 1
        for i in range(3):
            memory.insert(MemoryRecord(
                message_id=f"msg_v1_{i}",
                video_id="vid_001",
                role="user",
                content=f"Video 1 Message {i}",
                timestamp=datetime.now()
            ))
        
        # Insert messages for video 2
        for i in range(2):
            memory.insert(MemoryRecord(
                message_id=f"msg_v2_{i}",
                video_id="vid_002",
                role="user",
                content=f"Video 2 Message {i}",
                timestamp=datetime.now()
            ))
        
        # Verify separate histories
        history1 = memory.get_conversation_history("vid_001")
        history2 = memory.get_conversation_history("vid_002")
        
        assert len(history1) == 3
        assert len(history2) == 2
        assert all("Video 1" in r.content for r in history1)
        assert all("Video 2" in r.content for r in history2)


class TestMemoryReset:
    """Tests for Memory.reset_memory() method."""
    
    def test_reset_memory_deletes_all_messages(self, memory):
        """Test that reset_memory deletes all messages for a video."""
        # Insert messages
        for i in range(5):
            memory.insert(MemoryRecord(
                message_id=f"msg_{i}",
                video_id="vid_001",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now()
            ))
        
        # Verify messages exist
        assert memory.count_messages("vid_001") == 5
        
        # Reset memory
        deleted_count = memory.reset_memory("vid_001")
        
        # Verify deletion
        assert deleted_count == 5
        assert memory.count_messages("vid_001") == 0
        history = memory.get_conversation_history("vid_001")
        assert history == []
    
    def test_reset_memory_only_affects_target_video(self, memory):
        """Test that reset_memory only deletes messages for specified video."""
        # Insert messages for video 1
        for i in range(3):
            memory.insert(MemoryRecord(
                message_id=f"msg_v1_{i}",
                video_id="vid_001",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now()
            ))
        
        # Insert messages for video 2
        for i in range(2):
            memory.insert(MemoryRecord(
                message_id=f"msg_v2_{i}",
                video_id="vid_002",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now()
            ))
        
        # Reset video 1
        memory.reset_memory("vid_001")
        
        # Verify video 1 is empty, video 2 is intact
        assert memory.count_messages("vid_001") == 0
        assert memory.count_messages("vid_002") == 2
    
    def test_reset_nonexistent_video(self, memory):
        """Test resetting memory for video with no messages."""
        deleted_count = memory.reset_memory("vid_nonexistent")
        assert deleted_count == 0


class TestMemoryHelperMethods:
    """Tests for helper methods in Memory class."""
    
    def test_get_by_message_id(self, memory, sample_memory_record):
        """Test retrieving specific message by ID."""
        memory.insert(sample_memory_record)
        
        retrieved = memory.get_by_message_id(sample_memory_record.message_id)
        
        assert retrieved is not None
        assert retrieved.message_id == sample_memory_record.message_id
        assert retrieved.content == sample_memory_record.content
    
    def test_get_by_message_id_nonexistent(self, memory):
        """Test retrieving nonexistent message returns None."""
        retrieved = memory.get_by_message_id("msg_nonexistent")
        assert retrieved is None
    
    def test_count_messages(self, memory):
        """Test counting messages for a video."""
        # Insert messages
        for i in range(7):
            memory.insert(MemoryRecord(
                message_id=f"msg_{i}",
                video_id="vid_001",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now()
            ))
        
        count = memory.count_messages("vid_001")
        assert count == 7
    
    def test_count_messages_empty_video(self, memory):
        """Test counting messages for video with no messages."""
        count = memory.count_messages("vid_nonexistent")
        assert count == 0
    
    def test_add_memory_pair(self, memory):
        """Test convenience method for adding user-assistant pair."""
        user_id, assistant_id = memory.add_memory_pair(
            video_id="vid_001",
            user_message="What's in the video?",
            assistant_message="I see a park scene."
        )
        
        # Verify both messages were inserted
        assert memory.count_messages("vid_001") == 2
        
        user_msg = memory.get_by_message_id(user_id)
        assistant_msg = memory.get_by_message_id(assistant_id)
        
        assert user_msg.role == "user"
        assert user_msg.content == "What's in the video?"
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "I see a park scene."
    
    def test_get_recent_context(self, memory):
        """Test getting recent conversation as formatted string."""
        # Add conversation pairs
        memory.add_memory_pair(
            "vid_001",
            "What's happening?",
            "I see a person walking."
        )
        memory.add_memory_pair(
            "vid_001",
            "What are they wearing?",
            "They're wearing a blue jacket."
        )
        
        context = memory.get_recent_context("vid_001", max_messages=4)
        
        assert "User: What's happening?" in context
        assert "Assistant: I see a person walking." in context
        assert "User: What are they wearing?" in context
        assert "Assistant: They're wearing a blue jacket." in context
    
    def test_get_recent_context_empty(self, memory):
        """Test getting recent context for video with no messages."""
        context = memory.get_recent_context("vid_nonexistent")
        assert context == ""
    
    def test_get_recent_context_with_limit(self, memory):
        """Test getting recent context respects max_messages limit."""
        # Add 3 pairs (6 messages)
        for i in range(3):
            memory.add_memory_pair(
                "vid_001",
                f"Question {i}",
                f"Answer {i}"
            )
        
        # Get only 2 most recent messages
        context = memory.get_recent_context("vid_001", max_messages=2)
        
        # Should only contain the last pair
        assert "Question 2" in context
        assert "Answer 2" in context
        assert "Question 0" not in context


class TestMemoryContextManager:
    """Tests for Memory context manager functionality."""
    
    def test_context_manager(self, temp_db):
        """Test using Memory as context manager."""
        db = Database(db_path=temp_db)
        
        with Memory(db=db) as mem:
            mem.insert(MemoryRecord(
                message_id="msg_001",
                video_id="vid_001",
                role="user",
                content="Test message",
                timestamp=datetime.now()
            ))
            
            count = mem.count_messages("vid_001")
            assert count == 1
        
        # Verify connection is closed after context
        # (Memory should still work if we create a new instance)
        db2 = Database(db_path=temp_db)
        mem2 = Memory(db=db2)
        count = mem2.count_messages("vid_001")
        assert count == 1
        mem2.close()


class TestMemoryEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_insert_with_special_characters(self, memory):
        """Test inserting messages with special characters."""
        record = MemoryRecord(
            message_id="msg_special",
            video_id="vid_001",
            role="user",
            content="What's happening at 1:30? Show me the \"scene\" with <tags>!",
            timestamp=datetime.now()
        )
        
        memory.insert(record)
        retrieved = memory.get_by_message_id("msg_special")
        
        assert retrieved.content == record.content
    
    def test_insert_with_very_long_content(self, memory):
        """Test inserting message with very long content."""
        long_content = "A" * 10000  # 10k characters
        
        record = MemoryRecord(
            message_id="msg_long",
            video_id="vid_001",
            role="user",
            content=long_content,
            timestamp=datetime.now()
        )
        
        memory.insert(record)
        retrieved = memory.get_by_message_id("msg_long")
        
        assert len(retrieved.content) == 10000
    
    def test_insert_with_unicode_content(self, memory):
        """Test inserting messages with unicode characters."""
        record = MemoryRecord(
            message_id="msg_unicode",
            video_id="vid_001",
            role="user",
            content="こんにちは 🎉 Привет مرحبا",
            timestamp=datetime.now()
        )
        
        memory.insert(record)
        retrieved = memory.get_by_message_id("msg_unicode")
        
        assert retrieved.content == record.content
    
    def test_timestamp_ordering_with_same_second(self, memory):
        """Test that messages with very close timestamps maintain order."""
        base_time = datetime.now()
        
        # Insert messages with microsecond differences
        for i in range(5):
            memory.insert(MemoryRecord(
                message_id=f"msg_{i}",
                video_id="vid_001",
                role="user",
                content=f"Message {i}",
                timestamp=base_time + timedelta(microseconds=i)
            ))
        
        history = memory.get_conversation_history("vid_001")
        
        # Verify order is maintained
        for i, record in enumerate(history):
            assert record.message_id == f"msg_{i}"
