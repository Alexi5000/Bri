# BRI Architecture Map

## Overview

BRI (Brianna) employs a modular, layered architecture designed for separation of concerns between user interaction, intelligent orchestration, video processing, and data persistence. The system is composed of five primary layers: UI, Agent, MCP Server, Tools, and Storage.

## Layer Breakdown

### 1. Streamlit UI Layer (`ui/`, `app.py`)
- **Responsibilities**: Handles user interactions, manages session state, and visualizes video content and analysis results.
- **Key Components**:
  - `app.py`: Application entry point, session management, and view routing.
  - `ui/welcome.py`: Landing page.
  - `ui/library.py`: Video library management.
  - `ui/chat.py`: Chat interface integration.
  - `ui/player.py`: Video player with timestamp navigation.
- **Status**: **Fully Implemented**. Features include drag-and-drop upload, library view, and conversational chat with media embedding.

### 2. Agent Layer (`services/`)
- **Responsibilities**: Orchestrates the user's intent, manages conversation context, routes queries to appropriate tools, and generates natural language responses.
- **Key Components**:
  - `services/agent.py` (`GroqAgent`): Core logic engine. Uses Groq LLM for reasoning.
  - `services/router.py` (`ToolRouter`): Analyzes queries to determine necessary tools.
  - `services/memory.py` (`Memory`): Manages conversation history per video.
  - `services/context.py` (`ContextBuilder`): Aggregates video data (captions, transcripts) for the LLM.
- **Status**: **Fully Implemented**. Includes intelligent routing, context-aware memory, and graceful error handling.

### 3. MCP Server Layer (`mcp_server/`)
- **Responsibilities**: Exposes video processing capabilities as a RESTful API (Model Context Protocol). Handles request validation, rate limiting, caching, and execution orchestration.
- **Key Components**:
  - `mcp_server/main.py`: FastAPI application defining endpoints.
  - `mcp_server/registry.py`: Registry of available tools.
  - `mcp_server/cache.py`: Redis-based caching layer (with fallback).
  - `mcp_server/circuit_breaker.py`: Fault tolerance mechanisms.
- **Status**: **Fully Implemented**. API versioning, health checks, and parallel processing support are active.
  - **Progressive Processing**: Implemented via `process_video_progressive` endpoint and background queue.
  - **Vector Search**: **Optional/Partial**. `SemanticSearchService` exists but depends on optional `chromadb` and `sentence-transformers` packages.

### 4. Tools Layer (`tools/`)
- **Responsibilities**: Performs specific video processing tasks.
- **Key Components**:
  - `tools/frame_extractor.py`: OpenCV-based frame extraction.
  - `tools/image_captioner.py`: BLIP model for visual description.
  - `tools/audio_transcriber.py`: Whisper model for speech-to-text.
  - `tools/object_detector.py`: YOLOv8 for object detection.
- **Status**: **Fully Implemented**. All four core tools are integrated and operational.

### 5. Storage Layer (`storage/`)
- **Responsibilities**: Persists application data, video metadata, and processing results.
- **Key Components**:
  - `storage/database.py`: SQLite connection manager.
  - `services/video_processing_service.py`: Centralized service for writing results with transactions and idempotency.
  - `storage/schema.sql`: Database schema definition.
  - File System: Stores raw video files (`data/videos`) and extracted frames (`data/frames`).
- **Status**: **Fully Implemented**. Includes ACID compliance, schema migration support, and data lineage tracking.

## Request & Data Flow

1.  **User Query**: User submits a question in the Streamlit UI (`app.py`).
2.  **Agent Invocation**: UI calls `GroqAgent.chat()` (`services/agent.py`).
3.  **Context Assembly**:
    - `GroqAgent` calls `ContextBuilder` to check `storage/` for existing processed data (frames, captions, etc.).
    - **Read Path**: Direct DB access for speed (`SELECT`).
4.  **Decision Making**:
    - If data is missing or query requires new analysis, `ToolRouter` identifies needed tools.
5.  **Tool Execution (Write Path)**:
    - `GroqAgent` sends HTTP request to `mcp_server` (`POST /tools/.../execute`).
    - `mcp_server` checks Redis cache.
    - If uncached, `mcp_server` invokes specific tool from `tools/`.
    - `mcp_server` uses `VideoProcessingService` to write results to SQLite (`INSERT`).
6.  **Response Generation**:
    - `GroqAgent` combines User Query + Video Context + Conversation History.
    - Sends prompt to Groq API.
7.  **Delivery**: Response (text + media links) is returned to UI for display.

## Integration Points

- **UI ↔ Agent**: Direct Python import (`from services.agent import GroqAgent`).
- **Agent ↔ MCP Server**: HTTP/REST coupling (`httpx` calls to `http://localhost:8000`).
- **Agent ↔ Storage**: Direct read access (`ContextBuilder` queries SQLite).
- **MCP Server ↔ Storage**: Direct write access (`VideoProcessingService` writes to SQLite).
- **External Dependencies**:
  - **Groq**: LLM inference (via `groq` python client).
  - **Redis**: Caching (via `redis` client).
  - **HuggingFace/OpenAI**: Models for tools (BLIP, Whisper, YOLO).

## System Status Summary

- **Core Architecture**: ✅ **Stable**. The separation of UI, Agent, and Server allows for independent scaling and development.
- **Data Persistence**: ✅ **Robust**. Transactional writes and idempotent operations ensure data integrity.
- **Error Handling**: ✅ **Comprehensive**. Circuit breakers and graceful degradation strategies are in place across layers.
- **Performance**: ✅ **Optimized**. Multi-tier caching (Memory -> Redis -> SQLite) and lazy loading in UI.
