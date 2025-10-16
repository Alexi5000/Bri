# Database Management Guide

## Quick Reference

This guide provides quick commands for managing the BRI database using the new tools from Task 45.

## Health Monitoring

### Check Overall Health
```bash
python scripts/health_check.py report
```
Generates a comprehensive health report with:
- Health score (0-100)
- Database size and growth rate
- Connection pool status
- Integrity check results
- Constraint violations
- Slow query detection

### Check Specific Metrics
```bash
# Database size
python scripts/health_check.py size

# Growth rate and projections
python scripts/health_check.py growth

# Integrity check only
python scripts/health_check.py integrity
```

## Backup Management

### Create Backup
```bash
python scripts/health_check.py backup
```
Creates a timestamped backup in `data/backups/`

### Clean Up Old Backups
```bash
# Keep last 30 days (default)
python scripts/health_check.py cleanup-backups

# Keep last 60 days
python scripts/health_check.py cleanup-backups --keep-days 60
```

## Data Archival & Cleanup

### Check Retention Status
```bash
python scripts/archival_cli.py status
```
Shows:
- Database size
- Total records (videos, conversations, context)
- Soft-deleted videos
- Old conversations

### Apply Retention Policies
```bash
# Apply all policies with defaults
python scripts/archival_cli.py apply-policies

# Custom settings
python scripts/archival_cli.py apply-policies \
  --archive-days 60 \
  --delete-days 14 \
  --no-vacuum
```

Default policies:
- Archive conversations older than 30 days
- Permanently delete soft-deleted videos after 7 days
- Clean up orphaned data
- Run VACUUM to optimize database

### Manual Operations

#### Soft Delete Video
```bash
python scripts/archival_cli.py soft-delete VIDEO_ID
```

#### Restore Video
```bash
python scripts/archival_cli.py restore VIDEO_ID
```

#### List Deleted Videos
```bash
python scripts/archival_cli.py list-deleted
```

#### Clean Up Orphaned Data
```bash
python scripts/archival_cli.py cleanup
```

#### Optimize Database
```bash
python scripts/archival_cli.py vacuum
```

## Schema Migrations

### Check Migration Status
```bash
python scripts/migrate_db.py status
```
Shows:
- Current schema version
- Applied migrations
- Pending migrations

### Apply Migrations
```bash
# Apply all pending migrations
python scripts/migrate_db.py migrate

# Migrate to specific version
python scripts/migrate_db.py migrate --to 3
```

### Rollback Migrations
```bash
# Rollback last migration
python scripts/migrate_db.py rollback

# Rollback to specific version
python scripts/migrate_db.py rollback --to 2

# Rollback multiple steps
python scripts/migrate_db.py rollback --steps 3
```

### Test Migrations
```bash
python scripts/migrate_db.py test
```

## Scheduled Maintenance

### Daily Tasks
```bash
# Create backup
python scripts/health_check.py backup

# Check health
python scripts/health_check.py report
```

### Weekly Tasks
```bash
# Apply retention policies
python scripts/archival_cli.py apply-policies

# Clean up old backups
python scripts/health_check.py cleanup-backups
```

### Monthly Tasks
```bash
# Review growth rate
python scripts/health_check.py growth

# Check integrity
python scripts/health_check.py integrity
```

## Troubleshooting

### Database Growing Too Fast
```bash
# Check growth rate
python scripts/health_check.py growth

# Apply aggressive retention policies
python scripts/archival_cli.py apply-policies --archive-days 14 --delete-days 3

# Clean up orphaned data
python scripts/archival_cli.py cleanup

# Optimize database
python scripts/archival_cli.py vacuum
```

### Slow Queries Detected
```bash
# Generate health report to see slow queries
python scripts/health_check.py report

# Check logs/health_report.json for details
```

### Integrity Check Failed
```bash
# Check integrity
python scripts/health_check.py integrity

# If failed, restore from backup
# 1. Stop application
# 2. Restore backup: cp data/backups/bri_backup_YYYYMMDD_HHMMSS.db data/bri.db
# 3. Restart application
```

### Orphaned Data
```bash
# Check for orphaned data
python scripts/archival_cli.py status

# Clean up
python scripts/archival_cli.py cleanup
```

## Programmatic Usage

### Python Integration

#### Health Monitoring
```python
from storage.health_monitor import get_health_monitor

monitor = get_health_monitor()

# Get health report
report = monitor.get_health_report()
print(f"Health Score: {report['health_score']}/100")

# Create backup
backup_path = monitor.create_backup()

# Monitor query performance
with monitor.query_monitor.monitor_query("SELECT * FROM videos"):
    results = db.execute_query("SELECT * FROM videos")
```

#### Archival Management
```python
from storage.archival import get_archival_manager

archival = get_archival_manager()

# Soft delete video
archival.soft_delete_video("video_id")

# Apply retention policies
results = archival.apply_retention_policies(
    archive_conversations_days=30,
    delete_soft_deleted_days=7,
    cleanup_orphaned=True,
    vacuum=True
)
```

#### Migration Management
```python
from storage.migrations import get_migration_manager

manager = get_migration_manager()

# Check status
status = manager.status()
print(f"Current Version: {status['current_version']}")

# Apply migrations
manager.migrate()
```

## Best Practices

1. **Daily Backups**: Create backups before major operations
2. **Weekly Cleanup**: Apply retention policies weekly
3. **Monthly Review**: Review growth rate and health metrics
4. **Monitor Health Score**: Keep score above 80
5. **Test Migrations**: Always test migrations before production
6. **Soft Delete First**: Use soft delete before permanent deletion
7. **Regular VACUUM**: Run VACUUM monthly to optimize database

## Health Score Interpretation

- **90-100**: Excellent - No action needed
- **80-89**: Good - Monitor regularly
- **60-79**: Warning - Review issues and plan maintenance
- **Below 60**: Critical - Immediate action required

## Common Issues

### Issue: Health Score Below 80
**Solution:**
1. Check health report for specific issues
2. Run integrity check
3. Clean up orphaned data
4. Apply retention policies
5. Run VACUUM

### Issue: Database Size Growing Rapidly
**Solution:**
1. Check growth rate
2. Review retention policies
3. Archive old conversations
4. Delete unnecessary videos
5. Run VACUUM

### Issue: Slow Queries
**Solution:**
1. Review slow query log in health report
2. Check if indexes are being used
3. Optimize problematic queries
4. Consider adding new indexes

## Support

For issues or questions:
1. Check health report: `python scripts/health_check.py report`
2. Review logs: `logs/database_health.log`
3. Check documentation: `docs/TASK_45_SUMMARY.md`
