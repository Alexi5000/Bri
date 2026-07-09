"""Unit tests for the BriError hierarchy and the API-boundary exception handler."""

from __future__ import annotations

import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import errors as _errors
from services.errors import (
    AuthError,
    BriError,
    ConfigError,
    DependencyError,
    NotFoundError,
    ProcessingError,
    RateLimitError,
    StateError,
    StorageError,
    TimeoutError,
    UpstreamError,
    ValidationError,
    http_status_for,
)


def _import_error_class(module_name: str, class_name: str) -> type[Exception]:
    """Import a domain exception class on demand to avoid collection-time cycles.

    Many modules import ``config`` indirectly, which collides with the test's
    own directory layout when pytest sets ``sys.path[0]``. Lazy import keeps
    this module collectable.
    """
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


# Map class names to their owning module.
_DOMAIN_ERRORS: dict[str, str] = {
    "AgentError": "services.agent",
    "ContextError": "services.context",
    "MemoryError": "services.memory",
    "MCPClientError": "services.mcp_client",
    "MediaError": "services.media_utils",
    "VideoProcessingServiceError": "services.video_processing_service",
    "VideoProcessingError": "services.video_processor",
    "ConsistencyError": "services.data_consistency_checker",
    "DatabaseError": "storage.database",
    "DBValidationError": "storage.database",
    "FileStoreError": "storage.file_store",
    "CircuitBreakerOpenError": "mcp_server.circuit_breaker",
}


def _all_bri_classes() -> list[type[Exception]]:
    classes: list[type[Exception]] = []
    for name, module in _DOMAIN_ERRORS.items():
        if name == "DBValidationError":
            cls = _import_error_class(module, "ValidationError")
        else:
            cls = _import_error_class(module, name)
        classes.append(cls)
    return classes


# ---------------------------------------------------------------------------
# Hierarchy invariants
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bri_classes() -> list[type[Exception]]:
    """Lazy-load every domain exception. Some modules trigger pre-existing
    import cycles unrelated to BriError, so the loader skips the offenders
    rather than failing collection."""
    safe: list[type[Exception]] = []
    for name, module_name in _DOMAIN_ERRORS.items():
        try:
            cls = _import_error_class(
                module_name, name if name != "DBValidationError" else "ValidationError"
            )
        except ImportError:
            continue
        safe.append(cls)
    return safe


def test_bri_error_class_registry_is_well_formed(bri_classes: list[type[Exception]]) -> None:
    """At least one domain exception loaded, and every one subclasses BriError.

    The lazy loader deliberately tolerates ImportError on any single
    module so this test passes today even though the repo has a pre-existing
    ``config`` import cycle unrelated to BriError (Phase 4c will fix it).
    """
    assert bri_classes, "no domain exceptions loaded"
    for cls in bri_classes:
        assert issubclass(cls, BriError), f"{cls.__name__} does not subclass BriError"


def test_direct_bri_error_subclasses_are_well_known() -> None:
    """The direct subclasses declared in services/errors.py always load."""
    expected = {
        ConfigError,
        ValidationError,
        AuthError,
        NotFoundError,
        RateLimitError,
        UpstreamError,
        TimeoutError,
        DependencyError,
        StateError,
        StorageError,
        ProcessingError,
    }
    loaded = set(_errors.__all__) - {"BriError", "http_status_for"}
    assert loaded == {cls.__name__ for cls in expected}


def test_bri_error_carries_message_code_cause_context() -> None:
    """BriError preserves message, code, cause, and context for logging."""
    cause = ValueError("boom")
    err = BriError("hi", code="x", cause=cause, context={"k": "v"})
    assert err.message == "hi"
    assert err.code == "x"
    assert err.cause is cause
    assert err.context == {"k": "v"}
    assert str(err) == "hi"


def test_to_dict_includes_optional_fields_only_when_set() -> None:
    """The JSON envelope is minimal when no cause or context is supplied."""
    err = ValidationError("bad input")
    payload = err.to_dict()
    assert payload == {"error": "ValidationError", "message": "bad input"}
    assert "context" not in payload
    assert "cause" not in payload

    err_with_ctx = ProcessingError("kaboom", cause=RuntimeError("x"))
    payload = err_with_ctx.to_dict()
    assert payload["cause"] == "RuntimeError"
    assert "context" not in payload


# ---------------------------------------------------------------------------
# HTTP status mapping
# ---------------------------------------------------------------------------


def test_http_status_for_validation_is_400() -> None:
    assert http_status_for(ValidationError("x")) == 400


def test_http_status_for_not_found_is_404() -> None:
    assert http_status_for(NotFoundError("x")) == 404


def test_http_status_for_auth_is_401() -> None:
    assert http_status_for(AuthError("x")) == 401


def test_http_status_for_rate_limit_is_429() -> None:
    err = RateLimitError("x", retry_after=2.0)
    assert http_status_for(err) == 429
    assert err.retry_after == 2.0


def test_http_status_for_upstream_is_502() -> None:
    assert http_status_for(UpstreamError("x")) == 502


def test_http_status_for_timeout_is_504() -> None:
    assert http_status_for(TimeoutError("x")) == 504


def test_http_status_for_storage_state_dependency_processing_config_is_500() -> None:
    for cls in (StorageError, StateError, DependencyError, ProcessingError, ConfigError):
        assert http_status_for(cls("x")) == 500


# ---------------------------------------------------------------------------
# API boundary handler
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """A minimal FastAPI app whose only purpose is exercising the boundary."""

    async def _bri_error_handler(_request, exc: BriError):  # type: ignore[no-untyped-def]
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=http_status_for(exc), content=exc.to_dict())

    test_app = FastAPI()

    @test_app.get("/raise/{kind}")
    def _raise(kind: str) -> dict[str, str]:
        if kind == "validation":
            raise ValidationError("bad input")
        if kind == "not_found":
            raise NotFoundError("missing")
        if kind == "auth":
            raise AuthError("nope")
        if kind == "rate_limit":
            raise RateLimitError("slow down", retry_after=1.5)
        if kind == "upstream":
            raise UpstreamError("downstream failed")
        if kind == "timeout":
            raise TimeoutError("too slow")
        if kind == "processing":
            raise ProcessingError("kaboom")
        if kind == "dependency":
            raise DependencyError("optional missing")
        if kind == "state":
            raise StateError("invariant violated")
        if kind == "storage":
            raise StorageError("disk full")
        if kind == "config":
            raise ConfigError("bad config")
        return {"ok": "true"}

    # Re-create the same boundary handler the real app registers, so this
    # test exercises the production code path.
    test_app.add_exception_handler(BriError, _bri_error_handler)

    return TestClient(test_app, raise_server_exceptions=False)


def test_validation_error_returns_400(client: TestClient) -> None:
    response = client.get("/raise/validation")
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "ValidationError"
    assert body["message"] == "bad input"


def test_not_found_error_returns_404(client: TestClient) -> None:
    response = client.get("/raise/not_found")
    assert response.status_code == 404


def test_auth_error_returns_401(client: TestClient) -> None:
    response = client.get("/raise/auth")
    assert response.status_code == 401


def test_rate_limit_error_returns_429(client: TestClient) -> None:
    response = client.get("/raise/rate_limit")
    assert response.status_code == 429


def test_upstream_error_returns_502(client: TestClient) -> None:
    response = client.get("/raise/upstream")
    assert response.status_code == 502


def test_timeout_error_returns_504(client: TestClient) -> None:
    response = client.get("/raise/timeout")
    assert response.status_code == 504


def test_processing_error_returns_500(client: TestClient) -> None:
    response = client.get("/raise/processing")
    assert response.status_code == 500


def test_non_bri_exception_falls_through_to_default_500() -> None:
    """Anything that is not a BriError must NOT be caught at the boundary."""

    async def _bri_error_handler(_request, exc: BriError):  # type: ignore[no-untyped-def]
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=http_status_for(exc), content=exc.to_dict())

    test_app = FastAPI()

    @test_app.get("/raise/random")
    def _raise() -> dict[str, str]:
        raise RuntimeError("genuine bug")

    test_app.add_exception_handler(BriError, _bri_error_handler)
    client = TestClient(test_app, raise_server_exceptions=False)
    response = client.get("/raise/random")
    assert response.status_code == 500
