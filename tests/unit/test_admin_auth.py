from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_client(monkeypatch):
    from mcp_server import main

    client = TestClient(main.app)
    effect = Mock(return_value=True)
    monkeypatch.setattr(main.cache_manager, "clear_all", effect)
    return client, effect


@pytest.mark.parametrize("configured", [None, "", "short"])
def test_admin_disabled_without_strong_configuration(monkeypatch, admin_client, configured):
    client, effect = admin_client
    if configured is None:
        monkeypatch.delenv("BRI_ADMIN_TOKEN", raising=False)
    else:
        monkeypatch.setenv("BRI_ADMIN_TOKEN", configured)
    response = client.delete("/cache", headers={"Authorization": "Bearer short"})
    assert response.status_code == 503
    effect.assert_not_called()


@pytest.mark.parametrize("authorization", ["", "Bearer wrong", "Basic " + "x" * 32])
def test_admin_denies_invalid_credentials(monkeypatch, admin_client, authorization):
    client, effect = admin_client
    monkeypatch.setenv("BRI_ADMIN_TOKEN", "x" * 32)
    response = client.delete("/cache", headers={"Authorization": authorization})
    assert response.status_code == 401
    effect.assert_not_called()


def test_authorized_admin_keeps_operation(monkeypatch, admin_client):
    client, effect = admin_client
    monkeypatch.setenv("BRI_ADMIN_TOKEN", "x" * 32)
    response = client.delete("/cache", headers={"Authorization": "Bearer " + "x" * 32})
    assert response.status_code == 200
    effect.assert_called_once_with()


@pytest.mark.parametrize(
    "method,path", [("delete", "/cache/videos/1"), ("post", "/circuit-breakers/cache/reset")]
)
def test_adjacent_admin_routes_are_protected(monkeypatch, admin_client, method, path):
    client, _ = admin_client
    monkeypatch.setenv("BRI_ADMIN_TOKEN", "x" * 32)
    assert client.request(method, path).status_code == 401
