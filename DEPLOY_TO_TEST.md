# BRI Video Agent - Deploy to Test

This guide will help you deploy the BRI Video Agent application for testing using Docker Compose.

## Prerequisites

- Docker installed and running
- Docker Compose v2.0+ installed
- At least 4GB of RAM available
- At least 10GB of disk space
- A valid Groq API key

## Quick Start

### 1. Set Your API Key

Edit the `.env` file and replace `your_groq_api_key_here` with your actual Groq API key:

```bash
nano .env
# or
vim .env
```

Look for this line and update it:
```
GROQ_API_KEY=your_actual_api_key_here
```

### 2. Deploy the Application

Run the deployment script:

```bash
./deploy_test.sh
```

This script will:
- Check that Docker is running
- Create necessary directories
- Build Docker images
- Start all services (Redis, MCP Server, Streamlit UI)
- Wait for services to be healthy
- Display access URLs

The first deployment will take 5-10 minutes as it:
- Downloads base Docker images
- Installs Python dependencies
- Downloads AI models (BLIP, Whisper, YOLOv8)

Subsequent deployments will be much faster (30-60 seconds).

### 3. Access the Application

Once deployed, open your browser and navigate to:

**http://localhost:8501**

You should see the BRI welcome screen.

## What Gets Deployed

The deployment consists of three Docker containers:

1. **Redis** (port 6379)
   - Caching layer for improved performance
   - Stores temporary data

2. **MCP Server** (port 8000)
   - Backend API server
   - Runs video processing tools
   - Hosts AI models (BLIP, Whisper, YOLOv8)

3. **Streamlit UI** (port 8501)
   - Frontend web interface
   - Interactive chat interface
   - Video player and library

All containers share persistent volumes for:
- Video files (`./data/videos`)
- Extracted frames (`./data/frames`)
- Database (`./data/bri.db`)
- Logs (`./logs`)

## Testing the Application

### Quick Test (5 minutes)

1. Open http://localhost:8501
2. Upload a short video (30-60 seconds, MP4 format recommended)
3. Wait for processing to complete (30-90 seconds)
4. Ask: "What's happening in this video?"
5. Click on a timestamp in the response
6. Verify the video seeks to that timestamp

### Full Feature Test (15 minutes)

Test different query types:

1. **Visual Description**
   - "What's happening in this video?"
   - "Describe what you see"

2. **Audio Transcription**
   - "What did they say?"
   - "Transcribe the audio"

3. **Object Detection**
   - "What objects can you detect?"
   - "What things are visible?"

4. **Timestamp Navigation**
   - Click timestamps in responses
   - Use video player controls

5. **Follow-up Questions**
   - Ask related questions
   - Test conversation memory

6. **Multiple Videos**
   - Upload 2-3 videos
   - Switch between them
   - Verify separate conversations

## Monitoring

### View Logs

View all logs:
```bash
docker compose logs -f
```

View specific service logs:
```bash
docker compose logs -f streamlit-ui
docker compose logs -f mcp-server
docker compose logs -f redis
```

View recent errors:
```bash
docker compose logs --tail=50 mcp-server | grep -i error
```

### Check Service Status

```bash
docker compose ps
```

### Check Service Health

```bash
# MCP Server health
curl http://localhost:8000/health

# Redis health
docker compose exec redis redis-cli ping

# View API documentation
open http://localhost:8000/docs
```

### Monitor Resource Usage

```bash
docker stats
```

## Troubleshooting

### Services Won't Start

1. Check if ports are already in use:
```bash
# Check port 8501 (Streamlit)
netstat -an | grep 8501

# Check port 8000 (MCP Server)
netstat -an | grep 8000

# Check port 6379 (Redis)
netstat -an | grep 6379
```

2. Stop conflicting services or change ports in `docker-compose.yml`

3. Check logs for errors:
```bash
docker compose logs
```

### Services Fail Health Checks

Wait a bit longer - first startup can take 60-90 seconds as models are loaded.

Check specific service logs:
```bash
docker compose logs mcp-server
```

### Video Processing Fails

1. Check MCP server logs:
```bash
docker compose logs -f mcp-server
```

2. Verify video format is supported (MP4, AVI, MOV, MKV)

3. Try a shorter video (30-60 seconds)

4. Check disk space:
```bash
df -h
```

### Out of Memory

1. Check memory usage:
```bash
docker stats
```

2. Close other applications

3. Restart Docker:
```bash
docker compose down
docker compose up -d
```

### Permission Issues

Ensure the data directories are writable:
```bash
chmod -R 755 data logs
```

### Database Locked

Stop all services and restart:
```bash
docker compose down
rm -f data/bri.db-journal
docker compose up -d
```

## Stopping the Application

To stop all services:

```bash
./stop_test.sh
```

Or manually:

```bash
docker compose down
```

This will stop and remove containers but **preserve your data** in the `data/` directory.

To also remove all data (reset to fresh state):

```bash
docker compose down -v
rm -rf data/* logs/*
```

## Restarting Services

Restart all services:
```bash
docker compose restart
```

Restart specific service:
```bash
docker compose restart mcp-server
```

## Rebuilding After Code Changes

If you've made changes to the code:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Configuration

All configuration is in the `.env` file. After changing values, restart services:

```bash
docker compose down
docker compose up -d
```

Key configuration options:

- `GROQ_API_KEY` - Your Groq API key (required)
- `MAX_FRAMES_PER_VIDEO` - Maximum frames to extract (default: 100)
- `FRAME_EXTRACTION_INTERVAL` - Seconds between frames (default: 2.0)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)
- `CACHE_TTL_HOURS` - How long to cache results (default: 24)

## Performance Tips

1. **Use shorter videos** - 30-60 seconds is ideal for testing
2. **Enable Redis** - Already enabled by default for caching
3. **Adjust frame extraction** - Increase `FRAME_EXTRACTION_INTERVAL` for faster processing
4. **Monitor resources** - Use `docker stats` to watch memory/CPU
5. **Clean up old data** - Periodically remove old videos and frames

## Data Backup

Back up your data:
```bash
tar -czf bri-backup-$(date +%Y%m%d).tar.gz data/ logs/
```

Restore from backup:
```bash
docker compose down
tar -xzf bri-backup-YYYYMMDD.tar.gz
docker compose up -d
```

## Common Issues

### "Cannot connect to MCP Server"
- MCP Server may still be starting (wait 30-60 seconds)
- Check logs: `docker compose logs mcp-server`
- Verify it's running: `docker compose ps`

### "Redis connection failed"
- Application works without Redis (caching disabled)
- Check Redis status: `docker compose ps redis`
- Restart Redis: `docker compose restart redis`

### "GROQ API Error"
- Verify your API key in `.env`
- Check you have API credits available
- Check internet connectivity

### "Video upload failed"
- Check disk space: `df -h`
- Verify file format (MP4, AVI, MOV, MKV)
- Check file size (< 500MB recommended)

## Next Steps

After successful testing:

1. **Document Issues** - Note any bugs or problems
2. **Test Different Videos** - Try various formats and lengths
3. **Stress Test** - Upload multiple videos simultaneously
4. **Review Logs** - Check for warnings or errors
5. **Performance Testing** - Measure response times
6. **Plan Production** - Prepare for production deployment

## Support

### Useful Resources
- [README.md](README.md) - Project overview
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Detailed checklist
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Troubleshooting guide
- [docker-compose.yml](docker-compose.yml) - Service configuration

### Quick Commands Reference

```bash
# Deploy
./deploy_test.sh

# Stop
./stop_test.sh

# View logs
docker compose logs -f

# Check status
docker compose ps

# Restart
docker compose restart

# Clean up
docker compose down
docker system prune

# Rebuild
docker compose build --no-cache
```

## Success Criteria

Your deployment is successful when:

- ✅ All three services are running (`docker compose ps`)
- ✅ You can access http://localhost:8501
- ✅ You can upload a video
- ✅ Video processing completes successfully
- ✅ You get responses to queries
- ✅ Timestamps work and navigate the video
- ✅ No critical errors in logs

## Getting Help

If you encounter issues:

1. Check the logs: `docker compose logs`
2. Review this guide's Troubleshooting section
3. Check service health: `curl http://localhost:8000/health`
4. Verify configuration in `.env`
5. Try restarting: `docker compose restart`

---

**Happy Testing!** 🎉

For questions or issues, check the documentation in the `docs/` directory.
