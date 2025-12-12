# BRI Video Agent - Deployment Architecture

## Docker Compose Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                        Host Machine                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Docker Network (bri-network)                   │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   Redis      │  │  MCP Server  │  │ Streamlit UI │    │ │
│  │  │   Container  │  │   Container  │  │   Container  │    │ │
│  │  │              │  │              │  │              │    │ │
│  │  │  Port: 6379  │  │  Port: 8000  │  │  Port: 8501  │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  │         │                  │                  │            │ │
│  │         └──────────────────┴──────────────────┘            │ │
│  │                            │                                │ │
│  │                    ┌───────▼────────┐                       │ │
│  │                    │  Shared Volume │                       │ │
│  │                    │                │                       │ │
│  │                    │  ./data/       │                       │ │
│  │                    │  ./logs/       │                       │ │
│  │                    └────────────────┘                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Access Points:                                                 │
│  • http://localhost:8501  (Streamlit UI)                       │
│  • http://localhost:8000  (MCP Server API)                     │
│  • http://localhost:6379  (Redis)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Container Details

### Redis Container
- **Image**: redis:7-alpine
- **Purpose**: Caching layer for improved performance
- **Port**: 6379
- **Volume**: redis-data (persistent)
- **Health Check**: `redis-cli ping`

### MCP Server Container
- **Image**: Built from Dockerfile.mcp
- **Purpose**: Backend API server, tool orchestration, AI models
- **Port**: 8000
- **Models Loaded**:
  - BLIP (image captioning)
  - Whisper (audio transcription)
  - YOLOv8 (object detection)
- **Health Check**: GET /health
- **Restart Policy**: unless-stopped

### Streamlit UI Container
- **Image**: Built from Dockerfile.ui
- **Purpose**: Frontend web interface
- **Port**: 8501
- **Health Check**: GET /_stcore/health
- **Restart Policy**: unless-stopped

## Data Flow

### Video Upload Flow
```
User Browser
    │
    ├─► [Upload Video] ─► Streamlit UI Container
    │                          │
    │                          ├─► Save to ./data/videos/
    │                          └─► Create DB entry
    │
    └─► [Process Video] ─► MCP Server Container
                                │
                                ├─► Extract Frames (OpenCV)
                                ├─► Caption Frames (BLIP)
                                ├─► Transcribe Audio (Whisper)
                                ├─► Detect Objects (YOLO)
                                │
                                ├─► Save to ./data/frames/
                                ├─► Cache in Redis
                                └─► Store results in DB
```

### Query Flow
```
User Question
    │
    ├─► Streamlit UI Container
    │       │
    │       ├─► Groq Agent (LLM)
    │       │       │
    │       │       └─► Determine intent & tools
    │       │
    │       └─► MCP Server Container
    │               │
    │               ├─► Check Redis Cache
    │               │       ├─► Cache Hit ✓ (fast!)
    │               │       └─► Cache Miss ✗
    │               │
    │               ├─► Execute Tools
    │               │   ├─► Frame Captioning
    │               │   ├─► Audio Transcription
    │               │   └─► Object Detection
    │               │
    │               ├─► Store in Cache
    │               └─► Return Results
    │
    └─► Display Response
            ├─► Show text
            ├─► Show timestamps
            └─► Show frame thumbnails
```

## Storage Structure

```
project/
├── data/
│   ├── videos/              # Uploaded video files
│   │   ├── video1.mp4
│   │   └── video2.mp4
│   ├── frames/              # Extracted video frames
│   │   ├── video1/
│   │   │   ├── frame_001.jpg
│   │   │   └── frame_002.jpg
│   │   └── video2/
│   ├── cache/               # Cached processing results
│   ├── backups/             # Database backups
│   └── bri.db              # SQLite database
│
└── logs/
    ├── bri.log             # Application logs
    ├── bri_errors.log      # Error logs
    └── bri_performance.log # Performance metrics
```

## Network Communication

```
┌─────────────┐         ┌─────────────┐
│  External   │         │   Docker    │
│   World     │         │   Network   │
│             │         │             │
│  Browser    ├────────►│ Streamlit  │
│             │  8501   │    UI      │
└─────────────┘         └──────┬──────┘
                               │ HTTP
                               │
                        ┌──────▼──────┐
                        │  MCP Server │
                        │             │
                        └──────┬──────┘
                               │
                               │
                        ┌──────▼──────┐
                        │    Redis    │
                        │             │
                        └─────────────┘
```

## Health Monitoring

Each service includes health checks:

### Redis
```bash
Command: redis-cli ping
Expected: PONG
Interval: 10s
Timeout: 5s
```

### MCP Server
```bash
Command: GET http://localhost:8000/health
Expected: {"status": "healthy", ...}
Interval: 30s
Timeout: 10s
Start Period: 40s
```

### Streamlit UI
```bash
Command: GET http://localhost:8501/_stcore/health
Expected: 200 OK
Interval: 30s
Timeout: 10s
Start Period: 40s
```

## Scaling Considerations

### Horizontal Scaling
- **Streamlit UI**: Can run multiple instances behind load balancer
- **MCP Server**: Stateless, can scale horizontally
- **Redis**: Can use Redis Cluster for distributed caching

### Vertical Scaling
- **Memory**: 8GB+ recommended for production
- **CPU**: 4+ cores recommended
- **Storage**: SSD recommended for video I/O

### Performance Optimization
1. **Enable Redis**: 10x faster repeated queries
2. **Adjust Frame Extraction**: Balance quality vs. speed
3. **Use SSD**: Faster video and frame I/O
4. **Increase Workers**: More parallel processing
5. **CDN for Videos**: Offload video serving

## Security

### Container Security
- **Non-root Users**: Containers run as non-root
- **Network Isolation**: Services communicate via internal network
- **Volume Permissions**: Proper file permissions enforced

### Data Security
- **API Keys**: Stored in .env, not in images
- **Database**: File-based SQLite with proper permissions
- **Videos**: Stored locally, not exposed externally

### Network Security
- **Firewall**: Restrict external access to necessary ports
- **HTTPS**: Use reverse proxy (nginx/traefik) for SSL
- **Rate Limiting**: Built into MCP server

## Backup Strategy

### What to Backup
1. **Database**: `./data/bri.db`
2. **Videos**: `./data/videos/`
3. **Configuration**: `.env`

### Backup Command
```bash
tar -czf bri-backup-$(date +%Y%m%d).tar.gz data/ .env
```

### Automated Backups
```bash
# Add to crontab for daily backups
0 2 * * * cd /path/to/bri && tar -czf backups/bri-backup-$(date +\%Y\%m\%d).tar.gz data/ .env
```

## Disaster Recovery

### Service Failure
1. Check logs: `docker compose logs [service]`
2. Restart service: `docker compose restart [service]`
3. If persistent, rebuild: `docker compose up -d --build [service]`

### Data Corruption
1. Stop services: `docker compose down`
2. Restore from backup: `tar -xzf backup.tar.gz`
3. Restart: `docker compose up -d`

### Complete Reset
```bash
docker compose down -v
rm -rf data/* logs/*
./deploy_test.sh
```

## Monitoring & Observability

### Built-in Monitoring
- Health endpoints for all services
- Application logs in `./logs/`
- Performance metrics logged
- Error tracking

### External Monitoring (Optional)
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation
- **Sentry**: Error tracking

## Production Deployment

For production environments:

1. **Use docker-compose.prod.yml**: Production-optimized configuration
2. **Enable HTTPS**: Use reverse proxy with SSL certificates
3. **Set up monitoring**: Prometheus + Grafana recommended
4. **Configure backups**: Automated daily backups
5. **Set resource limits**: CPU and memory limits per container
6. **Use secrets**: Docker secrets for sensitive data
7. **Enable logging**: External log aggregation
8. **Set up alerts**: Alert on service failures

---

## Quick Reference

| Component | Port | Purpose | Health Check |
|-----------|------|---------|--------------|
| Streamlit UI | 8501 | Frontend | `/_stcore/health` |
| MCP Server | 8000 | Backend API | `/health` |
| Redis | 6379 | Caching | `redis-cli ping` |

| Directory | Purpose | Backup |
|-----------|---------|--------|
| `./data/videos` | Video files | Yes |
| `./data/frames` | Extracted frames | No (regenerable) |
| `./data/bri.db` | Database | Yes |
| `./logs/` | Application logs | Optional |

---

For more details, see:
- [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md) - Deployment guide
- [docker-compose.yml](docker-compose.yml) - Service configuration
- [QUICK_START.md](QUICK_START.md) - Quick start guide
