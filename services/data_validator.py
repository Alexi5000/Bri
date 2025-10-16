"""
Data Validation Layer for BRI Video Agent
Validates all data before database insertion to ensure integrity
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class DataValidator:
    """
    Comprehensive data validation for video processing results.
    
    Validates:
    - JSON structure matches expected schema
    - Data types and ranges
    - Foreign key relationships
    - Required fields presence
    - Value constraints
    """
    
    # Schema definitions for each context type
    FRAME_SCHEMA = {
        'required_fields': ['timestamp', 'frame_number'],
        'optional_fields': ['image_path', 'image_base64', 'width', 'height'],
        'field_types': {
            'timestamp': (int, float),
            'frame_number': int,
            'image_path': str,
            'image_base64': str,
            'width': int,
            'height': int
        },
        'field_ranges': {
            'timestamp': (0, float('inf')),
            'frame_number': (0, float('inf')),
            'width': (1, 10000),
            'height': (1, 10000)
        }
    }
    
    CAPTION_SCHEMA = {
        'required_fields': ['frame_timestamp', 'text'],
        'optional_fields': ['confidence', 'model_version'],
        'field_types': {
            'frame_timestamp': (int, float),
            'text': str,
            'confidence': (int, float),
            'model_version': str
        },
        'field_ranges': {
            'frame_timestamp': (0, float('inf')),
            'confidence': (0, 1)
        }
    }
    
    TRANSCRIPT_SCHEMA = {
        'required_fields': ['start', 'end', 'text'],
        'optional_fields': ['confidence', 'language', 'model_version'],
        'field_types': {
            'start': (int, float),
            'end': (int, float),
            'text': str,
            'confidence': (int, float),
            'language': str,
            'model_version': str
        },
        'field_ranges': {
            'start': (0, float('inf')),
            'end': (0, float('inf')),
            'confidence': (0, 1)
        }
    }
    
    OBJECT_SCHEMA = {
        'required_fields': ['frame_timestamp', 'objects'],
        'optional_fields': ['model_version'],
        'field_types': {
            'frame_timestamp': (int, float),
            'objects': list,
            'model_version': str
        },
        'field_ranges': {
            'frame_timestamp': (0, float('inf'))
        }
    }
    
    OBJECT_DETECTION_SCHEMA = {
        'required_fields': ['class_name', 'confidence'],
        'optional_fields': ['bbox', 'track_id'],
        'field_types': {
            'class_name': str,
            'confidence': (int, float),
            'bbox': (list, tuple),
            'track_id': int
        },
        'field_ranges': {
            'confidence': (0, 1)
        }
    }
    
    def __init__(self, db=None):
        """
        Initialize DataValidator.
        
        Args:
            db: Optional database instance for foreign key validation
        """
        self.db = db
        logger.info("DataValidator initialized")
    
    def validate_frame(self, frame_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate frame data structure.
        
        Args:
            frame_data: Frame data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self._validate_against_schema(frame_data, self.FRAME_SCHEMA, 'frame')
    
    def validate_caption(self, caption_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate caption data structure.
        
        Args:
            caption_data: Caption data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error = self._validate_against_schema(caption_data, self.CAPTION_SCHEMA, 'caption')
        
        # Additional validation: text should not be empty
        if is_valid and not caption_data.get('text', '').strip():
            return False, "Caption text cannot be empty"
        
        return is_valid, error
    
    def validate_transcript(self, transcript_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate transcript segment data structure.
        
        Args:
            transcript_data: Transcript segment data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error = self._validate_against_schema(
            transcript_data, self.TRANSCRIPT_SCHEMA, 'transcript'
        )
        
        if not is_valid:
            return is_valid, error
        
        # Additional validation: end time must be after start time
        start = transcript_data.get('start', 0)
        end = transcript_data.get('end', 0)
        if end <= start:
            return False, f"Transcript end time ({end}) must be after start time ({start})"
        
        # Text should not be empty
        if not transcript_data.get('text', '').strip():
            return False, "Transcript text cannot be empty"
        
        return True, None
    
    def validate_object_detection(self, detection_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate object detection data structure.
        
        Args:
            detection_data: Object detection data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error = self._validate_against_schema(
            detection_data, self.OBJECT_SCHEMA, 'object_detection'
        )
        
        if not is_valid:
            return is_valid, error
        
        # Validate each object in the objects list
        objects = detection_data.get('objects', [])
        if not isinstance(objects, list):
            return False, "Objects field must be a list"
        
        for idx, obj in enumerate(objects):
            obj_valid, obj_error = self._validate_against_schema(
                obj, self.OBJECT_DETECTION_SCHEMA, f'object[{idx}]'
            )
            if not obj_valid:
                return False, f"Object {idx}: {obj_error}"
            
            # Validate bbox if present
            if 'bbox' in obj:
                bbox = obj['bbox']
                if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                    return False, f"Object {idx}: bbox must be a list/tuple of 4 numbers [x, y, w, h]"
                if not all(isinstance(v, (int, float)) and v >= 0 for v in bbox):
                    return False, f"Object {idx}: bbox values must be non-negative numbers"
        
        return True, None
    
    def validate_video_id_exists(self, video_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a video_id exists in the database (foreign key check).
        
        Args:
            video_id: Video identifier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.db:
            logger.warning("Database not provided, skipping foreign key validation")
            return True, None
        
        try:
            query = "SELECT COUNT(*) FROM videos WHERE video_id = ?"
            rows = self.db.execute_query(query, (video_id,))
            exists = rows[0][0] > 0 if rows else False
            
            if not exists:
                return False, f"Video ID {video_id} does not exist in database"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to validate video_id: {e}")
            return False, f"Foreign key validation failed: {e}"
    
    def validate_json_structure(self, data: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate that data can be serialized to JSON.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            json.dumps(data)
            return True, None
        except (TypeError, ValueError) as e:
            return False, f"Data is not JSON serializable: {e}"
    
    def validate_timestamp_ordering(
        self,
        timestamps: List[float],
        allow_duplicates: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that timestamps are in monotonically increasing order.
        
        Args:
            timestamps: List of timestamps
            allow_duplicates: Whether to allow duplicate timestamps
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not timestamps:
            return True, None
        
        for i in range(1, len(timestamps)):
            if allow_duplicates:
                if timestamps[i] < timestamps[i-1]:
                    return False, f"Timestamps not in order: {timestamps[i]} < {timestamps[i-1]} at index {i}"
            else:
                if timestamps[i] <= timestamps[i-1]:
                    return False, f"Duplicate or out-of-order timestamp: {timestamps[i]} at index {i}"
        
        return True, None
    
    def validate_batch(
        self,
        context_type: str,
        data_list: List[Dict[str, Any]],
        video_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate a batch of data items.
        
        Args:
            context_type: Type of data ('frame', 'caption', 'transcript', 'object')
            data_list: List of data dictionaries
            video_id: Optional video_id for foreign key validation
            
        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []
        
        # Validate video_id if provided
        if video_id:
            valid, error = self.validate_video_id_exists(video_id)
            if not valid:
                errors.append(error)
                return False, errors
        
        # Validate each item
        validator_map = {
            'frame': self.validate_frame,
            'caption': self.validate_caption,
            'transcript': self.validate_transcript,
            'object': self.validate_object_detection
        }
        
        validator = validator_map.get(context_type)
        if not validator:
            errors.append(f"Unknown context type: {context_type}")
            return False, errors
        
        for idx, data in enumerate(data_list):
            # Validate JSON structure
            valid, error = self.validate_json_structure(data)
            if not valid:
                errors.append(f"Item {idx}: {error}")
                continue
            
            # Validate against schema
            valid, error = validator(data)
            if not valid:
                errors.append(f"Item {idx}: {error}")
        
        # Validate timestamp ordering for time-based data
        if context_type in ['frame', 'caption', 'transcript', 'object']:
            timestamp_field_map = {
                'frame': 'timestamp',
                'caption': 'frame_timestamp',
                'transcript': 'start',
                'object': 'frame_timestamp'
            }
            
            timestamp_field = timestamp_field_map[context_type]
            timestamps = [item.get(timestamp_field, 0) for item in data_list]
            
            valid, error = self.validate_timestamp_ordering(timestamps, allow_duplicates=True)
            if not valid:
                errors.append(f"Timestamp ordering: {error}")
        
        all_valid = len(errors) == 0
        return all_valid, errors
    
    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        data_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate data against a schema definition.
        
        Args:
            data: Data dictionary to validate
            schema: Schema definition
            data_type: Type of data (for error messages)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for field in schema['required_fields']:
            if field not in data:
                return False, f"{data_type}: Missing required field '{field}'"
        
        # Check field types
        field_types = schema.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in data:
                value = data[field]
                if not isinstance(value, expected_type):
                    return False, (
                        f"{data_type}: Field '{field}' has wrong type. "
                        f"Expected {expected_type}, got {type(value)}"
                    )
        
        # Check field ranges
        field_ranges = schema.get('field_ranges', {})
        for field, (min_val, max_val) in field_ranges.items():
            if field in data:
                value = data[field]
                if not isinstance(value, (int, float)):
                    continue
                
                if value < min_val or value > max_val:
                    return False, (
                        f"{data_type}: Field '{field}' value {value} "
                        f"out of range [{min_val}, {max_val}]"
                    )
        
        return True, None


# Global validator instance
_validator_instance: Optional[DataValidator] = None


def get_data_validator(db=None) -> DataValidator:
    """
    Get or create global data validator instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        DataValidator instance
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DataValidator(db)
    return _validator_instance
