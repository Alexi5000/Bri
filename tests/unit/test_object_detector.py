"""Unit tests for ObjectDetector."""

import pytest
import tempfile
import os
import numpy as np
from PIL import Image
from unittest.mock import patch, MagicMock
from tools.object_detector import ObjectDetector
from models.tools import DetectedObject, DetectionResult


@pytest.fixture
def mock_yolo_model():
    """Create mock YOLO model."""
    with patch('tools.object_detector.YOLO') as mock_yolo_class:
        # Mock YOLO model
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        
        # Mock model.names (COCO classes)
        mock_model.names = {
            0: 'person',
            1: 'bicycle',
            2: 'car',
            16: 'dog',
            17: 'cat'
        }
        
        yield {
            'yolo_class': mock_yolo_class,
            'model': mock_model
        }


@pytest.fixture
def object_detector(mock_yolo_model):
    """Create ObjectDetector instance with mocked YOLO model."""
    detector = ObjectDetector()
    return detector


@pytest.fixture
def sample_image():
    """Create a sample image file for testing."""
    fd, path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    
    # Create a simple test image
    img = Image.new('RGB', (640, 480), color=(255, 0, 0))
    img.save(path)
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def multiple_images():
    """Create multiple sample images for batch testing."""
    images = []
    
    for i in range(5):
        fd, path = tempfile.mkstemp(suffix=f'_{i}.jpg')
        os.close(fd)
        
        img = Image.new('RGB', (320, 240), color=(i * 50, 100, 200))
        img.save(path)
        
        images.append(path)
    
    yield images
    
    # Cleanup
    for path in images:
        if os.path.exists(path):
            os.unlink(path)


def create_mock_detection_result(num_objects=2, class_ids=None, confidences=None):
    """Helper to create mock YOLO detection result."""
    mock_result = MagicMock()
    
    if num_objects == 0:
        mock_result.boxes = None
        return mock_result
    
    # Default class IDs and confidences
    if class_ids is None:
        class_ids = [0, 2]  # person, car
    if confidences is None:
        confidences = [0.85, 0.75]
    
    # Mock boxes
    mock_boxes = MagicMock()
    
    # Mock xyxy coordinates (x1, y1, x2, y2)
    xyxy_coords = []
    for i in range(num_objects):
        x1, y1 = 100 + i * 50, 100 + i * 50
        x2, y2 = x1 + 100, y1 + 80
        xyxy_coords.append([x1, y1, x2, y2])
    
    mock_xyxy = MagicMock()
    mock_xyxy.__len__ = lambda self: num_objects
    mock_xyxy.__getitem__ = lambda self, i: MagicMock(cpu=lambda: MagicMock(numpy=lambda: np.array(xyxy_coords[i])))
    mock_boxes.xyxy = mock_xyxy
    
    # Mock confidence scores
    mock_conf = MagicMock()
    mock_conf.__len__ = lambda self: num_objects
    mock_conf.__getitem__ = lambda self, i: MagicMock(cpu=lambda: MagicMock(numpy=lambda: confidences[i]))
    mock_boxes.conf = mock_conf
    
    # Mock class IDs
    mock_cls = MagicMock()
    mock_cls.__len__ = lambda self: num_objects
    mock_cls.__getitem__ = lambda self, i: MagicMock(cpu=lambda: MagicMock(numpy=lambda: class_ids[i]))
    mock_boxes.cls = mock_cls
    
    mock_boxes.__len__ = lambda: num_objects
    mock_result.boxes = mock_boxes
    
    # Mock names dictionary
    mock_result.names = {
        0: 'person',
        1: 'bicycle',
        2: 'car',
        16: 'dog',
        17: 'cat'
    }
    
    return mock_result


class TestObjectDetectorInitialization:
    """Tests for ObjectDetector initialization."""
    
    def test_init_with_default_model(self, mock_yolo_model):
        """Test initialization with default YOLOv8 model."""
        detector = ObjectDetector()
        
        # Verify model was loaded
        mock_yolo_model['yolo_class'].assert_called_once_with("yolov8n.pt")
        assert detector.model_name == "yolov8n.pt"
    
    def test_init_with_custom_model(self, mock_yolo_model):
        """Test initialization with custom model name."""
        custom_model = "yolov8s.pt"
        detector = ObjectDetector(model_name=custom_model)
        
        # Verify custom model was loaded
        mock_yolo_model['yolo_class'].assert_called_with(custom_model)
        assert detector.model_name == custom_model


class TestDetectObjectsInFrames:
    """Tests for ObjectDetector.detect_objects_in_frames() method."""
    
    def test_detect_objects_success(self, object_detector, sample_image, mock_yolo_model):
        """Test detecting objects in frames successfully."""
        frame_paths = [sample_image]
        timestamps = [5.0]
        
        # Mock model inference result
        mock_result = create_mock_detection_result(num_objects=2)
        mock_yolo_model['model'].return_value = [mock_result]
        
        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)
        
        # Verify DetectionResult objects
        assert len(results) == 1
        assert isinstance(results[0], DetectionResult)
        assert results[0].frame_timestamp == 5.0
        assert len(results[0].objects) == 2
        
        # Verify detected objects
        for obj in results[0].objects:
            assert isinstance(obj, DetectedObject)
            assert obj.class_name in ['person', 'car']
            assert 0.0 <= obj.confidence <= 1.0
            assert len(obj.bbox) == 4
    
    def test_detect_objects_multiple_frames(self, object_detector, multiple_images, mock_yolo_model):
        """Test detecting objects in multiple frames."""
        timestamps = [0.0, 2.0, 4.0, 6.0, 8.0]
        
        # Mock model inference results for each frame
        mock_results = [
            create_mock_detection_result(num_objects=2),
            create_mock_detection_result(num_objects=1, class_ids=[16], confidences=[0.9]),
            create_mock_detection_result(num_objects=0),
            create_mock_detection_result(num_objects=3, class_ids=[0, 2, 17], confidences=[0.8, 0.7, 0.85]),
            create_mock_detection_result(num_objects=1, class_ids=[1], confidences=[0.65])
        ]
        mock_yolo_model['model'].return_value = mock_results
        
        results = object_detector.detect_objects_in_frames(multiple_images, timestamps)
        
        # Verify all frames were processed
        assert len(results) == 5
        
        # Verify timestamps
        for result, expected_ts in zip(results, timestamps):
            assert result.frame_timestamp == expected_ts
        
        # Verify object counts
        assert len(results[0].objects) == 2
        assert len(results[1].objects) == 1
        assert len(results[2].objects) == 0  # No objects detected
        assert len(results[3].objects) == 3
        assert len(results[4].objects) == 1
    
    def test_detect_objects_mismatched_lengths(self, object_detector, multiple_images):
        """Test that mismatched frame_paths and timestamps raises ValueError."""
        timestamps = [0.0, 2.0]  # Only 2 timestamps for 5 images
        
        with pytest.raises(ValueError, match="must match"):
            object_detector.detect_objects_in_frames(multiple_images, timestamps)
    
    def test_detect_objects_empty_lists(self, object_detector):
        """Test detecting objects with empty lists."""
        results = object_detector.detect_objects_in_frames([], [])
        
        assert results == []
    
    def test_detect_objects_nonexistent_frame(self, object_detector, mock_yolo_model):
        """Test detecting objects with nonexistent frame file."""
        frame_paths = ["/nonexistent/frame.jpg"]
        timestamps = [1.0]
        
        # Should handle gracefully and return empty result
        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)
        
        assert len(results) == 1
        assert results[0].frame_timestamp == 1.0
        assert len(results[0].objects) == 0
    
    def test_detect_objects_mixed_valid_invalid(self, object_detector, sample_image, mock_yolo_model):
        """Test detecting objects with mix of valid and invalid frames."""
        frame_paths = [sample_image, "/nonexistent/frame.jpg", sample_image]
        timestamps = [0.0, 1.0, 2.0]
        
        # Mock results for valid frames only
        mock_results = [
            create_mock_detection_result(num_objects=1),
            create_mock_detection_result(num_objects=2)
        ]
        mock_yolo_model['model'].return_value = mock_results
        
        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)
        
        # Should have results for all frames (empty for invalid)
        assert len(results) == 3
        assert results[0].frame_timestamp == 0.0
        assert len(results[0].objects) > 0
        assert results[1].frame_timestamp == 1.0
        assert len(results[1].objects) == 0  # Invalid frame
        assert results[2].frame_timestamp == 2.0
        assert len(results[2].objects) > 0
    
    def test_detect_objects_custom_confidence_threshold(self, object_detector, sample_image, mock_yolo_model):
        """Test detecting objects with custom confidence threshold."""
        frame_paths = [sample_image]
        timestamps = [1.0]
        confidence_threshold = 0.5
        
        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model['model'].return_value = [mock_result]
        
        results = object_detector.detect_objects_in_frames(
            frame_paths, 
            timestamps, 
            confidence_threshold=confidence_threshold
        )
        
        # Verify model was called with correct confidence threshold
        mock_yolo_model['model'].assert_called_once()
        call_kwargs = mock_yolo_model['model'].call_args[1]
        assert call_kwargs['conf'] == confidence_threshold
        
        assert len(results) == 1
    
    def test_detect_objects_no_detections(self, object_detector, sample_image, mock_yolo_model):
        """Test detecting objects when no objects are found."""
        frame_paths = [sample_image]
        timestamps = [1.0]
        
        # Mock result with no detections
        mock_result = create_mock_detection_result(num_objects=0)
        mock_yolo_model['model'].return_value = [mock_result]
        
        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)
        
        assert len(results) == 1
        assert results[0].frame_timestamp == 1.0
        assert len(results[0].objects) == 0
    
    def test_detect_objects_bbox_format(self, object_detector, sample_image, mock_yolo_model):
        """Test that bounding boxes are in correct format (x, y, w, h)."""
        frame_paths = [sample_image]
        timestamps = [1.0]
        
        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model['model'].return_value = [mock_result]
        
        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)
        
        obj = results[0].objects[0]
        x, y, w, h = obj.bbox
        
        # Verify bbox values are positive integers
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(w, int)
        assert isinstance(h, int)
        assert x >= 0
        assert y >= 0
        assert w > 0
        assert h > 0
    
    def test_detect_objects_custom_confidence_threshold(self, object_detector, sample_image, mock_yolo_model):
        """Test detecting objects with custom confidence threshold."""
        frame_paths = [sample_image]
        timestamps = [1.0]
        confidence_threshold = 0.5
        
        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model['model'].return_value = [mock_result]
        
        results = object_detector.detect_objects_in_frames(
            frame_paths, 
            timestamps, 
            confidence_threshold=confidence_threshold
        )
        
        # Verify model was called with correct confidence threshold
        mock_yolo_model['model'].assert_called_once()
        call_kwargs = mock_yolo_model['model'].call_args[1]
        assert call_kwargs['conf'] == confidence_threshold
        
        assert len(results) == 1
    
    def test_detect_objects_no_detections(self, object_detector, sample_image, mock_yolo_model):
        """Test detecting objects when no objects are found."""
        frame_paths = [sample_image]
        timestamps = [1.0]
        
        # Mock result with no detections
        mock_result = create_mock_detection_result(num_objects=0)
        mock_yolo_model['model'].return_value = [mock_result]
        
        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)
        
        assert len(results) == 1
        assert results[0].frame_timestamp == 1.0
        assert len(results[0].objects) == 0
    
    def test_detect_objects_bbox_format(self, object_detector, sample_image, mock_yolo_model):
        """Test that bounding boxes are in correct format (x, y, w, h)."""
        frame_paths = [sample_image]
        timestamps = [1.0]
        
        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model['model'].return_value = [mock_result]
        
        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)
        
        obj = results[0].objects[0]
        x, y, w, h = obj.bbox
        
        # Verify bbox values are positive integers
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(w, int)
        assert isinstance(h, int)
        assert x >= 0
        assert y >= 0
        assert w > 0
        assert h > 0
