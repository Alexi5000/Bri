#!/usr/bin/env python3
"""Smoke test the BRI MCP API.

By default this script validates the FastAPI application in-process with
``TestClient`` so CI and local validation do not require a separately running
server. Pass ``--url`` to smoke test a live deployment instead.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def smoke_in_process() -> int:
    os.environ.setdefault("ALLOW_MISSING_GROQ_FOR_TESTS", "true")
    os.environ.setdefault("APP_ENV", "test")
    try:
        from fastapi.testclient import TestClient

        from mcp_server.main import app
    except Exception as exc:  # pragma: no cover - dependency/environment guard
        print(f"In-process API smoke could not start: {exc}", file=sys.stderr)
        return 1

    with TestClient(app) as client:
        health = client.get("/health")
        tools = client.get("/tools")

    if health.status_code != 200:
        print(
            f"Health smoke failed with status {health.status_code}: {health.text}", file=sys.stderr
        )
        return 1
    if tools.status_code != 200:
        print(f"Tools smoke failed with status {tools.status_code}: {tools.text}", file=sys.stderr)
        return 1

    print("In-process API smoke passed.")
    return 0


def smoke_live_server(base_url: str, *, allow_offline: bool) -> int:
    try:
        import requests
    except ModuleNotFoundError:
        print("The requests package is required for --url smoke checks.", file=sys.stderr)
        return 1

    base = base_url.rstrip("/") + "/"
    try:
        health = requests.get(urljoin(base, "health"), timeout=5)
        health.raise_for_status()
        tools = requests.get(urljoin(base, "tools"), timeout=5)
        tools.raise_for_status()
    except requests.RequestException as exc:
        if allow_offline:
            print(f"Live API smoke skipped because server is offline: {exc}")
            return 0
        print(f"Live API smoke failed: {exc}", file=sys.stderr)
        return 1

    print("Live API smoke passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the BRI FastAPI service")
    parser.add_argument(
        "--url", help="Optional live API base URL. If omitted, TestClient is used in-process."
    )
    parser.add_argument(
        "--allow-offline", action="store_true", help="Return success if the live API is not running"
    )
    args = parser.parse_args()

    if args.url:
        return smoke_live_server(args.url, allow_offline=args.allow_offline)
    return smoke_in_process()


if __name__ == "__main__":
    raise SystemExit(main())
