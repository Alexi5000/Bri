"""Embedding pipeline for batch processing and incremental updates."""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Optional imports
try:
    from services.semantic_search import get_semantic_search_service
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    logger.warning("Semantic search not available")


class EmbeddingPipeline:
    """Pipeline for managing video embedding generation and updates.
    
    Features:
    - Batch embedding generation for multiple videos
    - Incremental updates (only process new/changed data)
    - Embedding versioning (track model versions)
    - Fallback to keyword search if embeddings unavailable
    - Quality monitoring and metrics
    
    Example:
        pipeline = EmbeddingPipeline()
        pipeline.process_video(video_id)
        pipeline.process_batch([video_id1, video_id2, video_id3])
    """
    
    def __init__(
        self,
        metadata_file: str = "data/vector_db/embedding_metadata.json"
    ):
        """Initialize embedding pipeline.
        
        Args:
            metadata_file: Path to store embedding metadata (versions, timestamps, etc.)
        """
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()
        
        # Initialize semantic search service
        self.semantic_search = None
        self.enabled = False
        
        if SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.semantic_search = get_semantic_search_service()
                self.enabled = self.semantic_search.is_enabled()
                if self.enabled:
                    logger.info("Embedding pipeline initialized")
                else:
                    logger.warning("Embedding pipeline disabled (semantic search unavailable)")
            except Exception as e:
                logger.error(f"Failed to initialize embedding pipeline: {e}")
        else:
            logger.warning("Embedding pipeline disabled (dependencies not installed)")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load embedding metadata from file."""
        try:
            if Path(self.metadata_file).exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load embedding metadata: {e}")
        
        return {
            "videos": {},  # video_id -> {model_version, timestamp, caption_count, transcript_count}
            "model_version": "all-MiniLM-L6-v2",  # Current model version
            "created_at": datetime.now().isoformat()
        }
    
    def _save_metadata(self) -> None:
        """Save embedding metadata to file."""
        try:
            Path(self.metadata_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save embedding metadata: {e}")
    
    def is_enabled(self) -> bool:
        """Check if embedding pipeline is available."""
        return self.enabled
    
    def needs_indexing(self, video_id: str) -> bool:
        """Check if a video needs (re)indexing.
        
        A video needs indexing if:
        - It has never been indexed
        - The model version has changed
        - It's been marked for reindexing
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if video needs indexing, False otherwise
        """
        if not self.enabled:
            return False
        
        if video_id not in self.metadata["videos"]:
            return True
        
        video_meta = self.metadata["videos"][video_id]
        
        # Check if model version changed
        if video_meta.get("model_version") != self.metadata["model_version"]:
            logger.info(f"Video {video_id} needs reindexing (model version changed)")
            return True
        
        # Check if marked for reindexing
        if video_meta.get("needs_reindex", False):
            logger.info(f"Video {video_id} marked for reindexing")
            return True
        
        return False
    
    def process_video(
        self,
        video_id: str,
        captions: Optional[List[Dict[str, Any]]] = None,
        transcript_segments: Optional[List[Dict[str, Any]]] = None,
        force: bool = False
    ) -> bool:
        """Process a single video for embedding generation.
        
        Args:
            video_id: Video identifier
            captions: Optional list of caption dicts (if not provided, will fetch from DB)
            transcript_segments: Optional list of transcript segment dicts
            force: Force reindexing even if already indexed
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Embedding pipeline not enabled")
            return False
        
        # Check if indexing needed
        if not force and not self.needs_indexing(video_id):
            logger.info(f"Video {video_id} already indexed, skipping")
            return True
        
        try:
            logger.info(f"Processing video {video_id} for embedding generation")
            
            caption_count = 0
            transcript_count = 0
            
            # Index captions
            if captions is not None:
                if captions:
                    success = self.semantic_search.index_captions(video_id, captions)
                    if success:
                        caption_count = len(captions)
                        logger.info(f"Indexed {caption_count} captions for video {video_id}")
            
            # Index transcript segments
            if transcript_segments is not None:
                if transcript_segments:
                    success = self.semantic_search.index_transcripts(video_id, transcript_segments)
                    if success:
                        transcript_count = len(transcript_segments)
                        logger.info(f"Indexed {transcript_count} transcript segments for video {video_id}")
            
            # Update metadata
            self.metadata["videos"][video_id] = {
                "model_version": self.metadata["model_version"],
                "timestamp": datetime.now().isoformat(),
                "caption_count": caption_count,
                "transcript_count": transcript_count,
                "needs_reindex": False
            }
            self._save_metadata()
            
            logger.info(f"Successfully processed video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process video {video_id}: {e}")
            return False
    
    def process_batch(
        self,
        video_ids: List[str],
        fetch_data_callback: Optional[callable] = None,
        force: bool = False
    ) -> Dict[str, bool]:
        """Process multiple videos in batch.
        
        Args:
            video_ids: List of video identifiers
            fetch_data_callback: Optional callback to fetch caption/transcript data
                                 Should accept video_id and return (captions, segments)
            force: Force reindexing even if already indexed
            
        Returns:
            Dictionary mapping video_id to success status
        """
        if not self.enabled:
            logger.warning("Embedding pipeline not enabled")
            return {vid: False for vid in video_ids}
        
        logger.info(f"Processing batch of {len(video_ids)} videos")
        
        results = {}
        for video_id in video_ids:
            # Check if indexing needed
            if not force and not self.needs_indexing(video_id):
                logger.info(f"Video {video_id} already indexed, skipping")
                results[video_id] = True
                continue
            
            # Fetch data if callback provided
            captions = None
            segments = None
            if fetch_data_callback:
                try:
                    captions, segments = fetch_data_callback(video_id)
                except Exception as e:
                    logger.error(f"Failed to fetch data for video {video_id}: {e}")
                    results[video_id] = False
                    continue
            
            # Process video
            success = self.process_video(video_id, captions, segments, force=force)
            results[video_id] = success
        
        success_count = sum(1 for s in results.values() if s)
        logger.info(f"Batch processing complete: {success_count}/{len(video_ids)} successful")
        
        return results
    
    def mark_for_reindex(self, video_id: str) -> None:
        """Mark a video for reindexing.
        
        Useful when video data has been updated and embeddings need to be regenerated.
        
        Args:
            video_id: Video identifier
        """
        if video_id in self.metadata["videos"]:
            self.metadata["videos"][video_id]["needs_reindex"] = True
            self._save_metadata()
            logger.info(f"Marked video {video_id} for reindexing")
    
    def update_model_version(self, new_version: str) -> None:
        """Update the embedding model version.
        
        This will mark all videos for reindexing since embeddings need to be regenerated
        with the new model.
        
        Args:
            new_version: New model version identifier
        """
        old_version = self.metadata["model_version"]
        self.metadata["model_version"] = new_version
        
        # Mark all videos for reindexing
        for video_id in self.metadata["videos"]:
            self.metadata["videos"][video_id]["needs_reindex"] = True
        
        self._save_metadata()
        logger.info(f"Updated model version from {old_version} to {new_version}. All videos marked for reindexing.")
    
    def get_indexed_videos(self) -> List[str]:
        """Get list of videos that have been indexed.
        
        Returns:
            List of video IDs
        """
        return list(self.metadata["videos"].keys())
    
    def get_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding metadata for a specific video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Metadata dict or None if not indexed
        """
        return self.metadata["videos"].get(video_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics.
        
        Returns:
            Dictionary with stats
        """
        if not self.enabled:
            return {"enabled": False}
        
        total_videos = len(self.metadata["videos"])
        needs_reindex = sum(
            1 for v in self.metadata["videos"].values()
            if v.get("needs_reindex", False)
        )
        total_captions = sum(
            v.get("caption_count", 0)
            for v in self.metadata["videos"].values()
        )
        total_transcripts = sum(
            v.get("transcript_count", 0)
            for v in self.metadata["videos"].values()
        )
        
        return {
            "enabled": True,
            "model_version": self.metadata["model_version"],
            "total_videos_indexed": total_videos,
            "videos_needing_reindex": needs_reindex,
            "total_captions_indexed": total_captions,
            "total_transcripts_indexed": total_transcripts,
            "semantic_search_stats": self.semantic_search.get_stats() if self.semantic_search else {}
        }
    
    def delete_video_embeddings(self, video_id: str) -> bool:
        """Delete embeddings for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Delete from vector database
            success = self.semantic_search.delete_video_embeddings(video_id)
            
            # Remove from metadata
            if video_id in self.metadata["videos"]:
                del self.metadata["videos"][video_id]
                self._save_metadata()
            
            logger.info(f"Deleted embeddings for video {video_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete embeddings for video {video_id}: {e}")
            return False
    
    def reindex_all(self, fetch_data_callback: callable) -> Dict[str, bool]:
        """Reindex all videos in the system.
        
        Args:
            fetch_data_callback: Callback to fetch caption/transcript data
                                 Should accept video_id and return (captions, segments)
            
        Returns:
            Dictionary mapping video_id to success status
        """
        if not self.enabled:
            logger.warning("Embedding pipeline not enabled")
            return {}
        
        video_ids = self.get_indexed_videos()
        logger.info(f"Reindexing {len(video_ids)} videos")
        
        return self.process_batch(video_ids, fetch_data_callback, force=True)
    
    def monitor_quality(self, test_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Monitor embedding quality using test queries.
        
        Args:
            test_queries: List of test query dicts with 'query', 'video_id', 'expected_results'
            
        Returns:
            Quality metrics dictionary
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            total_queries = len(test_queries)
            successful_queries = 0
            total_precision = 0.0
            total_recall = 0.0
            
            for test in test_queries:
                query = test['query']
                video_id = test['video_id']
                expected = set(test.get('expected_results', []))
                
                # Perform search
                results = self.semantic_search.search(
                    query=query,
                    video_id=video_id,
                    top_k=5
                )
                
                if results:
                    successful_queries += 1
                    
                    # Calculate precision and recall
                    retrieved = set([r.text for r in results])
                    
                    if retrieved:
                        precision = len(retrieved & expected) / len(retrieved)
                        total_precision += precision
                    
                    if expected:
                        recall = len(retrieved & expected) / len(expected)
                        total_recall += recall
            
            avg_precision = total_precision / total_queries if total_queries > 0 else 0
            avg_recall = total_recall / total_queries if total_queries > 0 else 0
            success_rate = successful_queries / total_queries if total_queries > 0 else 0
            
            return {
                "enabled": True,
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": success_rate,
                "avg_precision": avg_precision,
                "avg_recall": avg_recall,
                "f1_score": 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor quality: {e}")
            return {"enabled": True, "error": str(e)}


# Global singleton instance
_embedding_pipeline = None


def get_embedding_pipeline() -> EmbeddingPipeline:
    """Get or create the global embedding pipeline instance."""
    global _embedding_pipeline
    if _embedding_pipeline is None:
        _embedding_pipeline = EmbeddingPipeline()
    return _embedding_pipeline
