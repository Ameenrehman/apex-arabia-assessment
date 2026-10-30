"""Automated Check 4: Schema Input Validation & Bad Request Handling."""



def test_reject_missing_required_fields(client):
    """Verifies that requests missing required fields are rejected with 422 Unprocessable Entity."""
    # Missing 'service_name'
    payload = {"title": "Deploy Cluster"}
    response = client.post("/api/v1/operations", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_reject_invalid_title_length(client):
    """Verifies that titles shorter than min_length (3 chars) are rejected."""
    payload = {"title": "ab", "service_name": "apex-auth"}
    response = client.post("/api/v1/operations", json=payload)

    assert response.status_code == 422
