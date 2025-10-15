# BRI Configuration Reference

Complete reference for all configuration options in BRI.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Required Configuration](#required-configuration)
3. [Groq API Settings](#groq-api-settings)
4. [Redis Caching](#redis-caching)
5. [Storage Paths](#storage-paths)
6. [MCP Server](#mcp-server)
7. [Processing Settings](#processing-settings)
8. [Memory & Performance](#memory--performance)
9. [Application Settings](#application-settings)
10. [Environment-Specific Configs](#environment-specific-configs)

## Configuration Overview

BRI uses environment variables for configuration, stored in a `.env` file in the project root.

### Configuration File Location

```
bri-video-agent/
├── .env              # Your configuration (gitignored)
└── .env.example      # Template with defaults
```

### Creating Your Configuration

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

### Configuration Validation

BRI validates configuration on startup:
- ✗ **Fails** if required values are missing
- ⚠️ **Warns** about suboptimal settings
- ✓ **Creates** necessary directories automatically

```bash
# Validate your configuration
python scripts/validate_setup.py
```

## Required Configuration

### GROQ_API_KEY

**Required**: Yes  
**Type**: String  
**Default**: None

Your Groq API key for LLM functionality.

```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

**How to get**:
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy and paste into `.env`

**Security**:
- Never commit this to version control
- Keep `.env` in `.gitignore`
- Rotate keys periodically
- Use different keys for dev/prod

## Groq API Settings

### GROQ_MODEL

**Required**: No  
**Type**: String  
**Default**: `llama-3.1-70b-versatile`

The LLM model to use for natural language understanding and response generation.

```bash
GROQ_MODEL=llama-3.1-70b-versatile
```

**Available Models**:
- `llama-3.1-70b-versatile` - Best quality, slower (recommended)
- `llama-3.1-8b-instant` - Faster, good quality
- `llama-3-70b-8192` - Alternative 70B model
- `llama-3-8b-8192` - Alternative 8B model
- `mixtral-8x7b-32768` - Good for longer contexts

**Choosing a Model**:
- **Quality priority**: Use 70B models
- **Speed priority**: Use 8B models
- **Long videos**: Use models with larger context windows

### GROQ_TEMPERATURE

**Required**: No  
**Type**: Float (0.0 - 2.0)  
**Default**: `0.7`

Controls response creativity and randomness.

```bash
GROQ_TEMPERATURE=0.7
```

**Values**:
- `0.0` - Deterministic, factual responses
- `0.5` - Balanced, slightly creative
- `0.7` - Recommended balance (default)
- `1.0` - More creative and varied
- `1.5+` - Very creative, less predictable

**Use Cases**:
- **Factual queries**: 0.3 - 0.5
- **General use**: 0.7 (default)
- **Creative exploration**: 1.0 - 1.2

### GROQ_MAX_TOKENS

**Required**: No  
**Type**: Integer  
**Default**: `1024`

Maximum length of generated responses.

```bash
GROQ_MAX_TOKENS=1024
```

**Values**:
- `512` - Short, concise responses
- `1024` - Standard responses (default)
- `2048` - Longer, detailed responses
- `4096` - Very detailed responses

**Considerations**:
- Higher values = slower responses
- Higher values = more API cost
- Adjust based on your needs

## Redis Caching

### REDIS_URL

**Required**: No  
**Type**: String (URL)  
**Default**: `redis://localhost:6379`

Redis server connection URL.

```bash
REDIS_URL=redis://localhost:6379
```

**Formats**:
- Local: `redis://localhost:6379`
- With password: `redis://:password@localhost:6379`
- Remote: `redis://hostname:6379`
- With database: `redis://localhost:6379/0`

**Cloud Redis**:
```bash
# Redis Cloud
REDIS_URL=redis://username:password@redis-12345.cloud.redislabs.com:12345

# AWS ElastiCache
REDIS_URL=redis://your-cluster.cache.amazonaws.com:6379

# Azure Cache
REDIS_URL=redis://:password@your-cache.redis.cache.windows.net:6380
```

### REDIS_ENABLED

**Required**: No  
**Type**: Boolean  
**Default**: `true`

Enable or disable Redis caching.

```bash
REDIS_ENABLED=true
```

**Values**:
- `true` - Use Redis for caching (recommended)
- `false` - Disable caching (fallback mode)

**When to Disable**:
- Redis not available
- Development/testing without Redis
- Troubleshooting cache issues

**Impact of Disabling**:
- Slower repeated queries
- No cache persistence
- Higher API usage
- Application still works normally

### CACHE_TTL_HOURS

**Required**: No  
**Type**: Integer  
**Default**: `24`

How long to keep cached results (in hours).

```bash
CACHE_TTL_HOURS=24
```

**Values**:
- `1` - 1 hour (frequent updates)
- `12` - 12 hours (balanced)
- `24` - 24 hours (default)
- `72` - 3 days (long-term)
- `168` - 1 week (maximum recommended)

**Considerations**:
- Longer TTL = less reprocessing
- Shorter TTL = fresher results
- Balance based on video update frequency

## Storage Paths

### DATABASE_PATH

**Required**: No  
**Type**: String (file path)  
**Default**: `data/bri.db`

SQLite database file location.

```bash
DATABASE_PATH=data/bri.db
```

**Considerations**:
- Use absolute path for production
- Ensure directory is writable
- Backup regularly
- Don't store in temp directories

### VIDEO_STORAGE_PATH

**Required**: No  
**Type**: String (directory path)  
**Default**: `data/videos`

Directory for uploaded video files.

```bash
VIDEO_STORAGE_PATH=data/videos
```

**Considerations**:
- Ensure sufficient disk space
- Use fast storage (SSD recommended)
- Consider network storage for multi-instance
- Implement cleanup policy for old videos

### FRAME_STORAGE_PATH

**Required**: No  
**Type**: String (directory path)  
**Default**: `data/frames`

Directory for extracted video frames.

```bash
FRAME_STORAGE_PATH=data/frames
```

**Considerations**:
- Can grow large (100+ frames per video)
- Use same storage as videos
- Clean up with videos on deletion

### CACHE_STORAGE_PATH

**Required**: No  
**Type**: String (directory path)  
**Default**: `data/cache`

Directory for processing cache files.

```bash
CACHE_STORAGE_PATH=data/cache
```

**Considerations**:
- Temporary storage
- Can be cleared safely
- Separate from Redis cache

## MCP Server

### MCP_SERVER_HOST

**Required**: No  
**Type**: String (hostname)  
**Default**: `localhost`

MCP server host address.

```bash
MCP_SERVER_HOST=localhost
```

**Values**:
- `localhost` - Local development (default)
- `0.0.0.0` - Listen on all interfaces
- `hostname` - Specific host for production

**Security**:
- Use `localhost` for single-machine setup
- Use `0.0.0.0` only if needed for remote access
- Implement authentication for remote access

### MCP_SERVER_PORT

**Required**: No  
**Type**: Integer (1-65535)  
**Default**: `8000`

MCP server port number.

```bash
MCP_SERVER_PORT=8000
```

**Considerations**:
- Ensure port is available
- Use non-privileged port (>1024)
- Configure firewall if needed
- Document for team if changed

## Processing Settings

### MAX_FRAMES_PER_VIDEO

**Required**: No  
**Type**: Integer  
**Default**: `100`

Maximum number of frames to extract per video.

```bash
MAX_FRAMES_PER_VIDEO=100
```

**Values**:
- `25` - Minimal (fast processing)
- `50` - Light (good for short videos)
- `100` - Standard (default)
- `200` - Detailed (long videos)
- `500` - Maximum (very detailed)

**Impact**:
- More frames = better coverage
- More frames = slower processing
- More frames = more storage
- More frames = more memory usage

**Recommendations**:
- Short videos (<5 min): 50-100
- Medium videos (5-15 min): 100-200
- Long videos (>15 min): 200-500

### FRAME_EXTRACTION_INTERVAL

**Required**: No  
**Type**: Float (seconds)  
**Default**: `2.0`

Interval between extracted frames in seconds.

```bash
FRAME_EXTRACTION_INTERVAL=2.0
```

**Values**:
- `0.5` - Very frequent (action videos)
- `1.0` - Frequent (detailed analysis)
- `2.0` - Standard (default)
- `5.0` - Sparse (slow-paced videos)
- `10.0` - Very sparse (minimal coverage)

**Adaptive Behavior**:
BRI automatically adjusts interval for very long videos to respect `MAX_FRAMES_PER_VIDEO`.

**Choosing Interval**:
- Fast-paced content: 0.5 - 1.0 seconds
- Normal content: 2.0 seconds (default)
- Slow-paced content: 5.0 - 10.0 seconds

## Memory & Performance

### MAX_CONVERSATION_HISTORY

**Required**: No  
**Type**: Integer  
**Default**: `10`

Number of conversation turns to keep in context.

```bash
MAX_CONVERSATION_HISTORY=10
```

**Values**:
- `5` - Minimal context (faster)
- `10` - Standard (default)
- `20` - Extended context
- `50` - Maximum (slower)

**Impact**:
- More history = better context awareness
- More history = slower responses
- More history = higher API costs

**Recommendations**:
- Quick queries: 5
- Normal use: 10 (default)
- Complex analysis: 20

### TOOL_EXECUTION_TIMEOUT

**Required**: No  
**Type**: Integer (seconds)  
**Default**: `120`

Maximum time to wait for tool execution.

```bash
TOOL_EXECUTION_TIMEOUT=120
```

**Values**:
- `60` - 1 minute (short videos)
- `120` - 2 minutes (default)
- `300` - 5 minutes (long videos)
- `600` - 10 minutes (very long videos)

**Considerations**:
- Longer videos need more time
- Slower hardware needs more time
- Balance between patience and responsiveness

### REQUEST_TIMEOUT

**Required**: No  
**Type**: Integer (seconds)  
**Default**: `30`

Maximum time to wait for API requests.

```bash
REQUEST_TIMEOUT=30
```

**Values**:
- `10` - Fast timeout (may fail on slow connections)
- `30` - Standard (default)
- `60` - Patient (slow connections)

### LAZY_LOAD_BATCH_SIZE

**Required**: No  
**Type**: Integer  
**Default**: `3`

Number of images to load per batch in UI.

```bash
LAZY_LOAD_BATCH_SIZE=3
```

**Values**:
- `1` - Minimal memory usage
- `3` - Balanced (default)
- `5` - Faster loading
- `10` - Maximum performance

**Impact**:
- Larger batches = faster UI
- Larger batches = more memory
- Adjust based on available RAM

## Application Settings

### DEBUG

**Required**: No  
**Type**: Boolean  
**Default**: `false`

Enable debug mode with verbose logging.

```bash
DEBUG=false
```

**Values**:
- `true` - Debug mode (development)
- `false` - Normal mode (production)

**Debug Mode Effects**:
- Verbose logging
- Detailed error messages
- Stack traces in responses
- Performance metrics
- No error suppression

**⚠️ Warning**: Never use `DEBUG=true` in production!

### LOG_LEVEL

**Required**: No  
**Type**: String  
**Default**: `INFO`

Logging verbosity level.

```bash
LOG_LEVEL=INFO
```

**Values**:
- `DEBUG` - Everything (very verbose)
- `INFO` - Normal operations (default)
- `WARNING` - Warnings and errors only
- `ERROR` - Errors only
- `CRITICAL` - Critical errors only

**Recommendations**:
- Development: `DEBUG`
- Production: `INFO` or `WARNING`
- Troubleshooting: `DEBUG`

## Environment-Specific Configs

### Development Configuration

```bash
# .env.development
GROQ_API_KEY=your_dev_key
DEBUG=true
LOG_LEVEL=DEBUG
REDIS_ENABLED=false
MAX_FRAMES_PER_VIDEO=25
FRAME_EXTRACTION_INTERVAL=5.0
```

### Production Configuration

```bash
# .env.production
GROQ_API_KEY=your_prod_key
DEBUG=false
LOG_LEVEL=INFO
REDIS_ENABLED=true
REDIS_URL=redis://your-redis-server:6379
MAX_FRAMES_PER_VIDEO=100
FRAME_EXTRACTION_INTERVAL=2.0
MCP_SERVER_HOST=0.0.0.0
```

### Testing Configuration

```bash
# .env.test
GROQ_API_KEY=your_test_key
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_PATH=data/test.db
VIDEO_STORAGE_PATH=data/test_videos
REDIS_ENABLED=false
MAX_FRAMES_PER_VIDEO=10
```

## Configuration Best Practices

### Security

1. **Never commit `.env` files** to version control
2. **Use different API keys** for dev/prod
3. **Rotate keys regularly**
4. **Restrict file permissions**: `chmod 600 .env`
5. **Use secrets management** in production

### Performance

1. **Enable Redis** for production
2. **Adjust frame extraction** based on video length
3. **Monitor resource usage** and adjust limits
4. **Use appropriate model** for your needs
5. **Set reasonable timeouts**

### Reliability

1. **Validate configuration** on startup
2. **Use absolute paths** in production
3. **Set up log rotation**
4. **Monitor disk space**
5. **Implement backup strategy**

### Maintenance

1. **Document custom values** and reasons
2. **Keep `.env.example` updated**
3. **Version control** configuration changes (not values)
4. **Test configuration changes** before deploying
5. **Have rollback plan** for config changes

## Configuration Troubleshooting

### Configuration Not Loading

```bash
# Verify .env file exists
ls -la .env

# Check file format (no spaces around =)
cat .env

# Test loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('GROQ_API_KEY', 'NOT LOADED'))"
```

### Invalid Values

```bash
# Run validation
python scripts/validate_setup.py

# Check specific value
python -c "from config import settings; print(settings.GROQ_MODEL)"
```

### Changes Not Taking Effect

1. Restart both servers (MCP and Streamlit)
2. Clear any cached configurations
3. Verify file was saved
4. Check for typos in variable names

## Complete Configuration Example

```bash
# BRI Configuration File
# Copy this to .env and customize

# ============================================
# REQUIRED CONFIGURATION
# ============================================

# Groq API Key (REQUIRED)
# Get yours at: https://console.groq.com
GROQ_API_KEY=your_actual_key_here

# ============================================
# GROQ API SETTINGS
# ============================================

# LLM Model
GROQ_MODEL=llama-3.1-70b-versatile

# Response creativity (0.0 - 2.0)
GROQ_TEMPERATURE=0.7

# Maximum response length
GROQ_MAX_TOKENS=1024

# ============================================
# REDIS CACHING
# ============================================

# Redis connection URL
REDIS_URL=redis://localhost:6379

# Enable/disable Redis
REDIS_ENABLED=true

# Cache expiration (hours)
CACHE_TTL_HOURS=24

# ============================================
# STORAGE PATHS
# ============================================

# Database file
DATABASE_PATH=data/bri.db

# Video storage directory
VIDEO_STORAGE_PATH=data/videos

# Frame storage directory
FRAME_STORAGE_PATH=data/frames

# Cache storage directory
CACHE_STORAGE_PATH=data/cache

# ============================================
# MCP SERVER
# ============================================

# Server host
MCP_SERVER_HOST=localhost

# Server port
MCP_SERVER_PORT=8000

# ============================================
# PROCESSING SETTINGS
# ============================================

# Maximum frames per video
MAX_FRAMES_PER_VIDEO=100

# Frame extraction interval (seconds)
FRAME_EXTRACTION_INTERVAL=2.0

# ============================================
# MEMORY & PERFORMANCE
# ============================================

# Conversation history limit
MAX_CONVERSATION_HISTORY=10

# Tool execution timeout (seconds)
TOOL_EXECUTION_TIMEOUT=120

# Request timeout (seconds)
REQUEST_TIMEOUT=30

# Lazy load batch size
LAZY_LOAD_BATCH_SIZE=3

# ============================================
# APPLICATION SETTINGS
# ============================================

# Debug mode (true/false)
DEBUG=false

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

For more help with configuration, see:
- [README.md](../README.md) - Setup guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [USER_GUIDE.md](USER_GUIDE.md) - Usage instructions
