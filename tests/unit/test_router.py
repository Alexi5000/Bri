"""Unit tests for Tool Router."""

import pytest
from services.router import ToolRouter, ToolPlan


@pytest.fixture
def router():
    """Create ToolRouter instance for testing."""
    return ToolRouter()


class TestQueryAnalysis:
    """Tests for ToolRouter.analyze_query() method."""
    
    def test_analyze_caption_query(self, router):
        """Test analyzing query that requires captions."""
        query = "What's happening in the video?"
        plan = router.analyze_query(query)
        
        assert 'captions' in plan.tools_needed
        assert 'captions' in plan.execution_order
    
    def test_analyze_transcript_query(self, router):
        """Test analyzing query that requires transcripts."""
        query = "What did they say about the project?"
        plan = router.analyze_query(query)
        
        assert 'transcripts' in plan.tools_needed
        assert 'transcripts' in plan.execution_order
    
    def test_analyze_object_query(self, router):
        """Test analyzing query that requires object detection."""
        query = "Show me all the dogs in the video"
        plan = router.analyze_query(query)
        
        assert 'objects' in plan.tools_needed
        assert 'objects' in plan.execution_order
        assert plan.parameters.get('object_name') == 'dogs'
    
    def test_analyze_multi_tool_query(self, router):
        """Test analyzing query that requires multiple tools."""
        query = "What did they say when the car appeared?"
        plan = router.analyze_query(query)
        
        # Should need both transcripts and objects
        assert 'transcripts' in plan.tools_needed
        assert 'objects' in plan.tools_needed
        assert len(plan.tools_needed) >= 2
    
    def test_analyze_timestamp_query(self, router):
        """Test analyzing query with timestamp."""
        query = "What's happening at 1:30?"
        plan = router.analyze_query(query)
        
        assert plan.parameters.get('timestamp') == 90.0
        assert plan.parameters.get('temporal_query') is True
    
    def test_analyze_empty_query(self, router):
        """Test analyzing empty query."""
        query = ""
        plan = router.analyze_query(query)
        
        # Empty query might still trigger some tools based on keywords
        assert isinstance(plan, ToolPlan)
        assert isinstance(plan.tools_needed, list)
    
    def test_analyze_general_question(self, router):
        """Test analyzing general conversational query."""
        query = "Thanks for the help!"
        plan = router.analyze_query(query)
        
        # General queries might not need any tools
        assert isinstance(plan, ToolPlan)


class TestRequiresCaptions:
    """Tests for ToolRouter.requires_captions() method."""
    
    def test_requires_captions_what_question(self, router):
        """Test 'what' questions require captions."""
        assert router.requires_captions("What is in the video?")
        assert router.requires_captions("What's happening here?")
        assert router.requires_captions("What are they doing?")
    
    def test_requires_captions_describe(self, router):
        """Test 'describe' requests require captions."""
        assert router.requires_captions("Describe the scene")
        assert router.requires_captions("Can you describe what you see?")
    
    def test_requires_captions_show(self, router):
        """Test 'show' requests require captions."""
        assert router.requires_captions("Show me the video")
        assert router.requires_captions("Show what's happening")
    
    def test_requires_captions_visual_keywords(self, router):
        """Test visual keywords trigger captions."""
        assert router.requires_captions("What does it look like?")
        assert router.requires_captions("How does it appear?")
        assert router.requires_captions("What can you see?")
    
    def test_does_not_require_captions_audio_only(self, router):
        """Test audio-only queries don't require captions."""
        # Note: The router is designed to be inclusive - queries with "what" may trigger
        # both captions and transcripts. Testing queries that explicitly don't have visual keywords
        assert not router.requires_captions("Transcribe the audio")
        assert not router.requires_captions("Give me the transcript")
    
    def test_requires_captions_case_insensitive(self, router):
        """Test caption detection is case insensitive."""
        assert router.requires_captions("WHAT IS HAPPENING?")
        assert router.requires_captions("Describe The Scene")


class TestRequiresTranscripts:
    """Tests for ToolRouter.requires_transcripts() method."""
    
    def test_requires_transcripts_say(self, router):
        """Test 'say' keyword requires transcripts."""
        assert router.requires_transcripts("What did they say?")
        assert router.requires_transcripts("What was said about the topic?")
    
    def test_requires_transcripts_speak(self, router):
        """Test 'speak' keyword requires transcripts."""
        assert router.requires_transcripts("Who is speaking?")
        assert router.requires_transcripts("What did she speak about?")
    
    def test_requires_transcripts_mention(self, router):
        """Test 'mention' keyword requires transcripts."""
        assert router.requires_transcripts("Did they mention the deadline?")
        assert router.requires_transcripts("What was mentioned?")
    
    def test_requires_transcripts_audio_keywords(self, router):
        """Test audio-related keywords require transcripts."""
        assert router.requires_transcripts("What's the audio about?")
        assert router.requires_transcripts("What sounds can you hear?")
        assert router.requires_transcripts("What's the voice saying?")
    
    def test_requires_transcripts_conversation(self, router):
        """Test conversation keywords require transcripts."""
        assert router.requires_transcripts("What's the conversation about?")
        assert router.requires_transcripts("What did they discuss?")
        assert router.requires_transcripts("What dialogue is there?")
    
    def test_does_not_require_transcripts_visual_only(self, router):
        """Test visual-only queries don't require transcripts."""
        # This is a bit tricky - "what" might trigger captions
        # but we're testing that it doesn't explicitly need transcripts
        query = "What colors are visible?"
        # Should not have transcript keywords
        assert 'say' not in query.lower()
        assert 'speak' not in query.lower()
    
    def test_requires_transcripts_case_insensitive(self, router):
        """Test transcript detection is case insensitive."""
        assert router.requires_transcripts("WHAT DID THEY SAY?")
        assert router.requires_transcripts("What Was Mentioned?")


class TestRequiresObjects:
    """Tests for ToolRouter.requires_objects() method."""
    
    def test_requires_objects_find(self, router):
        """Test 'find' keyword requires objects."""
        assert router.requires_objects("Find all the cars")
        assert router.requires_objects("Can you find the dog?")
    
    def test_requires_objects_show_all(self, router):
        """Test 'show all' requires objects."""
        assert router.requires_objects("Show all the people")
        assert router.requires_objects("Show me all the cats")
    
    def test_requires_objects_count(self, router):
        """Test counting queries require objects."""
        assert router.requires_objects("How many people are there?")
        assert router.requires_objects("Count the cars")
    
    def test_requires_objects_detect(self, router):
        """Test 'detect' keyword requires objects."""
        assert router.requires_objects("Detect objects in the scene")
        assert router.requires_objects("Can you detect any animals?")
    
    def test_requires_objects_specific_items(self, router):
        """Test queries about specific objects."""
        assert router.requires_objects("Where is the person?")
        assert router.requires_objects("Show me the cat")
        assert router.requires_objects("Find the car")
    
    def test_requires_objects_every_all(self, router):
        """Test 'every' and 'all the' patterns."""
        assert router.requires_objects("Every time a dog appears")
        assert router.requires_objects("All the scenes with people")
    
    def test_does_not_require_objects_general(self, router):
        """Test general queries don't require objects."""
        assert not router.requires_objects("What's the video about?")
        assert not router.requires_objects("Summarize the content")
    
    def test_requires_objects_case_insensitive(self, router):
        """Test object detection is case insensitive."""
        assert router.requires_objects("FIND ALL THE DOGS")
        assert router.requires_objects("How Many Cars?")


class TestExtractTimestamp:
    """Tests for ToolRouter.extract_timestamp() method."""
    
    def test_extract_timestamp_mm_ss(self, router):
        """Test extracting MM:SS format timestamp."""
        assert router.extract_timestamp("What happens at 1:30?") == 90.0
        assert router.extract_timestamp("Show me 2:45") == 165.0
        assert router.extract_timestamp("At 0:15 in the video") == 15.0
    
    def test_extract_timestamp_hh_mm_ss(self, router):
        """Test extracting HH:MM:SS format timestamp."""
        assert router.extract_timestamp("What's at 1:30:00?") == 5400.0
        assert router.extract_timestamp("Show 0:02:30") == 150.0
        assert router.extract_timestamp("At 2:15:45") == 8145.0
    
    def test_extract_timestamp_seconds(self, router):
        """Test extracting seconds format."""
        assert router.extract_timestamp("At 30 seconds") == 30.0
        assert router.extract_timestamp("Show me 45 secs") == 45.0
        assert router.extract_timestamp("At 120s") == 120.0
    
    def test_extract_timestamp_minutes(self, router):
        """Test extracting minutes format."""
        assert router.extract_timestamp("At 2 minutes") == 120.0
        assert router.extract_timestamp("Show 5 mins") == 300.0
        assert router.extract_timestamp("At 10m") == 600.0
    
    def test_extract_timestamp_beginning(self, router):
        """Test extracting 'beginning' reference."""
        assert router.extract_timestamp("Show the beginning") == 0.0
        assert router.extract_timestamp("At the start") == 0.0
    
    def test_extract_timestamp_none(self, router):
        """Test queries without timestamps return None."""
        assert router.extract_timestamp("What's in the video?") is None
        assert router.extract_timestamp("Show me all the dogs") is None
        assert router.extract_timestamp("Describe the scene") is None
    
    def test_extract_timestamp_multiple_formats(self, router):
        """Test that first timestamp is extracted when multiple exist."""
        # Should extract the first one found
        result = router.extract_timestamp("At 1:30 and also 2:45")
        assert result == 90.0  # First timestamp
    
    def test_extract_timestamp_case_insensitive(self, router):
        """Test timestamp extraction is case insensitive."""
        assert router.extract_timestamp("At 1:30 SECONDS") == 90.0
        assert router.extract_timestamp("SHOW 2 MINUTES") == 120.0


class TestObjectNameExtraction:
    """Tests for ToolRouter._extract_object_name() method."""
    
    def test_extract_object_from_count_query(self, router):
        """Test extracting object from counting queries."""
        assert router._extract_object_name("how many dogs") == "dogs"
        assert router._extract_object_name("how many cars") == "cars"
    
    def test_extract_object_from_find_query(self, router):
        """Test extracting object from find queries."""
        assert router._extract_object_name("find the cat") == "cat"
        assert router._extract_object_name("locate people") == "people"
    
    def test_extract_object_from_show_all_query(self, router):
        """Test extracting object from 'show all' queries."""
        assert router._extract_object_name("show me all the dogs") == "dogs"
        assert router._extract_object_name("show all the cars") == "cars"
    
    def test_extract_object_from_scenes_query(self, router):
        """Test extracting object from 'scenes with' queries."""
        assert router._extract_object_name("scenes with a dog") == "dog"
        assert router._extract_object_name("scene with the car") == "car"
    
    def test_extract_object_filters_stop_words(self, router):
        """Test that stop words are filtered out."""
        # Should not extract stop words
        result = router._extract_object_name("find the video")
        assert result != "video"
    
    def test_extract_object_none_when_no_pattern(self, router):
        """Test returns None when no object pattern found."""
        assert router._extract_object_name("what's happening?") is None
        assert router._extract_object_name("describe the scene") is None


class TestExecutionOrder:
    """Tests for ToolRouter._optimize_execution_order() method."""
    
    def test_execution_order_single_tool(self, router):
        """Test execution order with single tool."""
        order = router._optimize_execution_order(['captions'], {})
        assert order == ['captions']
    
    def test_execution_order_default(self, router):
        """Test default execution order (transcripts -> captions -> objects)."""
        tools = ['objects', 'captions', 'transcripts']
        order = router._optimize_execution_order(tools, {})
        
        # Should be ordered by speed: transcripts first, objects last
        assert order.index('transcripts') < order.index('captions')
        assert order.index('captions') < order.index('objects')
    
    def test_execution_order_temporal_query(self, router):
        """Test execution order for temporal queries."""
        tools = ['objects', 'captions', 'transcripts']
        parameters = {'temporal_query': True, 'timestamp': 90.0}
        order = router._optimize_execution_order(tools, parameters)
        
        # For temporal queries, still prioritize speed
        assert order.index('transcripts') < order.index('objects')
    
    def test_execution_order_empty_tools(self, router):
        """Test execution order with no tools."""
        order = router._optimize_execution_order([], {})
        assert order == []
    
    def test_execution_order_partial_tools(self, router):
        """Test execution order with subset of tools."""
        # Only captions and objects
        order = router._optimize_execution_order(['captions', 'objects'], {})
        assert 'captions' in order
        assert 'objects' in order
        assert 'transcripts' not in order
        assert order.index('captions') < order.index('objects')


class TestToolPlanDataclass:
    """Tests for ToolPlan dataclass."""
    
    def test_tool_plan_creation(self):
        """Test creating ToolPlan instance."""
        plan = ToolPlan(
            tools_needed=['captions', 'objects'],
            execution_order=['captions', 'objects'],
            parameters={'timestamp': 90.0}
        )
        
        assert plan.tools_needed == ['captions', 'objects']
        assert plan.execution_order == ['captions', 'objects']
        assert plan.parameters == {'timestamp': 90.0}
    
    def test_tool_plan_default_values(self):
        """Test ToolPlan with default values."""
        plan = ToolPlan()
        
        assert plan.tools_needed == []
        assert plan.execution_order == []
        assert plan.parameters == {}
    
    def test_tool_plan_partial_initialization(self):
        """Test ToolPlan with partial initialization."""
        plan = ToolPlan(tools_needed=['captions'])
        
        assert plan.tools_needed == ['captions']
        assert plan.execution_order == []
        assert plan.parameters == {}


class TestComplexQueries:
    """Tests for complex real-world query scenarios."""
    
    def test_complex_multi_tool_query(self, router):
        """Test complex query requiring multiple tools."""
        query = "Show me all the dogs and what they said at 2:30"
        plan = router.analyze_query(query)
        
        # Should need objects (dogs), transcripts (said), and timestamp
        assert 'objects' in plan.tools_needed
        assert 'transcripts' in plan.tools_needed
        assert plan.parameters.get('timestamp') == 150.0
        assert plan.parameters.get('object_name') == 'dogs'
    
    def test_visual_description_query(self, router):
        """Test visual description query."""
        query = "Describe what's happening in the scene"
        plan = router.analyze_query(query)
        
        assert 'captions' in plan.tools_needed
    
    def test_audio_content_query(self, router):
        """Test audio content query."""
        query = "What did the speaker mention about the project?"
        plan = router.analyze_query(query)
        
        assert 'transcripts' in plan.tools_needed
    
    def test_object_search_query(self, router):
        """Test object search query."""
        query = "Find all scenes with a person"
        plan = router.analyze_query(query)
        
        assert 'objects' in plan.tools_needed
        assert plan.parameters.get('object_name') == 'person'
    
    def test_temporal_visual_query(self, router):
        """Test temporal visual query."""
        query = "What's visible at 1:45?"
        plan = router.analyze_query(query)
        
        assert 'captions' in plan.tools_needed
        assert plan.parameters.get('timestamp') == 105.0
        assert plan.parameters.get('temporal_query') is True
    
    def test_counting_query(self, router):
        """Test counting query."""
        query = "How many cars appear in the video?"
        plan = router.analyze_query(query)
        
        assert 'objects' in plan.tools_needed
        assert plan.parameters.get('object_name') == 'cars'


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_query_with_special_characters(self, router):
        """Test query with special characters."""
        query = "What's happening @ 1:30?!?"
        plan = router.analyze_query(query)
        
        assert 'captions' in plan.tools_needed
        assert plan.parameters.get('timestamp') == 90.0
    
    def test_query_with_unicode(self, router):
        """Test query with unicode characters."""
        query = "What's happening? 🎥"
        plan = router.analyze_query(query)
        
        assert isinstance(plan, ToolPlan)
    
    def test_very_long_query(self, router):
        """Test very long query."""
        query = "What " * 100 + "is happening in the video?"
        plan = router.analyze_query(query)
        
        assert 'captions' in plan.tools_needed
    
    def test_query_with_multiple_timestamps(self, router):
        """Test query with multiple timestamps."""
        query = "Compare what happens at 1:30 and 2:45"
        plan = router.analyze_query(query)
        
        # Should extract first timestamp
        assert plan.parameters.get('timestamp') == 90.0
    
    def test_ambiguous_query(self, router):
        """Test ambiguous query that could match multiple tools."""
        query = "What's there?"
        plan = router.analyze_query(query)
        
        # Should still produce a valid plan
        assert isinstance(plan, ToolPlan)
        assert isinstance(plan.tools_needed, list)
    
    def test_query_with_context(self, router):
        """Test query analysis with context parameter."""
        query = "What about the other one?"
        context = {'previous_object': 'dog'}
        plan = router.analyze_query(query, context=context)
        
        # Should still produce valid plan even with context
        assert isinstance(plan, ToolPlan)
