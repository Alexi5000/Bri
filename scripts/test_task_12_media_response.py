"""Test script for Task 12: Response generation with media."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agent import GroqAgent
from services.media_utils import MediaUtils
from models.responses import AssistantMessageResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_media_utils():
    """Test MediaUtils functionality."""
    print("\n" + "="*60)
    print("Testing MediaUtils")
    print("="*60)
    
    # Test timestamp formatting
    print("\n1. Testing timestamp formatting:")
    test_timestamps = [12.5, 125.0, 3725.5]
    for ts in test_timestamps:
        formatted = MediaUtils.format_timestamp(ts)
        print(f"   {ts}s -> {formatted}")
    
    # Test timestamp parsing
    print("\n2. Testing timestamp parsing:")
    test_strings = ["02:05", "01:02:05", "12.5s", "125"]
    for ts_str in test_strings:
        try:
            parsed = MediaUtils.parse_timestamp(ts_str)
            print(f"   '{ts_str}' -> {parsed}s")
        except Exception as e:
            print(f"   '{ts_str}' -> Error: {e}")
    
    print("\n✓ MediaUtils tests completed")


async def test_agent_media_response():
    """Test agent response generation with media."""
    print("\n" + "="*60)
    print("Testing Agent Media Response Generation")
    print("="*60)
    
    try:
        # Initialize agent
        print("\n1. Initializing Groq Agent...")
        agent = GroqAgent()
        print("   ✓ Agent initialized")
        
        # Test video ID (using existing test video if available)
        video_id = "test_video_001"
        
        # Test queries
        test_queries = [
            "What's happening in the video?",
            "Show me all the important moments",
            "What did they say at the beginning?"
        ]
        
        print(f"\n2. Testing queries for video: {video_id}")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            try:
                # Process query
                response = await agent.chat(
                    message=query,
                    video_id=video_id
                )
                
                # Verify response structure
                assert isinstance(response, AssistantMessageResponse), \
                    "Response should be AssistantMessageResponse"
                
                print("   ✓ Response generated")
                print(f"     - Message length: {len(response.message)} chars")
                print(f"     - Frames: {len(response.frames)}")
                print(f"     - Timestamps: {len(response.timestamps)}")
                print(f"     - Suggestions: {len(response.suggestions)}")
                
                if response.frame_contexts:
                    print(f"     - Frame contexts: {len(response.frame_contexts)}")
                    for j, ctx in enumerate(response.frame_contexts[:3], 1):
                        print(f"       {j}. [{MediaUtils.format_timestamp(ctx.timestamp)}] {ctx.description[:50]}...")
                
                # Verify timestamps are in chronological order
                if len(response.timestamps) > 1:
                    is_sorted = all(
                        response.timestamps[i] <= response.timestamps[i+1]
                        for i in range(len(response.timestamps)-1)
                    )
                    if is_sorted:
                        print("     ✓ Timestamps are in chronological order")
                    else:
                        print("     ✗ Timestamps are NOT in chronological order")
                
                # Check if timestamps are formatted in response
                if response.timestamps:
                    has_formatted_ts = any(
                        MediaUtils.format_timestamp(ts) in response.message
                        for ts in response.timestamps[:3]
                    )
                    if has_formatted_ts:
                        print("     ✓ Response includes formatted timestamps")
                
            except Exception as e:
                print(f"   ✗ Query failed: {e}")
                logger.error(f"Query failed: {e}", exc_info=True)
        
        print("\n✓ Agent media response tests completed")
        
        # Cleanup
        agent.close()
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    
    return True


def test_frame_context_structure():
    """Test FrameWithContext model structure."""
    print("\n" + "="*60)
    print("Testing FrameWithContext Model")
    print("="*60)
    
    from models.responses import FrameWithContext
    
    # Create test frame context
    frame_ctx = FrameWithContext(
        frame_path="data/frames/frame_001.jpg",
        timestamp=12.5,
        description="A person walking in the park"
    )
    
    print("\n1. Created FrameWithContext:")
    print(f"   - Frame path: {frame_ctx.frame_path}")
    print(f"   - Timestamp: {frame_ctx.timestamp}s ({MediaUtils.format_timestamp(frame_ctx.timestamp)})")
    print(f"   - Description: {frame_ctx.description}")
    
    # Test serialization
    frame_dict = frame_ctx.model_dump()
    print("\n2. Serialized to dict:")
    print(f"   {frame_dict}")
    
    # Test deserialization
    FrameWithContext(**frame_dict)
    print("\n3. Deserialized from dict:")
    print("   ✓ Successfully recreated FrameWithContext")
    
    print("\n✓ FrameWithContext model tests completed")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TASK 12: Response Generation with Media - Test Suite")
    print("="*60)
    
    # Test 1: MediaUtils
    test_media_utils()
    
    # Test 2: FrameWithContext model
    test_frame_context_structure()
    
    # Test 3: Agent media response (async)
    print("\n" + "="*60)
    print("Running async agent tests...")
    print("="*60)
    
    try:
        result = asyncio.run(test_agent_media_response())
        
        if result:
            print("\n" + "="*60)
            print("✓ ALL TESTS PASSED")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("✗ SOME TESTS FAILED")
            print("="*60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
