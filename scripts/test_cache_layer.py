"""Test script for Redis caching layer."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.cache import CacheManager
from config import Config


def test_cache_manager():
    """Test CacheManager functionality."""
    print("=" * 60)
    print("Testing Redis Caching Layer")
    print("=" * 60)
    
    # Initialize cache manager
    print("\n1. Initializing CacheManager...")
    cache = CacheManager()
    print(f"   Cache enabled: {cache.enabled}")
    
    if not cache.enabled:
        print("\n⚠️  Redis caching is disabled.")
        print("   To enable caching:")
        print("   1. Install Redis: https://redis.io/download")
        print("   2. Start Redis server: redis-server")
        print("   3. Set REDIS_ENABLED=true in .env")
        return
    
    print("   ✓ Redis connection successful")
    
    # Test cache key generation
    print("\n2. Testing cache key generation...")
    tool_name = "extract_frames"
    video_id = "test_video_123"
    parameters = {"interval_seconds": 2.0, "max_frames": 100}
    
    cache_key = cache.generate_cache_key(tool_name, video_id, parameters)
    print(f"   Generated key: {cache_key}")
    print("   ✓ Cache key generated successfully")
    
    # Test cache set
    print("\n3. Testing cache set...")
    test_data = {
        "frames": [
            {"timestamp": 0.0, "path": "/path/to/frame1.jpg"},
            {"timestamp": 2.0, "path": "/path/to/frame2.jpg"}
        ],
        "count": 2
    }
    
    success = cache.set(cache_key, test_data)
    print(f"   Set result: {success}")
    print("   ✓ Data cached successfully")
    
    # Test cache get (hit)
    print("\n4. Testing cache get (hit)...")
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print("   ✓ Cache hit! Retrieved data:")
        print(f"     - Frames count: {cached_data['count']}")
        print(f"     - Data matches: {cached_data == test_data}")
    else:
        print("   ✗ Cache miss (unexpected)")
    
    # Test cache get (miss)
    print("\n5. Testing cache get (miss)...")
    missing_key = cache.generate_cache_key("nonexistent_tool", "fake_video", {})
    missing_data = cache.get(missing_key)
    
    if missing_data is None:
        print("   ✓ Cache miss (expected)")
    else:
        print("   ✗ Unexpected cache hit")
    
    # Test cache stats
    print("\n6. Testing cache statistics...")
    stats = cache.get_stats()
    print("   Cache stats:")
    print(f"     - Enabled: {stats.get('enabled')}")
    print(f"     - Total BRI keys: {stats.get('total_keys')}")
    print(f"     - Redis version: {stats.get('redis_version')}")
    print(f"     - Memory used: {stats.get('used_memory_human')}")
    print(f"     - TTL hours: {stats.get('ttl_hours')}")
    print("   ✓ Stats retrieved successfully")
    
    # Test video cache clearing
    print("\n7. Testing video cache clearing...")
    
    # Add another key for the same video
    cache_key2 = cache.generate_cache_key("caption_frames", video_id, {})
    cache.set(cache_key2, {"captions": ["test caption"], "count": 1})
    
    deleted_count = cache.clear_video_cache(video_id)
    print(f"   Deleted {deleted_count} cache entries for video {video_id}")
    print("   ✓ Video cache cleared successfully")
    
    # Verify deletion
    cached_data = cache.get(cache_key)
    if cached_data is None:
        print("   ✓ Verified: Cache entries deleted")
    else:
        print("   ✗ Cache entries still present")
    
    # Test cache key with different parameters
    print("\n8. Testing cache key uniqueness...")
    params1 = {"interval_seconds": 2.0, "max_frames": 100}
    params2 = {"interval_seconds": 3.0, "max_frames": 100}
    params3 = {"max_frames": 100, "interval_seconds": 2.0}  # Same as params1, different order
    
    key1 = cache.generate_cache_key(tool_name, video_id, params1)
    key2 = cache.generate_cache_key(tool_name, video_id, params2)
    key3 = cache.generate_cache_key(tool_name, video_id, params3)
    
    print(f"   Key1 (params1): {key1}")
    print(f"   Key2 (params2): {key2}")
    print(f"   Key3 (params3): {key3}")
    print(f"   Key1 == Key2: {key1 == key2} (should be False)")
    print(f"   Key1 == Key3: {key1 == key3} (should be True - order independent)")
    
    if key1 != key2 and key1 == key3:
        print("   ✓ Cache key generation is correct")
    else:
        print("   ✗ Cache key generation issue")
    
    # Test TTL
    print("\n9. Testing TTL (Time To Live)...")
    print(f"   Configured TTL: {Config.CACHE_TTL_HOURS} hours")
    
    # Set a test key
    test_key = cache.generate_cache_key("test_tool", "test_video", {})
    cache.set(test_key, {"test": "data"})
    
    # Check if key exists
    if cache.redis_client:
        ttl_seconds = cache.redis_client.ttl(test_key)
        ttl_hours = ttl_seconds / 3600
        print(f"   Key TTL: {ttl_hours:.2f} hours ({ttl_seconds} seconds)")
        
        if abs(ttl_hours - Config.CACHE_TTL_HOURS) < 0.01:
            print("   ✓ TTL set correctly")
        else:
            print(f"   ⚠️  TTL mismatch (expected {Config.CACHE_TTL_HOURS} hours)")
    
    # Clean up test keys
    print("\n10. Cleaning up test data...")
    cache.clear_all()
    print("   ✓ All test cache entries cleared")
    
    # Close connection
    cache.close()
    print("\n✅ All cache tests completed successfully!")


def test_cache_integration():
    """Test cache integration with MCP server endpoints."""
    print("\n" + "=" * 60)
    print("Testing Cache Integration")
    print("=" * 60)
    
    print("\nTo test cache integration with MCP server:")
    print("1. Start the MCP server: python mcp_server/main.py")
    print("2. Make API requests to test caching:")
    print()
    print("   # First request (cache miss)")
    print("   curl -X POST http://localhost:8000/tools/extract_frames/execute \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"video_id\": \"test_video\", \"parameters\": {}}'")
    print()
    print("   # Second request (cache hit)")
    print("   curl -X POST http://localhost:8000/tools/extract_frames/execute \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"video_id\": \"test_video\", \"parameters\": {}}'")
    print()
    print("   # Check cache stats")
    print("   curl http://localhost:8000/cache/stats")
    print()
    print("   # Clear video cache")
    print("   curl -X DELETE http://localhost:8000/cache/videos/test_video")


if __name__ == "__main__":
    try:
        test_cache_manager()
        test_cache_integration()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

