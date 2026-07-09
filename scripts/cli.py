"""Command-line entry points for the ``bri-video-agent`` package.

Three console scripts are exposed via ``pyproject.toml``:

- ``bri-video-agent`` -> :func:`main` (decides whether to run the API, the
  UI, or print help based on the first argument).
- ``bri-mcp`` -> :func:`run_mcp` (FastAPI MCP server).
- ``bri-ui`` -> :func:`run_ui` (Streamlit front-end).

The CLI is deliberately thin: it forwards to uvicorn and streamlit with
the project's documented defaults so ``pip install bri-video-agent`` is
the only thing an operator needs to do.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence


def _python_executable() -> str:
    """Return the path to the current Python interpreter."""
    return sys.executable


def run_mcp(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> int:
    """Start the FastAPI MCP server.

    Parameters
    ----------
    host:
        Interface to bind. Defaults to all interfaces so Docker users
        can reach the service from a sibling container.
    port:
        TCP port. Defaults to 8000.
    reload:
        Enable uvicorn auto-reload. Off by default; turn on for local dev.
    """
    import uvicorn

    uvicorn.run(
        "mcp_server.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
    return 0


def run_ui(host: str = "0.0.0.0", port: int = 8501) -> int:
    """Start the Streamlit UI.

    Uses ``streamlit run`` so configuration in ``.streamlit/config.toml``
    is honoured. Operators that prefer a Python entry point can still
    import ``app.main`` from their own launcher.
    """
    import subprocess

    cmd = [
        _python_executable(),
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(port),
        "--server.address",
        host,
    ]
    return subprocess.call(cmd)


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the first CLI argument to the right sub-command.

    With no arguments, prints a one-screen help banner.
    """
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help"}:
        print(
            "Usage:\n"
            "  bri-video-agent mcp [--host HOST] [--port PORT] [--reload]\n"
            "  bri-video-agent ui  [--host HOST] [--port PORT]\n"
            "  bri-video-agent --help\n"
        )
        return 0
    sub = args[0]

    if sub == "mcp":
        return run_mcp()
    if sub == "ui":
        return run_ui()
    print(f"Unknown sub-command: {sub!r}. Run with --help for usage.")
    return 2


if __name__ == "__main__":  # pragma: no cover - thin entry point
    raise SystemExit(main())
