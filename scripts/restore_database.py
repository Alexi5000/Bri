"""Script to restore database from backup."""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.backup import DatabaseBackup
from utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Restore database from backup."""
    parser = argparse.ArgumentParser(description='Restore BRI database from backup')
    parser.add_argument(
        'backup_path',
        type=str,
        nargs='?',
        help='Path to backup file (default: latest backup)'
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip backup verification before restore'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available backups'
    )
    
    args = parser.parse_args()
    
    try:
        backup_manager = DatabaseBackup()
        
        # List backups if requested
        if args.list:
            backups = backup_manager.list_backups()
            if not backups:
                print("No backups available")
                return 0
            
            print(f"\nAvailable backups ({len(backups)}):")
            print("-" * 80)
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['filename']}")
                print(f"   Created: {backup['created']}")
                print(f"   Size: {backup['size_mb']:.2f} MB")
                if 'tables' in backup:
                    print(f"   Tables: {', '.join(f'{k}({v})' for k, v in backup['tables'].items())}")
                print()
            return 0
        
        # Determine backup to restore
        if args.backup_path:
            backup_path = args.backup_path
        else:
            # Use latest backup
            backups = backup_manager.list_backups()
            if not backups:
                print("✗ No backups available")
                return 1
            backup_path = backups[0]['path']
            print(f"Using latest backup: {backups[0]['filename']}")
        
        # Confirm restore
        print(f"\n⚠️  WARNING: This will replace the current database!")
        print(f"Backup to restore: {backup_path}")
        response = input("Continue? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Restore cancelled")
            return 0
        
        # Restore backup
        logger.info(f"Restoring database from: {backup_path}")
        verify = not args.no_verify
        
        if backup_manager.restore_backup(backup_path, verify=verify):
            print("✓ Database restored successfully")
            return 0
        else:
            print("✗ Database restore failed")
            return 1
        
    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        print(f"✗ Restore failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
