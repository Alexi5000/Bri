"""Database health monitoring for BRI video agent.

This module provides functionality for:
- Monitoring database size and growth rate
- Tracking query performance (slow query log)
- Monitoring connection pool usage
- Logging database errors/failures
- Database backup strategy
"""

import logging
import json
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
from storage.database import Database, get_database

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """Monitor query performance and log slow queries."""
    
    def __init__(self, slow_query_threshold_ms: float = 100.0):
        """Initialize query performance monitor.
        
        Args:
            slow_query_threshold_ms: Threshold in milliseconds for slow queries
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_stats: Dict[str, Dict[str, Any]] = {}
    
    @contextmanager
    def monitor_query(self, query: str, parameters: Optional[tuple] = None):
        """Context manager to monitor query execution time.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            
        Yields:
            None
            
        Example:
            with monitor.monitor_query("SELECT * FROM videos"):
                cursor.execute(query)
        """
        start_time = time.time()
        query_key = query.strip()[:100]  # Use first 100 chars as key
        
        try:
            yield
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            if query_key not in self.query_stats:
                self.query_stats[query_key] = {
                    'count': 0,
                    'total_time_ms': 0,
                    'min_time_ms': float('inf'),
                    'max_time_ms': 0,
                    'slow_count': 0
                }
            
            stats = self.query_stats[query_key]
            stats['count'] += 1
            stats['total_time_ms'] += execution_time_ms
            stats['min_time_ms'] = min(stats['min_time_ms'], execution_time_ms)
            stats['max_time_ms'] = max(stats['max_time_ms'], execution_time_ms)
            
            # Log slow queries
            if execution_time_ms > self.slow_query_threshold_ms:
                stats['slow_count'] += 1
                logger.warning(
                    f"Slow query detected ({execution_time_ms:.2f}ms): {query_key}"
                )
    
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get query performance statistics.
        
        Returns:
            Dictionary of query statistics
        """
        # Calculate average times
        for query_key, stats in self.query_stats.items():
            if stats['count'] > 0:
                stats['avg_time_ms'] = stats['total_time_ms'] / stats['count']
        
        return self.query_stats
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get list of slow queries.
        
        Returns:
            List of slow query statistics
        """
        slow_queries = []
        for query_key, stats in self.query_stats.items():
            if stats['slow_count'] > 0:
                slow_queries.append({
                    'query': query_key,
                    'slow_count': stats['slow_count'],
                    'total_count': stats['count'],
                    'max_time_ms': stats['max_time_ms'],
                    'avg_time_ms': stats.get('avg_time_ms', 0)
                })
        
        # Sort by slow count descending
        slow_queries.sort(key=lambda x: x['slow_count'], reverse=True)
        return slow_queries
    
    def reset_statistics(self) -> None:
        """Reset query statistics."""
        self.query_stats.clear()
        logger.info("Query statistics reset")


class DatabaseHealthMonitor:
    """Monitor database health and performance."""
    
    def __init__(self, db: Optional[Database] = None):
        """Initialize database health monitor.
        
        Args:
            db: Optional database instance
        """
        self.db = db or get_database()
        self.query_monitor = QueryPerformanceMonitor()
        self.health_log_path = Path("logs/database_health.log")
        self.health_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_database_size(self) -> Dict[str, Any]:
        """Get database size information.
        
        Returns:
            Dictionary with size information
        """
        try:
            db_path = Path(self.db.db_path)
            
            if not db_path.exists():
                return {'size_bytes': 0, 'size_mb': 0}
            
            size_bytes = db_path.stat().st_size
            size_mb = size_bytes / 1024 / 1024
            
            return {
                'size_bytes': size_bytes,
                'size_mb': round(size_mb, 2),
                'path': str(db_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return {'size_bytes': 0, 'size_mb': 0}
    
    def get_growth_rate(self, days: int = 7) -> Dict[str, Any]:
        """Calculate database growth rate.
        
        Args:
            days: Number of days to calculate growth over
            
        Returns:
            Dictionary with growth rate information
        """
        try:
            current_size = self.get_database_size()
            
            # Get record counts
            video_count = self.db.execute_query("SELECT COUNT(*) as count FROM videos")[0]['count']
            memory_count = self.db.execute_query("SELECT COUNT(*) as count FROM memory")[0]['count']
            context_count = self.db.execute_query("SELECT COUNT(*) as count FROM video_context")[0]['count']
            
            # Get recent uploads (last N days)
            recent_videos = self.db.execute_query(
                f"SELECT COUNT(*) as count FROM videos WHERE upload_timestamp >= datetime('now', '-{days} days')"
            )[0]['count']
            
            # Estimate growth rate
            if video_count > 0:
                growth_rate_mb_per_day = (current_size['size_mb'] / video_count) * (recent_videos / days)
            else:
                growth_rate_mb_per_day = 0
            
            return {
                'current_size_mb': current_size['size_mb'],
                'total_videos': video_count,
                'total_memory': memory_count,
                'total_context': context_count,
                'recent_videos': recent_videos,
                'days_analyzed': days,
                'growth_rate_mb_per_day': round(growth_rate_mb_per_day, 2),
                'estimated_size_30_days_mb': round(current_size['size_mb'] + (growth_rate_mb_per_day * 30), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate growth rate: {e}")
            return {}
    
    def check_connection_pool(self) -> Dict[str, Any]:
        """Check database connection pool status.
        
        Returns:
            Dictionary with connection pool information
        """
        try:
            conn = self.db.get_connection()
            
            # Get SQLite connection info
            info = {
                'connected': conn is not None,
                'database_path': self.db.db_path,
                'foreign_keys_enabled': False,
                'journal_mode': 'unknown',
                'cache_size': 0
            }
            
            if conn:
                # Check foreign keys
                fk_result = conn.execute("PRAGMA foreign_keys").fetchone()
                info['foreign_keys_enabled'] = fk_result[0] == 1 if fk_result else False
                
                # Check journal mode
                journal_result = conn.execute("PRAGMA journal_mode").fetchone()
                info['journal_mode'] = journal_result[0] if journal_result else 'unknown'
                
                # Check cache size
                cache_result = conn.execute("PRAGMA cache_size").fetchone()
                info['cache_size'] = cache_result[0] if cache_result else 0
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to check connection pool: {e}")
            return {'connected': False, 'error': str(e)}
    
    def check_table_integrity(self) -> Dict[str, Any]:
        """Check database table integrity.
        
        Returns:
            Dictionary with integrity check results
        """
        try:
            conn = self.db.get_connection()
            
            # Run integrity check
            integrity_result = conn.execute("PRAGMA integrity_check").fetchone()
            is_ok = integrity_result[0] == 'ok' if integrity_result else False
            
            # Get table information
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            
            table_info = {}
            for table in tables:
                table_name = table[0]
                count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                table_info[table_name] = count_result[0] if count_result else 0
            
            return {
                'integrity_ok': is_ok,
                'integrity_message': integrity_result[0] if integrity_result else 'unknown',
                'tables': table_info
            }
            
        except Exception as e:
            logger.error(f"Failed to check table integrity: {e}")
            return {'integrity_ok': False, 'error': str(e)}
    
    def check_index_usage(self) -> List[Dict[str, Any]]:
        """Check index usage statistics.
        
        Returns:
            List of index information
        """
        try:
            conn = self.db.get_connection()
            
            # Get all indexes
            indexes = conn.execute("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' AND sql IS NOT NULL
                ORDER BY tbl_name, name
            """).fetchall()
            
            index_info = []
            for idx in indexes:
                index_info.append({
                    'name': idx[0],
                    'table': idx[1],
                    'sql': idx[2]
                })
            
            return index_info
            
        except Exception as e:
            logger.error(f"Failed to check index usage: {e}")
            return []
    
    def log_health_metrics(self) -> None:
        """Log current health metrics to file."""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'database_size': self.get_database_size(),
                'growth_rate': self.get_growth_rate(),
                'connection_pool': self.check_connection_pool(),
                'integrity': self.check_table_integrity(),
                'query_stats': self.query_monitor.get_statistics()
            }
            
            # Append to health log
            with open(self.health_log_path, 'a') as f:
                f.write(json.dumps(metrics) + '\n')
            
            logger.info("Health metrics logged")
            
        except Exception as e:
            logger.error(f"Failed to log health metrics: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report.
        
        Returns:
            Dictionary with health report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_size': self.get_database_size(),
            'growth_rate': self.get_growth_rate(),
            'connection_pool': self.check_connection_pool(),
            'integrity': self.check_table_integrity(),
            'indexes': self.check_index_usage(),
            'constraints': self.db.check_constraints(),
            'slow_queries': self.query_monitor.get_slow_queries()
        }
        
        # Calculate health score (0-100)
        score = 100
        
        if not report['integrity']['integrity_ok']:
            score -= 50
        
        if not report['connection_pool']['foreign_keys_enabled']:
            score -= 10
        
        if report['constraints']['orphaned_memory'] > 0:
            score -= 5
        
        if report['constraints']['orphaned_context'] > 0:
            score -= 5
        
        if len(report['slow_queries']) > 10:
            score -= 10
        
        report['health_score'] = max(0, score)
        report['health_status'] = 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical'
        
        return report
    
    def create_backup(self, backup_dir: Optional[str] = None) -> Optional[str]:
        """Create database backup.
        
        Args:
            backup_dir: Optional backup directory (default: data/backups)
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            if backup_dir is None:
                backup_dir = Path("data/backups")
            else:
                backup_dir = Path(backup_dir)
            
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"bri_backup_{timestamp}.db"
            backup_path = backup_dir / backup_filename
            
            # Copy database file
            shutil.copy2(self.db.db_path, backup_path)
            
            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def cleanup_old_backups(self, backup_dir: Optional[str] = None, keep_days: int = 30) -> int:
        """Clean up old backup files.
        
        Args:
            backup_dir: Optional backup directory
            keep_days: Number of days to keep backups
            
        Returns:
            Number of backups deleted
        """
        try:
            if backup_dir is None:
                backup_dir = Path("data/backups")
            else:
                backup_dir = Path(backup_dir)
            
            if not backup_dir.exists():
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_count = 0
            
            for backup_file in backup_dir.glob("bri_backup_*.db"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return 0


def get_health_monitor(db: Optional[Database] = None) -> DatabaseHealthMonitor:
    """Get database health monitor instance.
    
    Args:
        db: Optional database instance
        
    Returns:
        DatabaseHealthMonitor instance
    """
    return DatabaseHealthMonitor(db)
