"""
Welcome Screen Component for BRI
Implements friendly greeting, introduction, and upload prompt
"""

import streamlit as st


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
            <p style='font-size: 1.3rem; color: #666; font-weight: 300; margin-bottom: 0.5rem;'>
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
                <p style='font-size: 1.2rem; line-height: 1.8; color: #555;'>
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
            <h2 style='font-size: 2rem; color: #333; margin-bottom: 1rem;'>
                🎥 Ready when you are!
            </h2>
            <p style='font-size: 1.1rem; color: #666; margin-bottom: 1.5rem;'>
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
            <p style='font-size: 0.95rem; color: #999; font-style: italic;'>
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
            <h3 style='font-size: 1.5rem; color: #333; margin-bottom: 1.5rem;'>
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
            <p style='font-size: 1rem; color: #888;'>
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
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            text-align: center;
            height: 100%;
            transition: transform 0.3s ease;
        '>
            <div style='font-size: 3rem; margin-bottom: 0.5rem;'>
                {emoji}
            </div>
            <h4 style='font-size: 1.2rem; color: #333; margin-bottom: 0.5rem; font-weight: 600;'>
                {title}
            </h4>
            <p style='font-size: 0.95rem; color: #666; line-height: 1.5;'>
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def _handle_upload(uploaded_file):
    """
    Handle video file upload with friendly confirmation.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
    """
    # Show friendly confirmation message
    st.success(
        f"✨ Got it! I received **{uploaded_file.name}**. "
        "Let me take a look... (Upload functionality will be fully implemented in Task 17)"
    )
    
    # Show file details in a friendly way
    file_size_mb = uploaded_file.size / (1024 * 1024)
    
    st.markdown(
        f"""
        <div style='
            background: rgba(64, 224, 208, 0.1);
            border-left: 4px solid #40E0D0;
            border-radius: 15px;
            padding: 1rem 1.5rem;
            margin: 1rem 0;
        '>
            <p style='margin: 0; color: #333;'>
                📹 <strong>File:</strong> {uploaded_file.name}<br>
                📊 <strong>Size:</strong> {file_size_mb:.2f} MB<br>
                🎬 <strong>Type:</strong> {uploaded_file.type}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Encouraging next steps message
    st.info(
        "🎉 Once I finish processing (coming in Task 17-18), "
        "you'll be able to ask me anything about this video!"
    )
    
    # Show what's coming next
    with st.expander("🔮 What happens next?"):
        st.markdown(
            """
            When video processing is fully implemented, I'll:
            
            1. 🎞️ **Extract key frames** from your video
            2. 🖼️ **Describe what's happening** in each scene
            3. 🎤 **Transcribe any audio** with timestamps
            4. 🔍 **Detect objects and people** throughout
            5. ✅ **Let you know** when I'm ready to chat!
            
            Then you can ask me things like:
            - "What happens at 2:30?"
            - "Show me all the scenes with a dog"
            - "Summarize the first minute"
            - "What did they say about the project?"
            
            Pretty cool, right? 😊
            """
        )


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
            <h2 style='color: #666; font-weight: 400; margin-bottom: 1rem;'>
                No videos yet!
            </h2>
            <p style='font-size: 1.1rem; color: #888;'>
                Upload your first video to get started 🚀
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
