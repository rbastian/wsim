"""Tests for FastAPI application."""

from fastapi.testclient import TestClient

from wsim_api.main import app

client = TestClient(app)


def test_root() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Wooden Ships & Iron Men API"
    assert data["version"] == "0.1.0"


def test_health() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
