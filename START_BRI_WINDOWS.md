# 🚀 Start BRI on Windows - Quick Guide

## ✅ Prerequisites (Already Done!)
- [x] Python 3.11+ installed
- [x] Dependencies installed (`pip install -r requirements.txt`)
- [x] `.env` file configured with GROQ_API_KEY
- [x] Database initialized

## 🎯 Start BRI (2 Steps)

### Step 1: Start MCP Server

Open a **NEW** Command Prompt or PowerShell window and run:

```cmd
python -m uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this window open!** The MCP server needs to stay running.

### Step 2: Start Streamlit UI

Open **ANOTHER** Command Prompt or PowerShell window and run:

```cmd
streamlit run app.py
```

You should see:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**Keep this window open too!**

### Step 3: Open BRI in Browser

Your browser should automatically open to:
```
http://localhost:8501
```

If not, manually open your browser and go to that URL.

🎉 **BRI is now running!**

---

## 🧪 Quick Test

1. **Upload a video** (drag & drop or browse)
2. **Wait for processing** (you'll see progress messages)
3. **Ask a question**: "What's happening in this video?"
4. **See the response** with frames and timestamps!

---

## 🛑 Stop BRI

To stop BRI:
1. Press `Ctrl+C` in the Streamlit window
2. Press `Ctrl+C` in the MCP Server window
3. Close both windows

---

## 🔧 Troubleshooting

### "Address already in use" error

**For Port 8000 (MCP Server)**:
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**For Port 8501 (Streamlit)**:
```cmd
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

Then restart the services.

### "Module not found" error

```cmd
pip install -r requirements.txt --force-reinstall
```

### MCP Server not responding

1. Check the MCP Server window for errors
2. Make sure you're in the project root directory
3. Verify `.env` file has GROQ_API_KEY set

### Streamlit shows connection error

1. Make sure MCP Server is running first (Step 1)
2. Wait 5-10 seconds for MCP Server to fully start
3. Then start Streamlit (Step 2)

---

## 📝 Alternative: Use the Batch Script

If you prefer, you can use the automated script:

```cmd
scripts\start_dev.bat
```

This will start both services automatically, but you'll need to open separate windows to see the logs.

---

## 🎥 Test Video Recommendations

For best results, use:
- **Duration**: 30 seconds - 2 minutes
- **Format**: MP4 (most compatible)
- **Content**: Videos with clear speech and visible objects
- **Size**: Under 100MB

Sample test videos:
- Short demo from your phone
- Screen recording
- Download samples from: https://sample-videos.com/

---

## ✨ Features to Test

1. **Video Upload** - Drag & drop or browse
2. **Visual Questions** - "What do you see?"
3. **Audio Questions** - "What did they say?"
4. **Object Detection** - "Show me all the [objects]"
5. **Timestamp Navigation** - "What happens at 0:30?"
6. **Follow-up Questions** - "Tell me more about that"
7. **Suggestions** - Click on suggested questions
8. **Video Player** - Click timestamps to navigate
9. **Conversation History** - See past messages
10. **Multiple Videos** - Upload and switch between videos

---

## 📊 What You Should See

### MCP Server Window:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Streamlit Window:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Browser:
- Welcome screen with BRI's greeting
- Soft colors (blush pink, lavender, teal)
- Upload area for videos
- Friendly, conversational interface

---

## 🆘 Need Help?

If something isn't working:

1. **Check both windows** for error messages
2. **Verify .env file** has your GROQ_API_KEY
3. **Check ports** aren't already in use
4. **Review logs** in the `logs/` directory
5. **Restart both services** (Ctrl+C and start again)

---

## 🎉 Success Indicators

You know BRI is working when:
- ✅ MCP Server shows "Application startup complete"
- ✅ Streamlit shows "You can now view your Streamlit app"
- ✅ Browser opens to http://localhost:8501
- ✅ You see BRI's welcome screen
- ✅ You can upload a video
- ✅ You can ask questions and get responses

---

Enjoy using BRI! 💜
