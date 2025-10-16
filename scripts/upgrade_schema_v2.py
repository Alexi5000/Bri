"""Upgrade existing database to schema version 2.

This script upgrades an existing BRI database to version 2 with enhanced constraints.
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import get_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade_to_v2():
    """Upgrade database to version 2."""
    db = get_database()
    conn = db.get_connection()
    
    try:
        logger.info("Starting schema upgrade to version 2...")
        
        # Check if schema_version table exists
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        ).fetchone()
        
        if not result:
            logger.info("Creating schema_version table...")
            conn.execute("""
                CREATE TABLE schema_version (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    applied_by TEXT DEFAULT 'system'
                )
            """)
            conn.execute(
                "INSERT INTO schema_version (version, description) VALUES (1, 'Initial schema')"
            )
        
        # Check if deleted_at column exists
        result = conn.execute("PRAGMA table_info(videos)").fetchall()
        columns = [row[1] for row in result]
        
        if 'deleted_at' not in columns:
            logger.info("Adding deleted_at column to videos table...")
            conn.execute("ALTER TABLE videos ADD COLUMN deleted_at DATETIME")
        
        # Create new indexes
        logger.info("Creating new indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_videos_deleted_at ON videos(deleted_at)",
            "CREATE INDEX IF NOT EXISTS idx_memory_video_timestamp ON memory(video_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_video_context_lookup ON video_context(video_id, context_type, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_video_context_type_timestamp ON video_context(context_type, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_data_lineage_video ON data_lineage(video_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_data_lineage_context ON data_lineage(context_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_videos_active ON videos(processing_status) WHERE deleted_at IS NULL"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except sqlite3.Error as e:
                logger.warning(f"Index creation warning: {e}")
        
        # Record version 2
        conn.execute(
            "INSERT OR IGNORE INTO schema_version (version, description) VALUES (2, 'Enhanced constraints and indexes')"
        )
        
        conn.commit()
        logger.info("✓ Schema upgrade to version 2 complete!")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Schema upgrade failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    upgrade_to_v2()
