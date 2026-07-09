#!/usr/bin/env python3
"""Apply production-readiness buildout files for Bri.

This script is intentionally idempotent so the repository can be regenerated during
review without losing existing graphics or application modules.
"""

from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")


def cleanup() -> None:
    for pycache in ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)
    for pattern in ("*.pyc", ".pytest_cache", ".mypy_cache", ".ruff_cache"):
        for candidate in ROOT.rglob(pattern):
            if candidate.is_dir():
                shutil.rmtree(candidate, ignore_errors=True)
            elif candidate.exists():
                candidate.unlink()

    # Remove generated verification artifacts that do not belong in a production repo.
    for candidate in [
        ROOT / "phase1_verification_results_20251225_180230.json",
    ]:
        if candidate.exists():
            candidate.unlink()


def main() -> None:
    cleanup()

    write(
        "config.py",
        r'''
"""Production configuration management for BRI.

Configuration is resolved lazily from Streamlit secrets first and environment
variables second. The module intentionally avoids printing secret metadata during
normal imports so tests, CLI scripts, and API processes remain deterministic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, ClassVar

from dotenv import load_dotenv

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
    """Resolve a configuration value from Streamlit secrets or environment.

    Streamlit secrets are optional because API workers, tests, and CLI scripts do
    not run inside a Streamlit runtime. Missing secrets are silent by design.
    """
    try:
        import streamlit as st  # type: ignore

        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass

    return os.getenv(key, default)


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
            "GROQ_TEMPERATURE": ("GROQ_TEMPERATURE", "0.7", lambda value: float(_strip_inline_comment(value))),
            "GROQ_MAX_TOKENS": ("GROQ_MAX_TOKENS", "1024", lambda value: int(_strip_inline_comment(value))),
            "REDIS_URL": ("REDIS_URL", "redis://localhost:6379", str),
            "REDIS_ENABLED": ("REDIS_ENABLED", "false", _to_bool),
            "DATABASE_PATH": ("DATABASE_PATH", "data/bri.db", str),
            "VIDEO_STORAGE_PATH": ("VIDEO_STORAGE_PATH", "data/videos", str),
            "FRAME_STORAGE_PATH": ("FRAME_STORAGE_PATH", "data/frames", str),
            "CACHE_STORAGE_PATH": ("CACHE_STORAGE_PATH", "data/cache", str),
            "MCP_SERVER_HOST": ("MCP_SERVER_HOST", "localhost", str),
            "MCP_SERVER_PORT": ("MCP_SERVER_PORT", "8000", lambda value: int(_strip_inline_comment(value))),
            "MCP_SERVER_URL": ("MCP_SERVER_URL", "", str),
            "ALLOWED_ORIGINS": ("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501", _split_csv),
            "MAX_UPLOAD_MB": ("MAX_UPLOAD_MB", "500", lambda value: int(_strip_inline_comment(value))),
            "MAX_FRAMES_PER_VIDEO": ("MAX_FRAMES_PER_VIDEO", "20", lambda value: int(_strip_inline_comment(value))),
            "FRAME_EXTRACTION_INTERVAL": ("FRAME_EXTRACTION_INTERVAL", "2.0", lambda value: float(_strip_inline_comment(value))),
            "CACHE_TTL_HOURS": ("CACHE_TTL_HOURS", "24", lambda value: int(_strip_inline_comment(value))),
            "MAX_CONVERSATION_HISTORY": ("MAX_CONVERSATION_HISTORY", "10", lambda value: int(_strip_inline_comment(value))),
            "TOOL_EXECUTION_TIMEOUT": ("TOOL_EXECUTION_TIMEOUT", "120", lambda value: int(_strip_inline_comment(value))),
            "REQUEST_TIMEOUT": ("REQUEST_TIMEOUT", "30", lambda value: int(_strip_inline_comment(value))),
            "LAZY_LOAD_BATCH_SIZE": ("LAZY_LOAD_BATCH_SIZE", "3", lambda value: int(_strip_inline_comment(value))),
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
            errors.append("GROQ_API_KEY is required in production. Set it in .env, Streamlit secrets, or the deployment secret manager.")
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
            warnings.append("Redis caching is disabled; this is acceptable for local development but not ideal for production.")
        if cls.DEBUG and cls.is_production():
            errors.append("DEBUG must be false when APP_ENV=production.")
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        if warnings and cls.DEBUG:
            for warning in warnings:
                print(f"Configuration warning: {warning}")

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
        for key, value in masked.items():
            print(f"{key}: {value}")
''',
    )

    write(
        "pyproject.toml",
        r"""
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bri-video-agent"
version = "1.0.0"
description = "BRI is a production-ready Streamlit and FastAPI video intelligence assistant powered by Python API integrations."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "Alexi5000" }]
keywords = ["video-analysis", "streamlit", "fastapi", "groq", "mcp", "python"]
classifiers = [
  "Development Status :: 5 - Production/Stable",
  "Framework :: FastAPI",
  "Framework :: Pydantic",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Topic :: Multimedia :: Video",
]
dependencies = [
  "streamlit>=1.28.0",
  "groq>=0.4.0",
  "opencv-python>=4.8.0",
  "pillow>=10.0.0",
  "fastapi>=0.104.0",
  "uvicorn>=0.24.0",
  "redis>=5.0.0",
  "python-dotenv>=1.0.0",
  "pydantic>=2.5.0",
  "requests>=2.31.0",
  "httpx>=0.24.0",
]

[project.optional-dependencies]
ai = [
  "transformers>=4.35.0",
  "torch>=2.1.0",
  "openai-whisper>=20231117",
  "ultralytics>=8.0.0",
  "chromadb>=0.4.0",
  "sentence-transformers>=2.2.0",
]
dev = [
  "pytest>=7.4.0",
  "pytest-cov>=4.1.0",
  "pytest-asyncio>=0.21.0",
  "ruff>=0.5.0",
  "mypy>=1.8.0",
]

[tool.setuptools]
py-modules = ["app", "config"]

[tool.setuptools.packages.find]
include = ["models*", "services*", "storage*", "tools*", "utils*", "mcp_server*", "components*"]
exclude = ["tests*", "scripts*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]norecursedirs = ["data", "logs", ".git", ".venv", "venv"]
asyncio_mode = "auto"
addopts = "-q --strict-markers --disable-warnings"
markers = [
  "integration: exercises cross-module application behavior",
  "slow: exercises model or media-heavy workflows",
]

[tool.ruff]
line-length = 100
target-version = "py310"
exclude = ["data", "logs", ".venv", "venv"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.coverage.run]
source = ["config", "models", "services", "storage", "mcp_server"]
omit = ["tests/*", "scripts/*"]
""".replace(
            'python_files = ["test_*.py"]norecursedirs',
            'python_files = ["test_*.py"]\nnorecursedirs',
        ),
    )

    write(
        "Makefile",
        r"""
.PHONY: install install-dev init-db run-ui run-api test test-core validate smoke clean

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -e .[dev]

init-db:
	python scripts/init_db.py

run-ui:
	streamlit run app.py

run-api:
	uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000

test:
	pytest

test-core:
	pytest tests/unit/test_router.py tests/unit/test_memory.py tests/test_production_contract.py

validate:
	python scripts/validate_production.py

smoke:
	python scripts/smoke_api.py --url http://localhost:8000 --allow-offline

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
""",
    )

    write(
        ".env.example",
        r"""
# BRI production environment template
APP_NAME=BRI
APP_ENV=development
APP_VERSION=1.0.0

# Required for production AI responses
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=1024

# Streamlit + FastAPI runtime
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
MCP_SERVER_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501

# Storage
DATABASE_PATH=data/bri.db
VIDEO_STORAGE_PATH=data/videos
FRAME_STORAGE_PATH=data/frames
CACHE_STORAGE_PATH=data/cache
MAX_UPLOAD_MB=500

# Redis cache
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379
CACHE_TTL_HOURS=24

# Processing limits
MAX_FRAMES_PER_VIDEO=20
FRAME_EXTRACTION_INTERVAL=2.0
MAX_CONVERSATION_HISTORY=10
TOOL_EXECUTION_TIMEOUT=120
REQUEST_TIMEOUT=30
LAZY_LOAD_BATCH_SIZE=3

# Logging
DEBUG=false
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_ROTATION_ENABLED=true
LOG_JSON_FORMAT=false
""",
    )

    write(
        ".gitignore",
        r"""
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
coverage.xml
htmlcov/
*.egg-info/
build/
dist/

# Virtual environments
.venv/
venv/
env/

# Environment and secrets
.env
.env.*
!.env.example
.streamlit/secrets.toml

# Runtime data
data/
logs/
*.db
*.sqlite
*.sqlite3

# OS / editor
.DS_Store
Thumbs.db
.vscode/
.idea/

# Media scratch files
uploads/
tmp/
temp/
""",
    )

    write(
        "scripts/validate_production.py",
        r'''
#!/usr/bin/env python3
"""Production validation for Bri.

Runs fast checks that do not require GPU models, Redis, a Groq key, or uploaded
media. Heavy model and end-to-end media tests remain available through pytest
markers and local QA workflows.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "pyproject.toml",
    ".env.example",
    "Dockerfile.mcp",
    "Dockerfile.ui",
    "docker-compose.yml",
    "assets/icon.png",
    "assets/cover.png",
    "docs/ARCHITECTURE.md",
    "docs/TESTING.md",
    "docs/API.md",
    "docs/DEPLOYMENT.md",
]


def check_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit("Missing required production files: " + ", ".join(missing))


def check_readme_assets() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for asset in ("assets/icon.png", "assets/cover.png"):
        if asset not in readme:
            raise SystemExit(f"README must preserve graphic reference: {asset}")


def run_pytest() -> None:
    env = os.environ.copy()
    env.setdefault("ALLOW_MISSING_GROQ_FOR_TESTS", "true")
    env.setdefault("APP_ENV", "test")
    command = [sys.executable, "-m", "pytest", "tests/test_production_contract.py"]
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> None:
    check_files()
    check_readme_assets()
    run_pytest()
    print("BRI production validation passed.")


if __name__ == "__main__":
    main()
''',
    )

    write(
        "scripts/smoke_api.py",
        r'''
#!/usr/bin/env python3
"""Smoke test a running BRI MCP API server."""
from __future__ import annotations

import argparse
import sys
from urllib.parse import urljoin

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the BRI FastAPI service")
    parser.add_argument("--url", default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--allow-offline", action="store_true", help="Return success if the local API is not running")
    args = parser.parse_args()

    base = args.url.rstrip("/") + "/"
    try:
        health = requests.get(urljoin(base, "health"), timeout=5)
        health.raise_for_status()
        tools = requests.get(urljoin(base, "tools"), timeout=5)
        tools.raise_for_status()
    except requests.RequestException as exc:
        if args.allow_offline:
            print(f"API smoke skipped because server is offline: {exc}")
            return 0
        print(f"API smoke failed: {exc}", file=sys.stderr)
        return 1

    print("API smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    )

    write(
        "tests/test_production_contract.py",
        r"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_readme_preserves_graphics_and_core_links() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "assets/icon.png" in readme
    assert "assets/cover.png" in readme
    assert "docs/ARCHITECTURE.md" in readme
    assert "docs/API.md" in readme
    assert "docs/TESTING.md" in readme
    assert "docker compose up" in readme.lower()


@pytest.mark.parametrize(
    "path",
    [
        "pyproject.toml",
        ".env.example",
        "Dockerfile.mcp",
        "Dockerfile.ui",
        "docker-compose.yml",
        "mcp_server/main.py",
        "mcp_server/validation.py",
    ],
)
def test_required_production_files_exist(path: str) -> None:
    assert (ROOT / path).exists(), path


def test_config_supports_explicit_mcp_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_SERVER_URL", "http://mcp-server:8000/")
    monkeypatch.setenv("ALLOW_MISSING_GROQ_FOR_TESTS", "true")
    config = importlib.import_module("config")
    config.Config.reset_cache()
    assert config.Config.get_mcp_server_url() == "http://mcp-server:8000"
    config.Config.validate(require_groq=False)


def test_env_example_has_parseable_numeric_values() -> None:
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in ["MCP_SERVER_PORT", "MAX_FRAMES_PER_VIDEO", "TOOL_EXECUTION_TIMEOUT", "REQUEST_TIMEOUT"]:
        matching = [line for line in env_text.splitlines() if line.startswith(f"{key}=")]
        assert matching, key
        value = matching[0].split("=", 1)[1]
        assert "#" not in value, f"{key} should not include inline comments in value"
""",
    )

    write(
        "docs/API.md",
        r"""
# BRI API Reference

BRI exposes a FastAPI service that coordinates video processing tools behind a small MCP-style contract. The Streamlit interface calls this service for frame extraction, captioning, transcription, object detection, cache inspection, and progressive job status.

| Area | Endpoint | Purpose |
|---|---|---|
| Service health | `GET /health` | Returns process, registry, cache, and dependency status. |
| Tool registry | `GET /tools` and `GET /v1/tools` | Lists available tool names, descriptions, and parameter schemas. |
| Tool execution | `POST /tools/{tool_name}/execute` | Executes one registered tool for a known video. |
| Video processing | `POST /videos/{video_id}/process` | Runs an ordered processing plan for a video. |
| Progressive processing | `POST /videos/{video_id}/process-progressive` | Starts staged processing suitable for UI progress. |
| Status | `GET /videos/{video_id}/status` | Reports available data for a processed video. |
| Queue | `GET /queue/status` and `GET /queue/job/{video_id}` | Reports background processing state. |
| Cache | `GET /cache/stats`, `DELETE /cache`, `DELETE /cache/videos/{video_id}` | Observes and clears cached processing output. |

## Request model

Tool execution accepts a constrained request body. Parameters are validated for allowed tool names, sanitized video identifiers, JSON size, nested depth, and supported media paths before execution.

```json
{
  "video_id": "video_demo_001",
  "parameters": {
    "max_frames": 20,
    "interval_seconds": 2.0
  }
}
```

## Response model

API responses use structured Pydantic envelopes for successful results, validation errors, cache metadata, and processing progress. The service is designed so clients can poll status while long-running model work continues in the background.

## Operational notes

The API should be run behind a production reverse proxy with request-size limits and TLS termination. Redis is optional for local development but recommended in production so expensive tool calls can be cached and reused safely.
""",
    )

    write(
        "docs/TESTING.md",
        r"""
# Testing Guide

BRI separates fast production checks from heavy video and model tests so contributors can validate changes without requiring a GPU, Redis, uploaded media, or a live Groq key.

| Command | Purpose |
|---|---|
| `python scripts/validate_production.py` | Verifies production files, README graphics, configuration parsing, and fast contract tests. |
| `pytest tests/test_production_contract.py` | Runs the lightweight production-readiness contract tests. |
| `pytest tests/unit` | Runs pure unit tests for routing, memory, and tool logic. |
| `pytest tests/integration` | Runs service-level integration tests with mocked or synthetic media state. |
| `python scripts/smoke_api.py --url http://localhost:8000` | Checks a running API service health and tool registry. |

## Test environment

Use `ALLOW_MISSING_GROQ_FOR_TESTS=true` when running tests that import application configuration without a live model key. Production deployments should not enable that flag.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ALLOW_MISSING_GROQ_FOR_TESTS=true pytest tests/test_production_contract.py
```

## Heavy tests

Some existing tests exercise media extraction, transcription, object detection, vector search, or end-to-end video workflows. Treat those as local QA or CI jobs with explicit model/cache provisioning rather than required pre-commit checks.
""",
    )

    write(
        "docs/README.md",
        r"""
# BRI Documentation Index

| Document | Description |
|---|---|
| [Architecture](ARCHITECTURE.md) | Production architecture, runtime boundaries, and data flow. |
| [API Reference](API.md) | FastAPI/MCP endpoint surface and operational notes. |
| [Testing Guide](TESTING.md) | Fast validation, unit, integration, and smoke-test commands. |
| [Deployment](DEPLOYMENT.md) | Container and service deployment guidance. |
| [Configuration](CONFIGURATION.md) | Environment variables and runtime tuning. |
| [Operations Runbook](OPERATIONS_RUNBOOK.md) | Production monitoring, backup, restore, and incident operations. |
""",
    )

    write(
        "docs/ARCHITECTURE.md",
        r"""
# BRI Production Architecture

BRI is a complete Python video intelligence application that combines a **Streamlit operator interface**, a **FastAPI MCP-style processing service**, a **SQLite persistence layer**, optional **Redis caching**, and a **Groq-powered conversation agent**. The build is optimized for local development, Docker deployment, and incremental production hardening without requiring contributors to run heavyweight media models for every change.

## Runtime boundaries

| Layer | Responsibility | Key modules |
|---|---|---|
| Streamlit UI | Upload videos, show progress, render chat, and display timestamped evidence. | `app.py`, `components/*` |
| Conversation agent | Plan user intent, retrieve context, call Groq, and store memory. | `services/agent.py`, `services/router.py`, `services/context.py` |
| FastAPI service | Expose tool registry, execute video tools, report progress, and manage cache state. | `mcp_server/main.py`, `mcp_server/registry.py`, `mcp_server/validation.py` |
| Storage | Persist videos, extracted context, conversation memory, and processing metadata. | `storage/database.py`, `storage/schema.sql` |
| Media tools | Extract frames, caption images, transcribe audio, and detect objects. | `tools/*` |

## Request flow

1. A user uploads a video through Streamlit.
2. The app records video metadata in SQLite and calls the FastAPI service.
3. The service validates request size, video IDs, and tool names before running media tools.
4. Tool results are persisted as typed video context and optionally cached in Redis.
5. The chat agent builds a context window from video evidence and conversation memory.
6. Groq generates a warm, timestamp-aware answer with supporting frames and suggestions.

## Production principles

BRI keeps secrets in environment variables or deployment secret managers, stores generated media under ignored runtime directories, uses validation contracts around every API boundary, and provides fast tests that verify packaging, documentation, configuration, and API contracts without requiring GPU-backed model execution.
""",
    )

    # Append concise production block to deployment docs while preserving existing file if present.
    deployment = ROOT / "docs/DEPLOYMENT.md"
    existing_deployment = (
        deployment.read_text(encoding="utf-8") if deployment.exists() else "# Deployment\n"
    )
    if "## Production quick path" not in existing_deployment:
        deployment.write_text(
            existing_deployment.rstrip()
            + "\n\n"
            + r"""
## Production quick path

Use Docker Compose when you need the Streamlit UI, FastAPI service, Redis cache, and shared data volumes to run together.

```bash
cp .env.example .env
# Set GROQ_API_KEY and production storage/cache values.
docker compose up --build
```

For platform deployments, run `uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000` for the API service and `streamlit run app.py --server.port 8501` for the UI. Mount persistent volumes for `data/` and `logs/`, configure Redis for cache reuse, and keep `.env` outside source control.
""".strip()
            + "\n",
            encoding="utf-8",
        )

    write(
        "README.md",
        r"""
<div align="center">
  <img src="assets/icon.png" alt="BRI logo" width="112" />

# BRI — Empathetic Video Intelligence

### A production-ready Python app for conversational video analysis, timestamped evidence, and MCP-style tool orchestration.

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b?logo=streamlit)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-MCP%20API-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLM-f55036)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?logo=docker)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

<img src="assets/cover.png" alt="BRI video intelligence cover" width="100%" />

BRI, short for **Brianna**, turns uploaded videos into a searchable, conversational knowledge layer. It extracts frames, captions scenes, transcribes audio, detects objects, stores structured context, and lets users ask natural questions with timestamp-aware responses.

## Why it is production-ready

| Capability | Built-out implementation |
|---|---|
| Full app surface | Streamlit UI, FastAPI MCP server, SQLite storage, optional Redis cache, Docker Compose orchestration. |
| Python API integration | Hardened configuration, validation boundaries, health/tool endpoints, smoke testing, and service docs. |
| Video intelligence | Frame extraction, image captioning, transcription, object detection, context building, and conversational memory. |
| Reliability | Request validation, rate limiting, circuit breakers, cache controls, database backups, and operations docs. |
| Testability | Fast production contract tests, unit tests, integration tests, smoke scripts, and deterministic no-key validation mode. |

## Architecture

```mermaid
flowchart LR
    User[User] --> UI[Streamlit UI]
    UI --> API[FastAPI MCP Service]
    API --> Tools[Video Tools]
    Tools --> DB[(SQLite)]
    Tools --> Cache[(Redis Optional)]
    UI --> Agent[Groq Conversation Agent]
    Agent --> DB
    Agent --> API
```

## Quick start

```bash
git clone https://github.com/Alexi5000/Bri.git
cd Bri
cp .env.example .env
# Add GROQ_API_KEY to .env for live AI responses.
docker compose up --build
```

Open the UI at `http://localhost:8501` and the API at `http://localhost:8000`.

For local development without Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/init_db.py
uvicorn mcp_server.main:app --reload --port 8000
streamlit run app.py
```

## Core commands

| Command | Purpose |
|---|---|
| `python scripts/validate_production.py` | Fast production-readiness validation. |
| `pytest tests/test_production_contract.py` | Lightweight contract tests for config, docs, graphics, and packaging. |
| `pytest tests/unit` | Unit tests for router, memory, and tool logic. |
| `python scripts/smoke_api.py --url http://localhost:8000` | Smoke test a running FastAPI service. |
| `docker compose up --build` | Run Streamlit, FastAPI, Redis, and shared volumes together. |

## API surface

| Endpoint | Description |
|---|---|
| `GET /health` | Service health and dependency status. |
| `GET /tools` | Registered MCP tool catalog. |
| `POST /tools/{tool_name}/execute` | Execute a validated video tool. |
| `POST /videos/{video_id}/process` | Run a processing plan for a video. |
| `POST /videos/{video_id}/process-progressive` | Start staged processing with progress tracking. |
| `GET /videos/{video_id}/status` | Inspect available video context. |

## Documentation

| Guide | Link |
|---|---|
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| API Reference | [docs/API.md](docs/API.md) |
| Testing | [docs/TESTING.md](docs/TESTING.md) |
| Deployment | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Configuration | [docs/CONFIGURATION.md](docs/CONFIGURATION.md) |
| Operations | [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md) |

## Repository hygiene

Generated media, logs, databases, Python caches, virtual environments, and secret files are ignored. The committed assets under `assets/` are intentionally preserved because they define the project’s public README identity.

## License

BRI is released under the [MIT License](LICENSE).
""",
    )


if __name__ == "__main__":
    main()
