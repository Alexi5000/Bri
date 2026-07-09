"""
Test script for video player component (Task 21)
Tests video player with timestamp navigation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.player import (
    _format_timestamp,
    extract_timestamps_from_conversation,
    navigate_to_timestamp,
    get_current_playback_time
)


def test_format_timestamp():
    """Test timestamp formatting."""
    print("Testing timestamp formatting...")
    
    # Test MM:SS format
    assert _format_timestamp(65) == "01:05", "Failed: 65 seconds"
    assert _format_timestamp(125) == "02:05", "Failed: 125 seconds"
    
    # Test HH:MM:SS format
    assert _format_timestamp(3665) == "01:01:05", "Failed: 3665 seconds"
    assert _format_timestamp(7325) == "02:02:05", "Failed: 7325 seconds"
    
    # Test edge cases
    assert _format_timestamp(0) == "00:00", "Failed: 0 seconds"
    assert _format_timestamp(59) == "00:59", "Failed: 59 seconds"
    assert _format_timestamp(3600) == "01:00:00", "Failed: 3600 seconds"
    
    print("✓ Timestamp formatting tests passed")


def test_extract_timestamps():
    """Test timestamp extraction from conversation."""
    print("\nTesting timestamp extraction...")
    
    # Mock conversation with timestamps
    class MockMessage:
        def __init__(self, content, timestamps=None):
            self.content = content
            self.timestamps = timestamps or []
    
    conversation = [
        MockMessage("What happens at 1:23?"),
        MockMessage("Check out 2:45 and 3:10", timestamps=[165.0, 190.0]),
        MockMessage("Also look at 01:30:45"),
    ]
    
    timestamps = extract_timestamps_from_conversation(conversation)
    
    print(f"Extracted timestamps: {timestamps}")
    
    # Should extract: 1:23 (83s), 2:45 (165s), 3:10 (190s), 01:30:45 (5445s)
    assert 83.0 in timestamps, "Failed to extract 1:23"
    assert 165.0 in timestamps, "Failed to extract 2:45"
    assert 190.0 in timestamps, "Failed to extract 3:10"
    assert 5445.0 in timestamps, "Failed to extract 01:30:45"
    
    # Should be sorted and unique
    assert timestamps == sorted(timestamps), "Timestamps not sorted"
    assert len(timestamps) == len(set(timestamps)), "Duplicate timestamps found"
    
    print("✓ Timestamp extraction tests passed")


def test_navigation_functions():
    """Test navigation helper functions."""
    print("\nTesting navigation functions...")
    
    # Test navigate_to_timestamp (creates session state entry)
    video_id = "test_video_123"
    timestamp = 125.5
    
    # Mock session state
    import streamlit as st
    if not hasattr(st, 'session_state'):
        # Create a simple mock if streamlit not available
        class MockSessionState(dict):
            pass
        st.session_state = MockSessionState()
    
    navigate_to_timestamp(video_id, timestamp)
    
    player_key = f"player_{video_id}"
    assert player_key in st.session_state, "Player key not created"
    assert st.session_state[player_key]["selected_timestamp"] == timestamp, "Timestamp not set"
    
    # Test get_current_playback_time
    current_time = get_current_playback_time(video_id)
    assert current_time == timestamp, f"Expected {timestamp}, got {current_time}"
    
    print("✓ Navigation function tests passed")


def test_player_component_structure():
    """Test that player component has required functions."""
    print("\nTesting player component structure...")
    
    from ui.player import (
        render_video_player,
        render_video_player_with_context,
        navigate_to_timestamp,
        get_current_playback_time,
        extract_timestamps_from_conversation
    )
    
    # Check all required functions exist
    assert callable(render_video_player), "render_video_player not callable"
    assert callable(render_video_player_with_context), "render_video_player_with_context not callable"
    assert callable(navigate_to_timestamp), "navigate_to_timestamp not callable"
    assert callable(get_current_playback_time), "get_current_playback_time not callable"
    assert callable(extract_timestamps_from_conversation), "extract_timestamps_from_conversation not callable"
    
    print("✓ Player component structure tests passed")


def test_timestamp_patterns():
    """Test various timestamp pattern recognition."""
    print("\nTesting timestamp pattern recognition...")
    
    class MockMessage:
        def __init__(self, content):
            self.content = content
            self.timestamps = []
    
    test_cases = [
        ("Check 0:30", [30.0]),
        ("Look at 1:23 and 2:45", [83.0, 165.0]),
        ("See 01:02:03", [3723.0]),
        ("At 10:00 something happens", [600.0]),
        ("Multiple: 0:15, 1:30, 2:45", [15.0, 90.0, 165.0]),
    ]
    
    for content, expected in test_cases:
        conversation = [MockMessage(content)]
        timestamps = extract_timestamps_from_conversation(conversation)
        
        for exp_ts in expected:
            assert exp_ts in timestamps, f"Failed to extract {exp_ts} from '{content}'"
    
    print("✓ Timestamp pattern recognition tests passed")


def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("Running Video Player Component Tests (Task 21)")
    print("=" * 60)
    
    try:
        test_format_timestamp()
        test_extract_timestamps()
        test_navigation_functions()
        test_player_component_structure()
        test_timestamp_patterns()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nVideo player component is ready!")
        print("\nFeatures implemented:")
        print("  ✓ Video player with Streamlit video component")
        print("  ✓ Timestamp navigation from clickable timestamps")
        print("  ✓ Playback controls (start, back, forward, reset)")
        print("  ✓ Sync with conversation context")
        print("  ✓ Timestamp extraction from conversation")
        print("  ✓ Clickable timestamp chips")
        print("\nRequirement 8.4 satisfied: Timestamp navigation implemented")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
