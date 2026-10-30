"""Automated Check 3: Operations API CRUD Workflow Validation."""

from fastapi import status


def test_create_and_retrieve_operation_task(client):
    """Verifies complete lifecycle of creating and retrieving an operation task."""
    payload = {
        "title": "Run Security Vulnerability Scan",
        "service_name": "apex-core-api",
        "environment": "staging",
        "status": "pending",
    }

    # 1. Create task
    create_resp = client.post("/api/v1/operations", json=payload)
    assert create_resp.status_code == status.HTTP_201_CREATED
    created_task = create_resp.json()
    assert created_task["title"] == payload["title"]
    assert created_task["service_name"] == payload["service_name"]
    assert created_task["id"] is not None

    task_id = created_task["id"]

    # 2. Retrieve task by ID
    get_resp = client.get(f"/api/v1/operations/{task_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["id"] == task_id

    # 3. List tasks
    list_resp = client.get("/api/v1/operations")
    assert list_resp.status_code == status.HTTP_200_OK
    items = list_resp.json()
    assert any(item["id"] == task_id for item in items)


def test_get_nonexistent_task_returns_404(client):
    """Verifies that requesting an invalid task ID returns a clean 404 Not Found."""
    response = client.get("/api/v1/operations/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
