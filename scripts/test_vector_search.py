"""Test script for vector search and semantic search functionality."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_semantic_search_availability():
    """Test if semantic search dependencies are available."""
    print("\n" + "="*60)
    print("TEST 1: Semantic Search Availability")
    print("="*60)
    
    try:
        from services.semantic_search import get_semantic_search_service
        
        service = get_semantic_search_service()
        
        if service.is_enabled():
            print("✅ Semantic search is ENABLED")
            stats = service.get_stats()
            print(f"   Model: {stats.get('model')}")
            print(f"   Embedding dimension: {stats.get('embedding_dim')}")
            print(f"   Total embeddings: {stats.get('total_embeddings')}")
            return True
        else:
            print("⚠️  Semantic search is DISABLED")
            print("   Install dependencies: pip install chromadb sentence-transformers")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_embedding_generation():
    """Test embedding generation."""
    print("\n" + "="*60)
    print("TEST 2: Embedding Generation")
    print("="*60)
    
    try:
        from services.semantic_search import get_semantic_search_service
        
        service = get_semantic_search_service()
        
        if not service.is_enabled():
            print("⚠️  Skipping (semantic search not enabled)")
            return False
        
        # Test single embedding
        text = "A person walking a dog in the park"
        embedding = service.generate_embedding(text)
        
        if embedding:
            print(f"✅ Generated embedding for: '{text}'")
            print(f"   Embedding length: {len(embedding)}")
            print(f"   First 5 values: {embedding[:5]}")
        else:
            print("❌ Failed to generate embedding")
            return False
        
        # Test batch embeddings
        texts = [
            "A cat sitting on a couch",
            "People playing soccer in a field",
            "A car driving on a highway"
        ]
        embeddings = service.generate_embeddings_batch(texts)
        
        if embeddings:
            print(f"✅ Generated {len(embeddings)} batch embeddings")
            return True
        else:
            print("❌ Failed to generate batch embeddings")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_indexing_and_search():
    """Test indexing captions and searching."""
    print("\n" + "="*60)
    print("TEST 3: Indexing and Search")
    print("="*60)
    
    try:
        from services.semantic_search import get_semantic_search_service
        
        service = get_semantic_search_service()
        
        if not service.is_enabled():
            print("⚠️  Skipping (semantic search not enabled)")
            return False
        
        # Create test captions
        test_video_id = "test_video_001"
        test_captions = [
            {
                "text": "A person walking a dog in the park",
                "frame_timestamp": 5.0,
                "confidence": 0.95
            },
            {
                "text": "A cat sitting on a windowsill",
                "frame_timestamp": 10.0,
                "confidence": 0.92
            },
            {
                "text": "People playing soccer in a field",
                "frame_timestamp": 15.0,
                "confidence": 0.88
            },
            {
                "text": "A car driving on a highway",
                "frame_timestamp": 20.0,
                "confidence": 0.90
            },
            {
                "text": "A dog running on the beach",
                "frame_timestamp": 25.0,
                "confidence": 0.93
            }
        ]
        
        # Index captions
        print(f"Indexing {len(test_captions)} test captions...")
        success = service.index_captions(test_video_id, test_captions)
        
        if not success:
            print("❌ Failed to index captions")
            return False
        
        print("✅ Captions indexed successfully")
        
        # Test search
        test_queries = [
            "dog",
            "person with pet",
            "sports activity",
            "vehicle on road"
        ]
        
        print("\nTesting semantic search:")
        for query in test_queries:
            results = service.search(
                query=query,
                video_id=test_video_id,
                top_k=2
            )
            
            print(f"\n  Query: '{query}'")
            if results:
                for i, result in enumerate(results, 1):
                    print(f"    {i}. {result.text} (score: {result.score:.3f})")
            else:
                print("    No results found")
        
        # Clean up
        service.delete_video_embeddings(test_video_id)
        print("\n✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_pipeline():
    """Test embedding pipeline functionality."""
    print("\n" + "="*60)
    print("TEST 4: Embedding Pipeline")
    print("="*60)
    
    try:
        from services.embedding_pipeline import get_embedding_pipeline
        
        pipeline = get_embedding_pipeline()
        
        if not pipeline.is_enabled():
            print("⚠️  Embedding pipeline not enabled")
            return False
        
        print("✅ Embedding pipeline is enabled")
        
        # Get stats
        stats = pipeline.get_stats()
        print(f"   Model version: {stats.get('model_version')}")
        print(f"   Total videos indexed: {stats.get('total_videos_indexed')}")
        print(f"   Total captions indexed: {stats.get('total_captions_indexed')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_performance_optimizer():
    """Test performance optimizer."""
    print("\n" + "="*60)
    print("TEST 5: Performance Optimizer")
    print("="*60)
    
    try:
        from services.vector_search_optimizer import get_vector_search_optimizer
        
        optimizer = get_vector_search_optimizer()
        print("✅ Performance optimizer initialized")
        
        # Get stats
        stats = optimizer.get_performance_stats()
        print(f"   Cache enabled: {stats.get('cache_enabled')}")
        print(f"   Total queries: {stats.get('total_queries')}")
        
        if "cache" in stats:
            cache_stats = stats["cache"]
            print(f"   Cache size: {cache_stats.get('size')}/{cache_stats.get('max_size')}")
            print(f"   Cache hit rate: {cache_stats.get('hit_rate', 0):.1%}")
        
        # Get recommendations
        recommendations = optimizer.recommend_optimizations(stats)
        if recommendations:
            print("\n   Recommendations:")
            for rec in recommendations:
                print(f"     - {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_hybrid_search():
    """Test hybrid search (keyword + semantic)."""
    print("\n" + "="*60)
    print("TEST 6: Hybrid Search")
    print("="*60)
    
    try:
        from services.semantic_search import get_semantic_search_service
        
        service = get_semantic_search_service()
        
        if not service.is_enabled():
            print("⚠️  Skipping (semantic search not enabled)")
            return False
        
        # Create test data
        test_video_id = "test_video_hybrid"
        test_captions = [
            {"text": "A golden retriever playing fetch", "frame_timestamp": 5.0, "confidence": 0.95},
            {"text": "A person throwing a ball", "frame_timestamp": 10.0, "confidence": 0.92},
            {"text": "A dog catching a frisbee", "frame_timestamp": 15.0, "confidence": 0.90}
        ]
        
        service.index_captions(test_video_id, test_captions)
        
        # Simulate keyword results
        keyword_results = [
            {"text": "A golden retriever playing fetch", "score": 80.0},
            {"text": "A person throwing a ball", "score": 40.0}
        ]
        
        # Perform hybrid search
        hybrid_results = service.hybrid_search(
            query="dog playing with toy",
            keyword_results=keyword_results,
            video_id=test_video_id,
            top_k=3
        )
        
        print("Hybrid search results:")
        for i, result in enumerate(hybrid_results, 1):
            print(f"  {i}. {result['text']}")
            print(f"     Combined: {result.get('combined_score', 0):.3f}, "
                  f"Keyword: {result.get('keyword_score', 0):.3f}, "
                  f"Semantic: {result.get('semantic_score', 0):.3f}")
        
        # Clean up
        service.delete_video_embeddings(test_video_id)
        
        print("✅ Hybrid search test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("VECTOR SEARCH TEST SUITE")
    print("="*60)
    
    tests = [
        ("Semantic Search Availability", test_semantic_search_availability),
        ("Embedding Generation", test_embedding_generation),
        ("Indexing and Search", test_indexing_and_search),
        ("Embedding Pipeline", test_embedding_pipeline),
        ("Performance Optimizer", test_performance_optimizer),
        ("Hybrid Search", test_hybrid_search)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
