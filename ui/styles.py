"""
Custom CSS Styles for BRI
Implements feminine color scheme with soft touches
"""

import streamlit as st

# Color Palette
COLORS = {
    'blush_pink': '#FFB6C1',
    'lavender': '#E6E6FA',
    'teal': '#40E0D0',
    'cream': '#FFFDD0',
    'soft_gray': '#F5F5F5',
    'text_dark': '#333333',
    'text_light': '#666666',
    'white': '#FFFFFF',
    'accent_pink': '#FF69B4',
    'accent_purple': '#DDA0DD',
}

def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app"""
    
    custom_css = f"""
    <style>
    /* Import Google Fonts - Rounded, friendly typography */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&family=Quicksand:wght@400;500;600&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {{
        font-family: 'Nunito', sans-serif;
        color: {COLORS['text_dark']};
    }}
    
    /* Main container */
    .main {{
        background: linear-gradient(135deg, {COLORS['cream']} 0%, {COLORS['white']} 50%, {COLORS['lavender']} 100%);
        padding: 2rem;
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['lavender']} 0%, {COLORS['blush_pink']} 100%);
        padding: 2rem 1rem;
    }}
    
    [data-testid="stSidebar"] .css-1d391kg {{
        padding-top: 2rem;
    }}
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Quicksand', sans-serif;
        font-weight: 600;
        color: {COLORS['text_dark']};
    }}
    
    h1 {{
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }}
    
    h2 {{
        font-size: 2rem;
        margin-bottom: 0.8rem;
    }}
    
    h3 {{
        font-size: 1.5rem;
        margin-bottom: 0.6rem;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['blush_pink']} 0%, {COLORS['accent_pink']} 100%);
        color: {COLORS['white']};
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-family: 'Quicksand', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 4px 15px rgba(255, 182, 193, 0.3);
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 182, 193, 0.4);
        background: linear-gradient(135deg, {COLORS['accent_pink']} 0%, {COLORS['blush_pink']} 100%);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {{
        background: {COLORS['white']};
        color: {COLORS['accent_pink']};
        border: 2px solid {COLORS['accent_pink']};
        box-shadow: 0 2px 8px rgba(255, 105, 180, 0.2);
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: {COLORS['accent_pink']};
        color: {COLORS['white']};
        border-color: {COLORS['accent_pink']};
    }}
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border-radius: 15px;
        border: 2px solid {COLORS['lavender']};
        padding: 0.75rem 1rem;
        font-family: 'Nunito', sans-serif;
        transition: all 0.3s ease;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COLORS['teal']};
        box-shadow: 0 0 0 3px rgba(64, 224, 208, 0.1);
    }}
    
    /* Cards and containers */
    .stAlert {{
        border-radius: 15px;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }}
    
    /* Info boxes */
    .stAlert[data-baseweb="notification"] {{
        background-color: {COLORS['lavender']};
        border-left: 4px solid {COLORS['accent_purple']};
    }}
    
    /* Success boxes */
    .stSuccess {{
        background-color: rgba(64, 224, 208, 0.1);
        border-left: 4px solid {COLORS['teal']};
        border-radius: 15px;
    }}
    
    /* Warning boxes */
    .stWarning {{
        background-color: rgba(255, 182, 193, 0.1);
        border-left: 4px solid {COLORS['blush_pink']};
        border-radius: 15px;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{
        border: 2px dashed {COLORS['teal']};
        border-radius: 20px;
        padding: 2rem;
        background: {COLORS['white']};
        transition: all 0.3s ease;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: {COLORS['accent_pink']};
        background: rgba(255, 182, 193, 0.05);
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        border-radius: 15px;
        background-color: {COLORS['soft_gray']};
        font-family: 'Quicksand', sans-serif;
        font-weight: 600;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 15px 15px 0 0;
        padding: 0.75rem 1.5rem;
        font-family: 'Quicksand', sans-serif;
        font-weight: 600;
        background-color: {COLORS['soft_gray']};
        color: {COLORS['text_light']};
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {COLORS['blush_pink']} 0%, {COLORS['lavender']} 100%);
        color: {COLORS['white']};
    }}
    
    /* Markdown styling */
    .stMarkdown {{
        font-size: 1rem;
        line-height: 1.6;
    }}
    
    /* Links */
    a {{
        color: {COLORS['teal']};
        text-decoration: none;
        transition: color 0.3s ease;
    }}
    
    a:hover {{
        color: {COLORS['accent_pink']};
    }}
    
    /* Divider */
    hr {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, {COLORS['lavender']}, transparent);
        margin: 2rem 0;
    }}
    
    /* Spinner */
    .stSpinner > div {{
        border-top-color: {COLORS['accent_pink']} !important;
    }}
    
    /* Progress bar */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {COLORS['teal']} 0%, {COLORS['accent_pink']} 100%);
        border-radius: 10px;
    }}
    
    /* Selectbox */
    .stSelectbox > div > div {{
        border-radius: 15px;
        border: 2px solid {COLORS['lavender']};
    }}
    
    /* Slider */
    .stSlider > div > div > div {{
        background: {COLORS['lavender']};
    }}
    
    .stSlider > div > div > div > div {{
        background: {COLORS['accent_pink']};
    }}
    
    /* Chat message styling (for future chat interface) */
    .chat-message {{
        padding: 1rem;
        border-radius: 20px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        animation: fadeIn 0.3s ease;
    }}
    
    .chat-message.user {{
        background: linear-gradient(135deg, {COLORS['teal']} 0%, rgba(64, 224, 208, 0.8) 100%);
        color: {COLORS['white']};
        margin-left: 2rem;
    }}
    
    .chat-message.assistant {{
        background: {COLORS['white']};
        border: 2px solid {COLORS['lavender']};
        margin-right: 2rem;
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {COLORS['soft_gray']};
        border-radius: 10px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, {COLORS['blush_pink']} 0%, {COLORS['lavender']} 100%);
        border-radius: 10px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(180deg, {COLORS['accent_pink']} 0%, {COLORS['accent_purple']} 100%);
    }}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .main {{
            padding: 1rem;
        }}
        
        h1 {{
            font-size: 2rem;
        }}
        
        .chat-message.user,
        .chat-message.assistant {{
            margin-left: 0;
            margin-right: 0;
        }}
    }}
    
    /* Custom utility classes */
    .text-center {{
        text-align: center;
    }}
    
    .text-muted {{
        color: {COLORS['text_light']};
    }}
    
    .rounded-box {{
        border-radius: 20px;
        padding: 1.5rem;
        background: {COLORS['white']};
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }}
    
    .gradient-text {{
        background: linear-gradient(135deg, {COLORS['accent_pink']} 0%, {COLORS['teal']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)

def get_color(color_name: str) -> str:
    """Get color value by name"""
    return COLORS.get(color_name, COLORS['text_dark'])
