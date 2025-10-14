"""Frame extraction tool using OpenCV."""

import cv2
import base64
import os
from pathlib import Path
from typing import List, Optional
import logging

from models.video import Frame, VideoMetadata
from config import Config

logger = logging.getLogger(__name__)


class FrameExtractor:
    """Extract frames from videos using OpenCV."""
    
    def __init__(self, frame_storage_path: Optional[str] = None):
        """
        Initialize the FrameExtractor.
        
        Args:
            frame_storage_path: Directory to store extracted frames. 
                              Defaults to Config.FRAME_STORAGE_PATH.
        """
        self.frame_storage_path = frame_storage_path or Config.FRAME_STORAGE_PATH
        Path(self.frame_storage_path).mkdir(parents=True, exist_ok=True)
    
    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """
        Retrieve video properties (duration, fps, resolution, codec, file size).
        
        Args:
            video_path: Path to the video file
            
        Returns:
            VideoMetadata object with video properties
            
        Raises:
            ValueError: If video cannot be opened or read
        """
        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate duration
            duration = frame_count / fps if fps > 0 else 0
            
            # Get codec (fourcc code)
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            # Get file size
            file_size = os.path.getsize(video_path)
            
            return VideoMetadata(
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                codec=codec,
                file_size=file_size
            )
        finally:
            cap.release()
    
    def _calculate_adaptive_interval(self, duration: float, max_frames: int) -> float:
        """
        Calculate adaptive frame extraction interval based on video length.
        
        Args:
            duration: Video duration in seconds
            max_frames: Maximum number of frames to extract
            
        Returns:
            Interval in seconds between frame extractions
        """
        # Calculate interval needed to stay within max_frames
        calculated_interval = duration / max_frames if max_frames > 0 else 2.0
        
        # Use at least 1 second interval for very short videos
        # Use at most the calculated interval for longer videos
        return max(1.0, calculated_interval)
    
    def extract_frames(
        self,
        video_path: str,
        video_id: str,
        interval_seconds: Optional[float] = None,
        max_frames: Optional[int] = None
    ) -> List[Frame]:
        """
        Extract frames from video at regular intervals.
        
        Args:
            video_path: Path to the video file
            video_id: Unique identifier for the video
            interval_seconds: Interval between frames in seconds. 
                            If None, uses Config.FRAME_EXTRACTION_INTERVAL
            max_frames: Maximum number of frames to extract.
                       If None, uses Config.MAX_FRAMES_PER_VIDEO
            
        Returns:
            List of Frame objects with extracted frame information
            
        Raises:
            ValueError: If video cannot be opened or read
        """
        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")
        
        # Use config defaults if not specified
        interval_seconds = interval_seconds or Config.FRAME_EXTRACTION_INTERVAL
        max_frames = max_frames or Config.MAX_FRAMES_PER_VIDEO
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        try:
            # Get video metadata for adaptive interval calculation
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Use adaptive interval if video is longer than would produce max_frames
            if duration / interval_seconds > max_frames:
                interval_seconds = self._calculate_adaptive_interval(duration, max_frames)
                logger.info(f"Using adaptive interval: {interval_seconds:.2f}s for {duration:.2f}s video")
            
            # Create directory for this video's frames
            video_frame_dir = Path(self.frame_storage_path) / video_id
            video_frame_dir.mkdir(parents=True, exist_ok=True)
            
            frames = []
            frame_number = 0
            extracted_count = 0
            
            while cap.isOpened() and extracted_count < max_frames:
                ret, frame_img = cap.read()
                
                if not ret:
                    break
                
                # Calculate current timestamp
                current_timestamp = frame_number / fps if fps > 0 else 0
                
                # Check if we should extract this frame based on interval
                if extracted_count == 0 or current_timestamp >= extracted_count * interval_seconds:
                    # Save frame to file
                    frame_filename = f"frame_{extracted_count:04d}_{current_timestamp:.2f}s.jpg"
                    frame_path = video_frame_dir / frame_filename
                    
                    cv2.imwrite(str(frame_path), frame_img)
                    
                    # Create Frame object
                    frame = Frame(
                        timestamp=current_timestamp,
                        image_path=str(frame_path),
                        frame_number=frame_number
                    )
                    
                    frames.append(frame)
                    extracted_count += 1
                    
                    logger.debug(f"Extracted frame {extracted_count}/{max_frames} at {current_timestamp:.2f}s")
                
                frame_number += 1
            
            logger.info(f"Extracted {len(frames)} frames from video {video_id}")
            return frames
            
        finally:
            cap.release()
    
    def extract_frame_at_timestamp(
        self,
        video_path: str,
        video_id: str,
        timestamp: float
    ) -> Frame:
        """
        Extract a single frame at a specific timestamp.
        
        Args:
            video_path: Path to the video file
            video_id: Unique identifier for the video
            timestamp: Timestamp in seconds to extract frame from
            
        Returns:
            Frame object with extracted frame information
            
        Raises:
            ValueError: If video cannot be opened, timestamp is invalid, or frame cannot be extracted
        """
        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")
        
        if timestamp < 0:
            raise ValueError(f"Timestamp must be non-negative, got {timestamp}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            if timestamp > duration:
                raise ValueError(f"Timestamp {timestamp}s exceeds video duration {duration:.2f}s")
            
            # Calculate frame number for the timestamp
            target_frame_number = int(timestamp * fps)
            
            # Seek to the target frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_number)
            
            ret, frame_img = cap.read()
            
            if not ret:
                raise ValueError(f"Failed to extract frame at timestamp {timestamp}s")
            
            # Create directory for this video's frames
            video_frame_dir = Path(self.frame_storage_path) / video_id
            video_frame_dir.mkdir(parents=True, exist_ok=True)
            
            # Save frame to file
            frame_filename = f"frame_ts_{timestamp:.2f}s.jpg"
            frame_path = video_frame_dir / frame_filename
            
            cv2.imwrite(str(frame_path), frame_img)
            
            # Create Frame object
            frame = Frame(
                timestamp=timestamp,
                image_path=str(frame_path),
                frame_number=target_frame_number
            )
            
            logger.info(f"Extracted frame at timestamp {timestamp}s from video {video_id}")
            return frame
            
        finally:
            cap.release()
    
    def encode_frame_to_base64(self, frame_path: str) -> str:
        """
        Encode a frame image to base64 string.
        
        Args:
            frame_path: Path to the frame image file
            
        Returns:
            Base64-encoded string of the image
            
        Raises:
            ValueError: If frame file cannot be read
        """
        if not os.path.exists(frame_path):
            raise ValueError(f"Frame file not found: {frame_path}")
        
        with open(frame_path, "rb") as f:
            image_data = f.read()
            return base64.b64encode(image_data).decode("utf-8")
