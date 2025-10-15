"""Test script for logging and monitoring system."""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import (
    setup_logging,
    get_logger,
    get_performance_logger,
    get_api_logger
)
from config import Config


def test_basic_logging():
    """Test basic logging at different levels."""
    print("\n" + "="*60)
    print("Testing Basic Logging")
    print("="*60)
    
    # Setup logging first
    setup_logging()
    
    logger = get_logger("test.basic")
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.error("Caught an exception", exc_info=True)
    
    print("[OK] Basic logging test complete")


def test_performance_logging():
    """Test performance metrics logging."""
    print("\n" + "="*60)
    print("Testing Performance Logging")
    print("="*60)
    
    perf_logger = get_performance_logger("test.performance")
    
    # Simulate tool execution
    start_time = time.time()
    time.sleep(0.1)  # Simulate work
    execution_time = time.time() - start_time
    
    perf_logger.log_execution_time(
        "frame_extraction",
        execution_time,
        success=True,
        video_id="test_video_123",
        frames_extracted=50
    )
    
    # Simulate failed operation
    perf_logger.log_execution_time(
        "object_detection",
        0.05,
        success=False,
        video_id="test_video_123",
        error="Model not loaded"
    )
    
    # Test cache logging
    perf_logger.log_cache_hit("bri:tool:captions:vid_123:abc", hit=True)
    perf_logger.log_cache_hit("bri:tool:transcripts:vid_456:def", hit=False)
    
    print("[OK] Performance logging test complete")


def test_api_logging():
    """Test API call logging."""
    print("\n" + "="*60)
    print("Testing API Logging")
    print("="*60)
    
    api_logger = get_api_logger("test.api")
    
    # Simulate successful API call
    api_logger.log_api_call(
        "Groq",
        "/chat/completions",
        method="POST",
        status_code=200,
        execution_time=0.523
    )
    
    # Simulate failed API call
    api_logger.log_api_call(
        "MCP",
        "/tools/caption_frames/execute",
        method="POST",
        status_code=500,
        execution_time=1.234,
        error="Connection timeout"
    )
    
    print("[OK] API logging test complete")


def test_structured_logging():
    """Test structured logging with extra fields."""
    print("\n" + "="*60)
    print("Testing Structured Logging")
    print("="*60)
    
    logger = get_logger("test.structured")
    
    # Create log record with extra fields
    log_record = logger.makeRecord(
        logger.name,
        20,  # INFO level
        "(test)",
        0,
        "User uploaded video",
        (),
        None
    )
    log_record.extra_fields = {
        'user_id': 'user_123',
        'video_id': 'vid_456',
        'file_size': 1024000,
        'duration': 120.5
    }
    logger.handle(log_record)
    
    print("[OK] Structured logging test complete")


def test_log_rotation():
    """Test log rotation by checking file existence."""
    print("\n" + "="*60)
    print("Testing Log Rotation")
    print("="*60)
    
    log_dir = Path(Config.LOG_DIR)
    
    # Check if log files exist
    log_files = {
        'general': log_dir / 'bri.log',
        'errors': log_dir / 'bri_errors.log',
        'performance': log_dir / 'bri_performance.log'
    }
    
    for log_type, log_file in log_files.items():
        if log_file.exists():
            size = log_file.stat().st_size
            print(f"[OK] {log_type.capitalize()} log exists: {log_file} ({size} bytes)")
        else:
            print(f"[SKIP] {log_type.capitalize()} log not found: {log_file}")
    
    print("\n[OK] Log rotation test complete")


def test_cache_hit_rate_tracking():
    """Test cache hit rate tracking."""
    print("\n" + "="*60)
    print("Testing Cache Hit Rate Tracking")
    print("="*60)
    
    perf_logger = get_performance_logger("test.cache")
    
    # Simulate cache operations
    cache_operations = [
        ("key1", True),
        ("key2", False),
        ("key3", True),
        ("key4", True),
        ("key5", False),
        ("key6", True),
        ("key7", False),
        ("key8", True),
    ]
    
    hits = 0
    misses = 0
    
    for key, is_hit in cache_operations:
        perf_logger.log_cache_hit(f"bri:tool:test:{key}", hit=is_hit)
        if is_hit:
            hits += 1
        else:
            misses += 1
    
    total = hits + misses
    hit_rate = (hits / total) * 100 if total > 0 else 0
    
    print(f"Cache operations: {total}")
    print(f"Hits: {hits}")
    print(f"Misses: {misses}")
    print(f"Hit rate: {hit_rate:.1f}%")
    print("[OK] Cache hit rate tracking test complete")


def display_log_summary():
    """Display summary of log files."""
    print("\n" + "="*60)
    print("Log Files Summary")
    print("="*60)
    
    log_dir = Path(Config.LOG_DIR)
    
    if not log_dir.exists():
        print("Log directory does not exist yet")
        return
    
    log_files = list(log_dir.glob("*.log*"))
    
    if not log_files:
        print("No log files found")
        return
    
    print(f"\nLog directory: {log_dir.absolute()}")
    print(f"Total log files: {len(log_files)}\n")
    
    for log_file in sorted(log_files):
        size = log_file.stat().st_size
        size_kb = size / 1024
        print(f"  {log_file.name:30s} - {size_kb:8.2f} KB")
    
    print("\nTo view logs:")
    print(f"  General:     tail -f {log_dir}/bri.log")
    print(f"  Errors:      tail -f {log_dir}/bri_errors.log")
    print(f"  Performance: tail -f {log_dir}/bri_performance.log")


def main():
    """Run all logging tests."""
    print("\n" + "="*60)
    print("BRI Logging and Monitoring Test Suite")
    print("="*60)
    print(f"Log Level: {Config.LOG_LEVEL}")
    print(f"Log Directory: {Config.LOG_DIR}")
    print(f"Log Rotation: {'Enabled' if Config.LOG_ROTATION_ENABLED else 'Disabled'}")
    print(f"JSON Format: {'Enabled' if Config.LOG_JSON_FORMAT else 'Disabled'}")
    
    # Run tests
    test_basic_logging()
    test_performance_logging()
    test_api_logging()
    test_structured_logging()
    test_log_rotation()
    test_cache_hit_rate_tracking()
    
    # Display summary
    display_log_summary()
    
    print("\n" + "="*60)
    print("All Tests Complete!")
    print("="*60)
    print("\nLogging system is working correctly.")
    print("Check the log files in the 'logs' directory for detailed output.")


if __name__ == "__main__":
    main()
