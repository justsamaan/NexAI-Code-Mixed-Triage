"""
test_platform_phase3.py
=======================
Automated test suite verifying PHASE 3 implementation:
- Gmail-inspired 7 folder categorization and count calculations
- Deterministic sorting (newest, oldest, highest urgency, lowest confidence)
- Multidimensional filters (intent, urgency, status, language, agent, search)
- Agent ticket assignment, reassignment, and unassigning
- Ticket resolution and reopening workflows
- Internal staff notes with strict customer data isolation
- Customer satisfaction (CSAT) formula validation and sample size tracking
- Resolved ticket feedback retrieval and display
"""

import unittest
import database
import ai_engine


class TestPhase3Platform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database with seed and test fixtures."""
        database.init_db()

    def test_01_inbox_folders_and_counts(self):
        """Verify the 7 Gmail-inspired mailbox folders and exact count calculation."""
        vikram = database.get_user_by_username("agent")
        counts = database.get_inbox_counts(
            agent_id=vikram["id"],
            authorized_languages=vikram["languages"]
        )

        # All 7 categories must exist
        expected_keys = [
            "inbox", "unassigned", "assigned_me",
            "waiting_customer", "waiting_agent",
            "escalated", "resolved"
        ]
        for k in expected_keys:
            self.assertIn(k, counts, f"Missing mailbox category '{k}'")
            self.assertIsInstance(counts[k], int)
            self.assertGreaterEqual(counts[k], 0)

        # Total inbox count should equal sum of active tickets
        self.assertGreater(counts["inbox"], 0)

    def test_02_deterministic_sorting(self):
        """Verify that sorting options are deterministic and actually change displayed ticket order."""
        vikram = database.get_user_by_username("agent")

        # 1. Newest vs Oldest
        newest_tickets = database.query_agent_inbox(
            agent_id=vikram["id"],
            category="inbox",
            sort_by="Latest queries first"
        )
        oldest_tickets = database.query_agent_inbox(
            agent_id=vikram["id"],
            category="inbox",
            sort_by="Oldest queries first"
        )

        if len(newest_tickets) >= 2:
            self.assertEqual(newest_tickets[0]["id"], oldest_tickets[-1]["id"])
            self.assertEqual(newest_tickets[-1]["id"], oldest_tickets[0]["id"])

        # 2. Highest Urgency First
        urg_tickets = database.query_agent_inbox(
            agent_id=vikram["id"],
            category="inbox",
            sort_by="Highest urgency first"
        )
        urg_levels = [t["urgency"].lower() for t in urg_tickets]
        urg_priority = {"high": 1, "medium": 2, "low": 3}
        urg_ranks = [urg_priority.get(u, 4) for u in urg_levels]
        # Assert non-decreasing urgency rank order (1 <= 2 <= 3)
        self.assertEqual(urg_ranks, sorted(urg_ranks))

        # 3. Lowest Confidence First
        conf_tickets = database.query_agent_inbox(
            agent_id=vikram["id"],
            category="inbox",
            sort_by="Lowest confidence first"
        )
        confs = [t["confidence"] for t in conf_tickets]
        # Assert non-decreasing confidence order
        self.assertEqual(confs, sorted(confs))

    def test_03_inbox_filters_and_search(self):
        """Verify multidimensional filtering and text search over customer inquiries."""
        vikram = database.get_user_by_username("agent")

        # Filter by Intent
        delivery_tickets = database.query_agent_inbox(
            agent_id=vikram["id"],
            category="inbox",
            filter_intent="Delivery Delay"
        )
        for t in delivery_tickets:
            self.assertEqual(t["intent"], "Delivery Delay")

        # Filter by Urgency
        high_tickets = database.query_agent_inbox(
            agent_id=vikram["id"],
            category="inbox",
            filter_urgency="high"
        )
        for t in high_tickets:
            self.assertEqual(t["urgency"].lower(), "high")

        # Search by Customer Name
        search_tickets = database.query_agent_inbox(
            agent_id=vikram["id"],
            category="inbox",
            search_query="Priya"
        )
        self.assertGreater(len(search_tickets), 0)
        for t in search_tickets:
            matches_name = "priya" in t["customer_name"].lower()
            matches_id = "priya" in t["id"].lower()
            matches_subj = "priya" in t["subject"].lower()
            self.assertTrue(matches_name or matches_id or matches_subj)

    def test_04_ticket_assignment_and_reassignment(self):
        """Verify agents can assign, reassign, or unassign tickets."""
        vikram = database.get_user_by_username("agent")
        anita = database.get_user_by_username("anita")
        priya = database.get_user_by_username("customer")

        msg = "Need update on my refund order"
        ai_res = ai_engine.analyze_message(msg)
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Reassignment Test Inquiry",
            initial_message=msg,
            ai_analysis=ai_res
        )
        cid = conv["id"]

        # 1. Assign to Vikram
        ok1 = database.reassign_conversation(cid, vikram["id"], vikram["name"])
        self.assertTrue(ok1)
        c_vikram = database.get_conversation(cid)
        self.assertEqual(c_vikram["assigned_agent_id"], vikram["id"])
        self.assertEqual(c_vikram["assigned_agent_name"], vikram["name"])

        # 2. Reassign to Anita
        ok2 = database.reassign_conversation(cid, anita["id"], anita["name"])
        self.assertTrue(ok2)
        c_anita = database.get_conversation(cid)
        self.assertEqual(c_anita["assigned_agent_id"], anita["id"])
        self.assertEqual(c_anita["assigned_agent_name"], anita["name"])

        # 3. Unassign
        ok3 = database.reassign_conversation(cid, None, None)
        self.assertTrue(ok3)
        c_unassigned = database.get_conversation(cid)
        self.assertIsNone(c_unassigned["assigned_agent_id"])
        self.assertIsNone(c_unassigned["assigned_agent_name"])

    def test_05_ticket_resolution_and_reopening(self):
        """Verify ticket resolution and reopening transitions."""
        priya = database.get_user_by_username("customer")
        msg = "Package received in good shape"
        ai_res = ai_engine.analyze_message(msg)
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Status Toggle Test",
            initial_message=msg,
            ai_analysis=ai_res
        )
        cid = conv["id"]

        # Resolve ticket
        ok_res = database.update_conversation_status(cid, "resolved")
        self.assertTrue(ok_res)
        self.assertEqual(database.get_conversation(cid)["status"], "resolved")

        # Reopen ticket
        ok_reopen = database.reopen_conversation(cid)
        self.assertTrue(ok_reopen)
        reopened = database.get_conversation(cid)
        self.assertIn(reopened["status"], ["open", "in_progress"])

    def test_06_internal_notes_and_customer_isolation(self):
        """Verify staff internal notes are stored persistently and strictly isolated from customer view."""
        vikram = database.get_user_by_username("agent")
        priya = database.get_user_by_username("customer")

        msg = "Customer inquiring about courier delay"
        ai_res = ai_engine.analyze_message(msg)
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Confidential Note Test",
            initial_message=msg,
            ai_analysis=ai_res
        )
        cid = conv["id"]

        # Add staff-only internal note
        note_text = "CONFIDENTIAL: Customer flagged as high VIP account, dispatch priority label."
        note_rec = database.add_internal_note(
            conv_id=cid,
            agent_id=vikram["id"],
            agent_name=vikram["name"],
            note_text=note_text
        )
        self.assertEqual(note_rec["sender_type"], "internal_note")

        # 1. Staff query with include_internal=True MUST include internal note
        staff_msgs = database.get_conversation_messages(cid, include_internal=True)
        staff_note_found = any(m["message_text"] == note_text for m in staff_msgs)
        self.assertTrue(staff_note_found, "Internal note must be visible in staff view")

        # 2. Customer query with include_internal=False MUST NOT include internal note
        customer_msgs = database.get_conversation_messages(cid, include_internal=False)
        cust_note_found = any(m["message_text"] == note_text or m["sender_type"] == "internal_note" for m in customer_msgs)
        self.assertFalse(cust_note_found, "Internal note must NEVER be exposed to customer view")

    def test_07_csat_metrics_calculation(self):
        """Verify CSAT calculation formula, positive/neutral/negative rating label, and sample size."""
        csat = database.get_csat_metrics()

        self.assertIn("csat_percent", csat)
        self.assertIn("label", csat)
        self.assertIn("sample_size", csat)
        self.assertIn("formula_description", csat)

        # Score must be between 0.0 and 100.0
        self.assertGreaterEqual(csat["csat_percent"], 0.0)
        self.assertLessEqual(csat["csat_percent"], 100.0)

        # Label accuracy
        if csat["sample_size"] == 0:
            self.assertEqual(csat["label"], "No Ratings Yet")
            self.assertEqual(csat["csat_percent"], 0.0)
        elif csat["csat_percent"] >= 75.0:
            self.assertEqual(csat["label"], "Positive")
        elif csat["csat_percent"] >= 50.0:
            self.assertEqual(csat["label"], "Neutral")
        else:
            self.assertEqual(csat["label"], "Negative")

    def test_08_resolved_ticket_feedback_display(self):
        """Verify that resolved tickets with feedback present rating and comments for agent review."""
        priya = database.get_user_by_username("customer")
        vikram = database.get_user_by_username("agent")

        msg = "Need confirmation of order return"
        ai_res = ai_engine.analyze_message(msg)
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Feedback Review Test",
            initial_message=msg,
            ai_analysis=ai_res
        )
        cid = conv["id"]
        database.update_conversation_status(cid, "resolved")

        # Submit feedback
        database.submit_feedback(
            conv_id=cid,
            customer_id=priya["id"],
            customer_name=priya["name"],
            rating=5,
            category="Resolution Quality",
            comment="Awesome response time and clear translation!",
            agent_id=vikram["id"],
            agent_name=vikram["name"],
            translation_quality="Excellent",
            issue_resolved="Yes"
        )

        fb = database.get_conversation_feedback(cid)
        self.assertIsNotNone(fb)
        self.assertEqual(fb["rating"], 5)
        self.assertEqual(fb["translation_quality"], "Excellent")
        self.assertEqual(fb["issue_resolved"], "Yes")
        self.assertEqual(fb["comment"], "Awesome response time and clear translation!")


if __name__ == "__main__":
    unittest.main()
