# BRI Video Agent - Deployment Guide

This guide covers deployment options for the BRI Video Agent, including local development and production Docker deployments.

## Prerequisites

### For Local Development
- Python 3.11+
- Redis (optional, for caching)
- FFmpeg (for video processing)
- Git

### For Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+

## Environment Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd bri-video-agent
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Edit `.env` and add your API keys**
```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

## Local Development Deployment

### Linux/Mac

1. **Make scripts executable**
```bash
chmod +x scripts/start_dev.sh
chmod +x scripts/start_prod.sh
chmod +x scripts/stop_prod.sh
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Start development server**
```bash
./scripts/start_dev.sh
```

This script will:
- Check environment variables
- Create necessary directories
- Initialize the database
- Start Redis (if available)
- Start MCP server on port 8000
- Start Streamlit UI on port 8501

4. **Access the application**
- Streamlit UI: http://localhost:8501
- MCP Server: http://localhost:8000

5. **Stop services**
Press `Ctrl+C` in the terminal where the script is running.

### Windows

1. **Install Python dependencies**
```cmd
pip install -r requirements.txt
```

2. **Start development server**
```cmd
scripts\start_dev.bat
```

3. **Access the application**
- Streamlit UI: http://localhost:8501
- MCP Server: http://localhost:8000

4. **Stop services**
Press `Ctrl+C` in the command prompt.

## Production Docker Deployment

### Quick Start

1. **Start production services**
```bash
./scripts/start_prod.sh
```

This script will:
- Validate environment variables
- Build Docker images
- Start all services (Redis, MCP Server, Streamlit UI)
- Initialize the database
- Display service URLs

2. **Access the application**
- Streamlit UI: http://localhost:8501
- MCP Server: http://localhost:8000
- Redis: localhost:6379

3. **Stop services**
```bash
./scripts/stop_prod.sh
```

Or manually:
```bash
docker-compose down
```

### Manual Docker Deployment

1. **Build images**
```bash
docker-compose build
```

2. **Start services**
```bash
docker-compose up -d
```

3. **View logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f streamlit-ui
docker-compose logs -f mcp-server
docker-compose logs -f redis
```

4. **Check service status**
```bash
docker-compose ps
```

5. **Restart services**
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart streamlit-ui
```

6. **Stop and remove containers**
```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Service Architecture

The Docker deployment consists of three services:

### 1. Redis (Port 6379)
- Caching layer for tool results
- Improves response times for repeated queries
- Data persisted in Docker volume

### 2. MCP Server (Port 8000)
- FastAPI server exposing video processing tools
- Handles frame extraction, captioning, transcription, object detection
- Health check endpoint: http://localhost:8000/health

### 3. Streamlit UI (Port 8501)
- User interface for video upload and chat
- Communicates with MCP server for processing
- Health check endpoint: http://localhost:8501/_stcore/health

## Data Persistence

### Docker Volumes
- `redis-data`: Redis cache data
- `./data`: Video files, frames, database (bind mount)
- `./logs`: Application logs (bind mount)

### Database Location
- Development: `./data/bri.db`
- Docker: `/app/data/bri.db` (mounted from host)

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | - | Groq API key for LLM |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection URL |
| `DATABASE_PATH` | No | `./data/bri.db` | SQLite database path |
| `VIDEO_STORAGE_PATH` | No | `./data/videos` | Video storage directory |
| `FRAME_STORAGE_PATH` | No | `./data/frames` | Frame storage directory |
| `CACHE_STORAGE_PATH` | No | `./data/cache` | Cache storage directory |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MCP_SERVER_URL` | No | `http://localhost:8000` | MCP server URL (for UI) |

### Port Configuration

To change default ports, edit `docker-compose.yml`:

```yaml
services:
  streamlit-ui:
    ports:
      - "8080:8501"  # Change 8080 to your desired port
  
  mcp-server:
    ports:
      - "9000:8000"  # Change 9000 to your desired port
```

## Troubleshooting

### Services won't start

1. **Check if ports are already in use**
```bash
# Linux/Mac
lsof -i :8501
lsof -i :8000
lsof -i :6379

# Windows
netstat -ano | findstr :8501
netstat -ano | findstr :8000
netstat -ano | findstr :6379
```

2. **Check Docker logs**
```bash
docker-compose logs
```

3. **Verify environment variables**
```bash
docker-compose config
```

### Database initialization fails

```bash
# Manually initialize database
docker-compose exec mcp-server python scripts/init_docker_db.py
```

### Redis connection issues

```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### MCP Server not responding

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs mcp-server

# Restart service
docker-compose restart mcp-server
```

### Streamlit UI not loading

```bash
# Check health
curl http://localhost:8501/_stcore/health

# View logs
docker-compose logs streamlit-ui

# Restart service
docker-compose restart streamlit-ui
```

## Performance Tuning

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Redis Configuration

For production, consider:
- Increasing Redis memory limit
- Configuring persistence settings
- Setting up Redis replication

### Video Processing

- Adjust frame extraction intervals in config
- Limit maximum video file size
- Configure parallel processing workers

## Security Considerations

1. **API Keys**: Never commit `.env` file to version control
2. **Network**: Use Docker networks to isolate services
3. **Volumes**: Set appropriate file permissions on mounted volumes
4. **Firewall**: Restrict access to ports 8000, 8501, 6379
5. **HTTPS**: Use reverse proxy (nginx) for SSL/TLS in production

## Monitoring

### Health Checks

All services include health checks:
- Redis: `redis-cli ping`
- MCP Server: `GET /health`
- Streamlit UI: `GET /_stcore/health`

### Logs

View logs in real-time:
```bash
# All services
docker-compose logs -f

# Specific service with timestamps
docker-compose logs -f --timestamps streamlit-ui
```

### Metrics

Consider adding:
- Prometheus for metrics collection
- Grafana for visualization
- Application performance monitoring (APM)

## Backup and Recovery

### Backup Data

```bash
# Backup database and videos
tar -czf bri-backup-$(date +%Y%m%d).tar.gz data/

# Backup Docker volumes
docker run --rm -v bri-redis-data:/data -v $(pwd):/backup alpine tar -czf /backup/redis-backup.tar.gz /data
```

### Restore Data

```bash
# Restore from backup
tar -xzf bri-backup-YYYYMMDD.tar.gz

# Restart services
docker-compose restart
```

## Scaling

For production deployments with multiple users:

1. **Use PostgreSQL** instead of SQLite
2. **Add load balancer** for multiple MCP server instances
3. **Use S3/MinIO** for video storage
4. **Add message queue** (Celery + RabbitMQ) for async processing
5. **Deploy on Kubernetes** for orchestration

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Review documentation: `README.md`
- Open an issue on GitHub

## License

[Your License Here]
