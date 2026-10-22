"""
test_app.py
===========
Automated test suite verifying the Code-Mixed Support Triage Assistant:
- ai_engine contract and output structure (including detected_language & english_translation)
- Telugu + English (Tenglish), Tanglish, Hinglish, and English detection and classification
- test_cases format and counts (47 benchmark test cases)
- evaluate accuracy and metrics
- Streamlit app execution, UI interactions, and complete removal of Quick Example Messages
"""

import unittest
import ai_engine
import evaluate
from test_cases import TEST_CASES
from streamlit.testing.v1 import AppTest


class TestSupportTriage(unittest.TestCase):

    def test_test_cases_count_and_schema(self):
        """Verify at least 45 test cases exist with proper schema and Telugu cases."""
        self.assertGreaterEqual(len(TEST_CASES), 45, "Must have at least 45 test cases")
        telugu_cases = [tc for tc in TEST_CASES if tc.get("language") == "Telugu + English"]
        self.assertGreaterEqual(len(telugu_cases), 10, "Must have at least 10 Telugu + English cases")
        
        for tc in TEST_CASES:
            self.assertIn("id", tc)
            self.assertIn("message", tc)
            self.assertIn("expected_intent", tc)
            self.assertIn("expected_urgency", tc)
            self.assertIn("expected_escalate", tc)
            self.assertIn(tc["expected_urgency"], ["high", "medium", "low"])
            self.assertIsInstance(tc["expected_escalate"], bool)

    def test_ai_engine_output_schema_and_fields(self):
        """Verify analyze_message returns all required fields including language & translation."""
        samples = [
            "naa order inka delivery avvaledu",
            "refund kavali, amount account lo padaledu",
            "mera paisa do baar cut gaya",
            "order vandhuchu but box damaged, refund venum",
            "I was charged twice on my credit card",
            "",  # Empty message test
        ]
        
        required_keys = [
            "intent", "urgency", "confidence", "draft_reply", "escalate",
            "escalation_reason", "detected_language", "english_translation"
        ]
        
        for msg in samples:
            res = ai_engine.analyze_message(msg)
            for k in required_keys:
                self.assertIn(k, res, f"Field '{k}' missing for input '{msg}'")
            
            self.assertIsInstance(res["intent"], str)
            self.assertIn(res["urgency"], ["high", "medium", "low"])
            self.assertIsInstance(res["confidence"], (int, float))
            self.assertGreaterEqual(res["confidence"], 0.0)
            self.assertLessEqual(res["confidence"], 1.0)
            self.assertIsInstance(res["draft_reply"], str)
            self.assertGreater(len(res["draft_reply"]), 0)
            self.assertIsInstance(res["escalate"], bool)
            self.assertIsInstance(res["escalation_reason"], str)
            self.assertIsInstance(res["detected_language"], str)
            self.assertIsInstance(res["english_translation"], str)

    def test_telugu_english_language_detection(self):
        """Verify Telugu + English messages receive the appropriate language label."""
        telugu_msgs = [
            "naa order inka delivery avvaledu",
            "refund kavali, amount account lo padaledu",
            "payment rendu saarlu cut ayyindi",
            "naa account login avvatledu",
            "wrong product vachindi, return cheyyali",
            "delivery chala late avutundi",
        ]
        for msg in telugu_msgs:
            res = ai_engine.analyze_message(msg)
            self.assertEqual(res["detected_language"], "Telugu + English", f"Failed for '{msg}'")

    def test_english_translations_returned(self):
        """Verify English translations are generated and preserve key meaning."""
        pairs = [
            ("naa order inka delivery avvaledu", "not been delivered"),
            ("payment rendu saarlu cut ayyindi", "two times"),
            ("mera paisa do baar cut gaya", "two times"),
            ("order vandhuchu but box damaged, refund venum", "damaged"),
            ("I was charged twice on my credit card", "charged twice"),
        ]
        for src, expected_fragment in pairs:
            res = ai_engine.analyze_message(src)
            trans = res["english_translation"].lower()
            self.assertIn(expected_fragment.lower(), trans, f"Translation of '{src}' missing '{expected_fragment}'")

    def test_original_message_preserved(self):
        """Verify original message is preserved in analysis and session history."""
        msg = "wrong product vachindi, return cheyyali"
        res = ai_engine.analyze_message(msg)
        self.assertIsNotNone(res)
        # In streamlit flow
        at = AppTest.from_file("app.py").run()
        at.text_area[0].set_value(msg).run()
        analyze_btn = [b for b in at.button if "Analyze" in b.label][0]
        analyze_btn.click().run()
        latest = at.session_state["latest_result"]
        self.assertEqual(latest["message"], msg)

    def test_existing_languages_still_work(self):
        """Verify Hinglish, Tanglish, and English continue to be triaged accurately."""
        samples = [
            ("mera paisa do baar cut gaya", "Payment Issue", "Hinglish"),
            ("delivery romba late aagudhu", "Delivery Delay", "Tanglish"),
            ("Please cancel order #88491 as I ordered the incorrect model", "Order Cancellation", "English"),
        ]
        for msg, exp_intent, exp_lang in samples:
            res = ai_engine.analyze_message(msg)
            self.assertEqual(res["intent"], exp_intent)
            self.assertEqual(res["detected_language"], exp_lang)

    def test_missing_translation_fields_do_not_crash_ui(self):
        """Verify UI handles tickets missing language or translation gracefully."""
        at = AppTest.from_file("app.py").run()
        # Insert a ticket missing new fields
        at.session_state["tickets"] = [{
            "id": 1,
            "timestamp": "10:00:00",
            "message": "legacy ticket without translation",
            "intent": "General Inquiry",
            "urgency": "low",
            "confidence": 0.85,
            "draft_reply": "How can we help?",
            "escalate": False,
            "escalation_reason": "",
            "backend": "Local NLP"
            # note: detected_language and english_translation intentionally omitted
        }]
        at.session_state["latest_result"] = at.session_state["tickets"][0]
        at.run()
        self.assertEqual(len(at.exception), 0, "UI crashed on missing translation fields")

    def test_low_confidence_escalation_policy(self):
        """Verify ambiguous / low-confidence cases follow escalation policy."""
        res = ai_engine.analyze_message("xyz abc unknown token sequence")
        if res["confidence"] < 0.70:
            self.assertTrue(res["escalate"], "Low confidence should trigger escalation")
            self.assertGreater(len(res["escalation_reason"]), 0)

    def test_support_inbox_no_quick_example_buttons(self):
        """Verify Quick Example Messages section and buttons are completely removed."""
        at = AppTest.from_file("app.py").run()
        button_labels = [b.label for b in at.button]
        
        # Verify no example message buttons exist
        forbidden_buttons = [
            "Damaged (Tanglish)",
            "Payment (Hinglish)",
            "Order Issue (Hinglish)",
            "Login (Hinglish)",
            "Delay (Tanglish)",
        ]
        for fb in forbidden_buttons:
            self.assertNotIn(fb, button_labels, f"Found removed example button: '{fb}'")
            
        # Verify markdown text does not have "Quick Example Messages" heading
        for md in at.markdown:
            self.assertNotIn("Quick Example Messages", md.value)

    def test_evaluation_pipeline_full_benchmark(self):
        """Verify evaluation runs across all 47 benchmark test cases with high pass rate."""
        eval_out = evaluate.evaluate_dataset(test_cases=TEST_CASES)
        m = eval_out["metrics"]
        
        self.assertEqual(m["total_tests"], len(TEST_CASES))
        self.assertEqual(m["total_errors"], 0)
        self.assertGreaterEqual(m["overall_pass_rate"], 95.0)
        self.assertGreaterEqual(m["intent_accuracy"], 95.0)
        self.assertGreaterEqual(m["urgency_accuracy"], 95.0)
        self.assertGreaterEqual(m["escalate_accuracy"], 95.0)

    def test_streamlit_app_evaluation_flow(self):
        """Test Streamlit app evaluation view runs all 47 tests."""
        at = AppTest.from_file("app.py").run()
        at.radio[0].set_value("🧪 Evaluation Suite").run()
        self.assertEqual(len(at.exception), 0)

        run_btn = [b for b in at.button if "Run All" in b.label][0]
        run_btn.click().run()
        self.assertEqual(len(at.exception), 0)

        eval_res = at.session_state["eval_results"]
        self.assertIsNotNone(eval_res)
        self.assertEqual(eval_res["metrics"]["total_tests"], len(TEST_CASES))

    def test_streamlit_app_analytics_flow(self):
        """Test Streamlit app analytics dashboard with language breakdown."""
        at = AppTest.from_file("app.py").run()
        at.session_state["tickets"] = [{
            "id": 1,
            "timestamp": "10:00:00",
            "message": "payment rendu saarlu cut ayyindi",
            "detected_language": "Telugu + English",
            "english_translation": "Payment was deducted two times.",
            "intent": "Payment Issue",
            "urgency": "high",
            "confidence": 0.92,
            "draft_reply": "Apologies for the duplicate charge...",
            "escalate": True,
            "escalation_reason": "Duplicate payment",
            "backend": "Local NLP"
        }]
        at.radio[0].set_value("📊 Session Analytics").run()
        self.assertEqual(len(at.exception), 0)


if __name__ == "__main__":
    unittest.main()
