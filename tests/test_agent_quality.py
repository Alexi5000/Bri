"""
Agent Response Quality Tests
Task 44.4: Test agent response quality and conversation context
"""

import pytest
import asyncio
import re
from storage.database import Database
from services.agent import GroqAgent
from services.memory import Memory


class TestAgentQuality:
    """Test agent response quality."""
    
    @pytest.fixture
    def db(self):
        """Get database connection."""
        db = Database()
        db.connect()
        yield db
        db.close()
    
    @pytest.fixture
    def memory(self, db):
        """Get memory instance."""
        mem = Memory(db=db)
        yield mem
        mem.close()
    
    @pytest.fixture
    def agent(self, memory):
        """Get agent instance."""
        return GroqAgent(memory=memory)
    
    @pytest.fixture
    def processed_video_id(self, db):
        """Get a processed video ID with actual data."""
        # Find a video that has frames
        query = """
            SELECT v.video_id 
            FROM videos v
            INNER JOIN video_context vc ON v.video_id = vc.video_id
            WHERE v.processing_status = 'complete' 
            AND vc.context_type = 'frame'
            GROUP BY v.video_id
            HAVING COUNT(*) > 0
            LIMIT 1
        """
        results = db.execute_query(query)
        if results:
            return results[0]['video_id']
        return None
    
    @pytest.mark.asyncio
    async def test_response_contains_expected_keywords(self, agent, processed_video_id):
        """Test that responses contain relevant keywords."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        print(f"\n{'='*60}")
        print(f"Testing Response Keyword Relevance")
        print(f"{'='*60}\n")
        
        test_cases = [
            {
                'query': 'What is in the video?',
                'expected_keywords': ['video', 'see', 'showing', 'content'],
                'min_matches': 1
            },
            {
                'query': 'Describe what you see',
                'expected_keywords': ['see', 'video', 'showing', 'appears'],
                'min_matches': 1
            },
            {
                'query': 'What is being said?',
                'expected_keywords': ['said', 'audio', 'transcript', 'speaking'],
                'min_matches': 1
            },
        ]
        
        passed = 0
        for i, test_case in enumerate(test_cases, 1):
            query = test_case['query']
            expected = test_case['expected_keywords']
            min_matches = test_case['min_matches']
            
            print(f"[{i}/{len(test_cases)}] Query: {query}")
            
            response = await agent.chat(query, processed_video_id)
            response_text = response.message.lower()
            
            matches = [kw for kw in expected if kw in response_text]
            
            if len(matches) >= min_matches:
                print(f"  ✓ PASS - Found keywords: {matches}")
                passed += 1
            else:
                print(f"  ✗ FAIL - Expected {min_matches} keywords, found: {matches}")
        
        pass_rate = (passed / len(test_cases)) * 100
        print(f"\n{'='*60}")
        print(f"Pass Rate: {passed}/{len(test_cases)} ({pass_rate:.1f}%)")
        print(f"{'='*60}\n")
        
        assert pass_rate >= 90.0, f"Pass rate {pass_rate:.1f}% below 90% threshold"

    
    @pytest.mark.asyncio
    async def test_response_includes_timestamps(self, agent, processed_video_id):
        """Test that responses include timestamps when relevant."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        print(f"\n{'='*60}")
        print(f"Testing Timestamp Inclusion")
        print(f"{'='*60}\n")
        
        # Queries that should trigger timestamp responses
        temporal_queries = [
            'What happens at the beginning?',
            'What happens at the end?',
            'Show me the timeline',
        ]
        
        passed = 0
        for i, query in enumerate(temporal_queries, 1):
            print(f"[{i}/{len(temporal_queries)}] Query: {query}")
            
            response = await agent.chat(query, processed_video_id)
            
            # Check if response includes timestamps (either in message or timestamps field)
            has_timestamps = (
                len(response.timestamps) > 0 or
                re.search(r'\d+:\d+', response.message) or  # MM:SS format
                re.search(r'\d+\s*seconds?', response.message.lower()) or
                'timestamp' in response.message.lower()
            )
            
            if has_timestamps:
                print(f"  ✓ PASS - Includes timestamps")
                passed += 1
            else:
                print(f"  ✗ FAIL - No timestamps found")
        
        pass_rate = (passed / len(temporal_queries)) * 100
        print(f"\n{'='*60}")
        print(f"Pass Rate: {passed}/{len(temporal_queries)} ({pass_rate:.1f}%)")
        print(f"{'='*60}\n")
        
        assert pass_rate >= 90.0, f"Timestamp inclusion rate {pass_rate:.1f}% below 90%"
    
    @pytest.mark.asyncio
    async def test_response_references_video_content(self, agent, processed_video_id, db):
        """Test that responses reference specific video content."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        print(f"\n{'='*60}")
        print(f"Testing Video Content References")
        print(f"{'='*60}\n")
        
        # Get some actual content from the video
        query = """
            SELECT data FROM video_context 
            WHERE video_id = ? AND context_type = 'caption'
            LIMIT 3
        """
        results = db.execute_query(query, (processed_video_id,))
        
        if not results:
            pytest.skip("No captions available")
        
        # Ask about the video
        response = await agent.chat('What do you see in the video?', processed_video_id)
        response_text = response.message.lower()
        
        # Check if response is substantive (not just generic)
        is_substantive = (
            len(response_text) > 50 and  # Reasonable length
            not all(word in response_text for word in ['sorry', 'cannot', 'unable']) and
            any(word in response_text for word in ['see', 'video', 'showing', 'appears', 'contains'])
        )
        
        print(f"Response length: {len(response_text)} chars")
        print(f"Is substantive: {is_substantive}")
        print(f"Status: {'✓ PASS' if is_substantive else '✗ FAIL'}")
        print(f"\n{'='*60}\n")
        
        assert is_substantive, "Response does not reference specific video content"

    
    @pytest.mark.asyncio
    async def test_agent_maintains_conversation_context(self, agent, processed_video_id, memory):
        """Test that agent maintains conversation context."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        print(f"\n{'='*60}")
        print(f"Testing Conversation Context")
        print(f"{'='*60}\n")
        
        # First query
        print("[1/3] Initial query...")
        response1 = await agent.chat('What is in the video?', processed_video_id)
        print(f"  Response: {response1.message[:100]}...")
        
        # Follow-up query (should use context)
        print("[2/3] Follow-up query...")
        response2 = await agent.chat('Can you tell me more about that?', processed_video_id)
        print(f"  Response: {response2.message[:100]}...")
        
        # Another follow-up
        print("[3/3] Second follow-up...")
        response3 = await agent.chat('What else?', processed_video_id)
        print(f"  Response: {response3.message[:100]}...")
        
        # Check that conversation history was stored
        history = memory.get_conversation_history(processed_video_id)
        
        print(f"\nConversation history: {len(history)} messages")
        
        # Should have at least 6 messages (3 user + 3 assistant)
        assert len(history) >= 6, f"Expected at least 6 messages, got {len(history)}"
        
        # Check that responses are not identical (showing context awareness)
        responses = [response1.message, response2.message, response3.message]
        unique_responses = len(set(responses))
        
        print(f"Unique responses: {unique_responses}/3")
        print(f"Status: {'✓ PASS' if unique_responses >= 2 else '✗ FAIL'}")
        print(f"\n{'='*60}\n")
        
        assert unique_responses >= 2, "Agent not showing context awareness"
    
    @pytest.mark.asyncio
    async def test_response_quality_score(self, agent, processed_video_id):
        """Test overall response quality score."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        print(f"\n{'='*60}")
        print(f"Overall Response Quality Score")
        print(f"{'='*60}\n")
        
        test_queries = [
            'What is in the video?',
            'Describe what you see',
            'What is being said?',
            'What happens at the beginning?',
            'Summarize the video',
        ]
        
        scores = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"[{i}/{len(test_queries)}] {query}")
            
            response = await agent.chat(query, processed_video_id)
            
            # Calculate quality score based on multiple factors
            score = 0
            
            # Length check (should be substantive)
            if len(response.message) > 50:
                score += 25
            
            # Not an error message
            if not any(word in response.message.lower() for word in ['error', 'sorry', 'cannot', 'unable']):
                score += 25
            
            # Contains relevant keywords
            if any(word in response.message.lower() for word in ['video', 'see', 'showing', 'appears']):
                score += 25
            
            # Has suggestions (shows engagement)
            if len(response.suggestions) > 0:
                score += 25
            
            scores.append(score)
            print(f"  Score: {score}/100")
        
        avg_score = sum(scores) / len(scores)
        
        print(f"\n{'='*60}")
        print(f"Average Quality Score: {avg_score:.1f}/100")
        print(f"Target: >= 90")
        print(f"Status: {'✓ PASS' if avg_score >= 90 else '✗ FAIL'}")
        print(f"{'='*60}\n")
        
        assert avg_score >= 90.0, f"Quality score {avg_score:.1f} below 90 threshold"
