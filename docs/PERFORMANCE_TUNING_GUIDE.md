# BRI Performance Tuning Guide

## Overview

This guide provides detailed instructions for optimizing BRI's performance across different deployment scenarios and workloads.

## Performance Targets

### Response Times
- Video upload: <5 seconds
- Frame extraction: <10 seconds
- Full processing: <2 minutes (5-min video)
- Chat query: <3 seconds (80th percentile)
- Database queries: <100ms (95th percentile)

### Resource Usage
- Memory: <2GB under normal load
- CPU: <50% average
- Disk I/O: <100 MB/s
- Cache hit rate: >70%

## Configuration Optimization

### Video Processing

**Frame Extraction:**
```bash
# Faster processing (fewer frames)
MAX_FRAMES_PER_VIDEO=15
FRAME_EXTRACTION_INTERVAL=3.0

# Better quality (more frames)
MAX_FRAMES_PER_VIDEO=30
FRAME_EXTRACTION_INTERVAL=1.0

# Balanced (default)
MAX_FRAMES_PER_VIDEO=20
FRAME_EXTRACTION_INTERVAL=2.0
```

**Model Selection:**
```bash
# Faster inference
GROQ_MODEL=llama-3.1-8b-instant

# Better quality
GROQ_MODEL=llama-3.1-70b-versatile

# Balanced (default)
GROQ_MODEL=llama-3.1-70b-versatile
```

### Caching Strategy

**Redis Configuration:**
```bash
# Enable caching
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379

# Cache TTL
CACHE_TTL_HOURS=24  # Increase for better hit rate
```

**Cache Warming:**
```python
from services.data_prefetcher import DataPrefetcher

prefetcher = DataPrefetcher()
prefetcher.warm_cache_for_video(video_id)
```

### Database Optimization

**Connection Pooling:**
```python
# In storage/database.py
# Already implemented with WAL mode
```

**Query Optimization:**
```bash
# Run ANALYZE regularly
sqlite3 data/bri.db "ANALYZE"

# Check query plans
sqlite3 data/bri.db "EXPLAIN QUERY PLAN SELECT * FROM videos WHERE video_id='vid_123'"
```

**Indexes:**
```sql
-- Already created in schema
CREATE INDEX IF NOT EXISTS idx_memory_video_id ON memory(video_id);
CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp);
CREATE INDEX IF NOT EXISTS idx_video_context_video_id ON video_context(video_id);
CREATE INDEX IF NOT EXISTS idx_video_context_timestamp ON video_context(timestamp);
```

## Performance Monitoring

### Real-Time Monitoring

**Dashboard:**
```bash
# Access logging dashboard
streamlit run ui/logging_dashboard.py
```

**Metrics:**
```python
from utils.metrics_logger import MetricsLogger

# Log resource usage
MetricsLogger.log_resource_usage("video_processing")
```

### Performance Profiling

**Profile Video Processing:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Process video
from services.video_processing_service import VideoProcessingService
service = VideoProcessingService()
service.process_video(video_id)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

**Profile Database Queries:**
```python
import time
from storage.database import Database

db = Database()

start = time.time()
result = db.get_video_context(video_id)
elapsed = time.time() - start

print(f"Query took {elapsed:.3f}s")
```

## Optimization Strategies

### 1. Progressive Processing

**Enable staged processing:**
```python
from services.progressive_processor import ProgressiveProcessor

processor = ProgressiveProcessor()

# Stage 1: Fast (frames only)
processor.process_stage_1(video_id)  # ~10s

# User can start chatting here

# Stage 2: Medium (captions)
processor.process_stage_2(video_id)  # ~60s

# Stage 3: Full (transcripts + objects)
processor.process_stage_3(video_id)  # ~120s
```

### 2. Batch Processing

**Process multiple videos:**
```python
from services.processing_queue import ProcessingQueue

queue = ProcessingQueue()

# Add videos to queue
for video_id in video_ids:
    queue.add(video_id)

# Process in parallel
queue.process_all(max_workers=3)
```

### 3. Lazy Loading

**Load data on demand:**
```python
from ui.lazy_loader import LazyLoader

loader = LazyLoader()

# Load frames in batches
for batch in loader.load_frames_batched(video_id, batch_size=5):
    display_frames(batch)
```

### 4. Query Optimization

**Use indexes:**
```python
# Good: Uses index
db.cursor.execute(
    "SELECT * FROM memory WHERE video_id = ? ORDER BY timestamp DESC LIMIT 10",
    (video_id,)
)

# Bad: Full table scan
db.cursor.execute(
    "SELECT * FROM memory WHERE content LIKE '%keyword%'"
)
```

**Limit results:**
```python
# Good: Limited results
db.get_conversation_history(video_id, limit=10)

# Bad: Unlimited results
db.get_all_memory(video_id)
```

### 5. Cache Optimization

**Multi-tier caching:**
```python
from storage.multi_tier_cache import MultiTierCache

cache = MultiTierCache()

# L1: In-memory (fastest)
# L2: Redis (fast)
# L3: Database (slower)

result = cache.get_or_compute(
    key="video_context:vid_123",
    compute_fn=lambda: db.get_video_context("vid_123"),
    ttl=3600
)
```

## Bottleneck Identification

### Common Bottlenecks

**1. Frame Extraction**
- **Symptom:** High CPU during extraction
- **Solution:** Reduce MAX_FRAMES_PER_VIDEO or increase FRAME_EXTRACTION_INTERVAL

**2. Model Inference**
- **Symptom:** Long processing times
- **Solution:** Use GPU if available, reduce batch sizes

**3. Database Queries**
- **Symptom:** Slow query times
- **Solution:** Add indexes, run VACUUM, optimize queries

**4. API Calls**
- **Symptom:** Slow Groq responses
- **Solution:** Enable caching, reduce max_tokens, use faster model

**5. Memory Usage**
- **Symptom:** High memory consumption
- **Solution:** Reduce frame count, clear cache, restart services

### Diagnostic Tools

**Check Processing Times:**
```bash
grep "Pipeline.*completed" logs/bri_pipeline.log | \
  awk '{print $NF}' | \
  sort -n | \
  awk '{sum+=$1; count++} END {print "Avg:", sum/count, "Max:", $NF}'
```

**Check Database Performance:**
```bash
grep "DB.*execution_time" logs/bri.log | \
  grep -oP "execution_time=\K[\d.]+" | \
  sort -n | \
  tail -20
```

**Check Cache Hit Rate:**
```bash
hits=$(grep "Cache HIT" logs/bri_performance.log | wc -l)
misses=$(grep "Cache MISS" logs/bri_performance.log | wc -l)
total=$((hits + misses))
rate=$((hits * 100 / total))
echo "Cache hit rate: ${rate}%"
```

## Hardware Recommendations

### Minimum Requirements
- CPU: 4 cores
- RAM: 4GB
- Disk: 20GB SSD
- Network: 10 Mbps

### Recommended
- CPU: 8 cores
- RAM: 8GB
- Disk: 50GB SSD
- Network: 100 Mbps
- GPU: Optional (for faster inference)

### High Performance
- CPU: 16+ cores
- RAM: 16GB+
- Disk: 100GB+ NVMe SSD
- Network: 1 Gbps
- GPU: NVIDIA with 8GB+ VRAM

## Scaling Strategies

### Vertical Scaling

**Increase Resources:**
- Add more CPU cores
- Increase RAM
- Use faster storage (NVMe)
- Add GPU for inference

### Horizontal Scaling

**Multiple Instances:**
```bash
# Run multiple MCP servers
python mcp_server/main.py --port 8000 &
python mcp_server/main.py --port 8001 &
python mcp_server/main.py --port 8002 &

# Load balancer configuration
# (nginx, HAProxy, etc.)
```

**Distributed Processing:**
```python
# Use Celery for distributed tasks
from celery import Celery

app = Celery('bri', broker='redis://localhost:6379')

@app.task
def process_video(video_id):
    # Process video in background worker
    pass
```

## Performance Testing

### Load Testing

**Test video processing:**
```python
import time
from concurrent.futures import ThreadPoolExecutor

def process_test_video():
    start = time.time()
    # Upload and process video
    elapsed = time.time() - start
    return elapsed

# Test with multiple concurrent uploads
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_test_video) for _ in range(10)]
    times = [f.result() for f in futures]

print(f"Avg: {sum(times)/len(times):.2f}s")
print(f"Max: {max(times):.2f}s")
```

### Benchmark Results

**Expected Performance (8-core, 8GB RAM):**
- Video upload: 2-3 seconds
- Frame extraction (20 frames): 5-8 seconds
- Caption generation: 15-20 seconds
- Audio transcription: 30-40 seconds
- Object detection: 10-15 seconds
- Total processing: 60-90 seconds

## Troubleshooting Performance Issues

### Slow Video Processing

**Check:**
1. CPU usage: `top`
2. Memory usage: `free -h`
3. Disk I/O: `iostat`
4. Processing logs: `grep "Pipeline" logs/bri_pipeline.log`

**Fix:**
1. Reduce MAX_FRAMES_PER_VIDEO
2. Enable caching
3. Use faster storage
4. Add more CPU cores

### Slow Database Queries

**Check:**
```bash
grep "DB.*execution_time" logs/bri.log | sort -t'=' -k2 -rn | head -20
```

**Fix:**
1. Run VACUUM: `sqlite3 data/bri.db "VACUUM"`
2. Run ANALYZE: `sqlite3 data/bri.db "ANALYZE"`
3. Check indexes: `sqlite3 data/bri.db ".indexes"`
4. Optimize queries

### High Memory Usage

**Check:**
```bash
ps aux | grep python | grep bri
```

**Fix:**
1. Reduce MAX_FRAMES_PER_VIDEO
2. Clear cache: `redis-cli FLUSHALL`
3. Restart services
4. Check for memory leaks

### Low Cache Hit Rate

**Check:**
```bash
grep "Cache" logs/bri_performance.log | tail -100
```

**Fix:**
1. Increase CACHE_TTL_HOURS
2. Warm cache for popular videos
3. Check Redis memory: `redis-cli INFO memory`
4. Increase Redis maxmemory

## Best Practices

1. **Monitor regularly:** Check logs and metrics daily
2. **Optimize incrementally:** Make one change at a time
3. **Test thoroughly:** Benchmark before and after changes
4. **Document changes:** Keep track of configuration changes
5. **Plan for growth:** Monitor trends and plan capacity

## Summary

Key performance optimizations:
- ✅ Enable Redis caching
- ✅ Reduce frame extraction for faster processing
- ✅ Use progressive processing for better UX
- ✅ Run database maintenance regularly
- ✅ Monitor performance metrics
- ✅ Optimize queries with indexes
- ✅ Use lazy loading for large datasets
- ✅ Implement multi-tier caching

For questions or issues, check the Operations Runbook or create a GitHub issue.
