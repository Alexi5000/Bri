"""Data prefetching service for BRI video agent.

Features:
- Prefetch related data (frames + captions together)
- Predictive prefetching based on user patterns
- Lazy loading for large datasets
- Streaming for large result sets
- N+1 query optimization
"""

import time
import asyncio
from typing import Any, Optional, List, Dict, AsyncIterator
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from utils.logging_config import get_logger, get_performance_logger
from storage.multi_tier_cache import get_multi_tier_cache
from storage.query_optimizer import get_query_optimizer

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


@dataclass
class AccessPattern:
    """User access pattern for predictive prefetching."""
    video_id: str
    data_types: List[str]  # e.g., ['frames', 'captions', 'transcript']
    timestamp: datetime
    frequency: int = 1


class PrefetchStrategy:
    """Base class for prefetch strategies."""
    
    def should_prefetch(self, video_id: str, data_type: str) -> bool:
        """Determine if data should be prefetched.
        
        Args:
            video_id: Video identifier
            data_type: Type of data to prefetch
            
        Returns:
            True if data should be prefetched
        """
        raise NotImplementedError


class RelatedDataStrategy(PrefetchStrategy):
    """Prefetch related data together (e.g., frames + captions)."""
    
    RELATED_DATA = {
        'frames': ['captions', 'objects'],
        'captions': ['frames'],
        'transcript': ['captions'],
        'objects': ['frames']
    }
    
    def should_prefetch(self, video_id: str, data_type: str) -> bool:
        """Always prefetch related data."""
        return True
    
    def get_related_types(self, data_type: str) -> List[str]:
        """Get related data types for a given type.
        
        Args:
            data_type: Primary data type
            
        Returns:
            List of related data types
        """
        return self.RELATED_DATA.get(data_type, [])


class PredictiveStrategy(PrefetchStrategy):
    """Prefetch based on user access patterns."""
    
    def __init__(self, pattern_window: int = 100):
        """Initialize predictive strategy.
        
        Args:
            pattern_window: Number of recent accesses to track
        """
        self.access_history: deque = deque(maxlen=pattern_window)
        self.pattern_frequency: Dict[str, int] = defaultdict(int)
        self.prefetch_threshold = 3  # Prefetch if accessed 3+ times
    
    def record_access(self, video_id: str, data_type: str) -> None:
        """Record a data access for pattern learning.
        
        Args:
            video_id: Video identifier
            data_type: Type of data accessed
        """
        pattern_key = f"{video_id}:{data_type}"
        self.access_history.append(pattern_key)
        self.pattern_frequency[pattern_key] += 1
    
    def should_prefetch(self, video_id: str, data_type: str) -> bool:
        """Determine if data should be prefetched based on patterns.
        
        Args:
            video_id: Video identifier
            data_type: Type of data to prefetch
            
        Returns:
            True if data is frequently accessed
        """
        pattern_key = f"{video_id}:{data_type}"
        return self.pattern_frequency.get(pattern_key, 0) >= self.prefetch_threshold
    
    def get_likely_next_access(self, video_id: str) -> List[str]:
        """Predict likely next data types to be accessed.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List of data types likely to be accessed next
        """
        # Find patterns for this video
        video_patterns = [
            (key.split(':')[1], freq)
            for key, freq in self.pattern_frequency.items()
            if key.startswith(f"{video_id}:")
        ]
        
        # Sort by frequency
        video_patterns.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 3 most frequent
        return [data_type for data_type, _ in video_patterns[:3]]


class DataPrefetcher:
    """Data prefetching service with multiple strategies.
    
    Features:
    - Prefetch related data together (frames + captions)
    - Predictive prefetching based on user patterns
    - Lazy loading for large datasets
    - Streaming for large result sets
    - N+1 query optimization
    """
    
    def __init__(self):
        """Initialize data prefetcher."""
        self.cache = get_multi_tier_cache()
        self.query_optimizer = get_query_optimizer()
        
        # Prefetch strategies
        self.related_strategy = RelatedDataStrategy()
        self.predictive_strategy = PredictiveStrategy()
        
        # Prefetch queue
        self.prefetch_queue: asyncio.Queue = asyncio.Queue()
        self.prefetch_worker_running = False
        
        # Lazy loading state
        self.lazy_load_cache: Dict[str, Any] = {}
        
        logger.info("Data prefetcher initialized")
    
    async def prefetch_related_data(
        self,
        video_id: str,
        primary_data_type: str
    ) -> None:
        """Prefetch related data for a video.
        
        Args:
            video_id: Video identifier
            primary_data_type: Primary data type being accessed
        """
        start_time = time.time()
        
        # Get related data types
        related_types = self.related_strategy.get_related_types(primary_data_type)
        
        if not related_types:
            return
        
        logger.info(
            f"Prefetching related data for video {video_id}: "
            f"{primary_data_type} → {related_types}"
        )
        
        # Prefetch each related type
        prefetched = []
        for data_type in related_types:
            try:
                # Check if already cached
                cache_key = f"{video_id}:{data_type}"
                if self.cache.get(cache_key, namespace="prefetch") is not None:
                    continue
                
                # Load and cache data
                data = await self._load_data(video_id, data_type)
                if data:
                    self.cache.set(cache_key, data, namespace="prefetch", ttl=600)
                    prefetched.append(data_type)
            except Exception as e:
                logger.error(f"Failed to prefetch {data_type} for video {video_id}: {e}")
        
        elapsed = time.time() - start_time
        logger.info(
            f"Prefetched {len(prefetched)} related data types in {elapsed:.2f}s: {prefetched}"
        )
        perf_logger.log_execution_time(
            "data_prefetch",
            elapsed,
            success=True,
            video_id=video_id,
            prefetched_count=len(prefetched)
        )
    
    async def prefetch_predictive(self, video_id: str) -> None:
        """Prefetch data based on predicted access patterns.
        
        Args:
            video_id: Video identifier
        """
        # Get likely next accesses
        likely_types = self.predictive_strategy.get_likely_next_access(video_id)
        
        if not likely_types:
            return
        
        logger.info(
            f"Predictive prefetch for video {video_id}: {likely_types}"
        )
        
        # Prefetch predicted data types
        for data_type in likely_types:
            try:
                cache_key = f"{video_id}:{data_type}"
                if self.cache.get(cache_key, namespace="prefetch") is None:
                    data = await self._load_data(video_id, data_type)
                    if data:
                        self.cache.set(cache_key, data, namespace="prefetch", ttl=600)
            except Exception as e:
                logger.error(f"Failed to predictive prefetch {data_type}: {e}")
    
    def record_access(self, video_id: str, data_type: str) -> None:
        """Record a data access for pattern learning.
        
        Args:
            video_id: Video identifier
            data_type: Type of data accessed
        """
        self.predictive_strategy.record_access(video_id, data_type)
    
    async def _load_data(self, video_id: str, data_type: str) -> Optional[Any]:
        """Load data from database.
        
        Args:
            video_id: Video identifier
            data_type: Type of data to load
            
        Returns:
            Loaded data or None if not found
        """
        try:
            if data_type == 'frames':
                return await self._load_frames(video_id)
            elif data_type == 'captions':
                return await self._load_captions(video_id)
            elif data_type == 'transcript':
                return await self._load_transcript(video_id)
            elif data_type == 'objects':
                return await self._load_objects(video_id)
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to load {data_type} for video {video_id}: {e}")
            return None
    
    async def _load_frames(self, video_id: str) -> List[Dict]:
        """Load frames from database."""
        query = """
            SELECT data, timestamp
            FROM video_context
            WHERE video_id = ? AND context_type = 'frame'
            ORDER BY timestamp ASC
        """
        return self.query_optimizer.execute_query(
            query,
            (video_id,),
            cache_key=f"frames:{video_id}"
        )
    
    async def _load_captions(self, video_id: str) -> List[Dict]:
        """Load captions from database."""
        query = """
            SELECT data, timestamp
            FROM video_context
            WHERE video_id = ? AND context_type = 'caption'
            ORDER BY timestamp ASC
        """
        return self.query_optimizer.execute_query(
            query,
            (video_id,),
            cache_key=f"captions:{video_id}"
        )
    
    async def _load_transcript(self, video_id: str) -> Optional[Dict]:
        """Load transcript from database."""
        query = """
            SELECT data
            FROM video_context
            WHERE video_id = ? AND context_type = 'transcript'
            ORDER BY created_at DESC
            LIMIT 1
        """
        results = self.query_optimizer.execute_query(
            query,
            (video_id,),
            cache_key=f"transcript:{video_id}"
        )
        return results[0] if results else None
    
    async def _load_objects(self, video_id: str) -> List[Dict]:
        """Load object detections from database."""
        query = """
            SELECT data, timestamp
            FROM video_context
            WHERE video_id = ? AND context_type = 'object'
            ORDER BY timestamp ASC
        """
        return self.query_optimizer.execute_query(
            query,
            (video_id,),
            cache_key=f"objects:{video_id}"
        )
    
    async def lazy_load_paginated(
        self,
        video_id: str,
        data_type: str,
        page_size: int = 10,
        page: int = 0
    ) -> Dict[str, Any]:
        """Lazy load data with pagination.
        
        Args:
            video_id: Video identifier
            data_type: Type of data to load
            page_size: Number of items per page
            page: Page number (0-indexed)
            
        Returns:
            Dictionary with data and pagination info
        """
        offset = page * page_size
        
        query = (
            "SELECT data, timestamp "
            "FROM video_context "
            "WHERE video_id = ? AND context_type = ? "
            "ORDER BY timestamp ASC "
            "LIMIT ? OFFSET ?"
        )
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as count
            FROM video_context
            WHERE video_id = ? AND context_type = ?
        """
        count_result = self.query_optimizer.execute_query(
            count_query,
            (video_id, data_type),
            cache_key=f"count:{video_id}:{data_type}"
        )
        total_count = count_result[0]['count'] if count_result else 0
        
        # Get page data
        results = self.query_optimizer.execute_query(
            query,
            (video_id, data_type, page_size, offset),
            cache_key=f"page:{video_id}:{data_type}:{page}:{page_size}"
        )
        
        return {
            "data": results,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": (page + 1) * page_size < total_count
        }
    
    async def stream_large_dataset(
        self,
        video_id: str,
        data_type: str,
        chunk_size: int = 100
    ) -> AsyncIterator[List[Dict]]:
        """Stream large dataset in chunks.
        
        Args:
            video_id: Video identifier
            data_type: Type of data to stream
            chunk_size: Number of items per chunk
            
        Yields:
            Chunks of data
        """
        offset = 0
        
        while True:
            query = (
                "SELECT data, timestamp "
                "FROM video_context "
                "WHERE video_id = ? AND context_type = ? "
                "ORDER BY timestamp ASC "
                "LIMIT ? OFFSET ?"
            )
            
            results = self.query_optimizer.execute_query(
                query,
                (video_id, data_type, chunk_size, offset),
                cache_key=f"stream:{video_id}:{data_type}:{offset}:{chunk_size}",
                cache_ttl=60  # Short TTL for streaming
            )
            
            if not results:
                break
            
            yield results
            offset += chunk_size
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.01)
    
    def optimize_n_plus_one(
        self,
        video_ids: List[str],
        data_type: str
    ) -> Dict[str, List[Dict]]:
        """Optimize N+1 query problem by batching.
        
        Instead of querying each video separately (N+1 queries),
        fetch all data in a single query.
        
        Args:
            video_ids: List of video identifiers
            data_type: Type of data to fetch
            
        Returns:
            Dictionary mapping video_id to data
        """
        if not video_ids:
            return {}
        
        start_time = time.time()
        
        # Build query with IN clause
        placeholders = ','.join(['?' for _ in video_ids])
        query = f"""
            SELECT video_id, data, timestamp
            FROM video_context
            WHERE video_id IN ({placeholders}) AND context_type = ?
            ORDER BY video_id, timestamp ASC
        """
        
        # Execute single query for all videos
        results = self.query_optimizer.execute_query(
            query,
            tuple(video_ids) + (data_type,),
            cache_key=f"batch:{','.join(video_ids)}:{data_type}"
        )
        
        # Group results by video_id
        grouped_results = defaultdict(list)
        for row in results:
            grouped_results[row['video_id']].append(row)
        
        elapsed = time.time() - start_time
        logger.info(
            f"Optimized N+1 query: fetched {data_type} for {len(video_ids)} videos "
            f"in {elapsed:.2f}s (single query)"
        )
        perf_logger.log_execution_time(
            "n_plus_one_optimization",
            elapsed,
            success=True,
            video_count=len(video_ids),
            data_type=data_type
        )
        
        return dict(grouped_results)
    
    async def start_prefetch_worker(self) -> None:
        """Start background worker for prefetch queue."""
        if self.prefetch_worker_running:
            return
        
        self.prefetch_worker_running = True
        logger.info("Prefetch worker started")
        
        while self.prefetch_worker_running:
            try:
                # Get prefetch task from queue (with timeout)
                task = await asyncio.wait_for(
                    self.prefetch_queue.get(),
                    timeout=1.0
                )
                
                video_id, data_type = task
                await self.prefetch_related_data(video_id, data_type)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Prefetch worker error: {e}")
    
    def stop_prefetch_worker(self) -> None:
        """Stop background prefetch worker."""
        self.prefetch_worker_running = False
        logger.info("Prefetch worker stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prefetcher statistics.
        
        Returns:
            Dictionary with prefetcher stats
        """
        return {
            "prefetch_queue_size": self.prefetch_queue.qsize(),
            "worker_running": self.prefetch_worker_running,
            "predictive_patterns": len(self.predictive_strategy.pattern_frequency),
            "cache_stats": self.cache.get_stats()
        }


# Global data prefetcher instance
_data_prefetcher: Optional[DataPrefetcher] = None


def get_data_prefetcher() -> DataPrefetcher:
    """Get or create global data prefetcher instance.
    
    Returns:
        DataPrefetcher instance
    """
    global _data_prefetcher
    if _data_prefetcher is None:
        _data_prefetcher = DataPrefetcher()
    return _data_prefetcher
