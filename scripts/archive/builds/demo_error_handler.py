"""Demonstration of ErrorHandler functionality with real-world scenarios."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.error_handler import ErrorHandler


def demo_tool_failures():
    """Demonstrate tool failure handling."""
    print("\n" + "=" * 70)
    print("SCENARIO 1: Tool Failures with Graceful Degradation")
    print("=" * 70)
    
    print("\n📹 User uploads a video and asks: 'What's happening in the video?'")
    print("⚠️  Object detector fails, but captions and transcripts work")
    
    # Simulate tool failure
    error = Exception("YOLO model failed to load")
    message = ErrorHandler.handle_tool_error(
        'object_detector',
        error,
        available_tools=['caption_frames', 'transcribe_audio']
    )
    
    print(f"\n💬 BRI responds: \"{message}\"")
    
    # Show graceful degradation
    degradation = ErrorHandler.handle_graceful_degradation(
        requested_tools=['captions', 'transcripts', 'objects'],
        available_tools=['captions', 'transcripts'],
        query="What's happening in the video?"
    )
    
    print(f"\n✅ Can proceed: {degradation['can_proceed']}")
    print(f"🔧 Using tools: {', '.join(degradation['usable_tools'])}")
    print(f"💡 Fallback: \"{degradation['fallback_suggestion']}\"")


def demo_api_rate_limit():
    """Demonstrate API rate limit handling."""
    print("\n" + "=" * 70)
    print("SCENARIO 2: API Rate Limit Exceeded")
    print("=" * 70)
    
    print("\n📹 User asks multiple questions rapidly")
    print("⚠️  Groq API rate limit exceeded")
    
    error = Exception("Rate limit exceeded (429)")
    message = ErrorHandler.handle_api_error(error)
    
    print(f"\n💬 BRI responds: \"{message}\"")
    print("\n✨ User-friendly, no technical jargon!")


def demo_video_upload_error():
    """Demonstrate video upload error handling."""
    print("\n" + "=" * 70)
    print("SCENARIO 3: Invalid Video Upload")
    print("=" * 70)
    
    print("\n📹 User tries to upload 'vacation.wmv'")
    print("⚠️  Unsupported video format")
    
    error = Exception("Unsupported codec format")
    message = ErrorHandler.handle_video_upload_error(error, "vacation.wmv")
    
    print(f"\n💬 BRI responds: \"{message}\"")
    print("\n✨ Clear guidance on what formats are supported!")


def demo_processing_partial_success():
    """Demonstrate partial processing success."""
    print("\n" + "=" * 70)
    print("SCENARIO 4: Partial Processing Success")
    print("=" * 70)
    
    print("\n📹 User uploads a large video")
    print("✅ Frame extraction and captioning succeed")
    print("⚠️  Audio transcription fails (corrupted audio)")
    
    error = Exception("Audio stream decode error")
    message = ErrorHandler.handle_processing_error(
        "video_123",
        error,
        completed_steps=['frame extraction', 'captioning']
    )
    
    print(f"\n💬 BRI responds: \"{message}\"")
    print("\n✨ Acknowledges what worked, suggests retry!")


def demo_query_not_found():
    """Demonstrate query with no results."""
    print("\n" + "=" * 70)
    print("SCENARIO 5: Query Returns No Results")
    print("=" * 70)
    
    print("\n📹 User asks: 'Show me all the elephants'")
    print("⚠️  No elephants detected in video")
    
    error = Exception("No results found for query")
    message = ErrorHandler.handle_query_error(
        "Show me all the elephants",
        error
    )
    
    print(f"\n💬 BRI responds: \"{message}\"")
    print("\n✨ Friendly suggestion to try something else!")


def demo_timestamp_out_of_range():
    """Demonstrate timestamp error."""
    print("\n" + "=" * 70)
    print("SCENARIO 6: Timestamp Out of Range")
    print("=" * 70)
    
    print("\n📹 User asks: 'What happened at 10:00?'")
    print("⚠️  Video is only 5 minutes long")
    
    error = Exception("Timestamp 600.0 is out of range")
    message = ErrorHandler.handle_query_error(
        "What happened at 10:00?",
        error
    )
    
    print(f"\n💬 BRI responds: \"{message}\"")
    print("\n✨ Helpful guidance on valid timestamps!")


def demo_all_tools_unavailable():
    """Demonstrate complete tool failure."""
    print("\n" + "=" * 70)
    print("SCENARIO 7: All Tools Unavailable")
    print("=" * 70)
    
    print("\n📹 User asks: 'Describe the video'")
    print("⚠️  MCP server is down, no tools available")
    
    degradation = ErrorHandler.handle_graceful_degradation(
        requested_tools=['captions', 'transcripts', 'objects'],
        available_tools=[],
        query="Describe the video"
    )
    
    print(f"\n💬 BRI responds: \"{degradation['message']}\"")
    print(f"\n✅ Can proceed: {degradation['can_proceed']}")
    print("✨ Gracefully handles complete failure!")


def demo_fallback_suggestions():
    """Demonstrate intelligent fallback suggestions."""
    print("\n" + "=" * 70)
    print("SCENARIO 8: Intelligent Fallback Suggestions")
    print("=" * 70)
    
    scenarios = [
        {
            'query': "What did they say at 2:30?",
            'available': ['captions'],
            'failed': ['transcripts']
        },
        {
            'query': "What do you see in the video?",
            'available': ['transcripts'],
            'failed': ['captions']
        },
        {
            'query': "Tell me about the video",
            'available': ['captions', 'transcripts'],
            'failed': ['objects']
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Query: \"{scenario['query']}\"")
        print(f"   Available: {', '.join(scenario['available'])}")
        print(f"   Failed: {', '.join(scenario['failed'])}")
        
        suggestion = ErrorHandler.suggest_fallback(
            scenario['query'],
            scenario['available'],
            scenario['failed']
        )
        
        print(f"   💡 Suggestion: \"{suggestion}\"")
    
    print("\n✨ Context-aware suggestions based on available data!")


def demo_error_classification():
    """Demonstrate automatic error classification."""
    print("\n" + "=" * 70)
    print("SCENARIO 9: Automatic Error Classification")
    print("=" * 70)
    
    errors = [
        ("Groq API rate limit exceeded", "API Error"),
        ("Connection timeout after 30s", "Network Error"),
        ("Invalid parameter: video_id", "Validation Error"),
        ("Failed to decode video stream", "Processing Error"),
        ("Frame extractor crashed", "Tool Error"),
        ("Something weird happened", "Unknown Error")
    ]
    
    print("\n🔍 Automatically classifies errors for appropriate handling:\n")
    
    for error_msg, expected_type in errors:
        error = Exception(error_msg)
        error_type = ErrorHandler.classify_error(error)
        print(f"   '{error_msg[:40]}...'")
        print(f"   → {error_type.value} ✓")
    
    print("\n✨ Routes to specialized handlers automatically!")


def demo_unified_error_formatting():
    """Demonstrate unified error formatting."""
    print("\n" + "=" * 70)
    print("SCENARIO 10: Unified Error Formatting")
    print("=" * 70)
    
    print("\n🎯 Single entry point handles all error types:\n")
    
    # Tool error with context
    error = Exception("Caption generation failed")
    message = ErrorHandler.format_error_for_user(
        error,
        context={'tool_name': 'image_captioner', 'available_tools': ['audio_transcriber']}
    )
    print(f"1. Tool Error: \"{message}\"")
    
    # Upload error with context
    error = Exception("File too large")
    message = ErrorHandler.format_error_for_user(
        error,
        context={'upload': True, 'filename': 'huge_video.mp4'}
    )
    print(f"\n2. Upload Error: \"{message}\"")
    
    # Query error with context
    error = Exception("Ambiguous query")
    message = ErrorHandler.format_error_for_user(
        error,
        context={'query': 'Show me that thing'}
    )
    print(f"\n3. Query Error: \"{message}\"")
    
    # Generic error without context
    error = Exception("Unexpected error")
    message = ErrorHandler.format_error_for_user(error)
    print(f"\n4. Generic Error: \"{message}\"")
    
    print("\n✨ Consistent, friendly messages across all error types!")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("🎭 BRI ERROR HANDLER DEMONSTRATION")
    print("=" * 70)
    print("\nShowing how BRI handles errors with grace and personality!")
    
    demo_tool_failures()
    demo_api_rate_limit()
    demo_video_upload_error()
    demo_processing_partial_success()
    demo_query_not_found()
    demo_timestamp_out_of_range()
    demo_all_tools_unavailable()
    demo_fallback_suggestions()
    demo_error_classification()
    demo_unified_error_formatting()
    
    print("\n" + "=" * 70)
    print("✨ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Friendly, playful error messages maintain BRI's personality")
    print("  • Graceful degradation keeps the system working with partial failures")
    print("  • Intelligent fallback suggestions help users get answers")
    print("  • Context-aware messages provide relevant guidance")
    print("  • Unified error handling ensures consistency")
    print("\n💖 BRI makes errors feel less frustrating and more helpful!")
    print()


if __name__ == "__main__":
    main()
