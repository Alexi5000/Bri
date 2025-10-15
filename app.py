"""
BRI (Brianna) - Video Analysis Agent
Main Streamlit Application Entry Point
"""

import streamlit as st

# Import UI components
from ui.welcome import render_welcome_screen
from ui.library import render_video_library  # Task 19
from ui.player import render_video_player, extract_timestamps_from_conversation, navigate_to_timestamp  # Task 21
from ui.history import render_conversation_history_panel  # Task 22
from ui.styles import apply_custom_styles

# Configure page
st.set_page_config(
    page_title="BRI - Your Video Assistant",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'current_video_id' not in st.session_state:
        st.session_state.current_video_id = None
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = {}
    
    if 'uploaded_videos' not in st.session_state:
        # Load videos from database
        from storage.database import get_all_videos
        try:
            videos = get_all_videos()
            st.session_state.uploaded_videos = [
                {
                    'video_id': video['video_id'],
                    'filename': video['filename'],
                    'file_path': video['file_path'],
                    'duration': video['duration'],
                    'processing_status': video['processing_status']
                }
                for video in videos
            ]
        except Exception:
            # If database not initialized yet, start with empty list
            st.session_state.uploaded_videos = []
    
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'welcome'  # 'welcome', 'library', 'chat'
    
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = {}
    
    if 'user_message' not in st.session_state:
        st.session_state.user_message = ""
    
    if 'delete_confirm_video_id' not in st.session_state:
        st.session_state.delete_confirm_video_id = None

def render_sidebar():
    """Render sidebar with navigation and video selection"""
    with st.sidebar:
        st.markdown("### 💜 BRI")
        st.markdown("*Ask. Understand. Remember.*")
        st.markdown("---")
        
        # Navigation
        st.markdown("#### Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_view = 'welcome'
            st.session_state.current_video_id = None
            st.rerun()
        
        if st.button("📚 Video Library", use_container_width=True):
            st.session_state.current_view = 'library'
            st.rerun()
        
        st.markdown("---")
        
        # Video selection (if videos exist)
        if st.session_state.uploaded_videos:
            st.markdown("#### Your Videos")
            for video in st.session_state.uploaded_videos:
                video_id = video.get('video_id', '')
                filename = video.get('filename', 'Unknown')
                if st.button(f"🎬 {filename[:20]}...", key=f"vid_{video_id}", use_container_width=True):
                    st.session_state.current_video_id = video_id
                    st.session_state.current_view = 'chat'
                    st.rerun()
        
        st.markdown("---")
        
        # Conversation history panel (Task 22)
        # Show history panel when a video is selected and in chat view
        if st.session_state.current_video_id and st.session_state.current_view == 'chat':
            from services.memory import Memory
            
            try:
                memory = Memory()
                render_conversation_history_panel(
                    video_id=st.session_state.current_video_id,
                    memory=memory,
                    on_conversation_select=lambda session: load_conversation_context(
                        session,
                        st.session_state.current_video_id
                    )
                )
            except Exception as e:
                st.error(f"Failed to load conversation history: {e}")
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #999; font-size: 0.8em;'>"
            "Made with 💜 by BRI<br>"
            "Open Source Video Assistant"
            "</div>",
            unsafe_allow_html=True  # noqa: S308
        )


def load_conversation_context(session, video_id):
    """Load a conversation session into the current context.
    
    Args:
        session: List of MemoryRecord objects to load
        video_id: Current video ID
    """
    from ui.history import load_conversation_context as load_context
    load_context(session, video_id)

def render_main_content():
    """Render main content area based on current view"""
    if st.session_state.current_view == 'welcome':
        render_welcome_placeholder()
    elif st.session_state.current_view == 'library':
        render_library_placeholder()
    elif st.session_state.current_view == 'chat':
        render_chat_placeholder()
    else:
        render_welcome_placeholder()

def render_welcome_placeholder():
    """Welcome screen (Task 16 - Implemented)"""
    render_welcome_screen()

def render_library_placeholder():
    """Video library view (Task 19 - Implemented)"""
    render_video_library()

def render_chat_placeholder():
    """Chat interface with video player (Tasks 20, 21, 23)"""
    if st.session_state.current_video_id:
        video_id = st.session_state.current_video_id
        
        # Get video info from uploaded videos
        video_info = None
        for video in st.session_state.uploaded_videos:
            if video['video_id'] == video_id:
                video_info = video
                break
        
        if not video_info:
            st.error("Video not found!")
            return
        
        # Page header
        st.markdown("# 💬 Chat with BRI")
        st.markdown(f"**Video:** {video_info['filename']}")
        st.markdown("---")
        
        # Create two columns: video player (left) and chat (right)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Get conversation history for this video
            from services.memory import Memory
            memory = Memory()
            conversation_history = memory.get_conversation_history(video_id, limit=20)
            
            # Extract timestamps from conversation
            timestamps = extract_timestamps_from_conversation(conversation_history)
            
            # Check if user clicked a timestamp in chat
            clicked_timestamp = st.session_state.get("clicked_timestamp")
            if clicked_timestamp is not None:
                navigate_to_timestamp(video_id, clicked_timestamp)
                # Clear the clicked timestamp
                st.session_state["clicked_timestamp"] = None
            
            # Render video player with timestamps
            render_video_player(
                video_path=video_info['file_path'],
                video_id=video_id,
                current_timestamp=None,
                timestamps=timestamps
            )
        
        with col2:
            # Render chat window with agent integration
            render_chat_with_agent(video_id, video_info)
    else:
        st.warning("Please select a video from the sidebar to start chatting!")


def render_chat_with_agent(video_id: str, video_info: dict):
    """Render chat window with full agent integration.
    
    Args:
        video_id: Current video ID
        video_info: Video information dictionary
    """
    import asyncio
    from services.memory import Memory
    from services.agent import GroqAgent
    from models.responses import AssistantMessageResponse
    
    # Initialize components
    memory = Memory()
    
    # Get conversation history
    conversation_history = memory.get_conversation_history(video_id, limit=20)
    
    # Display conversation history
    st.markdown("### 💭 Conversation")
    
    if not conversation_history:
        st.info("👋 Hi! I'm BRI. Ask me anything about this video!")
    else:
        # Display messages with proper formatting
        for message in conversation_history:
            role = message.role
            content = message.content
            timestamp = message.timestamp
            
            if role == 'user':
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                        <span style="font-size: 1.2rem;">👤</span>
                        <span style="font-weight: 600; color: #40E0D0;">You</span>
                        <span style="font-size: 0.85rem; color: #999;">{format_message_timestamp(timestamp)}</span>
                    </div>
                    <div style="padding: 1rem 1.25rem; border-radius: 20px; background: linear-gradient(135deg, #40E0D0 0%, rgba(64, 224, 208, 0.8) 100%); color: white; margin-left: 2rem; border-bottom-right-radius: 5px;">
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                        <span style="font-size: 1.2rem;">💖</span>
                        <span style="font-weight: 600; color: #FF69B4;">BRI</span>
                        <span style="font-size: 0.85rem; color: #999;">{format_message_timestamp(timestamp)}</span>
                    </div>
                    <div style="padding: 1rem 1.25rem; border-radius: 20px; background: white; border: 2px solid #E6E6FA; margin-right: 2rem; border-bottom-left-radius: 5px;">
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Check if there's a pending response to display
    if 'pending_response' in st.session_state and st.session_state.pending_response:
        response = st.session_state.pending_response
        display_agent_response(response)
        # Clear pending response
        st.session_state.pending_response = None
    
    # Message input area
    st.markdown("---")
    
    # Handle suggestion clicks
    if 'selected_suggestion' in st.session_state and st.session_state.selected_suggestion:
        user_input = st.session_state.selected_suggestion
        st.session_state.selected_suggestion = None
        # Process the suggestion as a message
        process_user_message(video_id, user_input)
        st.rerun()
    
    # Create input form
    with st.form(key=f"chat_form_{video_id}", clear_on_submit=True):
        user_input = st.text_input(
            "Message",
            placeholder="Ask me anything about this video... 💭",
            label_visibility="collapsed",
            key=f"chat_input_{video_id}"
        )
        
        col1, col2 = st.columns([5, 1])
        with col2:
            submit_button = st.form_submit_button("Send", use_container_width=True)
        
        if submit_button and user_input.strip():
            # Show loading state
            with st.spinner("🤔 Thinking..."):
                process_user_message(video_id, user_input.strip())
            st.rerun()
    
    # Keyboard shortcut hint
    st.markdown("""
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.85rem; color: #666666;">
            Press Enter to send 💌
        </div>
    """, unsafe_allow_html=True)


def process_user_message(video_id: str, message: str):
    """Process user message with the agent.
    
    Args:
        video_id: Current video ID
        message: User's message
    """
    import asyncio
    from services.agent import GroqAgent
    
    try:
        # Initialize agent
        agent = GroqAgent()
        
        # Process message (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(agent.chat(message, video_id))
        loop.close()
        
        # Store response for display
        st.session_state.pending_response = response
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to process message: {e}", exc_info=True)
        
        # Show error message
        st.error(f"Oops! Something went wrong: {str(e)}")


def display_agent_response(response):
    """Display agent response with frames, timestamps, and suggestions.
    
    Args:
        response: AssistantMessageResponse object
    """
    from ui.lazy_loader import LazyImageLoader
    from config import Config
    
    # Display main message
    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
            <span style="font-size: 1.2rem;">💖</span>
            <span style="font-weight: 600; color: #FF69B4;">BRI</span>
            <span style="font-size: 0.85rem; color: #999;">just now</span>
        </div>
        <div style="padding: 1rem 1.25rem; border-radius: 20px; background: white; border: 2px solid #E6E6FA; margin-right: 2rem; border-bottom-left-radius: 5px;">
            {response.message}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display frames if present with lazy loading
    if response.frames and response.timestamps:
        st.markdown("**Relevant moments:**")
        
        # Use lazy loader for better performance
        lazy_loader = LazyImageLoader(batch_size=Config.LAZY_LOAD_BATCH_SIZE)
        lazy_loader.render_lazy_images(
            image_paths=response.frames,
            timestamps=response.timestamps,
            columns=3
        )
    
    # Display follow-up suggestions
    if response.suggestions:
        st.markdown("""
        <div style="margin-top: 1rem; padding: 1rem; background: #F5F5F5; border-radius: 15px; border-left: 4px solid #FFB6C1;">
            <div style="font-weight: 600; margin-bottom: 0.5rem; color: #333;">
                💡 You might also want to ask:
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display suggestion buttons
        for idx, suggestion in enumerate(response.suggestions):
            if st.button(
                suggestion,
                key=f"suggestion_{idx}_{hash(suggestion)}",
                help="Click to ask this question"
            ):
                st.session_state["selected_suggestion"] = suggestion
                st.rerun()


def format_message_timestamp(timestamp) -> str:
    """Format message timestamp for display.
    
    Args:
        timestamp: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    from datetime import datetime
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except Exception:
            return "recently"
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        return timestamp.strftime("%b %d, %I:%M %p")


def format_video_timestamp(seconds: float) -> str:
    """Format video timestamp in MM:SS or HH:MM:SS format.
    
    Args:
        seconds: Timestamp in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def main():
    """Main application entry point"""
    # Apply custom styles
    apply_custom_styles()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()

if __name__ == "__main__":
    main()
