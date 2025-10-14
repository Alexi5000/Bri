# Technology Stack

## Core Technologies

### Frontend
- **Streamlit**: Web UI framework for rapid prototyping
- **Custom CSS**: Soft color palette (blush pink, lavender, teal) with rounded edges

### Backend & Agent
- **Groq API**: LLM for natural language understanding and response generation
  - Model: `llama-3.1-70b-versatile` (or `llama-4-scout` for faster responses)
  - Temperature: 0.7 for balanced creativity and accuracy
- **FastAPI**: MCP (Model Context Protocol) server for tool orchestration
- **Redis**: Caching layer for tool results (24-hour TTL)

### Video Processing Tools
- **OpenCV**: Frame extraction from videos
- **BLIP** (Salesforce/blip-image-captioning-large): Image captioning via Hugging Face Transformers
- **Whisper** (OpenAI): Audio transcription with timestamps
- **YOLOv8**: Object detection and tracking (Ultralytics)

### Storage
- **SQLite**: Conversation memory, video metadata, and processed context
- **File System**: Video files and extracted frames/assets

## Key Dependencies

```
streamlit
groq
opencv-python
transformers
whisper
ultralytics
fastapi
redis
sqlite3
python-dotenv
pydantic
```

## Architecture Pattern

**Layered Architecture**:
1. **Presentation Layer**: Streamlit UI
2. **Agent Layer**: Groq-powered conversational agent with tool routing
3. **Tool Layer**: MCP server exposing video processing capabilities
4. **Storage Layer**: SQLite + file system

## Common Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_key_here"

# Initialize database
python scripts/init_db.py
```

### Running the Application
```bash
# Start MCP server (in one terminal)
python mcp_server/main.py

# Start Streamlit UI (in another terminal)
streamlit run app.py
```

### Testing
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=. tests/
```

## Configuration

- **Environment Variables**: Stored in `.env` file (see `.env.example`)
- **API Keys**: Groq API key required for LLM functionality
- **Database**: SQLite database initialized on first run
- **Redis**: Optional for caching (falls back to no cache if unavailable)

## Performance Considerations

- **Frame Extraction**: Adaptive intervals based on video length (max 100 frames)
- **Batch Processing**: Captions processed in batches of 10 frames
- **Caching**: Redis cache for tool results to improve response times
- **Memory Limits**: Conversation history limited to last 10 messages
- **Parallel Execution**: Tools run in parallel where possible
