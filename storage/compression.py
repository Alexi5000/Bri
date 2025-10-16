"""Data compression utilities for BRI video agent.

Features:
- Compress large JSON blobs in database
- Compress frame images (WebP format)
- Compress API responses (gzip)
- Implement deduplication for similar frames
- Balance compression ratio vs CPU cost
"""

import gzip
import json
import zlib
import io
from typing import Any, Optional, Dict, Tuple
from pathlib import Path
from PIL import Image
from utils.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class CompressionLevel:
    """Compression level constants."""
    NONE = 0
    FAST = 1  # Low compression, fast
    BALANCED = 6  # Medium compression, balanced
    BEST = 9  # High compression, slow


class JSONCompressor:
    """Compress and decompress JSON data.
    
    Uses zlib compression for JSON blobs stored in database.
    Balances compression ratio vs CPU cost.
    """
    
    def __init__(self, compression_level: int = CompressionLevel.BALANCED):
        """Initialize JSON compressor.
        
        Args:
            compression_level: Compression level (0-9)
        """
        self.compression_level = compression_level
        logger.info(f"JSON compressor initialized (level: {compression_level})")
    
    def compress(self, data: Dict[str, Any]) -> bytes:
        """Compress JSON data.
        
        Args:
            data: Dictionary to compress
            
        Returns:
            Compressed bytes
        """
        # Serialize to JSON
        json_str = json.dumps(data, separators=(',', ':'))  # Compact format
        json_bytes = json_str.encode('utf-8')
        
        # Compress
        compressed = zlib.compress(json_bytes, level=self.compression_level)
        
        # Log compression ratio
        original_size = len(json_bytes)
        compressed_size = len(compressed)
        ratio = (1 - compressed_size / original_size) * 100
        
        logger.debug(
            f"JSON compressed: {original_size} → {compressed_size} bytes "
            f"({ratio:.1f}% reduction)"
        )
        
        return compressed
    
    def decompress(self, compressed_data: bytes) -> Dict[str, Any]:
        """Decompress JSON data.
        
        Args:
            compressed_data: Compressed bytes
            
        Returns:
            Decompressed dictionary
        """
        # Decompress
        json_bytes = zlib.decompress(compressed_data)
        
        # Parse JSON
        json_str = json_bytes.decode('utf-8')
        data = json.loads(json_str)
        
        return data
    
    def should_compress(self, data: Dict[str, Any], threshold_bytes: int = 1024) -> bool:
        """Determine if data should be compressed.
        
        Small data may not benefit from compression due to overhead.
        
        Args:
            data: Dictionary to check
            threshold_bytes: Minimum size to compress
            
        Returns:
            True if data should be compressed
        """
        json_str = json.dumps(data)
        size = len(json_str.encode('utf-8'))
        return size >= threshold_bytes


class ImageCompressor:
    """Compress frame images to WebP format.
    
    WebP provides better compression than JPEG/PNG while maintaining quality.
    """
    
    def __init__(self, quality: int = 85, lossless: bool = False):
        """Initialize image compressor.
        
        Args:
            quality: Compression quality (0-100, higher = better quality)
            lossless: Use lossless compression
        """
        self.quality = quality
        self.lossless = lossless
        logger.info(
            f"Image compressor initialized "
            f"(quality: {quality}, lossless: {lossless})"
        )
    
    def compress_to_webp(
        self,
        input_path: str,
        output_path: Optional[str] = None
    ) -> Tuple[str, int, int]:
        """Compress image to WebP format.
        
        Args:
            input_path: Path to input image
            output_path: Path to output WebP file (auto-generated if None)
            
        Returns:
            Tuple of (output_path, original_size, compressed_size)
        """
        try:
            # Open image
            img = Image.open(input_path)
            
            # Get original size
            original_size = Path(input_path).stat().st_size
            
            # Generate output path if not provided
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.with_suffix('.webp'))
            
            # Save as WebP
            img.save(
                output_path,
                'WEBP',
                quality=self.quality,
                lossless=self.lossless
            )
            
            # Get compressed size
            compressed_size = Path(output_path).stat().st_size
            
            # Log compression ratio
            ratio = (1 - compressed_size / original_size) * 100
            logger.debug(
                f"Image compressed: {original_size} → {compressed_size} bytes "
                f"({ratio:.1f}% reduction)"
            )
            
            return output_path, original_size, compressed_size
            
        except Exception as e:
            logger.error(f"Failed to compress image {input_path}: {e}")
            raise
    
    def compress_to_bytes(self, input_path: str) -> bytes:
        """Compress image to WebP bytes.
        
        Args:
            input_path: Path to input image
            
        Returns:
            Compressed image bytes
        """
        try:
            img = Image.open(input_path)
            
            # Save to bytes buffer
            buffer = io.BytesIO()
            img.save(
                buffer,
                'WEBP',
                quality=self.quality,
                lossless=self.lossless
            )
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to compress image to bytes: {e}")
            raise
    
    def batch_compress(
        self,
        input_paths: list[str],
        output_dir: Optional[str] = None
    ) -> Dict[str, Tuple[str, int, int]]:
        """Compress multiple images in batch.
        
        Args:
            input_paths: List of input image paths
            output_dir: Output directory (uses input dir if None)
            
        Returns:
            Dictionary mapping input_path to (output_path, original_size, compressed_size)
        """
        results = {}
        total_original = 0
        total_compressed = 0
        
        for input_path in input_paths:
            try:
                # Generate output path
                if output_dir:
                    input_name = Path(input_path).stem
                    output_path = str(Path(output_dir) / f"{input_name}.webp")
                else:
                    output_path = None
                
                # Compress
                output_path, original_size, compressed_size = self.compress_to_webp(
                    input_path,
                    output_path
                )
                
                results[input_path] = (output_path, original_size, compressed_size)
                total_original += original_size
                total_compressed += compressed_size
                
            except Exception as e:
                logger.error(f"Failed to compress {input_path}: {e}")
        
        # Log batch results
        if total_original > 0:
            ratio = (1 - total_compressed / total_original) * 100
            logger.info(
                f"Batch compression complete: {len(results)} images, "
                f"{total_original} → {total_compressed} bytes ({ratio:.1f}% reduction)"
            )
        
        return results


class ResponseCompressor:
    """Compress API responses with gzip.
    
    Reduces network bandwidth for large responses.
    """
    
    def __init__(self, compression_level: int = CompressionLevel.BALANCED):
        """Initialize response compressor.
        
        Args:
            compression_level: Compression level (0-9)
        """
        self.compression_level = compression_level
        logger.info(f"Response compressor initialized (level: {compression_level})")
    
    def compress(self, data: str) -> bytes:
        """Compress response data with gzip.
        
        Args:
            data: Response string to compress
            
        Returns:
            Compressed bytes
        """
        data_bytes = data.encode('utf-8')
        compressed = gzip.compress(data_bytes, compresslevel=self.compression_level)
        
        # Log compression ratio
        original_size = len(data_bytes)
        compressed_size = len(compressed)
        ratio = (1 - compressed_size / original_size) * 100
        
        logger.debug(
            f"Response compressed: {original_size} → {compressed_size} bytes "
            f"({ratio:.1f}% reduction)"
        )
        
        return compressed
    
    def decompress(self, compressed_data: bytes) -> str:
        """Decompress gzip response data.
        
        Args:
            compressed_data: Compressed bytes
            
        Returns:
            Decompressed string
        """
        data_bytes = gzip.decompress(compressed_data)
        return data_bytes.decode('utf-8')
    
    def should_compress(self, data: str, threshold_bytes: int = 1024) -> bool:
        """Determine if response should be compressed.
        
        Args:
            data: Response string
            threshold_bytes: Minimum size to compress
            
        Returns:
            True if response should be compressed
        """
        size = len(data.encode('utf-8'))
        return size >= threshold_bytes


class FrameDeduplicator:
    """Deduplicate similar frames to save storage.
    
    Uses perceptual hashing to identify similar frames.
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        """Initialize frame deduplicator.
        
        Args:
            similarity_threshold: Similarity threshold (0-1, higher = more similar)
        """
        self.similarity_threshold = similarity_threshold
        self.frame_hashes: Dict[str, str] = {}  # video_id:timestamp -> hash
        logger.info(
            f"Frame deduplicator initialized "
            f"(threshold: {similarity_threshold})"
        )
    
    def compute_hash(self, image_path: str) -> str:
        """Compute perceptual hash of image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Perceptual hash string
        """
        try:
            # Open and resize image to 8x8
            img = Image.open(image_path)
            img = img.convert('L')  # Convert to grayscale
            img = img.resize((8, 8), Image.Resampling.LANCZOS)
            
            # Get pixel values
            pixels = list(img.getdata())
            
            # Compute average
            avg = sum(pixels) / len(pixels)
            
            # Create hash (1 if pixel > avg, 0 otherwise)
            hash_bits = ''.join(['1' if p > avg else '0' for p in pixels])
            
            return hash_bits
            
        except Exception as e:
            logger.error(f"Failed to compute hash for {image_path}: {e}")
            raise
    
    def is_duplicate(
        self,
        video_id: str,
        timestamp: float,
        image_path: str
    ) -> Tuple[bool, Optional[float]]:
        """Check if frame is a duplicate of an existing frame.
        
        Args:
            video_id: Video identifier
            timestamp: Frame timestamp
            image_path: Path to frame image
            
        Returns:
            Tuple of (is_duplicate, original_timestamp)
        """
        # Compute hash for new frame
        new_hash = self.compute_hash(image_path)
        
        # Check against existing frames for this video
        for key, existing_hash in self.frame_hashes.items():
            if not key.startswith(f"{video_id}:"):
                continue
            
            # Compute Hamming distance
            distance = sum(c1 != c2 for c1, c2 in zip(new_hash, existing_hash))
            similarity = 1 - (distance / len(new_hash))
            
            if similarity >= self.similarity_threshold:
                # Found duplicate
                original_timestamp = float(key.split(':')[1])
                logger.debug(
                    f"Duplicate frame detected: {timestamp}s similar to "
                    f"{original_timestamp}s (similarity: {similarity:.2f})"
                )
                return True, original_timestamp
        
        # Not a duplicate, store hash
        key = f"{video_id}:{timestamp}"
        self.frame_hashes[key] = new_hash
        
        return False, None
    
    def clear_video(self, video_id: str) -> None:
        """Clear hashes for a specific video.
        
        Args:
            video_id: Video identifier
        """
        keys_to_remove = [
            key for key in self.frame_hashes.keys()
            if key.startswith(f"{video_id}:")
        ]
        
        for key in keys_to_remove:
            del self.frame_hashes[key]
        
        logger.debug(f"Cleared {len(keys_to_remove)} frame hashes for video {video_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplicator statistics.
        
        Returns:
            Dictionary with stats
        """
        # Count frames per video
        video_counts = {}
        for key in self.frame_hashes.keys():
            video_id = key.split(':')[0]
            video_counts[video_id] = video_counts.get(video_id, 0) + 1
        
        return {
            "total_frames": len(self.frame_hashes),
            "videos": len(video_counts),
            "avg_frames_per_video": (
                sum(video_counts.values()) / len(video_counts)
                if video_counts else 0
            )
        }


class CompressionManager:
    """Unified compression manager for all data types.
    
    Provides a single interface for compressing JSON, images, and responses.
    """
    
    def __init__(
        self,
        json_level: int = CompressionLevel.BALANCED,
        image_quality: int = 85,
        response_level: int = CompressionLevel.BALANCED
    ):
        """Initialize compression manager.
        
        Args:
            json_level: JSON compression level
            image_quality: Image compression quality
            response_level: Response compression level
        """
        self.json_compressor = JSONCompressor(json_level)
        self.image_compressor = ImageCompressor(image_quality)
        self.response_compressor = ResponseCompressor(response_level)
        self.frame_deduplicator = FrameDeduplicator()
        
        logger.info("Compression manager initialized")
    
    def compress_json(self, data: Dict[str, Any]) -> bytes:
        """Compress JSON data."""
        return self.json_compressor.compress(data)
    
    def decompress_json(self, compressed_data: bytes) -> Dict[str, Any]:
        """Decompress JSON data."""
        return self.json_compressor.decompress(compressed_data)
    
    def compress_image(self, input_path: str, output_path: Optional[str] = None) -> Tuple[str, int, int]:
        """Compress image to WebP."""
        return self.image_compressor.compress_to_webp(input_path, output_path)
    
    def compress_response(self, data: str) -> bytes:
        """Compress API response."""
        return self.response_compressor.compress(data)
    
    def decompress_response(self, compressed_data: bytes) -> str:
        """Decompress API response."""
        return self.response_compressor.decompress(compressed_data)
    
    def check_frame_duplicate(
        self,
        video_id: str,
        timestamp: float,
        image_path: str
    ) -> Tuple[bool, Optional[float]]:
        """Check if frame is duplicate."""
        return self.frame_deduplicator.is_duplicate(video_id, timestamp, image_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive compression statistics.
        
        Returns:
            Dictionary with all compression stats
        """
        return {
            "frame_deduplication": self.frame_deduplicator.get_stats()
        }


# Global compression manager instance
_compression_manager: Optional[CompressionManager] = None


def get_compression_manager() -> CompressionManager:
    """Get or create global compression manager instance.
    
    Returns:
        CompressionManager instance
    """
    global _compression_manager
    if _compression_manager is None:
        _compression_manager = CompressionManager(
            json_level=CompressionLevel.BALANCED,
            image_quality=85,
            response_level=CompressionLevel.BALANCED
        )
    return _compression_manager
