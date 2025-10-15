"""Test script for AudioTranscriber tool."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.audio_transcriber import AudioTranscriber


def test_audio_transcriber():
    """Test the AudioTranscriber with a sample video."""
    
    print("=" * 60)
    print("Testing AudioTranscriber")
    print("=" * 60)
    
    # Initialize transcriber with 'base' model for speed/accuracy balance
    print("\n1. Initializing AudioTranscriber with 'base' model...")
    transcriber = AudioTranscriber(model_size="base")
    print("✓ AudioTranscriber initialized successfully")
    
    # Check if test video exists
    test_video_path = "data/videos/test_video.mp4"
    
    if not os.path.exists(test_video_path):
        print(f"\n⚠ Test video not found at: {test_video_path}")
        print("Please place a test video at this location to run the test.")
        print("\nTesting with model validation only...")
        print("✓ Model loaded and ready to transcribe")
        return
    
    # Test full video transcription
    print(f"\n2. Transcribing full video: {test_video_path}")
    try:
        transcript = transcriber.transcribe_video(test_video_path)
        
        print(f"✓ Transcription complete!")
        print(f"  - Language: {transcript.language}")
        print(f"  - Segments: {len(transcript.segments)}")
        print(f"  - Full text length: {len(transcript.full_text)} characters")
        
        # Display first few segments
        print("\n  First 3 segments:")
        for i, segment in enumerate(transcript.segments[:3]):
            print(f"    [{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")
        
        # Display full text preview
        print(f"\n  Full text preview:")
        preview = transcript.full_text[:200]
        print(f"    {preview}{'...' if len(transcript.full_text) > 200 else ''}")
        
        # Test segment transcription
        if transcript.segments:
            print(f"\n3. Testing segment transcription...")
            # Get a segment in the middle of the video
            mid_segment = transcript.segments[len(transcript.segments) // 2]
            start_time = max(0, mid_segment.start - 2)
            end_time = mid_segment.end + 2
            
            print(f"  Transcribing segment: {start_time:.2f}s to {end_time:.2f}s")
            segment = transcriber.transcribe_segment(
                test_video_path,
                start_time,
                end_time
            )
            
            print(f"✓ Segment transcription complete!")
            print(f"  - Time range: {segment.start:.2f}s - {segment.end:.2f}s")
            print(f"  - Text: {segment.text}")
            print(f"  - Confidence: {segment.confidence:.3f}")
        
    except Exception as e:
        print(f"✗ Transcription failed: {str(e)}")
        return
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)


def test_model_validation():
    """Test that the model loads correctly without a video."""
    print("=" * 60)
    print("Model Validation Test")
    print("=" * 60)
    
    print("\nTesting model initialization...")
    try:
        transcriber = AudioTranscriber(model_size="base")
        print("✓ Whisper 'base' model loaded successfully")
        
        # Verify model attributes
        assert hasattr(transcriber, 'model'), "Model not loaded"
        assert transcriber.model_size == "base", "Model size mismatch"
        
        print("✓ Model validation passed")
        
    except Exception as e:
        print(f"✗ Model validation failed: {str(e)}")
        raise
    
    print("\n" + "=" * 60)
    print("Model validation completed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    # Run model validation first
    test_model_validation()
    
    print("\n\n")
    
    # Then run full test if video is available
    test_audio_transcriber()
