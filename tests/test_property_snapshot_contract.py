"""Property-based, snapshot, and contract tests for the public surface.

- Property tests use Hypothesis to exercise every validator with random
  inputs and prove an invariant that must hold for all of them.
- Snapshot tests use syrupy to lock the JSON shape of every public
  response envelope. Any unintentional shape change is a CI failure
  until the snapshot is updated on purpose.
- Contract tests use httpx + FastAPI ASGI transport to exercise the
  live FastAPI app without a real HTTP server, Docker, or network.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings, strategies as st
from syrupy.assertion import SnapshotAssertion

# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestValidatorsProperty:
    """Property-based tests using Hypothesis.

    These cover invariants of the public BriError hierarchy and Pydantic
    response models. They are pure functions and safe to exercise without
    any database, network, or filesystem setup.
    """

    @given(
        message=st.text(min_size=1, max_size=200),
        code=st.one_of(st.none(), st.text(min_size=1, max_size=32, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), max_codepoint=0x7E,
        ))),
        extra_ctx=st.dictionaries(
            keys=st.text(min_size=1, max_size=16, alphabet=st.characters(
                whitelist_categories=("Lu", "Ll"), max_codepoint=0x7E,
            )),
            values=st.integers(min_value=-1000, max_value=1000),
            max_size=4,
        ),
    )
    @settings(max_examples=40, deadline=None)
    def test_bri_error_round_trips_to_dict(
        self, message: str, code: str | None, extra_ctx: dict[str, int]
    ) -> None:
        """BriError.to_dict() must always serialise to valid JSON."""
        from services.errors import BriError

        err = BriError(message, code=code, context=extra_ctx)
        payload = err.to_dict()
        # Must always have error and message.
        assert "error" in payload
        assert "message" in payload
        assert payload["message"] == message
        # Round-trip through JSON to confirm serialisability.
        serialised = json.dumps(payload)
        restored = json.loads(serialised)
        assert restored == payload

    @given(
        count=st.integers(min_value=0, max_value=10_000),
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
    )
    @settings(max_examples=30)
    def test_pydantic_validation_round_trip(
        self, count: int, temperature: float
    ) -> None:
        """Response models must round-trip through dict and back."""
        from models.responses import ToolExecutionResponse

        original = ToolExecutionResponse(
            status="success",
            result={"count": count, "temperature": temperature},
            cached=False,
            execution_time=0.042,
        )
        payload = original.model_dump()
        restored = ToolExecutionResponse(**payload)
        assert restored.status == original.status
        assert restored.result == original.result
        assert restored.cached == original.cached
        assert restored.execution_time == original.execution_time


# ---------------------------------------------------------------------------
# Snapshot tests
# ---------------------------------------------------------------------------


class TestResponseEnvelopesSnapshot:
    """Lock the JSON shape of every public response envelope.

    Update snapshots intentionally with ``pytest --snapshot-update``.
    """

    # The ``snapshot`` fixture is provided by pytest-syrupy automatically;
    # no explicit fixture definition is required here.

    def test_bri_error_envelope_shape(self, snapshot: SnapshotAssertion) -> None:
        """Every BriError subclass serialises to a stable JSON envelope."""
        from services.errors import (
            AuthError,
            BriError,
            DependencyError,
            ProcessingError,
            StorageError,
            ValidationError,
        )

        cases = {
            "validation": ValidationError("bad input", code="bad_input"),
            "auth": AuthError("nope"),
            "dependency": DependencyError("optional missing"),
            "processing": ProcessingError("kaboom"),
            "storage": StorageError("disk full"),
        }
        envelope = {name: err.to_dict() for name, err in cases.items()}
        envelope["bare"] = BriError("plain").to_dict()
        assert envelope == snapshot

    def test_tool_execution_response_shape(
        self, snapshot: SnapshotAssertion
    ) -> None:
        """The standard tool-execution envelope serialises to a stable JSON."""
        from models.responses import ToolExecutionResponse

        response = ToolExecutionResponse(
            status="success",
            result={"frames": [{"timestamp": 0.0, "path": "/tmp/x.jpg"}]},
            cached=False,
            execution_time=0.042,
        )
        payload = response.model_dump()
        assert payload == snapshot

    def test_assistant_message_response_shape(
        self, snapshot: SnapshotAssertion
    ) -> None:
        """The chat-panel assistant message shape is locked."""
        from models.responses import AssistantMessageResponse

        payload = AssistantMessageResponse(
            message="BRI found three frames of interest.",
            frames=["/tmp/frame_001.jpg"],
            timestamps=[15.0],
            suggestions=["What happens next?"],
        ).model_dump()
        assert payload == snapshot


# ---------------------------------------------------------------------------
# Contract tests (live FastAPI app via httpx ASGI transport)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fastapi_client():
    """Live FastAPI app via TestClient; runs the real BriError handler."""
    from mcp_server.main import app

    return TestClient(app, raise_server_exceptions=False)


class TestMCPContracts:
    """Public endpoint contracts against the live FastAPI app."""

    def test_health_contract(self, fastapi_client: TestClient) -> None:
        """GET /health returns the documented envelope."""
        response = fastapi_client.get("/health")
        assert response.status_code in (200, 503)  # 503 if DB unhealthy
        body = response.json()
        # Top-level fields: status, version, timestamp, checks.
        assert "status" in body
        assert "version" in body
        assert "checks" in body
        assert isinstance(body["checks"], dict)

    def test_tools_contract(self, fastapi_client: TestClient) -> None:
        """GET /tools returns the documented envelope with a tools list."""
        response = fastapi_client.get("/tools")
        assert response.status_code == 200
        body = response.json()
        assert body.get("success") is True or "data" in body
        data = body.get("data", body)
        assert "tools" in data
        assert isinstance(data["tools"], list)
        if data["tools"]:
            tool = data["tools"][0]
            assert "name" in tool
            assert "description" in tool

    def test_validation_error_returns_400(
        self, fastapi_client: TestClient
    ) -> None:
        """POST /tools/{name}/execute with a bad payload returns 400 or 422."""
        # Pick the first tool name and submit a clearly invalid body.
        tools_resp = fastapi_client.get("/tools")
        if tools_resp.status_code != 200:
            pytest.skip("tools endpoint not available")
        tools = tools_resp.json().get("data", {}).get("tools", [])
        if not tools:
            pytest.skip("No tools registered in this environment")
        name = tools[0]["name"]
        response = fastapi_client.post(
            f"/tools/{name}/execute",
            json={"video_id": "", "parameters": {}},
        )
        # 400 for ValidationError, 404/422 for unknown tool / pydantic.
        assert response.status_code in (400, 404, 422)

    def test_bri_error_envelope_via_http(
        self, fastapi_client: TestClient
    ) -> None:
        """BriError raised inside a handler becomes a structured JSON error."""
        from fastapi import FastAPI

        from services.errors import NotFoundError, http_status_for

        # Mount a one-off route on the real app so we exercise the production
        # exception handler, not a copy.
        test_app = fastapi_client.app

        @test_app.get("/_contract_test/raise_not_found")
        def _raise() -> dict[str, str]:
            raise NotFoundError("missing video", code="video_not_found")

        response = fastapi_client.get("/_contract_test/raise_not_found")
        assert response.status_code == http_status_for(NotFoundError("x"))
        body = response.json()
        # The code field reflects the explicit ``code`` we passed, not the
        # class name. This lets clients branch on stable identifiers like
        # "video_not_found" instead of implementation details.
        assert body["error"] == "video_not_found"
        assert body["message"] == "missing video"
        # context is only present when set, and an empty dict is omitted
        # from the payload to keep the envelope minimal.
        assert "context" not in body or body["context"] == {}


# ---------------------------------------------------------------------------
# Schema tests for storage
# ---------------------------------------------------------------------------


class TestStorageSchemaContract:
    """The on-disk SQLite schema must remain stable for downstream tooling."""

    def test_schema_file_exists(self) -> None:
        schema = Path("storage/schema.sql")
        assert schema.exists()

    def test_schema_required_tables(self) -> None:
        text = Path("storage/schema.sql").read_text(encoding="utf-8")
        for required in ("videos", "video_context", "memory"):
            assert "CREATE TABLE" in text
            assert required in text, required