"""
Chat Window Component for BRI
Provides conversational interface with message history and input
"""

import streamlit as st
from datetime import datetime
from typing import List
import logging

from models.memory import MemoryRecord
from models.responses import AssistantMessageResponse
from ui.styles import COLORS

logger = logging.getLogger(__name__)


def render_chat_window(
    video_id: str,
    conversation_history: List[MemoryRecord],
    on_send_message: callable
) -> None:
    """Render the chat window interface with message history and input.
    
    Args:
        video_id: Current video ID being discussed
        conversation_history: List of previous messages
        on_send_message: Callback function to handle new messages
    """
    
    # Chat container with custom styling
    st.markdown("""
        <style>
        .chat-container {
            max-height: 600px;
            overflow-y: auto;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .message-wrapper {
            margin-bottom: 1rem;
            animation: fadeIn 0.3s ease;
        }
        
        .message-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            gap: 0.5rem;
        }
        
        .message-role {
            font-weight: 600;
            font-family: 'Quicksand', sans-serif;
        }
        
        .message-timestamp {
            font-size: 0.85rem;
            color: #666;
        }
        
        .message-content {
            padding: 1rem 1.25rem;
            border-radius: 20px;
            line-height: 1.6;
            word-wrap: break-word;
        }
        
        .user-message .message-content {
            background: linear-gradient(135deg, #26C6DA 0%, #00ACC1 100%);
            color: white;
            margin-left: 2rem;
            border-bottom-right-radius: 5px;
            font-weight: 500;
        }
        
        .assistant-message .message-content {
            background: #2a2a2a;
            border: 1px solid #333333;
            margin-right: 2rem;
            border-bottom-left-radius: 5px;
            color: #333333;
        }
        
        .assistant-message .message-content * {
            color: #333333 !important;
        }
        
        .user-message .message-role {
            color: #40E0D0;
        }
        
        .assistant-message .message-role {
            color: #FF69B4;
        }
        
        .emoji-icon {
            font-size: 1.2rem;
        }
        
        .input-container {
            position: sticky;
            bottom: 0;
            background: #1a1a1a;
            padding: 1rem;
            border-radius: 20px;
            border: 1px solid #333333;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
            margin-top: 1rem;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display conversation history
    if conversation_history:
        _render_message_history(conversation_history)
    else:
        _render_empty_state()
    
    # Message input area
    _render_message_input(video_id, on_send_message)


def _render_message_history(conversation_history: List[MemoryRecord]) -> None:
    """Render the message history with proper styling."""
    
    chat_container = st.container()
    
    with chat_container:
        for message in conversation_history:
            _render_message(message)
    
    # Auto-scroll to latest message using JavaScript
    st.markdown("""
        <script>
        // Auto-scroll to bottom of chat
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        </script>
    """, unsafe_allow_html=True)


def _render_message(message: MemoryRecord) -> None:
    """Render a single message with appropriate styling.
    
    Args:
        message: MemoryRecord to display
    """
    
    # Determine message type and styling
    is_user = message.role == "user"
    message_class = "user-message" if is_user else "assistant-message"
    emoji = "👤" if is_user else "💖"
    role_label = "You" if is_user else "BRI"
    
    # Format timestamp
    timestamp_str = _format_timestamp(message.timestamp)
    
    # Render message HTML
    message_html = f"""
    <div class="message-wrapper {message_class}">
        <div class="message-header">
            <span class="emoji-icon">{emoji}</span>
            <span class="message-role">{role_label}</span>
            <span class="message-timestamp">{timestamp_str}</span>
        </div>
        <div class="message-content">
            {_format_message_content(message.content)}
        </div>
    </div>
    """
    
    st.markdown(message_html, unsafe_allow_html=True)


def _render_empty_state() -> None:
    """Render empty state when no messages exist."""
    
    st.markdown(f"""
        <div style="text-align: center; padding: 3rem 1rem; color: {COLORS['text_light']};">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
            <h3 style="color: {COLORS['text_light']}; font-weight: 400;">
                Ready to chat!
            </h3>
            <p style="margin-top: 0.5rem;">
                Ask me anything about this video. I'm here to help! ✨
            </p>
        </div>
    """, unsafe_allow_html=True)


def _render_message_input(video_id: str, on_send_message: callable) -> None:
    """Render the message input field and send button.
    
    Args:
        video_id: Current video ID
        on_send_message: Callback function for sending messages
    """
    
    # Create input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # Use columns for input and button
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Text input with unique key per video
        user_input = st.text_input(
            "Message",
            key=f"chat_input_{video_id}",
            placeholder="Ask me anything about this video... 💭",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send", key=f"send_btn_{video_id}", use_container_width=True)
    
    # Handle message sending
    if send_button and user_input.strip():
        on_send_message(user_input.strip())
        # Clear input by rerunning
        st.rerun()
    
    # Add keyboard shortcut hint
    st.markdown("""
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.85rem; color: #444444;">
            Press Enter to send 💌
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def _format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display.
    
    Args:
        timestamp: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    now = datetime.now()
    diff = now - timestamp
    
    # Show relative time for recent messages
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        # Show date for older messages
        return timestamp.strftime("%b %d, %I:%M %p")


def _format_message_content(content: str) -> str:
    """Format message content with emoji support and line breaks.
    
    Args:
        content: Raw message content
        
    Returns:
        HTML-formatted content
    """
    # Replace newlines with <br> tags
    formatted = content.replace("\n", "<br>")
    
    # Ensure emoji rendering
    formatted = formatted.replace(":)", "😊")
    formatted = formatted.replace(":D", "😄")
    formatted = formatted.replace(":(", "😢")
    formatted = formatted.replace(":P", "😛")
    
    return formatted


def render_assistant_response(response: AssistantMessageResponse) -> None:
    """Render an assistant response with frames and suggestions.
    
    Args:
        response: AssistantMessageResponse object with message, frames, and suggestions
    """
    
    # Display main message
    st.markdown(f"""
        <div class="message-wrapper assistant-message">
            <div class="message-header">
                <span class="emoji-icon">💖</span>
                <span class="message-role">BRI</span>
                <span class="message-timestamp">just now</span>
            </div>
            <div class="message-content">
                {_format_message_content(response.message)}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display frames if present
    if response.frames:
        _render_response_frames(response.frames, response.timestamps)
    
    # Display follow-up suggestions
    if response.suggestions:
        _render_suggestions(response.suggestions)


def _render_response_frames(frames: List[str], timestamps: List[float]) -> None:
    """Render frame thumbnails with clickable timestamps.
    
    Args:
        frames: List of frame image paths
        timestamps: List of corresponding timestamps
    """
    
    st.markdown("**Relevant moments:**")
    
    # Display frames in columns
    cols = st.columns(min(len(frames), 3))
    
    for idx, (frame_path, timestamp) in enumerate(zip(frames, timestamps)):
        col_idx = idx % 3
        with cols[col_idx]:
            try:
                st.image(frame_path, use_container_width=True)
                
                # Clickable timestamp button
                if st.button(
                    f"⏱️ {_format_video_timestamp(timestamp)}",
                    key=f"frame_ts_{idx}_{timestamp}",
                    help="Click to jump to this moment in the video"
                ):
                    # Store clicked timestamp in session state
                    st.session_state["clicked_timestamp"] = timestamp
                    st.rerun()
                    
            except Exception as e:
                logger.warning(f"Failed to display frame {frame_path}: {e}")
                st.caption(f"⏱️ {_format_video_timestamp(timestamp)}")


def _render_suggestions(suggestions: List[str]) -> None:
    """Render follow-up question suggestions.
    
    Args:
        suggestions: List of suggested questions
    """
    
    st.markdown(f"""
        <div style="margin-top: 1rem; padding: 1rem; background: {COLORS['soft_gray']}; 
                    border-radius: 15px; border-left: 4px solid {COLORS['accent_pink']};">
            <div style="font-weight: 600; margin-bottom: 0.5rem; color: {COLORS['text_dark']};">
                💡 You might also want to ask:
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Render suggestion buttons
    for idx, suggestion in enumerate(suggestions):
        if st.button(
            suggestion,
            key=f"suggestion_{idx}",
            help="Click to ask this question"
        ):
            # Store selected suggestion in session state
            st.session_state["selected_suggestion"] = suggestion
            st.rerun()


def _format_video_timestamp(seconds: float) -> str:
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


def add_emoji_reactions(message_id: str) -> None:
    """Add emoji reaction support to messages.
    
    Args:
        message_id: ID of the message to add reactions to
    """
    
    # Emoji options
    emojis = ["👍", "❤️", "😊", "🎉", "🤔"]
    
    cols = st.columns(len(emojis))
    
    for idx, emoji in enumerate(emojis):
        with cols[idx]:
            if st.button(emoji, key=f"reaction_{message_id}_{emoji}"):
                # Store reaction in session state
                if "reactions" not in st.session_state:
                    st.session_state.reactions = {}
                
                if message_id not in st.session_state.reactions:
                    st.session_state.reactions[message_id] = []
                
                st.session_state.reactions[message_id].append(emoji)
                st.rerun()
