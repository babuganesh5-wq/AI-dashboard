# backend/test_database.py
# Antigravity AI - Relational Database Integrity Test Suite
# Simulated Database QA Team Assertions

import os
import unittest
import sqlite3
import hashlib
from backend.db_manager import RhythmDatabaseManager

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_antigravity.db")

class TestRhythmDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure a fresh test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        cls.db = RhythmDatabaseManager(db_path=TEST_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        # Cleanup test database
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except PermissionError:
                pass

    def test_01_prospect_crud(self):
        """Verify CRM Prospect creation, retrieval, and fields integrity."""
        pid = self.db.create_prospect(
            first_name="Ganesh",
            last_name="Babu",
            email="ganesh@rhythmacademy.com",
            phone="+919876543210",
            funnel_stage="INQUIRY"
        )
        self.assertIsNotNone(pid)
        self.assertEqual(len(pid), 36) # UUID length

        prospect = self.db.get_prospect(pid)
        self.assertIsNotNone(prospect)
        self.assertEqual(prospect["first_name"], "Ganesh")
        self.assertEqual(prospect["last_name"], "Babu")
        self.assertEqual(prospect["current_funnel_stage"], "INQUIRY")
        
        # Test unique constraint for email hashes
        email_hash = hashlib.sha256("ganesh@rhythmacademy.com".encode()).hexdigest()
        self.assertEqual(prospect["email_hashed"], email_hash)

    def test_02_platform_identity_mapping(self):
        """Verify resolving a third-party social handle to the master CRM prospect."""
        pid = self.db.create_prospect("Aditya", "Sharma", "aditya@rhythm.com", "+919999999999")
        
        # Register a WhatsApp PSID
        self.db.register_platform_identity(
            prospect_id=pid,
            platform_name="WHATSAPP",
            external_id="919999999999",
            handle_name="aditya_sharma_ig",
            fbclid="fb_click_id_abc123"
        )

        # Resolve identity back to master prospect
        prospect = self.db.get_prospect_by_identity("WHATSAPP", "919999999999")
        self.assertIsNotNone(prospect)
        self.assertEqual(prospect["first_name"], "Aditya")
        self.assertEqual(prospect["attribution_fbclid"], "fb_click_id_abc123")

    def test_03_lead_and_installment_flows(self):
        """Verify Rhythm Academy Course enrollments and Split Installments Ledger entries."""
        pid = self.db.create_prospect("Siddharth", "Roy", "sid@rhythm.com", "+918888888888")
        
        # Create Academy lead targeting a 6-month Production course
        lead_id = self.db.create_lead(
            prospect_id=pid,
            student_name="Siddharth Roy",
            whatsapp_number="918888888888",
            target_program="6M_PRODUCTION",
            source="META_ADS"
        )
        self.assertIsNotNone(lead_id)

        lead = self.db.get_lead(lead_id)
        self.assertEqual(lead["student_name"], "Siddharth Roy")
        self.assertEqual(lead["target_program"], "6M_PRODUCTION")
        self.assertEqual(lead["is_qualified"], 0)

        # Record split installments (₹15,000 + ₹15,000)
        inst1_id = self.db.record_installment(lead_id, installment_number=1, amount=15000.00, due_days=1)
        inst2_id = self.db.record_installment(lead_id, installment_number=2, amount=15000.00, due_days=30)
        self.assertIsNotNone(inst1_id)
        self.assertIsNotNone(inst2_id)

        # Test updating lead to Qualified
        self.db.update_lead_qualification(lead_id, is_qualified=True, visit_scheduled="2026-06-01T11:00:00")
        lead_updated = self.db.get_lead(lead_id)
        self.assertEqual(lead_updated["is_qualified"], 1)
        self.assertEqual(lead_updated["studio_visit_scheduled"], "2026-06-01T11:00:00")

        # Confirm the CRM prospect stage automatically escalated to QUALIFIED
        prospect_updated = self.db.get_prospect(pid)
        self.assertEqual(prospect_updated["current_funnel_stage"], "QUALIFIED")

        # Pay off the first installment and test balance updates
        self.db.update_installment_status(inst1_id, "PAID")
        
        # Verify first installment status
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status, payment_date FROM Rhythm_Installments_Ledger WHERE installment_id = ?", (inst1_id,)).fetchone()
            self.assertEqual(row["status"], "PAID")
            self.assertIsNotNone(row["payment_date"])

        # Pay off second installment (triggers Customer conversion)
        self.db.update_installment_status(inst2_id, "PAID")
        prospect_converted = self.db.get_prospect(pid)
        self.assertEqual(prospect_converted["current_funnel_stage"], "CUSTOMER")

    def test_04_cascading_deletes(self):
        """Test strict OpenSec deletion cascades to isolate student record removals."""
        pid = self.db.create_prospect("Temp", "Student", "temp@rhythm.com", "+917777777777")
        lead_id = self.db.create_lead(pid, "Temp Student", "917777777777")
        inst_id = self.db.record_installment(lead_id, installment_number=1)

        # Delete the root prospect and check cascades
        deleted = self.db.delete_prospect(pid)
        self.assertTrue(deleted)

        self.assertIsNone(self.db.get_prospect(pid))
        self.assertIsNone(self.db.get_lead(lead_id))
        
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM Rhythm_Installments_Ledger WHERE installment_id = ?", (inst_id,)).fetchone()
            self.assertIsNone(row)

    def test_05_faculty_batches(self):
        """Verify faculty assigned double batches schedule setups."""
        bid = self.db.create_batch(
            batch_name="Batch Alpha",
            program_type="DIPLOMA",
            faculty_name="Prof. Keith",
            slots="Mon/Wed 10:00-12:00"
        )
        self.assertIsNotNone(bid)
        
        batches = self.db.get_batches()
        self.assertGreater(len(batches), 0)
        self.assertEqual(batches[0]["assigned_faculty_name"], "Prof. Keith")
        self.assertEqual(batches[0]["batch_name"], "Batch Alpha")

if __name__ == "__main__":
    print("\n\033[0;36m====================================================\033[RESET]")
    print("\033[0;36m    RUNNING DATABASE QA INTEGRITY TEST SUITE...     \033[RESET]")
    print("\033[0;36m====================================================\033[RESET]")
    unittest.main()
