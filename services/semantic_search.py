"""Semantic search service using vector embeddings and ChromaDB."""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Optional imports - gracefully handle if not installed
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Semantic search will be unavailable.")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Semantic search will be unavailable.")


@dataclass
class SemanticSearchResult:
    """Result from semantic search."""
    text: str
    score: float  # Similarity score (0-1, higher is better)
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class SemanticSearchService:
    """Semantic search service using embeddings and vector similarity.
    
    Features:
    - Generate embeddings for captions and transcripts
    - Store embeddings in ChromaDB vector database
    - Perform similarity search with metadata filtering
    - Hybrid search combining keyword and semantic matching
    - Batch processing for efficiency
    
    Example:
        service = SemanticSearchService()
        service.index_captions(video_id, captions)
        results = service.search_captions(video_id, "person walking dog", top_k=5)
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_directory: str = "data/vector_db",
        collection_name: str = "bri_captions",
        enable_cache: bool = True
    ):
        """Initialize semantic search service.
        
        Args:
            model_name: Sentence transformer model name
                - "all-MiniLM-L6-v2": Fast, 384 dims, good quality (RECOMMENDED)
                - "all-mpnet-base-v2": Slower, 768 dims, best quality
                - "paraphrase-MiniLM-L6-v2": Fast, 384 dims, paraphrase focused
            persist_directory: Directory to store vector database
            collection_name: Name of the ChromaDB collection
            enable_cache: Whether to enable query result caching
        """
        self.model_name = model_name
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        self.model = None
        self.client = None
        self.collection = None
        self.enabled = False
        
        # Initialize optimizer for performance
        self.optimizer = None
        if enable_cache:
            try:
                from services.vector_search_optimizer import get_vector_search_optimizer
                self.optimizer = get_vector_search_optimizer()
            except Exception as e:
                logger.warning(f"Failed to initialize optimizer: {e}")
        
        # Initialize if dependencies available
        if CHROMADB_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self._initialize()
                self.enabled = True
                logger.info(f"Semantic search enabled with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize semantic search: {e}")
                self.enabled = False
        else:
            missing = []
            if not CHROMADB_AVAILABLE:
                missing.append("chromadb")
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                missing.append("sentence-transformers")
            logger.warning(
                f"Semantic search disabled. Missing dependencies: {', '.join(missing)}. "
                f"Install with: pip install {' '.join(missing)}"
            )
    
    def _initialize(self) -> None:
        """Initialize embedding model and vector database."""
        # Load sentence transformer model
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "BRI video caption embeddings"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def is_enabled(self) -> bool:
        """Check if semantic search is available."""
        return self.enabled
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats, or None if disabled
        """
        if not self.enabled or not self.model:
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for multiple texts (more efficient).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors, or None if disabled
        """
        if not self.enabled or not self.model:
            return None
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return None
    
    def index_captions(
        self,
        video_id: str,
        captions: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> bool:
        """Index captions for a video with embeddings.
        
        Args:
            video_id: Video identifier
            captions: List of caption dicts with 'text', 'frame_timestamp', 'confidence'
            batch_size: Number of captions to process at once
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.collection:
            logger.warning("Semantic search not enabled. Skipping indexing.")
            return False
        
        if not captions:
            logger.warning(f"No captions to index for video {video_id}")
            return False
        
        try:
            logger.info(f"Indexing {len(captions)} captions for video {video_id}")
            
            # Process in batches for efficiency
            for i in range(0, len(captions), batch_size):
                batch = captions[i:i + batch_size]
                
                # Extract texts
                texts = [cap['text'] for cap in batch]
                
                # Generate embeddings
                embeddings = self.generate_embeddings_batch(texts)
                if not embeddings:
                    logger.error("Failed to generate embeddings")
                    return False
                
                # Prepare IDs and metadata
                ids = [f"{video_id}_cap_{i+j}" for j in range(len(batch))]
                metadatas = [
                    {
                        "video_id": video_id,
                        "timestamp": cap['frame_timestamp'],
                        "confidence": cap.get('confidence', 1.0),
                        "type": "caption"
                    }
                    for cap in batch
                ]
                
                # Add to collection
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.debug(f"Indexed batch {i//batch_size + 1}/{(len(captions)-1)//batch_size + 1}")
            
            logger.info(f"Successfully indexed {len(captions)} captions for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index captions: {e}")
            return False
    
    def index_transcripts(
        self,
        video_id: str,
        segments: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> bool:
        """Index transcript segments for a video with embeddings.
        
        Args:
            video_id: Video identifier
            segments: List of segment dicts with 'text', 'start', 'end', 'confidence'
            batch_size: Number of segments to process at once
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.collection:
            logger.warning("Semantic search not enabled. Skipping indexing.")
            return False
        
        if not segments:
            logger.warning(f"No transcript segments to index for video {video_id}")
            return False
        
        try:
            logger.info(f"Indexing {len(segments)} transcript segments for video {video_id}")
            
            # Process in batches
            for i in range(0, len(segments), batch_size):
                batch = segments[i:i + batch_size]
                
                # Extract texts
                texts = [seg['text'] for seg in batch]
                
                # Generate embeddings
                embeddings = self.generate_embeddings_batch(texts)
                if not embeddings:
                    logger.error("Failed to generate embeddings")
                    return False
                
                # Prepare IDs and metadata
                ids = [f"{video_id}_trans_{i+j}" for j in range(len(batch))]
                metadatas = [
                    {
                        "video_id": video_id,
                        "timestamp": seg['start'],
                        "end_timestamp": seg['end'],
                        "confidence": seg.get('confidence', 1.0),
                        "type": "transcript"
                    }
                    for seg in batch
                ]
                
                # Add to collection
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.debug(f"Indexed batch {i//batch_size + 1}/{(len(segments)-1)//batch_size + 1}")
            
            logger.info(f"Successfully indexed {len(segments)} transcript segments for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index transcript segments: {e}")
            return False
    
    def search(
        self,
        query: str,
        video_id: Optional[str] = None,
        content_type: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.0,
        use_cache: bool = True
    ) -> List[SemanticSearchResult]:
        """Perform semantic similarity search.
        
        Args:
            query: Search query text
            video_id: Optional video ID to filter results
            content_type: Optional content type filter ("caption" or "transcript")
            top_k: Number of results to return
            min_score: Minimum similarity score threshold (0-1)
            use_cache: Whether to use cached results (if available)
            
        Returns:
            List of SemanticSearchResult objects sorted by relevance
        """
        if not self.enabled or not self.collection:
            logger.warning("Semantic search not enabled")
            return []
        
        # Use optimizer cache if available
        if use_cache and self.optimizer:
            results, was_cached = self.optimizer.search_with_cache(
                search_func=self._search_internal,
                query=query,
                video_id=video_id,
                content_type=content_type,
                top_k=top_k,
                min_score=min_score
            )
            return results
        
        # Direct search without cache
        return self._search_internal(query, video_id, content_type, top_k, min_score)
    
    def _search_internal(
        self,
        query: str,
        video_id: Optional[str] = None,
        content_type: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[SemanticSearchResult]:
        """Internal search implementation (called by search() with/without cache).
        
        Args:
            query: Search query text
            video_id: Optional video ID to filter results
            content_type: Optional content type filter ("caption" or "transcript")
            top_k: Number of results to return
            min_score: Minimum similarity score threshold (0-1)
            
        Returns:
            List of SemanticSearchResult objects sorted by relevance
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Build metadata filter
            where_filter = {}
            if video_id:
                where_filter["video_id"] = video_id
            if content_type:
                where_filter["type"] = content_type
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None
            )
            
            # Parse results
            search_results = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    # ChromaDB returns distances, convert to similarity scores
                    # Distance is L2 distance, convert to similarity (0-1)
                    distance = results['distances'][0][i] if results['distances'] else 0
                    score = 1.0 / (1.0 + distance)  # Convert distance to similarity
                    
                    if score >= min_score:
                        search_results.append(SemanticSearchResult(
                            text=doc,
                            score=score,
                            metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                        ))
            
            logger.info(f"Semantic search found {len(search_results)} results for query: {query}")
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        keyword_results: List[Dict[str, Any]],
        video_id: Optional[str] = None,
        top_k: int = 5,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining keyword and semantic matching.
        
        Args:
            query: Search query text
            keyword_results: Results from keyword search (with 'text' and 'score' fields)
            video_id: Optional video ID to filter results
            top_k: Number of results to return
            semantic_weight: Weight for semantic scores (0-1), keyword weight = 1 - semantic_weight
            
        Returns:
            List of results with combined scores, sorted by relevance
        """
        if not self.enabled:
            logger.info("Semantic search disabled, returning keyword results only")
            return keyword_results[:top_k]
        
        try:
            # Get semantic search results
            semantic_results = self.search(query, video_id=video_id, top_k=top_k * 2)
            
            if not semantic_results:
                logger.info("No semantic results, returning keyword results only")
                return keyword_results[:top_k]
            
            # Combine scores
            # Create lookup for semantic scores by text
            semantic_scores = {r.text: r.score for r in semantic_results}
            
            # Score all results
            combined_results = []
            seen_texts = set()
            
            # Process keyword results
            for kw_result in keyword_results:
                text = kw_result.get('text', '')
                if text in seen_texts:
                    continue
                seen_texts.add(text)
                
                kw_score = kw_result.get('score', 0.0)
                sem_score = semantic_scores.get(text, 0.0)
                
                # Normalize scores to 0-1 range
                kw_score_norm = min(kw_score / 100.0, 1.0)  # Assuming keyword scores are 0-100
                
                # Combine scores
                combined_score = (
                    (1 - semantic_weight) * kw_score_norm +
                    semantic_weight * sem_score
                )
                
                result = kw_result.copy()
                result['combined_score'] = combined_score
                result['keyword_score'] = kw_score_norm
                result['semantic_score'] = sem_score
                combined_results.append(result)
            
            # Add semantic-only results (not in keyword results)
            for sem_result in semantic_results:
                if sem_result.text not in seen_texts:
                    seen_texts.add(sem_result.text)
                    combined_results.append({
                        'text': sem_result.text,
                        'metadata': sem_result.metadata,
                        'combined_score': semantic_weight * sem_result.score,
                        'keyword_score': 0.0,
                        'semantic_score': sem_result.score
                    })
            
            # Sort by combined score
            combined_results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            logger.info(
                f"Hybrid search combined {len(keyword_results)} keyword + "
                f"{len(semantic_results)} semantic results → {len(combined_results[:top_k])} final"
            )
            
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return keyword_results[:top_k]
    
    def delete_video_embeddings(self, video_id: str) -> bool:
        """Delete all embeddings for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.collection:
            return False
        
        try:
            # Query for all IDs with this video_id
            results = self.collection.get(
                where={"video_id": video_id}
            )
            
            if results and results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} embeddings for video {video_id}")
                return True
            else:
                logger.info(f"No embeddings found for video {video_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete embeddings: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database.
        
        Returns:
            Dictionary with stats (count, model info, etc.)
        """
        if not self.enabled or not self.collection:
            return {"enabled": False}
        
        try:
            count = self.collection.count()
            stats = {
                "enabled": True,
                "model": self.model_name,
                "embedding_dim": self.model.get_sentence_embedding_dimension() if self.model else None,
                "total_embeddings": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
            
            # Add performance stats if optimizer available
            if self.optimizer:
                stats["performance"] = self.optimizer.get_performance_stats()
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations.
        
        Returns:
            List of recommendation strings
        """
        if not self.optimizer:
            return ["Performance optimizer not available"]
        
        stats = self.get_stats()
        if "performance" in stats:
            return self.optimizer.recommend_optimizations(stats["performance"])
        
        return []
    
    def invalidate_cache(self, video_id: Optional[str] = None) -> None:
        """Invalidate query cache.
        
        Args:
            video_id: If provided, only invalidate entries for this video
        """
        if self.optimizer:
            self.optimizer.invalidate_cache(video_id)
    
    def close(self) -> None:
        """Clean up resources."""
        if self.client:
            # ChromaDB client doesn't need explicit closing
            logger.info("Semantic search service closed")


# Global singleton instance
_semantic_search_service = None


def get_semantic_search_service() -> SemanticSearchService:
    """Get or create the global semantic search service instance."""
    global _semantic_search_service
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    return _semantic_search_service
