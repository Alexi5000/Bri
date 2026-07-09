"""Production SQLite maintenance helpers for Bri.

The Streamlit product, FastAPI MCP service, and optional multimodal tooling all share
SQLite as Bri's durable local memory. This module provides operational helpers that
are safe to call from scripts, tests, or an administrative UI without coupling those
surfaces to low-level sqlite3 details.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import Config


@dataclass(frozen=True)
class DatabaseIntegrityReport:
    """Operational integrity result for Bri's SQLite database."""

    ok: bool
    database_path: str
    page_count: int
    freelist_count: int
    journal_mode: str
    wal_checkpoint: dict[str, Any]
    messages: tuple[str, ...]


@dataclass(frozen=True)
class DatabaseBackupResult:
    """Result returned after an online SQLite backup."""

    ok: bool
    source_path: str
    backup_path: str
    size_bytes: int
    created_at: str
    message: str


def _database_path(db_path: str | None = None) -> Path:
    return Path(db_path or Config.DATABASE_PATH)


def _backup_directory(backup_dir: str | None = None) -> Path:
    directory = Path(backup_dir or Path(Config.DATABASE_PATH).parent / "backups")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def configure_sqlite_for_production(db_path: str | None = None) -> dict[str, Any]:
    """Apply production-friendly SQLite pragmas and return the resulting settings."""

    path = _database_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        journal_mode = conn.execute("PRAGMA journal_mode = WAL").fetchone()[0]
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA optimize")
        synchronous = conn.execute("PRAGMA synchronous").fetchone()[0]
        busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
    return {
        "database_path": str(path),
        "journal_mode": str(journal_mode),
        "synchronous": synchronous,
        "busy_timeout_ms": busy_timeout,
    }


def create_sqlite_backup(db_path: str | None = None, backup_dir: str | None = None) -> DatabaseBackupResult:
    """Create an online backup using SQLite's backup API.

    This keeps the application usable while a backup is created and avoids copying
    partial WAL state by hand.
    """

    source = _database_path(db_path)
    if not source.exists():
        return DatabaseBackupResult(
            ok=False,
            source_path=str(source),
            backup_path="",
            size_bytes=0,
            created_at=datetime.now(UTC).isoformat(),
            message="Database file does not exist yet; no backup was created.",
        )

    created_at = datetime.now(UTC)
    backup_path = _backup_directory(backup_dir) / f"bri-{created_at.strftime('%Y%m%dT%H%M%SZ')}.db"
    with sqlite3.connect(source) as src, sqlite3.connect(backup_path) as dst:
        src.backup(dst)
        dst.execute("PRAGMA optimize")
    return DatabaseBackupResult(
        ok=True,
        source_path=str(source),
        backup_path=str(backup_path),
        size_bytes=backup_path.stat().st_size,
        created_at=created_at.isoformat(),
        message="SQLite online backup completed successfully.",
    )


def run_integrity_check(db_path: str | None = None) -> DatabaseIntegrityReport:
    """Run Bri's SQLite integrity and WAL checkpoint checks."""

    path = _database_path(db_path)
    if not path.exists():
        return DatabaseIntegrityReport(
            ok=False,
            database_path=str(path),
            page_count=0,
            freelist_count=0,
            journal_mode="missing",
            wal_checkpoint={},
            messages=("Database file does not exist.",),
        )

    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        messages = tuple(str(row[0]) for row in conn.execute("PRAGMA integrity_check").fetchall())
        page_count = int(conn.execute("PRAGMA page_count").fetchone()[0])
        freelist_count = int(conn.execute("PRAGMA freelist_count").fetchone()[0])
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0])
        checkpoint_row = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
        wal_checkpoint = {
            "busy": int(checkpoint_row[0]),
            "log_frames": int(checkpoint_row[1]),
            "checkpointed_frames": int(checkpoint_row[2]),
        }
    return DatabaseIntegrityReport(
        ok=messages == ("ok",),
        database_path=str(path),
        page_count=page_count,
        freelist_count=freelist_count,
        journal_mode=journal_mode,
        wal_checkpoint=wal_checkpoint,
        messages=messages,
    )


def vacuum_database(db_path: str | None = None) -> dict[str, Any]:
    """Run a controlled VACUUM after verifying database integrity."""

    report = run_integrity_check(db_path)
    if not report.ok:
        raise RuntimeError(f"Refusing to vacuum unhealthy database: {report.messages}")

    path = _database_path(db_path)
    before_bytes = path.stat().st_size
    with sqlite3.connect(path) as conn:
        conn.execute("VACUUM")
        conn.execute("PRAGMA optimize")
    after_bytes = path.stat().st_size
    return {
        "database_path": str(path),
        "before_bytes": before_bytes,
        "after_bytes": after_bytes,
        "reclaimed_bytes": max(0, before_bytes - after_bytes),
    }


__all__ = [
    "DatabaseBackupResult",
    "DatabaseIntegrityReport",
    "configure_sqlite_for_production",
    "create_sqlite_backup",
    "run_integrity_check",
    "vacuum_database",
]
