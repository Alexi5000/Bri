# BRI Video Agent - Windows Local Deployment Guide

Complete guide to deploy and test BRI on Windows (with optional WSL support).

## 🎯 Quick Start (5 Minutes)

### Prerequisites Check

1. **Python 3.11+** installed
   ```cmd
   python --version
   ```
   If not installed, download from: https://www.python.org/downloads/

2. **Git** installed (you already have this)
   ```cmd
   git --version
   ```

3. **Groq API Key** (Required)
   - Get your free API key from: https://console.groq.com/keys
   - Keep it handy for the next step

### Step 1: Configure Environment

1. **Copy the environment template**:
   ```cmd
   copy .env.example .env
   ```

2. **Edit `.env` file** and add your Groq API key:
   ```cmd
   notepad .env
   ```
   
   Replace `your_groq_api_key_here` with your actual Groq API key:
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
   
   Save and close the file.

### Step 2: Install Dependencies

```cmd
pip install -r requirements.txt
```

This will install all required packages (takes 2-3 minutes).

### Step 3: Start BRI

```cmd
scripts\start_dev.bat
```

This script will:
- ✅ Create necessary directories
- ✅ Initialize the database
- ✅ Start the MCP server (port 8000)
- ✅ Start the Streamlit UI (port 8501)

### Step 4: Access BRI

Open your browser and go to:
```
http://localhost:8501
```

🎉 **BRI is now running!**

---

## 📋 Detailed Testing Checklist

### Test 1: Welcome Screen ✨
- [ ] See the welcome screen with BRI's greeting
- [ ] See the tagline "Ask. Understand. Remember."
- [ ] See the upload prompt with friendly message
- [ ] Notice the soft color scheme (blush pink, lavender, teal)

### Test 2: Video Upload 📹
- [ ] Click on "Browse files" or drag-and-drop a video
- [ ] Upload a short video (MP4, AVI, MOV, or MKV)
- [ ] See friendly confirmation message
- [ ] See processing progress indicators
- [ ] Wait for "All set! What would you like to know?" message

**Test Video Suggestions**:
- Use a short video (30 seconds - 2 minutes) for faster processing
- Videos with clear speech work best for transcription
- Videos with visible objects work best for detection

### Test 3: Video Library 📚
- [ ] See your uploaded video in the library
- [ ] See video thumbnail
- [ ] See video metadata (filename, duration, upload date)
- [ ] Click on the video to open chat interface

### Test 4: Chat Interface 💬

**Test Query 1: Visual Description**
```
What's happening in this video?
```
- [ ] Get a descriptive response
- [ ] See relevant frame thumbnails
- [ ] See timestamps
- [ ] See 1-3 follow-up suggestions

**Test Query 2: Audio Transcription**
```
What did they say?
```
- [ ] Get transcript of audio content
- [ ] See timestamps for speech segments
- [ ] Get follow-up suggestions

**Test Query 3: Object Detection**
```
Show me all the [objects] in the video
```
(Replace [objects] with something in your video: people, cars, dogs, etc.)
- [ ] Get list of detected objects
- [ ] See frames where objects appear
- [ ] See timestamps

**Test Query 4: Timestamp Navigation**
```
What happens at 0:30?
```
- [ ] Get description of that specific moment
- [ ] See frame from that timestamp
- [ ] Click timestamp to navigate video player

**Test Query 5: Follow-up Question**
```
Tell me more about that
```
- [ ] Get contextual response based on previous conversation
- [ ] See that BRI remembers the context

### Test 5: Video Player 🎬
- [ ] See video player embedded in the interface
- [ ] Click on a timestamp in a response
- [ ] See video jump to that timestamp
- [ ] Use playback controls (play, pause, seek)

### Test 6: Conversation History 📝
- [ ] See conversation history in the sidebar
- [ ] See all your questions and BRI's responses
- [ ] See timestamps for each message
- [ ] Scroll through conversation history

### Test 7: Follow-up Suggestions 💡
- [ ] See 1-3 suggested questions after each response
- [ ] Click on a suggestion
- [ ] See it automatically submitted as a query
- [ ] Get relevant response

### Test 8: Error Handling 🛡️

**Test Error 1: Tool Failure**
- Disconnect internet briefly and ask a question
- [ ] Get friendly error message (not technical)
- [ ] See suggestion for what to do next

**Test Error 2: Invalid Query**
```
Show me the unicorns
```
- [ ] Get friendly "couldn't find" message
- [ ] Get suggestion to try something else

### Test 9: Memory & Context 🧠
- [ ] Upload a second video
- [ ] Switch between videos
- [ ] See that conversations are separate per video
- [ ] See that BRI remembers context within each video

### Test 10: Performance ⚡
- [ ] Responses come within 3-5 seconds
- [ ] Frame thumbnails load smoothly
- [ ] Video player is responsive
- [ ] No lag when scrolling conversation history

---

## 🔧 Troubleshooting

### Issue: "GROQ_API_KEY not found"
**Solution**: 
1. Make sure you copied `.env.example` to `.env`
2. Edit `.env` and add your actual Groq API key
3. Restart the application

### Issue: "Port 8501 already in use"
**Solution**:
```cmd
# Find what's using the port
netstat -ano | findstr :8501

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Restart BRI
scripts\start_dev.bat
```

### Issue: "MCP Server failed to start"
**Solution**:
```cmd
# Check if port 8000 is available
netstat -ano | findstr :8000

# If blocked, kill the process
taskkill /PID <PID> /F

# Restart BRI
scripts\start_dev.bat
```

### Issue: Video processing is slow
**Solution**:
- Use shorter videos (under 2 minutes) for testing
- Close other applications to free up CPU/memory
- Check that your video format is supported (MP4 works best)

### Issue: "Module not found" errors
**Solution**:
```cmd
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Database errors
**Solution**:
```cmd
# Reinitialize database
python scripts\init_db.py

# Restart BRI
scripts\start_dev.bat
```

---

## 🐧 Optional: Using WSL (Windows Subsystem for Linux)

If you prefer to run BRI in WSL:

### Step 1: Install WSL
```powershell
# In PowerShell (as Administrator)
wsl --install
```

### Step 2: Open WSL Terminal
```cmd
wsl
```

### Step 3: Install Dependencies in WSL
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install FFmpeg (for video processing)
sudo apt install ffmpeg

# Install Redis (optional, for caching)
sudo apt install redis-server
sudo service redis-server start
```

### Step 4: Navigate to Project
```bash
# WSL can access Windows files at /mnt/c/
cd /mnt/c/TechTide/Apps/Bri
```

### Step 5: Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 6: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 7: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with nano or vim
nano .env
# Add your GROQ_API_KEY, save (Ctrl+X, Y, Enter)
```

### Step 8: Start BRI
```bash
# Make script executable
chmod +x scripts/start_dev.sh

# Start BRI
./scripts/start_dev.sh
```

### Step 9: Access BRI
Open your Windows browser and go to:
```
http://localhost:8501
```

---

## 📊 Performance Tips

### For Faster Processing:
1. **Use shorter videos** (30 seconds - 2 minutes) for testing
2. **Close other applications** to free up resources
3. **Use MP4 format** (most optimized)
4. **Enable Redis** for caching (optional but recommended)

### To Enable Redis on Windows:
1. Download Redis for Windows: https://github.com/microsoftarchive/redis/releases
2. Install and start Redis
3. Verify it's running:
   ```cmd
   redis-cli ping
   ```
   Should return: `PONG`

---

## 🎥 Sample Test Videos

For testing, you can use:
1. **Short demo videos** from your phone
2. **Screen recordings** (30-60 seconds)
3. **Sample videos** from: https://sample-videos.com/

Recommended test video characteristics:
- Duration: 30 seconds - 2 minutes
- Format: MP4
- Resolution: 720p or 1080p
- Contains: Clear speech and visible objects

---

## 🛑 Stopping BRI

To stop all services:
1. Press `Ctrl+C` in the terminal where BRI is running
2. Wait for graceful shutdown
3. All services will stop automatically

---

## 📝 Logs and Debugging

### View Logs:
```cmd
# Application logs
type logs\bri.log

# Error logs
type logs\bri_errors.log

# Performance logs
type logs\bri_performance.log
```

### Enable Debug Mode:
Edit `.env` and change:
```
LOG_LEVEL=DEBUG
```
Restart BRI to see detailed logs.

---

## ✅ Success Checklist

After deployment, you should be able to:
- [x] Access BRI at http://localhost:8501
- [x] Upload a video successfully
- [x] Ask questions about the video
- [x] See frame thumbnails in responses
- [x] Navigate video using timestamps
- [x] Get follow-up suggestions
- [x] See conversation history
- [x] Switch between multiple videos

---

## 🆘 Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Verify your `.env` configuration
4. Ensure all dependencies are installed
5. Try restarting BRI

---

## 🎉 Next Steps

Once BRI is running successfully:
1. Try different types of videos
2. Experiment with various queries
3. Test the follow-up suggestions
4. Explore the conversation history
5. Try the timestamp navigation feature

Enjoy using BRI! 💜
