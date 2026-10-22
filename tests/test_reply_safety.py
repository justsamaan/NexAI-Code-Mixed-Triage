"""
Unit tests for response drafting safety and promise validation.
"""

import pytest
from src.escalation import EscalationDecision
from src.intent_model import IntentPrediction
from src.normalize import normalize_message
from src.output_validator import validate_reply_draft
from src.reply_drafter import draft_safe_reply
from src.urgency import UrgencyAssessment


def test_draft_requires_human_approval():
    norm = normalize_message("Cancel order #ORD-44910 please")
    intent_pred = IntentPrediction(
        intent="cancel_order", category="CANCEL", confidence=0.88, raw_score=0.88,
        margin=0.4, entropy=0.1, is_uncertain=False, top_candidates=[], evidence_tokens=[], model_version="1.0"
    )
    urg_ass = UrgencyAssessment(level="Normal", score=0.5, reason_codes=[], override_triggered=False, triggers_matched=[], explanation="")
    esc_dec = EscalationDecision(escalate_to_human=False, priority_level="P3-ROUTINE", primary_reason="none", reason_details="", audit_tags=[], suggested_queue="")

    draft_res = draft_safe_reply(norm, intent_pred, urg_ass, esc_dec)
    assert draft_res.requires_human_approval is True
    assert "HUMAN_APPROVAL_MANDATORY" in draft_res.safety_warnings[0]


def test_validator_catches_unauthorized_refund_promise():
    unsafe_text = "Hello, your refund has been processed and credited to your card."
    is_safe, violations = validate_reply_draft(unsafe_text)
    assert is_safe is False
    assert len(violations) > 0


def test_validator_catches_guaranteed_delivery_promise():
    unsafe_text = "Do not worry, we guarantee 100% full refund immediately."
    is_safe, violations = validate_reply_draft(unsafe_text)
    assert is_safe is False
    assert len(violations) > 0


def test_validator_approves_safe_draft():
    safe_text = "Namaste. We are reviewing your cancellation request with our fulfillment team."
    is_safe, violations = validate_reply_draft(safe_text)
    assert is_safe is True
    assert len(violations) == 0
