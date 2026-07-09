# Video Upload Functionality - Usage Guide

## For Users

### How to Upload a Video

1. **Start the Application**
   ```bash
   streamlit run app.py
   ```

2. **Navigate to Welcome Screen**
   - The welcome screen appears automatically on first load
   - Or click "🏠 Home" in the sidebar

3. **Upload Your Video**
   - Drag and drop a video file onto the upload area
   - Or click "Browse files" to select a video
   - Supported formats: MP4, AVI, MOV, MKV
   - Maximum size: 500MB

4. **Wait for Confirmation**
   - You'll see a friendly message: "✨ Perfect! I've got **your-video.mp4** saved and ready to go!"
   - File details will be displayed (size, duration, type)

5. **View in Library**
   - Click "📚 View in Library" button
   - Or navigate using the sidebar

### Supported Formats

✅ **MP4** - Most common format
✅ **AVI** - Windows video format
✅ **MOV** - QuickTime format
✅ **MKV** - Matroska format

### File Size Limits

- **Maximum**: 500MB
- **Recommended**: Under 100MB for faster processing
- **Tip**: Shorter videos process faster!

### Common Error Messages

**"Oops! I can only work with MP4, AVI, MOV, or MKV files..."**
- Your file format is not supported
- Convert your video to one of the supported formats

**"This video is a bit too big for me right now. Can you try one under 500MB?"**
- Your file exceeds the 500MB limit
- Try compressing the video or uploading a shorter clip

**"Hmm, something went wrong with the upload. Mind giving it another shot?"**
- Generic upload error
- Try uploading again
- Check your internet connection
- Ensure the file isn't corrupted

## For Developers

### Programmatic Upload

```python
from storage.file_store import get_file_store
from storage.database import insert_video
import uuid
import cv2

# Initialize file store
file_store = get_file_store()

# Validate file
is_valid, error_msg = file_store.validate_video_file(
    filename="my_video.mp4",
    file_size=50 * 1024 * 1024  # 50MB
)

if not is_valid:
    print(f"Validation failed: {error_msg}")
    exit(1)

# Generate video ID
video_id = str(uuid.uuid4())

# Save video
with open("path/to/video.mp4", 'rb') as f:
    video_id, file_path = file_store.save_uploaded_video(
        f,
        "my_video.mp4",
        video_id
    )

# Extract metadata
cap = cv2.VideoCapture(file_path)
duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
cap.release()

# Create database record
insert_video(
    video_id=video_id,
    filename="my_video.mp4",
    file_path=file_path,
    duration=duration
)

print(f"Video uploaded successfully: {video_id}")
```

### Retrieving Videos

```python
from storage.database import get_video, get_all_videos

# Get specific video
video = get_video("video-id-here")
if video:
    print(f"Filename: {video['filename']}")
    print(f"Duration: {video['duration']}s")
    print(f"Status: {video['processing_status']}")

# Get all videos
videos = get_all_videos()
for video in videos:
    print(f"{video['filename']} - {video['duration']}s")
```

### Updating Video Status

```python
from storage.database import update_video_status

# Update processing status
update_video_status("video-id-here", "processing")
# Later...
update_video_status("video-id-here", "complete")
```

### Deleting Videos

```python
from storage.file_store import get_file_store
from storage.database import delete_video as db_delete_video

video_id = "video-id-here"

# Delete from database
db_delete_video(video_id)

# Delete from file system
file_store = get_file_store()
file_store.delete_video(video_id)
```

### Custom Validation

```python
from storage.file_store import FileStore

# Create custom file store with different limits
file_store = FileStore()

# Override max file size (in bytes)
FileStore.MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024  # 1GB

# Add custom format
FileStore.SUPPORTED_VIDEO_FORMATS.add('.webm')

# Validate
is_valid, error = file_store.validate_video_file("video.webm", 500_000_000)
```

### Error Handling

```python
from services.error_handler import ErrorHandler

try:
    # Upload code here
    pass
except Exception as e:
    # Get friendly error message
    error_msg = ErrorHandler.format_error_for_user(
        e,
        context={'upload': True, 'filename': 'video.mp4'}
    )
    print(f"Error: {error_msg}")
```

### Configuration

Set these in your `.env` file:

```env
# Storage paths
VIDEO_STORAGE_PATH=data/videos
FRAME_STORAGE_PATH=data/frames
CACHE_STORAGE_PATH=data/cache

# Database
DATABASE_PATH=data/bri.db

# Processing limits
MAX_FRAMES_PER_VIDEO=100
FRAME_EXTRACTION_INTERVAL=2.0
```

### Testing

Run the test suite:

```bash
# Unit and integration tests
python scripts/test_video_upload.py

# Complete flow test
python scripts/test_upload_integration.py
```

### File Structure

After upload, files are organized as:

```
data/
├── videos/
│   └── {video_id}.mp4          # Uploaded video
├── frames/
│   └── {video_id}/             # Extracted frames (Task 18)
│       ├── frame_0001_0.00.jpg
│       └── frame_0002_2.00.jpg
├── cache/
│   └── {video_id}/             # Cached processing results
└── bri.db                      # SQLite database
```

### Database Schema

```sql
CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    duration REAL NOT NULL,
    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',
    thumbnail_path TEXT,
    CHECK (processing_status IN ('pending', 'processing', 'complete', 'error'))
);
```

### API Reference

#### FileStore Class

**Methods**:
- `validate_video_file(filename, file_size)` - Validate format and size
- `save_uploaded_video(file_data, filename, video_id)` - Save video
- `get_video_path(video_id, extension)` - Get path to video
- `video_exists(video_id)` - Check if video exists
- `delete_video(video_id)` - Delete video and assets
- `get_frame_directory(video_id)` - Get frames directory
- `format_file_size(size_bytes)` - Format size for display

**Constants**:
- `SUPPORTED_VIDEO_FORMATS` - Set of supported extensions
- `MAX_FILE_SIZE_BYTES` - Maximum file size (500MB)

#### Database Functions

- `insert_video(video_id, filename, file_path, duration, thumbnail_path)` - Insert video
- `get_video(video_id)` - Get video by ID
- `get_all_videos()` - Get all videos
- `update_video_status(video_id, status)` - Update status
- `delete_video(video_id)` - Delete video record

### Troubleshooting

**Problem**: "Module not found" errors
**Solution**: Ensure you're in the project root and virtual environment is activated

**Problem**: Database errors on startup
**Solution**: Run `python scripts/init_db.py` to initialize the database

**Problem**: Videos not appearing in library
**Solution**: Check that database is initialized and videos table exists

**Problem**: Upload fails silently
**Solution**: Check logs for errors, ensure directories have write permissions

**Problem**: Can't extract video duration
**Solution**: Ensure OpenCV is installed: `pip install opencv-python`

### Best Practices

1. **Always validate before saving**
   ```python
   is_valid, error = file_store.validate_video_file(filename, size)
   if not is_valid:
       return error
   ```

2. **Use context managers for file operations**
   ```python
   with open(video_path, 'rb') as f:
       video_id, path = file_store.save_uploaded_video(f, filename)
   ```

3. **Clean up on errors**
   ```python
   try:
       insert_video(...)
   except Exception as e:
       file_store.delete_video(video_id)  # Clean up file
       raise
   ```

4. **Log important operations**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info(f"Uploaded video: {video_id}")
   ```

5. **Use friendly error messages**
   ```python
   error_msg = ErrorHandler.format_error_for_user(e, context)
   ```

### Next Steps

After uploading a video:
1. Video processing (Task 18) will extract frames
2. Captions will be generated for frames
3. Audio will be transcribed
4. Objects will be detected
5. You can then chat about the video content

---

For more information, see:
- `docs/task_17_video_upload.md` - Implementation details
- `docs/task_17_summary.md` - Task completion summary
- `storage/file_store.py` - Source code
- `storage/database.py` - Database operations
