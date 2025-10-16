"""Script to verify all database backups."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.backup import DatabaseBackup
from utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Verify all database backups."""
    try:
        backup_manager = DatabaseBackup()
        backups = backup_manager.list_backups()
        
        if not backups:
            print("No backups to verify")
            return 0
        
        print(f"Verifying {len(backups)} backups...")
        print("-" * 80)
        
        valid_count = 0
        invalid_count = 0
        
        for backup in backups:
            print(f"Checking: {backup['filename']}...", end=' ')
            
            if backup_manager.verify_backup(backup['path']):
                print("✓ VALID")
                valid_count += 1
            else:
                print("✗ INVALID")
                invalid_count += 1
        
        print("-" * 80)
        print(f"\nResults:")
        print(f"  Valid: {valid_count}")
        print(f"  Invalid: {invalid_count}")
        print(f"  Total: {len(backups)}")
        
        if invalid_count > 0:
            print(f"\n⚠️  Warning: {invalid_count} invalid backup(s) found!")
            return 1
        else:
            print("\n✓ All backups are valid")
            return 0
        
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        print(f"✗ Verification failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
