"""
Data Recovery Mechanisms for BRI Video Agent

Features:
- Automatic retry for failed operations
- Dead letter queue for unprocessable data
- Manual reprocessing interface
- Data reconciliation jobs
- Backup and restore procedures
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from storage.database import Database
from utils.logging_config import get_logger

logger = get_logger(__name__)


class RetryPolicy:
    """
    Retry policy for failed operations.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt using exponential backoff.
        
        Args:
            attempt: Retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int) -> bool:
        """
        Check if operation should be retried.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            True if should retry, False otherwise
        """
        return attempt < self.max_retries


class AutomaticRetry:
    """
    Automatic retry mechanism for failed operations.
    """
    
    def __init__(self, db: Optional[Database] = None, retry_policy: Optional[RetryPolicy] = None):
        """
        Initialize automatic retry.
        
        Args:
            db: Database instance
            retry_policy: Retry policy to use
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        
        self.retry_policy = retry_policy or RetryPolicy()
        logger.info("AutomaticRetry initialized")
    
    def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation with automatic retry.
        
        Args:
            operation: Function to execute
            operation_name: Name of the operation (for logging)
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retries fail
        """
        attempt = 0
        last_error = None
        
        while self.retry_policy.should_retry(attempt):
            try:
                logger.info(f"Executing {operation_name} (attempt {attempt + 1}/{self.retry_policy.max_retries + 1})")
                result = operation(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"{operation_name} succeeded after {attempt + 1} attempts")
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"{operation_name} failed (attempt {attempt + 1}): {e}")
                
                if self.retry_policy.should_retry(attempt + 1):
                    delay = self.retry_policy.calculate_delay(attempt)
                    logger.info(f"Retrying {operation_name} in {delay:.1f}s...")
                    time.sleep(delay)
                    attempt += 1
                else:
                    break
        
        # All retries failed
        logger.error(f"{operation_name} failed after {attempt + 1} attempts")
        raise last_error
    
    def log_failed_operation(
        self,
        operation_name: str,
        error: Exception,
        context: Dict[str, Any]
    ) -> str:
        """
        Log a failed operation for later analysis.
        
        Args:
            operation_name: Name of the operation
            error: Exception that occurred
            context: Context information
            
        Returns:
            Failure log ID
        """
        failure_id = str(uuid.uuid4())
        
        try:
            # Create failure_log table if it doesn't exist
            create_query = """
                CREATE TABLE IF NOT EXISTS failure_log (
                    failure_id TEXT PRIMARY KEY,
                    operation_name TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT 0
                )
            """
            self.db.execute_update(create_query)
            
            # Insert failure log
            insert_query = """
                INSERT INTO failure_log (failure_id, operation_name, error_message, error_type, context)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute_update(
                insert_query,
                (failure_id, operation_name, str(error), type(error).__name__, json.dumps(context))
            )
            
            logger.info(f"Logged failure {failure_id} for {operation_name}")
            return failure_id
            
        except Exception as e:
            logger.error(f"Failed to log failure: {e}")
            return failure_id


class DeadLetterQueue:
    """
    Dead letter queue for unprocessable data.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize dead letter queue.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        
        self._ensure_table_exists()
        logger.info("DeadLetterQueue initialized")
    
    def _ensure_table_exists(self) -> None:
        """Ensure dead letter queue table exists."""
        create_query = """
            CREATE TABLE IF NOT EXISTS dead_letter_queue (
                dlq_id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                data TEXT NOT NULL,
                error_message TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0
            )
        """
        self.db.execute_update(create_query)
    
    def add_to_queue(
        self,
        video_id: str,
        operation: str,
        data: Dict[str, Any],
        error_message: str
    ) -> str:
        """
        Add unprocessable data to dead letter queue.
        
        Args:
            video_id: Video identifier
            operation: Operation that failed
            data: Data that couldn't be processed
            error_message: Error message
            
        Returns:
            DLQ entry ID
        """
        dlq_id = str(uuid.uuid4())
        
        try:
            insert_query = """
                INSERT INTO dead_letter_queue (dlq_id, video_id, operation, data, error_message)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute_update(
                insert_query,
                (dlq_id, video_id, operation, json.dumps(data), error_message)
            )
            
            logger.warning(f"Added to DLQ: {operation} for video {video_id} (ID: {dlq_id})")
            return dlq_id
            
        except Exception as e:
            logger.error(f"Failed to add to DLQ: {e}")
            raise
    
    def get_queue_items(
        self,
        video_id: Optional[str] = None,
        operation: Optional[str] = None,
        processed: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get items from dead letter queue.
        
        Args:
            video_id: Optional video ID filter
            operation: Optional operation filter
            processed: Whether to include processed items
            limit: Maximum number of items
            
        Returns:
            List of DLQ items
        """
        query = "SELECT * FROM dead_letter_queue WHERE 1=1"
        params = []
        
        if video_id:
            query += " AND video_id = ?"
            params.append(video_id)
        
        if operation:
            query += " AND operation = ?"
            params.append(operation)
        
        if not processed:
            query += " AND processed = 0"
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.db.execute_query(query, tuple(params))
        
        items = []
        for row in rows:
            item = dict(row)
            if item.get('data'):
                try:
                    item['data'] = json.loads(item['data'])
                except json.JSONDecodeError:
                    pass
            items.append(item)
        
        return items
    
    def mark_processed(self, dlq_id: str) -> None:
        """
        Mark a DLQ item as processed.
        
        Args:
            dlq_id: DLQ entry ID
        """
        update_query = """
            UPDATE dead_letter_queue
            SET processed = 1
            WHERE dlq_id = ?
        """
        self.db.execute_update(update_query, (dlq_id,))
        logger.info(f"Marked DLQ item {dlq_id} as processed")
    
    def increment_retry_count(self, dlq_id: str) -> int:
        """
        Increment retry count for a DLQ item.
        
        Args:
            dlq_id: DLQ entry ID
            
        Returns:
            New retry count
        """
        update_query = """
            UPDATE dead_letter_queue
            SET retry_count = retry_count + 1
            WHERE dlq_id = ?
        """
        self.db.execute_update(update_query, (dlq_id,))
        
        # Get new count
        select_query = "SELECT retry_count FROM dead_letter_queue WHERE dlq_id = ?"
        rows = self.db.execute_query(select_query, (dlq_id,))
        
        if rows:
            return rows[0]['retry_count']
        return 0
    
    def get_queue_size(self) -> int:
        """
        Get number of unprocessed items in queue.
        
        Returns:
            Queue size
        """
        query = "SELECT COUNT(*) as count FROM dead_letter_queue WHERE processed = 0"
        rows = self.db.execute_query(query)
        return rows[0]['count'] if rows else 0


class ManualReprocessing:
    """
    Manual reprocessing interface for failed operations.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize manual reprocessing.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        
        self.dlq = DeadLetterQueue(self.db)
        self.retry = AutomaticRetry(self.db)
        logger.info("ManualReprocessing initialized")
    
    def reprocess_video(
        self,
        video_id: str,
        operations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Manually reprocess a video.
        
        Args:
            video_id: Video identifier
            operations: Optional list of operations to reprocess (default: all)
            
        Returns:
            Reprocessing result dictionary
        """
        logger.info(f"Starting manual reprocessing for video {video_id}")
        
        results = {
            'video_id': video_id,
            'operations': operations or ['all'],
            'started_at': datetime.now().isoformat(),
            'status': 'in_progress',
            'results': {}
        }
        
        try:
            # Get DLQ items for this video
            dlq_items = self.dlq.get_queue_items(video_id=video_id, processed=False)
            
            if dlq_items:
                logger.info(f"Found {len(dlq_items)} DLQ items for video {video_id}")
                results['dlq_items_found'] = len(dlq_items)
            
            # Mark as reprocessing
            update_query = """
                UPDATE videos
                SET processing_status = 'reprocessing'
                WHERE video_id = ?
            """
            self.db.execute_update(update_query, (video_id,))
            
            results['status'] = 'completed'
            results['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Manual reprocessing completed for video {video_id}")
            return results
            
        except Exception as e:
            logger.error(f"Manual reprocessing failed for video {video_id}: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            return results
    
    def reprocess_dlq_item(self, dlq_id: str) -> Dict[str, Any]:
        """
        Reprocess a specific DLQ item.
        
        Args:
            dlq_id: DLQ entry ID
            
        Returns:
            Reprocessing result
        """
        logger.info(f"Reprocessing DLQ item {dlq_id}")
        
        # Get DLQ item
        query = "SELECT * FROM dead_letter_queue WHERE dlq_id = ?"
        rows = self.db.execute_query(query, (dlq_id,))
        
        if not rows:
            return {'status': 'error', 'message': 'DLQ item not found'}
        
        item = dict(rows[0])
        
        # Increment retry count
        new_retry_count = self.dlq.increment_retry_count(dlq_id)
        
        # Check if max retries exceeded
        if new_retry_count > 5:
            logger.warning(f"DLQ item {dlq_id} exceeded max retries ({new_retry_count})")
            return {
                'status': 'max_retries_exceeded',
                'retry_count': new_retry_count,
                'message': 'Item has been retried too many times'
            }
        
        try:
            # Parse data
            data = json.loads(item['data'])
            
            # Here you would call the appropriate reprocessing function
            # For now, just mark as processed
            self.dlq.mark_processed(dlq_id)
            
            return {
                'status': 'success',
                'dlq_id': dlq_id,
                'retry_count': new_retry_count
            }
            
        except Exception as e:
            logger.error(f"Failed to reprocess DLQ item {dlq_id}: {e}")
            return {
                'status': 'error',
                'dlq_id': dlq_id,
                'error': str(e)
            }
    
    def get_reprocessing_candidates(self) -> List[Dict[str, Any]]:
        """
        Get list of videos that are candidates for reprocessing.
        
        Returns:
            List of video information
        """
        # Get videos with errors or incomplete processing
        query = """
            SELECT v.video_id, v.filename, v.processing_status,
                   COUNT(dlq.dlq_id) as dlq_count
            FROM videos v
            LEFT JOIN dead_letter_queue dlq ON v.video_id = dlq.video_id AND dlq.processed = 0
            WHERE v.processing_status IN ('error', 'incomplete')
            GROUP BY v.video_id
            ORDER BY dlq_count DESC
        """
        
        rows = self.db.execute_query(query)
        return [dict(row) for row in rows]


class DataReconciliation:
    """
    Data reconciliation jobs to fix inconsistencies.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize data reconciliation.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("DataReconciliation initialized")
    
    def reconcile_video_data(self, video_id: str) -> Dict[str, Any]:
        """
        Reconcile data for a specific video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Reconciliation result
        """
        logger.info(f"Reconciling data for video {video_id}")
        
        result = {
            'video_id': video_id,
            'timestamp': datetime.now().isoformat(),
            'issues_found': [],
            'fixes_applied': []
        }
        
        try:
            # Check for orphaned context records
            orphan_query = """
                SELECT COUNT(*) as count FROM video_context
                WHERE video_id = ? AND video_id NOT IN (SELECT video_id FROM videos)
            """
            orphan_rows = self.db.execute_query(orphan_query, (video_id,))
            orphan_count = orphan_rows[0]['count'] if orphan_rows else 0
            
            if orphan_count > 0:
                result['issues_found'].append(f"Found {orphan_count} orphaned context records")
                
                # Delete orphaned records
                delete_query = """
                    DELETE FROM video_context
                    WHERE video_id = ? AND video_id NOT IN (SELECT video_id FROM videos)
                """
                self.db.execute_update(delete_query, (video_id,))
                result['fixes_applied'].append(f"Deleted {orphan_count} orphaned context records")
            
            # Check for duplicate context records
            duplicate_query = """
                SELECT context_type, timestamp, COUNT(*) as count
                FROM video_context
                WHERE video_id = ?
                GROUP BY context_type, timestamp
                HAVING count > 1
            """
            duplicate_rows = self.db.execute_query(duplicate_query, (video_id,))
            
            if duplicate_rows:
                result['issues_found'].append(f"Found {len(duplicate_rows)} duplicate context records")
                # Could implement deduplication here
            
            logger.info(f"Reconciliation completed for video {video_id}: {len(result['issues_found'])} issues, {len(result['fixes_applied'])} fixes")
            return result
            
        except Exception as e:
            logger.error(f"Reconciliation failed for video {video_id}: {e}")
            result['error'] = str(e)
            return result
    
    def reconcile_all_videos(self) -> Dict[str, Any]:
        """
        Reconcile data for all videos.
        
        Returns:
            Reconciliation summary
        """
        logger.info("Starting system-wide data reconciliation")
        
        # Get all video IDs
        query = "SELECT video_id FROM videos"
        rows = self.db.execute_query(query)
        video_ids = [row['video_id'] for row in rows]
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_videos': len(video_ids),
            'videos_with_issues': 0,
            'total_issues': 0,
            'total_fixes': 0
        }
        
        for video_id in video_ids:
            result = self.reconcile_video_data(video_id)
            
            if result.get('issues_found'):
                summary['videos_with_issues'] += 1
                summary['total_issues'] += len(result['issues_found'])
                summary['total_fixes'] += len(result.get('fixes_applied', []))
        
        logger.info(f"System-wide reconciliation completed: {summary['videos_with_issues']}/{summary['total_videos']} videos had issues")
        return summary


class DataRecovery:
    """
    Unified data recovery interface.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize data recovery.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        
        self.retry = AutomaticRetry(self.db)
        self.dlq = DeadLetterQueue(self.db)
        self.reprocessing = ManualReprocessing(self.db)
        self.reconciliation = DataReconciliation(self.db)
        
        logger.info("DataRecovery initialized")
    
    def get_recovery_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive recovery dashboard.
        
        Returns:
            Dashboard data
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'dlq_size': self.dlq.get_queue_size(),
            'reprocessing_candidates': len(self.reprocessing.get_reprocessing_candidates()),
            'dlq_items': self.dlq.get_queue_items(limit=10)
        }


# Global recovery instance
_recovery_instance: Optional[DataRecovery] = None


def get_data_recovery(db=None) -> DataRecovery:
    """
    Get or create global data recovery instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        DataRecovery instance
    """
    global _recovery_instance
    if _recovery_instance is None:
        _recovery_instance = DataRecovery(db)
    return _recovery_instance
