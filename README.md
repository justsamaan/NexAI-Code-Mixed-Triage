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

### B. Customer-Care Agent Workspace
- **Agent Profile & Availability**: Live toggle between `🟢 Online`, `🟡 Busy`, and `⚪ Offline`.
- **Language Capability Matching**: Agents declare their supported languages (e.g. Vikram handles Hindi, Telugu, and English; Anita handles Tamil and English).
- **Specialized Workspaces**:
  - `Customer Queries`: Central triage desk with Queue filtering (`All Authorized`, `Assigned to Me`, `Unassigned Queue`, `Awaiting Human Specialist`, `Escalated Only`), status updates, and interactive manual message analyzer.
  - `Live Sessions`: Direct two-way messaging between agents and active customers.
  - `Agent Reply Composer & Translator`: One-click translation of draft agent replies into the customer's preferred native language (Telugu, Tamil, Hindi) with review and edit capability before sending.
  - `Session Analytics`: Real-time operational KPI metrics, Intent distribution chart, Urgency distribution chart, Language distribution chart, and exportable session logs.
  - `Root-Cause Analysis`: Dedicated page diagnosing primary escalation drivers (duplicate debits, delivery delays > 48h, item damage), escalation rate by dialect, and low-confidence ambiguity cases (< 75% confidence).
  - `🧪 Evaluation Suite`: 47 benchmark test cases running against ground-truth code-mixed datasets with confusion matrices and performance metrics.

### C. Role-Based Access Control (RBAC)
- Strict access boundary enforced server-side. Customers can never access agent views or session data via URL parameters or navigation tampering.

---

## 3. Persistent Data Foundation (`database.py`)

Persistent SQLite database (`data/support_platform.db`) operating in **Write-Ahead Logging (WAL)** mode with indexed querying:
- `users`: User identity, hashed passwords, salts, roles (`customer`, `agent`, `admin`), supported languages, and availability.
- `conversations`: Support tickets, customer IDs, subject, status (`open`, `in_progress`, `resolved`, `closed`), urgency (`high`, `medium`, `low`), detected language, English translation, predicted intent, AI confidence, escalation status, assigned agent, `preferred_language`, `handoff_requested`, and `live_agent_joined`.
- `messages`: Chronological dialogue preserving distinction between `customer`, `agent`, `ai`, and `system` authors.
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

### 1. Phase 2 Platform Suite (`test_platform_phase2.py`)
```bash
python -m unittest test_platform_phase2.py
```
- **Tests run**: 6
- **Result**: `OK` (100% pass)
- Verifies: Native Tamil, Telugu, and Hindi script detection; agent reply translation; translation uncertainty handling; human handoff & agent matching; multi-role message threading; single feedback submission constraint.

### 2. Phase 1 Platform Suite (`test_platform_phase1.py`)
```bash
python -m unittest test_platform_phase1.py
```
- **Tests run**: 9
- **Result**: `OK` (100% pass)
- Verifies: PBKDF2 password hashing & salts, customer isolation, agent language authorization, availability status updates, conversation creation & AI triage, agent reply dispatch, feedback persistence, and root-cause metrics.

### 3. Application Unit Test Suite (`test_app.py`)
```bash
python -m unittest test_app.py
```
- **Tests run**: 12
- **Result**: `OK` (100% pass)
- Verifies: Schema count, AI output contract, Telugu+English detection, English translations, original message preservation, backwards-compatibility, and AppTest flows.

### 4. Code-Mixed Benchmark Evaluation Suite (`evaluate.py`)
```bash
python evaluate.py
```
- **Benchmark Test Cases**: 47 ground-truth tests across all 4 code-mixed dialects.
- **Pass Rate**: 100.0%
- **Intent Accuracy**: 100.0%
- **Urgency Accuracy**: 100.0%
- **Escalation Accuracy**: 100.0%

### 5. Service & Subsystem Tests (`pytest tests`)
```bash
python -m pytest tests
```
- **Tests run**: 39
- **Result**: `39 passed` (100% pass)
