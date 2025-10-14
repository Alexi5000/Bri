"""Database connection and utilities for BRI video agent."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass


class Database:
    """SQLite database connection manager with error handling."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. Uses Config.DATABASE_PATH if not provided.
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_database_directory()
        self._connection: Optional[sqlite3.Connection] = None
        
    def _ensure_database_directory(self) -> None:
        """Create database directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
    def connect(self) -> sqlite3.Connection:
        """Establish database connection with proper configuration.
        
        Returns:
            SQLite connection object
            
        Raises:
            DatabaseError: If connection fails
        """
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            self._connection = conn
            logger.info(f"Connected to database: {self.db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get existing connection or create new one.
        
        Returns:
            SQLite connection object
        """
        if self._connection is None:
            return self.connect()
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with automatic commit/rollback.
        
        Yields:
            SQLite cursor object
            
        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM videos")
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            cursor.close()
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Tuple] = None
    ) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            parameters: Query parameters tuple
            
        Returns:
            List of result rows
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.get_cursor() as cursor:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {query} - {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    def execute_update(
        self,
        query: str,
        parameters: Optional[Tuple] = None
    ) -> int:
        """Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            parameters: Query parameters tuple
            
        Returns:
            Number of affected rows
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.get_cursor() as cursor:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Update execution failed: {query} - {e}")
            raise DatabaseError(f"Update execution failed: {e}")
    
    def execute_many(
        self,
        query: str,
        parameters_list: List[Tuple]
    ) -> int:
        """Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            parameters_list: List of parameter tuples
            
        Returns:
            Number of affected rows
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(query, parameters_list)
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Batch execution failed: {query} - {e}")
            raise DatabaseError(f"Batch execution failed: {e}")
    
    def initialize_schema(self, schema_path: Optional[str] = None) -> None:
        """Initialize database schema from SQL file.
        
        Args:
            schema_path: Path to schema SQL file. Uses default if not provided.
            
        Raises:
            DatabaseError: If schema initialization fails
        """
        if schema_path is None:
            schema_path = Path(__file__).parent / "schema.sql"
        
        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            conn = self.get_connection()
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("Database schema initialized successfully")
        except FileNotFoundError:
            logger.error(f"Schema file not found: {schema_path}")
            raise DatabaseError(f"Schema file not found: {schema_path}")
        except sqlite3.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            raise DatabaseError(f"Schema initialization failed: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database instance
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """Get or create global database instance.
    
    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.connect()
    return _db_instance


def initialize_database(schema_path: Optional[str] = None) -> None:
    """Initialize database with schema.
    
    Args:
        schema_path: Optional path to schema SQL file
    """
    db = get_database()
    db.initialize_schema(schema_path)
