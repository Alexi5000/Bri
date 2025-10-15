"""
Test script for Task 23: Agent-UI Integration
Validates that the agent is properly integrated with the UI.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agent import GroqAgent
from services.memory import Memory
from models.responses import AssistantMessageResponse
from config import Config


def test_agent_initialization():
    """Test that agent can be initialized."""
    print("Testing agent initialization...")
    try:
        _ = GroqAgent()
        print("✓ Agent initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        return False


async def test_agent_chat():
    """Test agent chat functionality."""
    print("\nTesting agent chat...")
    try:
        agent = GroqAgent()
        
        # Test with a simple query
        response = await agent.chat(
            message="Hello, who are you?",
            video_id="test_video_123"
        )
        
        # Validate response structure
        assert isinstance(response, AssistantMessageResponse), "Response should be AssistantMessageResponse"
        assert response.message, "Response should have a message"
        assert isinstance(response.frames, list), "Frames should be a list"
        assert isinstance(response.timestamps, list), "Timestamps should be a list"
        assert isinstance(response.suggestions, list), "Suggestions should be a list"
        
        print(f"✓ Agent chat successful")
        print(f"  Response: {response.message[:100]}...")
        print(f"  Frames: {len(response.frames)}")
        print(f"  Timestamps: {len(response.timestamps)}")
        print(f"  Suggestions: {len(response.suggestions)}")
        
        return True
    except Exception as e:
        print(f"✗ Agent chat failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_integration():
    """Test memory integration."""
    print("\nTesting memory integration...")
    try:
        from storage.database import insert_video, delete_video, get_video
        
        # Create a test video first
        test_video_id = "test_video_integration_123"
        
        # Clean up any existing test video
        try:
            delete_video(test_video_id)
        except Exception:
            pass
        
        # Insert test video
        insert_video(
            video_id=test_video_id,
            filename="test_video.mp4",
            file_path="data/videos/test_video.mp4",
            duration=120.0
        )
        
        # Verify video was created
        video = get_video(test_video_id)
        assert video is not None, "Test video should exist"
        
        memory = Memory()
        
        # Test adding memory
        memory.add_memory_pair(
            video_id=test_video_id,
            user_message="Test question",
            assistant_message="Test response"
        )
        
        # Test retrieving memory
        history = memory.get_conversation_history(test_video_id, limit=10)
        
        print(f"✓ Memory integration successful")
        print(f"  Retrieved {len(history)} messages")
        
        # Clean up
        delete_video(test_video_id)
        
        return True
    except Exception as e:
        print(f"✗ Memory integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_formatting():
    """Test response formatting functions."""
    print("\nTesting response formatting...")
    try:
        from datetime import datetime
        
        # Test timestamp formatting
        from app import format_message_timestamp, format_video_timestamp
        
        # Test message timestamp
        now = datetime.now()
        formatted = format_message_timestamp(now)
        assert formatted == "just now", "Expected 'just now', got '{}'".format(formatted)
        
        # Test video timestamp
        formatted = format_video_timestamp(125.5)
        assert formatted == "02:05", "Expected '02:05', got '{}'".format(formatted)
        
        formatted = format_video_timestamp(3725.0)
        assert formatted == "01:02:05", "Expected '01:02:05', got '{}'".format(formatted)
        
        print("✓ Response formatting successful")
        return True
    except Exception as e:
        print(f"✗ Response formatting failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Test configuration validation."""
    print("\nTesting configuration...")
    try:
        # Check if GROQ_API_KEY is set
        if not Config.GROQ_API_KEY:
            print("⚠ Warning: GROQ_API_KEY not set in environment")
            print("  Set it in .env file for full functionality")
            return False
        
        print("✓ Configuration valid")
        print(f"  Model: {Config.GROQ_MODEL}")
        print(f"  Temperature: {Config.GROQ_TEMPERATURE}")
        print(f"  Max Tokens: {Config.GROQ_MAX_TOKENS}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 23: Agent-UI Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Configuration
    results.append(("Configuration", test_config_validation()))
    
    # Test 2: Agent initialization
    results.append(("Agent Initialization", test_agent_initialization()))
    
    # Test 3: Memory integration
    results.append(("Memory Integration", test_memory_integration()))
    
    # Test 4: Response formatting
    results.append(("Response Formatting", test_response_formatting()))
    
    # Test 5: Agent chat (only if API key is set)
    if Config.GROQ_API_KEY:
        results.append(("Agent Chat", asyncio.run(test_agent_chat())))
    else:
        print("\nSkipping agent chat test (no API key)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Task 23 integration is complete.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
