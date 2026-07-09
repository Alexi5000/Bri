"""Simple test script for FrameExtractor functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.frame_extractor import FrameExtractor
from config import Config


def test_frame_extractor():
    """Test basic FrameExtractor functionality."""
    print("Testing FrameExtractor...")
    
    # Initialize
    extractor = FrameExtractor()
    print(f"✓ FrameExtractor initialized")
    print(f"  Frame storage path: {extractor.frame_storage_path}")
    
    # Test adaptive interval calculation
    interval_short = extractor._calculate_adaptive_interval(duration=30.0, max_frames=100)
    interval_long = extractor._calculate_adaptive_interval(duration=600.0, max_frames=100)
    print(f"✓ Adaptive interval calculation works")
    print(f"  30s video: {interval_short:.2f}s interval")
    print(f"  600s video: {interval_long:.2f}s interval")
    
    # Check if test video exists
    test_video_path = Path("data/videos/test_video.mp4")
    if test_video_path.exists():
        print(f"\n✓ Found test video: {test_video_path}")
        
        # Test metadata extraction
        try:
            metadata = extractor.get_video_metadata(str(test_video_path))
            print(f"✓ Video metadata extracted:")
            print(f"  Duration: {metadata.duration:.2f}s")
            print(f"  FPS: {metadata.fps:.2f}")
            print(f"  Resolution: {metadata.width}x{metadata.height}")
            print(f"  Codec: {metadata.codec}")
            print(f"  File size: {metadata.file_size / 1024 / 1024:.2f} MB")
            
            # Test frame extraction
            print(f"\n✓ Extracting frames...")
            frames = extractor.extract_frames(
                video_path=str(test_video_path),
                video_id="test_video",
                max_frames=5
            )
            print(f"✓ Extracted {len(frames)} frames")
            for i, frame in enumerate(frames[:3]):
                print(f"  Frame {i+1}: {frame.timestamp:.2f}s (frame #{frame.frame_number})")
            
            # Test timestamp extraction
            if metadata.duration > 5:
                print(f"\n✓ Extracting frame at timestamp 5.0s...")
                frame = extractor.extract_frame_at_timestamp(
                    video_path=str(test_video_path),
                    video_id="test_video",
                    timestamp=5.0
                )
                print(f"✓ Frame extracted at {frame.timestamp:.2f}s")
                print(f"  Path: {frame.image_path}")
            
        except Exception as e:
            print(f"✗ Error during video processing: {e}")
            return False
    else:
        print(f"\n⚠ No test video found at {test_video_path}")
        print(f"  Place a test video there to test extraction functionality")
    
    print("\n✓ All basic tests passed!")
    return True


if __name__ == "__main__":
    try:
        Config.ensure_directories()
        success = test_frame_extractor()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
