# BRI API Reference

BRI exposes a FastAPI service that coordinates video processing tools behind a small MCP-style contract. The Streamlit interface calls this service for frame extraction, captioning, transcription, object detection, cache inspection, and progressive job status.

| Area | Endpoint | Purpose |
|---|---|---|
| Service health | `GET /health` | Returns process, registry, cache, and dependency status. |
| Tool registry | `GET /tools` and `GET /v1/tools` | Lists available tool names, descriptions, and parameter schemas. |
| Tool execution | `POST /tools/{tool_name}/execute` | Executes one registered tool for a known video. |
| Video processing | `POST /videos/{video_id}/process` | Runs an ordered processing plan for a video. |
| Progressive processing | `POST /videos/{video_id}/process-progressive` | Starts staged processing suitable for UI progress. |
| Status | `GET /videos/{video_id}/status` | Reports available data for a processed video. |
| Queue | `GET /queue/status` and `GET /queue/job/{video_id}` | Reports background processing state. |
| Cache | `GET /cache/stats`, `DELETE /cache`, `DELETE /cache/videos/{video_id}` | Observes and clears cached processing output. |

## Request model

Tool execution accepts a constrained request body. Parameters are validated for allowed tool names, sanitized video identifiers, JSON size, nested depth, and supported media paths before execution.

```json
{
  "video_id": "video_demo_001",
  "parameters": {
    "max_frames": 20,
    "interval_seconds": 2.0
  }
}
```

## Response model

API responses use structured Pydantic envelopes for successful results, validation errors, cache metadata, and processing progress. The service is designed so clients can poll status while long-running model work continues in the background.

## Operational notes

The API should be run behind a production reverse proxy with request-size limits and TLS termination. Redis is optional for local development but recommended in production so expensive tool calls can be cached and reused safely.
