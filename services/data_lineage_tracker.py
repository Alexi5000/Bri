"""
Data Lineage Tracker for BRI Video Agent
Tracks which tool version generated each result and enables reproducibility
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from storage.database import Database
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DataLineageTracker:
    """
    Track data lineage for reproducibility and debugging.
    
    Features:
    - Track which tool version generated each result
    - Store processing metadata (model version, parameters)
    - Enable reproducibility of results
    - Audit trail for data modifications
    """
    
    # Tool versions (should be loaded from config or environment)
    TOOL_VERSIONS = {
        'extract_frames': '1.0.0',
        'caption_frames': '1.0.0',
        'transcribe_audio': '1.0.0',
        'detect_objects': '1.0.0'
    }
    
    # Model versions
    MODEL_VERSIONS = {
        'blip': 'Salesforce/blip-image-captioning-large',
        'whisper': 'base',
        'yolo': 'yolov8n'
    }
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize DataLineageTracker.
        
        Args:
            db: Database instance
        """
        self.db = db or Database()
        if not self.db._connection:
            self.db.connect()
        logger.info("DataLineageTracker initialized")
    
    def record_processing(
        self,
        video_id: str,
        context_id: str,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Record a data processing operation in the lineage table.
        
        Args:
            video_id: Video identifier
            context_id: Context record identifier
            tool_name: Name of tool that processed the data
            parameters: Processing parameters used
            user_id: Optional user identifier
            
        Returns:
            Lineage record ID
        """
        lineage_id = str(uuid.uuid4())
        tool_version = self.TOOL_VERSIONS.get(tool_name, 'unknown')
        model_version = self._get_model_version(tool_name)
        
        params_json = json.dumps(parameters) if parameters else None
        
        try:
            query = """
                INSERT INTO data_lineage (
                    lineage_id, video_id, context_id, operation,
                    tool_name, tool_version, model_version, parameters, user_id
                )
                VALUES (?, ?, ?, 'create', ?, ?, ?, ?, ?)
            """
            self.db.execute_update(
                query,
                (lineage_id, video_id, context_id, tool_name, tool_version, model_version, params_json, user_id)
            )
            
            logger.debug(f"Recorded lineage for {tool_name} on video {video_id}")
            return lineage_id
            
        except Exception as e:
            logger.error(f"Failed to record lineage: {e}")
            raise
    
    def record_batch_processing(
        self,
        video_id: str,
        context_ids: List[str],
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Record multiple processing operations in batch.
        
        Args:
            video_id: Video identifier
            context_ids: List of context record identifiers
            tool_name: Name of tool that processed the data
            parameters: Processing parameters used
            user_id: Optional user identifier
            
        Returns:
            List of lineage record IDs
        """
        lineage_ids = []
        tool_version = self.TOOL_VERSIONS.get(tool_name, 'unknown')
        model_version = self._get_model_version(tool_name)
        params_json = json.dumps(parameters) if parameters else None
        
        try:
            # Prepare batch insert
            insert_data = []
            for context_id in context_ids:
                lineage_id = str(uuid.uuid4())
                lineage_ids.append(lineage_id)
                insert_data.append((
                    lineage_id, video_id, context_id, 'create',
                    tool_name, tool_version, model_version, params_json, user_id
                ))
            
            query = """
                INSERT INTO data_lineage (
                    lineage_id, video_id, context_id, operation,
                    tool_name, tool_version, model_version, parameters, user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_many(query, insert_data)
            
            logger.info(f"Recorded {len(lineage_ids)} lineage records for {tool_name} on video {video_id}")
            return lineage_ids
            
        except Exception as e:
            logger.error(f"Failed to record batch lineage: {e}")
            raise
    
    def update_context_lineage(
        self,
        context_id: str,
        tool_name: str,
        tool_version: Optional[str] = None,
        model_version: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update lineage metadata in video_context table.
        
        Args:
            context_id: Context record identifier
            tool_name: Name of tool
            tool_version: Tool version (uses default if not provided)
            model_version: Model version (uses default if not provided)
            parameters: Processing parameters
        """
        tool_version = tool_version or self.TOOL_VERSIONS.get(tool_name, 'unknown')
        model_version = model_version or self._get_model_version(tool_name)
        params_json = json.dumps(parameters) if parameters else None
        
        try:
            query = """
                UPDATE video_context
                SET tool_name = ?, tool_version = ?, model_version = ?, processing_params = ?
                WHERE context_id = ?
            """
            self.db.execute_update(
                query,
                (tool_name, tool_version, model_version, params_json, context_id)
            )
            
            logger.debug(f"Updated lineage metadata for context {context_id}")
            
        except Exception as e:
            logger.error(f"Failed to update context lineage: {e}")
            raise
    
    def get_lineage_history(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get complete lineage history for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List of lineage records
        """
        try:
            query = """
                SELECT * FROM data_lineage
                WHERE video_id = ?
                ORDER BY timestamp DESC
            """
            rows = self.db.execute_query(query, (video_id,))
            
            lineage = []
            for row in rows:
                record = dict(row)
                # Parse parameters JSON
                if record.get('parameters'):
                    try:
                        record['parameters'] = json.loads(record['parameters'])
                    except json.JSONDecodeError:
                        pass
                lineage.append(record)
            
            return lineage
            
        except Exception as e:
            logger.error(f"Failed to get lineage history: {e}")
            return []
    
    def get_context_lineage(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get lineage information for a specific context record.
        
        Args:
            context_id: Context record identifier
            
        Returns:
            Lineage information dictionary or None
        """
        try:
            query = """
                SELECT tool_name, tool_version, model_version, processing_params, created_at
                FROM video_context
                WHERE context_id = ?
            """
            rows = self.db.execute_query(query, (context_id,))
            
            if not rows:
                return None
            
            row = rows[0]
            lineage = {
                'tool_name': row['tool_name'],
                'tool_version': row['tool_version'],
                'model_version': row['model_version'],
                'created_at': row['created_at']
            }
            
            # Parse parameters
            if row['processing_params']:
                try:
                    lineage['parameters'] = json.loads(row['processing_params'])
                except json.JSONDecodeError:
                    lineage['parameters'] = None
            
            return lineage
            
        except Exception as e:
            logger.error(f"Failed to get context lineage: {e}")
            return None
    
    def get_reproducibility_info(self, video_id: str) -> Dict[str, Any]:
        """
        Get all information needed to reproduce processing results.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with reproducibility information
        """
        try:
            # Get all unique tool/version combinations used
            query = """
                SELECT DISTINCT tool_name, tool_version, model_version, processing_params
                FROM video_context
                WHERE video_id = ? AND tool_name IS NOT NULL
            """
            rows = self.db.execute_query(query, (video_id,))
            
            tools_used = []
            for row in rows:
                tool_info = {
                    'tool_name': row['tool_name'],
                    'tool_version': row['tool_version'],
                    'model_version': row['model_version']
                }
                
                if row['processing_params']:
                    try:
                        tool_info['parameters'] = json.loads(row['processing_params'])
                    except json.JSONDecodeError:
                        pass
                
                tools_used.append(tool_info)
            
            # Get video metadata
            video_query = "SELECT * FROM videos WHERE video_id = ?"
            video_rows = self.db.execute_query(video_query, (video_id,))
            video_info = dict(video_rows[0]) if video_rows else {}
            
            return {
                'video_id': video_id,
                'video_info': video_info,
                'tools_used': tools_used,
                'reproducible': len(tools_used) > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get reproducibility info: {e}")
            return {
                'video_id': video_id,
                'reproducible': False,
                'error': str(e)
            }
    
    def record_reprocessing(
        self,
        video_id: str,
        tool_name: str,
        reason: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record a reprocessing operation.
        
        Args:
            video_id: Video identifier
            tool_name: Name of tool being rerun
            reason: Reason for reprocessing
            parameters: Processing parameters
            
        Returns:
            Lineage record ID
        """
        lineage_id = str(uuid.uuid4())
        tool_version = self.TOOL_VERSIONS.get(tool_name, 'unknown')
        model_version = self._get_model_version(tool_name)
        
        params = parameters or {}
        params['reprocess_reason'] = reason
        params_json = json.dumps(params)
        
        try:
            query = """
                INSERT INTO data_lineage (
                    lineage_id, video_id, context_id, operation,
                    tool_name, tool_version, model_version, parameters
                )
                VALUES (?, ?, NULL, 'reprocess', ?, ?, ?, ?)
            """
            self.db.execute_update(
                query,
                (lineage_id, video_id, tool_name, tool_version, model_version, params_json)
            )
            
            logger.info(f"Recorded reprocessing for {tool_name} on video {video_id}: {reason}")
            return lineage_id
            
        except Exception as e:
            logger.error(f"Failed to record reprocessing: {e}")
            raise
    
    def _get_model_version(self, tool_name: str) -> Optional[str]:
        """
        Get model version for a tool.
        
        Args:
            tool_name: Tool name
            
        Returns:
            Model version string or None
        """
        model_map = {
            'caption_frames': self.MODEL_VERSIONS.get('blip'),
            'transcribe_audio': self.MODEL_VERSIONS.get('whisper'),
            'detect_objects': self.MODEL_VERSIONS.get('yolo')
        }
        return model_map.get(tool_name)


# Global tracker instance
_tracker_instance: Optional[DataLineageTracker] = None


def get_lineage_tracker(db=None) -> DataLineageTracker:
    """
    Get or create global lineage tracker instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        DataLineageTracker instance
    """
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = DataLineageTracker(db)
    return _tracker_instance
