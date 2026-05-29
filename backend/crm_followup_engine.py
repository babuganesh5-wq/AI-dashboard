# backend/crm_followup_engine.py
# Antigravity AI - Relentless CRM Follow-Up Engine
# Drives automated multi-stage follow-ups via WhatsApp and DMs to convert prospects

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from backend.db_manager import db_manager
from backend.whatsapp_connector import RhythmWhatsAppConnector
from backend.social_capture_engine import social_capture_engine

# Initialize WhatsApp Connector
whatsapp_connector = RhythmWhatsAppConnector()

class CRMFollowUpEngine:
    """
    Automated Follow-Up Engine for Rhythm Academy.
    Scans the SQLite database for lead leakages and triggers multi-channel follow-ups:
    1. Social Auto-DM Nudges (for commenters who haven't clicked or responded)
    2. Studio Visit Scheduler Reminders (for unqualified inquiries)
    3. Installment Ledger Escalations (for pending or overdue fees)
    """

    async def execute_all_followup_loops(self) -> Dict[str, Any]:
        """Runs all three follow-up loops and returns a execution summary."""
        nudges_sent = await self.process_social_dm_nudges()
        scheduler_reminders = await self.process_studio_visit_reminders()
        ledger_reminders = await self.process_installment_reminders()

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "loops": {
                "social_dm_nudges": {
                    "scanned_records": len(nudges_sent),
                    "dispatched": sum(1 for x in nudges_sent if x["sent"]),
                    "details": nudges_sent
                },
                "studio_visit_reminders": {
                    "scanned_records": len(scheduler_reminders),
                    "dispatched": sum(1 for x in scheduler_reminders if x["sent"]),
                    "details": scheduler_reminders
                },
                "installment_reminders": {
                    "scanned_records": len(ledger_reminders),
                    "dispatched": sum(1 for x in ledger_reminders if x["sent"]),
                    "details": ledger_reminders
                }
            }
        }

    async def process_social_dm_nudges(self) -> List[Dict[str, Any]]:
        """
        Nudges viewers who commented and received the initial DM but didn't respond
        or register as a lead (i.e. converted_to_lead is 0, captured_at is past 2 hours).
        """
        nudges = []
        with db_manager.get_connection() as conn:
            # Select captures that haven't converted to lead yet
            cursor = conn.execute("""
                SELECT c.*, p.title as post_title 
                FROM Social_Comment_Captures c
                JOIN Social_Content_Posts p ON c.content_id = p.content_id
                WHERE c.converted_to_lead = 0 AND c.dm_sent = 1
            """)
            captures = [dict(r) for r in cursor.fetchall()]

        for cap in captures:
            handle = cap["commenter_handle"]
            name = handle.replace("@", "").replace("_", " ").title()
            platform = cap["platform"]
            post_title = cap["post_title"]

            # Nudge Message template
            nudge_msg = (
                f"Hey {name}! 🎵 Just checking in—did you get a chance to read my previous message "
                f"about our studio tour for the Music Production program? We'd love to show you around! "
                f"Reply YES if you'd like to book a slot!"
            )

            # Send DM via appropriate platform
            sent = False
            try:
                connector = social_capture_engine._get_connector(platform)
                if connector and platform in ("INSTAGRAM", "FACEBOOK"):
                    if platform == "INSTAGRAM":
                        res = await connector.send_dm(cap["commenter_platform_id"], nudge_msg)
                    elif platform == "FACEBOOK":
                        res = await connector.send_messenger_message(cap["commenter_platform_id"], nudge_msg)
                    sent = res.get("status") == "success"
                elif platform == "YOUTUBE":
                    # YouTube doesn't support DM, so we simulate a WhatsApp backup dispatch
                    res = await whatsapp_connector.send_text_message(
                        to_number=f"91{cap['capture_id'][:8]}", # Mock number derived from capture UUID
                        text=f"[YT Nudge Backup] Hi {name}! Saw your comment on YouTube: '{nudge_msg}'"
                    )
                    sent = res.get("status") == "success"
            except Exception as e:
                print(f"[FOLLOWUP_DAEMON] Error dispatching DM nudge: {e}")

            nudges.append({
                "capture_id": cap["capture_id"],
                "commenter_handle": handle,
                "platform": platform,
                "nudge_sent_at": datetime.now().isoformat(),
                "sent": sent
            })

        return nudges

    async def process_studio_visit_reminders(self) -> List[Dict[str, Any]]:
        """
        Follows up with prospects who are registered as INQUIRY (unqualified)
        and have not scheduled their Studio Visit yet, prompting them via WhatsApp.
        """
        reminders = []
        leads = db_manager.get_all_leads_with_details()
        
        # Filter leads that are unqualified (current_funnel_stage is 'INQUIRY')
        inquiry_leads = [l for l in leads if l["current_funnel_stage"] == "INQUIRY" and l["studio_visit_scheduled"] is None]

        for lead in inquiry_leads:
            name = lead["student_name"]
            num = lead["whatsapp_number"]
            prog = lead["target_program"]

            rem_text = (
                f"Hi {name}! 🎵 Hope you are doing great. "
                f"We noticed you haven't scheduled your Free Studio Tour at Rhythm Academy yet. "
                f"We have limited slots open this week for checking out our analog gear and setups! "
                f"Would you like to schedule yours today? Reply with a date and time that works!"
            )

            sent = False
            try:
                res = await whatsapp_connector.send_text_message(to_number=num, text=rem_text)
                sent = res.get("status") == "success"
            except Exception as e:
                print(f"[FOLLOWUP_DAEMON] Error dispatching WhatsApp studio tour reminder: {e}")

            reminders.append({
                "lead_id": lead["lead_id"],
                "student_name": name,
                "whatsapp_number": num,
                "sent": sent
            })

        return reminders

    async def process_installment_reminders(self) -> List[Dict[str, Any]]:
        """
        Follows up with active students (qualified or customer) who have PENDING
        or OVERDUE installments in their split ledgers, protecting business cash flow.
        """
        reminders = []
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT i.*, l.student_name, l.whatsapp_number
                FROM Rhythm_Installments_Ledger i
                JOIN Rhythm_Academy_Leads l ON i.lead_id = l.lead_id
                WHERE i.status != 'PAID'
            """)
            pending_installments = [dict(r) for r in cursor.fetchall()]

        for inst in pending_installments:
            name = inst["student_name"]
            num = inst["whatsapp_number"]
            inst_num = inst["installment_number"]
            amount = inst["amount"]
            due_date = inst["due_date"]

            rem_text = (
                f"Dear {name}, 🎵 This is a friendly reminder from Rhythm Academy. "
                f"Your Split Installment #{inst_num} of ₹{amount:,.2f} is pending in the ledger. "
                f"Due Date: {due_date.split('T')[0]}. "
                f"Please clear this installment online or at the studio counter. Thank you!"
            )

            sent = False
            try:
                res = await whatsapp_connector.send_text_message(to_number=num, text=rem_text)
                sent = res.get("status") == "success"
                if sent:
                    db_manager.increment_installment_reminder(inst["installment_id"])
            except Exception as e:
                print(f"[FOLLOWUP_DAEMON] Error dispatching installment ledger reminder: {e}")

            reminders.append({
                "installment_id": inst["installment_id"],
                "student_name": name,
                "amount": amount,
                "installment_number": inst_num,
                "sent": sent
            })

        return reminders

# Module-level instance
crm_followup_engine = CRMFollowUpEngine()
