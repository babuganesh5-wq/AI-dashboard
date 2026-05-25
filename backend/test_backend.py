# backend/test_backend.py
# Antigravity AI - Backend Integrations & Business Logic Test Suite
# Simulated Backend QA Team Assertions

import os
import unittest
import hmac
import hashlib
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Force test database for isolation
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_antigravity.db")
os.environ["DATABASE_PATH"] = TEST_DB_PATH

# Mock Redis BEFORE importing backend.ingest_router to prevent connection failure crashes
mock_redis = MagicMock()
mock_redis.publish = AsyncMock(return_value=1)

with patch('redis.asyncio.from_url', return_value=mock_redis):
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.conversion_engine import AdAlgorithmOptimizer
    from backend.workflow import AgentWorkflowState, get_event_field
    from backend.ingest_router import InboundSocialEvent
    from backend.db_manager import db_manager

class TestRhythmBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up active test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        db_manager.__init__(db_path=TEST_DB_PATH)
        cls.client = TestClient(app)
        cls.optimizer = AdAlgorithmOptimizer()

    @classmethod
    def tearDownClass(cls):
        # Cleanup
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except PermissionError:
                pass

    def test_01_value_lift_engine(self):
        """Test the Asynchronous Value Lift Engine formulas & modifiers."""
        # 1A: Base standard WhatsApp lead (no modifiers)
        val = self.client.get("/").json() # Just checking API status
        self.assertEqual(val["status"], "online")
        
        # Test calculations directly
        import asyncio
        
        # Standard: 5000.00
        calc_std = asyncio.run(self.optimizer.calculate_value_lift("WHATSAPP_LEAD", response_speed_seconds=300.0, program_type="6M_PRODUCTION"))
        self.assertEqual(calc_std, 5000.00)
        
        # Fast response modifier (<= 180s) -> 1.5x -> 7500.00
        calc_fast = asyncio.run(self.optimizer.calculate_value_lift("WHATSAPP_LEAD", response_speed_seconds=120.0, program_type="6M_PRODUCTION"))
        self.assertEqual(calc_fast, 7500.00)
        
        # Diploma program target booster -> 1.2x -> 6000.00
        calc_dip = asyncio.run(self.optimizer.calculate_value_lift("WHATSAPP_LEAD", response_speed_seconds=300.0, program_type="DIPLOMA"))
        self.assertEqual(calc_dip, 6000.00)
        
        # Dual modifiers (Fast + Diploma) -> 5000 * 1.5 * 1.2 -> 9000.00
        calc_both = asyncio.run(self.optimizer.calculate_value_lift("WHATSAPP_LEAD", response_speed_seconds=60.0, program_type="DIPLOMA"))
        self.assertEqual(calc_both, 9000.00)
        
        # Studio Visit baseline -> 10000.00
        calc_visit = asyncio.run(self.optimizer.calculate_value_lift("STUDIO_VISIT", response_speed_seconds=300.0, program_type="6M_PRODUCTION"))
        self.assertEqual(calc_visit, 10000.00)

    @patch('backend.ingest_router.redis_client', mock_redis)
    def test_02_cryptographic_webhook_signatures(self):
        """Verify OpenSec HMAC SHA-256 Meta webhook validation and spoof blocks."""
        payload = {"object": "page", "entry": [{"id": "123", "changes": [{"field": "comments", "value": {"comment_id": "c1", "text": "I want to SCALE", "from": {"id": "user_ig_1"}}}]}]}
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        # Compute valid HMAC signature
        secret = "meta_app_secret_credential_hash"
        signature_hash = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        
        # 2A: Valid signature should pass with 200 Accepted
        response_ok = self.client.post(
            "/api/v1/webhooks/meta",
            content=payload_bytes,
            headers={
                "x-hub-signature-256": f"sha256={signature_hash}",
                "Content-Type": "application/json"
            }
        )
        self.assertEqual(response_ok.status_code, 200)
        self.assertEqual(response_ok.json()["status"], "accepted")
        
        # 2B: Invalid/Spoofed signature must be blocked instantly (403 Forbidden)
        response_bad = self.client.post(
            "/api/v1/webhooks/meta",
            content=payload_bytes,
            headers={
                "x-hub-signature-256": "sha256=spoofed_signature_hash_xyz",
                "Content-Type": "application/json"
            }
        )
        self.assertEqual(response_bad.status_code, 403)
        self.assertEqual(response_bad.json()["detail"], "Invalid hub signature.")

    def test_03_youtube_webhook_ingest(self):
        """Verify YouTube subscription XML feed webhook processing."""
        response = self.client.post(
            "/api/v1/webhooks/youtube",
            content="<feed><entry><id>yt_id_123</id></entry></feed>",
            headers={"Content-Type": "application/xml"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_04_langgraph_workflow_routing(self):
        """Verify multi-agent StateGraph flow, database operations, and CAPI lift."""
        import asyncio
        
        # Create state graph orchestrator
        workflow = AgentWorkflowState()
        
        # Prepare inbound event
        mock_event = InboundSocialEvent(
            platform="WHATSAPP",
            sender_platform_id="919988776655",
            text_content="I am looking to enroll in the music PRODUCTION course!",
            attribution_click_id="fb_click_id_99999"
        )
        
        initial_state = {
            "event": mock_event,
            "sender_name": "Tushar Dev"
        }
        
        # Execute workflow loop asynchronously
        final_state = asyncio.run(workflow.runtime.ainvoke(initial_state))
        
        # Verify state changes
        self.assertEqual(final_state["whatsapp_number"], "919988776655")
        self.assertEqual(final_state["student_name"], "Tushar Dev")
        self.assertEqual(final_state["course_intent"], "MUSIC_PRODUCTION")
        self.assertTrue(final_state["qualification_completed"])
        self.assertTrue(final_state["studio_visit_booked"])
        self.assertEqual(final_state["milestone"], "STUDIO_VISIT")
        
        # Verify Value Lift CAPI details
        self.assertIn("value_lift_metrics", final_state)
        self.assertEqual(final_state["value_lift_metrics"]["status"], "success")
        self.assertEqual(final_state["value_lift_metrics"]["value_lifted"], 15000.00) # Fast (<=180s) Studio Visit conversion value
        
        # Check that the database contains the registered prospect, lead, and split installments
        prospect = db_manager.get_prospect_by_identity("WHATSAPP", "919988776655")
        self.assertIsNotNone(prospect)
        self.assertEqual(prospect["first_name"], "Tushar")
        self.assertEqual(prospect["current_funnel_stage"], "QUALIFIED")
        
        leads = db_manager.get_all_leads_with_details()
        self.assertGreater(len(leads), 0)
        
        # Find the matching lead and verify installment rows in DB
        matching_lead = None
        for l in leads:
            if l["whatsapp_number"] == "919988776655":
                matching_lead = l
                break
                
        self.assertIsNotNone(matching_lead)
        self.assertEqual(matching_lead["is_qualified"], 1)
        
        # Check split installments ledger
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM Rhythm_Installments_Ledger WHERE lead_id = ? ORDER BY installment_number", (matching_lead["lead_id"],)).fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["installment_number"], 1)
            self.assertEqual(rows[0]["amount"], 15000.00)
            self.assertEqual(rows[1]["installment_number"], 2)
            self.assertEqual(rows[1]["amount"], 15000.00)

if __name__ == "__main__":
    print("\n\033[0;32m====================================================\033[RESET]")
    print("\033[0;32m    RUNNING BACKEND INTEGRITY TEST SUITE...         \033[RESET]")
    print("\033[0;32m====================================================\033[RESET]")
    unittest.main()
