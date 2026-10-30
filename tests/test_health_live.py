"""Automated Check 1: Liveness Probe Validation."""

from fastapi import status


def test_liveness_probe_returns_ok(client):
    """Verifies that the /health/live endpoint returns HTTP 200 and 'alive' status,

    proving the application process is running and responding to HTTP requests.
    """
    response = client.get("/health/live")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "alive"
    assert "version" in data
    assert "timestamp" in data
    # Verify correlation ID middleware header is present
    assert "x-request-id" in response.headers
