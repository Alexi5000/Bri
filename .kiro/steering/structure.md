# Project Structure

## Directory Organization

```
bri-video-agent/
├── .kiro/
│   ├── specs/              # Project specifications
│   │   └── bri-video-agent/
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   └── steering/           # AI assistant guidance documents
│
├── app.py                  # Main Streamlit application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore patterns
│
├── models/                # Data models and schemas
│   ├── video.py          # Video, VideoMetadata, Frame models
│   ├── memory.py         # MemoryRecord model
│   ├── responses.py      # AssistantMessageResponse, UserQuery
│   └── tools.py          # Tool-related models (Caption, Transcript, etc.)
│
├── services/             # Core business logic
│   ├── agent.py         # GroqAgent - main conversational agent
│   ├── memory.py        # Memory - conversation history manager
│   ├── context.py       # ContextBuilder - aggregates video data
│   ├── router.py        # ToolRouter - query analysis and tool selection
│   └── error_handler.py # ErrorHandler - friendly error messages
│
├── tools/               # Video processing tools
│   ├── frame_extractor.py    # OpenCV frame extraction
│   ├── image_captioner.py    # BLIP image captioning
│   ├── audio_transcriber.py  # Whisper audio transcription
│   └── object_detector.py    # YOLO object detection
│
├── mcp_server/          # Model Context Protocol server
│   ├── main.py         # FastAPI application
│   ├── registry.py     # Tool registry for discovery
│   └── cache.py        # Redis caching layer
│
├── ui/                  # Streamlit UI components
│   ├── welcome.py      # Welcome screen component
│   ├── library.py      # Video library view
│   ├── chat.py         # Chat window interface
│   ├── player.py       # Video player with timestamp navigation
│   └── styles.py       # Custom CSS and styling
│
├── storage/             # Data storage utilities
│   ├── database.py     # SQLite connection and queries
│   ├── file_store.py   # File system operations for videos/frames
│   └── schema.sql      # Database schema definition
│
├── scripts/             # Utility scripts
│   ├── init_db.py      # Database initialization
│   └── setup.py        # Project setup automation
│
├── tests/               # Test suite
│   ├── unit/           # Unit tests for individual components
│   │   ├── test_memory.py
│   │   ├── test_frame_extractor.py
│   │   ├── test_captioner.py
│   │   ├── test_transcriber.py
│   │   ├── test_detector.py
│   │   └── test_router.py
│   ├── integration/    # Integration tests
│   │   ├── test_e2e_flow.py
│   │   └── test_error_handling.py
│   └── fixtures/       # Test data (sample videos, etc.)
│
└── data/                # Runtime data (gitignored)
    ├── videos/         # Uploaded video files
    ├── frames/         # Extracted frames
    ├── cache/          # Cached processing results
    └── bri.db          # SQLite database
```

## Key Component Relationships

### Data Flow
1. **Upload**: `ui/library.py` → `storage/file_store.py` → `storage/database.py`
2. **Processing**: `mcp_server/main.py` → `tools/*` → `storage/file_store.py`
3. **Query**: `ui/chat.py` → `services/agent.py` → `services/router.py` → `mcp_server/main.py`
4. **Response**: `services/agent.py` → `services/context.py` → `ui/chat.py`

### Module Dependencies
- **UI Layer** depends on: `services/agent.py`, `storage/database.py`, `storage/file_store.py`
- **Agent Layer** depends on: `services/router.py`, `services/memory.py`, `services/context.py`, `mcp_server/`
- **MCP Server** depends on: `tools/*`, `mcp_server/cache.py`, `mcp_server/registry.py`
- **Tools** depend on: `storage/file_store.py`, external libraries (OpenCV, BLIP, Whisper, YOLO)

## Database Schema

### Tables
- **videos**: Video metadata (video_id, filename, file_path, duration, processing_status)
- **memory**: Conversation history (message_id, video_id, role, content, timestamp)
- **video_context**: Processed data (context_id, video_id, context_type, timestamp, data JSON)

### Indexes
- `video_id` on all tables for fast lookups
- `timestamp` on memory and video_context for temporal queries

## Configuration Files

- **`.env`**: Environment variables (GROQ_API_KEY, REDIS_URL, etc.)
- **`requirements.txt`**: Python package dependencies
- **`storage/schema.sql`**: Database schema definition
- **`.gitignore`**: Excludes data/, .env, __pycache__, etc.

## Naming Conventions

- **Files**: snake_case (e.g., `frame_extractor.py`)
- **Classes**: PascalCase (e.g., `FrameExtractor`, `GroqAgent`)
- **Functions/Methods**: snake_case (e.g., `extract_frames`, `chat`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_FRAMES`, `CACHE_TTL`)
- **Database Tables**: snake_case (e.g., `video_context`)
