# BRI Production Architecture

BRI is a complete Python video intelligence application that combines a **Streamlit operator interface**, a **FastAPI MCP-style processing service**, a **SQLite persistence layer**, optional **Redis caching**, and a **Groq-powered conversation agent**. The build is optimized for local development, Docker deployment, and incremental production hardening without requiring contributors to run heavyweight media models for every change.

## Runtime boundaries

| Layer | Responsibility | Key modules |
|---|---|---|
| Streamlit UI | Upload videos, show progress, render chat, and display timestamped evidence. | `app.py`, `components/*` |
| Conversation agent | Plan user intent, retrieve context, call Groq, and store memory. | `services/agent.py`, `services/router.py`, `services/context.py` |
| FastAPI service | Expose tool registry, execute video tools, report progress, and manage cache state. | `mcp_server/main.py`, `mcp_server/registry.py`, `mcp_server/validation.py` |
| Storage | Persist videos, extracted context, conversation memory, and processing metadata. | `storage/database.py`, `storage/schema.sql` |
| Media tools | Extract frames, caption images, transcribe audio, and detect objects. | `tools/*` |

## Request flow

1. A user uploads a video through Streamlit.
2. The app records video metadata in SQLite and calls the FastAPI service.
3. The service validates request size, video IDs, and tool names before running media tools.
4. Tool results are persisted as typed video context and optionally cached in Redis.
5. The chat agent builds a context window from video evidence and conversation memory.
6. Groq generates a warm, timestamp-aware answer with supporting frames and suggestions.

## Production principles

BRI keeps secrets in environment variables or deployment secret managers, stores generated media under ignored runtime directories, uses validation contracts around every API boundary, and provides fast tests that verify packaging, documentation, configuration, and API contracts without requiring GPU-backed model execution.
