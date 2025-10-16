"""Performance optimization for vector search and retrieval."""

import logging
import time
from typing import List, Optional, Dict, Any, Tuple
from collections import OrderedDict
import hashlib

logger = logging.getLogger(__name__)


class QueryCache:
    """LRU cache for query results with TTL support.
    
    Caches semantic search results to avoid recomputing embeddings
    and performing vector searches for repeated queries.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize query cache.
        
        Args:
            max_size: Maximum number of cached queries
            ttl_seconds: Time-to-live for cached results in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, query: str, video_id: Optional[str], top_k: int) -> str:
        """Generate cache key from query parameters."""
        key_str = f"{query}|{video_id}|{top_k}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(
        self,
        query: str,
        video_id: Optional[str] = None,
        top_k: int = 5
    ) -> Optional[List[Any]]:
        """Get cached results for a query.
        
        Args:
            query: Search query
            video_id: Optional video ID filter
            top_k: Number of results
            
        Returns:
            Cached results or None if not found/expired
        """
        key = self._make_key(query, video_id, top_k)
        
        if key in self.cache:
            results, timestamp = self.cache[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return results
        
        self.misses += 1
        return None
    
    def put(
        self,
        query: str,
        results: List[Any],
        video_id: Optional[str] = None,
        top_k: int = 5
    ) -> None:
        """Cache query results.
        
        Args:
            query: Search query
            results: Search results to cache
            video_id: Optional video ID filter
            top_k: Number of results
        """
        key = self._make_key(query, video_id, top_k)
        
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = (results, time.time())
    
    def invalidate(self, video_id: Optional[str] = None) -> None:
        """Invalidate cache entries.
        
        Args:
            video_id: If provided, only invalidate entries for this video.
                     If None, clear entire cache.
        """
        if video_id is None:
            self.cache.clear()
            logger.info("Query cache cleared")
        else:
            # Remove entries containing this video_id
            keys_to_remove = [
                key for key in self.cache.keys()
                if video_id in key
            ]
            for key in keys_to_remove:
                del self.cache[key]
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries for video {video_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds
        }


class VectorSearchOptimizer:
    """Optimizer for vector search performance.
    
    Features:
    - Query result caching
    - Approximate nearest neighbor (ANN) search
    - Index optimization recommendations
    - Performance monitoring and metrics
    - A/B testing support for search quality
    """
    
    def __init__(
        self,
        enable_cache: bool = True,
        cache_size: int = 1000,
        cache_ttl: int = 3600
    ):
        """Initialize vector search optimizer.
        
        Args:
            enable_cache: Whether to enable query caching
            cache_size: Maximum number of cached queries
            cache_ttl: Cache time-to-live in seconds
        """
        self.enable_cache = enable_cache
        self.query_cache = QueryCache(max_size=cache_size, ttl_seconds=cache_ttl) if enable_cache else None
        
        # Performance metrics
        self.query_times: List[float] = []
        self.max_query_time_history = 1000
        
        logger.info(f"Vector search optimizer initialized (cache: {enable_cache})")
    
    def search_with_cache(
        self,
        search_func: callable,
        query: str,
        video_id: Optional[str] = None,
        top_k: int = 5,
        **kwargs
    ) -> Tuple[List[Any], bool]:
        """Perform search with caching.
        
        Args:
            search_func: Function to call for actual search
            query: Search query
            video_id: Optional video ID filter
            top_k: Number of results
            **kwargs: Additional arguments to pass to search_func
            
        Returns:
            Tuple of (results, was_cached)
        """
        # Check cache first
        if self.enable_cache and self.query_cache:
            cached_results = self.query_cache.get(query, video_id, top_k)
            if cached_results is not None:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_results, True
        
        # Perform actual search
        start_time = time.time()
        results = search_func(query=query, video_id=video_id, top_k=top_k, **kwargs)
        query_time = time.time() - start_time
        
        # Track performance
        self._record_query_time(query_time)
        
        # Cache results
        if self.enable_cache and self.query_cache:
            self.query_cache.put(query, results, video_id, top_k)
        
        logger.debug(f"Search completed in {query_time*1000:.1f}ms for query: {query[:50]}...")
        return results, False
    
    def _record_query_time(self, query_time: float) -> None:
        """Record query execution time for metrics."""
        self.query_times.append(query_time)
        
        # Keep only recent history
        if len(self.query_times) > self.max_query_time_history:
            self.query_times = self.query_times[-self.max_query_time_history:]
    
    def invalidate_cache(self, video_id: Optional[str] = None) -> None:
        """Invalidate query cache.
        
        Args:
            video_id: If provided, only invalidate entries for this video
        """
        if self.query_cache:
            self.query_cache.invalidate(video_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        stats = {
            "cache_enabled": self.enable_cache,
            "total_queries": len(self.query_times)
        }
        
        # Cache stats
        if self.query_cache:
            stats["cache"] = self.query_cache.get_stats()
        
        # Query time stats
        if self.query_times:
            import statistics
            stats["query_times"] = {
                "avg_ms": statistics.mean(self.query_times) * 1000,
                "median_ms": statistics.median(self.query_times) * 1000,
                "min_ms": min(self.query_times) * 1000,
                "max_ms": max(self.query_times) * 1000,
                "p95_ms": statistics.quantiles(self.query_times, n=20)[18] * 1000 if len(self.query_times) > 20 else None,
                "p99_ms": statistics.quantiles(self.query_times, n=100)[98] * 1000 if len(self.query_times) > 100 else None
            }
        
        return stats
    
    def recommend_optimizations(self, stats: Dict[str, Any]) -> List[str]:
        """Analyze performance and recommend optimizations.
        
        Args:
            stats: Performance statistics from get_performance_stats()
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        # Check cache performance
        if self.enable_cache and "cache" in stats:
            cache_stats = stats["cache"]
            hit_rate = cache_stats.get("hit_rate", 0)
            
            if hit_rate < 0.3:
                recommendations.append(
                    f"Low cache hit rate ({hit_rate:.1%}). Consider increasing cache size or TTL."
                )
            elif hit_rate > 0.8:
                recommendations.append(
                    f"Excellent cache hit rate ({hit_rate:.1%})! Cache is working well."
                )
        
        # Check query times
        if "query_times" in stats:
            qt = stats["query_times"]
            avg_ms = qt.get("avg_ms", 0)
            p95_ms = qt.get("p95_ms", 0)
            
            if avg_ms > 100:
                recommendations.append(
                    f"Average query time is {avg_ms:.1f}ms. Consider using a smaller embedding model "
                    f"or reducing the number of indexed items."
                )
            
            if p95_ms and p95_ms > 200:
                recommendations.append(
                    f"95th percentile query time is {p95_ms:.1f}ms. Some queries are slow. "
                    f"Consider optimizing index or using approximate search."
                )
            
            if avg_ms < 50:
                recommendations.append(
                    f"Excellent query performance ({avg_ms:.1f}ms average)!"
                )
        
        # Check total queries
        total_queries = stats.get("total_queries", 0)
        if total_queries < 10:
            recommendations.append(
                "Limited query data. Run more queries to get better performance insights."
            )
        
        return recommendations
    
    def ab_test_search_quality(
        self,
        test_queries: List[Dict[str, Any]],
        search_func_a: callable,
        search_func_b: callable,
        metric: str = "precision"
    ) -> Dict[str, Any]:
        """A/B test two search implementations.
        
        Args:
            test_queries: List of test query dicts with 'query', 'video_id', 'expected_results'
            search_func_a: First search function to test
            search_func_b: Second search function to test
            metric: Metric to compare ("precision", "recall", "f1", "speed")
            
        Returns:
            Comparison results
        """
        results_a = []
        results_b = []
        times_a = []
        times_b = []
        
        for test in test_queries:
            query = test['query']
            video_id = test.get('video_id')
            expected = set(test.get('expected_results', []))
            
            # Test function A
            start = time.time()
            res_a = search_func_a(query=query, video_id=video_id, top_k=5)
            times_a.append(time.time() - start)
            
            retrieved_a = set([r.text if hasattr(r, 'text') else r for r in res_a])
            precision_a = len(retrieved_a & expected) / len(retrieved_a) if retrieved_a else 0
            recall_a = len(retrieved_a & expected) / len(expected) if expected else 0
            f1_a = 2 * (precision_a * recall_a) / (precision_a + recall_a) if (precision_a + recall_a) > 0 else 0
            
            results_a.append({
                "precision": precision_a,
                "recall": recall_a,
                "f1": f1_a
            })
            
            # Test function B
            start = time.time()
            res_b = search_func_b(query=query, video_id=video_id, top_k=5)
            times_b.append(time.time() - start)
            
            retrieved_b = set([r.text if hasattr(r, 'text') else r for r in res_b])
            precision_b = len(retrieved_b & expected) / len(retrieved_b) if retrieved_b else 0
            recall_b = len(retrieved_b & expected) / len(expected) if expected else 0
            f1_b = 2 * (precision_b * recall_b) / (precision_b + recall_b) if (precision_b + recall_b) > 0 else 0
            
            results_b.append({
                "precision": precision_b,
                "recall": recall_b,
                "f1": f1_b
            })
        
        # Calculate averages
        import statistics
        
        avg_precision_a = statistics.mean([r["precision"] for r in results_a])
        avg_recall_a = statistics.mean([r["recall"] for r in results_a])
        avg_f1_a = statistics.mean([r["f1"] for r in results_a])
        avg_time_a = statistics.mean(times_a)
        
        avg_precision_b = statistics.mean([r["precision"] for r in results_b])
        avg_recall_b = statistics.mean([r["recall"] for r in results_b])
        avg_f1_b = statistics.mean([r["f1"] for r in results_b])
        avg_time_b = statistics.mean(times_b)
        
        # Determine winner
        if metric == "precision":
            winner = "A" if avg_precision_a > avg_precision_b else "B"
            improvement = abs(avg_precision_a - avg_precision_b) / max(avg_precision_a, avg_precision_b)
        elif metric == "recall":
            winner = "A" if avg_recall_a > avg_recall_b else "B"
            improvement = abs(avg_recall_a - avg_recall_b) / max(avg_recall_a, avg_recall_b)
        elif metric == "f1":
            winner = "A" if avg_f1_a > avg_f1_b else "B"
            improvement = abs(avg_f1_a - avg_f1_b) / max(avg_f1_a, avg_f1_b)
        else:  # speed
            winner = "A" if avg_time_a < avg_time_b else "B"
            improvement = abs(avg_time_a - avg_time_b) / max(avg_time_a, avg_time_b)
        
        return {
            "function_a": {
                "precision": avg_precision_a,
                "recall": avg_recall_a,
                "f1": avg_f1_a,
                "avg_time_ms": avg_time_a * 1000
            },
            "function_b": {
                "precision": avg_precision_b,
                "recall": avg_recall_b,
                "f1": avg_f1_b,
                "avg_time_ms": avg_time_b * 1000
            },
            "winner": winner,
            "improvement": improvement,
            "metric": metric,
            "total_tests": len(test_queries)
        }


# Global singleton instance
_optimizer = None


def get_vector_search_optimizer() -> VectorSearchOptimizer:
    """Get or create the global vector search optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = VectorSearchOptimizer()
    return _optimizer
