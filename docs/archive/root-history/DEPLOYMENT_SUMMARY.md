# BRI Video Agent - Deployment Summary

## Overview

The BRI Video Agent is now ready for deployment and testing. This document summarizes the deployment setup and how to get started.

## What's Been Added

### 🚀 Deployment Scripts

1. **`deploy_test.sh`** - Main deployment script
   - Checks Docker availability
   - Validates environment configuration
   - Creates necessary directories
   - Builds Docker images
   - Starts all services
   - Monitors service health
   - Displays access URLs

2. **`stop_test.sh`** - Stop deployment script
   - Gracefully stops all services
   - Preserves data volumes
   - Shows cleanup options

### 📚 Documentation

1. **`DEPLOY_TO_TEST.md`** - Comprehensive deployment guide
   - Prerequisites and setup
   - Detailed deployment instructions
   - Testing scenarios and checklists
   - Troubleshooting guide
   - Performance tips
   - Common issues and solutions

2. **`QUICK_START.md`** - Quick reference guide
   - 5-minute quick start
   - Essential commands
   - Common troubleshooting
   - Access points

3. **`TEST_CHECKLIST.md`** - Systematic testing checklist
   - Pre-test setup
   - Basic functionality tests
   - Query testing for all capabilities
   - Advanced feature tests
   - System health checks
   - Performance metrics

4. **`DEPLOYMENT_ARCHITECTURE.md`** - Architecture diagrams
   - Container architecture
   - Data flow diagrams
   - Storage structure
   - Network communication
   - Scaling considerations
   - Security overview
   - Backup strategy

### 🔧 Configuration

1. **`.env`** - Environment configuration file
   - Pre-configured with sensible defaults
   - Placeholder for GROQ_API_KEY
   - Docker-optimized settings (using service names)

### ✨ Improvements

1. **`Dockerfile.ui`** - Updated
   - Added `curl` for health checks
   - Ensures health check endpoint works

2. **`README.md`** - Updated
   - Added Docker deployment section at top
   - Links to new deployment documentation
   - Clearer quick start path

## How to Deploy

### Step 1: Configure API Key

Edit the `.env` file and add your Groq API key:

```bash
nano .env
```

Update this line:
```
GROQ_API_KEY=your_actual_api_key_here
```

### Step 2: Deploy

Run the deployment script:

```bash
./deploy_test.sh
```

This will:
1. Check Docker is running
2. Validate configuration
3. Create data directories
4. Build Docker images (5-10 minutes first time)
5. Start all services
6. Wait for health checks
7. Display access URLs

### Step 3: Access

Open your browser to:
```
http://localhost:8501
```

### Step 4: Test

Follow the testing guide in `TEST_CHECKLIST.md` or try a quick test:

1. Upload a short video (30-60 seconds)
2. Wait for processing (~30-90 seconds)
3. Ask: "What's happening in this video?"
4. Click timestamps to navigate

## What Gets Deployed

### Three Docker Containers

1. **Redis** (port 6379)
   - Caching layer
   - Improves performance 10x for repeated queries
   - Health checked: `redis-cli ping`

2. **MCP Server** (port 8000)
   - Backend API server
   - Video processing tools
   - AI models (BLIP, Whisper, YOLOv8)
   - Health checked: `GET /health`
   - API docs: `http://localhost:8000/docs`

3. **Streamlit UI** (port 8501)
   - Frontend web interface
   - Conversational chat interface
   - Video player and library
   - Health checked: `GET /_stcore/health`

### Persistent Data

All data is stored in local directories (mounted as volumes):

- `./data/videos/` - Uploaded videos
- `./data/frames/` - Extracted frames
- `./data/bri.db` - SQLite database
- `./logs/` - Application logs

Data persists even when containers are stopped/restarted.

## Useful Commands

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f streamlit-ui
docker compose logs -f mcp-server
docker compose logs -f redis
```

### Check Status
```bash
# Service status
docker compose ps

# Resource usage
docker stats

# Health checks
curl http://localhost:8000/health
```

### Manage Services
```bash
# Stop
./stop_test.sh

# Restart
docker compose restart

# Restart specific service
docker compose restart mcp-server

# Rebuild after code changes
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Testing Checklist

Use `TEST_CHECKLIST.md` for systematic testing, or quick test:

- [ ] Services are running: `docker compose ps`
- [ ] Can access http://localhost:8501
- [ ] Can upload a video
- [ ] Processing completes successfully
- [ ] Can ask questions and get responses
- [ ] Timestamps work and navigate video
- [ ] No errors in logs: `docker compose logs`

## Troubleshooting

### Services Won't Start

1. Check Docker is running: `docker info`
2. Check ports aren't in use: `netstat -an | grep 8501`
3. Check logs: `docker compose logs`

### API Key Error

1. Verify API key in `.env` is correct
2. Restart services: `docker compose restart`

### Slow Performance

1. Wait for first-time model downloads
2. Check resources: `docker stats`
3. Close other applications
4. Try shorter videos (30-60 seconds)

### "Cannot Connect to MCP Server"

1. Wait 30-60 seconds - services still starting
2. Check MCP server logs: `docker compose logs mcp-server`
3. Verify it's healthy: `curl http://localhost:8000/health`

For more troubleshooting, see `DEPLOY_TO_TEST.md`.

## Performance Expectations

### First-Time Deployment
- Image build: 5-10 minutes
- Model downloads: 2-3 minutes
- Service startup: 30-60 seconds
- **Total: ~10-15 minutes**

### Subsequent Deployments
- Service startup: 30-60 seconds
- **Total: ~1 minute**

### Video Processing
- Frame extraction: 5-10 seconds
- Captioning: 15-30 seconds
- Transcription: 20-40 seconds
- Object detection: 10-20 seconds
- **Total: 60-120 seconds for 1-minute video**

### Queries
- First query: 3-5 seconds
- Cached queries: <1 second
- **With Redis: 10x faster**

## Architecture

```
┌─────────────────────────────────────────┐
│           Docker Network                │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Redis   │  │   MCP    │  │   UI   │ │
│  │  :6379   │  │  :8000   │  │ :8501  │ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       └─────────────┴────────────┘      │
│                     │                    │
│               ┌─────▼─────┐              │
│               │   Data    │              │
│               │  Volumes  │              │
│               └───────────┘              │
└─────────────────────────────────────────┘
```

## Data Flow

```
User → Streamlit UI → Groq Agent → MCP Server → Tools
                                       ↓
                                   Redis Cache
                                       ↓
                                  SQLite DB
                                       ↓
                                  File Storage
```

## Security

- API keys stored in `.env` (not committed to git)
- Containers use internal network
- Only necessary ports exposed
- Data stored locally
- No external dependencies except Groq API

## Backup

### Manual Backup
```bash
tar -czf bri-backup-$(date +%Y%m%d).tar.gz data/ .env
```

### Restore
```bash
docker compose down
tar -xzf bri-backup-YYYYMMDD.tar.gz
docker compose up -d
```

## Next Steps

1. ✅ Set your API key in `.env`
2. ✅ Run `./deploy_test.sh`
3. ✅ Open http://localhost:8501
4. ✅ Follow `TEST_CHECKLIST.md`
5. ✅ Report any issues

## Documentation Index

| Document | Purpose |
|----------|---------|
| `QUICK_START.md` | Get running in 5 minutes |
| `DEPLOY_TO_TEST.md` | Comprehensive deployment guide |
| `TEST_CHECKLIST.md` | Systematic testing checklist |
| `DEPLOYMENT_ARCHITECTURE.md` | Architecture and diagrams |
| `README.md` | Project overview |
| `docker-compose.yml` | Service configuration |
| `.env.example` | Configuration reference |

## Support

For questions or issues:

1. Check the documentation above
2. Review logs: `docker compose logs`
3. Check health: `curl http://localhost:8000/health`
4. Try the troubleshooting sections

## Success Criteria

Deployment is successful when:

✅ All services show "healthy" in `docker compose ps`  
✅ Can access http://localhost:8501  
✅ Can upload and process videos  
✅ Can query videos and get responses  
✅ Timestamps navigate the video  
✅ No critical errors in logs  

---

## Quick Reference

### Deploy
```bash
./deploy_test.sh
```

### Access
- **UI**: http://localhost:8501
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### Monitor
```bash
docker compose logs -f
docker compose ps
docker stats
```

### Stop
```bash
./stop_test.sh
```

---

**Ready to deploy!** 🚀

Follow the steps above and you'll have BRI running in ~15 minutes (first time) or ~1 minute (subsequent deployments).

For the quickest start, see `QUICK_START.md`.

For comprehensive testing, see `TEST_CHECKLIST.md`.

For troubleshooting, see `DEPLOY_TO_TEST.md`.
