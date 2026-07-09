"""
BRI (Brianna) - Video Analysis Agent
Main Streamlit Application Entry Point
"""

import streamlit as st

from config import Config

# Initialize logging first
from utils.logging_config import get_logger, setup_logging

setup_logging(
    log_level=Config.LOG_LEVEL,
    log_dir=Config.LOG_DIR,
    json_format=Config.LOG_JSON_FORMAT,
    enable_rotation=Config.LOG_ROTATION_ENABLED,
)

logger = get_logger(__name__)
logger.info("Starting BRI Streamlit application")

# Validate configuration on startup
try:
    Config.validate()
    Config.ensure_directories()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    st.error(f"⚠️ Configuration Error\n\n{e}")
    st.info("Please check your .env file and ensure all required values are set.")
    st.stop()
except Exception as e:
    logger.error(f"Startup error: {e}", exc_info=True)
    st.error(f"⚠️ Startup Error\n\n{e}")
    st.stop()

# Import UI components
from services.application import get_application_service
from ui.chat_workflow import render_video_chat_workspace
from ui.history import render_conversation_history_panel  # Task 22
from ui.library import render_video_library  # Task 19
from ui.shell import (
    render_dashboard,
    render_enterprise_styles,
    render_persistence_panel,
    render_product_header,
    render_sidebar_readiness,
    render_video_workflow,
)
from ui.styles import apply_custom_styles
from ui.welcome import render_welcome_screen

# Configure page
st.set_page_config(
    page_title="BRI - Your Video Assistant",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner=False)
def get_bri_service():
    """Return the production application-service facade for this Streamlit session."""
    return get_application_service()


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "current_video_id" not in st.session_state:
        st.session_state.current_video_id = None

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = {}

    if "uploaded_videos" not in st.session_state:
        # Load videos from database
        try:
            videos = get_bri_service().list_videos()
            st.session_state.uploaded_videos = [
                {
                    "video_id": video.video_id,
                    "filename": video.filename,
                    "file_path": video.file_path,
                    "duration": video.duration,
                    "processing_status": video.processing_status,
                    "thumbnail_path": video.thumbnail_path,
                    "upload_timestamp": video.upload_timestamp,
                }
                for video in videos
            ]
        except Exception:
            # If database not initialized yet, start with empty list
            st.session_state.uploaded_videos = []

    if "current_view" not in st.session_state:
        st.session_state.current_view = "welcome"  # 'welcome', 'library', 'chat'

    if "processing_status" not in st.session_state:
        st.session_state.processing_status = {}

    if "user_message" not in st.session_state:
        st.session_state.user_message = ""

    if "delete_confirm_video_id" not in st.session_state:
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
            st.session_state.current_view = "welcome"
            st.session_state.current_video_id = None
            st.rerun()

        if st.button("📚 Video Library", use_container_width=True):
            st.session_state.current_view = "library"
            st.rerun()

        st.markdown("---")

        # Video selection (if videos exist)
        if st.session_state.uploaded_videos:
            st.markdown("#### Your Videos")
            for video in st.session_state.uploaded_videos:
                video_id = video.get("video_id", "")
                filename = video.get("filename", "Unknown")
                if st.button(
                    f"🎬 {filename[:20]}...", key=f"vid_{video_id}", use_container_width=True
                ):
                    st.session_state.current_video_id = video_id
                    st.session_state.current_view = "chat"
                    st.rerun()

        st.markdown("---")

        # Conversation history panel (Task 22)
        # Show history panel when a video is selected and in chat view
        if st.session_state.current_video_id and st.session_state.current_view == "chat":
            from services.memory import Memory

            try:
                memory = Memory()
                render_conversation_history_panel(
                    video_id=st.session_state.current_video_id,
                    memory=memory,
                    on_conversation_select=lambda session: load_conversation_context(
                        session, st.session_state.current_video_id
                    ),
                )
            except Exception as e:
                st.error(f"Failed to load conversation history: {e}")

        try:
            render_sidebar_readiness(get_bri_service().snapshot(include_tools=False))
        except Exception as e:
            st.caption(f"Readiness panel unavailable: {e}")

        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
            "Made with 💜 by BRI<br>"
            "Open Source Video Assistant"
            "</div>",
            unsafe_allow_html=True,  # noqa: S308
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
    if st.session_state.current_view == "welcome":
        render_welcome_placeholder()
    elif st.session_state.current_view == "library":
        render_library_placeholder()
    elif st.session_state.current_view == "chat":
        render_chat_placeholder()
    else:
        render_welcome_placeholder()


def render_welcome_placeholder():
    """Welcome screen with production command-center context."""
    service = get_bri_service()
    snapshot = service.snapshot(include_tools=True)
    render_product_header(snapshot)
    render_dashboard(snapshot)
    render_persistence_panel(service.persistence_readiness())
    render_video_workflow(snapshot.videos)
    render_welcome_screen()


def render_library_placeholder():
    """Video library view (Task 19 - Implemented)"""
    render_video_library()


def render_chat_placeholder():
    """Render the selected-video chat workspace through the production UI module."""

    video_id = st.session_state.get("current_video_id")
    if not video_id:
        st.warning("Please select a video from the sidebar to start chatting!")
        return

    service = get_bri_service()
    video = service.get_video(video_id)
    if not video:
        st.error("Video not found!")
        return

    render_video_chat_workspace(service, video)


def main():
    """Main application entry point"""
    # Apply custom styles
    apply_custom_styles()
    render_enterprise_styles()

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    render_main_content()


if __name__ == "__main__":
    main()
