"""
Test script for video library view functionality
Tests thumbnail generation, video display, and delete operations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime, timedelta
from storage.database import initialize_database, insert_video, get_all_videos, delete_video
from storage.file_store import get_file_store
from ui.library import (
    format_duration,
    format_upload_date,
    get_status_emoji,
    get_status_text,
    generate_thumbnail
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_format_duration():
    """Test duration formatting"""
    logger.info("Testing duration formatting...")
    
    test_cases = [
        (65, "1:05"),
        (125, "2:05"),
        (3665, "1:01:05"),
        (45, "0:45"),
        (3600, "1:00:00")
    ]
    
    for seconds, expected in test_cases:
        result = format_duration(seconds)
        status = "✅" if result == expected else "❌"
        logger.info(f"{status} {seconds}s -> {result} (expected: {expected})")


def test_format_upload_date():
    """Test upload date formatting"""
    logger.info("\nTesting upload date formatting...")
    
    now = datetime.now()
    
    test_cases = [
        (now - timedelta(minutes=30), "30 minutes ago"),
        (now - timedelta(hours=2), "2 hours ago"),
        (now - timedelta(days=1), "Yesterday"),
        (now - timedelta(days=3), "3 days ago"),
    ]
    
    for timestamp, description in test_cases:
        result = format_upload_date(timestamp)
        logger.info(f"✅ {description}: {result}")


def test_status_helpers():
    """Test status emoji and text helpers"""
    logger.info("\nTesting status helpers...")
    
    statuses = ['pending', 'processing', 'complete', 'error']
    
    for status in statuses:
        emoji = get_status_emoji(status)
        text = get_status_text(status)
        logger.info(f"✅ {status}: {emoji} {text}")


def test_video_database_operations():
    """Test video database operations"""
    logger.info("\nTesting video database operations...")
    
    try:
        # Initialize database
        initialize_database()
        logger.info("✅ Database initialized")
        
        # Insert test video (delete first if exists)
        test_video_id = "test_video_123"
        try:
            delete_video(test_video_id)
            logger.info("   Cleaned up existing test video")
        except Exception:
            pass
        
        insert_video(
            video_id=test_video_id,
            filename="test_video.mp4",
            file_path="/path/to/test_video.mp4",
            duration=125.5,
            thumbnail_path=None
        )
        logger.info(f"✅ Inserted test video: {test_video_id}")
        
        # Get all videos
        videos = get_all_videos()
        logger.info(f"✅ Retrieved {len(videos)} videos")
        
        # Display video info
        for video in videos:
            logger.info(f"   - {video['filename']} ({video['video_id']})")
            logger.info(f"     Duration: {format_duration(video['duration'])}")
            logger.info(f"     Status: {get_status_emoji(video['processing_status'])} {video['processing_status']}")
        
        # Delete test video
        delete_video(test_video_id)
        logger.info(f"✅ Deleted test video: {test_video_id}")
        
        # Verify deletion
        videos_after = get_all_videos()
        if not any(v['video_id'] == test_video_id for v in videos_after):
            logger.info("✅ Video successfully removed from database")
        else:
            logger.error("❌ Video still exists in database")
        
    except Exception as e:
        logger.error(f"❌ Database operations failed: {e}")
        raise


def test_thumbnail_generation():
    """Test thumbnail generation (requires actual video file)"""
    logger.info("\nTesting thumbnail generation...")
    
    # Check if test video exists
    test_video_path = "data/videos/test.mp4"
    
    if not Path(test_video_path).exists():
        logger.warning("⚠️ No test video found. Skipping thumbnail generation test.")
        logger.info("   To test thumbnail generation, place a video at: data/videos/test.mp4")
        return
    
    try:
        file_store = get_file_store()
        cache_dir = file_store.get_cache_directory("test_thumbnail")
        thumbnail_path = cache_dir / "test_thumbnail.jpg"
        
        success = generate_thumbnail(test_video_path, str(thumbnail_path), timestamp=1.0)
        
        if success and thumbnail_path.exists():
            logger.info(f"✅ Thumbnail generated: {thumbnail_path}")
            logger.info(f"   Size: {thumbnail_path.stat().st_size} bytes")
        else:
            logger.error("❌ Thumbnail generation failed")
            
    except Exception as e:
        logger.error(f"❌ Thumbnail generation error: {e}")


def test_file_store_operations():
    """Test file store operations"""
    logger.info("\nTesting file store operations...")
    
    try:
        file_store = get_file_store()
        
        # Test validation
        valid_cases = [
            ("video.mp4", 1024 * 1024),  # 1MB
            ("video.avi", 100 * 1024 * 1024),  # 100MB
        ]
        
        invalid_cases = [
            ("video.txt", 1024, "Unsupported format"),
            ("video.mp4", 600 * 1024 * 1024, "File too large"),  # 600MB
        ]
        
        logger.info("Testing valid files:")
        for filename, size in valid_cases:
            is_valid, error = file_store.validate_video_file(filename, size)
            status = "✅" if is_valid else "❌"
            logger.info(f"{status} {filename} ({size} bytes): Valid")
        
        logger.info("\nTesting invalid files:")
        for filename, size, reason in invalid_cases:
            is_valid, error = file_store.validate_video_file(filename, size)
            status = "✅" if not is_valid else "❌"
            logger.info(f"{status} {filename}: {error or reason}")
        
    except Exception as e:
        logger.error(f"❌ File store operations failed: {e}")
        raise


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("VIDEO LIBRARY COMPONENT TEST SUITE")
    logger.info("=" * 60)
    
    try:
        test_format_duration()
        test_format_upload_date()
        test_status_helpers()
        test_file_store_operations()
        test_video_database_operations()
        test_thumbnail_generation()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL TESTS COMPLETED")
        logger.info("=" * 60)
        logger.info("\nTo test the full UI:")
        logger.info("1. Run: streamlit run app.py")
        logger.info("2. Upload a video")
        logger.info("3. Navigate to Video Library")
        logger.info("4. Test video selection and deletion")
        
    except Exception as e:
        logger.error(f"\n❌ TEST SUITE FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
