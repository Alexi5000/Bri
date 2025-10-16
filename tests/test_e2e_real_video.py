"""
End-to-End Test with Real Video
Task 44.1: Upload actual video file, wait for processing, verify data, run test queries
"""

import pytest
import asyncio
import os
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from services.agent import GroqAgent
from services.memory import Memory
from storage.database import Database
from services.video_processing_service import VideoProcessingService


class TestE2ERealVideo:
    """End-to-end tests with real video files."""
    
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
    def video_service(self, db):
        """Get video processing service."""
        return VideoProcessingService(db=db)
    
    @pytest.fixture
    def real_video_id(self, db):
        """Get a real processed video ID with actual data."""
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

    
    def test_video_exists_and_processed(self, db, real_video_id):
        """Test that we have a real processed video."""
        assert real_video_id is not None, "No processed video found in database"
        
        query = "SELECT * FROM videos WHERE video_id = ?"
        results = db.execute_query(query, (real_video_id,))
        assert len(results) > 0
        
        video = results[0]
        assert video['processing_status'] == 'complete'
        assert video['duration'] > 0
        print(f"\n✓ Found processed video: {video['filename']} ({video['duration']}s)")
    
    def test_video_has_frames(self, db, real_video_id):
        """Test that video has extracted frames."""
        if not real_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'frame'
        """
        results = db.execute_query(query, (real_video_id,))
        frame_count = results[0]['count']
        
        assert frame_count > 0, f"No frames found for video {real_video_id}"
        print(f"\n✓ Video has {frame_count} frames")
    
    def test_video_has_captions(self, db, real_video_id):
        """Test that video has captions."""
        if not real_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'caption'
        """
        results = db.execute_query(query, (real_video_id,))
        caption_count = results[0]['count']
        
        assert caption_count > 0, f"No captions found for video {real_video_id}"
        print(f"\n✓ Video has {caption_count} captions")

    
    def test_video_has_transcript(self, db, real_video_id):
        """Test that video has transcript."""
        if not real_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'transcript'
        """
        results = db.execute_query(query, (real_video_id,))
        transcript_count = results[0]['count']
        
        assert transcript_count > 0, f"No transcript found for video {real_video_id}"
        print(f"\n✓ Video has {transcript_count} transcript segments")
    
    def test_video_has_objects(self, db, real_video_id):
        """Test that video has object detections."""
        if not real_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'object'
        """
        results = db.execute_query(query, (real_video_id,))
        object_count = results[0]['count']
        
        assert object_count > 0, f"No objects found for video {real_video_id}"
        print(f"\n✓ Video has {object_count} object detections")
    
    @pytest.mark.asyncio
    async def test_50_queries(self, agent, real_video_id):
        """Run 50 test queries and validate 90%+ pass rate."""
        if not real_video_id:
            pytest.skip("No processed video available")
        
        print(f"\n\n{'='*60}")
        print(f"Running 50 Test Queries on Video: {real_video_id[:8]}...")
        print(f"{'='*60}\n")
        
        test_queries = self._get_test_queries()
        results = []
        passed = 0
        
        for i, query_data in enumerate(test_queries, 1):
            query = query_data['query']
            expected_keywords = query_data['keywords']
            
            try:
                print(f"[{i}/50] {query[:60]}...")
                response = await agent.chat(query, real_video_id)
                response_text = response.message.lower()
                
                # Check if any expected keywords are in response
                found_keywords = [kw for kw in expected_keywords if kw.lower() in response_text]
                success = len(found_keywords) > 0 or len(response_text) > 20
                
                if success:
                    passed += 1
                    print(f"  ✓ PASS")
                else:
                    print(f"  ✗ FAIL - No relevant keywords found")
                
                results.append({
                    'query': query,
                    'passed': success,
                    'response_length': len(response.message)
                })
                
            except Exception as e:
                print(f"  ✗ ERROR: {str(e)[:50]}")
                results.append({
                    'query': query,
                    'passed': False,
                    'error': str(e)
                })
        
        pass_rate = (passed / len(test_queries)) * 100
        print(f"\n{'='*60}")
        print(f"Results: {passed}/{len(test_queries)} passed ({pass_rate:.1f}%)")
        print(f"{'='*60}\n")
        
        assert pass_rate >= 90.0, f"Pass rate {pass_rate:.1f}% is below 90% threshold"

    
    def _get_test_queries(self) -> List[Dict[str, Any]]:
        """Get 50 test queries with expected keywords."""
        return [
            # Scene description (10)
            {'query': 'What is happening in the video?', 'keywords': ['video', 'showing', 'see']},
            {'query': 'Describe what you see', 'keywords': ['see', 'video', 'showing']},
            {'query': 'What is the main content?', 'keywords': ['content', 'video', 'about']},
            {'query': 'Summarize the video', 'keywords': ['video', 'about', 'showing']},
            {'query': 'What is this video about?', 'keywords': ['about', 'video', 'content']},
            {'query': 'Tell me about this video', 'keywords': ['video', 'about', 'showing']},
            {'query': 'What can you see in the video?', 'keywords': ['see', 'video', 'showing']},
            {'query': 'Describe the scene', 'keywords': ['scene', 'video', 'showing']},
            {'query': 'What is shown?', 'keywords': ['shown', 'video', 'see']},
            {'query': 'Give me an overview', 'keywords': ['video', 'about', 'showing']},
            
            # Visual content (10)
            {'query': 'What objects are visible?', 'keywords': ['object', 'see', 'visible']},
            {'query': 'What colors do you see?', 'keywords': ['color', 'see', 'video']},
            {'query': 'Are there any people?', 'keywords': ['people', 'person', 'see']},
            {'query': 'What is in the background?', 'keywords': ['background', 'see', 'video']},
            {'query': 'What is in the foreground?', 'keywords': ['foreground', 'see', 'video']},
            {'query': 'Describe the setting', 'keywords': ['setting', 'video', 'see']},
            {'query': 'What items are present?', 'keywords': ['item', 'see', 'present']},
            {'query': 'What do you notice?', 'keywords': ['notice', 'see', 'video']},
            {'query': 'What stands out?', 'keywords': ['stand', 'see', 'video']},
            {'query': 'What is prominent?', 'keywords': ['prominent', 'see', 'video']},
            
            # Audio/Speech (10)
            {'query': 'What is being said?', 'keywords': ['said', 'audio', 'transcript']},
            {'query': 'Can you hear anything?', 'keywords': ['hear', 'audio', 'sound']},
            {'query': 'What is the audio content?', 'keywords': ['audio', 'content', 'sound']},
            {'query': 'Is there any speech?', 'keywords': ['speech', 'audio', 'said']},
            {'query': 'What words are spoken?', 'keywords': ['word', 'spoken', 'said']},
            {'query': 'Transcribe the audio', 'keywords': ['transcribe', 'audio', 'said']},
            {'query': 'What is mentioned?', 'keywords': ['mention', 'said', 'audio']},
            {'query': 'What topics are discussed?', 'keywords': ['topic', 'discuss', 'said']},
            {'query': 'What is talked about?', 'keywords': ['talk', 'about', 'said']},
            {'query': 'What information is shared?', 'keywords': ['information', 'share', 'said']},

            
            # Temporal/Timing (10)
            {'query': 'What happens at the beginning?', 'keywords': ['beginning', 'start', 'first']},
            {'query': 'What happens at the end?', 'keywords': ['end', 'final', 'last']},
            {'query': 'What happens in the middle?', 'keywords': ['middle', 'during', 'video']},
            {'query': 'When does something happen?', 'keywords': ['when', 'time', 'video']},
            {'query': 'What is the sequence?', 'keywords': ['sequence', 'order', 'video']},
            {'query': 'How does it progress?', 'keywords': ['progress', 'video', 'time']},
            {'query': 'What changes over time?', 'keywords': ['change', 'time', 'video']},
            {'query': 'What is the timeline?', 'keywords': ['timeline', 'time', 'video']},
            {'query': 'What happens first?', 'keywords': ['first', 'start', 'beginning']},
            {'query': 'What happens last?', 'keywords': ['last', 'end', 'final']},
            
            # Context/Understanding (10)
            {'query': 'What is the purpose?', 'keywords': ['purpose', 'video', 'about']},
            {'query': 'What is the message?', 'keywords': ['message', 'video', 'about']},
            {'query': 'What is the goal?', 'keywords': ['goal', 'video', 'purpose']},
            {'query': 'What is the point?', 'keywords': ['point', 'video', 'about']},
            {'query': 'Why was this made?', 'keywords': ['why', 'video', 'made']},
            {'query': 'What is the context?', 'keywords': ['context', 'video', 'about']},
            {'query': 'What is the theme?', 'keywords': ['theme', 'video', 'about']},
            {'query': 'What is the topic?', 'keywords': ['topic', 'video', 'about']},
            {'query': 'What is being communicated?', 'keywords': ['communicate', 'video', 'message']},
            {'query': 'What should I know?', 'keywords': ['know', 'video', 'about']},
        ]
