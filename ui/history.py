"""
Conversation History Panel Component for BRI
Displays past conversations for selected video in sidebar
"""

import streamlit as st
from datetime import datetime
from typing import List, Optional
import logging

from models.memory import MemoryRecord
from services.memory import Memory
from ui.styles import COLORS

logger = logging.getLogger(__name__)


def render_conversation_history_panel(
    video_id: str,
    memory: Memory,
    on_conversation_select: Optional[callable] = None
) -> None:
    """Render conversation history panel in sidebar with pagination.
    
    Args:
        video_id: Current video ID
        memory: Memory instance for retrieving conversation history
        on_conversation_select: Optional callback when conversation is selected
    """
    from config import Config
    
    st.markdown("### 💬 Conversation History")
    
    try:
        # Initialize pagination state
        page_key = f"history_page_{video_id}"
        if page_key not in st.session_state:
            st.session_state[page_key] = 0
        
        # Get total message count
        total_messages = memory.count_messages(video_id)
        
        if total_messages == 0:
            _render_empty_history()
            return
        
        # Calculate pagination
        messages_per_page = Config.MAX_CONVERSATION_HISTORY
        current_page = st.session_state[page_key]
        offset = current_page * messages_per_page
        
        # Get conversation history for current page
        conversation_history = memory.get_conversation_history(
            video_id,
            limit=messages_per_page,
            offset=offset
        )
        
        # Group conversations by session (pairs of user-assistant messages)
        conversation_sessions = _group_into_sessions(conversation_history)
        
        # Display conversation count
        total_pages = (total_messages + messages_per_page - 1) // messages_per_page
        st.markdown(
            f"<div style='color: {COLORS['text_light']}; font-size: 0.9rem; margin-bottom: 1rem;'>"
            f"📝 {total_messages} message{'s' if total_messages != 1 else ''} "
            f"(Page {current_page + 1}/{total_pages})"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Display each conversation session
        for idx, session in enumerate(conversation_sessions):
            _render_conversation_session(session, idx + offset, on_conversation_select)
        
        # Pagination controls
        if total_pages > 1:
            col1, col2 = st.columns(2)
            with col1:
                if current_page > 0:
                    if st.button("⬅️ Newer", key=f"history_prev_{video_id}", use_container_width=True):
                        st.session_state[page_key] -= 1
                        st.rerun()
            with col2:
                if current_page < total_pages - 1:
                    if st.button("Older ➡️", key=f"history_next_{video_id}", use_container_width=True):
                        st.session_state[page_key] += 1
                        st.rerun()
        
        # Memory wipe button
        st.markdown("---")
        _render_memory_wipe_button(video_id, memory)
        
    except Exception as e:
        logger.error(f"Failed to render conversation history: {e}")
        st.error("Oops! I had trouble loading the conversation history. 😅")


def _render_empty_history() -> None:
    """Render empty state when no conversation history exists."""
    
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem 1rem; color: {COLORS['text_light']};">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">💭</div>
            <p style="font-size: 0.9rem; margin: 0;">
                No conversations yet.<br>
                Start chatting to build history!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def _group_into_sessions(conversation_history: List[MemoryRecord]) -> List[List[MemoryRecord]]:
    """Group conversation history into sessions (user-assistant pairs).
    
    Args:
        conversation_history: List of MemoryRecord objects
        
    Returns:
        List of conversation sessions, each containing related messages
    """
    
    sessions = []
    current_session = []
    
    for message in conversation_history:
        current_session.append(message)
        
        # Start new session after assistant response
        if message.role == "assistant":
            sessions.append(current_session)
            current_session = []
    
    # Add any remaining messages as a session
    if current_session:
        sessions.append(current_session)
    
    return sessions


def _render_conversation_session(
    session: List[MemoryRecord],
    session_idx: int,
    on_conversation_select: Optional[callable]
) -> None:
    """Render a single conversation session.
    
    Args:
        session: List of MemoryRecord objects in this session
        session_idx: Index of this session
        on_conversation_select: Optional callback when session is selected
    """
    
    # Get the first user message as preview
    user_message = next((msg for msg in session if msg.role == "user"), None)
    
    if not user_message:
        return
    
    # Get timestamp of first message
    timestamp = session[0].timestamp
    timestamp_str = _format_conversation_timestamp(timestamp)
    
    # Truncate message for preview
    preview_text = user_message.content[:50]
    if len(user_message.content) > 50:
        preview_text += "..."
    
    # Create expandable conversation item
    with st.expander(f"🗨️ {preview_text}", expanded=False):
        # Display timestamp
        st.markdown(
            f"<div style='color: {COLORS['text_light']}; font-size: 0.85rem; margin-bottom: 0.5rem;'>"
            f"⏰ {timestamp_str}"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Display all messages in session
        for message in session:
            _render_history_message(message)
        
        # Load conversation button
        if on_conversation_select and st.button(
            "📖 Load this conversation",
            key=f"load_conv_{session_idx}",
            help="Load this conversation context"
        ):
            on_conversation_select(session)


def _render_history_message(message: MemoryRecord) -> None:
    """Render a single message in the history panel.
    
    Args:
        message: MemoryRecord to display
    """
    
    is_user = message.role == "user"
    emoji = "👤" if is_user else "💖"
    role_label = "You" if is_user else "BRI"
    
    # Truncate long messages
    content = message.content
    if len(content) > 150:
        content = content[:150] + "..."
    
    # Message styling
    bg_color = COLORS['teal'] if is_user else COLORS['lavender']
    text_color = COLORS['white'] if is_user else COLORS['text_dark']
    
    st.markdown(
        f"""
        <div style="
            background: {bg_color};
            color: {text_color};
            padding: 0.5rem 0.75rem;
            border-radius: 12px;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
            line-height: 1.4;
        ">
            <strong>{emoji} {role_label}:</strong><br>
            {content}
        </div>
        """,
        unsafe_allow_html=True
    )


def _render_memory_wipe_button(video_id: str, memory: Memory) -> None:
    """Render memory wipe button with confirmation.
    
    Args:
        video_id: Current video ID
        memory: Memory instance for wiping conversation
    """
    
    # Check if confirmation is pending
    confirm_key = f"confirm_wipe_{video_id}"
    
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    
    if not st.session_state[confirm_key]:
        # Show initial wipe button
        if st.button(
            "🗑️ Clear Conversation History",
            key=f"wipe_btn_{video_id}",
            help="Delete all conversation history for this video",
            use_container_width=True
        ):
            st.session_state[confirm_key] = True
            st.rerun()
    else:
        # Show confirmation
        st.markdown(
            f"""
            <div style="
                background: rgba(255, 182, 193, 0.2);
                border: 2px solid {COLORS['blush_pink']};
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
                text-align: center;
            ">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚠️</div>
                <div style="font-size: 0.9rem; color: {COLORS['text_dark']}; margin-bottom: 0.75rem;">
                    Are you sure you want to clear all conversation history?
                    This can't be undone!
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                "✅ Yes, clear it",
                key=f"confirm_yes_{video_id}",
                use_container_width=True
            ):
                try:
                    deleted_count = memory.reset_memory(video_id)
                    st.success(f"✨ Cleared {deleted_count} messages! Starting fresh.")
                    st.session_state[confirm_key] = False
                    
                    # Clear conversation history from session state
                    if video_id in st.session_state.get('conversation_history', {}):
                        st.session_state.conversation_history[video_id] = []
                    
                    st.rerun()
                except Exception as e:
                    logger.error(f"Failed to wipe memory: {e}")
                    st.error("Oops! Something went wrong. Please try again. 😅")
        
        with col2:
            if st.button(
                "❌ Cancel",
                key=f"confirm_no_{video_id}",
                use_container_width=True
            ):
                st.session_state[confirm_key] = False
                st.rerun()


def _format_conversation_timestamp(timestamp: datetime) -> str:
    """Format timestamp for conversation display.
    
    Args:
        timestamp: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    now = datetime.now()
    diff = now - timestamp
    
    # Show relative time for recent conversations
    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.total_seconds() < 604800:  # 7 days
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        # Show date for older conversations
        return timestamp.strftime("%b %d, %Y")


def get_conversation_summary(session: List[MemoryRecord]) -> str:
    """Get a summary of a conversation session.
    
    Args:
        session: List of MemoryRecord objects
        
    Returns:
        Summary string
    """
    
    user_messages = [msg for msg in session if msg.role == "user"]
    
    if not user_messages:
        return "Empty conversation"
    
    first_question = user_messages[0].content[:100]
    if len(user_messages[0].content) > 100:
        first_question += "..."
    
    return f"{len(user_messages)} question{'s' if len(user_messages) != 1 else ''}: {first_question}"


def load_conversation_context(
    session: List[MemoryRecord],
    video_id: str
) -> None:
    """Load a conversation session into the current context.
    
    Args:
        session: List of MemoryRecord objects to load
        video_id: Current video ID
    """
    
    # Update session state with loaded conversation
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = {}
    
    st.session_state.conversation_history[video_id] = session
    
    # Show success message
    st.success(f"✨ Loaded conversation with {len(session)} messages!")
    
    logger.info(f"Loaded conversation context for video {video_id}: {len(session)} messages")
