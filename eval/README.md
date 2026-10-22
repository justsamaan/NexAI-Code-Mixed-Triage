# Code-Mixed Evaluation Challenge Dataset
**NexAI Hack 2026 · Problem Statement 1.1: Code-Mixed Support Triage Assistant**

## 1. Overview & Objective
This evaluation suite provides a held-out benchmark of realistic, conversational Latin-script customer support inquiries in **Hinglish** (Hindi-English) and **Tanglish** (Tamil-English), alongside representative English baseline queries.

Evaluating code-mixed performance strictly on English or synthetic translation fails to reflect conversational reality. This dataset tests:
- Phonetic transliteration variations (e.g. *kedaikala* vs *kidaikala*, *nahi* vs *nhi* vs *nahin*).
- Vernacular morphology and suffixes (e.g. `-la`, `-ku`, `-oda`, `-aachu`, `-wala`, `-gaya`).
- Code-switching at syntactic boundaries.
- Negation reversals (e.g., *"Mujhe refund nahi chahiye! Sirf size exchange karke bada wala bhej do"* — must classify as `change_order`, NOT `get_refund`).
- Critical safety triggers (account takeovers, fraud, physical harm, legal notices).
- Adversarial prompt injection attacks.
- Missing context requests (high-urgency refund requests lacking an Order ID).

---

## 2. Dataset Schema
Each entry in `eval/code_mixed_cases.jsonl` adheres to the schema:
```json
{
  "id": "CM-001",
  "text": "Mera order #ORD-8812 abhi tak deliver nahi hua, delivery status check karke batao.",
  "language": "hinglish",
  "expected_intent": "track_order",
  "expected_urgency": "Normal",
  "expected_escalation": false,
  "notes": "Standard Hinglish order tracking"
}
```

---

## 3. Annotation Guidelines & Adjudication Rules
1. **Intent Grounding:** Every case is annotated with one of the 27 official Bitext intents or `out_of_scope`.
2. **Urgency Policy:**
   - `Critical`: Direct safety risk, unauthorized financial compromise, physical harm, or legal action threats.
   - `High`: Repeated unresolved complaints (3rd+ contact), imminent hard deadlines, access lockout, or monetary discrepancy.
   - `Normal`: Routine answerable customer service requests.
   - `Low`: Informational requests, newsletter subscriptions, or general curiosity.
3. **Escalation Ground Truth:**
   - Cases with `Critical` urgency must always escalate (`true`).
   - High-urgency financial cases lacking verified order identifiers must escalate (`true`).
   - Out-of-scope or adversarial cases must escalate (`true`).
   - Low-confidence or ambiguous phrasing must escalate (`true`).
   - Routine, answerable queries with valid parameters route directly to draft review without mandatory escalation (`false`).

---

## 4. Benchmark Execution
Run the evaluation benchmark from project root:
```bash
python -c "from src.evaluation import run_evaluation_suite; run_evaluation_suite()"
```
Results are saved to `eval/latest_benchmark_report.json`.
