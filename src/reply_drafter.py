"""
Safe, constrained response drafter for code-mixed support triage.
Guarantees ZERO unauthorized promises (no fake refunds, fake tracking numbers, or fake policy exceptions).
Adapts tone and greeting appropriately for Hinglish, Tanglish, and English contexts.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.config import UrgencyLevel
from src.escalation import EscalationDecision
from src.intent_model import IntentPrediction
from src.normalize import NormalizedText
from src.urgency import UrgencyAssessment

# Verified response templates by intent and language slice
DRAFT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "cancel_order": {
        "hinglish": (
            "Namaste. Aapke cancellation request ke regarding hum verify kar rahe hain. "
            "{order_ref} Humare representative order status check karke turant confirm karenge. "
            "Kripya dhyan dein ki dispatch hone ke baad order cancel nahi kiya ja sakta."
        ),
        "tanglish": (
            "Vanakkam. Unga order cancel request-ai naanga review panrom. "
            "{order_ref} Enga support agent order status check panni udane update tharuvaanga. "
            "Dispatch aana orders cancel panna mudiyathu enbathai kavanathil kollavum."
        ),
        "english": (
            "Hello. Thank you for reaching out regarding your order cancellation request. "
            "{order_ref} A support specialist is verifying whether your order has entered dispatch. "
            "We will follow up with confirmation shortly."
        )
    },
    "get_refund": {
        "hinglish": (
            "Namaste. Aapke refund request ko note kar liya gaya hai. "
            "{order_ref} Refund process karne se pehle humare account team verification complete karegi. "
            "Agar refund approve hota hai, toh yeh 5-7 working days mein aapke original payment method par credit hoga."
        ),
        "tanglish": (
            "Vanakkam. Unga refund request register seiyyapattathu. "
            "{order_ref} Accounts team verification mudithavudan status update anuppuvom. "
            "Approve aagum patchathil, 5-7 working days-kull unga account-ku transfer aagum."
        ),
        "english": (
            "Hello. We have received your refund inquiry. "
            "{order_ref} Our billing department will verify the return eligibility before initiating any refund. "
            "Once approved, refunds typically reflect within 5-7 business days."
        )
    },
    "track_order": {
        "hinglish": (
            "Namaste. Aapke order ki delivery status check karne ke liye hum logistics partner se verify kar rahe hain. "
            "{order_ref} Live tracking status update aate hi hum aapko details share karenge."
        ),
        "tanglish": (
            "Vanakkam. Unga order delivery status kurithu courier partner-idam check seigirom. "
            "{order_ref} Latest tracking update therinjavudan ungalukku thagaval tharugirom."
        ),
        "english": (
            "Hello. Thank you for contacting us regarding your order tracking status. "
            "{order_ref} We are checking the latest scan with our logistics carrier and will share an update shortly."
        )
    },
    "payment_issue": {
        "hinglish": (
            "Namaste. Payment deduction ko lekar hui pareshani ke liye hum shama chahte hain. "
            "{order_ref} Kripya bank transaction reference / UTR number share karein taaki hum payment gateway se verify kar sakein."
        ),
        "tanglish": (
            "Vanakkam. Payment issue thodarbana ungal varuthathai purinthu kolgirom. "
            "{order_ref} Dhayavuseithu ungal bank UTR / transaction ID-yai pagiravum; gateway-il check seithu udane uthavi seigirom."
        ),
        "english": (
            "Hello. We apologize for the inconvenience caused by this payment deduction issue. "
            "{order_ref} Please share your bank reference (UTR number) so our billing team can trace the transaction with our payment gateway."
        )
    },
    "complaint": {
        "hinglish": (
            "Namaste. Aapko jo asuvidha hui hai uske liye hum behad khed vyakt karte hain. "
            "Aapki complaint priority ke sath escalate kar di gayi hai, aur ek senior supervisor aapse sampark karega."
        ),
        "tanglish": (
            "Vanakkam. Ungalukku yerpatta siramathirkku manamvarundhi mannippu ketkirom. "
            "Unga complaint-ai supervisor gavanam panna escalate seithullom; udane ungalai thodarbu kolvaargal."
        ),
        "english": (
            "Hello. We sincerely apologize for this frustrating experience. "
            "Your complaint has been escalated to a customer experience manager who will review the situation and respond directly."
        )
    },
    "recover_password": {
        "hinglish": (
            "Namaste. Account access recover karne ke liye kripya registered email address par bheja gaya secure password reset link use karein. "
            "Kabhi bhi apna OTP ya password kisi ke sath share na karein."
        ),
        "tanglish": (
            "Vanakkam. Unga password reset seiyya, ungal registered email-ku anuppappatta secure link-ai payanpaduthavum. "
            "Ungal OTP-yai yaaridameiyum share seiyyatheergal."
        ),
        "english": (
            "Hello. To safely recover your account, please check your registered email for an automated password reset link. "
            "Remember that our team will never ask for your password or OTP."
        )
    },
    "contact_human_agent": {
        "hinglish": (
            "Namaste. Hum aapko turant ek human support executive ke sath connect kar rahe hain. "
            "Kripya kuch kshan intezar karein."
        ),
        "tanglish": (
            "Vanakkam. Ungalai ippothu oru support executive-udan connect seigirom. "
            "Dhayavuseithu sirithu neram kaathirukkavum."
        ),
        "english": (
            "Hello. We are transferring your session to a live support representative. "
            "Please hold while our next available agent joins."
        )
    }
}

DEFAULT_FALLBACK_DRAFT = {
    "hinglish": (
        "Namaste. Aapka sandesh humein mil gaya hai. Ek support representative aapke query ko review kar raha hai "
        "aur jald hi detailed information ke sath reply karega. Dhanyawad."
    ),
    "tanglish": (
        "Vanakkam. Ungal thagaval kidaithathu. Oru support specialist unga inquiry-ai review seithu udane badhil tharuvaanga. "
        "Nandri."
    ),
    "english": (
        "Hello. Thank you for reaching out to customer support. A support specialist is reviewing your message "
        "and will get back to you with the required assistance shortly."
    )
}

@dataclass
class ReplyDraftResult:
    """Structured response draft output."""
    draft_text: str
    language_used: str
    tone: str
    requires_human_approval: bool
    context_applied: List[str]
    safety_warnings: List[str]


def draft_safe_reply(
    norm_text: NormalizedText,
    intent_pred: IntentPrediction,
    urgency_ass: UrgencyAssessment,
    escalation_dec: EscalationDecision
) -> ReplyDraftResult:
    """
    Generates an auditable, conservative reply draft.
    Prevents unauthorized commitments and enforces human approval.
    """
    safety_warnings: List[str] = [
        "HUMAN_APPROVAL_MANDATORY: Do not deliver without agent review.",
        "ZERO_UNVERIFIED_PROMISES: No financial, shipping, or policy commitment made."
    ]
    context_applied: List[str] = []

    # Select language matching normalized text
    lang = norm_text.language_detected if norm_text.language_detected in ("hinglish", "tanglish") else "english"

    # Format order reference if present
    order_ids = norm_text.entities.get("order_ids", [])
    if order_ids:
        order_ref = f"(Reference Order ID: #{order_ids[0]})."
        context_applied.append(f"Referenced Order ID: {order_ids[0]}")
    else:
        order_ref = "If you have an associated Order ID or Invoice reference, please provide it."
        context_applied.append("Requested missing Order ID context")

    # Critical risk override draft
    if urgency_ass.level == UrgencyLevel.CRITICAL:
        safety_warnings.append("CRITICAL_SAFETY_HOLD: Escalate immediately; minimize auto-draft communication.")
        if lang == "hinglish":
            draft = (
                "Namaste. Aapki suraksha aur account safety humari sabse badi priority hai. "
                "Yeh case high-priority investigation ke liye security desk ko escalate kar diya gaya hai. "
                "Humare senior supervisor turant aapse sampark karenge."
            )
        elif lang == "tanglish":
            draft = (
                "Vanakkam. Ungal arakattalai mattrum security engalukku migavum mukkiyam. "
                "Indha inquiry priority-il security specialist-ku anuppappattullathu. "
                "Senior supervisor udane ungalai thodarbu kolvaargal."
            )
        else:
            draft = (
                "Hello. Your security and safety are our highest priorities. "
                "This issue has been routed to our specialized Trust & Safety team for immediate review. "
                "A senior officer will contact you shortly."
            )

        return ReplyDraftResult(
            draft_text=draft,
            language_used=lang,
            tone="Urgent & Reassuring",
            requires_human_approval=True,
            context_applied=context_applied,
            safety_warnings=safety_warnings
        )

    # Standard intent lookup
    intent_templates = DRAFT_TEMPLATES.get(intent_pred.intent)
    if intent_templates and lang in intent_templates:
        template = intent_templates[lang]
        draft = template.format(order_ref=order_ref)
        tone = "Empathetic & Professional"
    else:
        draft = DEFAULT_FALLBACK_DRAFT.get(lang, DEFAULT_FALLBACK_DRAFT["english"])
        tone = "Helpful & Professional"

    return ReplyDraftResult(
        draft_text=draft,
        language_used=lang,
        tone=tone,
        requires_human_approval=True,
        context_applied=context_applied,
        safety_warnings=safety_warnings
    )
