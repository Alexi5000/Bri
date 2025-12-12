# BRI Video Agent - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

✅ Docker installed and running  
✅ Groq API key  

## 1️⃣ Pre-flight Check (Optional)

Verify your environment is ready:
```bash
./preflight_check.sh
```

This checks Docker, ports, disk space, and configuration.

## 2️⃣ Configure API Key

Edit `.env` file:
```bash
nano .env
```

Update this line with your actual API key:
```
GROQ_API_KEY=your_actual_api_key_here
```

Save and close (Ctrl+X, Y, Enter).

## 3️⃣ Deploy

Run the deployment script:
```bash
./deploy_test.sh
```

Wait 2-3 minutes for first-time setup (downloads models and builds images).

## 4️⃣ Access

Open your browser:
```
http://localhost:8501
```

## 5️⃣ Test

1. **Upload a video** (MP4, 30-60 seconds recommended)
2. **Wait for processing** (~30-90 seconds)
3. **Ask a question**: "What's happening in this video?"
4. **Click timestamps** to navigate the video

## 🎉 You're Done!

The app is now running and ready for testing.

---

## Common Commands

### View logs
```bash
docker compose logs -f
```

### Check status
```bash
docker compose ps
```

### Stop application
```bash
./stop_test.sh
```

### Restart
```bash
docker compose restart
```

---

## Troubleshooting

### "Cannot connect to server"
Wait 30-60 seconds - services are still starting.

### "API key error"
Check your API key in `.env` is correct.

### Port already in use
Stop the conflicting service or change ports in `docker-compose.yml`.

---

## Need Help?

- 📖 Full guide: [DEPLOY_TO_TEST.md](DEPLOY_TO_TEST.md)
- ✅ Test checklist: [TEST_CHECKLIST.md](TEST_CHECKLIST.md)
- 📚 Documentation: [README.md](README.md)

---

## Access Points

- **Streamlit UI**: http://localhost:8501
- **MCP Server**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs

---

**Happy Testing!** 🚀
