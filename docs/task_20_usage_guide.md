# Chat Window Component - Usage Guide

## Quick Start

### Basic Usage

```python
import streamlit as st
from ui.chat import render_chat_window
from services.memory import Memory
from models.memory import MemoryRecord

# Initialize memory
memory = Memory()

# Get conversation history
video_id = "vid_123"
conversation_history = memory.get_conversation_history(video_id)

# Define message handler
def handle_send_message(message: str):
    # Process message (integrate with agent)
    response = f"You said: {message}"
    
    # Store in memory
    memory.add_memory_pair(video_id, message, response)
    
    # Refresh UI
    st.rerun()

# Render chat window
render_chat_window(video_id, conversation_history, handle_send_message)
```

## Advanced Usage

### With Agent Integration

```python
from ui.chat import render_chat_window, render_assistant_response
from services.agent import GroqAgent
from services.memory import Memory

# Initialize components
agent = GroqAgent(api_key="your_key")
memory = Memory()

# Get conversation history
video_id = st.session_state.get("current_video_id")
conversation_history = memory.get_conversation_history(video_id)

# Message handler with agent
def handle_send_message(message: str):
    # Show loading state
    with st.spinner("BRI is thinking... 💭"):
        # Get agent response
        response = agent.chat(message, video_id)
        
        # Store in memory
        memory.add_memory_pair(video_id, message, response.message)
    
    # Refresh to show new message
    st.rerun()

# Render chat
render_chat_window(video_id, conversation_history, handle_send_message)
```

### Displaying Rich Responses

```python
from ui.chat import render_assistant_response
from models.responses import AssistantMessageResponse

# Create response with frames and suggestions
response = AssistantMessageResponse(
    message="I found a dog at 0:45! 🐕",
    frames=["data/frames/vid_123/frame_045.jpg"],
    timestamps=[45.0],
    suggestions=[
        "What breed is the dog?",
        "Are there other animals?",
        "What happens next?"
    ]
)

# Render the response
render_assistant_response(response)
```

### Adding Emoji Reactions

```python
from ui.chat import add_emoji_reactions

# Add reactions to a specific message
message_id = "msg_123"
add_emoji_reactions(message_id)

# Check reactions in session state
if "reactions" in st.session_state:
    reactions = st.session_state.reactions.get(message_id, [])
    st.write(f"Reactions: {' '.join(reactions)}")
```

## Customization

### Custom Message Styling

You can customize message appearance by modifying the CSS in `ui/chat.py`:

```python
# In render_chat_window function
st.markdown("""
    <style>
    .user-message .message-content {
        background: linear-gradient(135deg, #YOUR_COLOR 0%, #YOUR_COLOR_2 100%);
        color: white;
    }
    
    .assistant-message .message-content {
        background: #YOUR_BG_COLOR;
        border: 2px solid #YOUR_BORDER_COLOR;
    }
    </style>
""", unsafe_allow_html=True)
```

### Custom Timestamp Format

Override the `_format_timestamp` function:

```python
def custom_format_timestamp(timestamp: datetime) -> str:
    """Custom timestamp formatting."""
    return timestamp.strftime("%I:%M %p")  # e.g., "02:30 PM"
```

### Custom Empty State

Modify `_render_empty_state()` to show custom content:

```python
def _render_empty_state() -> None:
    st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h3>Your Custom Message Here</h3>
            <p>Custom description...</p>
        </div>
    """, unsafe_allow_html=True)
```

## Integration Examples

### Example 1: Simple Chat

```python
import streamlit as st
from ui.chat import render_chat_window
from models.memory import MemoryRecord
from datetime import datetime

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Convert to MemoryRecord format
conversation_history = [
    MemoryRecord(
        message_id=f"msg_{i}",
        video_id="vid_test",
        role=msg["role"],
        content=msg["content"],
        timestamp=datetime.now()
    )
    for i, msg in enumerate(st.session_state.messages)
]

# Message handler
def handle_message(message: str):
    st.session_state.messages.append({
        "role": "user",
        "content": message
    })
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Echo: {message}"
    })
    st.rerun()

# Render
render_chat_window("vid_test", conversation_history, handle_message)
```

### Example 2: With Video Context

```python
from ui.chat import render_chat_window
from services.context import ContextBuilder

# Get video context
context_builder = ContextBuilder()
video_context = context_builder.build_video_context(video_id)

# Enhanced message handler
def handle_message_with_context(message: str):
    # Check if message references timestamp
    if "at" in message.lower() or ":" in message:
        # Extract timestamp and get context
        timestamp = extract_timestamp(message)
        context = context_builder.get_context_at_timestamp(
            video_id, 
            timestamp
        )
        
        # Generate response with context
        response = f"At {timestamp}s: {context.captions[0].text}"
    else:
        response = "General response"
    
    # Store and refresh
    memory.add_memory_pair(video_id, message, response)
    st.rerun()

render_chat_window(video_id, conversation_history, handle_message_with_context)
```

### Example 3: With Suggestions

```python
from ui.chat import render_chat_window

# Check for selected suggestion
if "selected_suggestion" in st.session_state:
    suggestion = st.session_state.selected_suggestion
    
    # Process suggestion as new message
    handle_send_message(suggestion)
    
    # Clear from session state
    del st.session_state.selected_suggestion

# Render chat
render_chat_window(video_id, conversation_history, handle_send_message)
```

## Best Practices

### 1. Message Handling

```python
# ✓ Good: Clear separation of concerns
def handle_send_message(message: str):
    # Validate input
    if not message.strip():
        return
    
    # Process with agent
    response = agent.chat(message, video_id)
    
    # Store in memory
    memory.add_memory_pair(video_id, message, response.message)
    
    # Update UI
    st.rerun()

# ✗ Bad: Mixing concerns
def handle_send_message(message: str):
    # Don't mix UI rendering with message handling
    st.write("Processing...")
    response = agent.chat(message, video_id)
    st.write(response)
```

### 2. Error Handling

```python
def handle_send_message(message: str):
    try:
        response = agent.chat(message, video_id)
        memory.add_memory_pair(video_id, message, response.message)
    except Exception as e:
        # Show friendly error
        st.error(f"Oops! Something went wrong: {e}")
        logger.error(f"Chat error: {e}")
        return
    
    st.rerun()
```

### 3. Loading States

```python
def handle_send_message(message: str):
    # Show loading indicator
    with st.spinner("BRI is thinking... 💭"):
        response = agent.chat(message, video_id)
    
    # Store and refresh
    memory.add_memory_pair(video_id, message, response.message)
    st.rerun()
```

### 4. Session State Management

```python
# Initialize session state properly
if "current_video_id" not in st.session_state:
    st.session_state.current_video_id = None

if "chat_initialized" not in st.session_state:
    st.session_state.chat_initialized = False

# Use unique keys per video
video_id = st.session_state.current_video_id
render_chat_window(
    video_id,
    conversation_history,
    handle_send_message
)
```

## Troubleshooting

### Issue: Messages not displaying

**Solution**: Ensure MemoryRecord objects have all required fields:
```python
message = MemoryRecord(
    message_id="msg_123",  # Required
    video_id="vid_456",    # Required
    role="user",           # Required: "user" or "assistant"
    content="Hello",       # Required
    timestamp=datetime.now()  # Required
)
```

### Issue: Input not clearing after send

**Solution**: Use `st.rerun()` after handling message:
```python
def handle_send_message(message: str):
    # Process message
    memory.add_memory_pair(video_id, message, response)
    
    # This clears the input
    st.rerun()
```

### Issue: Auto-scroll not working

**Solution**: Ensure JavaScript is enabled and container has proper class:
```python
# The component handles this automatically
# If issues persist, check browser console for errors
```

### Issue: Emoji not rendering

**Solution**: Ensure proper encoding and HTML rendering:
```python
# Use unsafe_allow_html=True for emoji
st.markdown("Hello 👋", unsafe_allow_html=True)
```

## Performance Tips

### 1. Limit Conversation History

```python
# Retrieve only recent messages
conversation_history = memory.get_conversation_history(
    video_id,
    limit=20  # Last 20 messages only
)
```

### 2. Lazy Load Frames

```python
# Only load frames when needed
if response.frames:
    for frame_path in response.frames:
        if os.path.exists(frame_path):
            st.image(frame_path)
```

### 3. Cache Responses

```python
@st.cache_data(ttl=3600)
def get_cached_response(message: str, video_id: str):
    return agent.chat(message, video_id)
```

## API Reference

### Main Functions

#### `render_chat_window(video_id, conversation_history, on_send_message)`
Renders the complete chat interface.

**Parameters:**
- `video_id` (str): Current video identifier
- `conversation_history` (List[MemoryRecord]): Previous messages
- `on_send_message` (callable): Callback for new messages

**Returns:** None

#### `render_assistant_response(response)`
Renders an assistant response with rich content.

**Parameters:**
- `response` (AssistantMessageResponse): Response object

**Returns:** None

#### `add_emoji_reactions(message_id)`
Adds emoji reaction buttons to a message.

**Parameters:**
- `message_id` (str): Message identifier

**Returns:** None

### Helper Functions

#### `_format_timestamp(timestamp)`
Formats datetime to relative time string.

**Parameters:**
- `timestamp` (datetime): Timestamp to format

**Returns:** str (e.g., "just now", "5m ago")

#### `_format_video_timestamp(seconds)`
Formats video timestamp in MM:SS or HH:MM:SS.

**Parameters:**
- `seconds` (float): Timestamp in seconds

**Returns:** str (e.g., "01:30", "01:01:01")

## Examples Repository

Find more examples in:
- `scripts/test_chat_window.py` - Test scenarios
- `app.py` - Main application integration
- `docs/task_20_chat_window.md` - Implementation details
