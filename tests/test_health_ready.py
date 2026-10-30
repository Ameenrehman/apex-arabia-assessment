"""Automated Check 2: Readiness Probe Validation (Healthy Database)."""

from unittest.mock import patch

from fastapi import status


def test_readiness_probe_healthy_database(client):
    """Verifies that /health/ready returns HTTP 200 and 'ready' status

    when the persistent database connection check succeeds.
    """
    with patch("app.routers.health.check_database_connection", return_value=True):
        response = client.get("/health/ready")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert "x-request-id" in response.headers
