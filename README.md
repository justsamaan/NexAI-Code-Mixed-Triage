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
- **Optional Language Selection**: English, தமிழ் (Tamil), తెలుగు (Telugu), हिन्दी (Hindi), and Auto-Detect with fast native script input chips.
- **Live Conversation Thread**: Clean chat layout distinguishing Customer, AI Assistant, Human Specialist, and System Dispatcher messages with waiting and joined banners.
- **Post-Resolution Customer Feedback**: 1-to-5 star rating, explanation comment, translation quality review, and issue resolution status with enforced single submission.

### B. Customer-Care Agent Workspace (Phase 3: Gmail-Inspired Inbox)
- **Top Summary Indicators & CSAT Progress Bar**: Total received, resolved, pending, and active escalated queries with popover status breakdown and CSAT progress bar ($\text{CSAT \%} = \frac{\text{Ratings } \ge 4}{\text{Total}} \times 100\%$).
- **Gmail-Inspired 3-Area Ticket Inbox**:
  - **Left Folder Navigation**: 7 mailboxes with live dynamic ticket counts (📥 Inbox, 👤 Unassigned, 📌 Assigned to Me, ⏳ Waiting for Agent, 💬 Waiting for Customer, 🚨 Escalated, ✅ Resolved).
  - **Main Ticket List**: Compact rows with customer name, preview, intent, urgency indicators, calibrated confidence percentage, status, agent, and timestamps.
  - **Details Panel**: Side-by-side inspection without losing inbox context.
- **Deterministic Sorting & Multidimensional Filtering**: Latest/oldest, highest urgency, lowest confidence, relevance sorting, and filters for intent, urgency, status, language, agent, and full-text search.
- **Agent Action & Reply Controls**: Editable draft responses, one-click translation to customer's dialect, clarification quick-templates, ticket takeover, reassignment, resolution toggle, and **private staff internal notes** hidden from customers.
- **Session Analytics**: Active sessions, waiting customers, human handoffs, resolution counts, and average response times.

### C. Root-Cause Analysis & Complaint Trends Dashboard (Phase 4)
- **Dedicated Executive Console**: Separate from Customer Queries, with navigation back to the inbox.
- **Overview Metrics**: Real-time totals for Period Volume, Refund Issues, Delivery Issues, Payment Issues, Product/Damage Issues, Escalation Rate (%), and Resolution Rate (%).
- **Complaint Trends Charts**:
  - Total volume trends with toggle between **Daily** and **Weekly** aggregation.
  - Refund vs. Delivery Delay complaint trajectory over time.
  - Urgency distribution (High / Medium / Low) stacked over time.
  - Escalation Rate (%) and Resolution Rate (%) trajectory.
- **Explainable Spike Detection**:
  - Baseline comparison ($+30\%$ threshold against prior comparison period).
  - Explicit comparison period labeling (e.g. *Current 7 days vs Previous 7 days*).
  - Statistical threshold guard preventing false alerts on small sample sizes ($N < 5$).
- **Recurring Issue Clusters**:
  - Transparent keyword and intent grouping (e.g. *Duplicate Checkout Payment Debits*, *In-Transit Courier SLA Breaches*, *Fragile Item Packaging Damage*, *SMS Gateway OTP Verification*, *Apparel Size SKU Mismatches*).
  - Real customer quote excerpts, cluster volume, trend vs baseline, typical urgency, and cluster escalation rate.
- **Product & Process Diagnostic Analysis**:
  - Factual distinction between:
    - **Observed Complaint Patterns** (factual evidence from ticket logs)
    - **Possible Explanations** (operational hypotheses)
    - **Confirmed Root Causes** (evidence-backed findings)
- **Emerging Issues Executive Summary**:
  - Bulleted data-backed takeaways detailing complaint volume concentrations, percentage shifts, and recommended interventions.

### D. Role-Based Access Control (RBAC)
- Strict access boundary enforced server-side. Customers can never access agent views or session data via URL parameters or navigation tampering.

---

## 3. Persistent Data Foundation (`database.py`)

Persistent SQLite database (`data/support_platform.db`) operating in **Write-Ahead Logging (WAL)** mode with indexed querying:
- `users`: User identity, hashed passwords, salts, roles (`customer`, `agent`, `admin`), supported languages, and availability.
- `conversations`: Support tickets, customer IDs, subject, status (`open`, `in_progress`, `resolved`, `closed`), urgency (`high`, `medium`, `low`), detected language, English translation, predicted intent, AI confidence, escalation status, assigned agent, `preferred_language`, `handoff_requested`, and `live_agent_joined`.
- `messages`: Chronological dialogue preserving distinction between `customer`, `agent`, `ai`, `system`, and `internal_note` authors.
- `feedback`: Customer ratings (1-5), categories, comments, `translation_quality`, `issue_resolved`, and assigned agent links.

---

## 4. Quick Start & Demo Instructions

### Starting the Application
```bash
streamlit run app.py
```

### Pre-Configured Demo Accounts
| Persona | Role | Username | Password | Languages Understood |
| :--- | :--- | :--- | :--- | :--- |
| **Priya Sharma** | Customer | `customer` | `DemoCustomer@2026` | Telugu + English, Hinglish, English |
| **Rahul Varma** | Customer | `rahul` | `DemoCustomer@2026` | Hinglish, English |
| **Vikram Patel** | Support Agent | `agent` | `DemoAgent@2026` | Telugu + English, Hinglish, English |
| **Anita Sundaram** | Support Agent | `anita` | `DemoAgent@2026` | Tanglish, English |

---

## 5. Verification & Automated Test Results

### 1. Phase 4 Root-Cause Analysis Suite (`test_platform_phase4.py`)
```bash
python -m unittest test_platform_phase4.py
```
- **Tests run**: 8
- **Result**: `OK` (100% pass)
- Verifies: Overview metrics calculation, daily & weekly aggregation views, graceful empty state handling, date range filtering, explainable spike detection baseline, recurring issue clustering with customer quotes, product/process evidence levels, and emerging issues summary.

### 2. Phase 3 Inbox Platform Suite (`test_platform_phase3.py`)
```bash
python -m unittest test_platform_phase3.py
```
- **Tests run**: 8
- **Result**: `OK` (100% pass)
- Verifies: 7 mailbox folder counts; deterministic sorting; multidimensional filters and search; ticket assignment/reassignment; ticket resolution/reopening; internal notes customer isolation; CSAT calculation formula and sample size; resolved ticket feedback inspection.

### 3. Phase 2 Live Support Suite (`test_platform_phase2.py`)
```bash
python -m unittest test_platform_phase2.py
```
- **Tests run**: 6
- **Result**: `OK` (100% pass)
- Verifies: Native Tamil, Telugu, and Hindi script detection; agent reply translation; translation uncertainty handling; human handoff & agent matching; multi-role message threading; single feedback submission constraint.

### 4. Phase 1 Platform Suite (`test_platform_phase1.py`)
```bash
python -m unittest test_platform_phase1.py
```
- **Tests run**: 9
- **Result**: `OK` (100% pass)
- Verifies: PBKDF2 password hashing & salts, customer isolation, agent language authorization, availability status updates, conversation creation & AI triage, agent reply dispatch, feedback persistence, and root-cause metrics.

### 5. Application Unit Test Suite (`test_app.py`)
```bash
python -m unittest test_app.py
```
- **Tests run**: 12
- **Result**: `OK` (100% pass)
- Verifies: Schema count, AI output contract, Telugu+English detection, English translations, original message preservation, backwards-compatibility, and AppTest flows.

### 6. Code-Mixed Benchmark Evaluation Suite (`evaluate.py`)
```bash
python evaluate.py
```
- **Benchmark Test Cases**: 47 ground-truth tests across all 4 code-mixed dialects.
- **Pass Rate**: 100.0%
- **Intent Accuracy**: 100.0%
- **Urgency Accuracy**: 100.0%
- **Escalation Accuracy**: 100.0%

### 7. Service & Subsystem Tests (`pytest tests`)
```bash
python -m pytest tests
```
- **Tests run**: 39
- **Result**: `39 passed` (100% pass)
