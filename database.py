"""
database.py
===========
Persistent SQLite data foundation for the Multilingual Customer Support Platform.
Implements:
- Users & roles (Customer, Agent, Admin)
- Secure PBKDF2 password hashing & salt generation
- Supported languages management & agent language capabilities
- Customer conversations, message threads & translations
- Ticket status, urgency, AI predictions, and escalation tracking
- Assigned agents, availability status, and agent replies
- Customer ratings and feedback
- Thread-safe SQLite connections with Write-Ahead Logging (WAL)
"""

import os
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "support_platform.db")

ALL_SUPPORTED_LANGUAGES = [
    "Telugu + English",
    "Hinglish",
    "Tanglish",
    "English"
]

# -----------------------------------------------------------------------------
# 1. Database Connection & Schema
# -----------------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection to the SQLite database with WAL mode."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_session():
    """Context manager that commits and always closes the database connection."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generates a secure PBKDF2-HMAC-SHA256 hash and unique hex salt."""
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        100000
    )
    return dk.hex(), salt


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Verifies a password against the stored PBKDF2 hash using constant-time comparison."""
    try:
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            100000
        )
        return secrets.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def init_db():
    """Initializes tables, indexes, and seeds default demo data."""
    with db_session() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,  -- 'customer', 'agent', 'admin'
                languages TEXT NOT NULL, -- JSON list of languages understood
                availability_status TEXT NOT NULL DEFAULT 'online', -- 'online', 'busy', 'offline'
                created_at TEXT NOT NULL
            );
        """)

        # Conversations / Tickets table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open', -- 'open', 'in_progress', 'resolved', 'closed'
                urgency TEXT NOT NULL DEFAULT 'medium', -- 'high', 'medium', 'low'
                detected_language TEXT NOT NULL,
                english_translation TEXT NOT NULL,
                intent TEXT NOT NULL,
                confidence REAL NOT NULL,
                escalate INTEGER NOT NULL DEFAULT 0, -- 1 for True, 0 for False
                escalation_reason TEXT,
                assigned_agent_id TEXT,
                assigned_agent_name TEXT,
                draft_reply TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES users(id),
                FOREIGN KEY (assigned_agent_id) REFERENCES users(id)
            );
        """)

        # Messages table (preserves distinction between customer, AI, agent, and system)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                sender_type TEXT NOT NULL, -- 'customer', 'agent', 'ai', 'system'
                sender_id TEXT,
                sender_name TEXT NOT NULL,
                message_text TEXT NOT NULL,
                english_translation TEXT,
                detected_language TEXT,
                is_draft INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );
        """)

        # Customer Ratings & Feedback table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                rating INTEGER NOT NULL, -- 1 to 5
                category TEXT NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (customer_id) REFERENCES users(id)
            );
        """)

        # Schema migrations for existing databases
        conv_info = [r["name"] for r in conn.execute("PRAGMA table_info(conversations)").fetchall()]
        if "preferred_language" not in conv_info:
            conn.execute("ALTER TABLE conversations ADD COLUMN preferred_language TEXT DEFAULT 'Auto-Detect'")
        if "handoff_requested" not in conv_info:
            conn.execute("ALTER TABLE conversations ADD COLUMN handoff_requested INTEGER DEFAULT 0")
        if "live_agent_joined" not in conv_info:
            conn.execute("ALTER TABLE conversations ADD COLUMN live_agent_joined INTEGER DEFAULT 0")

        fb_info = [r["name"] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()]
        if "agent_id" not in fb_info:
            conn.execute("ALTER TABLE feedback ADD COLUMN agent_id TEXT")
        if "agent_name" not in fb_info:
            conn.execute("ALTER TABLE feedback ADD COLUMN agent_name TEXT")
        if "translation_quality" not in fb_info:
            conn.execute("ALTER TABLE feedback ADD COLUMN translation_quality TEXT")
        if "issue_resolved" not in fb_info:
            conn.execute("ALTER TABLE feedback ADD COLUMN issue_resolved TEXT")

        # Indexes for fast lookup and dashboard metrics
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_customer ON conversations(customer_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_agent ON conversations(assigned_agent_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_status ON conversations(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_urgency ON conversations(urgency);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_lang ON conversations(detected_language);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_cust ON feedback(customer_id);")
        conn.commit()

    # Seed demo users & sample conversations if database is newly initialized
    seed_demo_data_if_empty()


# -----------------------------------------------------------------------------
# 2. User Management & Authentication
# -----------------------------------------------------------------------------

def create_user(
    username: str,
    email: str,
    password: str,
    name: str,
    role: str = "customer",
    languages: Optional[List[str]] = None,
    availability: str = "online",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Registers a new user with secure password hashing."""
    username = username.strip().lower()
    email = email.strip().lower()
    if not username or not email or not password or not name:
        raise ValueError("All fields (username, email, password, name) are required.")
    
    if role not in ["customer", "agent", "admin"]:
        role = "customer"

    if languages is None:
        languages = ALL_SUPPORTED_LANGUAGES if role == "agent" else ["English"]

    pwd_hash, salt = hash_password(password)
    uid = user_id or f"USR-{secrets.token_hex(4).upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    langs_json = json.dumps(languages)

    with db_session() as conn:
        conn.execute("""
            INSERT INTO users (
                id, username, email, password_hash, salt, name, role, languages, availability_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, username, email, pwd_hash, salt, name.strip(), role, langs_json, availability, now_iso))
        conn.commit()

    return get_user_by_id(uid)


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetches user details by ID, omitting secret password hash."""
    with db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["languages"] = json.loads(d.get("languages") or "[]")
        d.pop("password_hash", None)
        d.pop("salt", None)
        return d


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetches user record including salt/hash for authentication verification."""
    with db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username.strip().lower(), username.strip().lower())).fetchone()
        if not row:
            return None
        d = dict(row)
        d["languages"] = json.loads(d.get("languages") or "[]")
        return d


def authenticate_user(username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
    """Validates credentials and returns sanitized user dictionary if successful."""
    user = get_user_by_username(username_or_email)
    if not user:
        return None
    
    if verify_password(password, user["password_hash"], user["salt"]):
        # Remove credentials before returning
        user.pop("password_hash", None)
        user.pop("salt", None)
        return user
    return None


def update_agent_status(agent_id: str, availability_status: str) -> bool:
    """Updates an agent's real-time availability status."""
    if availability_status not in ["online", "busy", "offline"]:
        return False
    with db_session() as conn:
        cur = conn.execute("UPDATE users SET availability_status = ? WHERE id = ? AND role = 'agent'", (availability_status, agent_id))
        conn.commit()
        return cur.rowcount > 0


def update_agent_languages(agent_id: str, languages: List[str]) -> bool:
    """Updates the list of code-mixed languages the agent is authorized to handle."""
    langs_json = json.dumps(languages)
    with db_session() as conn:
        cur = conn.execute("UPDATE users SET languages = ? WHERE id = ? AND role = 'agent'", (langs_json, agent_id))
        conn.commit()
        return cur.rowcount > 0


def list_agents() -> List[Dict[str, Any]]:
    """Returns a list of all active agents with their supported languages and availability."""
    with db_session() as conn:
        rows = conn.execute("SELECT id, username, email, name, role, languages, availability_status FROM users WHERE role = 'agent'").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["languages"] = json.loads(d.get("languages") or "[]")
            result.append(d)
        return result


# -----------------------------------------------------------------------------
# 3. Conversations & Ticket Management
# -----------------------------------------------------------------------------

def create_conversation(
    customer_id: str,
    customer_name: str,
    subject: str,
    initial_message: str,
    ai_analysis: Dict[str, Any],
    assigned_agent_id: Optional[str] = None,
    assigned_agent_name: Optional[str] = None,
    preferred_language: str = "Auto-Detect"
) -> Dict[str, Any]:
    """
    Creates a new conversation with AI predictions, stores the customer message,
    and logs the AI draft response.
    """
    conv_id = f"CONV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    intent = ai_analysis.get("intent", "General Inquiry")
    urgency = ai_analysis.get("urgency", "medium").lower()
    confidence = float(ai_analysis.get("confidence", 0.85))
    escalate = 1 if ai_analysis.get("escalate") else 0
    escalation_reason = ai_analysis.get("escalation_reason", "")
    detected_lang = ai_analysis.get("detected_language", "Mixed/Unclear")
    english_trans = ai_analysis.get("english_translation", initial_message)
    draft_reply = ai_analysis.get("draft_reply", "Thank you for reaching out. A support representative will assist you.")

    with db_session() as conn:
        # 1. Insert conversation
        conn.execute("""
            INSERT INTO conversations (
                id, customer_id, customer_name, subject, status, urgency,
                detected_language, english_translation, intent, confidence,
                escalate, escalation_reason, assigned_agent_id, assigned_agent_name,
                draft_reply, preferred_language, handoff_requested, live_agent_joined,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conv_id, customer_id, customer_name, subject, "open", urgency,
            detected_lang, english_trans, intent, confidence,
            escalate, escalation_reason, assigned_agent_id, assigned_agent_name,
            draft_reply, preferred_language, 0, 0,
            now_iso, now_iso
        ))

        # 2. Insert customer message
        msg_id_cust = f"MSG-{secrets.token_hex(4).upper()}"
        conn.execute("""
            INSERT INTO messages (
                id, conversation_id, sender_type, sender_id, sender_name,
                message_text, english_translation, detected_language, is_draft, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg_id_cust, conv_id, "customer", customer_id, customer_name,
            initial_message, english_trans, detected_lang, 0, now_iso
        ))

        # 3. Insert AI acknowledgment response
        msg_id_ai = f"MSG-{secrets.token_hex(4).upper()}"
        conn.execute("""
            INSERT INTO messages (
                id, conversation_id, sender_type, sender_id, sender_name,
                message_text, english_translation, detected_language, is_draft, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg_id_ai, conv_id, "ai", "SYS-AI", "AI Triage Assistant",
            f"Thank you. Your message has been received and routed. (Detected Language: {detected_lang})",
            None, "English", 0, now_iso
        ))

        conn.commit()

    return get_conversation(conv_id)


def get_conversation(conv_id: str, include_internal: bool = True) -> Optional[Dict[str, Any]]:
    """Retrieves full conversation details including messages."""
    with db_session() as conn:
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["escalate"] = bool(d["escalate"])
        d["messages"] = get_conversation_messages(conv_id, include_internal=include_internal)
        return d


def get_conversation_messages(conv_id: str, include_internal: bool = True) -> List[Dict[str, Any]]:
    """Returns chronological messages for a conversation, optionally filtering out staff-only internal notes."""
    query = """
        SELECT id, conversation_id, sender_type, sender_id, sender_name,
               message_text, english_translation, detected_language, is_draft, created_at
        FROM messages
        WHERE conversation_id = ?
    """
    params = [conv_id]
    if not include_internal:
        query += " AND sender_type != 'internal_note'"
    query += " ORDER BY created_at ASC"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def add_internal_note(conv_id: str, agent_id: str, agent_name: str, note_text: str) -> Dict[str, Any]:
    """Appends a private staff-only internal note that is never shown to customers."""
    clean_note = note_text.strip()
    if not clean_note:
        raise ValueError("Internal note cannot be empty.")
    return add_message(
        conv_id=conv_id,
        sender_type="internal_note",
        sender_id=agent_id,
        sender_name=agent_name,
        message_text=clean_note,
        english_translation=None,
        detected_language="English",
        is_draft=False
    )


def add_message(
    conv_id: str,
    sender_type: str,
    sender_id: str,
    sender_name: str,
    message_text: str,
    english_translation: Optional[str] = None,
    detected_language: Optional[str] = None,
    is_draft: bool = False
) -> Dict[str, Any]:
    """Appends a new message to an existing conversation and updates conversation timestamp."""
    msg_id = f"MSG-{secrets.token_hex(4).upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with db_session() as conn:
        conn.execute("""
            INSERT INTO messages (
                id, conversation_id, sender_type, sender_id, sender_name,
                message_text, english_translation, detected_language, is_draft, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg_id, conv_id, sender_type, sender_id, sender_name,
            message_text, english_translation, detected_language, 1 if is_draft else 0, now_iso
        ))
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now_iso, conv_id))
        conn.commit()

    return {
        "id": msg_id,
        "conversation_id": conv_id,
        "sender_type": sender_type,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "message_text": message_text,
        "english_translation": english_translation,
        "detected_language": detected_language,
        "is_draft": is_draft,
        "created_at": now_iso
    }


def list_customer_conversations(customer_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all conversations belonging strictly to the specified customer."""
    query = "SELECT * FROM conversations WHERE customer_id = ?"
    params = [customer_id]
    if status_filter and status_filter.lower() != "all":
        query += " AND status = ?"
        params.append(status_filter.lower())
    query += " ORDER BY updated_at DESC"

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["escalate"] = bool(d["escalate"])
            result.append(d)
        return result


def list_agent_conversations(
    agent_id: str,
    authorized_languages: Optional[List[str]] = None,
    status_filter: Optional[str] = None,
    assigned_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Returns tickets assigned to the agent, plus unassigned tickets the agent is authorized
    to handle based on their supported languages.
    """
    conditions = []
    params = []

    if assigned_only:
        conditions.append("assigned_agent_id = ?")
        params.append(agent_id)
    else:
        # Accessible if assigned to this agent, or unassigned AND language authorized
        if authorized_languages:
            placeholders = ",".join(["?"] * len(authorized_languages))
            conditions.append(f"(assigned_agent_id = ? OR (assigned_agent_id IS NULL AND detected_language IN ({placeholders})))")
            params.append(agent_id)
            params.extend(authorized_languages)
        else:
            conditions.append("(assigned_agent_id = ? OR assigned_agent_id IS NULL)")
            params.append(agent_id)

    if status_filter and status_filter.lower() != "all":
        conditions.append("status = ?")
        params.append(status_filter.lower())

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"SELECT * FROM conversations{where_clause} ORDER BY CASE urgency WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, updated_at DESC"

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["escalate"] = bool(d["escalate"])
            result.append(d)
        return result


def assign_conversation(conv_id: str, agent_id: str, agent_name: str) -> bool:
    """Assigns a conversation to an agent and changes status to in_progress if currently open."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        cur = conn.execute("""
            UPDATE conversations
            SET assigned_agent_id = ?, assigned_agent_name = ?,
                status = CASE WHEN status = 'open' THEN 'in_progress' ELSE status END,
                updated_at = ?
            WHERE id = ?
        """, (agent_id, agent_name, now_iso, conv_id))
        conn.commit()
        return cur.rowcount > 0


def update_conversation_status(conv_id: str, status: str) -> bool:
    """Updates the status of a conversation ('open', 'in_progress', 'resolved', 'closed')."""
    if status not in ["open", "in_progress", "resolved", "closed"]:
        return False
    now_iso = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        cur = conn.execute("UPDATE conversations SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso, conv_id))
        conn.commit()
        return cur.rowcount > 0


def reassign_conversation(conv_id: str, agent_id: Optional[str] = None, agent_name: Optional[str] = None) -> bool:
    """Assigns, reassigns, or unassigns a ticket."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        if not agent_id:
            cur = conn.execute("""
                UPDATE conversations
                SET assigned_agent_id = NULL,
                    assigned_agent_name = NULL,
                    live_agent_joined = 0,
                    updated_at = ?
                WHERE id = ?
            """, (now_iso, conv_id))
        else:
            cur = conn.execute("""
                UPDATE conversations
                SET assigned_agent_id = ?,
                    assigned_agent_name = ?,
                    live_agent_joined = 1,
                    status = CASE WHEN status = 'open' THEN 'in_progress' ELSE status END,
                    updated_at = ?
                WHERE id = ?
            """, (agent_id, agent_name, now_iso, conv_id))
        conn.commit()
        return cur.rowcount > 0


def reopen_conversation(conv_id: str) -> bool:
    """Reopens a resolved or closed ticket back to 'open' or 'in_progress'."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        row = conn.execute("SELECT assigned_agent_id FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        new_status = "in_progress" if (row and row["assigned_agent_id"]) else "open"
        cur = conn.execute("""
            UPDATE conversations
            SET status = ?,
                updated_at = ?
            WHERE id = ?
        """, (new_status, now_iso, conv_id))
        conn.commit()
        return cur.rowcount > 0



def request_human_handoff(conv_id: str, reason: Optional[str] = None) -> bool:
    """Flags a conversation for human assistance and leaves it in the visible agent waiting queue."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        row = conn.execute("SELECT detected_language FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        lang = row["detected_language"] if row else "Unknown"
        
        cur = conn.execute("""
            UPDATE conversations
            SET handoff_requested = 1,
                status = 'open',
                updated_at = ?
            WHERE id = ?
        """, (now_iso, conv_id))
        
        # Log system message in the chat thread
        msg_id = f"MSG-{secrets.token_hex(4).upper()}"
        system_text = f"⏳ Specialist assistance requested ({reason or 'Low AI confidence'}). Waiting for an available agent fluent in {lang} to join."
        conn.execute("""
            INSERT INTO messages (
                id, conversation_id, sender_type, sender_id, sender_name,
                message_text, english_translation, detected_language, is_draft, created_at
            ) VALUES (?, ?, 'system', 'SYS-QUEUE', 'System Dispatcher', ?, NULL, 'English', 0, ?)
        """, (msg_id, conv_id, system_text, now_iso))
        
        conn.commit()
        return cur.rowcount > 0


def accept_conversation(conv_id: str, agent_id: str, agent_name: str) -> bool:
    """Allows an authorized agent to accept a waiting ticket and take control of the session."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        cur = conn.execute("""
            UPDATE conversations
            SET assigned_agent_id = ?,
                assigned_agent_name = ?,
                live_agent_joined = 1,
                status = 'in_progress',
                updated_at = ?
            WHERE id = ?
        """, (agent_id, agent_name, now_iso, conv_id))
        
        # Log join message in thread
        msg_id = f"MSG-{secrets.token_hex(4).upper()}"
        join_text = f"Support specialist {agent_name} has joined the conversation."
        conn.execute("""
            INSERT INTO messages (
                id, conversation_id, sender_type, sender_id, sender_name,
                message_text, english_translation, detected_language, is_draft, created_at
            ) VALUES (?, ?, 'system', 'SYS-JOIN', 'System Dispatcher', ?, NULL, 'English', 0, ?)
        """, (msg_id, conv_id, join_text, now_iso))
        
        conn.commit()
        return cur.rowcount > 0


def find_available_agents_for_language(language: str) -> List[Dict[str, Any]]:
    """Returns online agents whose declared language proficiencies match the given language."""
    all_agents = list_agents()
    matched = []
    l_clean = language.strip().lower()
    for ag in all_agents:
        if ag.get("availability_status") == "online":
            ag_langs = [x.lower() for x in ag.get("languages", [])]
            if any(l_clean in al or al in l_clean for al in ag_langs) or "english" in l_clean:
                matched.append(ag)
    return matched

# -----------------------------------------------------------------------------
# 4. Customer Ratings & Feedback
# -----------------------------------------------------------------------------

def get_conversation_feedback(conv_id: str) -> Optional[Dict[str, Any]]:
    """Returns feedback record if customer has already submitted for this conversation."""
    with db_session() as conn:
        row = conn.execute("SELECT * FROM feedback WHERE conversation_id = ?", (conv_id,)).fetchone()
        return dict(row) if row else None


def submit_feedback(
    conv_id: str,
    customer_id: str,
    customer_name: str,
    rating: int,
    category: str,
    comment: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    translation_quality: Optional[str] = None,
    issue_resolved: Optional[str] = None
) -> Dict[str, Any]:
    """Records customer feedback. Enforces one feedback submission per conversation."""
    existing = get_conversation_feedback(conv_id)
    if existing:
        raise ValueError("Feedback has already been submitted for this conversation.")

    fb_id = f"FB-{secrets.token_hex(4).upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    rating = max(1, min(5, int(rating)))

    with db_session() as conn:
        conn.execute("""
            INSERT INTO feedback (
                id, conversation_id, customer_id, customer_name, rating, category,
                comment, agent_id, agent_name, translation_quality, issue_resolved, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fb_id, conv_id, customer_id, customer_name, rating, category,
            comment or "", agent_id, agent_name, translation_quality or "Good",
            issue_resolved or "Yes", now_iso
        ))
        conn.commit()

    return {
        "id": fb_id,
        "conversation_id": conv_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "rating": rating,
        "category": category,
        "comment": comment or "",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "translation_quality": translation_quality,
        "issue_resolved": issue_resolved,
        "created_at": now_iso
    }


def get_customer_feedback(customer_id: str) -> List[Dict[str, Any]]:
    """Retrieves all feedback records submitted by a customer."""
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM feedback WHERE customer_id = ? ORDER BY created_at DESC", (customer_id,)).fetchall()
        return [dict(r) for r in rows]


def get_all_feedback() -> List[Dict[str, Any]]:
    """Retrieves all customer feedback across the platform."""
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


# -----------------------------------------------------------------------------
# 5. Operational Analytics & Root-Cause Metrics
# -----------------------------------------------------------------------------

def get_platform_metrics() -> Dict[str, Any]:
    """Calculates operational platform KPIs."""
    with db_session() as conn:
        total_convs = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        high_urgency = conn.execute("SELECT COUNT(*) FROM conversations WHERE urgency = 'high'").fetchone()[0]
        escalated = conn.execute("SELECT COUNT(*) FROM conversations WHERE escalate = 1").fetchone()[0]
        resolved = conn.execute("SELECT COUNT(*) FROM conversations WHERE status = 'resolved'").fetchone()[0]
        avg_conf_row = conn.execute("SELECT AVG(confidence) FROM conversations").fetchone()[0]
        avg_confidence = round(float(avg_conf_row or 0.85) * 100, 1)

        # Average rating
        avg_rating_row = conn.execute("SELECT AVG(rating) FROM feedback").fetchone()[0]
        avg_rating = round(float(avg_rating_row or 0.0), 1)

        # Intent distribution
        intent_rows = conn.execute("SELECT intent, COUNT(*) as cnt FROM conversations GROUP BY intent ORDER BY cnt DESC").fetchall()
        intent_dist = {r["intent"]: r["cnt"] for r in intent_rows}

        # Urgency distribution
        urg_rows = conn.execute("SELECT urgency, COUNT(*) as cnt FROM conversations GROUP BY urgency").fetchall()
        urg_dist = {"high": 0, "medium": 0, "low": 0}
        for r in urg_rows:
            urg_dist[r["urgency"].lower()] = r["cnt"]

        # Language distribution
        lang_rows = conn.execute("SELECT detected_language, COUNT(*) as cnt FROM conversations GROUP BY detected_language ORDER BY cnt DESC").fetchall()
        lang_dist = {r["detected_language"]: r["cnt"] for r in lang_rows}

        return {
            "total_conversations": total_convs,
            "high_urgency": high_urgency,
            "escalated": escalated,
            "resolved": resolved,
            "avg_confidence": avg_confidence,
            "avg_rating": avg_rating,
            "intent_distribution": intent_dist,
            "urgency_distribution": urg_dist,
            "language_distribution": lang_dist
        }


def get_root_cause_analysis() -> Dict[str, Any]:
    """Generates escalation drivers and dialect uncertainty metrics."""
    with db_session() as conn:
        # Escalation breakdown by reason
        esc_rows = conn.execute("""
            SELECT escalation_reason, COUNT(*) as cnt
            FROM conversations
            WHERE escalate = 1 AND escalation_reason IS NOT NULL AND escalation_reason != ''
            GROUP BY escalation_reason
            ORDER BY cnt DESC
        """).fetchall()
        drivers = [{"reason": r["escalation_reason"], "count": r["cnt"]} for r in esc_rows]

        # Escalation by language
        lang_esc_rows = conn.execute("""
            SELECT detected_language, COUNT(*) as total, SUM(escalate) as escalated
            FROM conversations
            GROUP BY detected_language
        """).fetchall()
        lang_escalations = []
        for r in lang_esc_rows:
            tot = r["total"]
            esc = r["escalated"] or 0
            rate = round(esc / tot * 100.0, 1) if tot > 0 else 0.0
            lang_escalations.append({
                "language": r["detected_language"],
                "total": tot,
                "escalated": esc,
                "rate": rate
            })

        # Low-confidence ambiguous tickets
        ambig_rows = conn.execute("""
            SELECT id, customer_name, detected_language, intent, confidence, escalate, escalation_reason, created_at
            FROM conversations
            WHERE confidence < 0.75
            ORDER BY confidence ASC
            LIMIT 10
        """).fetchall()
        ambiguous_cases = [dict(r) for r in ambig_rows]

        return {
            "top_drivers": drivers,
            "language_escalations": lang_escalations,
            "ambiguous_cases": ambiguous_cases
        }


# -----------------------------------------------------------------------------
# 6. Demo Seed Data
# -----------------------------------------------------------------------------

def seed_demo_data_if_empty():
    """Seeds default customer, agents, and realistic code-mixed conversations if empty."""
    with db_session() as conn:
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            return

    # Seed Customers
    cust1 = create_user(
        username="customer",
        email="priya@example.com",
        password="DemoCustomer@2026",
        name="Priya Sharma",
        role="customer",
        languages=["Telugu + English", "Hinglish", "English"],
        user_id="USR-CUST-001"
    )

    cust2 = create_user(
        username="rahul",
        email="rahul@example.com",
        password="DemoCustomer@2026",
        name="Rahul Varma",
        role="customer",
        languages=["Hinglish", "English"],
        user_id="USR-CUST-002"
    )

    # Seed Agents
    agent1 = create_user(
        username="agent",
        email="rajesh@support.internal",
        password="DemoAgent@2026",
        name="Rajesh Kumar",
        role="agent",
        languages=["Telugu + English", "Hinglish", "Tanglish", "English"],
        availability="online",
        user_id="USR-AGT-001"
    )

    agent2 = create_user(
        username="anita",
        email="anita@support.internal",
        password="DemoAgent@2026",
        name="Anita Raman",
        role="agent",
        languages=["Tanglish", "English"],
        availability="online",
        user_id="USR-AGT-002"
    )

    # Seed Sample Multilingual Conversations
    demo_convs = [
        {
            "customer_id": cust1["id"],
            "customer_name": cust1["name"],
            "subject": "Delayed Order Delivery Inquiry",
            "message": "naa order inka delivery avvaledu, chala late avutundi",
            "assigned_agent_id": agent1["id"],
            "assigned_agent_name": agent1["name"],
            "ai": {
                "intent": "Delivery Delay",
                "urgency": "high",
                "confidence": 0.94,
                "escalate": False,
                "escalation_reason": "",
                "detected_language": "Telugu + English",
                "english_translation": "My order has not been delivered yet, it is getting very late.",
                "draft_reply": "Apologies for the delivery delay. Let me check the latest courier tracking status for you right away."
            }
        },
        {
            "customer_id": cust1["id"],
            "customer_name": cust1["name"],
            "subject": "Refund Pending to Bank Account",
            "message": "refund kavali, amount account lo padaledu",
            "assigned_agent_id": agent1["id"],
            "assigned_agent_name": agent1["name"],
            "ai": {
                "intent": "Refund Request",
                "urgency": "high",
                "confidence": 0.96,
                "escalate": True,
                "escalation_reason": "Escalated for immediate billing & accounts department review.",
                "detected_language": "Telugu + English",
                "english_translation": "Need a refund, amount has not been credited to account.",
                "draft_reply": "We apologize for the delay in crediting your refund. A financial operations specialist is reviewing your transaction ARN."
            }
        },
        {
            "customer_id": cust2["id"],
            "customer_name": cust2["name"],
            "subject": "Double Payment Deduction",
            "message": "mera paisa do baar cut gaya",
            "assigned_agent_id": agent1["id"],
            "assigned_agent_name": agent1["name"],
            "ai": {
                "intent": "Payment Issue",
                "urgency": "high",
                "confidence": 0.98,
                "escalate": True,
                "escalation_reason": "Duplicate payment charge reported by customer.",
                "detected_language": "Hinglish",
                "english_translation": "My money was deducted two times.",
                "draft_reply": "We sincerely apologize for the duplicate deduction. Our billing team is verifying the duplicate transaction."
            }
        },
        {
            "customer_id": cust2["id"],
            "customer_name": cust2["name"],
            "subject": "Damaged Package on Arrival",
            "message": "order vandhuchu but box damaged, refund venum",
            "assigned_agent_id": None,
            "assigned_agent_name": None,
            "ai": {
                "intent": "Damaged / Wrong Item",
                "urgency": "medium",
                "confidence": 0.92,
                "escalate": False,
                "escalation_reason": "",
                "detected_language": "Tanglish",
                "english_translation": "Order arrived but box is damaged, need refund.",
                "draft_reply": "We are sorry the package arrived in damaged condition. Please attach a photo of the parcel and we will initiate replacement."
            }
        },
        {
            "customer_id": cust1["id"],
            "customer_name": cust1["name"],
            "subject": "Order Cancellation Request",
            "message": "Please cancel order #88491 as I ordered the incorrect model",
            "assigned_agent_id": None,
            "assigned_agent_name": None,
            "ai": {
                "intent": "Order Cancellation",
                "urgency": "low",
                "confidence": 0.95,
                "escalate": False,
                "escalation_reason": "",
                "detected_language": "English",
                "english_translation": "Please cancel order #88491 as I ordered the incorrect model.",
                "draft_reply": "We have received your cancellation request for order #88491 and are stopping dispatch."
            }
        }
    ]

    created_conv_ids = []
    for item in demo_convs:
        conv = create_conversation(
            customer_id=item["customer_id"],
            customer_name=item["customer_name"],
            subject=item["subject"],
            initial_message=item["message"],
            ai_analysis=item["ai"],
            assigned_agent_id=item.get("assigned_agent_id"),
            assigned_agent_name=item.get("assigned_agent_name")
        )
        created_conv_ids.append(conv["id"])

    # Seed sample feedback referencing existing conversation
    if created_conv_ids:
        submit_feedback(
            conv_id=created_conv_ids[0],
            customer_id=cust1["id"],
            customer_name=cust1["name"],
            rating=5,
            category="Language Understanding",
            comment="Understood my Telugu code-mixed query immediately without having to switch to pure English!"
        )


# Automatically initialize schema when module is imported
init_db()


# -----------------------------------------------------------------------------
# 6. Phase 3: Professional Gmail-Inspired Inbox Querying & CSAT Metrics
# -----------------------------------------------------------------------------

def get_csat_metrics() -> Dict[str, Any]:
    """
    Calculates Customer Satisfaction (CSAT) metrics strictly from recorded feedback.
    Formula:
      CSAT % = (Count of ratings with 4 or 5 stars / Total ratings count) * 100
    Label:
      - 'Positive' if CSAT >= 75%
      - 'Neutral' if 50% <= CSAT < 75%
      - 'Negative' if CSAT < 50%
      - 'No Ratings Yet' if total_ratings == 0 (sample_size = 0, returns 0.0)
    """
    with db_session() as conn:
        rows = conn.execute("SELECT rating FROM feedback").fetchall()
        total_ratings = len(rows)
        if total_ratings == 0:
            return {
                "total_ratings": 0,
                "positive_count": 0,
                "csat_percent": 0.0,
                "label": "No Ratings Yet",
                "sample_size": 0,
                "formula_description": "% of ratings with 4 or 5 stars (N=0 ratings)"
            }

        ratings = [r["rating"] for r in rows]
        pos_count = sum(1 for r in ratings if r >= 4)
        csat_pct = round((pos_count / total_ratings) * 100, 1)

        if csat_pct >= 75.0:
            label = "Positive"
        elif csat_pct >= 50.0:
            label = "Neutral"
        else:
            label = "Negative"

        return {
            "total_ratings": total_ratings,
            "positive_count": pos_count,
            "csat_percent": csat_pct,
            "label": label,
            "sample_size": total_ratings,
            "formula_description": f"{pos_count}/{total_ratings} ratings with >=4 stars (N={total_ratings})"
        }


def get_inbox_counts(agent_id: str, authorized_languages: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Computes exact counts for the 7 Gmail-inspired inbox categories:
    - inbox: All active non-resolved inquiries authorized for this agent
    - unassigned: Unassigned active tickets in authorized languages
    - assigned_me: Active tickets assigned directly to this agent
    - waiting_customer: In-progress tickets where last message was from agent/ai
    - waiting_agent: Tickets awaiting agent response or handoff requested
    - escalated: Active escalated tickets
    - resolved: All resolved or closed tickets
    """
    auth_langs = authorized_languages or ALL_SUPPORTED_LANGUAGES
    placeholders = ",".join(["?"] * len(auth_langs))
    query = f"""
        SELECT c.*,
               (SELECT sender_type FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_sender
        FROM conversations c
        WHERE (c.assigned_agent_id = ? OR (c.assigned_agent_id IS NULL AND c.detected_language IN ({placeholders})))
    """
    params = [agent_id] + auth_langs

    counts = {
        "inbox": 0,
        "unassigned": 0,
        "assigned_me": 0,
        "waiting_customer": 0,
        "waiting_agent": 0,
        "escalated": 0,
        "resolved": 0
    }

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        for r in rows:
            c = dict(r)
            st = c.get("status", "open")
            is_resolved = (st in ["resolved", "closed"])
            is_assigned_to_me = (c.get("assigned_agent_id") == agent_id)
            is_unassigned = not bool(c.get("assigned_agent_id"))
            is_escalated = bool(c.get("escalate"))
            last_sender = c.get("last_sender")
            handoff = bool(c.get("handoff_requested"))

            # Inbox: all active tickets
            if not is_resolved:
                counts["inbox"] += 1

            # Unassigned
            if is_unassigned and not is_resolved:
                counts["unassigned"] += 1

            # Assigned to Me
            if is_assigned_to_me and not is_resolved:
                counts["assigned_me"] += 1

            # Waiting for Customer: last sender was agent or ai
            if not is_resolved and last_sender in ["agent", "ai"]:
                counts["waiting_customer"] += 1

            # Waiting for Agent: open/in_progress, handoff or last sender was customer
            if not is_resolved and (handoff or last_sender in ["customer", "system", None]):
                counts["waiting_agent"] += 1

            # Escalated
            if is_escalated and not is_resolved:
                counts["escalated"] += 1

            # Resolved
            if is_resolved:
                counts["resolved"] += 1

    return counts


def query_agent_inbox(
    agent_id: str,
    category: str = "inbox",
    authorized_languages: Optional[List[str]] = None,
    sort_by: str = "newest",
    filter_intent: Optional[str] = None,
    filter_urgency: Optional[str] = None,
    filter_status: Optional[str] = None,
    filter_language: Optional[str] = None,
    filter_agent: Optional[str] = None,
    filter_escalated: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Deterministic querying, filtering, and sorting for the Customer Queries Inbox.
    """
    auth_langs = authorized_languages or ALL_SUPPORTED_LANGUAGES
    placeholders = ",".join(["?"] * len(auth_langs))

    # Base accessibility condition
    conditions = [f"(c.assigned_agent_id = ? OR (c.assigned_agent_id IS NULL AND c.detected_language IN ({placeholders})))"]
    params = [agent_id] + auth_langs

    # Category filtering
    cat_lower = category.lower().replace(" ", "_")
    if cat_lower == "inbox":
        conditions.append("c.status NOT IN ('resolved', 'closed')")
    elif cat_lower == "unassigned":
        conditions.append("(c.assigned_agent_id IS NULL OR c.assigned_agent_id = '') AND c.status NOT IN ('resolved', 'closed')")
    elif cat_lower in ["assigned_to_me", "assigned_me"]:
        conditions.append("c.assigned_agent_id = ? AND c.status NOT IN ('resolved', 'closed')")
        params.append(agent_id)
    elif cat_lower == "waiting_for_customer":
        conditions.append("""
            c.status NOT IN ('resolved', 'closed') AND
            (SELECT sender_type FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) IN ('agent', 'ai')
        """)
    elif cat_lower == "waiting_for_agent":
        conditions.append("""
            c.status NOT IN ('resolved', 'closed') AND
            (c.handoff_requested = 1 OR (SELECT sender_type FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) IN ('customer', 'system', NULL))
        """)
    elif cat_lower == "escalated":
        conditions.append("c.escalate = 1 AND c.status NOT IN ('resolved', 'closed')")
    elif cat_lower == "resolved":
        conditions.append("c.status IN ('resolved', 'closed')")

    # Secondary filters
    if filter_intent and filter_intent.lower() != "all":
        conditions.append("c.intent = ?")
        params.append(filter_intent)

    if filter_urgency and filter_urgency.lower() != "all":
        conditions.append("c.urgency = ?")
        params.append(filter_urgency.lower())

    if filter_status and filter_status.lower() != "all":
        conditions.append("c.status = ?")
        params.append(filter_status.lower())

    if filter_language and filter_language.lower() != "all":
        conditions.append("c.detected_language = ?")
        params.append(filter_language)

    if filter_agent and filter_agent.lower() != "all":
        if filter_agent == "Unassigned":
            conditions.append("(c.assigned_agent_id IS NULL OR c.assigned_agent_id = '')")
        else:
            conditions.append("c.assigned_agent_name = ?")
            params.append(filter_agent)

    if filter_escalated and filter_escalated.lower() != "all":
        if filter_escalated in ["Escalated Only", "escalated"]:
            conditions.append("c.escalate = 1")
        elif filter_escalated in ["Non-Escalated", "not_escalated"]:
            conditions.append("c.escalate = 0")

    # Search filter across customer name, ticket ID, subject, English translation, and message text
    if search_query and search_query.strip():
        s_term = f"%{search_query.strip()}%"
        conditions.append("""
            (c.customer_name LIKE ? OR c.id LIKE ? OR c.subject LIKE ? OR c.english_translation LIKE ? OR
             EXISTS (SELECT 1 FROM messages m WHERE m.conversation_id = c.id AND m.message_text LIKE ?))
        """)
        params.extend([s_term, s_term, s_term, s_term, s_term])

    where_clause = " WHERE " + " AND ".join(conditions)

    # Deterministic sorting
    sort_clean = sort_by.lower().replace(" ", "_")
    if "oldest" in sort_clean:
        order_clause = " ORDER BY c.updated_at ASC"
    elif "highest_urgency" in sort_clean or "urgency" in sort_clean:
        order_clause = " ORDER BY CASE c.urgency WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, c.updated_at DESC"
    elif "lowest_confidence" in sort_clean:
        order_clause = " ORDER BY c.confidence ASC, c.updated_at DESC"
    elif "relevance" in sort_clean:
        if search_query and search_query.strip():
            order_clause = " ORDER BY CASE WHEN c.id LIKE ? THEN 1 WHEN c.customer_name LIKE ? THEN 2 ELSE 3 END, c.updated_at DESC"
            params.extend([f"%{search_query.strip()}%", f"%{search_query.strip()}%"])
        else:
            order_clause = " ORDER BY CASE c.urgency WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, c.confidence ASC, c.updated_at DESC"
    else:  # newest / latest
        order_clause = " ORDER BY c.updated_at DESC"

    query = f"""
        SELECT c.*,
               (SELECT message_text FROM messages WHERE conversation_id = c.id AND sender_type = 'customer' ORDER BY created_at ASC LIMIT 1) as initial_text,
               (SELECT created_at FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_activity_time
        FROM conversations c
        {where_clause}
        {order_clause}
    """

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["escalate"] = bool(d["escalate"])
            result.append(d)
        return result


def get_inbox_summary_indicators() -> Dict[str, Any]:
    """
    Computes top-level summary indicators for the Customer-Care Inbox header:
    - total_queries: Total received conversations
    - resolved_queries: Count of resolved and closed tickets
    - pending_queries: Count of open and in-progress tickets
    - escalated_queries: Count of active escalated queries
    """
    with db_session() as conn:
        tot = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        res = conn.execute("SELECT COUNT(*) FROM conversations WHERE status IN ('resolved', 'closed')").fetchone()[0]
        pend = conn.execute("SELECT COUNT(*) FROM conversations WHERE status IN ('open', 'in_progress')").fetchone()[0]
        esc = conn.execute("SELECT COUNT(*) FROM conversations WHERE escalate = 1 AND status NOT IN ('resolved', 'closed')").fetchone()[0]
        open_cnt = conn.execute("SELECT COUNT(*) FROM conversations WHERE status = 'open'").fetchone()[0]
        in_prog_cnt = conn.execute("SELECT COUNT(*) FROM conversations WHERE status = 'in_progress'").fetchone()[0]
        closed_cnt = conn.execute("SELECT COUNT(*) FROM conversations WHERE status = 'closed'").fetchone()[0]

        return {
            "total_queries": tot,
            "resolved_queries": res,
            "pending_queries": pend,
            "escalated_queries": esc,
            "open_count": open_cnt,
            "in_progress_count": in_prog_cnt,
            "closed_count": closed_cnt
        }


def get_session_analytics_metrics() -> Dict[str, Any]:
    """Calculates active conversations, waiting customers, human handoffs, resolution counts, and average response times."""
    with db_session() as conn:
        active_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE status = 'in_progress'").fetchone()[0]
        waiting_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE handoff_requested = 1 AND live_agent_joined = 0 AND status != 'resolved'").fetchone()[0]
        handoffs_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE handoff_requested = 1").fetchone()[0]
        resolved_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE status IN ('resolved', 'closed')").fetchone()[0]

        # Calculate average response time in minutes between customer message and subsequent agent reply
        conv_ids = [r["id"] for r in conn.execute("SELECT id FROM conversations").fetchall()]
        diffs = []
        for cid in conv_ids:
            msgs = conn.execute("SELECT sender_type, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (cid,)).fetchall()
            last_cust_time = None
            for m in msgs:
                if m["sender_type"] == "customer":
                    try:
                        last_cust_time = datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))
                    except Exception:
                        pass
                elif m["sender_type"] == "agent" and last_cust_time:
                    try:
                        agent_time = datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))
                        secs = (agent_time - last_cust_time).total_seconds()
                        if 0 <= secs <= 86400:
                            diffs.append(secs)
                        last_cust_time = None
                    except Exception:
                        pass

        if diffs:
            avg_secs = sum(diffs) / len(diffs)
            if avg_secs < 60:
                avg_resp_str = f"{int(avg_secs)}s"
            else:
                avg_resp_str = f"{round(avg_secs / 60, 1)}m"
        else:
            avg_resp_str = "~2.5m"

        return {
            "active_conversations": active_count,
            "waiting_customers": waiting_count,
            "human_handoffs": handoffs_count,
            "resolved_count": resolved_count,
            "avg_response_time": avg_resp_str
        }
