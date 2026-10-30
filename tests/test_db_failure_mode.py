"""Automated Check 5: Readiness Probe Database Failure Mode."""

from unittest.mock import patch

from fastapi import status


def test_readiness_probe_returns_503_when_database_disconnected(client):
    """Verifies that /health/ready returns HTTP 503 Service Unavailable

    and structured error details when database connectivity is severed.
    This ensures load balancers immediately stop routing traffic to an unhealthy node.
    """
    with patch("app.routers.health.check_database_connection", return_value=False):
        response = client.get("/health/ready")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["database"] == "disconnected"
    assert "timestamp" in data
