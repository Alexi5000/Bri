# Data Flow Audit - BRI Video Agent

## Executive Summary

**Date:** 2025-10-16  
**Status:** CRITICAL ISSUES IDENTIFIED  
**Priority:** Fix data persistence gaps immediately

### Key Findings

✅ **Working:**
- MCP server `/videos/{video_id}/process` endpoint stores results in database
- MCP server `/tools/{tool_name}/execute` endpoint has storage logic implemented
- Database schema supports all data types (frames, captions, transcripts, objects)
- Context Builder can retrieve data from database

❌ **Broken:**
- Individual tool classes (FrameExtractor, ImageCaptioner, etc.) do NOT store results
- Tools only return data in memory - no database persistence
- Agent relies on database for context but tools don't populate it
- Silent failures: tools execute successfully but data is lost

---

## Complete Data Flow Map

### 1. Upload → Extract → Process → Store → Retrieve

```
┌─────────────────────────────────────────────────────────────────┐
│ UPLOAD PHASE                                                     │
├─────────────────────────────────────────────────────────────────┤
│ User uploads video via Streamlit UI                             │
│   ↓                                                              │
│ storage/file_store.py saves video file                          │
│   ↓                                                              │
│ storage/database.py inserts video record                        │
│   ↓                                                              │
│ Status: 'pending' ✅ WORKS                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PROCESSING PHASE                                                 │
├─────────────────────────────────────────────────────────────────┤
│ services/video_processor.py triggers batch processing           │
│   ↓                                                              │
│ POST /videos/{video_id}/process on MCP server                   │
│   ↓                                                              │
│ mcp_server/main.py orchestrates parallel tool execution         │
│   ↓                                                              │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │ Tool Execution (4 tools in parallel)                    │    │
│ │                                                          │    │
│ │ 1. extract_frames → tools/frame_extractor.py           │    │
│ │    - Extracts frames to disk ✅                         │    │
│ │    - Returns Frame objects in memory ✅                 │    │
│ │    - Database storage: ❌ NOT IMPLEMENTED               │    │
│ │                                                          │    │
│ │ 2. caption_frames → tools/image_captioner.py           │    │
│ │    - Generates captions ✅                              │    │
│ │    - Returns Caption objects in memory ✅               │    │
│ │    - Database storage: ❌ NOT IMPLEMENTED               │    │
│ │                                                          │    │
│ │ 3. transcribe_audio → tools/audio_transcriber.py       │    │
│ │    - Transcribes audio ✅                               │    │
│ │    - Returns Transcript object in memory ✅             │    │
│ │    - Database storage: ❌ NOT IMPLEMENTED               │    │
│ │                                                          │    │
│ │ 4. detect_objects → tools/object_detector.py           │    │
│ │    - Detects objects ✅                                 │    │
│ │    - Returns DetectionResult objects in memory ✅       │    │
│ │    - Database storage: ❌ NOT IMPLEMENTED               │    │
│ └─────────────────────────────────────────────────────────┘    │
│   ↓                                                              │
│ mcp_server/main.py receives results                             │
│   ↓                                                              │
│ _store_tool_result_in_db() called ✅ IMPLEMENTED                │
│   ↓                                                              │
│ Results stored in video_context table ✅ WORKS                  │
│   ↓                                                              │
│ Status updated to 'complete' ✅ WORKS                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ RETRIEVAL PHASE                                                  │
├─────────────────────────────────────────────────────────────────┤
│ User asks question via chat                                     │
│   ↓                                                              │
│ services/agent.py processes query                               │
│   ↓                                                              │
│ services/context.py builds context from database                │
│   ↓                                                              │
│ Queries video_context table for:                                │
│   - Frames (context_type='frame')                               │
│   - Captions (context_type='caption')                           │
│   - Transcripts (context_type='transcript')                     │
│   - Objects (context_type='object')                             │
│   ↓                                                              │
│ Returns VideoContext with all data ✅ WORKS IF DATA EXISTS      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Endpoint Storage Analysis

### MCP Server Endpoints

#### ✅ POST `/videos/{video_id}/process` - STORES DATA
**Location:** `mcp_server/main.py:process_video()`

**Flow:**
1. Executes tools in parallel via `_execute_tool_with_cache()`
2. Each tool result is cached in Redis
3. **CRITICAL:** Calls `_store_tool_result_in_db()` for each tool ✅
4. Stores results in `video_context` table

**Storage Logic:**
```python
def _store_tool_result_in_db(video_id: str, tool_name: str, result: dict):
    # Stores captions, transcripts, objects, frames in video_context table
    # Uses INSERT INTO video_context (video_id, context_type, timestamp, data)
```

**Status:** ✅ WORKING - Data is persisted

---

#### ✅ POST `/tools/{tool_name}/execute` - STORES DATA
**Location:** `mcp_server/main.py:execute_tool()`

**Flow:**
1. Checks cache first
2. Executes tool via `tool.execute()`
3. Caches result
4. **CRITICAL:** Calls `_store_tool_result_in_db()` ✅
5. Returns result

**Status:** ✅ WORKING - Data is persisted

---

### Tool Classes (Individual Execution)

#### ❌ `tools/frame_extractor.py` - NO STORAGE
**Methods:**
- `extract_frames()` - Returns `List[Frame]`, saves images to disk
- `extract_frame_at_timestamp()` - Returns `Frame`, saves image to disk
- `get_video_metadata()` - Returns `VideoMetadata`

**Storage:** ❌ NONE - Only returns data in memory

---

#### ❌ `tools/image_captioner.py` - NO STORAGE
**Methods:**
- `caption_frame()` - Returns `Caption`
- `caption_frames_batch()` - Returns `List[Caption]`

**Storage:** ❌ NONE - Only returns data in memory

---

#### ❌ `tools/audio_transcriber.py` - NO STORAGE
**Methods:**
- `transcribe_video()` - Returns `Transcript`
- `transcribe_segment()` - Returns `TranscriptSegment`

**Storage:** ❌ NONE - Only returns data in memory

---

#### ❌ `tools/object_detector.py` - NO STORAGE
**Methods:**
- `detect_objects_in_frames()` - Returns `List[DetectionResult]`
- `search_for_object()` - Returns `List[DetectionResult]`

**Storage:** ❌ NONE - Only returns data in memory

---

## 3. Data Persistence Gaps

### Gap #1: Tool Classes Don't Store Results
**Problem:** Individual tool classes have no database integration
**Impact:** If tools are called directly (not via MCP server), data is lost
**Solution:** Tools should remain stateless; MCP server handles storage ✅

### Gap #2: No Validation After Storage
**Problem:** No verification that data was actually written to database
**Impact:** Silent failures - processing completes but data is missing
**Solution:** Add SELECT after INSERT to confirm data persistence

### Gap #3: No Transaction Support
**Problem:** Multi-step operations can fail partially
**Impact:** Inconsistent state - some data stored, some lost
**Solution:** Wrap storage operations in database transactions

### Gap #4: No Retry Logic
**Problem:** Database write failures are not retried
**Impact:** Transient errors cause permanent data loss
**Solution:** Implement exponential backoff retry for failed writes

---

## 4. Current vs Desired State

### Current State (Broken)
```
Tool Execution → Returns Data → MCP Server → Stores in DB
                                              ↓
                                         Sometimes fails
                                              ↓
                                         No validation
                                              ↓
                                         Silent failure
```

### Desired State (Fixed)
```
Tool Execution → Returns Data → MCP Server → Transaction Start
                                              ↓
                                         Store in DB
                                              ↓
                                         Validate (SELECT)
                                              ↓
                                         Retry if failed
                                              ↓
                                         Transaction Commit
                                              ↓
                                         Log metrics
```

---

## 5. Recommendations

### Immediate Actions (Task 40.2)
1. ✅ Keep `_store_tool_result_in_db()` in MCP server (already exists)
2. ✅ Add transaction support to database writes
3. ✅ Add validation after INSERT (SELECT to confirm)
4. ✅ Implement retry logic with exponential backoff
5. ✅ Create `VideoProcessingService` to centralize storage logic

### Verification Actions (Task 40.3)
1. Create `verify_video_data()` function
2. Check completeness: frames, captions, transcripts, objects
3. Add GET `/videos/{video_id}/status` endpoint
4. Return detailed status report

### Testing Actions (Task 40.4)
1. Test `/tools/{tool_name}/execute` storage
2. Test `/videos/{video_id}/process` storage
3. Add database write confirmation logs
4. Add metrics: "X captions stored", "Y transcript segments stored"

---

## 6. Database Schema Verification

### ✅ Schema Supports All Data Types

```sql
CREATE TABLE video_context (
    context_id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    context_type TEXT NOT NULL,  -- 'frame', 'caption', 'transcript', 'object'
    timestamp REAL,
    data TEXT NOT NULL,  -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    CHECK (context_type IN ('frame', 'caption', 'transcript', 'object', 'metadata'))
);
```

**Status:** ✅ Schema is correct and supports all data types

---

## Conclusion

**Root Cause:** Data persistence is implemented in MCP server but lacks:
- Transaction support
- Validation after writes
- Retry logic for failures
- Comprehensive logging

**Fix Strategy:** Enhance `_store_tool_result_in_db()` with:
1. Database transactions
2. Write validation
3. Retry logic
4. Detailed logging

**Expected Outcome:** 100% data persistence reliability
