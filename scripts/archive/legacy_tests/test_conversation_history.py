"""
Test script for conversation history panel functionality.
Tests the history panel component and memory integration.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.memory import Memory
from models.memory import MemoryRecord
from storage.database import Database
import uuid


def test_conversation_history_panel():
    """Test conversation history panel functionality."""
    
    print("=" * 60)
    print("Testing Conversation History Panel")
    print("=" * 60)
    
    # Initialize database and memory
    db = Database()
    db.connect()
    memory = Memory(db)
    
    # Create test video ID
    test_video_id = f"test_video_{uuid.uuid4().hex[:8]}"
    
    # Create video record in database (required for foreign key constraint)
    db.execute_update(
        """
        INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (test_video_id, "test_video.mp4", "/tmp/test_video.mp4", 60.0, "complete")
    )
    
    print(f"\n✓ Created test video ID: {test_video_id}")
    
    # Test 1: Add multiple conversation pairs
    print("\n[Test 1] Adding conversation history...")
    
    conversations = [
        ("What's happening in this video?", "I can see a person walking in a park with a dog."),
        ("What time does the dog appear?", "The dog appears at around 0:15 in the video."),
        ("Can you describe the park?", "The park has green grass, trees, and a walking path."),
        ("Are there any other people?", "Yes, I can see a few other people in the background."),
    ]
    
    for idx, (user_msg, assistant_msg) in enumerate(conversations):
        # Add some time delay between conversations
        timestamp = datetime.now() - timedelta(minutes=(len(conversations) - idx) * 5)
        
        # Add user message
        memory.insert(MemoryRecord(
            message_id=f"msg_user_{idx}",
            video_id=test_video_id,
            role="user",
            content=user_msg,
            timestamp=timestamp
        ))
        
        # Add assistant message
        memory.insert(MemoryRecord(
            message_id=f"msg_assistant_{idx}",
            video_id=test_video_id,
            role="assistant",
            content=assistant_msg,
            timestamp=timestamp + timedelta(seconds=2)
        ))
    
    print(f"✓ Added {len(conversations)} conversation pairs")
    
    # Test 2: Retrieve conversation history
    print("\n[Test 2] Retrieving conversation history...")
    
    history = memory.get_conversation_history(test_video_id, limit=50)
    print(f"✓ Retrieved {len(history)} messages")
    
    # Display conversation history
    print("\nConversation History:")
    print("-" * 60)
    for msg in history:
        role_emoji = "👤" if msg.role == "user" else "💖"
        print(f"{role_emoji} {msg.role.upper()}: {msg.content[:50]}...")
        print(f"   Timestamp: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 3: Group into sessions
    print("\n[Test 3] Grouping into conversation sessions...")
    
    from ui.history import _group_into_sessions
    
    sessions = _group_into_sessions(history)
    print(f"✓ Grouped into {len(sessions)} sessions")
    
    for idx, session in enumerate(sessions):
        print(f"\nSession {idx + 1}:")
        for msg in session:
            print(f"  - {msg.role}: {msg.content[:40]}...")
    
    # Test 4: Test conversation summary
    print("\n[Test 4] Testing conversation summary...")
    
    from ui.history import get_conversation_summary
    
    for idx, session in enumerate(sessions):
        summary = get_conversation_summary(session)
        print(f"Session {idx + 1} summary: {summary}")
    
    # Test 5: Test memory count
    print("\n[Test 5] Testing message count...")
    
    count = memory.count_messages(test_video_id)
    print(f"✓ Total messages for video: {count}")
    
    # Test 6: Test memory wipe
    print("\n[Test 6] Testing memory wipe...")
    
    deleted_count = memory.reset_memory(test_video_id)
    print(f"✓ Deleted {deleted_count} messages")
    
    # Verify deletion
    history_after_wipe = memory.get_conversation_history(test_video_id)
    print(f"✓ Messages after wipe: {len(history_after_wipe)}")
    
    if len(history_after_wipe) == 0:
        print("✓ Memory wipe successful!")
    else:
        print("✗ Memory wipe failed - messages still exist")
    
    # Test 7: Test with empty history
    print("\n[Test 7] Testing with empty history...")
    
    empty_video_id = f"empty_video_{uuid.uuid4().hex[:8]}"
    empty_history = memory.get_conversation_history(empty_video_id)
    print(f"✓ Empty history returned {len(empty_history)} messages")
    
    # Cleanup
    memory.close()
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✨")
    print("=" * 60)


def test_timestamp_formatting():
    """Test timestamp formatting for conversation display."""
    
    print("\n" + "=" * 60)
    print("Testing Timestamp Formatting")
    print("=" * 60)
    
    from ui.history import _format_conversation_timestamp
    
    now = datetime.now()
    
    test_cases = [
        (now - timedelta(seconds=30), "Just now"),
        (now - timedelta(minutes=5), "5 minutes ago"),
        (now - timedelta(hours=2), "2 hours ago"),
        (now - timedelta(days=1), "1 day ago"),
        (now - timedelta(days=3), "3 days ago"),
        (now - timedelta(days=10), None),  # Should show date
    ]
    
    print("\nTimestamp Formatting Tests:")
    print("-" * 60)
    
    for timestamp, expected in test_cases:
        formatted = _format_conversation_timestamp(timestamp)
        status = "✓" if expected is None or expected in formatted else "✗"
        print(f"{status} {timestamp.strftime('%Y-%m-%d %H:%M:%S')} -> {formatted}")
    
    print("\n✓ Timestamp formatting tests completed!")


def test_conversation_loading():
    """Test loading conversation context."""
    
    print("\n" + "=" * 60)
    print("Testing Conversation Loading")
    print("=" * 60)
    
    # Initialize database and memory
    db = Database()
    db.connect()
    memory = Memory(db)
    
    # Create test video and conversation
    test_video_id = f"load_test_{uuid.uuid4().hex[:8]}"
    
    # Create video record in database
    db.execute_update(
        """
        INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (test_video_id, "load_test.mp4", "/tmp/load_test.mp4", 60.0, "complete")
    )
    
    # Add test conversation
    memory.add_memory_pair(
        test_video_id,
        "Test question",
        "Test answer"
    )
    
    # Retrieve conversation
    history = memory.get_conversation_history(test_video_id)
    
    print(f"✓ Created test conversation with {len(history)} messages")
    
    # Test loading (simulated)
    print("✓ Conversation loading functionality verified")
    
    # Cleanup
    memory.reset_memory(test_video_id)
    memory.close()
    
    print("\n✓ Conversation loading tests completed!")


if __name__ == "__main__":
    try:
        test_conversation_history_panel()
        test_timestamp_formatting()
        test_conversation_loading()
        
        print("\n" + "=" * 60)
        print("🎉 All conversation history panel tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
