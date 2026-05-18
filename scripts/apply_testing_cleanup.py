from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")


def move_if_exists(src: str, dst: str) -> None:
    source = ROOT / src
    target = ROOT / dst
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            source.unlink()
        else:
            shutil.move(str(source), str(target))


# Keep the default suite deterministic and independent of heavyweight media models.
move_if_exists("tests/test_production_contract.py", "tests/production/test_production_contract.py")

write(
    "tools/__init__.py",
    '''"""Video processing tool exports.

The concrete tool modules depend on optional media and model packages such as
OpenCV, Transformers, Whisper, and Torch. Importing this package should stay
cheap for API workers, documentation checks, and lightweight CI. Tool classes
are therefore resolved lazily when accessed.
"""

from __future__ import annotations

from typing import Any

__all__ = ["FrameExtractor", "ImageCaptioner", "AudioTranscriber"]

_EXPORTS = {
    "FrameExtractor": ("tools.frame_extractor", "FrameExtractor"),
    "ImageCaptioner": ("tools.image_captioner", "ImageCaptioner"),
    "AudioTranscriber": ("tools.audio_transcriber", "AudioTranscriber"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    try:
        module = __import__(module_name, fromlist=[attr_name])
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency-specific help
        raise ModuleNotFoundError(
            f"{name} requires an optional media dependency that is not installed. "
            "Install the full requirements or the appropriate optional extra before using this tool."
        ) from exc
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
''',
)

write(
    "tests/production/test_config_validation.py",
    '''from __future__ import annotations

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
''',
)

write(
    "tests/production/test_api_contract.py",
    '''from __future__ import annotations

from fastapi.testclient import TestClient

from mcp_server.main import app


client = TestClient(app)


def test_health_endpoint_exposes_operational_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "degraded"}
    assert "version" in payload


def test_tools_endpoint_returns_public_tool_catalog() -> None:
    response = client.get("/tools")

    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert {tool["name"] for tool in tools} >= {"process_video", "ask_video", "get_video_summary"}


def test_tool_execution_rejects_unknown_tool() -> None:
    response = client.post(
        "/tools/not_a_tool/execute",
        json={"video_id": "clip-001", "parameters": {}},
    )

    assert response.status_code in {400, 404}


def test_tool_execution_rejects_path_traversal_payload() -> None:
    response = client.post(
        "/tools/process_video/execute",
        json={"video_id": "../secret", "parameters": {}},
    )

    assert response.status_code == 422
''',
)

write(
    "tests/production/test_storage_contract.py",
    '''from __future__ import annotations

from pathlib import Path

from storage.database import Database


def test_database_initializes_schema_and_records_video(tmp_path: Path) -> None:
    db_path = tmp_path / "bri.sqlite3"
    database = Database(str(db_path))

    assert db_path.exists()
    video_id = database.add_video("demo.mp4", "/tmp/demo.mp4", 12.5)
    video = database.get_video(video_id)

    assert video is not None
    assert video["filename"] == "demo.mp4"
    assert video["duration"] == 12.5


def test_database_records_processing_status(tmp_path: Path) -> None:
    database = Database(str(tmp_path / "bri.sqlite3"))
    video_id = database.add_video("demo.mp4", "/tmp/demo.mp4", 12.5)

    database.update_video_status(video_id, "processing")
    database.update_video_status(video_id, "completed")

    assert database.get_video(video_id)["status"] == "completed"
''',
)

write(
    "tests/production/test_agent_contract.py",
    '''from __future__ import annotations

from services.agent import AgentService


class DummyMemory:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def add_conversation(self, video_id: str, question: str, answer: str) -> None:
        self.calls.append((video_id, question, answer))


def test_agent_service_provides_deterministic_fallback_without_client() -> None:
    memory = DummyMemory()
    agent = AgentService(groq_client=None, memory=memory)

    response = agent.answer_question(
        video_id="clip-001",
        question="What happened in the clip?",
        context={"summary": "A person walks through a lobby."},
    )

    assert "clip-001" in response["video_id"]
    assert response["answer"]
    assert memory.calls


def test_agent_service_builds_prompt_with_context() -> None:
    agent = AgentService(groq_client=None, memory=None)
    prompt = agent.build_prompt("Summarize", {"objects": ["person", "door"], "transcript": "hello"})

    assert "Summarize" in prompt
    assert "person" in prompt
    assert "hello" in prompt
''',
)

write(
    "tests/README.md",
    '''# Bri Test Strategy

Bri uses a tiered test strategy so the default suite is reliable in CI while the
media and model workflows can still be exercised in fully provisioned developer
environments.

| Suite | Command | Purpose |
| --- | --- | --- |
| Production contract | `pytest` | Fast checks for configuration, API contracts, storage, docs, and deterministic AI fallback behavior. |
| Smoke validation | `python scripts/smoke_api.py` | In-process FastAPI smoke check with no network dependency. |
| Production readiness | `python scripts/validate_production.py` | Required-file, README graphics, and contract-test validation for release gates. |
| Extended media tests | `pytest tests/unit tests/integration -m "slow or integration"` | Optional video, model, and dependency-heavy coverage for environments with OpenCV, Whisper, Torch, and model assets installed. |

The default `pytest` command intentionally points at `tests/production`. Legacy
media tests remain available, but they are not part of the release gate because
they require large optional dependencies and local model downloads.
''',
)

write(
    ".github/workflows/ci.yml",
    '''name: Bri CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  production-contract:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install package and development tools
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Run production validation
        env:
          APP_ENV: test
          ALLOW_MISSING_GROQ_FOR_TESTS: "true"
        run: |
          python scripts/validate_production.py
          python scripts/smoke_api.py
          pytest
''',
)

# Update production validation to the new default suite location.
validation_path = ROOT / "scripts" / "validate_production.py"
if validation_path.exists():
    text = validation_path.read_text(encoding="utf-8")
    text = text.replace("pytest tests/test_production_contract.py", "pytest tests/production")
    text = text.replace('"pytest", "tests/test_production_contract.py"', '"pytest", "tests/production"')
    validation_path.write_text(text, encoding="utf-8")

# Patch pyproject test collection to the stable production suite and add markers.
pyproject_path = ROOT / "pyproject.toml"
pyproject = pyproject_path.read_text(encoding="utf-8")
pyproject = pyproject.replace('testpaths = ["tests"]', 'testpaths = ["tests/production"]')
pyproject = pyproject.replace(
    'markers = [\n    "integration: marks tests as integration tests",\n    "slow: marks tests as slow",\n]',
    'markers = [\n    "integration: marks tests as integration tests",\n    "slow: marks tests as slow",\n    "media: marks tests that require local media/model dependencies",\n    "contract: marks production contract tests",\n]',
)
pyproject_path.write_text(pyproject, encoding="utf-8")

# Remove generated caches and local runtime artifacts from the working tree.
for pattern in ["**/__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov"]:
    for path in ROOT.glob(pattern):
        if path.exists() and path.is_dir():
            shutil.rmtree(path)

for file_pattern in [".coverage", "coverage.xml"]:
    path = ROOT / file_pattern
    if path.exists():
        path.unlink()

print("Applied Bri production testing, CI, optional import, and cleanup updates.")
