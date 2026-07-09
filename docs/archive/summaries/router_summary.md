# Tool Router Implementation Summary

## Overview
The Tool Router is a query analysis component that determines which video processing tools are needed based on user queries and optimizes their execution order.

## Implementation Details

### Core Components

1. **ToolPlan Dataclass**
   - `tools_needed`: List of tools required (e.g., ['captions', 'objects'])
   - `execution_order`: Optimized order for tool execution
   - `parameters`: Query-specific parameters (timestamp, object_name, etc.)

2. **ToolRouter Class**
   - Analyzes natural language queries
   - Determines required tools (captions, transcripts, objects)
   - Extracts timestamps and object names
   - Optimizes execution order for efficiency

### Key Features

#### Query Analysis
- **Caption-based queries**: Detects visual description requests
  - Keywords: what, describe, scene, happening, show, see, visual, look, appear
  - Examples: "What's happening?", "Describe the scene"

- **Transcript-based queries**: Detects audio/speech-related requests
  - Keywords: say, speak, talk, mention, audio, sound, voice, word, conversation
  - Examples: "What did they say?", "Find when they mentioned Python"

- **Object-based queries**: Detects object detection needs
  - Keywords: find, locate, search, detect, spot, identify, count, how many
  - Examples: "Show me all the dogs", "How many people are there?"

#### Timestamp Extraction
Supports multiple timestamp formats:
- `HH:MM:SS` format (e.g., "1:30:45")
- `MM:SS` format (e.g., "2:15")
- Natural language (e.g., "at 30 seconds", "at 5 minutes")
- Relative references (e.g., "beginning", "start")

#### Object Name Extraction
Extracts object names from queries for targeted detection:
- "Show me all the dogs" → extracts "dogs"
- "Find the car" → extracts "car"
- "How many people are there?" → extracts "people"

#### Execution Order Optimization
- **Temporal queries**: Prioritizes tools based on timestamp context
- **Default order**: transcripts (fastest) → captions → objects (slowest)
- Allows for early results while heavier processing continues

## Usage Example

```python
from services.router import ToolRouter

router = ToolRouter()

# Analyze a query
query = "What did they say about the dog at 2:30?"
plan = router.analyze_query(query)

print(f"Tools needed: {plan.tools_needed}")
# Output: ['transcripts', 'objects']

print(f"Execution order: {plan.execution_order}")
# Output: ['transcripts', 'objects']

print(f"Parameters: {plan.parameters}")
# Output: {'object_name': 'dog', 'timestamp': 150.0, 'temporal_query': True}
```

## Testing

Comprehensive test suite in `scripts/test_tool_router.py` covers:
- Caption query detection
- Transcript query detection
- Object detection query analysis
- Timestamp extraction (multiple formats)
- Multi-tool query handling
- Execution order optimization
- Object name extraction

All tests pass successfully.

## Integration Points

The Tool Router integrates with:
- **Groq Agent**: Provides tool selection for query processing
- **MCP Server**: Execution order guides tool invocation
- **Context Builder**: Parameters inform context retrieval

## Requirements Satisfied

- ✅ 7.1: Analyze query to determine required tools
- ✅ 7.2: Coordinate tool execution in appropriate sequence
- ✅ 7.3: Skip unnecessary processing to optimize response time
- ✅ 7.4: Synthesize information from multiple sources
- ✅ 7.5: Attempt alternative data sources when tools unavailable

## Future Enhancements

Potential improvements:
- Machine learning-based query classification
- Support for more complex temporal queries
- Enhanced object name disambiguation
- Query intent confidence scoring
- Support for comparative queries ("show me more like this")
