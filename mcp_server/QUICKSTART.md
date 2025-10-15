# MCP Server Quick Start Guide

## Prerequisites

1. Python 3.8+ installed
2. Virtual environment activated
3. Dependencies installed: `pip install -r requirements.txt`
4. Environment variables configured in `.env`

## Starting the Server

### Option 1: Using Python directly
```bash
python mcp_server/main.py
```

### Option 2: Using uvicorn
```bash
uvicorn mcp_server.main:app --host localhost --port 8000 --reload
```

### Option 3: Production mode
```bash
uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Verify Server is Running

Open your browser and navigate to:
- Server info: http://localhost:8000/
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs (Swagger UI)
- Available tools: http://localhost:8000/tools

## Quick Test

```bash
# List available tools
curl http://localhost:8000/tools

# Check health
curl http://localhost:8000/health

# Get cache stats
curl http://localhost:8000/cache/stats
```

## Common Issues

### Port Already in Use
If port 8000 is already in use, change the port in `.env`:
```bash
MCP_SERVER_PORT=8001
```

### Redis Connection Failed
If Redis is not available, the server will continue without caching. To enable caching:
1. Install Redis: https://redis.io/download
2. Start Redis: `redis-server`
3. Verify connection: `redis-cli ping`

### Models Not Loading
The first time you run the server, it will download AI models (BLIP, Whisper, YOLO). This may take several minutes and requires internet connection.

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Next Steps

1. Review the API documentation: [README.md](README.md)
2. Run integration tests: `python scripts/test_mcp_server_integration.py`
3. Integrate with the BRI agent layer (Task 11)
