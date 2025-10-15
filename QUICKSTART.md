# BRI Quick Start Guide

Get BRI up and running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Groq API key ([Get one free here](https://console.groq.com))

## Installation Steps

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd bri-video-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key
# On Windows: notepad .env
# On Mac/Linux: nano .env
```

**Required:** Set your `GROQ_API_KEY` in the `.env` file:
```
GROQ_API_KEY=your_actual_api_key_here
```

### 3. Validate Setup (Optional but Recommended)

```bash
python scripts/validate_setup.py
```

This will check:
- ✓ Python version
- ✓ Dependencies installed
- ✓ Configuration valid
- ✓ Directories created
- ✓ Redis availability (optional)

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Start the Application

**Terminal 1 - Start MCP Server:**
```bash
python mcp_server/main.py
```

**Terminal 2 - Start Streamlit UI:**
```bash
streamlit run app.py
```

### 6. Open in Browser

Navigate to: `http://localhost:8501`

## First Steps

1. **Upload a Video**: Drag and drop a video file (MP4, AVI, MOV, or MKV)
2. **Wait for Processing**: BRI will analyze your video (this takes a minute)
3. **Start Chatting**: Ask questions like:
   - "What's happening in this video?"
   - "What did they say at 1:30?"
   - "Show me all the scenes with a dog"
   - "Summarize the main points"

## Common Issues

### "GROQ_API_KEY is required"
- Make sure you created a `.env` file (not `.env.example`)
- Add your actual API key from [console.groq.com](https://console.groq.com)

### "Connection refused"
- Make sure both terminals are running (MCP server + Streamlit)
- Check that ports 8000 and 8501 are available

### Redis warnings
- Redis is optional - set `REDIS_ENABLED=false` in `.env` to disable warnings
- Or install Redis for better performance

## What's Next?

- Check out the full [README.md](README.md) for detailed documentation
- Review [Configuration Options](README.md#configuration) to customize BRI
- Read the [Troubleshooting Guide](README.md#troubleshooting) if you encounter issues

## Need Help?

- Run `python scripts/validate_setup.py` to diagnose issues
- Check the [Requirements](.kiro/specs/bri-video-agent/requirements.md) document
- Review the [Design](.kiro/specs/bri-video-agent/design.md) document

---

**Enjoy using BRI! 💜**
