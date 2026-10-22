"""
Triage Service Pipeline Orchestrator.
Coordinates validation, normalization, intent classification, urgency evaluation,
escalation decision, and safe response drafting into a cohesive pipeline.
"""

import time
from typing import Any, Dict, Optional

from src.config import CONFIDENCE_THRESHOLD, TicketStatus
from src.escalation import evaluate_escalation
from src.intent_model import get_intent_classifier
from src.normalize import normalize_message
from src.output_validator import validate_incoming_message, validate_reply_draft
from src.persistence import save_ticket
from src.reply_drafter import draft_safe_reply
from src.urgency import assess_urgency


def process_support_message(
    raw_text: str,
    language_hint: Optional[str] = None,
    save_to_db: bool = False,
    confidence_threshold: float = CONFIDENCE_THRESHOLD
) -> Dict[str, Any]:
    """
    Executes end-to-end triage flow for a single customer message.
    Conforms to TRD Section 5.3 structured response schema.
    """
    start_time = time.perf_counter()

    # Step 1: Input validation and security checks
    val_res = validate_incoming_message(raw_text)
    if not val_res.is_valid:
        return {
            "status": "error",
            "error": val_res.error_message,
            "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
        }

    # Step 2: Conservative Normalization and Language Identification
    norm = normalize_message(val_res.sanitized_text, language_hint=language_hint)

    # Step 3: Intent Classification
    classifier = get_intent_classifier()
    intent_res = classifier.predict(norm, confidence_threshold=confidence_threshold)

    # Step 4: Urgency Assessment
    urgency_res = assess_urgency(norm, predicted_intent=intent_res.intent)

    # Step 5: Escalation Decision Engine
    escalation_res = evaluate_escalation(
        norm_text=norm,
        intent_pred=intent_res,
        urgency_ass=urgency_res,
        confidence_threshold=confidence_threshold
    )

    # Step 6: Safe Reply Drafting
    reply_res = draft_safe_reply(
        norm_text=norm,
        intent_pred=intent_res,
        urgency_ass=urgency_res,
        escalation_dec=escalation_res
    )

    # Step 7: Output Safety Validation
    is_safe, safety_violations = validate_reply_draft(reply_res.draft_text)
    all_warnings = list(val_res.warning_messages) + list(reply_res.safety_warnings)
    if not is_safe:
        all_warnings.extend(safety_violations)

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    triage_payload = {
        "status": "escalated" if escalation_res.escalate_to_human else "ready_for_review",
        "raw_text": norm.raw_text,
        "cleaned_text": norm.cleaned_text,
        "language": {
            "detected": norm.language_detected,
            "confidence": norm.language_confidence,
            "hinglish_score": norm.hinglish_score,
            "tanglish_score": norm.tanglish_score,
            "english_score": norm.english_score,
        },
        "intent": {
            "label": intent_res.intent,
            "category": intent_res.category,
            "confidence": intent_res.confidence,
            "raw_score": intent_res.raw_score,
            "margin": intent_res.margin,
            "entropy": intent_res.entropy,
            "is_uncertain": intent_res.is_uncertain,
            "top_candidates": intent_res.top_candidates,
            "evidence_tokens": intent_res.evidence_tokens
        },
        "urgency": {
            "label": urgency_res.level,
            "score": urgency_res.score,
            "reason_codes": urgency_res.reason_codes,
            "triggers_matched": urgency_res.triggers_matched,
            "explanation": urgency_res.explanation,
            "override_triggered": urgency_res.override_triggered
        },
        "escalation": {
            "required": escalation_res.escalate_to_human,
            "priority": escalation_res.priority_level,
            "primary_reason": escalation_res.primary_reason,
            "details": escalation_res.reason_details,
            "suggested_queue": escalation_res.suggested_queue,
            "audit_tags": escalation_res.audit_tags
        },
        "reply_draft": {
            "text": reply_res.draft_text,
            "language_used": reply_res.language_used,
            "tone": reply_res.tone,
            "requires_human_approval": True,
            "context_applied": reply_res.context_applied
        },
        "entities": norm.entities,
        "negations": norm.negations_found,
        "warnings": all_warnings,
        "model_version": intent_res.model_version,
        "latency_ms": latency_ms
    }

    # Optional Persistence
    if save_to_db:
        ticket_id = save_ticket({
            "raw_text": norm.raw_text,
            "cleaned_text": norm.cleaned_text,
            "language_detected": norm.language_detected,
            "language_confidence": norm.language_confidence,
            "predicted_intent": intent_res.intent,
            "intent_category": intent_res.category,
            "intent_confidence": intent_res.confidence,
            "intent_margin": intent_res.margin,
            "urgency_level": urgency_res.level,
            "urgency_score": urgency_res.score,
            "urgency_reasons": urgency_res.reason_codes,
            "escalate_to_human": escalation_res.escalate_to_human,
            "escalation_priority": escalation_res.priority_level,
            "escalation_reason": escalation_res.primary_reason,
            "reply_draft": reply_res.draft_text,
            "status": TicketStatus.ESCALATED if escalation_res.escalate_to_human else TicketStatus.PENDING_REVIEW
        })
        triage_payload["ticket_id"] = ticket_id

    return triage_payload
