"""
Data Observability for BRI Video Agent
Logs all data mutations, tracks lineage, monitors pipeline latency, and visualizes data flow
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import contextmanager
from storage.database import Database
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DataMutationLogger:
    """
    Log all data mutations (insert/update/delete) for audit trail.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize DataMutationLogger.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("DataMutationLogger initialized")
    
    def log_insert(
        self,
        table: str,
        record_id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """
        Log an insert operation.
        
        Args:
            table: Table name
            record_id: Record identifier
            data: Data being inserted
            user_id: Optional user identifier
        """
        try:
            mutation_data = {
                'operation': 'insert',
                'table': table,
                'record_id': record_id,
                'data': data,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"DATA_MUTATION: INSERT {table} {record_id}", extra=mutation_data)
            
            # Store in audit log table if it exists
            self._store_audit_log(mutation_data)
            
        except Exception as e:
            logger.error(f"Failed to log insert: {e}")
    
    def log_update(
        self,
        table: str,
        record_id: str,
        old_data: Optional[Dict[str, Any]],
        new_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """
        Log an update operation.
        
        Args:
            table: Table name
            record_id: Record identifier
            old_data: Previous data state
            new_data: New data state
            user_id: Optional user identifier
        """
        try:
            mutation_data = {
                'operation': 'update',
                'table': table,
                'record_id': record_id,
                'old_data': old_data,
                'new_data': new_data,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"DATA_MUTATION: UPDATE {table} {record_id}", extra=mutation_data)
            
            # Store in audit log table if it exists
            self._store_audit_log(mutation_data)
            
        except Exception as e:
            logger.error(f"Failed to log update: {e}")
    
    def log_delete(
        self,
        table: str,
        record_id: str,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Log a delete operation.
        
        Args:
            table: Table name
            record_id: Record identifier
            data: Data being deleted
            user_id: Optional user identifier
        """
        try:
            mutation_data = {
                'operation': 'delete',
                'table': table,
                'record_id': record_id,
                'data': data,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"DATA_MUTATION: DELETE {table} {record_id}", extra=mutation_data)
            
            # Store in audit log table if it exists
            self._store_audit_log(mutation_data)
            
        except Exception as e:
            logger.error(f"Failed to log delete: {e}")
    
    def _store_audit_log(self, mutation_data: Dict[str, Any]) -> None:
        """Store mutation in audit log table."""
        try:
            # Check if audit_log table exists
            check_query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='audit_log'
            """
            rows = self.db.execute_query(check_query)
            
            if not rows:
                # Create audit_log table
                create_query = """
                    CREATE TABLE IF NOT EXISTS audit_log (
                        log_id TEXT PRIMARY KEY,
                        operation TEXT NOT NULL,
                        table_name TEXT NOT NULL,
                        record_id TEXT NOT NULL,
                        data TEXT,
                        user_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                self.db.execute_update(create_query)
                logger.info("Created audit_log table")
            
            # Insert audit log
            import uuid
            log_id = str(uuid.uuid4())
            data_json = json.dumps(mutation_data)
            
            insert_query = """
                INSERT INTO audit_log (log_id, operation, table_name, record_id, data, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute_update(
                insert_query,
                (log_id, mutation_data['operation'], mutation_data['table'],
                 mutation_data['record_id'], data_json, mutation_data.get('user_id'))
            )
            
        except Exception as e:
            logger.debug(f"Could not store audit log: {e}")
    
    def get_mutation_history(
        self,
        table: Optional[str] = None,
        record_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get mutation history.
        
        Args:
            table: Optional table filter
            record_id: Optional record ID filter
            limit: Maximum number of records
            
        Returns:
            List of mutation records
        """
        try:
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            
            if table:
                query += " AND table_name = ?"
                params.append(table)
            
            if record_id:
                query += " AND record_id = ?"
                params.append(record_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            rows = self.db.execute_query(query, tuple(params))
            
            history = []
            for row in rows:
                record = dict(row)
                if record.get('data'):
                    try:
                        record['data'] = json.loads(record['data'])
                    except json.JSONDecodeError:
                        pass
                history.append(record)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get mutation history: {e}")
            return []


class PipelineLatencyMonitor:
    """
    Monitor data pipeline latency and performance.
    """
    
    def __init__(self):
        """Initialize PipelineLatencyMonitor."""
        self.stage_timings: Dict[str, List[float]] = {}
        logger.info("PipelineLatencyMonitor initialized")
    
    @contextmanager
    def monitor_stage(self, stage_name: str, video_id: str):
        """
        Context manager to monitor a pipeline stage.
        
        Args:
            stage_name: Name of the pipeline stage
            video_id: Video identifier
            
        Yields:
            None
            
        Example:
            with monitor.monitor_stage('frame_extraction', video_id):
                extract_frames(video_id)
        """
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            # Store timing
            if stage_name not in self.stage_timings:
                self.stage_timings[stage_name] = []
            self.stage_timings[stage_name].append(duration)
            
            # Log timing
            logger.info(
                f"PIPELINE_LATENCY: {stage_name} completed in {duration:.2f}s for video {video_id}",
                extra={
                    'stage': stage_name,
                    'video_id': video_id,
                    'duration_seconds': duration
                }
            )
    
    def get_stage_statistics(self, stage_name: str) -> Dict[str, float]:
        """
        Get statistics for a pipeline stage.
        
        Args:
            stage_name: Name of the pipeline stage
            
        Returns:
            Dictionary with statistics (min, max, avg, p50, p95, p99)
        """
        timings = self.stage_timings.get(stage_name, [])
        
        if not timings:
            return {}
        
        sorted_timings = sorted(timings)
        count = len(sorted_timings)
        
        return {
            'count': count,
            'min': round(min(sorted_timings), 2),
            'max': round(max(sorted_timings), 2),
            'avg': round(sum(sorted_timings) / count, 2),
            'p50': round(sorted_timings[int(count * 0.5)], 2),
            'p95': round(sorted_timings[int(count * 0.95)], 2) if count > 20 else None,
            'p99': round(sorted_timings[int(count * 0.99)], 2) if count > 100 else None
        }
    
    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all pipeline stages.
        
        Returns:
            Dictionary mapping stage names to statistics
        """
        return {
            stage: self.get_stage_statistics(stage)
            for stage in self.stage_timings.keys()
        }
    
    def reset_statistics(self) -> None:
        """Reset all timing statistics."""
        self.stage_timings.clear()
        logger.info("Pipeline latency statistics reset")


class DataFlowVisualizer:
    """
    Visualize data flow through the system.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize DataFlowVisualizer.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("DataFlowVisualizer initialized")
    
    def get_video_data_flow(self, video_id: str) -> Dict[str, Any]:
        """
        Get data flow for a specific video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary describing data flow:
            {
                'video_id': 'vid_123',
                'stages': [
                    {
                        'stage': 'upload',
                        'timestamp': '2024-01-01T12:00:00',
                        'status': 'complete'
                    },
                    {
                        'stage': 'frame_extraction',
                        'timestamp': '2024-01-01T12:00:05',
                        'status': 'complete',
                        'output_count': 30
                    },
                    ...
                ],
                'current_stage': 'complete',
                'completion_percentage': 100
            }
        """
        try:
            # Get video info
            video_query = "SELECT * FROM videos WHERE video_id = ?"
            video_rows = self.db.execute_query(video_query, (video_id,))
            
            if not video_rows:
                return {'video_id': video_id, 'error': 'Video not found'}
            
            video = dict(video_rows[0])
            
            # Get context counts
            frame_count = self._get_context_count(video_id, 'frame')
            caption_count = self._get_context_count(video_id, 'caption')
            transcript_count = self._get_context_count(video_id, 'transcript')
            object_count = self._get_context_count(video_id, 'object')
            
            # Build stages
            stages = [
                {
                    'stage': 'upload',
                    'timestamp': video['upload_timestamp'],
                    'status': 'complete'
                }
            ]
            
            if frame_count > 0:
                stages.append({
                    'stage': 'frame_extraction',
                    'timestamp': self._get_earliest_context_time(video_id, 'frame'),
                    'status': 'complete',
                    'output_count': frame_count
                })
            
            if caption_count > 0:
                stages.append({
                    'stage': 'caption_generation',
                    'timestamp': self._get_earliest_context_time(video_id, 'caption'),
                    'status': 'complete',
                    'output_count': caption_count
                })
            
            if transcript_count > 0:
                stages.append({
                    'stage': 'audio_transcription',
                    'timestamp': self._get_earliest_context_time(video_id, 'transcript'),
                    'status': 'complete',
                    'output_count': transcript_count
                })
            
            if object_count > 0:
                stages.append({
                    'stage': 'object_detection',
                    'timestamp': self._get_earliest_context_time(video_id, 'object'),
                    'status': 'complete',
                    'output_count': object_count
                })
            
            # Determine current stage and completion
            processing_status = video.get('processing_status', 'pending')
            
            if processing_status == 'complete':
                current_stage = 'complete'
                completion_percentage = 100
            elif processing_status == 'processing':
                current_stage = stages[-1]['stage'] if stages else 'upload'
                completion_percentage = (len(stages) / 5) * 100  # 5 total stages
            else:
                current_stage = 'pending'
                completion_percentage = 0
            
            return {
                'video_id': video_id,
                'stages': stages,
                'current_stage': current_stage,
                'completion_percentage': round(completion_percentage, 1),
                'processing_status': processing_status
            }
            
        except Exception as e:
            logger.error(f"Failed to get video data flow: {e}")
            return {'video_id': video_id, 'error': str(e)}
    
    def get_system_data_flow(self) -> Dict[str, Any]:
        """
        Get system-wide data flow statistics.
        
        Returns:
            Dictionary with system data flow metrics
        """
        try:
            # Get video counts by status
            status_query = """
                SELECT processing_status, COUNT(*) as count
                FROM videos
                GROUP BY processing_status
            """
            status_rows = self.db.execute_query(status_query)
            
            status_counts = {row['processing_status']: row['count'] for row in status_rows}
            
            # Get recent activity (last 24 hours)
            recent_query = """
                SELECT COUNT(*) as count FROM videos
                WHERE upload_timestamp >= datetime('now', '-1 day')
            """
            recent_rows = self.db.execute_query(recent_query)
            recent_uploads = recent_rows[0]['count'] if recent_rows else 0
            
            # Get processing throughput
            completed_query = """
                SELECT COUNT(*) as count FROM videos
                WHERE processing_status = 'complete'
                AND upload_timestamp >= datetime('now', '-1 day')
            """
            completed_rows = self.db.execute_query(completed_query)
            recent_completed = completed_rows[0]['count'] if completed_rows else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'status_distribution': status_counts,
                'recent_uploads_24h': recent_uploads,
                'recent_completed_24h': recent_completed,
                'processing_throughput': recent_completed / 24 if recent_completed > 0 else 0,  # per hour
                'pending_count': status_counts.get('pending', 0),
                'processing_count': status_counts.get('processing', 0),
                'complete_count': status_counts.get('complete', 0),
                'error_count': status_counts.get('error', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get system data flow: {e}")
            return {'error': str(e)}
    
    def visualize_lineage(self, video_id: str) -> str:
        """
        Generate a text-based visualization of data lineage.
        
        Args:
            video_id: Video identifier
            
        Returns:
            ASCII art visualization of data lineage
        """
        flow = self.get_video_data_flow(video_id)
        
        if 'error' in flow:
            return f"Error: {flow['error']}"
        
        lines = [
            f"Data Flow for Video: {video_id}",
            f"Status: {flow['processing_status']} ({flow['completion_percentage']}% complete)",
            "",
            "Pipeline Stages:",
            ""
        ]
        
        for i, stage in enumerate(flow['stages']):
            stage_name = stage['stage'].replace('_', ' ').title()
            timestamp = stage['timestamp']
            output = f" → {stage['output_count']} items" if 'output_count' in stage else ""
            
            lines.append(f"  {i+1}. {stage_name}")
            lines.append(f"     Time: {timestamp}")
            lines.append(f"     Status: {stage['status']}{output}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_context_count(self, video_id: str, context_type: str) -> int:
        """Get count of context records."""
        query = """
            SELECT COUNT(*) as count FROM video_context
            WHERE video_id = ? AND context_type = ?
        """
        rows = self.db.execute_query(query, (video_id, context_type))
        return rows[0]['count'] if rows else 0
    
    def _get_earliest_context_time(self, video_id: str, context_type: str) -> Optional[str]:
        """Get earliest timestamp for a context type."""
        query = """
            SELECT MIN(created_at) as earliest FROM video_context
            WHERE video_id = ? AND context_type = ?
        """
        rows = self.db.execute_query(query, (video_id, context_type))
        return rows[0]['earliest'] if rows and rows[0]['earliest'] else None


class DataObservability:
    """
    Unified data observability interface.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize DataObservability.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        
        self.mutation_logger = DataMutationLogger(self.db)
        self.latency_monitor = PipelineLatencyMonitor()
        self.flow_visualizer = DataFlowVisualizer(self.db)
        
        logger.info("DataObservability initialized")
    
    def get_observability_dashboard(self, video_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive observability dashboard.
        
        Args:
            video_id: Optional video ID for video-specific dashboard
            
        Returns:
            Dashboard data dictionary
        """
        if video_id:
            return {
                'video_id': video_id,
                'data_flow': self.flow_visualizer.get_video_data_flow(video_id),
                'mutation_history': self.mutation_logger.get_mutation_history(record_id=video_id, limit=50),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'system_flow': self.flow_visualizer.get_system_data_flow(),
                'pipeline_latency': self.latency_monitor.get_all_statistics(),
                'recent_mutations': self.mutation_logger.get_mutation_history(limit=100),
                'timestamp': datetime.now().isoformat()
            }


# Global observability instance
_observability_instance: Optional[DataObservability] = None


def get_data_observability(db=None) -> DataObservability:
    """
    Get or create global data observability instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        DataObservability instance
    """
    global _observability_instance
    if _observability_instance is None:
        _observability_instance = DataObservability(db)
    return _observability_instance
