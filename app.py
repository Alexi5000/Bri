"""
BRI (Brianna) - Video Analysis Agent
Main Streamlit Application Entry Point
"""

import streamlit as st

# Import UI components
from ui.welcome import render_welcome_screen
from ui.library import render_video_library  # Task 19
from ui.chat import render_chat_window  # Task 20
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
    """Chat interface with video player (Tasks 20 & 21)"""
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
        st.markdown(f"# 💬 Chat with BRI")
        st.markdown(f"**Video:** {video_info['filename']}")
        st.markdown("---")
        
        # Create two columns: video player (left) and chat (right)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Get conversation history for this video
            conversation_history = st.session_state.conversation_history.get(video_id, [])
            
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
            # Render chat window
            st.markdown("### 💭 Conversation")
            
            # Get conversation history
            conversation_history = st.session_state.conversation_history.get(video_id, [])
            
            # Placeholder for chat functionality
            if not conversation_history:
                st.info("👋 Hi! I'm BRI. Ask me anything about this video!")
            else:
                # Display conversation history
                for message in conversation_history:
                    role = message.get('role', 'user')
                    content = message.get('content', '')
                    
                    if role == 'user':
                        st.markdown(f"**You:** {content}")
                    else:
                        st.markdown(f"**BRI:** {content}")
            
            # Message input
            st.markdown("---")
            user_input = st.text_input(
                "Ask me anything...",
                key=f"chat_input_{video_id}",
                placeholder="What's happening in this video? 💭"
            )
            
            if st.button("Send", key=f"send_{video_id}"):
                if user_input.strip():
                    # Add to conversation history
                    if video_id not in st.session_state.conversation_history:
                        st.session_state.conversation_history[video_id] = []
                    
                    st.session_state.conversation_history[video_id].append({
                        'role': 'user',
                        'content': user_input
                    })
                    
                    # Placeholder response
                    st.session_state.conversation_history[video_id].append({
                        'role': 'assistant',
                        'content': "I'm still learning! Full chat functionality coming soon. 💜"
                    })
                    
                    st.rerun()
    else:
        st.warning("Please select a video from the sidebar to start chatting!")

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
