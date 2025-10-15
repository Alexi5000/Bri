# Groq Agent Implementation Summary

## Overview

The Groq Agent is the core conversational component of BRI, providing natural language understanding and response generation for video analysis queries. It integrates with the Groq API for LLM capabilities and coordinates with video processing tools via the MCP server.

## Implementation Details

### File Location
- **Path**: `services/agent.py`
- **Test Script**: `scripts/test_groq_agent.py`

### Key Components

#### 1. GroqAgent Class
Main agent class that handles all conversational interactions.

**Initialization**:
```python
agent = GroqAgent(
    groq_api_key=None,  # Uses Config.GROQ_API_KEY if not provided
    memory=None,        # Creates new Memory instance if not provided
    context_builder=None  # Creates new ContextBuilder if not provided
)
```

**Key Attributes**:
- `groq_client`: Groq API client for LLM interactions
- `memory`: Memory manager for conversation history
- `context_builder`: Context builder for video data aggregation
- `router`: Tool router for query analysis
- `mcp_base_url`: MCP server URL for tool execution

#### 2. Main Entry Point: `chat()`

```python
async def chat(
    message: str,
    video_id: str,
    image_base64: Optional[str] = None
) -> AssistantMessageResponse
```

**Process Flow**:
1. Determine if tools are needed (`_should_use_tool`)
2. If tools needed: Execute tool-based processing (`_run_with_tool`)
3. If no tools: Generate general conversational response (`_respond_general`)
4. Generate follow-up suggestions
5. Store interaction in memory
6. Return response with message, frames, timestamps, and suggestions

#### 3. Tool Detection: `_should_use_tool()`

Analyzes user queries to determine if video processing tools are needed.

**Logic**:
- Checks for purely conversational patterns (greetings, thanks, etc.)
- Uses ToolRouter to analyze query for video analysis needs
- Returns `'video_analysis'` if tools needed, `None` otherwise

**Examples**:
- "Hello!" → None (general conversation)
- "What's happening in this video?" → 'video_analysis'
- "Show me all the dogs" → 'video_analysis'

#### 4. Tool-Based Processing: `_run_with_tool()`

Executes video analysis queries using MCP server tools.

**Process**:
1. Analyze query with ToolRouter to get execution plan
2. Gather context from tools via MCP server (`_gather_tool_context`)
3. Retrieve conversation history for context
4. Build prompt with all context data
5. Generate response using Groq API
6. Extract frames and timestamps from context
7. Return response with media

#### 5. Tool Context Gathering: `_gather_tool_context()`

Communicates with MCP server to execute video processing tools.

**Supported Tools**:
- `captions`: Image captioning (BLIP)
- `transcripts`: Audio transcription (Whisper)
- `objects`: Object detection (YOLO)

**MCP Integration**:
```python
# Execute tool via HTTP POST
POST {mcp_base_url}/tools/{tool_name}/execute
Body: {
    "tool_name": "caption_frames",
    "video_id": "video_123",
    "parameters": {...}
}
```

#### 6. Response Generation: `_generate_response()`

Uses Groq API to generate natural language responses.

**Configuration**:
- Model: `Config.GROQ_MODEL` (default: llama-3.1-70b-versatile)
- Temperature: `Config.GROQ_TEMPERATURE` (default: 0.7)
- Max Tokens: `Config.GROQ_MAX_TOKENS` (default: 1024)

**System Prompt**:
Defines BRI's personality as warm, supportive, and knowledgeable with:
- Friendly and approachable tone
- Clear and concise communication
- Playful when appropriate
- Empathetic and understanding

#### 7. Memory Management: `_add_memory_pair()`

Stores user-assistant interactions in conversation history.

**Storage**:
- Uses Memory service to persist conversations
- Stores both user message and assistant response
- Maintains separate contexts per video
- Gracefully handles storage failures without breaking requests

#### 8. Follow-up Suggestions: `_generate_suggestions()`

Generates contextual follow-up questions based on query type.

**Suggestion Types**:
- Visual queries → "Can you describe a specific moment?"
- Audio queries → "Can you summarize the main points?"
- Object queries → "Are there any other similar moments?"
- Generic → "What's the overall theme of this video?"

Returns up to 3 suggestions per response.

#### 9. Error Handling: `_handle_error()`

Converts technical errors into friendly, user-facing messages.

**Error Types**:
- API errors → "I'm having trouble thinking right now. Give me a moment and try again! 🤔"
- Timeout errors → "That's taking longer than expected. Mind trying again? ⏱️"
- Connection errors → "I'm having trouble connecting to my tools. Let's try that again! 🔌"
- Generic errors → "Oops, something unexpected happened! Could you try rephrasing your question? 😅"

## Configuration

### Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=1024
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
```

### Dependencies
- `groq`: Groq API client
- `httpx`: Async HTTP client for MCP server communication
- `services.memory`: Conversation history management
- `services.router`: Query analysis and tool routing
- `services.context`: Video context aggregation

## Testing

### Test Coverage
All tests passing (7/7):
1. ✓ Agent Initialization
2. ✓ Tool Detection
3. ✓ General Response
4. ✓ Memory Storage
5. ✓ Suggestion Generation
6. ✓ Error Handling
7. ✓ Conversation Context

### Running Tests
```bash
python scripts/test_groq_agent.py
```

### Test Requirements
- Groq API key must be set in environment
- Database must be initialized
- Test videos are created automatically in database

## Usage Examples

### Basic Conversation
```python
from services.agent import GroqAgent

agent = GroqAgent()

# General greeting
response = await agent.chat(
    message="Hello! What can you do?",
    video_id="video_123"
)
print(response.message)
print(response.suggestions)
```

### Video Analysis Query
```python
# Query about video content
response = await agent.chat(
    message="What's happening at 1:30?",
    video_id="video_123"
)
print(response.message)
print(f"Frames: {response.frames}")
print(f"Timestamps: {response.timestamps}")
```

### Follow-up Question
```python
# First question
response1 = await agent.chat(
    message="What's in this video?",
    video_id="video_123"
)

# Follow-up (uses conversation context)
response2 = await agent.chat(
    message="Can you tell me more about that?",
    video_id="video_123"
)
```

## Integration Points

### With Memory Service
- Stores conversation history per video
- Retrieves recent context for follow-up questions
- Supports memory wipe functionality

### With Tool Router
- Analyzes queries to determine required tools
- Optimizes tool execution order
- Extracts parameters (timestamps, object names)

### With MCP Server
- Executes video processing tools via HTTP API
- Handles tool results and errors
- Supports caching for performance

### With Context Builder
- Aggregates video processing results
- Searches captions and transcripts
- Retrieves temporal context

## Performance Considerations

### Response Time
- General conversation: < 1 second
- Tool-based queries: 2-5 seconds (depends on tool execution)
- Cached results: < 1 second

### Memory Usage
- Conversation history limited to last 10 messages
- Tool results cached in Redis (24-hour TTL)
- Async operations prevent blocking

### Error Recovery
- Graceful degradation when tools fail
- Continues with available data
- Friendly error messages maintain user experience

## Future Enhancements

1. **Multi-turn Tool Execution**: Support complex queries requiring multiple tool rounds
2. **Streaming Responses**: Stream LLM responses for better UX
3. **Voice Integration**: Add voice input/output support
4. **Custom Tools**: Allow dynamic tool registration
5. **Advanced Context**: Use embeddings for semantic search
6. **Multi-video Analysis**: Compare and analyze multiple videos

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **4.1**: Natural language query processing using Groq API ✓
- **4.2**: Content analysis with captions ✓
- **4.3**: Timestamp-based queries with transcripts ✓
- **4.4**: Object/people search with detection results ✓
- **4.5**: Follow-up question handling with conversation context ✓
- **4.6**: Supportive, clear, and engaging tone ✓
- **4.7**: Friendly error handling and alternative suggestions ✓
- **5.1**: Conversation memory storage ✓
- **7.1**: Intelligent tool routing ✓

## Notes

- Agent requires valid Groq API key to function
- MCP server must be running for tool-based queries
- Database must have video records before storing memory
- All async operations use httpx for HTTP requests
- Error handling ensures graceful degradation
- System prompt defines BRI's warm personality
