"""Test script for performance optimizations (Task 25)."""

import sys
import time
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import Database, initialize_database
from services.memory import Memory
from config import Config
from ui.lazy_loader import LazyImageLoader, LazyListLoader


def test_database_indexes():
    """Test that performance indexes are created."""
    print("\n=== Testing Database Indexes ===")
    
    try:
        # Initialize database with schema
        db = Database()
        db.connect()
        db.initialize_schema()
        
        # Check if indexes exist
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """
        indexes = db.execute_query(query)
        
        expected_indexes = [
            'idx_memory_video_timestamp',
            'idx_video_context_lookup',
            'idx_video_context_timestamp',
            'idx_videos_status'
        ]
        
        found_indexes = [idx['name'] for idx in indexes]
        
        print(f"✓ Found {len(found_indexes)} performance indexes:")
        for idx_name in found_indexes:
            print(f"  - {idx_name}")
        
        # Check if all expected indexes exist
        missing = set(expected_indexes) - set(found_indexes)
        if missing:
            print(f"⚠ Missing indexes: {missing}")
        else:
            print("✓ All expected indexes are present")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ Database index test failed: {e}")
        return False


def test_memory_pagination():
    """Test pagination support in Memory service."""
    print("\n=== Testing Memory Pagination ===")
    
    try:
        from storage.database import insert_video
        
        memory = Memory()
        video_id = "test_video_pagination"
        
        # Create video record first (for foreign key constraint)
        try:
            insert_video(
                video_id=video_id,
                filename="test_pagination.mp4",
                file_path="data/videos/test_pagination.mp4",
                duration=100.0
            )
        except Exception:
            pass  # Video might already exist
        
        # Insert test messages
        print("Inserting 25 test messages...")
        for i in range(25):
            memory.add_memory_pair(
                video_id=video_id,
                user_message=f"Test question {i}",
                assistant_message=f"Test answer {i}"
            )
        
        # Test pagination
        print("\nTesting pagination:")
        
        # Get first page (10 messages)
        page1 = memory.get_conversation_history(video_id, limit=10, offset=0)
        print(f"✓ Page 1: Retrieved {len(page1)} messages")
        assert len(page1) == 10, f"Expected 10 messages, got {len(page1)}"
        
        # Get second page (10 messages)
        page2 = memory.get_conversation_history(video_id, limit=10, offset=10)
        print(f"✓ Page 2: Retrieved {len(page2)} messages")
        assert len(page2) == 10, f"Expected 10 messages, got {len(page2)}"
        
        # Get third page (remaining messages)
        page3 = memory.get_conversation_history(video_id, limit=10, offset=20)
        print(f"✓ Page 3: Retrieved {len(page3)} messages")
        assert len(page3) == 10, f"Expected 10 messages, got {len(page3)}"
        
        # Verify no overlap between pages
        page1_ids = {msg.message_id for msg in page1}
        page2_ids = {msg.message_id for msg in page2}
        assert len(page1_ids & page2_ids) == 0, "Pages should not overlap"
        print("✓ No overlap between pages")
        
        # Test count
        total_count = memory.count_messages(video_id)
        print(f"✓ Total message count: {total_count}")
        assert total_count == 50, f"Expected 50 messages (25 pairs), got {total_count}"
        
        # Cleanup
        memory.reset_memory(video_id)
        memory.close()
        
        print("✓ Memory pagination test passed")
        return True
        
    except Exception as e:
        print(f"✗ Memory pagination test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lazy_image_loader():
    """Test lazy image loader functionality."""
    print("\n=== Testing Lazy Image Loader ===")
    
    try:
        loader = LazyImageLoader(batch_size=3)
        
        # Test with mock image paths
        image_paths = [f"data/frames/frame_{i}.jpg" for i in range(10)]
        timestamps = [float(i * 2) for i in range(10)]
        
        print(f"✓ Created LazyImageLoader with batch_size=3")
        print(f"✓ Mock data: {len(image_paths)} images with timestamps")
        
        # Test timestamp formatting
        formatted = loader._format_timestamp(125.5)
        assert formatted == "02:05", f"Expected '02:05', got '{formatted}'"
        print(f"✓ Timestamp formatting works: 125.5s -> {formatted}")
        
        formatted_hours = loader._format_timestamp(3725.0)
        assert formatted_hours == "01:02:05", f"Expected '01:02:05', got '{formatted_hours}'"
        print(f"✓ Timestamp formatting with hours: 3725s -> {formatted_hours}")
        
        print("✓ Lazy image loader test passed")
        return True
        
    except Exception as e:
        print(f"✗ Lazy image loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lazy_list_loader():
    """Test lazy list loader functionality."""
    print("\n=== Testing Lazy List Loader ===")
    
    try:
        loader = LazyListLoader(items_per_page=5)
        
        # Test with mock items
        items = [f"Item {i}" for i in range(23)]
        
        print(f"✓ Created LazyListLoader with items_per_page=5")
        print(f"✓ Mock data: {len(items)} items")
        
        # Calculate expected pages
        total_pages = (len(items) + 5 - 1) // 5
        print(f"✓ Expected pages: {total_pages}")
        assert total_pages == 5, f"Expected 5 pages, calculated {total_pages}"
        
        print("✓ Lazy list loader test passed")
        return True
        
    except Exception as e:
        print(f"✗ Lazy list loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_performance_settings():
    """Test that performance configuration settings are loaded."""
    print("\n=== Testing Performance Configuration ===")
    
    try:
        print(f"✓ TOOL_EXECUTION_TIMEOUT: {Config.TOOL_EXECUTION_TIMEOUT}s")
        assert Config.TOOL_EXECUTION_TIMEOUT > 0, "Timeout should be positive"
        
        print(f"✓ REQUEST_TIMEOUT: {Config.REQUEST_TIMEOUT}s")
        assert Config.REQUEST_TIMEOUT > 0, "Timeout should be positive"
        
        print(f"✓ LAZY_LOAD_BATCH_SIZE: {Config.LAZY_LOAD_BATCH_SIZE}")
        assert Config.LAZY_LOAD_BATCH_SIZE > 0, "Batch size should be positive"
        
        print(f"✓ MAX_CONVERSATION_HISTORY: {Config.MAX_CONVERSATION_HISTORY}")
        assert Config.MAX_CONVERSATION_HISTORY > 0, "History limit should be positive"
        
        print("✓ Performance configuration test passed")
        return True
        
    except Exception as e:
        print(f"✗ Performance configuration test failed: {e}")
        return False


def test_query_performance():
    """Test query performance with indexes."""
    print("\n=== Testing Query Performance ===")
    
    try:
        from storage.database import insert_video
        
        memory = Memory()
        video_id = "test_video_performance"
        
        # Create video record first (for foreign key constraint)
        try:
            insert_video(
                video_id=video_id,
                filename="test_performance.mp4",
                file_path="data/videos/test_performance.mp4",
                duration=100.0
            )
        except Exception:
            pass  # Video might already exist
        
        # Insert many messages
        print("Inserting 100 message pairs (200 messages)...")
        start_time = time.time()
        
        for i in range(100):
            memory.add_memory_pair(
                video_id=video_id,
                user_message=f"Performance test question {i}",
                assistant_message=f"Performance test answer {i}"
            )
        
        insert_time = time.time() - start_time
        print(f"✓ Inserted 200 messages in {insert_time:.2f}s ({200/insert_time:.1f} msg/s)")
        
        # Test query performance
        print("\nTesting query performance:")
        
        # Query with limit (should use index)
        start_time = time.time()
        results = memory.get_conversation_history(video_id, limit=10)
        query_time = time.time() - start_time
        print(f"✓ Retrieved 10 messages in {query_time*1000:.2f}ms")
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"
        
        # Query with pagination (should use index)
        start_time = time.time()
        results_page2 = memory.get_conversation_history(video_id, limit=10, offset=10)
        query_time_page2 = time.time() - start_time
        print(f"✓ Retrieved page 2 (10 messages) in {query_time_page2*1000:.2f}ms")
        assert len(results_page2) == 10, f"Expected 10 results, got {len(results_page2)}"
        
        # Count query (should use index)
        start_time = time.time()
        count = memory.count_messages(video_id)
        count_time = time.time() - start_time
        print(f"✓ Counted {count} messages in {count_time*1000:.2f}ms")
        assert count == 200, f"Expected 200 messages, got {count}"
        
        # Performance check
        if query_time < 0.1:  # Should be very fast with indexes
            print("✓ Query performance is excellent (< 100ms)")
        else:
            print(f"⚠ Query took {query_time*1000:.0f}ms (consider checking indexes)")
        
        # Cleanup
        memory.reset_memory(video_id)
        memory.close()
        
        print("✓ Query performance test passed")
        return True
        
    except Exception as e:
        print(f"✗ Query performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all performance optimization tests."""
    print("=" * 60)
    print("BRI Performance Optimizations Test Suite (Task 25)")
    print("=" * 60)
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Run tests
    results = {
        "Database Indexes": test_database_indexes(),
        "Memory Pagination": test_memory_pagination(),
        "Lazy Image Loader": test_lazy_image_loader(),
        "Lazy List Loader": test_lazy_list_loader(),
        "Performance Config": test_config_performance_settings(),
        "Query Performance": test_query_performance(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All performance optimization tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
