"""Generate the per-module API reference stub files mkdocstrings consumes.

Run before ``mkdocs build`` to populate ``docs/reference/<package>/<module>.md``
with one stub per module. The stub uses the ``:::<package>.<module>`` directive
that mkdocstrings resolves at build time.

Usage:
    python scripts/build_api_reference.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_REF = ROOT / "docs" / "reference"

PACKAGES: dict[str, list[str]] = {
    "mcp_server": [
        "main",
        "cache",
        "circuit_breaker",
        "middleware",
        "registry",
        "response_models",
        "validation",
        "versioning",
    ],
    "services": [
        "agent",
        "application",
        "context",
        "errors",
        "mcp_client",
        "memory",
        "router",
    ],
    "storage": [
        "database",
        "file_store",
        "maintenance",
        "migrations",
    ],
    "models": [
        "memory",
        "responses",
        "tools",
        "video",
    ],
}


def _stub(package: str, module: str) -> str:
    """Return the mkdocstrings stub for one module."""
    return (
        f"# `{package}.{module}`\n\n::: {package}.{module}\n    options:\n      show_source: true\n"
    )


def main() -> None:
    written = 0
    for package, modules in PACKAGES.items():
        target_dir = DOCS_REF / package
        target_dir.mkdir(parents=True, exist_ok=True)
        for module in modules:
            target = target_dir / f"{module}.md"
            target.write_text(_stub(package, module), encoding="utf-8")
            written += 1
    print(f"Wrote {written} reference stubs under {DOCS_REF}")


if __name__ == "__main__":
    main()
