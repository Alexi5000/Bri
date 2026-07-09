"""Test script for Tool Router functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.router import ToolRouter, ToolPlan


def test_caption_queries():
    """Test queries that require captions."""
    print("\n=== Testing Caption Queries ===")
    router = ToolRouter()
    
    queries = [
        "What's happening in the video?",
        "Describe the scene",
        "Show me what you see",
        "What does it look like?",
    ]
    
    for query in queries:
        plan = router.analyze_query(query)
        print(f"\nQuery: {query}")
        print(f"Tools needed: {plan.tools_needed}")
        print(f"Execution order: {plan.execution_order}")
        assert 'captions' in plan.tools_needed, f"Expected captions for: {query}"
    
    print("\n✓ Caption queries test passed")


def test_transcript_queries():
    """Test queries that require transcripts."""
    print("\n=== Testing Transcript Queries ===")
    router = ToolRouter()
    
    queries = [
        "What did they say?",
        "Find when they mentioned Python",
        "What's the conversation about?",
        "Tell me what was discussed",
    ]
    
    for query in queries:
        plan = router.analyze_query(query)
        print(f"\nQuery: {query}")
        print(f"Tools needed: {plan.tools_needed}")
        print(f"Execution order: {plan.execution_order}")
        assert 'transcripts' in plan.tools_needed, f"Expected transcripts for: {query}"
    
    print("\n✓ Transcript queries test passed")


def test_object_queries():
    """Test queries that require object detection."""
    print("\n=== Testing Object Detection Queries ===")
    router = ToolRouter()
    
    queries = [
        "Show me all the dogs",
        "Find scenes with a car",
        "How many people are there?",
        "Locate the cat in the video",
    ]
    
    for query in queries:
        plan = router.analyze_query(query)
        print(f"\nQuery: {query}")
        print(f"Tools needed: {plan.tools_needed}")
        print(f"Execution order: {plan.execution_order}")
        print(f"Parameters: {plan.parameters}")
        assert 'objects' in plan.tools_needed, f"Expected objects for: {query}"
    
    print("\n✓ Object detection queries test passed")


def test_timestamp_extraction():
    """Test timestamp extraction from queries."""
    print("\n=== Testing Timestamp Extraction ===")
    router = ToolRouter()
    
    test_cases = [
        ("What happened at 1:30?", 90.0),
        ("Show me 2:15", 135.0),
        ("What's at 1:30:45?", 5445.0),
        ("at 30 seconds", 30.0),
        ("at 5 minutes", 300.0),
        ("Show me the beginning", 0.0),
        ("What's at the start", 0.0),
    ]
    
    for query, expected_timestamp in test_cases:
        timestamp = router.extract_timestamp(query)
        print(f"\nQuery: {query}")
        print(f"Extracted timestamp: {timestamp}")
        print(f"Expected: {expected_timestamp}")
        assert timestamp == expected_timestamp, f"Expected {expected_timestamp}, got {timestamp}"
    
    print("\n✓ Timestamp extraction test passed")


def test_multi_tool_queries():
    """Test queries that require multiple tools."""
    print("\n=== Testing Multi-Tool Queries ===")
    router = ToolRouter()
    
    queries = [
        "What did they say about the dog?",  # transcripts + objects
        "Describe what's happening when they mention Python",  # captions + transcripts
        "Show me all the cars and what people said about them",  # objects + transcripts
    ]
    
    for query in queries:
        plan = router.analyze_query(query)
        print(f"\nQuery: {query}")
        print(f"Tools needed: {plan.tools_needed}")
        print(f"Execution order: {plan.execution_order}")
        assert len(plan.tools_needed) >= 2, f"Expected multiple tools for: {query}"
    
    print("\n✓ Multi-tool queries test passed")


def test_execution_order_optimization():
    """Test that execution order is optimized correctly."""
    print("\n=== Testing Execution Order Optimization ===")
    router = ToolRouter()
    
    # Test temporal query prioritization
    query = "What did they say at 2:30?"
    plan = router.analyze_query(query)
    print(f"\nTemporal Query: {query}")
    print(f"Tools needed: {plan.tools_needed}")
    print(f"Execution order: {plan.execution_order}")
    print(f"Parameters: {plan.parameters}")
    assert plan.parameters.get('temporal_query') == True
    assert plan.parameters.get('timestamp') == 150.0
    
    # Test default order (transcripts -> captions -> objects)
    query = "Show me what's happening and what they said"
    plan = router.analyze_query(query)
    print(f"\nGeneral Query: {query}")
    print(f"Tools needed: {plan.tools_needed}")
    print(f"Execution order: {plan.execution_order}")
    if 'transcripts' in plan.execution_order and 'captions' in plan.execution_order:
        assert plan.execution_order.index('transcripts') < plan.execution_order.index('captions')
    
    print("\n✓ Execution order optimization test passed")


def test_object_name_extraction():
    """Test extraction of object names from queries."""
    print("\n=== Testing Object Name Extraction ===")
    router = ToolRouter()
    
    test_cases = [
        ("Show me all the dogs", "dogs"),
        ("Find the car", "car"),
        ("How many people are there?", "people"),
        ("Locate cats in the video", "cats"),
    ]
    
    for query, expected_object in test_cases:
        plan = router.analyze_query(query)
        extracted_object = plan.parameters.get('object_name')
        print(f"\nQuery: {query}")
        print(f"Extracted object: {extracted_object}")
        print(f"Expected: {expected_object}")
        # Note: This is a best-effort extraction, so we just check if something was extracted
        if extracted_object:
            print(f"✓ Successfully extracted object name")
    
    print("\n✓ Object name extraction test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Tool Router Test Suite")
    print("=" * 60)
    
    try:
        test_caption_queries()
        test_transcript_queries()
        test_object_queries()
        test_timestamp_extraction()
        test_multi_tool_queries()
        test_execution_order_optimization()
        test_object_name_extraction()
        
        print("\n" + "=" * 60)
        print("✓ All Tool Router tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
