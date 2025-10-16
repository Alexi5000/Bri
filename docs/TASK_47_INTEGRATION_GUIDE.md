# Task 47: Integration Guide for Data Flow Optimization & Caching

## Quick Start

### 1. Import the Components

```python
# Multi-tier caching
from storage.multi_tier_cache import get_multi_tier_cache

# Query optimization
from storage.query_optimizer import get_query_optimizer

# Data prefetching
from services.data_prefetcher import get_data_prefetcher

# Compression
from storage.compression import get_compression_manager
```

### 2. Basic Usage

#### Caching Video Data

```python
cache = get_multi_tier_cache()

# Cache video frames
cache.set(
    f"video:{video_id}:frames",
    frames_data,
    namespace="video",
    ttl=600  # 10 minutes
)

# Retrieve cached frames
frames = cache.get(f"video:{video_id}:frames", namespace="video")

# Invalidate all data for a video
cache.invalidate_pattern(f"video:{video_id}:*", namespace="video")
```

#### Optimized Database Queries

```python
optimizer = get_query_optimizer()

# Query with automatic caching
captions = optimizer.execute_query(
    "SELECT * FROM video_context WHERE video_id = ? AND context_type = 'caption'",
    parameters=(video_id,),
    cache_key=f"captions:{video_id}",
    cache_ttl=300
)

# Batch insert with transaction
optimizer.execute_batch(
    "INSERT INTO video_context (video_id, context_type, data) VALUES (?, ?, ?)",
    parameters_list=batch_data,
    batch_size=100
)
```

#### Intelligent Prefetching

```python
prefetcher = get_data_prefetcher()

# Prefetch related data when user accesses frames
await prefetcher.prefetch_related_data(video_id, "frames")

# Record access patterns for prediction
prefetcher.record_access(video_id, "captions")

# Lazy load large datasets
result = await prefetcher.lazy_load_paginated(
    video_id,
    "frames",
    page_size=20,
    page=0
)
```

#### Data Compression

```python
manager = get_compression_manager()

# Compress JSON before storing
compressed_data = manager.compress_json(large_dict)

# Compress frame images to WebP
output_path, orig_size, comp_size = manager.compress_image(
    "frame.jpg",
    "frame.webp"
)

# Check for duplicate frames
is_dup, orig_ts = manager.check_frame_duplicate(
    video_id,
    timestamp,
    frame_path
)
```

## Integration with Existing Components

### Context Builder Enhancement

```python
# In services/context.py

from storage.multi_tier_cache import get_multi_tier_cache
from services.data_prefetcher import get_data_prefetcher

class ContextBuilder:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.cache = get_multi_tier_cache()
        self.prefetcher = get_data_prefetcher()
    
    def build_video_context(self, video_id: str) -> VideoContext:
        # Check cache first
        cache_key = f"context:{video_id}"
        cached = self.cache.get(cache_key, namespace="context")
        if cached:
            return VideoContext(**cached)
        
        # Build context from database
        context = self._build_from_db(video_id)
        
        # Cache the result
        self.cache.set(
            cache_key,
            context.__dict__,
            namespace="context",
            ttl=600
        )
        
        # Prefetch related data
        asyncio.create_task(
            self.prefetcher.prefetch_related_data(video_id, "frames")
        )
        
        return context
```

### MCP Server Enhancement

```python
# In mcp_server/main.py

from storage.query_optimizer import get_query_optimizer
from storage.compression import get_compression_manager

optimizer = get_query_optimizer()
compressor = get_compression_manager()

@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    # Use query optimizer for database operations
    results = optimizer.execute_query(
        "SELECT * FROM video_context WHERE video_id = ?",
        parameters=(request.video_id,),
        cache_key=f"tool:{tool_name}:{request.video_id}"
    )
    
    # Compress response if large
    response_json = json.dumps(results)
    if len(response_json) > 1024:
        compressed = compressor.compress_response(response_json)
        return Response(
            content=compressed,
            media_type="application/json",
            headers={"Content-Encoding": "gzip"}
        )
    
    return results
```

### Video Processing Service Enhancement

```python
# In services/video_processing_service.py

from storage.compression import get_compression_manager
from storage.multi_tier_cache import get_multi_tier_cache

class VideoProcessingService:
    def __init__(self):
        self.compressor = get_compression_manager()
        self.cache = get_multi_tier_cache()
    
    def store_frames(self, video_id: str, frames: List[Frame]):
        # Check for duplicates
        unique_frames = []
        for frame in frames:
            is_dup, orig_ts = self.compressor.check_frame_duplicate(
                video_id,
                frame.timestamp,
                frame.image_path
            )
            
            if not is_dup:
                # Compress to WebP
                webp_path, _, _ = self.compressor.compress_image(
                    frame.image_path
                )
                frame.image_path = webp_path
                unique_frames.append(frame)
        
        # Store unique frames
        self._store_to_db(video_id, unique_frames)
        
        # Invalidate cache
        self.cache.invalidate_pattern(
            f"video:{video_id}:frames*",
            namespace="video"
        )
```

## Performance Monitoring

### Get Statistics

```python
# Cache statistics
cache_stats = cache.get_stats()
print(f"L1 hit rate: {cache_stats['l1']['hit_rate']}")
print(f"L2 enabled: {cache_stats['l2']['enabled']}")
print(f"L3 size: {cache_stats['l3']['size']}")

# Query optimizer statistics
optimizer_stats = optimizer.get_stats()
print(f"Connection pool: {optimizer_stats['connection_pool']}")
print(f"Query performance: {optimizer_stats['query_performance']}")

# Prefetcher statistics
prefetch_stats = prefetcher.get_stats()
print(f"Queue size: {prefetch_stats['prefetch_queue_size']}")
print(f"Patterns tracked: {prefetch_stats['predictive_patterns']}")

# Compression statistics
comp_stats = compressor.get_stats()
print(f"Frames tracked: {comp_stats['frame_deduplication']['total_frames']}")
```

### Logging

All components use the standard BRI logging system:

```python
from utils.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

# Components automatically log:
# - Cache hits/misses
# - Query execution times
# - Compression ratios
# - Prefetch operations
```

## Configuration

### Environment Variables

No additional configuration needed. Components use existing settings:

```python
# In .env
DATABASE_PATH=data/bri.db
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379
CACHE_TTL_HOURS=24
LOG_LEVEL=INFO
LOG_DIR=logs
```

### Tuning Parameters

```python
# Multi-tier cache
cache = MultiTierCache(
    l1_capacity=100,      # L1 cache size
    l2_enabled=True,      # Enable Redis
    l3_enabled=True       # Enable query cache
)

# Query optimizer
optimizer = QueryOptimizer(
    db_path="data/bri.db",
    pool_size=5           # Connection pool size
)

# Compression
compressor = CompressionManager(
    json_level=6,         # 0-9, higher = better compression
    image_quality=85,     # 0-100, higher = better quality
    response_level=6      # 0-9, higher = better compression
)
```

## Best Practices

### 1. Cache Invalidation

Always invalidate cache when data changes:

```python
# After updating video data
cache.invalidate_pattern(f"video:{video_id}:*", namespace="video")

# After batch updates
optimizer.execute_update(
    query,
    parameters,
    invalidate_pattern=f"video:{video_id}:*"
)
```

### 2. Prefetch Strategy

Record access patterns for better prediction:

```python
# Record every data access
prefetcher.record_access(video_id, data_type)

# Prefetch related data proactively
await prefetcher.prefetch_related_data(video_id, primary_type)
```

### 3. Compression Decisions

Use compression for large data:

```python
# Check if compression is beneficial
if compressor.json_compressor.should_compress(data):
    compressed = compressor.compress_json(data)
    store_compressed(compressed)
else:
    store_uncompressed(data)
```

### 4. Query Optimization

Use batching for bulk operations:

```python
# Instead of N individual inserts
for item in items:
    db.execute("INSERT INTO table VALUES (?)", (item,))

# Use batch insert
optimizer.execute_batch(
    "INSERT INTO table VALUES (?)",
    [(item,) for item in items],
    batch_size=100
)
```

## Troubleshooting

### High Cache Miss Rate

```python
# Check cache statistics
stats = cache.get_stats()
if float(stats['l1']['hit_rate'].rstrip('%')) < 50:
    # Increase L1 capacity
    cache.l1_cache.capacity = 200
    
    # Enable cache warming
    cache.warm_cache(
        keys=frequently_accessed_keys,
        loader=load_data_function
    )
```

### Slow Query Performance

```python
# Check query statistics
stats = optimizer.get_query_stats()
for query_type, metrics in stats.items():
    if float(metrics['avg_ms']) > 100:
        logger.warning(f"Slow {query_type} queries: {metrics['avg_ms']}ms")
        
        # Increase cache TTL
        # Add database indexes
        # Use query batching
```

### High Memory Usage

```python
# Reduce L1 cache size
cache.l1_cache.capacity = 50

# Reduce L3 cache TTL
cache.l3_default_ttl = 60  # 1 minute

# Clear old cache entries
cache.clear_all()
```

## Testing

Run the comprehensive test suite:

```bash
python scripts/test_task_47_caching_optimization.py
```

Expected output:
```
✅ L1 Cache tests passed
✅ Multi-tier cache tests passed
✅ Query optimizer tests passed
✅ Data prefetcher tests passed
✅ JSON compression tests passed
✅ Image compression tests passed
✅ Response compression tests passed
✅ Frame deduplication tests passed
```

## Support

For issues or questions:
1. Check logs in `logs/bri.log` and `logs/bri_performance.log`
2. Review statistics with `get_stats()` methods
3. Refer to `docs/TASK_47_SUMMARY.md` for detailed documentation
