# BRI Operations Runbook

## Overview

This runbook provides step-by-step procedures for common operational tasks, troubleshooting, and maintenance of the BRI video agent system.

## Table of Contents

1. [System Health Checks](#system-health-checks)
2. [Database Maintenance](#database-maintenance)
3. [Log Analysis](#log-analysis)
4. [Performance Tuning](#performance-tuning)
5. [Data Recovery](#data-recovery)
6. [Common Error Patterns](#common-error-patterns)
7. [Emergency Procedures](#emergency-procedures)

---

## System Health Checks

### Daily Health Check

Run the automated health check script:

```bash
python scripts/health_check.py
```

**Expected Output:**
- ✅ Database: Connected
- ✅ Cache: Available
- ✅ Groq API: Responding
- ✅ Disk Space: >20% free
- ✅ Recent Backups: <24 hours old

**If any checks fail:**
1. Check logs: `tail -f logs/bri.log`
2. Review specific service logs
3. Follow troubleshooting steps below

### Manual Health Verification

```python
from services.graceful_degradation import degradation_service

# Get system health
health = degradation_service.get_system_health()
print(health)
```

**Healthy System:**
```json
{
  "overall_status": "available",
  "services": {
    "database": "available",
    "cache": "available",
    "groq_api": "available"
  },
  "degradation_events_count": 0,
  "queued_requests": 0
}
```

---

## Database Maintenance

### Routine Maintenance (Weekly)

**1. Vacuum Database**
```bash
sqlite3 data/bri.db "VACUUM"
```
Reduces database size and improves performance.

**2. Analyze Tables**
```bash
sqlite3 data/bri.db "ANALYZE"
```
Updates query optimizer statistics.

**3. Check Integrity**
```bash
sqlite3 data/bri.db "PRAGMA integrity_check"
```
Expected output: `ok`

**4. Review Database Size**
```bash
du -sh data/bri.db
```
Alert if >1GB without corresponding video count.

### Backup Procedures

**Create Manual Backup:**
```bash
python scripts/backup_database.py --name weekly_backup --verify --cleanup
```

**Verify All Backups:**
```bash
python scripts/verify_backups.py
```

**Restore from Backup:**
```bash
# List available backups
python scripts/restore_database.py --list

# Restore specific backup
python scripts/restore_database.py data/backups/bri_backup_20251016_143000.db
```

### Database Performance Issues

**Symptom:** Slow queries (>1 second)

**Diagnosis:**
```bash
# Check slow queries in logs
grep "execution_time.*[1-9]\." logs/bri_performance.log

# Check database size
du -sh data/bri.db

# Check table sizes
sqlite3 data/bri.db "
SELECT name, COUNT(*) as rows 
FROM sqlite_master 
JOIN (SELECT name FROM sqlite_master WHERE type='table') 
GROUP BY name
"
```

**Resolution:**
1. Run VACUUM to compact database
2. Run ANALYZE to update statistics
3. Check for missing indexes
4. Consider archiving old data

---

## Log Analysis

### Finding Errors

**Recent Errors:**
```bash
tail -100 logs/bri_errors.log
```

**Errors for Specific Video:**
```bash
grep "video_id=vid_123" logs/bri.log | grep ERROR
```

**Error Frequency:**
```bash
grep ERROR logs/bri.log | wc -l
```

### Performance Analysis

**Slow Operations:**
```bash
grep "completed in [1-9]" logs/bri_performance.log
```

**Cache Hit Rate:**
```bash
hits=$(grep "Cache HIT" logs/bri_performance.log | wc -l)
misses=$(grep "Cache MISS" logs/bri_performance.log | wc -l)
total=$((hits + misses))
rate=$((hits * 100 / total))
echo "Cache hit rate: ${rate}%"
```

**API Call Times:**
```bash
grep "Groq API" logs/bri.log | grep -oP "completed in \K[\d.]+" | sort -n
```

### Log Rotation Issues

**Symptom:** Log files not rotating

**Check:**
```bash
ls -lh logs/bri.log*
```

**Fix:**
```python
from utils.logging_config import setup_logging
setup_logging(enable_rotation=True)
```

---

## Performance Tuning

### Slow Video Processing

**Symptom:** Video processing takes >5 minutes

**Diagnosis:**
```bash
# Check processing times by stage
grep "Pipeline.*completed" logs/bri_pipeline.log
```

**Tuning Options:**

1. **Reduce Frame Extraction:**
```bash
# In .env
MAX_FRAMES_PER_VIDEO=15  # Default: 20
FRAME_EXTRACTION_INTERVAL=3.0  # Default: 2.0
```

2. **Enable Caching:**
```bash
# In .env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379
```

3. **Optimize Model Loading:**
- Models are loaded once at startup
- Restart services if memory issues occur

### High Memory Usage

**Symptom:** Memory >2GB

**Diagnosis:**
```bash
# Check current memory
ps aux | grep python | grep bri

# Check memory logs
grep "memory_mb" logs/bri.log
```

**Resolution:**
1. Reduce MAX_FRAMES_PER_VIDEO
2. Clear cache: `redis-cli FLUSHALL`
3. Restart services
4. Check for memory leaks in logs

### Slow API Responses

**Symptom:** Groq API calls >5 seconds

**Diagnosis:**
```bash
grep "Groq API" logs/bri_performance.log | grep -oP "completed in \K[\d.]+"
```

**Resolution:**
1. Check Groq API status
2. Reduce GROQ_MAX_TOKENS
3. Enable response caching
4. Check network connectivity

---

## Data Recovery

### Corrupted Database

**Symptom:** `database disk image is malformed`

**Recovery Steps:**

1. **Stop all services**
```bash
# Stop Streamlit
pkill -f streamlit

# Stop MCP server
pkill -f mcp_server
```

2. **Attempt repair**
```bash
sqlite3 data/bri.db ".recover" | sqlite3 data/bri_recovered.db
```

3. **If repair fails, restore from backup**
```bash
python scripts/restore_database.py
```

4. **Verify restored database**
```bash
sqlite3 data/bri.db "PRAGMA integrity_check"
```

### Missing Video Data

**Symptom:** Video uploaded but no processing results

**Diagnosis:**
```python
from storage.database import Database

db = Database()
video_id = "vid_123"

# Check video record
video = db.get_video(video_id)
print(f"Status: {video.processing_status}")

# Check context data
context = db.get_video_context(video_id)
print(f"Frames: {len(context.get('frames', []))}")
print(f"Captions: {len(context.get('captions', []))}")
```

**Resolution:**
1. Check processing logs for errors
2. Reprocess video:
```python
from services.video_processing_service import VideoProcessingService

service = VideoProcessingService()
service.process_video(video_id)
```

### Lost Conversation History

**Symptom:** Conversation history missing

**Recovery:**
1. Check if data exists in database:
```bash
sqlite3 data/bri.db "SELECT COUNT(*) FROM memory WHERE video_id='vid_123'"
```

2. If data exists but not showing, clear cache:
```bash
redis-cli DEL "bri:memory:vid_123"
```

3. If data lost, check backups:
```bash
python scripts/restore_database.py --list
```

---

## Common Error Patterns

### Error: "Groq API rate limit exceeded"

**Cause:** Too many API requests in short time

**Solution:**
1. Wait 60 seconds
2. Reduce request frequency
3. Enable response caching
4. Check for retry loops in code

**Prevention:**
```python
# In .env
GROQ_TEMPERATURE=0.7  # Lower = more cacheable
```

### Error: "Database is locked"

**Cause:** Multiple processes accessing database

**Solution:**
1. Check for multiple running instances:
```bash
ps aux | grep python | grep bri
```

2. Kill duplicate processes:
```bash
pkill -f "streamlit run app.py"
pkill -f "python mcp_server/main.py"
```

3. Restart services properly

**Prevention:**
- Use single Streamlit instance
- Use single MCP server instance
- Enable WAL mode (already enabled)

### Error: "Out of memory"

**Cause:** Processing large video or too many frames

**Solution:**
1. Reduce MAX_FRAMES_PER_VIDEO
2. Increase FRAME_EXTRACTION_INTERVAL
3. Process video in smaller chunks
4. Restart services to clear memory

**Prevention:**
```bash
# In .env
MAX_FRAMES_PER_VIDEO=15
FRAME_EXTRACTION_INTERVAL=3.0
```

### Error: "Model not found"

**Cause:** ML models not downloaded

**Solution:**
```bash
# Download models
python -c "
from transformers import BlipProcessor, BlipForConditionalGeneration
import whisper
from ultralytics import YOLO

# Download BLIP
BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-large')
BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-large')

# Download Whisper
whisper.load_model('base')

# Download YOLO
YOLO('yolov8n.pt')
"
```

### Error: "Redis connection refused"

**Cause:** Redis not running or wrong URL

**Solution:**
1. Check Redis status:
```bash
redis-cli ping
```

2. Start Redis if not running:
```bash
redis-server
```

3. Or disable Redis:
```bash
# In .env
REDIS_ENABLED=false
```

---

## Emergency Procedures

### System Unresponsive

**Steps:**

1. **Check system resources**
```bash
top
df -h
```

2. **Check logs for errors**
```bash
tail -100 logs/bri_errors.log
```

3. **Restart services**
```bash
# Stop all
pkill -f streamlit
pkill -f mcp_server

# Wait 5 seconds
sleep 5

# Start MCP server
python mcp_server/main.py &

# Start Streamlit
streamlit run app.py
```

4. **Verify health**
```bash
python scripts/health_check.py
```

### Data Corruption

**Steps:**

1. **Stop all services immediately**
```bash
pkill -f streamlit
pkill -f mcp_server
```

2. **Create emergency backup**
```bash
cp data/bri.db data/bri_emergency_$(date +%Y%m%d_%H%M%S).db
```

3. **Check integrity**
```bash
sqlite3 data/bri.db "PRAGMA integrity_check"
```

4. **If corrupted, restore from backup**
```bash
python scripts/restore_database.py
```

5. **Verify and restart**
```bash
python scripts/health_check.py
```

### Disk Space Full

**Steps:**

1. **Check disk usage**
```bash
df -h
du -sh data/*
```

2. **Clean up old logs**
```bash
find logs/ -name "*.log.*" -mtime +30 -delete
```

3. **Clean up old backups**
```bash
python scripts/backup_database.py --cleanup
```

4. **Archive old videos**
```bash
python scripts/archival_cli.py --archive-older-than 90
```

5. **Vacuum database**
```bash
sqlite3 data/bri.db "VACUUM"
```

### Complete System Reset

**⚠️ WARNING: This will delete all data!**

**Steps:**

1. **Backup everything**
```bash
python scripts/backup_database.py --name pre_reset_backup
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

2. **Stop services**
```bash
pkill -f streamlit
pkill -f mcp_server
```

3. **Reset database**
```bash
rm data/bri.db
python scripts/init_db.py
```

4. **Clear cache**
```bash
redis-cli FLUSHALL
rm -rf data/cache/*
```

5. **Restart services**
```bash
python mcp_server/main.py &
streamlit run app.py
```

---

## Monitoring Checklist

### Daily
- [ ] Check system health
- [ ] Review error logs
- [ ] Verify backups completed
- [ ] Check disk space

### Weekly
- [ ] Vacuum database
- [ ] Verify backup integrity
- [ ] Review performance metrics
- [ ] Clean up old logs

### Monthly
- [ ] Test backup restore
- [ ] Review and archive old data
- [ ] Update dependencies
- [ ] Performance tuning review

---

## Contact and Escalation

For issues not covered in this runbook:

1. Check logs: `logs/bri.log`, `logs/bri_errors.log`
2. Review documentation: `docs/`
3. Check GitHub issues
4. Create new issue with:
   - Error logs
   - System health output
   - Steps to reproduce

---

## Appendix: Useful Commands

### Quick Diagnostics
```bash
# System health
python scripts/health_check.py

# Recent errors
tail -50 logs/bri_errors.log

# Database size
du -sh data/bri.db

# Cache status
redis-cli INFO stats

# Process status
ps aux | grep python | grep bri
```

### Quick Fixes
```bash
# Restart everything
pkill -f streamlit; pkill -f mcp_server; sleep 5; python mcp_server/main.py & streamlit run app.py

# Clear cache
redis-cli FLUSHALL

# Vacuum database
sqlite3 data/bri.db "VACUUM"

# Create backup
python scripts/backup_database.py
```

### Log Analysis
```bash
# Error count by type
grep ERROR logs/bri.log | cut -d'-' -f4 | sort | uniq -c | sort -rn

# Slowest operations
grep "completed in" logs/bri_performance.log | sort -t'=' -k2 -rn | head -20

# Most active videos
grep "video_id=" logs/bri.log | grep -oP "video_id=\K[^]]*" | sort | uniq -c | sort -rn
```
