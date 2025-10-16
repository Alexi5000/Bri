"""Database migration CLI tool for BRI video agent.

Usage:
    python scripts/migrate_db.py status          # Show migration status
    python scripts/migrate_db.py migrate         # Apply all pending migrations
    python scripts/migrate_db.py migrate --to 3  # Migrate to specific version
    python scripts/migrate_db.py rollback        # Rollback last migration
    python scripts/migrate_db.py rollback --to 2 # Rollback to specific version
    python scripts/migrate_db.py test            # Test all migrations
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import get_database, initialize_database
from storage.migrations import get_migration_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_status():
    """Show current migration status."""
    try:
        db = get_database()
        manager = get_migration_manager(db)
        status = manager.status()
        
        print("\n=== Database Migration Status ===")
        print(f"Current Version: {status['current_version']}")
        print(f"Applied Migrations: {status['applied_count']}")
        print(f"Pending Migrations: {status['pending_count']}")
        
        if status['applied_migrations']:
            print("\nApplied Migrations:")
            for migration in status['applied_migrations']:
                print(f"  [{migration['version']}] {migration['description']}")
                print(f"      Applied: {migration['applied_at']}")
        
        if status['pending_migrations']:
            print("\nPending Migrations:")
            for migration in status['pending_migrations']:
                print(f"  [{migration['version']}] {migration['description']}")
        else:
            print("\n✓ Database is up to date")
        
        print()
        
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        sys.exit(1)


def migrate(target_version=None):
    """Apply pending migrations."""
    try:
        db = get_database()
        manager = get_migration_manager(db)
        
        current = manager.get_current_version()
        pending = manager.get_pending_migrations()
        
        if not pending:
            print("✓ No pending migrations")
            return
        
        target = target_version or pending[-1].version
        print(f"\nMigrating from version {current} to {target}...")
        
        manager.migrate(target_version=target_version)
        
        print(f"✓ Migration complete. Current version: {manager.get_current_version()}\n")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


def rollback(target_version=None, steps=1):
    """Rollback migrations."""
    try:
        db = get_database()
        manager = get_migration_manager(db)
        
        current = manager.get_current_version()
        
        if current == 0:
            print("✓ No migrations to rollback")
            return
        
        if target_version is not None:
            print(f"\nRolling back from version {current} to {target_version}...")
            manager.rollback(target_version=target_version)
        else:
            print(f"\nRolling back {steps} migration(s) from version {current}...")
            manager.rollback(steps=steps)
        
        print(f"✓ Rollback complete. Current version: {manager.get_current_version()}\n")
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        sys.exit(1)


def test_migrations():
    """Test all migrations."""
    try:
        db = get_database()
        manager = get_migration_manager(db)
        
        print("\n=== Testing Migrations ===")
        
        all_passed = True
        for migration in manager.migrations:
            print(f"Testing migration {migration.version}: {migration.description}...", end=" ")
            if manager.test_migration(migration):
                print("✓ PASS")
            else:
                print("✗ FAIL")
                all_passed = False
        
        if all_passed:
            print("\n✓ All migrations passed\n")
        else:
            print("\n✗ Some migrations failed\n")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Migration testing failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database migration tool for BRI video agent"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Status command
    subparsers.add_parser('status', help='Show migration status')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Apply pending migrations')
    migrate_parser.add_argument(
        '--to',
        type=int,
        dest='target_version',
        help='Target version to migrate to'
    )
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migrations')
    rollback_parser.add_argument(
        '--to',
        type=int,
        dest='target_version',
        help='Target version to rollback to'
    )
    rollback_parser.add_argument(
        '--steps',
        type=int,
        default=1,
        help='Number of migrations to rollback (default: 1)'
    )
    
    # Test command
    subparsers.add_parser('test', help='Test all migrations')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Ensure database is initialized
    try:
        initialize_database()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    # Execute command
    if args.command == 'status':
        show_status()
    elif args.command == 'migrate':
        migrate(target_version=args.target_version)
    elif args.command == 'rollback':
        rollback(target_version=args.target_version, steps=args.steps)
    elif args.command == 'test':
        test_migrations()


if __name__ == '__main__':
    main()
