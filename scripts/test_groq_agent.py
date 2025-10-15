"""Test script for Groq Agent."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agent import GroqAgent
from services.memory import Memory
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agent_initialization():
    """Test agent initialization."""
    print("\n" + "="*60)
    print("TEST 1: Agent Initialization")
    print("="*60)
    
    try:
        agent = GroqAgent()
        print("✓ Agent initialized successfully")
        print(f"  - Groq model: {Config.GROQ_MODEL}")
        print(f"  - Temperature: {Config.GROQ_TEMPERATURE}")
        print(f"  - MCP server: {Config.get_mcp_server_url()}")
        agent.close()
        return True
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        return False


async def test_should_use_tool():
    """Test tool detection logic."""
    print("\n" + "="*60)
    print("TEST 2: Tool Detection")
    print("="*60)
    
    try:
        agent = GroqAgent()
        
        test_cases = [
            ("Hello, how are you?", None, "General greeting"),
            ("What's happening in this video?", "video_analysis", "Visual query"),
            ("What did they say at 1:30?", "video_analysis", "Transcript query"),
            ("Show me all the dogs", "video_analysis", "Object query"),
            ("Thanks for your help!", None, "Gratitude"),
        ]
        
        all_passed = True
        for message, expected, description in test_cases:
            result = agent._should_use_tool(message)
            passed = result == expected
            status = "✓" if passed else "✗"
            print(f"{status} {description}: '{message}'")
            print(f"  Expected: {expected}, Got: {result}")
            if not passed:
                all_passed = False
        
        agent.close()
        return all_passed
    except Exception as e:
        print(f"✗ Tool detection test failed: {e}")
        return False


async def test_general_response():
    """Test general conversational response."""
    print("\n" + "="*60)
    print("TEST 3: General Conversational Response")
    print("="*60)
    
    try:
        agent = GroqAgent()
        
        # Create test video in database first
        from storage.database import Database
        db = Database()
        db.execute_update(
            "INSERT OR IGNORE INTO videos (video_id, filename, file_path, duration) VALUES (?, ?, ?, ?)",
            ("test_video_123", "test.mp4", "data/videos/test.mp4", 60.0)
        )
        db.close()
        
        # Test general greeting
        response = await agent.chat(
            message="Hello! What can you help me with?",
            video_id="test_video_123"
        )
        
        print("✓ Generated response successfully")
        print(f"  Message: {response.message[:100]}...")
        print(f"  Frames: {len(response.frames)}")
        print(f"  Timestamps: {len(response.timestamps)}")
        print(f"  Suggestions: {response.suggestions}")
        
        agent.close()
        return True
    except Exception as e:
        print(f"✗ General response test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_storage():
    """Test memory storage."""
    print("\n" + "="*60)
    print("TEST 4: Memory Storage")
    print("="*60)
    
    try:
        agent = GroqAgent()
        video_id = "test_video_memory"
        
        # Create test video in database first
        from storage.database import Database
        db = Database()
        db.execute_update(
            "INSERT OR IGNORE INTO videos (video_id, filename, file_path, duration) VALUES (?, ?, ?, ?)",
            (video_id, "test.mp4", "data/videos/test.mp4", 60.0)
        )
        db.close()
        
        # Send a message
        await agent.chat(
            message="Hello BRI!",
            video_id=video_id
        )
        
        # Check memory
        history = agent.memory.get_conversation_history(video_id)
        
        if len(history) >= 2:  # User + assistant messages
            print("✓ Memory stored successfully")
            print(f"  Stored {len(history)} messages")
            for record in history:
                print(f"  - {record.role}: {record.content[:50]}...")
            
            # Clean up
            agent.memory.reset_memory(video_id)
            agent.close()
            return True
        else:
            print(f"✗ Expected at least 2 messages, got {len(history)}")
            agent.close()
            return False
            
    except Exception as e:
        print(f"✗ Memory storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_suggestion_generation():
    """Test follow-up suggestion generation."""
    print("\n" + "="*60)
    print("TEST 5: Follow-up Suggestion Generation")
    print("="*60)
    
    try:
        agent = GroqAgent()
        
        test_queries = [
            "What's happening in this video?",
            "What did they say?",
            "Find all the cars",
        ]
        
        all_passed = True
        for query in test_queries:
            suggestions = agent._generate_suggestions(
                query,
                "Sample response",
                "test_video"
            )
            
            if suggestions and len(suggestions) <= 3:
                print(f"✓ Generated {len(suggestions)} suggestions for: '{query}'")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
            else:
                print(f"✗ Invalid suggestions for: '{query}'")
                all_passed = False
        
        agent.close()
        return all_passed
    except Exception as e:
        print(f"✗ Suggestion generation test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling."""
    print("\n" + "="*60)
    print("TEST 6: Error Handling")
    print("="*60)
    
    try:
        agent = GroqAgent()
        
        test_errors = [
            (Exception("API error"), "API"),
            (Exception("Connection timeout"), "timeout"),
            (Exception("Network error"), "network"),
            (Exception("Unknown error"), "generic"),
        ]
        
        for error, error_type in test_errors:
            message = agent._handle_error(error)
            print(f"✓ {error_type} error: {message}")
        
        agent.close()
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def test_conversation_context():
    """Test conversation context building."""
    print("\n" + "="*60)
    print("TEST 7: Conversation Context")
    print("="*60)
    
    try:
        agent = GroqAgent()
        video_id = "test_video_context"
        
        # Create test video in database first
        from storage.database import Database
        db = Database()
        db.execute_update(
            "INSERT OR IGNORE INTO videos (video_id, filename, file_path, duration) VALUES (?, ?, ?, ?)",
            (video_id, "test.mp4", "data/videos/test.mp4", 60.0)
        )
        db.close()
        
        # Add some conversation history
        agent.memory.add_memory_pair(
            video_id,
            "What's in the video?",
            "I see a park scene with people walking."
        )
        agent.memory.add_memory_pair(
            video_id,
            "Are there any dogs?",
            "Yes, I can see a dog being walked."
        )
        
        # Get context
        context = agent.memory.get_recent_context(video_id, max_messages=4)
        
        if context and "park" in context and "dog" in context:
            print("✓ Conversation context built successfully")
            print(f"  Context length: {len(context)} characters")
            print(f"  Context preview: {context[:150]}...")
            
            # Clean up
            agent.memory.reset_memory(video_id)
            agent.close()
            return True
        else:
            print("✗ Context missing expected content")
            agent.close()
            return False
            
    except Exception as e:
        print(f"✗ Conversation context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("GROQ AGENT TEST SUITE")
    print("="*60)
    
    # Check configuration
    if not Config.GROQ_API_KEY:
        print("\n✗ GROQ_API_KEY not set in environment")
        print("  Please set GROQ_API_KEY in .env file")
        return
    
    print(f"\nConfiguration:")
    print(f"  Groq Model: {Config.GROQ_MODEL}")
    print(f"  Temperature: {Config.GROQ_TEMPERATURE}")
    print(f"  Max Tokens: {Config.GROQ_MAX_TOKENS}")
    print(f"  MCP Server: {Config.get_mcp_server_url()}")
    
    # Run tests
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Tool Detection", test_should_use_tool),
        ("General Response", test_general_response),
        ("Memory Storage", test_memory_storage),
        ("Suggestion Generation", test_suggestion_generation),
        ("Error Handling", test_error_handling),
        ("Conversation Context", test_conversation_context),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
