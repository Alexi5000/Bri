"""Database connection and utilities for BRI video agent."""

import sqlite3
import logging
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass


class ValidationError(Exception):
    """Custom exception for data validation errors."""
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
    
    @contextmanager
    def transaction(self, isolation_level: Optional[str] = None):
        """Context manager for explicit transaction control with savepoint support.
        
        Args:
            isolation_level: Optional isolation level ('DEFERRED', 'IMMEDIATE', 'EXCLUSIVE')
            
        Yields:
            Transaction object with savepoint support
            
        Example:
            with db.transaction() as txn:
                cursor = txn.cursor()
                cursor.execute("INSERT INTO videos ...")
                savepoint = txn.savepoint()
                try:
                    cursor.execute("INSERT INTO video_context ...")
                except:
                    txn.rollback_to(savepoint)
        """
        conn = self.get_connection()
        
        # Begin transaction with specified isolation level
        if isolation_level:
            conn.execute(f"BEGIN {isolation_level}")
        else:
            conn.execute("BEGIN")
        
        txn = Transaction(conn)
        
        try:
            yield txn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise DatabaseError(f"Transaction failed: {e}")
    
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
            
            # Create performance indexes
            self._create_performance_indexes()
        except FileNotFoundError:
            logger.error(f"Schema file not found: {schema_path}")
            raise DatabaseError(f"Schema file not found: {schema_path}")
        except sqlite3.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            raise DatabaseError(f"Schema initialization failed: {e}")
    
    def _create_performance_indexes(self) -> None:
        """Create indexes for performance optimization."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Index for memory table queries (video_id + timestamp for conversation history)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_video_timestamp 
                ON memory(video_id, timestamp DESC)
            """)
            
            # Index for video_context queries (video_id + context_type + timestamp)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_context_lookup 
                ON video_context(video_id, context_type, timestamp)
            """)
            
            # Index for video_context timestamp queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_context_timestamp 
                ON video_context(video_id, timestamp)
            """)
            
            # Index for videos processing status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_status 
                ON videos(processing_status)
            """)
            
            conn.commit()
            logger.info("Performance indexes created successfully")
            
        except sqlite3.Error as e:
            logger.warning(f"Failed to create performance indexes: {e}")
    
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
    
    @staticmethod
    def validate_json(data: str, schema_type: Optional[str] = None) -> bool:
        """Validate JSON data structure.
        
        Args:
            data: JSON string to validate
            schema_type: Optional schema type for specific validation
            
        Returns:
            True if valid JSON
            
        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            parsed = json.loads(data)
            
            # Type-specific validation
            if schema_type == 'caption':
                if not isinstance(parsed, dict):
                    raise ValidationError("Caption data must be a dictionary")
                if 'text' not in parsed:
                    raise ValidationError("Caption data must contain 'text' field")
                if 'confidence' in parsed:
                    confidence = parsed['confidence']
                    if not (0 <= confidence <= 1):
                        raise ValidationError("Confidence must be between 0 and 1")
                        
            elif schema_type == 'transcript':
                if not isinstance(parsed, dict):
                    raise ValidationError("Transcript data must be a dictionary")
                if 'text' not in parsed:
                    raise ValidationError("Transcript data must contain 'text' field")
                    
            elif schema_type == 'object':
                if not isinstance(parsed, dict):
                    raise ValidationError("Object detection data must be a dictionary")
                if 'objects' in parsed:
                    if not isinstance(parsed['objects'], list):
                        raise ValidationError("Objects field must be a list")
                    for obj in parsed['objects']:
                        if 'confidence' in obj:
                            confidence = obj['confidence']
                            if not (0 <= confidence <= 1):
                                raise ValidationError("Object confidence must be between 0 and 1")
            
            return True
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")
    
    def validate_video_data(
        self,
        video_id: str,
        filename: str,
        file_path: str,
        duration: float
    ) -> None:
        """Validate video data before insertion.
        
        Args:
            video_id: Video identifier
            filename: Video filename
            file_path: Path to video file
            duration: Video duration in seconds
            
        Raises:
            ValidationError: If validation fails
        """
        if not video_id or not isinstance(video_id, str):
            raise ValidationError("video_id must be a non-empty string")
        if not filename or not isinstance(filename, str):
            raise ValidationError("filename must be a non-empty string")
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("file_path must be a non-empty string")
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValidationError("duration must be a positive number")
    
    def validate_context_data(
        self,
        context_id: str,
        video_id: str,
        context_type: str,
        data: str,
        timestamp: Optional[float] = None
    ) -> None:
        """Validate video context data before insertion.
        
        Args:
            context_id: Context identifier
            video_id: Video identifier
            context_type: Type of context data
            data: JSON data string
            timestamp: Optional timestamp
            
        Raises:
            ValidationError: If validation fails
        """
        if not context_id or not isinstance(context_id, str):
            raise ValidationError("context_id must be a non-empty string")
        if not video_id or not isinstance(video_id, str):
            raise ValidationError("video_id must be a non-empty string")
        if context_type not in ['frame', 'caption', 'transcript', 'object', 'metadata', 'idempotency']:
            raise ValidationError(f"Invalid context_type: {context_type}")
        if not data or not isinstance(data, str):
            raise ValidationError("data must be a non-empty string")
        if timestamp is not None and (not isinstance(timestamp, (int, float)) or timestamp < 0):
            raise ValidationError("timestamp must be a non-negative number")
        
        # Validate JSON structure
        self.validate_json(data, context_type)
    
    def get_schema_version(self) -> Optional[int]:
        """Get current database schema version.
        
        Returns:
            Current schema version or None if not found
        """
        try:
            query = "SELECT MAX(version) as version FROM schema_version"
            results = self.execute_query(query)
            if results and results[0]['version']:
                return results[0]['version']
            return None
        except sqlite3.Error:
            return None
    
    def check_constraints(self) -> Dict[str, Any]:
        """Check database constraints and integrity.
        
        Returns:
            Dictionary with constraint check results
        """
        results = {
            'foreign_keys_enabled': False,
            'orphaned_memory': 0,
            'orphaned_context': 0,
            'invalid_durations': 0,
            'invalid_timestamps': 0
        }
        
        try:
            # Check if foreign keys are enabled
            fk_check = self.execute_query("PRAGMA foreign_keys")
            results['foreign_keys_enabled'] = fk_check[0][0] == 1 if fk_check else False
            
            # Check for orphaned memory records
            orphaned_memory = self.execute_query("""
                SELECT COUNT(*) as count FROM memory 
                WHERE video_id NOT IN (SELECT video_id FROM videos)
            """)
            results['orphaned_memory'] = orphaned_memory[0]['count'] if orphaned_memory else 0
            
            # Check for orphaned context records
            orphaned_context = self.execute_query("""
                SELECT COUNT(*) as count FROM video_context 
                WHERE video_id NOT IN (SELECT video_id FROM videos)
            """)
            results['orphaned_context'] = orphaned_context[0]['count'] if orphaned_context else 0
            
            # Check for invalid durations
            invalid_durations = self.execute_query("""
                SELECT COUNT(*) as count FROM videos WHERE duration <= 0
            """)
            results['invalid_durations'] = invalid_durations[0]['count'] if invalid_durations else 0
            
            # Check for invalid timestamps
            invalid_timestamps = self.execute_query("""
                SELECT COUNT(*) as count FROM video_context WHERE timestamp < 0
            """)
            results['invalid_timestamps'] = invalid_timestamps[0]['count'] if invalid_timestamps else 0
            
        except sqlite3.Error as e:
            logger.error(f"Constraint check failed: {e}")
        
        return results


class Transaction:
    """Transaction object with savepoint support for partial rollback."""
    
    def __init__(self, connection: sqlite3.Connection):
        """Initialize transaction with database connection.
        
        Args:
            connection: SQLite connection object
        """
        self.connection = connection
        self._savepoint_counter = 0
        self._savepoints: List[str] = []
    
    def cursor(self) -> sqlite3.Cursor:
        """Get a cursor for this transaction.
        
        Returns:
            SQLite cursor object
        """
        return self.connection.cursor()
    
    def savepoint(self) -> str:
        """Create a savepoint for partial rollback.
        
        Returns:
            Savepoint name
            
        Example:
            sp = txn.savepoint()
            try:
                # risky operation
            except:
                txn.rollback_to(sp)
        """
        self._savepoint_counter += 1
        savepoint_name = f"sp_{self._savepoint_counter}"
        self.connection.execute(f"SAVEPOINT {savepoint_name}")
        self._savepoints.append(savepoint_name)
        logger.debug(f"Created savepoint: {savepoint_name}")
        return savepoint_name
    
    def rollback_to(self, savepoint_name: str) -> None:
        """Rollback to a specific savepoint.
        
        Args:
            savepoint_name: Name of savepoint to rollback to
            
        Raises:
            DatabaseError: If savepoint doesn't exist
        """
        if savepoint_name not in self._savepoints:
            raise DatabaseError(f"Savepoint {savepoint_name} does not exist")
        
        self.connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
        logger.debug(f"Rolled back to savepoint: {savepoint_name}")
    
    def release_savepoint(self, savepoint_name: str) -> None:
        """Release a savepoint (commit changes up to that point).
        
        Args:
            savepoint_name: Name of savepoint to release
            
        Raises:
            DatabaseError: If savepoint doesn't exist
        """
        if savepoint_name not in self._savepoints:
            raise DatabaseError(f"Savepoint {savepoint_name} does not exist")
        
        self.connection.execute(f"RELEASE SAVEPOINT {savepoint_name}")
        self._savepoints.remove(savepoint_name)
        logger.debug(f"Released savepoint: {savepoint_name}")
    
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
            
            # Create performance indexes
            self._create_performance_indexes()
        except FileNotFoundError:
            logger.error(f"Schema file not found: {schema_path}")
            raise DatabaseError(f"Schema file not found: {schema_path}")
        except sqlite3.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            raise DatabaseError(f"Schema initialization failed: {e}")
    
    def _create_performance_indexes(self) -> None:
        """Create indexes for performance optimization."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Index for memory table queries (video_id + timestamp for conversation history)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_video_timestamp 
                ON memory(video_id, timestamp DESC)
            """)
            
            # Index for video_context queries (video_id + context_type + timestamp)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_context_lookup 
                ON video_context(video_id, context_type, timestamp)
            """)
            
            # Index for video_context timestamp queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_context_timestamp 
                ON video_context(video_id, timestamp)
            """)
            
            # Index for videos processing status
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_status 
                ON videos(processing_status)
            """)
            
            conn.commit()
            logger.info("Performance indexes created successfully")
            
        except sqlite3.Error as e:
            logger.warning(f"Failed to create performance indexes: {e}")
    
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


# Video-specific database operations

def insert_video(
    video_id: str,
    filename: str,
    file_path: str,
    duration: float,
    thumbnail_path: Optional[str] = None
) -> None:
    """
    Insert a new video record into the database.
    
    Args:
        video_id: Unique video identifier
        filename: Original filename
        file_path: Path to video file
        duration: Video duration in seconds
        thumbnail_path: Optional path to thumbnail
        
    Raises:
        DatabaseError: If insert fails
        ValidationError: If data validation fails
    """
    db = get_database()
    
    # Validate data before insertion
    db.validate_video_data(video_id, filename, file_path, duration)
    
    query = """
        INSERT INTO videos (video_id, filename, file_path, duration, thumbnail_path, processing_status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    """
    db.execute_update(query, (video_id, filename, file_path, duration, thumbnail_path))
    logger.info(f"Inserted video record: {video_id}")


def get_video(video_id: str) -> Optional[sqlite3.Row]:
    """
    Retrieve a video record by ID.
    
    Args:
        video_id: Video identifier
        
    Returns:
        Video record or None if not found
    """
    db = get_database()
    query = "SELECT * FROM videos WHERE video_id = ?"
    results = db.execute_query(query, (video_id,))
    return results[0] if results else None


def get_all_videos() -> List[sqlite3.Row]:
    """
    Retrieve all video records.
    
    Returns:
        List of video records
    """
    db = get_database()
    query = "SELECT * FROM videos ORDER BY upload_timestamp DESC"
    return db.execute_query(query)


def update_video_status(video_id: str, status: str) -> None:
    """
    Update video processing status.
    
    Args:
        video_id: Video identifier
        status: New status ('pending', 'processing', 'complete', 'error')
        
    Raises:
        DatabaseError: If update fails
    """
    db = get_database()
    query = "UPDATE videos SET processing_status = ? WHERE video_id = ?"
    db.execute_update(query, (status, video_id))
    logger.info(f"Updated video {video_id} status to: {status}")


def delete_video(video_id: str) -> None:
    """
    Delete a video record from the database.
    
    Args:
        video_id: Video identifier
        
    Raises:
        DatabaseError: If delete fails
    """
    db = get_database()
    query = "DELETE FROM videos WHERE video_id = ?"
    db.execute_update(query, (video_id,))
    logger.info(f"Deleted video record: {video_id}")
