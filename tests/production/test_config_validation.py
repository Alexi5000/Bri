from __future__ import annotations

from pathlib import Path

import pytest

from config import Config


def reset_config(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [
        "APP_ENV",
        "DEBUG",
        "GROQ_API_KEY",
        "ALLOW_MISSING_GROQ_FOR_TESTS",
        "GROQ_TEMPERATURE",
        "GROQ_MAX_TOKENS",
        "MCP_SERVER_HOST",
        "MCP_SERVER_PORT",
        "MCP_SERVER_URL",
        "DATABASE_PATH",
        "VIDEO_STORAGE_PATH",
        "FRAME_STORAGE_PATH",
        "CACHE_STORAGE_PATH",
        "LOG_DIR",
    ]:
        monkeypatch.delenv(key, raising=False)
    Config.reset_cache()


def test_configuration_masks_secrets_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_config(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value")
    Config.reset_cache()

    public_config = Config.as_dict()
    secret_config = Config.as_dict(include_secrets=True)

    assert "groq_api_key" not in public_config
    assert secret_config["groq_api_key"] == "gsk_secret_value"


def test_production_requires_groq_key_unless_explicit_test_override(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_config(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    Config.reset_cache()

    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        Config.validate()

    monkeypatch.setenv("ALLOW_MISSING_GROQ_FOR_TESTS", "true")
    Config.reset_cache()
    Config.validate()


def test_debug_mode_is_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_config(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ALLOW_MISSING_GROQ_FOR_TESTS", "true")
    Config.reset_cache()

    with pytest.raises(ValueError, match="DEBUG"):
        Config.validate()


def test_ensure_directories_creates_runtime_locations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reset_config(monkeypatch)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "db" / "bri.sqlite3"))
    monkeypatch.setenv("VIDEO_STORAGE_PATH", str(tmp_path / "videos"))
    monkeypatch.setenv("FRAME_STORAGE_PATH", str(tmp_path / "frames"))
    monkeypatch.setenv("CACHE_STORAGE_PATH", str(tmp_path / "cache"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    Config.reset_cache()

    Config.ensure_directories()

    for directory in ["db", "videos", "frames", "cache", "logs"]:
        assert (tmp_path / directory).is_dir()
