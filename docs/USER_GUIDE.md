# BRI User Guide

Welcome to BRI (Brianna)! This guide will help you get the most out of your video analysis experience.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Uploading Videos](#uploading-videos)
3. [Asking Questions](#asking-questions)
4. [Understanding Responses](#understanding-responses)
5. [Using the Video Library](#using-the-video-library)
6. [Managing Conversations](#managing-conversations)
7. [Tips & Best Practices](#tips--best-practices)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### First Time Setup

1. **Launch BRI**: After installation, start the application by running both the MCP server and Streamlit UI (see [README.md](../README.md) for details)
2. **Open Your Browser**: Navigate to `http://localhost:8501`
3. **Welcome Screen**: You'll see BRI's friendly welcome screen with the tagline "Ask. Understand. Remember."

### The Interface

BRI's interface has three main areas:

- **Sidebar**: Video library and conversation history
- **Main Area**: Chat window and video player
- **Welcome Screen**: Initial landing page with upload prompt

## Uploading Videos

### Supported Formats

BRI accepts the following video formats:
- MP4 (recommended)
- AVI
- MOV
- MKV

### Upload Process

1. **Drag and Drop**: Simply drag your video file onto the upload area
2. **Or Click to Browse**: Click the upload area to select a file from your computer
3. **Wait for Confirmation**: You'll see "Got it! Let me take a look..." when upload starts
4. **Processing**: BRI will analyze your video (this may take a few minutes)
5. **Ready**: When you see "All set! What would you like to know?", you can start asking questions

### What Happens During Processing?

BRI performs several analyses on your video:

- **Frame Extraction**: Captures key frames at regular intervals
- **Image Captioning**: Describes what's happening in each frame
- **Audio Transcription**: Converts speech to text with timestamps
- **Object Detection**: Identifies objects, people, and scenes

This processing happens once per video and enables BRI to answer your questions quickly.

## Asking Questions

### Types of Questions You Can Ask

#### Content Questions
Ask about what's happening in the video:
- "What's happening in this video?"
- "Describe the main scene"
- "What are the key moments?"

#### Timestamp Questions
Ask about specific times:
- "What happens at 1:30?"
- "What did they say at 2:15?"
- "Show me the beginning"

#### Object/People Questions
Search for specific things:
- "Show me all the cats in this video"
- "Find scenes with a car"
- "When does the person in blue appear?"

#### Transcript Questions
Ask about what was said:
- "What did they say about the project?"
- "Find when they mentioned 'deadline'"
- "Summarize the conversation"

#### Follow-up Questions
BRI remembers your conversation:
- "Tell me more about that"
- "What happened next?"
- "Show me another example"

### Writing Effective Questions

**Do:**
- ✓ Be specific: "Show me when the dog appears" vs "Show me animals"
- ✓ Use natural language: Ask as you would ask a friend
- ✓ Reference timestamps: "What happens around 2 minutes in?"
- ✓ Ask follow-ups: BRI remembers your conversation

**Don't:**
- ✗ Use technical jargon: No need for "extract frames at timestamp X"
- ✗ Be too vague: "Show me stuff" won't get good results
- ✗ Ask about content not in the video: BRI can only analyze what's there

## Understanding Responses

### Response Components

BRI's responses may include:

#### 1. Text Response
A conversational answer to your question in BRI's warm, friendly tone.

#### 2. Frame Thumbnails
Relevant images from the video showing what you asked about. Click on any frame to jump to that moment in the video.

#### 3. Timestamps
Clickable timestamps that navigate the video player to specific moments:
- Format: `[1:23]` or `[2:45]`
- Click to jump to that time in the video

#### 4. Follow-up Suggestions
BRI proactively suggests 1-3 related questions you might want to ask:
- "Want me to summarize the Q&A session too?"
- "Would you like to see other scenes with the same person?"
- "Curious about what happens next?"

Click any suggestion to ask that question automatically.

### Response Tone

BRI uses a warm, supportive tone:
- **Friendly**: "I found something interesting!"
- **Encouraging**: "Great question! Let me show you..."
- **Helpful**: "I couldn't find that exactly, but here's what I did find..."
- **Playful**: Occasional emoji and casual language 😊

## Using the Video Library

### Viewing Your Videos

The sidebar shows all your uploaded videos with:
- **Thumbnail**: Preview image from the video
- **Filename**: Original name of the video file
- **Duration**: Length of the video
- **Upload Date**: When you uploaded it

### Selecting a Video

Click on any video in the library to:
- Open the chat interface for that video
- Load the conversation history
- Start or continue asking questions

### Deleting Videos

To remove a video:
1. Click the delete button (🗑️) next to the video
2. Confirm the deletion
3. The video and all associated conversations will be removed

**Note**: This action cannot be undone!

## Managing Conversations

### Conversation History

BRI maintains separate conversation histories for each video:
- **Per-Video Memory**: Each video has its own conversation thread
- **Context Awareness**: BRI remembers what you've asked about this video
- **Chronological Order**: Messages appear in the order they were sent

### Viewing Past Conversations

In the sidebar, you'll see:
- Recent messages for the selected video
- Timestamps for each message
- User questions and BRI's responses

### Memory Wipe

If you want to start fresh:
1. Click the "Memory Wipe" button in the conversation history panel
2. Confirm the action
3. BRI will forget all previous conversations about this video

**Use cases for memory wipe:**
- Starting a new analysis of the same video
- Privacy: removing conversation history
- Clearing context that's no longer relevant

## Tips & Best Practices

### Getting the Best Results

1. **Be Patient During Processing**: Initial video processing takes time but only happens once
2. **Start Broad, Then Narrow**: Ask general questions first, then follow up with specifics
3. **Use Timestamps**: If you know roughly when something happens, mention it
4. **Try Follow-up Suggestions**: BRI's suggestions often lead to interesting discoveries
5. **Experiment with Phrasing**: If you don't get the answer you want, try asking differently

### Performance Tips

1. **Shorter Videos Process Faster**: Consider splitting long videos into segments
2. **Enable Redis Caching**: Dramatically speeds up repeated queries
3. **Close Unused Videos**: Keep only the video you're working with open
4. **Clear Old Videos**: Delete videos you no longer need to free up space

### Privacy & Security

1. **Local Storage**: Videos are stored locally on your machine by default
2. **API Keys**: Keep your Groq API key secure in the `.env` file
3. **Memory Wipe**: Use this feature to clear sensitive conversations
4. **Delete Videos**: Remove videos when you're done with them

## Troubleshooting

### "I can't find what I'm looking for"

**Try:**
- Rephrasing your question with different words
- Being more specific about what you want
- Using timestamps if you know roughly when it happens
- Asking BRI to "show me everything" first, then narrowing down

### "BRI's response doesn't match the video"

**Possible causes:**
- The video quality may be too low for accurate analysis
- Audio may be unclear for transcription
- Objects may be too small or obscured for detection

**Try:**
- Asking about a different aspect (e.g., audio instead of visuals)
- Being more specific about what you're looking for
- Checking if the timestamp is correct

### "Processing is taking too long"

**Normal processing times:**
- Short videos (< 5 min): 1-3 minutes
- Medium videos (5-15 min): 3-8 minutes
- Long videos (> 15 min): 8+ minutes

**If it's taking longer:**
- Check the MCP server logs for errors
- Ensure your computer has enough resources
- Try a shorter video first to test

### "BRI says it can't answer my question"

**Common reasons:**
- The information isn't in the video
- The question is too vague or ambiguous
- Processing failed for that particular aspect

**Try:**
- Asking a more specific question
- Checking if the video actually contains what you're asking about
- Asking about a different aspect of the video

### Error Messages

#### "Oops! I can only work with MP4, AVI, MOV, or MKV files"
- Your video format isn't supported
- Convert your video to a supported format

#### "This video is a bit too big for me right now"
- Your video exceeds the size limit
- Try compressing the video or splitting it into parts

#### "I'm having trouble thinking right now"
- The Groq API is temporarily unavailable
- Wait a moment and try again

#### "My tools are taking a break"
- The MCP server is not responding
- Check that the MCP server is running
- Restart the MCP server if needed

## Getting Help

If you encounter issues not covered in this guide:

1. **Check the README**: See [README.md](../README.md) for setup and configuration help
2. **Review Requirements**: See [requirements.md](../.kiro/specs/bri-video-agent/requirements.md) for feature details
3. **Check Logs**: Look at the application logs for error messages
4. **Report Issues**: Open a GitHub issue with details about your problem

## Keyboard Shortcuts

- **Enter**: Send message in chat
- **Shift + Enter**: New line in message input
- **Esc**: Close modals/dialogs

## Accessibility Features

BRI is designed to be accessible:
- **Keyboard Navigation**: Full keyboard support throughout the interface
- **Screen Reader Friendly**: Semantic HTML and ARIA labels
- **High Contrast**: Readable text with sufficient contrast ratios
- **Responsive Design**: Works on different screen sizes

---

**Happy analyzing! 🎥✨**

If you have suggestions for improving BRI, we'd love to hear from you!
