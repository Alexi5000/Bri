# Video Player Usage Guide

## For Users

### Accessing the Video Player

1. **Upload a Video**
   - Go to the welcome screen
   - Upload your video file
   - Wait for processing to complete

2. **Open Chat Interface**
   - Click on a video from the library or sidebar
   - The chat interface opens with the video player on the left

### Using the Video Player

#### Basic Playback
- The video loads automatically when you select it
- Click the play button in the video to start playback
- Use the browser's native controls for play/pause

#### Navigation Controls
The player provides several navigation buttons:

- **⏮️ Start** - Jump to the beginning of the video
- **⏪ -10s** - Go back 10 seconds
- **⏸️ Pause** - Pause playback
- **⏩ +10s** - Go forward 10 seconds
- **🔄 Reset** - Reset to the beginning

#### Timestamp Navigation

**From Chat Responses:**
When BRI shows you relevant frames, each frame has a clickable timestamp button:
1. Look for the "⏱️ MM:SS" button under each frame
2. Click the timestamp to jump to that moment
3. The video will reload at that position

**From Timestamp Chips:**
Below the video player, you'll see chips for all relevant moments:
1. Look for the "📍 Jump to relevant moments" section
2. Click any timestamp chip to navigate
3. The active timestamp is highlighted

### Example Workflow

1. **Ask a Question**
   ```
   You: "What happens at the beginning?"
   ```

2. **BRI Responds with Frames**
   - BRI shows relevant frames with timestamps
   - Each frame has a clickable timestamp

3. **Navigate to Moment**
   - Click the timestamp under a frame
   - Video jumps to that exact moment
   - Watch the scene in context

4. **Continue Conversation**
   ```
   You: "What happens next?"
   ```
   - BRI remembers the context
   - Shows subsequent moments
   - All timestamps remain clickable

## For Developers

### Basic Integration

#### Render Video Player
```python
from ui.player import render_video_player

render_video_player(
    video_path="data/videos/my_video.mp4",
    video_id="video_123",
    current_timestamp=None,  # Optional start time
    timestamps=[30.0, 65.5, 120.0]  # Optional relevant moments
)
```

#### With Conversation Context
```python
from ui.player import render_video_player_with_context

# Automatically uses most recent timestamp from conversation
render_video_player_with_context(
    video_path="data/videos/my_video.mp4",
    video_id="video_123",
    conversation_timestamps=[30.0, 65.5, 120.0]
)
```

### Advanced Usage

#### Programmatic Navigation
```python
from ui.player import navigate_to_timestamp

# Jump to a specific timestamp
navigate_to_timestamp("video_123", 135.0)  # Jump to 2:15

# This updates session state and triggers navigation
```

#### Extract Timestamps from Conversation
```python
from ui.player import extract_timestamps_from_conversation

# Extract all timestamps mentioned in conversation
timestamps = extract_timestamps_from_conversation(conversation_history)

# Returns sorted list of unique timestamps in seconds
# Example: [30.0, 65.5, 120.0, 180.0]
```

#### Get Current Playback Time
```python
from ui.player import get_current_playback_time

# Get current playback position
current_time = get_current_playback_time("video_123")
print(f"Currently at: {current_time}s")
```

### Session State Management

The player uses session state to maintain playback position:

```python
# Session state structure
st.session_state[f"player_{video_id}"] = {
    "current_time": 0.0,          # Current playback position
    "is_playing": False,           # Playback state
    "selected_timestamp": None     # User-selected timestamp
}
```

### Timestamp Format Utilities

#### Format Timestamp for Display
```python
from ui.player import _format_timestamp

# Format seconds to MM:SS or HH:MM:SS
formatted = _format_timestamp(125.5)  # Returns "02:05"
formatted = _format_timestamp(3665)   # Returns "01:01:05"
```

### Integration with Chat

#### Make Timestamps Clickable
```python
import streamlit as st

# Display frame with clickable timestamp
st.image(frame_path)
if st.button(f"⏱️ {timestamp_str}", key=f"ts_{idx}"):
    st.session_state["clicked_timestamp"] = timestamp
    st.rerun()
```

#### Check for Clicked Timestamps
```python
# In your player rendering code
clicked_timestamp = st.session_state.get("clicked_timestamp")
if clicked_timestamp is not None:
    navigate_to_timestamp(video_id, clicked_timestamp)
    st.session_state["clicked_timestamp"] = None  # Clear
```

### Custom Styling

The player uses BRI's color scheme. To customize:

```python
# In ui/player.py, modify the CSS in render_video_player()
st.markdown("""
    <style>
    .video-player-container {
        background: white;
        border-radius: 20px;
        /* Add your custom styles */
    }
    
    .timestamp-chip {
        background: linear-gradient(135deg, #E6E6FA 0%, #FFB6C1 100%);
        /* Customize chip appearance */
    }
    </style>
""", unsafe_allow_html=True)
```

### Error Handling

#### Video File Not Found
```python
from pathlib import Path

if not Path(video_path).exists():
    st.error(f"Video file not found: {video_path}")
    logger.error(f"Video file not found: {video_path}")
    return
```

#### Invalid Timestamp
```python
# Ensure timestamp is within video duration
if timestamp < 0:
    timestamp = 0.0
elif timestamp > video_duration:
    timestamp = video_duration
```

### Testing

#### Unit Tests
```python
# Test timestamp formatting
from ui.player import _format_timestamp

assert _format_timestamp(65) == "01:05"
assert _format_timestamp(3665) == "01:01:05"
```

#### Integration Tests
```python
# Test full player workflow
def test_player_navigation():
    video_id = "test_video"
    timestamp = 125.5
    
    # Navigate to timestamp
    navigate_to_timestamp(video_id, timestamp)
    
    # Verify navigation
    current = get_current_playback_time(video_id)
    assert current == timestamp
```

## Common Use Cases

### Use Case 1: Show Relevant Moments
```python
# User asks about specific content
user_query = "Show me all the cats in this video"

# Agent finds relevant frames with timestamps
relevant_frames = [
    {"path": "frame_001.jpg", "timestamp": 30.0},
    {"path": "frame_045.jpg", "timestamp": 90.0},
    {"path": "frame_089.jpg", "timestamp": 178.0}
]

# Extract timestamps
timestamps = [frame["timestamp"] for frame in relevant_frames]

# Render player with these timestamps
render_video_player(
    video_path=video_path,
    video_id=video_id,
    timestamps=timestamps
)
```

### Use Case 2: Continue from Last Position
```python
# Get last mentioned timestamp from conversation
last_timestamp = None
for message in reversed(conversation_history):
    if hasattr(message, 'timestamps') and message.timestamps:
        last_timestamp = message.timestamps[-1]
        break

# Start player at last position
render_video_player(
    video_path=video_path,
    video_id=video_id,
    current_timestamp=last_timestamp
)
```

### Use Case 3: Timestamp-Based Search
```python
# User asks about specific time
user_query = "What happens at 2:30?"

# Parse timestamp from query
import re
match = re.search(r'(\d+):(\d+)', user_query)
if match:
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    timestamp = minutes * 60 + seconds
    
    # Navigate to that timestamp
    navigate_to_timestamp(video_id, timestamp)
```

## Tips & Best Practices

### For Users
1. **Use Timestamps Liberally** - Click timestamps to explore the video
2. **Watch Context** - The player shows moments before/after for context
3. **Combine with Chat** - Ask follow-up questions about what you see
4. **Use Controls** - The ±10s buttons are great for fine-tuning position

### For Developers
1. **Always Validate Paths** - Check video file exists before rendering
2. **Handle Edge Cases** - Timestamps at 0, negative, or beyond duration
3. **Clear State** - Clear clicked timestamps after navigation
4. **Provide Feedback** - Show visual feedback for navigation actions
5. **Test Thoroughly** - Test with various video formats and durations

## Troubleshooting

### Video Won't Play
- Check video file exists at the specified path
- Verify video format is supported (MP4, AVI, MOV, MKV)
- Check browser codec support (MP4/H.264 recommended)

### Timestamps Not Working
- Verify timestamps are in seconds (float)
- Check session state is properly initialized
- Ensure video_id is consistent across components

### Navigation Not Smooth
- Streamlit's video component has limitations
- Consider using custom video player for better control
- Current implementation reloads video at new position

### Styling Issues
- Check CSS is properly injected with `unsafe_allow_html=True`
- Verify color values match BRI's design system
- Test in different browsers for compatibility

## API Reference

### Main Functions

#### `render_video_player(video_path, video_id, current_timestamp, timestamps)`
Render video player with full controls and timestamp navigation.

**Parameters:**
- `video_path` (str): Path to video file
- `video_id` (str): Unique video identifier
- `current_timestamp` (float, optional): Initial playback position
- `timestamps` (List[float], optional): Relevant timestamps to display

**Returns:** None

---

#### `render_video_player_with_context(video_path, video_id, conversation_timestamps)`
Render player synced with conversation context.

**Parameters:**
- `video_path` (str): Path to video file
- `video_id` (str): Unique video identifier
- `conversation_timestamps` (List[float]): Timestamps from conversation

**Returns:** None

---

#### `navigate_to_timestamp(video_id, timestamp)`
Navigate video player to specific timestamp.

**Parameters:**
- `video_id` (str): Video identifier
- `timestamp` (float): Target timestamp in seconds

**Returns:** None

---

#### `get_current_playback_time(video_id)`
Get current playback position.

**Parameters:**
- `video_id` (str): Video identifier

**Returns:** float - Current playback time in seconds

---

#### `extract_timestamps_from_conversation(conversation_history)`
Extract all timestamps from conversation.

**Parameters:**
- `conversation_history` (List): List of conversation messages

**Returns:** List[float] - Sorted list of unique timestamps

## Examples

See `scripts/test_video_player.py` for comprehensive examples and test cases.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test cases in `scripts/test_video_player.py`
3. Consult the implementation in `ui/player.py`
4. Check the main documentation in `docs/task_21_video_player.md`
