from __future__ import annotations

import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


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
    for key in [
        "MCP_SERVER_PORT",
        "MAX_FRAMES_PER_VIDEO",
        "TOOL_EXECUTION_TIMEOUT",
        "REQUEST_TIMEOUT",
    ]:
        matching = [line for line in env_text.splitlines() if line.startswith(f"{key}=")]
        assert matching, key
        value = matching[0].split("=", 1)[1]
        assert "#" not in value, f"{key} should not include inline comments in value"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"video_id": "../secret.mp4", "parameters": {}}, "invalid character"),
        (
            {
                "video_id": "clip-001",
                "parameters": {"nested": {"a": {"b": {"c": {"d": {"e": {"f": "too-deep"}}}}}}},
            },
            "nesting",
        ),
    ],
)
def test_tool_execution_request_rejects_unsafe_payloads(
    payload: dict[str, object], message: str
) -> None:
    from mcp_server.validation import ValidatedToolExecutionRequest

    with pytest.raises(Exception) as error:
        ValidatedToolExecutionRequest(**payload)

    assert message.lower() in str(error.value).lower()


def test_progressive_process_request_rejects_traversal_and_unsupported_formats() -> None:
    from mcp_server.validation import ValidatedProgressiveProcessRequest

    with pytest.raises(Exception):
        ValidatedProgressiveProcessRequest(video_path="../private.mov")

    with pytest.raises(Exception):
        ValidatedProgressiveProcessRequest(video_path="uploads/clip.txt")

    assert (
        ValidatedProgressiveProcessRequest(video_path="uploads/clip.mp4").video_path
        == "uploads/clip.mp4"
    )


def test_api_documentation_tracks_mcp_endpoints() -> None:
    api_doc = (ROOT / "docs/API.md").read_text(encoding="utf-8")
    server = (ROOT / "mcp_server/main.py").read_text(encoding="utf-8")

    for route in ["/health", "/tools", "/tools/{tool_name}/execute", "/videos/{video_id}/process"]:
        assert route in api_doc

    assert '@app.get("/health' in server
    assert '@app.post("/tools/{tool_name}/execute")' in server


def test_smoke_script_uses_fastapi_test_client_not_network() -> None:
    smoke = (ROOT / "scripts/smoke_api.py").read_text(encoding="utf-8")
    assert "TestClient" in smoke
    assert "smoke_in_process" in smoke
    assert "requests.get" in smoke


def test_existing_graphic_files_are_preserved() -> None:
    for asset in ["assets/icon.png", "assets/cover.png"]:
        path = ROOT / asset
        assert path.exists(), asset
        assert path.stat().st_size > 1000, asset
