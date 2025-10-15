"""Audio transcription tool using OpenAI Whisper."""

import os
import logging
from typing import Optional
import whisper

from models.tools import Transcript, TranscriptSegment

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Audio transcriber using OpenAI Whisper."""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize the audio transcriber with Whisper model.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
                       'base' or 'small' recommended for balance of speed/accuracy
        """
        self.model_size = model_size
        
        logger.info(f"Loading Whisper model: {model_size}...")
        self.model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully!")
    
    def transcribe_video(
        self,
        video_path: str,
        language: Optional[str] = None
    ) -> Transcript:
        """
        Transcribe entire video audio with timestamps.
        
        Args:
            video_path: Path to the video file
            language: Optional language code (e.g., 'en', 'es'). 
                     If None, language will be auto-detected
            
        Returns:
            Transcript object with segments and full text
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            Exception: If transcription fails
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        try:
            logger.info(f"Transcribing video: {video_path}")
            
            # Transcribe with Whisper
            # Whisper can handle video files directly (extracts audio internally)
            result = self.model.transcribe(
                video_path,
                language=language,
                verbose=False,
                word_timestamps=False  # Segment-level timestamps are sufficient
            )
            
            # Extract segments with timestamps
            segments = []
            for segment in result.get("segments", []):
                transcript_segment = TranscriptSegment(
                    start=segment["start"],
                    end=segment["end"],
                    text=segment["text"].strip(),
                    confidence=segment.get("no_speech_prob", 0.0)  # Lower is better
                )
                segments.append(transcript_segment)
            
            # Get full text
            full_text = result.get("text", "").strip()
            
            # Get detected language
            detected_language = result.get("language", "unknown")
            
            transcript = Transcript(
                segments=segments,
                language=detected_language,
                full_text=full_text
            )
            
            logger.info(
                f"Transcription complete: {len(segments)} segments, "
                f"language: {detected_language}"
            )
            
            return transcript
            
        except Exception as e:
            logger.error(f"Failed to transcribe video {video_path}: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_segment(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        language: Optional[str] = None
    ) -> TranscriptSegment:
        """
        Transcribe a specific time range of the video.
        
        Args:
            video_path: Path to the video file
            start_time: Start time in seconds
            end_time: End time in seconds
            language: Optional language code
            
        Returns:
            TranscriptSegment object for the specified time range
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If time range is invalid
            Exception: If transcription fails
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if start_time < 0 or end_time < 0:
            raise ValueError("Start and end times must be non-negative")
        
        if start_time >= end_time:
            raise ValueError(f"Start time ({start_time}) must be less than end time ({end_time})")
        
        try:
            logger.info(
                f"Transcribing segment: {video_path} "
                f"from {start_time:.2f}s to {end_time:.2f}s"
            )
            
            # Transcribe the full video (Whisper doesn't support direct segment extraction)
            # Then filter to the requested time range
            result = self.model.transcribe(
                video_path,
                language=language,
                verbose=False,
                word_timestamps=False
            )
            
            # Find segments that overlap with the requested time range
            matching_segments = []
            for segment in result.get("segments", []):
                seg_start = segment["start"]
                seg_end = segment["end"]
                
                # Check if segment overlaps with requested range
                if seg_start < end_time and seg_end > start_time:
                    matching_segments.append(segment)
            
            # Combine matching segments
            if matching_segments:
                combined_text = " ".join(
                    seg["text"].strip() for seg in matching_segments
                )
                
                # Use the actual start/end from the matching segments
                actual_start = matching_segments[0]["start"]
                actual_end = matching_segments[-1]["end"]
                
                # Average confidence (inverse of no_speech_prob)
                avg_confidence = sum(
                    seg.get("no_speech_prob", 0.0) for seg in matching_segments
                ) / len(matching_segments)
                
                transcript_segment = TranscriptSegment(
                    start=actual_start,
                    end=actual_end,
                    text=combined_text,
                    confidence=avg_confidence
                )
            else:
                # No speech detected in the requested range
                transcript_segment = TranscriptSegment(
                    start=start_time,
                    end=end_time,
                    text="[No speech detected]",
                    confidence=1.0  # High no_speech_prob
                )
            
            logger.info(f"Segment transcription complete: {len(transcript_segment.text)} characters")
            
            return transcript_segment
            
        except Exception as e:
            logger.error(
                f"Failed to transcribe segment {start_time}-{end_time} "
                f"from {video_path}: {str(e)}"
            )
            raise Exception(f"Segment transcription failed: {str(e)}")
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'model'):
            del self.model
