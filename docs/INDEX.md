# BRI Documentation Index

BRI’s documentation is organized around production use, API integration, operations, and long-term maintainability. The repository root is intentionally kept clean: `README.md` is the public entry point, runtime code lives in top-level Python packages, operational scripts live under `scripts/`, and historical build notes are preserved under `docs/archive/root-history/` for auditability.

## Primary documentation

| Audience | Document | Purpose |
|---|---|---|
| Product evaluators and new users | [Project README](../README.md) | Explains the product, architecture, quick start flow, and production validation commands. |
| First-time operators | [Quickstart](QUICKSTART.md) | Provides the shortest path to running BRI locally. |
| End users | [User Guide](USER_GUIDE.md) | Describes upload, library, playback, and conversational video workflows. |
| API integrators | [API Reference](API.md) | Documents the FastAPI MCP service, response envelopes, endpoints, and tool contracts. |
| API integrators | [API Examples](API_EXAMPLES.md) | Provides practical request examples for automation and integration work. |
| System administrators | [Configuration](CONFIGURATION.md) | Explains environment variables, secrets, runtime paths, and environment-specific settings. |
| Platform operators | [Deployment](DEPLOYMENT.md) | Covers production deployment patterns, Docker usage, and environment setup. |
| Platform operators | [Operations Runbook](OPERATIONS_RUNBOOK.md) | Defines routine operational checks, recovery steps, and maintenance procedures. |
| Developers and release owners | [Testing](TESTING.md) | Describes deterministic production contract tests and validation workflows. |
| Support and maintainers | [Troubleshooting](TROUBLESHOOTING.md) | Provides diagnosis guidance for installation, runtime, API, and processing issues. |

## Architecture and implementation references

| Topic | Document | Notes |
|---|---|---|
| System architecture | [Architecture](ARCHITECTURE.md) | Primary architecture document for runtime components and integration boundaries. |
| Database operations | [Database Management Guide](DATABASE_MANAGEMENT_GUIDE.md) | SQLite lifecycle, records, backups, and operational care. |
| Backup and recovery | [Backup and Restore Guide](BACKUP_RESTORE_GUIDE.md) | Practical backup and restore procedures. |
| Data quality | [Data Quality Integration Guide](DATA_QUALITY_INTEGRATION_GUIDE.md) | Guidance for validating context quality and processing outputs. |
| Performance | [Performance Tuning Guide](PERFORMANCE_TUNING_GUIDE.md) | Runtime tuning and resource considerations. |
| Error handling | [Error Patterns and Solutions](ERROR_PATTERNS_SOLUTIONS.md) | Known failure modes and remediation patterns. |
| AI assistant context | [AI Contributor Guide](ai/CLAUDE.md) | Preserved guidance from the former assistant branch, moved out of the root for cleanliness. |

## Repository layout

The cleaned root keeps the files that are expected in a production Python application while moving generated, historical, and workflow-specific materials into dedicated folders. Hidden workspace folders such as `.kiro`, `.devcontainer`, `.streamlit`, and cache directories are excluded from source control.

| Path | Responsibility |
|---|---|
| `README.md` | Public project overview and quick start. |
| `app.py` and `config.py` | Streamlit entry point and runtime configuration. |
| `mcp_server/` | FastAPI MCP service, middleware, registry, and API routing. |
| `services/`, `tools/`, `storage/`, `models/`, `utils/`, `ui/` | Application domain packages. |
| `scripts/` | Validation, smoke testing, database initialization, cleanup generators, and deployment helpers. |
| `scripts/deployment/` | Legacy shell and Windows deployment helpers moved out of the root. |
| `scripts/archive/` | Historical one-off verification scripts retained for auditability. |
| `tests/` | Production, integration, unit, and utility tests. |
| `docs/` | Enterprise documentation and operational references. |
| `docs/archive/root-history/` | Historical root-level markdown reports moved out of the root without losing traceability. |
| `assets/` | Committed product graphics used by the README. |

## Production validation commands

| Command | Expected result |
|---|---|
| `APP_ENV=test ALLOW_MISSING_GROQ_FOR_TESTS=true python3 -m pytest tests/production -q` | Runs deterministic production tests for API, configuration, storage, and service boundaries. |
| `APP_ENV=test ALLOW_MISSING_GROQ_FOR_TESTS=true python3 scripts/smoke_api.py` | Verifies in-process API health and tool discovery. |
| `APP_ENV=test ALLOW_MISSING_GROQ_FOR_TESTS=true python3 scripts/validate_production.py` | Runs repository-level production-readiness checks. |
| `git diff --check` | Confirms there are no whitespace errors in the working tree. |

## Historical archive policy

Historical implementation notes remain available so future maintainers can trace how the app evolved, but they are intentionally separated from the root-level production surface. The archive is not the source of truth for current operations; use the primary documentation table above for production setup, deployment, and validation.

## Maintenance guidance

When adding or updating documentation, keep operational instructions in the primary documents, place transient build notes in `docs/archive/`, update this index when new long-lived documents are introduced, and verify commands before publishing them. The default production branch is `master`, and the remote repository has been consolidated so `origin/master` is the single branch of record.
