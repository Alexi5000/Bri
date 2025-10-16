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
    with patch("tools.object_detector.YOLO") as mock_yolo_class:
        # Mock YOLO model
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model

        # Mock model.names (COCO classes)
        mock_model.names = {0: "person", 1: "bicycle", 2: "car", 16: "dog", 17: "cat"}

        yield {"yolo_class": mock_yolo_class, "model": mock_model}


@pytest.fixture
def object_detector(mock_yolo_model):
    """Create ObjectDetector instance with mocked YOLO model."""
    detector = ObjectDetector()
    return detector


@pytest.fixture
def sample_image():
    """Create a sample image file for testing."""
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)

    # Create a simple test image
    img = Image.new("RGB", (640, 480), color=(255, 0, 0))
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
        fd, path = tempfile.mkstemp(suffix=f"_{i}.jpg")
        os.close(fd)

        img = Image.new("RGB", (320, 240), color=(i * 50, 100, 200))
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
        mock_result.names = {0: "person", 1: "bicycle", 2: "car", 16: "dog", 17: "cat"}
        return mock_result

    # Default class IDs and confidences
    if class_ids is None:
        class_ids = [0, 2][:num_objects]  # person, car
    if confidences is None:
        confidences = [0.85, 0.75][:num_objects]

    # Ensure we have enough values
    while len(class_ids) < num_objects:
        class_ids.append(0)
    while len(confidences) < num_objects:
        confidences.append(0.8)

    # Mock boxes
    mock_boxes = MagicMock()

    # Mock xyxy coordinates (x1, y1, x2, y2)
    xyxy_coords = []
    for i in range(num_objects):
        x1, y1 = 100 + i * 50, 100 + i * 50
        x2, y2 = x1 + 100, y1 + 80
        xyxy_coords.append([x1, y1, x2, y2])

    # Create mock xyxy with proper indexing
    class MockXYXY:
        def __len__(self):
            return num_objects

        def __getitem__(self, i):
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value.numpy.return_value = np.array(xyxy_coords[i])
            return mock_tensor

    mock_boxes.xyxy = MockXYXY()

    # Create mock confidence with proper indexing
    class MockConf:
        def __len__(self):
            return num_objects

        def __getitem__(self, i):
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value.numpy.return_value = confidences[i]
            return mock_tensor

    mock_boxes.conf = MockConf()

    # Create mock class IDs with proper indexing
    class MockCls:
        def __len__(self):
            return num_objects

        def __getitem__(self, i):
            mock_tensor = MagicMock()
            mock_tensor.cpu.return_value.numpy.return_value = class_ids[i]
            return mock_tensor

    mock_boxes.cls = MockCls()

    # Set __len__ for boxes
    mock_boxes.__len__ = MagicMock(return_value=num_objects)
    mock_result.boxes = mock_boxes

    # Mock names dictionary
    mock_result.names = {0: "person", 1: "bicycle", 2: "car", 16: "dog", 17: "cat"}

    return mock_result


class TestObjectDetectorInitialization:
    """Tests for ObjectDetector initialization."""

    def test_init_with_default_model(self, mock_yolo_model):
        """Test initialization with default YOLOv8 model."""
        detector = ObjectDetector()

        # Verify model was loaded
        mock_yolo_model["yolo_class"].assert_called_once_with("yolov8n.pt")
        assert detector.model_name == "yolov8n.pt"

    def test_init_with_custom_model(self, mock_yolo_model):
        """Test initialization with custom model name."""
        custom_model = "yolov8s.pt"
        detector = ObjectDetector(model_name=custom_model)

        # Verify custom model was loaded
        mock_yolo_model["yolo_class"].assert_called_with(custom_model)
        assert detector.model_name == custom_model


class TestDetectObjectsInFrames:
    """Tests for ObjectDetector.detect_objects_in_frames() method."""

    def test_detect_objects_success(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detecting objects in frames successfully."""
        frame_paths = [sample_image]
        timestamps = [5.0]

        # Mock model inference result
        mock_result = create_mock_detection_result(num_objects=2)
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)

        # Verify DetectionResult objects
        assert len(results) == 1
        assert isinstance(results[0], DetectionResult)
        assert results[0].frame_timestamp == 5.0
        assert len(results[0].objects) == 2

        # Verify detected objects
        for obj in results[0].objects:
            assert isinstance(obj, DetectedObject)
            assert obj.class_name in ["person", "car"]
            assert 0.0 <= obj.confidence <= 1.0
            assert len(obj.bbox) == 4

    def test_detect_objects_multiple_frames(
        self, object_detector, multiple_images, mock_yolo_model
    ):
        """Test detecting objects in multiple frames."""
        timestamps = [0.0, 2.0, 4.0, 6.0, 8.0]

        # Mock model inference results for each frame
        mock_results = [
            create_mock_detection_result(num_objects=2),
            create_mock_detection_result(
                num_objects=1, class_ids=[16], confidences=[0.9]
            ),
            create_mock_detection_result(num_objects=0),
            create_mock_detection_result(
                num_objects=3, class_ids=[0, 2, 17], confidences=[0.8, 0.7, 0.85]
            ),
            create_mock_detection_result(
                num_objects=1, class_ids=[1], confidences=[0.65]
            ),
        ]
        mock_yolo_model["model"].return_value = mock_results

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

    def test_detect_objects_mixed_valid_invalid(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detecting objects with mix of valid and invalid frames."""
        frame_paths = [sample_image, "/nonexistent/frame.jpg", sample_image]
        timestamps = [0.0, 1.0, 2.0]

        # Mock results for valid frames only
        mock_results = [
            create_mock_detection_result(num_objects=1),
            create_mock_detection_result(num_objects=2),
        ]
        mock_yolo_model["model"].return_value = mock_results

        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)

        # Should have results for all frames
        assert len(results) == 3

        # Find results by timestamp (order may vary due to implementation)
        results_by_ts = {r.frame_timestamp: r for r in results}

        # Valid frames should have objects
        assert results_by_ts[0.0].frame_timestamp == 0.0
        assert len(results_by_ts[0.0].objects) > 0

        # Invalid frame should have empty objects
        assert results_by_ts[1.0].frame_timestamp == 1.0
        assert len(results_by_ts[1.0].objects) == 0

        # Valid frame should have objects
        assert results_by_ts[2.0].frame_timestamp == 2.0
        assert len(results_by_ts[2.0].objects) > 0

    def test_detect_objects_custom_confidence_threshold(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detecting objects with custom confidence threshold."""
        frame_paths = [sample_image]
        timestamps = [1.0]
        confidence_threshold = 0.5

        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames(
            frame_paths, timestamps, confidence_threshold=confidence_threshold
        )

        # Verify model was called with correct confidence threshold
        mock_yolo_model["model"].assert_called_once()
        call_kwargs = mock_yolo_model["model"].call_args[1]
        assert call_kwargs["conf"] == confidence_threshold

        assert len(results) == 1

    def test_detect_objects_no_detections(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detecting objects when no objects are found."""
        frame_paths = [sample_image]
        timestamps = [1.0]

        # Mock result with no detections
        mock_result = create_mock_detection_result(num_objects=0)
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)

        assert len(results) == 1
        assert results[0].frame_timestamp == 1.0
        assert len(results[0].objects) == 0

    def test_detect_objects_bbox_format(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test that bounding boxes are in correct format (x, y, w, h)."""
        frame_paths = [sample_image]
        timestamps = [1.0]

        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model["model"].return_value = [mock_result]

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

    def test_detect_objects_inference_error_handling(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test that inference errors are handled gracefully."""
        frame_paths = [sample_image]
        timestamps = [1.0]

        # Mock model to raise exception
        mock_yolo_model["model"].side_effect = Exception("Inference failed")

        results = object_detector.detect_objects_in_frames(frame_paths, timestamps)

        # Should return empty results instead of crashing
        assert len(results) == 1
        assert results[0].frame_timestamp == 1.0
        assert len(results[0].objects) == 0


class TestSearchForObject:
    """Tests for ObjectDetector.search_for_object() method."""

    def test_search_for_object_found(
        self, object_detector, multiple_images, mock_yolo_model
    ):
        """Test searching for specific object class that exists."""
        timestamps = [0.0, 2.0, 4.0, 6.0, 8.0]

        # Mock results: person in frames 0, 2, 4; car in frames 1, 3
        mock_results = [
            create_mock_detection_result(
                num_objects=2, class_ids=[0, 2], confidences=[0.9, 0.8]
            ),  # person, car
            create_mock_detection_result(
                num_objects=1, class_ids=[2], confidences=[0.85]
            ),  # car
            create_mock_detection_result(
                num_objects=1, class_ids=[0], confidences=[0.75]
            ),  # person
            create_mock_detection_result(
                num_objects=2, class_ids=[2, 16], confidences=[0.7, 0.9]
            ),  # car, dog
            create_mock_detection_result(
                num_objects=1, class_ids=[0], confidences=[0.88]
            ),  # person
        ]
        mock_yolo_model["model"].return_value = mock_results

        # Search for 'person'
        results = object_detector.search_for_object(
            multiple_images, timestamps, "person"
        )

        # Should find person in frames 0, 2, 4
        assert len(results) == 3
        assert results[0].frame_timestamp == 0.0
        assert results[1].frame_timestamp == 4.0
        assert results[2].frame_timestamp == 8.0

        # Verify only person objects are included
        for result in results:
            for obj in result.objects:
                assert obj.class_name == "person"

    def test_search_for_object_not_found(
        self, object_detector, multiple_images, mock_yolo_model
    ):
        """Test searching for object class that doesn't exist."""
        timestamps = [0.0, 2.0, 4.0]

        # Mock results with no 'cat' objects
        mock_results = [
            create_mock_detection_result(
                num_objects=1, class_ids=[0], confidences=[0.9]
            ),  # person
            create_mock_detection_result(
                num_objects=1, class_ids=[2], confidences=[0.85]
            ),  # car
            create_mock_detection_result(
                num_objects=1, class_ids=[16], confidences=[0.75]
            ),  # dog
        ]
        mock_yolo_model["model"].return_value = mock_results

        # Search for 'cat'
        results = object_detector.search_for_object(
            multiple_images[:3], timestamps, "cat"
        )

        # Should return empty list
        assert len(results) == 0

    def test_search_for_object_case_insensitive(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test that object search is case-insensitive."""
        timestamps = [1.0]

        mock_result = create_mock_detection_result(
            num_objects=1, class_ids=[2], confidences=[0.9]
        )  # car
        mock_yolo_model["model"].return_value = [mock_result]

        # Search with different cases
        results_lower = object_detector.search_for_object(
            [sample_image], timestamps, "car"
        )
        results_upper = object_detector.search_for_object(
            [sample_image], timestamps, "CAR"
        )
        results_mixed = object_detector.search_for_object(
            [sample_image], timestamps, "Car"
        )

        # All should find the object
        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1

    def test_search_for_object_multiple_instances(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test searching when multiple instances of object exist in same frame."""
        timestamps = [1.0]

        # Mock result with 3 persons in one frame
        mock_result = create_mock_detection_result(
            num_objects=3,
            class_ids=[0, 0, 0],  # 3 persons
            confidences=[0.9, 0.85, 0.8],
        )
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.search_for_object(
            [sample_image], timestamps, "person"
        )

        # Should return one result with all 3 person objects
        assert len(results) == 1
        assert len(results[0].objects) == 3
        assert all(obj.class_name == "person" for obj in results[0].objects)

    def test_search_for_object_with_confidence_threshold(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test searching with custom confidence threshold."""
        timestamps = [1.0]

        mock_result = create_mock_detection_result(
            num_objects=1, class_ids=[0], confidences=[0.9]
        )
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.search_for_object(
            [sample_image], timestamps, "person", confidence_threshold=0.6
        )

        # Verify model was called with correct threshold
        mock_yolo_model["model"].assert_called_once()
        call_kwargs = mock_yolo_model["model"].call_args[1]
        assert call_kwargs["conf"] == 0.6

        assert len(results) == 1

    def test_search_for_object_filters_other_classes(
        self, object_detector, multiple_images, mock_yolo_model
    ):
        """Test that search only returns specified class, filtering out others."""
        timestamps = [0.0, 2.0, 4.0]

        # Mock results with mixed objects
        mock_results = [
            create_mock_detection_result(
                num_objects=3, class_ids=[0, 2, 16], confidences=[0.9, 0.8, 0.85]
            ),
            create_mock_detection_result(
                num_objects=2, class_ids=[2, 17], confidences=[0.75, 0.9]
            ),
            create_mock_detection_result(
                num_objects=2, class_ids=[0, 2], confidences=[0.88, 0.82]
            ),
        ]
        mock_yolo_model["model"].return_value = mock_results

        # Search for 'car' only
        results = object_detector.search_for_object(
            multiple_images[:3], timestamps, "car"
        )

        # Should find car in all 3 frames
        assert len(results) == 3

        # Verify only car objects are included
        for result in results:
            assert all(obj.class_name == "car" for obj in result.objects)
            assert len(result.objects) == 1  # Only one car per frame in mock data

    def test_search_for_object_empty_frames(self, object_detector):
        """Test searching with empty frame list."""
        results = object_detector.search_for_object([], [], "person")
        assert results == []


class TestDetectSingleFrame:
    """Tests for ObjectDetector.detect_single_frame() method."""

    def test_detect_single_frame_success(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detecting objects in a single frame."""
        timestamp = 5.5

        mock_result = create_mock_detection_result(num_objects=2)
        mock_yolo_model["model"].return_value = [mock_result]

        result = object_detector.detect_single_frame(sample_image, timestamp)

        assert isinstance(result, DetectionResult)
        assert result.frame_timestamp == 5.5
        assert len(result.objects) == 2

    def test_detect_single_frame_no_objects(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detecting single frame with no objects."""
        timestamp = 1.0

        mock_result = create_mock_detection_result(num_objects=0)
        mock_yolo_model["model"].return_value = [mock_result]

        result = object_detector.detect_single_frame(sample_image, timestamp)

        assert result.frame_timestamp == 1.0
        assert len(result.objects) == 0

    def test_detect_single_frame_nonexistent(self, object_detector, mock_yolo_model):
        """Test detecting single frame that doesn't exist."""
        result = object_detector.detect_single_frame("/nonexistent/frame.jpg", 1.0)

        assert result.frame_timestamp == 1.0
        assert len(result.objects) == 0


class TestGetAvailableClasses:
    """Tests for ObjectDetector.get_available_classes() method."""

    def test_get_available_classes(self, object_detector, mock_yolo_model):
        """Test getting list of available object classes."""
        classes = object_detector.get_available_classes()

        # Should return list of class names from model
        assert isinstance(classes, list)
        assert "person" in classes
        assert "bicycle" in classes
        assert "car" in classes
        assert "dog" in classes
        assert "cat" in classes

    def test_available_classes_count(self, object_detector, mock_yolo_model):
        """Test that available classes match model's class count."""
        classes = object_detector.get_available_classes()

        # Mock model has 5 classes
        assert len(classes) == 5


class TestObjectDetectorEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_detect_with_very_high_confidence_threshold(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detection with very high confidence threshold."""
        timestamps = [1.0]

        # Mock result with low confidence objects
        mock_result = create_mock_detection_result(num_objects=1, confidences=[0.3])
        mock_yolo_model["model"].return_value = [mock_result]

        # Use high threshold (0.9) - should filter out low confidence detections
        results = object_detector.detect_objects_in_frames(
            [sample_image], timestamps, confidence_threshold=0.9
        )

        # Model is called with high threshold, so it should filter internally
        assert len(results) == 1

    def test_detect_with_zero_confidence_threshold(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test detection with zero confidence threshold."""
        timestamps = [1.0]

        mock_result = create_mock_detection_result(num_objects=2)
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames(
            [sample_image], timestamps, confidence_threshold=0.0
        )

        # Should accept all detections
        assert len(results) == 1
        assert len(results[0].objects) == 2

    def test_bbox_coordinates_are_integers(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test that bounding box coordinates are converted to integers."""
        timestamps = [1.0]

        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames([sample_image], timestamps)

        obj = results[0].objects[0]
        x, y, w, h = obj.bbox

        # All bbox values should be integers
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(w, int)
        assert isinstance(h, int)

    def test_confidence_values_are_floats(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test that confidence values are floats between 0 and 1."""
        timestamps = [1.0]

        mock_result = create_mock_detection_result(
            num_objects=2, confidences=[0.85, 0.92]
        )
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames([sample_image], timestamps)

        for obj in results[0].objects:
            assert isinstance(obj.confidence, float)
            assert 0.0 <= obj.confidence <= 1.0

    def test_class_names_are_strings(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test that class names are strings."""
        timestamps = [1.0]

        mock_result = create_mock_detection_result(num_objects=2)
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames([sample_image], timestamps)

        for obj in results[0].objects:
            assert isinstance(obj.class_name, str)
            assert len(obj.class_name) > 0

    def test_detection_result_structure(
        self, object_detector, sample_image, mock_yolo_model
    ):
        """Test that DetectionResult has correct structure."""
        timestamps = [1.0]

        mock_result = create_mock_detection_result(num_objects=1)
        mock_yolo_model["model"].return_value = [mock_result]

        results = object_detector.detect_objects_in_frames([sample_image], timestamps)

        result = results[0]

        # Verify DetectionResult structure
        assert hasattr(result, "frame_timestamp")
        assert hasattr(result, "objects")
        assert isinstance(result.frame_timestamp, float)
        assert isinstance(result.objects, list)

        # Verify DetectedObject structure
        if len(result.objects) > 0:
            obj = result.objects[0]
            assert hasattr(obj, "class_name")
            assert hasattr(obj, "confidence")
            assert hasattr(obj, "bbox")
            assert isinstance(obj.bbox, tuple)
            assert len(obj.bbox) == 4
