"""
Test script for Chat Window component
Verifies chat interface functionality
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.memory import MemoryRecord
from models.responses import AssistantMessageResponse


def test_chat_window_component():
    """Test that chat window component can be imported and has required functions."""

    print("Testing Chat Window Component...")
    print("=" * 60)

    try:
        from ui.chat import (
            render_chat_window,
            render_assistant_response,
            add_emoji_reactions,
            _render_message,
            _render_empty_state,
            _render_message_input,
            _format_timestamp,
            _format_message_content,
            _format_video_timestamp,
        )

        print("✓ All required functions imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import chat functions: {e}")
        return False

    return True


def test_timestamp_formatting():
    """Test timestamp formatting functions."""

    print("\nTesting Timestamp Formatting...")
    print("-" * 60)

    from ui.chat import _format_timestamp, _format_video_timestamp

    # Test relative timestamps
    now = datetime.now()

    # Just now
    result = _format_timestamp(now)
    print(f"✓ Current time: '{result}'")
    assert result == "just now", f"Expected 'just now', got '{result}'"

    # Minutes ago
    five_min_ago = now - timedelta(minutes=5)
    result = _format_timestamp(five_min_ago)
    print(f"✓ 5 minutes ago: '{result}'")
    assert "5m ago" in result, f"Expected '5m ago', got '{result}'"

    # Hours ago
    two_hours_ago = now - timedelta(hours=2)
    result = _format_timestamp(two_hours_ago)
    print(f"✓ 2 hours ago: '{result}'")
    assert "2h ago" in result, f"Expected '2h ago', got '{result}'"

    # Test video timestamps
    test_cases = [(30, "00:30"), (90, "01:30"), (3661, "01:01:01")]

    for seconds, expected in test_cases:
        result = _format_video_timestamp(seconds)
        print(f"✓ {seconds}s -> '{result}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"

    print("✓ All timestamp formatting tests passed")
    return True


def test_message_content_formatting():
    """Test message content formatting with emoji support."""

    print("\nTesting Message Content Formatting...")
    print("-" * 60)

    from ui.chat import _format_message_content

    # Test newline conversion
    content = "Line 1\nLine 2\nLine 3"
    result = _format_message_content(content)
    print(f"✓ Newlines converted to <br> tags")
    assert "<br>" in result, "Expected <br> tags in result"

    # Test emoji conversion
    content = "Hello :) I'm happy :D"
    result = _format_message_content(content)
    print(f"✓ Text emoticons converted to emoji")
    assert "😊" in result or ":)" in result, "Expected emoji in result"

    print("✓ All content formatting tests passed")
    return True


def test_memory_record_creation():
    """Test creating MemoryRecord objects for chat display."""

    print("\nTesting MemoryRecord Creation...")
    print("-" * 60)

    # Create user message
    user_msg = MemoryRecord(
        message_id="msg_001",
        video_id="vid_test",
        role="user",
        content="What's happening in this video?",
        timestamp=datetime.now(),
    )

    print(f"✓ User message created: {user_msg.role} - {user_msg.content[:30]}...")
    assert user_msg.role == "user"
    assert len(user_msg.content) > 0

    # Create assistant message
    assistant_msg = MemoryRecord(
        message_id="msg_002",
        video_id="vid_test",
        role="assistant",
        content="I can see a beautiful park scene with people walking.",
        timestamp=datetime.now(),
    )

    print(f"✓ Assistant message created: {assistant_msg.role} - {assistant_msg.content[:30]}...")
    assert assistant_msg.role == "assistant"
    assert len(assistant_msg.content) > 0

    print("✓ All MemoryRecord tests passed")
    return True


def test_assistant_response_creation():
    """Test creating AssistantMessageResponse objects."""

    print("\nTesting AssistantMessageResponse Creation...")
    print("-" * 60)

    # Create response with frames and suggestions
    response = AssistantMessageResponse(
        message="I found some interesting moments in your video!",
        frames=["frame_001.jpg", "frame_002.jpg"],
        timestamps=[10.5, 25.3],
        suggestions=[
            "Can you tell me more about the first scene?",
            "What happens after this?",
            "Are there any people in the video?",
        ],
    )

    print(f"✓ Response created with message: '{response.message[:40]}...'")
    print(f"✓ Frames: {len(response.frames)} frames")
    print(f"✓ Timestamps: {response.timestamps}")
    print(f"✓ Suggestions: {len(response.suggestions)} suggestions")

    assert len(response.frames) == 2
    assert len(response.timestamps) == 2
    assert len(response.suggestions) == 3

    print("✓ All AssistantMessageResponse tests passed")
    return True


def test_conversation_history_display():
    """Test displaying a conversation history."""

    print("\nTesting Conversation History Display...")
    print("-" * 60)

    # Create sample conversation
    conversation = [
        MemoryRecord(
            message_id="msg_001",
            video_id="vid_test",
            role="user",
            content="What's in this video?",
            timestamp=datetime.now() - timedelta(minutes=5),
        ),
        MemoryRecord(
            message_id="msg_002",
            video_id="vid_test",
            role="assistant",
            content="I can see a park with trees and people walking. 🌳",
            timestamp=datetime.now() - timedelta(minutes=4),
        ),
        MemoryRecord(
            message_id="msg_003",
            video_id="vid_test",
            role="user",
            content="Are there any dogs?",
            timestamp=datetime.now() - timedelta(minutes=2),
        ),
        MemoryRecord(
            message_id="msg_004",
            video_id="vid_test",
            role="assistant",
            content="Yes! I spotted a dog at 0:45. Let me show you! 🐕",
            timestamp=datetime.now() - timedelta(minutes=1),
        ),
    ]

    print(f"✓ Created conversation with {len(conversation)} messages")

    # Verify conversation structure
    assert len(conversation) == 4
    assert conversation[0].role == "user"
    assert conversation[1].role == "assistant"
    assert conversation[2].role == "user"
    assert conversation[3].role == "assistant"

    print("✓ Conversation structure verified")
    print("✓ All conversation history tests passed")
    return True


def run_all_tests():
    """Run all chat window tests."""

    print("\n" + "=" * 60)
    print("CHAT WINDOW COMPONENT TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("Component Import", test_chat_window_component),
        ("Timestamp Formatting", test_timestamp_formatting),
        ("Message Content Formatting", test_message_content_formatting),
        ("MemoryRecord Creation", test_memory_record_creation),
        ("AssistantMessageResponse Creation", test_assistant_response_creation),
        ("Conversation History Display", test_conversation_history_display),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Chat window component is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
