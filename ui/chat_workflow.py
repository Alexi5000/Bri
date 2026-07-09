"""Focused Streamlit workflow for Bri's conversational video analysis view.

This module keeps chat-specific presentation, user input validation, rate limiting,
and progress wiring out of ``app.py``. The only backend dependency it receives is
Bri's application-service facade, preserving a clean Streamlit -> middle-layer
boundary.
"""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

from services.application import BriApplicationService, VideoSummary
from ui.player import (
    extract_timestamps_from_conversation,
    navigate_to_timestamp,
    render_video_player,
)
from ui.shell import render_progress_panel

MESSAGE_COOLDOWN_SECONDS = 2.0
MAX_MESSAGE_CHARS = 5_000


def render_video_chat_workspace(service: BriApplicationService, video: VideoSummary) -> None:
    """Render the two-column video player and chat workspace for one video."""

    st.markdown("# 💬 Chat with BRI")
    st.markdown(
        f"""
        <div style="margin-bottom: 0.5rem; padding: 0.5rem 0;">
            <span style="font-weight: 600; color: #6A1B9A;">📹 {video.filename}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    player_col, chat_col = st.columns([1, 1], gap="medium")
    conversation_history = service.get_conversation_history(video.video_id, limit=20)

    with player_col:
        _render_player(video, conversation_history)

    with chat_col:
        _render_processing_progress(service, video.video_id)
        render_chat_panel(service, video.video_id, conversation_history)


def render_chat_panel(
    service: BriApplicationService, video_id: str, conversation_history: list[Any]
) -> None:
    """Render conversation history, suggestions, and message input for a video."""

    st.markdown("### 💭 Conversation")
    if not conversation_history:
        st.info("👋 Hi! I'm BRI. Ask me anything about this video!")
    else:
        for message in conversation_history:
            _render_message(message)

    _clear_pending_response_flag()
    st.markdown("---")
    _handle_selected_suggestion(service, video_id)
    _render_message_input(service, video_id)
    _render_keyboard_hint()


def process_user_message(service: BriApplicationService, video_id: str, message: str) -> bool:
    """Validate and submit one user message through the application service."""

    validation_error = _validate_message(video_id, message)
    if validation_error:
        st.warning(validation_error) if validation_error.startswith(
            "⚠️"
        ) or validation_error.startswith("⏱️") else st.error(validation_error)
        return False

    st.session_state.last_message_time = time.time()
    result = service.send_message(video_id, message.strip(), timeout_seconds=60.0)
    if result.ok:
        st.session_state.pending_response = result.response
        return True

    st.error(f"😅 {result.message}")
    return False


def _render_player(video: VideoSummary, conversation_history: list[Any]) -> None:
    timestamps = extract_timestamps_from_conversation(conversation_history)
    clicked_timestamp = st.session_state.get("clicked_timestamp")
    if clicked_timestamp is not None:
        navigate_to_timestamp(video.video_id, clicked_timestamp)
        st.session_state["clicked_timestamp"] = None

    render_video_player(
        video_path=video.file_path,
        video_id=video.video_id,
        current_timestamp=None,
        timestamps=timestamps,
    )


def _render_processing_progress(service: BriApplicationService, video_id: str) -> None:
    try:
        progress = service.get_processing_progress(video_id)
    except Exception:
        progress = None
    render_progress_panel(progress)


def _render_message(message: Any) -> None:
    role = getattr(message, "role", "assistant")
    content = getattr(message, "content", "")
    is_user = role == "user"
    label = "You" if is_user else "BRI"
    icon = "👤" if is_user else "💖"
    color = "#26C6DA" if is_user else "#BA68C8"
    bubble_style = (
        "background: linear-gradient(135deg, #26C6DA 0%, #00ACC1 100%); color: white; "
        "margin-left: 1.5rem; border-bottom-right-radius: 4px; font-weight: 500; "
        "box-shadow: 0 2px 8px rgba(38, 198, 218, 0.2);"
        if is_user
        else "background: #2a2a2a; border: 1px solid #333333; margin-right: 1.5rem; "
        "border-bottom-left-radius: 4px; color: #ffffff;"
    )
    st.markdown(
        f"""
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                <span style="font-size: 1.1rem;">{icon}</span>
                <span style="font-weight: 600; color: {color};">{label}</span>
                <span style="font-size: 0.8rem; color: #666;">just now</span>
            </div>
            <div style="padding: 1rem 1.25rem; border-radius: 18px; {bubble_style}">
                {str(content).replace(chr(10), "<br>")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_message_input(service: BriApplicationService, video_id: str) -> None:
    with st.form(key=f"chat_form_{video_id}", clear_on_submit=True):
        user_input = st.text_input(
            "Message",
            placeholder="Ask me anything about this video... 💭",
            label_visibility="collapsed",
            key=f"chat_input_{video_id}",
            max_chars=MAX_MESSAGE_CHARS,
        )
        _, button_col = st.columns([5, 1])
        with button_col:
            submitted = st.form_submit_button("Send", use_container_width=True, type="primary")

        if submitted:
            if process_user_message(service, video_id, user_input):
                st.rerun()


def _handle_selected_suggestion(service: BriApplicationService, video_id: str) -> None:
    suggestion = st.session_state.get("selected_suggestion")
    if not suggestion:
        return
    st.session_state.selected_suggestion = None
    if process_user_message(service, video_id, str(suggestion)):
        st.rerun()


def _validate_message(video_id: str, message: str) -> str | None:
    sanitized = (message or "").strip()
    if not sanitized:
        return "⚠️ Please enter a message"
    if len(sanitized) < 2:
        return "⚠️ Message too short"
    if len(sanitized) > MAX_MESSAGE_CHARS:
        return "⚠️ Message too long. Please keep it under 5,000 characters."
    if not video_id:
        return "No video selected"

    current_time = time.time()
    last_message_time = float(st.session_state.get("last_message_time", 0) or 0)
    remaining = MESSAGE_COOLDOWN_SECONDS - (current_time - last_message_time)
    if remaining > 0:
        return f"⏱️ Please wait {remaining:.1f} seconds before sending another message"
    return None


def _clear_pending_response_flag() -> None:
    if "pending_response" in st.session_state:
        st.session_state.pending_response = None


def _render_keyboard_hint() -> None:
    st.markdown(
        """
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.85rem; color: #444444;">
            Press Enter to send 💌
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_video_chat_workspace", "render_chat_panel", "process_user_message"]
