"""Data archival and cleanup policies for BRI video agent.

This module provides functionality for:
- Soft delete of videos
- Archival of old conversation history
- Cleanup of orphaned frames/captions
- Data retention policies
- Database optimization (VACUUM)
"""

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from storage.database import Database, DatabaseError, get_database

logger = logging.getLogger(__name__)


class ArchivalManager:
    """Manages data archival and cleanup operations."""
    
    def __init__(self, db: Optional[Database] = None):
        """Initialize archival manager.
        
        Args:
            db: Optional database instance (uses global instance if not provided)
        """
        self.db = db or get_database()
    
    def soft_delete_video(self, video_id: str) -> bool:
        """Soft delete a video by setting deleted_at timestamp.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE videos 
                SET deleted_at = CURRENT_TIMESTAMP 
                WHERE video_id = ? AND deleted_at IS NULL
            """
            rows_affected = self.db.execute_update(query, (video_id,))
            
            if rows_affected > 0:
                logger.info(f"Soft deleted video: {video_id}")
                return True
            else:
                logger.warning(f"Video not found or already deleted: {video_id}")
                return False
                
        except DatabaseError as e:
            logger.error(f"Failed to soft delete video {video_id}: {e}")
            return False
    
    def restore_video(self, video_id: str) -> bool:
        """Restore a soft-deleted video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE videos 
                SET deleted_at = NULL 
                WHERE video_id = ? AND deleted_at IS NOT NULL
            """
            rows_affected = self.db.execute_update(query, (video_id,))
            
            if rows_affected > 0:
                logger.info(f"Restored video: {video_id}")
                return True
            else:
                logger.warning(f"Video not found or not deleted: {video_id}")
                return False
                
        except DatabaseError as e:
            logger.error(f"Failed to restore video {video_id}: {e}")
            return False
    
    def get_deleted_videos(self, days_old: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of soft-deleted videos.
        
        Args:
            days_old: Optional filter for videos deleted N days ago or more
            
        Returns:
            List of deleted video records
        """
        try:
            if days_old:
                query = """
                    SELECT * FROM videos 
                    WHERE deleted_at IS NOT NULL 
                    AND deleted_at <= datetime('now', '-' || ? || ' days')
                    ORDER BY deleted_at DESC
                """
                results = self.db.execute_query(query, (days_old,))
            else:
                query = """
                    SELECT * FROM videos 
                    WHERE deleted_at IS NOT NULL 
                    ORDER BY deleted_at DESC
                """
                results = self.db.execute_query(query)
            
            return [dict(row) for row in results]
            
        except DatabaseError as e:
            logger.error(f"Failed to get deleted videos: {e}")
            return []
    
    def permanently_delete_video(self, video_id: str, delete_files: bool = True) -> bool:
        """Permanently delete a video and all associated data.
        
        Args:
            video_id: Video identifier
            delete_files: Whether to delete associated files (frames, video file)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get video info before deletion
            video = self.db.execute_query(
                "SELECT * FROM videos WHERE video_id = ?",
                (video_id,)
            )
            
            if not video:
                logger.warning(f"Video not found: {video_id}")
                return False
            
            video_data = dict(video[0])
            
            # Delete from database (CASCADE will handle related records)
            self.db.execute_update("DELETE FROM videos WHERE video_id = ?", (video_id,))
            
            # Delete associated files if requested
            if delete_files:
                self._delete_video_files(video_data)
            
            logger.info(f"Permanently deleted video: {video_id}")
            return True
            
        except DatabaseError as e:
            logger.error(f"Failed to permanently delete video {video_id}: {e}")
            return False
    
    def _delete_video_files(self, video_data: Dict[str, Any]) -> None:
        """Delete video files and associated frames.
        
        Args:
            video_data: Video record dictionary
        """
        try:
            video_id = video_data['video_id']
            
            # Delete video file
            if video_data.get('file_path'):
                video_path = Path(video_data['file_path'])
                if video_path.exists():
                    video_path.unlink()
                    logger.info(f"Deleted video file: {video_path}")
            
            # Delete thumbnail
            if video_data.get('thumbnail_path'):
                thumb_path = Path(video_data['thumbnail_path'])
                if thumb_path.exists():
                    thumb_path.unlink()
                    logger.info(f"Deleted thumbnail: {thumb_path}")
            
            # Delete frames directory
            frames_dir = Path("data/frames") / video_id
            if frames_dir.exists():
                shutil.rmtree(frames_dir)
                logger.info(f"Deleted frames directory: {frames_dir}")
            
            # Delete cache directory
            cache_dir = Path("data/cache") / video_id
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                logger.info(f"Deleted cache directory: {cache_dir}")
                
        except Exception as e:
            logger.error(f"Failed to delete video files: {e}")
    
    def archive_old_conversations(self, days_old: int = 30) -> int:
        """Archive old conversation history.
        
        Args:
            days_old: Archive conversations older than N days
            
        Returns:
            Number of conversations archived
        """
        try:
            # For now, we'll just delete old conversations
            # In a production system, you might want to export to a separate archive database
            query = """
                DELETE FROM memory 
                WHERE timestamp <= datetime('now', '-' || ? || ' days')
            """
            rows_affected = self.db.execute_update(query, (days_old,))
            
            logger.info(f"Archived {rows_affected} old conversation records")
            return rows_affected
            
        except DatabaseError as e:
            logger.error(f"Failed to archive old conversations: {e}")
            return 0
    
    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """Clean up orphaned data (context without videos, files without database records).
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'orphaned_memory': 0,
            'orphaned_context': 0,
            'orphaned_lineage': 0,
            'orphaned_files': 0
        }
        
        try:
            # Clean up orphaned memory records
            query = """
                DELETE FROM memory 
                WHERE video_id NOT IN (SELECT video_id FROM videos)
            """
            stats['orphaned_memory'] = self.db.execute_update(query)
            
            # Clean up orphaned context records
            query = """
                DELETE FROM video_context 
                WHERE video_id NOT IN (SELECT video_id FROM videos)
            """
            stats['orphaned_context'] = self.db.execute_update(query)
            
            # Clean up orphaned lineage records
            query = """
                DELETE FROM data_lineage 
                WHERE video_id NOT IN (SELECT video_id FROM videos)
            """
            stats['orphaned_lineage'] = self.db.execute_update(query)
            
            # Clean up orphaned files
            stats['orphaned_files'] = self._cleanup_orphaned_files()
            
            logger.info(f"Cleanup complete: {stats}")
            return stats
            
        except DatabaseError as e:
            logger.error(f"Failed to cleanup orphaned data: {e}")
            return stats
    
    def _cleanup_orphaned_files(self) -> int:
        """Clean up orphaned video files and frames.
        
        Returns:
            Number of orphaned files/directories removed
        """
        count = 0
        
        try:
            # Get all video IDs from database
            video_ids = set()
            results = self.db.execute_query("SELECT video_id FROM videos")
            for row in results:
                video_ids.add(row['video_id'])
            
            # Check frames directory
            frames_dir = Path("data/frames")
            if frames_dir.exists():
                for video_dir in frames_dir.iterdir():
                    if video_dir.is_dir() and video_dir.name not in video_ids:
                        shutil.rmtree(video_dir)
                        logger.info(f"Removed orphaned frames directory: {video_dir}")
                        count += 1
            
            # Check cache directory
            cache_dir = Path("data/cache")
            if cache_dir.exists():
                for video_dir in cache_dir.iterdir():
                    if video_dir.is_dir() and video_dir.name not in video_ids:
                        shutil.rmtree(video_dir)
                        logger.info(f"Removed orphaned cache directory: {video_dir}")
                        count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned files: {e}")
            return count
    
    def vacuum_database(self) -> bool:
        """Optimize database by running VACUUM command.
        
        This reclaims unused space and defragments the database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db.get_connection()
            
            # Get database size before vacuum
            size_before = Path(self.db.db_path).stat().st_size
            
            logger.info("Running VACUUM on database...")
            conn.execute("VACUUM")
            conn.commit()
            
            # Get database size after vacuum
            size_after = Path(self.db.db_path).stat().st_size
            space_saved = size_before - size_after
            
            logger.info(
                f"VACUUM complete. Space saved: {space_saved / 1024 / 1024:.2f} MB "
                f"({size_before / 1024 / 1024:.2f} MB -> {size_after / 1024 / 1024:.2f} MB)"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            return False
    
    def analyze_database(self) -> bool:
        """Update database statistics for query optimization.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db.get_connection()
            logger.info("Running ANALYZE on database...")
            conn.execute("ANALYZE")
            conn.commit()
            logger.info("ANALYZE complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to analyze database: {e}")
            return False
    
    def get_retention_policy_status(self) -> Dict[str, Any]:
        """Get status of data retention policies.
        
        Returns:
            Dictionary with retention policy statistics
        """
        try:
            stats = {}
            
            # Count soft-deleted videos
            deleted_videos = self.db.execute_query("""
                SELECT COUNT(*) as count FROM videos WHERE deleted_at IS NOT NULL
            """)
            stats['soft_deleted_videos'] = deleted_videos[0]['count'] if deleted_videos else 0
            
            # Count old conversations (>30 days)
            old_conversations = self.db.execute_query("""
                SELECT COUNT(*) as count FROM memory 
                WHERE timestamp <= datetime('now', '-30 days')
            """)
            stats['old_conversations'] = old_conversations[0]['count'] if old_conversations else 0
            
            # Get database size
            db_size = Path(self.db.db_path).stat().st_size
            stats['database_size_mb'] = db_size / 1024 / 1024
            
            # Count total records
            stats['total_videos'] = self.db.execute_query("SELECT COUNT(*) as count FROM videos")[0]['count']
            stats['total_memory'] = self.db.execute_query("SELECT COUNT(*) as count FROM memory")[0]['count']
            stats['total_context'] = self.db.execute_query("SELECT COUNT(*) as count FROM video_context")[0]['count']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get retention policy status: {e}")
            return {}
    
    def apply_retention_policies(
        self,
        archive_conversations_days: int = 30,
        delete_soft_deleted_days: int = 7,
        cleanup_orphaned: bool = True,
        vacuum: bool = True
    ) -> Dict[str, Any]:
        """Apply all retention policies.
        
        Args:
            archive_conversations_days: Archive conversations older than N days
            delete_soft_deleted_days: Permanently delete videos soft-deleted N days ago
            cleanup_orphaned: Whether to cleanup orphaned data
            vacuum: Whether to vacuum database after cleanup
            
        Returns:
            Dictionary with operation results
        """
        results = {
            'archived_conversations': 0,
            'deleted_videos': 0,
            'cleanup_stats': {},
            'vacuum_success': False
        }
        
        logger.info("Applying retention policies...")
        
        # Archive old conversations
        results['archived_conversations'] = self.archive_old_conversations(archive_conversations_days)
        
        # Permanently delete old soft-deleted videos
        deleted_videos = self.get_deleted_videos(days_old=delete_soft_deleted_days)
        for video in deleted_videos:
            if self.permanently_delete_video(video['video_id'], delete_files=True):
                results['deleted_videos'] += 1
        
        # Cleanup orphaned data
        if cleanup_orphaned:
            results['cleanup_stats'] = self.cleanup_orphaned_data()
        
        # Vacuum database
        if vacuum:
            results['vacuum_success'] = self.vacuum_database()
            self.analyze_database()
        
        logger.info(f"Retention policies applied: {results}")
        return results


def get_archival_manager(db: Optional[Database] = None) -> ArchivalManager:
    """Get archival manager instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        ArchivalManager instance
    """
    return ArchivalManager(db)
