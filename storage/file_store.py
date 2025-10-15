"""File storage utilities for videos and extracted assets."""

import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import Optional, BinaryIO
from config import Config

logger = logging.getLogger(__name__)


class FileStoreError(Exception):
    """Custom exception for file storage errors."""
    pass


class FileStore:
    """
    Manages file system operations for videos, frames, and cached data.
    
    Handles video uploads, frame storage, and file organization with
    proper error handling and validation.
    """
    
    # Supported video formats
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv'}
    
    # Maximum file size (500MB)
    MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024
    
    def __init__(
        self,
        video_path: Optional[str] = None,
        frame_path: Optional[str] = None,
        cache_path: Optional[str] = None
    ):
        """
        Initialize file store with storage paths.
        
        Args:
            video_path: Path for video storage (uses Config if not provided)
            frame_path: Path for frame storage (uses Config if not provided)
            cache_path: Path for cache storage (uses Config if not provided)
        """
        self.video_path = Path(video_path or Config.VIDEO_STORAGE_PATH)
        self.frame_path = Path(frame_path or Config.FRAME_STORAGE_PATH)
        self.cache_path = Path(cache_path or Config.CACHE_STORAGE_PATH)
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for path in [self.video_path, self.frame_path, self.cache_path]:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")
    
    def validate_video_file(
        self,
        filename: str,
        file_size: int
    ) -> tuple[bool, Optional[str]]:
        """
        Validate video file format and size.
        
        Args:
            filename: Name of the video file
            file_size: Size of the file in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.SUPPORTED_VIDEO_FORMATS:
            supported = ', '.join(self.SUPPORTED_VIDEO_FORMATS)
            return False, f"Unsupported format. Please use: {supported}"
        
        # Check file size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            max_size_mb = self.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            return False, f"File too large. Maximum size is {max_size_mb:.0f}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, None
    
    def save_uploaded_video(
        self,
        file_data: BinaryIO,
        original_filename: str,
        video_id: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Save uploaded video file to storage.
        
        Args:
            file_data: Binary file data stream
            original_filename: Original filename from upload
            video_id: Optional video ID (generates new UUID if not provided)
            
        Returns:
            Tuple of (video_id, file_path)
            
        Raises:
            FileStoreError: If save operation fails
        """
        try:
            # Generate video ID if not provided
            if video_id is None:
                video_id = str(uuid.uuid4())
            
            # Get file extension
            file_ext = Path(original_filename).suffix.lower()
            
            # Create filename: video_id + extension
            filename = f"{video_id}{file_ext}"
            file_path = self.video_path / filename
            
            # Save file
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)
            
            logger.info(f"Saved video: {filename} (ID: {video_id})")
            
            return video_id, str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save video: {e}")
            raise FileStoreError(f"Failed to save video: {e}")
    
    def get_video_path(self, video_id: str, extension: str = '.mp4') -> Path:
        """
        Get the file path for a video by ID.
        
        Args:
            video_id: Video identifier
            extension: File extension (default: .mp4)
            
        Returns:
            Path to video file
        """
        return self.video_path / f"{video_id}{extension}"
    
    def video_exists(self, video_id: str) -> bool:
        """
        Check if a video file exists.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if video exists, False otherwise
        """
        # Check for any supported format
        for ext in self.SUPPORTED_VIDEO_FORMATS:
            if (self.video_path / f"{video_id}{ext}").exists():
                return True
        return False
    
    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video file and associated assets.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            deleted = False
            
            # Delete video file (check all supported formats)
            for ext in self.SUPPORTED_VIDEO_FORMATS:
                video_file = self.video_path / f"{video_id}{ext}"
                if video_file.exists():
                    video_file.unlink()
                    logger.info(f"Deleted video: {video_file}")
                    deleted = True
            
            # Delete associated frames directory
            frames_dir = self.frame_path / video_id
            if frames_dir.exists():
                shutil.rmtree(frames_dir)
                logger.info(f"Deleted frames directory: {frames_dir}")
            
            # Delete cache directory
            cache_dir = self.cache_path / video_id
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                logger.info(f"Deleted cache directory: {cache_dir}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete video {video_id}: {e}")
            return False
    
    def get_frame_directory(self, video_id: str) -> Path:
        """
        Get or create the directory for storing video frames.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Path to frames directory
        """
        frames_dir = self.frame_path / video_id
        frames_dir.mkdir(parents=True, exist_ok=True)
        return frames_dir
    
    def save_frame(
        self,
        video_id: str,
        frame_data: bytes,
        timestamp: float,
        frame_number: int
    ) -> str:
        """
        Save an extracted video frame.
        
        Args:
            video_id: Video identifier
            frame_data: Frame image data
            timestamp: Frame timestamp in seconds
            frame_number: Frame number
            
        Returns:
            Path to saved frame
            
        Raises:
            FileStoreError: If save operation fails
        """
        try:
            frames_dir = self.get_frame_directory(video_id)
            
            # Create filename: frame_NNNN_timestamp.jpg
            filename = f"frame_{frame_number:04d}_{timestamp:.2f}.jpg"
            frame_path = frames_dir / filename
            
            # Save frame
            with open(frame_path, 'wb') as f:
                f.write(frame_data)
            
            logger.debug(f"Saved frame: {filename}")
            
            return str(frame_path)
            
        except Exception as e:
            logger.error(f"Failed to save frame: {e}")
            raise FileStoreError(f"Failed to save frame: {e}")
    
    def get_cache_directory(self, video_id: str) -> Path:
        """
        Get or create the cache directory for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Path to cache directory
        """
        cache_dir = self.cache_path / video_id
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Failed to get file size: {e}")
            return 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., "15.3 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


# Global file store instance
_file_store_instance: Optional[FileStore] = None


def get_file_store() -> FileStore:
    """
    Get or create global file store instance.
    
    Returns:
        FileStore instance
    """
    global _file_store_instance
    if _file_store_instance is None:
        _file_store_instance = FileStore()
    return _file_store_instance
