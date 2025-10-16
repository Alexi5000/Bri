"""Data archival and cleanup CLI tool for BRI video agent.

Usage:
    python scripts/archival_cli.py status                    # Show retention policy status
    python scripts/archival_cli.py soft-delete VIDEO_ID      # Soft delete a video
    python scripts/archival_cli.py restore VIDEO_ID          # Restore a soft-deleted video
    python scripts/archival_cli.py cleanup                   # Clean up orphaned data
    python scripts/archival_cli.py vacuum                    # Optimize database
    python scripts/archival_cli.py apply-policies            # Apply all retention policies
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.database import get_database, initialize_database
from storage.archival import get_archival_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_status():
    """Show retention policy status."""
    try:
        manager = get_archival_manager()
        status = manager.get_retention_policy_status()
        
        print("\n=== Data Retention Policy Status ===")
        print(f"Database Size: {status.get('database_size_mb', 0):.2f} MB")
        print(f"\nTotal Records:")
        print(f"  Videos: {status.get('total_videos', 0)}")
        print(f"  Conversations: {status.get('total_memory', 0)}")
        print(f"  Context Entries: {status.get('total_context', 0)}")
        print(f"\nRetention Status:")
        print(f"  Soft-Deleted Videos: {status.get('soft_deleted_videos', 0)}")
        print(f"  Old Conversations (>30 days): {status.get('old_conversations', 0)}")
        print()
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        sys.exit(1)


def soft_delete(video_id: str):
    """Soft delete a video."""
    try:
        manager = get_archival_manager()
        
        if manager.soft_delete_video(video_id):
            print(f"✓ Video {video_id} soft deleted successfully")
        else:
            print(f"✗ Failed to soft delete video {video_id}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to soft delete video: {e}")
        sys.exit(1)


def restore(video_id: str):
    """Restore a soft-deleted video."""
    try:
        manager = get_archival_manager()
        
        if manager.restore_video(video_id):
            print(f"✓ Video {video_id} restored successfully")
        else:
            print(f"✗ Failed to restore video {video_id}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to restore video: {e}")
        sys.exit(1)


def list_deleted():
    """List soft-deleted videos."""
    try:
        manager = get_archival_manager()
        deleted = manager.get_deleted_videos()
        
        if not deleted:
            print("\n✓ No soft-deleted videos")
            return
        
        print(f"\n=== Soft-Deleted Videos ({len(deleted)}) ===")
        for video in deleted:
            print(f"\nVideo ID: {video['video_id']}")
            print(f"  Filename: {video['filename']}")
            print(f"  Deleted: {video['deleted_at']}")
            print(f"  Duration: {video['duration']:.1f}s")
        print()
        
    except Exception as e:
        logger.error(f"Failed to list deleted videos: {e}")
        sys.exit(1)


def cleanup():
    """Clean up orphaned data."""
    try:
        manager = get_archival_manager()
        
        print("\nCleaning up orphaned data...")
        stats = manager.cleanup_orphaned_data()
        
        print("\n=== Cleanup Results ===")
        print(f"Orphaned Memory Records: {stats['orphaned_memory']}")
        print(f"Orphaned Context Records: {stats['orphaned_context']}")
        print(f"Orphaned Lineage Records: {stats['orphaned_lineage']}")
        print(f"Orphaned Files/Directories: {stats['orphaned_files']}")
        print("\n✓ Cleanup complete\n")
        
    except Exception as e:
        logger.error(f"Failed to cleanup: {e}")
        sys.exit(1)


def vacuum():
    """Optimize database."""
    try:
        manager = get_archival_manager()
        
        print("\nOptimizing database...")
        if manager.vacuum_database():
            manager.analyze_database()
            print("✓ Database optimization complete\n")
        else:
            print("✗ Database optimization failed\n")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to vacuum database: {e}")
        sys.exit(1)


def apply_policies(
    archive_days: int = 30,
    delete_days: int = 7,
    cleanup_orphaned: bool = True,
    vacuum_db: bool = True
):
    """Apply all retention policies."""
    try:
        manager = get_archival_manager()
        
        print("\n=== Applying Retention Policies ===")
        print(f"Archive conversations older than: {archive_days} days")
        print(f"Delete soft-deleted videos older than: {delete_days} days")
        print(f"Cleanup orphaned data: {cleanup_orphaned}")
        print(f"Vacuum database: {vacuum_db}")
        print()
        
        results = manager.apply_retention_policies(
            archive_conversations_days=archive_days,
            delete_soft_deleted_days=delete_days,
            cleanup_orphaned=cleanup_orphaned,
            vacuum=vacuum_db
        )
        
        print("\n=== Results ===")
        print(f"Archived Conversations: {results['archived_conversations']}")
        print(f"Permanently Deleted Videos: {results['deleted_videos']}")
        
        if cleanup_orphaned:
            stats = results['cleanup_stats']
            print(f"\nCleanup Statistics:")
            print(f"  Orphaned Memory: {stats.get('orphaned_memory', 0)}")
            print(f"  Orphaned Context: {stats.get('orphaned_context', 0)}")
            print(f"  Orphaned Lineage: {stats.get('orphaned_lineage', 0)}")
            print(f"  Orphaned Files: {stats.get('orphaned_files', 0)}")
        
        if vacuum_db:
            print(f"\nDatabase Vacuum: {'✓ Success' if results['vacuum_success'] else '✗ Failed'}")
        
        print("\n✓ Retention policies applied successfully\n")
        
    except Exception as e:
        logger.error(f"Failed to apply policies: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Data archival and cleanup tool for BRI video agent"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Status command
    subparsers.add_parser('status', help='Show retention policy status')
    
    # Soft delete command
    soft_delete_parser = subparsers.add_parser('soft-delete', help='Soft delete a video')
    soft_delete_parser.add_argument('video_id', help='Video ID to soft delete')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore a soft-deleted video')
    restore_parser.add_argument('video_id', help='Video ID to restore')
    
    # List deleted command
    subparsers.add_parser('list-deleted', help='List soft-deleted videos')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up orphaned data')
    
    # Vacuum command
    subparsers.add_parser('vacuum', help='Optimize database')
    
    # Apply policies command
    policies_parser = subparsers.add_parser('apply-policies', help='Apply all retention policies')
    policies_parser.add_argument(
        '--archive-days',
        type=int,
        default=30,
        help='Archive conversations older than N days (default: 30)'
    )
    policies_parser.add_argument(
        '--delete-days',
        type=int,
        default=7,
        help='Delete soft-deleted videos older than N days (default: 7)'
    )
    policies_parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip orphaned data cleanup'
    )
    policies_parser.add_argument(
        '--no-vacuum',
        action='store_true',
        help='Skip database vacuum'
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
    if args.command == 'status':
        show_status()
    elif args.command == 'soft-delete':
        soft_delete(args.video_id)
    elif args.command == 'restore':
        restore(args.video_id)
    elif args.command == 'list-deleted':
        list_deleted()
    elif args.command == 'cleanup':
        cleanup()
    elif args.command == 'vacuum':
        vacuum()
    elif args.command == 'apply-policies':
        apply_policies(
            archive_days=args.archive_days,
            delete_days=args.delete_days,
            cleanup_orphaned=not args.no_cleanup,
            vacuum_db=not args.no_vacuum
        )


if __name__ == '__main__':
    main()
