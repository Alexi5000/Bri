# Video Processing Tools

This directory contains video processing tools for the BRI video agent.

## FrameExtractor

The `FrameExtractor` class provides functionality to extract frames from videos using OpenCV.

### Features

- **Extract frames at regular intervals**: Extract frames from a video at configurable time intervals
- **Extract frame at specific timestamp**: Get a single frame at an exact timestamp
- **Get video metadata**: Retrieve video properties (duration, fps, resolution, codec, file size)
- **Adaptive interval calculation**: Automatically adjusts extraction interval based on video length to stay within max frame limits
- **Organized storage**: Stores extracted frames in organized directory structure by video ID

### Usage

```python
from tools.frame_extractor import FrameExtractor

# Initialize
extractor = FrameExtractor()

# Get video metadata
metadata = extractor.get_video_metadata("path/to/video.mp4")
print(f"Duration: {metadata.duration}s, FPS: {metadata.fps}")

# Extract frames at regular intervals
frames = extractor.extract_frames(
    video_path="path/to/video.mp4",
    video_id="unique_video_id",
    interval_seconds=2.0,  # Extract every 2 seconds
    max_frames=100  # Maximum 100 frames
)

# Extract a specific frame at timestamp
frame = extractor.extract_frame_at_timestamp(
    video_path="path/to/video.mp4",
    video_id="unique_video_id",
    timestamp=5.0  # Extract frame at 5 seconds
)

# Encode frame to base64 (useful for API responses)
base64_image = extractor.encode_frame_to_base64(frame.image_path)
```

### Configuration

The FrameExtractor uses configuration from `config.py`:

- `FRAME_STORAGE_PATH`: Directory to store extracted frames (default: `data/frames`)
- `MAX_FRAMES_PER_VIDEO`: Maximum frames to extract per video (default: 100)
- `FRAME_EXTRACTION_INTERVAL`: Default interval between frames in seconds (default: 2.0)

### Adaptive Interval

For longer videos, the extractor automatically calculates an adaptive interval to ensure the total number of extracted frames doesn't exceed `max_frames`. This prevents excessive storage usage and processing time for long videos.

Example:
- 30-second video with max_frames=100: Uses 1.0s interval (minimum)
- 600-second video with max_frames=100: Uses 6.0s interval (adaptive)

### Storage Structure

Extracted frames are stored in the following structure:

```
data/frames/
└── {video_id}/
    ├── frame_0000_0.00s.jpg
    ├── frame_0001_2.00s.jpg
    ├── frame_0002_4.00s.jpg
    └── ...
```

### Testing

Run the test script to verify functionality:

```bash
python scripts/test_frame_extractor.py
```

Note: Place a test video at `data/videos/test_video.mp4` to test extraction functionality.
