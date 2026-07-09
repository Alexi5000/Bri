"""Test script for Context Builder functionality."""

import sys
import os
import json
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.context import ContextBuilder, VideoContext, TimestampContext
from models.video import VideoMetadata, Frame
from models.tools import Caption, Transcript, TranscriptSegment, DetectionResult, DetectedObject
from storage.database import Database
from config import Config


def setup_test_data(db: Database, video_id: str) -> None:
    """Set up test data in the database."""
    print(f"\n{'='*60}")
    print("Setting up test data...")
    print(f"{'='*60}")
    
    # Insert video record
    db.execute_update(
        """
        INSERT OR REPLACE INTO videos (video_id, filename, file_path, duration, processing_status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (video_id, "test_video.mp4", "/data/videos/test_video.mp4", 60.0, "complete")
    )
    print(f"✓ Created video record: {video_id}")
    
    # Insert metadata
    metadata = VideoMetadata(
        duration=60.0,
        fps=30.0,
        width=1920,
        height=1080,
        codec="h264",
        file_size=10485760
    )
    db.execute_update(
        """
        INSERT INTO video_context (context_id, video_id, context_type, data)
        VALUES (?, ?, ?, ?)
        """,
        (f"ctx_{uuid.uuid4().hex[:16]}", video_id, "metadata", json.dumps(metadata.model_dump()))
    )
    print("✓ Inserted video metadata")
    
    # Insert frames
    frames_data = [
        Frame(timestamp=5.0, image_path="/data/frames/frame_5.jpg", frame_number=150),
        Frame(timestamp=10.0, image_path="/data/frames/frame_10.jpg", frame_number=300),
        Frame(timestamp=15.0, image_path="/data/frames/frame_15.jpg", frame_number=450),
        Frame(timestamp=20.0, image_path="/data/frames/frame_20.jpg", frame_number=600),
    ]
    for frame in frames_data:
        db.execute_update(
            """
            INSERT INTO video_context (context_id, video_id, context_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (f"ctx_{uuid.uuid4().hex[:16]}", video_id, "frame", frame.timestamp, json.dumps(frame.model_dump()))
        )
    print(f"✓ Inserted {len(frames_data)} frames")
    
    # Insert captions
    captions_data = [
        Caption(frame_timestamp=5.0, text="a person walking in a park", confidence=0.95),
        Caption(frame_timestamp=10.0, text="a dog running on grass", confidence=0.92),
        Caption(frame_timestamp=15.0, text="a person throwing a ball", confidence=0.88),
        Caption(frame_timestamp=20.0, text="a dog catching a ball", confidence=0.90),
    ]
    for caption in captions_data:
        db.execute_update(
            """
            INSERT INTO video_context (context_id, video_id, context_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (f"ctx_{uuid.uuid4().hex[:16]}", video_id, "caption", caption.frame_timestamp, json.dumps(caption.model_dump()))
        )
    print(f"✓ Inserted {len(captions_data)} captions")
    
    # Insert transcript
    transcript = Transcript(
        segments=[
            TranscriptSegment(start=3.0, end=7.0, text="Look at that beautiful park", confidence=0.94),
            TranscriptSegment(start=8.0, end=12.0, text="The dog is so happy running around", confidence=0.96),
            TranscriptSegment(start=14.0, end=18.0, text="Let's play fetch with the ball", confidence=0.93),
            TranscriptSegment(start=19.0, end=23.0, text="Good catch buddy", confidence=0.95),
        ],
        language="en",
        full_text="Look at that beautiful park. The dog is so happy running around. Let's play fetch with the ball. Good catch buddy."
    )
    db.execute_update(
        """
        INSERT INTO video_context (context_id, video_id, context_type, data)
        VALUES (?, ?, ?, ?)
        """,
        (f"ctx_{uuid.uuid4().hex[:16]}", video_id, "transcript", json.dumps(transcript.model_dump()))
    )
    print(f"✓ Inserted transcript with {len(transcript.segments)} segments")
    
    # Insert object detections
    detections_data = [
        DetectionResult(
            frame_timestamp=5.0,
            objects=[
                DetectedObject(class_name="person", confidence=0.96, bbox=(100, 200, 150, 300)),
            ]
        ),
        DetectionResult(
            frame_timestamp=10.0,
            objects=[
                DetectedObject(class_name="dog", confidence=0.94, bbox=(300, 400, 100, 150)),
                DetectedObject(class_name="person", confidence=0.92, bbox=(500, 200, 150, 300)),
            ]
        ),
        DetectionResult(
            frame_timestamp=15.0,
            objects=[
                DetectedObject(class_name="person", confidence=0.95, bbox=(100, 200, 150, 300)),
                DetectedObject(class_name="sports ball", confidence=0.88, bbox=(600, 300, 50, 50)),
            ]
        ),
        DetectionResult(
            frame_timestamp=20.0,
            objects=[
                DetectedObject(class_name="dog", confidence=0.97, bbox=(350, 380, 120, 160)),
                DetectedObject(class_name="sports ball", confidence=0.91, bbox=(400, 350, 50, 50)),
            ]
        ),
    ]
    for detection in detections_data:
        db.execute_update(
            """
            INSERT INTO video_context (context_id, video_id, context_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (f"ctx_{uuid.uuid4().hex[:16]}", video_id, "object", detection.frame_timestamp, json.dumps(detection.model_dump()))
        )
    print(f"✓ Inserted {len(detections_data)} object detection results")


def test_build_video_context(builder: ContextBuilder, video_id: str) -> None:
    """Test building complete video context."""
    print(f"\n{'='*60}")
    print("TEST: build_video_context")
    print(f"{'='*60}")
    
    context = builder.build_video_context(video_id, include_conversation=False)
    
    print(f"Video ID: {context.video_id}")
    print(f"Metadata: {context.metadata}")
    print(f"Frames: {len(context.frames)}")
    print(f"Captions: {len(context.captions)}")
    print(f"Transcript segments: {len(context.transcript.segments) if context.transcript else 0}")
    print(f"Object detections: {len(context.objects)}")
    
    assert context.video_id == video_id
    assert context.metadata is not None
    assert len(context.frames) == 4
    assert len(context.captions) == 4
    assert context.transcript is not None
    assert len(context.transcript.segments) == 4
    assert len(context.objects) == 4
    
    print("✓ All assertions passed")


def test_search_captions(builder: ContextBuilder, video_id: str) -> None:
    """Test caption search functionality."""
    print(f"\n{'='*60}")
    print("TEST: search_captions")
    print(f"{'='*60}")
    
    # Test 1: Search for "dog"
    print("\nSearching for 'dog'...")
    results = builder.search_captions(video_id, "dog", top_k=5)
    print(f"Found {len(results)} results:")
    for caption in results:
        print(f"  - {caption.frame_timestamp}s: {caption.text}")
    assert len(results) >= 2  # Should find at least 2 captions with "dog"
    print("✓ Found expected results for 'dog'")
    
    # Test 2: Search for "ball"
    print("\nSearching for 'ball'...")
    results = builder.search_captions(video_id, "ball", top_k=5)
    print(f"Found {len(results)} results:")
    for caption in results:
        print(f"  - {caption.frame_timestamp}s: {caption.text}")
    assert len(results) >= 2  # Should find at least 2 captions with "ball"
    print("✓ Found expected results for 'ball'")
    
    # Test 3: Search for "person walking"
    print("\nSearching for 'person walking'...")
    results = builder.search_captions(video_id, "person walking", top_k=3)
    print(f"Found {len(results)} results:")
    for caption in results:
        print(f"  - {caption.frame_timestamp}s: {caption.text}")
    assert len(results) >= 1
    print("✓ Found expected results for 'person walking'")


def test_search_transcripts(builder: ContextBuilder, video_id: str) -> None:
    """Test transcript search functionality."""
    print(f"\n{'='*60}")
    print("TEST: search_transcripts")
    print(f"{'='*60}")
    
    # Test 1: Search for "dog"
    print("\nSearching for 'dog'...")
    results = builder.search_transcripts(video_id, "dog")
    print(f"Found {len(results)} segments:")
    for segment in results:
        print(f"  - {segment.start}s-{segment.end}s: {segment.text}")
    assert len(results) >= 1
    print("✓ Found expected segments for 'dog'")
    
    # Test 2: Search for "park"
    print("\nSearching for 'park'...")
    results = builder.search_transcripts(video_id, "park")
    print(f"Found {len(results)} segments:")
    for segment in results:
        print(f"  - {segment.start}s-{segment.end}s: {segment.text}")
    assert len(results) >= 1
    print("✓ Found expected segments for 'park'")
    
    # Test 3: Search for "ball"
    print("\nSearching for 'ball'...")
    results = builder.search_transcripts(video_id, "ball")
    print(f"Found {len(results)} segments:")
    for segment in results:
        print(f"  - {segment.start}s-{segment.end}s: {segment.text}")
    assert len(results) >= 1
    print("✓ Found expected segments for 'ball'")


def test_get_frames_with_object(builder: ContextBuilder, video_id: str) -> None:
    """Test finding frames with specific objects."""
    print(f"\n{'='*60}")
    print("TEST: get_frames_with_object")
    print(f"{'='*60}")
    
    # Test 1: Search for "dog"
    print("\nSearching for frames with 'dog'...")
    frames = builder.get_frames_with_object(video_id, "dog")
    print(f"Found {len(frames)} frames:")
    for frame in frames:
        print(f"  - Frame at {frame.timestamp}s")
    assert len(frames) == 2  # Dog appears at 10s and 20s
    print("✓ Found expected frames with 'dog'")
    
    # Test 2: Search for "person"
    print("\nSearching for frames with 'person'...")
    frames = builder.get_frames_with_object(video_id, "person")
    print(f"Found {len(frames)} frames:")
    for frame in frames:
        print(f"  - Frame at {frame.timestamp}s")
    assert len(frames) == 3  # Person appears at 5s, 10s, and 15s
    print("✓ Found expected frames with 'person'")
    
    # Test 3: Search for "ball"
    print("\nSearching for frames with 'ball'...")
    frames = builder.get_frames_with_object(video_id, "ball")
    print(f"Found {len(frames)} frames:")
    for frame in frames:
        print(f"  - Frame at {frame.timestamp}s")
    assert len(frames) == 2  # Ball appears at 15s and 20s
    print("✓ Found expected frames with 'ball'")


def test_get_context_at_timestamp(builder: ContextBuilder, video_id: str) -> None:
    """Test getting context at specific timestamp."""
    print(f"\n{'='*60}")
    print("TEST: get_context_at_timestamp")
    print(f"{'='*60}")
    
    # Test 1: Context at 10s with 3s window
    print("\nGetting context at 10s (±3s window)...")
    context = builder.get_context_at_timestamp(video_id, 10.0, window=3.0)
    print(f"Timestamp: {context.timestamp}s")
    print(f"Nearby frames: {len(context.nearby_frames)}")
    print(f"Captions: {len(context.captions)}")
    print(f"Transcript segment: {context.transcript_segment.text if context.transcript_segment else 'None'}")
    print(f"Detected objects: {len(context.detected_objects)}")
    
    assert context.timestamp == 10.0
    assert len(context.nearby_frames) >= 1  # Should have frame at 10s
    assert len(context.captions) >= 1
    assert context.transcript_segment is not None
    print("✓ Context retrieved successfully")
    
    # Test 2: Context at 15s with 5s window
    print("\nGetting context at 15s (±5s window)...")
    context = builder.get_context_at_timestamp(video_id, 15.0, window=5.0)
    print(f"Timestamp: {context.timestamp}s")
    print(f"Nearby frames: {len(context.nearby_frames)}")
    print(f"Captions: {len(context.captions)}")
    print(f"Transcript segment: {context.transcript_segment.text if context.transcript_segment else 'None'}")
    print(f"Detected objects: {len(context.detected_objects)}")
    
    assert context.timestamp == 15.0
    assert len(context.nearby_frames) >= 2  # Should have frames at 10s, 15s, 20s
    print("✓ Context retrieved successfully")


def main():
    """Run all Context Builder tests."""
    print("\n" + "="*60)
    print("CONTEXT BUILDER TEST SUITE")
    print("="*60)
    
    # Initialize database with test path
    test_db_path = "data/test_context.db"
    db = Database(test_db_path)
    db.connect()
    db.initialize_schema()
    
    # Generate test video ID
    video_id = f"test_vid_{uuid.uuid4().hex[:8]}"
    
    try:
        # Set up test data
        setup_test_data(db, video_id)
        
        # Initialize Context Builder
        builder = ContextBuilder(db)
        
        # Run tests
        test_build_video_context(builder, video_id)
        test_search_captions(builder, video_id)
        test_search_transcripts(builder, video_id)
        test_get_frames_with_object(builder, video_id)
        test_get_context_at_timestamp(builder, video_id)
        
        print(f"\n{'='*60}")
        print("✓ ALL TESTS PASSED")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ TEST FAILED: {e}")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Clean up
        db.close()


if __name__ == "__main__":
    main()
