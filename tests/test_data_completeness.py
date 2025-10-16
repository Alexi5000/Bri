"""
Data Completeness Tests
Task 44.2: Verify all expected data is stored after video processing
"""

import pytest
import json
from storage.database import Database
from services.video_processing_service import VideoProcessingService


class TestDataCompleteness:
    """Test that processed videos have complete data."""
    
    @pytest.fixture
    def db(self):
        """Get database connection."""
        db = Database()
        db.connect()
        yield db
        db.close()
    
    @pytest.fixture
    def video_service(self, db):
        """Get video processing service."""
        return VideoProcessingService(db=db)
    
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
    
    def test_video_has_expected_frames(self, db, processed_video_id):
        """Test that video has expected number of frames based on duration."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        # Get video duration
        query = "SELECT duration FROM videos WHERE video_id = ?"
        results = db.execute_query(query, (processed_video_id,))
        duration = results[0]['duration']
        
        # Get frame count
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'frame'
        """
        results = db.execute_query(query, (processed_video_id,))
        frame_count = results[0]['count']
        
        # Expected: at least 1 frame per 5 seconds (conservative estimate)
        min_expected_frames = max(1, int(duration / 5))
        
        assert frame_count >= min_expected_frames, \
            f"Expected at least {min_expected_frames} frames for {duration}s video, got {frame_count}"
        
        print(f"\n✓ Video has {frame_count} frames (duration: {duration}s)")

    
    def test_video_has_captions_for_frames(self, db, processed_video_id):
        """Test that video has captions matching frame count."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        # Get frame count
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'frame'
        """
        results = db.execute_query(query, (processed_video_id,))
        frame_count = results[0]['count']
        
        # Get caption count
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'caption'
        """
        results = db.execute_query(query, (processed_video_id,))
        caption_count = results[0]['count']
        
        # Should have captions for most frames (allow some tolerance)
        min_expected_captions = max(1, int(frame_count * 0.8))
        
        assert caption_count >= min_expected_captions, \
            f"Expected at least {min_expected_captions} captions for {frame_count} frames, got {caption_count}"
        
        print(f"\n✓ Video has {caption_count} captions for {frame_count} frames")
    
    def test_video_has_transcript_segments(self, db, processed_video_id):
        """Test that video has transcript segments."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'transcript'
        """
        results = db.execute_query(query, (processed_video_id,))
        transcript_count = results[0]['count']
        
        # Should have at least 1 transcript segment
        assert transcript_count > 0, \
            f"Expected at least 1 transcript segment, got {transcript_count}"
        
        print(f"\n✓ Video has {transcript_count} transcript segments")
    
    def test_video_has_object_detections(self, db, processed_video_id):
        """Test that video has object detections."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT COUNT(*) as count FROM video_context 
            WHERE video_id = ? AND context_type = 'object'
        """
        results = db.execute_query(query, (processed_video_id,))
        object_count = results[0]['count']
        
        # Should have at least 1 object detection
        assert object_count > 0, \
            f"Expected at least 1 object detection, got {object_count}"
        
        print(f"\n✓ Video has {object_count} object detections")

    
    def test_all_context_has_valid_json(self, db, processed_video_id):
        """Test that all context data is valid JSON."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT context_id, context_type, data FROM video_context 
            WHERE video_id = ?
        """
        results = db.execute_query(query, (processed_video_id,))
        
        assert len(results) > 0, "No context data found"
        
        invalid_count = 0
        for row in results:
            try:
                json.loads(row['data'])
            except json.JSONDecodeError:
                invalid_count += 1
                print(f"  ✗ Invalid JSON in {row['context_type']}: {row['context_id']}")
        
        assert invalid_count == 0, f"Found {invalid_count} invalid JSON entries"
        print(f"\n✓ All {len(results)} context entries have valid JSON")
    
    def test_frames_have_timestamps(self, db, processed_video_id):
        """Test that all frames have valid timestamps."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT timestamp FROM video_context 
            WHERE video_id = ? AND context_type = 'frame'
        """
        results = db.execute_query(query, (processed_video_id,))
        
        assert len(results) > 0, "No frames found"
        
        for row in results:
            timestamp = row['timestamp']
            assert timestamp is not None, "Frame has null timestamp"
            assert timestamp >= 0, f"Frame has negative timestamp: {timestamp}"
        
        print(f"\n✓ All {len(results)} frames have valid timestamps")
    
    def test_captions_have_text(self, db, processed_video_id):
        """Test that all captions have text content."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT data FROM video_context 
            WHERE video_id = ? AND context_type = 'caption'
        """
        results = db.execute_query(query, (processed_video_id,))
        
        assert len(results) > 0, "No captions found"
        
        empty_count = 0
        for row in results:
            data = json.loads(row['data'])
            text = data.get('text', '')
            if not text or len(text.strip()) == 0:
                empty_count += 1
        
        assert empty_count == 0, f"Found {empty_count} empty captions"
        print(f"\n✓ All {len(results)} captions have text content")

    
    def test_transcripts_have_text(self, db, processed_video_id):
        """Test that all transcripts have text content."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT data FROM video_context 
            WHERE video_id = ? AND context_type = 'transcript'
        """
        results = db.execute_query(query, (processed_video_id,))
        
        assert len(results) > 0, "No transcripts found"
        
        empty_count = 0
        for row in results:
            data = json.loads(row['data'])
            text = data.get('text', '')
            if not text or len(text.strip()) == 0:
                empty_count += 1
        
        assert empty_count == 0, f"Found {empty_count} empty transcripts"
        print(f"\n✓ All {len(results)} transcripts have text content")
    
    def test_objects_have_class_names(self, db, processed_video_id):
        """Test that all object detections have class names."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        query = """
            SELECT data FROM video_context 
            WHERE video_id = ? AND context_type = 'object'
        """
        results = db.execute_query(query, (processed_video_id,))
        
        assert len(results) > 0, "No objects found"
        
        missing_class_count = 0
        for row in results:
            data = json.loads(row['data'])
            if 'objects' in data:
                for obj in data['objects']:
                    if not obj.get('class_name'):
                        missing_class_count += 1
            elif not data.get('class_name'):
                missing_class_count += 1
        
        assert missing_class_count == 0, f"Found {missing_class_count} objects without class names"
        print(f"\n✓ All object detections have class names")
    
    def test_no_missing_data_after_processing(self, db, video_service, processed_video_id):
        """Test comprehensive data completeness check."""
        if not processed_video_id:
            pytest.skip("No processed video available")
        
        # Use video service to verify data
        status = video_service.verify_video_data(processed_video_id)
        
        print(f"\n{'='*60}")
        print(f"Data Completeness Report for {processed_video_id[:8]}...")
        print(f"{'='*60}")
        print(f"Frames: {status['frames']['count']} ({'✓' if status['frames']['complete'] else '✗'})")
        print(f"Captions: {status['captions']['count']} ({'✓' if status['captions']['complete'] else '✗'})")
        print(f"Transcripts: {status['transcripts']['count']} ({'✓' if status['transcripts']['complete'] else '✗'})")
        print(f"Objects: {status['objects']['count']} ({'✓' if status['objects']['complete'] else '✗'})")
        print(f"Overall: {'✓ COMPLETE' if status['complete'] else '✗ INCOMPLETE'}")
        print(f"{'='*60}\n")
        
        assert status['complete'], f"Video data is incomplete: {status}"
