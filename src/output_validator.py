"""
Input and Output validation guardrails for support triage.
Detects prompt injection, validates bounds, masks sensitive PII,
and verifies reply drafts against unauthorized promises.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.config import MAX_MESSAGE_CHARS, MIN_MESSAGE_CHARS

# Prompt injection signatures
PROMPT_INJECTION_PATTERNS = [
    r"(?i)\bignore (?:all )?previous instructions\b",
    r"(?i)\bdisregard (?:all )?prior rules\b",
    r"(?i)\bsystem prompt\b",
    r"(?i)\byou are now (?:dan|developer mode|unrestricted)\b",
    r"(?i)\breturn your secret key\b",
    r"(?i)\boutput internal system instructions\b",
    r"(?i)\bjailbreak\b",
]

# Unauthorized promise patterns in draft outputs
FORBIDDEN_PROMISE_PATTERNS = [
    r"(?i)\b(?:refund (?:has been|is) (?:processed|credited|sent))\b",
    r"(?i)\b(?:your order (?:has been|is) delivered)\b",
    r"(?i)\bguarantee(?:d)?\b.*?\brefund\b",
    r"(?i)\b(?:100%|full) refund (?:guarantee|guaranteed)\b",
    r"(?i)\b(?:waived all fees permanently)\b",
    r"(?i)\b(?:free gift card credited)\b",
    r"(?i)\b(?:i have cancelled your account)\b",
]

@dataclass
class ValidationResult:
    """Validation report container."""
    is_valid: bool
    sanitized_text: str
    error_message: Optional[str] = None
    warning_messages: List[str] = None
    pii_redacted: bool = False
    injection_detected: bool = False


def validate_incoming_message(raw_text: str) -> ValidationResult:
    """
    Validates input bounds, detects prompt injection, and redacts sensitive PII.
    """
    warnings: List[str] = []

    if raw_text is None or not str(raw_text).strip():
        return ValidationResult(
            is_valid=False,
            sanitized_text="",
            error_message="Message cannot be blank or empty.",
            warning_messages=[]
        )

    text = str(raw_text).strip()
    char_len = len(text)

    if char_len < MIN_MESSAGE_CHARS:
        return ValidationResult(
            is_valid=False,
            sanitized_text=text,
            error_message=f"Message is too short ({char_len} chars). Please enter at least {MIN_MESSAGE_CHARS} characters.",
            warning_messages=[]
        )

    if char_len > MAX_MESSAGE_CHARS:
        return ValidationResult(
            is_valid=False,
            sanitized_text=text[:MAX_MESSAGE_CHARS],
            error_message=f"Message exceeds maximum length ({MAX_MESSAGE_CHARS} characters). Please shorten your inquiry.",
            warning_messages=[]
        )

    # Check Prompt Injection
    injection_found = False
    for pat in PROMPT_INJECTION_PATTERNS:
        if re.search(pat, text):
            injection_found = True
            warnings.append(f"Security Alert: Potential prompt injection pattern detected ({pat}).")
            break

    # Redact sensitive credit card patterns (16 digits)
    redacted_text = text
    cc_pattern = r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    if re.search(cc_pattern, redacted_text):
        redacted_text = re.sub(cc_pattern, "[REDACTED-CARD-NUMBER]", redacted_text)
        warnings.append("Sensitive 16-digit card number was redacted for PCI compliance.")

    return ValidationResult(
        is_valid=True,
        sanitized_text=redacted_text,
        error_message=None,
        warning_messages=warnings,
        pii_redacted=(redacted_text != text),
        injection_detected=injection_found
    )


def validate_reply_draft(draft_text: str) -> Tuple[bool, List[str]]:
    """
    Verifies that generated or human-edited reply draft contains NO unauthorized promises.
    Returns: (is_safe, list_of_violations)
    """
    violations = []
    for pat in FORBIDDEN_PROMISE_PATTERNS:
        matches = re.findall(pat, draft_text)
        if matches:
            violations.append(f"Forbidden promise detected: '{matches[0]}'. Cannot commit to unverified status.")

    return len(violations) == 0, violations
