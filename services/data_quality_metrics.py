"""
Data Quality Metrics for BRI Video Agent
Tracks data completeness, freshness, accuracy, and volume
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from storage.database import Database
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DataQualityMetrics:
    """
    Track and monitor data quality metrics for video processing.
    
    Metrics tracked:
    - Data completeness per video (% of expected data)
    - Data freshness (time since last update)
    - Data accuracy (confidence scores)
    - Data volume (growth rate)
    - Quality degradation alerts
    """
    
    # Quality thresholds
    COMPLETENESS_THRESHOLD = 0.8  # 80% completeness required
    FRESHNESS_THRESHOLD_HOURS = 24  # Data should be < 24 hours old
    ACCURACY_THRESHOLD = 0.7  # 70% average confidence required
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize DataQualityMetrics.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("DataQualityMetrics initialized")
    
    def calculate_completeness(self, video_id: str) -> Dict[str, Any]:
        """
        Calculate data completeness for a video.
        
        Completeness is measured as the percentage of expected data that exists:
        - Frames: Expected based on video duration
        - Captions: Should match frame count
        - Transcript: Should exist for videos with audio
        - Objects: Should exist for all frames
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with completeness metrics:
            {
                'video_id': 'vid_123',
                'overall_completeness': 0.85,
                'frames_completeness': 1.0,
                'captions_completeness': 0.9,
                'transcript_completeness': 0.8,
                'objects_completeness': 0.7,
                'is_complete': True/False,
                'missing_data': ['objects']
            }
        """
        logger.debug(f"Calculating completeness for video {video_id}")
        
        try:
            # Get video metadata
            video_query = "SELECT duration FROM videos WHERE video_id = ?"
            video_rows = self.db.execute_query(video_query, (video_id,))
            
            if not video_rows:
                return {
                    'video_id': video_id,
                    'overall_completeness': 0.0,
                    'error': 'Video not found'
                }
            
            duration = video_rows[0]['duration']
            
            # Expected frame count (assuming 2-second intervals)
            expected_frames = max(1, int(duration / 2))
            
            # Get actual counts
            frame_count = self._get_context_count(video_id, 'frame')
            caption_count = self._get_context_count(video_id, 'caption')
            transcript_count = self._get_context_count(video_id, 'transcript')
            object_count = self._get_context_count(video_id, 'object')
            
            # Calculate completeness for each type
            frames_completeness = min(1.0, frame_count / expected_frames) if expected_frames > 0 else 0.0
            captions_completeness = min(1.0, caption_count / frame_count) if frame_count > 0 else 0.0
            transcript_completeness = 1.0 if transcript_count > 0 else 0.0
            objects_completeness = min(1.0, object_count / frame_count) if frame_count > 0 else 0.0
            
            # Overall completeness (weighted average)
            overall_completeness = (
                frames_completeness * 0.3 +
                captions_completeness * 0.3 +
                transcript_completeness * 0.2 +
                objects_completeness * 0.2
            )
            
            # Identify missing data
            missing_data = []
            if frames_completeness < 0.9:
                missing_data.append('frames')
            if captions_completeness < 0.9:
                missing_data.append('captions')
            if transcript_completeness < 0.5:
                missing_data.append('transcript')
            if objects_completeness < 0.9:
                missing_data.append('objects')
            
            is_complete = overall_completeness >= self.COMPLETENESS_THRESHOLD
            
            result = {
                'video_id': video_id,
                'overall_completeness': round(overall_completeness, 3),
                'frames_completeness': round(frames_completeness, 3),
                'captions_completeness': round(captions_completeness, 3),
                'transcript_completeness': round(transcript_completeness, 3),
                'objects_completeness': round(objects_completeness, 3),
                'is_complete': is_complete,
                'missing_data': missing_data,
                'counts': {
                    'expected_frames': expected_frames,
                    'actual_frames': frame_count,
                    'captions': caption_count,
                    'transcripts': transcript_count,
                    'objects': object_count
                }
            }
            
            logger.debug(f"Completeness for {video_id}: {overall_completeness:.1%}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate completeness: {e}")
            return {
                'video_id': video_id,
                'overall_completeness': 0.0,
                'error': str(e)
            }
    
    def calculate_freshness(self, video_id: str) -> Dict[str, Any]:
        """
        Calculate data freshness (time since last update).
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with freshness metrics:
            {
                'video_id': 'vid_123',
                'upload_time': '2024-01-01T12:00:00',
                'last_update_time': '2024-01-01T12:05:00',
                'age_hours': 2.5,
                'is_fresh': True/False,
                'staleness_warning': False
            }
        """
        logger.debug(f"Calculating freshness for video {video_id}")
        
        try:
            # Get video upload time
            video_query = "SELECT upload_timestamp FROM videos WHERE video_id = ?"
            video_rows = self.db.execute_query(video_query, (video_id,))
            
            if not video_rows:
                return {
                    'video_id': video_id,
                    'error': 'Video not found'
                }
            
            upload_time_str = video_rows[0]['upload_timestamp']
            upload_time = datetime.fromisoformat(upload_time_str)
            
            # Get last context update time
            context_query = """
                SELECT MAX(created_at) as last_update
                FROM video_context
                WHERE video_id = ?
            """
            context_rows = self.db.execute_query(context_query, (video_id,))
            
            last_update_str = context_rows[0]['last_update'] if context_rows and context_rows[0]['last_update'] else upload_time_str
            last_update_time = datetime.fromisoformat(last_update_str)
            
            # Calculate age
            now = datetime.now()
            age_delta = now - last_update_time
            age_hours = age_delta.total_seconds() / 3600
            
            is_fresh = age_hours < self.FRESHNESS_THRESHOLD_HOURS
            staleness_warning = age_hours > (self.FRESHNESS_THRESHOLD_HOURS * 2)
            
            result = {
                'video_id': video_id,
                'upload_time': upload_time_str,
                'last_update_time': last_update_str,
                'age_hours': round(age_hours, 2),
                'is_fresh': is_fresh,
                'staleness_warning': staleness_warning
            }
            
            if staleness_warning:
                logger.warning(f"Video {video_id} data is stale ({age_hours:.1f} hours old)")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate freshness: {e}")
            return {
                'video_id': video_id,
                'error': str(e)
            }
    
    def calculate_accuracy(self, video_id: str) -> Dict[str, Any]:
        """
        Calculate data accuracy based on confidence scores.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with accuracy metrics:
            {
                'video_id': 'vid_123',
                'overall_accuracy': 0.85,
                'caption_accuracy': 0.9,
                'transcript_accuracy': 0.85,
                'object_accuracy': 0.8,
                'is_accurate': True/False,
                'low_confidence_count': 5
            }
        """
        logger.debug(f"Calculating accuracy for video {video_id}")
        
        try:
            # Get caption confidence scores
            caption_confidences = self._get_confidence_scores(video_id, 'caption', 'confidence')
            caption_accuracy = sum(caption_confidences) / len(caption_confidences) if caption_confidences else 0.0
            
            # Get transcript confidence scores
            transcript_confidences = self._get_confidence_scores(video_id, 'transcript', 'confidence')
            transcript_accuracy = sum(transcript_confidences) / len(transcript_confidences) if transcript_confidences else 0.0
            
            # Get object detection confidence scores
            object_confidences = self._get_object_confidence_scores(video_id)
            object_accuracy = sum(object_confidences) / len(object_confidences) if object_confidences else 0.0
            
            # Overall accuracy (weighted average)
            weights = []
            scores = []
            
            if caption_confidences:
                weights.append(0.4)
                scores.append(caption_accuracy)
            if transcript_confidences:
                weights.append(0.3)
                scores.append(transcript_accuracy)
            if object_confidences:
                weights.append(0.3)
                scores.append(object_accuracy)
            
            if scores:
                total_weight = sum(weights)
                overall_accuracy = sum(s * w for s, w in zip(scores, weights)) / total_weight
            else:
                overall_accuracy = 0.0
            
            # Count low confidence items
            low_confidence_count = (
                sum(1 for c in caption_confidences if c < 0.5) +
                sum(1 for c in transcript_confidences if c < 0.5) +
                sum(1 for c in object_confidences if c < 0.5)
            )
            
            is_accurate = overall_accuracy >= self.ACCURACY_THRESHOLD
            
            result = {
                'video_id': video_id,
                'overall_accuracy': round(overall_accuracy, 3),
                'caption_accuracy': round(caption_accuracy, 3) if caption_confidences else None,
                'transcript_accuracy': round(transcript_accuracy, 3) if transcript_confidences else None,
                'object_accuracy': round(object_accuracy, 3) if object_confidences else None,
                'is_accurate': is_accurate,
                'low_confidence_count': low_confidence_count,
                'sample_counts': {
                    'captions': len(caption_confidences),
                    'transcripts': len(transcript_confidences),
                    'objects': len(object_confidences)
                }
            }
            
            logger.debug(f"Accuracy for {video_id}: {overall_accuracy:.1%}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate accuracy: {e}")
            return {
                'video_id': video_id,
                'overall_accuracy': 0.0,
                'error': str(e)
            }
    
    def calculate_volume_metrics(self) -> Dict[str, Any]:
        """
        Calculate data volume and growth rate metrics.
        
        Returns:
            Dictionary with volume metrics:
            {
                'total_videos': 100,
                'total_frames': 5000,
                'total_captions': 4800,
                'total_transcripts': 95,
                'total_objects': 4500,
                'growth_rate_videos_per_day': 5.2,
                'growth_rate_data_mb_per_day': 150.5,
                'storage_used_mb': 2500.0
            }
        """
        logger.debug("Calculating volume metrics")
        
        try:
            # Get total counts
            total_videos = self._get_total_count('videos')
            total_frames = self._get_total_context_count('frame')
            total_captions = self._get_total_context_count('caption')
            total_transcripts = self._get_total_context_count('transcript')
            total_objects = self._get_total_context_count('object')
            
            # Calculate growth rate (last 7 days)
            days = 7
            recent_videos_query = f"""
                SELECT COUNT(*) as count FROM videos
                WHERE upload_timestamp >= datetime('now', '-{days} days')
            """
            recent_videos_rows = self.db.execute_query(recent_videos_query)
            recent_videos = recent_videos_rows[0]['count'] if recent_videos_rows else 0
            
            growth_rate_videos_per_day = recent_videos / days if days > 0 else 0.0
            
            # Estimate storage (rough calculation)
            # Assume: 1 frame = 100KB, 1 caption = 1KB, 1 transcript = 5KB, 1 object = 2KB
            estimated_storage_mb = (
                (total_frames * 100 +
                 total_captions * 1 +
                 total_transcripts * 5 +
                 total_objects * 2) / 1024
            )
            
            growth_rate_data_mb_per_day = (estimated_storage_mb / total_videos) * growth_rate_videos_per_day if total_videos > 0 else 0.0
            
            result = {
                'total_videos': total_videos,
                'total_frames': total_frames,
                'total_captions': total_captions,
                'total_transcripts': total_transcripts,
                'total_objects': total_objects,
                'growth_rate_videos_per_day': round(growth_rate_videos_per_day, 2),
                'growth_rate_data_mb_per_day': round(growth_rate_data_mb_per_day, 2),
                'storage_used_mb': round(estimated_storage_mb, 2),
                'measurement_period_days': days
            }
            
            logger.info(f"Volume metrics: {total_videos} videos, {estimated_storage_mb:.1f} MB")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate volume metrics: {e}")
            return {'error': str(e)}
    
    def check_quality_degradation(self, video_id: str) -> Dict[str, Any]:
        """
        Check for quality degradation and generate alerts.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with degradation alerts:
            {
                'video_id': 'vid_123',
                'has_degradation': True/False,
                'alerts': [
                    {'severity': 'warning', 'message': 'Low completeness'},
                    {'severity': 'error', 'message': 'Stale data'}
                ],
                'recommendations': ['Re-process video', 'Check tool status']
            }
        """
        logger.debug(f"Checking quality degradation for video {video_id}")
        
        alerts = []
        recommendations = []
        
        try:
            # Check completeness
            completeness = self.calculate_completeness(video_id)
            if not completeness.get('is_complete', False):
                alerts.append({
                    'severity': 'warning',
                    'metric': 'completeness',
                    'message': f"Data completeness is {completeness.get('overall_completeness', 0):.1%} (threshold: {self.COMPLETENESS_THRESHOLD:.1%})"
                })
                recommendations.append(f"Process missing data: {', '.join(completeness.get('missing_data', []))}")
            
            # Check freshness
            freshness = self.calculate_freshness(video_id)
            if freshness.get('staleness_warning', False):
                alerts.append({
                    'severity': 'error',
                    'metric': 'freshness',
                    'message': f"Data is stale ({freshness.get('age_hours', 0):.1f} hours old)"
                })
                recommendations.append("Re-process video to refresh data")
            elif not freshness.get('is_fresh', True):
                alerts.append({
                    'severity': 'warning',
                    'metric': 'freshness',
                    'message': f"Data is aging ({freshness.get('age_hours', 0):.1f} hours old)"
                })
            
            # Check accuracy
            accuracy = self.calculate_accuracy(video_id)
            if not accuracy.get('is_accurate', False):
                alerts.append({
                    'severity': 'warning',
                    'metric': 'accuracy',
                    'message': f"Low accuracy ({accuracy.get('overall_accuracy', 0):.1%}), {accuracy.get('low_confidence_count', 0)} low-confidence items"
                })
                recommendations.append("Review low-confidence results manually")
            
            has_degradation = len(alerts) > 0
            
            result = {
                'video_id': video_id,
                'has_degradation': has_degradation,
                'alerts': alerts,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
            if has_degradation:
                logger.warning(f"Quality degradation detected for video {video_id}: {len(alerts)} alerts")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check quality degradation: {e}")
            return {
                'video_id': video_id,
                'has_degradation': False,
                'error': str(e)
            }
    
    def get_quality_report(self, video_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive quality report for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Complete quality report dictionary
        """
        logger.info(f"Generating quality report for video {video_id}")
        
        report = {
            'video_id': video_id,
            'timestamp': datetime.now().isoformat(),
            'completeness': self.calculate_completeness(video_id),
            'freshness': self.calculate_freshness(video_id),
            'accuracy': self.calculate_accuracy(video_id),
            'degradation': self.check_quality_degradation(video_id)
        }
        
        # Calculate overall quality score (0-100)
        score = 100
        
        if not report['completeness'].get('is_complete', False):
            score -= 30
        
        if not report['freshness'].get('is_fresh', True):
            score -= 20
        
        if not report['accuracy'].get('is_accurate', False):
            score -= 20
        
        if report['degradation'].get('has_degradation', False):
            score -= 10
        
        report['quality_score'] = max(0, score)
        report['quality_status'] = 'excellent' if score >= 90 else 'good' if score >= 70 else 'fair' if score >= 50 else 'poor'
        
        logger.info(f"Quality report for {video_id}: {report['quality_status']} ({score}/100)")
        return report
    
    def get_system_quality_report(self) -> Dict[str, Any]:
        """
        Generate system-wide quality report.
        
        Returns:
            System quality report dictionary
        """
        logger.info("Generating system-wide quality report")
        
        try:
            # Get all videos
            videos_query = "SELECT video_id FROM videos"
            video_rows = self.db.execute_query(videos_query)
            video_ids = [row['video_id'] for row in video_rows]
            
            # Calculate metrics for each video
            video_reports = []
            for video_id in video_ids[:100]:  # Limit to first 100 for performance
                completeness = self.calculate_completeness(video_id)
                video_reports.append({
                    'video_id': video_id,
                    'completeness': completeness.get('overall_completeness', 0),
                    'is_complete': completeness.get('is_complete', False)
                })
            
            # Aggregate metrics
            if video_reports:
                avg_completeness = sum(r['completeness'] for r in video_reports) / len(video_reports)
                complete_count = sum(1 for r in video_reports if r['is_complete'])
                complete_percentage = complete_count / len(video_reports)
            else:
                avg_completeness = 0.0
                complete_percentage = 0.0
            
            # Get volume metrics
            volume = self.calculate_volume_metrics()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_videos': len(video_ids),
                'videos_analyzed': len(video_reports),
                'average_completeness': round(avg_completeness, 3),
                'complete_videos_percentage': round(complete_percentage, 3),
                'volume_metrics': volume,
                'system_health': 'healthy' if complete_percentage >= 0.8 else 'degraded'
            }
            
            logger.info(f"System quality: {report['system_health']} ({complete_percentage:.1%} complete)")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate system quality report: {e}")
            return {'error': str(e)}
    
    # Helper methods
    
    def _get_context_count(self, video_id: str, context_type: str) -> int:
        """Get count of context records for a video."""
        query = """
            SELECT COUNT(*) as count FROM video_context
            WHERE video_id = ? AND context_type = ?
        """
        rows = self.db.execute_query(query, (video_id, context_type))
        return rows[0]['count'] if rows else 0
    
    def _get_total_count(self, table: str) -> int:
        """Get total count from a table."""
        query = f"SELECT COUNT(*) as count FROM {table}"
        rows = self.db.execute_query(query)
        return rows[0]['count'] if rows else 0
    
    def _get_total_context_count(self, context_type: str) -> int:
        """Get total count of context records by type."""
        query = """
            SELECT COUNT(*) as count FROM video_context
            WHERE context_type = ?
        """
        rows = self.db.execute_query(query, (context_type,))
        return rows[0]['count'] if rows else 0
    
    def _get_confidence_scores(self, video_id: str, context_type: str, field: str) -> List[float]:
        """Extract confidence scores from context data."""
        query = """
            SELECT data FROM video_context
            WHERE video_id = ? AND context_type = ?
        """
        rows = self.db.execute_query(query, (video_id, context_type))
        
        confidences = []
        for row in rows:
            try:
                data = json.loads(row['data'])
                if field in data and isinstance(data[field], (int, float)):
                    confidences.append(float(data[field]))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        
        return confidences
    
    def _get_object_confidence_scores(self, video_id: str) -> List[float]:
        """Extract object detection confidence scores."""
        query = """
            SELECT data FROM video_context
            WHERE video_id = ? AND context_type = 'object'
        """
        rows = self.db.execute_query(query, (video_id,))
        
        confidences = []
        for row in rows:
            try:
                data = json.loads(row['data'])
                objects = data.get('objects', [])
                for obj in objects:
                    if 'confidence' in obj and isinstance(obj['confidence'], (int, float)):
                        confidences.append(float(obj['confidence']))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        
        return confidences


# Global metrics instance
_metrics_instance: Optional[DataQualityMetrics] = None


def get_quality_metrics(db=None) -> DataQualityMetrics:
    """
    Get or create global quality metrics instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        DataQualityMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = DataQualityMetrics(db)
    return _metrics_instance
