# BRI - Streamlit Cloud Deployment Guide

## Overview

This guide will help you deploy BRI to Streamlit Cloud's free tier for online testing and sharing.

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Streamlit Cloud Account** - Sign up at https://streamlit.io/cloud
3. **Groq API Key** - Get from https://console.groq.com/keys

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

Your repository is already prepared with:
- ✅ `app.py` - Main application file
- ✅ `requirements.txt` - Python dependencies
- ✅ `packages.txt` - System packages (FFmpeg, OpenCV dependencies)
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.streamlit/secrets.toml` - Secrets template (not committed)

### Step 2: Push to GitHub

Your code is already pushed to GitHub at:
```
https://github.com/Alexi5000/Bri.git
```

### Step 3: Sign Up for Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Click "Sign up" or "Get started"
3. Sign in with your GitHub account
4. Authorize Streamlit to access your repositories

### Step 4: Create New App

1. Click "New app" button
2. Select your repository: `Alexi5000/Bri`
3. Select branch: `master`
4. Main file path: `app.py`
5. Click "Advanced settings" before deploying

### Step 5: Configure Secrets

In the Advanced settings, add your secrets:

```toml
# Groq API Configuration
GROQ_API_KEY = "gsk_your_actual_groq_api_key_here"
GROQ_MODEL = "llama-3.1-70b-versatile"
GROQ_TEMPERATURE = "0.7"
GROQ_MAX_TOKENS = "1024"

# Redis Configuration (disabled for free tier)
REDIS_ENABLED = "false"

# Processing Settings (optimized for free tier)
MAX_FRAMES_PER_VIDEO = "15"
FRAME_EXTRACTION_INTERVAL = "3.0"

# Application Settings
DEBUG = "false"
LOG_LEVEL = "INFO"
```

**Important**: Replace `gsk_your_actual_groq_api_key_here` with your actual Groq API key!

### Step 6: Deploy

1. Click "Deploy!"
2. Wait for deployment (5-10 minutes first time)
3. Watch the logs for any errors

### Step 7: Access Your App

Once deployed, you'll get a URL like:
```
https://your-app-name.streamlit.app
```

Share this URL with anyone for testing!

## Important Notes for Free Tier

### Limitations

1. **No MCP Server**: The MCP server architecture won't work on Streamlit Cloud free tier
   - Tools will be called directly from the app
   - No separate backend server

2. **Resource Limits**:
   - 1 GB RAM
   - Limited CPU
   - No persistent storage (files deleted on restart)

3. **Performance**:
   - Slower video processing
   - Limited concurrent users
   - App sleeps after inactivity

### Optimizations for Free Tier

We've already optimized the app:
- ✅ Reduced max frames to 15 (from 20)
- ✅ Increased frame interval to 3.0s (from 2.0s)
- ✅ Disabled Redis caching
- ✅ Optimized model loading

### What Works

- ✅ Video upload (small videos recommended)
- ✅ Frame extraction
- ✅ Image captioning (BLIP)
- ✅ Audio transcription (Whisper)
- ✅ Object detection (YOLO)
- ✅ Conversational interface
- ✅ Conversation history (session-based)

### What Doesn't Work

- ❌ Persistent storage (videos deleted on restart)
- ❌ MCP server architecture
- ❌ Redis caching
- ❌ Database backups
- ❌ Long-running processes

## Troubleshooting

### Deployment Fails

**Error: "Requirements installation failed"**
- Check `requirements.txt` for incompatible packages
- Some packages may not work on Streamlit Cloud
- Try removing optional dependencies

**Error: "App crashed"**
- Check the logs in Streamlit Cloud dashboard
- Look for missing dependencies
- Verify secrets are configured correctly

### App is Slow

**Solutions**:
1. Use shorter videos (30-60 seconds)
2. Reduce MAX_FRAMES_PER_VIDEO in secrets
3. Increase FRAME_EXTRACTION_INTERVAL
4. Test during off-peak hours

### GROQ_API_KEY Not Found

**Solution**:
1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Click "Settings" → "Secrets"
4. Add your GROQ_API_KEY
5. Click "Save"
6. Reboot the app

### Models Not Loading

**Error: "Model download failed"**
- Streamlit Cloud may have network restrictions
- Models are downloaded on first run
- Wait for initial deployment to complete
- Check logs for specific errors

## Testing Your Deployed App

### Quick Test

1. Open your app URL
2. Upload a short video (30 seconds)
3. Wait for processing (2-3 minutes)
4. Ask: "What's happening in this video?"
5. Verify you get a response

### Recommended Test Videos

For Streamlit Cloud free tier:
- **Duration**: 30-60 seconds
- **Format**: MP4
- **Size**: < 50 MB
- **Resolution**: 720p or lower

## Updating Your App

### Method 1: Git Push

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update app"
   git push origin master
   ```
3. Streamlit Cloud auto-deploys on push

### Method 2: Manual Reboot

1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Click "Reboot app"

## Monitoring

### View Logs

1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Click "Manage app" → "Logs"
4. Watch real-time logs

### Check Resource Usage

1. In Streamlit Cloud dashboard
2. View "Resource usage" section
3. Monitor RAM and CPU

## Secrets Management

### Adding Secrets

1. Streamlit Cloud dashboard
2. Your app → Settings → Secrets
3. Add secrets in TOML format
4. Click Save
5. Reboot app

### Updating Secrets

1. Edit secrets in dashboard
2. Click Save
3. App automatically reboots

### Security

- ✅ Secrets are encrypted
- ✅ Not visible in logs
- ✅ Not accessible from browser
- ✅ Only accessible to your app

## Cost Considerations

### Free Tier Includes

- ✅ Unlimited public apps
- ✅ 1 GB RAM per app
- ✅ Community support
- ✅ Automatic HTTPS
- ✅ Custom subdomain

### Upgrade Options

If you need more resources:
- **Starter**: $20/month - More resources
- **Team**: $250/month - Private apps, more resources
- **Enterprise**: Custom pricing

## Alternative Deployment Options

If Streamlit Cloud free tier is too limited:

### Option 1: Heroku
- More resources
- Persistent storage
- Can run MCP server
- Free tier available

### Option 2: Railway
- Modern platform
- Good free tier
- Easy deployment
- Persistent storage

### Option 3: Render
- Free tier available
- Persistent storage
- Can run multiple services
- Good performance

### Option 4: Self-Hosted
- Full control
- No resource limits
- Requires server management
- See `docs/DEPLOYMENT.md`

## Best Practices

### For Free Tier

1. **Optimize Video Size**:
   - Keep videos under 1 minute
   - Use 720p or lower resolution
   - Compress videos before upload

2. **Reduce Processing**:
   - Lower MAX_FRAMES_PER_VIDEO
   - Increase FRAME_EXTRACTION_INTERVAL
   - Skip optional processing steps

3. **Manage Memory**:
   - Clear session state when done
   - Don't store large objects
   - Use lazy loading

4. **User Experience**:
   - Show processing progress
   - Set expectations (slower processing)
   - Provide clear error messages

## Support

### Streamlit Cloud Issues

- Documentation: https://docs.streamlit.io/streamlit-community-cloud
- Community Forum: https://discuss.streamlit.io
- GitHub Issues: https://github.com/streamlit/streamlit/issues

### BRI-Specific Issues

- Check logs in Streamlit Cloud dashboard
- Review `docs/TROUBLESHOOTING.md`
- Check GitHub repository issues

## Summary

### Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Streamlit Cloud account created
- [ ] New app created in Streamlit Cloud
- [ ] Secrets configured (GROQ_API_KEY)
- [ ] App deployed successfully
- [ ] Test video uploaded and processed
- [ ] Queries working correctly

### Quick Reference

**Repository**: https://github.com/Alexi5000/Bri.git  
**Main File**: `app.py`  
**Branch**: `master`  
**Required Secret**: `GROQ_API_KEY`

### Next Steps

1. Deploy to Streamlit Cloud
2. Test with short videos
3. Share URL for feedback
4. Monitor performance
5. Optimize as needed

**Ready to deploy!** Follow the steps above to get BRI online. 🚀
