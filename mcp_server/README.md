# BRI MCP Server

Model Context Protocol (MCP) server for BRI video processing tools. This FastAPI-based server exposes video processing capabilities through a standardized REST API with caching support.

## Features

- **Dynamic Tool Discovery**: Automatically registers and exposes available video processing tools
- **Tool Execution**: Execute tools with standardized input/output interfaces
- **Batch Processing**: Process videos with multiple tools in a single request
- **Redis Caching**: Cache tool results with configurable TTL (24 hours default)
- **Error Handling**: Graceful error handling with friendly error messages
- **CORS Support**: Cross-origin resource sharing enabled for web clients

## Available Tools

### 1. Frame Extraction (`extract_frames`)
Extract frames from videos at regular intervals or specific timestamps.

**Parameters:**
- `interval_seconds` (number, optional): Interval between frames in seconds (default: 2.0)
- `max_frames` (integer, optional): Maximum number of frames to extract (default: 100)
- `timestamp` (number, optional): Extract single frame at specific timestamp

### 2. Image Captioning (`caption_frames`)
Generate natural language captions for video frames using BLIP.

**Parameters:**
- `frame_paths` (array of strings): List of frame image paths to caption
- `timestamps` (array of numbers): List of timestamps corresponding to frames

### 3. Audio Transcription (`transcribe_audio`)
Transcribe audio from videos using Whisper with timestamps.

**Parameters:**
- `language` (string, optional): Language code (e.g., 'en', 'es'). Auto-detected if not provided
- `start_time` (number, optional): Start time for segment transcription
- `end_time` (number, optional): End time for segment transcription

### 4. Object Detection (`detect_objects`)
Detect objects in video frames using YOLOv8.

**Parameters:**
- `frame_paths` (array of strings): List of frame image paths to analyze
- `timestamps` (array of numbers): List of timestamps corresponding to frames
- `confidence_threshold` (number, optional): Minimum confidence score (0-1, default: 0.25)
- `object_class` (string, optional): Specific object class to search for

## API Endpoints

### Server Information

#### `GET /`
Get server information and status.

**Response:**
```json
{
  "name": "BRI MCP Server",
  "version": "1.0.0",
  "status": "running",
  "tools_available": 4
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "cache_enabled": true,
  "tools_registered": 4
}
```

### Tool Discovery

#### `GET /tools`
List all available tools with their schemas.

**Response:**
```json
{
  "tools": [
    {
      "name": "extract_frames",
      "type": "function",
      "description": "Extract frames from video at regular intervals or specific timestamps",
      "parameters": {
        "type": "object",
        "properties": {
          "interval_seconds": {
            "type": "number",
            "description": "Interval between frames in seconds",
            "default": 2.0
          },
          ...
        }
      }
    },
    ...
  ]
}
```

### Tool Execution

#### `POST /tools/{tool_name}/execute`
Execute a specific tool with provided parameters.

**Request Body:**
```json
{
  "tool_name": "extract_frames",
  "video_id": "video_123",
  "parameters": {
    "interval_seconds": 2.0,
    "max_frames": 50
  }
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "frames": [...],
    "count": 50
  },
  "cached": false,
  "execution_time": 2.34
}
```

### Batch Processing

#### `POST /videos/{video_id}/process`
Process a video with multiple tools in batch.

**Request Body:**
```json
{
  "tools": ["extract_frames", "caption_frames", "transcribe_audio", "detect_objects"]
}
```

**Response:**
```json
{
  "status": "complete",
  "video_id": "video_123",
  "results": {
    "extract_frames": {
      "result": {...},
      "cached": false
    },
    "caption_frames": {
      "result": {...},
      "cached": false
    },
    ...
  },
  "errors": null,
  "execution_time": 45.67
}
```

### Cache Management

#### `GET /cache/stats`
Get cache statistics.

**Response:**
```json
{
  "enabled": true,
  "total_keys": 42,
  "redis_version": "7.0.0",
  "used_memory_human": "1.23M",
  "ttl_hours": 24
}
```

#### `DELETE /cache/videos/{video_id}`
Clear all cached results for a specific video.

**Response:**
```json
{
  "status": "success",
  "video_id": "video_123",
  "deleted_count": 4
}
```

#### `DELETE /cache`
Clear all BRI cache entries.

**Response:**
```json
{
  "status": "success",
  "message": "All cache entries cleared"
}
```

## Running the Server

### Development Mode

```bash
# Start the server with auto-reload
python mcp_server/main.py
```

Or using uvicorn directly:

```bash
uvicorn mcp_server.main:app --host localhost --port 8000 --reload
```

### Production Mode

```bash
# Start the server without auto-reload
uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Configuration

Configure the server using environment variables in `.env`:

```bash
# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
CACHE_TTL_HOURS=24

# Processing Configuration
MAX_FRAMES_PER_VIDEO=100
FRAME_EXTRACTION_INTERVAL=2.0

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

## Error Handling

The server implements comprehensive error handling:

- **404 Not Found**: Tool not found or video not found
- **500 Internal Server Error**: Tool execution failed or server error
- **Graceful Degradation**: If a tool fails during batch processing, other tools continue

Error responses include:
```json
{
  "status": "error",
  "result": {
    "error": "Detailed error message"
  },
  "cached": false,
  "execution_time": 0.12
}
```

## Caching Strategy

- **Cache Key Format**: `bri:tool:{tool_name}:{video_id}:{params_hash}`
- **TTL**: 24 hours (configurable via `CACHE_TTL_HOURS`)
- **Cache Hit**: Returns cached result immediately
- **Cache Miss**: Executes tool and caches result
- **Fallback**: If Redis is unavailable, caching is disabled but server continues to function

## Testing

Run the MCP server tests:

```bash
python scripts/test_mcp_server.py
```

## Architecture

```
mcp_server/
├── main.py          # FastAPI application and endpoints
├── registry.py      # Tool registry and tool implementations
├── cache.py         # Redis caching layer
└── README.md        # This file
```

## Dependencies

- **FastAPI**: Web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Redis**: Caching layer (optional)
- **Pydantic**: Data validation and serialization

## Future Enhancements

- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] WebSocket support for real-time progress updates
- [ ] Tool versioning
- [ ] Custom tool registration via API
- [ ] Metrics and monitoring endpoints
