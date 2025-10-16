"""
Video Library View Component
Displays uploaded videos in a grid layout with thumbnails and metadata
"""

import streamlit as st
import cv2
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

from storage.database import get_all_videos, delete_video as db_delete_video
from storage.file_store import get_file_store

logger = logging.getLogger(__name__)


def generate_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
    """
    Generate a thumbnail from a video at a specific timestamp.
    
    Args:
        video_path: Path to video file
        output_path: Path to save thumbnail
        timestamp: Timestamp in seconds to capture (default: 1.0)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Adjust timestamp if it exceeds video duration
        if timestamp > duration:
            timestamp = duration / 2  # Use middle frame
        
        # Set position to timestamp
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            logger.error(f"Failed to read frame at timestamp {timestamp}")
            return False
        
        # Resize to thumbnail size (320x180 - 16:9 aspect ratio)
        thumbnail = cv2.resize(frame, (320, 180))
        
        # Save thumbnail
        cv2.imwrite(output_path, thumbnail)
        logger.info(f"Generated thumbnail: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return False


def get_or_create_thumbnail(video_id: str, video_path: str) -> Optional[str]:
    """
    Get existing thumbnail or create a new one.
    
    Args:
        video_id: Video identifier
        video_path: Path to video file
        
    Returns:
        Path to thumbnail or None if failed
    """
    file_store = get_file_store()
    cache_dir = file_store.get_cache_directory(video_id)
    thumbnail_path = cache_dir / "thumbnail.jpg"
    
    # Return existing thumbnail if it exists
    if thumbnail_path.exists():
        return str(thumbnail_path)
    
    # Generate new thumbnail
    if generate_thumbnail(video_path, str(thumbnail_path)):
        return str(thumbnail_path)
    
    return None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2:35" or "1:23:45")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def format_upload_date(timestamp: datetime) -> str:
    """
    Format upload timestamp to human-readable format.
    
    Args:
        timestamp: Upload datetime
        
    Returns:
        Formatted date string
    """
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days == 0:
        if diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    else:
        return timestamp.strftime("%b %d, %Y")


def get_status_emoji(status: str) -> str:
    """
    Get emoji for processing status.
    
    Args:
        status: Processing status
        
    Returns:
        Emoji string
    """
    status_emojis = {
        'pending': '⏳',
        'processing': '⚙️',
        'complete': '✅',
        'error': '❌'
    }
    return status_emojis.get(status, '❓')


def get_status_text(status: str) -> str:
    """
    Get friendly text for processing status.
    
    Args:
        status: Processing status
        
    Returns:
        Status text
    """
    status_texts = {
        'pending': 'Pending',
        'processing': 'Processing...',
        'complete': 'Ready',
        'error': 'Error'
    }
    return status_texts.get(status, 'Unknown')


def render_video_card(video: Dict, col) -> None:
    """
    Render a single video card in the grid.
    
    Args:
        video: Video data dictionary
        col: Streamlit column to render in
    """
    with col:
        # Create card container
        with st.container():
            video_id = video['video_id']
            filename = video['filename']
            file_path = video['file_path']
            duration = video.get('duration', 0)
            status = video.get('processing_status', 'pending')
            upload_time = video.get('upload_timestamp')
            
            # Parse upload timestamp if it's a string
            if isinstance(upload_time, str):
                try:
                    upload_time = datetime.fromisoformat(upload_time)
                except (ValueError, TypeError):
                    upload_time = datetime.now()
            
            # Get or create thumbnail
            thumbnail_path = get_or_create_thumbnail(video_id, file_path)
            
            # Display thumbnail
            if thumbnail_path and Path(thumbnail_path).exists():
                st.image(thumbnail_path, use_container_width=True)
            else:
                # Placeholder if thumbnail generation failed
                st.markdown(
                    """
                    <div style="
                        width: 100%;
                        height: 180px;
                        background: linear-gradient(135deg, #FFB6C1 0%, #E6E6FA 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 15px;
                        font-size: 3rem;
                    ">
                        🎬
                    </div>
                    """,
                    unsafe_allow_html=True  # noqa: S308
                )
            
            # Video title
            st.markdown(f"**{filename[:30]}{'...' if len(filename) > 30 else ''}**")
            
            # Metadata row
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"⏱️ {format_duration(duration)}")
            with col2:
                status_emoji = get_status_emoji(status)
                status_text = get_status_text(status)
                st.caption(f"{status_emoji} {status_text}")
            
            # Upload date
            st.caption(f"📅 {format_upload_date(upload_time)}")
            
            # Action buttons
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button("💬 Chat", key=f"chat_{video_id}", use_container_width=True):
                    st.session_state.current_video_id = video_id
                    st.session_state.current_view = 'chat'
                    st.rerun()
            
            with btn_col2:
                if st.button("🗑️ Delete", key=f"delete_{video_id}", use_container_width=True):
                    st.session_state.delete_confirm_video_id = video_id
                    st.rerun()
            
            # Show delete confirmation dialog
            if st.session_state.get('delete_confirm_video_id') == video_id:
                st.warning("⚠️ Are you sure?")
                conf_col1, conf_col2 = st.columns(2)
                
                with conf_col1:
                    if st.button("✅ Yes", key=f"confirm_{video_id}", use_container_width=True):
                        delete_video(video_id, file_path)
                        st.session_state.delete_confirm_video_id = None
                        st.rerun()
                
                with conf_col2:
                    if st.button("❌ No", key=f"cancel_{video_id}", use_container_width=True):
                        st.session_state.delete_confirm_video_id = None
                        st.rerun()
            
            # Add spacing
            st.markdown("<br>", unsafe_allow_html=True)  # noqa: S308


def delete_video(video_id: str, file_path: str) -> None:
    """
    Delete a video and its associated data.
    
    Args:
        video_id: Video identifier
        file_path: Path to video file
    """
    try:
        # Delete from file system
        file_store = get_file_store()
        file_store.delete_video(video_id)
        
        # Delete from database
        db_delete_video(video_id)
        
        # Update session state
        st.session_state.uploaded_videos = [
            v for v in st.session_state.uploaded_videos
            if v['video_id'] != video_id
        ]
        
        # Show success message
        st.success("🎉 Video deleted successfully!")
        logger.info(f"Deleted video: {video_id}")
        
    except Exception as e:
        st.error(f"😔 Oops! Couldn't delete the video: {str(e)}")
        logger.error(f"Failed to delete video {video_id}: {e}")


def render_video_library() -> None:
    """
    Render the video library view with grid layout.
    """
    # Header
    st.markdown("# 📚 Video Library")
    st.markdown("*Your collection of videos, ready for exploration!*")
    st.markdown("---")
    
    # Refresh videos from database
    try:
        videos = get_all_videos()
        st.session_state.uploaded_videos = [
            {
                'video_id': video['video_id'],
                'filename': video['filename'],
                'file_path': video['file_path'],
                'duration': video['duration'],
                'processing_status': video['processing_status'],
                'upload_timestamp': video['upload_timestamp']
            }
            for video in videos
        ]
    except Exception as e:
        logger.error(f"Failed to load videos: {e}")
        st.error("😔 Oops! Couldn't load your videos. Try refreshing the page.")
        return
    
    # Check if there are videos
    if not st.session_state.uploaded_videos:
        # Empty state
        st.markdown(
            """
            <div style="
                text-align: center;
                padding: 4rem 2rem;
                background: linear-gradient(135deg, rgba(255, 182, 193, 0.1) 0%, rgba(230, 230, 250, 0.1) 100%);
                border-radius: 20px;
                margin: 2rem 0;
            ">
                <div style="font-size: 5rem; margin-bottom: 1rem;">📹</div>
                <h2 style="color: #1a1a1a; margin-bottom: 1rem;">No videos yet!</h2>
                <p style="color: #1a1a1a; font-size: 1.1rem;">
                    Upload your first video to get started with BRI.<br>
                    I'm excited to help you explore your content! 💜
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Upload button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📤 Upload Video", use_container_width=True, type="primary"):
                st.session_state.current_view = 'welcome'
                st.rerun()
        
        return
    
    # Stats row
    total_videos = len(st.session_state.uploaded_videos)
    ready_videos = sum(1 for v in st.session_state.uploaded_videos if v.get('processing_status') == 'complete')
    processing_videos = sum(1 for v in st.session_state.uploaded_videos if v.get('processing_status') == 'processing')
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Total Videos", total_videos, delta=None)
    
    with stat_col2:
        st.metric("Ready to Chat", ready_videos, delta=None)
    
    with stat_col3:
        st.metric("Processing", processing_videos, delta=None)
    
    with stat_col4:
        if st.button("📤 Upload New", use_container_width=True):
            st.session_state.current_view = 'welcome'
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter options
    filter_col1, filter_col2 = st.columns([3, 1])
    
    with filter_col1:
        search_query = st.text_input(
            "🔍 Search videos",
            placeholder="Search by filename...",
            label_visibility="collapsed"
        )
    
    with filter_col2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Ready", "Processing", "Pending", "Error"],
            label_visibility="collapsed"
        )
    
    # Filter videos
    filtered_videos = st.session_state.uploaded_videos
    
    if search_query:
        filtered_videos = [
            v for v in filtered_videos
            if search_query.lower() in v['filename'].lower()
        ]
    
    if status_filter != "All":
        status_map = {
            "Ready": "complete",
            "Processing": "processing",
            "Pending": "pending",
            "Error": "error"
        }
        filtered_videos = [
            v for v in filtered_videos
            if v.get('processing_status') == status_map[status_filter]
        ]
    
    # Show filtered count
    if len(filtered_videos) != total_videos:
        st.caption(f"Showing {len(filtered_videos)} of {total_videos} videos")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render video grid (3 columns)
    if filtered_videos:
        # Sort by upload timestamp (newest first)
        filtered_videos.sort(
            key=lambda v: v.get('upload_timestamp', ''),
            reverse=True
        )
        
        # Create grid
        num_cols = 3
        for i in range(0, len(filtered_videos), num_cols):
            cols = st.columns(num_cols)
            for j, col in enumerate(cols):
                if i + j < len(filtered_videos):
                    render_video_card(filtered_videos[i + j], col)
    else:
        st.info("🔍 No videos match your search criteria.")
