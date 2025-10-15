# Task 26: Configuration Setup - Usage Guide

## For New Users

### Quick Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Add your Groq API key**:
   - Open `.env` in a text editor
   - Replace `your_groq_api_key_here` with your actual key
   - Get a free key at [console.groq.com](https://console.groq.com)

3. **Validate setup**:
   ```bash
   python scripts/validate_setup.py
   ```

4. **If all checks pass**, you're ready to go! 🎉

### Understanding Validation Output

```
✓ = Check passed
✗ = Check failed (needs fixing)
⚠️ = Warning (optional, but recommended)
```

## For Developers

### Configuration Access

```python
from config import Config

# Access any configuration value
api_key = Config.GROQ_API_KEY
model = Config.GROQ_MODEL
max_frames = Config.MAX_FRAMES_PER_VIDEO
server_url = Config.get_mcp_server_url()
```

### Display Current Configuration

```python
from config import Config

# Show all settings (masks sensitive values)
Config.display_config()
```

### Validate Configuration Programmatically

```python
from config import Config

try:
    Config.validate()
    print("Configuration is valid!")
except ValueError as e:
    print(f"Configuration error: {e}")
```

### Ensure Directories Exist

```python
from config import Config

# Creates all required directories
Config.ensure_directories()
```

## Configuration Categories

### 1. Groq API (Required)
```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=1024
```

**When to modify**:
- Use different model for speed/quality tradeoff
- Adjust temperature for more/less creative responses
- Increase max tokens for longer responses

### 2. Redis Caching (Optional)
```env
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
```

**When to modify**:
- Disable if Redis not available: `REDIS_ENABLED=false`
- Change URL for remote Redis server
- Performance improves significantly with Redis enabled

### 3. Storage Paths
```env
DATABASE_PATH=data/bri.db
VIDEO_STORAGE_PATH=data/videos
FRAME_STORAGE_PATH=data/frames
CACHE_STORAGE_PATH=data/cache
```

**When to modify**:
- Use different storage location
- Separate data across drives
- Network storage for shared access

### 4. Processing Settings
```env
MAX_FRAMES_PER_VIDEO=100
FRAME_EXTRACTION_INTERVAL=2.0
CACHE_TTL_HOURS=24
```

**When to modify**:
- Reduce `MAX_FRAMES_PER_VIDEO` for faster processing
- Increase `FRAME_EXTRACTION_INTERVAL` for longer videos
- Adjust `CACHE_TTL_HOURS` for cache retention

### 5. Performance Tuning
```env
TOOL_EXECUTION_TIMEOUT=120
REQUEST_TIMEOUT=30
LAZY_LOAD_BATCH_SIZE=3
```

**When to modify**:
- Increase timeouts for slow connections
- Reduce batch size for lower memory usage
- Adjust for your hardware capabilities

### 6. Application Settings
```env
DEBUG=false
LOG_LEVEL=INFO
```

**When to modify**:
- Enable `DEBUG=true` for development
- Change `LOG_LEVEL` to DEBUG for troubleshooting
- Use ERROR in production for minimal logging

## Common Scenarios

### Scenario 1: First Time Setup
```bash
# 1. Copy template
cp .env.example .env

# 2. Edit .env and add GROQ_API_KEY

# 3. Validate
python scripts/validate_setup.py

# 4. Initialize database
python scripts/init_db.py
```

### Scenario 2: No Redis Available
```env
# In .env file
REDIS_ENABLED=false
```

This disables caching but allows BRI to run without Redis.

### Scenario 3: Slow Video Processing
```env
# Reduce frames extracted
MAX_FRAMES_PER_VIDEO=50

# Increase interval between frames
FRAME_EXTRACTION_INTERVAL=3.0
```

### Scenario 4: Memory Issues
```env
# Reduce batch size
LAZY_LOAD_BATCH_SIZE=1

# Reduce max frames
MAX_FRAMES_PER_VIDEO=50

# Reduce conversation history
MAX_CONVERSATION_HISTORY=5
```

### Scenario 5: Production Deployment
```env
# Disable debug mode
DEBUG=false

# Set appropriate log level
LOG_LEVEL=WARNING

# Enable Redis for performance
REDIS_ENABLED=true

# Adjust timeouts for production
TOOL_EXECUTION_TIMEOUT=60
REQUEST_TIMEOUT=15
```

## Troubleshooting

### "GROQ_API_KEY is required"
**Solution**: Add your API key to `.env` file
```env
GROQ_API_KEY=gsk_your_actual_key_here
```

### "Configuration validation failed: GROQ_TEMPERATURE must be between 0 and 2"
**Solution**: Fix the temperature value in `.env`
```env
GROQ_TEMPERATURE=0.7
```

### "Redis not available"
**Solution**: Either install Redis or disable it
```env
REDIS_ENABLED=false
```

### Validation script fails on dependencies
**Solution**: Install missing packages
```bash
pip install -r requirements.txt
```

### Directories not created
**Solution**: Check permissions or manually create
```bash
mkdir -p data/videos data/frames data/cache
```

## Best Practices

1. **Never commit `.env`**: Keep API keys secret
2. **Use `.env.example`**: Template for team members
3. **Validate before running**: Catch issues early
4. **Start with defaults**: Only change what you need
5. **Document changes**: Comment custom settings
6. **Test after changes**: Run validation script

## Integration with Application

### Streamlit App
- Validates configuration on startup
- Shows error message if invalid
- Stops execution until fixed

### MCP Server
- Validates configuration on startup
- Logs validation status
- Fails fast if configuration invalid

### Tools and Services
- All components use `Config` class
- Consistent configuration across application
- No hardcoded values

## Advanced Usage

### Environment-Specific Configuration

**Development** (`.env.dev`):
```env
DEBUG=true
LOG_LEVEL=DEBUG
REDIS_ENABLED=false
```

**Production** (`.env.prod`):
```env
DEBUG=false
LOG_LEVEL=WARNING
REDIS_ENABLED=true
```

Load specific environment:
```bash
cp .env.dev .env  # For development
cp .env.prod .env  # For production
```

### Configuration Validation in CI/CD

```bash
# In your CI/CD pipeline
python scripts/validate_setup.py
if [ $? -ne 0 ]; then
    echo "Configuration validation failed"
    exit 1
fi
```

### Custom Validation

```python
from config import Config

# Add custom validation
if Config.MAX_FRAMES_PER_VIDEO > 200:
    print("Warning: High frame count may impact performance")

if Config.GROQ_TEMPERATURE > 1.5:
    print("Warning: High temperature may produce inconsistent results")
```

## Summary

The configuration system provides:
- ✓ Simple setup for new users
- ✓ Comprehensive validation
- ✓ Clear error messages
- ✓ Flexible customization
- ✓ Production-ready defaults
- ✓ Easy troubleshooting

For more details, see:
- [QUICKSTART.md](../QUICKSTART.md) - Quick setup guide
- [README.md](../README.md) - Full documentation
- [task_26_configuration_setup.md](task_26_configuration_setup.md) - Implementation details
