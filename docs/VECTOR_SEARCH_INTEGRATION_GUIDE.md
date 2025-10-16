# Vector Search Integration Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install chromadb sentence-transformers
```

### 2. Verify Installation

```bash
python scripts/test_vector_search.py
```

Expected output:
```
✅ PASS: Semantic Search Availability
✅ PASS: Embedding Generation
✅ PASS: Indexing and Search
✅ PASS: Embedding Pipeline
✅ PASS: Performance Optimizer
✅ PASS: Hybrid Search

Total: 6/6 tests passed (100%)
🎉 All tests passed!
```

### 3. Automatic Integration

Once dependencies are installed, semantic search is **automatically enabled**:

- Video processing auto-indexes captions and transcripts
- Search queries automatically use hybrid search (keyword + semantic)
- Performance caching is enabled by default
- No code changes required!

## Usage Examples

### Basic Search

```python
from services.context import ContextBuilder

builder = ContextBuilder()

# Hybrid search (automatically uses semantic if available)
captions = builder.search_captions(
    video_id="vid_123",
    query="person walking dog",
    top_k=5
)

for caption in captions:
    print(f"[{caption.frame_timestamp}s] {caption.text}")
```

### Pure Semantic Search

```python
# Force semantic-only search
captions = builder.search_captions_semantic(
    video_id="vid_123",
    query="person walking dog",
    top_k=5,
    min_score=0.5  # Minimum similarity threshold
)
```

### Disable Semantic Search

```python
# Use keyword-only search
captions = builder.search_captions(
    video_id="vid_123",
    query="person walking dog",
    top_k=5,
    use_semantic=False  # Disable semantic search
)
```


## Manual Indexing

### Index Existing Videos

If you have videos processed before installing semantic search:

```python
from services.embedding_pipeline import get_embedding_pipeline
from services.context import ContextBuilder

pipeline = get_embedding_pipeline()
builder = ContextBuilder()

# Index single video
def fetch_video_data(video_id):
    captions = builder._get_captions(video_id)
    transcript = builder._get_transcript(video_id)
    
    caption_dicts = [
        {
            'text': cap.text,
            'frame_timestamp': cap.frame_timestamp,
            'confidence': cap.confidence
        }
        for cap in captions
    ]
    
    segment_dicts = [
        {
            'text': seg.text,
            'start': seg.start,
            'end': seg.end,
            'confidence': getattr(seg, 'confidence', 1.0)
        }
        for seg in transcript.segments
    ] if transcript and transcript.segments else []
    
    return caption_dicts, segment_dicts

# Index one video
video_id = "vid_123"
captions, segments = fetch_video_data(video_id)
pipeline.process_video(video_id, captions, segments)

# Or batch index multiple videos
video_ids = ["vid_123", "vid_456", "vid_789"]
results = pipeline.process_batch(video_ids, fetch_video_data)
print(f"Indexed {sum(results.values())}/{len(video_ids)} videos")
```

### Reindex After Model Update

```python
pipeline = get_embedding_pipeline()

# Update model version (marks all videos for reindex)
pipeline.update_model_version("all-mpnet-base-v2")

# Reindex all videos
results = pipeline.reindex_all(fetch_video_data)
```

## Monitoring

### Check Statistics

```python
from services.semantic_search import get_semantic_search_service

service = get_semantic_search_service()

# Get comprehensive stats
stats = service.get_stats()
print(f"Model: {stats['model']}")
print(f"Embedding dimension: {stats['embedding_dim']}")
print(f"Total embeddings: {stats['total_embeddings']}")

# Performance stats
if 'performance' in stats:
    perf = stats['performance']
    print(f"Total queries: {perf['total_queries']}")
    
    if 'cache' in perf:
        cache = perf['cache']
        print(f"Cache hit rate: {cache['hit_rate']:.1%}")
    
    if 'query_times' in perf:
        qt = perf['query_times']
        print(f"Avg query time: {qt['avg_ms']:.1f}ms")
        print(f"P95 query time: {qt['p95_ms']:.1f}ms")
```

### Get Recommendations

```python
recommendations = service.get_performance_recommendations()
for rec in recommendations:
    print(f"💡 {rec}")
```

Example output:
```
💡 Excellent cache hit rate (85.3%)! Cache is working well.
💡 Excellent query performance (42.3ms average)!
```


## Advanced Configuration

### Change Embedding Model

Edit `services/semantic_search.py`:

```python
# Default (recommended)
service = SemanticSearchService(
    model_name="all-MiniLM-L6-v2"  # Fast, 384 dims
)

# Higher quality (slower)
service = SemanticSearchService(
    model_name="all-mpnet-base-v2"  # Best quality, 768 dims
)

# Paraphrase focused
service = SemanticSearchService(
    model_name="paraphrase-MiniLM-L6-v2"  # Paraphrase matching
)
```

### Adjust Cache Settings

Edit `services/vector_search_optimizer.py`:

```python
optimizer = VectorSearchOptimizer(
    enable_cache=True,
    cache_size=2000,      # Max 2000 cached queries (default: 1000)
    cache_ttl=7200        # 2 hours TTL (default: 3600)
)
```

### Hybrid Search Weights

Adjust semantic vs keyword weighting:

```python
# In services/context.py, search_captions method
hybrid_results = self.semantic_search.hybrid_search(
    query=query,
    keyword_results=kw_results_dict,
    video_id=video_id,
    top_k=top_k,
    semantic_weight=0.8  # 80% semantic, 20% keyword (default: 0.7)
)
```

## Troubleshooting

### Issue: Dependencies Won't Install

**Solution 1**: Upgrade pip
```bash
python -m pip install --upgrade pip
pip install chromadb sentence-transformers
```

**Solution 2**: Install with specific versions
```bash
pip install chromadb==0.4.0 sentence-transformers==2.2.0
```

**Solution 3**: Use conda (if pip fails)
```bash
conda install -c conda-forge chromadb sentence-transformers
```

### Issue: Model Download Fails

First run downloads ~90MB model. If it fails:

```python
# Pre-download manually
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

Or set cache directory:
```bash
export SENTENCE_TRANSFORMERS_HOME=/path/to/cache
```

### Issue: Slow Search Performance

**Check cache hit rate:**
```python
stats = service.get_stats()
hit_rate = stats['performance']['cache']['hit_rate']
print(f"Cache hit rate: {hit_rate:.1%}")
```

**If low (<30%):**
- Increase cache size
- Increase cache TTL
- Check if queries are too diverse

**If query times high (>100ms):**
- Use smaller model (all-MiniLM-L6-v2)
- Reduce indexed items
- Check system resources

### Issue: Out of Memory

**Reduce batch size:**
```python
service.index_captions(
    video_id,
    captions,
    batch_size=16  # Reduce from default 32
)
```

**Use smaller model:**
```python
service = SemanticSearchService(
    model_name="all-MiniLM-L6-v2"  # 384 dims vs 768
)
```

## Performance Tuning

### Optimize for Speed

```python
# Use fastest model
model_name = "all-MiniLM-L6-v2"

# Enable aggressive caching
cache_size = 5000
cache_ttl = 7200

# Reduce top_k
top_k = 3  # Instead of 5
```

### Optimize for Quality

```python
# Use best model
model_name = "all-mpnet-base-v2"

# Increase semantic weight
semantic_weight = 0.9  # 90% semantic

# Increase top_k
top_k = 10
```

### Optimize for Memory

```python
# Use smallest model
model_name = "all-MiniLM-L6-v2"

# Reduce cache size
cache_size = 500

# Process in smaller batches
batch_size = 16
```

## Migration Guide

### From Keyword-Only to Semantic

1. Install dependencies
2. Run test suite to verify
3. Index existing videos (optional, auto-indexes new videos)
4. Monitor performance
5. Adjust weights if needed

### From ChromaDB to Qdrant (Future)

If you exceed 10M vectors:

1. Export embeddings from ChromaDB
2. Install Qdrant: `pip install qdrant-client`
3. Update `services/semantic_search.py` to use Qdrant client
4. Import embeddings to Qdrant
5. Update connection config

Code changes minimal - same interface!

## Best Practices

1. **Always enable caching** for production
2. **Monitor cache hit rate** - aim for >50%
3. **Use hybrid search** for best results
4. **Index incrementally** - don't reindex everything
5. **Test with real queries** - validate search quality
6. **Set appropriate min_score** - filter low-quality matches
7. **Batch process** when indexing multiple videos
8. **Monitor query times** - optimize if >100ms

## FAQ

**Q: Do I need to reprocess videos?**
A: No, just install dependencies. New videos auto-index, old videos can be indexed manually.

**Q: What if I don't install dependencies?**
A: System works normally with keyword search only. No errors.

**Q: How much disk space needed?**
A: ~1MB per 1000 embeddings. 10K captions ≈ 10MB.

**Q: Can I use GPU?**
A: Yes! sentence-transformers auto-detects GPU. Speeds up indexing 10x.

**Q: How to disable semantic search?**
A: Uninstall dependencies or pass `use_semantic=False` to search methods.

**Q: Does it work offline?**
A: Yes, after first model download. No internet needed.

## Support

For issues or questions:
1. Check test output: `python scripts/test_vector_search.py`
2. Review logs for warnings/errors
3. Check documentation: `docs/TASK_49_SUMMARY.md`
4. Verify dependencies: `pip list | grep -E "chromadb|sentence"`
