"""Media utilities for frame thumbnail generation and processing."""

import logging
import os
from typing import Optional, Tuple
from PIL import Image
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class MediaError(Exception):
    """Custom exception for media processing errors."""
    pass


class MediaUtils:
    """Utilities for media processing including thumbnail generation.
    
    Provides methods to:
    - Generate thumbnails from frames
    - Convert images to base64
    - Resize images while maintaining aspect ratio
    """
    
    # Default thumbnail dimensions
    DEFAULT_THUMBNAIL_WIDTH = 320
    DEFAULT_THUMBNAIL_HEIGHT = 180
    
    @staticmethod
    def generate_thumbnail(
        image_path: str,
        output_path: Optional[str] = None,
        max_width: int = DEFAULT_THUMBNAIL_WIDTH,
        max_height: int = DEFAULT_THUMBNAIL_HEIGHT,
        quality: int = 85
    ) -> str:
        """
        Generate a thumbnail from an image file.
        
        Args:
            image_path: Path to source image
            output_path: Path for thumbnail output. If None, generates path automatically.
            max_width: Maximum thumbnail width in pixels
            max_height: Maximum thumbnail height in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            Path to generated thumbnail
            
        Raises:
            MediaError: If thumbnail generation fails
            
        Example:
            thumbnail_path = MediaUtils.generate_thumbnail(
                "data/frames/frame_001.jpg",
                max_width=320,
                max_height=180
            )
        """
        try:
            if not os.path.exists(image_path):
                raise MediaError(f"Image file not found: {image_path}")
            
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Calculate thumbnail size maintaining aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Generate output path if not provided
                if output_path is None:
                    base_dir = os.path.dirname(image_path)
                    base_name = os.path.basename(image_path)
                    name, ext = os.path.splitext(base_name)
                    output_path = os.path.join(base_dir, f"{name}_thumb{ext}")
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save thumbnail
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                logger.debug(f"Generated thumbnail: {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
            raise MediaError(f"Thumbnail generation failed: {e}")
    
    @staticmethod
    def generate_thumbnail_base64(
        image_path: str,
        max_width: int = DEFAULT_THUMBNAIL_WIDTH,
        max_height: int = DEFAULT_THUMBNAIL_HEIGHT,
        quality: int = 85
    ) -> str:
        """
        Generate a thumbnail and return as base64-encoded string.
        
        Useful for embedding thumbnails directly in responses without
        saving to disk.
        
        Args:
            image_path: Path to source image
            max_width: Maximum thumbnail width in pixels
            max_height: Maximum thumbnail height in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            Base64-encoded thumbnail image
            
        Raises:
            MediaError: If thumbnail generation fails
            
        Example:
            base64_thumb = MediaUtils.generate_thumbnail_base64(
                "data/frames/frame_001.jpg"
            )
        """
        try:
            if not os.path.exists(image_path):
                raise MediaError(f"Image file not found: {image_path}")
            
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Calculate thumbnail size maintaining aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save to bytes buffer
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                buffer.seek(0)
                
                # Encode to base64
                base64_data = base64.b64encode(buffer.read()).decode('utf-8')
                
                logger.debug(f"Generated base64 thumbnail for {image_path}")
                return base64_data
                
        except Exception as e:
            logger.error(f"Failed to generate base64 thumbnail for {image_path}: {e}")
            raise MediaError(f"Base64 thumbnail generation failed: {e}")
    
    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """
        Convert an image file to base64-encoded string.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64-encoded image
            
        Raises:
            MediaError: If conversion fails
        """
        try:
            if not os.path.exists(image_path):
                raise MediaError(f"Image file not found: {image_path}")
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
            logger.debug(f"Converted image to base64: {image_path}")
            return base64_data
            
        except Exception as e:
            logger.error(f"Failed to convert image to base64: {e}")
            raise MediaError(f"Base64 conversion failed: {e}")
    
    @staticmethod
    def get_image_dimensions(image_path: str) -> Tuple[int, int]:
        """
        Get the dimensions of an image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (width, height) in pixels
            
        Raises:
            MediaError: If reading dimensions fails
        """
        try:
            if not os.path.exists(image_path):
                raise MediaError(f"Image file not found: {image_path}")
            
            with Image.open(image_path) as img:
                return img.size
                
        except Exception as e:
            logger.error(f"Failed to get image dimensions: {e}")
            raise MediaError(f"Failed to read image dimensions: {e}")
    
    @staticmethod
    def batch_generate_thumbnails(
        image_paths: list[str],
        max_width: int = DEFAULT_THUMBNAIL_WIDTH,
        max_height: int = DEFAULT_THUMBNAIL_HEIGHT,
        quality: int = 85
    ) -> list[str]:
        """
        Generate thumbnails for multiple images.
        
        Args:
            image_paths: List of paths to source images
            max_width: Maximum thumbnail width in pixels
            max_height: Maximum thumbnail height in pixels
            quality: JPEG quality (1-100)
            
        Returns:
            List of paths to generated thumbnails
            
        Example:
            frame_paths = ["frame1.jpg", "frame2.jpg", "frame3.jpg"]
            thumbnails = MediaUtils.batch_generate_thumbnails(frame_paths)
        """
        thumbnails = []
        
        for image_path in image_paths:
            try:
                thumbnail_path = MediaUtils.generate_thumbnail(
                    image_path,
                    max_width=max_width,
                    max_height=max_height,
                    quality=quality
                )
                thumbnails.append(thumbnail_path)
            except MediaError as e:
                logger.warning(f"Skipping thumbnail generation for {image_path}: {e}")
                # Add original path as fallback
                thumbnails.append(image_path)
        
        logger.info(f"Generated {len(thumbnails)} thumbnails from {len(image_paths)} images")
        return thumbnails
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Format a timestamp in seconds to human-readable format.
        
        Args:
            seconds: Timestamp in seconds
            
        Returns:
            Formatted timestamp string (MM:SS or HH:MM:SS)
            
        Example:
            >>> MediaUtils.format_timestamp(125.5)
            '02:05'
            >>> MediaUtils.format_timestamp(3725.0)
            '01:02:05'
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """
        Parse a timestamp string to seconds.
        
        Supports formats: "MM:SS", "HH:MM:SS", "12.5s", "125"
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            Timestamp in seconds
            
        Raises:
            MediaError: If parsing fails
            
        Example:
            >>> MediaUtils.parse_timestamp("02:05")
            125.0
            >>> MediaUtils.parse_timestamp("12.5s")
            12.5
        """
        try:
            timestamp_str = timestamp_str.strip()
            
            # Handle "12.5s" format
            if timestamp_str.endswith('s'):
                return float(timestamp_str[:-1])
            
            # Handle "MM:SS" or "HH:MM:SS" format
            if ':' in timestamp_str:
                parts = timestamp_str.split(':')
                if len(parts) == 2:
                    # MM:SS
                    minutes, seconds = map(int, parts)
                    return minutes * 60 + seconds
                elif len(parts) == 3:
                    # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    return hours * 3600 + minutes * 60 + seconds
            
            # Handle plain number (seconds)
            return float(timestamp_str)
            
        except Exception as e:
            raise MediaError(f"Failed to parse timestamp '{timestamp_str}': {e}")
