# Context Builder Implementation Summary

## Overview

The Context Builder is a service component that aggregates video processing results and provides search capabilities for querying video content. It serves as the central data aggregation layer between the database and the agent.

## Implementation Details

### File Location
- **Module**: `services/context.py`
- **Test Script**: `scripts/test_context_builder.py`

### Key Classes

#### 1. ContextBuilder
Main class for aggregating and searching video processing results.

**Methods**:
- `build_video_context(video_id, include_conversation)`: Compile all available data for a video
- `search_captions(video_id, query, top_k)`: Find relevant captions using text similarity
- `search_transcripts(video_id, query)`: Search transcript for keywords
- `get_frames_with_object(video_id, object_class)`: Find frames containing specific objects
- `get_context_at_timestamp(video_id, timestamp, window)`: Retrieve all context around a specific time

#### 2. VideoContext (Dataclass)
Aggregated context for a video including all processed data.

**Fields**:
- `video_id`: Video identifier
- `metadata`: VideoMetadata object
- `frames`: List of Frame objects
- `captions`: List of Caption objects
- `transcript`: Transcript object
- `objects`: List of DetectionResult objects
- `conversation_history`: List of MemoryRecord objects

#### 3. TimestampContext (Dataclass)
Context around a specific timestamp in a video.

**Fields**:
- `timestamp`: Target timestamp
- `nearby_frames`: Frames within time window
- `captions`: Captions within time window
- `transcript_segment`: Transcript segment at timestamp
- `detected_objects`: Objects detected within time window

## Features Implemented

### 1. Video Context Aggregation
- Retrieves all processed data for a video from the database
- Combines metadata, frames, captions, transcripts, and object detections
- Optionally includes conversation history
- Handles missing data gracefully

### 2. Caption Search
- Keyword-based text similarity search
- Scores captions based on:
  - Exact phrase matching (highest priority)
  - Word overlap with query
  - Caption confidence scores
- Returns top-k most relevant results
- Sorted by relevance score

### 3. Transcript Search
- Simple keyword matching in transcript segments
- Case-insensitive search
- Returns all segments containing the query text
- Preserves timestamp information

### 4. Object-Based Frame Search
- Finds frames containing specific object classes
- Case-insensitive object class matching
- Returns frames with timestamps
- Handles partial matches (e.g., "ball" matches "sports ball")

### 5. Timestamp Context Retrieval
- Retrieves all context within a time window around a timestamp
- Configurable window size (default: ±5 seconds)
- Includes:
  - Nearby frames
  - Relevant captions
  - Transcript segment at timestamp
  - Detected objects in window

## Database Integration

### Data Retrieval
The Context Builder retrieves data from the `video_context` table:

```sql
-- Frames
SELECT data, timestamp FROM video_context 
WHERE video_id = ? AND context_type = 'frame'

-- Captions
SELECT data, timestamp FROM video_context 
WHERE video_id = ? AND context_type = 'caption'

-- Transcript
SELECT data FROM video_context 
WHERE video_id = ? AND context_type = 'transcript'

-- Objects
SELECT data, timestamp FROM video_context 
WHERE video_id = ? AND context_type = 'object'

-- Metadata
SELECT data FROM video_context 
WHERE video_id = ? AND context_type = 'metadata'
```

### Data Format
All data is stored as JSON in the `data` column and deserialized into Pydantic models.

## Testing

### Test Coverage
The test suite (`scripts/test_context_builder.py`) covers:

1. **build_video_context**: Verifies complete context aggregation
2. **search_captions**: Tests keyword search with various queries
3. **search_transcripts**: Tests transcript keyword search
4. **get_frames_with_object**: Tests object-based frame retrieval
5. **get_context_at_timestamp**: Tests timestamp-based context retrieval

### Test Results
All tests pass successfully:
- ✓ Context aggregation works correctly
- ✓ Caption search finds relevant results
- ✓ Transcript search finds matching segments
- ✓ Object search finds correct frames
- ✓ Timestamp context retrieval works with time windows

## Usage Examples

### Example 1: Build Complete Video Context
```python
from services.context import ContextBuilder

builder = ContextBuilder()
context = builder.build_video_context("vid_123")

print(f"Found {len(context.frames)} frames")
print(f"Found {len(context.captions)} captions")
print(f"Transcript: {context.transcript.full_text}")
```

### Example 2: Search Captions
```python
captions = builder.search_captions("vid_123", "person walking", top_k=5)
for caption in captions:
    print(f"{caption.frame_timestamp}s: {caption.text}")
```

### Example 3: Find Frames with Object
```python
frames = builder.get_frames_with_object("vid_123", "dog")
print(f"Found dog in {len(frames)} frames")
for frame in frames:
    print(f"Frame at {frame.timestamp}s: {frame.image_path}")
```

### Example 4: Get Context at Timestamp
```python
context = builder.get_context_at_timestamp("vid_123", 30.5, window=3.0)
print(f"At 30.5s:")
print(f"  Frames: {len(context.nearby_frames)}")
print(f"  Transcript: {context.transcript_segment.text}")
print(f"  Objects: {[obj.class_name for obj in context.detected_objects]}")
```

## Error Handling

### ContextError Exception
Custom exception raised when context operations fail.

### Graceful Degradation
- Missing data returns empty lists or None
- Warnings logged for retrieval failures
- Operations continue with available data

## Performance Considerations

### Optimization Strategies
1. **Database Indexing**: Uses indexes on `video_id`, `context_type`, and `timestamp`
2. **Lazy Loading**: Only retrieves requested data types
3. **Efficient Queries**: Single queries per data type
4. **In-Memory Processing**: Search operations performed in memory after retrieval

### Scalability Notes
- Current implementation uses simple keyword matching
- For production, consider:
  - Vector embeddings for semantic search
  - Caching frequently accessed contexts
  - Pagination for large result sets

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **Requirement 4.4**: Aggregates video processing results for agent queries
- **Requirement 8.1**: Provides context with timestamps and frames
- **Requirement 8.2**: Enables search across captions, transcripts, and objects

## Future Enhancements

1. **Semantic Search**: Use embeddings for better caption/transcript search
2. **Caching**: Cache frequently accessed contexts
3. **Pagination**: Support paginated results for large datasets
4. **Filtering**: Add filters for confidence scores, time ranges, etc.
5. **Aggregation**: Add statistics and summaries (e.g., most common objects)
6. **Multi-Video Search**: Search across multiple videos simultaneously

## Dependencies

- `models.video`: VideoMetadata, Frame
- `models.memory`: MemoryRecord
- `models.tools`: Caption, Transcript, TranscriptSegment, DetectionResult, DetectedObject
- `storage.database`: Database
- `services.memory`: Memory (for conversation history)

## Status

✅ **Implementation Complete**
✅ **All Tests Passing**
✅ **Ready for Integration**

The Context Builder is fully implemented and tested, ready to be integrated with the Tool Router and Groq Agent in subsequent tasks.
