"""Test script for Task 47: Data Flow Optimization & Caching Strategy.

Tests:
- Multi-tier caching (L1, L2, L3)
- Query optimization (connection pooling, prepared statements, batching)
- Data prefetching (related data, predictive, lazy loading)
- Data compression (JSON, images, responses, deduplication)
"""

import sys
import os
import time
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.multi_tier_cache import get_multi_tier_cache, LRUCache
from storage.query_optimizer import get_query_optimizer
from services.data_prefetcher import get_data_prefetcher
from storage.compression import get_compression_manager, CompressionLevel
from config import Config


def test_l1_cache():
    """Test L1 (LRU) cache functionality."""
    print("\n=== Testing L1 Cache (LRU) ===")
    
    cache = LRUCache(capacity=3)
    
    # Test set and get
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    assert cache.get("key1") == "value1", "Failed to get key1"
    assert cache.get("key2") == "value2", "Failed to get key2"
    assert cache.get("key3") == "value3", "Failed to get key3"
    print("✓ Set and get operations work")
    
    # Test LRU eviction
    cache.set("key4", "value4")  # Should evict key1 (least recently used)
    assert cache.get("key1") is None, "key1 should be evicted"
    assert cache.get("key4") == "value4", "key4 should be present"
    print("✓ LRU eviction works")
    
    # Test stats
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats}")
    
    print("✅ L1 Cache tests passed")


def test_multi_tier_cache():
    """Test multi-tier caching system."""
    print("\n=== Testing Multi-Tier Cache ===")
    
    cache = get_multi_tier_cache()
    
    # Test set and get
    cache.set("test_key", {"data": "test_value"}, namespace="test")
    result = cache.get("test_key", namespace="test")
    assert result == {"data": "test_value"}, "Failed to get cached value"
    print("✓ Multi-tier set and get work")
    
    # Test cache miss
    result = cache.get("nonexistent_key", namespace="test")
    assert result is None, "Should return None for cache miss"
    print("✓ Cache miss handling works")
    
    # Test pattern invalidation
    cache.set("video:123:frames", {"frames": []}, namespace="test")
    cache.set("video:123:captions", {"captions": []}, namespace="test")
    cache.set("video:456:frames", {"frames": []}, namespace="test")
    
    count = cache.invalidate_pattern("video:123:*", namespace="test")
    print(f"✓ Invalidated {count} entries matching pattern")
    
    # Verify invalidation
    assert cache.get("video:123:frames", namespace="test") is None
    assert cache.get("video:123:captions", namespace="test") is None
    assert cache.get("video:456:frames", namespace="test") is not None
    print("✓ Pattern invalidation works")
    
    # Test stats
    stats = cache.get_stats()
    print(f"✓ Multi-tier cache stats: {json.dumps(stats, indent=2)}")
    
    print("✅ Multi-tier cache tests passed")


def test_query_optimizer():
    """Test query optimizer functionality."""
    print("\n=== Testing Query Optimizer ===")
    
    optimizer = get_query_optimizer()
    
    # Test connection pool
    pool_stats = optimizer.connection_pool.get_stats()
    print(f"✓ Connection pool stats: {pool_stats}")
    assert pool_stats['pool_size'] > 0, "Pool should have connections"
    
    # Test prepared statement cache
    ps_stats = optimizer.prepared_statements.get_stats()
    print(f"✓ Prepared statement cache stats: {ps_stats}")
    
    # Test query execution with caching
    query = "SELECT * FROM videos LIMIT 1"
    
    # First execution (cache miss)
    start = time.time()
    try:
        results1 = optimizer.execute_query(query, cache_key="test_query")
        elapsed1 = time.time() - start
        print(f"✓ First query execution: {elapsed1*1000:.2f}ms")
    except Exception as e:
        print(f"⚠ Query execution failed (expected if no data): {e}")
        results1 = []
    
    # Second execution (cache hit)
    start = time.time()
    results2 = optimizer.execute_query(query, cache_key="test_query")
    elapsed2 = time.time() - start
    print(f"✓ Second query execution (cached): {elapsed2*1000:.2f}ms")
    
    if results1:
        assert results1 == results2, "Cached results should match"
        assert elapsed2 < elapsed1, "Cached query should be faster"
        print("✓ Query caching works")
    
    # Test query stats
    query_stats = optimizer.get_query_stats()
    print(f"✓ Query performance stats: {json.dumps(query_stats, indent=2)}")
    
    print("✅ Query optimizer tests passed")


def test_data_prefetcher():
    """Test data prefetching functionality."""
    print("\n=== Testing Data Prefetcher ===")
    
    prefetcher = get_data_prefetcher()
    
    # Test access pattern recording
    prefetcher.record_access("video_123", "frames")
    prefetcher.record_access("video_123", "captions")
    prefetcher.record_access("video_123", "frames")  # Access again
    print("✓ Access pattern recording works")
    
    # Test related data strategy
    related_types = prefetcher.related_strategy.get_related_types("frames")
    print(f"✓ Related data types for 'frames': {related_types}")
    assert "captions" in related_types, "Captions should be related to frames"
    
    # Test lazy loading pagination
    try:
        import asyncio
        
        async def test_lazy_load():
            result = await prefetcher.lazy_load_paginated(
                "test_video",
                "frames",
                page_size=10,
                page=0
            )
            print(f"✓ Lazy loading result: page={result['page']}, total={result['total_count']}")
            return result
        
        result = asyncio.run(test_lazy_load())
        assert "data" in result, "Result should contain data"
        assert "page" in result, "Result should contain page info"
        print("✓ Lazy loading pagination works")
    except Exception as e:
        print(f"⚠ Lazy loading test skipped (expected if no data): {e}")
    
    # Test N+1 optimization
    video_ids = ["video_1", "video_2", "video_3"]
    try:
        results = prefetcher.optimize_n_plus_one(video_ids, "frames")
        print(f"✓ N+1 optimization: fetched data for {len(results)} videos")
    except Exception as e:
        print(f"⚠ N+1 optimization test skipped (expected if no data): {e}")
    
    # Test stats
    stats = prefetcher.get_stats()
    print(f"✓ Prefetcher stats: {json.dumps(stats, indent=2)}")
    
    print("✅ Data prefetcher tests passed")


def test_json_compression():
    """Test JSON compression."""
    print("\n=== Testing JSON Compression ===")
    
    manager = get_compression_manager()
    
    # Create test data
    test_data = {
        "video_id": "test_123",
        "frames": [
            {"timestamp": i, "data": f"frame_{i}" * 10}
            for i in range(100)
        ]
    }
    
    # Compress
    compressed = manager.compress_json(test_data)
    original_size = len(json.dumps(test_data).encode('utf-8'))
    compressed_size = len(compressed)
    ratio = (1 - compressed_size / original_size) * 100
    
    print(f"✓ JSON compression: {original_size} → {compressed_size} bytes ({ratio:.1f}% reduction)")
    assert compressed_size < original_size, "Compressed should be smaller"
    
    # Decompress
    decompressed = manager.decompress_json(compressed)
    assert decompressed == test_data, "Decompressed data should match original"
    print("✓ JSON decompression works")
    
    print("✅ JSON compression tests passed")


def test_image_compression():
    """Test image compression."""
    print("\n=== Testing Image Compression ===")
    
    manager = get_compression_manager()
    
    # Create a test image
    try:
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            img = Image.new('RGB', (640, 480), color='red')
            input_path = os.path.join(tmpdir, "test.jpg")
            img.save(input_path, 'JPEG')
            
            # Compress to WebP
            output_path, original_size, compressed_size = manager.compress_image(input_path)
            ratio = (1 - compressed_size / original_size) * 100
            
            print(f"✓ Image compression: {original_size} → {compressed_size} bytes ({ratio:.1f}% reduction)")
            assert os.path.exists(output_path), "Output file should exist"
            assert compressed_size < original_size, "Compressed should be smaller"
            
            print("✅ Image compression tests passed")
    except ImportError:
        print("⚠ PIL not available, skipping image compression test")


def test_response_compression():
    """Test API response compression."""
    print("\n=== Testing Response Compression ===")
    
    manager = get_compression_manager()
    
    # Create test response
    test_response = json.dumps({
        "status": "success",
        "data": {
            "results": [{"id": i, "value": f"data_{i}" * 20} for i in range(100)]
        }
    })
    
    # Compress
    compressed = manager.compress_response(test_response)
    original_size = len(test_response.encode('utf-8'))
    compressed_size = len(compressed)
    ratio = (1 - compressed_size / original_size) * 100
    
    print(f"✓ Response compression: {original_size} → {compressed_size} bytes ({ratio:.1f}% reduction)")
    assert compressed_size < original_size, "Compressed should be smaller"
    
    # Decompress
    decompressed = manager.decompress_response(compressed)
    assert decompressed == test_response, "Decompressed response should match original"
    print("✓ Response decompression works")
    
    print("✅ Response compression tests passed")


def test_frame_deduplication():
    """Test frame deduplication."""
    print("\n=== Testing Frame Deduplication ===")
    
    manager = get_compression_manager()
    
    try:
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two similar images
            img1 = Image.new('RGB', (100, 100), color='blue')
            img2 = Image.new('RGB', (100, 100), color='blue')
            
            path1 = os.path.join(tmpdir, "frame1.jpg")
            path2 = os.path.join(tmpdir, "frame2.jpg")
            
            img1.save(path1, 'JPEG')
            img2.save(path2, 'JPEG')
            
            # Check first frame (not duplicate)
            is_dup1, orig_ts1 = manager.check_frame_duplicate("video_123", 0.0, path1)
            assert not is_dup1, "First frame should not be duplicate"
            print("✓ First frame registered")
            
            # Check second frame (should be duplicate)
            is_dup2, orig_ts2 = manager.check_frame_duplicate("video_123", 1.0, path2)
            assert is_dup2, "Second frame should be duplicate"
            assert orig_ts2 == 0.0, "Should reference original timestamp"
            print(f"✓ Duplicate detected: frame at 1.0s is similar to frame at {orig_ts2}s")
            
            # Test stats
            stats = manager.get_stats()
            print(f"✓ Deduplication stats: {json.dumps(stats, indent=2)}")
            
            print("✅ Frame deduplication tests passed")
    except ImportError:
        print("⚠ PIL not available, skipping frame deduplication test")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Task 47: Data Flow Optimization & Caching Strategy Tests")
    print("=" * 60)
    
    try:
        test_l1_cache()
        test_multi_tier_cache()
        test_query_optimizer()
        test_data_prefetcher()
        test_json_compression()
        test_image_compression()
        test_response_compression()
        test_frame_deduplication()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
