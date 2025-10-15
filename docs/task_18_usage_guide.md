# Task 18: Video Processing Workflow - Usage Guide

## Quick Start

### 1. Start the MCP Server

The video processing workflow requires the MCP server to be running:

```bash
# In a separate terminal
python mcp_server/main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000
```

### 2. Start the Streamlit UI

```bash
# In your main terminal
streamlit run app.py
```

### 3. Upload and Process a Video

1. Navigate to the welcome screen
2. Upload a video file (MP4, AVI, MOV, or MKV)
3. Watch the processing workflow automatically start:
   - Progress bar shows completion percentage
   - Status messages update in real-time
   - Friendly messages guide you through each step

## Testing the Implementation

### Run the Test Suite

```bash
python scripts/test_video_processing.py
```

Expected output:
```
======================================================================
VIDEO PROCESSING WORKFLOW TEST SUITE (Task 18)
======================================================================

✅ PASS: Initialization
✅ PASS: Friendly Step Names
✅ PASS: Processing Messages
✅ PASS: MCP Server Health
✅ PASS: Processing Status
✅ PASS: Error Handling
✅ PASS: Video Processing with Callback

Total: 7/7 tests passed
🎉 All tests passed!
```

### Manual Testing Scenarios

#### Scenario 1: Successful Processing
1. Ensure MCP server is running
2. Upload a video
3. Observe:
   - Progress bar advances smoothly
   - Status messages change for each step
   - Success message appears when complete
   - Processing summary shows completed tasks

#### Scenario 2: MCP Server Not Running
1. Stop the MCP server
2. Upload a video
3. Observe:
   - Warning message about server not running
   - Instructions to start the server
   - Video is still saved for later processing

#### Scenario 3: Processing Error
1. Upload an invalid or corrupted video
2. Observe:
   - Friendly error message
   - Explanation of what went wrong
   - Option to retry later

## Processing Steps

The workflow processes videos through four steps:

### 1. Extract Frames (🎞️)
- Extracts key frames from the video
- Messages:
  - "Taking snapshots of your video... 📸"
  - "Capturing the best moments... ✨"
  - "Almost done with frame extraction! 🎬"

### 2. Caption Frames (🖼️)
- Generates descriptions for each frame
- Messages:
  - "Looking at what's happening in each scene... 👀"
  - "Understanding the visual content... 🖼️"
  - "Nearly finished describing everything! 💭"

### 3. Transcribe Audio (🎤)
- Transcribes audio with timestamps
- Messages:
  - "Listening to the audio... 🎧"
  - "Writing down what I hear... ✍️"
  - "Almost done with transcription! 🎤"

### 4. Detect Objects (🔍)
- Identifies objects and people
- Messages:
  - "Spotting interesting things in your video... 🔍"
  - "Identifying objects and people... 👥"
  - "Finishing up object detection! ✅"

## Status Messages

### Database Statuses
- **pending**: Video uploaded, waiting to process
- **processing**: Currently being analyzed
- **complete**: Ready for queries
- **error**: Processing failed

### UI Messages
- **pending**: "⏳ Waiting to start processing..."
- **processing**: "🔄 Processing your video..."
- **complete**: "✅ Ready to chat!"
- **error**: "❌ Processing encountered an issue"

## Programmatic Usage

### Basic Processing

```python
from services.video_processor import get_video_processor

processor = get_video_processor()

# Check server health
if processor.check_mcp_server_health():
    # Process video
    result = await processor.process_video(video_id)
    print(f"Status: {result['status']}")
else:
    print("MCP server not available")
```

### With Progress Callback

```python
def on_progress(step_name, progress, message):
    print(f"[{progress:.0f}%] {step_name}")
    print(f"  {message}")

result = await processor.process_video(video_id, on_progress)
```

### Check Processing Status

```python
status = processor.get_processing_status(video_id)
print(status["message"])
```

## Troubleshooting

### MCP Server Connection Issues

**Problem**: "Could not connect to processing server"

**Solution**:
1. Check if MCP server is running: `http://localhost:8000/health`
2. Verify port 8000 is not in use by another application
3. Check firewall settings
4. Review MCP server logs for errors

### Processing Timeout

**Problem**: "Processing took too long"

**Solution**:
1. Try with a shorter video (< 5 minutes recommended)
2. Check MCP server logs for performance issues
3. Ensure sufficient system resources (RAM, CPU)
4. Consider increasing timeout in `video_processor.py`

### Partial Processing Success

**Problem**: Some tools succeed, others fail

**Solution**:
1. Check processing summary to see which tools failed
2. Review MCP server logs for specific tool errors
3. Verify all required models are downloaded
4. Check system resources (GPU for object detection)

### Database Status Not Updating

**Problem**: Status stuck on "processing"

**Solution**:
1. Check database connection
2. Verify database schema is initialized
3. Review application logs for database errors
4. Manually update status if needed:
   ```python
   from storage.database import update_video_status
   update_video_status(video_id, "complete")
   ```

## Configuration

### Environment Variables

```bash
# .env file
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
```

### Processing Settings

```python
# config.py
MAX_FRAMES_PER_VIDEO = 100
FRAME_EXTRACTION_INTERVAL = 2.0
CACHE_TTL_HOURS = 24
```

## Integration with Other Tasks

### Task 17: Video Upload
- Processing automatically triggered after successful upload
- Upload flow seamlessly transitions to processing

### Task 19: Video Library
- Library will show processing status for each video
- Users can retry processing from library view

### Task 20: Chat Interface
- Chat only enabled for videos with status "complete"
- Processing status displayed if video not ready

## Performance Tips

1. **Use Caching**: MCP server caches results for 24 hours
2. **Batch Processing**: Process multiple videos by calling MCP server directly
3. **Monitor Resources**: Watch CPU/GPU usage during processing
4. **Optimize Videos**: Shorter videos process faster
5. **Check Health**: Always verify MCP server health before processing

## Next Steps

After implementing Task 18, you can:

1. **Task 19**: Build video library view to show all processed videos
2. **Task 20**: Implement chat interface to query processed videos
3. **Task 21**: Add video player with timestamp navigation
4. **Task 22**: Create conversation history panel

## Support

For issues or questions:
1. Check the test suite output
2. Review MCP server logs
3. Check application logs
4. Verify all dependencies are installed
5. Ensure database is initialized

## Summary

Task 18 provides a complete video processing workflow with:
- ✅ Automatic processing on upload
- ✅ Real-time progress tracking
- ✅ Friendly status messages
- ✅ Comprehensive error handling
- ✅ Database status management
- ✅ MCP server integration

The implementation is production-ready and fully tested!
