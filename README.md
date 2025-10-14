# BRI (Brianna) - Video Analysis Agent

BRI is an open-source, empathetic multimodal agent for video processing that enables users to upload videos and ask natural language questions to receive context-aware, conversational responses.

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

All configuration is managed through environment variables in the `.env` file. See `.env.example` for available options.

Key configurations:
- `GROQ_API_KEY`: Your Groq API key (required)
- `REDIS_URL`: Redis connection URL (optional)
- `MAX_FRAMES_PER_VIDEO`: Maximum frames to extract per video
- `GROQ_MODEL`: LLM model to use (default: llama-3.1-70b-versatile)

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

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
