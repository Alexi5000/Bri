# BRI 110% Full-Stack Streamlit and Middle-Layer Implementation Plan

BRI will remain a **Python-native full-stack product** with Streamlit as the state-of-the-art frontend, FastAPI as the MCP and processing API, SQLite as the durable local persistence system, and optional multimodal ML tools for frame, image-caption, audio, and object intelligence. The buildout will add a formal middle layer between UI and backend services so the Streamlit app no longer reaches directly into raw persistence or raw HTTP calls for critical workflows.

## Architecture Direction

The production architecture will use a layered Python structure that preserves the current repository while introducing clearer application-service boundaries. Streamlit will own presentation, session state, and user interaction. A new middle layer will own video upload orchestration, MCP health/processing calls, video catalog state, progress status, and chat execution. FastAPI remains the MCP service for tool discovery, execution, progressive processing, queue status, and health. SQLite remains the local durable system of record with backups, integrity checks, schema constraints, and safe file lifecycle behavior.

| Layer | Production Responsibility | Implementation Target |
|---|---|---|
| Streamlit frontend | Empathetic product UX, upload, library, chat, progress, diagnostics, accessibility-oriented copy, safe state transitions. | `ui/state.py`, `ui/layout.py`, enhanced `app.py`, enhanced `ui/welcome.py`. |
| Middle layer | Typed orchestration between UI, SQLite, file store, FastAPI MCP service, and agent chat. | `services/application.py`, `services/mcp_client.py`, `services/video_workflow.py`. |
| FastAPI MCP service | Tool catalog, validated execution, progressive processing, queue and job status, cache and circuit-breaker endpoints. | Existing `mcp_server/` APIs retained and consumed through typed clients. |
| SQLite persistence | Durable videos, memory, context, lineage, schema versioning, backup readiness, safe active-video queries. | Existing `storage/` layer plus small helper aliases and app-level snapshots. |
| Optional ML tools | Frame extraction, captioning, transcription, object detection with graceful degradation when dependencies are absent. | Existing `tools/` and `mcp_server/registry.py` exposed through status-aware workflows. |

## Immediate Build Targets

The first production increment will add an application facade and typed DTOs. This facade will expose a stable API for the UI: `get_dashboard_snapshot()`, `upload_video()`, `start_processing()`, `get_processing_progress()`, `send_chat_message()`, and `get_system_readiness()`. Streamlit components will call this facade rather than importing low-level persistence and direct HTTP clients. This is the core change that turns Bri from a collection of Python modules into a full-stack application.

The Streamlit UI will be upgraded with a production shell, consistent session initialization, operational status cards, video intelligence metrics, processing stage descriptions, and a polished product dashboard. The UI must keep the empathetic product identity while reducing duplicated chat/session code and centralizing error display through a predictable result object.

The MCP client will standardize requests, timeouts, response-envelope unwrapping, health parsing, offline behavior, and progressive processing start/status calls. This keeps Streamlit from depending on endpoint response details and makes API contract tests easier to maintain.

## Validation Strategy

The buildout will add production tests for the new middle layer using dependency injection and mocks, plus focused frontend-safe tests for session defaults and status formatting. Existing production tests, smoke tests, and repository hygiene checks must continue to pass. The final validation gate will include `pytest tests/production`, the in-process API smoke script, `scripts/validate_production.py`, README graphics preservation, hidden folder hygiene, and clean Git state checks.

## Documentation Updates

The README will be updated to communicate that Bri is now a full-stack Streamlit + FastAPI + SQLite application, not merely a Python API integration. The documentation index will include the new architecture plan, and production operations guidance will mention the Streamlit frontend, FastAPI MCP service, SQLite backup posture, and optional ML dependency model.
