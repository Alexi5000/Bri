"""Database backup and restore functionality for BRI.

Provides automated backup, point-in-time recovery, and backup verification.
"""

import os
import shutil
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import hashlib

from config import Config

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Manages database backups and restores."""
    
    def __init__(
        self,
        db_path: str = None,
        backup_dir: str = None,
        retention_days: int = 30
    ):
        """Initialize backup manager.
        
        Args:
            db_path: Path to database file
            backup_dir: Directory for backup files
            retention_days: Number of days to retain backups
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self.backup_dir = backup_dir or os.path.join(
            Path(Config.DATABASE_PATH).parent,
            'backups'
        )
        self.retention_days = retention_days
        
        # Create backup directory
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Backup manager initialized: db={self.db_path}, backup_dir={self.backup_dir}")
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of the database.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Path to backup file
            
        Raises:
            FileNotFoundError: If database file doesn't exist
            IOError: If backup creation fails
        """
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        
        # Generate backup filename
        if backup_name:
            backup_filename = f"{backup_name}.db"
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"bri_backup_{timestamp}.db"
        
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Use SQLite backup API for consistent backup
            logger.info(f"Creating backup: {backup_path}")
            
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Create metadata file
            metadata = self._create_backup_metadata(backup_path)
            metadata_path = backup_path + '.meta'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_path}")
            logger.info(f"Backup size: {metadata['size_mb']:.2f} MB, checksum: {metadata['checksum']}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}", exc_info=True)
            # Clean up partial backup
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise IOError(f"Failed to create backup: {e}")
    
    def _create_backup_metadata(self, backup_path: str) -> Dict:
        """Create metadata for backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Metadata dictionary
        """
        file_size = os.path.getsize(backup_path)
        checksum = self._calculate_checksum(backup_path)
        
        # Get database statistics
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        
        # Count records in main tables
        tables_info = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for (table_name,) in cursor.fetchall():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            tables_info[table_name] = count
        
        conn.close()
        
        return {
            'backup_time': datetime.now().isoformat(),
            'source_db': self.db_path,
            'backup_path': backup_path,
            'size_bytes': file_size,
            'size_mb': file_size / (1024 * 1024),
            'checksum': checksum,
            'tables': tables_info
        }
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of checksum
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def restore_backup(self, backup_path: str, verify: bool = True) -> bool:
        """Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            verify: Whether to verify backup before restoring
            
        Returns:
            True if restore successful
            
        Raises:
            FileNotFoundError: If backup file doesn't exist
            ValueError: If backup verification fails
            IOError: If restore fails
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Verify backup if requested
        if verify:
            logger.info(f"Verifying backup: {backup_path}")
            if not self.verify_backup(backup_path):
                raise ValueError("Backup verification failed")
        
        try:
            # Create backup of current database before restoring
            logger.info("Creating safety backup of current database")
            safety_backup = self.create_backup("pre_restore_safety")
            logger.info(f"Safety backup created: {safety_backup}")
            
            # Close any existing connections
            logger.info(f"Restoring database from: {backup_path}")
            
            # Copy backup to database location
            shutil.copy2(backup_path, self.db_path)
            
            logger.info("Database restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            raise IOError(f"Failed to restore backup: {e}")
    
    def verify_backup(self, backup_path: str) -> bool:
        """Verify backup integrity.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if backup is valid
        """
        try:
            # Check if file exists
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Check metadata file
            metadata_path = backup_path + '.meta'
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Verify checksum
                current_checksum = self._calculate_checksum(backup_path)
                if current_checksum != metadata['checksum']:
                    logger.error(f"Checksum mismatch: expected {metadata['checksum']}, got {current_checksum}")
                    return False
            
            # Try to open database
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            conn.close()
            
            if result != 'ok':
                logger.error(f"Database integrity check failed: {result}")
                return False
            
            logger.info(f"Backup verification passed: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}", exc_info=True)
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db'):
                backup_path = os.path.join(self.backup_dir, filename)
                metadata_path = backup_path + '.meta'
                
                backup_info = {
                    'filename': filename,
                    'path': backup_path,
                    'size_mb': os.path.getsize(backup_path) / (1024 * 1024),
                    'created': datetime.fromtimestamp(os.path.getctime(backup_path))
                }
                
                # Load metadata if available
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        backup_info.update(metadata)
                
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self) -> int:
        """Remove backups older than retention period.
        
        Returns:
            Number of backups removed
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        logger.info(f"Cleaning up backups older than {cutoff_date}")
        
        for backup_info in self.list_backups():
            if backup_info['created'] < cutoff_date:
                # Skip safety backups
                if 'safety' in backup_info['filename']:
                    continue
                
                try:
                    os.remove(backup_info['path'])
                    
                    # Remove metadata file
                    metadata_path = backup_info['path'] + '.meta'
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                    
                    logger.info(f"Removed old backup: {backup_info['filename']}")
                    removed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to remove backup {backup_info['filename']}: {e}")
        
        logger.info(f"Cleanup complete: {removed_count} backups removed")
        return removed_count
    
    def get_backup_stats(self) -> Dict:
        """Get backup statistics.
        
        Returns:
            Dictionary with backup statistics
        """
        backups = self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size_mb': 0,
                'oldest_backup': None,
                'newest_backup': None
            }
        
        total_size = sum(b['size_mb'] for b in backups)
        
        return {
            'total_backups': len(backups),
            'total_size_mb': total_size,
            'oldest_backup': backups[-1]['created'].isoformat(),
            'newest_backup': backups[0]['created'].isoformat(),
            'retention_days': self.retention_days,
            'backup_dir': self.backup_dir
        }


def create_automated_backup() -> str:
    """Create an automated daily backup.
    
    Returns:
        Path to backup file
    """
    backup_manager = DatabaseBackup()
    backup_path = backup_manager.create_backup()
    
    # Cleanup old backups
    backup_manager.cleanup_old_backups()
    
    return backup_path


def restore_latest_backup() -> bool:
    """Restore from the most recent backup.
    
    Returns:
        True if restore successful
    """
    backup_manager = DatabaseBackup()
    backups = backup_manager.list_backups()
    
    if not backups:
        logger.error("No backups available")
        return False
    
    latest_backup = backups[0]
    logger.info(f"Restoring from latest backup: {latest_backup['filename']}")
    
    return backup_manager.restore_backup(latest_backup['path'])


def verify_all_backups() -> Tuple[int, int]:
    """Verify all backups.
    
    Returns:
        Tuple of (valid_count, invalid_count)
    """
    backup_manager = DatabaseBackup()
    backups = backup_manager.list_backups()
    
    valid_count = 0
    invalid_count = 0
    
    for backup_info in backups:
        if backup_manager.verify_backup(backup_info['path']):
            valid_count += 1
        else:
            invalid_count += 1
    
    logger.info(f"Backup verification complete: {valid_count} valid, {invalid_count} invalid")
    
    return valid_count, invalid_count
