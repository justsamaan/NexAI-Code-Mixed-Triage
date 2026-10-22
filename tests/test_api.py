"""
Integration tests for RESTful API endpoints.
"""

import json
import pytest
from src.api import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True


def test_triage_api_success(client):
    payload = {
        "raw_text": "Mera order #ORD-1120 kab deliver hoga please batayein",
        "save_to_db": False
    }
    res = client.post("/api/triage", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "intent" in data
    assert "urgency" in data
    assert "escalation" in data
    assert "reply_draft" in data
    assert data["intent"]["label"] in ("track_order", "delivery_period")


def test_triage_api_empty_error(client):
    res = client.post("/api/triage", json={"raw_text": ""})
    assert res.status_code == 400
    data = res.get_json()
    assert "Missing 'raw_text'" in data["message"]


def test_list_and_patch_ticket_api(client):
    # Create a ticket
    triage_res = client.post("/api/triage", json={
        "raw_text": "Indha order #ORD-TEST-99 cancel pannunga",
        "save_to_db": True
    })
    ticket_id = triage_res.get_json()["ticket_id"]

    # Retrieve ticket
    get_res = client.get(f"/api/tickets/{ticket_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["id"] == ticket_id

    # Patch ticket
    patch_res = client.patch(f"/api/tickets/{ticket_id}", json={
        "status": "approved",
        "agent_response": "Cancellation approved and verified by agent."
    })
    assert patch_res.status_code == 200

    # Verify metrics endpoint
    metrics_res = client.get("/api/metrics")
    assert metrics_res.status_code == 200
    assert metrics_res.get_json()["total_tickets"] >= 1
