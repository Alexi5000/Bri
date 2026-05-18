# Testing Guide

BRI separates fast production checks from heavy video and model tests so contributors can validate changes without requiring a GPU, Redis, uploaded media, or a live Groq key.

| Command | Purpose |
|---|---|
| `python scripts/validate_production.py` | Verifies production files, README graphics, configuration parsing, and fast contract tests. |
| `pytest tests/test_production_contract.py` | Runs the lightweight production-readiness contract tests. |
| `pytest tests/unit` | Runs pure unit tests for routing, memory, and tool logic. |
| `pytest tests/integration` | Runs service-level integration tests with mocked or synthetic media state. |
| `python scripts/smoke_api.py --url http://localhost:8000` | Checks a running API service health and tool registry. |

## Test environment

Use `ALLOW_MISSING_GROQ_FOR_TESTS=true` when running tests that import application configuration without a live model key. Production deployments should not enable that flag.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ALLOW_MISSING_GROQ_FOR_TESTS=true pytest tests/test_production_contract.py
```

## Heavy tests

Some existing tests exercise media extraction, transcription, object detection, vector search, or end-to-end video workflows. Treat those as local QA or CI jobs with explicit model/cache provisioning rather than required pre-commit checks.
