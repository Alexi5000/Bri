"""
Custom CSS Styles for BRI
Implements feminine color scheme with soft touches
"""

import streamlit as st

# Color Palette - Dark Theme
COLORS = {
    'bg_dark': '#0a0a0a',           # Main background - deep black
    'bg_secondary': '#1a1a1a',      # Secondary background
    'bg_tertiary': '#2a2a2a',       # Cards and containers
    'text_primary': '#ffffff',      # Primary text - white
    'text_secondary': '#a0a0a0',    # Secondary text - light gray
    'text_muted': '#666666',        # Muted text
    'accent_pink': '#FF69B4',       # Pink accent
    'accent_purple': '#BA68C8',     # Purple accent
    'accent_teal': '#40E0D0',       # Teal accent
    'border': '#333333',            # Border color
    'hover': '#2d2d2d',             # Hover state
}

def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app"""
    
    custom_css = f"""
    <style>
    /* Import Google Fonts - Modern, clean typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ========================================
       HARDENED DARK THEME - Maximum Priority
       ======================================== */
    
    /* CRITICAL: Universal dark background enforcement */
    *, *::before, *::after {{
        box-sizing: border-box;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}
    
    /* Root level - Absolute priority */
    :root {{
        color-scheme: dark;
        --background-color: {COLORS['bg_dark']};
        --text-color: {COLORS['text_primary']};
        --secondary-bg: {COLORS['bg_secondary']};
        --tertiary-bg: {COLORS['bg_tertiary']};
    }}
    
    /* Global Styles - Maximum specificity */
    html, body, #root, [data-testid="stAppViewContainer"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: {COLORS['bg_dark']} !important;
        color: {COLORS['text_primary']} !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    /* Force all backgrounds to dark */
    body, .main, .stApp, [class*="css"], [data-testid="stApp"] {{
        background-color: {COLORS['bg_dark']} !important;
        background-image: none !important;
    }}
    
    /* Main container - Black background */
    .main, [data-testid="stAppViewContainer"] > section {{
        background-color: {COLORS['bg_dark']} !important;
        padding: 1rem 2rem !important;
    }}
    
    /* Streamlit app background - Hardened */
    .stApp, [data-testid="stApp"], [data-testid="stDecoration"] {{
        background-color: {COLORS['bg_dark']} !important;
    }}
    
    /* ========================================
       TEXT COLOR ENFORCEMENT - White Text
       ======================================== */
    
    /* All text elements - Maximum priority white */
    p, span, div, label, li, td, th, a, h1, h2, h3, h4, h5, h6, small,
    strong, em, b, i, u, code, pre, blockquote {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Streamlit specific text elements */
    .stMarkdown, .stMarkdown *, 
    .stText, .stText *, 
    .element-container *,
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"] * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Secondary text - Muted but readable */
    .text-secondary, .stCaption, [data-testid="stCaption"] {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* Block container */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        background-color: {COLORS['bg_dark']} !important;
    }}
    
    /* ========================================
       SIDEBAR - Hardened Dark Theme
       ======================================== */
    
    /* Sidebar container - Maximum priority */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"],
    .css-1d391kg {{
        background-color: {COLORS['bg_secondary']} !important;
        background-image: none !important;
        padding: 2rem 1rem !important;
        border-right: 1px solid {COLORS['border']} !important;
    }}
    
    /* Sidebar text - Absolute white enforcement */
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {{
        color: {COLORS['text_primary']} !important;
        font-weight: 600 !important;
    }}
    
    /* Remove any sidebar background images or gradients */
    [data-testid="stSidebar"]::before,
    [data-testid="stSidebar"]::after {{
        display: none !important;
    }}
    
    /* Sidebar buttons - Dark cards */
    [data-testid="stSidebar"] .stButton > button {{
        background-color: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
        box-shadow: none !important;
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: {COLORS['hover']} !important;
        border-color: {COLORS['accent_pink']} !important;
    }}
    
    /* Force all sidebar button containers to be dark */
    [data-testid="stSidebar"] .stButton {{
        background-color: transparent !important;
    }}
    
    [data-testid="stSidebar"] button {{
        background-color: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
    }}
    
    [data-testid="stSidebar"] button:hover {{
        background-color: {COLORS['hover']} !important;
        border-color: {COLORS['accent_pink']} !important;
    }}
    
    /* All cards and containers - Dark background */
    div[class*="css"] {{
        background-color: transparent !important;
    }}
    
    /* Specific card elements */
    .element-container > div {{
        background-color: transparent !important;
    }}
    
    /* Feature cards and info boxes */
    div[style*="background"] {{
        background-color: {COLORS['bg_tertiary']} !important;
    }}
    
    /* Override any white backgrounds */
    div[style*="background: white"],
    div[style*="background-color: white"],
    div[style*="background: #fff"],
    div[style*="background-color: #fff"],
    div[style*="background: #ffffff"],
    div[style*="background-color: #ffffff"] {{
        background-color: {COLORS['bg_tertiary']} !important;
    }}
    
    /* Sidebar specific overrides */
    [data-testid="stSidebar"] div[style*="background"],
    [data-testid="stSidebar"] div[class*="css"] {{
        background-color: transparent !important;
    }}
    
    /* Button base styles in sidebar */
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"],
    [data-testid="stSidebar"] [data-testid="baseButton-primary"] {{
        background-color: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover,
    [data-testid="stSidebar"] [data-testid="baseButton-primary"]:hover {{
        background-color: {COLORS['hover']} !important;
        border-color: {COLORS['accent_pink']} !important;
    }}
    
    /* Headers - White text */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: {COLORS['text_primary']} !important;
        letter-spacing: -0.02em;
    }}
    
    h1 {{
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }}
    
    h2 {{
        font-size: 2rem;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }}
    
    h3 {{
        font-size: 1.5rem;
        margin-bottom: 0.6rem;
        font-weight: 600;
    }}
    
    /* Buttons - Modern dark theme */
    .stButton > button {{
        background: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    
    .stButton > button:hover {{
        background: {COLORS['hover']} !important;
        border-color: {COLORS['accent_pink']} !important;
        transform: translateY(-1px);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Primary action buttons */
    .stButton > button[kind="primary"] {{
        background: {COLORS['accent_pink']} !important;
        border-color: {COLORS['accent_pink']} !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background: {COLORS['accent_purple']} !important;
        border-color: {COLORS['accent_purple']} !important;
    }}
    
    /* Input fields - Dark theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stChatInput > div > div > input {{
        background-color: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
        color: {COLORS['text_primary']} !important;
        transition: all 0.2s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stChatInput > div > div > input:focus {{
        border-color: {COLORS['accent_pink']} !important;
        box-shadow: 0 0 0 2px rgba(255, 105, 180, 0.2) !important;
        outline: none !important;
    }}
    
    /* Placeholder text */
    input::placeholder, textarea::placeholder {{
        color: {COLORS['text_muted']} !important;
    }}
    
    /* Cards and containers - Dark theme */
    .stAlert {{
        background-color: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Info boxes */
    .stAlert[data-baseweb="notification"] {{
        background-color: {COLORS['bg_tertiary']} !important;
        border-left: 3px solid {COLORS['accent_purple']} !important;
    }}
    
    /* Success boxes */
    .stSuccess {{
        background-color: {COLORS['bg_tertiary']} !important;
        border-left: 3px solid {COLORS['accent_teal']} !important;
        border-radius: 8px !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Warning boxes */
    .stWarning {{
        background-color: {COLORS['bg_tertiary']} !important;
        border-left: 3px solid {COLORS['accent_pink']} !important;
        border-radius: 8px !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Error boxes */
    .stError {{
        background-color: {COLORS['bg_tertiary']} !important;
        border-left: 3px solid #ff4444 !important;
        border-radius: 8px !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    /* File uploader - Dark theme */
    [data-testid="stFileUploader"] {{
        border: 2px dashed {COLORS['border']} !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        background-color: {COLORS['bg_tertiary']} !important;
        transition: all 0.2s ease !important;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: {COLORS['accent_pink']} !important;
        background-color: {COLORS['hover']} !important;
    }}
    
    [data-testid="stFileUploader"] * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Expander - Dark theme */
    .streamlit-expanderHeader {{
        background-color: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    .streamlit-expanderContent {{
        background-color: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-top: none !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Tabs - Dark theme */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: {COLORS['bg_dark']} !important;
        border-bottom: 1px solid {COLORS['border']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0 !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        background-color: {COLORS['bg_secondary']} !important;
        color: {COLORS['text_secondary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-bottom: none !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border-color: {COLORS['accent_pink']} !important;
    }}
    
    /* Markdown styling */
    .stMarkdown {{
        font-size: 1rem;
        line-height: 1.6;
    }}
    
    /* Links - Dark theme */
    a {{
        color: {COLORS['accent_teal']} !important;
        text-decoration: none;
        transition: color 0.2s ease;
    }}
    
    a:hover {{
        color: {COLORS['accent_pink']} !important;
    }}
    
    /* Divider - Dark theme */
    hr {{
        border: none;
        height: 1px;
        background: {COLORS['border']};
        margin: 2rem 0;
    }}
    
    /* Spinner - Dark theme */
    .stSpinner > div {{
        border-top-color: {COLORS['accent_pink']} !important;
    }}
    
    /* Progress bar - Dark theme */
    .stProgress > div > div > div {{
        background: {COLORS['accent_pink']} !important;
        border-radius: 4px;
    }}
    
    .stProgress > div > div {{
        background-color: {COLORS['bg_tertiary']} !important;
    }}
    
    /* Selectbox - Dark theme */
    .stSelectbox > div > div {{
        background-color: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Slider - Dark theme */
    .stSlider > div > div > div {{
        background: {COLORS['bg_tertiary']} !important;
    }}
    
    .stSlider > div > div > div > div {{
        background: {COLORS['accent_pink']} !important;
    }}
    
    /* Chat message styling - Dark theme */
    .chat-message {{
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease;
    }}
    
    .chat-message.user {{
        background: {COLORS['accent_teal']} !important;
        color: {COLORS['bg_dark']} !important;
        margin-left: 2rem;
        font-weight: 500;
        border: 1px solid {COLORS['accent_teal']};
    }}
    
    .chat-message.user * {{
        color: {COLORS['bg_dark']} !important;
    }}
    
    .chat-message.assistant {{
        background: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']} !important;
        margin-right: 2rem;
        color: {COLORS['text_primary']} !important;
    }}
    
    .chat-message.assistant * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    .chat-message.assistant p {{
        color: {COLORS['text_primary']} !important;
        margin-bottom: 0.5rem;
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
    
    /* Scrollbar styling - Dark theme */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {COLORS['bg_secondary']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['border']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['text_muted']};
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
    
    /* Custom utility classes - Dark theme */
    .text-center {{
        text-align: center;
    }}
    
    .text-muted {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    .rounded-box {{
        border-radius: 12px;
        padding: 1.5rem;
        background: {COLORS['bg_tertiary']} !important;
        border: 1px solid {COLORS['border']};
    }}
    
    .gradient-text {{
        background: linear-gradient(135deg, {COLORS['accent_pink']} 0%, {COLORS['accent_teal']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Response cards - ensure dark text */
    .stMarkdown p {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Suggestion boxes */
    .element-container {{
        color: {COLORS['text_primary']};
    }}
    
    /* Info/success/warning boxes - better contrast */
    .stAlert {{
        color: {COLORS['text_primary']} !important;
    }}
    
    .stAlert * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Ensure all container text is readable */
    div[data-testid="stVerticalBlock"] {{
        color: {COLORS['text_primary']};
    }}
    
    /* Video player section - Dark theme */
    .video-player-container {{
        margin-top: 0 !important;
        padding-top: 0.5rem !important;
        background-color: {COLORS['bg_dark']} !important;
    }}
    
    /* Video element */
    video {{
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
    }}
    
    [data-testid="stVideo"] {{
        background-color: {COLORS['bg_tertiary']} !important;
        border-radius: 12px;
        padding: 0.5rem;
    }}
    
    /* Chat section styling */
    .stMarkdown h3 {{
        margin-top: 0.5rem !important;
        margin-bottom: 0.75rem !important;
    }}
    
    /* Fix white text on light backgrounds */
    .stMarkdown, .stText {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Timestamp and metadata text */
    .stCaption {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* Suggestion buttons - better visibility */
    .stButton button[kind="secondary"] {{
        background: {COLORS['text_primary']} !important;
        color: #6A1B9A !important;
        border: 2px solid #E1BEE7 !important;
        font-weight: 600 !important;
    }}
    
    .stButton button[kind="secondary"]:hover {{
        background: #F3E5F5 !important;
        border-color: #BA68C8 !important;
        color: #6A1B9A !important;
    }}
    
    /* CRITICAL: Force all text to be dark and readable */
    p, span, div, label, li, td, th {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Input placeholders */
    input::placeholder, textarea::placeholder {{
        color: {COLORS['text_secondary']} !important;
        opacity: 0.7;
    }}
    
    /* Chat input box */
    .stChatInput input {{
        color: {COLORS['text_primary']} !important;
        background: {COLORS['text_primary']} !important;
    }}
    
    /* Text areas */
    textarea {{
        color: {COLORS['text_primary']} !important;
        background: {COLORS['text_primary']} !important;
    }}
    
    /* All input fields */
    input {{
        color: {COLORS['text_primary']} !important;
        background: {COLORS['text_primary']} !important;
    }}
    
    /* Conversation header */
    [data-testid="stChatMessageContainer"] {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Chat messages - force dark text */
    [data-testid="stChatMessage"] {{
        color: {COLORS['text_primary']} !important;
    }}
    
    [data-testid="stChatMessage"] * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Ensure markdown content is dark */
    .stMarkdown p, .stMarkdown span, .stMarkdown div {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Labels and captions */
    label, .stCaption, small {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Video player controls text */
    [data-testid="stVideo"] + div {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Column content */
    [data-testid="column"] * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Expander content */
    .streamlit-expanderContent {{
        color: {COLORS['text_primary']} !important;
    }}
    
    .streamlit-expanderContent * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Metrics - Dark theme */
    [data-testid="stMetricValue"] {{
        color: {COLORS['text_primary']} !important;
        font-weight: 600 !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* Column backgrounds */
    [data-testid="column"] {{
        background-color: {COLORS['bg_dark']} !important;
    }}
    
    /* Radio buttons and checkboxes */
    .stRadio > label, .stCheckbox > label {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* AGGRESSIVE: Force all sidebar buttons to be dark */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] button[class*="Button"],
    [data-testid="stSidebar"] .row-widget.stButton button {{
        background-color: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px !important;
    }}
    
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    [data-testid="stSidebar"] button[kind="primary"]:hover,
    [data-testid="stSidebar"] button[class*="Button"]:hover,
    [data-testid="stSidebar"] .row-widget.stButton button:hover {{
        background-color: {COLORS['hover']} !important;
        border-color: {COLORS['accent_pink']} !important;
    }}
    
    /* Remove any box shadows from sidebar buttons */
    [data-testid="stSidebar"] button {{
        box-shadow: none !important;
    }}
    
    /* Target Streamlit's internal button classes */
    [data-testid="stSidebar"] .stButton > button[data-testid="baseButton-secondary"] {{
        background-color: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
    }}
    
    /* Force button container backgrounds */
    [data-testid="stSidebar"] .stButton,
    [data-testid="stSidebar"] .row-widget {{
        background-color: transparent !important;
    }}
    
    /* Override Streamlit's default white button background */
    [data-testid="stSidebar"] button[class*="st-"] {{
        background-color: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
    }}
    
    /* ========================================
       HARDENING - Nuclear Option Overrides
       ======================================== */
    
    /* Eliminate ALL white backgrounds */
    [style*="background: white"] *,
    [style*="background-color: white"] *,
    [style*="background: #fff"] *,
    [style*="background-color: #fff"] *,
    [style*="background: #ffffff"] *,
    [style*="background-color: #ffffff"] * {{
        background-color: {COLORS['bg_tertiary']} !important;
    }}
    
    /* Force all containers to respect dark theme */
    div[class], section[class], article[class], aside[class] {{
        background-color: transparent !important;
    }}
    
    /* Ensure no light colors leak through */
    [class*="st-"] {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Maximum priority text color */
    * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Exception: User input should be visible */
    input, textarea, select {{
        color: {COLORS['text_primary']} !important;
        background-color: {COLORS['bg_tertiary']} !important;
    }}
    
    /* Exception: Buttons keep their styling */
    button, button * {{
        color: {COLORS['text_primary']} !important;
    }}
    
    /* Exception: Links keep accent color */
    a {{
        color: {COLORS['accent_teal']} !important;
    }}
    
    a:hover {{
        color: {COLORS['accent_pink']} !important;
    }}
    
    /* ========================================
       VIDEO PLAYER CONTROLS - Dark Theme
       ======================================== */
    
    /* ALL buttons in columns - Nuclear option */
    [data-testid="column"] button,
    [data-testid="column"] .stButton > button,
    [data-testid="column"] [data-testid="baseButton-secondary"],
    .video-player-container button,
    .video-player-container .stButton > button {{
        background-color: {COLORS['bg_tertiary']} !important;
        background: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
        box-shadow: none !important;
    }}
    
    [data-testid="column"] button:hover,
    [data-testid="column"] .stButton > button:hover,
    .video-player-container button:hover {{
        background-color: {COLORS['hover']} !important;
        background: {COLORS['hover']} !important;
        border-color: {COLORS['accent_pink']} !important;
    }}
    
    /* Force button containers in columns to be transparent */
    [data-testid="column"] .stButton,
    [data-testid="column"] .row-widget {{
        background-color: transparent !important;
        background: transparent !important;
    }}
    
    /* Main content area buttons */
    .main button,
    .main .stButton > button {{
        background-color: {COLORS['bg_tertiary']} !important;
        background: {COLORS['bg_tertiary']} !important;
        color: {COLORS['text_primary']} !important;
        border: 1px solid {COLORS['border']} !important;
    }}
    
    .main button:hover,
    .main .stButton > button:hover {{
        background-color: {COLORS['hover']} !important;
        background: {COLORS['hover']} !important;
        border-color: {COLORS['accent_pink']} !important;
    }}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)

def get_color(color_name: str) -> str:
    """Get color value by name"""
    return COLORS.get(color_name, COLORS['bg_dark'])
