"""Database migration system for BRI video agent.

This module provides a simple migration framework for managing database schema changes.
Migrations are versioned and tracked in the schema_version table.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from storage.database import Database, DatabaseError

logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration."""
    
    def __init__(
        self,
        version: int,
        description: str,
        up: Callable[[sqlite3.Connection], None],
        down: Optional[Callable[[sqlite3.Connection], None]] = None
    ):
        """Initialize migration.
        
        Args:
            version: Migration version number (must be unique and sequential)
            description: Human-readable description of the migration
            up: Function to apply the migration (takes connection as argument)
            down: Optional function to rollback the migration
        """
        self.version = version
        self.description = description
        self.up = up
        self.down = down
    
    def apply(self, conn: sqlite3.Connection) -> None:
        """Apply the migration.
        
        Args:
            conn: Database connection
            
        Raises:
            DatabaseError: If migration fails
        """
        try:
            logger.info(f"Applying migration {self.version}: {self.description}")
            self.up(conn)
            
            # Record migration in schema_version table
            conn.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (self.version, self.description)
            )
            conn.commit()
            logger.info(f"Migration {self.version} applied successfully")
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Migration {self.version} failed: {e}")
            raise DatabaseError(f"Migration {self.version} failed: {e}")
    
    def rollback(self, conn: sqlite3.Connection) -> None:
        """Rollback the migration.
        
        Args:
            conn: Database connection
            
        Raises:
            DatabaseError: If rollback fails or no rollback function defined
        """
        if self.down is None:
            raise DatabaseError(f"Migration {self.version} has no rollback function")
        
        try:
            logger.info(f"Rolling back migration {self.version}: {self.description}")
            self.down(conn)
            
            # Remove migration from schema_version table
            conn.execute("DELETE FROM schema_version WHERE version = ?", (self.version,))
            conn.commit()
            logger.info(f"Migration {self.version} rolled back successfully")
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Rollback of migration {self.version} failed: {e}")
            raise DatabaseError(f"Rollback of migration {self.version} failed: {e}")


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db: Database):
        """Initialize migration manager.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.migrations: List[Migration] = []
        self._register_migrations()
    
    def _register_migrations(self) -> None:
        """Register all available migrations."""
        # Migration 1: Initial schema (already applied via schema.sql)
        # This is a placeholder for tracking purposes
        
        # Migration 2: Enhanced constraints and indexes (current version)
        # Already applied via updated schema.sql
        
        # Future migrations can be added here
        pass
    
    def get_current_version(self) -> int:
        """Get current database schema version.
        
        Returns:
            Current version number, or 0 if no migrations applied
        """
        try:
            result = self.db.execute_query(
                "SELECT MAX(version) as version FROM schema_version"
            )
            if result and result[0]['version']:
                return result[0]['version']
            return 0
        except sqlite3.Error:
            # schema_version table doesn't exist yet
            return 0
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations.
        
        Returns:
            List of migrations that haven't been applied yet
        """
        current_version = self.get_current_version()
        return [m for m in self.migrations if m.version > current_version]
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations.
        
        Returns:
            List of migration records from schema_version table
        """
        try:
            results = self.db.execute_query(
                "SELECT * FROM schema_version ORDER BY version"
            )
            return [dict(row) for row in results]
        except sqlite3.Error:
            return []
    
    def migrate(self, target_version: Optional[int] = None) -> None:
        """Apply pending migrations up to target version.
        
        Args:
            target_version: Target version to migrate to (None = latest)
            
        Raises:
            DatabaseError: If migration fails
        """
        current_version = self.get_current_version()
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return
        
        # Filter migrations up to target version
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            logger.info(f"Already at version {current_version}")
            return
        
        logger.info(f"Migrating from version {current_version} to {pending[-1].version}")
        
        conn = self.db.get_connection()
        for migration in pending:
            migration.apply(conn)
        
        logger.info(f"Migration complete. Current version: {self.get_current_version()}")
    
    def rollback(self, target_version: Optional[int] = None, steps: int = 1) -> None:
        """Rollback migrations.
        
        Args:
            target_version: Target version to rollback to (None = rollback N steps)
            steps: Number of migrations to rollback (default: 1)
            
        Raises:
            DatabaseError: If rollback fails
        """
        current_version = self.get_current_version()
        
        if current_version == 0:
            logger.info("No migrations to rollback")
            return
        
        # Determine which migrations to rollback
        if target_version is not None:
            migrations_to_rollback = [
                m for m in reversed(self.migrations)
                if target_version < m.version <= current_version
            ]
        else:
            migrations_to_rollback = [
                m for m in reversed(self.migrations)
                if m.version <= current_version
            ][:steps]
        
        if not migrations_to_rollback:
            logger.info("No migrations to rollback")
            return
        
        logger.info(f"Rolling back {len(migrations_to_rollback)} migration(s)")
        
        conn = self.db.get_connection()
        for migration in migrations_to_rollback:
            migration.rollback(conn)
        
        logger.info(f"Rollback complete. Current version: {self.get_current_version()}")
    
    def status(self) -> Dict[str, Any]:
        """Get migration status.
        
        Returns:
            Dictionary with migration status information
        """
        current_version = self.get_current_version()
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'current_version': current_version,
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_migrations': applied,
            'pending_migrations': [
                {'version': m.version, 'description': m.description}
                for m in pending
            ]
        }
    
    def test_migration(self, migration: Migration) -> bool:
        """Test a migration by applying and rolling back.
        
        Args:
            migration: Migration to test
            
        Returns:
            True if test successful, False otherwise
        """
        logger.info(f"Testing migration {migration.version}")
        
        try:
            # Create a test database
            test_db_path = Path(self.db.db_path).parent / "test_migration.db"
            test_db = Database(str(test_db_path))
            test_db.connect()
            test_db.initialize_schema()
            
            conn = test_db.get_connection()
            
            # Apply migration
            migration.apply(conn)
            logger.info(f"Migration {migration.version} applied successfully in test")
            
            # Rollback migration
            if migration.down:
                migration.rollback(conn)
                logger.info(f"Migration {migration.version} rolled back successfully in test")
            
            # Clean up
            test_db.close()
            test_db_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Migration test failed: {e}")
            return False


def create_migration(
    version: int,
    description: str,
    up_sql: str,
    down_sql: Optional[str] = None
) -> Migration:
    """Helper function to create a migration from SQL strings.
    
    Args:
        version: Migration version number
        description: Migration description
        up_sql: SQL to apply the migration
        down_sql: Optional SQL to rollback the migration
        
    Returns:
        Migration instance
    """
    def up(conn: sqlite3.Connection) -> None:
        conn.executescript(up_sql)
    
    down_func = None
    if down_sql:
        def down(conn: sqlite3.Connection) -> None:
            conn.executescript(down_sql)
        down_func = down
    
    return Migration(
        version=version,
        description=description,
        up=up,
        down=down_func
    )


# Example migration definitions
# These can be moved to separate files as the project grows

def migration_003_add_video_tags() -> Migration:
    """Example migration: Add tags support to videos."""
    up_sql = """
    -- Add tags column to videos table
    ALTER TABLE videos ADD COLUMN tags TEXT;
    
    -- Create tags index
    CREATE INDEX IF NOT EXISTS idx_videos_tags ON videos(tags);
    """
    
    down_sql = """
    -- Remove tags column (SQLite doesn't support DROP COLUMN directly)
    -- Would need to recreate table without tags column
    """
    
    return create_migration(
        version=3,
        description="Add tags support to videos",
        up_sql=up_sql,
        down_sql=None  # Rollback not supported for this migration
    )


def get_migration_manager(db: Optional[Database] = None) -> MigrationManager:
    """Get migration manager instance.
    
    Args:
        db: Optional database instance (uses global instance if not provided)
        
    Returns:
        MigrationManager instance
    """
    if db is None:
        from storage.database import get_database
        db = get_database()
    
    return MigrationManager(db)
