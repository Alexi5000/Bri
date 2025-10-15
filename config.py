"""Configuration management for BRI video agent."""

import os
from pathlib import Path
from typing import Optional
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
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        errors = []
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required. Please set it in .env file.")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            cls.VIDEO_STORAGE_PATH,
            cls.FRAME_STORAGE_PATH,
            cls.CACHE_STORAGE_PATH,
            Path(cls.DATABASE_PATH).parent,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_mcp_server_url(cls) -> str:
        """Get the full MCP server URL."""
        return f"http://{cls.MCP_SERVER_HOST}:{cls.MCP_SERVER_PORT}"


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Warning: {e}")
    print("Some features may not work without proper configuration.")
