"""
Integration tests for error handling and graceful degradation.

Tests the system's ability to handle failures gracefully and provide
friendly error messages to users.

Covers Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
import sqlite3

from services.agent import GroqAgent
from services.memory import Memory
from services.error_handler import ErrorHandler, ErrorType
from storage.database import Database
from models.responses import AssistantMessageResponse


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
def mock_groq_client():
    """Create mock Groq client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "This is a test response from the agent."
    
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    
    return mock_client


class TestToolFailureGracefulDegradation:
    """
    Test graceful degradation when tools fail.
    
    Requirement 10.1, 10.2, 10.4, 10.5
    """
    
    @pytest.mark.asyncio
    async def test_single_tool_failure_continues_with_others(self, memory, mock_groq_client, database):
        """Test that when one tool fails, others continue to execute."""
        video_id = "test_video_001"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'complete')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent with mocked Groq client
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock httpx client to simulate one tool failing
            with patch('httpx.AsyncClient') as mock_client:
                # Create mock responses for different tools
                async def mock_post(url, **kwargs):
                    mock_response = Mock()
                    
                    # Simulate caption tool failing
                    if 'caption_frames' in url:
                        mock_response.status_code = 500
                        mock_response.json.return_value = {
                            'status': 'error',
                            'error': 'Caption service unavailable'
                        }
                    # Other tools succeed
                    else:
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            'status': 'success',
                            'result': {
                                'segments': [
                                    {'start': 10.0, 'text': 'Test transcript'}
                                ]
                            }
                        }
                    
                    return mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=mock_post
                )
                
                # Query should still return a response despite caption tool failure
                response = await agent.chat(
                    message="What's being said in the video?",
                    video_id=video_id
                )
                
                # Should get a response
                assert isinstance(response, AssistantMessageResponse)
                assert response.message
                assert len(response.message) > 0
    
    @pytest.mark.asyncio
    async def test_all_tools_fail_returns_friendly_message(self, memory, mock_groq_client, database):
        """Test that when all tools fail, a friendly message is returned."""
        video_id = "test_video_002"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'complete')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent with mocked Groq client
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock httpx client to simulate all tools failing
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.json.return_value = {
                    'status': 'error',
                    'error': 'Service unavailable'
                }
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                # Query should still return a response
                response = await agent.chat(
                    message="What's in the video?",
                    video_id=video_id
                )
                
                # Should get a friendly response
                assert isinstance(response, AssistantMessageResponse)
                assert response.message
                # Message should be friendly and not contain technical error details
                assert 'error' not in response.message.lower() or 'trouble' in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_tool_timeout_handled_gracefully(self, memory, mock_groq_client, database):
        """Test that tool timeouts are handled gracefully."""
        video_id = "test_video_003"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'complete')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent with mocked Groq client
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock httpx client to simulate timeout
            with patch('httpx.AsyncClient') as mock_client:
                import httpx
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=httpx.TimeoutException("Request timed out")
                )
                
                # Query should still return a response
                response = await agent.chat(
                    message="What's happening in the video?",
                    video_id=video_id
                )
                
                # Should get a response
                assert isinstance(response, AssistantMessageResponse)
                assert response.message
    
    @pytest.mark.asyncio
    async def test_partial_tool_results_used(self, memory, mock_groq_client, database):
        """Test that partial results from successful tools are used."""
        video_id = "test_video_004"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'complete')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent with mocked Groq client
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock httpx client with mixed success/failure
            with patch('httpx.AsyncClient') as mock_client:
                call_count = {'count': 0}
                
                async def mock_post(url, **kwargs):
                    mock_response = Mock()
                    call_count['count'] += 1
                    
                    # First call succeeds, second fails
                    if call_count['count'] == 1:
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            'status': 'success',
                            'result': {
                                'captions': [
                                    {
                                        'timestamp': 10.0,
                                        'text': 'A person walking',
                                        'frame_path': 'frame_001.jpg'
                                    }
                                ]
                            }
                        }
                    else:
                        mock_response.status_code = 500
                        mock_response.json.return_value = {
                            'status': 'error',
                            'error': 'Tool failed'
                        }
                    
                    return mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=mock_post
                )
                
                # Query requiring multiple tools
                response = await agent.chat(
                    message="What's happening and what's being said?",
                    video_id=video_id
                )
                
                # Should get a response using partial results
                assert isinstance(response, AssistantMessageResponse)
                assert response.message


class TestErrorMessageGeneration:
    """
    Test friendly error message generation.
    
    Requirement 10.1, 10.2, 10.3
    """
    
    def test_tool_error_messages_are_friendly(self):
        """Test that tool errors generate friendly messages."""
        # Test frame extractor error
        error = Exception("Frame extraction failed")
        message = ErrorHandler.handle_tool_error('frame_extractor', error)
        
        assert message
        assert 'trouble' in message.lower() or 'tricky' in message.lower()
        assert 'frame' in message.lower() or 'audio' in message.lower()
        # Should not contain technical jargon
        assert 'exception' not in message.lower()
        assert 'traceback' not in message.lower()
    
    def test_api_error_messages_are_friendly(self):
        """Test that API errors generate friendly messages."""
        # Test rate limit error
        error = Exception("Rate limit exceeded (429)")
        message = ErrorHandler.handle_api_error(error)
        
        assert message
        assert 'moment' in message.lower() or 'try again' in message.lower()
        # Should not contain HTTP status codes in user message
        assert '429' not in message
    
    def test_timeout_error_messages_are_friendly(self):
        """Test that timeout errors generate friendly messages."""
        error = Exception("Request timed out")
        message = ErrorHandler.handle_api_error(error)
        
        assert message
        assert 'longer' in message.lower() or 'expected' in message.lower()
        assert 'timeout' not in message.lower()  # Avoid technical terms
    
    def test_authentication_error_messages_are_helpful(self):
        """Test that auth errors provide helpful guidance."""
        error = Exception("Authentication failed (401)")
        message = ErrorHandler.handle_api_error(error)
        
        assert message
        assert 'api key' in message.lower() or 'configuration' in message.lower()
        # Should guide user to fix the issue
        assert 'check' in message.lower() or 'trouble' in message.lower()
    
    def test_upload_error_messages_are_friendly(self):
        """Test that upload errors generate friendly messages."""
        # Test format error
        error = Exception("Unsupported format")
        message = ErrorHandler.handle_video_upload_error(error, "test.avi")
        
        assert message
        assert 'format' in message.lower() or 'mp4' in message.lower()
        # Should be playful
        assert 'oops' in message.lower() or 'hmm' in message.lower()
    
    def test_processing_error_messages_include_context(self):
        """Test that processing errors include helpful context."""
        error = Exception("Processing failed")
        completed_steps = ['frame_extraction', 'captioning']
        
        message = ErrorHandler.handle_processing_error(
            'test_video_001',
            error,
            completed_steps
        )
        
        assert message
        # Should mention what succeeded
        assert 'frame' in message.lower() or 'caption' in message.lower()
        # Should be encouraging
        assert 'manage' in message.lower() or 'complete' in message.lower()
    
    def test_query_error_messages_suggest_alternatives(self):
        """Test that query errors suggest alternatives."""
        error = Exception("No results found")
        message = ErrorHandler.handle_query_error("Show me the dog", error)
        
        assert message
        # Should suggest trying something else
        assert 'try' in message.lower() or 'else' in message.lower()
        assert 'find' in message.lower() or "couldn't" in message.lower()
    
    def test_error_classification_is_accurate(self):
        """Test that errors are classified correctly."""
        # API error
        api_error = Exception("Groq API rate limit exceeded")
        assert ErrorHandler.classify_error(api_error) == ErrorType.API_ERROR
        
        # Network error
        network_error = Exception("Connection timeout")
        assert ErrorHandler.classify_error(network_error) == ErrorType.NETWORK_ERROR
        
        # Tool error
        tool_error = Exception("Frame extractor failed")
        assert ErrorHandler.classify_error(tool_error) == ErrorType.TOOL_ERROR
        
        # Validation error
        validation_error = ValueError("Invalid input")
        assert ErrorHandler.classify_error(validation_error) == ErrorType.VALIDATION_ERROR


class TestFallbackSuggestions:
    """
    Test fallback suggestion generation.
    
    Requirement 10.3
    """
    
    def test_suggests_alternatives_when_captions_unavailable(self):
        """Test suggestions when captions fail but transcripts available."""
        query = "What do you see in the video?"
        available_data = ['transcripts']
        
        suggestion = ErrorHandler.suggest_fallback(query, available_data)
        
        assert suggestion
        assert 'said' in suggestion.lower() or 'audio' in suggestion.lower()
    
    def test_suggests_alternatives_when_transcripts_unavailable(self):
        """Test suggestions when transcripts fail but captions available."""
        query = "What did they say?"
        available_data = ['captions']
        
        suggestion = ErrorHandler.suggest_fallback(query, available_data)
        
        assert suggestion
        assert 'describe' in suggestion.lower() or 'visible' in suggestion.lower()
    
    def test_suggests_alternatives_when_objects_unavailable(self):
        """Test suggestions when object detection fails."""
        query = "Find all the dogs"
        available_data = ['captions', 'transcripts']
        
        suggestion = ErrorHandler.suggest_fallback(query, available_data)
        
        assert suggestion
        # Should suggest using available data
        assert 'describe' in suggestion.lower() or 'said' in suggestion.lower()
    
    def test_suggests_reupload_when_no_data_available(self):
        """Test suggestions when no data is available."""
        query = "What's in the video?"
        available_data = []
        
        suggestion = ErrorHandler.suggest_fallback(query, available_data)
        
        assert suggestion
        assert 'upload' in suggestion.lower() or 'try' in suggestion.lower()
    
    def test_fallback_suggestions_are_contextual(self):
        """Test that fallback suggestions match the query context."""
        # Visual query with only audio available
        visual_query = "Show me the scenes with cars"
        suggestion = ErrorHandler.suggest_fallback(visual_query, ['transcripts'])
        assert 'said' in suggestion.lower() or 'audio' in suggestion.lower()
        
        # Audio query with only visual available
        audio_query = "What did they talk about?"
        suggestion = ErrorHandler.suggest_fallback(audio_query, ['captions'])
        assert 'describe' in suggestion.lower() or 'see' in suggestion.lower()


class TestGracefulDegradationStrategy:
    """
    Test graceful degradation strategy implementation.
    
    Requirement 10.4, 10.5
    """
    
    def test_degradation_plan_with_partial_tools(self):
        """Test degradation plan when some tools are unavailable."""
        requested_tools = ['captions', 'transcripts', 'objects']
        available_tools = ['captions', 'transcripts']
        query = "What's happening in the video?"
        
        plan = ErrorHandler.handle_graceful_degradation(
            requested_tools,
            available_tools,
            query
        )
        
        assert plan['can_proceed'] is True
        assert len(plan['usable_tools']) == 2
        assert 'objects' in plan['unavailable_tools']
        assert plan['message']
        assert 'trouble' in plan['message'].lower() or 'working' in plan['message'].lower()
    
    def test_degradation_plan_with_no_tools(self):
        """Test degradation plan when no tools are available."""
        requested_tools = ['captions', 'transcripts']
        available_tools = []
        query = "Describe the video"
        
        plan = ErrorHandler.handle_graceful_degradation(
            requested_tools,
            available_tools,
            query
        )
        
        assert plan['can_proceed'] is False
        assert len(plan['usable_tools']) == 0
        assert plan['message']
        assert 'break' in plan['message'].lower() or 'chat' in plan['message'].lower()
    
    def test_degradation_includes_fallback_suggestions(self):
        """Test that degradation plan includes fallback suggestions."""
        # Request captions and transcripts, but only captions available
        requested_tools = ['captions', 'transcripts']
        available_tools = ['captions']
        query = "What's being said in the video?"
        
        plan = ErrorHandler.handle_graceful_degradation(
            requested_tools,
            available_tools,
            query
        )
        
        # Should be able to proceed with captions
        assert plan['can_proceed'] is True
        assert 'captions' in plan['usable_tools']
        assert 'transcripts' in plan['unavailable_tools']
        # Should have a fallback suggestion since we have usable tools
        assert plan['fallback_suggestion'] is not None
        # Suggestion should be relevant to available data (captions)
        assert 'describe' in plan['fallback_suggestion'].lower() or 'visible' in plan['fallback_suggestion'].lower()
    
    def test_degradation_message_maintains_personality(self):
        """Test that degradation messages maintain BRI's friendly personality."""
        requested_tools = ['captions']
        available_tools = []
        query = "What do you see?"
        
        plan = ErrorHandler.handle_graceful_degradation(
            requested_tools,
            available_tools,
            query
        )
        
        message = plan['message']
        # Should be friendly and supportive
        assert any(word in message.lower() for word in [
            'break', 'moment', 'chat', 'found', 'still'
        ])
        # Should not be technical or cold
        assert 'error' not in message.lower()
        assert 'failed' not in message.lower()


class TestEndToEndErrorRecovery:
    """
    Test end-to-end error recovery scenarios.
    
    Requirement 10.1, 10.2, 10.4, 10.5
    """
    
    @pytest.mark.asyncio
    async def test_agent_recovers_from_groq_api_error(self, memory, database):
        """Test that agent handles Groq API errors gracefully."""
        video_id = "test_video_005"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'complete')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent with mocked Groq client that fails
        with patch('services.agent.Groq') as mock_groq:
            mock_client = Mock()
            mock_client.chat.completions.create = Mock(
                side_effect=Exception("API rate limit exceeded")
            )
            mock_groq.return_value = mock_client
            
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Query should return friendly error message
            response = await agent.chat(
                message="What's in the video?",
                video_id=video_id
            )
            
            # Should get a response with friendly error
            assert isinstance(response, AssistantMessageResponse)
            assert response.message
            # Should be friendly, not technical - check for various friendly phrases
            message_lower = response.message.lower()
            is_friendly = any(phrase in message_lower for phrase in [
                'thinking', 'moment', 'try', 'trouble', 'again', 'rephrase'
            ])
            assert is_friendly, f"Expected friendly message, got: {response.message}"
            # Should not contain technical error details
            assert 'exception' not in message_lower
            assert 'traceback' not in message_lower
    
    @pytest.mark.asyncio
    async def test_agent_continues_after_tool_failure(self, memory, mock_groq_client, database):
        """Test that agent continues processing after a tool fails."""
        video_id = "test_video_006"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'complete')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock tool failure
            with patch('httpx.AsyncClient') as mock_client:
                # First tool fails, subsequent tools succeed
                call_count = {'count': 0}
                
                async def mock_post(url, **kwargs):
                    mock_response = Mock()
                    call_count['count'] += 1
                    
                    if call_count['count'] == 1:
                        # First call fails
                        mock_response.status_code = 500
                        mock_response.json.return_value = {
                            'status': 'error',
                            'error': 'Tool unavailable'
                        }
                    else:
                        # Subsequent calls succeed
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            'status': 'success',
                            'result': {'segments': []}
                        }
                    
                    return mock_response
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=mock_post
                )
                
                # Should complete successfully despite first tool failure
                response = await agent.chat(
                    message="Describe the video and tell me what's said",
                    video_id=video_id
                )
                
                assert isinstance(response, AssistantMessageResponse)
                assert response.message
    
    @pytest.mark.asyncio
    async def test_error_messages_stored_in_memory(self, memory, mock_groq_client, database):
        """Test that error interactions are stored in memory."""
        video_id = "test_video_007"
        
        # Insert test video
        query = """
            INSERT INTO videos (video_id, filename, file_path, duration, processing_status)
            VALUES (?, ?, ?, ?, 'complete')
        """
        database.execute_update(query, (video_id, "test.mp4", "test_path.mp4", 100.0))
        
        # Create agent
        with patch('services.agent.Groq', return_value=mock_groq_client):
            agent = GroqAgent(
                groq_api_key="test_key",
                memory=memory
            )
            
            # Mock all tools failing
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.json.return_value = {
                    'status': 'error',
                    'error': 'All tools unavailable'
                }
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                
                # Send query
                user_message = "What's in the video?"
                await agent.chat(
                    message=user_message,
                    video_id=video_id
                )
                
                # Verify interaction was stored in memory
                history = memory.get_conversation_history(video_id)
                
                assert len(history) >= 2
                # User message should be stored
                assert any(msg.role == "user" and user_message in msg.content for msg in history)
                # Assistant response (even error) should be stored
                assert any(msg.role == "assistant" for msg in history)


class TestErrorHandlerUtilities:
    """Test ErrorHandler utility methods."""
    
    def test_format_error_for_user_routes_correctly(self):
        """Test that format_error_for_user routes to correct handler."""
        # Tool error
        tool_error = Exception("Tool failed")
        message = ErrorHandler.format_error_for_user(
            tool_error,
            context={'tool_name': 'frame_extractor'}
        )
        assert 'frame' in message.lower() or 'audio' in message.lower()
        
        # API error
        api_error = Exception("Rate limit exceeded")
        message = ErrorHandler.format_error_for_user(api_error)
        assert 'moment' in message.lower() or 'thinking' in message.lower()
        
        # Upload error
        upload_error = Exception("Invalid format")
        message = ErrorHandler.format_error_for_user(
            upload_error,
            context={'upload': True, 'filename': 'test.avi'}
        )
        assert 'format' in message.lower() or 'mp4' in message.lower()
    
    def test_generic_error_message_is_friendly(self):
        """Test that generic error messages are friendly."""
        message = ErrorHandler.get_generic_error_message()
        
        assert message
        assert len(message) > 0
        # Should be friendly and contain common phrases from GENERAL_ERROR_MESSAGES
        assert any(phrase in message.lower() for phrase in [
            'oops', 'try', 'again', 'snag', 'shot', 'planned', 'approach', 'moment', 'way'
        ])
    
    def test_tool_fallback_suggestions_are_relevant(self):
        """Test that tool fallback suggestions are relevant."""
        # Caption tool fails, transcribe available
        suggestion = ErrorHandler._suggest_tool_fallback(
            'caption_frames',
            ['transcribe_audio']
        )
        assert suggestion
        assert 'said' in suggestion.lower() or 'audio' in suggestion.lower()
        
        # Transcribe fails, caption available
        suggestion = ErrorHandler._suggest_tool_fallback(
            'transcribe_audio',
            ['caption_frames']
        )
        assert suggestion
        assert 'visible' in suggestion.lower() or 'see' in suggestion.lower()
        
        # No alternatives available
        suggestion = ErrorHandler._suggest_tool_fallback(
            'caption_frames',
            []
        )
        assert suggestion is None
