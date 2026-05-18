# BRI Video Agent - Deployment Files

This directory contains everything needed to deploy and test the BRI Video Agent using Docker.

## 🚀 Quick Start

**New to deployment?** Start here:

1. Run preflight check: `./preflight_check.sh`
2. Edit `.env` and add your Groq API key
3. Deploy: `./deploy_test.sh`
4. Access: http://localhost:8501

For detailed instructions, see [QUICK_START.md](QUICK_START.md).

## 📁 Deployment Files

### Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `deploy_test.sh` | Main deployment script | `./deploy_test.sh` |
| `stop_test.sh` | Stop deployment | `./stop_test.sh` |
| `preflight_check.sh` | Pre-deployment checks | `./preflight_check.sh` |

### Docker Configuration

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates all services |
| `Dockerfile.mcp` | MCP Server container |
| `Dockerfile.ui` | Streamlit UI container |
| `.dockerignore` | Excludes files from builds |
| `.env` | Environment configuration |
| `.env.example` | Configuration template |

### Documentation

| File | Description | Best For |
|------|-------------|----------|
| `QUICK_START.md` | 5-minute quick start | First-time users |
| `DEPLOY_TO_TEST.md` | Comprehensive guide | Detailed deployment |
| `TEST_CHECKLIST.md` | Testing checklist | Systematic testing |
| `DEPLOYMENT_ARCHITECTURE.md` | Architecture diagrams | Understanding system |
| `DEPLOYMENT_SUMMARY.md` | Overview & summary | Quick reference |
| `DEPLOYMENT_README.md` | This file | Navigation |

## 🎯 Choose Your Path

### Path 1: Quick Deploy (5 minutes)
For those who want to get started immediately:

```bash
./preflight_check.sh  # Optional
nano .env              # Add API key
./deploy_test.sh       # Deploy
```

Then open http://localhost:8501

**Read**: [QUICK_START.md](QUICK_START.md)

### Path 2: Careful Deploy (15 minutes)
For those who want to understand what they're deploying:

1. **Read**: [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)
2. **Run**: `./preflight_check.sh`
3. **Configure**: Edit `.env` with your settings
4. **Read**: [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)
5. **Deploy**: `./deploy_test.sh`
6. **Test**: Follow [TEST_CHECKLIST.md](TEST_CHECKLIST.md)

### Path 3: Developer Deploy (30 minutes)
For developers who want to customize:

1. Review architecture and code
2. Customize `docker-compose.yml` if needed
3. Adjust `.env` configuration
4. Build: `docker compose build`
5. Start: `docker compose up -d`
6. Monitor: `docker compose logs -f`

**Read**: Full [README.md](README.md) and [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)

## 📋 What Gets Deployed

### Three Docker Containers

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Redis     │  │ MCP Server  │  │ Streamlit   │
│   :6379     │  │   :8000     │  │   :8501     │
└─────────────┘  └─────────────┘  └─────────────┘
      │                 │                 │
      └─────────────────┴─────────────────┘
                        │
                  ┌─────▼─────┐
                  │   Data    │
                  │  Volumes  │
                  └───────────┘
```

### Data Persistence

All data stored in local directories:
- `./data/videos/` - Your uploaded videos
- `./data/frames/` - Extracted video frames
- `./data/bri.db` - SQLite database
- `./logs/` - Application logs

Data persists even when containers are stopped.

## ⚡ Common Commands

### Deploy & Stop
```bash
./deploy_test.sh    # Deploy all services
./stop_test.sh      # Stop all services
```

### Monitor
```bash
docker compose ps              # Service status
docker compose logs -f         # All logs
docker compose logs -f mcp-server  # Specific service
docker stats                   # Resource usage
```

### Manage
```bash
docker compose restart         # Restart all
docker compose restart mcp-server  # Restart one
docker compose down           # Stop and remove
docker compose down -v        # Stop and remove data
```

### Health Checks
```bash
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8501/_stcore/health  # Streamlit
docker compose exec redis redis-cli ping  # Redis
```

## 🐛 Troubleshooting

### Quick Fixes

**Services won't start**
```bash
docker compose logs
docker compose restart
```

**Port already in use**
```bash
docker compose down
# Stop conflicting service
./deploy_test.sh
```

**API key error**
```bash
nano .env  # Fix API key
docker compose restart
```

**Need fresh start**
```bash
docker compose down -v
rm -rf data/* logs/*
./deploy_test.sh
```

For more troubleshooting, see [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#troubleshooting).

## ✅ Testing

### Quick Test (2 minutes)
1. Open http://localhost:8501
2. Upload a video
3. Ask a question
4. Verify response

### Full Test (20 minutes)
Follow the comprehensive [TEST_CHECKLIST.md](TEST_CHECKLIST.md).

### Test Scenarios
- Upload multiple videos
- Test all query types (visual, audio, objects)
- Test timestamp navigation
- Test conversation memory
- Check error handling

## 📊 Performance

### Expected Times
- **First deployment**: 10-15 minutes
- **Subsequent deployments**: 1 minute
- **Video processing**: 60-120 seconds/minute of video
- **Query response**: 2-5 seconds
- **Cached response**: <1 second

### Resource Usage
- **Memory**: 2-4 GB
- **CPU**: 20-40% average
- **Disk**: 5+ GB (more with videos)

## 🔒 Security

- API keys stored in `.env` (git-ignored)
- Containers isolated on internal network
- Only necessary ports exposed
- Data stored locally
- No telemetry or external tracking

## 📚 Documentation Index

### For End Users
- [QUICK_START.md](QUICK_START.md) - Get started in 5 minutes
- [TEST_CHECKLIST.md](TEST_CHECKLIST.md) - Testing guide

### For Operators
- [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md) - Full deployment guide
- [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) - Overview

### For Developers
- [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) - Architecture
- [README.md](README.md) - Project documentation
- [docker-compose.yml](docker-compose.yml) - Service config

## 🆘 Getting Help

1. **Check logs**: `docker compose logs`
2. **Check health**: `curl http://localhost:8000/health`
3. **Review docs**: See files above
4. **Run checks**: `./preflight_check.sh`
5. **Fresh start**: `docker compose down && ./deploy_test.sh`

## 🎓 Learning Path

**New to Docker?**
1. Start with [QUICK_START.md](QUICK_START.md)
2. Run `./deploy_test.sh` and explore
3. Read [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)
4. Experiment with `docker compose` commands

**Experienced with Docker?**
1. Review [docker-compose.yml](docker-compose.yml)
2. Customize `.env` as needed
3. Read [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)
4. Deploy and extend as needed

## 🚀 Next Steps

After successful deployment:

1. ✅ Test all features (use [TEST_CHECKLIST.md](TEST_CHECKLIST.md))
2. ✅ Monitor performance (`docker stats`)
3. ✅ Review logs for issues (`docker compose logs`)
4. ✅ Set up backups (see [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md#backup))
5. ✅ Plan production deployment if needed

## 📝 Deployment Checklist

- [ ] Docker installed and running
- [ ] Groq API key obtained
- [ ] `.env` configured
- [ ] Preflight check passed
- [ ] Services deployed
- [ ] All services healthy
- [ ] Can access UI at http://localhost:8501
- [ ] Video upload works
- [ ] Video processing works
- [ ] Queries return responses
- [ ] No critical errors in logs

## 🎉 You're Ready!

Everything you need to deploy BRI is in this directory.

**Quickest path**: Run `./deploy_test.sh` and open http://localhost:8501

**Need help?** Start with [QUICK_START.md](QUICK_START.md)

**Want details?** Read [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)

---

**Questions?** Check the documentation files above or review the logs with `docker compose logs`.

**Happy Testing!** 🚀
