"""
Unit tests for urgency classification and deterministic triggers.
"""

import pytest
from src.config import UrgencyLevel
from src.normalize import normalize_message
from src.urgency import assess_urgency


def test_critical_security_hack_trigger():
    norm = normalize_message("Mera account hacked ho gaya hai aur card stolen hai!")
    urg = assess_urgency(norm, predicted_intent="delete_account")
    assert urg.level == UrgencyLevel.CRITICAL
    assert urg.override_triggered is True
    assert "security_fraud_compromise" in urg.reason_codes


def test_critical_legal_action_threat():
    norm = normalize_message("Consumer court mein case karunga aur police complaint hogi!")
    urg = assess_urgency(norm, predicted_intent="complaint")
    assert urg.level == UrgencyLevel.CRITICAL
    assert urg.override_triggered is True
    assert "legal_action_threat" in urg.reason_codes


def test_high_urgency_explicit_keyword():
    norm = normalize_message("Need delivery urgent asap today right now!")
    urg = assess_urgency(norm, predicted_intent="track_order")
    assert urg.level == UrgencyLevel.HIGH
    assert "explicit_urgency_keyword" in urg.reason_codes


def test_high_urgency_repeated_complaint():
    norm = normalize_message("This is 3rd time complaining about wrong product delivered!")
    urg = assess_urgency(norm, predicted_intent="complaint")
    assert urg.level == UrgencyLevel.HIGH
    assert "repeated_unresolved_complaint" in urg.reason_codes


def test_low_urgency_newsletter():
    norm = normalize_message("I would like to subscribe to the weekly newsletter.")
    urg = assess_urgency(norm, predicted_intent="newsletter_subscription")
    assert urg.level == UrgencyLevel.LOW


def test_normal_urgency_routine_inquiry():
    norm = normalize_message("Where can I find the invoice for my past orders?")
    urg = assess_urgency(norm, predicted_intent="get_invoice")
    assert urg.level == UrgencyLevel.NORMAL
