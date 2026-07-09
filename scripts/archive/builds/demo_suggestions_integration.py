"""
Demo script showing follow-up suggestion generation in action.

This demonstrates how suggestions are generated and integrated into
the conversational flow with BRI.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agent import GroqAgent


def demo_suggestion_flow():
    """Demonstrate the suggestion generation flow."""
    
    print("=" * 80)
    print("BRI Follow-up Suggestion Generation - Interactive Demo")
    print("=" * 80)
    print("\nThis demo shows how BRI generates intelligent follow-up suggestions")
    print("based on user queries and responses.\n")
    
    # Simulate conversation scenarios
    scenarios = [
        {
            "title": "Scenario 1: Exploring Visual Content",
            "conversation": [
                {
                    "user": "What's happening in the video?",
                    "bri": "The video shows a cooking demonstration where a chef is preparing pasta. You can see various ingredients on the counter including tomatoes, garlic, and fresh basil.",
                },
                {
                    "user": "Can you describe a specific moment in more detail?",
                    "bri": "At around 2:15, the chef is carefully chopping fresh basil leaves on a wooden cutting board. The knife movements are precise and the basil releases its aromatic oils.",
                }
            ]
        },
        {
            "title": "Scenario 2: Understanding Audio Content",
            "conversation": [
                {
                    "user": "What did they say about the recipe?",
                    "bri": "The chef explains that this is a traditional Italian recipe passed down through generations. They emphasize the importance of using fresh, quality ingredients and taking time with each step.",
                },
                {
                    "user": "Can you summarize the main points discussed?",
                    "bri": "The main points are: 1) Use fresh ingredients, especially basil and tomatoes, 2) Don't rush the cooking process, 3) Taste and adjust seasoning throughout, 4) The sauce should simmer for at least 20 minutes.",
                }
            ]
        },
        {
            "title": "Scenario 3: Proactive Content Discovery",
            "conversation": [
                {
                    "user": "What's in this video?",
                    "bri": "This video contains a cooking tutorial followed by a Q&A session where the chef answers viewer questions about Italian cooking techniques.",
                },
                {
                    "user": "Want me to summarize the Q&A session?",
                    "bri": "In the Q&A, viewers asked about pasta alternatives, sauce storage tips, and how to adjust the recipe for dietary restrictions. The chef provided detailed answers for each question.",
                }
            ]
        }
    ]
    
    # Mock agent for generating suggestions
    agent = GroqAgent.__new__(GroqAgent)
    agent._classify_query_type = GroqAgent._classify_query_type.__get__(agent, GroqAgent)
    agent._suggest_visual_followups = GroqAgent._suggest_visual_followups.__get__(agent, GroqAgent)
    agent._suggest_audio_followups = GroqAgent._suggest_audio_followups.__get__(agent, GroqAgent)
    agent._suggest_object_followups = GroqAgent._suggest_object_followups.__get__(agent, GroqAgent)
    agent._suggest_timestamp_followups = GroqAgent._suggest_timestamp_followups.__get__(agent, GroqAgent)
    agent._suggest_summary_followups = GroqAgent._suggest_summary_followups.__get__(agent, GroqAgent)
    agent._suggest_general_followups = GroqAgent._suggest_general_followups.__get__(agent, GroqAgent)
    agent._suggest_exploration_followups = GroqAgent._suggest_exploration_followups.__get__(agent, GroqAgent)
    agent._detect_additional_content = GroqAgent._detect_additional_content.__get__(agent, GroqAgent)
    agent._generate_suggestions = GroqAgent._generate_suggestions.__get__(agent, GroqAgent)
    
    # Run through scenarios
    for scenario in scenarios:
        print("\n" + "=" * 80)
        print(scenario["title"])
        print("=" * 80)
        
        for i, turn in enumerate(scenario["conversation"], 1):
            print(f"\n--- Turn {i} ---")
            print(f"\n👤 User: {turn['user']}")
            print(f"\n🤖 BRI: {turn['bri']}")
            
            # Generate suggestions
            suggestions = agent._generate_suggestions(
                turn['user'],
                turn['bri'],
                "demo_video_id"
            )
            
            print(f"\n💡 Suggestions ({len(suggestions)}):")
            for j, suggestion in enumerate(suggestions, 1):
                print(f"   {j}. {suggestion}")
            
            # Show how the next turn uses a suggestion
            if i < len(scenario["conversation"]):
                next_turn = scenario["conversation"][i]
                # Check if next user message matches a suggestion
                for suggestion in suggestions:
                    if suggestion.lower() in next_turn['user'].lower() or \
                       next_turn['user'].lower() in suggestion.lower():
                        print(f"\n   ✨ User selected suggestion {suggestions.index(suggestion) + 1}!")
                        break
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nKey Observations:")
    print("  • Suggestions are contextual and relevant to the query type")
    print("  • Users can naturally select suggestions to continue exploring")
    print("  • Proactive suggestions help discover additional content")
    print("  • The conversation flows naturally with guided exploration")
    print("\nThis creates a warm, supportive experience that helps users")
    print("get the most out of their video content! 🎉")


def show_suggestion_variety():
    """Show the variety of suggestions across different query types."""
    
    print("\n" + "=" * 80)
    print("Suggestion Variety Across Query Types")
    print("=" * 80)
    
    agent = GroqAgent.__new__(GroqAgent)
    agent._classify_query_type = GroqAgent._classify_query_type.__get__(agent, GroqAgent)
    agent._suggest_visual_followups = GroqAgent._suggest_visual_followups.__get__(agent, GroqAgent)
    agent._suggest_audio_followups = GroqAgent._suggest_audio_followups.__get__(agent, GroqAgent)
    agent._suggest_object_followups = GroqAgent._suggest_object_followups.__get__(agent, GroqAgent)
    agent._suggest_timestamp_followups = GroqAgent._suggest_timestamp_followups.__get__(agent, GroqAgent)
    agent._suggest_summary_followups = GroqAgent._suggest_summary_followups.__get__(agent, GroqAgent)
    agent._suggest_general_followups = GroqAgent._suggest_general_followups.__get__(agent, GroqAgent)
    agent._suggest_exploration_followups = GroqAgent._suggest_exploration_followups.__get__(agent, GroqAgent)
    agent._detect_additional_content = GroqAgent._detect_additional_content.__get__(agent, GroqAgent)
    agent._generate_suggestions = GroqAgent._generate_suggestions.__get__(agent, GroqAgent)
    
    query_examples = [
        ("What's happening?", "Visual scene description"),
        ("What did they say?", "Audio transcript content"),
        ("Find all the dogs", "Object search"),
        ("What happens at 3:45?", "Timestamp navigation"),
        ("Summarize this video", "Content summary"),
        ("Hello!", "General conversation"),
    ]
    
    print("\nGenerating suggestions for different query types:\n")
    
    for query, description in query_examples:
        query_type = agent._classify_query_type(query.lower())
        suggestions = agent._generate_suggestions(
            query,
            "Sample response for demonstration purposes.",
            "demo_video"
        )
        
        print(f"Query Type: {description} ({query_type})")
        print(f"Example: \"{query}\"")
        print("Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        print()


if __name__ == "__main__":
    try:
        demo_suggestion_flow()
        show_suggestion_variety()
        
        print("\n" + "=" * 80)
        print("✅ Demo completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
