# BRI Scripts Directory

This directory contains utility scripts for development, deployment, and database management.

## Development Scripts

### `start_dev.sh` (Linux/Mac)
Starts BRI in development mode with all services running locally.

**Usage:**
```bash
chmod +x scripts/start_dev.sh
./scripts/start_dev.sh
```

**What it does:**
- Validates environment variables
- Creates necessary directories
- Initializes database
- Starts Redis (if available)
- Starts MCP server on port 8000
- Starts Streamlit UI on port 8501

### `start_dev.bat` (Windows)
Windows version of the development startup script.

**Usage:**
```cmd
scripts\start_dev.bat
```

## Production Scripts

### `start_prod.sh`
Starts BRI in production mode using Docker Compose.

**Usage:**
```bash
chmod +x scripts/start_prod.sh
./scripts/start_prod.sh
```

**What it does:**
- Validates environment variables
- Creates data directories
- Builds Docker images
- Starts all services (Redis, MCP Server, Streamlit UI)
- Initializes database in container
- Displays service URLs

### `stop_prod.sh`
Stops all production Docker services.

**Usage:**
```bash
chmod +x scripts/stop_prod.sh
./scripts/stop_prod.sh
```

## Database Scripts

### `init_db.py`
Initializes the SQLite database with required tables for local development.

**Usage:**
```bash
python scripts/init_db.py
```

**What it does:**
- Creates `data/bri.db` if it doesn't exist
- Creates tables: `videos`, `memory`, `video_context`
- Creates indexes for performance
- Validates schema

### `init_docker_db.py`
Database initialization script for Docker deployments.

**Usage:**
```bash
# Inside Docker container
python scripts/init_docker_db.py

# From host (via docker-compose)
docker-compose exec mcp-server python scripts/init_docker_db.py
```

## Testing Scripts

### `test_*.py`
Various test scripts for validating components:

- `test_audio_transcriber.py` - Test Whisper audio transcription
- `test_cache_layer.py` - Test Redis caching
- `test_chat_window.py` - Test chat UI component
- `test_context_builder.py` - Test context aggregation
- `test_conversation_history.py` - Test memory management
- `test_error_handler.py` - Test error handling
- `test_frame_extractor.py` - Test OpenCV frame extraction
- `test_groq_agent.py` - Test Groq agent integration
- `test_image_captioner.py` - Test BLIP captioning
- `test_mcp_server.py` - Test MCP server endpoints
- `test_object_detector.py` - Test YOLO object detection
- `test_streamlit_ui.py` - Test Streamlit UI
- `test_tool_router.py` - Test tool routing logic
- `test_video_library.py` - Test video library component
- `test_video_player.py` - Test video player component
- `test_video_processing.py` - Test end-to-end video processing
- `test_video_upload.py` - Test video upload functionality

**Usage:**
```bash
python scripts/test_<component>.py
```

### `validate_setup.py`
Validates that all dependencies and configurations are correct.

**Usage:**
```bash
python scripts/validate_setup.py
```

**What it checks:**
- Python version
- Required packages installed
- Environment variables set
- Database accessible
- Redis connection (optional)
- File permissions

## Demo Scripts

### `demo_error_handler.py`
Demonstrates error handling capabilities.

### `demo_suggestions_integration.py`
Demonstrates follow-up suggestion generation.

## Common Tasks

### First-time Setup
```bash
# Linux/Mac
chmod +x scripts/*.sh
python scripts/init_db.py
./scripts/start_dev.sh

# Windows
python scripts\init_db.py
scripts\start_dev.bat
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test
python scripts/test_frame_extractor.py
```

### Production Deployment
```bash
# Start services
./scripts/start_prod.sh

# View logs
docker-compose logs -f

# Stop services
./scripts/stop_prod.sh
```

### Database Management
```bash
# Initialize database
python scripts/init_db.py

# Backup database
cp data/bri.db data/bri.db.backup

# Reset database (WARNING: deletes all data)
rm data/bri.db
python scripts/init_db.py
```

## Troubleshooting

### Permission Denied (Linux/Mac)
```bash
chmod +x scripts/*.sh
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8501  # Streamlit
lsof -i :8000  # MCP Server
lsof -i :6379  # Redis

# Kill process
kill -9 <PID>
```

### Database Locked
```bash
# Stop all services
./scripts/stop_prod.sh  # or Ctrl+C for dev

# Remove lock file
rm data/bri.db-journal

# Restart services
./scripts/start_dev.sh
```

### Redis Not Available
The application will work without Redis, but caching will be disabled. To install Redis:

```bash
# Linux (Ubuntu/Debian)
sudo apt-get install redis-server

# Mac
brew install redis

# Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

## Environment Variables

All scripts respect these environment variables from `.env`:

- `GROQ_API_KEY` - Required for LLM functionality
- `REDIS_URL` - Redis connection URL (optional)
- `DATABASE_PATH` - SQLite database path
- `VIDEO_STORAGE_PATH` - Video storage directory
- `FRAME_STORAGE_PATH` - Frame storage directory
- `CACHE_STORAGE_PATH` - Cache storage directory
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Contributing

When adding new scripts:
1. Add clear comments explaining what the script does
2. Include error handling
3. Make scripts executable: `chmod +x script.sh`
4. Update this README with usage instructions
5. Add validation for required dependencies
