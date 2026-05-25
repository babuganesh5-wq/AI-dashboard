# backend/db_manager.py
# Antigravity AI - Rhythm Academy Local Database Manager
# Implements real SQLite persistence matching schema.sql specifications

import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "antigravity.db")

class RhythmDatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes the database schema matching PostgreSQL schema.sql specifications."""
        with self.get_connection() as conn:
            # CRM Prospects Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS CRM_Prospects (
                prospect_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email_hashed TEXT UNIQUE,
                phone_hashed TEXT UNIQUE,
                lead_score REAL DEFAULT 0.00,
                current_funnel_stage TEXT CHECK(current_funnel_stage IN ('INQUIRY', 'QUALIFIED', 'OPPORTUNITY', 'CUSTOMER')) DEFAULT 'INQUIRY',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Platform Identities Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Platform_Identities (
                identity_id TEXT PRIMARY KEY,
                prospect_id TEXT REFERENCES CRM_Prospects(prospect_id) ON DELETE CASCADE,
                platform_name TEXT CHECK(platform_name IN ('INSTAGRAM', 'FACEBOOK', 'WHATSAPP', 'YOUTUBE', 'TELEGRAM')) NOT NULL,
                external_platform_id TEXT NOT NULL,
                handle_name TEXT,
                attribution_gclid TEXT,
                attribution_fbclid TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform_name, external_platform_id)
            );
            """)

            # Comment Triggers Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Comment_Triggers (
                trigger_id TEXT PRIMARY KEY,
                platform_name TEXT CHECK(platform_name IN ('INSTAGRAM', 'YOUTUBE')) NOT NULL,
                keyword TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform_name, keyword)
            );
            """)

            # Conversation Memory Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Multi_Agent_Conversation_Memory (
                memory_id TEXT PRIMARY KEY,
                prospect_id TEXT REFERENCES CRM_Prospects(prospect_id) ON DELETE CASCADE,
                speaker_role TEXT CHECK(speaker_role IN ('PROSPECT', 'AGENT')) NOT NULL,
                message_body TEXT NOT NULL,
                embedding TEXT, -- Stringified floats representing vectors
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Rhythm Academy Leads Table (incorporates course programs ENUM)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Rhythm_Academy_Leads (
                lead_id TEXT PRIMARY KEY,
                prospect_id TEXT REFERENCES CRM_Prospects(prospect_id) ON DELETE CASCADE,
                student_name TEXT NOT NULL,
                whatsapp_number TEXT NOT NULL,
                target_program TEXT CHECK(target_program IN ('3M_PRODUCTION', '6M_PRODUCTION', 'DIPLOMA', 'MUSIC_SCHOOL')) DEFAULT '6M_PRODUCTION',
                lead_source TEXT DEFAULT 'META_ADS',
                is_qualified INTEGER DEFAULT 0,
                studio_visit_scheduled TEXT,
                studio_visit_completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Rhythm Installments Ledger (incorporates installment status ENUM)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Rhythm_Installments_Ledger (
                installment_id TEXT PRIMARY KEY,
                lead_id TEXT REFERENCES Rhythm_Academy_Leads(lead_id) ON DELETE CASCADE,
                installment_number INTEGER NOT NULL,
                amount REAL NOT NULL DEFAULT 15000.00,
                status TEXT CHECK(status IN ('PAID', 'PENDING', 'OVERDUE')) DEFAULT 'PENDING',
                due_date TEXT NOT NULL,
                payment_date TEXT,
                reminder_sent_count INTEGER DEFAULT 0,
                last_reminder_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Rhythm Batches & Faculty
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Rhythm_Batches_Faculty (
                batch_id TEXT PRIMARY KEY,
                batch_name TEXT NOT NULL,
                program_type TEXT CHECK(program_type IN ('3M_PRODUCTION', '6M_PRODUCTION', 'DIPLOMA', 'MUSIC_SCHOOL')) DEFAULT '6M_PRODUCTION',
                assigned_faculty_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                scheduled_slots TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            # Seed comment triggers if empty
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Comment_Triggers")
            if cursor.fetchone()[0] == 0:
                conn.execute("INSERT OR IGNORE INTO Comment_Triggers (trigger_id, platform_name, keyword, workflow_id) VALUES (?, ?, ?, ?)",
                             (str(uuid.uuid4()), "INSTAGRAM", "GROWTH", "ad_generator_workflow"))
                conn.execute("INSERT OR IGNORE INTO Comment_Triggers (trigger_id, platform_name, keyword, workflow_id) VALUES (?, ?, ?, ?)",
                             (str(uuid.uuid4()), "INSTAGRAM", "LEAD", "whatsapp_qualifier_workflow"))
            conn.commit()

    # --- CRM Prospect Queries ---
    def create_prospect(self, first_name: str, last_name: str, email: str, phone: str, funnel_stage: str = "INQUIRY") -> str:
        prospect_id = str(uuid.uuid4())
        import hashlib
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        phone_hash = hashlib.sha256(phone.encode()).hexdigest()
        
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO CRM_Prospects (prospect_id, first_name, last_name, email_hashed, phone_hashed, current_funnel_stage)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (prospect_id, first_name, last_name, email_hash, phone_hash, funnel_stage))
            conn.commit()
        return prospect_id

    def get_prospect(self, prospect_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM CRM_Prospects WHERE prospect_id = ?", (prospect_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_prospect(self, prospect_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM CRM_Prospects WHERE prospect_id = ?", (prospect_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Platform Identity Queries ---
    def register_platform_identity(self, prospect_id: str, platform_name: str, external_id: str, handle_name: str, fbclid: str = None, gclid: str = None) -> str:
        identity_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO Platform_Identities (identity_id, prospect_id, platform_name, external_platform_id, handle_name, attribution_fbclid, attribution_gclid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (identity_id, prospect_id, platform_name, external_id, handle_name, fbclid, gclid))
            conn.commit()
        return identity_id

    def get_prospect_by_identity(self, platform_name: str, external_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT p.*, i.handle_name, i.attribution_fbclid, i.attribution_gclid 
            FROM CRM_Prospects p
            JOIN Platform_Identities i ON p.prospect_id = i.prospect_id
            WHERE i.platform_name = ? AND i.external_platform_id = ?
            """, (platform_name, external_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Rhythm Academy Leads Queries ---
    def create_lead(self, prospect_id: str, student_name: str, whatsapp_number: str, target_program: str = "6M_PRODUCTION", source: str = "META_ADS") -> str:
        lead_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO Rhythm_Academy_Leads (lead_id, prospect_id, student_name, whatsapp_number, target_program, lead_source)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (lead_id, prospect_id, student_name, whatsapp_number, target_program, source))
            conn.commit()
        return lead_id

    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM Rhythm_Academy_Leads WHERE lead_id = ?", (lead_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_lead_qualification(self, lead_id: str, is_qualified: bool, visit_scheduled: str = None, visit_completed: bool = False) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute("""
            UPDATE Rhythm_Academy_Leads
            SET is_qualified = ?, studio_visit_scheduled = ?, studio_visit_completed = ?
            WHERE lead_id = ?
            """, (1 if is_qualified else 0, visit_scheduled, 1 if visit_completed else 0, lead_id))
            
            # If qualified, update the main CRM funnel stage to QUALIFIED
            if is_qualified:
                conn.execute("""
                UPDATE CRM_Prospects
                SET current_funnel_stage = 'QUALIFIED'
                WHERE prospect_id = (SELECT prospect_id FROM Rhythm_Academy_Leads WHERE lead_id = ?)
                """, (lead_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_leads_with_details(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT l.*, p.current_funnel_stage, 
                   (SELECT COUNT(*) FROM Rhythm_Installments_Ledger WHERE lead_id = l.lead_id AND status = 'PAID') as installments_paid,
                   (SELECT COUNT(*) FROM Rhythm_Installments_Ledger WHERE lead_id = l.lead_id AND status = 'OVERDUE') as installments_overdue
            FROM Rhythm_Academy_Leads l
            JOIN CRM_Prospects p ON l.prospect_id = p.prospect_id
            ORDER BY l.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # --- Rhythm Installments Ledger Queries ---
    def record_installment(self, lead_id: str, installment_number: int, amount: float = 15000.00, due_days: int = 30) -> str:
        installment_id = str(uuid.uuid4())
        due_date = (datetime.now() + timedelta(days=due_days)).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO Rhythm_Installments_Ledger (installment_id, lead_id, installment_number, amount, status, due_date)
            VALUES (?, ?, ?, ?, 'PENDING', ?)
            """, (installment_id, lead_id, installment_number, amount, due_date))
            conn.commit()
        return installment_id

    def update_installment_status(self, installment_id: str, status: str) -> bool:
        pay_date = datetime.now().isoformat() if status == "PAID" else None
        with self.get_connection() as conn:
            cursor = conn.execute("""
            UPDATE Rhythm_Installments_Ledger
            SET status = ?, payment_date = ?
            WHERE installment_id = ?
            """, (status, pay_date, installment_id))
            
            # If second installment is paid, update CRM Prospect to CUSTOMER
            if status == "PAID":
                cursor_lead = conn.execute("SELECT lead_id, installment_number FROM Rhythm_Installments_Ledger WHERE installment_id = ?", (installment_id,))
                lead_row = cursor_lead.fetchone()
                if lead_row and lead_row["installment_number"] == 2:
                    conn.execute("""
                    UPDATE CRM_Prospects
                    SET current_funnel_stage = 'CUSTOMER'
                    WHERE prospect_id = (SELECT prospect_id FROM Rhythm_Academy_Leads WHERE lead_id = ?)
                    """, (lead_row["lead_id"],))
            conn.commit()
            return cursor.rowcount > 0

    def increment_installment_reminder(self, installment_id: str) -> bool:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute("""
            UPDATE Rhythm_Installments_Ledger
            SET reminder_sent_count = reminder_sent_count + 1, last_reminder_at = ?
            WHERE installment_id = ?
            """, (now, installment_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_overdue_installments(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT i.*, l.student_name, l.whatsapp_number, l.target_program
            FROM Rhythm_Installments_Ledger i
            JOIN Rhythm_Academy_Leads l ON i.lead_id = l.lead_id
            WHERE i.status = 'OVERDUE' OR (i.status = 'PENDING' AND datetime(i.due_date) < datetime('now'))
            """)
            return [dict(row) for row in cursor.fetchall()]

    # --- Rhythm Batches & Faculty Queries ---
    def create_batch(self, batch_name: str, program_type: str, faculty_name: str, slots: str) -> str:
        batch_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO Rhythm_Batches_Faculty (batch_id, batch_name, program_type, assigned_faculty_name, scheduled_slots)
            VALUES (?, ?, ?, ?, ?)
            """, (batch_id, batch_name, program_type, faculty_name, slots))
            conn.commit()
        return batch_id

    def get_batches(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM Rhythm_Batches_Faculty WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

db_manager = RhythmDatabaseManager()
