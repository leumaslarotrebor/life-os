"""
Tests for GET /health.

Verifies:
- endpoint returns HTTP 200
- response contains status: ok
- response identifies the LIFE OS backend
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_is_ok():
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_identifies_service():
    response = client.get("/health")
    data = response.json()
    assert data["service"] == "life-os-backend"
