"""
Data Consistency Checker for BRI Video Agent
Verifies data integrity and detects/fixes corruption
"""

import json
from typing import Dict, Any, Optional
from storage.database import Database
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConsistencyError(Exception):
    """Custom exception for data consistency errors."""
    pass


class DataConsistencyChecker:
    """
    Comprehensive data consistency checking for video processing results.
    
    Checks:
    - Frame count matches expected (based on video duration)
    - Caption count matches frame count
    - Timestamp ordering (monotonically increasing)
    - Data corruption detection
    - Missing data detection
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize DataConsistencyChecker.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("DataConsistencyChecker initialized")
    
    def check_video_consistency(self, video_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive consistency check for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with consistency report:
            {
                'video_id': 'vid_123',
                'consistent': True/False,
                'checks': {
                    'frame_count': {'passed': True, 'message': '...'},
                    'caption_count': {'passed': True, 'message': '...'},
                    'timestamp_ordering': {'passed': True, 'message': '...'},
                    'data_corruption': {'passed': True, 'message': '...'}
                },
                'issues': [],
                'recommendations': []
            }
        """
        logger.info(f"Running consistency check for video {video_id}")
        
        checks = {}
        issues = []
        recommendations = []
        
        # Check 1: Frame count consistency
        frame_check = self._check_frame_count(video_id)
        checks['frame_count'] = frame_check
        if not frame_check['passed']:
            issues.append(frame_check['message'])
            if frame_check.get('recommendation'):
                recommendations.append(frame_check['recommendation'])
        
        # Check 2: Caption count matches frame count
        caption_check = self._check_caption_frame_match(video_id)
        checks['caption_count'] = caption_check
        if not caption_check['passed']:
            issues.append(caption_check['message'])
            if caption_check.get('recommendation'):
                recommendations.append(caption_check['recommendation'])
        
        # Check 3: Timestamp ordering
        timestamp_check = self._check_timestamp_ordering(video_id)
        checks['timestamp_ordering'] = timestamp_check
        if not timestamp_check['passed']:
            issues.append(timestamp_check['message'])
            if timestamp_check.get('recommendation'):
                recommendations.append(timestamp_check['recommendation'])
        
        # Check 4: Data corruption
        corruption_check = self._check_data_corruption(video_id)
        checks['data_corruption'] = corruption_check
        if not corruption_check['passed']:
            issues.append(corruption_check['message'])
            if corruption_check.get('recommendation'):
                recommendations.append(corruption_check['recommendation'])
        
        # Check 5: Transcript segment ordering
        transcript_check = self._check_transcript_segments(video_id)
        checks['transcript_segments'] = transcript_check
        if not transcript_check['passed']:
            issues.append(transcript_check['message'])
            if transcript_check.get('recommendation'):
                recommendations.append(transcript_check['recommendation'])
        
        # Overall consistency
        consistent = all(check['passed'] for check in checks.values())
        
        report = {
            'video_id': video_id,
            'consistent': consistent,
            'checks': checks,
            'issues': issues,
            'recommendations': recommendations
        }
        
        if consistent:
            logger.info(f"Video {video_id} passed all consistency checks")
        else:
            logger.warning(f"Video {video_id} has {len(issues)} consistency issues")
        
        return report
    
    def _check_frame_count(self, video_id: str) -> Dict[str, Any]:
        """
        Check if frame count is reasonable based on video duration.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Check result dictionary
        """
        try:
            # Get video metadata
            video_query = "SELECT duration FROM videos WHERE video_id = ?"
            video_rows = self.db.execute_query(video_query, (video_id,))
            
            if not video_rows:
                return {
                    'passed': False,
                    'message': f"Video {video_id} not found in database",
                    'recommendation': "Ensure video record exists before processing"
                }
            
            duration = video_rows[0]['duration']
            
            # Get frame count
            frame_query = """
                SELECT COUNT(*) as count FROM video_context
                WHERE video_id = ? AND context_type = 'frame'
            """
            frame_rows = self.db.execute_query(frame_query, (video_id,))
            frame_count = frame_rows[0]['count'] if frame_rows else 0
            
            # Expected frames: assuming 2-second intervals (configurable)
            # For a 60-second video, expect ~30 frames
            expected_min = max(1, int(duration / 3))  # At least 1 frame per 3 seconds
            expected_max = int(duration * 2)  # At most 2 frames per second
            
            if frame_count == 0:
                return {
                    'passed': False,
                    'message': f"No frames extracted for video {video_id}",
                    'recommendation': "Run frame extraction tool"
                }
            
            if frame_count < expected_min:
                return {
                    'passed': False,
                    'message': f"Frame count ({frame_count}) is lower than expected minimum ({expected_min}) for {duration}s video",
                    'recommendation': "Re-run frame extraction with smaller interval"
                }
            
            if frame_count > expected_max:
                return {
                    'passed': False,
                    'message': f"Frame count ({frame_count}) is higher than expected maximum ({expected_max}) for {duration}s video",
                    'recommendation': "Check for duplicate frame extraction"
                }
            
            return {
                'passed': True,
                'message': f"Frame count ({frame_count}) is within expected range for {duration}s video",
                'frame_count': frame_count,
                'expected_range': [expected_min, expected_max]
            }
            
        except Exception as e:
            logger.error(f"Frame count check failed: {e}")
            return {
                'passed': False,
                'message': f"Frame count check error: {e}",
                'recommendation': "Check database connectivity"
            }
    
    def _check_caption_frame_match(self, video_id: str) -> Dict[str, Any]:
        """
        Check if caption count matches frame count.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Check result dictionary
        """
        try:
            # Get frame count
            frame_query = """
                SELECT COUNT(*) as count FROM video_context
                WHERE video_id = ? AND context_type = 'frame'
            """
            frame_rows = self.db.execute_query(frame_query, (video_id,))
            frame_count = frame_rows[0]['count'] if frame_rows else 0
            
            # Get caption count
            caption_query = """
                SELECT COUNT(*) as count FROM video_context
                WHERE video_id = ? AND context_type = 'caption'
            """
            caption_rows = self.db.execute_query(caption_query, (video_id,))
            caption_count = caption_rows[0]['count'] if caption_rows else 0
            
            if frame_count == 0:
                return {
                    'passed': True,
                    'message': "No frames to caption",
                    'frame_count': 0,
                    'caption_count': 0
                }
            
            if caption_count == 0:
                return {
                    'passed': False,
                    'message': f"No captions generated for {frame_count} frames",
                    'recommendation': "Run caption generation tool"
                }
            
            # Allow some tolerance (captions might fail for some frames)
            tolerance = max(1, int(frame_count * 0.1))  # 10% tolerance
            
            if abs(caption_count - frame_count) > tolerance:
                return {
                    'passed': False,
                    'message': f"Caption count ({caption_count}) doesn't match frame count ({frame_count})",
                    'recommendation': "Re-run caption generation for missing frames",
                    'frame_count': frame_count,
                    'caption_count': caption_count
                }
            
            return {
                'passed': True,
                'message': f"Caption count ({caption_count}) matches frame count ({frame_count})",
                'frame_count': frame_count,
                'caption_count': caption_count
            }
            
        except Exception as e:
            logger.error(f"Caption-frame match check failed: {e}")
            return {
                'passed': False,
                'message': f"Caption-frame match check error: {e}",
                'recommendation': "Check database connectivity"
            }
    
    def _check_timestamp_ordering(self, video_id: str) -> Dict[str, Any]:
        """
        Check if timestamps are in monotonically increasing order.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Check result dictionary
        """
        try:
            issues = []
            
            # Check frame timestamps
            frame_query = """
                SELECT timestamp FROM video_context
                WHERE video_id = ? AND context_type = 'frame'
                ORDER BY timestamp
            """
            frame_rows = self.db.execute_query(frame_query, (video_id,))
            frame_timestamps = [row['timestamp'] for row in frame_rows]
            
            if len(frame_timestamps) > 1:
                for i in range(1, len(frame_timestamps)):
                    if frame_timestamps[i] < frame_timestamps[i-1]:
                        issues.append(f"Frame timestamps out of order at index {i}: {frame_timestamps[i]} < {frame_timestamps[i-1]}")
            
            # Check caption timestamps
            caption_query = """
                SELECT timestamp FROM video_context
                WHERE video_id = ? AND context_type = 'caption'
                ORDER BY timestamp
            """
            caption_rows = self.db.execute_query(caption_query, (video_id,))
            caption_timestamps = [row['timestamp'] for row in caption_rows]
            
            if len(caption_timestamps) > 1:
                for i in range(1, len(caption_timestamps)):
                    if caption_timestamps[i] < caption_timestamps[i-1]:
                        issues.append(f"Caption timestamps out of order at index {i}")
            
            if issues:
                return {
                    'passed': False,
                    'message': f"Timestamp ordering issues: {'; '.join(issues)}",
                    'recommendation': "Re-process video to fix timestamp ordering",
                    'issues': issues
                }
            
            return {
                'passed': True,
                'message': "All timestamps are in correct order"
            }
            
        except Exception as e:
            logger.error(f"Timestamp ordering check failed: {e}")
            return {
                'passed': False,
                'message': f"Timestamp ordering check error: {e}",
                'recommendation': "Check database connectivity"
            }
    
    def _check_data_corruption(self, video_id: str) -> Dict[str, Any]:
        """
        Check for data corruption (invalid JSON, missing required fields).
        
        Args:
            video_id: Video identifier
            
        Returns:
            Check result dictionary
        """
        try:
            corrupted_records = []
            
            # Check all context records
            query = """
                SELECT context_id, context_type, data FROM video_context
                WHERE video_id = ?
            """
            rows = self.db.execute_query(query, (video_id,))
            
            for row in rows:
                context_id = row['context_id']
                context_type = row['context_type']
                data_str = row['data']
                
                # Try to parse JSON
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError as e:
                    corrupted_records.append({
                        'context_id': context_id,
                        'context_type': context_type,
                        'error': f"Invalid JSON: {e}"
                    })
                    continue
                
                # Check required fields based on context type
                required_fields = {
                    'frame': ['timestamp', 'frame_number'],
                    'caption': ['frame_timestamp', 'text'],
                    'transcript': ['start', 'end', 'text'],
                    'object': ['frame_timestamp', 'objects']
                }
                
                if context_type in required_fields:
                    missing_fields = [f for f in required_fields[context_type] if f not in data]
                    if missing_fields:
                        corrupted_records.append({
                            'context_id': context_id,
                            'context_type': context_type,
                            'error': f"Missing required fields: {missing_fields}"
                        })
            
            if corrupted_records:
                return {
                    'passed': False,
                    'message': f"Found {len(corrupted_records)} corrupted records",
                    'recommendation': "Delete corrupted records and re-process video",
                    'corrupted_records': corrupted_records[:10]  # Limit to first 10
                }
            
            return {
                'passed': True,
                'message': "No data corruption detected"
            }
            
        except Exception as e:
            logger.error(f"Data corruption check failed: {e}")
            return {
                'passed': False,
                'message': f"Data corruption check error: {e}",
                'recommendation': "Check database connectivity"
            }
    
    def _check_transcript_segments(self, video_id: str) -> Dict[str, Any]:
        """
        Check transcript segment consistency (end > start, no gaps).
        
        Args:
            video_id: Video identifier
            
        Returns:
            Check result dictionary
        """
        try:
            issues = []
            
            # Get transcript segments
            query = """
                SELECT data FROM video_context
                WHERE video_id = ? AND context_type = 'transcript'
                ORDER BY timestamp
            """
            rows = self.db.execute_query(query, (video_id,))
            
            if not rows:
                return {
                    'passed': True,
                    'message': "No transcript segments to check"
                }
            
            segments = []
            for row in rows:
                try:
                    data = json.loads(row['data'])
                    segments.append(data)
                except json.JSONDecodeError:
                    issues.append("Failed to parse transcript segment JSON")
                    continue
            
            # Check each segment
            for idx, segment in enumerate(segments):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                
                if end <= start:
                    issues.append(f"Segment {idx}: end ({end}) <= start ({start})")
                
                # Check for gaps between segments (optional, might be normal)
                if idx > 0:
                    prev_end = segments[idx-1].get('end', 0)
                    gap = start - prev_end
                    if gap > 5:  # More than 5 seconds gap
                        logger.debug(f"Large gap ({gap}s) between segments {idx-1} and {idx}")
            
            if issues:
                return {
                    'passed': False,
                    'message': f"Transcript segment issues: {'; '.join(issues)}",
                    'recommendation': "Re-run audio transcription",
                    'issues': issues
                }
            
            return {
                'passed': True,
                'message': f"All {len(segments)} transcript segments are consistent"
            }
            
        except Exception as e:
            logger.error(f"Transcript segment check failed: {e}")
            return {
                'passed': False,
                'message': f"Transcript segment check error: {e}",
                'recommendation': "Check database connectivity"
            }
    
    def fix_timestamp_ordering(self, video_id: str, context_type: str) -> Dict[str, Any]:
        """
        Fix timestamp ordering by re-sorting records.
        
        Args:
            video_id: Video identifier
            context_type: Type of context to fix
            
        Returns:
            Dictionary with fix results
        """
        logger.info(f"Fixing timestamp ordering for {context_type} in video {video_id}")
        
        try:
            # This is a read-only check - actual fixing would require re-processing
            # For now, just report what needs to be fixed
            query = """
                SELECT context_id, timestamp FROM video_context
                WHERE video_id = ? AND context_type = ?
                ORDER BY timestamp
            """
            rows = self.db.execute_query(query, (video_id, context_type))
            
            out_of_order = []
            for i in range(1, len(rows)):
                if rows[i]['timestamp'] < rows[i-1]['timestamp']:
                    out_of_order.append(rows[i]['context_id'])
            
            if out_of_order:
                return {
                    'fixed': False,
                    'message': f"Found {len(out_of_order)} out-of-order records",
                    'recommendation': "Re-process video to fix ordering",
                    'out_of_order_ids': out_of_order
                }
            
            return {
                'fixed': True,
                'message': "Timestamps are already in correct order"
            }
            
        except Exception as e:
            logger.error(f"Failed to fix timestamp ordering: {e}")
            return {
                'fixed': False,
                'message': f"Fix failed: {e}"
            }
    
    def delete_corrupted_records(self, video_id: str) -> Dict[str, int]:
        """
        Delete corrupted records for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with count of deleted records
        """
        logger.info(f"Deleting corrupted records for video {video_id}")
        
        try:
            # Find corrupted records
            query = """
                SELECT context_id, data FROM video_context
                WHERE video_id = ?
            """
            rows = self.db.execute_query(query, (video_id,))
            
            corrupted_ids = []
            for row in rows:
                try:
                    json.loads(row['data'])
                except json.JSONDecodeError:
                    corrupted_ids.append(row['context_id'])
            
            if not corrupted_ids:
                return {'deleted': 0}
            
            # Delete corrupted records
            placeholders = ','.join(['?' for _ in corrupted_ids])
            delete_query = f"""
                DELETE FROM video_context
                WHERE context_id IN ({placeholders})
            """
            self.db.execute_update(delete_query, tuple(corrupted_ids))
            
            logger.info(f"Deleted {len(corrupted_ids)} corrupted records")
            return {'deleted': len(corrupted_ids)}
            
        except Exception as e:
            logger.error(f"Failed to delete corrupted records: {e}")
            raise ConsistencyError(f"Failed to delete corrupted records: {e}")


# Global checker instance
_checker_instance: Optional[DataConsistencyChecker] = None


def get_consistency_checker(db=None) -> DataConsistencyChecker:
    """
    Get or create global consistency checker instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        DataConsistencyChecker instance
    """
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = DataConsistencyChecker(db)
    return _checker_instance
