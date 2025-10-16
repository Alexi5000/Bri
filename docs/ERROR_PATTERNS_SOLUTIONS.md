# BRI Common Error Patterns and Solutions

## Overview

This document catalogs common error patterns encountered in BRI, their root causes, and proven solutions.

## Error Categories

1. [Database Errors](#database-errors)
2. [API Errors](#api-errors)
3. [Processing Errors](#processing-errors)
4. [Cache Errors](#cache-errors)
5. [Model Errors](#model-errors)
6. [System Errors](#system-errors)

---

## Database Errors

### Error: "database is locked"

**Pattern:**
```
sqlite3.OperationalError: database is locked
```

**Cause:**
- Multiple processes accessing database simultaneously
- Long-running transaction blocking others
- WAL mode not enabled

**Solution:**
```bash
# 1. Check for multiple processes
ps aux | grep python | grep bri

# 2. Kill duplicate processes
pkill -f "streamlit run app.py"

# 3. Verify WAL mode is enabled
sqlite3 data/bri.db "PRAGMA journal_mode"
# Should return: wal

# 4. If not WAL, enable it
sqlite3 data/bri.db "PRAGMA journal_mode=WAL"
```

**Prevention:**
- Use single Streamlit instance
- Use single MCP server instance
- Keep transactions short
- WAL mode is enabled by default

---

### Error: "database disk image is malformed"

**Pattern:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Cause:**
- Disk corruption
- Improper shutdown
- Disk full during write
- Hardware failure

**Solution:**
```bash
# 1. Stop all services
pkill -f streamlit
pkill -f mcp_server

# 2. Backup corrupted database
cp data/bri.db data/bri_corrupted_$(date +%Y%m%d).db

# 3. Attempt recovery
sqlite3 data/bri.db ".recover" | sqlite3 data/bri_recovered.db

# 4. If recovery fails, restore from backup
python scripts/restore_database.py

# 5. Verify integrity
sqlite3 data/bri.db "PRAGMA integrity_check"
```

**Prevention:**
- Regular backups (automated daily)
- Monitor disk space
- Use reliable storage (SSD)
- Graceful shutdown procedures

---

### Error: "no such table: videos"

**Pattern:**
```
sqlite3.OperationalError: no such table: videos
```

**Cause:**
- Database not initialized
- Wrong database path
- Database file deleted

**Solution:**
```bash
# 1. Check if database exists
ls -la data/bri.db

# 2. Initialize database
python scripts/init_db.py

# 3. Verify tables created
sqlite3 data/bri.db ".tables"
# Should show: videos, memory, video_context
```

**Prevention:**
- Run init_db.py during setup
- Don't delete database file
- Use correct DATABASE_PATH in .env

---

## API Errors

### Error: "Groq API rate limit exceeded"

**Pattern:**
```
groq.RateLimitError: Rate limit exceeded. Please try again in 60 seconds.
```

**Cause:**
- Too many requests in short time
- Exceeded API quota
- Retry loop without backoff

**Solution:**
```python
# 1. Wait for rate limit to reset
import time
time.sleep(60)

# 2. Enable response caching
# In .env
REDIS_ENABLED=true

# 3. Implement exponential backoff
from mcp_server.circuit_breaker import retry_with_backoff

result = await retry_with_backoff(
    api_call_function,
    max_retries=3,
    base_delay=1.0
)
```

**Prevention:**
- Enable caching for repeated queries
- Implement rate limiting
- Use circuit breaker pattern
- Monitor API usage

---

### Error: "Groq API authentication failed"

**Pattern:**
```
groq.AuthenticationError: Invalid API key
```

**Cause:**
- Missing API key
- Invalid API key
- Expired API key
- Wrong environment variable

**Solution:**
```bash
# 1. Check API key is set
echo $GROQ_API_KEY

# 2. Verify API key in .env
cat .env | grep GROQ_API_KEY

# 3. Test API key
python -c "
from groq import Groq
from config import Config
client = Groq(api_key=Config.GROQ_API_KEY)
print('API key valid')
"

# 4. If invalid, update .env
# GROQ_API_KEY=your_valid_key_here
```

**Prevention:**
- Store API key in .env file
- Don't commit .env to git
- Validate API key on startup
- Monitor API key expiration

---

### Error: "Groq API timeout"

**Pattern:**
```
groq.APITimeoutError: Request timed out
```

**Cause:**
- Network issues
- API server overloaded
- Request too large
- Slow connection

**Solution:**
```python
# 1. Increase timeout
from config import Config
Config.REQUEST_TIMEOUT = 60  # Increase from 30

# 2. Reduce request size
Config.GROQ_MAX_TOKENS = 512  # Reduce from 1024

# 3. Retry with backoff
from mcp_server.circuit_breaker import retry_with_backoff

result = await retry_with_backoff(
    api_call,
    max_retries=3,
    base_delay=2.0
)
```

**Prevention:**
- Set appropriate timeouts
- Monitor network latency
- Use circuit breaker
- Cache responses

---

## Processing Errors

### Error: "Out of memory during video processing"

**Pattern:**
```
MemoryError: Unable to allocate memory
```

**Cause:**
- Video too large
- Too many frames extracted
- Memory leak
- Insufficient RAM

**Solution:**
```bash
# 1. Reduce frame extraction
# In .env
MAX_FRAMES_PER_VIDEO=10
FRAME_EXTRACTION_INTERVAL=5.0

# 2. Clear memory
pkill -f streamlit
pkill -f mcp_server
sleep 5

# 3. Restart services
python mcp_server/main.py &
streamlit run app.py

# 4. Process video again
```

**Prevention:**
- Set reasonable MAX_FRAMES_PER_VIDEO
- Monitor memory usage
- Process videos in chunks
- Add more RAM if needed

---

### Error: "Video codec not supported"

**Pattern:**
```
cv2.error: OpenCV: Unsupported codec
```

**Cause:**
- Unsupported video format
- Missing codec
- Corrupted video file

**Solution:**
```bash
# 1. Check video format
ffprobe video.mp4

# 2. Convert to supported format
ffmpeg -i video.mov -c:v libx264 -c:a aac video.mp4

# 3. Upload converted video
```

**Prevention:**
- Accept only common formats (MP4, AVI, MOV, MKV)
- Validate video format on upload
- Provide format conversion tool
- Document supported formats

---

### Error: "Frame extraction failed"

**Pattern:**
```
ERROR - tools.frame_extractor - Failed to extract frames: [error details]
```

**Cause:**
- Corrupted video
- Insufficient disk space
- Permission issues
- OpenCV error

**Solution:**
```bash
# 1. Check disk space
df -h

# 2. Check permissions
ls -la data/frames/

# 3. Verify video file
ffprobe data/videos/video_id.mp4

# 4. Retry extraction
python -c "
from tools.frame_extractor import FrameExtractor
extractor = FrameExtractor()
frames = extractor.extract_frames('data/videos/video_id.mp4')
print(f'Extracted {len(frames)} frames')
"
```

**Prevention:**
- Validate video on upload
- Monitor disk space
- Set proper permissions
- Handle extraction errors gracefully

---

## Cache Errors

### Error: "Redis connection refused"

**Pattern:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Cause:**
- Redis not running
- Wrong Redis URL
- Network issues
- Redis crashed

**Solution:**
```bash
# 1. Check if Redis is running
redis-cli ping
# Should return: PONG

# 2. Start Redis if not running
redis-server &

# 3. Or disable Redis
# In .env
REDIS_ENABLED=false

# 4. Verify connection
python -c "
import redis
from config import Config
r = redis.from_url(Config.REDIS_URL)
r.ping()
print('Redis connected')
"
```

**Prevention:**
- Start Redis before BRI
- Use systemd/supervisor for Redis
- Monitor Redis health
- Implement cache fallback

---

### Error: "Redis out of memory"

**Pattern:**
```
redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'
```

**Cause:**
- Cache too large
- No eviction policy
- Memory limit too low

**Solution:**
```bash
# 1. Check Redis memory
redis-cli INFO memory

# 2. Clear cache
redis-cli FLUSHALL

# 3. Set eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 4. Increase memory limit
redis-cli CONFIG SET maxmemory 2gb
```

**Prevention:**
- Set appropriate maxmemory
- Use LRU eviction policy
- Monitor cache size
- Set reasonable TTLs

---

## Model Errors

### Error: "BLIP model not found"

**Pattern:**
```
OSError: Model 'Salesforce/blip-image-captioning-large' not found
```

**Cause:**
- Model not downloaded
- Network issues during download
- Insufficient disk space
- Hugging Face API issues

**Solution:**
```python
# 1. Download model manually
from transformers import BlipProcessor, BlipForConditionalGeneration

processor = BlipProcessor.from_pretrained(
    'Salesforce/blip-image-captioning-large'
)
model = BlipForConditionalGeneration.from_pretrained(
    'Salesforce/blip-image-captioning-large'
)

print("Model downloaded successfully")
```

**Prevention:**
- Download models during setup
- Cache models locally
- Monitor disk space
- Handle download errors

---

### Error: "Whisper model loading failed"

**Pattern:**
```
RuntimeError: Failed to load Whisper model
```

**Cause:**
- Model file corrupted
- Insufficient memory
- Wrong model name
- Missing dependencies

**Solution:**
```python
# 1. Download model again
import whisper

model = whisper.load_model("base", download_root="./models")
print("Whisper model loaded")

# 2. Or use smaller model
model = whisper.load_model("tiny")
```

**Prevention:**
- Use appropriate model size
- Verify model files
- Monitor memory usage
- Cache models locally

---

## System Errors

### Error: "Disk space full"

**Pattern:**
```
OSError: [Errno 28] No space left on device
```

**Cause:**
- Too many videos
- Large log files
- Many backups
- Cache not cleaned

**Solution:**
```bash
# 1. Check disk usage
df -h
du -sh data/*

# 2. Clean up logs
find logs/ -name "*.log.*" -mtime +30 -delete

# 3. Clean up backups
python scripts/backup_database.py --cleanup

# 4. Archive old videos
python scripts/archival_cli.py --archive-older-than 90

# 5. Vacuum database
sqlite3 data/bri.db "VACUUM"
```

**Prevention:**
- Monitor disk space
- Automated cleanup
- Set retention policies
- Use archival system

---

### Error: "Permission denied"

**Pattern:**
```
PermissionError: [Errno 13] Permission denied: 'data/videos/video.mp4'
```

**Cause:**
- Wrong file permissions
- Wrong directory permissions
- Running as wrong user

**Solution:**
```bash
# 1. Check permissions
ls -la data/

# 2. Fix permissions
chmod 755 data/
chmod 644 data/videos/*

# 3. Fix ownership
chown -R $USER:$USER data/
```

**Prevention:**
- Set correct permissions during setup
- Run as appropriate user
- Document permission requirements

---

## Error Pattern Analysis

### How to Identify Patterns

**1. Group Similar Errors:**
```bash
grep ERROR logs/bri_errors.log | \
  sed 's/[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}.*ERROR/ERROR/' | \
  sort | uniq -c | sort -rn
```

**2. Find Error Frequency:**
```bash
grep ERROR logs/bri_errors.log | \
  grep -oP '\d{4}-\d{2}-\d{2} \d{2}' | \
  uniq -c
```

**3. Correlate with Events:**
```bash
# Find errors around specific time
grep "2025-10-16 14:" logs/bri_errors.log
```

### Error Reporting

When reporting errors, include:

1. **Error message:** Full error text
2. **Stack trace:** Complete traceback
3. **Context:** What were you doing?
4. **Logs:** Relevant log entries
5. **Environment:** OS, Python version, etc.
6. **Steps to reproduce:** How to trigger error

**Example Report:**
```
Error: Database is locked

Stack trace:
[paste full traceback]

Context:
- Uploading video while processing another
- Multiple browser tabs open

Logs:
[paste relevant log entries]

Environment:
- OS: Ubuntu 22.04
- Python: 3.10.12
- BRI version: 1.0.0

Steps to reproduce:
1. Upload video A
2. While processing, upload video B
3. Error occurs
```

## Summary

Common error patterns and quick fixes:

| Error | Quick Fix |
|-------|-----------|
| Database locked | Kill duplicate processes |
| API rate limit | Wait 60s, enable caching |
| Out of memory | Reduce MAX_FRAMES_PER_VIDEO |
| Redis connection | Start Redis or disable |
| Model not found | Download models |
| Disk full | Clean up logs/backups |
| Permission denied | Fix file permissions |

For detailed solutions, see the Operations Runbook.
