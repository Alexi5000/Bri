from unittest.mock import Mock

from mcp_server.cache import CacheManager


def test_cache_statistics_do_not_expose_backend_exception():
    manager = CacheManager.__new__(CacheManager)
    manager.enabled = True
    manager.redis_client = Mock()
    manager.redis_client.scan_iter.side_effect = RuntimeError(
        "redis://user:private-password@internal-host:6379 failed"
    )

    result = manager.get_stats()

    assert result == {"enabled": True, "error": "Cache statistics unavailable"}
    assert "private-password" not in str(result)


def test_disabled_cache_preserves_statistics_response():
    manager = CacheManager.__new__(CacheManager)
    manager.enabled = False
    manager.redis_client = None

    assert manager.get_stats() == {"enabled": False, "total_keys": 0}


def test_unhandled_api_exception_does_not_expose_backend_details():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from mcp_server.main import global_exception_handler

    app = FastAPI()
    app.add_exception_handler(Exception, global_exception_handler)

    @app.get("/failure")
    async def fail():
        raise RuntimeError("postgres://admin:private-password@internal-host/database")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure")

    assert response.status_code == 500
    assert response.json() == {
        "status": "error",
        "detail": "An unexpected error occurred",
        "error": "Internal server error",
    }
    assert "private-password" not in response.text
    assert "internal-host" not in response.text
