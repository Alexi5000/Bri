from __future__ import annotations

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
    payload = response.json()
    assert payload["success"] is True
    assert payload["metadata"]["version"] == "1.0"

    tools = payload["data"]["tools"]
    assert isinstance(tools, list)
    assert payload["data"]["count"] == len(tools)
    assert {tool["name"] for tool in tools} >= {
        "extract_frames",
        "caption_frames",
        "transcribe_audio",
        "detect_objects",
    }


def test_tool_execution_rejects_unknown_tool() -> None:
    response = client.post(
        "/tools/not_a_tool/execute",
        json={"video_id": "clip-001", "parameters": {}},
    )

    assert response.status_code in {400, 404}


def test_tool_execution_rejects_path_traversal_payload() -> None:
    response = client.post(
        "/tools/extract_frames/execute",
        json={"video_id": "../secret", "parameters": {}},
    )

    assert response.status_code == 422
