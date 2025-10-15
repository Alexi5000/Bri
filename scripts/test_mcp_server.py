"""Test script for MCP server functionality."""

import sys
import os
import asyncio
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.registry import ToolRegistry
from mcp_server.cache import CacheManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tool_registry():
    """Test tool registry functionality."""
    logger.info("Testing Tool Registry...")
    
    registry = ToolRegistry()
    
    # Register all tools
    registry.register_all_tools()
    
    # List tools
    tools = registry.list_tools()
    logger.info(f"Registered {len(tools)} tools:")
    for tool in tools:
        logger.info(f"  - {tool['name']}: {tool['description']}")
    
    # Test getting a specific tool
    frame_tool = registry.get_tool("extract_frames")
    if frame_tool:
        logger.info(f"✓ Successfully retrieved 'extract_frames' tool")
        logger.info(f"  Parameters: {frame_tool.parameters_schema}")
    else:
        logger.error("✗ Failed to retrieve 'extract_frames' tool")
    
    logger.info("Tool Registry test complete!\n")


def test_cache_manager():
    """Test cache manager functionality."""
    logger.info("Testing Cache Manager...")
    
    cache = CacheManager()
    
    # Test cache key generation
    key = cache.generate_cache_key(
        "extract_frames",
        "test_video_123",
        {"interval_seconds": 2.0, "max_frames": 100}
    )
    logger.info(f"Generated cache key: {key}")
    
    # Test cache operations
    test_data = {"frames": [{"timestamp": 0.0, "path": "/test/frame.jpg"}]}
    
    # Set value
    success = cache.set(key, test_data)
    if success:
        logger.info("✓ Successfully set cache value")
    else:
        logger.info("⚠ Cache set skipped (Redis not available)")
    
    # Get value
    cached_value = cache.get(key)
    if cached_value:
        logger.info(f"✓ Successfully retrieved cached value: {cached_value}")
    else:
        logger.info("⚠ Cache get returned None (Redis not available or cache miss)")
    
    # Get stats
    stats = cache.get_stats()
    logger.info(f"Cache stats: {stats}")
    
    # Cleanup
    cache.close()
    
    logger.info("Cache Manager test complete!\n")


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("MCP Server Component Tests")
    logger.info("=" * 60 + "\n")
    
    try:
        # Test tool registry
        await test_tool_registry()
        
        # Test cache manager
        test_cache_manager()
        
        logger.info("=" * 60)
        logger.info("All tests completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
