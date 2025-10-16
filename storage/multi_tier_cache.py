"""Multi-tier caching system for BRI video agent.

Implements a 3-tier caching strategy:
- L1 Cache: In-memory LRU cache for hot data (fastest)
- L2 Cache: Redis for shared cache across instances (fast)
- L3 Cache: Database query result cache (medium)

Cache invalidation uses TTL + event-based strategies.
"""

import time
from typing import Any, Optional, Dict, List
from collections import OrderedDict
from threading import Lock

from config import Config
from utils.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache implementation.
    
    Provides O(1) get and set operations with automatic eviction of
    least recently used items when capacity is reached.
    """
    
    def __init__(self, capacity: int = 100):
        """Initialize LRU cache.
        
        Args:
            capacity: Maximum number of items to store
        """
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        
        logger.info(f"L1 Cache (LRU) initialized with capacity: {capacity}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                logger.debug(f"L1 cache hit: {key}")
                return self.cache[key]
            else:
                self.misses += 1
                logger.debug(f"L1 cache miss: {key}")
                return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache.move_to_end(key)
            else:
                # Add new key
                if len(self.cache) >= self.capacity:
                    # Remove least recently used item
                    evicted_key = next(iter(self.cache))
                    del self.cache[evicted_key]
                    logger.debug(f"L1 cache evicted: {evicted_key}")
            
            self.cache[key] = value
            logger.debug(f"L1 cache set: {key}")
    
    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"L1 cache deleted: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("L1 cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "capacity": self.capacity,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%",
                "utilization": f"{len(self.cache) / self.capacity * 100:.1f}%"
            }


class MultiTierCache:
    """Multi-tier caching system with L1 (memory), L2 (Redis), and L3 (DB query cache).
    
    Cache lookup order: L1 → L2 → L3 → Source
    Cache write order: Source → L3 → L2 → L1
    
    Features:
    - Automatic cache warming for frequently accessed data
    - TTL-based expiration
    - Event-based invalidation
    - Cache statistics and monitoring
    """
    
    def __init__(
        self,
        l1_capacity: int = 100,
        l2_enabled: bool = None,
        l3_enabled: bool = True
    ):
        """Initialize multi-tier cache.
        
        Args:
            l1_capacity: L1 cache capacity (number of items)
            l2_enabled: Enable L2 (Redis) cache. Uses Config.REDIS_ENABLED if None
            l3_enabled: Enable L3 (database query) cache
        """
        # L1 Cache: In-memory LRU
        self.l1_cache = LRUCache(capacity=l1_capacity)
        
        # L2 Cache: Redis
        self.l2_enabled = l2_enabled if l2_enabled is not None else Config.REDIS_ENABLED
        self.l2_cache = None
        
        if self.l2_enabled:
            try:
                from mcp_server.cache import CacheManager
                self.l2_cache = CacheManager()
                logger.info("L2 Cache (Redis) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize L2 cache: {e}")
                self.l2_enabled = False
        
        # L3 Cache: Database query cache
        self.l3_enabled = l3_enabled
        self.l3_cache: Dict[str, Any] = {}
        self.l3_cache_ttl: Dict[str, float] = {}
        self.l3_lock = Lock()
        self.l3_default_ttl = 300  # 5 minutes
        
        if self.l3_enabled:
            logger.info("L3 Cache (DB query) initialized")
        
        # Cache warming configuration
        self.warm_cache_enabled = True
        self.warm_cache_keys: List[str] = []
        
        logger.info(
            f"Multi-tier cache initialized: "
            f"L1={True}, L2={self.l2_enabled}, L3={self.l3_enabled}"
        )
    
    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache (checks L1 → L2 → L3).
        
        Args:
            key: Cache key
            namespace: Cache namespace for organization
            
        Returns:
            Cached value or None if not found
        """
        full_key = f"{namespace}:{key}"
        start_time = time.time()
        
        # Try L1 cache first (fastest)
        value = self.l1_cache.get(full_key)
        if value is not None:
            perf_logger.log_cache_hit(f"{full_key}:L1", hit=True)
            logger.debug(f"Cache hit (L1): {full_key}")
            return value
        
        # Try L2 cache (Redis)
        if self.l2_enabled and self.l2_cache:
            value = self.l2_cache.get(full_key)
            if value is not None:
                # Promote to L1
                self.l1_cache.set(full_key, value)
                perf_logger.log_cache_hit(f"{full_key}:L2", hit=True)
                logger.debug(f"Cache hit (L2): {full_key}, promoted to L1")
                return value
        
        # Try L3 cache (DB query cache)
        if self.l3_enabled:
            value = self._get_l3(full_key)
            if value is not None:
                # Promote to L2 and L1
                if self.l2_enabled and self.l2_cache:
                    self.l2_cache.set(full_key, value)
                self.l1_cache.set(full_key, value)
                perf_logger.log_cache_hit(f"{full_key}:L3", hit=True)
                logger.debug(f"Cache hit (L3): {full_key}, promoted to L2 and L1")
                return value
        
        # Cache miss
        elapsed = time.time() - start_time
        perf_logger.log_cache_hit(full_key, hit=False)
        logger.debug(f"Cache miss: {full_key} (checked in {elapsed*1000:.1f}ms)")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None
    ) -> None:
        """Set value in all cache tiers.
        
        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace
            ttl: Time-to-live in seconds (None = use defaults)
        """
        full_key = f"{namespace}:{key}"
        
        # Set in L1 (always)
        self.l1_cache.set(full_key, value)
        
        # Set in L2 (Redis)
        if self.l2_enabled and self.l2_cache:
            self.l2_cache.set(full_key, value)
        
        # Set in L3 (DB query cache)
        if self.l3_enabled:
            self._set_l3(full_key, value, ttl or self.l3_default_ttl)
        
        logger.debug(f"Cache set (all tiers): {full_key}")
    
    def delete(self, key: str, namespace: str = "default") -> None:
        """Delete value from all cache tiers.
        
        Args:
            key: Cache key
            namespace: Cache namespace
        """
        full_key = f"{namespace}:{key}"
        
        # Delete from L1
        self.l1_cache.delete(full_key)
        
        # Delete from L2
        if self.l2_enabled and self.l2_cache:
            self.l2_cache.delete(full_key)
        
        # Delete from L3
        if self.l3_enabled:
            self._delete_l3(full_key)
        
        logger.debug(f"Cache deleted (all tiers): {full_key}")
    
    def invalidate_pattern(self, pattern: str, namespace: str = "default") -> int:
        """Invalidate all keys matching a pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            namespace: Cache namespace
            
        Returns:
            Number of keys invalidated
        """
        full_pattern = f"{namespace}:{pattern}"
        count = 0
        
        # Invalidate L1 (check all keys)
        with self.l1_cache.lock:
            keys_to_delete = [
                k for k in self.l1_cache.cache.keys()
                if self._matches_pattern(k, full_pattern)
            ]
            for key in keys_to_delete:
                del self.l1_cache.cache[key]
                count += 1
        
        # Invalidate L2 (Redis pattern matching)
        if self.l2_enabled and self.l2_cache and self.l2_cache.redis_client:
            try:
                keys = list(self.l2_cache.redis_client.scan_iter(match=full_pattern))
                if keys:
                    deleted = self.l2_cache.redis_client.delete(*keys)
                    count += deleted
            except Exception as e:
                logger.error(f"Failed to invalidate L2 pattern: {e}")
        
        # Invalidate L3
        if self.l3_enabled:
            with self.l3_lock:
                keys_to_delete = [
                    k for k in self.l3_cache.keys()
                    if self._matches_pattern(k, full_pattern)
                ]
                for key in keys_to_delete:
                    del self.l3_cache[key]
                    if key in self.l3_cache_ttl:
                        del self.l3_cache_ttl[key]
                    count += 1
        
        logger.info(f"Invalidated {count} cache entries matching pattern: {full_pattern}")
        return count
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple wildcard support).
        
        Args:
            key: Cache key
            pattern: Pattern with * wildcards
            
        Returns:
            True if key matches pattern
        """
        import re
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace("*", ".*")
        return re.match(f"^{regex_pattern}$", key) is not None
    
    def _get_l3(self, key: str) -> Optional[Any]:
        """Get value from L3 cache with TTL check.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self.l3_lock:
            if key in self.l3_cache:
                # Check TTL
                if key in self.l3_cache_ttl:
                    if time.time() > self.l3_cache_ttl[key]:
                        # Expired
                        del self.l3_cache[key]
                        del self.l3_cache_ttl[key]
                        return None
                
                return self.l3_cache[key]
            return None
    
    def _set_l3(self, key: str, value: Any, ttl: int) -> None:
        """Set value in L3 cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        with self.l3_lock:
            self.l3_cache[key] = value
            self.l3_cache_ttl[key] = time.time() + ttl
    
    def _delete_l3(self, key: str) -> None:
        """Delete value from L3 cache.
        
        Args:
            key: Cache key
        """
        with self.l3_lock:
            if key in self.l3_cache:
                del self.l3_cache[key]
            if key in self.l3_cache_ttl:
                del self.l3_cache_ttl[key]
    
    def warm_cache(self, keys: List[str], loader) -> None:
        """Warm cache with frequently accessed data.
        
        Args:
            keys: List of keys to warm
            loader: Function to load data for a key
        """
        if not self.warm_cache_enabled:
            return
        
        logger.info(f"Warming cache with {len(keys)} keys...")
        warmed = 0
        
        for key in keys:
            try:
                # Check if already cached
                if self.get(key) is not None:
                    continue
                
                # Load and cache data
                value = loader(key)
                if value is not None:
                    self.set(key, value)
                    warmed += 1
            except Exception as e:
                logger.error(f"Failed to warm cache for key {key}: {e}")
        
        logger.info(f"Cache warming complete: {warmed}/{len(keys)} keys loaded")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics.
        
        Returns:
            Dictionary with stats for all cache tiers
        """
        stats = {
            "l1": self.l1_cache.get_stats(),
            "l2": {"enabled": self.l2_enabled},
            "l3": {"enabled": self.l3_enabled}
        }
        
        # L2 stats
        if self.l2_enabled and self.l2_cache:
            try:
                stats["l2"].update(self.l2_cache.get_stats())
            except Exception as e:
                stats["l2"]["error"] = str(e)
        
        # L3 stats
        if self.l3_enabled:
            with self.l3_lock:
                # Clean expired entries
                current_time = time.time()
                expired_keys = [
                    k for k, ttl in self.l3_cache_ttl.items()
                    if current_time > ttl
                ]
                for key in expired_keys:
                    del self.l3_cache[key]
                    del self.l3_cache_ttl[key]
                
                stats["l3"]["size"] = len(self.l3_cache)
                stats["l3"]["expired_cleaned"] = len(expired_keys)
        
        return stats
    
    def clear_all(self) -> None:
        """Clear all cache tiers."""
        self.l1_cache.clear()
        
        if self.l2_enabled and self.l2_cache:
            self.l2_cache.clear_all()
        
        if self.l3_enabled:
            with self.l3_lock:
                self.l3_cache.clear()
                self.l3_cache_ttl.clear()
        
        logger.info("All cache tiers cleared")


# Global multi-tier cache instance
_multi_tier_cache: Optional[MultiTierCache] = None


def get_multi_tier_cache() -> MultiTierCache:
    """Get or create global multi-tier cache instance.
    
    Returns:
        MultiTierCache instance
    """
    global _multi_tier_cache
    if _multi_tier_cache is None:
        _multi_tier_cache = MultiTierCache(
            l1_capacity=100,
            l2_enabled=Config.REDIS_ENABLED,
            l3_enabled=True
        )
    return _multi_tier_cache
