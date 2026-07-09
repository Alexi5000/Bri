.PHONY: install install-dev lock init-db run-ui run-api test test-core test-fast validate smoke clean docs

install:
	python -m pip install -r requirements.lock.txt

install-dev:
	python -m pip install -e .[dev]
	python -m pip install pip-tools

lock:
	python -m piptools compile --quiet --strip-extras --output-file=requirements.lock.txt pyproject.toml

init-db:
	python scripts/init_db.py

run-ui:
	streamlit run app.py

run-api:
	uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000

test:
	pytest

# Fast lane: unit + production contract suites only. Target: < 60 seconds.
test-fast:
	pytest tests/unit tests/production -q

test-core:
	pytest tests/unit/test_router.py tests/unit/test_memory.py tests/test_production_contract.py

# Full CI lane: matrix lint + type + test + compose.
ci: lint type test compose-validate compose-build
	@echo "All CI checks passed."

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .

type:
	mypy mcp_server services tools storage ui models || true
	@echo "Note: mypy is advisory until modules are fully annotated."

compose-validate:
	docker compose config --quiet

compose-build:
	docker build -f Dockerfile.mcp -t bri-mcp:ci .
	docker build -f Dockerfile.ui -t bri-ui:ci .

validate:
	python scripts/validate_production.py

smoke:
	python scripts/smoke_api.py --url http://localhost:8000 --allow-offline

docs:
	python scripts/build_api_reference.py
	python -m mkdocs build

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache .hypothesis .coverage coverage.xml htmlcov site