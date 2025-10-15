# BRI (Brianna) - Video Analysis Agent

BRI is an open-source, empathetic multimodal agent for video processing that enables users to upload videos and ask natural language questions to receive context-aware, conversational responses.

> **🚀 New to BRI?** Check out the [Quick Start Guide](QUICKSTART.md) to get up and running in 5 minutes!

## Features

- 🎥 **Video Upload & Management**: Drag-and-drop upload with library view
- 💬 **Conversational Interface**: Chat naturally about your video content
- 🔍 **Multimodal Analysis**: Frame captioning, audio transcription, object detection
- 🧠 **Smart Memory**: Maintains conversation history for seamless follow-ups
- 🎨 **Warm UI/UX**: Feminine design touches with soft colors and friendly interactions
- ⚡ **Fast Responses**: Intelligent caching and optimized processing

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Groq API key ([Get one here](https://console.groq.com))
- Redis (optional, for caching)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bri-video-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

4. Initialize the database:
```bash
python scripts/init_db.py
```

5. (Optional) Validate your setup:
```bash
python scripts/validate_setup.py
```

### Running the Application

1. Start the MCP server (in one terminal):
```bash
python mcp_server/main.py
```

2. Start the Streamlit UI (in another terminal):
```bash
streamlit run app.py
```

3. Open your browser to `http://localhost:8501`

## Project Structure

```
bri-video-agent/
├── models/          # Data models and schemas
├── services/        # Core business logic
├── tools/           # Video processing tools
├── mcp_server/      # Model Context Protocol server
├── ui/              # Streamlit UI components
├── storage/         # Database and file storage
├── scripts/         # Utility scripts
└── tests/           # Test suite
```

## Configuration

All configuration is managed through environment variables in the `.env` file. See `.env.example` for all available options.

### Required Configuration

- **`GROQ_API_KEY`**: Your Groq API key (required)
  - Get one at [console.groq.com](https://console.groq.com)
  - The application will not start without this

### Optional Configuration

#### Groq API Settings
- `GROQ_MODEL`: LLM model to use (default: `llama-3.1-70b-versatile`)
- `GROQ_TEMPERATURE`: Response creativity (0-2, default: `0.7`)
- `GROQ_MAX_TOKENS`: Maximum response length (default: `1024`)

#### Redis Caching
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379`)
- `REDIS_ENABLED`: Enable/disable Redis caching (default: `true`)
  - Falls back gracefully if Redis is unavailable

#### Storage Paths
- `DATABASE_PATH`: SQLite database location (default: `data/bri.db`)
- `VIDEO_STORAGE_PATH`: Uploaded videos directory (default: `data/videos`)
- `FRAME_STORAGE_PATH`: Extracted frames directory (default: `data/frames`)
- `CACHE_STORAGE_PATH`: Processing cache directory (default: `data/cache`)

#### MCP Server
- `MCP_SERVER_HOST`: Server host (default: `localhost`)
- `MCP_SERVER_PORT`: Server port (default: `8000`)

#### Processing Settings
- `MAX_FRAMES_PER_VIDEO`: Maximum frames to extract (default: `100`)
- `FRAME_EXTRACTION_INTERVAL`: Seconds between frames (default: `2.0`)
- `CACHE_TTL_HOURS`: Cache expiration time (default: `24`)

#### Memory & Performance
- `MAX_CONVERSATION_HISTORY`: Messages to keep in context (default: `10`)
- `TOOL_EXECUTION_TIMEOUT`: Tool timeout in seconds (default: `120`)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: `30`)
- `LAZY_LOAD_BATCH_SIZE`: Images per lazy load batch (default: `3`)

#### Application Settings
- `DEBUG`: Enable debug mode (default: `false`)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)

### Configuration Validation

The application validates configuration on startup and will:
- ✗ **Fail** if required values are missing or invalid
- ⚠️ **Warn** about suboptimal settings (e.g., Redis disabled, debug mode enabled)
- ✓ **Create** necessary directories automatically

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/unit/test_memory.py
```

### Project Documentation

- [Requirements](.kiro/specs/bri-video-agent/requirements.md)
- [Design](.kiro/specs/bri-video-agent/design.md)
- [Implementation Tasks](.kiro/specs/bri-video-agent/tasks.md)

## Technology Stack

- **Frontend**: Streamlit
- **LLM**: Groq API (Llama 3.1)
- **Video Processing**: OpenCV, BLIP, Whisper, YOLOv8
- **API Server**: FastAPI
- **Caching**: Redis
- **Database**: SQLite

## Troubleshooting

### Common Issues

#### "GROQ_API_KEY is required"
- Make sure you've created a `.env` file (copy from `.env.example`)
- Add your Groq API key: `GROQ_API_KEY=your_key_here`
- Get a key at [console.groq.com](https://console.groq.com)

#### "Connection refused" when accessing UI
- Make sure both the MCP server and Streamlit are running
- Check that ports 8000 (MCP) and 8501 (Streamlit) are available
- Try accessing `http://localhost:8501` directly

#### Redis connection errors
- Redis is optional - set `REDIS_ENABLED=false` in `.env` to disable
- Or install Redis: `brew install redis` (Mac) or `apt-get install redis` (Linux)
- Start Redis: `redis-server`

#### Video processing is slow
- Reduce `MAX_FRAMES_PER_VIDEO` for faster processing
- Increase `FRAME_EXTRACTION_INTERVAL` to extract fewer frames
- Enable Redis caching for repeated queries

#### Out of memory errors
- Reduce `MAX_FRAMES_PER_VIDEO` to process fewer frames
- Reduce `LAZY_LOAD_BATCH_SIZE` for lower memory usage
- Process shorter videos or split long videos into segments

### Getting Help

- Check the [Requirements](.kiro/specs/bri-video-agent/requirements.md) document
- Review the [Design](.kiro/specs/bri-video-agent/design.md) document
- Open an issue on GitHub with:
  - Your configuration (mask sensitive values)
  - Error messages
  - Steps to reproduce

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
