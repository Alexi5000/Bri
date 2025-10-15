"""Lazy loading utilities for UI components."""

import streamlit as st
from typing import List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LazyImageLoader:
    """Lazy loader for images to improve UI performance.
    
    Loads images on-demand rather than all at once, reducing initial load time
    and memory usage.
    """
    
    def __init__(self, batch_size: int = 3):
        """Initialize lazy image loader.
        
        Args:
            batch_size: Number of images to load per batch
        """
        self.batch_size = batch_size
    
    def render_lazy_images(
        self,
        image_paths: List[str],
        timestamps: Optional[List[float]] = None,
        columns: int = 3,
        on_timestamp_click: Optional[callable] = None
    ) -> None:
        """Render images with lazy loading support.
        
        Args:
            image_paths: List of image file paths
            timestamps: Optional list of timestamps corresponding to images
            columns: Number of columns for image grid
            on_timestamp_click: Optional callback when timestamp is clicked
        """
        if not image_paths:
            return
        
        # Initialize session state for loaded images
        if 'loaded_images' not in st.session_state:
            st.session_state.loaded_images = set()
        
        # Calculate how many images to show
        total_images = len(image_paths)
        loaded_count = len(st.session_state.loaded_images)
        
        # Show loaded images plus next batch
        images_to_show = min(loaded_count + self.batch_size, total_images)
        
        # Render images in grid
        for i in range(0, images_to_show, columns):
            cols = st.columns(columns)
            for j in range(columns):
                idx = i + j
                if idx < images_to_show:
                    with cols[j]:
                        self._render_single_image(
                            image_paths[idx],
                            timestamps[idx] if timestamps else None,
                            idx,
                            on_timestamp_click
                        )
                        # Mark as loaded
                        st.session_state.loaded_images.add(idx)
        
        # Show "Load More" button if there are more images
        if images_to_show < total_images:
            remaining = total_images - images_to_show
            if st.button(
                f"📸 Load {min(self.batch_size, remaining)} more images ({remaining} remaining)",
                key="load_more_images"
            ):
                st.rerun()
    
    def _render_single_image(
        self,
        image_path: str,
        timestamp: Optional[float],
        idx: int,
        on_timestamp_click: Optional[callable]
    ) -> None:
        """Render a single image with optional timestamp.
        
        Args:
            image_path: Path to image file
            timestamp: Optional timestamp for the image
            idx: Image index
            on_timestamp_click: Optional callback for timestamp clicks
        """
        try:
            # Check if image exists
            if not Path(image_path).exists():
                st.caption("⚠️ Image not found")
                return
            
            # Display image
            st.image(image_path, use_container_width=True)
            
            # Display timestamp button if provided
            if timestamp is not None:
                timestamp_str = self._format_timestamp(timestamp)
                if st.button(
                    f"⏱️ {timestamp_str}",
                    key=f"lazy_frame_ts_{idx}_{timestamp}",
                    help="Click to jump to this moment"
                ):
                    if on_timestamp_click:
                        on_timestamp_click(timestamp)
                    else:
                        st.session_state["clicked_timestamp"] = timestamp
                        st.rerun()
        
        except Exception as e:
            logger.warning(f"Failed to render image {image_path}: {e}")
            st.caption("⚠️ Failed to load image")
    
    def _format_timestamp(self, seconds: float) -> str:
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
    
    @staticmethod
    def reset_loader() -> None:
        """Reset the lazy loader state."""
        if 'loaded_images' in st.session_state:
            st.session_state.loaded_images = set()


class LazyListLoader:
    """Lazy loader for lists to improve UI performance with pagination."""
    
    def __init__(self, items_per_page: int = 10):
        """Initialize lazy list loader.
        
        Args:
            items_per_page: Number of items to show per page
        """
        self.items_per_page = items_per_page
    
    def render_paginated_list(
        self,
        items: List,
        render_item: callable,
        key_prefix: str = "lazy_list"
    ) -> None:
        """Render a paginated list with lazy loading.
        
        Args:
            items: List of items to render
            render_item: Function to render a single item
            key_prefix: Prefix for session state keys
        """
        if not items:
            return
        
        # Initialize pagination state
        page_key = f"{key_prefix}_page"
        if page_key not in st.session_state:
            st.session_state[page_key] = 0
        
        total_items = len(items)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        current_page = st.session_state[page_key]
        
        # Calculate slice indices
        start_idx = current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        
        # Render items for current page
        for item in items[start_idx:end_idx]:
            render_item(item)
        
        # Render pagination controls
        if total_pages > 1:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if current_page > 0:
                    if st.button("⬅️ Previous", key=f"{key_prefix}_prev"):
                        st.session_state[page_key] -= 1
                        st.rerun()
            
            with col2:
                st.markdown(
                    f"<div style='text-align: center; padding: 0.5rem;'>"
                    f"Page {current_page + 1} of {total_pages}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            
            with col3:
                if current_page < total_pages - 1:
                    if st.button("Next ➡️", key=f"{key_prefix}_next"):
                        st.session_state[page_key] += 1
                        st.rerun()
