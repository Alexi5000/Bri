# BRI Deployment Checklist - Testing Environment

## Pre-Deployment Verification ✅

- [x] Python 3.13.8 installed
- [x] Virtual environment activated (.venv)
- [x] .env file exists
- [x] GROQ_API_KEY configured
- [x] All dependencies installed
- [x] Git repository up to date

## Deployment Steps

### 1. Initialize Database
```powershell
python scripts/init_db.py
```

### 2. Verify Setup
```powershell
python scripts/validate_setup.py
```

### 3. Start Services

**Option A: Using Start Script (Recommended)**
```powershell
.\scripts\start_dev.bat
```

**Option B: Manual Start**

Terminal 1 - MCP Server:
```powershell
python mcp_server/main.py
```

Terminal 2 - Streamlit UI:
```powershell
streamlit run app.py
```

### 4. Access Application
Open browser to: http://localhost:8501

## Testing Checklist

### Basic Functionality
- [ ] Welcome screen loads
- [ ] Can upload video
- [ ] Video processes successfully
- [ ] Can ask questions
- [ ] Get responses with frames
- [ ] Timestamps work
- [ ] Follow-up suggestions appear

### Advanced Features
- [ ] Conversation history persists
- [ ] Multiple videos work
- [ ] Video player navigation
- [ ] Error handling is friendly
- [ ] Performance is acceptable

### Production Readiness Features (Task 50)
- [ ] Logs are being created in logs/ directory
- [ ] Database backup can be created
- [ ] Logging dashboard accessible
- [ ] Graceful degradation works
- [ ] Metrics are being logged

## Post-Deployment Verification

### Check Logs
```powershell
# View application logs
Get-Content logs/bri.log -Tail 50

# View errors
Get-Content logs/bri_errors.log -Tail 20

# View performance metrics
Get-Content logs/bri_performance.log -Tail 20
```

### Check Database
```powershell
# Verify database exists
Test-Path data/bri.db

# Check database size
(Get-Item data/bri.db).Length / 1MB
```

### Create Test Backup
```powershell
python scripts/backup_database.py --verify
```

### Check System Health
```powershell
python scripts/health_check.py
```

## Troubleshooting

### If MCP Server Fails
```powershell
# Check port 8000
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F
```

### If Streamlit Fails
```powershell
# Check port 8501
netstat -ano | findstr :8501

# Kill process if needed
taskkill /PID <PID> /F
```

### If Database Issues
```powershell
# Reinitialize database
python scripts/init_db.py
```

### If Dependencies Missing
```powershell
pip install -r requirements.txt --upgrade
```

## Performance Monitoring

### During Testing, Monitor:
- Response times (should be <5 seconds)
- Memory usage (should be <2GB)
- CPU usage (should be <50% average)
- Log file sizes
- Database size

### Access Logging Dashboard
```powershell
streamlit run ui/logging_dashboard.py --server.port 8502
```
Then open: http://localhost:8502

## Test Scenarios

### Scenario 1: Quick Test (5 minutes)
1. Upload a 30-second video
2. Ask "What's happening?"
3. Ask "What did they say?"
4. Click a timestamp
5. Verify video navigation works

### Scenario 2: Full Feature Test (15 minutes)
1. Upload 2-3 different videos
2. Test all query types:
   - Visual description
   - Audio transcription
   - Object detection
   - Timestamp queries
   - Follow-up questions
3. Test conversation history
4. Test video switching
5. Test error handling

### Scenario 3: Production Features Test (10 minutes)
1. Check logs are being created
2. Create a database backup
3. View logging dashboard
4. Check system health
5. Verify metrics are logged

## Success Criteria

✅ Application starts without errors
✅ Can upload and process videos
✅ Queries return relevant responses
✅ UI is responsive and friendly
✅ Logs are being created
✅ Backups can be created
✅ No critical errors in logs
✅ Performance is acceptable

## Stopping the Application

```powershell
# Press Ctrl+C in both terminals
# Or close the terminal windows
```

## Next Steps After Successful Testing

1. Document any issues found
2. Test with various video types
3. Stress test with multiple videos
4. Review logs for any warnings
5. Create production deployment plan

## Notes

- First video processing may take 1-2 minutes
- Subsequent queries should be faster (<5 seconds)
- Enable Redis for better caching (optional)
- Monitor logs/ directory for any errors
- Database backups are in data/backups/

## Support

If issues occur:
1. Check logs in logs/ directory
2. Review docs/TROUBLESHOOTING.md
3. Check docs/OPERATIONS_RUNBOOK.md
4. Run health check: `python scripts/health_check.py`
