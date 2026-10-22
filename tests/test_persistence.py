"""
Unit tests for SQLite database persistence, audit logging, and metric aggregation.
"""

import pytest
from src.config import TicketStatus, UrgencyLevel
from src.persistence import (
    get_dashboard_metrics,
    get_ticket,
    init_db,
    list_tickets,
    save_ticket,
    update_ticket_status,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_save_and_retrieve_ticket():
    ticket_payload = {
        "raw_text": "Mera order tracking status kahan hai #ORD-TEST-1",
        "cleaned_text": "Mera order tracking status kahan hai #ORD-TEST-1",
        "language_detected": "hinglish",
        "language_confidence": 0.90,
        "predicted_intent": "track_order",
        "intent_category": "ORDER",
        "intent_confidence": 0.88,
        "intent_margin": 0.40,
        "urgency_level": UrgencyLevel.NORMAL,
        "urgency_score": 0.50,
        "urgency_reasons": ["standard_queue"],
        "escalate_to_human": False,
        "escalation_priority": "P3-ROUTINE",
        "escalation_reason": "none",
        "reply_draft": "Tracking status being checked.",
        "status": TicketStatus.PENDING_REVIEW
    }

    ticket_id = save_ticket(ticket_payload)
    assert ticket_id.startswith("TCK-")

    retrieved = get_ticket(ticket_id)
    assert retrieved is not None
    assert retrieved["predicted_intent"] == "track_order"
    assert retrieved["language_detected"] == "hinglish"
    assert len(retrieved["audit_logs"]) >= 1
    assert retrieved["audit_logs"][0]["action"] == "TICKET_CREATED"


def test_update_ticket_status_and_audit():
    ticket_payload = {
        "raw_text": "Ennoda return pickup pannunga #REF-TEST-2",
        "language_detected": "tanglish",
        "predicted_intent": "get_refund",
        "intent_category": "REFUND",
        "urgency_level": UrgencyLevel.NORMAL,
        "reply_draft": "Draft reply",
        "status": TicketStatus.PENDING_REVIEW
    }
    tid = save_ticket(ticket_payload)

    success = update_ticket_status(
        ticket_id=tid,
        new_status=TicketStatus.APPROVED,
        agent_response="Approved by agent #42",
        actor="lead_agent_priya"
    )
    assert success is True

    updated = get_ticket(tid)
    assert updated["status"] == TicketStatus.APPROVED
    assert updated["agent_final_response"] == "Approved by agent #42"
    assert updated["reviewed_by"] == "lead_agent_priya"
    assert len(updated["audit_logs"]) >= 2


def test_list_tickets_with_filters():
    tickets, total = list_tickets(limit=10, offset=0)
    assert total >= 1
    assert isinstance(tickets, list)


def test_dashboard_metrics():
    metrics = get_dashboard_metrics()
    assert "total_tickets" in metrics
    assert metrics["total_tickets"] >= 1
    assert "urgency_distribution" in metrics
    assert "language_distribution" in metrics
