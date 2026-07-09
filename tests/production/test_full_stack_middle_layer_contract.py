from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.application import BriApplicationService
from services.mcp_client import MCPClient, MCPClientError
from storage.maintenance import (
    configure_sqlite_for_production,
    create_sqlite_backup,
    run_integrity_check,
    vacuum_database,
)


class DummyResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self) -> object:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_mcp_client_unwraps_standardized_tool_and_progress_envelopes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, timeout: float) -> DummyResponse:
        if url.endswith("/tools"):
            return DummyResponse(
                {
                    "success": True,
                    "request_id": "req-1",
                    "api_version": "1.0",
                    "data": {
                        "tools": [
                            {
                                "name": "analyze_video_context",
                                "description": "Analyze uploaded video context.",
                                "parameters": {"video_id": "string"},
                            }
                        ]
                    },
                }
            )
        if url.endswith("/videos/video-123/progress"):
            return DummyResponse(
                {
                    "success": True,
                    "request_id": "req-2",
                    "data": {
                        "video_id": "video-123",
                        "processing": True,
                        "stage": "captioning",
                        "progress_percent": 62.5,
                        "message": "Generating captions",
                        "frames_extracted": 12,
                        "captions_generated": 8,
                        "transcript_segments": 2,
                        "objects_detected": 4,
                    },
                }
            )
        raise AssertionError(f"Unexpected GET URL: {url}")

    monkeypatch.setattr("services.mcp_client.httpx.get", fake_get)

    client = MCPClient(base_url="http://mcp.local", timeout=3)
    tools = client.list_tools()
    progress = client.video_progress("video-123")

    assert [tool.name for tool in tools] == ["analyze_video_context"]
    assert tools[0].parameters == {"video_id": "string"}
    assert progress.video_id == "video-123"
    assert progress.processing is True
    assert progress.stage == "captioning"
    assert progress.progress_percent == 62.5
    assert progress.frames_extracted == 12


def test_mcp_client_rejects_failed_standardized_envelope() -> None:
    with pytest.raises(MCPClientError):
        MCPClient._unwrap({"success": False, "error": "tool execution rejected"})


def test_application_service_snapshot_uses_middle_layer_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeMCPClient:
        def health(self) -> SimpleNamespace:
            return SimpleNamespace(
                online=True, status="healthy", url="http://mcp.local", components={}, detail="ok"
            )

        def list_tools(self) -> list[SimpleNamespace]:
            return [SimpleNamespace(name="analyze_video_context")]

    monkeypatch.setattr(
        "services.application.database.get_all_videos",
        lambda: [
            {
                "video_id": "video-1",
                "filename": "interview.mp4",
                "file_path": "/tmp/interview.mp4",
                "duration": 65.0,
                "processing_status": "complete",
                "thumbnail_path": None,
                "upload_timestamp": "2026-05-18T00:00:00Z",
            },
            {
                "video_id": "video-2",
                "filename": "demo.mp4",
                "file_path": "/tmp/demo.mp4",
                "duration": 0.0,
                "processing_status": "processing",
                "thumbnail_path": None,
                "upload_timestamp": None,
            },
        ],
    )
    monkeypatch.setattr(
        "services.application.BriApplicationService._count_conversations", lambda self: 3
    )

    snapshot = BriApplicationService(mcp_client=FakeMCPClient()).snapshot()

    assert snapshot.total_videos == 2
    assert snapshot.ready_videos == 1
    assert snapshot.processing_videos == 1
    assert snapshot.conversations == 3
    assert snapshot.tools[0].name == "analyze_video_context"
    assert snapshot.videos[0].duration_label == "01:05"
    assert snapshot.videos[1].status_label == "Processing"


def test_application_service_progress_requires_persisted_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = BriApplicationService(mcp_client=SimpleNamespace())
    monkeypatch.setattr("services.application.database.get_video", lambda video_id: None)

    with pytest.raises(ValueError, match="Video not found"):
        service.get_processing_progress("missing-video")


def test_sqlite_maintenance_contract_supports_integrity_backup_and_vacuum(tmp_path: Path) -> None:
    db_path = tmp_path / "bri.sqlite3"
    backup_dir = tmp_path / "backups"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE videos (video_id TEXT PRIMARY KEY, filename TEXT NOT NULL)")
        conn.execute("INSERT INTO videos VALUES ('video-1', 'demo.mp4')")

    settings = configure_sqlite_for_production(str(db_path))
    report = run_integrity_check(str(db_path))
    backup = create_sqlite_backup(str(db_path), str(backup_dir))
    vacuum = vacuum_database(str(db_path))

    assert settings["journal_mode"].lower() in {"wal", "delete", "memory"}
    assert settings["busy_timeout_ms"] == 5000
    assert report.ok is True
    assert report.messages == ("ok",)
    assert set(report.wal_checkpoint) == {"busy", "log_frames", "checkpointed_frames"}
    assert backup.ok is True
    assert Path(backup.backup_path).exists()
    assert backup.size_bytes > 0
    assert vacuum["after_bytes"] > 0


def test_sqlite_backup_reports_missing_database_without_side_effects(tmp_path: Path) -> None:
    missing_db = tmp_path / "missing.sqlite3"

    result = create_sqlite_backup(str(missing_db), str(tmp_path / "backups"))

    assert result.ok is False
    assert result.backup_path == ""
    assert "does not exist" in result.message


def test_uncle_bob_documentation_and_mermaid_diagrams_are_published() -> None:
    required_docs = [
        Path("docs/architecture/UNCLE_BOB_CLEAN_CODE_REVIEW.md"),
        Path("docs/architecture/DATA_FLOW_AND_STATE.md"),
        Path("docs/architecture/DATABASE_SCHEMA_AND_DURABILITY.md"),
    ]

    for doc in required_docs:
        content = doc.read_text(encoding="utf-8")
        assert "```mermaid" in content
        assert "bri" in content.lower()

    index = Path("docs/INDEX.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "UNCLE_BOB_CLEAN_CODE_REVIEW" in index
    assert "DATA_FLOW_AND_STATE" in index
    assert "DATABASE_SCHEMA_AND_DURABILITY" in index
    assert "Uncle Bob" in readme
    assert "assets/icon.png" in readme
    assert "assets/cover.png" in readme


def test_frontend_entrypoint_delegates_chat_workflow_to_focused_module() -> None:
    app_source = Path("app.py").read_text(encoding="utf-8")
    chat_workflow_source = Path("ui/chat_workflow.py").read_text(encoding="utf-8")

    assert "from ui.chat_workflow import render_video_chat_workspace" in app_source
    assert "def render_video_chat_workspace" in chat_workflow_source
    assert "service.send_message" in chat_workflow_source
    assert "GroqAgent" not in app_source
