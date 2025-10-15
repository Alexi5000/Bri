"""Configuration management for BRI video agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/bri.db")
    
    # File Storage Configuration
    VIDEO_STORAGE_PATH: str = os.getenv("VIDEO_STORAGE_PATH", "data/videos")
    FRAME_STORAGE_PATH: str = os.getenv("FRAME_STORAGE_PATH", "data/frames")
    CACHE_STORAGE_PATH: str = os.getenv("CACHE_STORAGE_PATH", "data/cache")
    
    # MCP Server Configuration
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "localhost")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    # Processing Configuration
    MAX_FRAMES_PER_VIDEO: int = int(os.getenv("MAX_FRAMES_PER_VIDEO", "100"))
    FRAME_EXTRACTION_INTERVAL: float = float(os.getenv("FRAME_EXTRACTION_INTERVAL", "2.0"))
    CACHE_TTL_HOURS: int = int(os.getenv("CACHE_TTL_HOURS", "24"))
    
    # Memory Configuration
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    
    # Performance Configuration
    TOOL_EXECUTION_TIMEOUT: int = int(os.getenv("TOOL_EXECUTION_TIMEOUT", "120"))  # seconds
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
    LAZY_LOAD_BATCH_SIZE: int = int(os.getenv("LAZY_LOAD_BATCH_SIZE", "3"))  # images per batch
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_ROTATION_ENABLED: bool = os.getenv("LOG_ROTATION_ENABLED", "true").lower() == "true"
    LOG_JSON_FORMAT: bool = os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        errors = []
        warnings = []
        
        # Required configurations
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required. Please set it in .env file.")
        
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


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Warning: {e}")
    print("Some features may not work without proper configuration.")
