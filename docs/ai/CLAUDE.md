# CLAUDE.md - AI Assistant Guide for BRI Video Agent

> **Last Updated**: November 13, 2025
> **Version**: 1.0
> **Status**: Active Development

This document provides AI assistants with comprehensive context about the BRI (Brianna) video agent codebase, including architecture, conventions, workflows, and guidelines for effective contribution.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Codebase Structure](#codebase-structure)
3. [Architecture & Design Patterns](#architecture--design-patterns)
4. [Development Workflows](#development-workflows)
5. [Key Conventions & Standards](#key-conventions--standards)
6. [Configuration Management](#configuration-management)
7. [Testing Approach](#testing-approach)
8. [Deployment & Operations](#deployment--operations)
9. [Common Tasks](#common-tasks)
10. [AI Assistant Guidelines](#ai-assistant-guidelines)
11. [Current State & Roadmap](#current-state--roadmap)

---

## 🎯 Project Overview

### What is BRI?

BRI (Brianna) is an **empathetic multimodal agent** for video analysis that enables users to upload videos and ask natural language questions to receive context-aware, conversational responses.

### Core Capabilities

- **Video Upload & Management**: Drag-and-drop upload with library view
- **Conversational Interface**: Natural language queries with context awareness
- **Multimodal Analysis**:
  - Frame extraction (OpenCV)
  - Image captioning (BLIP)
  - Audio transcription (Whisper)
  - Object detection (YOLOv8)
- **Smart Memory**: Maintains conversation history per video
- **Intelligent Routing**: Automatically determines which tools to use

### Design Philosophy

BRI is designed to be:
- **Empathetic**: Warm, supportive tone with playful personality
- **Accessible**: No technical knowledge required
- **Conversational**: Like discussing content with a knowledgeable friend
- **Privacy-Focused**: Local storage by default
- **Graceful**: Friendly error messages and fallback strategies

### Technology Stack

- **Frontend**: Streamlit with custom CSS
- **LLM**: Groq API (Llama 3.1 70B)
- **Video Processing**: OpenCV, BLIP, Whisper, YOLOv8
- **API Server**: FastAPI with MCP (Model Context Protocol)
- **Caching**: Redis (optional)
- **Database**: SQLite
- **Language**: Python 3.9+

---

## 📁 Codebase Structure

### Directory Layout

```
bri-video-agent/
├── app.py                      # Main Streamlit application entry point
├── config.py                   # Configuration management (lazy loading)
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
│
├── models/                    # Data models and schemas (Pydantic)
│   ├── video.py              # VideoMetadata, Frame
│   ├── memory.py             # MemoryRecord
│   ├── tools.py              # Caption, Transcript, DetectedObject
│   └── responses.py          # API response models
│
├── services/                  # Core business logic
│   ├── agent.py              # GroqAgent - main conversational agent
│   ├── router.py             # ToolRouter - query analysis & routing
│   ├── memory.py             # Memory - conversation history
│   ├── context.py            # ContextBuilder - video data aggregation
│   ├── error_handler.py      # ErrorHandler - friendly error messages
│   ├── video_processing_service.py  # Video processing orchestration
│   ├── data_validator.py     # Data validation service
│   ├── semantic_search.py    # Semantic search (optional)
│   └── [other services...]
│
├── tools/                     # Video processing tools
│   ├── frame_extractor.py    # OpenCV frame extraction
│   ├── image_captioner.py    # BLIP image captioning
│   ├── audio_transcriber.py  # Whisper audio transcription
│   └── object_detector.py    # YOLOv8 object detection
│
├── storage/                   # Data persistence layer
│   ├── database.py           # SQLite operations
│   ├── schema.sql            # Database schema definition
│   ├── migrations.py         # Database migrations
│   ├── backup.py             # Backup/restore functionality
│   ├── file_store.py         # File system operations
│   ├── multi_tier_cache.py   # L1/L2/L3 caching
│   └── [other storage...]
│
├── mcp_server/               # Model Context Protocol server
│   ├── main.py              # FastAPI application
│   ├── registry.py          # Tool registry
│   ├── cache.py             # Redis caching layer
│   └── README.md            # MCP server documentation
│
├── ui/                       # Streamlit UI components
│   ├── welcome.py           # Welcome screen
│   ├── library.py           # Video library view
│   ├── chat.py              # Chat interface
│   ├── player.py            # Video player with timestamp navigation
│   └── styles.py            # Custom CSS and styling
│
├── utils/                    # Utilities
│   ├── logging_config.py    # Structured logging configuration
│   └── metrics_logger.py    # Operational metrics
│
├── scripts/                  # Utility scripts
│   ├── init_db.py           # Initialize database
│   ├── backup_database.py   # Create backups
│   ├── validate_setup.py    # Environment validation
│   ├── health_check.py      # System health monitoring
│   └── utils/               # Diagnostic utilities
│
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test data
│
├── docs/                     # Documentation
│   ├── USER_GUIDE.md
│   ├── DEPLOYMENT.md
│   ├── OPERATIONS_RUNBOOK.md
│   └── [other docs...]
│
└── data/                     # Runtime data (gitignored)
    ├── bri.db               # SQLite database
    ├── videos/              # Uploaded videos
    ├── frames/              # Extracted frames
    ├── cache/               # Processing cache
    └── backups/             # Database backups
```

### Key Files

- **`app.py`**: Main entry point, initializes Streamlit UI and services
- **`config.py`**: Centralized configuration with lazy loading via metaclass
- **`services/agent.py`**: Core conversational agent with empathetic personality
- **`storage/database.py`**: All database operations with transaction support
- **`storage/schema.sql`**: Database schema with indexes

---

## 🏗️ Architecture & Design Patterns

### Layered Architecture

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

### Key Design Patterns

#### 1. **Database-First Approach**
- Always check database for existing processed data before calling MCP tools
- Prioritize existing data: captions > transcripts > objects > frames
- Reduces redundant processing and API calls

#### 2. **Graceful Degradation**
- Agent works with partial data (frames-only, captions-only, or full intelligence)
- Friendly fallback messages when tools fail
- Continues operation even if optional services (Redis) are unavailable

#### 3. **Context Manager Pattern**
- Database, Memory, and ContextBuilder use context managers (`with` statements)
- Ensures proper resource cleanup
- Automatic transaction management

#### 4. **Singleton Pattern**
- Services like `get_file_store()` and `get_semantic_search_service()` use singletons
- Lazy initialization with caching
- Prevents duplicate resource allocation

#### 5. **Factory Pattern**
- Tool registry dynamically creates tool instances
- Configuration-driven service instantiation
- Extensible for new tools

#### 6. **Multi-Tier Caching**
- **L1 (LRU)**: In-memory cache with thread safety
- **L2 (Redis)**: Optional shared cache across instances
- **L3 (DB)**: Database-level query caching
- Hit rate tracking for performance monitoring

#### 7. **Separation of Concerns**
- **Models**: Data structures only (Pydantic)
- **Services**: Business logic
- **Storage**: Data persistence
- **Tools**: Video processing
- **UI**: User interface

#### 8. **Error Handling Strategy**
- Custom exceptions per domain (`AgentError`, `MemoryError`, `DatabaseError`, etc.)
- `ErrorHandler` service converts technical errors to warm, empathetic messages
- Tool-specific error messages maintain BRI's personality
- Logging at multiple levels (DEBUG, INFO, WARNING, ERROR)

---

## 🔄 Development Workflows

### Setup Development Environment

```bash
# 1. Clone and navigate to repository
git clone <repository-url>
cd bri-video-agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Initialize database
python scripts/init_db.py

# 6. Validate setup
python scripts/validate_setup.py
```

### Running the Application

```bash
# Terminal 1: Start MCP server
python mcp_server/main.py

# Terminal 2: Start Streamlit UI
streamlit run app.py
```

### Testing Workflow

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

### Database Management

```bash
# Create backup
python scripts/backup_database.py

# Restore from backup
python scripts/restore_database.py <backup_file>

# Run migrations
python scripts/migrate_db.py

# Check database health
python scripts/health_check.py report
```

### Logging & Monitoring

```bash
# View application logs
tail -f logs/bri.log

# View error logs only
tail -f logs/bri_errors.log

# View performance logs
tail -f logs/bri_performance.log

# Run logging dashboard
streamlit run ui/logging_dashboard.py --server.port 8503
```

### Git Workflow

**Current Status**: No pre-commit hooks or CI/CD configured

**Branch Strategy**: Feature branches recommended
```bash
git checkout -b feature/your-feature-name
# Make changes
git commit -m "Add your feature"
git push origin feature/your-feature-name
```

---

## 📏 Key Conventions & Standards

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private Methods**: `_leading_underscore()`

**Examples**:
```python
# Files
video_processing_service.py
image_captioner.py

# Classes
class GroqAgent:
class VideoMetadata:

# Functions
def extract_frames():
def build_video_context():

# Constants
MAX_FRAMES_PER_VIDEO = 100
GROQ_API_KEY = "..."

# Private
def _process_batch():
def _validate_input():
```

### Code Organization

#### Module Structure
```python
"""Module docstring explaining purpose."""

# 1. Standard library imports
import os
from pathlib import Path

# 2. Third-party imports
import streamlit as st
from groq import Groq

# 3. Local imports
from models.video import VideoMetadata
from services.memory import Memory

# 4. Constants
DEFAULT_TIMEOUT = 30

# 5. Classes and functions
class MyService:
    """Service docstring."""
    pass
```

#### Function/Method Documentation
```python
def process_video(video_id: str, max_frames: int = 100) -> VideoMetadata:
    """Process a video and extract metadata.

    Args:
        video_id: Unique identifier for the video
        max_frames: Maximum number of frames to extract (default: 100)

    Returns:
        VideoMetadata object with processing results

    Raises:
        VideoProcessingError: If video cannot be processed
        FileNotFoundError: If video file doesn't exist
    """
    pass
```

### Error Handling Patterns

#### Use Custom Exceptions
```python
# Good
if not video_exists(video_id):
    raise VideoNotFoundError(f"Video {video_id} not found")

# Avoid
if not video_exists(video_id):
    raise Exception("Video not found")
```

#### Provide Context in Error Messages
```python
# Good
try:
    result = process_frame(frame_id)
except ProcessingError as e:
    logger.error(f"Failed to process frame {frame_id} for video {video_id}",
                 extra={'frame_id': frame_id, 'video_id': video_id, 'error': str(e)})
    raise

# Avoid
except ProcessingError as e:
    logger.error("Processing failed")
    raise
```

#### Use ErrorHandler for User-Facing Messages
```python
from services.error_handler import ErrorHandler

error_handler = ErrorHandler()

try:
    captions = caption_frames(video_id)
except CaptioningError as e:
    friendly_message = error_handler.handle_tool_error('image_captioner', e)
    return {"error": friendly_message}
```

### Logging Patterns

#### Structured Logging
```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Use structured logging with context
logger.info("Processing video",
            extra={'video_id': video_id, 'frame_count': len(frames)})

# Performance logging
from utils.logging_config import get_performance_logger
perf_logger = get_performance_logger(__name__)
perf_logger.info("Frame extraction completed",
                 extra={'duration_ms': duration, 'frame_count': count})
```

#### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (operations, state changes)
- **WARNING**: Unexpected but handled situations
- **ERROR**: Error events that might still allow operation to continue
- **CRITICAL**: Serious errors causing operation to abort

### Data Validation Patterns

#### Always Validate Before Database Insertion
```python
from services.data_validator import DataValidator

validator = DataValidator()

# Validate single record
errors = validator.validate_caption({
    'video_id': video_id,
    'frame_number': 1,
    'timestamp': 0.5,
    'caption_text': "A cat sitting on a table"
})

if errors:
    raise ValidationError(f"Invalid caption data: {errors}")

# Validate batch
captions_batch = [...]
batch_errors = validator.validate_batch(captions_batch, 'caption')
```

### Database Patterns

#### Use Transactions
```python
from storage.database import Database

db = Database()

# Context manager automatically handles commit/rollback
with db.transaction():
    db.insert_video(video_data)
    db.insert_frames(frames_data)
    # If any error occurs, transaction is rolled back
```

#### Use Prepared Statements
```python
# Good - prevents SQL injection
cursor.execute(
    "SELECT * FROM videos WHERE video_id = ?",
    (video_id,)
)

# Avoid - SQL injection risk
cursor.execute(f"SELECT * FROM videos WHERE video_id = '{video_id}'")
```

### Testing Patterns

#### Use Fixtures for Test Data
```python
import pytest
import tempfile

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    db = Database(path)
    db.initialize_schema()
    yield db
    os.close(fd)
    os.unlink(path)

def test_insert_video(temp_db):
    """Test video insertion."""
    video_data = {'video_id': 'test-123', 'filename': 'test.mp4'}
    temp_db.insert_video(video_data)
    result = temp_db.get_video('test-123')
    assert result['filename'] == 'test.mp4'
```

---

## ⚙️ Configuration Management

### Configuration System

BRI uses a **lazy-loading metaclass-based configuration** system in `config.py`.

#### Priority Order
1. Streamlit secrets (for Streamlit Cloud deployment)
2. Environment variables
3. Default values

#### Usage
```python
from config import Config

# Access configuration values
api_key = Config.GROQ_API_KEY
max_frames = Config.MAX_FRAMES_PER_VIDEO
database_path = Config.DATABASE_PATH

# Validate configuration
Config.validate()

# Ensure directories exist
Config.ensure_directories()

# Get MCP server URL
server_url = Config.get_mcp_server_url()

# Display current configuration (masks sensitive values)
Config.display_config()
```

### Environment Variables

See `.env.example` for all available configuration options.

#### Required Configuration
- **`GROQ_API_KEY`**: Groq API key (get from console.groq.com)

#### Important Optional Configuration
- **`REDIS_ENABLED`**: Enable/disable Redis caching (default: `true`)
- **`MAX_FRAMES_PER_VIDEO`**: Maximum frames to extract (default: `100`)
- **`FRAME_EXTRACTION_INTERVAL`**: Seconds between frames (default: `2.0`)
- **`DEBUG`**: Enable debug mode (default: `false`)
- **`LOG_LEVEL`**: Logging level (default: `INFO`)

#### Configuration in Code
```python
# Don't hardcode configuration values
# Bad
max_frames = 100

# Good
from config import Config
max_frames = Config.MAX_FRAMES_PER_VIDEO
```

### Adding New Configuration

1. Add to `.env.example` with documentation
2. Add to `config.py` in the `config_map` dictionary
3. Update `Config.validate()` if validation needed
4. Document in `docs/CONFIGURATION.md`

---

## 🧪 Testing Approach

### Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests
└── fixtures/          # Test data
```

### Testing Principles

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use pytest fixtures for test data and temporary resources
3. **Coverage**: Aim for high coverage of critical paths
4. **Edge Cases**: Test error conditions and boundary cases
5. **Cleanup**: Always clean up test resources (temp files, databases)

### Current Test Status

- **37/50 tests passing (74%)**
- **Primary issues**: Data persistence in MCP server
- **Target**: 90%+ test pass rate

### Writing New Tests

```python
import pytest
from services.memory import Memory

@pytest.fixture
def memory_service():
    """Create memory service with temp database."""
    # Setup
    db = create_temp_database()
    memory = Memory(db)

    yield memory

    # Teardown
    cleanup_temp_database(db)

def test_store_and_retrieve_message(memory_service):
    """Test message storage and retrieval."""
    # Arrange
    video_id = "test-video-123"
    message = {"role": "user", "content": "Hello"}

    # Act
    memory_service.add_message(video_id, message)
    history = memory_service.get_history(video_id)

    # Assert
    assert len(history) == 1
    assert history[0]["content"] == "Hello"
```

---

## 🚀 Deployment & Operations

### Deployment Status

- **Current Status**: Development/Testing
- **Target**: Production-ready (Tasks 40-50)
- **Deployment Platform**: Local or Streamlit Cloud

### Starting the Application

#### Development Mode
```bash
# Terminal 1
python mcp_server/main.py

# Terminal 2
streamlit run app.py
```

#### Production Mode (Streamlit Cloud)
- Configure secrets in Streamlit Cloud dashboard
- Secrets take priority over environment variables
- See `DEPLOYMENT_STATUS.md` for details

### Health Monitoring

```bash
# System health check
python scripts/health_check.py

# Check database health
python scripts/health_check.py report

# View archival status
python scripts/archival_cli.py status
```

### Backup & Recovery

```bash
# Create backup
python scripts/backup_database.py

# Verify backups
python scripts/verify_backups.py

# Restore from backup
python scripts/restore_database.py data/backups/bri_backup_YYYYMMDD_HHMMSS.db
```

### Operations

See `docs/OPERATIONS_RUNBOOK.md` for detailed operational procedures including:
- Incident response
- Database maintenance
- Performance optimization
- Troubleshooting

---

## 🛠️ Common Tasks

### Adding a New Video Processing Tool

1. **Create tool file** in `tools/`
   ```python
   # tools/my_new_tool.py
   class MyNewTool:
       def process(self, video_id: str) -> dict:
           # Implementation
           pass
   ```

2. **Register in MCP server** (`mcp_server/registry.py`)
   ```python
   from tools.my_new_tool import MyNewTool

   registry.register_tool('my_new_tool', MyNewTool())
   ```

3. **Add to router** (`services/router.py`)
   - Update query classification logic
   - Add tool to execution order if needed

4. **Update database schema** if storing new data type
   - Add context_type to `video_context` table or create new table
   - Create migration in `storage/migrations.py`

5. **Add tests** in `tests/unit/`

### Adding a New Service

1. **Create service file** in `services/`
2. **Define Pydantic models** in `models/` if needed
3. **Add error handling** using custom exceptions
4. **Add logging** with appropriate logger
5. **Add tests**
6. **Document** in relevant docs

### Updating Database Schema

1. **Update `storage/schema.sql`** with new schema
2. **Create migration** in `storage/migrations.py`
   ```python
   MIGRATIONS = [
       # ... existing migrations
       {
           'version': 5,
           'description': 'Add new column',
           'sql': 'ALTER TABLE videos ADD COLUMN new_field TEXT;'
       }
   ]
   ```
3. **Run migration**: `python scripts/migrate_db.py`
4. **Update models** in `models/`
5. **Test thoroughly**

### Adding Configuration Option

1. **Add to `.env.example`** with documentation
2. **Add to `config.py`** in `config_map`
3. **Add validation** if needed in `Config.validate()`
4. **Use in code**: `Config.YOUR_NEW_OPTION`
5. **Document** in `docs/CONFIGURATION.md`

### Debugging Issues

1. **Check logs**: `tail -f logs/bri.log`
2. **Enable debug mode**: Set `DEBUG=true` in `.env`
3. **Run diagnostics**: `python scripts/diagnose_system.py`
4. **Check database**: Use SQLite browser or queries
5. **Test specific component**: Run relevant test file
6. **Check MCP server**: Visit `http://localhost:8000/docs`

### Processing a Test Video

```bash
# Process a specific video
python scripts/utils/process_test_video.py <video_id>

# Check video context data
python scripts/utils/check_video_context.py

# List all videos
python scripts/utils/list_videos.py
```

---

## 🤖 AI Assistant Guidelines

When working on this codebase as an AI assistant, follow these guidelines:

### 1. **Maintain BRI's Personality**

BRI has a warm, empathetic, playful personality. This should be reflected in:
- User-facing messages
- Error messages
- UI text
- Comments and documentation

**Examples**:
```python
# Good
"I'm having a little trouble with the visual descriptions right now, but I can tell you what was said! 🎵"

# Avoid
"Error: image_captioner service failed with status code 500"
```

### 2. **Database-First Approach**

Always check the database for existing data before calling tools:
```python
# Good
captions = db.get_captions(video_id)
if not captions:
    # Only call tool if no data exists
    captions = mcp_client.call_tool('caption_frames', {'video_id': video_id})
    db.store_captions(video_id, captions)

# Avoid - Always calling tools
captions = mcp_client.call_tool('caption_frames', {'video_id': video_id})
```

### 3. **Graceful Degradation**

Design features to work with partial data:
```python
# Good - works with what's available
context = []
if captions:
    context.append(f"Visual: {captions}")
if transcripts:
    context.append(f"Audio: {transcripts}")
if not context:
    context.append("I can describe the basic frames I see")

# Avoid - fails if any piece missing
context = f"Visual: {captions}, Audio: {transcripts}"  # Fails if either is None
```

### 4. **Comprehensive Logging**

Use structured logging with appropriate context:
```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Good
logger.info("Starting video processing",
            extra={'video_id': video_id, 'frame_count': len(frames)})

# Better
with log_context(video_id=video_id):
    logger.info("Starting video processing",
                extra={'frame_count': len(frames)})
```

### 5. **Use Type Hints Consistently**

```python
from typing import Optional, List, Dict
from models.video import VideoMetadata

# Good
def get_video(video_id: str) -> Optional[VideoMetadata]:
    pass

def get_frames(video_id: str) -> List[Dict[str, any]]:
    pass

# Avoid
def get_video(video_id):
    pass
```

### 6. **Validate Data Before Database Operations**

```python
from services.data_validator import DataValidator

validator = DataValidator()

# Good
errors = validator.validate_caption(caption_data)
if errors:
    logger.error("Invalid caption data", extra={'errors': errors})
    raise ValidationError(errors)
db.insert_caption(caption_data)

# Avoid
db.insert_caption(caption_data)  # No validation
```

### 7. **Handle Errors Appropriately**

```python
from services.error_handler import ErrorHandler

error_handler = ErrorHandler()

# Good - friendly user-facing message
try:
    result = process_video(video_id)
except ProcessingError as e:
    logger.error("Video processing failed", extra={'video_id': video_id, 'error': str(e)})
    friendly_msg = error_handler.handle_tool_error('frame_extractor', e)
    return {"error": friendly_msg}

# Avoid - technical error exposed to user
except ProcessingError as e:
    return {"error": str(e)}
```

### 8. **Use Transactions for Multi-Step Operations**

```python
from storage.database import Database

db = Database()

# Good
with db.transaction():
    db.insert_video(video_data)
    db.insert_frames(frames_data)
    db.update_processing_status(video_id, 'completed')
    # All or nothing

# Avoid
db.insert_video(video_data)
db.insert_frames(frames_data)  # Could fail leaving inconsistent state
db.update_processing_status(video_id, 'completed')
```

### 9. **Document Your Changes**

- Add docstrings to new functions/classes
- Update relevant documentation in `docs/`
- Add inline comments for complex logic
- Update this CLAUDE.md if adding new patterns or conventions

### 10. **Test Your Changes**

- Write unit tests for new functionality
- Run existing tests to ensure no regressions
- Test manually with actual video data
- Check logs for errors or warnings

---

## 📊 Current State & Roadmap

### Current Status (November 2025)

**Phase 1-3: Complete** (Tasks 1-30)
- ✅ ML Pipeline implemented (BLIP, Whisper, YOLO)
- ✅ Database schema created
- ✅ Agent architecture built
- ✅ MCP server operational
- ✅ Streamlit UI functional
- ✅ Basic testing (37/50 tests passing - 74%)

**Issues**:
- ⚠️ Data persistence partially broken (MCP server not storing results consistently)
- ⚠️ 13 tests failing (26%)
- ⚠️ No progressive processing (user waits for full processing)

### Roadmap

#### **Phase 4: Data Pipeline Fix** (Week 1 - CRITICAL)
Tasks 40-43:
- Fix data persistence with transactions
- Add progressive processing (frames → captions → transcripts → objects)
- Improve agent intelligence
- Comprehensive testing
- **Target**: 90%+ test pass rate

#### **Phase 5: Data Engineering** (Weeks 2-3 - HIGH)
Tasks 44-50:
- Database optimization (constraints, migrations, archival)
- API hardening (validation, circuit breakers, versioning)
- Data flow optimization (multi-tier caching, query optimization)
- Data quality (metrics, observability, recovery)
- Vector database integration (optional)
- Production readiness (logging, backups, monitoring)
- **Target**: Production-ready system

### Success Metrics

**Phase 4 Complete**:
- 100% data persistence
- 90%+ test pass rate
- <30s to chat availability
- Zero silent failures

**Phase 5 Complete**:
- ACID compliance
- <100ms for 95% of queries
- 99.9% uptime
- Full observability
- Automated backups

### Getting Involved

**For Critical Fixes**:
```bash
python scripts/diagnose_system.py
python scripts/utils/quick_fix.py
```

**For Full Implementation**:
See `.kiro/specs/bri-video-agent/tasks.md` for complete task list.

**For Understanding**:
- `PROJECT_STRUCTURE.md` - Directory structure
- `README.md` - User-facing documentation
- `docs/` - Comprehensive guides
- `FINAL_TASK_SUMMARY.md` - Task overview

---

## 📚 Additional Resources

### Key Documentation Files

- **README.md** - Main project README (user-facing)
- **PROJECT_STRUCTURE.md** - Detailed directory structure
- **FINAL_TASK_SUMMARY.md** - Complete task summary
- **DEPLOYMENT_STATUS.md** - Current deployment status
- **docs/USER_GUIDE.md** - User guide
- **docs/OPERATIONS_RUNBOOK.md** - Operations procedures
- **docs/TROUBLESHOOTING.md** - Common issues and solutions
- **mcp_server/README.md** - MCP server API documentation

### Useful Scripts

- **scripts/diagnose_system.py** - System diagnostics
- **scripts/health_check.py** - Health monitoring
- **scripts/backup_database.py** - Database backup
- **scripts/utils/check_video_context.py** - Check video data
- **scripts/utils/list_videos.py** - List all videos
- **scripts/utils/process_test_video.py** - Process test video

### Development References

- **Groq API**: https://console.groq.com
- **Streamlit Docs**: https://docs.streamlit.io
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Pydantic Docs**: https://docs.pydantic.dev

---

## ✅ Checklist for AI Assistants

Before starting work, review:
- [ ] This CLAUDE.md file
- [ ] PROJECT_STRUCTURE.md for directory layout
- [ ] FINAL_TASK_SUMMARY.md for current status
- [ ] Relevant documentation in `docs/`

When making changes:
- [ ] Follow naming conventions
- [ ] Add appropriate logging
- [ ] Validate data before database operations
- [ ] Use transactions for multi-step operations
- [ ] Handle errors gracefully with friendly messages
- [ ] Add/update tests
- [ ] Update documentation
- [ ] Maintain BRI's empathetic personality

Before committing:
- [ ] Run tests: `pytest`
- [ ] Check logs for errors
- [ ] Verify functionality manually
- [ ] Update relevant documentation

---

**Version**: 1.0
**Last Updated**: November 13, 2025
**Maintainer**: BRI Development Team

For questions or clarifications, refer to the documentation in `docs/` or run diagnostic scripts in `scripts/`.
