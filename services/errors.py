"""Exception hierarchy for BRI.

Every exception raised in production code must subclass :class:`BriError`. The
UI layer and the FastAPI boundary are the only places allowed to catch
:class:`BriError`; everything else (genuine bugs, KeyboardInterrupt, etc.) is
allowed to crash with a traceback so the operator sees it immediately.

The categories are chosen so that HTTP status mapping is unambiguous. Add a
new subclass only when no existing one fits; the rule of thumb is "if you can
name the recovery path, name the exception."
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class BriError(Exception):
    """Root of the BRI exception hierarchy.

    Subclasses describe a class of failure (validation, auth, upstream, etc.).
    The base class accepts a human-readable ``message``, an optional machine
    ``code`` for client-side handling, the originating ``cause`` exception,
    and a ``context`` mapping for structured logging.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        cause: BaseException | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        :param message: Human-readable description suitable for logs and UI text.
        :param code: Optional machine-readable identifier (e.g. ``"video_not_found"``).
        :param cause: Original exception when this error wraps a lower-level failure.
        :param context: Structured fields attached to log records.
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.cause = cause
        self.context: dict[str, Any] = dict(context) if context else {}

    def __str__(self) -> str:  # pragma: no cover - trivial formatting
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Render the error as a JSON-serializable dict for API responses."""
        payload: dict[str, Any] = {"error": self.code, "message": self.message}
        if self.context:
            payload["context"] = self.context
        if self.cause is not None:
            payload["cause"] = type(self.cause).__name__
        return payload


class ConfigError(BriError):
    """Raised when startup configuration is invalid or required values are missing.

    Caught at the application boundary and reported to the operator with the
    offending environment variable. Never returned over the wire to clients.
    """


class ValidationError(BriError):
    """Raised when user input fails structural or semantic validation.

    Mapped to HTTP 400. The message is safe to surface to the end user.
    """


class AuthError(BriError):
    """Raised when credentials are missing, malformed, or rejected.

    Mapped to HTTP 401 (missing/invalid) or 403 (insufficient scope).
    """


class NotFoundError(BriError):
    """Raised when a requested resource does not exist.

    Mapped to HTTP 404. The message is safe to surface to the end user.
    """


class RateLimitError(BriError):
    """Raised when an upstream service has rate-limited BRI.

    Mapped to HTTP 429. ``retry_after`` carries the seconds-to-wait hint when
    the upstream supplied one.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class UpstreamError(BriError):
    """Raised when a third-party service returns an unexpected failure.

    Mapped to HTTP 502. The original ``cause`` should carry the upstream error.
    """


class TimeoutError(BriError):  # noqa: A001 - shadowing built-in is intentional here
    """Raised when an operation exceeds its budget.

    Mapped to HTTP 504. Distinct from :class:`UpstreamError` because timeouts
    may indicate local saturation rather than an upstream failure.
    """


class DependencyError(BriError):
    """Raised when an optional dependency is unavailable.

    Caught at the boundary and converted to graceful degradation: the feature
    that requires the dependency is skipped, the rest of the application
    keeps working. Never propagated to the user as an error.
    """


class StateError(BriError):
    """Raised when an internal invariant is violated.

    Mapped to HTTP 500. Indicates a programming bug; never surface the
    message to end users.
    """


class StorageError(BriError):
    """Raised when the database or filesystem layer fails.

    Mapped to HTTP 500. Always log the ``cause``; never include filesystem
    paths in the user-facing message.
    """


class ProcessingError(BriError):
    """Raised when the video processing pipeline fails irrecoverably.

    Mapped to HTTP 500. Distinct from :class:`DependencyError` because
    processing failure is a terminal event for the request, not a degradation.
    """


__all__ = [
    "BriError",
    "ConfigError",
    "ValidationError",
    "AuthError",
    "NotFoundError",
    "RateLimitError",
    "UpstreamError",
    "TimeoutError",
    "DependencyError",
    "StateError",
    "StorageError",
    "ProcessingError",
]


# ---------------------------------------------------------------------------
# HTTP status mapping. Keep the table next to the hierarchy so the contract
# between exception class and response code is in one place.
# ---------------------------------------------------------------------------

HTTP_STATUS: dict[type[BriError], int] = {
    ConfigError: 500,  # never returned to clients; logged then 503.
    ValidationError: 400,
    AuthError: 401,
    NotFoundError: 404,
    RateLimitError: 429,
    UpstreamError: 502,
    TimeoutError: 504,
    DependencyError: 500,  # treated as graceful-degradation, not surfaced.
    StateError: 500,
    StorageError: 500,
    ProcessingError: 500,
}


def http_status_for(err: BriError) -> int:
    """Return the HTTP status code that the FastAPI handler should emit."""
    return HTTP_STATUS.get(type(err), 500)


__all__.append("http_status_for")