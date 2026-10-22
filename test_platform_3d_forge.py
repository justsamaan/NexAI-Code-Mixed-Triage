"""
test_platform_3d_forge.py
=========================
Automated test suite verifying:
1. Romanized Hindi parsing & translation (e.g. 'mera order deliver nahi hua', 'order nahi mila')
2. 5-Stage Bottom-Up Parser State Derivation Pipeline (S0 to S5 ACCEPT)
3. Workstation Creatures mapping (Vulcan, Gildor, Brog, Pyra, Hermes)
4. Three.js WebGL 3D Forge HTML generation and component integrity
5. AppTest navigation and instant ChatGPT-style default landing
"""

import unittest
import ai_engine
import forge_3d
from streamlit.testing.v1 import AppTest


class Test3DForgeAndRomanizedHindi(unittest.TestCase):

    def test_romanized_hindi_order_not_received_variations(self):
        """Verify Romanized Hindi expressions for undelivered orders are accurately classified."""
        test_phrases = [
            ("mera order deliver nahi hua", "Delivery Delay", "Hinglish", "delivered"),
            ("order deliver nahi hua", "Delivery Delay", "Hinglish", "delivered"),
            ("mera order abhi tak deliver nahi hua", "Delivery Delay", "Hinglish", "delivered"),
            ("mera order nahi mila", "Delivery Delay", "Hinglish", "received"),
            ("order nahi mila", "Delivery Delay", "Hinglish", "received"),
            ("mera package abhi tak nahi aaya", "Delivery Delay", "Hinglish", "arrived"),
            ("delivery nahi hui", "Delivery Delay", "Hinglish", "delivery"),
            ("order nahi pahuncha", "Delivery Delay", "Hinglish", "order")
        ]

        for phrase, exp_intent, exp_lang, exp_trans_keyword in test_phrases:
            res = ai_engine.analyze_message(phrase)
            self.assertEqual(res["intent"], exp_intent, f"Wrong intent for '{phrase}'")
            self.assertEqual(res["detected_language"], exp_lang, f"Wrong language for '{phrase}'")
            self.assertIn(exp_trans_keyword.lower(), res["english_translation"].lower(), f"Keyword '{exp_trans_keyword}' missing in translation of '{phrase}'")
            self.assertGreaterEqual(res["confidence"], 0.70)
            self.assertIn(res["urgency"], ["high", "medium", "low"])

    def test_bottom_up_parser_5_stage_derivation(self):
        """Verify the 5-stage bottom-up parser derivation from S0 to S5 ACCEPT."""
        prompt = "mera order deliver nahi hua"
        pipe = forge_3d.derive_parser_pipeline(prompt)

        self.assertEqual(pipe["message"], prompt)
        self.assertEqual(pipe["script"], "Latin / Romanized Script")
        self.assertIn("order", pipe["tokens"])
        
        steps = pipe["steps"]
        self.assertEqual(len(steps), 5, "Must have exactly 5 workstation stages")

        # Stage 1: Vulcan (Smelter Golem) - S0 -> S1 (SHIFT)
        s1 = steps[0]
        self.assertEqual(s1["state_label"], "S0 → S1")
        self.assertEqual(s1["creature"], "Vulcan")
        self.assertEqual(s1["action"], "SHIFT")
        self.assertEqual(s1["output_payload"]["script"], "Latin / Romanized Script")
        self.assertGreaterEqual(s1["output_payload"]["token_count"], 5)

        # Stage 2: Gildor (Dialect Imp) - S1 -> S2 (REDUCE)
        s2 = steps[1]
        self.assertEqual(s2["state_label"], "S1 → S2")
        self.assertEqual(s2["creature"], "Gildor")
        self.assertEqual(s2["action"], "REDUCE")
        self.assertEqual(s2["output_payload"]["detected_language"], "Hinglish")

        # Stage 3: Brog (Blacksmith Dwarf) - S2 -> S3 (REDUCE)
        s3 = steps[2]
        self.assertEqual(s3["state_label"], "S2 → S3")
        self.assertEqual(s3["creature"], "Brog")
        self.assertEqual(s3["action"], "REDUCE")
        self.assertIn("delivered", s3["output_payload"]["english_translation"].lower())

        # Stage 4: Pyra (Urgency Sprite) - S3 -> S4 (REDUCE)
        s4 = steps[3]
        self.assertEqual(s4["state_label"], "S3 → S4")
        self.assertEqual(s4["creature"], "Pyra")
        self.assertEqual(s4["action"], "REDUCE")
        self.assertEqual(s4["output_payload"]["intent"], "Delivery Delay")
        self.assertGreaterEqual(s4["output_payload"]["confidence"], 0.80)

        # Stage 5: Hermes (Dispatch Automaton) - S4 -> S5 (ACCEPT)
        s5 = steps[4]
        self.assertEqual(s5["state_label"], "S4 → S5")
        self.assertEqual(s5["creature"], "Hermes")
        self.assertEqual(s5["action"], "ACCEPT")
        self.assertIn("ACCEPT", s5["output_payload"]["status"])
        self.assertGreater(len(s5["output_payload"]["draft_reply"]), 0)

    def test_threejs_forge_html_generation(self):
        """Verify WebGL Three.js HTML scene contains all required elements."""
        prompt = "naa order inka delivery avvaledu"
        html = forge_3d.build_threejs_forge_html(prompt, active_state=3)

        self.assertIn("three.min.js", html)
        self.assertIn("OrbitControls.js", html)
        self.assertIn("Vulcan", html)
        self.assertIn("Gildor", html)
        self.assertIn("Brog", html)
        self.assertIn("Pyra", html)
        self.assertIn("Hermes", html)
        self.assertIn("promptPacket", html)
        self.assertIn("emberParticles", html)
        self.assertIn(prompt, html)

    def test_streamlit_app_chat_assistant_default_landing(self):
        """Verify Streamlit app opens immediately into the ChatGPT-style AI Chatbot view."""
        at = AppTest.from_file("app.py").run()
        self.assertEqual(len(at.exception), 0)

        # Radio navigation index 0 must be 💬 AI Chatbot
        self.assertEqual(at.radio[0].value, "💬 AI Chatbot")

        # Primary input must be present on page load
        self.assertGreaterEqual(len(at.text_area), 1)

        # Send a Romanized Hindi prompt
        at.text_area[0].set_value("mera order deliver nahi hua").run()
        analyze_btn = [b for b in at.button if "Analyze" in b.label][0]
        analyze_btn.click().run()

        self.assertEqual(len(at.exception), 0)
        latest = at.session_state["latest_result"]
        self.assertEqual(latest["message"], "mera order deliver nahi hua")
        self.assertEqual(latest["intent"], "Delivery Delay")
        self.assertEqual(latest["detected_language"], "Hinglish")
        self.assertIn("delivered", latest["english_translation"].lower())

    def test_streamlit_app_switch_to_3d_forge_view(self):
        """Verify navigation to 3D Workstation Forge view and table rendering."""
        at = AppTest.from_file("app.py").run()
        at.radio[0].set_value("⚒️ 3D Workstation Forge").run()
        self.assertEqual(len(at.exception), 0)

        # Confirm 3D forge state radio filter is present
        state_radios = [r for r in at.radio if "Free Navigation" in r.label or "Derivation" in r.label]
        self.assertGreaterEqual(len(state_radios), 1)


if __name__ == "__main__":
    unittest.main()
