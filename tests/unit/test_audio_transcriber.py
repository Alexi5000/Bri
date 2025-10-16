"""Unit tests for AudioTranscriber."""

import pytest
import tempfile
import os
import cv2
import numpy as np
from unittest.mock import Mock, patch
from tools.audio_transcriber import AudioTranscriber
from models.tools import Transcript, TranscriptSegment


@pytest.fixture
def mock_whisper_model():
    """Create a mock Whisper model for testing."""
    mock_model = Mock()
    return mock_model


@pytest.fixture
def audio_transcriber(mock_whisper_model):
    """Create AudioTranscriber instance with mocked Whisper model."""
    with patch('tools.audio_transcriber.whisper.load_model', return_value=mock_whisper_model):
        transcriber = AudioTranscriber(model_size="base")
        return transcriber


@pytest.fixture
def sample_video_file():
    """Create a sample video file for testing."""
    fd, path = tempfile.mkstemp(suffix='.mp4')
    os.close(fd)
    
    # Create a simple video file
    fps = 30.0
    duration_seconds = 5
    width, height = 320, 240
    total_frames = int(fps * duration_seconds)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))
    
    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def mock_transcribe_result():
    """Create a mock transcription result from Whisper."""
    return {
        "text": "Hello world. This is a test transcription. Thank you for listening.",
        "language": "en",
        "segments": [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world.",
                "no_speech_prob": 0.1
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "This is a test transcription.",
                "no_speech_prob": 0.05
            },
            {
                "start": 5.0,
                "end": 7.0,
                "text": "Thank you for listening.",
                "no_speech_prob": 0.15
            }
        ]
    }


class TestAudioTranscriberInitialization:
    """Tests for AudioTranscriber initialization."""
    
    def test_init_with_default_model(self):
        """Test initialization with default model size."""
        with patch('tools.audio_transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            transcriber = AudioTranscriber()
            
            mock_load.assert_called_once_with("base")
            assert transcriber.model_size == "base"
    
    def test_init_with_custom_model(self):
        """Test initialization with custom model size."""
        with patch('tools.audio_transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            transcriber = AudioTranscriber(model_size="small")
            
            mock_load.assert_called_once_with("small")
            assert transcriber.model_size == "small"
    
    def test_init_with_different_model_sizes(self):
        """Test initialization with various model sizes."""
        model_sizes = ["tiny", "base", "small", "medium", "large"]
        
        for size in model_sizes:
            with patch('tools.audio_transcriber.whisper.load_model') as mock_load:
                mock_load.return_value = Mock()
                transcriber = AudioTranscriber(model_size=size)
                
                mock_load.assert_called_once_with(size)
                assert transcriber.model_size == size


class TestTranscribeVideo:
    """Tests for AudioTranscriber.transcribe_video() method."""
    
    def test_transcribe_video_success(self, audio_transcriber, sample_video_file, mock_transcribe_result):
        """Test successful full video transcription."""
        audio_transcriber.model.transcribe.return_value = mock_transcribe_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        # Verify transcribe was called
        audio_transcriber.model.transcribe.assert_called_once()
        call_args = audio_transcriber.model.transcribe.call_args
        assert call_args[0][0] == sample_video_file
        assert call_args[1]['language'] is None
        assert call_args[1]['verbose'] is False
        
        # Verify Transcript object
        assert isinstance(transcript, Transcript)
        assert transcript.language == "en"
        assert transcript.full_text == "Hello world. This is a test transcription. Thank you for listening."
        assert len(transcript.segments) == 3
        
        # Verify segments
        assert transcript.segments[0].start == 0.0
        assert transcript.segments[0].end == 2.5
        assert transcript.segments[0].text == "Hello world."
        assert transcript.segments[0].confidence == 0.1
        
        assert transcript.segments[1].start == 2.5
        assert transcript.segments[1].end == 5.0
        assert transcript.segments[1].text == "This is a test transcription."
        
        assert transcript.segments[2].start == 5.0
        assert transcript.segments[2].end == 7.0
        assert transcript.segments[2].text == "Thank you for listening."
    
    def test_transcribe_video_with_language(self, audio_transcriber, sample_video_file, mock_transcribe_result):
        """Test transcription with specified language."""
        audio_transcriber.model.transcribe.return_value = mock_transcribe_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file, language="en")
        
        # Verify language parameter was passed
        call_args = audio_transcriber.model.transcribe.call_args
        assert call_args[1]['language'] == "en"
        
        assert isinstance(transcript, Transcript)
        assert transcript.language == "en"
    
    def test_transcribe_video_nonexistent_file(self, audio_transcriber):
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            audio_transcriber.transcribe_video("/nonexistent/video.mp4")
    
    def test_transcribe_video_empty_segments(self, audio_transcriber, sample_video_file):
        """Test transcription with no speech detected."""
        mock_result = {
            "text": "",
            "language": "en",
            "segments": []
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        assert isinstance(transcript, Transcript)
        assert transcript.full_text == ""
        assert len(transcript.segments) == 0
        assert transcript.language == "en"
    
    def test_transcribe_video_strips_whitespace(self, audio_transcriber, sample_video_file):
        """Test that transcription strips whitespace from text."""
        mock_result = {
            "text": "  Hello world  ",
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "  Hello world  ",
                    "no_speech_prob": 0.1
                }
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        # Verify whitespace is stripped
        assert transcript.full_text == "Hello world"
        assert transcript.segments[0].text == "Hello world"
    
    def test_transcribe_video_handles_missing_confidence(self, audio_transcriber, sample_video_file):
        """Test transcription handles missing no_speech_prob field."""
        mock_result = {
            "text": "Hello world",
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Hello world"
                    # no_speech_prob missing
                }
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        # Should default to 0.0
        assert transcript.segments[0].confidence == 0.0
    
    def test_transcribe_video_different_languages(self, audio_transcriber, sample_video_file):
        """Test transcription with different detected languages."""
        languages = ["en", "es", "fr", "de", "ja"]
        
        for lang in languages:
            mock_result = {
                "text": "Test text",
                "language": lang,
                "segments": [
                    {
                        "start": 0.0,
                        "end": 2.0,
                        "text": "Test text",
                        "no_speech_prob": 0.1
                    }
                ]
            }
            audio_transcriber.model.transcribe.return_value = mock_result
            
            transcript = audio_transcriber.transcribe_video(sample_video_file)
            
            assert transcript.language == lang
    
    def test_transcribe_video_handles_exception(self, audio_transcriber, sample_video_file):
        """Test that transcription exceptions are handled properly."""
        audio_transcriber.model.transcribe.side_effect = Exception("Transcription failed")
        
        with pytest.raises(Exception, match="Transcription failed"):
            audio_transcriber.transcribe_video(sample_video_file)
    
    def test_transcribe_video_long_transcript(self, audio_transcriber, sample_video_file):
        """Test transcription with many segments."""
        # Create mock result with 20 segments
        segments = [
            {
                "start": i * 2.0,
                "end": (i + 1) * 2.0,
                "text": f"Segment {i} text.",
                "no_speech_prob": 0.1
            }
            for i in range(20)
        ]
        
        mock_result = {
            "text": " ".join(f"Segment {i} text." for i in range(20)),
            "language": "en",
            "segments": segments
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        assert len(transcript.segments) == 20
        assert transcript.segments[0].text == "Segment 0 text."
        assert transcript.segments[19].text == "Segment 19 text."
        assert transcript.segments[19].start == 38.0
        assert transcript.segments[19].end == 40.0


class TestTranscribeSegment:
    """Tests for AudioTranscriber.transcribe_segment() method."""
    
    def test_transcribe_segment_success(self, audio_transcriber, sample_video_file, mock_transcribe_result):
        """Test successful segment transcription."""
        audio_transcriber.model.transcribe.return_value = mock_transcribe_result
        
        # Request segment from 2.0 to 6.0 seconds
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=2.0,
            end_time=6.0
        )
        
        # Verify transcribe was called
        audio_transcriber.model.transcribe.assert_called_once()
        
        # Verify TranscriptSegment object
        assert isinstance(segment, TranscriptSegment)
        
        # Should include segments that overlap with 2.0-6.0 range
        # Segments: [0-2.5], [2.5-5.0], [5.0-7.0]
        # Overlapping: All three segments overlap (seg_start < 6.0 and seg_end > 2.0)
        # [0-2.5] overlaps because 0.0 < 6.0 and 2.5 > 2.0
        # [2.5-5.0] overlaps because 2.5 < 6.0 and 5.0 > 2.0
        # [5.0-7.0] overlaps because 5.0 < 6.0 and 7.0 > 2.0
        assert "Hello world." in segment.text
        assert "This is a test transcription." in segment.text
        assert "Thank you for listening." in segment.text
        
        # Start should be from first matching segment
        assert segment.start == 0.0
        # End should be from last matching segment
        assert segment.end == 7.0
    
    def test_transcribe_segment_at_beginning(self, audio_transcriber, sample_video_file, mock_transcribe_result):
        """Test transcribing segment at the beginning of video."""
        audio_transcriber.model.transcribe.return_value = mock_transcribe_result
        
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=0.0,
            end_time=3.0
        )
        
        assert isinstance(segment, TranscriptSegment)
        # Should include first two segments
        assert "Hello world." in segment.text
        assert "This is a test transcription." in segment.text
    
    def test_transcribe_segment_at_end(self, audio_transcriber, sample_video_file, mock_transcribe_result):
        """Test transcribing segment at the end of video."""
        audio_transcriber.model.transcribe.return_value = mock_transcribe_result
        
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=5.0,
            end_time=10.0
        )
        
        assert isinstance(segment, TranscriptSegment)
        # Should include last segment
        assert "Thank you for listening." in segment.text
        assert segment.start == 5.0
        assert segment.end == 7.0
    
    def test_transcribe_segment_single_word(self, audio_transcriber, sample_video_file, mock_transcribe_result):
        """Test transcribing a very short segment."""
        audio_transcriber.model.transcribe.return_value = mock_transcribe_result
        
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=0.0,
            end_time=1.0
        )
        
        assert isinstance(segment, TranscriptSegment)
        # Should include first segment that overlaps
        assert "Hello world." in segment.text
    
    def test_transcribe_segment_no_speech_detected(self, audio_transcriber, sample_video_file):
        """Test transcribing segment with no speech."""
        mock_result = {
            "text": "Hello world",
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Hello world",
                    "no_speech_prob": 0.1
                }
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        # Request segment outside of speech range
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=10.0,
            end_time=15.0
        )
        
        assert isinstance(segment, TranscriptSegment)
        assert segment.text == "[No speech detected]"
        assert segment.start == 10.0
        assert segment.end == 15.0
        assert segment.confidence == 1.0  # High no_speech_prob
    
    def test_transcribe_segment_with_language(self, audio_transcriber, sample_video_file, mock_transcribe_result):
        """Test segment transcription with specified language."""
        audio_transcriber.model.transcribe.return_value = mock_transcribe_result
        
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=0.0,
            end_time=3.0,
            language="es"
        )
        
        # Verify language parameter was passed
        call_args = audio_transcriber.model.transcribe.call_args
        assert call_args[1]['language'] == "es"
        
        assert isinstance(segment, TranscriptSegment)
    
    def test_transcribe_segment_nonexistent_file(self, audio_transcriber):
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            audio_transcriber.transcribe_segment(
                video_path="/nonexistent/video.mp4",
                start_time=0.0,
                end_time=5.0
            )
    
    def test_transcribe_segment_negative_start_time(self, audio_transcriber, sample_video_file):
        """Test that negative start time raises ValueError."""
        with pytest.raises(ValueError, match="Start and end times must be non-negative"):
            audio_transcriber.transcribe_segment(
                video_path=sample_video_file,
                start_time=-1.0,
                end_time=5.0
            )
    
    def test_transcribe_segment_negative_end_time(self, audio_transcriber, sample_video_file):
        """Test that negative end time raises ValueError."""
        with pytest.raises(ValueError, match="Start and end times must be non-negative"):
            audio_transcriber.transcribe_segment(
                video_path=sample_video_file,
                start_time=0.0,
                end_time=-1.0
            )
    
    def test_transcribe_segment_start_after_end(self, audio_transcriber, sample_video_file):
        """Test that start time >= end time raises ValueError."""
        with pytest.raises(ValueError, match="Start time .* must be less than end time"):
            audio_transcriber.transcribe_segment(
                video_path=sample_video_file,
                start_time=5.0,
                end_time=2.0
            )
    
    def test_transcribe_segment_start_equals_end(self, audio_transcriber, sample_video_file):
        """Test that start time == end time raises ValueError."""
        with pytest.raises(ValueError, match="Start time .* must be less than end time"):
            audio_transcriber.transcribe_segment(
                video_path=sample_video_file,
                start_time=3.0,
                end_time=3.0
            )
    
    def test_transcribe_segment_combines_multiple_segments(self, audio_transcriber, sample_video_file):
        """Test that multiple overlapping segments are combined."""
        mock_result = {
            "text": "One two three four five",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "One", "no_speech_prob": 0.1},
                {"start": 1.0, "end": 2.0, "text": "two", "no_speech_prob": 0.1},
                {"start": 2.0, "end": 3.0, "text": "three", "no_speech_prob": 0.1},
                {"start": 3.0, "end": 4.0, "text": "four", "no_speech_prob": 0.1},
                {"start": 4.0, "end": 5.0, "text": "five", "no_speech_prob": 0.1}
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        # Request segment that spans multiple segments
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=1.5,
            end_time=4.5
        )
        
        # Should combine segments that overlap with 1.5-4.5 range
        # Segments that overlap: [1.0-2.0], [2.0-3.0], [3.0-4.0], [4.0-5.0]
        # (seg_start < 4.5 and seg_end > 1.5)
        assert "two" in segment.text
        assert "three" in segment.text
        assert "four" in segment.text
        assert "five" in segment.text
        assert segment.start == 1.0
        assert segment.end == 5.0
    
    def test_transcribe_segment_calculates_average_confidence(self, audio_transcriber, sample_video_file):
        """Test that confidence is averaged across multiple segments."""
        mock_result = {
            "text": "Test text",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "Test", "no_speech_prob": 0.1},
                {"start": 2.0, "end": 4.0, "text": "text", "no_speech_prob": 0.3}
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=0.0,
            end_time=5.0
        )
        
        # Average confidence should be (0.1 + 0.3) / 2 = 0.2
        assert segment.confidence == pytest.approx(0.2, abs=0.01)
    
    def test_transcribe_segment_handles_exception(self, audio_transcriber, sample_video_file):
        """Test that segment transcription exceptions are handled properly."""
        audio_transcriber.model.transcribe.side_effect = Exception("Transcription failed")
        
        with pytest.raises(Exception, match="Segment transcription failed"):
            audio_transcriber.transcribe_segment(
                video_path=sample_video_file,
                start_time=0.0,
                end_time=5.0
            )
    
    def test_transcribe_segment_partial_overlap(self, audio_transcriber, sample_video_file):
        """Test segment transcription with partial overlap."""
        mock_result = {
            "text": "Hello world",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 3.0, "text": "Hello", "no_speech_prob": 0.1},
                {"start": 3.0, "end": 6.0, "text": "world", "no_speech_prob": 0.1}
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        # Request segment that partially overlaps with first segment
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=2.0,
            end_time=4.0
        )
        
        # Should include both segments that overlap
        assert "Hello" in segment.text
        assert "world" in segment.text


class TestAudioTranscriberEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_transcribe_video_with_unknown_language(self, audio_transcriber, sample_video_file):
        """Test transcription when language cannot be detected."""
        mock_result = {
            "text": "Test",
            "language": "unknown",
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Test", "no_speech_prob": 0.5}
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        assert transcript.language == "unknown"
    
    def test_transcribe_video_with_special_characters(self, audio_transcriber, sample_video_file):
        """Test transcription with special characters in text."""
        mock_result = {
            "text": "Hello! How are you? I'm fine, thanks.",
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 3.0,
                    "text": "Hello! How are you? I'm fine, thanks.",
                    "no_speech_prob": 0.1
                }
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        assert transcript.full_text == "Hello! How are you? I'm fine, thanks."
        assert transcript.segments[0].text == "Hello! How are you? I'm fine, thanks."
    
    def test_transcribe_video_with_unicode(self, audio_transcriber, sample_video_file):
        """Test transcription with unicode characters."""
        mock_result = {
            "text": "こんにちは 世界",
            "language": "ja",
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "こんにちは 世界", "no_speech_prob": 0.1}
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        assert transcript.full_text == "こんにちは 世界"
        assert transcript.language == "ja"
    
    def test_transcribe_segment_exact_boundary_match(self, audio_transcriber, sample_video_file):
        """Test segment transcription with exact boundary match."""
        mock_result = {
            "text": "Test",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "Test", "no_speech_prob": 0.1}
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        # Request exact segment boundaries
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=0.0,
            end_time=2.0
        )
        
        assert segment.text == "Test"
        assert segment.start == 0.0
        assert segment.end == 2.0
    
    def test_model_cleanup_on_delete(self):
        """Test that model is cleaned up when transcriber is deleted."""
        with patch('tools.audio_transcriber.whisper.load_model') as mock_load:
            mock_model = Mock()
            mock_load.return_value = mock_model
            
            transcriber = AudioTranscriber()
            assert hasattr(transcriber, 'model')
            
            # Delete transcriber
            del transcriber
            
            # Model should be deleted (we can't directly test this,
            # but we verify __del__ doesn't raise errors)
    
    def test_transcribe_very_long_video(self, audio_transcriber, sample_video_file):
        """Test transcription of video with many segments."""
        # Simulate a long video with 100 segments
        segments = [
            {
                "start": i * 10.0,
                "end": (i + 1) * 10.0,
                "text": f"Segment {i}",
                "no_speech_prob": 0.1
            }
            for i in range(100)
        ]
        
        mock_result = {
            "text": " ".join(f"Segment {i}" for i in range(100)),
            "language": "en",
            "segments": segments
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        transcript = audio_transcriber.transcribe_video(sample_video_file)
        
        assert len(transcript.segments) == 100
        assert transcript.segments[0].start == 0.0
        assert transcript.segments[99].end == 1000.0
    
    def test_transcribe_segment_with_gaps(self, audio_transcriber, sample_video_file):
        """Test segment transcription when there are gaps in speech."""
        mock_result = {
            "text": "Hello world",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Hello", "no_speech_prob": 0.1},
                # Gap from 1.0 to 5.0
                {"start": 5.0, "end": 6.0, "text": "world", "no_speech_prob": 0.1}
            ]
        }
        audio_transcriber.model.transcribe.return_value = mock_result
        
        # Request segment that spans the gap
        segment = audio_transcriber.transcribe_segment(
            video_path=sample_video_file,
            start_time=0.0,
            end_time=7.0
        )
        
        # Should include both segments despite the gap
        assert "Hello" in segment.text
        assert "world" in segment.text
        assert segment.start == 0.0
        assert segment.end == 6.0
