.PHONY: install install-dev init-db run-ui run-api test test-core validate smoke clean

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -e .[dev]

init-db:
	python scripts/init_db.py

run-ui:
	streamlit run app.py

run-api:
	uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000

test:
	pytest

test-core:
	pytest tests/unit/test_router.py tests/unit/test_memory.py tests/test_production_contract.py

validate:
	python scripts/validate_production.py

smoke:
	python scripts/smoke_api.py --url http://localhost:8000 --allow-offline

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
