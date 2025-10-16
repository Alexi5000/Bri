"""Database query optimization utilities for BRI video agent.

Features:
- Query result caching with TTL
- Connection pooling
- Prepared statements
- Query batching
- Performance monitoring
"""

import time
import sqlite3
import hashlib
import json
from typing import Any, Optional, List, Tuple, Dict
from contextlib import contextmanager
from threading import Lock
from queue import Queue, Empty

from config import Config
from utils.logging_config import get_logger, get_performance_logger
from storage.multi_tier_cache import get_multi_tier_cache

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)


class ConnectionPool:
    """Thread-safe connection pool for SQLite database.
    
    Maintains a pool of reusable database connections to avoid
    the overhead of creating new connections for each query.
    """
    
    def __init__(self, db_path: str, pool_size: int = 5):
        """Initialize connection pool.
        
        Args:
            db_path: Path to SQLite database
            pool_size: Maximum number of connections in pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool: Queue = Queue(maxsize=pool_size)
        self.lock = Lock()
        self.active_connections = 0
        
        # Pre-create connections
        for _ in range(pool_size):
            conn = self._create_connection()
            self.pool.put(conn)
        
        logger.info(f"Connection pool initialized with {pool_size} connections")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety and performance
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp tables
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool.
        
        Yields:
            SQLite connection object
        """
        conn = None
        try:
            # Try to get connection from pool (with timeout)
            try:
                conn = self.pool.get(timeout=5.0)
            except Empty:
                # Pool exhausted, create temporary connection
                logger.warning("Connection pool exhausted, creating temporary connection")
                conn = self._create_connection()
            
            with self.lock:
                self.active_connections += 1
            
            yield conn
            
        finally:
            with self.lock:
                self.active_connections -= 1
            
            # Return connection to pool
            if conn is not None:
                try:
                    self.pool.put_nowait(conn)
                except Exception:
                    # Pool is full, close the connection
                    conn.close()
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break
        
        logger.info("All connections in pool closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics.
        
        Returns:
            Dictionary with pool stats
        """
        return {
            "pool_size": self.pool_size,
            "available": self.pool.qsize(),
            "active": self.active_connections,
            "utilization": f"{(self.active_connections / self.pool_size) * 100:.1f}%"
        }


class PreparedStatementCache:
    """Cache for prepared SQL statements.
    
    Prepared statements are pre-compiled SQL queries that can be
    executed multiple times with different parameters, improving performance.
    """
    
    def __init__(self, max_size: int = 50):
        """Initialize prepared statement cache.
        
        Args:
            max_size: Maximum number of prepared statements to cache
        """
        self.cache: Dict[str, str] = {}
        self.max_size = max_size
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
        
        logger.info(f"Prepared statement cache initialized (max size: {max_size})")
    
    def get_or_create(self, query: str) -> str:
        """Get prepared statement or create if not cached.
        
        Args:
            query: SQL query string
            
        Returns:
            Query string (prepared statements are implicit in SQLite)
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        with self.lock:
            if query_hash in self.cache:
                self.hits += 1
                return self.cache[query_hash]
            else:
                self.misses += 1
                
                # Add to cache
                if len(self.cache) >= self.max_size:
                    # Remove oldest entry (FIFO)
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                
                self.cache[query_hash] = query
                return query
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prepared statement cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%"
            }


class QueryOptimizer:
    """Database query optimizer with caching, pooling, and batching.
    
    Features:
    - Query result caching (integrated with multi-tier cache)
    - Connection pooling for reuse
    - Prepared statement caching
    - Query batching for bulk operations
    - Performance monitoring
    """
    
    def __init__(self, db_path: str, pool_size: int = 5):
        """Initialize query optimizer.
        
        Args:
            db_path: Path to SQLite database
            pool_size: Connection pool size
        """
        self.db_path = db_path
        self.connection_pool = ConnectionPool(db_path, pool_size)
        self.prepared_statements = PreparedStatementCache()
        self.cache = get_multi_tier_cache()
        
        # Query performance tracking
        self.query_times: Dict[str, List[float]] = {}
        self.query_lock = Lock()
        
        logger.info("Query optimizer initialized")
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Tuple] = None,
        cache_key: Optional[str] = None,
        cache_ttl: int = 300
    ) -> List[sqlite3.Row]:
        """Execute a SELECT query with caching and optimization.
        
        Args:
            query: SQL query string
            parameters: Query parameters tuple
            cache_key: Optional cache key (auto-generated if None)
            cache_ttl: Cache TTL in seconds
            
        Returns:
            List of result rows
        """
        start_time = time.time()
        
        # Generate cache key if not provided
        if cache_key is None:
            cache_key = self._generate_cache_key(query, parameters)
        
        # Check cache first
        cached_result = self.cache.get(cache_key, namespace="query")
        if cached_result is not None:
            elapsed = time.time() - start_time
            logger.debug(f"Query cache hit: {cache_key} ({elapsed*1000:.1f}ms)")
            perf_logger.log_cache_hit(f"query:{cache_key}", hit=True)
            return cached_result
        
        # Execute query
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use prepared statement
                prepared_query = self.prepared_statements.get_or_create(query)
                
                if parameters:
                    cursor.execute(prepared_query, parameters)
                else:
                    cursor.execute(prepared_query)
                
                results = cursor.fetchall()
                
                # Convert to list of dicts for caching
                results_list = [dict(row) for row in results]
                
                # Cache results
                self.cache.set(cache_key, results_list, namespace="query", ttl=cache_ttl)
                
                elapsed = time.time() - start_time
                self._track_query_time(query, elapsed)
                
                logger.debug(
                    f"Query executed: {len(results)} rows in {elapsed*1000:.1f}ms "
                    f"(cached for {cache_ttl}s)"
                )
                perf_logger.log_execution_time(
                    "database_query",
                    elapsed,
                    success=True,
                    query_hash=hashlib.md5(query.encode()).hexdigest()[:8],
                    row_count=len(results)
                )
                
                return results_list
                
        except sqlite3.Error as e:
            elapsed = time.time() - start_time
            logger.error(f"Query execution failed: {e}")
            perf_logger.log_execution_time(
                "database_query",
                elapsed,
                success=False,
                error=str(e)
            )
            raise
    
    def execute_update(
        self,
        query: str,
        parameters: Optional[Tuple] = None,
        invalidate_pattern: Optional[str] = None
    ) -> int:
        """Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            parameters: Query parameters tuple
            invalidate_pattern: Cache pattern to invalidate after update
            
        Returns:
            Number of affected rows
        """
        start_time = time.time()
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use prepared statement
                prepared_query = self.prepared_statements.get_or_create(query)
                
                if parameters:
                    cursor.execute(prepared_query, parameters)
                else:
                    cursor.execute(prepared_query)
                
                conn.commit()
                rowcount = cursor.rowcount
                
                # Invalidate cache if pattern provided
                if invalidate_pattern:
                    self.cache.invalidate_pattern(invalidate_pattern, namespace="query")
                    logger.debug(f"Invalidated cache pattern: {invalidate_pattern}")
                
                elapsed = time.time() - start_time
                self._track_query_time(query, elapsed)
                
                logger.debug(
                    f"Update executed: {rowcount} rows affected in {elapsed*1000:.1f}ms"
                )
                perf_logger.log_execution_time(
                    "database_update",
                    elapsed,
                    success=True,
                    row_count=rowcount
                )
                
                return rowcount
                
        except sqlite3.Error as e:
            elapsed = time.time() - start_time
            logger.error(f"Update execution failed: {e}")
            perf_logger.log_execution_time(
                "database_update",
                elapsed,
                success=False,
                error=str(e)
            )
            raise
    
    def execute_batch(
        self,
        query: str,
        parameters_list: List[Tuple],
        batch_size: int = 100,
        invalidate_pattern: Optional[str] = None
    ) -> int:
        """Execute a query multiple times with batching for performance.
        
        Args:
            query: SQL query string
            parameters_list: List of parameter tuples
            batch_size: Number of operations per batch
            invalidate_pattern: Cache pattern to invalidate after batch
            
        Returns:
            Total number of affected rows
        """
        start_time = time.time()
        total_affected = 0
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Use prepared statement
                prepared_query = self.prepared_statements.get_or_create(query)
                
                # Process in batches
                for i in range(0, len(parameters_list), batch_size):
                    batch = parameters_list[i:i + batch_size]
                    cursor.executemany(prepared_query, batch)
                    total_affected += cursor.rowcount
                    
                    logger.debug(
                        f"Batch {i//batch_size + 1}: {len(batch)} operations, "
                        f"{cursor.rowcount} rows affected"
                    )
                
                conn.commit()
                
                # Invalidate cache if pattern provided
                if invalidate_pattern:
                    self.cache.invalidate_pattern(invalidate_pattern, namespace="query")
                
                elapsed = time.time() - start_time
                self._track_query_time(query, elapsed)
                
                logger.info(
                    f"Batch execution complete: {len(parameters_list)} operations, "
                    f"{total_affected} rows affected in {elapsed:.2f}s"
                )
                perf_logger.log_execution_time(
                    "database_batch",
                    elapsed,
                    success=True,
                    operation_count=len(parameters_list),
                    row_count=total_affected
                )
                
                return total_affected
                
        except sqlite3.Error as e:
            elapsed = time.time() - start_time
            logger.error(f"Batch execution failed: {e}")
            perf_logger.log_execution_time(
                "database_batch",
                elapsed,
                success=False,
                error=str(e)
            )
            raise
    
    def _generate_cache_key(self, query: str, parameters: Optional[Tuple]) -> str:
        """Generate cache key for query and parameters.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            
        Returns:
            Cache key string
        """
        # Hash query and parameters
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        if parameters:
            params_str = json.dumps(parameters, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()
            return f"{query_hash}:{params_hash}"
        else:
            return query_hash
    
    def _track_query_time(self, query: str, elapsed: float) -> None:
        """Track query execution time for performance monitoring.
        
        Args:
            query: SQL query string
            elapsed: Execution time in seconds
        """
        # Extract query type (SELECT, INSERT, UPDATE, DELETE)
        query_type = query.strip().split()[0].upper()
        
        with self.query_lock:
            if query_type not in self.query_times:
                self.query_times[query_type] = []
            
            self.query_times[query_type].append(elapsed)
            
            # Keep only last 100 measurements per query type
            if len(self.query_times[query_type]) > 100:
                self.query_times[query_type] = self.query_times[query_type][-100:]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query performance statistics.
        
        Returns:
            Dictionary with query performance stats
        """
        with self.query_lock:
            stats = {}
            
            for query_type, times in self.query_times.items():
                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)
                    
                    stats[query_type] = {
                        "count": len(times),
                        "avg_ms": f"{avg_time * 1000:.2f}",
                        "min_ms": f"{min_time * 1000:.2f}",
                        "max_ms": f"{max_time * 1000:.2f}"
                    }
            
            return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimizer statistics.
        
        Returns:
            Dictionary with all optimizer stats
        """
        return {
            "connection_pool": self.connection_pool.get_stats(),
            "prepared_statements": self.prepared_statements.get_stats(),
            "query_performance": self.get_query_stats(),
            "cache": self.cache.get_stats()
        }
    
    def close(self) -> None:
        """Close all connections and cleanup resources."""
        self.connection_pool.close_all()
        logger.info("Query optimizer closed")


# Global query optimizer instance
_query_optimizer: Optional[QueryOptimizer] = None


def get_query_optimizer() -> QueryOptimizer:
    """Get or create global query optimizer instance.
    
    Returns:
        QueryOptimizer instance
    """
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer(
            db_path=Config.DATABASE_PATH,
            pool_size=5
        )
    return _query_optimizer
