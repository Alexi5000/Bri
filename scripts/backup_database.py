"""Script to create database backup."""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.backup import DatabaseBackup, create_automated_backup
from utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Create database backup."""
    parser = argparse.ArgumentParser(description='Create BRI database backup')
    parser.add_argument(
        '--name',
        type=str,
        help='Custom backup name (default: timestamp-based)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify backup after creation'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up old backups after creating new one'
    )
    
    args = parser.parse_args()
    
    try:
        backup_manager = DatabaseBackup()
        
        # Create backup
        logger.info("Creating database backup...")
        backup_path = backup_manager.create_backup(args.name)
        print(f"✓ Backup created: {backup_path}")
        
        # Verify if requested
        if args.verify:
            logger.info("Verifying backup...")
            if backup_manager.verify_backup(backup_path):
                print("✓ Backup verification passed")
            else:
                print("✗ Backup verification failed")
                return 1
        
        # Cleanup if requested
        if args.cleanup:
            logger.info("Cleaning up old backups...")
            removed = backup_manager.cleanup_old_backups()
            print(f"✓ Removed {removed} old backups")
        
        # Show stats
        stats = backup_manager.get_backup_stats()
        print(f"\nBackup Statistics:")
        print(f"  Total backups: {stats['total_backups']}")
        print(f"  Total size: {stats['total_size_mb']:.2f} MB")
        print(f"  Newest: {stats['newest_backup']}")
        print(f"  Oldest: {stats['oldest_backup']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        print(f"✗ Backup failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
