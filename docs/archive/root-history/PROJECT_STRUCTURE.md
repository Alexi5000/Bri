# BRI Project Structure

## Overview

This document describes the complete project structure after cleanup and organization (October 2025).

## Root Directory

```
bri-video-agent/
├── 📁 Core Application Files
│   ├── app.py                      # Main Streamlit application entry point
│   ├── config.py                   # Configuration management
│   ├── requirements.txt            # Python dependencies
│   └── .env.example               # Environment variable template
│
├── 📁 Docker Configuration
│   ├── docker-compose.yml         # Docker Compose configuration
│   ├── Dockerfile.mcp             # MCP server Docker image
│   ├── Dockerfile.ui              # Streamlit UI Docker image
│   └── .dockerignore              # Docker ignore patterns
│
├── 📁 Documentation
│   ├── README.md                  # Main project README
│   ├── INDEX.md                   # Documentation index
│   ├── FINAL_TASK_SUMMARY.md     # Complete task summary
│   └── TASK_EXECUTION_ORDER.md   # Task execution reference
│
└── 📁 Configuration Files
    ├── .env                       # Environment variables (gitignored)
    ├── .gitignore                 # Git ignore patterns
    └── .streamlit/                # Streamlit configuration
```

## Directory Structure

### `/data/` - Runtime Data (gitignored)

```
data/
├── bri.db                         # SQLite database
├── videos/                        # Uploaded video files
├── frames/                        # Extracted video frames
├── cache/                         # Processing cache
├── backups/                       # Database backups
│   ├── bri_backup_YYYYMMDD_HHMMSS.db
│   └── bri_backup_YYYYMMDD_HHMMSS.db.meta
└── evaluations/                   # Evaluation reports
    ├── eval_report_*.json
    └── evaluation_results/
```

### `/docs/` - Documentation

```
docs/
├── 📚 User Documentation
│   ├── USER_GUIDE.md              # Complete user guide
│   ├── QUICKSTART.md              # Quick start guide
│   ├── TROUBLESHOOTING.md         # Troubleshooting guide
│   └── CONFIGURATION.md           # Configuration reference
│
├── 📚 Deployment Documentation
│   ├── DEPLOYMENT.md              # Production deployment
│   ├── WINDOWS_DEPLOYMENT_GUIDE.md # Windows-specific deployment
│   └── START_BRI_WINDOWS.md       # Windows startup guide
│
├── 📚 Operations Documentation
│   ├── OPERATIONS_RUNBOOK.md      # Operations procedures
│   ├── PERFORMANCE_TUNING_GUIDE.md # Performance optimization
│   ├── ERROR_PATTERNS_SOLUTIONS.md # Common errors and fixes
│   ├── BACKUP_RESTORE_GUIDE.md    # Backup procedures
│   └── DATABASE_MANAGEMENT_GUIDE.md # Database maintenance
│
├── 📚 Developer Documentation
│   ├── API_EXAMPLES.md            # API usage examples
│   ├── DATA_FLOW_AUDIT.md         # Data flow documentation
│   └── VECTOR_SEARCH_INTEGRATION_GUIDE.md
│
├── 📚 Task Summaries
│   ├── TASK_40_SUMMARY.md         # Data persistence
│   ├── TASK_41_SUMMARY.md         # Data validation
│   ├── TASK_45_SUMMARY.md         # Database management
│   ├── TASK_46_SUMMARY.md         # API hardening
│   ├── TASK_47_SUMMARY.md         # Caching optimization
│   ├── TASK_48_SUMMARY.md         # Data quality
│   ├── TASK_49_IMPLEMENTATION_COMPLETE.md # Vector search
│   └── TASK_50_SUMMARY.md         # Production readiness
│
├── 📚 Integration Guides
│   ├── TASK_47_INTEGRATION_GUIDE.md
│   ├── DATA_QUALITY_INTEGRATION_GUIDE.md
│   ├── VECTOR_SEARCH_INTEGRATION_GUIDE.md
│   └── VECTOR_DB_EVALUATION.md
│
└── 📁 archive/                    # Archived documentation
    ├── ARCHITECTURE_ANALYSIS.md
    ├── DATA_ENGINEERING_ANALYSIS.md
    ├── EVALUATION_GUIDE.md
    ├── LOGGING_IMPLEMENTATION.md
    ├── PHASE5_SUMMARY.md
    ├── README_PHASE4.md
    ├── STYLING_IMPROVEMENTS.md
    ├── STYLING_TEST_CHECKLIST.md
    ├── TASK_ORDER_CHANGES.md
    ├── TEST_RESULTS.md
    ├── EXECUTE_THIS.md
    ├── EXECUTION_PLAN.md
    ├── LAYOUT_FIXES.md
    ├── QUICK_DATA_FIXES.md
    ├── analyze_failures.py
    └── analyze_passing.py
```

### `/logs/` - Application Logs (gitignored)

```
logs/
├── bri.log                        # General application logs
├── bri.log.YYYY-MM-DD             # Rotated logs
├── bri_errors.log                 # Error-only logs
├── bri_performance.log            # Performance metrics
├── bri_audit.log                  # Audit trail (90-day retention)
└── bri_pipeline.log               # Pipeline stage logs
```

### `/mcp_server/` - MCP Server

```
mcp_server/
├── main.py                        # FastAPI application
├── registry.py                    # Tool registry
├── cache.py                       # Redis caching layer
├── middleware.py                  # Request/response middleware
├── validation.py                  # Request validation
├── response_models.py             # Response schemas
├── versioning.py                  # API versioning
├── circuit_breaker.py             # Circuit breaker pattern
└── README.md                      # MCP server documentation
```

### `/models/` - Data Models

```
models/
├── video.py                       # Video, VideoMetadata, Frame models
├── memory.py                      # MemoryRecord model
├── responses.py                   # AssistantMessageResponse, UserQuery
├── tools.py                       # Tool-related models
└── yolov8n.pt                     # YOLO model weights
```

### `/scripts/` - Utility Scripts

```
scripts/
├── 🔧 Setup & Initialization
│   ├── init_db.py                 # Initialize database
│   └── validate_setup.py          # Validate installation
│
├── 🔧 Database Management
│   ├── backup_database.py         # Create database backup
│   ├── restore_database.py        # Restore from backup
│   ├── verify_backups.py          # Verify backup integrity
│   ├── migrate_db.py              # Database migrations
│   └── archival_cli.py            # Archive old data
│
├── 🔧 Monitoring & Health
│   ├── health_check.py            # System health check
│   └── test_vector_search.py     # Test vector search
│
├── 🔧 Testing Scripts
│   ├── test_task_41_validation.py
│   ├── test_task_46_api_hardening.py
│   ├── test_task_47_caching_optimization.py
│   └── test_data_persistence.py
│
└── 📁 utils/                      # Utility scripts
    ├── check_video_context.py     # Check video context data
    ├── check_videos.py            # Check video records
    ├── diagnose_system.py         # System diagnostics
    ├── get_videos.py              # Get video information
    ├── list_videos.py             # List all videos
    ├── process_test_video.py      # Process test video
    └── quick_fix.py               # Quick fixes
```

### `/services/` - Business Logic

```
services/
├── 🧠 Core Services
│   ├── agent.py                   # GroqAgent - main conversational agent
│   ├── router.py                  # ToolRouter - query analysis
│   ├── memory.py                  # Memory - conversation history
│   ├── context.py                 # ContextBuilder - video data aggregation
│   └── error_handler.py           # ErrorHandler - friendly errors
│
├── 🎥 Video Processing
│   └── video_processing_service.py # Video processing orchestration
│
├── 💾 Data Management
│   ├── data_validator.py          # Data validation
│   ├── data_consistency_checker.py # Consistency checks
│   ├── data_lineage_tracker.py    # Data lineage tracking
│   ├── data_quality_metrics.py    # Data quality metrics
│   ├── data_observability.py      # Data observability
│   ├── data_recovery.py           # Data recovery
│   └── data_prefetcher.py         # Data prefetching
│
├── 🔍 Search & Retrieval
│   ├── semantic_search.py         # Semantic search
│   ├── embedding_pipeline.py      # Embedding generation
│   ├── vector_search_optimizer.py # Vector search optimization
│   └── README_VECTOR_SEARCH.md    # Vector search documentation
│
└── 🛡️ Reliability
    └── graceful_degradation.py    # Graceful degradation service
```

### `/storage/` - Storage Layer

```
storage/
├── 📊 Database
│   ├── database.py                # SQLite connection and queries
│   ├── schema.sql                 # Database schema definition
│   ├── migrations.py              # Database migrations
│   └── health_monitor.py          # Database health monitoring
│
├── 💾 Backup & Recovery
│   ├── backup.py                  # Backup/restore functionality
│   └── archival.py                # Data archival
│
├── 🗄️ File Storage
│   ├── file_store.py              # File system operations
│   └── compression.py             # Data compression
│
└── ⚡ Performance
    ├── query_optimizer.py         # Query optimization
    └── multi_tier_cache.py        # Multi-tier caching
```

### `/tests/` - Test Suite

```
tests/
├── unit/                          # Unit tests
│   ├── test_memory.py
│   ├── test_frame_extractor.py
│   ├── test_captioner.py
│   ├── test_transcriber.py
│   ├── test_detector.py
│   └── test_router.py
│
├── integration/                   # Integration tests
│   ├── test_e2e_flow.py
│   └── test_error_handling.py
│
├── test_data_quality.py          # Data quality tests
└── fixtures/                      # Test data
```

### `/tools/` - Video Processing Tools

```
tools/
├── frame_extractor.py             # OpenCV frame extraction
├── image_captioner.py             # BLIP image captioning
├── audio_transcriber.py           # Whisper audio transcription
└── object_detector.py             # YOLO object detection
```

### `/ui/` - Streamlit UI Components

```
ui/
├── welcome.py                     # Welcome screen
├── library.py                     # Video library view
├── chat.py                        # Chat interface
├── player.py                      # Video player with timestamp navigation
├── styles.py                      # Custom CSS and styling
└── logging_dashboard.py           # Logging dashboard
```

### `/utils/` - Utilities

```
utils/
├── logging_config.py              # Logging configuration
└── metrics_logger.py              # Operational metrics logging
```

### `/.kiro/` - Kiro IDE Configuration

```
.kiro/
├── specs/                         # Project specifications
│   └── bri-video-agent/
│       ├── requirements.md        # Feature requirements
│       ├── design.md              # System design
│       └── tasks.md               # Implementation tasks
│
├── steering/                      # AI assistant guidance
│   ├── product.md                 # Product overview
│   ├── structure.md               # Project structure
│   └── tech.md                    # Technology stack
│
└── settings/                      # IDE settings
```

## File Naming Conventions

### Python Files
- **snake_case**: `frame_extractor.py`, `video_processing_service.py`
- **Classes**: PascalCase (e.g., `FrameExtractor`, `VideoProcessingService`)
- **Functions**: snake_case (e.g., `extract_frames`, `process_video`)

### Documentation Files
- **UPPERCASE**: `README.md`, `DEPLOYMENT.md`
- **Task summaries**: `TASK_XX_SUMMARY.md`
- **Guides**: `*_GUIDE.md`

### Database Files
- **Lowercase with extension**: `bri.db`
- **Backups**: `bri_backup_YYYYMMDD_HHMMSS.db`

### Log Files
- **Lowercase with extension**: `bri.log`, `bri_errors.log`
- **Rotated**: `bri.log.YYYY-MM-DD`

## Key Design Patterns

### Layered Architecture
```
UI Layer → Agent Layer → MCP Server → Tools → Storage
```

### Separation of Concerns
- **Models**: Data structures only
- **Services**: Business logic
- **Storage**: Data persistence
- **Tools**: Video processing
- **UI**: User interface

### Configuration Management
- All configuration in `.env` file
- Validated on startup
- Defaults for optional settings

### Error Handling
- Graceful degradation
- Friendly error messages
- Comprehensive logging

## Development Workflow

### Adding New Features

1. **Update Requirements**: `.kiro/specs/bri-video-agent/requirements.md`
2. **Update Design**: `.kiro/specs/bri-video-agent/design.md`
3. **Add Tasks**: `.kiro/specs/bri-video-agent/tasks.md`
4. **Implement**: Create/modify files in appropriate directories
5. **Test**: Add tests in `/tests/`
6. **Document**: Update relevant documentation

### File Placement Guidelines

- **New model**: `/models/`
- **New service**: `/services/`
- **New tool**: `/tools/`
- **New UI component**: `/ui/`
- **New script**: `/scripts/`
- **New storage logic**: `/storage/`
- **New documentation**: `/docs/`
- **New test**: `/tests/`

## Maintenance

### Regular Cleanup

- **Logs**: Rotated daily, 30-day retention
- **Backups**: 30-day retention (automated cleanup)
- **Cache**: Cleared on restart or manually
- **Old videos**: Archive after 90 days (optional)

### Documentation Updates

- Update README.md for major changes
- Update relevant guides in `/docs/`
- Create task summaries for completed tasks
- Archive obsolete documentation to `/docs/archive/`

## Summary

The BRI project structure is organized into clear, logical directories:

- **Root**: Core application files and configuration
- **`/data/`**: Runtime data (gitignored)
- **`/docs/`**: All documentation
- **`/logs/`**: Application logs (gitignored)
- **`/mcp_server/`**: API server
- **`/models/`**: Data models
- **`/scripts/`**: Utility scripts
- **`/services/`**: Business logic
- **`/storage/`**: Data persistence
- **`/tests/`**: Test suite
- **`/tools/`**: Video processing
- **`/ui/`**: User interface
- **`/utils/`**: Utilities

This structure promotes:
- ✅ Clear separation of concerns
- ✅ Easy navigation
- ✅ Maintainability
- ✅ Scalability
- ✅ Testability

For questions about where to place new code, refer to the "File Placement Guidelines" section above.
