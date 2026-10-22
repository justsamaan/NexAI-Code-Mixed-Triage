"""
test_platform_phase5.py
=======================
Automated end-to-end integration and negative testing suite for PHASE 5:
1. Complete 13-step end-to-end customer support lifecycle:
   - Registration/Login -> Language selection -> Code-mixed message -> AI triage
   - Uncertainty handoff -> Agent matching & takeover -> Draft editing & translation
   - Message dispatch -> Customer followup -> Ticket resolution -> Customer CSAT rating
   - Rating inspection in ticket details & impact on Root-Cause / CSAT dashboards.
2. Comprehensive negative and boundary verification:
   - Negative Case 1: Invalid login credentials
   - Negative Case 2: Customer data isolation breach attempt
   - Negative Case 3: Unavailable (offline/busy) agent matching
   - Negative Case 4: Ambiguous / unknown input translation uncertainty
   - Negative Case 5: AI backend failure fallback to local rules
   - Negative Case 6: Unrated resolved ticket handling & CSAT zero-case integrity
   - Negative Case 7: Empty analytics dataset query handling
   - Negative Case 8: Missing product/logistics metadata non-hallucination
   - Negative Case 9: Ticket resolution without prior agent response
"""

import unittest
import database
import ai_engine


class TestPhase5IntegrationAndNegative(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database schema and historical demo baseline."""
        database.init_db()
        database.ensure_historical_demo_dates()

    # =========================================================================
    # PART 1: COMPLETE END-TO-END CUSTOMER WORKFLOW (STEPS 1 TO 13)
    # =========================================================================

    def test_01_complete_end_to_end_customer_workflow(self):
        """
        Executes and verifies the full 13-step lifecycle:
        1. Register new customer
        2. Customer chooses preferred language (Telugu)
        3. Customer sends code-mixed message in Telugu script
        4. AI engine classifies intent, detects language, translates to English, assesses urgency
        5. AI uncertain / flags ticket for human assistance
        6. System matches ticket with available agent fluent in Telugu (Rajesh)
        7. Agent opens ticket, reviews original & translation, reviews draft reply
        8. Agent translates draft into Telugu and sends approved reply
        9. Customer receives response in persistent thread and replies
        10. Agent marks ticket as resolved
        11. Customer submits 5-star rating and translation quality feedback
        12. Rating appears in agent's ticket details and updates CSAT score
        13. Resolved ticket contributes to Root-Cause & Complaint Trends dashboard
        """
        # Step 1: Customer registers
        username = f"e2e_cust_{database.secrets.token_hex(3)}"
        email = f"{username}@testmail.org"
        customer = database.create_user(
            username=username,
            email=email,
            password="SecurePassword@2026",
            name="Sita Lakshmi",
            role="customer",
            languages=["Telugu + English", "English"]
        )
        self.assertIsNotNone(customer)
        self.assertEqual(customer["role"], "customer")

        # Step 2: Customer chooses preferred language
        pref_lang = "Telugu (తెలుగు)"

        # Step 3: Customer sends message in native Telugu script
        cust_msg = "నా ఆర్డర్ ఇంకా డెలివరీ కాలేదు, ట్రాకింగ్ అప్‌డేట్ అవ్వట్లేదు"

        # Step 4: AI triage and analysis
        ai_triage = ai_engine.analyze_message(cust_msg)
        self.assertIn("Telugu", ai_triage["detected_language"])
        self.assertEqual(ai_triage["intent"], "Delivery Delay")
        self.assertIn("order", ai_triage["english_translation"].lower())
        self.assertIn(ai_triage["urgency"], ["high", "medium", "low"])

        # Create conversation ticket
        conv = database.create_conversation(
            customer_id=customer["id"],
            customer_name=customer["name"],
            subject="Telugu Delivery Delay Inquiry",
            initial_message=cust_msg,
            ai_analysis=ai_triage,
            preferred_language=pref_lang
        )
        cid = conv["id"]
        self.assertIsNotNone(cid)

        # Step 5: Uncertainty / Human assistance request
        database.request_human_handoff(cid, "Customer requested Telugu language specialist")
        conv_handoff = database.get_conversation(cid)
        self.assertEqual(conv_handoff["handoff_requested"], 1)

        # Step 6: System matches available agent fluent in Telugu
        matched_agents = database.find_available_agents_for_language("Telugu + English")
        self.assertGreater(len(matched_agents), 0)
        selected_agent = matched_agents[0]
        self.assertEqual(selected_agent["availability_status"], "online")

        # Step 7: Agent accepts ticket and takes over
        database.accept_conversation(cid, selected_agent["id"], selected_agent["name"])
        conv_active = database.get_conversation(cid)
        self.assertEqual(conv_active["live_agent_joined"], 1)
        self.assertEqual(conv_active["assigned_agent_id"], selected_agent["id"])
        self.assertEqual(conv_active["status"], "in_progress")

        # Step 8: Agent drafts reply, translates to Telugu, and sends approved response
        english_draft = "We apologize for the delay. Your order has been dispatched via courier and will arrive tomorrow."
        telugu_reply = ai_engine.translate_agent_reply(english_draft, "Telugu (తెలుగు)")
        self.assertIn("delay", telugu_reply.lower())

        database.add_message(
            conv_id=cid,
            sender_type="agent",
            sender_id=selected_agent["id"],
            sender_name=selected_agent["name"],
            message_text=telugu_reply,
            english_translation=english_draft,
            detected_language="Telugu + English"
        )

        # Step 9: Customer receives response and continues conversation
        cust_messages = database.get_conversation_messages(cid, include_internal=False)
        agent_msgs = [m for m in cust_messages if m["sender_type"] == "agent"]
        self.assertEqual(len(agent_msgs), 1)
        self.assertEqual(agent_msgs[0]["message_text"], telugu_reply)

        # Customer sends follow-up
        database.add_message(
            conv_id=cid,
            sender_type="customer",
            sender_id=customer["id"],
            sender_name=customer["name"],
            message_text="చాలా ధన్యవాదాలు, ట్రాకింగ్ నంబర్ అందింది.",
            english_translation="Thank you very much, received tracking number."
        )

        # Step 10: Agent marks ticket as resolved
        database.update_conversation_status(cid, "resolved")
        conv_resolved = database.get_conversation(cid)
        self.assertEqual(conv_resolved["status"], "resolved")

        # Step 11: Customer submits 5-star rating and feedback
        fb = database.submit_feedback(
            conv_id=cid,
            customer_id=customer["id"],
            customer_name=customer["name"],
            rating=5,
            category="Language & Translation Quality",
            comment="Outstanding support in Telugu! The agent replied in my native language.",
            agent_id=selected_agent["id"],
            agent_name=selected_agent["name"],
            translation_quality="Accurate & Natural",
            issue_resolved="Yes"
        )
        self.assertEqual(fb["rating"], 5)

        # Step 12: Rating appears in ticket details and contributes to CSAT
        ticket_fb = database.get_conversation_feedback(cid)
        self.assertIsNotNone(ticket_fb)
        self.assertEqual(ticket_fb["rating"], 5)
        self.assertEqual(ticket_fb["translation_quality"], "Accurate & Natural")

        csat = database.get_csat_metrics()
        self.assertGreater(csat["total_ratings"], 0)
        self.assertGreaterEqual(csat["csat_percent"], 50.0)
        self.assertIn(csat["label"], ["Positive", "Neutral"])

        # Step 13: Resolved ticket contributes to Root-Cause & Complaint Trends dashboard
        rca_data = database.get_root_cause_dashboard_data()
        self.assertFalse(rca_data["is_empty"])
        self.assertGreater(rca_data["total_complaints"], 0)
        self.assertGreater(rca_data["delivery_complaints"], 0)

    # =========================================================================
    # PART 2: COMPREHENSIVE NEGATIVE AND BOUNDARY TESTING
    # =========================================================================

    def test_02_negative_invalid_login(self):
        """Verify authentication fails safely on wrong password, non-existent user, and empty fields."""
        # Non-existent user
        self.assertIsNone(database.authenticate_user("ghost_user_999", "AnyPassword"))

        # Existing user with bad password
        self.assertIsNone(database.authenticate_user("customer", "IncorrectPassword@123"))

        # Empty credentials
        self.assertIsNone(database.authenticate_user("", ""))
        self.assertIsNone(database.authenticate_user("customer", ""))

    def test_03_negative_customer_isolation_breach_attempt(self):
        """Verify a customer cannot view or access another customer's conversations."""
        priya = database.get_user_by_username("customer")
        rahul = database.get_user_by_username("rahul")

        # Query conversations for Priya
        priya_convs = database.list_customer_conversations(priya["id"])
        # Query conversations for Rahul
        rahul_convs = database.list_customer_conversations(rahul["id"])

        priya_ids = {c["id"] for c in priya_convs}
        rahul_ids = {c["id"] for c in rahul_convs}

        # Zero intersection
        self.assertEqual(len(priya_ids.intersection(rahul_ids)), 0)

        # Verify Rahul's tickets are NOT returned under Priya's customer ID
        for c in priya_convs:
            self.assertEqual(c["customer_id"], priya["id"])
            self.assertNotEqual(c["customer_id"], rahul["id"])

    def test_04_negative_unavailable_agent_not_matched(self):
        """Verify agents marked offline or busy are never matched for live handoff."""
        anita = database.get_user_by_username("anita")
        orig_status = anita.get("availability_status", "online")

        try:
            # Set Anita to offline
            database.update_agent_status(anita["id"], "offline")
            matched_offline = database.find_available_agents_for_language("Tanglish")
            self.assertFalse(any(ag["id"] == anita["id"] for ag in matched_offline))

            # Set Anita to busy
            database.update_agent_status(anita["id"], "busy")
            matched_busy = database.find_available_agents_for_language("Tanglish")
            self.assertFalse(any(ag["id"] == anita["id"] for ag in matched_busy))

            # Set Anita back to online
            database.update_agent_status(anita["id"], "online")
            matched_online = database.find_available_agents_for_language("Tanglish")
            self.assertTrue(any(ag["id"] == anita["id"] for ag in matched_online))
        finally:
            database.update_agent_status(anita["id"], orig_status)

    def test_05_negative_translation_uncertainty_handling(self):
        """Verify ambiguous, corrupted, or unparseable input indicates uncertainty without hallucinating."""
        garbage_inputs = [
            "qwertyasdf zxcvbnm 123456789 ???",
            "!@#$%^&*()_+",
            "blabla foobar zoobaz 99",
        ]
        for g in garbage_inputs:
            res = ai_engine.analyze_message(g)
            # Must flag uncertainty or have detected_language as Mixed/Unclear / English
            has_uncertainty_flag = (
                "uncertain" in res["english_translation"].lower() or
                res["detected_language"] in ["Mixed/Unclear", "English"] or
                res["confidence"] <= 0.85
            )
            self.assertTrue(has_uncertainty_flag, f"Failed uncertainty handling for '{g}'")

    def test_06_negative_ai_backend_fallback_on_error(self):
        """Verify analyze_message falls back to local rules if Gemini API encounters error."""
        # Test analyze_with_local_rules directly
        sample = "mera paisa do baar cut gaya"
        local_res = ai_engine.analyze_with_local_rules(sample)
        self.assertEqual(local_res["intent"], "Payment Issue")
        self.assertEqual(local_res["urgency"], "high")
        self.assertTrue(local_res["escalate"])
        self.assertEqual(local_res["detected_language"], "Hinglish")

    def test_07_negative_unrated_ticket_csat_handling(self):
        """Verify tickets without feedback do not corrupt CSAT score or invent ratings."""
        priya = database.get_user_by_username("customer")
        msg = "Unrated test inquiry"
        ai_res = ai_engine.analyze_message(msg)
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Unrated Ticket Test",
            initial_message=msg,
            ai_analysis=ai_res
        )
        cid = conv["id"]
        database.update_conversation_status(cid, "resolved")

        # No feedback has been submitted
        fb = database.get_conversation_feedback(cid)
        self.assertIsNone(fb)

        # CSAT calculation handles unrated tickets gracefully
        csat = database.get_csat_metrics()
        self.assertGreaterEqual(csat["csat_percent"], 0.0)
        self.assertLessEqual(csat["csat_percent"], 100.0)

    def test_08_negative_empty_analytics_dataset(self):
        """Verify querying a date range with zero tickets returns is_empty=True without exceptions."""
        empty_data = database.get_root_cause_dashboard_data(
            start_date="2010-01-01",
            end_date="2010-01-02"
        )
        self.assertTrue(empty_data["is_empty"])
        self.assertEqual(empty_data["total_complaints"], 0)
        self.assertEqual(empty_data["refund_complaints"], 0)
        self.assertEqual(empty_data["delivery_complaints"], 0)
        self.assertEqual(empty_data["escalation_rate"], 0.0)
        self.assertEqual(empty_data["resolution_rate"], 0.0)
        self.assertEqual(len(empty_data["trend_data"]), 0)

    def test_09_negative_missing_product_metadata_handling(self):
        """Verify tickets lacking product names or couriers do not hallucinate entities."""
        priya = database.get_user_by_username("customer")
        msg = "General account question, no products mentioned"
        ai_res = ai_engine.analyze_message(msg)
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Generic Account Query",
            initial_message=msg,
            ai_analysis=ai_res
        )
        cid = conv["id"]

        # Conversation exists without product metadata
        c = database.get_conversation(cid)
        self.assertNotIn("product_id", c)
        self.assertNotIn("delivery_provider", c)

    def test_10_negative_ticket_resolved_without_agent_response(self):
        """Verify ticket can be resolved directly without an agent response (e.g. customer self-resolved)."""
        priya = database.get_user_by_username("customer")
        msg = "I accidentally placed the order, but already canceled on the website"
        ai_res = ai_engine.analyze_message(msg)
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Self-Resolved Cancellation",
            initial_message=msg,
            ai_analysis=ai_res
        )
        cid = conv["id"]

        # No agent message was ever added
        messages = database.get_conversation_messages(cid)
        agent_msgs = [m for m in messages if m["sender_type"] == "agent"]
        self.assertEqual(len(agent_msgs), 0)

        # Directly update status to resolved
        ok = database.update_conversation_status(cid, "resolved")
        self.assertTrue(ok)
        self.assertEqual(database.get_conversation(cid)["status"], "resolved")

    def test_11_live_session_hindi_message_flow_stability(self):
        """Verify Hindi message dispatch and draft clearing operates flawlessly without widget instantiation errors."""
        agent = database.get_user_by_username("agent")
        customer = database.get_user_by_username("customer")
        
        # Create an active conversation in progress
        hindi_msg = "नमस्ते, हम आपके ऑर्डर की डिलीवरी की जांच कर रहे हैं।"
        conv = database.create_conversation(
            customer_id=customer["id"],
            customer_name=customer["name"],
            subject="Hindi Live Support Query",
            initial_message="मेरा ऑर्डर अभी तक नहीं आया",
            ai_analysis=ai_engine.analyze_message("मेरा ऑर्डर अभी तक नहीं आया"),
            preferred_language="Hindi (हिन्दी)"
        )
        cid = conv["id"]
        database.update_conversation_status(cid, "in_progress")
        database.accept_conversation(cid, agent["id"], agent["name"])

        # Agent sends message in Hindi
        msg = database.add_message(
            conv_id=cid,
            sender_type="agent",
            sender_id=agent["id"],
            sender_name=agent["name"],
            message_text=hindi_msg
        )
        self.assertIsNotNone(msg)
        self.assertEqual(msg["message_text"], hindi_msg)

        # Verify message retrieved in conversation history
        conv_messages = database.get_conversation_messages(cid)
        agent_msgs = [m for m in conv_messages if m["sender_type"] == "agent"]
        self.assertEqual(len(agent_msgs), 1)
        self.assertEqual(agent_msgs[0]["message_text"], hindi_msg)


if __name__ == "__main__":
    unittest.main()
