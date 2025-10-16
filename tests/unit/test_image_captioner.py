"""Unit tests for ImageCaptioner."""

import pytest
import tempfile
import os
from PIL import Image
from unittest.mock import patch, MagicMock
from tools.image_captioner import ImageCaptioner
from models.tools import Caption


@pytest.fixture
def mock_blip_model():
    """Create mock BLIP model and processor."""
    with patch('tools.image_captioner.BlipProcessor') as mock_processor_class, \
         patch('tools.image_captioner.BlipForConditionalGeneration') as mock_model_class, \
         patch('tools.image_captioner.torch') as mock_torch:
        
        # Mock torch.cuda
        mock_torch.cuda.is_available.return_value = False
        
        # Mock processor
        mock_processor = MagicMock()
        mock_processor_class.from_pretrained.return_value = mock_processor
        
        # Mock model
        mock_model = MagicMock()
        mock_model_class.from_pretrained.return_value = mock_model
        mock_model.to.return_value = mock_model
        
        # Mock processor call (returns inputs)
        mock_inputs = {'pixel_values': MagicMock()}
        mock_processor.return_value = mock_inputs
        
        # Mock inputs.to() method
        mock_inputs_with_to = MagicMock()
        mock_inputs_with_to.to.return_value = mock_inputs
        mock_processor.return_value = mock_inputs_with_to
        
        # Mock model.generate (returns token IDs)
        mock_outputs = [MagicMock()]
        mock_model.generate.return_value = mock_outputs
        
        # Mock processor.decode (returns caption text)
        mock_processor.decode.return_value = "a person walking in a park"
        
        yield {
            'processor_class': mock_processor_class,
            'model_class': mock_model_class,
            'processor': mock_processor,
            'model': mock_model,
            'torch': mock_torch
        }


@pytest.fixture
def image_captioner(mock_blip_model):
    """Create ImageCaptioner instance with mocked BLIP model."""
    captioner = ImageCaptioner()
    return captioner


@pytest.fixture
def sample_image():
    """Create a sample image file for testing."""
    # Create temporary image file
    fd, path = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    
    # Create a simple test image (red square)
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
    
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    
    for i, color in enumerate(colors):
        fd, path = tempfile.mkstemp(suffix=f'_{i}.jpg')
        os.close(fd)
        
        img = Image.new('RGB', (320, 240), color=color)
        img.save(path)
        
        images.append(path)
    
    yield images
    
    # Cleanup
    for path in images:
        if os.path.exists(path):
            os.unlink(path)


class TestImageCaptionerInitialization:
    """Tests for ImageCaptioner initialization."""
    
    def test_init_with_default_model(self, mock_blip_model):
        """Test initialization with default BLIP model."""
        captioner = ImageCaptioner()
        
        # Verify model was loaded
        mock_blip_model['processor_class'].from_pretrained.assert_called_once_with(
            "Salesforce/blip-image-captioning-large"
        )
        mock_blip_model['model_class'].from_pretrained.assert_called_once_with(
            "Salesforce/blip-image-captioning-large"
        )
        
        assert captioner.model_name == "Salesforce/blip-image-captioning-large"
        assert captioner.device == "cpu"
    
    def test_init_with_custom_model(self, mock_blip_model):
        """Test initialization with custom model name."""
        custom_model = "Salesforce/blip-image-captioning-base"
        captioner = ImageCaptioner(model_name=custom_model)
        
        # Verify custom model was loaded
        mock_blip_model['processor_class'].from_pretrained.assert_called_with(custom_model)
        mock_blip_model['model_class'].from_pretrained.assert_called_with(custom_model)
        
        assert captioner.model_name == custom_model
    
    def test_init_with_cuda_available(self, mock_blip_model):
        """Test initialization when CUDA is available."""
        mock_blip_model['torch'].cuda.is_available.return_value = True
        
        captioner = ImageCaptioner()
        
        assert captioner.device == "cuda"
        mock_blip_model['model'].to.assert_called_with("cuda")


class TestCaptionFrame:
    """Tests for ImageCaptioner.caption_frame() method."""
    
    def test_caption_single_frame_success(self, image_captioner, sample_image, mock_blip_model):
        """Test captioning a single frame successfully."""
        timestamp = 5.0
        
        caption = image_captioner.caption_frame(sample_image, timestamp)
        
        # Verify Caption object
        assert isinstance(caption, Caption)
        assert caption.frame_timestamp == timestamp
        assert caption.text == "a person walking in a park"
        assert isinstance(caption.confidence, float)
        assert 0.0 <= caption.confidence <= 1.0
        
        # Verify model was called
        mock_blip_model['processor'].assert_called()
        mock_blip_model['model'].generate.assert_called()
        mock_blip_model['processor'].decode.assert_called()
    
    def test_caption_frame_with_zero_timestamp(self, image_captioner, sample_image):
        """Test captioning frame at timestamp 0."""
        caption = image_captioner.caption_frame(sample_image, timestamp=0.0)
        
        assert caption.frame_timestamp == 0.0
        assert isinstance(caption.text, str)
        assert len(caption.text) > 0
    
    def test_caption_frame_with_default_timestamp(self, image_captioner, sample_image):
        """Test captioning frame with default timestamp."""
        caption = image_captioner.caption_frame(sample_image)
        
        assert caption.frame_timestamp == 0.0
    
    def test_caption_frame_nonexistent_file(self, image_captioner):
        """Test that nonexistent image file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Image file not found"):
            image_captioner.caption_frame("/nonexistent/image.jpg", timestamp=1.0)
    
    def test_caption_frame_invalid_image_file(self, image_captioner):
        """Test that invalid image file raises Exception."""
        # Create a text file instead of image
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.write(fd, b"This is not an image file")
        os.close(fd)
        
        try:
            with pytest.raises(Exception, match="Failed to caption image"):
                image_captioner.caption_frame(path, timestamp=1.0)
        finally:
            os.unlink(path)
    
    def test_caption_frame_different_timestamps(self, image_captioner, sample_image):
        """Test captioning same frame with different timestamps."""
        timestamps = [0.0, 2.5, 5.0, 10.0]
        
        captions = []
        for ts in timestamps:
            caption = image_captioner.caption_frame(sample_image, ts)
            captions.append(caption)
        
        # Verify timestamps are preserved
        for caption, expected_ts in zip(captions, timestamps):
            assert caption.frame_timestamp == expected_ts
    
    def test_caption_frame_confidence_score(self, image_captioner, sample_image):
        """Test that confidence score is within valid range."""
        caption = image_captioner.caption_frame(sample_image, timestamp=1.0)
        
        assert isinstance(caption.confidence, float)
        assert 0.0 <= caption.confidence <= 1.0
    
    def test_caption_frame_text_not_empty(self, image_captioner, sample_image):
        """Test that caption text is not empty."""
        caption = image_captioner.caption_frame(sample_image, timestamp=1.0)
        
        assert isinstance(caption.text, str)
        assert len(caption.text) > 0
        assert caption.text.strip() != ""


class TestCaptionFramesBatch:
    """Tests for ImageCaptioner.caption_frames_batch() method."""
    
    def test_caption_batch_success(self, image_captioner, multiple_images, mock_blip_model):
        """Test batch captioning multiple frames successfully."""
        timestamps = [0.0, 2.0, 4.0, 6.0, 8.0]
        
        # Mock model.generate to return multiple outputs (one per image)
        mock_outputs = [MagicMock() for _ in range(len(multiple_images))]
        mock_blip_model['model'].generate.return_value = mock_outputs
        
        # Mock different captions for each frame
        mock_blip_model['processor'].decode.side_effect = [
            f"caption for frame {i}" for i in range(len(multiple_images))
        ]
        
        captions = image_captioner.caption_frames_batch(multiple_images, timestamps)
        
        # Verify all frames were captioned
        assert len(captions) == len(multiple_images)
        
        # Verify Caption objects
        for i, caption in enumerate(captions):
            assert isinstance(caption, Caption)
            assert caption.frame_timestamp == timestamps[i]
            assert isinstance(caption.text, str)
            assert len(caption.text) > 0
            assert isinstance(caption.confidence, float)
    
    def test_caption_batch_empty_lists(self, image_captioner):
        """Test batch captioning with empty lists."""
        captions = image_captioner.caption_frames_batch([], [])
        
        assert captions == []
    
    def test_caption_batch_single_image(self, image_captioner, sample_image):
        """Test batch captioning with single image."""
        captions = image_captioner.caption_frames_batch([sample_image], [1.0])
        
        assert len(captions) == 1
        assert captions[0].frame_timestamp == 1.0
        assert isinstance(captions[0].text, str)
    
    def test_caption_batch_mismatched_lengths(self, image_captioner, multiple_images):
        """Test that mismatched image_paths and timestamps raises ValueError."""
        timestamps = [0.0, 2.0]  # Only 2 timestamps for 5 images
        
        with pytest.raises(ValueError, match="must match"):
            image_captioner.caption_frames_batch(multiple_images, timestamps)
    
    def test_caption_batch_large_batch(self, image_captioner, mock_blip_model):
        """Test batch captioning with more than batch_size images."""
        # Create 25 image paths (more than batch_size of 10)
        image_paths = [f"/tmp/frame_{i}.jpg" for i in range(25)]
        timestamps = [float(i * 2) for i in range(25)]
        
        # Mock image existence and loading
        with patch('os.path.exists', return_value=True), \
             patch('PIL.Image.open') as mock_open:
            
            mock_img = MagicMock()
            mock_img.convert.return_value = mock_img
            mock_open.return_value = mock_img
            
            # Mock model.generate to return outputs for each batch
            # Will be called 3 times (10 + 10 + 5)
            def generate_side_effect(*args, **kwargs):
                # Return 10 outputs for first two calls, 5 for last
                batch_size = len(mock_blip_model['processor'].call_args[0][0])
                return [MagicMock() for _ in range(batch_size)]
            
            mock_blip_model['model'].generate.side_effect = generate_side_effect
            
            # Mock different captions
            mock_blip_model['processor'].decode.side_effect = [
                f"caption {i}" for i in range(25)
            ]
            
            captions = image_captioner.caption_frames_batch(image_paths, timestamps)
            
            # Should process all 25 images in batches
            assert len(captions) == 25
    
    def test_caption_batch_with_some_invalid_images(self, image_captioner, multiple_images, mock_blip_model):
        """Test batch captioning with some invalid images skips invalid ones in batch mode."""
        # Add a nonexistent image path
        image_paths = multiple_images + ["/nonexistent/image.jpg"]
        timestamps = [float(i) for i in range(len(image_paths))]
        
        # Mock model.generate to return outputs for valid images only (5)
        mock_outputs = [MagicMock() for _ in range(len(multiple_images))]
        mock_blip_model['model'].generate.return_value = mock_outputs
        
        # Mock captions for valid images
        mock_blip_model['processor'].decode.side_effect = [
            f"caption {i}" for i in range(len(multiple_images))
        ]
        
        # Should handle gracefully and return captions for valid images only
        captions = image_captioner.caption_frames_batch(image_paths, timestamps)
        
        # Should have captions only for valid images (batch mode skips invalid)
        assert len(captions) == len(multiple_images)
        
        # All captions should be for valid images
        for i, caption in enumerate(captions):
            assert caption.frame_timestamp == float(i)
            assert f"caption {i}" in caption.text
    
    def test_caption_batch_preserves_order(self, image_captioner, multiple_images, mock_blip_model):
        """Test that batch captioning preserves frame order."""
        timestamps = [0.0, 2.0, 4.0, 6.0, 8.0]
        
        # Mock model.generate to return multiple outputs
        mock_outputs = [MagicMock() for _ in range(len(multiple_images))]
        mock_blip_model['model'].generate.return_value = mock_outputs
        
        # Mock sequential captions
        mock_blip_model['processor'].decode.side_effect = [
            f"frame {i}" for i in range(len(multiple_images))
        ]
        
        captions = image_captioner.caption_frames_batch(multiple_images, timestamps)
        
        # Verify order is preserved
        for i, caption in enumerate(captions):
            assert caption.frame_timestamp == timestamps[i]
    
    def test_caption_batch_fallback_to_individual(self, image_captioner, multiple_images, mock_blip_model):
        """Test that batch processing falls back to individual on batch failure."""
        timestamps = [float(i) for i in range(len(multiple_images))]
        
        # Make batch processing fail initially
        call_count = [0]
        
        def side_effect_generate(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (batch) fails
                raise Exception("Batch processing failed")
            else:
                # Subsequent calls (individual) succeed
                return [MagicMock()]
        
        mock_blip_model['model'].generate.side_effect = side_effect_generate
        mock_blip_model['processor'].decode.return_value = "fallback caption"
        
        captions = image_captioner.caption_frames_batch(multiple_images, timestamps)
        
        # Should still get captions via fallback
        assert len(captions) == len(multiple_images)
        for caption in captions:
            assert isinstance(caption, Caption)
    
    def test_caption_batch_fallback_with_invalid_image(self, image_captioner, multiple_images, mock_blip_model):
        """Test that fallback mode adds placeholder for invalid images."""
        # Add a nonexistent image path
        image_paths = multiple_images + ["/nonexistent/image.jpg"]
        timestamps = [float(i) for i in range(len(image_paths))]
        
        # Make batch processing fail to trigger fallback
        call_count = [0]
        
        def side_effect_generate(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (batch) fails
                raise Exception("Batch processing failed")
            else:
                # Subsequent calls (individual) succeed
                return [MagicMock()]
        
        mock_blip_model['model'].generate.side_effect = side_effect_generate
        mock_blip_model['processor'].decode.return_value = "fallback caption"
        
        captions = image_captioner.caption_frames_batch(image_paths, timestamps)
        
        # Should have captions for all images (placeholder for invalid)
        assert len(captions) == len(image_paths)
        
        # Last caption should be placeholder
        assert captions[-1].text == "[Caption unavailable]"
        assert captions[-1].confidence == 0.0
    
    def test_caption_batch_timestamps_match(self, image_captioner, multiple_images):
        """Test that returned captions have correct timestamps."""
        timestamps = [1.5, 3.7, 5.2, 8.9, 12.3]
        
        captions = image_captioner.caption_frames_batch(multiple_images, timestamps)
        
        for caption, expected_ts in zip(captions, timestamps):
            assert caption.frame_timestamp == expected_ts


class TestProcessBatch:
    """Tests for ImageCaptioner._process_batch() internal method."""
    
    def test_process_batch_all_valid_images(self, image_captioner, multiple_images, mock_blip_model):
        """Test processing batch with all valid images."""
        timestamps = [float(i) for i in range(len(multiple_images))]
        
        # Mock model.generate to return multiple outputs
        mock_outputs = [MagicMock() for _ in range(len(multiple_images))]
        mock_blip_model['model'].generate.return_value = mock_outputs
        
        # Mock captions
        mock_blip_model['processor'].decode.side_effect = [
            f"caption {i}" for i in range(len(multiple_images))
        ]
        
        captions = image_captioner._process_batch(multiple_images, timestamps)
        
        assert len(captions) == len(multiple_images)
        for caption in captions:
            assert isinstance(caption, Caption)
    
    def test_process_batch_with_nonexistent_images(self, image_captioner):
        """Test processing batch with nonexistent images."""
        image_paths = ["/nonexistent/img1.jpg", "/nonexistent/img2.jpg"]
        timestamps = [0.0, 1.0]
        
        # Should raise exception when no valid images
        with pytest.raises(Exception, match="No valid images in batch"):
            image_captioner._process_batch(image_paths, timestamps)
    
    def test_process_batch_mixed_valid_invalid(self, image_captioner, sample_image, mock_blip_model):
        """Test processing batch with mix of valid and invalid images."""
        image_paths = [sample_image, "/nonexistent/img.jpg", sample_image]
        timestamps = [0.0, 1.0, 2.0]
        
        # Mock model.generate to return 2 outputs (for 2 valid images)
        mock_outputs = [MagicMock(), MagicMock()]
        mock_blip_model['model'].generate.return_value = mock_outputs
        
        # Mock captions
        mock_blip_model['processor'].decode.side_effect = ["test caption 1", "test caption 2"]
        
        # Should process valid images only
        captions = image_captioner._process_batch(image_paths, timestamps)
        
        # Should get captions for valid images (indices 0 and 2)
        assert len(captions) == 2
        assert captions[0].frame_timestamp == 0.0
        assert captions[1].frame_timestamp == 2.0


class TestCalculateConfidence:
    """Tests for ImageCaptioner._calculate_confidence() method."""
    
    def test_calculate_confidence_returns_valid_score(self, image_captioner):
        """Test that confidence calculation returns valid score."""
        mock_outputs = [MagicMock()]
        mock_inputs = MagicMock()
        
        confidence = image_captioner._calculate_confidence(mock_outputs, mock_inputs)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_confidence_baseline(self, image_captioner):
        """Test that confidence returns reasonable baseline for BLIP."""
        mock_outputs = [MagicMock()]
        mock_inputs = MagicMock()
        
        confidence = image_captioner._calculate_confidence(mock_outputs, mock_inputs)
        
        # BLIP baseline should be high (0.85)
        assert confidence == 0.85


class TestImageCaptionerCleanup:
    """Tests for ImageCaptioner cleanup and resource management."""
    
    def test_cleanup_on_delete(self, mock_blip_model):
        """Test that resources are cleaned up on deletion."""
        captioner = ImageCaptioner()
        
        # Manually trigger cleanup
        captioner.__del__()
        
        # Verify cleanup was attempted (model and processor deleted)
        assert not hasattr(captioner, 'model') or captioner.model is None
        assert not hasattr(captioner, 'processor') or captioner.processor is None


class TestImageCaptionerEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_caption_very_small_image(self, image_captioner):
        """Test captioning a very small image."""
        # Create tiny 10x10 image
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        
        img = Image.new('RGB', (10, 10), color=(128, 128, 128))
        img.save(path)
        
        try:
            caption = image_captioner.caption_frame(path, timestamp=1.0)
            
            assert isinstance(caption, Caption)
            assert caption.frame_timestamp == 1.0
        finally:
            os.unlink(path)
    
    def test_caption_very_large_image(self, image_captioner):
        """Test captioning a large image."""
        # Create large 4K image
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        
        img = Image.new('RGB', (3840, 2160), color=(64, 128, 192))
        img.save(path)
        
        try:
            caption = image_captioner.caption_frame(path, timestamp=1.0)
            
            assert isinstance(caption, Caption)
            assert caption.frame_timestamp == 1.0
        finally:
            os.unlink(path)
    
    def test_caption_grayscale_image(self, image_captioner):
        """Test captioning a grayscale image (should be converted to RGB)."""
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        
        # Create grayscale image
        img = Image.new('L', (640, 480), color=128)
        img.save(path)
        
        try:
            caption = image_captioner.caption_frame(path, timestamp=1.0)
            
            # Should handle conversion to RGB internally
            assert isinstance(caption, Caption)
        finally:
            os.unlink(path)
    
    def test_caption_image_with_alpha_channel(self, image_captioner):
        """Test captioning an image with alpha channel (RGBA)."""
        fd, path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        
        # Create RGBA image
        img = Image.new('RGBA', (640, 480), color=(255, 0, 0, 128))
        img.save(path)
        
        try:
            caption = image_captioner.caption_frame(path, timestamp=1.0)
            
            # Should handle conversion to RGB internally
            assert isinstance(caption, Caption)
        finally:
            os.unlink(path)
    
    def test_batch_caption_with_different_image_sizes(self, image_captioner, mock_blip_model):
        """Test batch captioning with images of different sizes."""
        image_paths = []
        sizes = [(320, 240), (640, 480), (1280, 720), (800, 600)]
        
        for i, size in enumerate(sizes):
            fd, path = tempfile.mkstemp(suffix=f'_{i}.jpg')
            os.close(fd)
            
            img = Image.new('RGB', size, color=(i * 50, 100, 200))
            img.save(path)
            
            image_paths.append(path)
        
        timestamps = [float(i) for i in range(len(image_paths))]
        
        try:
            # Mock model.generate to return multiple outputs
            mock_outputs = [MagicMock() for _ in range(len(image_paths))]
            mock_blip_model['model'].generate.return_value = mock_outputs
            
            # Mock captions
            mock_blip_model['processor'].decode.side_effect = [
                f"caption {i}" for i in range(len(image_paths))
            ]
            
            captions = image_captioner.caption_frames_batch(image_paths, timestamps)
            
            # Should handle different sizes with padding
            assert len(captions) == len(image_paths)
        finally:
            for path in image_paths:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_caption_frame_with_negative_timestamp(self, image_captioner, sample_image):
        """Test captioning with negative timestamp (should still work)."""
        caption = image_captioner.caption_frame(sample_image, timestamp=-1.0)
        
        # Should accept negative timestamp (validation is caller's responsibility)
        assert caption.frame_timestamp == -1.0
    
    def test_caption_frame_with_large_timestamp(self, image_captioner, sample_image):
        """Test captioning with very large timestamp."""
        large_timestamp = 999999.99
        
        caption = image_captioner.caption_frame(sample_image, timestamp=large_timestamp)
        
        assert caption.frame_timestamp == large_timestamp
    
    def test_batch_caption_exact_batch_size(self, image_captioner, mock_blip_model):
        """Test batch captioning with exactly batch_size images."""
        # Create exactly 10 images (batch_size)
        image_paths = []
        
        for i in range(10):
            fd, path = tempfile.mkstemp(suffix=f'_{i}.jpg')
            os.close(fd)
            
            img = Image.new('RGB', (320, 240), color=(i * 25, 100, 200))
            img.save(path)
            
            image_paths.append(path)
        
        timestamps = [float(i) for i in range(10)]
        
        try:
            # Mock model.generate to return 10 outputs
            mock_outputs = [MagicMock() for _ in range(10)]
            mock_blip_model['model'].generate.return_value = mock_outputs
            
            # Mock captions
            mock_blip_model['processor'].decode.side_effect = [
                f"caption {i}" for i in range(10)
            ]
            
            captions = image_captioner.caption_frames_batch(image_paths, timestamps)
            
            assert len(captions) == 10
        finally:
            for path in image_paths:
                if os.path.exists(path):
                    os.unlink(path)
