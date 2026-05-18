# Bri Test Strategy

Bri uses a tiered test strategy so the default suite is reliable in CI while the
media and model workflows can still be exercised in fully provisioned developer
environments.

| Suite | Command | Purpose |
| --- | --- | --- |
| Production contract | `pytest` | Fast checks for configuration, API contracts, storage, docs, and deterministic AI fallback behavior. |
| Smoke validation | `python scripts/smoke_api.py` | In-process FastAPI smoke check with no network dependency. |
| Production readiness | `python scripts/validate_production.py` | Required-file, README graphics, and contract-test validation for release gates. |
| Extended media tests | `pytest tests/unit tests/integration -m "slow or integration"` | Optional video, model, and dependency-heavy coverage for environments with OpenCV, Whisper, Torch, and model assets installed. |

The default `pytest` command intentionally points at `tests/production`. Legacy
media tests remain available, but they are not part of the release gate because
they require large optional dependencies and local model downloads.
