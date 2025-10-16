# BRI Video Agent - Execution Plan to 100%

## 🎯 Mission
Get BRI to 100% functionality with fluent, intelligent video chat within 30-60 seconds of upload.

## 🔍 Root Cause Analysis

### What We Built (Good Architecture)
- ✅ Solid ML pipeline (BLIP, Whisper, YOLO)
- ✅ Well-designed database schema
- ✅ Smart agent with context building
- ✅ MCP server with tool registry
- ✅ Clean separation of concerns

### What's Broken (Data Pipeline)
- ❌ **Tools execute but don't save results to database**
- ❌ **Agent can't find data that tools generated**
- ❌ **No progressive processing (all-or-nothing)**
- ❌ **Tests run against unprocessed videos**
- ❌ **Silent failures in data storage**

### The Disconnect
```
Current (Broken):
Upload → Extract Frames → [Tools Run] → Results Lost → Agent: "No data"

Desired (Working):
Upload → Extract Frames → Tools Run → Results Saved → Agent: "Smart answers"
```

## 📋 Execution Sequence

### **Task 40: Fix Data Persistence** (Priority: CRITICAL)

**Time Estimate: 2-3 hours**

#### 40.1 Run System Diagnostic
```bash
python diagnose_system.py
```
This will show you exactly what's broken.

#### 40.2 Verify MCP Server Fix
The fix is already in place (`_store_tool_result_in_db` added to individual tool execution).

**Action Required:**
1. Restart MCP server to pick up changes
2. Verify logs show "Stored X results in database"

#### 40.3 Test Data Storage
```bash
# Start MCP server
python mcp_server/main.py

# In another terminal, process a video
python process_test_video.py 75befeed-4502-492c-a62d-d30d1852ef9a

# Check if data was stored
python diagnose_system.py
```

**Expected Result:** Diagnostic shows captions, transcripts, objects > 0

#### 40.4 Add Verification Layer
Create `VideoProcessingService` that:
- Wraps all tool calls
- Verifies data was written after each tool
- Logs: "✓ Stored 87 captions for video X"
- Raises error if verification fails

---

### **Task 41: Progressive Processing** (Priority: HIGH)

**Time Estimate: 3-4 hours**

#### 41.1 Implement Staged Processing

**Stage 1 (Fast - 10s):** Extract frames only
```python
# In mcp_server/main.py
@app.post("/videos/{video_id}/process/stage1")
async def process_stage1(video_id: str):
    # Extract frames only
    # Update status: 'extracting'
    # Return immediately
```

**Stage 2 (Medium - 60s):** Generate captions
```python
@app.post("/videos/{video_id}/process/stage2")
async def process_stage2(video_id: str, background_tasks: BackgroundTasks):
    # Run captioning in background
    # Update status: 'captioning'
```

**Stage 3 (Slow - 120s):** Full analysis
```python
@app.post("/videos/{video_id}/process/stage3")
async def process_stage3(video_id: str, background_tasks: BackgroundTasks):
    # Run transcription + object detection
    # Update status: 'complete'
```

#### 41.2 Update Upload Flow
```python
# In Streamlit app
def handle_upload(video_file):
    # 1. Save video
    video_id = save_video(video_file)
    
    # 2. Start Stage 1 (blocking - 10s)
    process_stage1(video_id)
    
    # 3. Start Stage 2 & 3 (background)
    process_stage2(video_id)
    process_stage3(video_id)
    
    # 4. Enable chat immediately
    st.success("Video ready! Start chatting (full analysis in progress...)")
```

#### 41.3 Update Agent for Partial Data
```python
# In services/agent.py
def _check_video_context_exists(self, video_id: str) -> bool:
    # Accept video if it has ANY data (frames, captions, etc.)
    context = self.context_builder.build_video_context(video_id)
    return bool(context.frames or context.captions or context.transcript)

def _respond_with_partial_data(self, message: str, video_id: str):
    # Build response from whatever data is available
    # Add notice: "Still processing audio..." if transcript missing
```

---

### **Task 42: Agent Intelligence** (Priority: HIGH)

**Time Estimate: 2-3 hours**

#### 42.1 Fix Context Retrieval
```python
# In services/context.py
def build_video_context(self, video_id: str) -> VideoContext:
    # MUST retrieve ALL available data
    # Log what was found: "Found: 87 frames, 87 captions, 0 transcripts"
    # Never return empty context if ANY data exists
```

#### 42.2 Improve Query Routing
```python
# In services/router.py
def analyze_query(self, message: str) -> ToolPlan:
    # Visual questions → prioritize captions
    # Audio questions → prioritize transcripts
    # If data missing → trigger processing
```

#### 42.3 Optimize Prompts
- Reduce context size (top 10 relevant moments, not all 87)
- Structure: "Visual: ..., Audio: ..., Objects: ..."
- Add examples of good responses to system prompt

---

### **Task 43: Testing & Validation** (Priority: CRITICAL)

**Time Estimate: 2 hours**

#### 43.1 End-to-End Test
```bash
# 1. Upload video
# 2. Wait for processing
# 3. Verify data stored
python diagnose_system.py

# 4. Run evaluation
python tests/eval_bri_performance.py <video_id>

# Expected: 90%+ pass rate
```

#### 43.2 Create Smoke Test
```python
# tests/smoke_test.py
def test_complete_pipeline():
    # Upload video
    video_id = upload_test_video()
    
    # Process
    process_video(video_id)
    
    # Verify data
    assert get_frame_count(video_id) > 0
    assert get_caption_count(video_id) > 0
    assert get_transcript_count(video_id) > 0
    
    # Test agent
    response = agent.chat("What's in this video?", video_id)
    assert len(response.message) > 50
    assert "video" in response.message.lower()
```

---

## 🚀 Quick Start (Do This Now)

### Step 1: Diagnose
```bash
python diagnose_system.py
```

### Step 2: Fix Data Storage
```bash
# Terminal 1: Start MCP server
python mcp_server/main.py

# Terminal 2: Process video
python process_test_video.py 75befeed-4502-492c-a62d-d30d1852ef9a

# Terminal 3: Verify
python diagnose_system.py
```

### Step 3: Test Agent
```bash
python tests/eval_bri_performance.py 75befeed-4502-492c-a62d-d30d1852ef9a
```

**Expected Result:** 90%+ pass rate

---

## 📊 Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Test Pass Rate | 74% | 90%+ |
| Data Storage | 0% | 100% |
| Chat Availability | N/A | <30s |
| Full Processing | N/A | <120s |
| Agent Response Quality | Partial | Excellent |

---

## 🎯 Definition of Done

- [ ] Diagnostic shows 100% data storage
- [ ] Agent test pass rate ≥ 90%
- [ ] Chat available within 30 seconds of upload
- [ ] Full processing completes within 2 minutes
- [ ] Agent provides intelligent, contextual responses
- [ ] Zero silent failures in data pipeline
- [ ] All 50 test queries answered correctly

---

## 🔧 Tools Created

1. **diagnose_system.py** - Shows exactly what's broken
2. **process_test_video.py** - Processes a video through MCP server
3. **analyze_failures.py** - Analyzes test failures
4. **check_video_context.py** - Checks video data completeness

---

## 💡 Key Insights

1. **The architecture is solid** - We just have a data persistence bug
2. **The fix is simple** - Ensure tool results are stored
3. **The test is clear** - Run diagnostic → process → test
4. **The goal is achievable** - 90% is within reach with proper data flow

---

## 🎬 Next Action

**Run this command right now:**
```bash
python diagnose_system.py
```

This will tell you exactly what to fix next.
