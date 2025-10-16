# BRI Database Backup and Restore Guide

## Overview

BRI includes a comprehensive database backup system with automated backups, point-in-time recovery, and backup verification. This guide covers all backup and restore operations.

## Features

- **Automated Daily Backups**: Scheduled backups with configurable retention
- **Point-in-Time Recovery**: Restore database to any backup point
- **Backup Verification**: Integrity checks with checksums
- **30-Day Retention**: Automatic cleanup of old backups
- **Safety Backups**: Automatic backup before restore operations
- **Metadata Tracking**: Detailed backup information and statistics

## Quick Start

### Create a Backup

```bash
# Create backup with automatic name (timestamp-based)
python scripts/backup_database.py

# Create backup with custom name
python scripts/backup_database.py --name my_backup

# Create and verify backup
python scripts/backup_database.py --verify

# Create backup and cleanup old ones
python scripts/backup_database.py --cleanup
```

### Restore from Backup

```bash
# List available backups
python scripts/restore_database.py --list

# Restore from latest backup
python scripts/restore_database.py

# Restore from specific backup
python scripts/restore_database.py data/backups/bri_backup_20251016_143000.db

# Restore without verification (faster but risky)
python scripts/restore_database.py --no-verify
```

### Verify Backups

```bash
# Verify all backups
python scripts/verify_backups.py
```

## Backup Strategy

### Automated Daily Backups

Set up a scheduled task to run daily backups:

**Windows (Task Scheduler)**:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `scripts/backup_database.py --cleanup`
7. Start in: `C:\path\to\bri-video-agent`

**Linux/Mac (cron)**:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/bri-video-agent && python scripts/backup_database.py --cleanup
```

### Retention Policy

- **Default**: 30 days
- **Audit logs**: 90 days (for compliance)
- **Safety backups**: Never auto-deleted

Configure retention in `storage/backup.py`:
```python
backup_manager = DatabaseBackup(retention_days=30)
```

## Backup Files

### Location

Backups are stored in: `data/backups/`

### File Structure

```
data/backups/
├── bri_backup_20251016_143000.db       # Backup file
├── bri_backup_20251016_143000.db.meta  # Metadata
├── bri_backup_20251015_143000.db
├── bri_backup_20251015_143000.db.meta
└── pre_restore_safety.db               # Safety backup
```

### Metadata File

Each backup has a `.meta` file with:
- Backup timestamp
- File size and checksum
- Table record counts
- Source database path

Example:
```json
{
  "backup_time": "2025-10-16T14:30:00",
  "source_db": "data/bri.db",
  "backup_path": "data/backups/bri_backup_20251016_143000.db",
  "size_bytes": 10485760,
  "size_mb": 10.0,
  "checksum": "a1b2c3d4...",
  "tables": {
    "videos": 42,
    "memory": 1250,
    "video_context": 3500
  }
}
```

## Programmatic Usage

### Create Backup

```python
from storage.backup import DatabaseBackup

# Initialize backup manager
backup_manager = DatabaseBackup()

# Create backup
backup_path = backup_manager.create_backup()
print(f"Backup created: {backup_path}")

# Create named backup
backup_path = backup_manager.create_backup("before_migration")
```

### Restore Backup

```python
from storage.backup import DatabaseBackup

backup_manager = DatabaseBackup()

# Restore from specific backup
backup_manager.restore_backup("data/backups/bri_backup_20251016_143000.db")

# Restore without verification (faster)
backup_manager.restore_backup(backup_path, verify=False)
```

### Verify Backup

```python
from storage.backup import DatabaseBackup

backup_manager = DatabaseBackup()

# Verify single backup
is_valid = backup_manager.verify_backup(backup_path)

# Verify all backups
from storage.backup import verify_all_backups
valid, invalid = verify_all_backups()
print(f"Valid: {valid}, Invalid: {invalid}")
```

### List Backups

```python
from storage.backup import DatabaseBackup

backup_manager = DatabaseBackup()

# Get all backups (sorted by date, newest first)
backups = backup_manager.list_backups()

for backup in backups:
    print(f"{backup['filename']}: {backup['size_mb']:.2f} MB")
    print(f"  Created: {backup['created']}")
    print(f"  Tables: {backup['tables']}")
```

### Cleanup Old Backups

```python
from storage.backup import DatabaseBackup

backup_manager = DatabaseBackup(retention_days=30)

# Remove backups older than retention period
removed = backup_manager.cleanup_old_backups()
print(f"Removed {removed} old backups")
```

### Get Statistics

```python
from storage.backup import DatabaseBackup

backup_manager = DatabaseBackup()

stats = backup_manager.get_backup_stats()
print(f"Total backups: {stats['total_backups']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
print(f"Newest: {stats['newest_backup']}")
print(f"Oldest: {stats['oldest_backup']}")
```

## Recovery Scenarios

### Scenario 1: Accidental Data Deletion

```bash
# 1. List available backups
python scripts/restore_database.py --list

# 2. Restore from backup before deletion
python scripts/restore_database.py data/backups/bri_backup_20251016_120000.db
```

### Scenario 2: Database Corruption

```bash
# 1. Verify current database
sqlite3 data/bri.db "PRAGMA integrity_check"

# 2. If corrupted, restore from latest valid backup
python scripts/restore_database.py

# 3. Verify restored database
sqlite3 data/bri.db "PRAGMA integrity_check"
```

### Scenario 3: Failed Migration

```bash
# 1. Before migration, create named backup
python scripts/backup_database.py --name before_migration_v2

# 2. Run migration
python scripts/migrate_db.py

# 3. If migration fails, restore
python scripts/restore_database.py data/backups/before_migration_v2.db
```

### Scenario 4: Point-in-Time Recovery

```bash
# 1. List backups with timestamps
python scripts/restore_database.py --list

# 2. Choose backup closest to desired time
python scripts/restore_database.py data/backups/bri_backup_20251016_143000.db
```

## Best Practices

### 1. Regular Backups

- Run daily automated backups
- Create manual backups before major changes
- Verify backups weekly

### 2. Test Restores

```bash
# Test restore monthly
python scripts/restore_database.py --list
python scripts/verify_backups.py
```

### 3. Monitor Backup Health

```python
from storage.backup import DatabaseBackup

backup_manager = DatabaseBackup()
stats = backup_manager.get_backup_stats()

# Alert if no recent backups
from datetime import datetime, timedelta
newest = datetime.fromisoformat(stats['newest_backup'])
if datetime.now() - newest > timedelta(days=2):
    print("⚠️  Warning: No recent backups!")
```

### 4. Offsite Backups

For production, copy backups to offsite storage:

```bash
# Copy to cloud storage (example with AWS S3)
aws s3 sync data/backups/ s3://my-bucket/bri-backups/

# Copy to network drive
robocopy data\backups Z:\bri-backups /MIR
```

### 5. Backup Before Updates

```bash
# Before updating BRI
python scripts/backup_database.py --name before_update_v1.5

# Update BRI
git pull
pip install -r requirements.txt

# If issues occur, restore
python scripts/restore_database.py data/backups/before_update_v1.5.db
```

## Troubleshooting

### Backup Creation Fails

**Error**: `Database file not found`
```bash
# Check database path
ls -la data/bri.db

# Initialize database if missing
python scripts/init_db.py
```

**Error**: `Permission denied`
```bash
# Check backup directory permissions
mkdir -p data/backups
chmod 755 data/backups
```

### Restore Fails

**Error**: `Backup verification failed`
```bash
# Check backup integrity
python scripts/verify_backups.py

# Try restoring without verification (if backup is known good)
python scripts/restore_database.py --no-verify
```

**Error**: `Database is locked`
```bash
# Stop all BRI processes
# Then retry restore
python scripts/restore_database.py
```

### Backup Size Too Large

```bash
# Check backup size
du -sh data/backups/*

# Clean up old backups
python scripts/backup_database.py --cleanup

# Vacuum database to reduce size
sqlite3 data/bri.db "VACUUM"
```

## Monitoring

### Check Backup Status

```python
from storage.backup import DatabaseBackup
from datetime import datetime, timedelta

backup_manager = DatabaseBackup()
stats = backup_manager.get_backup_stats()

# Check if backups are current
newest = datetime.fromisoformat(stats['newest_backup'])
age_hours = (datetime.now() - newest).total_seconds() / 3600

if age_hours > 24:
    print(f"⚠️  Warning: Latest backup is {age_hours:.1f} hours old")
else:
    print(f"✓ Backups are current (latest: {age_hours:.1f} hours ago)")

# Check backup count
if stats['total_backups'] < 7:
    print(f"⚠️  Warning: Only {stats['total_backups']} backups available")
else:
    print(f"✓ {stats['total_backups']} backups available")
```

### Backup Health Report

```bash
# Generate health report
python -c "
from storage.backup import DatabaseBackup
import json

backup_manager = DatabaseBackup()
stats = backup_manager.get_backup_stats()

print(json.dumps(stats, indent=2))
"
```

## Security

### Backup Encryption

For sensitive data, encrypt backups:

```bash
# Encrypt backup (Linux/Mac)
openssl enc -aes-256-cbc -salt -in backup.db -out backup.db.enc

# Decrypt backup
openssl enc -d -aes-256-cbc -in backup.db.enc -out backup.db
```

### Access Control

```bash
# Restrict backup directory access (Linux/Mac)
chmod 700 data/backups

# Windows: Use folder properties to restrict access
```

## Summary

The BRI backup system provides:

- ✅ Automated daily backups
- ✅ 30-day retention with automatic cleanup
- ✅ Point-in-time recovery
- ✅ Backup verification with checksums
- ✅ Safety backups before restores
- ✅ Detailed metadata and statistics
- ✅ Easy-to-use scripts and API

For questions or issues, check the logs in `logs/bri.log` for detailed backup operation information.
