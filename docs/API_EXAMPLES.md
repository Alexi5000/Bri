# BRI API Examples

This guide provides practical examples for interacting with the BRI MCP Server API.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Server Information](#server-information)
3. [Tool Discovery](#tool-discovery)
4. [Frame Extraction](#frame-extraction)
5. [Image Captioning](#image-captioning)
6. [Audio Transcription](#audio-transcription)
7. [Object Detection](#object-detection)
8. [Batch Processing](#batch-processing)
9. [Cache Management](#cache-management)
10. [Error Handling](#error-handling)
11. [Python Client Examples](#python-client-examples)

## Getting Started

### Base URL

```
http://localhost:8000
```

### Prerequisites

- MCP server running (`python mcp_server/main.py`)
- Video uploaded and stored in the system
- Video ID from the database

### Tools Used in Examples

- **curl**: Command-line HTTP client
- **Python requests**: Python HTTP library
- **jq**: JSON processor (optional, for formatting)

## Server Information

### Get Server Status

```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "name": "BRI MCP Server",
  "version": "1.0.0",
  "status": "running",
  "tools_available": 4
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "cache_enabled": true,
  "tools_registered": 4
}
```

## Tool Discovery

### List All Available Tools

```bash
curl http://localhost:8000/tools | jq
```

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
          "max_frames": {
            "type": "integer",
            "description": "Maximum number of frames to extract",
            "default": 100
          }
        }
      }
    }
  ]
}
```

## Frame Extraction

### Extract Frames at Regular Intervals

```bash
curl -X POST http://localhost:8000/tools/extract_frames/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {
      "interval_seconds": 2.0,
      "max_frames": 50
    }
  }' | jq
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "frames": [
      {
        "timestamp": 0.0,
        "frame_number": 0,
        "image_path": "data/frames/video_123/frame_0000.jpg"
      },
      {
        "timestamp": 2.0,
        "frame_number": 60,
        "image_path": "data/frames/video_123/frame_0060.jpg"
      }
    ],
    "count": 50,
    "video_metadata": {
      "duration": 120.5,
      "fps": 30.0,
      "width": 1920,
      "height": 1080
    }
  },
  "cached": false,
  "execution_time": 3.45
}
```

### Extract Single Frame at Timestamp

```bash
curl -X POST http://localhost:8000/tools/extract_frames/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {
      "timestamp": 45.5
    }
  }' | jq
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "frame": {
      "timestamp": 45.5,
      "frame_number": 1365,
      "image_path": "data/frames/video_123/frame_1365.jpg"
    }
  },
  "cached": false,
  "execution_time": 0.23
}
```

## Image Captioning

### Caption Multiple Frames

```bash
curl -X POST http://localhost:8000/tools/caption_frames/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {
      "frame_paths": [
        "data/frames/video_123/frame_0000.jpg",
        "data/frames/video_123/frame_0060.jpg",
        "data/frames/video_123/frame_0120.jpg"
      ],
      "timestamps": [0.0, 2.0, 4.0]
    }
  }' | jq
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "captions": [
      {
        "frame_timestamp": 0.0,
        "text": "a person sitting at a desk with a laptop computer",
        "confidence": 0.92
      },
      {
        "frame_timestamp": 2.0,
        "text": "a close up of a computer screen showing code",
        "confidence": 0.88
      },
      {
        "frame_timestamp": 4.0,
        "text": "a person typing on a keyboard",
        "confidence": 0.91
      }
    ],
    "count": 3
  },
  "cached": false,
  "execution_time": 2.15
}
```

## Audio Transcription

### Transcribe Full Video

```bash
curl -X POST http://localhost:8000/tools/transcribe_audio/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {}
  }' | jq
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "transcript": {
      "segments": [
        {
          "start": 0.0,
          "end": 3.5,
          "text": "Hello everyone, welcome to this tutorial.",
          "confidence": 0.95
        },
        {
          "start": 3.5,
          "end": 7.2,
          "text": "Today we're going to learn about video processing.",
          "confidence": 0.93
        }
      ],
      "language": "en",
      "full_text": "Hello everyone, welcome to this tutorial. Today we're going to learn about video processing."
    }
  },
  "cached": false,
  "execution_time": 15.67
}
```

### Transcribe Specific Segment

```bash
curl -X POST http://localhost:8000/tools/transcribe_audio/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {
      "start_time": 30.0,
      "end_time": 45.0
    }
  }' | jq
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "segment": {
      "start": 30.0,
      "end": 45.0,
      "text": "This is the most important part of the process. Make sure to follow these steps carefully.",
      "confidence": 0.94
    }
  },
  "cached": false,
  "execution_time": 3.21
}
```

## Object Detection

### Detect Objects in Frames

```bash
curl -X POST http://localhost:8000/tools/detect_objects/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {
      "frame_paths": [
        "data/frames/video_123/frame_0000.jpg",
        "data/frames/video_123/frame_0060.jpg"
      ],
      "timestamps": [0.0, 2.0],
      "confidence_threshold": 0.5
    }
  }' | jq
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "detections": [
      {
        "frame_timestamp": 0.0,
        "objects": [
          {
            "class_name": "person",
            "confidence": 0.92,
            "bbox": [100, 50, 300, 400]
          },
          {
            "class_name": "laptop",
            "confidence": 0.87,
            "bbox": [150, 200, 250, 150]
          }
        ]
      },
      {
        "frame_timestamp": 2.0,
        "objects": [
          {
            "class_name": "person",
            "confidence": 0.91,
            "bbox": [105, 52, 295, 398]
          }
        ]
      }
    ],
    "total_objects": 3
  },
  "cached": false,
  "execution_time": 1.89
}
```

### Search for Specific Object

```bash
curl -X POST http://localhost:8000/tools/detect_objects/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {
      "frame_paths": [
        "data/frames/video_123/frame_0000.jpg",
        "data/frames/video_123/frame_0060.jpg",
        "data/frames/video_123/frame_0120.jpg"
      ],
      "timestamps": [0.0, 2.0, 4.0],
      "object_class": "cat"
    }
  }' | jq
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "occurrences": [
      {
        "timestamp": 2.0,
        "frame_path": "data/frames/video_123/frame_0060.jpg",
        "confidence": 0.89,
        "bbox": [200, 150, 180, 200]
      },
      {
        "timestamp": 4.0,
        "frame_path": "data/frames/video_123/frame_0120.jpg",
        "confidence": 0.91,
        "bbox": [210, 155, 175, 195]
      }
    ],
    "total_found": 2
  },
  "cached": false,
  "execution_time": 1.45
}
```

## Batch Processing

### Process Video with All Tools

```bash
curl -X POST http://localhost:8000/videos/video_123/process \
  -H "Content-Type: application/json" \
  -d '{
    "tools": ["extract_frames", "caption_frames", "transcribe_audio", "detect_objects"]
  }' | jq
```

**Response:**
```json
{
  "status": "complete",
  "video_id": "video_123",
  "results": {
    "extract_frames": {
      "status": "success",
      "result": {
        "frames": [...],
        "count": 50
      },
      "cached": false,
      "execution_time": 3.45
    },
    "caption_frames": {
      "status": "success",
      "result": {
        "captions": [...],
        "count": 50
      },
      "cached": false,
      "execution_time": 12.34
    },
    "transcribe_audio": {
      "status": "success",
      "result": {
        "transcript": {...}
      },
      "cached": false,
      "execution_time": 15.67
    },
    "detect_objects": {
      "status": "success",
      "result": {
        "detections": [...],
        "total_objects": 127
      },
      "cached": false,
      "execution_time": 8.92
    }
  },
  "errors": null,
  "total_execution_time": 40.38
}
```

### Process with Specific Tools Only

```bash
curl -X POST http://localhost:8000/videos/video_123/process \
  -H "Content-Type: application/json" \
  -d '{
    "tools": ["extract_frames", "caption_frames"]
  }' | jq
```

## Cache Management

### Get Cache Statistics

```bash
curl http://localhost:8000/cache/stats | jq
```

**Response:**
```json
{
  "enabled": true,
  "total_keys": 42,
  "redis_version": "7.0.0",
  "used_memory_human": "1.23M",
  "ttl_hours": 24,
  "hit_rate": 0.67
}
```

### Clear Cache for Specific Video

```bash
curl -X DELETE http://localhost:8000/cache/videos/video_123 | jq
```

**Response:**
```json
{
  "status": "success",
  "video_id": "video_123",
  "deleted_count": 4,
  "message": "Cache cleared for video_123"
}
```

### Clear All Cache

```bash
curl -X DELETE http://localhost:8000/cache | jq
```

**Response:**
```json
{
  "status": "success",
  "message": "All cache entries cleared",
  "deleted_count": 42
}
```

## Error Handling

### Tool Not Found

```bash
curl -X POST http://localhost:8000/tools/invalid_tool/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {}
  }' | jq
```

**Response (404):**
```json
{
  "detail": "Tool 'invalid_tool' not found"
}
```

### Tool Execution Failed

```bash
curl -X POST http://localhost:8000/tools/extract_frames/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "nonexistent_video",
    "parameters": {}
  }' | jq
```

**Response (500):**
```json
{
  "status": "error",
  "result": {
    "error": "Video file not found: data/videos/nonexistent_video.mp4"
  },
  "cached": false,
  "execution_time": 0.05
}
```

### Invalid Parameters

```bash
curl -X POST http://localhost:8000/tools/extract_frames/execute \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "video_123",
    "parameters": {
      "interval_seconds": "invalid"
    }
  }' | jq
```

**Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "parameters", "interval_seconds"],
      "msg": "value is not a valid float",
      "type": "type_error.float"
    }
  ]
}
```

## Python Client Examples

### Basic Client Setup

```python
import requests
import json

class BRIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check if server is healthy"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def list_tools(self):
        """Get all available tools"""
        response = self.session.get(f"{self.base_url}/tools")
        return response.json()
    
    def execute_tool(self, tool_name, video_id, parameters=None):
        """Execute a specific tool"""
        payload = {
            "video_id": video_id,
            "parameters": parameters or {}
        }
        response = self.session.post(
            f"{self.base_url}/tools/{tool_name}/execute",
            json=payload
        )
        return response.json()
    
    def process_video(self, video_id, tools=None):
        """Process video with multiple tools"""
        payload = {
            "tools": tools or ["extract_frames", "caption_frames", 
                              "transcribe_audio", "detect_objects"]
        }
        response = self.session.post(
            f"{self.base_url}/videos/{video_id}/process",
            json=payload
        )
        return response.json()

# Usage
client = BRIClient()

# Check health
health = client.health_check()
print(f"Server status: {health['status']}")

# List tools
tools = client.list_tools()
print(f"Available tools: {len(tools['tools'])}")

# Extract frames
result = client.execute_tool(
    "extract_frames",
    "video_123",
    {"interval_seconds": 2.0, "max_frames": 50}
)
print(f"Extracted {result['result']['count']} frames")
```

### Extract and Caption Frames

```python
def extract_and_caption(client, video_id):
    """Extract frames and generate captions"""
    
    # Step 1: Extract frames
    print("Extracting frames...")
    frames_result = client.execute_tool(
        "extract_frames",
        video_id,
        {"interval_seconds": 5.0, "max_frames": 20}
    )
    
    if frames_result["status"] != "success":
        print(f"Error: {frames_result['result']['error']}")
        return
    
    frames = frames_result["result"]["frames"]
    print(f"Extracted {len(frames)} frames")
    
    # Step 2: Caption frames
    print("Generating captions...")
    frame_paths = [f["image_path"] for f in frames]
    timestamps = [f["timestamp"] for f in frames]
    
    captions_result = client.execute_tool(
        "caption_frames",
        video_id,
        {
            "frame_paths": frame_paths,
            "timestamps": timestamps
        }
    )
    
    if captions_result["status"] != "success":
        print(f"Error: {captions_result['result']['error']}")
        return
    
    # Display results
    captions = captions_result["result"]["captions"]
    for caption in captions:
        print(f"[{caption['frame_timestamp']:.1f}s] {caption['text']}")

# Usage
client = BRIClient()
extract_and_caption(client, "video_123")
```

### Search for Objects

```python
def find_object_in_video(client, video_id, object_class):
    """Find all occurrences of an object in a video"""
    
    # First, extract frames
    frames_result = client.execute_tool(
        "extract_frames",
        video_id,
        {"interval_seconds": 2.0}
    )
    
    if frames_result["status"] != "success":
        return []
    
    frames = frames_result["result"]["frames"]
    frame_paths = [f["image_path"] for f in frames]
    timestamps = [f["timestamp"] for f in frames]
    
    # Detect objects
    detection_result = client.execute_tool(
        "detect_objects",
        video_id,
        {
            "frame_paths": frame_paths,
            "timestamps": timestamps,
            "object_class": object_class
        }
    )
    
    if detection_result["status"] != "success":
        return []
    
    occurrences = detection_result["result"]["occurrences"]
    
    print(f"Found {len(occurrences)} occurrences of '{object_class}':")
    for occ in occurrences:
        print(f"  - At {occ['timestamp']:.1f}s (confidence: {occ['confidence']:.2f})")
    
    return occurrences

# Usage
client = BRIClient()
find_object_in_video(client, "video_123", "cat")
```

### Async Client Example

```python
import aiohttp
import asyncio

class AsyncBRIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def execute_tool(self, session, tool_name, video_id, parameters=None):
        """Execute a tool asynchronously"""
        payload = {
            "video_id": video_id,
            "parameters": parameters or {}
        }
        async with session.post(
            f"{self.base_url}/tools/{tool_name}/execute",
            json=payload
        ) as response:
            return await response.json()
    
    async def process_video_parallel(self, video_id):
        """Process video with multiple tools in parallel"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.execute_tool(session, "extract_frames", video_id),
                self.execute_tool(session, "transcribe_audio", video_id),
            ]
            results = await asyncio.gather(*tasks)
            return results

# Usage
async def main():
    client = AsyncBRIClient()
    results = await client.process_video_parallel("video_123")
    print(f"Completed {len(results)} tasks")

asyncio.run(main())
```

## Best Practices

### 1. Use Batch Processing

Instead of calling tools individually, use the batch processing endpoint:

```bash
# Good: Single request
curl -X POST http://localhost:8000/videos/video_123/process \
  -d '{"tools": ["extract_frames", "caption_frames"]}'

# Less efficient: Multiple requests
curl -X POST http://localhost:8000/tools/extract_frames/execute ...
curl -X POST http://localhost:8000/tools/caption_frames/execute ...
```

### 2. Leverage Caching

Repeated queries with the same parameters will use cached results:

```python
# First call: processes video
result1 = client.execute_tool("extract_frames", "video_123")
print(f"Cached: {result1['cached']}")  # False

# Second call: uses cache
result2 = client.execute_tool("extract_frames", "video_123")
print(f"Cached: {result2['cached']}")  # True
```

### 3. Handle Errors Gracefully

```python
def safe_execute(client, tool_name, video_id, parameters=None):
    try:
        result = client.execute_tool(tool_name, video_id, parameters)
        if result["status"] == "error":
            print(f"Tool error: {result['result']['error']}")
            return None
        return result["result"]
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
```

### 4. Monitor Performance

```python
result = client.execute_tool("extract_frames", "video_123")
print(f"Execution time: {result['execution_time']:.2f}s")
print(f"Cached: {result['cached']}")
```

### 5. Clear Cache When Needed

```python
# Clear cache after video updates
client.session.delete(f"{client.base_url}/cache/videos/{video_id}")
```

---

For more information, see:
- [MCP Server README](../mcp_server/README.md) - Complete API reference
- [User Guide](USER_GUIDE.md) - Using BRI through the UI
- [Configuration](CONFIGURATION.md) - Server configuration options
