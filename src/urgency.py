"""
Urgency classification and deterministic safety policy engine.
Separates urgency assessment from intent classification.
Evaluates safety violations, financial loss, account lockouts, repeated complaints, and panic cues.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from src.config import UrgencyLevel
from src.normalize import NormalizedText

# Critical safety / security / legal patterns
CRITICAL_PATTERNS: Dict[str, str] = {
    r"(?i)\b(?:hack|hacked|unauthorized|stolen|fraudulent|compromised|scam|scammed|chor|fraud)\b": "security_fraud_compromise",
    r"(?i)\b(?:police|fir|lawyer|court|consumer court|legal notice|advocate|vakeel|case karunga)\b": "legal_action_threat",
    r"(?i)\b(?:suicide|kill|harm|abuse|harass|danger|threat|violence|jaan)\b": "severe_safety_harm",
    r"(?i)\b(?:otp (?:shared|stolen|leak)|bank account emptied|card stolen)\b": "credential_financial_drain",
}

# High urgency patterns (deadlines, repeated complaints, payment lockouts, severe distress)
HIGH_PATTERNS: Dict[str, str] = {
    r"(?i)\b(?:urgent|emergency|turant|jaldi|seekiram|asap|immediately|right now|aaj hi)\b": "explicit_urgency_keyword",
    r"(?i)\b(?:3rd time|4th time|multiple times|bar bar|kitni baar|ethana vaati|no response since|waiting for [0-9]+ days)\b": "repeated_unresolved_complaint",
    r"(?i)\b(?:account blocked|locked out|access denied|login nahi ho raha|cannot access)\b": "access_lockout",
    r"(?i)\b(?:money debited|amount deducted|paisa kat gaya|kaasu pochu|double charged|unauthorized charge)\b": "financial_discrepancy",
    r"(?i)\b(?:worst service|useless|cheat|cheaters|pathetic|horrible|gussa|bakwas|bekar)\b": "high_customer_frustration",
    r"(?i)\b(?:flight tomorrow|hospital|medical|emergency|marriage tonight|event today)\b": "imminent_hard_deadline",
}

# Low urgency patterns (exploratory, informational, newsletter)
LOW_PATTERNS: Dict[str, str] = {
    r"(?i)\b(?:just wondering|curious|general inquiry|newsletter|informational|policy details)\b": "exploratory_inquiry",
    r"(?i)\b(?:thank you|shukriya|nandri|dhanyawad|thanks|great service)\b": "polite_closure",
}

@dataclass
class UrgencyAssessment:
    """Detailed urgency assessment container."""
    level: str
    score: float
    reason_codes: List[str]
    override_triggered: bool
    triggers_matched: List[str]
    explanation: str


def assess_urgency(
    norm_text: NormalizedText,
    predicted_intent: str = ""
) -> UrgencyAssessment:
    """
    Evaluates urgency independently of intent.
    Combines rule-based safety overrides with linguistic panic markers.
    """
    raw_lower = norm_text.raw_text.lower()
    cleaned_lower = norm_text.cleaned_text.lower()
    full_text = f"{raw_lower} {cleaned_lower}"

    reason_codes: List[str] = []
    triggers_matched: List[str] = []

    # 1. Check CRITICAL Safety & Security Overrides
    for pattern, code in CRITICAL_PATTERNS.items():
        matches = re.findall(pattern, full_text)
        if matches:
            reason_codes.append(code)
            triggers_matched.extend(list(set(matches))[:3])

    if reason_codes:
        return UrgencyAssessment(
            level=UrgencyLevel.CRITICAL,
            score=0.98,
            reason_codes=reason_codes,
            override_triggered=True,
            triggers_matched=triggers_matched,
            explanation=f"Critical safety/security override triggered: {', '.join(reason_codes)}."
        )

    # 2. Check HIGH Urgency Triggers
    for pattern, code in HIGH_PATTERNS.items():
        matches = re.findall(pattern, full_text)
        if matches:
            reason_codes.append(code)
            triggers_matched.extend(list(set(matches))[:3])

    # Category / Intent specific high urgency elevation
    if predicted_intent in ("payment_issue", "complaint") and norm_text.entities.get("amounts"):
        reason_codes.append("financial_transaction_failure")
        triggers_matched.append(f"Amount: {norm_text.entities['amounts'][0]}")

    if reason_codes:
        return UrgencyAssessment(
            level=UrgencyLevel.HIGH,
            score=0.82,
            reason_codes=reason_codes,
            override_triggered=False,
            triggers_matched=triggers_matched,
            explanation=f"High urgency elevated by: {', '.join(reason_codes)}."
        )

    # 3. Check LOW Urgency
    if predicted_intent in ("newsletter_subscription", "check_refund_policy", "delivery_options"):
        for pattern, code in LOW_PATTERNS.items():
            matches = re.findall(pattern, full_text)
            if matches:
                reason_codes.append(code)
                triggers_matched.extend(list(set(matches))[:2])

        if reason_codes or predicted_intent == "newsletter_subscription":
            return UrgencyAssessment(
                level=UrgencyLevel.LOW,
                score=0.25,
                reason_codes=reason_codes or ["routine_information_lookup"],
                override_triggered=False,
                triggers_matched=triggers_matched,
                explanation="Low urgency: General informational request without active distress."
            )

    # 4. Default: NORMAL Urgency
    return UrgencyAssessment(
        level=UrgencyLevel.NORMAL,
        score=0.50,
        reason_codes=["standard_support_queue"],
        override_triggered=False,
        triggers_matched=[],
        explanation="Normal urgency: Routine customer service inquiry."
    )
