import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ogi.config import settings


@pytest.fixture()
def test_app(monkeypatch):
    monkeypatch.setattr(settings, "local_api_key", "test-secret-key")
    # Import here so the middleware sees the patched settings
    from ogi.api.middleware import ApiKeyMiddleware

    app = FastAPI()
    app.add_middleware(ApiKeyMiddleware)

    @app.get("/api/v1/projects")
    def projects():
        return {"projects": []}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


@pytest.fixture()
def client(test_app):
    return TestClient(test_app, raise_server_exceptions=False)


def test_request_without_key_returns_401(client):
    response = client.get("/api/v1/projects")
    assert response.status_code == 401


def test_request_with_wrong_key_returns_401(client):
    response = client.get(
        "/api/v1/projects", headers={"Authorization": "Bearer wrong-key"}
    )
    assert response.status_code == 401


def test_request_with_correct_key_passes(client):
    response = client.get(
        "/api/v1/projects", headers={"Authorization": "Bearer test-secret-key"}
    )
    assert response.status_code == 200


def test_health_endpoint_exempt_from_auth(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_missing_and_wrong_key_return_identical_responses(client):
    """Missing and wrong keys must return identical responses — no info leakage."""
    missing = client.get("/api/v1/projects")
    wrong = client.get(
        "/api/v1/projects", headers={"Authorization": "Bearer wrong"}
    )
    assert missing.status_code == wrong.status_code
    assert missing.json() == wrong.json()
