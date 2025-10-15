"""Redis caching layer for tool results."""

import json
import hashlib
import logging
from typing import Any, Optional, Dict
from datetime import timedelta

from config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manage caching of tool results using Redis."""
    
    def __init__(self):
        """Initialize cache manager with Redis connection."""
        self.enabled = Config.REDIS_ENABLED
        self.ttl = timedelta(hours=Config.CACHE_TTL_HOURS)
        self.redis_client = None
        
        if self.enabled:
            try:
                import redis
                self.redis_client = redis.from_url(
                    Config.REDIS_URL,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Redis cache enabled with TTL: {Config.CACHE_TTL_HOURS}h")
            except ImportError:
                logger.warning("Redis library not installed. Caching disabled.")
                self.enabled = False
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {str(e)}. Caching disabled.")
                self.enabled = False
        else:
            logger.info("Redis caching disabled by configuration")
    
    def generate_cache_key(
        self,
        tool_name: str,
        video_id: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Generate a unique cache key for tool execution.
        
        Args:
            tool_name: Name of the tool
            video_id: Video identifier
            parameters: Tool parameters
            
        Returns:
            Cache key string
        """
        # Create a deterministic string from parameters
        params_str = json.dumps(parameters, sort_keys=True)
        
        # Hash the parameters to keep key length manageable
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        # Format: bri:tool:{tool_name}:{video_id}:{params_hash}
        cache_key = f"bri:tool:{tool_name}:{video_id}:{params_hash}"
        
        return cache_key
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or cache disabled
        """
        if not self.enabled or self.redis_client is None:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is not None:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or self.redis_client is None:
            return False
        
        try:
            # Serialize value to JSON
            serialized_value = json.dumps(value)
            
            # Store with TTL
            self.redis_client.setex(
                key,
                self.ttl,
                serialized_value
            )
            
            logger.debug(f"Cache set: {key} (TTL: {self.ttl})")
            return True
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or self.redis_client is None:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {str(e)}")
            return False
    
    def clear_video_cache(self, video_id: str) -> int:
        """
        Clear all cached results for a specific video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or self.redis_client is None:
            return 0
        
        try:
            # Find all keys for this video
            pattern = f"bri:tool:*:{video_id}:*"
            keys = list(self.redis_client.scan_iter(match=pattern))
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries for video {video_id}")
                return deleted
            else:
                logger.debug(f"No cache entries found for video {video_id}")
                return 0
        except Exception as e:
            logger.error(f"Failed to clear cache for video {video_id}: {str(e)}")
            return 0
    
    def clear_all(self) -> bool:
        """
        Clear all BRI cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or self.redis_client is None:
            return False
        
        try:
            # Find all BRI keys
            pattern = "bri:tool:*"
            keys = list(self.redis_client.scan_iter(match=pattern))
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} total cache entries")
            else:
                logger.info("No cache entries to clear")
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear all cache: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or self.redis_client is None:
            return {
                "enabled": False,
                "total_keys": 0
            }
        
        try:
            # Count BRI cache keys
            pattern = "bri:tool:*"
            keys = list(self.redis_client.scan_iter(match=pattern))
            
            # Get Redis info
            info = self.redis_client.info()
            
            return {
                "enabled": True,
                "total_keys": len(keys),
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "ttl_hours": Config.CACHE_TTL_HOURS
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {
                "enabled": True,
                "error": str(e)
            }
    
    def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client is not None:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Failed to close Redis connection: {str(e)}")
