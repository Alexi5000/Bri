"""
Test script for Task 41: Data Pipeline Integrity & Validation
Verifies transactional writes, validation, consistency checks, and lineage tracking
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force reload to get latest changes
import importlib
import storage.database

importlib.reload(storage.database)

from storage.database import Database, get_database, initialize_database
from services.video_processing_service import VideoProcessingService
from services.data_validator import get_data_validator
from services.data_consistency_checker import get_consistency_checker
from services.data_lineage_tracker import get_lineage_tracker
from utils.logging_config import get_logger

logger = get_logger(__name__)


def test_transactional_writes():
    """Test 41.1: Transactional data writes with savepoints"""
    print("\n=== Testing Transactional Writes ===")

    db = get_database()

    # Test transaction with savepoint
    try:
        with db.transaction(isolation_level="IMMEDIATE") as txn:
            cursor = txn.cursor()

            # Create savepoint
            sp = txn.savepoint()
            print(f"✓ Created savepoint: {sp}")

            # Try to insert test data
            cursor.execute(
                "INSERT INTO videos (video_id, filename, file_path, duration) VALUES (?, ?, ?, ?)",
                ("test_txn_vid", "test.mp4", "/tmp/test.mp4", 60.0),
            )

            # Release savepoint
            txn.release_savepoint(sp)
            print("✓ Released savepoint successfully")

        print("✓ Transaction committed successfully")

        # Clean up
        db.execute_update("DELETE FROM videos WHERE video_id = ?", ("test_txn_vid",))

    except Exception as e:
        print(f"✗ Transaction test failed: {e}")
        return False

    return True


def test_data_validation():
    """Test 41.2: Data validation layer"""
    print("\n=== Testing Data Validation ===")

    validator = get_data_validator()

    # Test valid frame data
    valid_frame = {"timestamp": 1.5, "frame_number": 1, "image_path": "/tmp/frame_001.jpg"}
    valid, error = validator.validate_frame(valid_frame)
    if valid:
        print("✓ Valid frame data passed validation")
    else:
        print(f"✗ Valid frame failed: {error}")
        return False

    # Test invalid frame data (missing required field)
    invalid_frame = {
        "timestamp": 1.5
        # Missing frame_number
    }
    valid, error = validator.validate_frame(invalid_frame)
    if not valid:
        print(f"✓ Invalid frame correctly rejected: {error}")
    else:
        print("✗ Invalid frame incorrectly accepted")
        return False

    # Test valid caption data
    valid_caption = {
        "frame_timestamp": 1.5,
        "text": "A person walking in a park",
        "confidence": 0.95,
    }
    valid, error = validator.validate_caption(valid_caption)
    if valid:
        print("✓ Valid caption data passed validation")
    else:
        print(f"✗ Valid caption failed: {error}")
        return False

    # Test invalid caption (empty text)
    invalid_caption = {
        "frame_timestamp": 1.5,
        "text": "   ",  # Empty after strip
        "confidence": 0.95,
    }
    valid, error = validator.validate_caption(invalid_caption)
    if not valid:
        print(f"✓ Invalid caption correctly rejected: {error}")
    else:
        print("✗ Invalid caption incorrectly accepted")
        return False

    # Test valid transcript
    valid_transcript = {"start": 1.0, "end": 3.0, "text": "Hello world", "confidence": 0.9}
    valid, error = validator.validate_transcript(valid_transcript)
    if valid:
        print("✓ Valid transcript data passed validation")
    else:
        print(f"✗ Valid transcript failed: {error}")
        return False

    # Test invalid transcript (end <= start)
    invalid_transcript = {
        "start": 3.0,
        "end": 1.0,  # End before start
        "text": "Hello world",
    }
    valid, error = validator.validate_transcript(invalid_transcript)
    if not valid:
        print(f"✓ Invalid transcript correctly rejected: {error}")
    else:
        print("✗ Invalid transcript incorrectly accepted")
        return False

    # Test timestamp ordering
    timestamps = [0.0, 1.5, 3.0, 4.5]
    valid, error = validator.validate_timestamp_ordering(timestamps)
    if valid:
        print("✓ Timestamp ordering validation passed")
    else:
        print(f"✗ Timestamp ordering failed: {error}")
        return False

    # Test out-of-order timestamps
    bad_timestamps = [0.0, 3.0, 1.5, 4.5]
    valid, error = validator.validate_timestamp_ordering(bad_timestamps)
    if not valid:
        print(f"✓ Out-of-order timestamps correctly detected: {error}")
    else:
        print("✗ Out-of-order timestamps not detected")
        return False

    return True


def test_consistency_checks():
    """Test 41.3: Data consistency checks"""
    print("\n=== Testing Data Consistency Checks ===")

    checker = get_consistency_checker()
    db = get_database()

    # Create test video
    test_video_id = "test_consistency_vid"
    try:
        db.execute_update(
            "INSERT INTO videos (video_id, filename, file_path, duration) VALUES (?, ?, ?, ?)",
            (test_video_id, "test.mp4", "/tmp/test.mp4", 60.0),
        )
        print(f"✓ Created test video: {test_video_id}")

        # Run consistency check (should pass with no data)
        report = checker.check_video_consistency(test_video_id)
        print(f"✓ Consistency check completed: {report['consistent']}")
        print(f"  Checks: {list(report['checks'].keys())}")

        # Clean up
        db.execute_update("DELETE FROM videos WHERE video_id = ?", (test_video_id,))
        print("✓ Cleaned up test video")

    except Exception as e:
        print(f"✗ Consistency check test failed: {e}")
        return False

    return True


def test_lineage_tracking():
    """Test 41.4: Data lineage tracking"""
    print("\n=== Testing Data Lineage Tracking ===")

    tracker = get_lineage_tracker()
    db = get_database()

    # Create test video
    test_video_id = "test_lineage_vid"
    try:
        db.execute_update(
            "INSERT INTO videos (video_id, filename, file_path, duration) VALUES (?, ?, ?, ?)",
            (test_video_id, "test.mp4", "/tmp/test.mp4", 60.0),
        )
        print(f"✓ Created test video: {test_video_id}")

        # Record processing
        lineage_id = tracker.record_processing(
            video_id=test_video_id,
            context_id="test_context_123",
            tool_name="extract_frames",
            parameters={"interval": 2.0, "max_frames": 100},
        )
        print(f"✓ Recorded lineage: {lineage_id}")

        # Get lineage history
        history = tracker.get_lineage_history(test_video_id)
        if len(history) > 0:
            print(f"✓ Retrieved lineage history: {len(history)} records")
            print(f"  Latest: {history[0]['tool_name']} v{history[0]['tool_version']}")
        else:
            print("✗ No lineage history found")
            return False

        # Get reproducibility info
        info = tracker.get_reproducibility_info(test_video_id)
        print(f"✓ Reproducibility info: {info['reproducible']}")
        print(f"  Tools used: {len(info.get('tools_used', []))}")

        # Clean up
        db.execute_update("DELETE FROM data_lineage WHERE video_id = ?", (test_video_id,))
        db.execute_update("DELETE FROM videos WHERE video_id = ?", (test_video_id,))
        print("✓ Cleaned up test data")

    except Exception as e:
        print(f"✗ Lineage tracking test failed: {e}")
        return False

    return True


def test_idempotency():
    """Test idempotency in VideoProcessingService"""
    print("\n=== Testing Idempotency ===")

    service = VideoProcessingService()
    db = get_database()

    # Create test video
    test_video_id = "test_idempotency_vid"
    try:
        db.execute_update(
            "INSERT INTO videos (video_id, filename, file_path, duration) VALUES (?, ?, ?, ?)",
            (test_video_id, "test.mp4", "/tmp/test.mp4", 60.0),
        )
        print(f"✓ Created test video: {test_video_id}")

        # Store frames with idempotency key
        frames_data = {
            "frames": [
                {"timestamp": 0.0, "frame_number": 0, "image_path": "/tmp/frame_000.jpg"},
                {"timestamp": 2.0, "frame_number": 1, "image_path": "/tmp/frame_001.jpg"},
            ]
        }

        result1 = service.store_tool_results(
            video_id=test_video_id,
            tool_name="extract_frames",
            results=frames_data,
            idempotency_key="test_key_123",
        )
        print(f"✓ First store: {result1}")

        # Try to store again with same idempotency key (should skip)
        result2 = service.store_tool_results(
            video_id=test_video_id,
            tool_name="extract_frames",
            results=frames_data,
            idempotency_key="test_key_123",
        )
        print(f"✓ Second store (idempotent): {result2}")

        # Verify only one set of frames stored
        count_query = """
            SELECT COUNT(*) FROM video_context
            WHERE video_id = ? AND context_type = 'frame'
        """
        rows = db.execute_query(count_query, (test_video_id,))
        frame_count = rows[0][0] if rows else 0

        if frame_count == 2:
            print(f"✓ Idempotency working: {frame_count} frames (not duplicated)")
        else:
            print(f"✗ Idempotency failed: {frame_count} frames (expected 2)")
            return False

        # Clean up
        db.execute_update("DELETE FROM video_context WHERE video_id = ?", (test_video_id,))
        db.execute_update("DELETE FROM videos WHERE video_id = ?", (test_video_id,))
        print("✓ Cleaned up test data")

    except Exception as e:
        print(f"✗ Idempotency test failed: {e}")
        return False

    return True


def main():
    """Run all Task 41 tests"""
    print("=" * 60)
    print("Task 41: Data Pipeline Integrity & Validation - Test Suite")
    print("=" * 60)

    # Initialize database
    try:
        # Try to initialize, but if it fails because tables exist, that's okay
        try:
            initialize_database()
            print("✓ Database initialized")
        except Exception as init_error:
            # Database might already be initialized
            print(f"⚠️  Database initialization warning: {init_error}")
            print("   Continuing with existing database...")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Run tests
    tests = [
        ("41.1 Transactional Writes", test_transactional_writes),
        ("41.2 Data Validation", test_data_validation),
        ("41.3 Consistency Checks", test_consistency_checks),
        ("41.4 Lineage Tracking", test_lineage_tracking),
        ("Idempotency", test_idempotency),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Task 41 tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
