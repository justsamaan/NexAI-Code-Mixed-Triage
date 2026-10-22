"""
test_platform_phase1.py
=======================
Automated test suite verifying PHASE 1 implementation:
- Role separation: Customer vs Agent workspaces and authentication
- PBKDF2 password hashing & secure salt generation
- Customer inquiry isolation (strict customer data privacy)
- Agent language proficiency authorization & queue filtering
- Agent availability status updates
- Conversation persistence, message threading & translations
- Customer feedback submission & CSAT calculations
- Root-cause analysis metrics calculation
- Role-based access control (RBAC) integrity
"""

import unittest
import database
import ai_engine


class TestPhase1Platform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure fresh database initialization before tests."""
        database.init_db()

    def test_01_password_hashing_and_verification(self):
        """Verify PBKDF2 hashing produces unique salts and verifies securely."""
        pwd = "SecretPassword@2026"
        h1, s1 = database.hash_password(pwd)
        h2, s2 = database.hash_password(pwd)
        
        # Unique salts per generation
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(h1, h2)
        
        # Successful verification
        self.assertTrue(database.verify_password(pwd, h1, s1))
        self.assertTrue(database.verify_password(pwd, h2, s2))
        
        # Wrong password fails
        self.assertFalse(database.verify_password("WrongPassword", h1, s1))

    def test_02_user_registration_and_authentication(self):
        """Test customer registration and role assignment."""
        test_user = "test_cust_" + database.secrets.token_hex(3)
        test_email = f"{test_user}@testmail.com"
        created = database.create_user(
            username=test_user,
            email=test_email,
            password="ValidPassword@123",
            name="Test Customer",
            role="customer"
        )
        self.assertEqual(created["role"], "customer")
        self.assertEqual(created["name"], "Test Customer")
        self.assertNotIn("password_hash", created)

        # Authenticate with username
        auth_user = database.authenticate_user(test_user, "ValidPassword@123")
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user["id"], created["id"])

        # Authenticate with email
        auth_email = database.authenticate_user(test_email, "ValidPassword@123")
        self.assertIsNotNone(auth_email)
        self.assertEqual(auth_email["id"], created["id"])

        # Wrong password fails
        self.assertIsNone(database.authenticate_user(test_user, "BadPassword"))

    def test_03_customer_conversation_isolation(self):
        """Verify customers can only view their own support conversations."""
        priya = database.get_user_by_username("customer")
        rahul = database.get_user_by_username("rahul")
        
        priya_convs = database.list_customer_conversations(priya["id"])
        rahul_convs = database.list_customer_conversations(rahul["id"])
        
        self.assertGreater(len(priya_convs), 0)
        self.assertGreater(len(rahul_convs), 0)
        
        priya_ids = {c["id"] for c in priya_convs}
        rahul_ids = {c["id"] for c in rahul_convs}
        
        # Zero overlap between different customers
        self.assertEqual(len(priya_ids.intersection(rahul_ids)), 0)

    def test_04_agent_language_authorization(self):
        """Verify agents can only access tickets matching authorized languages."""
        # Anita is authorized for Tanglish and English only
        anita = database.get_user_by_username("anita")
        self.assertIn("Tanglish", anita["languages"])
        self.assertIn("English", anita["languages"])
        self.assertNotIn("Telugu + English", anita["languages"])
        
        anita_tickets = database.list_agent_conversations(
            agent_id=anita["id"],
            authorized_languages=anita["languages"]
        )
        
        for t in anita_tickets:
            # If not assigned directly to Anita, language must match her authorized skills
            if t.get("assigned_agent_id") != anita["id"]:
                self.assertIn(t["detected_language"], anita["languages"])

    def test_05_agent_availability_updates(self):
        """Verify agent availability status transitions persist."""
        agent = database.get_user_by_username("agent")
        
        # Transition to busy
        database.update_agent_status(agent["id"], "busy")
        refreshed = database.get_user_by_id(agent["id"])
        self.assertEqual(refreshed["availability_status"], "busy")
        
        # Transition back to online
        database.update_agent_status(agent["id"], "online")
        refreshed = database.get_user_by_id(agent["id"])
        self.assertEqual(refreshed["availability_status"], "online")

    def test_06_conversation_creation_and_ai_triage(self):
        """Verify customer can create a code-mixed inquiry and receive persistent AI triage."""
        priya = database.get_user_by_username("customer")
        msg = "naa order inka delivery avvaledu"
        
        # Analyze with real engine
        ai_res = ai_engine.analyze_message(msg)
        
        conv = database.create_conversation(
            customer_id=priya["id"],
            customer_name=priya["name"],
            subject="Late Order Inquiry",
            initial_message=msg,
            ai_analysis=ai_res
        )
        
        self.assertIsNotNone(conv)
        self.assertEqual(conv["customer_id"], priya["id"])
        self.assertEqual(conv["detected_language"], "Telugu + English")
        self.assertIn("delivered", conv["english_translation"].lower())
        self.assertGreater(len(conv["messages"]), 0)
        
        # Check messages distinguish sender_type
        cust_msg = conv["messages"][0]
        self.assertEqual(cust_msg["sender_type"], "customer")
        self.assertEqual(cust_msg["message_text"], msg)

    def test_07_agent_reply_and_status_transition(self):
        """Verify agent reply is distinguished and updates conversation status."""
        agent = database.get_user_by_username("agent")
        priya = database.get_user_by_username("customer")
        conv = database.list_customer_conversations(priya["id"])[0]
        
        # Agent sends human response
        reply_text = "We have escalated this to our logistics partner. Expected delivery by 4 PM."
        msg_record = database.add_message(
            conv_id=conv["id"],
            sender_type="agent",
            sender_id=agent["id"],
            sender_name=agent["name"],
            message_text=reply_text
        )
        self.assertEqual(msg_record["sender_type"], "agent")
        self.assertEqual(msg_record["message_text"], reply_text)
        
        # Update status
        database.update_conversation_status(conv["id"], "in_progress")
        updated_conv = database.get_conversation(conv["id"])
        self.assertEqual(updated_conv["status"], "in_progress")

    def test_08_customer_feedback_persistence(self):
        """Verify customer ratings and feedback persist and feed metrics."""
        priya = database.get_user_by_username("customer")
        convs = [c for c in database.list_customer_conversations(priya["id"]) if not database.get_conversation_feedback(c["id"])]
        if not convs:
            msg = "Feedback test query"
            ai_res = ai_engine.analyze_message(msg)
            conv = database.create_conversation(priya["id"], priya["name"], "Feedback Query", msg, ai_res)
        else:
            conv = convs[0]
        
        fb = database.submit_feedback(
            conv_id=conv["id"],
            customer_id=priya["id"],
            customer_name=priya["name"],
            rating=5,
            category="Resolution Quality",
            comment="Resolved my inquiry swiftly in Telugu."
        )
        self.assertEqual(fb["rating"], 5)
        self.assertEqual(fb["category"], "Resolution Quality")
        
        priya_fb = database.get_customer_feedback(priya["id"])
        self.assertGreaterEqual(len(priya_fb), 1)
        self.assertEqual(priya_fb[0]["customer_id"], priya["id"])

    def test_09_root_cause_analysis_metrics(self):
        """Verify root-cause analytics compute escalation drivers and dialect rates."""
        rc = database.get_root_cause_analysis()
        self.assertIn("top_drivers", rc)
        self.assertIn("language_escalations", rc)
        self.assertIn("ambiguous_cases", rc)
        
        # Metrics return valid structure
        metrics = database.get_platform_metrics()
        self.assertIn("total_conversations", metrics)
        self.assertIn("intent_distribution", metrics)
        self.assertIn("language_distribution", metrics)
        self.assertIn("urgency_distribution", metrics)
        self.assertGreater(metrics["total_conversations"], 0)


if __name__ == "__main__":
    unittest.main()
