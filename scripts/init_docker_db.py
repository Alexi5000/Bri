#!/usr/bin/env python3
"""
Database initialization script for Docker deployment.
Creates the SQLite database and tables if they don't exist.
"""

import os
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_PATH
from utils.logging_config import get_logger

logger = get_logger(__name__)


def init_database():
    """Initialize the database with required tables."""

    # Ensure data directory exists
    db_dir = Path(DATABASE_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing database at: %s", DATABASE_PATH)

    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Read schema from file
    schema_path = Path(__file__).parent.parent / "storage" / "schema.sql"

    if schema_path.exists():
        logger.info("Loading schema from: %s", schema_path)
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema
        cursor.executescript(schema_sql)
        logger.info("Database schema applied successfully")
    else:
        # Fallback: create tables inline
        logger.warning("Schema file not found, creating tables inline...")

        cursor.executescript("""
            -- Videos table
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                duration REAL,
                upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processing_status TEXT DEFAULT 'pending',
                thumbnail_path TEXT
            );

            -- Memory table for conversation history
            CREATE TABLE IF NOT EXISTS memory (
                message_id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
            );

            -- Video context table for processed data
            CREATE TABLE IF NOT EXISTS video_context (
                context_id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                context_type TEXT NOT NULL,
                timestamp REAL,
                data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_memory_video_id ON memory(video_id);
            CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp);
            CREATE INDEX IF NOT EXISTS idx_context_video_id ON video_context(video_id);
            CREATE INDEX IF NOT EXISTS idx_context_type ON video_context(context_type);
            CREATE INDEX IF NOT EXISTS idx_context_timestamp ON video_context(timestamp);
        """)
        logger.info("Database tables created successfully")

    # Commit and close
    conn.commit()
    conn.close()

    logger.info(
        "Database initialization complete: location=%s size=%d bytes",
        DATABASE_PATH,
        Path(DATABASE_PATH).stat().st_size,
    )


if __name__ == "__main__":
    try:
        init_database()
        sys.exit(0)
    except Exception as e:
        logger.error("Error initializing database: %s", e)
        sys.exit(1)
