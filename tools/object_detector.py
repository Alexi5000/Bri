"""Object detection tool using YOLOv8."""

import os
from typing import List
import logging

from ultralytics import YOLO

from models.tools import DetectedObject, DetectionResult

logger = logging.getLogger(__name__)


class ObjectDetector:
    """Object detector using YOLOv8 (Ultralytics)."""
    
    def __init__(self, model_name: str = "yolov8n.pt"):
        """
        Initialize the object detector with YOLOv8 model.
        
        Args:
            model_name: YOLOv8 model variant (yolov8n.pt for speed, yolov8s/m/l/x for accuracy)
        """
        self.model_name = model_name
        
        # Load YOLOv8 model
        logger.info(f"Loading YOLOv8 model: {model_name}...")
        self.model = YOLO(model_name)
        logger.info("YOLOv8 model loaded successfully!")
    
    def detect_objects_in_frames(
        self,
        frame_paths: List[str],
        timestamps: List[float],
        confidence_threshold: float = 0.25
    ) -> List[DetectionResult]:
        """
        Detect objects in multiple frames using batch processing.
        
        Args:
            frame_paths: List of paths to frame image files
            timestamps: List of timestamps corresponding to each frame
            confidence_threshold: Minimum confidence score for detections (0-1)
            
        Returns:
            List of DetectionResult objects with detected objects and bounding boxes
            
        Raises:
            ValueError: If frame_paths and timestamps lengths don't match
        """
        if len(frame_paths) != len(timestamps):
            raise ValueError(
                f"Number of frame paths ({len(frame_paths)}) must match "
                f"number of timestamps ({len(timestamps)})"
            )
        
        detection_results = []
        
        # Filter out non-existent files
        valid_frames = []
        valid_timestamps = []
        for path, ts in zip(frame_paths, timestamps):
            if os.path.exists(path):
                valid_frames.append(path)
                valid_timestamps.append(ts)
            else:
                logger.warning(f"Frame file not found: {path}")
                # Add empty result for missing frames
                detection_results.append(DetectionResult(
                    frame_timestamp=ts,
                    objects=[]
                ))
        
        if not valid_frames:
            logger.warning("No valid frames to process")
            return detection_results
        
        try:
            # Run batch inference
            logger.info(f"Running object detection on {len(valid_frames)} frames...")
            results = self.model(valid_frames, conf=confidence_threshold, verbose=False)
            
            # Process results
            for result, timestamp in zip(results, valid_timestamps):
                detected_objects = []
                
                # Extract detections from result
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    for i in range(len(boxes)):
                        # Get bounding box coordinates (xyxy format)
                        box_xyxy = boxes.xyxy[i].cpu().numpy()
                        x1, y1, x2, y2 = box_xyxy
                        
                        # Convert to xywh format
                        x = int(x1)
                        y = int(y1)
                        w = int(x2 - x1)
                        h = int(y2 - y1)
                        
                        # Get confidence and class
                        confidence = float(boxes.conf[i].cpu().numpy())
                        class_id = int(boxes.cls[i].cpu().numpy())
                        class_name = result.names[class_id]
                        
                        detected_objects.append(DetectedObject(
                            class_name=class_name,
                            confidence=confidence,
                            bbox=(x, y, w, h)
                        ))
                
                detection_results.append(DetectionResult(
                    frame_timestamp=timestamp,
                    objects=detected_objects
                ))
                
                logger.debug(
                    f"Detected {len(detected_objects)} objects at timestamp {timestamp:.2f}s"
                )
            
            logger.info(f"Object detection complete for {len(valid_frames)} frames")
            return detection_results
            
        except Exception as e:
            logger.error(f"Object detection failed: {str(e)}")
            # Return empty results for all frames on failure
            return [
                DetectionResult(frame_timestamp=ts, objects=[])
                for ts in timestamps
            ]
    
    def search_for_object(
        self,
        frame_paths: List[str],
        timestamps: List[float],
        object_class: str,
        confidence_threshold: float = 0.25
    ) -> List[DetectionResult]:
        """
        Find all occurrences of a specific object class across frames.
        
        Args:
            frame_paths: List of paths to frame image files
            timestamps: List of timestamps corresponding to each frame
            object_class: Object class name to search for (e.g., 'person', 'car', 'dog')
            confidence_threshold: Minimum confidence score for detections (0-1)
            
        Returns:
            List of DetectionResult objects containing only the specified object class
        """
        # First, detect all objects in frames
        all_detections = self.detect_objects_in_frames(
            frame_paths,
            timestamps,
            confidence_threshold
        )
        
        # Filter results to only include the specified object class
        filtered_results = []
        object_class_lower = object_class.lower()
        
        for detection in all_detections:
            # Filter objects to only include matching class
            matching_objects = [
                obj for obj in detection.objects
                if obj.class_name.lower() == object_class_lower
            ]
            
            # Only include frames where the object was found
            if matching_objects:
                filtered_results.append(DetectionResult(
                    frame_timestamp=detection.frame_timestamp,
                    objects=matching_objects
                ))
        
        logger.info(
            f"Found '{object_class}' in {len(filtered_results)} out of "
            f"{len(frame_paths)} frames"
        )
        
        return filtered_results
    
    def get_available_classes(self) -> List[str]:
        """
        Get list of object classes that the model can detect.
        
        Returns:
            List of class names
        """
        return list(self.model.names.values())
    
    def detect_single_frame(
        self,
        frame_path: str,
        timestamp: float,
        confidence_threshold: float = 0.25
    ) -> DetectionResult:
        """
        Detect objects in a single frame.
        
        Args:
            frame_path: Path to frame image file
            timestamp: Timestamp of the frame
            confidence_threshold: Minimum confidence score for detections (0-1)
            
        Returns:
            DetectionResult object with detected objects
        """
        results = self.detect_objects_in_frames(
            [frame_path],
            [timestamp],
            confidence_threshold
        )
        return results[0] if results else DetectionResult(
            frame_timestamp=timestamp,
            objects=[]
        )
