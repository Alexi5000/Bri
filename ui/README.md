# BRI UI Components

This directory contains the Streamlit UI components for the BRI video assistant.

## Structure

- `styles.py` - Custom CSS styling with feminine color scheme
- `welcome.py` - Welcome screen component (Task 16)
- `library.py` - Video library view (Task 19)
- `chat.py` - Chat window interface (Task 20)
- `player.py` - Video player with timestamp navigation (Task 21)

## Color Palette

The UI uses a warm, feminine color scheme:

- **Blush Pink** (#FFB6C1) - Primary accent color
- **Lavender** (#E6E6FA) - Secondary accent color
- **Teal** (#40E0D0) - Interactive elements
- **Cream** (#FFFDD0) - Background highlights
- **Soft Gray** (#F5F5F5) - Neutral backgrounds

## Typography

- **Primary Font**: Nunito (rounded, friendly sans-serif)
- **Heading Font**: Quicksand (soft, approachable)

## Design Principles

1. **Rounded Edges**: All UI elements use border-radius for soft appearance
2. **Soft Shadows**: Subtle box-shadows for depth without harshness
3. **Smooth Transitions**: All interactive elements have 0.3s ease transitions
4. **Generous Spacing**: Ample padding and margins for breathing room
5. **Gradient Accents**: Linear gradients for visual interest

## Session State Variables

The app maintains the following session state:

- `current_video_id` - Currently selected video
- `conversation_history` - Chat history per video
- `uploaded_videos` - List of uploaded videos
- `current_view` - Current page ('welcome', 'library', 'chat')
- `processing_status` - Video processing status
- `user_message` - Current user input

## Usage

The main app (`app.py`) imports and uses these components:

```python
from ui.styles import apply_custom_styles

# Apply styles at app startup
apply_custom_styles()
```

## Running the App

```bash
streamlit run app.py
```

The app will be available at http://localhost:8501
