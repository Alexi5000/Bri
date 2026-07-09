# Conversation History Panel - Usage Guide

## Overview

The conversation history panel allows you to view, navigate, and manage all your past conversations with BRI for each video. It appears in the sidebar when you're chatting with BRI about a video.

## Accessing the History Panel

1. **Select a Video**: Click on any video from your library or the sidebar video list
2. **Enter Chat View**: The chat interface will open with the video player
3. **View History**: The conversation history panel appears in the sidebar below the video list

## Features

### 1. Viewing Conversation History

The history panel displays all your past conversations with BRI about the current video:

- **Conversation Count**: Shows total number of conversations at the top
- **Session Preview**: Each conversation shows a preview of your first question
- **Timestamps**: Displays when each conversation took place (e.g., "5 minutes ago", "2 days ago")

### 2. Expanding Conversations

Click on any conversation to expand it and see the full details:

- **Full Messages**: View complete user questions and BRI's responses
- **Message Styling**: User messages in teal, BRI's responses in lavender
- **Chronological Order**: Messages displayed in the order they occurred

### 3. Loading Past Conversations

Want to continue from where you left off?

1. **Expand** the conversation you want to revisit
2. **Click** the "📖 Load this conversation" button
3. **Continue**: The conversation context is loaded, and you can continue chatting

### 4. Clearing History (Memory Wipe)

Need a fresh start? You can clear all conversation history:

1. **Scroll** to the bottom of the history panel
2. **Click** "🗑️ Clear Conversation History"
3. **Confirm**: A confirmation dialog appears
4. **Choose**:
   - "✅ Yes, clear it" - Permanently deletes all conversations
   - "❌ Cancel" - Keeps your history intact

⚠️ **Warning**: Clearing history cannot be undone!

## Empty State

If you haven't had any conversations yet, you'll see:

```
💭
No conversations yet.
Start chatting to build history!
```

## Tips & Best Practices

### 1. Organize Your Conversations
- Each video has its own separate conversation history
- Conversations are automatically grouped by session
- Use the history to track what you've already asked

### 2. Continue Previous Discussions
- Load past conversations to maintain context
- BRI will remember what you discussed before
- Great for multi-part questions or follow-ups

### 3. Privacy Management
- Use memory wipe when you want to start fresh
- Clear history before sharing your screen
- Each video's history is independent

### 4. Navigation
- Recent conversations appear at the top
- Timestamps help you find specific discussions
- Expand multiple conversations to compare responses

## Example Workflow

### Scenario: Analyzing a Tutorial Video

1. **First Session** (Today, 2:00 PM)
   - You: "What topics are covered in this video?"
   - BRI: "This tutorial covers Python basics, functions, and loops."

2. **Second Session** (Today, 2:15 PM)
   - You: "Can you show me where they explain functions?"
   - BRI: "Functions are explained at 5:30 in the video."

3. **Later** (Today, 4:00 PM)
   - You return and want to continue
   - Load the second session from history
   - Continue: "What about loops?"
   - BRI remembers the context and responds accordingly

## Troubleshooting

### History Not Showing
- **Check**: Make sure you're in chat view with a video selected
- **Verify**: The video must have at least one conversation
- **Refresh**: Try reloading the page

### Can't Load Conversation
- **Check**: Make sure the conversation is fully expanded
- **Try**: Click the load button again
- **Refresh**: Reload the page if issues persist

### Memory Wipe Not Working
- **Confirm**: Make sure you clicked "Yes, clear it" in the confirmation
- **Wait**: Give it a moment to process
- **Verify**: Check if the history panel shows empty state

## Technical Details

### Data Storage
- Conversations stored in SQLite database
- Each message has a unique ID and timestamp
- Foreign key relationship with video records

### Session Grouping
- Messages grouped into user-assistant pairs
- Each session represents one complete interaction
- Sessions displayed in chronological order

### Performance
- History limited to 50 most recent messages
- Long messages truncated for display
- Efficient database queries with indexing

## Keyboard Shortcuts

Currently, the history panel is mouse/touch-driven. Future versions may include:
- Arrow keys to navigate conversations
- Enter to expand/collapse
- Delete key for memory wipe

## Accessibility

The history panel is designed to be accessible:
- Clear visual hierarchy
- Descriptive button labels
- Color contrast meets WCAG standards
- Screen reader friendly

## Privacy & Security

### What's Stored
- Your questions to BRI
- BRI's responses
- Timestamps of conversations
- Video associations

### What's NOT Stored
- Video content itself
- Personal information (unless you include it in questions)
- Browsing history outside BRI

### Data Control
- You can delete all history anytime
- History is stored locally on your machine
- No data sent to external servers (except Groq API for responses)

## Future Features

Coming soon to the conversation history panel:
- 🔍 Search within conversations
- 📊 Conversation statistics
- 📤 Export conversations to file
- 🏷️ Tag and categorize conversations
- 📌 Pin important conversations

## Need Help?

If you encounter issues with the conversation history panel:
1. Check this guide for common solutions
2. Review the error messages (BRI provides friendly hints)
3. Try refreshing the page
4. Check the console for technical errors

## Feedback

We'd love to hear your thoughts on the conversation history panel! Let us know:
- What features you find most useful
- What could be improved
- What new features you'd like to see

---

**Remember**: The conversation history panel is here to help you keep track of your discussions with BRI and make it easy to continue where you left off. Use it to build a comprehensive understanding of your videos over time! 💜
