"""Typed client for Bri's FastAPI MCP service.

This module is the production middle-layer boundary between Streamlit-facing
application services and the FastAPI MCP server. It centralizes timeout policy,
standardized response-envelope handling, offline behavior, and endpoint naming
so UI code never depends on raw HTTP details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from config import Config


class MCPClientError(RuntimeError):
    """Raised when the MCP service returns an invalid or failed response."""


@dataclass(frozen=True)
class MCPHealth:
    """Operational view of the FastAPI MCP service."""

    online: bool
    status: str
    url: str
    components: dict[str, Any] = field(default_factory=dict)
    detail: str = ""


@dataclass(frozen=True)
class MCPToolSummary:
    """Public MCP tool descriptor used by Streamlit and readiness views."""

    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessingStartResult:
    """Result returned after requesting progressive video processing."""

    accepted: bool
    video_id: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoProgress:
    """Typed progress view for Bri's staged video intelligence pipeline."""

    video_id: str
    processing: bool
    message: str
    stage: str = "idle"
    progress_percent: float = 0.0
    frames_extracted: int = 0
    captions_generated: int = 0
    transcript_segments: int = 0
    objects_detected: int = 0
    payload: dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """Small, typed, resilient client for Bri's MCP API."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or Config.get_mcp_server_url()).rstrip("/")
        self.timeout = float(timeout or Config.REQUEST_TIMEOUT)

    def health(self) -> MCPHealth:
        """Return MCP health without raising for offline service states."""

        try:
            response = httpx.get(f"{self.base_url}/health", timeout=min(self.timeout, 5.0))
            response.raise_for_status()
            payload = self._unwrap(response.json())
            status = str(payload.get("status", "healthy")) if isinstance(payload, dict) else "healthy"
            components = payload.get("components", {}) if isinstance(payload, dict) else {}
            return MCPHealth(
                online=True,
                status=status,
                url=self.base_url,
                components=components if isinstance(components, dict) else {},
                detail="MCP service is reachable.",
            )
        except Exception as exc:  # pragma: no cover - exact exception varies by httpx version
            return MCPHealth(
                online=False,
                status="offline",
                url=self.base_url,
                detail=f"MCP service is not reachable: {exc}",
            )

    def list_tools(self) -> list[MCPToolSummary]:
        """Return the public MCP tool catalog.

        The API may return either a direct payload or Bri's standardized response
        envelope. Both are supported here so frontend code remains stable.
        """

        response = httpx.get(f"{self.base_url}/tools", timeout=min(self.timeout, 10.0))
        response.raise_for_status()
        payload = self._unwrap(response.json())
        raw_tools = payload.get("tools", payload) if isinstance(payload, dict) else payload
        if not isinstance(raw_tools, list):
            raise MCPClientError("MCP tool catalog response did not contain a tool list.")

        tools: list[MCPToolSummary] = []
        for item in raw_tools:
            if isinstance(item, str):
                tools.append(MCPToolSummary(name=item))
            elif isinstance(item, dict):
                tools.append(
                    MCPToolSummary(
                        name=str(item.get("name", "")),
                        description=str(item.get("description", "")),
                        parameters=item.get("parameters", {}) if isinstance(item.get("parameters", {}), dict) else {},
                    )
                )
        return [tool for tool in tools if tool.name]

    def start_progressive_processing(self, video_id: str, video_path: str) -> ProcessingStartResult:
        """Request staged processing for an uploaded video."""

        response = httpx.post(
            f"{self.base_url}/videos/{video_id}/process-progressive",
            json={"video_path": video_path},
            timeout=min(self.timeout, 15.0),
        )
        if response.status_code >= 400:
            raise MCPClientError(f"MCP progressive processing failed: {response.text}")
        payload = self._unwrap(response.json())
        message = "Processing started."
        if isinstance(payload, dict):
            message = str(payload.get("message") or payload.get("status") or message)
        return ProcessingStartResult(
            accepted=True,
            video_id=video_id,
            message=message,
            payload=payload if isinstance(payload, dict) else {"result": payload},
        )

    def video_status(self, video_id: str) -> dict[str, Any]:
        """Return processing/status data for a video from the MCP API."""

        response = httpx.get(f"{self.base_url}/videos/{video_id}/status", timeout=min(self.timeout, 10.0))
        response.raise_for_status()
        payload = self._unwrap(response.json())
        return payload if isinstance(payload, dict) else {"status": payload}

    def video_progress(self, video_id: str) -> VideoProgress:
        """Return typed progressive-processing status for a video."""

        response = httpx.get(f"{self.base_url}/videos/{video_id}/progress", timeout=min(self.timeout, 10.0))
        response.raise_for_status()
        payload = self._unwrap(response.json())
        data = payload if isinstance(payload, dict) else {"message": str(payload)}
        return VideoProgress(
            video_id=str(data.get("video_id") or video_id),
            processing=bool(data.get("processing", False)),
            stage=str(data.get("stage") or "idle"),
            progress_percent=float(data.get("progress_percent") or 0.0),
            message=str(data.get("message") or "No active processing for this video."),
            frames_extracted=int(data.get("frames_extracted") or 0),
            captions_generated=int(data.get("captions_generated") or 0),
            transcript_segments=int(data.get("transcript_segments") or 0),
            objects_detected=int(data.get("objects_detected") or 0),
            payload=data,
        )

    @staticmethod
    def _unwrap(payload: Any) -> Any:
        """Unwrap Bri's standardized API envelope when present."""

        if isinstance(payload, dict):
            if "data" in payload and any(key in payload for key in ("success", "request_id", "api_version")):
                return payload["data"]
            if payload.get("success") is False:
                raise MCPClientError(str(payload.get("error") or payload.get("message") or "MCP request failed."))
        return payload


__all__ = [
    "MCPClient",
    "MCPClientError",
    "MCPHealth",
    "MCPToolSummary",
    "ProcessingStartResult",
    "VideoProgress",
]
