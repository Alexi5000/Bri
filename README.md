# BRI (Brianna) - Video Analysis Agent

BRI is an open-source, empathetic multimodal agent for video processing that enables users to upload videos and ask natural language questions to receive context-aware, conversational responses.

> **🚀 New to BRI?** Check out the [Quick Start Guide](QUICKSTART.md) to get up and running in 5 minutes!

## Features

### Core Capabilities

- 🎥 **Video Upload & Management**: Drag-and-drop upload with library view and thumbnails
- 💬 **Conversational Interface**: Chat naturally about your video content with context awareness
- 🔍 **Multimodal Analysis**: 
  - Frame extraction and captioning (BLIP)
  - Audio transcription with timestamps (Whisper)
  - Object detection and tracking (YOLOv8)
- 🧠 **Smart Memory**: Maintains conversation history per video for seamless follow-ups
- 🎨 **Warm UI/UX**: Feminine design touches with soft colors and friendly interactions
- ⚡ **Fast Responses**: Intelligent Redis caching and optimized processing
- 🎯 **Intelligent Routing**: Automatically determines which tools to use based on your question
- 📍 **Timestamp Navigation**: Click timestamps in responses to jump to specific moments
- 💡 **Proactive Suggestions**: Get relevant follow-up questions after each response

### What You Can Ask

- **Content Questions**: "What's happening in this video?"
- **Timestamp Queries**: "What did they say at 2:30?"
- **Object Search**: "Show me all the cats in this video"
- **Transcript Search**: "Find when they mentioned 'deadline'"
- **Follow-ups**: "Tell me more about that" (BRI remembers context!)

### Design Philosophy

BRI is designed to be:
- **Empathetic**: Warm, supportive tone throughout
- **Accessible**: No technical knowledge required
- **Conversational**: Like discussing content with a knowledgeable friend
- **Privacy-Focused**: Local storage by default
- **Graceful**: Friendly error messages and fallback strategies

## Quick Start

### 🐳 Docker Deployment (Recommended for Testing)

The fastest way to get BRI up and running:

1. **Set your API key** in `.env`:
   ```bash
   nano .env
   # Update: GROQ_API_KEY=your_actual_key
   ```

2. **Deploy with one command**:
   ```bash
   ./deploy_test.sh
   ```

3. **Access the app**: http://localhost:8501

📖 **Full guide**: [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md) | ⚡ **Quick reference**: [QUICK_START.md](QUICK_START.md)

---

### 💻 Local Development Setup

For development and customization:

#### Prerequisites

- Python 3.9 or higher
- Groq API key ([Get one here](https://console.groq.com))
- Redis (optional, for caching)

#### Installation

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

## Documentation

📚 **[Complete Documentation Index](docs/INDEX.md)** - Find all documentation in one place

### User Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete guide to using BRI
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Solutions to common issues
- **[Configuration Reference](docs/CONFIGURATION.md)** - All configuration options explained

### Developer Documentation

- **[MCP Server API](mcp_server/README.md)** - API endpoints and tool documentation
- **[API Examples](docs/API_EXAMPLES.md)** - Practical code examples for API integration
- **[Requirements](.kiro/specs/bri-video-agent/requirements.md)** - Feature requirements
- **[Design](.kiro/specs/bri-video-agent/design.md)** - System architecture and design
- **[Implementation Tasks](.kiro/specs/bri-video-agent/tasks.md)** - Development task list

### Deployment Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Quick Start](QUICKSTART.md)** - Get started in 5 minutes

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/unit/test_memory.py

# Run integration tests
pytest tests/integration/
```

### Development Workflow

1. **Setup Development Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API key
   ```

2. **Run in Development Mode**:
   ```bash
   # Terminal 1: MCP Server with auto-reload
   python mcp_server/main.py
   
   # Terminal 2: Streamlit with auto-reload
   streamlit run app.py
   ```

3. **Run Tests Before Committing**:
   ```bash
   pytest
   ```

4. **Check Code Quality**:
   ```bash
   # Format code
   black .
   
   # Lint code
   flake8 .
   
   # Type checking
   mypy .
   ```

## Architecture

BRI uses a modular, layered architecture:

```
┌─────────────────────────────────────────┐
│         Streamlit UI Layer              │
│  (Chat, Library, Player, History)       │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Agent Layer                      │
│  (Groq Agent, Router, Memory, Context)  │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         MCP Server Layer                 │
│  (FastAPI, Tool Registry, Redis Cache)  │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│      Video Processing Tools              │
│  (OpenCV, BLIP, Whisper, YOLO)          │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Storage Layer                    │
│  (SQLite Database, File System)         │
└──────────────────────────────────────────┘
```

### Key Components

- **UI Layer**: Streamlit-based interface with warm, approachable design
- **Agent Layer**: Groq-powered conversational agent with intelligent tool routing
- **MCP Server**: FastAPI server exposing video processing capabilities
- **Tools Layer**: Open-source video processing tools (OpenCV, BLIP, Whisper, YOLO)
- **Storage Layer**: SQLite for metadata and memory, file system for videos and frames

For detailed architecture documentation, see [Design Document](.kiro/specs/bri-video-agent/design.md).

## Technology Stack

### Core Technologies

- **Frontend**: Streamlit with custom CSS
- **LLM**: Groq API (Llama 3.1 70B)
- **Video Processing**: 
  - OpenCV (frame extraction)
  - BLIP (image captioning)
  - Whisper (audio transcription)
  - YOLOv8 (object detection)
- **API Server**: FastAPI with CORS support
- **Caching**: Redis (optional but recommended)
- **Database**: SQLite
- **Language**: Python 3.9+

### Why These Technologies?

- **Groq**: Fast, high-quality LLM inference
- **Open-source tools**: No vendor lock-in, community-driven
- **Streamlit**: Rapid UI development with Python
- **SQLite**: Simple, reliable, no separate server needed
- **Redis**: Optional caching for performance boost

## API Reference

BRI exposes a REST API through the MCP server for programmatic access to video processing tools.

### Base URL

```
http://localhost:8000
```

### Key Endpoints

- `GET /` - Server information
- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /tools/{tool_name}/execute` - Execute a tool
- `POST /videos/{video_id}/process` - Batch process video
- `GET /cache/stats` - Cache statistics

For complete API documentation, see [MCP Server README](mcp_server/README.md).

## Troubleshooting

### Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Missing API key | Copy `.env.example` to `.env` and add your Groq API key |
| Connection refused | Ensure both MCP server and Streamlit are running |
| Redis errors | Set `REDIS_ENABLED=false` in `.env` (Redis is optional) |
| Slow processing | Reduce `MAX_FRAMES_PER_VIDEO` in `.env` |
| Out of memory | Reduce `MAX_FRAMES_PER_VIDEO` and `LAZY_LOAD_BATCH_SIZE` |

### Detailed Troubleshooting

For comprehensive troubleshooting, see the **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** which covers:

- Installation issues
- Configuration problems
- Server startup failures
- Video processing errors
- Performance optimization
- Database and cache issues
- Complete error message reference

### Getting Help

1. **Check Documentation**:
   - [User Guide](docs/USER_GUIDE.md) - How to use BRI
   - [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions
   - [Configuration Reference](docs/CONFIGURATION.md) - All settings explained

2. **Run Diagnostics**:
   ```bash
   python scripts/validate_setup.py
   ```

3. **Enable Debug Mode**:
   ```bash
   # In .env:
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

4. **Report Issues**:
   - Open a GitHub issue with:
     - Error messages and logs
     - Configuration (mask sensitive values)
     - Steps to reproduce
     - System information

## Contributing

We welcome contributions to BRI! Here's how you can help:

### Ways to Contribute

- 🐛 **Report Bugs**: Open an issue with details and reproduction steps
- 💡 **Suggest Features**: Share your ideas for new capabilities
- 📝 **Improve Documentation**: Help make docs clearer and more comprehensive
- 🔧 **Submit Pull Requests**: Fix bugs or implement features
- 🧪 **Write Tests**: Improve test coverage
- 🎨 **Enhance UI/UX**: Suggest or implement design improvements

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/bri-video-agent.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature-name`
8. Open a Pull Request

### Contribution Guidelines

- Follow existing code style and conventions
- Write tests for new features
- Update documentation as needed
- Keep commits focused and atomic
- Write clear commit messages
- Be respectful and constructive in discussions

### Code of Conduct

- Be welcoming and inclusive
- Respect differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

## License

[Add your license here - e.g., MIT, Apache 2.0, GPL]

## Acknowledgments

BRI is built with amazing open-source technologies:

- **Groq** - Fast LLM inference
- **OpenCV** - Computer vision library
- **Hugging Face** - BLIP image captioning model
- **OpenAI Whisper** - Audio transcription
- **Ultralytics YOLOv8** - Object detection
- **Streamlit** - Web UI framework
- **FastAPI** - Modern API framework

Special thanks to the open-source community for making projects like BRI possible! 💜

## Support

- 📖 **Documentation**: See [docs/](docs/) directory
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 📧 **Email**: [your-email@example.com]

---

**Made with 💜 by the BRI community**

*Ask. Understand. Remember.*
