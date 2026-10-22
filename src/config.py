"""
Central configuration module for Code-Mixed Support Triage Assistant.
NexAI Hack 2026 - Problem Statement 1.1
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Set

# Environment configuration
APP_NAME = "NexAI Code-Mixed Support Triage Assistant"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# File paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
EVAL_DIR = os.path.join(BASE_DIR, "eval")
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "support_triage.db"))
MODEL_PATH = os.path.join(MODELS_DIR, "intent_classifier.pkl")
BITEXT_RAW_PATH = os.path.join(DATA_DIR, "bitext_raw.csv")
BITEXT_CLEANED_PATH = os.path.join(DATA_DIR, "bitext_cleaned.csv")
CHALLENGE_SET_PATH = os.path.join(EVAL_DIR, "code_mixed_cases.jsonl")

# Constraints
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "3000"))
MIN_MESSAGE_CHARS = 3
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.62"))

# Official Color Palette (from PRD & TRD)
COLORS = {
    "aviation_navy": "#14263D",   # Header / main structure
    "deep_blue": "#203B57",       # Panels & card headers
    "signal_teal": "#12A89D",     # Primary actions & focus highlights
    "accessible_teal": "#087F79", # High contrast links & badges
    "mint_wash": "#DDF5F0",       # Reviewed / verified tint
    "background": "#F3F6FA",      # Application canvas background
    "white": "#FFFFFF",           # Cards & active panels
    "body_text": "#182B3A",       # High contrast main typography
    "muted_slate": "#607386",     # Secondary metadata & timestamps
    "border": "#D9E2EB",          # Structural dividers & card outlines
    "caution_amber": "#F0B44D",   # Uncertain / pending review
    "caution_bg": "#FFF3D8",      # Warning banner background
    "danger_red": "#C84D54",      # Critical urgency / safety violations
    "success_green": "#23856D",   # Human-approved & resolved
}

# Supported Language Slices
LANGUAGES = {
    "auto": "Automatic Detection",
    "hinglish": "Hinglish (Hindi-English Latin Mix)",
    "tanglish": "Tanglish (Tamil-English Latin Mix)",
    "english": "Standard English",
    "other": "Other / Unsupported",
}

# 4-tier Urgency Hierarchy
class UrgencyLevel:
    CRITICAL = "Critical"
    HIGH = "High"
    NORMAL = "Normal"
    LOW = "Low"
    ALL = [CRITICAL, HIGH, NORMAL, LOW]

# Escalation Reason Codes
class EscalationReason:
    CRITICAL_RISK = "critical_risk_safety_override"
    LOW_CONFIDENCE = "model_confidence_below_threshold"
    OUT_OF_SCOPE = "unsupported_or_out_of_scope_intent"
    MISSING_CONTEXT = "unverified_financial_or_order_context"
    INCONSISTENT_TRIAGE = "intent_urgency_semantic_conflict"
    REPEATED_UNRESOLVED = "repeated_unresolved_escalation"
    PROMPT_INJECTION = "adversarial_prompt_injection_detected"
    NONE = "none"

# Workflow Statuses
class TicketStatus:
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    RESOLVED = "resolved"

# Official 27 Bitext Intents and 11 Categories
BITEXT_CATEGORIES: Dict[str, List[str]] = {
    "ACCOUNT": [
        "create_account",
        "delete_account",
        "edit_account",
        "recover_password",
        "registration_problems",
        "switch_account",
    ],
    "CANCEL": [
        "cancel_order",
        "check_cancellation_fee",
    ],
    "CONTACT": [
        "contact_customer_service",
        "contact_human_agent",
    ],
    "DELIVERY": [
        "delivery_options",
        "delivery_period",
    ],
    "FEEDBACK": [
        "complaint",
        "review",
    ],
    "INVOICE": [
        "check_invoice",
        "get_invoice",
    ],
    "ORDER": [
        "change_order",
        "place_order",
        "track_order",
    ],
    "PAYMENT": [
        "check_payment_methods",
        "payment_issue",
    ],
    "REFUND": [
        "check_refund_policy",
        "get_refund",
        "track_refund",
    ],
    "SHIPPING": [
        "change_shipping_address",
        "set_up_shipping_address",
    ],
    "SUBSCRIPTION": [
        "newsletter_subscription",
    ],
}

ALL_INTENTS: List[str] = sorted(
    [intent for intents in BITEXT_CATEGORIES.values() for intent in intents]
)

# Friendly readable labels for intents
INTENT_LABELS: Dict[str, str] = {
    "cancel_order": "Cancel Order",
    "change_order": "Modify Order Items",
    "change_shipping_address": "Change Shipping Address",
    "check_cancellation_fee": "Check Cancellation Fee",
    "check_invoice": "Verify Invoice Details",
    "check_payment_methods": "Accepted Payment Methods",
    "check_refund_policy": "Check Refund Policy",
    "complaint": "File Customer Complaint",
    "contact_customer_service": "Contact Support Helpdesk",
    "contact_human_agent": "Request Human Representative",
    "create_account": "Create New Account",
    "delete_account": "Delete Account Request",
    "delivery_options": "Shipping & Delivery Options",
    "delivery_period": "Expected Delivery Timeline",
    "edit_account": "Update Account Profile",
    "get_invoice": "Download Invoice / Receipt",
    "get_refund": "Request Refund / Return",
    "newsletter_subscription": "Manage Newsletter Subscription",
    "payment_issue": "Payment Processing Failure",
    "place_order": "Assistance Placing Order",
    "recover_password": "Password Reset / Account Recovery",
    "registration_problems": "Registration / Login Trouble",
    "review": "Submit Product / Service Review",
    "set_up_shipping_address": "Add New Delivery Address",
    "switch_account": "Switch / Link Account",
    "track_order": "Track Order / Delivery Status",
    "track_refund": "Track Refund Status",
    "out_of_scope": "Out of Scope / Unknown Request",
}
