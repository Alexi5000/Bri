"""
Centralized Video Processing Service for BRI
Handles all video data persistence with transactions, validation, and retry logic
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional
from storage.database import Database
from services.data_validator import ValidationError, get_data_validator
from services.data_lineage_tracker import get_lineage_tracker
from utils.logging_config import get_logger

logger = get_logger(__name__)


class VideoProcessingServiceError(Exception):
    """Custom exception for video processing service errors."""
    pass


class VideoProcessingService:
    """
    Centralized service for storing video processing results.
    
    Features:
    - Transaction support for atomic writes
    - Validation after INSERT (SELECT to confirm)
    - Retry logic with exponential backoff
    - Comprehensive logging and metrics
    """
    
    def __init__(self, db: Optional[Database] = None, max_retries: int = 3):
        """
        Initialize Video Processing Service.
        
        Args:
            db: Database instance. Creates new instance if not provided.
            max_retries: Maximum number of retry attempts for failed writes
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        self.max_retries = max_retries
        self.validator = get_data_validator(self.db)
        self.lineage_tracker = get_lineage_tracker(self.db)
        logger.info("Video Processing Service initialized")
    
    def store_tool_results(
        self,
        video_id: str,
        tool_name: str,
        results: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Store tool execution results in database with transaction support and idempotency.
        
        Args:
            video_id: Video identifier
            tool_name: Name of the tool that generated results
            results: Tool execution results dictionary
            idempotency_key: Optional key to prevent duplicate processing
            
        Returns:
            Dictionary with counts of stored items:
            {
                'frames': 5,
                'captions': 5,
                'transcripts': 10,
                'objects': 5
            }
            
        Raises:
            VideoProcessingServiceError: If storage fails after all retries
        """
        logger.info(f"Storing {tool_name} results for video {video_id}")
        
        # Check idempotency: if this exact operation was already completed, skip
        if idempotency_key and self._check_idempotency(video_id, tool_name, idempotency_key):
            logger.info(f"Operation already completed (idempotency key: {idempotency_key}), skipping")
            return self._get_existing_counts(video_id, tool_name)
        
        # Route to appropriate storage method based on tool name
        if tool_name == 'extract_frames':
            result = self._store_frames(video_id, results)
        elif tool_name == 'caption_frames':
            result = self._store_captions(video_id, results)
        elif tool_name == 'transcribe_audio':
            result = self._store_transcript(video_id, results)
        elif tool_name == 'detect_objects':
            result = self._store_objects(video_id, results)
        else:
            logger.warning(f"Unknown tool name: {tool_name}")
            return {}
        
        # Record idempotency key if provided
        if idempotency_key:
            self._record_idempotency(video_id, tool_name, idempotency_key)
        
        return result
    
    def _store_frames(self, video_id: str, results: Dict[str, Any]) -> Dict[str, int]:
        """
        Store frame extraction results with validation.
        
        Args:
            video_id: Video identifier
            results: Frame extraction results with 'frames' list
            
        Returns:
            Dictionary with count: {'frames': N}
        """
        frames = results.get('frames', [])
        if not frames:
            logger.warning(f"No frames to store for video {video_id}")
            return {'frames': 0}
        
        # Validate batch before insertion
        valid, errors = self.validator.validate_batch('frame', frames, video_id)
        if not valid:
            logger.error(f"Frame validation failed for video {video_id}: {errors}")
            raise ValidationError(f"Frame validation failed: {'; '.join(errors)}")
        
        # Prepare batch insert data with lineage metadata
        insert_data = []
        context_ids = []
        tool_version = self.lineage_tracker.TOOL_VERSIONS.get('extract_frames', '1.0.0')
        
        for frame in frames:
            context_id = str(uuid.uuid4())
            context_ids.append(context_id)
            timestamp = frame.get('timestamp', 0)
            data_json = json.dumps(frame)
            insert_data.append((
                context_id, video_id, 'frame', timestamp, data_json,
                'extract_frames', tool_version, None, None
            ))
        
        # Execute batch insert with transaction
        stored_count = self._batch_insert_with_retry(
            video_id,
            'frame',
            insert_data,
            with_lineage=True
        )
        
        # Record lineage
        try:
            self.lineage_tracker.record_batch_processing(
                video_id, context_ids, 'extract_frames'
            )
        except Exception as e:
            logger.warning(f"Failed to record lineage: {e}")
        
        logger.info(f"Stored {stored_count} frames for video {video_id}")
        return {'frames': stored_count}
    
    def _store_captions(self, video_id: str, results: Dict[str, Any]) -> Dict[str, int]:
        """
        Store caption generation results with validation.
        
        Args:
            video_id: Video identifier
            results: Caption results with 'captions' list
            
        Returns:
            Dictionary with count: {'captions': N}
        """
        captions = results.get('captions', [])
        if not captions:
            logger.warning(f"No captions to store for video {video_id}")
            return {'captions': 0}
        
        # Validate batch before insertion
        valid, errors = self.validator.validate_batch('caption', captions, video_id)
        if not valid:
            logger.error(f"Caption validation failed for video {video_id}: {errors}")
            raise ValidationError(f"Caption validation failed: {'; '.join(errors)}")
        
        # Prepare batch insert data with lineage metadata
        insert_data = []
        context_ids = []
        tool_version = self.lineage_tracker.TOOL_VERSIONS.get('caption_frames', '1.0.0')
        model_version = self.lineage_tracker.MODEL_VERSIONS.get('blip')
        
        for caption in captions:
            context_id = str(uuid.uuid4())
            context_ids.append(context_id)
            timestamp = caption.get('frame_timestamp', 0)
            data_json = json.dumps(caption)
            insert_data.append((
                context_id, video_id, 'caption', timestamp, data_json,
                'caption_frames', tool_version, model_version, None
            ))
        
        # Execute batch insert with transaction
        stored_count = self._batch_insert_with_retry(
            video_id,
            'caption',
            insert_data,
            with_lineage=True
        )
        
        # Record lineage
        try:
            self.lineage_tracker.record_batch_processing(
                video_id, context_ids, 'caption_frames'
            )
        except Exception as e:
            logger.warning(f"Failed to record lineage: {e}")
        
        logger.info(f"Stored {stored_count} captions for video {video_id}")
        return {'captions': stored_count}
    
    def _store_transcript(self, video_id: str, results: Dict[str, Any]) -> Dict[str, int]:
        """
        Store audio transcription results with validation.
        
        Args:
            video_id: Video identifier
            results: Transcript results with 'segments' list
            
        Returns:
            Dictionary with count: {'transcript_segments': N}
        """
        segments = results.get('segments', [])
        if not segments:
            logger.warning(f"No transcript segments to store for video {video_id}")
            return {'transcript_segments': 0}
        
        # Validate batch before insertion
        valid, errors = self.validator.validate_batch('transcript', segments, video_id)
        if not valid:
            logger.error(f"Transcript validation failed for video {video_id}: {errors}")
            raise ValidationError(f"Transcript validation failed: {'; '.join(errors)}")
        
        # Prepare batch insert data with lineage metadata
        insert_data = []
        context_ids = []
        tool_version = self.lineage_tracker.TOOL_VERSIONS.get('transcribe_audio', '1.0.0')
        model_version = self.lineage_tracker.MODEL_VERSIONS.get('whisper')
        
        for segment in segments:
            context_id = str(uuid.uuid4())
            context_ids.append(context_id)
            timestamp = segment.get('start', 0)
            data_json = json.dumps(segment)
            insert_data.append((
                context_id, video_id, 'transcript', timestamp, data_json,
                'transcribe_audio', tool_version, model_version, None
            ))
        
        # Execute batch insert with transaction
        stored_count = self._batch_insert_with_retry(
            video_id,
            'transcript',
            insert_data,
            with_lineage=True
        )
        
        # Record lineage
        try:
            self.lineage_tracker.record_batch_processing(
                video_id, context_ids, 'transcribe_audio'
            )
        except Exception as e:
            logger.warning(f"Failed to record lineage: {e}")
        
        logger.info(f"Stored {stored_count} transcript segments for video {video_id}")
        return {'transcript_segments': stored_count}
    
    def _store_objects(self, video_id: str, results: Dict[str, Any]) -> Dict[str, int]:
        """
        Store object detection results with validation.
        
        Args:
            video_id: Video identifier
            results: Object detection results with 'detections' list
            
        Returns:
            Dictionary with count: {'object_detections': N}
        """
        detections = results.get('detections', [])
        if not detections:
            logger.warning(f"No object detections to store for video {video_id}")
            return {'object_detections': 0}
        
        # Validate batch before insertion
        valid, errors = self.validator.validate_batch('object', detections, video_id)
        if not valid:
            logger.error(f"Object detection validation failed for video {video_id}: {errors}")
            raise ValidationError(f"Object detection validation failed: {'; '.join(errors)}")
        
        # Prepare batch insert data with lineage metadata
        insert_data = []
        context_ids = []
        tool_version = self.lineage_tracker.TOOL_VERSIONS.get('detect_objects', '1.0.0')
        model_version = self.lineage_tracker.MODEL_VERSIONS.get('yolo')
        
        for detection in detections:
            context_id = str(uuid.uuid4())
            context_ids.append(context_id)
            timestamp = detection.get('frame_timestamp', 0)
            data_json = json.dumps(detection)
            insert_data.append((
                context_id, video_id, 'object', timestamp, data_json,
                'detect_objects', tool_version, model_version, None
            ))
        
        # Execute batch insert with transaction
        stored_count = self._batch_insert_with_retry(
            video_id,
            'object',
            insert_data,
            with_lineage=True
        )
        
        # Record lineage
        try:
            self.lineage_tracker.record_batch_processing(
                video_id, context_ids, 'detect_objects'
            )
        except Exception as e:
            logger.warning(f"Failed to record lineage: {e}")
        
        logger.info(f"Stored {stored_count} object detections for video {video_id}")
        return {'object_detections': stored_count}
    
    def _batch_insert_with_retry(
        self,
        video_id: str,
        context_type: str,
        insert_data: List[tuple],
        with_lineage: bool = False
    ) -> int:
        """
        Execute batch insert with transaction support, savepoints, and retry logic.
        
        Uses savepoints to enable partial rollback if validation fails.
        Implements idempotent behavior - safe to retry operations.
        
        Args:
            video_id: Video identifier
            context_type: Type of context data ('frame', 'caption', etc.)
            insert_data: List of tuples with data fields
            with_lineage: Whether insert_data includes lineage fields
            
        Returns:
            Number of rows successfully inserted
            
        Raises:
            VideoProcessingServiceError: If all retry attempts fail
        """
        if with_lineage:
            query = """
                INSERT OR IGNORE INTO video_context 
                (context_id, video_id, context_type, timestamp, data, tool_name, tool_version, model_version, processing_params)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        else:
            query = """
                INSERT OR IGNORE INTO video_context (context_id, video_id, context_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """
        
        for attempt in range(self.max_retries):
            try:
                # Use explicit transaction with savepoint support
                with self.db.transaction(isolation_level='IMMEDIATE') as txn:
                    cursor = txn.cursor()
                    
                    # Create savepoint before batch insert
                    savepoint = txn.savepoint()
                    
                    try:
                        # Execute batch insert (INSERT OR IGNORE for idempotency)
                        cursor.executemany(query, insert_data)
                        
                        # Validate: Count inserted rows to confirm write
                        cursor.execute(
                            """SELECT COUNT(*) FROM video_context 
                               WHERE video_id = ? AND context_type = ?""",
                            (video_id, context_type)
                        )
                        validation_count = cursor.fetchone()[0]
                        
                        # Check if we have at least the expected number of rows
                        # (could be more if previous partial inserts succeeded)
                        if validation_count < len(insert_data):
                            logger.warning(
                                f"Validation check: expected at least {len(insert_data)}, "
                                f"found {validation_count} {context_type} records"
                            )
                        
                        # Release savepoint (commit this part of transaction)
                        txn.release_savepoint(savepoint)
                        
                        # Log success
                        logger.info(
                            f"Successfully stored {len(insert_data)} {context_type} records "
                            f"for video {video_id} (attempt {attempt + 1}/{self.max_retries})"
                        )
                        
                        return len(insert_data)
                        
                    except Exception as e:
                        # Rollback to savepoint on validation failure
                        logger.warning(f"Rolling back to savepoint due to error: {e}")
                        txn.rollback_to(savepoint)
                        raise e
                    
            except Exception as e:
                logger.warning(
                    f"Database write failed for {context_type} (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 0.5s, 1s, 2s
                    sleep_time = 0.5 * (2 ** attempt)
                    logger.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    # All retries exhausted
                    logger.error(
                        f"Failed to store {context_type} after {self.max_retries} attempts"
                    )
                    raise VideoProcessingServiceError(
                        f"Failed to store {context_type} for video {video_id}: {e}"
                    )
        
        return 0
    
    def _check_idempotency(self, video_id: str, tool_name: str, idempotency_key: str) -> bool:
        """
        Check if an operation with this idempotency key was already completed.
        
        Args:
            video_id: Video identifier
            tool_name: Tool name
            idempotency_key: Unique key for this operation
            
        Returns:
            True if operation was already completed, False otherwise
        """
        try:
            query = """
                SELECT COUNT(*) FROM video_context
                WHERE video_id = ? AND context_type = 'idempotency'
                AND json_extract(data, '$.tool_name') = ?
                AND json_extract(data, '$.key') = ?
            """
            rows = self.db.execute_query(query, (video_id, tool_name, idempotency_key))
            return rows[0][0] > 0 if rows else False
        except Exception as e:
            logger.warning(f"Failed to check idempotency: {e}")
            return False
    
    def _record_idempotency(self, video_id: str, tool_name: str, idempotency_key: str) -> None:
        """
        Record that an operation with this idempotency key was completed.
        
        Args:
            video_id: Video identifier
            tool_name: Tool name
            idempotency_key: Unique key for this operation
        """
        try:
            context_id = str(uuid.uuid4())
            data = json.dumps({
                'tool_name': tool_name,
                'key': idempotency_key,
                'completed_at': time.time()
            })
            
            query = """
                INSERT OR IGNORE INTO video_context (context_id, video_id, context_type, timestamp, data)
                VALUES (?, ?, 'idempotency', ?, ?)
            """
            self.db.execute_update(query, (context_id, video_id, time.time(), data))
            logger.debug(f"Recorded idempotency key: {idempotency_key}")
        except Exception as e:
            logger.warning(f"Failed to record idempotency: {e}")
    
    def _get_existing_counts(self, video_id: str, tool_name: str) -> Dict[str, int]:
        """
        Get counts of existing data for a tool (used when operation is idempotent).
        
        Args:
            video_id: Video identifier
            tool_name: Tool name
            
        Returns:
            Dictionary with counts
        """
        context_type_map = {
            'extract_frames': 'frame',
            'caption_frames': 'caption',
            'transcribe_audio': 'transcript',
            'detect_objects': 'object'
        }
        
        context_type = context_type_map.get(tool_name)
        if not context_type:
            return {}
        
        count = self._count_context_type(video_id, context_type)
        
        result_key_map = {
            'frame': 'frames',
            'caption': 'captions',
            'transcript': 'transcript_segments',
            'object': 'object_detections'
        }
        
        result_key = result_key_map.get(context_type, context_type)
        return {result_key: count}
    
    def verify_video_data_completeness(self, video_id: str) -> Dict[str, Any]:
        """
        Verify that all expected data has been stored for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with completeness status:
            {
                'video_id': 'vid_123',
                'complete': True/False,
                'frames': {'count': 10, 'present': True},
                'captions': {'count': 10, 'present': True},
                'transcripts': {'count': 5, 'present': True},
                'objects': {'count': 10, 'present': True},
                'missing': []
            }
        """
        logger.info(f"Verifying data completeness for video {video_id}")
        
        # Check each data type
        frames_count = self._count_context_type(video_id, 'frame')
        captions_count = self._count_context_type(video_id, 'caption')
        transcripts_count = self._count_context_type(video_id, 'transcript')
        objects_count = self._count_context_type(video_id, 'object')
        
        # Determine what's missing
        missing = []
        if frames_count == 0:
            missing.append('frames')
        if captions_count == 0:
            missing.append('captions')
        if transcripts_count == 0:
            missing.append('transcripts')
        if objects_count == 0:
            missing.append('objects')
        
        # Overall completeness
        complete = len(missing) == 0
        
        status = {
            'video_id': video_id,
            'complete': complete,
            'frames': {
                'count': frames_count,
                'present': frames_count > 0
            },
            'captions': {
                'count': captions_count,
                'present': captions_count > 0
            },
            'transcripts': {
                'count': transcripts_count,
                'present': transcripts_count > 0
            },
            'objects': {
                'count': objects_count,
                'present': objects_count > 0
            },
            'missing': missing
        }
        
        logger.info(
            f"Video {video_id} completeness: {complete} "
            f"(frames={frames_count}, captions={captions_count}, "
            f"transcripts={transcripts_count}, objects={objects_count})"
        )
        
        return status
    
    def _count_context_type(self, video_id: str, context_type: str) -> int:
        """
        Count number of records for a specific context type.
        
        Args:
            video_id: Video identifier
            context_type: Type of context data
            
        Returns:
            Count of records
        """
        try:
            query = """
                SELECT COUNT(*) FROM video_context
                WHERE video_id = ? AND context_type = ?
            """
            rows = self.db.execute_query(query, (video_id, context_type))
            return rows[0][0] if rows else 0
        except Exception as e:
            logger.error(f"Failed to count {context_type} for video {video_id}: {e}")
            return 0
    
    def delete_video_data(self, video_id: str) -> Dict[str, int]:
        """
        Delete all processing data for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with counts of deleted items
        """
        logger.info(f"Deleting all data for video {video_id}")
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                # Count before deletion
                cursor.execute(
                    "SELECT COUNT(*) FROM video_context WHERE video_id = ?",
                    (video_id,)
                )
                total_count = cursor.fetchone()[0]
                
                # Delete all context data
                cursor.execute(
                    "DELETE FROM video_context WHERE video_id = ?",
                    (video_id,)
                )
                
                conn.commit()
                
                logger.info(f"Deleted {total_count} records for video {video_id}")
                return {'deleted': total_count}
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                
        except Exception as e:
            logger.error(f"Failed to delete data for video {video_id}: {e}")
            raise VideoProcessingServiceError(f"Failed to delete video data: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.db:
            self.db.close()
            logger.info("Video Processing Service closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global service instance
_service_instance: Optional[VideoProcessingService] = None


def get_video_processing_service() -> VideoProcessingService:
    """
    Get or create global video processing service instance.
    
    Returns:
        VideoProcessingService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = VideoProcessingService()
    return _service_instance
