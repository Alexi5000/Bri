"""Configuration management for BRI video agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_config_value(key: str, default: str = "") -> str:
    """Get configuration value from Streamlit secrets or environment variables.
    
    Priority:
    1. Streamlit secrets (if available)
    2. Environment variables
    3. Default value
    
    Args:
        key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            # Debug: Check if secrets are available
            if key in st.secrets:
                value = str(st.secrets[key])
                # Don't log the actual key value for security
                if key == "GROQ_API_KEY" and value:
                    print(f"✅ Found {key} in Streamlit secrets (length: {len(value)})")
                return value
            else:
                print(f"⚠️ {key} not found in Streamlit secrets. Available keys: {list(st.secrets.keys())}")
    except Exception as e:
        print(f"⚠️ Could not access Streamlit secrets: {e}")
    
    # Fall back to environment variables
    env_value = os.getenv(key, default)
    if env_value and env_value != default:
        print(f"✅ Found {key} in environment variables")
    return env_value


class ConfigMeta(type):
    """Metaclass for lazy configuration loading."""
    _cache = {}
    
    def __getattribute__(cls, name):
        if name.startswith('_') or name in ('validate', 'ensure_directories', 'get_mcp_server_url', 'display_config'):
            return super().__getattribute__(name)
        
        # Check cache first
        if name in cls._cache:
            return cls._cache[name]
        
        # Load value lazily
        value = cls._load_config_value(name)
        cls._cache[name] = value
        return value
    
    def _load_config_value(cls, name):
        """Load configuration value based on attribute name."""
        config_map = {
            # Groq API Configuration
            'GROQ_API_KEY': ('GROQ_API_KEY', ''),
            'GROQ_MODEL': ('GROQ_MODEL', 'llama-3.1-70b-versatile'),
            'GROQ_TEMPERATURE': ('GROQ_TEMPERATURE', '0.7', float),
            'GROQ_MAX_TOKENS': ('GROQ_MAX_TOKENS', '1024', int),
            
            # Redis Configuration
            'REDIS_URL': ('REDIS_URL', 'redis://localhost:6379'),
            'REDIS_ENABLED': ('REDIS_ENABLED', 'false', lambda x: x.lower() == 'true'),
            
            # Database Configuration
            'DATABASE_PATH': ('DATABASE_PATH', 'data/bri.db'),
            
            # File Storage Configuration
            'VIDEO_STORAGE_PATH': ('VIDEO_STORAGE_PATH', 'data/videos'),
            'FRAME_STORAGE_PATH': ('FRAME_STORAGE_PATH', 'data/frames'),
            'CACHE_STORAGE_PATH': ('CACHE_STORAGE_PATH', 'data/cache'),
            
            # MCP Server Configuration
            'MCP_SERVER_HOST': ('MCP_SERVER_HOST', 'localhost'),
            'MCP_SERVER_PORT': ('MCP_SERVER_PORT', '8000', int),
            
            # Processing Configuration
            'MAX_FRAMES_PER_VIDEO': ('MAX_FRAMES_PER_VIDEO', '20', int),
            'FRAME_EXTRACTION_INTERVAL': ('FRAME_EXTRACTION_INTERVAL', '2.0', float),
            'CACHE_TTL_HOURS': ('CACHE_TTL_HOURS', '24', int),
            
            # Memory Configuration
            'MAX_CONVERSATION_HISTORY': ('MAX_CONVERSATION_HISTORY', '10', int),
            
            # Performance Configuration
            'TOOL_EXECUTION_TIMEOUT': ('TOOL_EXECUTION_TIMEOUT', '120', int),
            'REQUEST_TIMEOUT': ('REQUEST_TIMEOUT', '30', int),
            'LAZY_LOAD_BATCH_SIZE': ('LAZY_LOAD_BATCH_SIZE', '3', int),
            
            # Application Configuration
            'DEBUG': ('DEBUG', 'false', lambda x: x.lower() == 'true'),
            'LOG_LEVEL': ('LOG_LEVEL', 'INFO'),
            'LOG_DIR': ('LOG_DIR', 'logs'),
            'LOG_ROTATION_ENABLED': ('LOG_ROTATION_ENABLED', 'true', lambda x: x.lower() == 'true'),
            'LOG_JSON_FORMAT': ('LOG_JSON_FORMAT', 'false', lambda x: x.lower() == 'true'),
        }
        
        if name not in config_map:
            raise AttributeError(f"Config has no attribute '{name}'")
        
        config_info = config_map[name]
        key = config_info[0]
        default = config_info[1]
        converter = config_info[2] if len(config_info) > 2 else str
        
        value = get_config_value(key, default)
        return converter(value) if converter != str else value


class Config(metaclass=ConfigMeta):
    """Application configuration loaded from environment variables or Streamlit secrets."""
    pass
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        errors = []
        warnings = []
        
        # Required configurations
        if not cls.GROQ_API_KEY:
            # Check if running on Streamlit Cloud
            try:
                import streamlit as st
                if hasattr(st, 'secrets'):
                    errors.append("GROQ_API_KEY is required. Please set it in Streamlit Cloud Secrets (Settings → Secrets).")
                else:
                    errors.append("GROQ_API_KEY is required. Please set it in .env file.")
            except:
                errors.append("GROQ_API_KEY is required. Please set it in .env file or Streamlit Cloud Secrets.")
        
        # Validate numeric ranges
        if cls.GROQ_TEMPERATURE < 0 or cls.GROQ_TEMPERATURE > 2:
            errors.append(f"GROQ_TEMPERATURE must be between 0 and 2 (got {cls.GROQ_TEMPERATURE})")
        
        if cls.GROQ_MAX_TOKENS < 1:
            errors.append(f"GROQ_MAX_TOKENS must be positive (got {cls.GROQ_MAX_TOKENS})")
        
        if cls.MAX_FRAMES_PER_VIDEO < 1:
            errors.append(f"MAX_FRAMES_PER_VIDEO must be positive (got {cls.MAX_FRAMES_PER_VIDEO})")
        
        if cls.FRAME_EXTRACTION_INTERVAL <= 0:
            errors.append(f"FRAME_EXTRACTION_INTERVAL must be positive (got {cls.FRAME_EXTRACTION_INTERVAL})")
        
        if cls.MAX_CONVERSATION_HISTORY < 1:
            errors.append(f"MAX_CONVERSATION_HISTORY must be positive (got {cls.MAX_CONVERSATION_HISTORY})")
        
        # Optional configurations with warnings
        if not cls.REDIS_ENABLED:
            warnings.append("Redis caching is disabled. Performance may be impacted.")
        
        if cls.DEBUG:
            warnings.append("DEBUG mode is enabled. This should be disabled in production.")
        
        # Print warnings
        if warnings:
            print("Configuration warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        
        # Raise errors if any
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  ❌ {e}" for e in errors)
            raise ValueError(error_msg)
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            cls.VIDEO_STORAGE_PATH,
            cls.FRAME_STORAGE_PATH,
            cls.CACHE_STORAGE_PATH,
            Path(cls.DATABASE_PATH).parent,
            cls.LOG_DIR,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_mcp_server_url(cls) -> str:
        """Get the full MCP server URL."""
        return f"http://{cls.MCP_SERVER_HOST}:{cls.MCP_SERVER_PORT}"
    
    @classmethod
    def display_config(cls) -> None:
        """Display current configuration (masking sensitive values)."""
        print("\n" + "="*60)
        print("BRI Configuration")
        print("="*60)
        
        print("\n🤖 Groq API:")
        print(f"  Model: {cls.GROQ_MODEL}")
        print(f"  Temperature: {cls.GROQ_TEMPERATURE}")
        print(f"  Max Tokens: {cls.GROQ_MAX_TOKENS}")
        api_key_status = '✓ Set' if cls.GROQ_API_KEY else '✗ Missing'
        print(f"  API Key: {api_key_status}")
        
        print("\n💾 Storage:")
        print(f"  Database: {cls.DATABASE_PATH}")
        print(f"  Videos: {cls.VIDEO_STORAGE_PATH}")
        print(f"  Frames: {cls.FRAME_STORAGE_PATH}")
        print(f"  Cache: {cls.CACHE_STORAGE_PATH}")
        
        print("\n🔧 Processing:")
        print(f"  Max Frames: {cls.MAX_FRAMES_PER_VIDEO}")
        print(f"  Frame Interval: {cls.FRAME_EXTRACTION_INTERVAL}s")
        print(f"  Cache TTL: {cls.CACHE_TTL_HOURS}h")
        
        print("\n🧠 Memory:")
        print(f"  Max History: {cls.MAX_CONVERSATION_HISTORY} messages")
        
        print("\n⚡ Performance:")
        print(f"  Tool Timeout: {cls.TOOL_EXECUTION_TIMEOUT}s")
        print(f"  Request Timeout: {cls.REQUEST_TIMEOUT}s")
        print(f"  Lazy Load Batch: {cls.LAZY_LOAD_BATCH_SIZE} images")
        
        print("\n🌐 MCP Server:")
        print(f"  URL: {cls.get_mcp_server_url()}")
        
        print("\n📦 Redis:")
        print(f"  Enabled: {'Yes' if cls.REDIS_ENABLED else 'No'}")
        if cls.REDIS_ENABLED:
            print(f"  URL: {cls.REDIS_URL}")
        
        print("\n🔍 Application:")
        print(f"  Debug: {'Yes' if cls.DEBUG else 'No'}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Log Directory: {cls.LOG_DIR}")
        print(f"  Log Rotation: {'Yes' if cls.LOG_ROTATION_ENABLED else 'No'}")
        
        print("\n" + "="*60 + "\n")


# Don't validate on import - let app.py handle validation after Streamlit is initialized
