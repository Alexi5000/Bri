"""Database health check CLI tool for BRI video agent.

Usage:
    python scripts/health_check.py report          # Generate health report
    python scripts/health_check.py size            # Show database size
    python scripts/health_check.py growth          # Show growth rate
    python scripts/health_check.py integrity       # Check integrity
    python scripts/health_check.py backup          # Create backup
    python scripts/health_check.py cleanup-backups # Clean up old backups
"""

import sys
import argparse
import logging
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import get_database, initialize_database
from storage.health_monitor import get_health_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_report():
    """Generate and display health report."""
    try:
        monitor = get_health_monitor()
        report = monitor.get_health_report()
        
        print("\n" + "="*60)
        print("DATABASE HEALTH REPORT")
        print("="*60)
        
        # Health score
        status_emoji = "✓" if report['health_status'] == 'healthy' else "⚠" if report['health_status'] == 'warning' else "✗"
        print(f"\n{status_emoji} Health Status: {report['health_status'].upper()}")
        print(f"   Health Score: {report['health_score']}/100")
        
        # Database size
        size_info = report['database_size']
        print(f"\n📊 Database Size:")
        print(f"   Size: {size_info['size_mb']} MB")
        print(f"   Path: {size_info['path']}")
        
        # Growth rate
        growth = report['growth_rate']
        print(f"\n📈 Growth Rate:")
        print(f"   Total Videos: {growth.get('total_videos', 0)}")
        print(f"   Total Conversations: {growth.get('total_memory', 0)}")
        print(f"   Total Context: {growth.get('total_context', 0)}")
        print(f"   Recent Videos ({growth.get('days_analyzed', 0)} days): {growth.get('recent_videos', 0)}")
        print(f"   Growth Rate: {growth.get('growth_rate_mb_per_day', 0)} MB/day")
        print(f"   Estimated Size (30 days): {growth.get('estimated_size_30_days_mb', 0)} MB")
        
        # Connection pool
        conn = report['connection_pool']
        print(f"\n🔌 Connection Pool:")
        print(f"   Connected: {'✓' if conn['connected'] else '✗'}")
        print(f"   Foreign Keys: {'✓ Enabled' if conn.get('foreign_keys_enabled') else '✗ Disabled'}")
        print(f"   Journal Mode: {conn.get('journal_mode', 'unknown')}")
        print(f"   Cache Size: {conn.get('cache_size', 0)}")
        
        # Integrity
        integrity = report['integrity']
        print(f"\n🔍 Integrity Check:")
        print(f"   Status: {'✓ OK' if integrity['integrity_ok'] else '✗ FAILED'}")
        if not integrity['integrity_ok']:
            print(f"   Message: {integrity.get('integrity_message', 'unknown')}")
        
        # Tables
        if 'tables' in integrity:
            print(f"\n📋 Tables:")
            for table, count in integrity['tables'].items():
                print(f"   {table}: {count} records")
        
        # Constraints
        constraints = report['constraints']
        print(f"\n⚙️  Constraints:")
        print(f"   Foreign Keys: {'✓ Enabled' if constraints['foreign_keys_enabled'] else '✗ Disabled'}")
        print(f"   Orphaned Memory: {constraints['orphaned_memory']}")
        print(f"   Orphaned Context: {constraints['orphaned_context']}")
        print(f"   Invalid Durations: {constraints['invalid_durations']}")
        print(f"   Invalid Timestamps: {constraints['invalid_timestamps']}")
        
        # Indexes
        indexes = report['indexes']
        print(f"\n📇 Indexes: {len(indexes)} total")
        
        # Slow queries
        slow_queries = report['slow_queries']
        if slow_queries:
            print(f"\n⏱️  Slow Queries: {len(slow_queries)} detected")
            for i, query in enumerate(slow_queries[:5], 1):
                print(f"   {i}. {query['query'][:60]}...")
                print(f"      Slow Count: {query['slow_count']}/{query['total_count']}")
                print(f"      Max Time: {query['max_time_ms']:.2f}ms")
        else:
            print(f"\n⏱️  Slow Queries: None detected")
        
        print("\n" + "="*60 + "\n")
        
        # Save report to file
        report_path = Path("logs/health_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Full report saved to: {report_path}\n")
        
    except Exception as e:
        logger.error(f"Failed to generate health report: {e}")
        sys.exit(1)


def show_size():
    """Show database size information."""
    try:
        monitor = get_health_monitor()
        size_info = monitor.get_database_size()
        
        print(f"\n📊 Database Size:")
        print(f"   Size: {size_info['size_mb']} MB ({size_info['size_bytes']:,} bytes)")
        print(f"   Path: {size_info['path']}\n")
        
    except Exception as e:
        logger.error(f"Failed to get database size: {e}")
        sys.exit(1)


def show_growth():
    """Show database growth rate."""
    try:
        monitor = get_health_monitor()
        growth = monitor.get_growth_rate()
        
        print(f"\n📈 Database Growth Rate:")
        print(f"   Current Size: {growth.get('current_size_mb', 0)} MB")
        print(f"   Total Videos: {growth.get('total_videos', 0)}")
        print(f"   Recent Videos ({growth.get('days_analyzed', 0)} days): {growth.get('recent_videos', 0)}")
        print(f"   Growth Rate: {growth.get('growth_rate_mb_per_day', 0)} MB/day")
        print(f"   Estimated Size (30 days): {growth.get('estimated_size_30_days_mb', 0)} MB\n")
        
    except Exception as e:
        logger.error(f"Failed to calculate growth rate: {e}")
        sys.exit(1)


def check_integrity():
    """Check database integrity."""
    try:
        monitor = get_health_monitor()
        integrity = monitor.check_table_integrity()
        
        print(f"\n🔍 Database Integrity Check:")
        print(f"   Status: {'✓ OK' if integrity['integrity_ok'] else '✗ FAILED'}")
        print(f"   Message: {integrity.get('integrity_message', 'unknown')}")
        
        if 'tables' in integrity:
            print(f"\n   Tables:")
            for table, count in integrity['tables'].items():
                print(f"     {table}: {count} records")
        
        print()
        
        if not integrity['integrity_ok']:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to check integrity: {e}")
        sys.exit(1)


def create_backup():
    """Create database backup."""
    try:
        monitor = get_health_monitor()
        
        print("\nCreating database backup...")
        backup_path = monitor.create_backup()
        
        if backup_path:
            print(f"✓ Backup created successfully: {backup_path}\n")
        else:
            print("✗ Backup failed\n")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        sys.exit(1)


def cleanup_backups(keep_days: int = 30):
    """Clean up old backups."""
    try:
        monitor = get_health_monitor()
        
        print(f"\nCleaning up backups older than {keep_days} days...")
        deleted_count = monitor.cleanup_old_backups(keep_days=keep_days)
        
        print(f"✓ Deleted {deleted_count} old backup(s)\n")
        
    except Exception as e:
        logger.error(f"Failed to cleanup backups: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database health check tool for BRI video agent"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Report command
    subparsers.add_parser('report', help='Generate comprehensive health report')
    
    # Size command
    subparsers.add_parser('size', help='Show database size')
    
    # Growth command
    subparsers.add_parser('growth', help='Show database growth rate')
    
    # Integrity command
    subparsers.add_parser('integrity', help='Check database integrity')
    
    # Backup command
    subparsers.add_parser('backup', help='Create database backup')
    
    # Cleanup backups command
    cleanup_parser = subparsers.add_parser('cleanup-backups', help='Clean up old backups')
    cleanup_parser.add_argument(
        '--keep-days',
        type=int,
        default=30,
        help='Number of days to keep backups (default: 30)'
    )
    
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
    if args.command == 'report':
        show_report()
    elif args.command == 'size':
        show_size()
    elif args.command == 'growth':
        show_growth()
    elif args.command == 'integrity':
        check_integrity()
    elif args.command == 'backup':
        create_backup()
    elif args.command == 'cleanup-backups':
        cleanup_backups(keep_days=args.keep_days)


if __name__ == '__main__':
    main()
