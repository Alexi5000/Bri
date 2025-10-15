# Implementation Plan

- [x] 1. Set up project structure and dependencies

  - Create directory structure for models, services, tools, and UI components
  - Set up requirements.txt with all necessary dependencies (streamlit, groq, opencv-python, transformers, whisper, ultralytics, fastapi, redis, sqlite3)
  - Create configuration management for API keys and settings
  - Initialize Git repository with .gitignore for Python projects
  - _Requirements: All requirements depend on proper project setup_

- [x] 2. Implement core data models and database schema

  - Define Pydantic models for Video, VideoMetadata, Frame, Caption, Transcript, DetectionResult, MemoryRecord, AssistantMessageResponse
  - Create SQLite database initialization script with tables for videos, memory, and video_context
  - Implement database connection utilities with proper error handling
  - _Requirements: 3.5, 5.1, 5.2, 11.2_

- [x] 3. Build Memory Manager component

  - Implement Memory class with SQLite backend for storing conversation history
  - Create methods for inserting memory records (insert)
  - Create methods for retrieving conversation history (get_conversation_history)
  - Create method for memory wipe functionality (reset_memory)
  - Add indexing on video_id and timestamp for performance
  - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.6_

- [x] 4. Implement Frame Extractor tool

  - Create FrameExtractor class using OpenCV for video frame extraction
  - Implement extract_frames method with configurable interval and max_frames
  - Implement extract_frame_at_timestamp for specific timestamp extraction
  - Implement get_video_metadata to retrieve video properties (duration, fps, resolution)
  - Add adaptive interval calculation based on video length
  - Store extracted frames to file system with organized directory structure
  - _Requirements: 3.1, 3.5, 12.5_

- [x] 5. Implement Image Captioner tool

  - Create ImageCaptioner class using Hugging Face BLIP model
  - Load BLIP model and processor (Salesforce/blip-image-captioning-large)
  - Implement caption_frame method for single frame captioning
  - Implement caption_frames_batch for efficient batch processing
  - Add confidence scoring to caption results

  - _Requirements: 3.2, 3.5_

- [x] 6. Implement Audio Transcriber tool

  - Create AudioTranscriber class using OpenAI Whisper
  - Load Whisper model (base or small for balance of speed/accuracy)
  - Implement transcribe_video method for full video transcription with timestamps
  - Implement transcribe_segment for specific time range transcription
  - Store transcript data with proper timestamp alignment
  - _Requirements: 3.3, 3.5_

- [x] 7. Implement Object Detector tool

  - Create ObjectDetector class using YOLO (YOLOv8)
  - Load YOLOv8 model (yolov8n.pt for speed)
  - Implement detect_objects_in_frames for batch object detection
  - Implement search_for_object to find specific object occurrences
  - Store detection results with bounding boxes and confidence scores
  - _Requirements: 3.4, 3.5_

- [x] 8. Build MCP Server with FastAPI

  - Create FastAPI application with CORS middleware
  - Implement tool registry for dynamic tool discovery
  - Create GET /tools endpoint to list available tools with schemas
  - Create POST /tools/{tool_name}/execute endpoint for tool execution
  - Create POST /videos/{video_id}/process endpoint for batch video processing
  - Add Redis integration for caching tool results
  - Implement proper error handling and status responses
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 9. Implement Context Builder

  - Create ContextBuilder class to aggregate video processing results
  - Implement build_video_context to compile all available data for a video
  - Implement search_captions using text similarity for relevant caption retrieval
  - Implement search_transcripts for keyword-based transcript search
  - Implement get_frames_with_object to find frames containing specific objects
  - Implement get_context_at_timestamp to retrieve all context around a specific time
  - _Requirements: 4.4, 8.1, 8.2_

- [x] 10. Implement Tool Router

  - Create ToolRouter class for query analysis and tool selection
  - Implement analyze_query to determine which tools are needed based on query content
  - Implement requires_captions, requires_transcripts, requires_objects helper methods
  - Implement extract_timestamp to parse temporal references from queries
  - Create ToolPlan dataclass to represent execution plan
  - Add logic to optimize tool execution order
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 11. Build Groq Agent core

  - Create GroqAgent class with Groq API client initialization
  - Implement chat method as main entry point for processing user messages
  - Implement \_should_use_tool to determine if tools are needed
  - Implement \_run_with_tool for tool-based query processing
  - Implement \_respond_general for conversational responses without tools
  - Implement \_add_memory_pair to store interactions in memory
  - Configure Groq with appropriate model (llama-3.1-70b-versatile) and parameters
  - Create system prompt defining BRI's warm, supportive personality
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 7.1_

- [x] 12. Implement response generation with media

  - Extend agent to include relevant frames in responses
  - Add timestamp extraction and formatting in responses
  - Implement frame thumbnail generation for response display
  - Add logic to present multiple relevant moments in chronological order
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 13. Implement follow-up suggestion generation

  - Add logic to generate 1-3 relevant follow-up questions based on response
  - Implement suggestion templates for different query types
  - Add proactive content discovery suggestions
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 14. Build error handling system

  - Create ErrorHandler class with friendly error message generation
  - Implement handle_tool_error for tool-specific failures
  - Implement handle_api_error for Groq API errors
  - Implement suggest_fallback for alternative approaches when primary method fails
  - Add graceful degradation logic when tools are unavailable
  - _Requirements: 3.8, 4.7, 6.4, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 15. Create Streamlit UI foundation

  - Set up Streamlit app structure with session state management
  - Implement color scheme with feminine touches (blush pink, lavender, teal)
  - Configure custom CSS for rounded edges, soft shadows, and typography
  - Create page layout with sidebar and main content area
  - _Requirements: 1.1, 1.2, 1.5_

- [x] 16. Implement welcome screen

  - Create welcome screen component with friendly greeting
  - Add BRI introduction and tagline ("Ask. Understand. Remember.")
  - Implement upload prompt with drag-and-drop area
  - Add friendly microcopy and emoji touches
  - _Requirements: 1.2, 2.3_

- [x] 17. Implement video upload functionality

  - Create file uploader component accepting MP4, AVI, MOV, MKV formats
  - Implement handle_video_upload to process uploaded files
  - Add video validation (format, size limits)
  - Store uploaded video to file system with unique ID
  - Create video record in database
  - Display friendly confirmation message on successful upload
  - Implement error handling with playful error messages
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

- [x] 18. Implement video processing workflow

  - Trigger MCP server batch processing on video upload
  - Display processing status with friendly progress messages
  - Show progress indicators for each processing step
  - Update video processing_status in database
  - Display completion notification
  - _Requirements: 1.3, 3.6, 3.7_

- [x] 19. Build video library view

  - Create grid layout for displaying uploaded videos
  - Generate and display video thumbnails
  - Show video metadata (filename, duration, upload
    date)
  - Implement video selection to open chat interface
  - Add delete functionality with confirmation
  - _Requirements: 2.5, 11.1, 11.5_

- [x] 20. Implement chat window interface

  - Create chat window component with message history display
  - Implement message input field with send button
  - Display user and assistant messages with distinct styling
  - Add timestamp display for messages
  - Implement auto-scroll to latest message
  - Add emoji/reaction support in messages
  - _Requirements: 1.4, 11.2, 11.3_

- [x] 21. Implement video player with timestamp navigation

  - Embed video player in UI using Streamlit video component
  - Implement timestamp navigation from clickable timestamps in responses
  - Add playback controls
  - Sync player with conversation context
  - _Requirements: 8.4_

- [x] 22. Implement conversation history panel

  - Create sidebar panel showing past conversations for selected video
  - Display conversation turns with timestamps
  - Implement conversation selection to load context
  - Add memory wipe button with confirmation
  - _Requirements: 5.5, 11.2, 11.3, 11.4_

- [x] 23. Integrate agent with UI

  - Connect chat input to GroqAgent.chat method
  - Display agent responses with proper formatting
  - Render frame thumbnails in responses
  - Display clickable timestamps

  - Show follow-up suggestions as clickable buttons
  - Handle loading states during agent processing
  - _Requirements: 4.1, 4.6, 8.1, 8.2, 9.4_

- [x] 24. Implement caching layer

  - Set up Redis connection for MCP server
  - Implement cache key generation for tool results
  - Add cache lookup before tool execution
  - Store tool results in cache with TTL (24 hours)
  - Add cache hit/miss logging
  - _Requirements: 6.6, 12.3_

- [x] 25. Add performance optimizations

  - Implement lazy loading for frame images in UI
  - Add pagination for conversation history (limit to last 10 messages)
  - Optimize database queries with proper indexing
  - Implement parallel tool execution where possible
  - Add request timeout handling
  - _Requirements: 12.1, 12.2, 12.4, 5.6_

- [x] 26. Create configuration and environment setup

  - Create .env.example file with required environment variables
  - Implement settings loader using python-dotenv
  - Add configuration validation on startup
  - Create setup documentation in README.md
  - _Requirements: All requirements depend on proper configuration_

- [x] 27. Add logging and monitoring


  - Implement structured logging throughout application
  - Add log levels (DEBUG, INFO, WARNING, ERROR)
  - Log tool execution times and cache hit rates
  - Log API calls and errors
  - Create log rotation policy
  - _Requirements: 10.4, 12.1_

- [ ] 28. Create deployment scripts

  - Create Dockerfile for MCP server
  - Create Dockerfile for Streamlit UI
  - Create docker-compose.yml for local development
  - Add database initialization script
  - Create startup scripts for development and production
  - _Requirements: All requirements for deployment_

- [ ] 29. Write documentation

  - Create comprehensive README.md with project overview, setup instructions, and usage guide
  - Document API endpoints for MCP server
  - Create user guide for BRI interface
  - Document configuration options
  - Add troubleshooting section
  - _Requirements: All requirements for user adoption_

- [ ]\* 30. Create test suite

  - [ ]\* 30.1 Write unit tests for Memory class

    - Test insert, retrieve, and reset operations
    - Test conversation history retrieval with limits
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ]\* 30.2 Write unit tests for FrameExtractor

    - Test frame extraction at intervals
    - Test timestamp-specific extraction
    - Test metadata retrieval
    - _Requirements: 3.1_

  - [ ]\* 30.3 Write unit tests for ImageCaptioner

    - Test single frame captioning
    - Test batch captioning
    - _Requirements: 3.2_

  - [ ]\* 30.4 Write unit tests for AudioTranscriber

    - Test full video transcription
    - Test segment transcription
    - _Requirements: 3.3_

  - [ ]\* 30.5 Write unit tests for ObjectDetector

    - Test object detection in frames
    - Test object search functionality
    - _Requirements: 3.4_

  - [ ]\* 30.6 Write unit tests for ToolRouter

    - Test query analysis and tool selection
    - Test timestamp extraction
    - _Requirements: 7.1, 7.2_

  - [ ]\* 30.7 Write integration tests for end-to-end video processing

    - Test upload → process → query → response flow
    - Test multi-tool queries
    - Test conversation continuity
    - _Requirements: 3.7, 4.1, 5.3_

  - [ ]\* 30.8 Write integration tests for error handling
    - Test graceful degradation when tools fail
    - Test error message generation
    - _Requirements: 10.1, 10.2, 10.3_
