# Task 23: Agent-UI Integration - Usage Guide

## Getting Started

### Prerequisites

1. **Environment Setup**
   - Ensure `.env` file has `GROQ_API_KEY` set
   - Database initialized with `python scripts/init_db.py`
   - At least one video uploaded to the system

2. **Start the Application**
   ```bash
   streamlit run app.py
   ```

## Using the Chat Interface

### Opening a Chat

1. **From Sidebar:**
   - Click on any video in the "Your Videos" section
   - Chat interface opens automatically

2. **From Video Library:**
   - Click on a video card
   - Select "Chat" option

### Asking Questions

#### Basic Questions

**Example 1: General Content**
```
You: What's happening in this video?
BRI: [Provides overview with relevant frames and timestamps]
```

**Example 2: Specific Moments**
```
You: What did they say at 1:30?
BRI: [Shows transcript and context around 1:30]
```

**Example 3: Object Search**
```
You: Show me all the cats in this video
BRI: [Displays frames with detected cats and timestamps]
```

#### Advanced Questions

**Example 4: Follow-up Questions**
```
You: What's the main topic?
BRI: The video discusses machine learning...
You: Can you tell me more about that?
BRI: [Uses conversation context to provide detailed answer]
```

**Example 5: Temporal Queries**
```
You: What happens at the beginning?
BRI: [Shows frames and description from start of video]
```

### Interacting with Responses

#### Viewing Frames

When BRI includes frames in the response:

1. **Frame Display**
   - Frames appear in a grid (max 3 per row)
   - Each frame shows a relevant moment
   - Frames are displayed chronologically

2. **Frame Quality**
   - Thumbnails are optimized for quick loading
   - Click to view in video player context

#### Navigating with Timestamps

1. **Clickable Timestamps**
   - Look for buttons like "⏱️ 02:15"
   - Click to jump to that moment in the video
   - Video player updates automatically

2. **Timestamp Format**
   - Short videos: MM:SS (e.g., "02:15")
   - Long videos: HH:MM:SS (e.g., "01:02:15")

#### Using Suggestions

After each response, BRI provides follow-up suggestions:

1. **Suggestion Box**
   - Appears below the response
   - Contains 1-3 relevant questions
   - Styled with 💡 icon

2. **Clicking Suggestions**
   - Click any suggestion button
   - Question is automatically processed
   - New response appears

**Example:**
```
💡 You might also want to ask:
[What happens next?]
[Tell me more about the speaker]
[Show me similar moments]
```

## Chat Features

### Message History

- **Persistent Storage**: All conversations saved to database
- **Scroll History**: Scroll up to view previous messages
- **Context Awareness**: BRI remembers previous questions

### Message Formatting

**User Messages:**
- Teal gradient background
- Right-aligned style
- 👤 icon

**BRI Messages:**
- White background with lavender border
- Left-aligned style
- 💖 icon

### Timestamps

Each message shows when it was sent:
- "just now" - Less than 1 minute ago
- "5m ago" - Minutes ago
- "2h ago" - Hours ago
- "Jan 15, 2:30 PM" - Older messages

## Tips for Best Results

### Asking Effective Questions

1. **Be Specific**
   - ❌ "Tell me about it"
   - ✅ "What's the main topic discussed?"

2. **Use Temporal References**
   - ✅ "What happens at 2:30?"
   - ✅ "Show me the beginning"
   - ✅ "What's said at the end?"

3. **Ask About Visual Content**
   - ✅ "What objects are visible?"
   - ✅ "Describe the scene"
   - ✅ "Show me when the cat appears"

4. **Ask About Audio**
   - ✅ "What did they say about X?"
   - ✅ "Summarize the conversation"
   - ✅ "Find when they mention Y"

### Follow-up Questions

BRI maintains context, so you can ask follow-ups:

```
You: What's the main topic?
BRI: The video discusses climate change...

You: Tell me more about that
BRI: [Provides detailed information using context]

You: When do they mention solutions?
BRI: [Searches for relevant moments]
```

### Using Suggestions

Suggestions help you explore the video:

1. **Discovery**: Find content you didn't know about
2. **Deep Dive**: Get more details on topics
3. **Navigation**: Jump to related moments

## Troubleshooting

### Common Issues

#### 1. "Oops! Something went wrong"

**Cause**: API error or processing failure

**Solutions:**
- Check internet connection
- Verify GROQ_API_KEY in .env
- Try asking the question differently
- Check logs for details

#### 2. No Frames Displayed

**Cause**: Video not processed or frames not extracted

**Solutions:**
- Wait for video processing to complete
- Check processing status in video library
- Re-upload video if needed

#### 3. Slow Responses

**Cause**: Complex query or large video

**Solutions:**
- Be patient during first query (no cache)
- Subsequent queries are faster (cached)
- Ask more specific questions
- Check MCP server is running

#### 4. Timestamps Don't Work

**Cause**: Video player not loaded or state issue

**Solutions:**
- Refresh the page
- Reselect the video
- Check video file exists

### Error Messages

BRI provides friendly error messages:

**Example 1: Tool Failure**
```
"I had trouble extracting frames, but I can still help with the audio!"
```

**Example 2: No Results**
```
"I couldn't find that in the video, but here's what I did find..."
```

**Example 3: API Issue**
```
"I'm having trouble thinking right now. Give me a moment and try again!"
```

## Advanced Usage

### Conversation Management

#### Viewing History

1. **Sidebar Panel**: Shows past conversations
2. **Click to Load**: Load previous conversation context
3. **Continue**: Pick up where you left off

#### Memory Wipe

1. **Privacy Feature**: Clear conversation history
2. **Fresh Start**: Begin new conversation
3. **Per Video**: Each video has separate memory

### Keyboard Shortcuts

- **Enter**: Send message
- **Shift+Enter**: New line in message (if supported)

### Best Practices

1. **One Question at a Time**
   - Focus on single topic per message
   - Use follow-ups for related questions

2. **Use Suggestions**
   - Explore suggested questions
   - Discover content you might miss

3. **Reference Timestamps**
   - Click timestamps to verify information
   - Watch relevant moments in context

4. **Provide Feedback**
   - If response is unclear, ask for clarification
   - BRI learns from conversation context

## Example Workflows

### Workflow 1: Video Summary

```
1. You: "Summarize this video"
   BRI: [Provides overview with key moments]

2. Click timestamp to view interesting moment

3. You: "Tell me more about this part"
   BRI: [Detailed explanation of that section]

4. Click suggestion: "What happens next?"
   BRI: [Continues narrative]
```

### Workflow 2: Finding Specific Content

```
1. You: "Find when they mention machine learning"
   BRI: [Shows relevant moments with timestamps]

2. Click timestamp to watch

3. You: "What else do they say about it?"
   BRI: [Finds related content]

4. Click suggestion: "Show me examples"
   BRI: [Displays visual examples]
```

### Workflow 3: Object Search

```
1. You: "Show me all the dogs in this video"
   BRI: [Displays frames with detected dogs]

2. Click timestamp to see dog in video

3. You: "What breed is it?"
   BRI: [Analyzes visual details]

4. Click suggestion: "Find other animals"
   BRI: [Shows other detected animals]
```

## Getting Help

### Resources

1. **Documentation**: Check `docs/` folder
2. **Test Scripts**: Run `scripts/test_task_23_integration.py`
3. **Logs**: Check console output for errors

### Support

If you encounter issues:

1. Check error messages in UI
2. Review console logs
3. Verify configuration in `.env`
4. Test with simple questions first
5. Report bugs with error details

## Conclusion

The agent-UI integration provides a powerful, intuitive way to interact with your videos. By asking natural language questions, clicking timestamps, and following suggestions, you can quickly find and understand video content.

**Key Takeaways:**
- Ask specific, clear questions
- Use timestamps to navigate
- Follow suggestions to explore
- Maintain conversation context
- Provide feedback for better results

Happy chatting with BRI! 💜
