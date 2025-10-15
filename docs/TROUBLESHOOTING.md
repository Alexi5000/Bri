# BRI Troubleshooting Guide

This guide helps you diagnose and resolve common issues with BRI.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Server Issues](#server-issues)
4. [Video Processing Issues](#video-processing-issues)
5. [Query & Response Issues](#query--response-issues)
6. [Performance Issues](#performance-issues)
7. [Database Issues](#database-issues)
8. [Cache Issues](#cache-issues)
9. [Error Messages Reference](#error-messages-reference)
10. [Diagnostic Tools](#diagnostic-tools)

## Installation Issues

### Python Version Errors

**Problem**: `SyntaxError` or compatibility errors during installation

**Solution**:
```bash
# Check Python version (must be 3.9+)
python --version

# If version is too old, install Python 3.9 or higher
# Then create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Dependency Installation Failures

**Problem**: `pip install` fails for specific packages

**Common Issues**:

1. **OpenCV Installation Fails**
   ```bash
   # Try installing system dependencies first (Linux)
   sudo apt-get install python3-opencv
   
   # Or use headless version
   pip install opencv-python-headless
   ```

2. **Whisper Installation Fails**
   ```bash
   # Install ffmpeg first
   # Mac: brew install ffmpeg
   # Linux: sudo apt-get install ffmpeg
   # Windows: Download from ffmpeg.org
   
   pip install openai-whisper
   ```

3. **PyTorch/Transformers Issues**
   ```bash
   # Install PyTorch first
   pip install torch torchvision torchaudio
   
   # Then install transformers
   pip install transformers
   ```

### Module Not Found Errors

**Problem**: `ModuleNotFoundError` when running the application

**Solution**:
```bash
# Ensure you're in the project root directory
cd bri-video-agent

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python scripts/validate_setup.py
```

## Configuration Issues

### Missing API Key

**Problem**: `GROQ_API_KEY is required` error

**Solution**:
```bash
# 1. Create .env file from example
cp .env.example .env

# 2. Edit .env and add your API key
# GROQ_API_KEY=your_actual_key_here

# 3. Get a key from https://console.groq.com if you don't have one

# 4. Verify the key is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key loaded:', bool(os.getenv('GROQ_API_KEY')))"
```

### Invalid Configuration Values

**Problem**: Application fails to start with configuration errors

**Solution**:
```bash
# Run configuration validation
python scripts/validate_setup.py

# Check for common issues:
# - Paths that don't exist
# - Invalid port numbers
# - Malformed URLs
# - Out-of-range numeric values

# Reset to defaults by copying from example
cp .env.example .env
# Then re-add your API key
```

### Environment Variables Not Loading

**Problem**: Configuration changes in `.env` not taking effect

**Solution**:
```bash
# 1. Verify .env file exists in project root
ls -la .env

# 2. Check file format (no spaces around =)
# Correct:   GROQ_API_KEY=abc123
# Incorrect: GROQ_API_KEY = abc123

# 3. Restart both servers after changes
# Stop with Ctrl+C, then restart

# 4. Verify variables are loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('GROQ_API_KEY', 'NOT LOADED'))"
```

## Server Issues

### MCP Server Won't Start

**Problem**: `python mcp_server/main.py` fails or exits immediately

**Diagnostic Steps**:
```bash
# 1. Check if port 8000 is already in use
# Linux/Mac:
lsof -i :8000
# Windows:
netstat -ano | findstr :8000

# 2. Try a different port
MCP_SERVER_PORT=8001 python mcp_server/main.py

# 3. Check for Python errors
python mcp_server/main.py 2>&1 | tee mcp_error.log

# 4. Verify dependencies
pip install fastapi uvicorn redis
```

**Common Causes**:
- Port already in use → Change port or kill existing process
- Missing dependencies → Run `pip install -r requirements.txt`
- Database not initialized → Run `python scripts/init_db.py`
- Redis connection fails → Set `REDIS_ENABLED=false` in `.env`

### Streamlit UI Won't Start

**Problem**: `streamlit run app.py` fails

**Diagnostic Steps**:
```bash
# 1. Check if port 8501 is in use
# Linux/Mac:
lsof -i :8501
# Windows:
netstat -ano | findstr :8501

# 2. Try a different port
streamlit run app.py --server.port 8502

# 3. Check Streamlit installation
streamlit --version

# 4. Verify app.py exists and is valid
python -m py_compile app.py
```

### Connection Refused Errors

**Problem**: UI can't connect to MCP server

**Solution**:
```bash
# 1. Verify MCP server is running
curl http://localhost:8000/health

# 2. Check server logs for errors
# Look for startup messages and error traces

# 3. Verify host/port configuration
# In .env:
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000

# 4. Test with explicit URL
curl http://127.0.0.1:8000/health

# 5. Check firewall settings
# Ensure localhost connections are allowed
```

## Video Processing Issues

### Video Upload Fails

**Problem**: Upload doesn't complete or shows error

**Diagnostic Steps**:
```bash
# 1. Check video format
ffprobe your_video.mp4

# 2. Verify file size
ls -lh your_video.mp4

# 3. Check storage path exists and is writable
ls -ld data/videos/
touch data/videos/test.txt && rm data/videos/test.txt

# 4. Check disk space
df -h
```

**Solutions**:
- **Unsupported format**: Convert to MP4 using ffmpeg
  ```bash
  ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
  ```
- **File too large**: Compress video or increase size limit
- **Permission denied**: Fix directory permissions
  ```bash
  chmod 755 data/videos/
  ```

### Processing Hangs or Takes Too Long

**Problem**: Video processing never completes

**Diagnostic Steps**:
```bash
# 1. Check MCP server logs for progress
# Look for tool execution messages

# 2. Monitor system resources
# Linux/Mac:
top
# Windows:
Task Manager

# 3. Check for specific tool failures
python scripts/test_frame_extractor.py
python scripts/test_image_captioner.py
python scripts/test_audio_transcriber.py
python scripts/test_object_detector.py
```

**Solutions**:
- **Long video**: Reduce `MAX_FRAMES_PER_VIDEO` in `.env`
- **Low memory**: Close other applications or increase `FRAME_EXTRACTION_INTERVAL`
- **Tool failure**: Check logs and disable problematic tools temporarily
- **Timeout**: Increase `TOOL_EXECUTION_TIMEOUT` in `.env`

### Frame Extraction Fails

**Problem**: "I had trouble extracting frames" error

**Diagnostic Steps**:
```bash
# Test frame extraction directly
python scripts/test_frame_extractor.py

# Check video codec
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 your_video.mp4

# Verify OpenCV installation
python -c "import cv2; print(cv2.__version__)"
```

**Solutions**:
- **Codec not supported**: Re-encode video
  ```bash
  ffmpeg -i input.mp4 -c:v libx264 -preset fast output.mp4
  ```
- **Corrupted video**: Try a different video file
- **OpenCV issue**: Reinstall opencv-python
  ```bash
  pip uninstall opencv-python
  pip install opencv-python
  ```

### Transcription Fails

**Problem**: Audio transcription errors or no transcript

**Diagnostic Steps**:
```bash
# Test transcription
python scripts/test_audio_transcriber.py

# Check if video has audio
ffprobe -v error -select_streams a:0 -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1 your_video.mp4

# Verify Whisper installation
python -c "import whisper; print(whisper.__version__)"
```

**Solutions**:
- **No audio track**: Video has no audio (expected behavior)
- **Whisper not installed**: Install with `pip install openai-whisper`
- **ffmpeg missing**: Install ffmpeg (required by Whisper)
- **Out of memory**: Use smaller Whisper model
  ```python
  # In tools/audio_transcriber.py, change model size
  self.model = whisper.load_model("tiny")  # or "base" instead of "small"
  ```

### Object Detection Fails

**Problem**: Object detection errors or no objects found

**Diagnostic Steps**:
```bash
# Test object detection
python scripts/test_object_detector.py

# Verify YOLO model exists
ls -lh yolov8n.pt

# Check ultralytics installation
python -c "from ultralytics import YOLO; print('OK')"
```

**Solutions**:
- **Model not found**: Download YOLOv8 model
  ```python
  from ultralytics import YOLO
  model = YOLO("yolov8n.pt")  # Auto-downloads if missing
  ```
- **No objects detected**: Lower confidence threshold in query
- **GPU issues**: Force CPU mode
  ```python
  # In tools/object_detector.py
  self.model = YOLO("yolov8n.pt", device="cpu")
  ```

## Query & Response Issues

### No Results Found

**Problem**: BRI says it can't find what you're asking about

**Diagnostic Steps**:
1. Verify the video actually contains what you're asking about
2. Check if processing completed successfully
3. Try a more general query first
4. Check database for processed data:
   ```bash
   sqlite3 data/bri.db "SELECT context_type, COUNT(*) FROM video_context WHERE video_id='your_video_id' GROUP BY context_type;"
   ```

**Solutions**:
- **Processing incomplete**: Wait for processing to finish
- **Query too specific**: Broaden your search terms
- **Wrong video selected**: Check you're querying the right video
- **Data not extracted**: Re-process the video

### Inaccurate Responses

**Problem**: BRI's answers don't match the video content

**Possible Causes**:
1. **Low video quality**: Captions may be inaccurate
2. **Poor audio quality**: Transcription errors
3. **Small objects**: Detection may miss them
4. **Ambiguous query**: BRI misunderstood the question

**Solutions**:
- Ask more specific questions
- Reference timestamps if you know them
- Try different phrasing
- Check the source data (frames, captions, transcript) directly

### Slow Response Times

**Problem**: Queries take too long to respond

**Diagnostic Steps**:
```bash
# 1. Check if Redis is enabled and working
redis-cli ping

# 2. Monitor query execution time in logs
# Look for "execution_time" in MCP server logs

# 3. Check Groq API response time
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-70b-versatile","messages":[{"role":"user","content":"test"}]}'
```

**Solutions**:
- **Enable Redis**: Set `REDIS_ENABLED=true` in `.env`
- **Use faster model**: Change to `llama-3-8b-8192` in `.env`
- **Reduce context**: Lower `MAX_CONVERSATION_HISTORY`
- **Optimize queries**: Be more specific to reduce tool usage

### Follow-up Questions Don't Work

**Problem**: BRI doesn't remember previous conversation

**Diagnostic Steps**:
```bash
# Check memory storage
sqlite3 data/bri.db "SELECT COUNT(*) FROM memory WHERE video_id='your_video_id';"

# Verify memory is being saved
# Look for INSERT statements in logs
```

**Solutions**:
- **Database error**: Check database permissions
- **Memory limit reached**: Increase `MAX_CONVERSATION_HISTORY`
- **Wrong video**: Ensure you're on the same video
- **Memory wiped**: Check if memory was cleared

## Performance Issues

### High Memory Usage

**Problem**: Application uses too much RAM

**Solutions**:
```bash
# In .env, reduce these values:
MAX_FRAMES_PER_VIDEO=50          # Default: 100
LAZY_LOAD_BATCH_SIZE=2           # Default: 3
MAX_CONVERSATION_HISTORY=5       # Default: 10

# Use smaller AI models:
# - Whisper: "tiny" or "base" instead of "small"
# - YOLO: "yolov8n.pt" (nano) instead of larger models
```

### High CPU Usage

**Problem**: CPU usage is very high during processing

**Expected Behavior**: High CPU during video processing is normal

**Solutions**:
- Process videos one at a time
- Increase `FRAME_EXTRACTION_INTERVAL` to extract fewer frames
- Use GPU acceleration if available (for YOLO and BLIP)
- Close other applications during processing

### Disk Space Issues

**Problem**: Running out of disk space

**Diagnostic Steps**:
```bash
# Check space usage
du -sh data/*

# Find large files
find data/ -type f -size +100M -exec ls -lh {} \;
```

**Solutions**:
```bash
# Delete old videos and their data
# Through UI: Use delete button in video library

# Or manually:
rm -rf data/videos/old_video_id/
sqlite3 data/bri.db "DELETE FROM videos WHERE video_id='old_video_id';"
sqlite3 data/bri.db "DELETE FROM memory WHERE video_id='old_video_id';"
sqlite3 data/bri.db "DELETE FROM video_context WHERE video_id='old_video_id';"

# Clear cache
redis-cli FLUSHDB  # If using Redis
rm -rf data/cache/*
```

## Database Issues

### Database Locked

**Problem**: `database is locked` error

**Solutions**:
```bash
# 1. Close all connections to the database
# Stop both MCP server and Streamlit UI

# 2. Check for stale lock files
rm -f data/bri.db-journal

# 3. Restart the application

# 4. If problem persists, backup and recreate database
cp data/bri.db data/bri.db.backup
python scripts/init_db.py
```

### Database Corruption

**Problem**: Database errors or inconsistent data

**Solutions**:
```bash
# 1. Check database integrity
sqlite3 data/bri.db "PRAGMA integrity_check;"

# 2. If corrupted, try to recover
sqlite3 data/bri.db ".recover" | sqlite3 data/bri_recovered.db

# 3. If recovery fails, reinitialize (loses data!)
mv data/bri.db data/bri.db.broken
python scripts/init_db.py
```

### Migration Issues

**Problem**: Database schema doesn't match application

**Solution**:
```bash
# Backup existing database
cp data/bri.db data/bri.db.backup

# Reinitialize with current schema
python scripts/init_db.py

# Note: This will lose existing data
# For production, implement proper migrations
```

## Cache Issues

### Redis Connection Fails

**Problem**: `Connection refused` to Redis

**Solutions**:
```bash
# Option 1: Disable Redis (application will work without it)
# In .env:
REDIS_ENABLED=false

# Option 2: Install and start Redis
# Mac:
brew install redis
brew services start redis

# Linux:
sudo apt-get install redis-server
sudo systemctl start redis

# Windows:
# Download from https://github.com/microsoftarchive/redis/releases

# Option 3: Use different Redis URL
# In .env:
REDIS_URL=redis://your-redis-host:6379
```

### Cache Not Working

**Problem**: Queries aren't using cached results

**Diagnostic Steps**:
```bash
# 1. Verify Redis is running
redis-cli ping
# Should return: PONG

# 2. Check cache keys
redis-cli KEYS "bri:*"

# 3. Monitor cache hits/misses in logs
# Look for "cached": true/false in MCP server responses

# 4. Check cache stats
curl http://localhost:8000/cache/stats
```

**Solutions**:
- Ensure `REDIS_ENABLED=true` in `.env`
- Verify Redis URL is correct
- Check Redis memory limits: `redis-cli INFO memory`
- Clear and rebuild cache: `redis-cli FLUSHDB`

### Stale Cache Data

**Problem**: Getting outdated results from cache

**Solutions**:
```bash
# Clear cache for specific video
curl -X DELETE http://localhost:8000/cache/videos/your_video_id

# Clear all cache
curl -X DELETE http://localhost:8000/cache

# Or use Redis CLI
redis-cli FLUSHDB

# Adjust cache TTL in .env:
CACHE_TTL_HOURS=12  # Default: 24
```

## Error Messages Reference

### User-Facing Errors

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Oops! I can only work with MP4, AVI, MOV, or MKV files" | Unsupported video format | Convert video to supported format |
| "This video is a bit too big for me right now" | File size exceeds limit | Compress video or split into parts |
| "Hmm, something went wrong with the upload" | Upload failed | Check network, disk space, permissions |
| "I had trouble extracting frames" | Frame extraction failed | Check video codec, try re-encoding |
| "The audio was a bit tricky" | Transcription failed | Check audio quality, ensure ffmpeg installed |
| "I couldn't spot specific objects this time" | Object detection failed | Lower confidence threshold, check video quality |
| "I'm having trouble thinking right now" | Groq API error | Check API key, wait and retry |
| "My tools are taking a break" | MCP server down | Restart MCP server |
| "I'm having trouble remembering" | Database error | Check database permissions, restart application |

### System Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `GROQ_API_KEY is required` | Missing API key | Add key to `.env` file |
| `ModuleNotFoundError` | Missing dependency | Run `pip install -r requirements.txt` |
| `Address already in use` | Port conflict | Change port or kill existing process |
| `Permission denied` | File/directory permissions | Fix permissions with `chmod` |
| `No such file or directory` | Missing file/path | Create directory or check path |
| `database is locked` | Concurrent access | Close other connections, restart |
| `Connection refused` | Server not running | Start the server |
| `Out of memory` | Insufficient RAM | Reduce processing parameters |

## Diagnostic Tools

### Validate Setup

```bash
# Run comprehensive setup validation
python scripts/validate_setup.py

# This checks:
# - Python version
# - Dependencies installed
# - Configuration valid
# - Directories exist
# - Database initialized
# - API key present
```

### Test Individual Components

```bash
# Test frame extraction
python scripts/test_frame_extractor.py

# Test image captioning
python scripts/test_image_captioner.py

# Test audio transcription
python scripts/test_audio_transcriber.py

# Test object detection
python scripts/test_object_detector.py

# Test MCP server
python scripts/test_mcp_server.py

# Test full integration
python scripts/test_mcp_server_integration.py
```

### Check Logs

```bash
# View application logs
tail -f logs/bri.log

# View error logs only
tail -f logs/bri_errors.log

# View performance logs
tail -f logs/bri_performance.log

# Search for specific errors
grep "ERROR" logs/bri.log

# View MCP server logs
# (Printed to console where server is running)
```

### Database Inspection

```bash
# Open database
sqlite3 data/bri.db

# List tables
.tables

# Check video count
SELECT COUNT(*) FROM videos;

# Check memory records
SELECT COUNT(*) FROM memory;

# Check processed context
SELECT video_id, context_type, COUNT(*) 
FROM video_context 
GROUP BY video_id, context_type;

# Exit
.quit
```

### Redis Inspection

```bash
# Connect to Redis
redis-cli

# Check connection
PING

# List all BRI keys
KEYS bri:*

# Get cache stats
INFO stats

# Check memory usage
INFO memory

# Clear all cache
FLUSHDB

# Exit
quit
```

## Getting More Help

If you've tried the solutions above and still have issues:

1. **Enable Debug Mode**:
   ```bash
   # In .env:
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

2. **Collect Diagnostic Information**:
   - Error messages (full stack traces)
   - Configuration (mask sensitive values)
   - System information (OS, Python version)
   - Steps to reproduce

3. **Check Documentation**:
   - [README.md](../README.md) - Setup and configuration
   - [USER_GUIDE.md](USER_GUIDE.md) - Usage instructions
   - [MCP Server README](../mcp_server/README.md) - API documentation

4. **Report Issues**:
   - Open a GitHub issue with diagnostic information
   - Include relevant log excerpts
   - Describe expected vs actual behavior

---

**Still stuck?** Don't hesitate to ask for help! The BRI community is here to support you. 💜
