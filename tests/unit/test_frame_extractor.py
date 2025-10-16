"""Unit tests for FrameExtractor."""

import pytest
import tempfile
import os
import cv2
import numpy as np
from pathlib import Path
from tools.frame_extractor import FrameExtractor
from models.video import Frame, VideoMetadata


@pytest.fixture
def temp_frame_storage():
    """Create a temporary directory for frame storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def frame_extractor(temp_frame_storage):
    """Create FrameExtractor instance with temporary storage."""
    return FrameExtractor(frame_storage_path=temp_frame_storage)


@pytest.fixture
def sample_video():
    """Create a sample video file for testing."""
    # Create temporary video file
    fd, path = tempfile.mkstemp(suffix='.mp4')
    os.close(fd)
    
    # Video properties
    fps = 30.0
    duration_seconds = 10
    width, height = 640, 480
    total_frames = int(fps * duration_seconds)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))
    
    # Write frames with different colors to distinguish them
    for i in range(total_frames):
        # Create frame with gradient based on frame number
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        color_value = int((i / total_frames) * 255)
        frame[:, :] = [color_value, 128, 255 - color_value]
        out.write(frame)
    
    out.release()
    
    yield path, fps, duration_seconds, width, height, total_frames
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def short_video():
    """Create a short video (2 seconds) for testing."""
    fd, path = tempfile.mkstemp(suffix='.mp4')
    os.close(fd)
    
    fps = 30.0
    duration_seconds = 2
    width, height = 320, 240
    total_frames = int(fps * duration_seconds)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))
    
    for i in range(total_frames):
        frame = np.ones((height, width, 3), dtype=np.uint8) * (i * 4)
        out.write(frame)
    
    out.release()
    
    yield path, fps, duration_seconds, width, height, total_frames
    
    if os.path.exists(path):
        os.unlink(path)


class TestGetVideoMetadata:
    """Tests for FrameExtractor.get_video_metadata() method."""
    
    def test_get_metadata_success(self, frame_extractor, sample_video):
        """Test retrieving video metadata successfully."""
        video_path, fps, duration, width, height, total_frames = sample_video
        
        metadata = frame_extractor.get_video_metadata(video_path)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.fps == pytest.approx(fps, rel=0.1)
        assert metadata.duration == pytest.approx(duration, rel=0.1)
        assert metadata.width == width
        assert metadata.height == height
        assert metadata.file_size > 0
        assert isinstance(metadata.codec, str)
    
    def test_get_metadata_nonexistent_file(self, frame_extractor):
        """Test that nonexistent file raises ValueError."""
        with pytest.raises(ValueError, match="Video file not found"):
            frame_extractor.get_video_metadata("/nonexistent/video.mp4")
    
    def test_get_metadata_invalid_file(self, frame_extractor):
        """Test that invalid video file raises ValueError."""
        # Create a text file instead of video
        fd, path = tempfile.mkstemp(suffix='.mp4')
        os.write(fd, b"This is not a video file")
        os.close(fd)
        
        try:
            with pytest.raises(ValueError, match="Failed to open video"):
                frame_extractor.get_video_metadata(path)
        finally:
            os.unlink(path)
    
    def test_get_metadata_different_video_properties(self, frame_extractor):
        """Test metadata retrieval for video with different properties."""
        # Create a smaller, different video
        fd, path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd)
        
        fps = 24.0
        width, height = 1280, 720
        total_frames = 48  # 2 seconds
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path, fourcc, fps, (width, height))
        
        for i in range(total_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            out.write(frame)
        
        out.release()
        
        try:
            metadata = frame_extractor.get_video_metadata(path)
            
            assert metadata.fps == pytest.approx(fps, rel=0.1)
            assert metadata.width == width
            assert metadata.height == height
            assert metadata.duration == pytest.approx(2.0, rel=0.1)
        finally:
            os.unlink(path)


class TestExtractFrames:
    """Tests for FrameExtractor.extract_frames() method."""
    
    def test_extract_frames_at_default_interval(self, frame_extractor, sample_video):
        """Test extracting frames at default interval."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_001"
        
        # Extract with 2 second interval (default)
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=2.0
        )
        
        # Should extract approximately duration/interval frames
        expected_frames = int(duration / 2.0) + 1  # +1 for frame at t=0
        assert len(frames) == pytest.approx(expected_frames, abs=1)
        
        # Verify Frame objects
        for frame in frames:
            assert isinstance(frame, Frame)
            assert frame.timestamp >= 0
            assert frame.timestamp <= duration
            assert os.path.exists(frame.image_path)
            assert frame.frame_number >= 0
        
        # Verify frames are in chronological order
        timestamps = [f.timestamp for f in frames]
        assert timestamps == sorted(timestamps)
    
    def test_extract_frames_custom_interval(self, frame_extractor, sample_video):
        """Test extracting frames with custom interval."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_002"
        
        # Extract with 1 second interval
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=1.0
        )
        
        # Should extract approximately 10-11 frames (0s, 1s, 2s, ..., 10s)
        assert len(frames) >= 10
        assert len(frames) <= 11
        
        # Check interval between frames
        if len(frames) > 1:
            intervals = [frames[i+1].timestamp - frames[i].timestamp 
                        for i in range(len(frames)-1)]
            for interval in intervals:
                assert interval == pytest.approx(1.0, abs=0.1)
    
    def test_extract_frames_with_max_frames_limit(self, frame_extractor, sample_video):
        """Test that max_frames limit is respected."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_003"
        
        # Extract with small interval but limit to 5 frames
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=0.5,
            max_frames=5
        )
        
        assert len(frames) == 5
    
    def test_extract_frames_adaptive_interval(self, frame_extractor, sample_video):
        """Test that adaptive interval is used for long videos."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_004"
        
        # Request small interval but limit frames
        # Should trigger adaptive interval calculation
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=0.1,  # Would extract 100 frames
            max_frames=5  # But limit to 5
        )
        
        # Should extract exactly 5 frames
        assert len(frames) == 5
        
        # Frames should be spread across the video
        assert frames[0].timestamp == pytest.approx(0, abs=0.5)
        assert frames[-1].timestamp >= duration * 0.8  # Last frame near end
    
    def test_extract_frames_creates_directory(self, frame_extractor, sample_video):
        """Test that frame extraction creates video-specific directory."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_005"
        
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=2.0
        )
        
        # Verify directory was created
        video_dir = Path(frame_extractor.frame_storage_path) / video_id
        assert video_dir.exists()
        assert video_dir.is_dir()
        
        # Verify frames are in the directory
        for frame in frames:
            assert video_id in frame.image_path
    
    def test_extract_frames_file_naming(self, frame_extractor, sample_video):
        """Test that extracted frames have proper naming convention."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_006"
        
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=2.0,
            max_frames=3
        )
        
        # Check filename format: frame_XXXX_Ys.jpg
        for i, frame in enumerate(frames):
            filename = Path(frame.image_path).name
            assert filename.startswith(f"frame_{i:04d}_")
            assert filename.endswith("s.jpg")
    
    def test_extract_frames_nonexistent_video(self, frame_extractor):
        """Test that nonexistent video raises ValueError."""
        with pytest.raises(ValueError, match="Video file not found"):
            frame_extractor.extract_frames(
                video_path="/nonexistent/video.mp4",
                video_id="test_video",
                interval_seconds=2.0
            )
    
    def test_extract_frames_from_short_video(self, frame_extractor, short_video):
        """Test extracting frames from a very short video."""
        video_path, fps, duration, width, height, total_frames = short_video
        video_id = "test_video_short"
        
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=1.0
        )
        
        # Should extract 2-3 frames from 2-second video
        assert len(frames) >= 2
        assert len(frames) <= 3
        
        # All frames should be within video duration
        for frame in frames:
            assert frame.timestamp <= duration


class TestExtractFrameAtTimestamp:
    """Tests for FrameExtractor.extract_frame_at_timestamp() method."""
    
    def test_extract_frame_at_specific_timestamp(self, frame_extractor, sample_video):
        """Test extracting a single frame at specific timestamp."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_ts_001"
        timestamp = 5.0  # Middle of 10-second video
        
        frame = frame_extractor.extract_frame_at_timestamp(
            video_path=video_path,
            video_id=video_id,
            timestamp=timestamp
        )
        
        assert isinstance(frame, Frame)
        assert frame.timestamp == timestamp
        assert os.path.exists(frame.image_path)
        assert frame.frame_number == pytest.approx(timestamp * fps, abs=2)
        
        # Verify file was created
        assert Path(frame.image_path).exists()
    
    def test_extract_frame_at_beginning(self, frame_extractor, sample_video):
        """Test extracting frame at timestamp 0."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_ts_002"
        
        frame = frame_extractor.extract_frame_at_timestamp(
            video_path=video_path,
            video_id=video_id,
            timestamp=0.0
        )
        
        assert frame.timestamp == 0.0
        assert frame.frame_number == 0
        assert os.path.exists(frame.image_path)
    
    def test_extract_frame_at_end(self, frame_extractor, sample_video):
        """Test extracting frame near the end of video."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_ts_003"
        timestamp = duration - 0.5  # Near end
        
        frame = frame_extractor.extract_frame_at_timestamp(
            video_path=video_path,
            video_id=video_id,
            timestamp=timestamp
        )
        
        assert frame.timestamp == timestamp
        assert os.path.exists(frame.image_path)
    
    def test_extract_frame_negative_timestamp(self, frame_extractor, sample_video):
        """Test that negative timestamp raises ValueError."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_ts_004"
        
        with pytest.raises(ValueError, match="Timestamp must be non-negative"):
            frame_extractor.extract_frame_at_timestamp(
                video_path=video_path,
                video_id=video_id,
                timestamp=-1.0
            )
    
    def test_extract_frame_timestamp_exceeds_duration(self, frame_extractor, sample_video):
        """Test that timestamp beyond video duration raises ValueError."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_ts_005"
        
        with pytest.raises(ValueError, match="exceeds video duration"):
            frame_extractor.extract_frame_at_timestamp(
                video_path=video_path,
                video_id=video_id,
                timestamp=duration + 5.0
            )
    
    def test_extract_frame_nonexistent_video(self, frame_extractor):
        """Test that nonexistent video raises ValueError."""
        with pytest.raises(ValueError, match="Video file not found"):
            frame_extractor.extract_frame_at_timestamp(
                video_path="/nonexistent/video.mp4",
                video_id="test_video",
                timestamp=1.0
            )
    
    def test_extract_frame_filename_format(self, frame_extractor, sample_video):
        """Test that extracted frame has proper filename format."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_ts_006"
        timestamp = 3.5
        
        frame = frame_extractor.extract_frame_at_timestamp(
            video_path=video_path,
            video_id=video_id,
            timestamp=timestamp
        )
        
        # Check filename format: frame_ts_Xs.jpg
        filename = Path(frame.image_path).name
        assert filename.startswith("frame_ts_")
        assert f"{timestamp:.2f}s.jpg" in filename
    
    def test_extract_multiple_frames_at_different_timestamps(self, frame_extractor, sample_video):
        """Test extracting multiple frames at different timestamps."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_ts_007"
        timestamps = [1.0, 3.0, 5.0, 7.0, 9.0]
        
        frames = []
        for ts in timestamps:
            frame = frame_extractor.extract_frame_at_timestamp(
                video_path=video_path,
                video_id=video_id,
                timestamp=ts
            )
            frames.append(frame)
        
        # Verify all frames were extracted
        assert len(frames) == len(timestamps)
        
        # Verify timestamps match
        for frame, expected_ts in zip(frames, timestamps):
            assert frame.timestamp == expected_ts
            assert os.path.exists(frame.image_path)


class TestEncodeFrameToBase64:
    """Tests for FrameExtractor.encode_frame_to_base64() method."""
    
    def test_encode_frame_to_base64(self, frame_extractor, sample_video):
        """Test encoding a frame to base64."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_b64_001"
        
        # Extract a frame first
        frame = frame_extractor.extract_frame_at_timestamp(
            video_path=video_path,
            video_id=video_id,
            timestamp=2.0
        )
        
        # Encode to base64
        base64_str = frame_extractor.encode_frame_to_base64(frame.image_path)
        
        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
        
        # Verify it's valid base64
        import base64
        try:
            decoded = base64.b64decode(base64_str)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Invalid base64 encoding: {e}")
    
    def test_encode_nonexistent_frame(self, frame_extractor):
        """Test that encoding nonexistent frame raises ValueError."""
        with pytest.raises(ValueError, match="Frame file not found"):
            frame_extractor.encode_frame_to_base64("/nonexistent/frame.jpg")


class TestAdaptiveInterval:
    """Tests for FrameExtractor._calculate_adaptive_interval() method."""
    
    def test_adaptive_interval_long_video(self, frame_extractor):
        """Test adaptive interval calculation for long video."""
        duration = 600.0  # 10 minutes
        max_frames = 100
        
        interval = frame_extractor._calculate_adaptive_interval(duration, max_frames)
        
        # Should calculate interval to stay within max_frames
        expected_interval = duration / max_frames  # 6.0 seconds
        assert interval == pytest.approx(expected_interval, rel=0.01)
    
    def test_adaptive_interval_short_video(self, frame_extractor):
        """Test adaptive interval for short video uses minimum 1 second."""
        duration = 5.0  # 5 seconds
        max_frames = 100
        
        interval = frame_extractor._calculate_adaptive_interval(duration, max_frames)
        
        # Should use minimum 1 second interval
        assert interval == 1.0
    
    def test_adaptive_interval_medium_video(self, frame_extractor):
        """Test adaptive interval for medium-length video."""
        duration = 120.0  # 2 minutes
        max_frames = 60
        
        interval = frame_extractor._calculate_adaptive_interval(duration, max_frames)
        
        # Should calculate 2 seconds
        assert interval == pytest.approx(2.0, rel=0.01)
    
    def test_adaptive_interval_zero_max_frames(self, frame_extractor):
        """Test adaptive interval with zero max_frames."""
        duration = 100.0
        max_frames = 0
        
        interval = frame_extractor._calculate_adaptive_interval(duration, max_frames)
        
        # Should return default 2.0 seconds
        assert interval == 2.0


class TestFrameExtractorEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_extract_frames_from_single_frame_video(self, frame_extractor):
        """Test extracting from a video with only one frame."""
        # Create a 1-frame video
        fd, path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd)
        
        fps = 30.0
        width, height = 320, 240
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(path, fourcc, fps, (width, height))
        
        # Write single frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        out.write(frame)
        out.release()
        
        try:
            frames = frame_extractor.extract_frames(
                video_path=path,
                video_id="single_frame_video",
                interval_seconds=1.0
            )
            
            # Should extract at least 1 frame
            assert len(frames) >= 1
        finally:
            os.unlink(path)
    
    def test_frame_storage_path_creation(self, temp_frame_storage):
        """Test that FrameExtractor creates storage directory if it doesn't exist."""
        # Create path that doesn't exist
        new_storage_path = os.path.join(temp_frame_storage, "new_frames_dir")
        assert not os.path.exists(new_storage_path)
        
        # Create extractor with non-existent path
        _ = FrameExtractor(frame_storage_path=new_storage_path)
        
        # Directory should be created
        assert os.path.exists(new_storage_path)
        assert os.path.isdir(new_storage_path)
    
    def test_extract_frames_with_zero_interval(self, frame_extractor, sample_video):
        """Test that zero interval is handled gracefully."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_zero_interval"
        
        # This should use adaptive interval or handle gracefully
        frames = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=0.0,
            max_frames=5
        )
        
        # Should still extract frames (using adaptive interval)
        assert len(frames) > 0
        assert len(frames) <= 5
    
    def test_concurrent_frame_extraction(self, frame_extractor, sample_video):
        """Test that multiple extractions to same video_id don't conflict."""
        video_path, fps, duration, width, height, total_frames = sample_video
        video_id = "test_video_concurrent"
        
        # Extract frames twice
        frames1 = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=2.0,
            max_frames=3
        )
        
        frames2 = frame_extractor.extract_frames(
            video_path=video_path,
            video_id=video_id,
            interval_seconds=3.0,
            max_frames=2
        )
        
        # Both should succeed
        assert len(frames1) == 3
        assert len(frames2) == 2
        
        # All frame files should exist
        for frame in frames1 + frames2:
            assert os.path.exists(frame.image_path)
