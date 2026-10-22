# NexAI Multilingual Customer Support & Triage Platform
**NexAI Code-Mixed Support Triage Assistant**  
*Problem Statement 1.1 · Production-Ready Enterprise Platform*

---

## 1. Overview & Architectural Transformation

NexAI transforms customer support operations by accurately understanding, triaging, and translating code-mixed queries written in colloquial Indian dialects and native Indic scripts. The platform provides separate, role-based workflows for **Customers** and **Customer-Care Agents**, backed by an **Apple-inspired design system** and persistent SQLite storage.

### Supported Languages & Dialects
1. **Telugu + English (Tenglish / తెలుగు)**: Native script and Latin transliteration parsing (e.g. *"నా ఆర్డర్ ఇంకా డెలివరీ కాలేదు"*, *"naa order inka delivery avvaledu"*)
2. **Tamil + English (Tanglish / தமிழ்)**: Native script and Latin transliteration parsing (e.g. *"என் ஆர்டர் இன்னும் வரவில்லை"*, *"order vandhuchu but box damaged, refund venum"*)
3. **Hindi + English (Hinglish / हिन्दी)**: Native Devanagari and Latin transliteration (e.g. *"मेरा ऑर्डर अभी तक नहीं आया"*, *"mera paisa do baar cut gaya"*)
4. **Standard English**: Monolingual inquiries and formal support communications
5. **Auto-Detect & Code-Mixed Handling**: Zero-guesswork language classification preserving original text and flagging ambiguous inputs

---

## 2. Key Capabilities & Role Separation

### A. Customer Workspace
- **Secure Authentication & Registration**: PBKDF2-HMAC-SHA256 password hashing with unique per-user salts.
- **Data Privacy & Isolation**: Customers can view, manage, and reply exclusively to their own conversations.
- **Optional Language Selection**:
  - English
  - தமிழ் (Tamil)
  - తెలుగు (Telugu)
  - हिन्दी (Hindi)
  - Auto-Detect
  - Fast native script input chips for common queries.
- **Live Conversation Thread**:
  - Clean chat layout clearly distinguishing Customer, AI Assistant, Human Specialist, and System Dispatcher messages.
  - Real-time status indicators (`Open`, `In Progress`, `Resolved`).
  - Waiting banner when human assistance is requested.
  - Active specialist banner when an agent joins the conversation.
- **Post-Resolution Customer Feedback**:
  - 1-to-5 star rating with category selection.
  - Explanation comments.
  - Translation quality assessment (`Excellent`, `Good`, `Needs Improvement`, `Poor`).
  - Resolution confirmation (`Yes`, `Partially`, `No`).
  - Strictly enforced one-review-per-conversation constraint.

### B. Customer-Care Agent Workspace (Phase 3: Gmail-Inspired Ticket Inbox)
- **Top Summary Indicators & CSAT Progress Bar**:
  - Total received queries, resolved queries, pending queries, and active escalated flags.
  - Interactive popover dialog detailing exact open, in-progress, resolved, and closed counts.
  - Customer Satisfaction (CSAT) indicator with $0-100\%$ progress bar, quality badge (`Positive`, `Neutral`, `Negative`), documented formula ($\% \text{ of ratings } \ge 4\text{ stars}$), and exact sample size ($N$).
- **Gmail-Inspired 3-Area Ticket Inbox**:
  - **Left Folder Navigation**: 7 mailboxes with live dynamic ticket counts:
    - 📥 Inbox
    - 👤 Unassigned
    - 📌 Assigned to Me
    - ⏳ Waiting for Agent
    - 💬 Waiting for Customer
    - 🚨 Escalated
    - ✅ Resolved
  - **Main Ticket List**: Compact rows showing customer name/ID, short message preview, predicted intent, urgency indicator (restrained Red/Amber/Green), calibrated AI confidence percentage ($XX\%$, distinct from urgency), status, assigned agent, and last activity timestamp.
  - **Details Panel**: Opens alongside the inbox list in the main workspace without losing context.
- **Deterministic Sorting & Multidimensional Filtering**:
  - Sorting: *Latest queries first*, *Oldest queries first*, *Highest urgency first*, *Lowest confidence first*, *Most relevant*.
  - Filters: Intent, Urgency, Status, Dialect, Assigned Agent, and Escalation status.
  - Search: Full-text search across customer name, ticket ID, subject, English translation, and message history.
- **Agent Action & Resolution Controls**:
  - Edit AI-generated draft responses in English.
  - One-click translation of draft into customer's preferred language (Telugu, Tamil, Hindi) with review and edit before dispatch.
  - Clarification quick-template chips (Order ID request, damage photo request, payment reference request).
  - Takeover button to assume control of an AI-handled or unassigned conversation.
  - Ticket assignment and reassignment dropdown.
  - Resolution toggle: mark as resolved or reopen resolved tickets.
  - **Internal Staff Notes**: Private staff-only notes that persist in the thread and are strictly isolated from customer views.
- **Session Analytics (Section 7)**:
  - Real-time tracking of active sessions, waiting customers, human handoffs, resolution counts, and average response times.
  - Distribution charts for predicted intents and detected dialects.
  - Customer feedback and translation quality log table.

### C. Role-Based Access Control (RBAC)
- Strict access boundary enforced server-side. Customers can never access agent views or session data via URL parameters or navigation tampering.

---

## 3. Persistent Data Foundation (`database.py`)

Persistent SQLite database (`data/support_platform.db`) operating in **Write-Ahead Logging (WAL)** mode with indexed querying:
- `users`: User identity, hashed passwords, salts, roles (`customer`, `agent`, `admin`), supported languages, and availability.
- `conversations`: Support tickets, customer IDs, subject, status (`open`, `in_progress`, `resolved`, `closed`), urgency (`high`, `medium`, `low`), detected language, English translation, predicted intent, AI confidence, escalation status, assigned agent, `preferred_language`, `handoff_requested`, and `live_agent_joined`.
- `messages`: Chronological dialogue preserving distinction between `customer`, `agent`, `ai`, `system`, and `internal_note` authors.
- `feedback`: Customer ratings (1-5), categories, comments, `translation_quality`, `issue_resolved`, and assigned agent links.

---

## 4. Apple-Inspired Design System

Inspired by Apple's clean, premium, and restrained design principles:
- **Surfaces**: Crisp white cards (`#ffffff`) on soft off-white canvas (`#fbfbfd`) with subtle 1px borders (`#d2d2d7`) and restrained shadows.
- **Typography**: Apple system typography stack (`-apple-system, SF Pro Display, SF Pro Text`) complemented by `Noto Sans Tamil`, `Noto Sans Telugu`, and `Noto Sans Devanagari` for native script rendering.
- **Accents & Indicators**:
  - System Blue (`#0071e3`): Primary actions and customer messages.
  - Success Green (`#34c759` / `#1b8738`): Resolved status and low urgency.
  - Warning Amber (`#ff9500` / `#b25e00`): In-progress status and medium urgency.
  - Critical Red (`#ff3b30` / `#d70015`): Escalation banners and high urgency.
- **Visuals**: Clean icons, subtle pills, accessible contrast, and zero excessive gradients or animations.

---

## 5. Quick Start & Demo Instructions

### Starting the Application
```bash
streamlit run app.py
```

### Pre-Configured Demo Accounts
For maximum convenience during evaluation, judges can use either:
1. **One-Click Quick Sign-In Buttons** directly on the login screen or sidebar persona switcher.
2. **Manual Login Credentials**:

| Persona | Role | Username | Password | Languages Understood |
| :--- | :--- | :--- | :--- | :--- |
| **Priya Sharma** | Customer | `customer` | `DemoCustomer@2026` | Telugu + English, Hinglish, English |
| **Rahul Varma** | Customer | `rahul` | `DemoCustomer@2026` | Hinglish, English |
| **Vikram Patel** | Support Agent | `agent` | `DemoAgent@2026` | Telugu + English, Hinglish, English |
| **Anita Sundaram** | Support Agent | `anita` | `DemoAgent@2026` | Tanglish, English |

---

## 6. Verification & Automated Test Results

### 1. Phase 3 Platform Suite (`test_platform_phase3.py`)
```bash
python -m unittest test_platform_phase3.py
```
- **Tests run**: 8
- **Result**: `OK` (100% pass)
- Verifies: 7 mailbox folder counts; deterministic sorting (newest, oldest, highest urgency, lowest confidence); multidimensional filters and search; ticket assignment/reassignment; ticket resolution/reopening; internal notes customer isolation; CSAT calculation formula and sample size; resolved ticket feedback inspection.

### 2. Phase 2 Platform Suite (`test_platform_phase2.py`)
```bash
python -m unittest test_platform_phase2.py
```
- **Tests run**: 6
- **Result**: `OK` (100% pass)
- Verifies: Native Tamil, Telugu, and Hindi script detection; agent reply translation; translation uncertainty handling; human handoff & agent matching; multi-role message threading; single feedback submission constraint.

### 3. Phase 1 Platform Suite (`test_platform_phase1.py`)
```bash
python -m unittest test_platform_phase1.py
```
- **Tests run**: 9
- **Result**: `OK` (100% pass)
- Verifies: PBKDF2 password hashing & salts, customer isolation, agent language authorization, availability status updates, conversation creation & AI triage, agent reply dispatch, feedback persistence, and root-cause metrics.

### 4. Application Unit Test Suite (`test_app.py`)
```bash
python -m unittest test_app.py
```
- **Tests run**: 12
- **Result**: `OK` (100% pass)
- Verifies: Schema count, AI output contract, Telugu+English detection, English translations, original message preservation, backwards-compatibility, and AppTest flows.

### 5. Code-Mixed Benchmark Evaluation Suite (`evaluate.py`)
```bash
python evaluate.py
```
- **Benchmark Test Cases**: 47 ground-truth tests across all 4 code-mixed dialects.
- **Pass Rate**: 100.0%
- **Intent Accuracy**: 100.0%
- **Urgency Accuracy**: 100.0%
- **Escalation Accuracy**: 100.0%

### 6. Service & Subsystem Tests (`pytest tests`)
```bash
python -m pytest tests
```
- **Tests run**: 39
- **Result**: `39 passed` (100% pass)
