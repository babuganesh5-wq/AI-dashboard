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

            # --- Social Media Insights Tables ---

            # Social Content Posts — tracks all monitored content across platforms
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Social_Content_Posts (
                content_id TEXT PRIMARY KEY,
                platform TEXT CHECK(platform IN ('INSTAGRAM','FACEBOOK','YOUTUBE')) NOT NULL,
                content_type TEXT CHECK(content_type IN ('REEL','STORY','POST','SHORT','VIDEO')) NOT NULL,
                title TEXT NOT NULL,
                caption TEXT,
                post_url TEXT,
                media_url TEXT,
                posted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Social Content Metrics — engagement analytics per content piece
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Social_Content_Metrics (
                metric_id TEXT PRIMARY KEY,
                content_id TEXT REFERENCES Social_Content_Posts(content_id) ON DELETE CASCADE,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                reach INTEGER DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                avg_watch_pct REAL DEFAULT 0.0,
                dm_triggers_fired INTEGER DEFAULT 0,
                leads_generated INTEGER DEFAULT 0,
                students_converted INTEGER DEFAULT 0,
                last_synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Social Comment Captures — comment-to-lead capture records
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Social_Comment_Captures (
                capture_id TEXT PRIMARY KEY,
                content_id TEXT REFERENCES Social_Content_Posts(content_id) ON DELETE CASCADE,
                prospect_id TEXT REFERENCES CRM_Prospects(prospect_id) ON DELETE SET NULL,
                platform TEXT NOT NULL,
                commenter_handle TEXT NOT NULL,
                commenter_platform_id TEXT,
                comment_text TEXT NOT NULL,
                keyword_matched TEXT,
                dm_sent INTEGER DEFAULT 0,
                dm_response_received INTEGER DEFAULT 0,
                converted_to_lead INTEGER DEFAULT 0,
                lead_id TEXT REFERENCES Rhythm_Academy_Leads(lead_id) ON DELETE SET NULL,
                captured_at TEXT DEFAULT CURRENT_TIMESTAMP
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

            # Seed social demo data if tables are empty
            self.seed_social_demo_data()

    def seed_social_demo_data(self):
        """Seeds demo social content posts with realistic metrics if tables are empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Social_Content_Posts")
            if cursor.fetchone()[0] > 0:
                return  # Already seeded

            import random

            demo_content = [
                {
                    "platform": "INSTAGRAM",
                    "content_type": "REEL",
                    "title": "Behind the Beats: Studio Tour at Rhythm Academy",
                    "caption": "Step inside our world-class production studio! 🎧🔥 #MusicProduction #RhythmAcademy",
                    "post_url": "https://instagram.com/reel/demo_reel_001",
                    "media_url": "https://cdn.rhythmacademy.com/reels/studio_tour.mp4",
                    "views": 145000, "likes": 12500, "comments": 890, "shares": 2300,
                    "saves": 4500, "reach": 120000, "impressions": 198000, "avg_watch_pct": 72.5,
                    "dm_triggers": 45, "leads": 18, "students": 4
                },
                {
                    "platform": "INSTAGRAM",
                    "content_type": "REEL",
                    "title": "Student Showcase: From Zero to Producer in 6 Months",
                    "caption": "Watch Arjun's incredible journey from beginner to certified producer! 🎵✨ #StudentSuccess",
                    "post_url": "https://instagram.com/reel/demo_reel_002",
                    "media_url": "https://cdn.rhythmacademy.com/reels/student_showcase.mp4",
                    "views": 230000, "likes": 22000, "comments": 1500, "shares": 5600,
                    "saves": 8200, "reach": 195000, "impressions": 340000, "avg_watch_pct": 81.2,
                    "dm_triggers": 78, "leads": 35, "students": 8
                },
                {
                    "platform": "YOUTUBE",
                    "content_type": "VIDEO",
                    "title": "Complete Music Production Course Preview | Rhythm Academy",
                    "caption": "Everything you need to know about our 6-month production diploma. Enroll now!",
                    "post_url": "https://youtube.com/watch?v=demo_video_001",
                    "media_url": "https://cdn.rhythmacademy.com/videos/course_preview.mp4",
                    "views": 89000, "likes": 6700, "comments": 420, "shares": 1200,
                    "saves": 3100, "reach": 72000, "impressions": 145000, "avg_watch_pct": 58.3,
                    "dm_triggers": 32, "leads": 14, "students": 3
                },
                {
                    "platform": "YOUTUBE",
                    "content_type": "SHORT",
                    "title": "60-Second Beat Making Challenge 🎹",
                    "caption": "Can you make a full beat in 60 seconds? Watch our students try! #Shorts #MusicChallenge",
                    "post_url": "https://youtube.com/shorts/demo_short_001",
                    "media_url": "https://cdn.rhythmacademy.com/shorts/beat_challenge.mp4",
                    "views": 320000, "likes": 28000, "comments": 2100, "shares": 8900,
                    "saves": 11000, "reach": 280000, "impressions": 520000, "avg_watch_pct": 88.7,
                    "dm_triggers": 95, "leads": 42, "students": 11
                },
                {
                    "platform": "FACEBOOK",
                    "content_type": "POST",
                    "title": "Rhythm Academy Batch Alpha Graduation Ceremony 🎓",
                    "caption": "Proud of our first batch of graduates! 15 certified music producers ready for the industry.",
                    "post_url": "https://facebook.com/rhythmacademy/posts/demo_post_001",
                    "media_url": "https://cdn.rhythmacademy.com/posts/graduation.jpg",
                    "views": 45000, "likes": 3800, "comments": 280, "shares": 950,
                    "saves": 620, "reach": 38000, "impressions": 62000, "avg_watch_pct": 0.0,
                    "dm_triggers": 15, "leads": 7, "students": 2
                },
                {
                    "platform": "INSTAGRAM",
                    "content_type": "STORY",
                    "title": "Live Q&A: Ask Our Faculty Anything About Music Production",
                    "caption": "Join our live session this Friday at 7 PM IST! Drop your questions below 👇",
                    "post_url": "https://instagram.com/stories/demo_story_001",
                    "media_url": "https://cdn.rhythmacademy.com/stories/live_qa.mp4",
                    "views": 18000, "likes": 2200, "comments": 340, "shares": 180,
                    "saves": 290, "reach": 15000, "impressions": 24000, "avg_watch_pct": 65.0,
                    "dm_triggers": 22, "leads": 9, "students": 1
                },
            ]

            for content in demo_content:
                content_id = str(uuid.uuid4())
                metric_id = str(uuid.uuid4())
                posted_days_ago = random.randint(1, 60)
                posted_at = (datetime.now() - timedelta(days=posted_days_ago)).isoformat()

                conn.execute("""
                INSERT INTO Social_Content_Posts 
                    (content_id, platform, content_type, title, caption, post_url, media_url, posted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_id, content["platform"], content["content_type"],
                    content["title"], content["caption"], content["post_url"],
                    content["media_url"], posted_at
                ))

                conn.execute("""
                INSERT INTO Social_Content_Metrics 
                    (metric_id, content_id, views, likes, comments, shares, saves, 
                     reach, impressions, avg_watch_pct, dm_triggers_fired, leads_generated, students_converted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric_id, content_id, content["views"], content["likes"],
                    content["comments"], content["shares"], content["saves"],
                    content["reach"], content["impressions"], content["avg_watch_pct"],
                    content["dm_triggers"], content["leads"], content["students"]
                ))

            conn.commit()
            print(f"[DB_SEED] Seeded {len(demo_content)} social content posts with metrics.")

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

    def get_all_prospects(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM CRM_Prospects")
            return [dict(row) for row in cursor.fetchall()]

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

    # --- Social Content Posts CRUD ---
    def create_content_post(
        self,
        platform: str,
        content_type: str,
        title: str,
        caption: str = "",
        post_url: str = "",
        media_url: str = "",
        posted_at: str = None
    ) -> str:
        """Creates a new social content post record and initializes its metrics."""
        content_id = str(uuid.uuid4())
        posted_at = posted_at or datetime.now().isoformat()

        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO Social_Content_Posts 
                (content_id, platform, content_type, title, caption, post_url, media_url, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (content_id, platform.upper(), content_type.upper(), title, caption, post_url, media_url, posted_at))
            conn.commit()

        # Auto-initialize a metrics record for this content
        self.create_content_metrics(content_id)
        return content_id

    def get_content_post(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single social content post by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM Social_Content_Posts WHERE content_id = ?", (content_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_content_posts(self) -> List[Dict[str, Any]]:
        """Retrieves all social content posts ordered by posted_at descending."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM Social_Content_Posts ORDER BY posted_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # --- Social Content Metrics CRUD ---
    def create_content_metrics(self, content_id: str) -> str:
        """Initializes a metrics record for a content post with zero values."""
        metric_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO Social_Content_Metrics (metric_id, content_id)
            VALUES (?, ?)
            """, (metric_id, content_id))
            conn.commit()
        return metric_id

    def update_content_metrics(
        self,
        content_id: str,
        views: int = None,
        likes: int = None,
        comments: int = None,
        shares: int = None,
        saves: int = None,
        reach: int = None,
        impressions: int = None,
        avg_watch_pct: float = None,
        dm_triggers_fired: int = None,
        leads_generated: int = None,
        students_converted: int = None
    ) -> bool:
        """Updates metrics for a content post. Only non-None fields are updated."""
        updates = []
        params = []

        field_map = {
            "views": views, "likes": likes, "comments": comments,
            "shares": shares, "saves": saves, "reach": reach,
            "impressions": impressions, "avg_watch_pct": avg_watch_pct,
            "dm_triggers_fired": dm_triggers_fired,
            "leads_generated": leads_generated,
            "students_converted": students_converted
        }

        for field, value in field_map.items():
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)

        if not updates:
            return False

        updates.append("last_synced_at = ?")
        params.append(datetime.now().isoformat())
        params.append(content_id)

        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE Social_Content_Metrics SET {', '.join(updates)} WHERE content_id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_content_metrics(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves metrics for a specific content post."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM Social_Content_Metrics WHERE content_id = ?", (content_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_content_with_metrics(self) -> List[Dict[str, Any]]:
        """Retrieves all content posts JOINed with their metrics."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT p.*, m.views, m.likes, m.comments, m.shares, m.saves,
                   m.reach, m.impressions, m.avg_watch_pct, m.dm_triggers_fired,
                   m.leads_generated, m.students_converted, m.last_synced_at
            FROM Social_Content_Posts p
            LEFT JOIN Social_Content_Metrics m ON p.content_id = m.content_id
            ORDER BY p.posted_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # --- Social Comment Captures CRUD ---
    def create_comment_capture(
        self,
        content_id: str,
        platform: str,
        commenter_handle: str,
        commenter_platform_id: str,
        comment_text: str,
        keyword_matched: str = None
    ) -> str:
        """Creates a new comment capture record for the comment-to-lead pipeline."""
        capture_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO Social_Comment_Captures 
                (capture_id, content_id, platform, commenter_handle, commenter_platform_id, comment_text, keyword_matched)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (capture_id, content_id, platform, commenter_handle, commenter_platform_id, comment_text, keyword_matched))
            conn.commit()
        return capture_id

    def update_capture_status(
        self,
        capture_id: str,
        dm_sent: int = 0,
        dm_response_received: int = 0,
        converted_to_lead: int = 0,
        prospect_id: str = None,
        lead_id: str = None
    ) -> bool:
        """Updates the capture status after DM dispatch and lead creation."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
            UPDATE Social_Comment_Captures 
            SET dm_sent = ?, dm_response_received = ?, converted_to_lead = ?, prospect_id = ?, lead_id = ?
            WHERE capture_id = ?
            """, (dm_sent, dm_response_received, converted_to_lead, prospect_id, lead_id, capture_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_captures(self) -> List[Dict[str, Any]]:
        """Retrieves all comment capture records ordered by captured_at descending."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT c.*, p.title as content_title, p.platform as content_platform
            FROM Social_Comment_Captures c
            LEFT JOIN Social_Content_Posts p ON c.content_id = p.content_id
            ORDER BY c.captured_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_captures_by_content(self, content_id: str) -> List[Dict[str, Any]]:
        """Retrieves all comment captures for a specific content post."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT * FROM Social_Comment_Captures 
            WHERE content_id = ? 
            ORDER BY captured_at DESC
            """, (content_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_social_analytics(self) -> Dict[str, Any]:
        """Returns aggregated analytics across all tracked social content."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT 
                COUNT(DISTINCT p.content_id) as total_content,
                COALESCE(SUM(m.views), 0) as total_views,
                COALESCE(SUM(m.likes), 0) as total_likes,
                COALESCE(SUM(m.comments), 0) as total_comments,
                COALESCE(SUM(m.shares), 0) as total_shares,
                COALESCE(SUM(m.saves), 0) as total_saves,
                COALESCE(SUM(m.reach), 0) as total_reach,
                COALESCE(SUM(m.impressions), 0) as total_impressions,
                COALESCE(ROUND(AVG(m.avg_watch_pct), 1), 0) as avg_watch_pct,
                COALESCE(SUM(m.dm_triggers_fired), 0) as total_dm_triggers,
                COALESCE(SUM(m.leads_generated), 0) as total_leads_generated,
                COALESCE(SUM(m.students_converted), 0) as total_students_converted
            FROM Social_Content_Posts p
            LEFT JOIN Social_Content_Metrics m ON p.content_id = m.content_id
            """)
            totals = dict(cursor.fetchone())

            # Per-platform breakdown
            cursor2 = conn.execute("""
            SELECT p.platform,
                COUNT(p.content_id) as content_count,
                COALESCE(SUM(m.views), 0) as views,
                COALESCE(SUM(m.leads_generated), 0) as leads,
                COALESCE(SUM(m.students_converted), 0) as students
            FROM Social_Content_Posts p
            LEFT JOIN Social_Content_Metrics m ON p.content_id = m.content_id
            GROUP BY p.platform
            """)
            platform_breakdown = [dict(row) for row in cursor2.fetchall()]

            # Capture funnel stats
            cursor3 = conn.execute("""
            SELECT 
                COUNT(*) as total_captures,
                SUM(dm_sent) as dms_sent,
                SUM(dm_response_received) as dm_responses,
                SUM(converted_to_lead) as converted_to_leads
            FROM Social_Comment_Captures
            """)
            capture_stats = dict(cursor3.fetchone())

            return {
                "overview": totals,
                "platform_breakdown": platform_breakdown,
                "capture_funnel": capture_stats
            }

    def get_top_performing_content(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns top content sorted by leads_generated descending."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
            SELECT p.*, m.views, m.likes, m.comments, m.shares, m.saves,
                   m.reach, m.impressions, m.avg_watch_pct, m.dm_triggers_fired,
                   m.leads_generated, m.students_converted, m.last_synced_at
            FROM Social_Content_Posts p
            LEFT JOIN Social_Content_Metrics m ON p.content_id = m.content_id
            ORDER BY m.leads_generated DESC, m.views DESC
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

db_manager = RhythmDatabaseManager()
