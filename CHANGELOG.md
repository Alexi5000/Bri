# Changelog

All notable changes to BRI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `services.errors.BriError` hierarchy with HTTP-status mapping and a FastAPI
  exception handler that returns a JSON envelope for any BriError subclass.
- 13 domain exceptions migrated to subclass BriError while preserving their
  identity for backward-compatible `except` clauses.
- `services.errors.http_status_for()` mapping BriError category to HTTP code.
- `py.typed` marker on the package.
- Per-module strict `mypy` configuration in `pyproject.toml`.
- `services/errors.py` and `mcp_server/response_models.py` are strict-clean.
- `hypothesis` and `syrupy` dev extras.
- Property-based tests for `BriError` invariants and Pydantic model round-trips.
- Snapshot tests locking the JSON envelope of every public response model.
- Contract tests against the live FastAPI app via `TestClient` (no Docker, no network).
- `mkdocs.yml` config + `mkdocs-material` theme + auto-generated API reference.
- `scripts/build_api_reference.py` to populate `docs/reference/<package>/<module>.md`.
- `.editorconfig`, `.gitattributes` with `linguist-generated` markers, `CODEOWNERS`.
- `assets/icon.svg`, `assets/cover.svg`, `docs/styles/palette.css`.
- `docs/README_TEMPLATE.md` describing the canonical 11-section README layout.
- `CONTRIBUTING.md`, `SECURITY.md`, `GOVERNANCE.md`, `MAINTAINERS.md`.
- `CODE_OF_CONDUCT.md` based on Contributor Covenant v2.1.
- Issue templates (`.github/ISSUE_TEMPLATE/bug.yml`, `feature.yml`, `question.yml`).
- Pull request template (`.github/PULL_REQUEST_TEMPLATE.md`).
- `cliff.toml` configuration for git-cliff release notes.

### Changed
- `get_config_value` in `config.py` now consults environment variables first
  and only falls back to Streamlit secrets when running inside a Streamlit
  runtime (detected via `STREAMLIT_RUNTIME_SCRIPT`). This makes
  `monkeypatch.setenv` reliable in tests.
- The `config` ↔ `utils.logging_config` circular import is broken by lazy
  imports inside both modules. Pytest collection went from 177 tests with
  16 errors to 425 tests with 0 errors.
- `MediaUtils.format_timestamp` drops leading zeros on minutes and hours
  so casual timestamps read `0:42` and `1:01:01`.
- `FileStore.SUPPORTED_VIDEO_FORMATS` includes `.mpeg`.
- `VideoProcessingService.verify_video_data` is exposed as an alias for
  `verify_video_data_completeness` and returns a per-category `complete` flag.
- `services.router.ToolRouter` recognises `the <noun>` as an object hint and
  adds a multi-tool path for audio queries that also name an object.
- `pyproject.toml` widens pytest `testpaths` from `["tests/production"]` to
  `["tests"]` so the full suite is collected by default.
- `[tool.coverage.run].source` now includes `tools` and `ui` so coverage
  reports cover the whole runtime surface.
- `README.md` rewritten to the canonical 11-section template with raster
  fallbacks for the brand assets and a Quality bar / Uncle Bob section.
- Logger calls across `mcp_server/cache.py`, `mcp_server/circuit_breaker.py`,
  `mcp_server/main.py`, `services/context.py`, and `services/memory.py`
  converted from f-strings to lazy `%-format` to match Python logging idiom.
- Stray `print()` calls in `config.py` and `tools/image_captioner.py`
  replaced with `logger.warning` / `logger.info`; module-level loggers
  added where missing.

### Fixed
- 11 pre-existing test failures across `tests/unit/test_router.py`,
  `tests/production/test_config_validation.py`,
  `tests/test_data_completeness.py`, `tests/test_frontend_complete.py`,
  `tests/test_e2e_real_video.py`, and the production contract suite.
- Three new tests in `tests/production/` were promoted from skip to passing
  by adding the missing `quality bar` section and PNG-fallback assets to
  `README.md`.

### Removed
- ~70 orphan task summaries, per-task implementation notes, and the lower-case
  `docs/task_*.md` family moved to `docs/archive/tasks/`, `docs/archive/`,
  and `docs/archive/summaries/` (preserved in git history, no destructive
  deletes).
- 32 legacy `scripts/test_*.py` smoke scripts moved to
  `scripts/archive/legacy_tests/`.
- 6 `scripts/{apply,patch,demo}_*.py` one-off patch scripts moved to
  `scripts/archive/builds/`.

## [1.0.0] - 2025-10-16

Initial public release: Streamlit UI, FastAPI MCP server, SQLite persistence,
optional BLIP / Whisper / YOLOv8 multimodal tools, Groq-backed conversational
agent with per-video memory. Production hardening, structured logging, and
Uncle Bob clean-code review applied across the codebase.

## [1.1.0] - 2026-07-09

Open-source flagship release. CI green, contributor experience polished,
distribution channels wired.

### Added
- Continuous integration: `ci.yml` matrix (ubuntu + windows × py3.11 + 3.12),
  `docs.yml` (markdownlint + lychee + mkdocs preview), `release.yml`
  (multi-arch GHCR with SBOM), `codeql.yml`, `dependabot.yml`.
- Design system: vector `assets/icon.svg` and `cover.svg`, `docs/styles/palette.css`,
  `.editorconfig`, `.gitattributes` with `linguist-generated` markers, `.github/CODEOWNERS`.
- `BriError` hierarchy under `services/errors.py` with `HTTP_STATUS` mapping and
  a FastAPI exception handler that returns a JSON envelope.
- 13 domain exceptions migrated to subclass BriError.
- `py.typed` marker; per-module strict `mypy` overrides.
- Property-based (Hypothesis) tests for public validators and Pydantic round-trips.
- Snapshot (syrupy) tests for every public response envelope.
- Contract tests against the live FastAPI app via `TestClient`.
- mkdocs-material docs site with auto-generated API reference via mkdocstrings.
- `scripts/build_api_reference.py` to generate per-module reference stubs.
- CLI entry points: `bri-video-agent`, `bri-mcp`, `bri-ui`.
- `docker-compose.prod.yml` overlay that pulls published GHCR images.
- Community files: `CONTRIBUTING.md`, `SECURITY.md`, `GOVERNANCE.md`,
  `MAINTAINERS.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `cliff.toml`.
- Issue and PR templates under `.github/ISSUE_TEMPLATE/` and
  `.github/PULL_REQUEST_TEMPLATE.md`.

### Changed
- `config.py` consults environment variables first; only falls back to
  Streamlit secrets when running inside a Streamlit runtime.
- The `config` ↔ `utils.logging_config` circular import is broken by lazy
  imports in both modules.
- `MediaUtils.format_timestamp` drops leading zeros on minutes and hours.
- `FileStore.SUPPORTED_VIDEO_FORMATS` includes `.mpeg`.
- `VideoProcessingService.verify_video_data` returns a per-category `complete` flag.
- `services.router.ToolRouter` recognises `the <noun>` as an object hint and
  adds a multi-tool path for audio queries that also name an object.
- `pyproject.toml` widens pytest `testpaths` from `["tests/production"]` to `["tests"]`.
- `[tool.coverage.run].source` includes `tools` and `ui`.
- `README.md` rewritten to the canonical 11-section template with raster
  fallbacks and a Quality bar / Uncle Bob section.
- Logger calls across five modules converted from f-strings to lazy `%-format`.
- Stray `print()` calls in `config.py` and `tools/image_captioner.py` replaced
  with proper logger calls.

### Fixed
- 11 pre-existing test failures across router, config-validation,
  data-completeness, frontend, and e2e suites brought to passing.
- Three production-contract tests promoted from skip to passing by adding
  the missing Quality bar section and raster PNG fallbacks to `README.md`.

### Removed
- ~70 orphan task summaries and the lowercase `docs/task_*.md` family moved
  to `docs/archive/tasks/`, `docs/archive/`, and `docs/archive/summaries/`.
- 32 legacy `scripts/test_*.py` smoke scripts moved to `scripts/archive/legacy_tests/`.
- 6 `scripts/{apply,patch,demo}_*.py` one-off patch scripts moved to `scripts/archive/builds/`.

### Security
- Streamlit secrets are now only consulted when `STREAMLIT_RUNTIME_SCRIPT` is set,
  preventing local `secrets.toml` from leaking into tests and CI.