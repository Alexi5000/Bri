"""
Welcome Screen Component for BRI
Implements friendly greeting, introduction, and upload prompt
"""

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def render_welcome_screen():
    """
    Render the welcome screen with friendly greeting and upload prompt.
    
    Features:
    - Friendly greeting with BRI introduction
    - Tagline: "Ask. Understand. Remember."
    - Upload prompt with drag-and-drop area
    - Friendly microcopy and emoji touches
    
    Requirements: 1.2, 2.3
    """
    
    # Hero section with greeting
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size: 3.5rem; margin-bottom: 0.5rem;'>
                👋 Hi, I'm BRI!
            </h1>
            <p style='font-size: 1.3rem; color: #222; font-weight: 300; margin-bottom: 0.5rem;'>
                (That's Brianna, but you can call me BRI 💜)
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Tagline
    st.markdown(
        """
        <div style='text-align: center; padding: 0.5rem 0 2rem 0;'>
            <p style='font-size: 1.8rem; font-weight: 600; 
                      background: linear-gradient(135deg, #FF69B4 0%, #40E0D0 100%);
                      -webkit-background-clip: text;
                      -webkit-text-fill-color: transparent;
                      background-clip: text;
                      font-family: "Quicksand", sans-serif;'>
                Ask. Understand. Remember.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Introduction section
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style='text-align: center; padding: 1.5rem;'>
                <p style='font-size: 1.2rem; line-height: 1.8; color: #1a1a1a;'>
                    I'm your friendly video assistant! 🎬✨<br><br>
                    Upload any video and I'll help you explore it through conversation.
                    Ask me questions, find specific moments, or just chat about what's happening.
                    I'll remember everything we discuss, so you can always pick up where we left off!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Upload section
    st.markdown(
        """
        <div style='text-align: center; padding: 1rem 0;'>
            <h2 style='font-size: 2rem; color: #1a1a1a; margin-bottom: 1rem;'>
                🎥 Ready when you are!
            </h2>
            <p style='font-size: 1.1rem; color: #1a1a1a; margin-bottom: 1.5rem;'>
                Drop a video below to start our conversation
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # File uploader with friendly microcopy
    uploaded_file = st.file_uploader(
        label="Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="I work best with MP4, AVI, MOV, or MKV files 📹",
        label_visibility="collapsed"
    )
    
    # Friendly microcopy below uploader
    st.markdown(
        """
        <div style='text-align: center; padding: 0.5rem 0 2rem 0;'>
            <p style='font-size: 0.95rem; color: #444; font-style: italic;'>
                💡 Tip: I can handle videos up to 500MB. The shorter the video, the faster I can help!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Handle file upload
    if uploaded_file is not None:
        _handle_upload(uploaded_file)
    
    # Feature highlights
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 1rem 0 0.5rem 0;'>
            <h3 style='font-size: 1.5rem; color: #1a1a1a; margin-bottom: 1.5rem;'>
                ✨ What I can do for you
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        _render_feature_card(
            emoji="🔍",
            title="Find Moments",
            description="Ask me to find specific scenes, objects, or people in your video"
        )
    
    with col2:
        _render_feature_card(
            emoji="💬",
            title="Natural Chat",
            description="Talk to me like a friend—I understand follow-up questions and context"
        )
    
    with col3:
        _render_feature_card(
            emoji="🧠",
            title="Remember Everything",
            description="I keep track of our conversations so you never have to repeat yourself"
        )
    
    # Footer with encouraging message
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <p style='font-size: 1rem; color: #333;'>
                🌟 I'm here to make video exploration easy and fun!<br>
                Upload your first video and let's get started! 🚀
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def _render_feature_card(emoji: str, title: str, description: str):
    """
    Render a feature highlight card.
    
    Args:
        emoji: Emoji icon for the feature
        title: Feature title
        description: Feature description
    """
    st.markdown(
        f"""
        <div style='
            background: #2a2a2a;
            border-radius: 20px;
            padding: 1.5rem;
            border: 1px solid #333333;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            text-align: center;
            height: 100%;
            transition: transform 0.3s ease;
        '>
            <div style='font-size: 3rem; margin-bottom: 0.5rem;'>
                {emoji}
            </div>
            <h4 style='font-size: 1.2rem; color: #1a1a1a; margin-bottom: 0.5rem; font-weight: 600;'>
                {title}
            </h4>
            <p style='font-size: 0.95rem; color: #1a1a1a; line-height: 1.5;'>
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def _handle_upload(uploaded_file):
    """
    Handle video file upload with friendly confirmation.
    
    Validates the file, saves it to storage, creates database record,
    and displays friendly confirmation or error messages.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.6
    """
    from services.application import get_application_service
    from services.error_handler import ErrorHandler
    
    try:
        # Show initial friendly message and route persistence through the production middle layer.
        with st.spinner("Got it! Let me take a look... 🔍"):
            service = get_application_service()
            result = service.upload_video(uploaded_file, start_processing=False)
            if not result.ok or not result.video:
                st.error(f"😅 {result.message}")
                st.info("💡 Try uploading a different video that meets the requirements!")
                return

            video = result.video
            video_id = video.video_id
            # file_path is intentionally not surfaced to the UI here;
            # it's read from the database when the chat panel needs it.
            duration = video.duration

            # Add to session state from the typed middle-layer result.
            if 'uploaded_videos' not in st.session_state:
                st.session_state.uploaded_videos = []

            st.session_state.uploaded_videos.append({
                'video_id': video.video_id,
                'filename': video.filename,
                'file_path': video.file_path,
                'duration': video.duration,
                'processing_status': video.processing_status,
                'thumbnail_path': video.thumbnail_path,
                'upload_timestamp': video.upload_timestamp,
            })
        
        # Show friendly success message
        st.success(
            f"✨ Perfect! I've got **{uploaded_file.name}** saved and ready to go!"
        )
        
        # Show file details in a friendly way
        file_size_mb = uploaded_file.size / (1024 * 1024)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration > 0 else "Unknown"
        
        st.markdown(
            f"""
            <div style='
                background: rgba(64, 224, 208, 0.1);
                border-left: 4px solid #40E0D0;
                border-radius: 15px;
                padding: 1rem 1.5rem;
                margin: 1rem 0;
            '>
                <p style='margin: 0; color: #1a1a1a;'>
                    📹 <strong>File:</strong> {uploaded_file.name}<br>
                    📊 <strong>Size:</strong> {file_size_mb:.2f} MB<br>
                    ⏱️ <strong>Duration:</strong> {duration_str}<br>
                    🎬 <strong>Type:</strong> {uploaded_file.type}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Start video processing
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; padding: 1rem 0;'>
                <h3 style='font-size: 1.5rem; color: #1a1a1a;'>
                    🔄 Processing Your Video
                </h3>
                <p style='font-size: 1rem; color: #1a1a1a;'>
                    Give me a moment to understand your video...
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Trigger video processing through the production middle layer.
        _process_video_with_progress(video_id)
        
        # Show button to view in library
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📚 View in Library", type="primary", use_container_width=True):
                st.session_state.current_view = 'library'
                st.rerun()
    
    except Exception as e:
        # Catch-all error handler
        logger.error(f"Unexpected error during upload: {e}")
        
        error_msg = ErrorHandler.format_error_for_user(
            e,
            {'upload': True, 'filename': uploaded_file.name}
        )
        st.error(f"😅 {error_msg}")


def _process_video_with_progress(video_id: str):
    """
    Process video progressively with stage-based progress indicators.
    
    Uses progressive processing (3 stages) so user can start chatting quickly.
    
    Args:
        video_id: Video identifier to process
        
    Requirements: 1.3, 3.6, 3.7
    """
    from services.application import get_application_service
    
    try:
        service = get_application_service()
        video = service.get_video(video_id)
        if not video:
            st.error("Video not found!")
            return

        if not service.mcp_client.health().online:
            st.warning(
                "⚠️ The processing server isn't running right now. "
                "Your video is saved, but I'll need the FastAPI MCP service to analyze it. "
                "Please start the service and try processing again!"
            )
            with st.expander("🔧 How to start the FastAPI MCP service"):
                st.code("python mcp_server/main.py", language="bash")
            return

        try:
            result = service.start_processing(video_id)
            logger.info("Progressive processing started: %s", result)
        except Exception as e:
            logger.error(f"Failed to start progressive processing: {e}")
            st.error(f"😅 Couldn't start processing: {str(e)}")
            return
        
        # Show immediate success message
        st.success(
            "✨ **Processing started!** I'm analyzing your video in the background."
        )
        
        # Show stage information
        st.info(
            """
            **📊 Processing Stages:**
            
            1. **Stage 1 (10s):** Extracting frames → You can start chatting!
            2. **Stage 2 (60s):** Analyzing content → Richer responses!
            3. **Stage 3 (120s):** Full intelligence → Complete understanding!
            
            💬 **You can start chatting as soon as Stage 1 completes!**
            """
        )
        
        # Show progress tracking option
        with st.expander("📈 Track Processing Progress"):
            st.markdown(
                """
                Processing is happening in the background. You can:
                - **Start chatting** as soon as frames are extracted (Stage 1)
                - **Check progress** by refreshing this page
                - **View the video** in your library
                
                I'll let you know when each stage completes! 🎉
                """
            )
    
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        st.error(f"😅 Couldn't process video: {str(e)}")


def render_empty_state():
    """
    Render empty state when no videos are uploaded.
    Used as a fallback or in library view.
    """
    st.markdown(
        """
        <div style='text-align: center; padding: 4rem 2rem;'>
            <div style='font-size: 5rem; margin-bottom: 1rem;'>
                🎬
            </div>
            <h2 style='color: #1a1a1a; font-weight: 400; margin-bottom: 1rem;'>
                No videos yet!
            </h2>
            <p style='font-size: 1.1rem; color: #1a1a1a;'>
                Upload your first video to get started 🚀
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
