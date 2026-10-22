"""
SQLite persistent storage engine for Code-Mixed Support Triage.
Features Write-Ahead Logging (WAL), indexed querying, full audit logging,
and comprehensive operational metric calculations.
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.config import DB_PATH, TicketStatus, UrgencyLevel


def get_db_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection to the SQLite database with WAL enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    """Initializes tables and indexes."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                cleaned_text TEXT NOT NULL,
                language_detected TEXT NOT NULL,
                language_confidence REAL NOT NULL,
                predicted_intent TEXT NOT NULL,
                intent_category TEXT NOT NULL,
                intent_confidence REAL NOT NULL,
                intent_margin REAL NOT NULL,
                urgency_level TEXT NOT NULL,
                urgency_score REAL NOT NULL,
                urgency_reasons TEXT NOT NULL,
                escalate_to_human INTEGER NOT NULL,
                escalation_priority TEXT NOT NULL,
                escalation_reason TEXT NOT NULL,
                reply_draft TEXT NOT NULL,
                agent_final_response TEXT,
                status TEXT NOT NULL,
                reviewed_by TEXT,
                reviewed_at TEXT
            );
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            );
        """)

        # Indexes for fast filtering and dashboard aggregation
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_urgency ON tickets(urgency_level);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_intent ON tickets(predicted_intent);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_lang ON tickets(language_detected);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets(created_at);")
        conn.commit()


def save_ticket(ticket_dict: Dict[str, Any]) -> str:
    """Inserts a new triage ticket and creates an initial audit log."""
    ticket_id = ticket_dict.get("id") or f"TCK-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    urgency_reasons = ticket_dict.get("urgency_reasons", [])
    if isinstance(urgency_reasons, list):
        urgency_reasons = json.dumps(urgency_reasons)

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO tickets (
                id, created_at, raw_text, cleaned_text, language_detected,
                language_confidence, predicted_intent, intent_category,
                intent_confidence, intent_margin, urgency_level, urgency_score,
                urgency_reasons, escalate_to_human, escalation_priority,
                escalation_reason, reply_draft, agent_final_response, status,
                reviewed_by, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            ticket_dict.get("created_at", now_iso),
            ticket_dict["raw_text"],
            ticket_dict.get("cleaned_text", ticket_dict["raw_text"]),
            ticket_dict.get("language_detected", "auto"),
            ticket_dict.get("language_confidence", 0.0),
            ticket_dict.get("predicted_intent", "unknown"),
            ticket_dict.get("intent_category", "GENERAL"),
            ticket_dict.get("intent_confidence", 0.0),
            ticket_dict.get("intent_margin", 0.0),
            ticket_dict.get("urgency_level", UrgencyLevel.NORMAL),
            ticket_dict.get("urgency_score", 0.5),
            urgency_reasons,
            1 if ticket_dict.get("escalate_to_human", False) else 0,
            ticket_dict.get("escalation_priority", "P3-ROUTINE"),
            ticket_dict.get("escalation_reason", "none"),
            ticket_dict.get("reply_draft", ""),
            ticket_dict.get("agent_final_response", None),
            ticket_dict.get("status", TicketStatus.PENDING_REVIEW),
            ticket_dict.get("reviewed_by", None),
            ticket_dict.get("reviewed_at", None)
        ))

        conn.execute("""
            INSERT INTO audit_logs (ticket_id, action, actor, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            ticket_id,
            "TICKET_CREATED",
            "system_triage_engine",
            now_iso,
            json.dumps({"intent": ticket_dict.get("predicted_intent"), "urgency": ticket_dict.get("urgency_level")})
        ))
        conn.commit()

    return ticket_id


def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single ticket with audit logs."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            return None
        res = dict(row)
        try:
            res["urgency_reasons"] = json.loads(res["urgency_reasons"])
        except Exception:
            res["urgency_reasons"] = []

        logs = conn.execute(
            "SELECT * FROM audit_logs WHERE ticket_id = ? ORDER BY id ASC",
            (ticket_id,)
        ).fetchall()
        res["audit_logs"] = [dict(l) for l in logs]
        return res


def list_tickets(
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    language: Optional[str] = None,
    intent: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """Lists tickets with dynamic filtering, search, and pagination."""
    query = "SELECT * FROM tickets WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM tickets WHERE 1=1"
    params: List[Any] = []

    if status and status != "All":
        query += " AND status = ?"
        count_query += " AND status = ?"
        params.append(status)

    if urgency and urgency != "All":
        query += " AND urgency_level = ?"
        count_query += " AND urgency_level = ?"
        params.append(urgency)

    if language and language != "All":
        query += " AND language_detected = ?"
        count_query += " AND language_detected = ?"
        params.append(language)

    if intent and intent != "All":
        query += " AND predicted_intent = ?"
        count_query += " AND predicted_intent = ?"
        params.append(intent)

    if search_query:
        query += " AND (raw_text LIKE ? OR id LIKE ?)"
        count_query += " AND (raw_text LIKE ? OR id LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    with get_db_connection() as conn:
        total_count = conn.execute(count_query, params).fetchone()[0]

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        exec_params = list(params) + [limit, offset]
        rows = conn.execute(query, exec_params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            try:
                d["urgency_reasons"] = json.loads(d["urgency_reasons"])
            except Exception:
                d["urgency_reasons"] = []
            results.append(d)

        return results, total_count


def update_ticket_status(
    ticket_id: str,
    new_status: str,
    agent_response: Optional[str] = None,
    actor: str = "support_agent"
) -> bool:
    """Updates a ticket's status and logs the review action."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE tickets
            SET status = ?, agent_final_response = COALESCE(?, agent_final_response),
                reviewed_by = ?, reviewed_at = ?
            WHERE id = ?
        """, (new_status, agent_response, actor, now_iso, ticket_id))

        if cur.rowcount == 0:
            return False

        conn.execute("""
            INSERT INTO audit_logs (ticket_id, action, actor, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            ticket_id,
            f"STATUS_CHANGED_TO_{new_status.upper()}",
            actor,
            now_iso,
            json.dumps({"new_status": new_status, "has_response": bool(agent_response)})
        ))
        conn.commit()
        return True


def get_dashboard_metrics() -> Dict[str, Any]:
    """Computes real operational statistics from the SQLite database."""
    with get_db_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if total == 0:
            return {
                "total_tickets": 0,
                "open_tickets": 0,
                "resolved_tickets": 0,
                "escalated_tickets": 0,
                "urgency_distribution": {},
                "intent_distribution": {},
                "language_distribution": {},
                "status_distribution": {},
                "avg_confidence": 0.0
            }

        # Status distribution
        status_rows = conn.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status").fetchall()
        status_dist = {r[0]: r[1] for r in status_rows}

        # Urgency distribution
        urg_rows = conn.execute("SELECT urgency_level, COUNT(*) FROM tickets GROUP BY urgency_level").fetchall()
        urg_dist = {r[0]: r[1] for r in urg_rows}

        # Intent distribution (Top 8)
        intent_rows = conn.execute(
            "SELECT predicted_intent, COUNT(*) FROM tickets GROUP BY predicted_intent ORDER BY COUNT(*) DESC LIMIT 8"
        ).fetchall()
        intent_dist = {r[0]: r[1] for r in intent_rows}

        # Language distribution
        lang_rows = conn.execute("SELECT language_detected, COUNT(*) FROM tickets GROUP BY language_detected").fetchall()
        lang_dist = {r[0]: r[1] for r in lang_rows}

        # Average confidence
        avg_conf = conn.execute("SELECT AVG(intent_confidence) FROM tickets").fetchone()[0] or 0.0

        escalated_count = conn.execute("SELECT COUNT(*) FROM tickets WHERE escalate_to_human = 1").fetchone()[0]

        return {
            "total_tickets": total,
            "open_tickets": status_dist.get(TicketStatus.PENDING_REVIEW, 0),
            "resolved_tickets": status_dist.get(TicketStatus.RESOLVED, 0) + status_dist.get(TicketStatus.APPROVED, 0),
            "escalated_tickets": escalated_count,
            "urgency_distribution": urg_dist,
            "intent_distribution": intent_dist,
            "language_distribution": lang_dist,
            "status_distribution": status_dist,
            "avg_confidence": round(float(avg_conf), 3)
        }


def seed_demo_tickets_if_empty():
    """Populates realistic demonstration tickets if the database is newly initialized."""
    with get_db_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if count > 0:
            return

    # Realistic demo dataset spanning Hinglish, Tanglish, and English
    demo_samples = [
        {
            "raw_text": "Mera order #ORD-98213 abhi tak deliver nahi hua! Tracking bol raha hai in transit for 5 days. Jaldi check karke batao.",
            "language_detected": "hinglish",
            "language_confidence": 0.94,
            "predicted_intent": "track_order",
            "intent_category": "ORDER",
            "intent_confidence": 0.89,
            "intent_margin": 0.45,
            "urgency_level": UrgencyLevel.HIGH,
            "urgency_score": 0.82,
            "urgency_reasons": ["explicit_urgency_keyword"],
            "escalate_to_human": True,
            "escalation_priority": "P1-HIGH",
            "escalation_reason": "explicit_urgency_keyword",
            "reply_draft": "Namaste. Aapke order ki delivery status check karne ke liye hum logistics partner se verify kar rahe hain. (Reference Order ID: #ORD-98213). Live tracking status update aate hi hum aapko details share karenge.",
            "status": TicketStatus.PENDING_REVIEW
        },
        {
            "raw_text": "Ennoda order #ORD-44910 cancel pannunga please, innum dispatch aagala. Cash on delivery dhaan.",
            "language_detected": "tanglish",
            "language_confidence": 0.92,
            "predicted_intent": "cancel_order",
            "intent_category": "CANCEL",
            "intent_confidence": 0.86,
            "intent_margin": 0.40,
            "urgency_level": UrgencyLevel.NORMAL,
            "urgency_score": 0.50,
            "urgency_reasons": ["standard_support_queue"],
            "escalate_to_human": False,
            "escalation_priority": "P3-ROUTINE",
            "escalation_reason": "none",
            "reply_draft": "Vanakkam. Unga order cancel request-ai naanga review panrom. (Reference Order ID: #ORD-44910). Enga support agent order status check panni udane update tharuvaanga.",
            "status": TicketStatus.APPROVED,
            "agent_final_response": "Vanakkam. Order #ORD-44910 has been verified and marked for cancellation before dispatch."
        },
        {
            "raw_text": "Aapka portal fraud hai! Bina OTP share kiye mere bank se 12,500 rupees cut gaye! Main cyber crime police me complaint karunga!",
            "language_detected": "hinglish",
            "language_confidence": 0.96,
            "predicted_intent": "complaint",
            "intent_category": "FEEDBACK",
            "intent_confidence": 0.88,
            "intent_margin": 0.52,
            "urgency_level": UrgencyLevel.CRITICAL,
            "urgency_score": 0.98,
            "urgency_reasons": ["security_fraud_compromise", "legal_action_threat"],
            "escalate_to_human": True,
            "escalation_priority": "P0-IMMEDIATE",
            "escalation_reason": "critical_risk_safety_override",
            "reply_draft": "Namaste. Aapki suraksha aur account safety humari sabse badi priority hai. Yeh case high-priority investigation ke liye security desk ko escalate kar diya gaya hai.",
            "status": TicketStatus.ESCALATED
        },
        {
            "raw_text": "Return parcel #REF-3312 pickup aayiduchu 3 days munnadi, aana refund innum credit aagala. Eppo kaasu varum?",
            "language_detected": "tanglish",
            "language_confidence": 0.91,
            "predicted_intent": "track_refund",
            "intent_category": "REFUND",
            "intent_confidence": 0.85,
            "intent_margin": 0.38,
            "urgency_level": UrgencyLevel.NORMAL,
            "urgency_score": 0.50,
            "urgency_reasons": ["standard_support_queue"],
            "escalate_to_human": False,
            "escalation_priority": "P3-ROUTINE",
            "escalation_reason": "none",
            "reply_draft": "Vanakkam. Unga refund request register seiyyapattathu. (Reference Order ID: #REF-3312). Accounts team verification mudithavudan status update anuppuvom.",
            "status": TicketStatus.PENDING_REVIEW
        },
        {
            "raw_text": "Need GST tax invoice for order #ORD-11029 for accounting records.",
            "language_detected": "english",
            "language_confidence": 0.95,
            "predicted_intent": "get_invoice",
            "intent_category": "INVOICE",
            "intent_confidence": 0.93,
            "intent_margin": 0.61,
            "urgency_level": UrgencyLevel.LOW,
            "urgency_score": 0.25,
            "urgency_reasons": ["routine_information_lookup"],
            "escalate_to_human": False,
            "escalation_priority": "P4-LOW",
            "escalation_reason": "none",
            "reply_draft": "Hello. Thank you for reaching out. (Reference Order ID: #ORD-11029). You can download your GST invoice directly from your order dashboard under documents.",
            "status": TicketStatus.RESOLVED,
            "agent_final_response": "Invoice copy sent to registered email address."
        },
        {
            "raw_text": "Password reset email link open nahi ho raha, expired token error aa raha hai bar bar.",
            "language_detected": "hinglish",
            "language_confidence": 0.88,
            "predicted_intent": "recover_password",
            "intent_category": "ACCOUNT",
            "intent_confidence": 0.81,
            "intent_margin": 0.35,
            "urgency_level": UrgencyLevel.NORMAL,
            "urgency_score": 0.50,
            "urgency_reasons": ["standard_support_queue"],
            "escalate_to_human": False,
            "escalation_priority": "P3-ROUTINE",
            "escalation_reason": "none",
            "reply_draft": "Namaste. Account access recover karne ke liye kripya registered email address par bheja gaya fresh password reset link use karein.",
            "status": TicketStatus.PENDING_REVIEW
        },
        {
            "raw_text": "Delivery address change panna mudiyuma? En veedu Chennai la irundhu Coimbatore-ku relocate aagiduchu. Order #ORD-77123.",
            "language_detected": "tanglish",
            "language_confidence": 0.93,
            "predicted_intent": "change_shipping_address",
            "intent_category": "SHIPPING",
            "intent_confidence": 0.84,
            "intent_margin": 0.42,
            "urgency_level": UrgencyLevel.NORMAL,
            "urgency_score": 0.50,
            "urgency_reasons": ["standard_support_queue"],
            "escalate_to_human": False,
            "escalation_priority": "P3-ROUTINE",
            "escalation_reason": "none",
            "reply_draft": "Vanakkam. Shipping address update request-ai review panrom. (Reference Order ID: #ORD-77123).",
            "status": TicketStatus.PENDING_REVIEW
        },
        {
            "raw_text": "Emergency! Tomorrow early morning flight at 6am. Passport holder order #ORD-55102 needs to be delivered today positively!",
            "language_detected": "english",
            "language_confidence": 0.92,
            "predicted_intent": "track_order",
            "intent_category": "ORDER",
            "intent_confidence": 0.83,
            "intent_margin": 0.36,
            "urgency_level": UrgencyLevel.HIGH,
            "urgency_score": 0.82,
            "urgency_reasons": ["explicit_urgency_keyword", "imminent_hard_deadline"],
            "escalate_to_human": True,
            "escalation_priority": "P1-HIGH",
            "escalation_reason": "imminent_hard_deadline",
            "reply_draft": "Hello. We understand your urgent travel timeline. (Reference Order ID: #ORD-55102). We have prioritized your parcel with our local delivery station dispatcher.",
            "status": TicketStatus.ESCALATED
        }
    ]

    for sample in demo_samples:
        save_ticket(sample)

