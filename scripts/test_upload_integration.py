"""Integration test for video upload with UI components."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.file_store import get_file_store
from storage.database import get_database, insert_video, get_video, get_all_videos
from config import Config
import uuid
import cv2


def test_complete_upload_flow():
    """Test the complete upload flow as it would happen in the UI."""
    print("=" * 60)
    print("TESTING COMPLETE UPLOAD FLOW")
    print("=" * 60)
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Initialize database
    db = get_database()
    db.initialize_schema()
    
    # Create a test video file
    test_video_path = Path("data/test_upload_flow.mp4")
    print(f"\n1. Creating test video file: {test_video_path}")
    
    # Create a minimal valid video file using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(test_video_path), fourcc, 30.0, (640, 480))
    
    # Write 90 frames (3 seconds at 30fps)
    import numpy as np
    for i in range(90):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some color variation
        frame[:, :] = [i % 255, (i * 2) % 255, (i * 3) % 255]
        out.write(frame)
    
    out.release()
    print(f"   ✓ Created test video: {test_video_path.stat().st_size} bytes")
    
    try:
        # Simulate upload process
        print("\n2. Simulating upload process...")
        
        file_store = get_file_store()
        
        # Step 1: Validate file
        print("   a) Validating file...")
        file_size = test_video_path.stat().st_size
        is_valid, error_msg = file_store.validate_video_file(
            test_video_path.name,
            file_size
        )
        print(f"      Valid: {is_valid}")
        if not is_valid:
            print(f"      Error: {error_msg}")
            return False
        
        # Step 2: Generate video ID
        print("   b) Generating video ID...")
        video_id = str(uuid.uuid4())
        print(f"      Video ID: {video_id}")
        
        # Step 3: Save video
        print("   c) Saving video to storage...")
        with open(test_video_path, 'rb') as f:
            saved_video_id, file_path = file_store.save_uploaded_video(
                f,
                test_video_path.name,
                video_id
            )
        print(f"      Saved to: {file_path}")
        assert saved_video_id == video_id
        
        # Step 4: Extract metadata
        print("   d) Extracting video metadata...")
        cap = cv2.VideoCapture(file_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        print(f"      Duration: {duration:.2f}s")
        print(f"      Resolution: {width}x{height}")
        print(f"      FPS: {fps}")
        
        # Step 5: Create database record
        print("   e) Creating database record...")
        insert_video(
            video_id=video_id,
            filename=test_video_path.name,
            file_path=file_path,
            duration=duration
        )
        print(f"      ✓ Database record created")
        
        # Step 6: Verify database record
        print("   f) Verifying database record...")
        video = get_video(video_id)
        assert video is not None
        assert video['video_id'] == video_id
        assert video['filename'] == test_video_path.name
        assert video['processing_status'] == 'pending'
        print(f"      ✓ Record verified")
        
        # Step 7: Verify file exists
        print("   g) Verifying file exists...")
        exists = file_store.video_exists(video_id)
        assert exists
        print(f"      ✓ File exists in storage")
        
        # Step 8: Test retrieval
        print("\n3. Testing video retrieval...")
        all_videos = get_all_videos()
        print(f"   Total videos in database: {len(all_videos)}")
        
        found = False
        for v in all_videos:
            if v['video_id'] == video_id:
                found = True
                print(f"   ✓ Found uploaded video: {v['filename']}")
                break
        
        assert found, "Should find uploaded video in database"
        
        # Step 9: Cleanup
        print("\n4. Cleaning up...")
        from storage.database import delete_video as db_delete_video
        
        # Delete from database
        db_delete_video(video_id)
        print("   ✓ Deleted from database")
        
        # Delete from file system
        file_store.delete_video(video_id)
        print("   ✓ Deleted from file system")
        
        # Verify deletion
        video = get_video(video_id)
        assert video is None
        exists = file_store.video_exists(video_id)
        assert not exists
        print("   ✓ Cleanup verified")
        
        print("\n" + "=" * 60)
        print("✅ COMPLETE UPLOAD FLOW TEST PASSED!")
        print("=" * 60)
        print("\nThe upload functionality is working correctly:")
        print("  ✓ File validation")
        print("  ✓ Video storage")
        print("  ✓ Metadata extraction")
        print("  ✓ Database integration")
        print("  ✓ File retrieval")
        print("  ✓ Cleanup operations")
        
        return True
        
    finally:
        # Cleanup test file
        if test_video_path.exists():
            test_video_path.unlink()
            print(f"\n   Cleaned up test file: {test_video_path}")


def main():
    """Run integration test."""
    try:
        success = test_complete_upload_flow()
        if not success:
            print("\n❌ Test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
