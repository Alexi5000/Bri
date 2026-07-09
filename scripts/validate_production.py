#!/usr/bin/env python3
"""Production validation for Bri.

Runs fast checks that do not require GPU models, Redis, a Groq key, or uploaded
media. Heavy model and end-to-end media tests remain available through pytest
markers and local QA workflows.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "pyproject.toml",
    ".env.example",
    "Dockerfile.mcp",
    "Dockerfile.ui",
    "docker-compose.yml",
    "assets/icon.png",
    "assets/cover.png",
    "docs/ARCHITECTURE.md",
    "docs/TESTING.md",
    "docs/API.md",
    "docs/DEPLOYMENT.md",
]


def check_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit("Missing required production files: " + ", ".join(missing))


def check_readme_assets() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for asset in ("assets/icon.png", "assets/cover.png"):
        if asset not in readme:
            raise SystemExit(f"README must preserve graphic reference: {asset}")


def run_pytest() -> None:
    env = os.environ.copy()
    env.setdefault("ALLOW_MISSING_GROQ_FOR_TESTS", "true")
    env.setdefault("APP_ENV", "test")
    command = [sys.executable, "-m", "pytest", "tests/production"]
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> None:
    check_files()
    check_readme_assets()
    run_pytest()
    print("BRI production validation passed.")


if __name__ == "__main__":
    main()
