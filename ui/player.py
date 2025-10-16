"""
Video Player Component for BRI
Provides video playback with timestamp navigation and controls
"""

import streamlit as st
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def render_video_player(
    video_path: str,
    video_id: str,
    current_timestamp: Optional[float] = None,
    timestamps: Optional[List[float]] = None
) -> None:
    """Render video player with timestamp navigation.
    
    Args:
        video_path: Path to video file
        video_id: Video identifier for session state
        current_timestamp: Current playback timestamp in seconds
        timestamps: List of relevant timestamps from conversation
    """
    
    # Initialize session state for this video
    player_key = f"player_{video_id}"
    if player_key not in st.session_state:
        st.session_state[player_key] = {
            "current_time": 0.0,
            "is_playing": False,
            "selected_timestamp": None
        }
    
    # Update current timestamp if provided
    if current_timestamp is not None:
        st.session_state[player_key]["current_time"] = current_timestamp
        st.session_state[player_key]["selected_timestamp"] = current_timestamp
    
    # Player container with custom styling
    st.markdown("""
        <style>
        .video-player-container {
            background: #2a2a2a;
            border-radius: 15px;
            padding: 1rem;
            border: 1px solid #333333;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
            margin-bottom: 1rem;
            margin-top: 0;
        }
        
        .player-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .player-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #6A1B9A;
            font-family: 'Quicksand', sans-serif;
        }
        
        .player-controls {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            margin-top: 1rem;
        }
        
        .timestamp-chip {
            display: inline-block;
            padding: 0.4rem 0.8rem;
            background: linear-gradient(135deg, #E6E6FA 0%, #FFB6C1 100%);
            border-radius: 15px;
            font-size: 0.9rem;
            font-weight: 500;
            color: #333;
            cursor: pointer;
            transition: all 0.2s ease;
            margin: 0.25rem;
        }
        
        .timestamp-chip:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        
        .timestamp-chip.active {
            background: linear-gradient(135deg, #40E0D0 0%, #20B2AA 100%);
            color: white;
        }
        
        .timestamps-section {
            margin-top: 1rem;
            padding: 1rem;
            background: #F9F9F9;
            border-radius: 15px;
        }
        
        .timestamps-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #666;
            font-size: 0.95rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Render player container
    st.markdown('<div class="video-player-container">', unsafe_allow_html=True)
    
    # Player header
    _render_player_header(video_id)
    
    # Video player
    _render_video_component(video_path, video_id, current_timestamp)
    
    # Playback controls
    _render_playback_controls(video_id)
    
    # Timestamp navigation (if timestamps provided)
    if timestamps and len(timestamps) > 0:
        _render_timestamp_navigation(timestamps, video_id)
    
    st.markdown('</div>', unsafe_allow_html=True)


def _render_player_header(video_id: str) -> None:
    """Render player header with title and info.
    
    Args:
        video_id: Video identifier
    """
    
    st.markdown("""
        <div class="player-header">
            <div class="player-title">
                🎬 Video Player
            </div>
        </div>
    """, unsafe_allow_html=True)


def _render_video_component(
    video_path: str,
    video_id: str,
    start_time: Optional[float] = None
) -> None:
    """Render the actual video player component.
    
    Args:
        video_path: Path to video file
        video_id: Video identifier
        start_time: Optional start time in seconds
    """
    
    try:
        # Check if video file exists
        if not Path(video_path).exists():
            st.error(f"Video file not found: {video_path}")
            logger.error(f"Video file not found: {video_path}")
            return
        
        # Get selected timestamp from session state
        player_key = f"player_{video_id}"
        selected_timestamp = st.session_state[player_key].get("selected_timestamp")
        
        # Use selected timestamp if available, otherwise use start_time
        playback_time = selected_timestamp if selected_timestamp is not None else start_time
        
        # Display video with Streamlit's video component
        # Note: Streamlit's video component doesn't support programmatic seeking,
        # but we can provide timestamp information to the user
        st.video(video_path, start_time=int(playback_time) if playback_time else 0)
        
        # Display current timestamp info if set
        if playback_time is not None:
            st.info(f"⏱️ Seeking to: {_format_timestamp(playback_time)}")
        
    except Exception as e:
        st.error(f"Failed to load video: {str(e)}")
        logger.error(f"Failed to load video {video_path}: {e}")


def _render_playback_controls(video_id: str) -> None:
    """Render playback control buttons.
    
    Args:
        video_id: Video identifier
    """
    
    player_key = f"player_{video_id}"
    
    st.markdown('<div class="player-controls">', unsafe_allow_html=True)
    
    # Create columns for controls
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️ Start", key=f"start_{video_id}", help="Jump to start"):
            st.session_state[player_key]["selected_timestamp"] = 0.0
            st.rerun()
    
    with col2:
        if st.button("⏪ -10s", key=f"back10_{video_id}", help="Go back 10 seconds"):
            current = st.session_state[player_key].get("current_time", 0.0)
            st.session_state[player_key]["selected_timestamp"] = max(0.0, current - 10.0)
            st.rerun()
    
    with col3:
        if st.button("⏸️ Pause", key=f"pause_{video_id}", help="Pause playback"):
            st.session_state[player_key]["is_playing"] = False
    
    with col4:
        if st.button("⏩ +10s", key=f"forward10_{video_id}", help="Go forward 10 seconds"):
            current = st.session_state[player_key].get("current_time", 0.0)
            st.session_state[player_key]["selected_timestamp"] = current + 10.0
            st.rerun()
    
    with col5:
        if st.button("🔄 Reset", key=f"reset_{video_id}", help="Reset to beginning"):
            st.session_state[player_key]["selected_timestamp"] = 0.0
            st.session_state[player_key]["current_time"] = 0.0
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def _render_timestamp_navigation(timestamps: List[float], video_id: str) -> None:
    """Render clickable timestamp chips for navigation.
    
    Args:
        timestamps: List of timestamps in seconds
        video_id: Video identifier
    """
    
    player_key = f"player_{video_id}"
    current_timestamp = st.session_state[player_key].get("selected_timestamp")
    
    st.markdown('<div class="timestamps-section">', unsafe_allow_html=True)
    st.markdown('<div class="timestamps-title">📍 Jump to relevant moments:</div>', unsafe_allow_html=True)
    
    # Sort timestamps
    sorted_timestamps = sorted(set(timestamps))
    
    # Create columns for timestamp chips (max 4 per row)
    num_cols = min(4, len(sorted_timestamps))
    cols = st.columns(num_cols)
    
    for idx, timestamp in enumerate(sorted_timestamps):
        col_idx = idx % num_cols
        with cols[col_idx]:
            # Check if this is the active timestamp
            is_active = current_timestamp == timestamp
            
            # Create button for timestamp
            button_label = f"⏱️ {_format_timestamp(timestamp)}"
            if st.button(
                button_label,
                key=f"ts_{video_id}_{idx}",
                help=f"Jump to {_format_timestamp(timestamp)}",
                type="primary" if is_active else "secondary"
            ):
                st.session_state[player_key]["selected_timestamp"] = timestamp
                st.session_state[player_key]["current_time"] = timestamp
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_video_player_with_context(
    video_path: str,
    video_id: str,
    conversation_timestamps: List[float]
) -> None:
    """Render video player synced with conversation context.
    
    This is a convenience function that combines the player with
    conversation-derived timestamps.
    
    Args:
        video_path: Path to video file
        video_id: Video identifier
        conversation_timestamps: Timestamps mentioned in conversation
    """
    
    # Get the most recent timestamp from conversation if available
    current_timestamp = None
    if conversation_timestamps:
        current_timestamp = conversation_timestamps[-1]
    
    render_video_player(
        video_path=video_path,
        video_id=video_id,
        current_timestamp=current_timestamp,
        timestamps=conversation_timestamps
    )


def navigate_to_timestamp(video_id: str, timestamp: float) -> None:
    """Navigate video player to a specific timestamp.
    
    This function can be called from other components (like chat)
    to trigger timestamp navigation.
    
    Args:
        video_id: Video identifier
        timestamp: Target timestamp in seconds
    """
    
    player_key = f"player_{video_id}"
    
    if player_key not in st.session_state:
        st.session_state[player_key] = {
            "current_time": 0.0,
            "is_playing": False,
            "selected_timestamp": None
        }
    
    st.session_state[player_key]["selected_timestamp"] = timestamp
    st.session_state[player_key]["current_time"] = timestamp
    
    logger.info(f"Navigating to timestamp: {timestamp}s for video {video_id}")


def _format_timestamp(seconds: float) -> str:
    """Format timestamp in MM:SS or HH:MM:SS format.
    
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


def get_current_playback_time(video_id: str) -> float:
    """Get the current playback time for a video.
    
    Args:
        video_id: Video identifier
        
    Returns:
        Current playback time in seconds
    """
    
    player_key = f"player_{video_id}"
    
    if player_key in st.session_state:
        return st.session_state[player_key].get("current_time", 0.0)
    
    return 0.0


def extract_timestamps_from_conversation(conversation_history: List) -> List[float]:
    """Extract all timestamps mentioned in conversation history.
    
    Args:
        conversation_history: List of conversation messages
        
    Returns:
        List of unique timestamps in seconds
    """
    
    timestamps = []
    
    for message in conversation_history:
        # Check if message has timestamps attribute
        if hasattr(message, 'timestamps') and message.timestamps:
            timestamps.extend(message.timestamps)
        
        # Also check content for timestamp patterns (MM:SS or HH:MM:SS)
        if hasattr(message, 'content'):
            import re
            # Pattern for timestamps like 1:23 or 01:23:45
            pattern = r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b'
            matches = re.findall(pattern, message.content)
            
            for match in matches:
                hours = 0
                if match[2]:  # HH:MM:SS format
                    hours = int(match[0])
                    minutes = int(match[1])
                    seconds = int(match[2])
                else:  # MM:SS format
                    minutes = int(match[0])
                    seconds = int(match[1])
                
                total_seconds = hours * 3600 + minutes * 60 + seconds
                timestamps.append(float(total_seconds))
    
    # Return unique timestamps sorted
    return sorted(set(timestamps))
