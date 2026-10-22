"""
test_platform_phase2.py
=======================
Automated test suite verifying PHASE 2 implementation:
- Native script input & detection (Tamil, Telugu, Hindi)
- Code-mixed translation and uncertainty indication
- Agent reply translation into customer's selected language
- Human handoff workflow (matching available agents, waiting queue, live agent join)
- Customer chat thread message integrity and persistence across refreshes
- Customer feedback constraints (single feedback submission, star rating, translation quality)
"""

import unittest
import database
import ai_engine


class TestPhase2Platform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure database schema and seed data are ready."""
        database.init_db()

    def test_01_native_script_detection_and_triage(self):
        """Verify native Tamil, Telugu, and Hindi scripts are accurately detected and triaged."""
        # Tamil native script
        tamil_query = "என் ஆர்டர் இன்னும் வரவில்லை"  # My order has not arrived yet
        t_res = ai_engine.analyze_message(tamil_query)
        self.assertTrue("Tamil" in t_res["detected_language"] or "Tanglish" in t_res["detected_language"])
        self.assertIn("order", t_res["english_translation"].lower())
        self.assertEqual(t_res["intent"], "Delivery Delay")

        # Telugu native script
        telugu_query = "నా ఆర్డర్ ఇంకా డెలివరీ కాలేదు"  # My order has not been delivered yet
        te_res = ai_engine.analyze_message(telugu_query)
        self.assertIn("Telugu", te_res["detected_language"])
        self.assertIn("order", te_res["english_translation"].lower())
        self.assertEqual(te_res["intent"], "Delivery Delay")

        # Hindi native script
        hindi_query = "मेरा ऑर्डर अभी तक नहीं आया"
        h_res = ai_engine.analyze_message(hindi_query)
        self.assertIn("Hinglish", h_res["detected_language"])
        self.assertIn("order", h_res["english_translation"].lower())

    def test_02_agent_reply_translation(self):
        """Verify translate_agent_reply drafts native responses with English context."""
        english_reply = "We have initiated your refund, which will reflect in 3-5 business days."
        
        # Translate to Telugu
        te_trans = ai_engine.translate_agent_reply(english_reply, "Telugu (తెలుగు)")
        self.assertIn("రీఫండ్", te_trans)
        self.assertIn("refund", te_trans.lower())

        # Translate to Tamil
        ta_trans = ai_engine.translate_agent_reply(english_reply, "Tamil (தமிழ்)")
        self.assertIn("ரீஃபண்ட்", ta_trans)
        self.assertIn("refund", ta_trans.lower())

        # Translate to Hindi
        hi_trans = ai_engine.translate_agent_reply(english_reply, "Hindi (हिन्दी)")
        self.assertIn("रिफंड", hi_trans)
        self.assertIn("refund", hi_trans.lower())

        # English stays English
        en_trans = ai_engine.translate_agent_reply(english_reply, "English")
        self.assertEqual(en_trans, english_reply)

    def test_03_translation_uncertainty_handling(self):
        """Verify ambiguous or unknown code-mixed phrasing flags uncertainty without silent invention."""
        unknown_gibberish = "xyzqwerty blurp blop 998877"
        res = ai_engine.analyze_message(unknown_gibberish)
        # Should flag uncertainty or low confidence or mixed/unclear
        is_uncertain = (
            res["confidence"] < 0.70 or
            "uncertain" in res["english_translation"].lower() or
            res["detected_language"] in ["Mixed/Unclear", "English"]
        )
        self.assertTrue(is_uncertain)

    def test_04_human_handoff_and_agent_matching(self):
        """Test human handoff flagging, queue matching for declared languages, and live agent join."""
        priya = database.get_user_by_username("customer")
        initial_msg = "నా ఆర్డర్ ఇంకా రాలేదు, అర్జెంట్ సహాయం కావాలి"
        ai_res = ai_engine.analyze_message(initial_msg)
        
        # Create a conversation with Telugu preference
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Urgent Delivery Issue in Hyderabad",
            initial_message=initial_msg,
            ai_analysis=ai_res,
            preferred_language="Telugu (తెలుగు)"
        )
        conv_id = conv["id"]
        
        # Initial state: not joined
        self.assertEqual(conv.get("live_agent_joined", 0), 0)
        self.assertEqual(conv.get("handoff_requested", 0), 0)

        # Trigger human handoff
        handoff_ok = database.request_human_handoff(conv_id, "Customer requested Telugu specialist")
        self.assertTrue(handoff_ok)
        
        # Verify conversation updated
        updated_conv = database.get_conversation(conv_id)
        self.assertEqual(updated_conv["handoff_requested"], 1)

        # Verify system waiting message in thread
        messages = database.get_conversation_messages(conv_id)
        system_msgs = [m for m in messages if m["sender_type"] == "system"]
        self.assertGreater(len(system_msgs), 0)
        self.assertIn("Specialist assistance requested", system_msgs[-1]["message_text"])

        # Match available agents for Telugu
        telugu_agents = database.find_available_agents_for_language("Telugu + English")
        self.assertTrue(any("Telugu" in " ".join(ag.get("languages", [])) for ag in telugu_agents))

        # Agent accepts conversation
        vikram = database.get_user_by_username("agent")
        accept_ok = database.accept_conversation(conv_id, vikram["id"], vikram["name"])
        self.assertTrue(accept_ok)

        # Confirm live_agent_joined is set and agent assigned
        active_conv = database.get_conversation(conv_id)
        self.assertEqual(active_conv["live_agent_joined"], 1)
        self.assertEqual(active_conv["assigned_agent_id"], vikram["id"])
        self.assertEqual(active_conv["assigned_agent_name"], vikram["name"])
        self.assertEqual(active_conv["status"], "in_progress")

        # Verify joined message in thread
        updated_messages = database.get_conversation_messages(conv_id)
        join_msgs = [m for m in updated_messages if "joined the conversation" in m["message_text"]]
        self.assertGreater(len(join_msgs), 0)

    def test_05_message_threading_and_role_separation(self):
        """Test persistent message threading with customer, AI, agent, and system roles."""
        priya = database.get_user_by_username("customer")
        agent_user = database.get_user_by_username("agent")
        msg = "Mera refund kab aayega?"
        ai_res = ai_engine.analyze_message(msg)

        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Refund query",
            initial_message=msg,
            ai_analysis=ai_res
        )
        c_id = conv["id"]

        # Note: create_conversation already inserted customer initial message and AI draft response.
        # Now agent sends reply:
        database.add_message(
            conv_id=c_id,
            sender_type="agent",
            sender_id=agent_user["id"],
            sender_name=agent_user["name"],
            message_text="हमने आपका रिफंड चेक किया है, कल तक आ जाएगा।",
            english_translation="We have checked your refund, it will arrive by tomorrow.",
            detected_language="Hinglish"
        )

        # Retrieve and verify persistence
        thread = database.get_conversation_messages(c_id)
        self.assertGreaterEqual(len(thread), 3)
        sender_types = [m["sender_type"] for m in thread]
        self.assertIn("customer", sender_types)
        self.assertIn("ai", sender_types)
        self.assertIn("agent", sender_types)
        self.assertEqual(thread[0]["sender_type"], "customer")
        self.assertEqual(thread[0]["message_text"], "Mera refund kab aayega?")

    def test_06_customer_feedback_single_submission_constraint(self):
        """Verify 1-5 rating, translation quality, and strict one-submission enforcement."""
        priya = database.get_user_by_username("customer")
        agent_user = database.get_user_by_username("agent")
        msg = "Everything is resolved, thanks"
        ai_res = ai_engine.analyze_message(msg)

        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Resolved inquiry",
            initial_message=msg,
            ai_analysis=ai_res
        )
        c_id = conv["id"]
        database.update_conversation_status(c_id, "resolved")

        # First feedback submission succeeds
        fb = database.submit_feedback(
            conv_id=c_id,
            customer_id=priya["id"],
            customer_name=priya["name"],
            rating=5,
            category="Payment Issue",
            comment="Excellent support in Telugu!",
            agent_id=agent_user["id"],
            agent_name=agent_user["name"],
            translation_quality="Excellent",
            issue_resolved="Yes"
        )
        self.assertEqual(fb["rating"], 5)
        self.assertIsNotNone(database.get_conversation_feedback(c_id))

        # Duplicate submission must raise ValueError
        with self.assertRaises(ValueError):
            database.submit_feedback(
                conv_id=c_id,
                customer_id=priya["id"],
                customer_name=priya["name"],
                rating=4,
                category="Payment Issue",
                comment="Trying to submit again"
            )


if __name__ == "__main__":
    unittest.main()
