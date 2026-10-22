"""
Deterministic escalation decision engine.
Combines calibrated model confidence, urgency overrides, context verification,
and semantic consistency checks.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.config import CONFIDENCE_THRESHOLD, EscalationReason, UrgencyLevel
from src.intent_model import IntentPrediction
from src.normalize import NormalizedText
from src.urgency import UrgencyAssessment

@dataclass
class EscalationDecision:
    """Structured escalation outcome."""
    escalate_to_human: bool
    priority_level: str
    primary_reason: str
    reason_details: str
    audit_tags: List[str]
    suggested_queue: str


def evaluate_escalation(
    norm_text: NormalizedText,
    intent_pred: IntentPrediction,
    urgency_ass: UrgencyAssessment,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    has_verified_context: bool = False
) -> EscalationDecision:
    """
    Evaluates whether a ticket must be escalated to a human supervisor or specialist.
    Never conceals uncertainty or high-risk cases behind model predictions.
    """
    audit_tags: List[str] = []

    # 1. Critical Risk Safety Override
    if urgency_ass.level == UrgencyLevel.CRITICAL:
        audit_tags.append("CRITICAL_SAFETY_OVERRIDE")
        return EscalationDecision(
            escalate_to_human=True,
            priority_level="P0-IMMEDIATE",
            primary_reason=EscalationReason.CRITICAL_RISK,
            reason_details=f"Immediate safety/security trigger: {urgency_ass.explanation}",
            audit_tags=audit_tags,
            suggested_queue="Executive & Trust Safety Tier 3"
        )

    # 2. Out of Scope Intent
    if intent_pred.intent in ("out_of_scope", "unknown") or intent_pred.confidence < 0.35:
        audit_tags.append("OUT_OF_SCOPE_INPUT")
        return EscalationDecision(
            escalate_to_human=True,
            priority_level="P2-NORMAL",
            primary_reason=EscalationReason.OUT_OF_SCOPE,
            reason_details="Message intent is ambiguous, unsupported, or out-of-scope.",
            audit_tags=audit_tags,
            suggested_queue="General Support Frontline"
        )

    # 3. Model Confidence Below Calibrated Threshold or Ambiguous Margin
    if intent_pred.confidence < confidence_threshold or intent_pred.margin < 0.10:
        audit_tags.append("LOW_MODEL_CONFIDENCE")
        reason_msg = (
            f"Model confidence ({intent_pred.confidence:.2f}) below threshold ({confidence_threshold:.2f}) "
            f"or top predictions margin ({intent_pred.margin:.2f}) too narrow."
        )
        return EscalationDecision(
            escalate_to_human=True,
            priority_level="P1-ELEVATED" if urgency_ass.level == UrgencyLevel.HIGH else "P2-NORMAL",
            primary_reason=EscalationReason.LOW_CONFIDENCE,
            reason_details=reason_msg,
            audit_tags=audit_tags,
            suggested_queue="Triage Review Queue"
        )

    # 4. High Urgency with Missing Order/Account Context for Financial/Order Action
    financial_intents = {"get_refund", "cancel_order", "payment_issue", "delete_account"}
    if intent_pred.intent in financial_intents and not norm_text.entities.get("order_ids") and not has_verified_context:
        audit_tags.append("MISSING_ORDER_ID_CONTEXT")
        if urgency_ass.level == UrgencyLevel.HIGH:
            return EscalationDecision(
                escalate_to_human=True,
                priority_level="P1-HIGH",
                primary_reason=EscalationReason.MISSING_CONTEXT,
                reason_details=f"Actionable '{intent_pred.intent}' request missing verified Order ID context.",
                audit_tags=audit_tags,
                suggested_queue="Escalated Financial & Order Resolution"
            )

    # 5. Semantic Consistency Violation (e.g. Complaint with High Distress)
    if intent_pred.intent == "complaint" and urgency_ass.level == UrgencyLevel.HIGH:
        audit_tags.append("HIGH_SEVERITY_COMPLAINT")
        return EscalationDecision(
            escalate_to_human=True,
            priority_level="P1-HIGH",
            primary_reason=EscalationReason.REPEATED_UNRESOLVED,
            reason_details="High-urgency customer complaint requiring empathetic supervisor review.",
            audit_tags=audit_tags,
            suggested_queue="Customer Retention & Complaints"
        )

    # 6. High Urgency (General)
    if urgency_ass.level == UrgencyLevel.HIGH:
        audit_tags.append("HIGH_PRIORITY_ROUTING")
        return EscalationDecision(
            escalate_to_human=True,
            priority_level="P1-HIGH",
            primary_reason=urgency_ass.reason_codes[0] if urgency_ass.reason_codes else "high_urgency_dispatch",
            reason_details=urgency_ass.explanation,
            audit_tags=audit_tags,
            suggested_queue="Priority Resolution Desk"
        )

    # Standard Routine Triage (No Escalation Required)
    return EscalationDecision(
        escalate_to_human=False,
        priority_level="P3-ROUTINE" if urgency_ass.level == UrgencyLevel.NORMAL else "P4-LOW",
        primary_reason=EscalationReason.NONE,
        reason_details="Standard verified ticket within model confidence tolerances.",
        audit_tags=["STANDARD_AUTO_TRIAGE"],
        suggested_queue="Standard Agent Inbox"
    )
