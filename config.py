"""Production configuration management for BRI.

Configuration is resolved lazily from Streamlit secrets first and environment
variables second. The module intentionally avoids printing secret metadata during
normal imports so tests, CLI scripts, and API processes remain deterministic.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    # Import only for type checkers; at runtime we lazy-load the logger to
    # avoid a circular import between config.py and utils.logging_config.
    pass


def _get_logger():
    """Lazy logger accessor that breaks the config <-> utils cycle."""
    from utils.logging_config import get_logger  # noqa: WPS433 (intentional lazy import)

    return get_logger(__name__)


try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - minimal validation environments

    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


load_dotenv()


Converter = Callable[[str], Any]


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _strip_inline_comment(value: str) -> str:
    """Strip shell-style inline comments from .env values used as numbers."""
    return value.split("#", 1)[0].strip()


def get_config_value(key: str, default: str = "") -> str:
    """Resolve a configuration value from environment, falling back to Streamlit secrets.

    Environment variables take precedence so that tests, CLI scripts, and CI
    jobs can override values without needing a Streamlit runtime. Streamlit
    secrets are only consulted when the env var is not set AND we are
    actually running inside a Streamlit runtime (detected via the
    ``STREAMLIT_RUNTIME_SCRIPT`` env var that Streamlit sets itself).

    Outside Streamlit, importing ``streamlit`` is enough to populate
    ``st.secrets`` from a developer's local ``.streamlit/secrets.toml``,
    which would otherwise leak local values into tests and CI.
    """
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    if not os.getenv("STREAMLIT_RUNTIME_SCRIPT"):
        return default
    try:
        import streamlit as st  # type: ignore

        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


class ConfigMeta(type):
    """Metaclass for lazy, cached configuration loading."""

    _cache: ClassVar[dict[str, Any]] = {}

    def __getattribute__(cls, name: str) -> Any:
        always_direct = {
            "validate",
            "ensure_directories",
            "get_mcp_server_url",
            "display_config",
            "reset_cache",
            "as_dict",
            "is_production",
        }
        if name.startswith("_") or name in always_direct:
            return super().__getattribute__(name)
        cache = super().__getattribute__("_cache")
        if name in cache:
            return cache[name]
        value = cls._load_config_value(name)
        cache[name] = value
        return value

    def _load_config_value(cls, name: str) -> Any:
        config_map: dict[str, tuple[str, str, Converter]] = {
            "APP_NAME": ("APP_NAME", "BRI", str),
            "APP_ENV": ("APP_ENV", "development", str),
            "APP_VERSION": ("APP_VERSION", "1.0.0", str),
            "GROQ_API_KEY": ("GROQ_API_KEY", "", str),
            "GROQ_MODEL": ("GROQ_MODEL", "llama-3.1-70b-versatile", str),
            "GROQ_TEMPERATURE": (
                "GROQ_TEMPERATURE",
                "0.7",
                lambda value: float(_strip_inline_comment(value)),
            ),
            "GROQ_MAX_TOKENS": (
                "GROQ_MAX_TOKENS",
                "1024",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "REDIS_URL": ("REDIS_URL", "redis://localhost:6379", str),
            "REDIS_ENABLED": ("REDIS_ENABLED", "false", _to_bool),
            "DATABASE_PATH": ("DATABASE_PATH", "data/bri.db", str),
            "VIDEO_STORAGE_PATH": ("VIDEO_STORAGE_PATH", "data/videos", str),
            "FRAME_STORAGE_PATH": ("FRAME_STORAGE_PATH", "data/frames", str),
            "CACHE_STORAGE_PATH": ("CACHE_STORAGE_PATH", "data/cache", str),
            "MCP_SERVER_HOST": ("MCP_SERVER_HOST", "localhost", str),
            "MCP_SERVER_PORT": (
                "MCP_SERVER_PORT",
                "8000",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "MCP_SERVER_URL": ("MCP_SERVER_URL", "", str),
            "ALLOWED_ORIGINS": (
                "ALLOWED_ORIGINS",
                "http://localhost:8501,http://127.0.0.1:8501",
                _split_csv,
            ),
            "MAX_UPLOAD_MB": (
                "MAX_UPLOAD_MB",
                "500",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "MAX_FRAMES_PER_VIDEO": (
                "MAX_FRAMES_PER_VIDEO",
                "20",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "FRAME_EXTRACTION_INTERVAL": (
                "FRAME_EXTRACTION_INTERVAL",
                "2.0",
                lambda value: float(_strip_inline_comment(value)),
            ),
            "CACHE_TTL_HOURS": (
                "CACHE_TTL_HOURS",
                "24",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "MAX_CONVERSATION_HISTORY": (
                "MAX_CONVERSATION_HISTORY",
                "10",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "TOOL_EXECUTION_TIMEOUT": (
                "TOOL_EXECUTION_TIMEOUT",
                "120",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "REQUEST_TIMEOUT": (
                "REQUEST_TIMEOUT",
                "30",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "LAZY_LOAD_BATCH_SIZE": (
                "LAZY_LOAD_BATCH_SIZE",
                "3",
                lambda value: int(_strip_inline_comment(value)),
            ),
            "DEBUG": ("DEBUG", "false", _to_bool),
            "LOG_LEVEL": ("LOG_LEVEL", "INFO", str),
            "LOG_DIR": ("LOG_DIR", "logs", str),
            "LOG_ROTATION_ENABLED": ("LOG_ROTATION_ENABLED", "true", _to_bool),
            "LOG_JSON_FORMAT": ("LOG_JSON_FORMAT", "false", _to_bool),
            "ALLOW_MISSING_GROQ_FOR_TESTS": ("ALLOW_MISSING_GROQ_FOR_TESTS", "false", _to_bool),
        }
        if name not in config_map:
            raise AttributeError(f"Config has no attribute {name!r}")
        key, default, converter = config_map[name]
        return converter(get_config_value(key, default))


class Config(metaclass=ConfigMeta):
    """Application configuration loaded from environment or Streamlit secrets."""

    @classmethod
    def reset_cache(cls) -> None:
        cls._cache.clear()

    @classmethod
    def is_production(cls) -> bool:
        return str(cls.APP_ENV).lower() == "production"

    @classmethod
    def get_mcp_server_url(cls) -> str:
        if cls.MCP_SERVER_URL:
            return cls.MCP_SERVER_URL.rstrip("/")
        return f"http://{cls.MCP_SERVER_HOST}:{cls.MCP_SERVER_PORT}"

    @classmethod
    def ensure_directories(cls) -> None:
        for directory in [
            cls.VIDEO_STORAGE_PATH,
            cls.FRAME_STORAGE_PATH,
            cls.CACHE_STORAGE_PATH,
            Path(cls.DATABASE_PATH).parent,
            cls.LOG_DIR,
        ]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls, *, require_groq: bool | None = None) -> None:
        errors: list[str] = []
        warnings: list[str] = []
        require_key = cls.is_production() if require_groq is None else require_groq
        if require_key and not cls.GROQ_API_KEY and not cls.ALLOW_MISSING_GROQ_FOR_TESTS:
            errors.append(
                "GROQ_API_KEY is required in production. Set it in .env, Streamlit secrets, or the deployment secret manager."
            )
        if not 0 <= cls.GROQ_TEMPERATURE <= 2:
            errors.append(f"GROQ_TEMPERATURE must be between 0 and 2; got {cls.GROQ_TEMPERATURE}.")
        if cls.GROQ_MAX_TOKENS < 1:
            errors.append("GROQ_MAX_TOKENS must be positive.")
        if cls.MAX_UPLOAD_MB < 1:
            errors.append("MAX_UPLOAD_MB must be positive.")
        if cls.MAX_FRAMES_PER_VIDEO < 1:
            errors.append("MAX_FRAMES_PER_VIDEO must be positive.")
        if cls.FRAME_EXTRACTION_INTERVAL <= 0:
            errors.append("FRAME_EXTRACTION_INTERVAL must be positive.")
        if cls.MAX_CONVERSATION_HISTORY < 1:
            errors.append("MAX_CONVERSATION_HISTORY must be positive.")
        if not cls.REDIS_ENABLED:
            warnings.append(
                "Redis caching is disabled; this is acceptable for local development but not ideal for production."
            )
        if cls.DEBUG and cls.is_production():
            errors.append("DEBUG must be false when APP_ENV=production.")
        if errors:
            raise ValueError(
                "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            )
        if warnings and cls.DEBUG:
            logger = _get_logger()
            for warning in warnings:
                logger.warning("Configuration warning: %s", warning)

    @classmethod
    def as_dict(cls, *, include_secrets: bool = False) -> dict[str, Any]:
        values = {
            "app_name": cls.APP_NAME,
            "app_env": cls.APP_ENV,
            "app_version": cls.APP_VERSION,
            "groq_model": cls.GROQ_MODEL,
            "redis_enabled": cls.REDIS_ENABLED,
            "database_path": cls.DATABASE_PATH,
            "video_storage_path": cls.VIDEO_STORAGE_PATH,
            "frame_storage_path": cls.FRAME_STORAGE_PATH,
            "cache_storage_path": cls.CACHE_STORAGE_PATH,
            "mcp_server_url": cls.get_mcp_server_url(),
            "max_upload_mb": cls.MAX_UPLOAD_MB,
            "max_frames_per_video": cls.MAX_FRAMES_PER_VIDEO,
            "request_timeout": cls.REQUEST_TIMEOUT,
            "log_level": cls.LOG_LEVEL,
        }
        if include_secrets:
            values["groq_api_key"] = cls.GROQ_API_KEY
        return values

    @classmethod
    def display_config(cls) -> None:
        masked = cls.as_dict(include_secrets=False)
        logger = _get_logger()
        for key, value in masked.items():
            logger.info("%s: %s", key, value)
