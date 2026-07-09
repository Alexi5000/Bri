"""Test script for ErrorHandler functionality."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.error_handler import ErrorHandler, ErrorType


def test_tool_errors():
    """Test tool-specific error handling."""
    print("=" * 60)
    print("Testing Tool Error Handling")
    print("=" * 60)
    
    # Test frame extractor error
    error = Exception("Failed to extract frames")
    message = ErrorHandler.handle_tool_error(
        'frame_extractor',
        error,
        available_tools=['audio_transcriber', 'image_captioner']
    )
    print(f"\n1. Frame Extractor Error:")
    print(f"   Message: {message}")
    assert "trouble extracting frames" in message.lower()
    assert "audio" in message.lower()
    
    # Test audio transcriber error
    error = Exception("Whisper model failed")
    message = ErrorHandler.handle_tool_error(
        'audio_transcriber',
        error,
        available_tools=['image_captioner']
    )
    print(f"\n2. Audio Transcriber Error:")
    print(f"   Message: {message}")
    assert "audio was a bit tricky" in message.lower()
    
    # Test object detector error
    error = Exception("YOLO detection failed")
    message = ErrorHandler.handle_tool_error(
        'object_detector',
        error,
        available_tools=['image_captioner', 'audio_transcriber']
    )
    print(f"\n3. Object Detector Error:")
    print(f"   Message: {message}")
    assert "couldn't spot specific objects" in message.lower()
    
    # Test unknown tool error
    error = Exception("Unknown tool failure")
    message = ErrorHandler.handle_tool_error(
        'unknown_tool',
        error,
        available_tools=['image_captioner']
    )
    print(f"\n4. Unknown Tool Error:")
    print(f"   Message: {message}")
    assert "trouble" in message.lower()
    
    print("\n✓ All tool error tests passed!")


def test_api_errors():
    """Test API error handling."""
    print("\n" + "=" * 60)
    print("Testing API Error Handling")
    print("=" * 60)
    
    # Test rate limit error
    error = Exception("Rate limit exceeded (429)")
    message = ErrorHandler.handle_api_error(error)
    print(f"\n1. Rate Limit Error:")
    print(f"   Message: {message}")
    assert "thinking a bit too hard" in message.lower() or "moment" in message.lower()
    
    # Test timeout error
    error = Exception("Request timed out")
    message = ErrorHandler.handle_api_error(error)
    print(f"\n2. Timeout Error:")
    print(f"   Message: {message}")
    assert "longer than expected" in message.lower() or "simpler" in message.lower()
    
    # Test authentication error
    error = Exception("Authentication failed (401)")
    message = ErrorHandler.handle_api_error(error)
    print(f"\n3. Authentication Error:")
    print(f"   Message: {message}")
    assert "api key" in message.lower() or "connecting" in message.lower()
    
    # Test service unavailable
    error = Exception("Service unavailable (503)")
    message = ErrorHandler.handle_api_error(error)
    print(f"\n4. Service Unavailable Error:")
    print(f"   Message: {message}")
    assert "trouble thinking" in message.lower() or "moment" in message.lower()
    
    # Test generic API error
    error = Exception("Unknown API error")
    message = ErrorHandler.handle_api_error(error)
    print(f"\n5. Generic API Error:")
    print(f"   Message: {message}")
    assert "trouble" in message.lower()
    
    print("\n✓ All API error tests passed!")


def test_fallback_suggestions():
    """Test fallback suggestion generation."""
    print("\n" + "=" * 60)
    print("Testing Fallback Suggestions")
    print("=" * 60)
    
    # Test with captions available
    query = "What did they say at 1:30?"
    available = ['captions']
    message = ErrorHandler.suggest_fallback(query, available, ['transcripts'])
    print(f"\n1. Audio query with captions available:")
    print(f"   Query: {query}")
    print(f"   Suggestion: {message}")
    assert "visible" in message.lower() or "describe" in message.lower()
    
    # Test with transcripts available
    query = "What do you see in the video?"
    available = ['transcripts']
    message = ErrorHandler.suggest_fallback(query, available, ['captions'])
    print(f"\n2. Visual query with transcripts available:")
    print(f"   Query: {query}")
    print(f"   Suggestion: {message}")
    assert "said" in message.lower() or "audio" in message.lower()
    
    # Test with multiple options
    query = "Tell me about the video"
    available = ['captions', 'transcripts']
    message = ErrorHandler.suggest_fallback(query, available, [])
    print(f"\n3. General query with multiple options:")
    print(f"   Query: {query}")
    print(f"   Suggestion: {message}")
    assert len(message) > 0
    
    # Test with no data available
    query = "What's in the video?"
    available = []
    message = ErrorHandler.suggest_fallback(query, available, ['captions', 'transcripts'])
    print(f"\n4. Query with no data available:")
    print(f"   Query: {query}")
    print(f"   Suggestion: {message}")
    assert "upload" in message.lower() or "try" in message.lower()
    
    print("\n✓ All fallback suggestion tests passed!")


def test_graceful_degradation():
    """Test graceful degradation logic."""
    print("\n" + "=" * 60)
    print("Testing Graceful Degradation")
    print("=" * 60)
    
    # Test with some tools unavailable
    requested = ['captions', 'transcripts', 'objects']
    available = ['captions', 'transcripts']
    query = "Show me all the dogs"
    
    result = ErrorHandler.handle_graceful_degradation(requested, available, query)
    print(f"\n1. Partial tool availability:")
    print(f"   Requested: {requested}")
    print(f"   Available: {available}")
    print(f"   Can proceed: {result['can_proceed']}")
    print(f"   Message: {result['message']}")
    print(f"   Usable tools: {result['usable_tools']}")
    
    assert result['can_proceed'] == True
    assert len(result['usable_tools']) == 2
    assert 'objects' in result['unavailable_tools']
    
    # Test with no tools available
    requested = ['captions', 'transcripts']
    available = []
    query = "What's happening?"
    
    result = ErrorHandler.handle_graceful_degradation(requested, available, query)
    print(f"\n2. No tools available:")
    print(f"   Requested: {requested}")
    print(f"   Available: {available}")
    print(f"   Can proceed: {result['can_proceed']}")
    print(f"   Message: {result['message']}")
    
    assert result['can_proceed'] == False
    assert len(result['usable_tools']) == 0
    assert "taking a break" in result['message'].lower()
    
    # Test with all tools available
    requested = ['captions']
    available = ['captions', 'transcripts', 'objects']
    query = "Describe the scene"
    
    result = ErrorHandler.handle_graceful_degradation(requested, available, query)
    print(f"\n3. All tools available:")
    print(f"   Requested: {requested}")
    print(f"   Available: {available}")
    print(f"   Can proceed: {result['can_proceed']}")
    print(f"   Usable tools: {result['usable_tools']}")
    
    assert result['can_proceed'] == True
    assert len(result['usable_tools']) == 1
    assert len(result['unavailable_tools']) == 0
    
    print("\n✓ All graceful degradation tests passed!")


def test_upload_errors():
    """Test video upload error handling."""
    print("\n" + "=" * 60)
    print("Testing Upload Error Handling")
    print("=" * 60)
    
    # Test format error
    error = Exception("Unsupported format")
    message = ErrorHandler.handle_video_upload_error(error, "video.avi")
    print(f"\n1. Format Error:")
    print(f"   Message: {message}")
    assert "mp4" in message.lower() or "format" in message.lower()
    
    # Test size error
    error = Exception("File too large")
    message = ErrorHandler.handle_video_upload_error(error, "large_video.mp4")
    print(f"\n2. Size Error:")
    print(f"   Message: {message}")
    assert "too big" in message.lower() or "500mb" in message.lower()
    
    # Test permission error
    error = Exception("Permission denied")
    message = ErrorHandler.handle_video_upload_error(error, "video.mp4")
    print(f"\n3. Permission Error:")
    print(f"   Message: {message}")
    assert "permission" in message.lower()
    
    # Test generic upload error
    error = Exception("Unknown upload error")
    message = ErrorHandler.handle_video_upload_error(error, "video.mp4")
    print(f"\n4. Generic Upload Error:")
    print(f"   Message: {message}")
    assert "wrong" in message.lower() or "try" in message.lower()
    
    print("\n✓ All upload error tests passed!")


def test_processing_errors():
    """Test video processing error handling."""
    print("\n" + "=" * 60)
    print("Testing Processing Error Handling")
    print("=" * 60)
    
    # Test with some completed steps
    error = Exception("Processing failed")
    message = ErrorHandler.handle_processing_error(
        "video123",
        error,
        completed_steps=['frame extraction', 'captioning']
    )
    print(f"\n1. Processing Error with Completed Steps:")
    print(f"   Message: {message}")
    assert "frame extraction" in message.lower() or "captioning" in message.lower()
    
    # Test with no completed steps
    error = Exception("Processing failed immediately")
    message = ErrorHandler.handle_processing_error("video123", error, completed_steps=[])
    print(f"\n2. Processing Error with No Completed Steps:")
    print(f"   Message: {message}")
    assert "hiccup" in message.lower() or "try" in message.lower()
    
    # Test memory error
    error = Exception("Out of memory")
    message = ErrorHandler.handle_processing_error("video123", error)
    print(f"\n3. Memory Error:")
    print(f"   Message: {message}")
    assert "large" in message.lower() or "memory" in message.lower()
    
    print("\n✓ All processing error tests passed!")


def test_query_errors():
    """Test query error handling."""
    print("\n" + "=" * 60)
    print("Testing Query Error Handling")
    print("=" * 60)
    
    # Test timestamp error
    error = Exception("Timestamp out of range")
    message = ErrorHandler.handle_query_error("What happened at 10:00?", error)
    print(f"\n1. Timestamp Error:")
    print(f"   Message: {message}")
    assert "timestamp" in message.lower() or "beyond" in message.lower()
    
    # Test not found error
    error = Exception("No results found")
    message = ErrorHandler.handle_query_error("Find the dog", error)
    print(f"\n2. Not Found Error:")
    print(f"   Message: {message}")
    assert "couldn't find" in message.lower() or "something else" in message.lower()
    
    # Test ambiguous query error
    error = Exception("Query is ambiguous")
    message = ErrorHandler.handle_query_error("Show me that thing", error)
    print(f"\n3. Ambiguous Query Error:")
    print(f"   Message: {message}")
    assert "not quite sure" in message.lower() or "specific" in message.lower()
    
    print("\n✓ All query error tests passed!")


def test_error_classification():
    """Test error classification."""
    print("\n" + "=" * 60)
    print("Testing Error Classification")
    print("=" * 60)
    
    # Test API error
    error = Exception("Groq API rate limit exceeded")
    error_type = ErrorHandler.classify_error(error)
    print(f"\n1. API Error: {error_type}")
    assert error_type == ErrorType.API_ERROR
    
    # Test network error
    error = Exception("Connection timeout")
    error_type = ErrorHandler.classify_error(error)
    print(f"2. Network Error: {error_type}")
    assert error_type == ErrorType.NETWORK_ERROR
    
    # Test validation error
    error = ValueError("Invalid parameter")
    error_type = ErrorHandler.classify_error(error)
    print(f"3. Validation Error: {error_type}")
    assert error_type == ErrorType.VALIDATION_ERROR
    
    # Test processing error
    error = Exception("Failed to decode video")
    error_type = ErrorHandler.classify_error(error)
    print(f"4. Processing Error: {error_type}")
    assert error_type == ErrorType.PROCESSING_ERROR
    
    # Test tool error
    error = Exception("Frame extractor failed")
    error_type = ErrorHandler.classify_error(error)
    print(f"5. Tool Error: {error_type}")
    assert error_type == ErrorType.TOOL_ERROR
    
    # Test unknown error
    error = Exception("Something weird happened")
    error_type = ErrorHandler.classify_error(error)
    print(f"6. Unknown Error: {error_type}")
    assert error_type == ErrorType.UNKNOWN_ERROR
    
    print("\n✓ All error classification tests passed!")


def test_format_error_for_user():
    """Test the main error formatting entry point."""
    print("\n" + "=" * 60)
    print("Testing Format Error for User")
    print("=" * 60)
    
    # Test with tool context
    error = Exception("Tool failed")
    context = {'tool_name': 'image_captioner', 'available_tools': ['audio_transcriber']}
    message = ErrorHandler.format_error_for_user(error, context)
    print(f"\n1. Tool Error with Context:")
    print(f"   Message: {message}")
    assert len(message) > 0
    
    # Test with upload context
    error = Exception("Invalid format")
    context = {'upload': True, 'filename': 'video.avi'}
    message = ErrorHandler.format_error_for_user(error, context)
    print(f"\n2. Upload Error with Context:")
    print(f"   Message: {message}")
    assert "format" in message.lower()
    
    # Test with processing context
    error = Exception("Processing failed")
    context = {'processing': True, 'video_id': 'video123', 'completed_steps': ['extraction']}
    message = ErrorHandler.format_error_for_user(error, context)
    print(f"\n3. Processing Error with Context:")
    print(f"   Message: {message}")
    assert "extraction" in message.lower()
    
    # Test with query context
    error = Exception("Query failed")
    context = {'query': 'What happened at 10:00?'}
    message = ErrorHandler.format_error_for_user(error, context)
    print(f"\n4. Query Error with Context:")
    print(f"   Message: {message}")
    assert len(message) > 0
    
    # Test without context
    error = Exception("Generic error")
    message = ErrorHandler.format_error_for_user(error)
    print(f"\n5. Generic Error without Context:")
    print(f"   Message: {message}")
    assert len(message) > 0
    
    print("\n✓ All format error tests passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BRI ERROR HANDLER TEST SUITE")
    print("=" * 60)
    
    try:
        test_tool_errors()
        test_api_errors()
        test_fallback_suggestions()
        test_graceful_degradation()
        test_upload_errors()
        test_processing_errors()
        test_query_errors()
        test_error_classification()
        test_format_error_for_user()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe ErrorHandler is working correctly with:")
        print("  • Friendly tool error messages")
        print("  • API error handling")
        print("  • Fallback suggestions")
        print("  • Graceful degradation")
        print("  • Upload error handling")
        print("  • Processing error handling")
        print("  • Query error handling")
        print("  • Error classification")
        print("  • Unified error formatting")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
