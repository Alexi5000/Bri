"""Test script for ImageCaptioner tool."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.image_captioner import ImageCaptioner


def test_image_captioner():
    """Test the ImageCaptioner with sample frames."""
    print("=" * 60)
    print("Testing ImageCaptioner Tool")
    print("=" * 60)
    
    # Check if we have any extracted frames to test with
    frames_dir = "data/frames"
    if not os.path.exists(frames_dir):
        print(f"\n❌ Frames directory not found: {frames_dir}")
        print("Please run frame extraction first to generate test frames.")
        return
    
    # Find sample frames
    frame_files = []
    for root, dirs, files in os.walk(frames_dir):
        for file in files:
            if file.endswith(('.jpg', '.png', '.jpeg')):
                frame_files.append(os.path.join(root, file))
                if len(frame_files) >= 3:  # Test with 3 frames
                    break
        if len(frame_files) >= 3:
            break
    
    if not frame_files:
        print(f"\n❌ No frame images found in {frames_dir}")
        print("Please run frame extraction first to generate test frames.")
        return
    
    print(f"\n✓ Found {len(frame_files)} test frames")
    
    # Initialize captioner
    print("\n" + "-" * 60)
    print("Initializing ImageCaptioner...")
    print("-" * 60)
    try:
        captioner = ImageCaptioner()
        print("✓ ImageCaptioner initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize ImageCaptioner: {str(e)}")
        return
    
    # Test single frame captioning
    print("\n" + "-" * 60)
    print("Test 1: Single Frame Captioning")
    print("-" * 60)
    try:
        test_frame = frame_files[0]
        print(f"Captioning: {test_frame}")
        caption = captioner.caption_frame(test_frame, timestamp=0.0)
        print("✓ Caption generated successfully!")
        print(f"  Timestamp: {caption.frame_timestamp}s")
        print(f"  Text: {caption.text}")
        print(f"  Confidence: {caption.confidence:.2f}")
    except Exception as e:
        print(f"❌ Single frame captioning failed: {str(e)}")
        return
    
    # Test batch captioning
    print("\n" + "-" * 60)
    print("Test 2: Batch Frame Captioning")
    print("-" * 60)
    try:
        timestamps = [float(i) for i in range(len(frame_files))]
        print(f"Captioning {len(frame_files)} frames in batch...")
        captions = captioner.caption_frames_batch(frame_files, timestamps)
        print("✓ Batch captioning completed successfully!")
        print(f"  Generated {len(captions)} captions")
        
        for i, caption in enumerate(captions):
            print(f"\n  Frame {i+1}:")
            print(f"    Timestamp: {caption.frame_timestamp}s")
            print(f"    Text: {caption.text}")
            print(f"    Confidence: {caption.confidence:.2f}")
    except Exception as e:
        print(f"❌ Batch captioning failed: {str(e)}")
        return
    
    # Test error handling
    print("\n" + "-" * 60)
    print("Test 3: Error Handling")
    print("-" * 60)
    try:
        print("Testing with non-existent file...")
        caption = captioner.caption_frame("nonexistent.jpg", timestamp=0.0)
        print("❌ Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("✓ FileNotFoundError raised correctly for missing file")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✓ All ImageCaptioner tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_image_captioner()
