"""Test script for ObjectDetector tool."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.object_detector import ObjectDetector
from tools.frame_extractor import FrameExtractor
from config import Config


def test_object_detector():
    """Test the ObjectDetector with sample video."""
    print("=" * 60)
    print("Testing ObjectDetector")
    print("=" * 60)
    
    # Find a test video
    video_dir = Path(Config.VIDEO_STORAGE_PATH)
    video_files = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.avi"))
    
    if not video_files:
        print("❌ No video files found in data/videos/")
        print("Please upload a video first or place a test video in data/videos/")
        return
    
    test_video = video_files[0]
    print(f"\n📹 Using test video: {test_video.name}")
    
    # Extract some frames first
    print("\n1️⃣ Extracting frames...")
    extractor = FrameExtractor()
    
    try:
        video_id = "test_detector"
        frames = extractor.extract_frames(
            str(test_video),
            video_id,
            interval_seconds=5.0,  # Extract every 5 seconds
            max_frames=5  # Only extract 5 frames for testing
        )
        print(f"✅ Extracted {len(frames)} frames")
        
        for frame in frames:
            print(f"   - Frame at {frame.timestamp:.2f}s: {frame.image_path}")
    
    except Exception as e:
        print(f"❌ Frame extraction failed: {str(e)}")
        return
    
    # Initialize ObjectDetector
    print("\n2️⃣ Initializing ObjectDetector...")
    try:
        detector = ObjectDetector(model_name="yolov8n.pt")
        print("✅ ObjectDetector initialized")
    except Exception as e:
        print(f"❌ Failed to initialize ObjectDetector: {str(e)}")
        return
    
    # Test batch object detection
    print("\n3️⃣ Testing batch object detection...")
    try:
        frame_paths = [frame.image_path for frame in frames]
        timestamps = [frame.timestamp for frame in frames]
        
        detections = detector.detect_objects_in_frames(
            frame_paths,
            timestamps,
            confidence_threshold=0.3
        )
        
        print(f"✅ Detected objects in {len(detections)} frames")
        
        total_objects = 0
        for detection in detections:
            num_objects = len(detection.objects)
            total_objects += num_objects
            print(f"\n   📍 Timestamp {detection.frame_timestamp:.2f}s: {num_objects} objects")
            
            # Show first 5 objects per frame
            for obj in detection.objects[:5]:
                print(f"      - {obj.class_name} (confidence: {obj.confidence:.2f}, bbox: {obj.bbox})")
            
            if len(detection.objects) > 5:
                print(f"      ... and {len(detection.objects) - 5} more objects")
        
        print(f"\n   Total objects detected: {total_objects}")
        
    except Exception as e:
        print(f"❌ Batch detection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test search for specific object
    print("\n4️⃣ Testing search for specific object...")
    try:
        # Try searching for common objects
        search_classes = ["person", "car", "dog", "cat", "chair"]
        
        for search_class in search_classes:
            results = detector.search_for_object(
                frame_paths,
                timestamps,
                search_class,
                confidence_threshold=0.3
            )
            
            if results:
                print(f"\n   🔍 Found '{search_class}' in {len(results)} frames:")
                for result in results:
                    count = len(result.objects)
                    print(f"      - Timestamp {result.frame_timestamp:.2f}s: {count} instance(s)")
                break
        else:
            print(f"   ℹ️  None of the searched objects ({', '.join(search_classes)}) were found")
        
    except Exception as e:
        print(f"❌ Object search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test single frame detection
    print("\n5️⃣ Testing single frame detection...")
    try:
        if frames:
            result = detector.detect_single_frame(
                frames[0].image_path,
                frames[0].timestamp,
                confidence_threshold=0.3
            )
            print(f"✅ Single frame detection: {len(result.objects)} objects found")
    except Exception as e:
        print(f"❌ Single frame detection failed: {str(e)}")
    
    # Show available classes
    print("\n6️⃣ Available object classes:")
    try:
        classes = detector.get_available_classes()
        print(f"   Model can detect {len(classes)} classes:")
        print(f"   {', '.join(classes[:20])}...")
        print(f"   (showing first 20 of {len(classes)} classes)")
    except Exception as e:
        print(f"❌ Failed to get classes: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ ObjectDetector test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_object_detector()
