# Task 13: Follow-up Suggestion Generation - Demo

## Feature Overview

BRI now intelligently generates 1-3 relevant follow-up questions after each response, helping users explore video content more thoroughly and naturally.

## How It Works

### 1. Query Analysis
When a user asks a question, BRI analyzes the query type:
- Visual description queries
- Audio/transcript queries
- Object search queries
- Timestamp-specific queries
- Summary queries
- General conversation

### 2. Template Selection
Based on the query type, BRI selects appropriate suggestion templates that guide users to related aspects of the video.

### 3. Proactive Discovery
BRI also analyzes its own response for mentions of additional content and proactively offers to share it.

## Live Examples

### Example 1: Visual Exploration
```
User: "What's happening in the video?"

BRI: "The video shows a person walking through a park with trees 
      and benches visible."

Suggestions:
  1. Can you describe a specific moment in more detail?
  2. What are the people doing in the video?
  3. How does the scene change throughout the video?
```

### Example 2: Audio Content
```
User: "What did they say about the project?"

BRI: "They mentioned that the project is progressing well and 
      discussed the timeline."

Suggestions:
  1. Can you summarize the main points discussed?
  2. What other topics are covered?
  3. What's the context around this conversation?
```

### Example 3: Object Search
```
User: "Show me all the cats in this video"

BRI: "I found 3 instances of cats appearing in the video at 
      different timestamps."

Suggestions:
  1. Are there any other similar moments?
  2. What's happening in those scenes?
  3. What else appears alongside it?
```

### Example 4: Timestamp Navigation
```
User: "What happens at 2:30?"

BRI: "At 2:30, the speaker begins discussing the main topic."

Suggestions:
  1. What happens right before this moment?
  2. What happens right after this?
  3. Are there other important moments like this?
```

### Example 5: Proactive Discovery
```
User: "What's in this video?"

BRI: "The video contains a presentation followed by a Q&A session 
      with the audience."

Suggestions:
  1. What's this video about?
  2. Can you describe what you see?
  3. Want me to summarize the Q&A session? ← Proactive!
```

## Benefits for Users

✅ **Guided Exploration**: Users don't need to think of what to ask next

✅ **Content Discovery**: Proactive suggestions help find hidden gems

✅ **Natural Flow**: Suggestions feel like a natural conversation

✅ **Reduced Friction**: Lower cognitive load for users

✅ **Better Engagement**: Users explore more of the video content

## Technical Implementation

### Query Classification
```python
# Analyzes query to determine type
query_type = self._classify_query_type(message_lower)

# Types: visual_description, audio_transcript, object_search,
#        timestamp_specific, summary, general
```

### Template Generation
```python
# Each query type has specific templates
if query_type == 'visual_description':
    suggestions = self._suggest_visual_followups(...)
elif query_type == 'audio_transcript':
    suggestions = self._suggest_audio_followups(...)
# ... etc
```

### Proactive Detection
```python
# Detects mentions of additional content
proactive = self._detect_additional_content(response_lower)

# Patterns: "also", "other moments", "Q&A", "interview", etc.
```

### Deduplication & Limiting
```python
# Ensures 1-3 unique suggestions
unique_suggestions = list(dict.fromkeys(suggestions))
return unique_suggestions[:3]
```

## Requirements Met

✅ **9.1**: System suggests 1-3 relevant follow-up questions

✅ **9.2**: Suggestions relate to specific topics being discussed

✅ **9.3**: Proactively offers to share additional relevant content

✅ **9.4**: Suggestions are actionable (can be processed as new queries)

## Testing

Run the test suite to verify functionality:

```bash
python scripts/test_task_13_suggestions.py
```

Expected output:
```
Total Tests: 8
Passed: 8
Failed: 0

✅ ALL TESTS PASSED - Task 13 Implementation Complete!
```

## Next Steps

This feature is now ready for integration with the UI layer (Tasks 15-23), where suggestions will be displayed as clickable buttons that users can select to continue the conversation.
