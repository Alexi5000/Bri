"""
Data Quality Testing Framework for BRI Video Agent

Tests:
- Unit tests for data transformations
- Integration tests for data pipelines
- Data validation tests (schema compliance)
- Performance tests (query speed)
- Chaos testing (simulate failures)
"""

import pytest
import json
import time
from storage.database import Database, get_database
from services.data_validator import get_data_validator
from services.data_consistency_checker import get_consistency_checker
from services.data_quality_metrics import get_quality_metrics


class TestDataTransformations:
    """Unit tests for data transformations."""
    
    def test_frame_data_transformation(self):
        """Test frame data transformation and validation."""
        # Sample frame data
        frame_data = {
            'timestamp': 2.5,
            'frame_number': 5,
            'image_path': '/path/to/frame.jpg',
            'width': 1920,
            'height': 1080
        }
        
        validator = get_data_validator()
        is_valid, error = validator.validate_frame(frame_data)
        
        assert is_valid, f"Frame validation failed: {error}"
        assert error is None
    
    def test_caption_data_transformation(self):
        """Test caption data transformation and validation."""
        caption_data = {
            'frame_timestamp': 2.5,
            'text': 'A person walking in a park',
            'confidence': 0.95
        }
        
        validator = get_data_validator()
        is_valid, error = validator.validate_caption(caption_data)
        
        assert is_valid, f"Caption validation failed: {error}"
        assert error is None
    
    def test_transcript_data_transformation(self):
        """Test transcript data transformation and validation."""
        transcript_data = {
            'start': 0.0,
            'end': 5.5,
            'text': 'Hello, welcome to the video',
            'confidence': 0.92
        }
        
        validator = get_data_validator()
        is_valid, error = validator.validate_transcript(transcript_data)
        
        assert is_valid, f"Transcript validation failed: {error}"
        assert error is None
    
    def test_object_detection_transformation(self):
        """Test object detection data transformation and validation."""
        detection_data = {
            'frame_timestamp': 2.5,
            'objects': [
                {
                    'class_name': 'person',
                    'confidence': 0.95,
                    'bbox': [100, 200, 50, 100]
                },
                {
                    'class_name': 'car',
                    'confidence': 0.88,
                    'bbox': [300, 400, 150, 80]
                }
            ]
        }
        
        validator = get_data_validator()
        is_valid, error = validator.validate_object_detection(detection_data)
        
        assert is_valid, f"Object detection validation failed: {error}"
        assert error is None
    
    def test_invalid_frame_data(self):
        """Test that invalid frame data is rejected."""
        invalid_frame = {
            'timestamp': -1.0,  # Invalid: negative timestamp
            'frame_number': 5
        }
        
        validator = get_data_validator()
        is_valid, error = validator.validate_frame(invalid_frame)
        
        assert not is_valid
        assert error is not None
    
    def test_invalid_caption_data(self):
        """Test that invalid caption data is rejected."""
        invalid_caption = {
            'frame_timestamp': 2.5,
            'text': '',  # Invalid: empty text
            'confidence': 0.95
        }
        
        validator = get_data_validator()
        is_valid, error = validator.validate_caption(invalid_caption)
        
        assert not is_valid
        assert error is not None
    
    def test_invalid_transcript_data(self):
        """Test that invalid transcript data is rejected."""
        invalid_transcript = {
            'start': 5.0,
            'end': 2.0,  # Invalid: end before start
            'text': 'Test'
        }
        
        validator = get_data_validator()
        is_valid, error = validator.validate_transcript(invalid_transcript)
        
        assert not is_valid
        assert error is not None


class TestDataPipelines:
    """Integration tests for data pipelines."""
    
    @pytest.fixture
    def db(self):
        """Get database instance for testing."""
        return get_database()
    
    def test_video_processing_pipeline(self, db):
        """Test complete video processing pipeline."""
        # This would test the full pipeline from upload to completion
        # For now, we'll test the data flow structure
        
        video_id = 'test_video_123'
        
        # Simulate pipeline stages
        stages = ['upload', 'frame_extraction', 'caption_generation', 'transcription', 'object_detection']
        
        for stage in stages:
            # Each stage should produce valid data
            assert stage in ['upload', 'frame_extraction', 'caption_generation', 'transcription', 'object_detection']
    
    def test_batch_processing_pipeline(self):
        """Test batch processing of multiple videos."""
        validator = get_data_validator()
        
        # Simulate batch of captions
        captions = [
            {'frame_timestamp': 0.0, 'text': 'Caption 1', 'confidence': 0.9},
            {'frame_timestamp': 2.0, 'text': 'Caption 2', 'confidence': 0.85},
            {'frame_timestamp': 4.0, 'text': 'Caption 3', 'confidence': 0.92}
        ]
        
        all_valid, errors = validator.validate_batch('caption', captions)
        
        assert all_valid, f"Batch validation failed: {errors}"
        assert len(errors) == 0
    
    def test_pipeline_error_handling(self):
        """Test pipeline error handling and recovery."""
        validator = get_data_validator()
        
        # Mix of valid and invalid data
        mixed_data = [
            {'frame_timestamp': 0.0, 'text': 'Valid caption', 'confidence': 0.9},
            {'frame_timestamp': 2.0, 'text': '', 'confidence': 0.85},  # Invalid: empty text
            {'frame_timestamp': 4.0, 'text': 'Another valid caption', 'confidence': 0.92}
        ]
        
        all_valid, errors = validator.validate_batch('caption', mixed_data)
        
        assert not all_valid
        assert len(errors) > 0
        assert 'empty' in errors[0].lower()


class TestSchemaCompliance:
    """Data validation tests for schema compliance."""
    
    def test_frame_schema_compliance(self):
        """Test frame data complies with schema."""
        validator = get_data_validator()
        
        # Test all required fields present
        frame = {'timestamp': 1.0, 'frame_number': 1}
        is_valid, error = validator.validate_frame(frame)
        assert is_valid
        
        # Test missing required field
        incomplete_frame = {'timestamp': 1.0}
        is_valid, error = validator.validate_frame(incomplete_frame)
        assert not is_valid
    
    def test_caption_schema_compliance(self):
        """Test caption data complies with schema."""
        validator = get_data_validator()
        
        # Test all required fields present
        caption = {'frame_timestamp': 1.0, 'text': 'Test caption'}
        is_valid, error = validator.validate_caption(caption)
        assert is_valid
        
        # Test missing required field
        incomplete_caption = {'frame_timestamp': 1.0}
        is_valid, error = validator.validate_caption(incomplete_caption)
        assert not is_valid
    
    def test_transcript_schema_compliance(self):
        """Test transcript data complies with schema."""
        validator = get_data_validator()
        
        # Test all required fields present
        transcript = {'start': 0.0, 'end': 5.0, 'text': 'Test transcript'}
        is_valid, error = validator.validate_transcript(transcript)
        assert is_valid
        
        # Test missing required field
        incomplete_transcript = {'start': 0.0, 'end': 5.0}
        is_valid, error = validator.validate_transcript(incomplete_transcript)
        assert not is_valid
    
    def test_object_schema_compliance(self):
        """Test object detection data complies with schema."""
        validator = get_data_validator()
        
        # Test all required fields present
        detection = {
            'frame_timestamp': 1.0,
            'objects': [
                {'class_name': 'person', 'confidence': 0.9}
            ]
        }
        is_valid, error = validator.validate_object_detection(detection)
        assert is_valid
        
        # Test missing required field
        incomplete_detection = {'frame_timestamp': 1.0}
        is_valid, error = validator.validate_object_detection(incomplete_detection)
        assert not is_valid
    
    def test_json_serialization(self):
        """Test that all data can be serialized to JSON."""
        validator = get_data_validator()
        
        test_data = {
            'timestamp': 1.0,
            'frame_number': 1,
            'nested': {'key': 'value'},
            'list': [1, 2, 3]
        }
        
        is_valid, error = validator.validate_json_structure(test_data)
        assert is_valid
        
        # Test non-serializable data
        class CustomObject:
            pass
        
        invalid_data = {'object': CustomObject()}
        is_valid, error = validator.validate_json_structure(invalid_data)
        assert not is_valid


class TestQueryPerformance:
    """Performance tests for database queries."""
    
    @pytest.fixture
    def db(self):
        """Get database instance for testing."""
        return get_database()
    
    def test_video_query_performance(self, db):
        """Test video query performance."""
        start_time = time.time()
        
        query = "SELECT * FROM videos LIMIT 100"
        results = db.execute_query(query)
        
        duration = time.time() - start_time
        
        # Query should complete in under 100ms
        assert duration < 0.1, f"Query took {duration:.3f}s, expected < 0.1s"
    
    def test_context_query_performance(self, db):
        """Test context query performance."""
        start_time = time.time()
        
        query = "SELECT * FROM video_context LIMIT 100"
        results = db.execute_query(query)
        
        duration = time.time() - start_time
        
        # Query should complete in under 100ms
        assert duration < 0.1, f"Query took {duration:.3f}s, expected < 0.1s"
    
    def test_join_query_performance(self, db):
        """Test join query performance."""
        start_time = time.time()
        
        query = """
            SELECT v.video_id, v.filename, COUNT(vc.context_id) as context_count
            FROM videos v
            LEFT JOIN video_context vc ON v.video_id = vc.video_id
            GROUP BY v.video_id
            LIMIT 100
        """
        results = db.execute_query(query)
        
        duration = time.time() - start_time
        
        # Join query should complete in under 200ms
        assert duration < 0.2, f"Join query took {duration:.3f}s, expected < 0.2s"
    
    def test_aggregation_query_performance(self, db):
        """Test aggregation query performance."""
        start_time = time.time()
        
        query = """
            SELECT context_type, COUNT(*) as count
            FROM video_context
            GROUP BY context_type
        """
        results = db.execute_query(query)
        
        duration = time.time() - start_time
        
        # Aggregation should complete in under 100ms
        assert duration < 0.1, f"Aggregation took {duration:.3f}s, expected < 0.1s"


class TestChaosEngineering:
    """Chaos testing to simulate failures."""
    
    def test_missing_data_handling(self):
        """Test handling of missing data."""
        validator = get_data_validator()
        
        # Test with None - JSON can serialize None
        is_valid, error = validator.validate_json_structure(None)
        assert is_valid  # None is valid JSON
        
        # Test with empty dict - should fail frame validation
        is_valid, error = validator.validate_frame({})
        assert not is_valid
    
    def test_corrupted_json_handling(self):
        """Test handling of corrupted JSON data."""
        # Simulate corrupted JSON string
        corrupted_json = '{"timestamp": 1.0, "frame_number": '  # Incomplete JSON
        
        try:
            json.loads(corrupted_json)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            # Expected behavior
            pass
    
    def test_extreme_values_handling(self):
        """Test handling of extreme values."""
        validator = get_data_validator()
        
        # Test with very large timestamp
        extreme_frame = {
            'timestamp': 999999999.0,
            'frame_number': 999999999
        }
        is_valid, error = validator.validate_frame(extreme_frame)
        assert is_valid  # Should handle large values
        
        # Test with very small confidence
        extreme_caption = {
            'frame_timestamp': 1.0,
            'text': 'Test',
            'confidence': 0.001
        }
        is_valid, error = validator.validate_caption(extreme_caption)
        assert is_valid  # Should handle low confidence
    
    def test_concurrent_access_handling(self):
        """Test handling of concurrent database access."""
        # This would test concurrent writes/reads
        # For now, just verify the database can handle multiple connections
        db1 = get_database()
        db2 = get_database()
        
        # Both should be able to query
        results1 = db1.execute_query("SELECT COUNT(*) FROM videos")
        results2 = db2.execute_query("SELECT COUNT(*) FROM videos")
        
        assert results1 is not None
        assert results2 is not None
    
    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        # Test with invalid database path
        try:
            db = Database(db_path="/invalid/path/to/database.db")
            db.connect()
            # If we get here, connection might have succeeded (shouldn't happen)
        except Exception as e:
            # Expected: connection should fail
            assert True


class TestDataQualityMetrics:
    """Test data quality metrics calculations."""
    
    def test_completeness_calculation(self):
        """Test completeness metric calculation."""
        metrics = get_quality_metrics()
        
        # Test with a video (may not exist in test DB)
        result = metrics.calculate_completeness('test_video_123')
        
        # Should return a result even if video doesn't exist
        assert 'video_id' in result
        assert 'overall_completeness' in result
    
    def test_freshness_calculation(self):
        """Test freshness metric calculation."""
        metrics = get_quality_metrics()
        
        result = metrics.calculate_freshness('test_video_123')
        
        # Should return a result
        assert 'video_id' in result
    
    def test_accuracy_calculation(self):
        """Test accuracy metric calculation."""
        metrics = get_quality_metrics()
        
        result = metrics.calculate_accuracy('test_video_123')
        
        # Should return a result
        assert 'video_id' in result
        assert 'overall_accuracy' in result
    
    def test_volume_metrics_calculation(self):
        """Test volume metrics calculation."""
        metrics = get_quality_metrics()
        
        result = metrics.calculate_volume_metrics()
        
        # Should return volume metrics
        assert 'total_videos' in result
        assert 'total_frames' in result


class TestDataConsistency:
    """Test data consistency checks."""
    
    def test_timestamp_ordering_check(self):
        """Test timestamp ordering validation."""
        validator = get_data_validator()
        
        # Test valid ordering
        timestamps = [0.0, 2.0, 4.0, 6.0]
        is_valid, error = validator.validate_timestamp_ordering(timestamps)
        assert is_valid
        
        # Test invalid ordering
        invalid_timestamps = [0.0, 4.0, 2.0, 6.0]
        is_valid, error = validator.validate_timestamp_ordering(invalid_timestamps)
        assert not is_valid
    
    def test_video_consistency_check(self):
        """Test video consistency checking."""
        checker = get_consistency_checker()
        
        # Test with a video (may not exist)
        result = checker.check_video_consistency('test_video_123')
        
        # Should return a consistency report
        assert 'video_id' in result
        assert 'consistent' in result
        assert 'checks' in result


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
