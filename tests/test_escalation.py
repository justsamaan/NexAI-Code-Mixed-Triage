"""
Unit tests for escalation decision engine.
"""

import pytest
from src.config import EscalationReason, UrgencyLevel
from src.escalation import evaluate_escalation
from src.intent_model import IntentPrediction
from src.normalize import normalize_message
from src.urgency import UrgencyAssessment


def test_escalate_critical_risk():
    norm = normalize_message("Police complaint FIR regarding unauthorized hack")
    intent_pred = IntentPrediction(
        intent="complaint", category="FEEDBACK", confidence=0.90, raw_score=0.90,
        margin=0.40, entropy=0.1, is_uncertain=False, top_candidates=[], evidence_tokens=[], model_version="1.0"
    )
    urg_ass = UrgencyAssessment(
        level=UrgencyLevel.CRITICAL, score=0.98, reason_codes=["security_fraud_compromise"],
        override_triggered=True, triggers_matched=["hack"], explanation="Critical"
    )
    decision = evaluate_escalation(norm, intent_pred, urg_ass)
    assert decision.escalate_to_human is True
    assert decision.priority_level == "P0-IMMEDIATE"
    assert decision.primary_reason == EscalationReason.CRITICAL_RISK


def test_escalate_low_confidence():
    norm = normalize_message("Kuch ajeeb ho raha hai")
    intent_pred = IntentPrediction(
        intent="track_order", category="ORDER", confidence=0.45, raw_score=0.45,
        margin=0.04, entropy=0.8, is_uncertain=True, top_candidates=[], evidence_tokens=[], model_version="1.0"
    )
    urg_ass = UrgencyAssessment(
        level=UrgencyLevel.NORMAL, score=0.50, reason_codes=["routine"],
        override_triggered=False, triggers_matched=[], explanation="Normal"
    )
    decision = evaluate_escalation(norm, intent_pred, urg_ass, confidence_threshold=0.62)
    assert decision.escalate_to_human is True
    assert decision.primary_reason == EscalationReason.LOW_CONFIDENCE


def test_escalate_missing_order_context_for_high_urgency_refund():
    norm = normalize_message("Paise wapas chahiye urgent!")
    intent_pred = IntentPrediction(
        intent="get_refund", category="REFUND", confidence=0.85, raw_score=0.85,
        margin=0.35, entropy=0.2, is_uncertain=False, top_candidates=[], evidence_tokens=[], model_version="1.0"
    )
    urg_ass = UrgencyAssessment(
        level=UrgencyLevel.HIGH, score=0.82, reason_codes=["financial_transaction_failure"],
        override_triggered=False, triggers_matched=[], explanation="High"
    )
    decision = evaluate_escalation(norm, intent_pred, urg_ass, has_verified_context=False)
    assert decision.escalate_to_human is True
    assert decision.primary_reason == EscalationReason.MISSING_CONTEXT


def test_no_escalation_for_routine_verified_ticket():
    norm = normalize_message("Order #ORD-12345 tracking status please")
    intent_pred = IntentPrediction(
        intent="track_order", category="ORDER", confidence=0.88, raw_score=0.88,
        margin=0.45, entropy=0.1, is_uncertain=False, top_candidates=[], evidence_tokens=[], model_version="1.0"
    )
    urg_ass = UrgencyAssessment(
        level=UrgencyLevel.NORMAL, score=0.50, reason_codes=["standard_queue"],
        override_triggered=False, triggers_matched=[], explanation="Normal"
    )
    decision = evaluate_escalation(norm, intent_pred, urg_ass)
    assert decision.escalate_to_human is False
    assert decision.primary_reason == EscalationReason.NONE
