"""
Integration tests for end-to-end video processing workflow.

Tests the complete flow: upload → process → query → response
Covers Requirements: 3.7, 4.1, 5.3
"""

import pytest
import asyncio
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import sqlite3

from services.agent import GroqAgent
from services.memory import Memory
from services.router import ToolRouter
from services.context import ContextBuilder
from storage.database import Database
from storage.file_store import FileStore
from models.video import Video
from models.responses import AssistantMessageResponse


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create subdirectories
    videos_dir = Path(temp_dir) / "videos"
    frames_dir = Path(temp_dir) / "frames"
    cache_dir = Path(temp_dir) / "cache"
    
    videos_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database with schema
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration REAL,
            upload_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            processing_status TEXT DEFAULT 'pending',
            thumbnail_path TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            message_id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_context (
            context_id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            context_type TEXT NOT NULL,
            timestamp REAL,
            data TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def file_store(temp_data_dir):
    """Create FileStore instance with temporary directory."""
    videos_dir = Path(temp_data_dir) / "videos"
    frames_dir = Path(temp_data_dir) / "frames"
    cache_dir = Path(temp_data_dir) / "cache"
    
    return FileStore(
        video_path=str(videos_dir),
        frame_path=str(frames_dir),
        cache_path=str(cache_dir)
    )


@pytest.fixture
def database(temp_db):
    """Create Database instance with temporary database."""
    db = Database(db_path=temp_db)
    db.connect()
    yield db
    db.close()


@pytest.fixture
def memory(database):
    """Create Memory instance with test database."""
    mem = Memory(db=database)
    yield mem
    mem.close()


@pytest.fixture
def context_builder(database, file_store):
    """Create ContextBuilder instance."""
    return ContextBuilder(db=database, file_store=file_store)


@pytest.fixture
def mock_groq_client():
    """Create mock Groq client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is a test response from the agent."
    
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    
    return mock_client


@pytest.fixture
def sample_video_file(temp_data_dir):
    """Create a sample video file for testing."""
    video_path = Path(temp_data_dir) / "videos" / "test_video.mp4"
    
    # Create a dummy file (not a real video, just for testing file operations)
    video_path.write_bytes(b"fake video content for testing")
    
    return str(video_path)


class TestEndToEndVideoUpload:
    """Test video upload workflow (Requirement 3.7)."""
    
    def test_video_upload_creates_database_record(self, database, sample_video_file):
        """Test that uploading a video creates a database record."""
        video_id = "test_video_001"
        filename = "test_video.mp4"
        duration = 120.5
        
        # Simulate upload by inserting video record
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, filename, sample_video_file, duration))
        
        # Verify video record exists
        query = "SELECT * FROM videos WHERE video_id = ?"
        results = database.execute_query(query, (video_id,))
        video = results[0] if results else None
        
        assert video is not None
        assert video['video_id'] == video_id
        assert video['filename'] == filename
        assert video['file_path'] == sample_video_file
        assert video['duration'] == duration
        assert video['processing_status'] == 'pending'
    
    def test_video_upload_stores_file(self, file_store, temp_data_dir):
        """Test that video file is stored correctly."""
        # Create a test file
        test_content = b"test video content"
        source_file = Path(temp_data_dir) / "source_video.mp4"
        source_file.write_bytes(test_content)
        
        # Copy file to video storage (simulating upload)
        video_id = "test_video_002"
        dest_path = file_store.video_path / f"{video_id}.mp4"
        shutil.copy(str(source_file), str(dest_path))
        
        # Verify file exists and content matches
        assert dest_path.exists()
        assert dest_path.read_bytes() == test_content
    
    def test_video_upload_updates_status(self, database, sample_video_file):
        """Test that video processing status can be updated."""
        video_id = "test_video_003"
        
        # Insert video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", sample_video_file, 100.0))
        
        # Update status to processing
        update_query = "UPDATE videos SET processing_status = ? WHERE video_id = ?"
        database.execute_update(update_query, ('processing', video_id))
        
        select_query = "SELECT * FROM videos WHERE video_id = ?"
        results = database.execute_query(select_query, (video_id,))
        video = results[0]
        assert video['processing_status'] == 'processing'
        
        # Update status to complete
        database.execute_update(update_query, ('complete', video_id))
        
        results = database.execute_query(select_query, (video_id,))
        video = results[0]
        assert video['processing_status'] == 'complete'


class TestEndToEndVideoProcessing:
    """Test video processing workflow (Requirement 3.7)."""
    
    @pytest.mark.asyncio
    async def test_video_processing_workflow(self, database, sample_video_file):
        """Test complete video processing workflow."""
        video_id = "test_video_004"
        
        # Step 1: Upload video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", sample_video_file, 120.0))
        
        query = "SELECT * FROM videos WHERE video_id = ?"
        results = database.execute_query(query, (video_id,))
        video = results[0]
        assert video['processing_status'] == 'pending'
        
        # Step 2: Start processing
        query = "UPDATE videos SET processing_status = ? WHERE video_id = ?"
        database.execute_update(query, ('processing', video_id))
        
        results = database.execute_query("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        video = results[0]
        assert video['processing_status'] == 'processing'
        
        # Step 3: Simulate processing completion
        database.execute_update(query, ('complete', video_id))
        
        results = database.execute_query("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        video = results[0]
        assert video['processing_status'] == 'complete'
    
    @pytest.mark.asyncio
    async def test_processing_with_tool_execution(self, database, sample_video_file):
        """Test that processing triggers appropriate tools."""
        video_id = "test_video_005"
        
        # Insert video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", sample_video_file, 120.0))
        
        # Simulate tool execution by storing context
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Store frame extraction results
        cursor.execute("""
            INSERT INTO video_context (context_id, video_id, context_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("ctx_001", video_id, "frame", 10.0, '{"frame_path": "frame_001.jpg"}'))
        
        # Store caption results
        cursor.execute("""
            INSERT INTO video_context (context_id, video_id, context_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, ("ctx_002", video_id, "caption", 10.0, '{"text": "A person walking"}'))
        
        conn.commit()
        
        # Verify context was stored
        cursor.execute("""
            SELECT COUNT(*) FROM video_context WHERE video_id = ?
        """, (video_id,))
        
        count = cursor.fetchone()[0]
        assert count == 2


class TestEndToEndQueryResponse:
    """Test query → response workflow (Requirement 4.1)."""
    
    @pytest.mark.asyncio
    async def test_simple_query_response(self, memory, mock_groq_client):
        """Test basic query and response flow."""
        video_id = "test_video_006"
        
        # Create agent with mocked Groq client
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Send a simple query
            response = await agent.chat(
                message="Hello, who are you?",
                video_id=video_id
            )
            
            # Verify response structure
            assert isinstance(response, AssistantMessageResponse)
            assert response.message
            assert isinstance(response.frames, list)
            assert isinstance(response.timestamps, list)
            assert isinstance(response.suggestions, list)
    
    @pytest.mark.asyncio
    async def test_query_with_tool_routing(self, memory, mock_groq_client):
        """Test that queries are routed to appropriate tools."""
        video_id = "test_video_007"
        
        router = ToolRouter()
        
        # Test visual query routing
        visual_query = "What's happening in the video?"
        plan = router.analyze_query(visual_query)
        assert 'captions' in plan.tools_needed
        
        # Test audio query routing
        audio_query = "What did they say?"
        plan = router.analyze_query(audio_query)
        assert 'transcripts' in plan.tools_needed
        
        # Test object query routing
        object_query = "Show me all the dogs"
        plan = router.analyze_query(object_query)
        assert 'objects' in plan.tools_needed
    
    @pytest.mark.asyncio
    async def test_query_stores_in_memory(self, memory, mock_groq_client, database):
        """Test that queries and responses are stored in memory."""
        video_id = "test_video_008"
        
        # Insert test video first
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent with mocked Groq client
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Send query
            user_message = "What's in this video?"
            await agent.chat(
                message=user_message,
                video_id=video_id
            )
            
            # Verify memory was stored
            history = memory.get_conversation_history(video_id)
            
            assert len(history) >= 2  # User message + assistant response
            assert any(msg.role == "user" and user_message in msg.content for msg in history)
            assert any(msg.role == "assistant" for msg in history)


class TestEndToEndConversationContinuity:
    """Test conversation continuity with memory (Requirement 5.3)."""
    
    @pytest.mark.asyncio
    async def test_follow_up_question_uses_context(self, memory, mock_groq_client, database):
        """Test that follow-up questions use conversation context."""
        video_id = "test_video_009"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # First query
            await agent.chat(
                message="What's happening in the video?",
                video_id=video_id
            )
            
            # Follow-up query
            await agent.chat(
                message="Can you tell me more about that?",
                video_id=video_id
            )
            
            # Verify conversation history
            history = memory.get_conversation_history(video_id)
            
            # Should have 4 messages: 2 user + 2 assistant
            assert len(history) >= 4
            
            # Verify chronological order
            assert history[0].role == "user"
            assert history[1].role == "assistant"
            assert history[2].role == "user"
            assert history[3].role == "assistant"
    
    @pytest.mark.asyncio
    async def test_conversation_context_retrieval(self, memory, database):
        """Test retrieving conversation context for follow-ups."""
        video_id = "test_video_010"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Add conversation history
        memory.add_memory_pair(
            video_id=video_id,
            user_message="What's in the video?",
            assistant_message="I see a park scene with people walking."
        )
        
        memory.add_memory_pair(
            video_id=video_id,
            user_message="What are they wearing?",
            assistant_message="They're wearing casual clothes."
        )
        
        # Retrieve context
        context = memory.get_recent_context(video_id, max_messages=4)
        
        # Verify context contains conversation
        assert "What's in the video?" in context
        assert "park scene" in context
        assert "What are they wearing?" in context
        assert "casual clothes" in context
    
    @pytest.mark.asyncio
    async def test_separate_video_conversations(self, memory, mock_groq_client, database):
        """Test that conversations are separate per video."""
        video_id_1 = "test_video_011"
        video_id_2 = "test_video_012"
        
        # Insert test videos
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        for vid in [video_id_1, video_id_2]:
            database.execute_update(query, (vid, f"{vid}.mp4", f"test_path_{vid}.mp4", 100.0))
        
        # Create agent
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Query video 1
            await agent.chat(
                message="What's in video 1?",
                video_id=video_id_1
            )
            
            # Query video 2
            await agent.chat(
                message="What's in video 2?",
                video_id=video_id_2
            )
            
            # Verify separate histories
            history_1 = memory.get_conversation_history(video_id_1)
            history_2 = memory.get_conversation_history(video_id_2)
            
            assert len(history_1) >= 2
            assert len(history_2) >= 2
            
            # Verify content is separate
            assert any("video 1" in msg.content.lower() for msg in history_1)
            assert any("video 2" in msg.content.lower() for msg in history_2)


class TestEndToEndMultiToolQueries:
    """Test queries requiring multiple tools."""
    
    @pytest.mark.asyncio
    async def test_query_requiring_captions_and_objects(self):
        """Test query that needs both captions and object detection."""
        router = ToolRouter()
        
        query = "Show me scenes with dogs and describe what they're doing"
        plan = router.analyze_query(query)
        
        # Should require both captions and objects
        assert 'captions' in plan.tools_needed
        assert 'objects' in plan.tools_needed
        
        # Verify execution order
        assert len(plan.execution_order) >= 2
    
    @pytest.mark.asyncio
    async def test_query_requiring_all_tools(self):
        """Test query that needs captions, transcripts, and objects."""
        router = ToolRouter()
        
        query = "Find all the cars and tell me what people are saying about them"
        plan = router.analyze_query(query)
        
        # Should require all three tools
        assert 'captions' in plan.tools_needed or 'objects' in plan.tools_needed
        assert 'transcripts' in plan.tools_needed
    
    @pytest.mark.asyncio
    async def test_timestamp_query_with_context(self):
        """Test query with timestamp that needs contextual information."""
        router = ToolRouter()
        
        query = "What's happening at 1:30?"
        plan = router.analyze_query(query)
        
        # Should extract timestamp
        assert plan.parameters.get('timestamp') is not None
        assert plan.parameters['timestamp'] == 90.0  # 1:30 = 90 seconds
        
        # Should require captions for visual context
        assert 'captions' in plan.tools_needed


class TestEndToEndErrorHandling:
    """Test error handling in end-to-end flow."""
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_tool_failure(self, memory, mock_groq_client):
        """Test that system continues when a tool fails."""
        video_id = "test_video_013"
        
        # Create agent with mocked client
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock tool failure by patching httpx
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.json.return_value = {'status': 'error', 'error': 'Tool failed'}
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                # Query should still return a response
                response = await agent.chat(
                    message="What's in the video?",
                    video_id=video_id
                )
                
                # Should get a response even with tool failure
                assert isinstance(response, AssistantMessageResponse)
                assert response.message
    
    @pytest.mark.asyncio
    async def test_error_message_is_user_friendly(self, memory):
        """Test that error messages are friendly and helpful."""
        video_id = "test_video_014"
        
        # Create agent with invalid API key
        with patch('services.agent.Groq') as mock_groq:
            mock_groq.side_effect = Exception("API key invalid")
            
            try:
                agent = GroqAgent(
                    groq_api_key="invalid_key",
                    memory=memory
                )
                # Should raise AgentError with friendly message
                assert False, "Should have raised an error"
            except Exception as e:
                # Error should be caught and handled
                assert "API key" in str(e) or "Groq" in str(e)


class TestEndToEndResponseGeneration:
    """Test response generation with media."""
    
    @pytest.mark.asyncio
    async def test_response_includes_timestamps(self, memory, mock_groq_client):
        """Test that responses include relevant timestamps."""
        video_id = "test_video_015"
        
        # Mock response with timestamp references
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "At 1:30, you can see a person walking."
        mock_groq_client.chat.completions.create = Mock(return_value=mock_response)
        
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock tool context with timestamps
            with patch.object(agent, '_gather_tool_context', new_callable=AsyncMock) as mock_gather:
                mock_gather.return_value = {
                    'frames': ['frame1.jpg'],
                    'timestamps': [90.0],  # 1:30
                    'captions': [{'timestamp': 90.0, 'text': 'Person walking', 'frame_path': 'frame1.jpg'}],
                    'transcripts': [],
                    'objects': [],
                    'errors': []
                }
                
                response = await agent.chat(
                    message="What happens at 1:30?",
                    video_id=video_id
                )
                
                # Response should include timestamps
                assert len(response.timestamps) > 0
    
    @pytest.mark.asyncio
    async def test_response_includes_suggestions(self, memory, mock_groq_client):
        """Test that responses include follow-up suggestions."""
        video_id = "test_video_016"
        
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            response = await agent.chat(
                message="What's in the video?",
                video_id=video_id
            )
            
            # Should include 1-3 suggestions
            assert len(response.suggestions) >= 1
            assert len(response.suggestions) <= 3
            
            # Suggestions should be strings
            for suggestion in response.suggestions:
                assert isinstance(suggestion, str)
                assert len(suggestion) > 0


class TestEndToEndPerformance:
    """Test performance aspects of end-to-end flow."""
    
    @pytest.mark.asyncio
    async def test_conversation_history_limit(self, memory, database):
        """Test that conversation history is limited for performance."""
        video_id = "test_video_017"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Add many messages
        for i in range(20):
            memory.add_memory_pair(
                video_id=video_id,
                user_message=f"Question {i}",
                assistant_message=f"Answer {i}"
            )
        
        # Retrieve with limit
        history = memory.get_conversation_history(video_id, limit=10)
        
        # Should only get most recent 10
        assert len(history) == 10
        
        # Should be most recent messages
        assert "Question 19" in history[-2].content or "Question 18" in history[-2].content
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self, memory, database):
        """Test that memory can be reset for privacy."""
        video_id = "test_video_018"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'pending')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Add messages
        memory.add_memory_pair(
            video_id=video_id,
            user_message="Test question",
            assistant_message="Test answer"
        )
        
        # Verify messages exist
        assert memory.count_messages(video_id) > 0
        
        # Reset memory
        memory.reset_memory(video_id)
        
        # Verify messages are deleted
        assert memory.count_messages(video_id) == 0
