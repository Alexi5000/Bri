# Task 23: Agent-UI Integration

## Overview

This task integrates the Groq-powered conversational agent with the Streamlit UI, enabling users to have natural conversations about their videos with full support for:
- Real-time agent responses
- Frame thumbnails in responses
- Clickable timestamps for video navigation
- Follow-up question suggestions
- Loading states during processing

## Implementation Details

### Components Modified

#### 1. `app.py` - Main Application

**Key Changes:**
- Replaced placeholder chat functionality with full agent integration
- Added `render_chat_with_agent()` function for agent-powered chat
- Added `process_user_message()` to handle async agent calls
- Added `display_agent_response()` to render rich responses
- Added helper functions for timestamp formatting

**New Functions:**

```python
def render_chat_with_agent(video_id: str, video_info: dict)
```
- Renders chat window with full agent integration
- Displays conversation history from database
- Handles user input and agent responses
- Manages loading states

```python
def process_user_message(video_id: str, message: str)
```
- Processes user messages through the GroqAgent
- Handles async/sync context bridging
- Stores responses for display
- Provides error handling

```python
def display_agent_response(response: AssistantMessageResponse)
```
- Displays agent responses with proper formatting
- Renders frame thumbnails in grid layout
- Shows clickable timestamps
- Displays follow-up suggestions as buttons

```python
def format_message_timestamp(timestamp) -> str
```
- Formats message timestamps (e.g., "just now", "5m ago")
- Handles relative time display

```python
def format_video_timestamp(seconds: float) -> str
```
- Formats video timestamps (e.g., "02:05", "01:02:05")
- Supports both MM:SS and HH:MM:SS formats

### Features Implemented

#### 1. Chat Input Connection (Requirement 4.1, 4.6)

The chat input is now connected to `GroqAgent.chat()` method:

```python
# In process_user_message()
agent = GroqAgent()
response = loop.run_until_complete(agent.chat(message, video_id))
```

**Features:**
- Form-based input with Enter key support
- Clear on submit for better UX
- Loading spinner during processing
- Error handling with friendly messages

#### 2. Agent Response Display (Requirement 8.1, 8.2)

Responses are displayed with proper formatting:

```python
# Message display with styling
st.markdown(f"""
<div style="padding: 1rem 1.25rem; border-radius: 20px; 
     background: white; border: 2px solid #E6E6FA;">
    {response.message}
</div>
""", unsafe_allow_html=True)
```

**Features:**
- Distinct styling for user vs. assistant messages
- Timestamp display for each message
- Emoji icons for visual distinction
- Rounded corners and soft shadows

#### 3. Frame Thumbnails (Requirement 8.1)

Frame thumbnails are rendered in a responsive grid:

```python
# Display frames in columns (max 3 per row)
for i in range(0, num_frames, cols_per_row):
    cols = st.columns(cols_per_row)
    for j in range(cols_per_row):
        with cols[j]:
            st.image(response.frames[idx], use_container_width=True)
```

**Features:**
- Responsive grid layout (max 3 per row)
- Full-width images within columns
- Error handling for missing frames
- Automatic thumbnail generation

#### 4. Clickable Timestamps (Requirement 8.2)

Timestamps are clickable and navigate to video moments:

```python
if st.button(f"⏱️ {timestamp_str}", key=f"frame_ts_{idx}_{timestamp}"):
    st.session_state["clicked_timestamp"] = timestamp
    st.rerun()
```

**Features:**
- Formatted timestamps (MM:SS or HH:MM:SS)
- Click to jump to video moment
- Visual feedback on hover
- Tooltip help text

#### 5. Follow-up Suggestions (Requirement 9.4)

Suggestions are displayed as clickable buttons:

```python
for idx, suggestion in enumerate(response.suggestions):
    if st.button(suggestion, key=f"suggestion_{idx}_{hash(suggestion)}"):
        st.session_state["selected_suggestion"] = suggestion
        st.rerun()
```

**Features:**
- Styled suggestion box with icon
- Clickable buttons for each suggestion
- Automatic processing when clicked
- Unique keys to prevent conflicts

#### 6. Loading States

Loading states provide feedback during processing:

```python
with st.spinner("🤔 Thinking..."):
    process_user_message(video_id, user_input.strip())
```

**Features:**
- Spinner with friendly message
- Blocks UI during processing
- Automatic dismissal on completion

### User Experience Flow

1. **User enters message** → Form input with placeholder text
2. **Click Send or press Enter** → Loading spinner appears
3. **Agent processes** → GroqAgent analyzes query and gathers context
4. **Response displayed** → Message, frames, timestamps, suggestions
5. **User clicks timestamp** → Video player jumps to moment
6. **User clicks suggestion** → New query processed automatically

### Integration with Existing Components

#### Memory Integration

```python
from services.memory import Memory
memory = Memory()
conversation_history = memory.get_conversation_history(video_id, limit=20)
```

- Retrieves conversation history from database
- Displays up to 20 recent messages
- Maintains context across sessions

#### Video Player Integration

```python
if st.session_state.get("clicked_timestamp"):
    navigate_to_timestamp(video_id, clicked_timestamp)
```

- Timestamps trigger video navigation
- Seamless integration with Task 21 player
- State management for timestamp clicks

#### Agent Integration

```python
agent = GroqAgent()
response = await agent.chat(message, video_id)
```

- Full integration with GroqAgent
- Async/sync context bridging
- Error handling and graceful degradation

## Testing

### Test Script: `scripts/test_task_23_integration.py`

Comprehensive test suite covering:

1. **Configuration Validation**
   - Verifies GROQ_API_KEY is set
   - Checks model configuration

2. **Agent Initialization**
   - Tests GroqAgent creation
   - Validates component setup

3. **Memory Integration**
   - Creates test video
   - Stores and retrieves messages
   - Validates foreign key constraints

4. **Response Formatting**
   - Tests timestamp formatting
   - Validates format functions

5. **Agent Chat**
   - End-to-end chat test
   - Validates response structure
   - Checks suggestions generation

### Running Tests

```bash
python scripts/test_task_23_integration.py
```

**Expected Output:**
```
============================================================
Task 23: Agent-UI Integration Tests
============================================================
✓ PASS: Configuration
✓ PASS: Agent Initialization
✓ PASS: Memory Integration
✓ PASS: Response Formatting
✓ PASS: Agent Chat

Total: 5/5 tests passed
🎉 All tests passed! Task 23 integration is complete.
```

## Requirements Satisfied

✅ **4.1** - Natural Language Query Processing
- Chat input connected to GroqAgent.chat method
- Full natural language understanding

✅ **4.6** - Supportive, Clear, Engaging Tone
- Agent responses use warm, friendly language
- Error messages are playful and helpful

✅ **8.1** - Response Generation with Timestamps and Media
- Responses include relevant timestamps
- Frame thumbnails displayed in grid

✅ **8.2** - Clickable Timestamps
- Timestamps are clickable buttons
- Navigate to specific video moments

✅ **9.4** - Follow-up Suggestions
- 1-3 suggestions displayed per response
- Clickable buttons for easy interaction

## Usage Example

### Starting a Conversation

1. Select a video from the sidebar
2. Type a question: "What's happening in this video?"
3. Press Enter or click Send
4. View BRI's response with frames and timestamps

### Clicking Timestamps

1. BRI shows relevant moments with timestamps
2. Click "⏱️ 02:15" button
3. Video player jumps to 2:15
4. Continue conversation about that moment

### Using Suggestions

1. BRI provides follow-up suggestions
2. Click a suggestion button
3. Question is automatically processed
4. New response appears

## Error Handling

### API Errors

```python
try:
    response = await agent.chat(message, video_id)
except Exception as e:
    st.error(f"Oops! Something went wrong: {str(e)}")
```

- Friendly error messages
- Graceful degradation
- Logging for debugging

### Missing Frames

```python
try:
    st.image(response.frames[idx], use_container_width=True)
except Exception as e:
    logger.warning(f"Failed to display frame: {e}")
```

- Continues without failing
- Logs warning for investigation
- Shows timestamp even if frame missing

## Performance Considerations

### Async/Sync Bridging

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
response = loop.run_until_complete(agent.chat(message, video_id))
loop.close()
```

- Proper event loop management
- Prevents blocking UI thread
- Clean resource cleanup

### Session State Management

```python
st.session_state.pending_response = response
st.session_state.clicked_timestamp = timestamp
st.session_state.selected_suggestion = suggestion
```

- Efficient state storage
- Prevents unnecessary reruns
- Clean state transitions

### Memory Limits

```python
conversation_history = memory.get_conversation_history(video_id, limit=20)
```

- Limits history to 20 messages
- Prevents UI slowdown
- Maintains performance

## Future Enhancements

1. **Streaming Responses**
   - Stream agent responses token by token
   - Better perceived performance

2. **Voice Input**
   - Add microphone button
   - Speech-to-text integration

3. **Message Editing**
   - Edit previous messages
   - Regenerate responses

4. **Export Conversations**
   - Download chat history
   - Share conversations

5. **Multi-modal Input**
   - Upload images for comparison
   - Draw on video frames

## Conclusion

Task 23 successfully integrates the Groq-powered agent with the Streamlit UI, providing a complete conversational experience for video analysis. Users can now:

- Ask natural language questions about videos
- Receive intelligent responses with context
- View relevant frames and timestamps
- Navigate to specific video moments
- Explore content through suggestions
- Maintain conversation history

The integration is robust, user-friendly, and ready for production use.
