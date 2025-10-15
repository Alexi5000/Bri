"""
BRI (Brianna) - Video Analysis Agent
Main Streamlit Application Entry Point
"""

import streamlit as st

# Import UI components
from ui.welcome import render_welcome_screen
from ui.library import render_video_library  # Task 19
# from ui.chat import render_chat_window  # Task 20
# from ui.player import render_video_player  # Task 21
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
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #999; font-size: 0.8em;'>"
            "Made with 💜 by BRI<br>"
            "Open Source Video Assistant"
            "</div>",
            unsafe_allow_html=True  # noqa: S308
        )

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
    """Placeholder for chat interface (Task 20)"""
    if st.session_state.current_video_id:
        st.markdown("# 💬 Chat")
        st.markdown("---")
        st.info("Chat interface coming soon! You'll be able to ask questions about your video here.")
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
