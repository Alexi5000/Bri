# Data Quality & Monitoring Integration Guide

## Quick Start

### 1. Import the Modules

```python
from services.data_quality_metrics import get_quality_metrics
from services.data_observability import get_data_observability
from services.data_recovery import get_data_recovery
```

### 2. Monitor Video Quality

```python
# Get quality metrics instance
metrics = get_quality_metrics()

# Check quality for a video
report = metrics.get_quality_report(video_id)

if report['quality_score'] < 70:
    print(f"⚠️ Low quality: {report['quality_status']}")
    print(f"Completeness: {report['completeness']['overall_completeness']:.1%}")
    print(f"Accuracy: {report['accuracy']['overall_accuracy']:.1%}")
```

### 3. Monitor Pipeline Performance

```python
# Get observability instance
observability = get_data_observability()

# Monitor a processing stage
with observability.latency_monitor.monitor_stage('frame_extraction', video_id):
    frames = extract_frames(video_id)

# Get performance stats
stats = observability.latency_monitor.get_stage_statistics('frame_extraction')
print(f"Average time: {stats['avg']:.2f}s")
```

### 4. Handle Failures with Automatic Retry

```python
# Get recovery instance
recovery = get_data_recovery()

# Execute with automatic retry
try:
    result = recovery.retry.execute_with_retry(
        process_video,
        'video_processing',
        video_id
    )
except Exception as e:
    # Add to dead letter queue for manual review
    dlq_id = recovery.dlq.add_to_queue(
        video_id,
        'video_processing',
        {'video_id': video_id},
        str(e)
    )
```

### 5. Reconcile Data

```python
# Reconcile a specific video
result = recovery.reconciliation.reconcile_video_data(video_id)
print(f"Fixed {len(result['fixes_applied'])} issues")

# Or reconcile all videos
summary = recovery.reconciliation.reconcile_all_videos()
print(f"Fixed {summary['total_fixes']} issues across {summary['total_videos']} videos")
```

## API Endpoints

Add these endpoints to your FastAPI application:

```python
from fastapi import APIRouter
from services.data_quality_metrics import get_quality_metrics
from services.data_observability import get_data_observability
from services.data_recovery import get_data_recovery

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/videos/{video_id}/quality")
async def get_video_quality(video_id: str):
    """Get quality report for a video."""
    metrics = get_quality_metrics()
    return metrics.get_quality_report(video_id)

@router.get("/videos/{video_id}/flow")
async def get_video_flow(video_id: str):
    """Get data flow visualization for a video."""
    observability = get_data_observability()
    return observability.flow_visualizer.get_video_data_flow(video_id)

@router.post("/videos/{video_id}/reprocess")
async def reprocess_video(video_id: str):
    """Manually reprocess a failed video."""
    recovery = get_data_recovery()
    return recovery.reprocessing.reprocess_video(video_id)

@router.get("/system/quality")
async def get_system_quality():
    """Get system-wide quality metrics."""
    metrics = get_quality_metrics()
    return metrics.get_system_quality_report()

@router.get("/system/recovery")
async def get_recovery_dashboard():
    """Get recovery dashboard with DLQ status."""
    recovery = get_data_recovery()
    return recovery.get_recovery_dashboard()

@router.get("/system/observability")
async def get_observability_dashboard():
    """Get observability dashboard."""
    observability = get_data_observability()
    return observability.get_observability_dashboard()
```

## Scheduled Jobs

Set up background jobs for continuous monitoring:

```python
import schedule
import time
from services.data_quality_metrics import get_quality_metrics
from services.data_recovery import get_data_recovery

def quality_check_job():
    """Check system quality every hour."""
    metrics = get_quality_metrics()
    report = metrics.get_system_quality_report()
    
    if report['system_health'] == 'degraded':
        # Send alert
        print(f"⚠️ System health degraded: {report['complete_videos_percentage']:.1%} complete")

def reconciliation_job():
    """Reconcile data every 6 hours."""
    recovery = get_data_recovery()
    summary = recovery.reconciliation.reconcile_all_videos()
    print(f"✓ Reconciliation: {summary['total_fixes']} fixes applied")

def dlq_processing_job():
    """Process DLQ items every 30 minutes."""
    recovery = get_data_recovery()
    items = recovery.dlq.get_queue_items(limit=10)
    
    for item in items:
        result = recovery.reprocessing.reprocess_dlq_item(item['dlq_id'])
        print(f"Reprocessed {item['dlq_id']}: {result['status']}")

# Schedule jobs
schedule.every(1).hours.do(quality_check_job)
schedule.every(6).hours.do(reconciliation_job)
schedule.every(30).minutes.do(dlq_processing_job)

# Run scheduler in background thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

import threading
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()
```

## Testing

Run the data quality tests:

```bash
# Run all tests
pytest tests/test_data_quality.py -v

# Run specific test category
pytest tests/test_data_quality.py::TestDataTransformations -v
pytest tests/test_data_quality.py::TestQueryPerformance -v
pytest tests/test_data_quality.py::TestChaosEngineering -v

# Run with coverage
pytest tests/test_data_quality.py --cov=services --cov-report=html
```

## Monitoring Dashboard Example

Create a simple monitoring dashboard:

```python
from services.data_quality_metrics import get_quality_metrics
from services.data_observability import get_data_observability
from services.data_recovery import get_data_recovery

def print_monitoring_dashboard():
    """Print a simple monitoring dashboard."""
    metrics = get_quality_metrics()
    observability = get_data_observability()
    recovery = get_data_recovery()
    
    # System quality
    system_report = metrics.get_system_quality_report()
    print("=" * 60)
    print("DATA QUALITY & MONITORING DASHBOARD")
    print("=" * 60)
    print(f"\n📊 System Health: {system_report['system_health'].upper()}")
    print(f"   Total Videos: {system_report['total_videos']}")
    print(f"   Average Completeness: {system_report['average_completeness']:.1%}")
    print(f"   Complete Videos: {system_report['complete_videos_percentage']:.1%}")
    
    # Volume metrics
    volume = system_report['volume_metrics']
    print(f"\n📈 Volume Metrics:")
    print(f"   Total Frames: {volume['total_frames']:,}")
    print(f"   Total Captions: {volume['total_captions']:,}")
    print(f"   Total Transcripts: {volume['total_transcripts']:,}")
    print(f"   Storage Used: {volume['storage_used_mb']:.1f} MB")
    print(f"   Growth Rate: {volume['growth_rate_videos_per_day']:.1f} videos/day")
    
    # Pipeline performance
    pipeline_stats = observability.latency_monitor.get_all_statistics()
    if pipeline_stats:
        print(f"\n⚡ Pipeline Performance:")
        for stage, stats in pipeline_stats.items():
            print(f"   {stage}: {stats['avg']:.2f}s avg ({stats['count']} runs)")
    
    # Recovery status
    recovery_dashboard = recovery.get_recovery_dashboard()
    print(f"\n🔧 Recovery Status:")
    print(f"   DLQ Size: {recovery_dashboard['dlq_size']}")
    print(f"   Reprocessing Candidates: {recovery_dashboard['reprocessing_candidates']}")
    
    print("\n" + "=" * 60)

# Run dashboard
print_monitoring_dashboard()
```

## Best Practices

### 1. Monitor Quality After Processing

```python
def process_video_with_monitoring(video_id: str):
    """Process video with quality monitoring."""
    observability = get_data_observability()
    metrics = get_quality_metrics()
    
    # Monitor processing
    with observability.latency_monitor.monitor_stage('video_processing', video_id):
        # Process video
        process_video(video_id)
    
    # Check quality
    report = metrics.get_quality_report(video_id)
    
    if report['quality_score'] < 70:
        logger.warning(f"Low quality for {video_id}: {report['quality_score']}/100")
        
        # Check what's missing
        if not report['completeness']['is_complete']:
            missing = report['completeness']['missing_data']
            logger.warning(f"Missing data: {', '.join(missing)}")
    
    return report
```

### 2. Use Automatic Retry for Transient Failures

```python
def extract_frames_with_retry(video_id: str):
    """Extract frames with automatic retry."""
    recovery = get_data_recovery()
    
    return recovery.retry.execute_with_retry(
        extract_frames,
        'frame_extraction',
        video_id
    )
```

### 3. Log All Data Mutations

```python
def save_context_with_logging(video_id: str, context_type: str, data: dict):
    """Save context with mutation logging."""
    observability = get_data_observability()
    
    # Save to database
    context_id = save_to_database(video_id, context_type, data)
    
    # Log mutation
    observability.mutation_logger.log_insert(
        'video_context',
        context_id,
        {'video_id': video_id, 'context_type': context_type}
    )
    
    return context_id
```

### 4. Regular Reconciliation

```python
def daily_reconciliation():
    """Run daily data reconciliation."""
    recovery = get_data_recovery()
    
    # Reconcile all videos
    summary = recovery.reconciliation.reconcile_all_videos()
    
    # Log results
    logger.info(f"Daily reconciliation completed:")
    logger.info(f"  Videos checked: {summary['total_videos']}")
    logger.info(f"  Issues found: {summary['total_issues']}")
    logger.info(f"  Fixes applied: {summary['total_fixes']}")
    
    return summary
```

## Troubleshooting

### Low Quality Score

If a video has a low quality score:

1. Check completeness: `report['completeness']['missing_data']`
2. Check freshness: `report['freshness']['age_hours']`
3. Check accuracy: `report['accuracy']['low_confidence_count']`
4. Reprocess if needed: `recovery.reprocessing.reprocess_video(video_id)`

### High DLQ Size

If the dead letter queue is growing:

1. Check DLQ items: `recovery.dlq.get_queue_items()`
2. Identify common failures: Group by operation
3. Fix root cause
4. Reprocess items: `recovery.reprocessing.reprocess_dlq_item(dlq_id)`

### Slow Pipeline

If pipeline performance degrades:

1. Check statistics: `observability.latency_monitor.get_all_statistics()`
2. Identify slow stages
3. Optimize bottlenecks
4. Monitor improvements

## Summary

The data quality and monitoring system provides:

- **Quality Metrics**: Track completeness, freshness, accuracy, and volume
- **Observability**: Full visibility into mutations, latency, and data flow
- **Recovery**: Automatic retry, DLQ, manual reprocessing, and reconciliation
- **Testing**: Comprehensive test framework for data integrity

Use these tools to ensure BRI maintains high data quality and reliability in production.
