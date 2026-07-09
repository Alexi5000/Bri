# Vector Search Services

This directory contains the optional vector search and semantic search implementation for BRI.

## Overview

Vector search enables semantic similarity matching for video captions and transcripts, significantly improving search quality beyond keyword matching.

## Components

### 1. `semantic_search.py`

Core semantic search service using ChromaDB and sentence-transformers.

**Key Features:**
- Embedding generation (single + batch)
- Vector storage in ChromaDB
- Similarity search with metadata filtering
- Hybrid search (keyword + semantic)

**Usage:**
```python
from services.semantic_search import get_semantic_search_service

service = get_semantic_search_service()
if service.is_enabled():
    results = service.search("person walking dog", video_id="vid_123")
```

### 2. `embedding_pipeline.py`

Pipeline for batch processing and incremental updates.

**Key Features:**
- Batch video processing
- Incremental updates (only new data)
- Embedding versioning
- Quality monitoring

**Usage:**
```python
from services.embedding_pipeline import get_embedding_pipeline

pipeline = get_embedding_pipeline()
pipeline.process_video(video_id, captions, segments)
```

### 3. `vector_search_optimizer.py`

Performance optimization with caching and metrics.

**Key Features:**
- LRU query cache with TTL
- Performance metrics tracking
- Optimization recommendations
- A/B testing support

**Usage:**
```python
from services.vector_search_optimizer import get_vector_search_optimizer

optimizer = get_vector_search_optimizer()
stats = optimizer.get_performance_stats()
```

## Installation

### Required Dependencies

```bash
pip install chromadb sentence-transformers
```

### Verification

```bash
python scripts/test_vector_search.py
```

## Integration

### Automatic (Recommended)

Once dependencies are installed, semantic search is automatically enabled:
- Video processing auto-indexes content
- Search queries use hybrid search
- No code changes needed

### Manual Control

```python
from services.context import ContextBuilder

builder = ContextBuilder()

# Hybrid search (automatic)
captions = builder.search_captions(video_id, query)

# Disable semantic search
captions = builder.search_captions(video_id, query, use_semantic=False)

# Pure semantic search
captions = builder.search_captions_semantic(video_id, query)
```

## Configuration

### Model Selection

Edit `semantic_search.py`:

```python
service = SemanticSearchService(
    model_name="all-MiniLM-L6-v2"  # Fast (default)
    # model_name="all-mpnet-base-v2"  # Best quality
)
```

### Cache Settings

Edit `vector_search_optimizer.py`:

```python
optimizer = VectorSearchOptimizer(
    cache_size=1000,  # Max cached queries
    cache_ttl=3600    # 1 hour TTL
)
```

## Performance

### Expected Metrics

- Embedding generation: ~10ms per text
- Batch indexing: ~1s per 100 items
- Search query (cold): ~50ms
- Search query (cached): ~5ms
- Memory usage: ~500MB for 10K embeddings

### Optimization

1. **Enable caching** (default: enabled)
2. **Use batch processing** for multiple videos
3. **Monitor cache hit rate** (aim for >50%)
4. **Adjust semantic weight** for hybrid search

## Graceful Degradation

The implementation is **fully optional**:

- **Dependencies missing**: Falls back to keyword search
- **Indexing fails**: Video processing continues
- **Search fails**: Returns keyword-only results
- **No impact**: Existing functionality unaffected

## Monitoring

### Check Status

```python
service = get_semantic_search_service()
print(f"Enabled: {service.is_enabled()}")

stats = service.get_stats()
print(f"Total embeddings: {stats['total_embeddings']}")
print(f"Cache hit rate: {stats['performance']['cache']['hit_rate']}")
```

### Get Recommendations

```python
recommendations = service.get_performance_recommendations()
for rec in recommendations:
    print(f"💡 {rec}")
```

## Troubleshooting

### Dependencies Won't Install

```bash
# Upgrade pip first
python -m pip install --upgrade pip
pip install chromadb sentence-transformers

# Or use specific versions
pip install chromadb==0.4.0 sentence-transformers==2.2.0
```

### Slow Performance

```python
# Check cache hit rate
stats = service.get_stats()
hit_rate = stats['performance']['cache']['hit_rate']

# If low, increase cache size/TTL
# If query times high, use smaller model
```

### Out of Memory

```python
# Reduce batch size
service.index_captions(video_id, captions, batch_size=16)

# Or use smaller model
service = SemanticSearchService(model_name="all-MiniLM-L6-v2")
```

## Documentation

- **Evaluation**: `docs/VECTOR_DB_EVALUATION.md`
- **Summary**: `docs/TASK_49_SUMMARY.md`
- **Integration Guide**: `docs/VECTOR_SEARCH_INTEGRATION_GUIDE.md`
- **Complete**: `docs/TASK_49_IMPLEMENTATION_COMPLETE.md`

## Testing

```bash
# Run test suite
python scripts/test_vector_search.py

# Expected: 6/6 tests pass (with dependencies)
# Expected: 1/6 tests pass (without dependencies - graceful degradation)
```

## Support

For issues or questions:
1. Check test output
2. Review logs for warnings
3. Verify dependencies installed
4. Check documentation

## License

Same as BRI project license.
