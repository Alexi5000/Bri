"""Test script for video upload functionality."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.file_store import FileStore, get_file_store
from storage.database import Database, insert_video, get_video, get_all_videos
from config import Config
import uuid


def test_file_store():
    """Test FileStore functionality."""
    print("=" * 60)
    print("Testing FileStore")
    print("=" * 60)
    
    file_store = get_file_store()
    
    # Test validation
    print("\n1. Testing file validation...")
    
    # Valid file
    is_valid, error = file_store.validate_video_file("test.mp4", 10 * 1024 * 1024)
    print(f"   Valid MP4 (10MB): {is_valid} - {error}")
    assert is_valid, "Should accept valid MP4"
    
    # Invalid format
    is_valid, error = file_store.validate_video_file("test.txt", 10 * 1024 * 1024)
    print(f"   Invalid format (.txt): {is_valid} - {error}")
    assert not is_valid, "Should reject invalid format"
    
    # File too large
    is_valid, error = file_store.validate_video_file("test.mp4", 600 * 1024 * 1024)
    print(f"   Too large (600MB): {is_valid} - {error}")
    assert not is_valid, "Should reject files over 500MB"
    
    # Empty file
    is_valid, error = file_store.validate_video_file("test.mp4", 0)
    print(f"   Empty file: {is_valid} - {error}")
    assert not is_valid, "Should reject empty files"
    
    # Test supported formats
    print("\n2. Testing supported formats...")
    for ext in ['.mp4', '.avi', '.mov', '.mkv']:
        is_valid, error = file_store.validate_video_file(f"test{ext}", 10 * 1024 * 1024)
        print(f"   {ext}: {is_valid}")
        assert is_valid, f"Should accept {ext} format"
    
    # Test file size formatting
    print("\n3. Testing file size formatting...")
    sizes = [
        (500, "500.0 B"),
        (1024, "1.0 KB"),
        (1024 * 1024, "1.0 MB"),
        (1024 * 1024 * 1024, "1.0 GB"),
    ]
    for size_bytes, expected in sizes:
        formatted = file_store.format_file_size(size_bytes)
        print(f"   {size_bytes} bytes -> {formatted}")
        assert formatted == expected, f"Expected {expected}, got {formatted}"
    
    print("\n✅ FileStore tests passed!")


def test_database_operations():
    """Test database video operations."""
    print("\n" + "=" * 60)
    print("Testing Database Operations")
    print("=" * 60)
    
    # Initialize database
    db = Database(db_path="data/test_upload.db")
    db.connect()
    db.initialize_schema()
    
    print("\n1. Testing video insertion...")
    video_id = str(uuid.uuid4())
    insert_video(
        video_id=video_id,
        filename="test_video.mp4",
        file_path="/path/to/test_video.mp4",
        duration=120.5
    )
    print(f"   Inserted video: {video_id}")
    
    print("\n2. Testing video retrieval...")
    video = get_video(video_id)
    assert video is not None, "Should retrieve inserted video"
    print(f"   Retrieved video: {video['filename']}")
    print(f"   Duration: {video['duration']}s")
    print(f"   Status: {video['processing_status']}")
    assert video['filename'] == "test_video.mp4"
    assert video['duration'] == 120.5
    assert video['processing_status'] == "pending"
    
    print("\n3. Testing get all videos...")
    videos = get_all_videos()
    print(f"   Found {len(videos)} video(s)")
    assert len(videos) >= 1, "Should have at least one video"
    
    print("\n4. Testing video status update...")
    from storage.database import update_video_status
    update_video_status(video_id, "complete")
    video = get_video(video_id)
    print(f"   Updated status: {video['processing_status']}")
    assert video['processing_status'] == "complete"
    
    print("\n5. Testing video deletion...")
    from storage.database import delete_video as db_delete_video
    db_delete_video(video_id)
    video = get_video(video_id)
    print(f"   Video after deletion: {video}")
    assert video is None, "Video should be deleted"
    
    # Cleanup
    db.close()
    if os.path.exists("data/test_upload.db"):
        os.remove("data/test_upload.db")
    
    print("\n✅ Database tests passed!")


def test_integration():
    """Test integration of file store and database."""
    print("\n" + "=" * 60)
    print("Testing Integration")
    print("=" * 60)
    
    # Create test file
    test_file_path = Path("data/test_video_upload.mp4")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a small dummy file
    with open(test_file_path, 'wb') as f:
        f.write(b'dummy video content for testing')
    
    try:
        file_store = get_file_store()
        
        print("\n1. Validating test file...")
        file_size = os.path.getsize(test_file_path)
        is_valid, error = file_store.validate_video_file(
            test_file_path.name,
            file_size
        )
        print(f"   Valid: {is_valid}")
        
        if is_valid:
            print("\n2. Saving test file...")
            with open(test_file_path, 'rb') as f:
                video_id, saved_path = file_store.save_uploaded_video(
                    f,
                    test_file_path.name
                )
            print(f"   Video ID: {video_id}")
            print(f"   Saved to: {saved_path}")
            
            print("\n3. Verifying file exists...")
            exists = file_store.video_exists(video_id)
            print(f"   File exists: {exists}")
            assert exists, "Saved file should exist"
            
            print("\n4. Cleaning up...")
            deleted = file_store.delete_video(video_id)
            print(f"   Deleted: {deleted}")
            assert deleted, "Should delete successfully"
            
            exists = file_store.video_exists(video_id)
            print(f"   File exists after deletion: {exists}")
            assert not exists, "File should not exist after deletion"
    
    finally:
        # Cleanup test file
        if test_file_path.exists():
            test_file_path.unlink()
    
    print("\n✅ Integration tests passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("VIDEO UPLOAD FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Ensure directories exist
    Config.ensure_directories()
    
    try:
        test_file_store()
        test_database_operations()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nVideo upload functionality is working correctly!")
        print("\nYou can now:")
        print("  1. Upload videos through the Streamlit UI")
        print("  2. Videos will be validated for format and size")
        print("  3. Videos will be saved to storage with unique IDs")
        print("  4. Database records will be created automatically")
        print("  5. Friendly error messages will be shown for issues")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
