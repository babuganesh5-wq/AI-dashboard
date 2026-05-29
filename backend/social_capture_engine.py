# backend/social_capture_engine.py
# Antigravity AI - Social Comment-to-Lead Capture Engine
# Scans social media comments for trigger keywords, processes captures,
# sends auto-DMs, and creates CRM prospects + Rhythm Academy leads

import uuid
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.db_manager import db_manager
from backend.social_insights_connector import (
    instagram_connector,
    facebook_connector,
    youtube_connector,
    _match_keyword,
    TRIGGER_KEYWORDS,
    SIMULATED_COMMENTERS,
    SIMULATED_COMMENTS_POOL,
)


# Auto-DM message template for comment capture follow-ups
AUTO_DM_TEMPLATE = (
    "Hey {name}! 🎵 Saw your interest in our music production content! "
    "We're running a special 6-month production program at Rhythm Academy. "
    "Want to schedule a free studio visit? Reply YES and we'll set it up!"
)


class SocialCaptureEngine:
    """
    End-to-end social comment capture pipeline.
    Detects trigger keywords → creates capture record → sends auto-DM →
    optionally creates CRM Prospect + Platform Identity + Rhythm Academy Lead →
    updates content metrics.
    """

    TRIGGER_KEYWORDS = TRIGGER_KEYWORDS

    def __init__(self):
        self.connectors = {
            "INSTAGRAM": instagram_connector,
            "FACEBOOK": facebook_connector,
            "YOUTUBE": youtube_connector,
        }

    def _get_connector(self, platform: str):
        """Returns the appropriate platform connector."""
        return self.connectors.get(platform.upper())

    async def scan_comments_for_triggers(self, content_id: str) -> List[Dict[str, Any]]:
        """
        Scans all comments on a piece of content for trigger keyword matches.
        Returns a list of comments that contain at least one trigger keyword.
        """
        content = db_manager.get_content_post(content_id)
        if not content:
            return []

        platform = content["platform"]
        connector = self._get_connector(platform)
        if not connector:
            return []

        # Fetch comments from the platform connector
        if platform == "INSTAGRAM":
            comments = await connector.fetch_reel_comments(content_id)
        elif platform == "FACEBOOK":
            comments = await connector.fetch_post_comments(content_id)
        elif platform == "YOUTUBE":
            comments = await connector.fetch_video_comments(content_id)
        else:
            comments = []

        # Filter to only trigger-matched comments
        trigger_comments = [c for c in comments if c.get("is_trigger")]
        return trigger_comments

    async def process_capture(
        self,
        content_id: str,
        commenter_handle: str,
        commenter_id: str,
        comment_text: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Full capture pipeline for an individual comment:
        1. Match keywords in comment text
        2. Create a Social_Comment_Captures record
        3. Send auto-DM via platform connector
        4. If DM is successful, create CRM_Prospect + Platform_Identity + Rhythm_Academy_Lead
        5. Update content metrics (dm_triggers_fired++, leads_generated++)
        6. Return the full capture result
        """
        # Step 1: Match keywords
        keyword = _match_keyword(comment_text)
        if not keyword:
            return {
                "status": "skipped",
                "reason": "No trigger keyword found in comment",
                "comment_text": comment_text
            }

        # Step 2: Create capture record
        capture_id = db_manager.create_comment_capture(
            content_id=content_id,
            platform=platform,
            commenter_handle=commenter_handle,
            commenter_platform_id=commenter_id,
            comment_text=comment_text,
            keyword_matched=keyword
        )

        # Step 3: Send auto-DM
        commenter_name = commenter_handle.replace("@", "").replace("_", " ").title()
        dm_message = AUTO_DM_TEMPLATE.format(name=commenter_name)

        dm_result = {}
        connector = self._get_connector(platform)
        if connector and platform in ("INSTAGRAM", "FACEBOOK"):
            if platform == "INSTAGRAM":
                dm_result = await connector.send_dm(commenter_id, dm_message)
            elif platform == "FACEBOOK":
                dm_result = await connector.send_messenger_message(commenter_id, dm_message)
        elif platform == "YOUTUBE":
            # YouTube doesn't support DMs — log for WhatsApp follow-up
            print(f"[YT_CAPTURE] YouTube DM not supported. Queuing {commenter_handle} for WhatsApp follow-up.")
            dm_result = {
                "status": "queued_whatsapp",
                "message": "YouTube does not support DMs. Queued for WhatsApp follow-up.",
                "simulated": True
            }

        dm_sent = 1 if dm_result.get("status") in ("success", "queued_whatsapp") else 0

        # Step 4: Create CRM entities if DM was successful
        prospect_id = None
        lead_id = None

        if dm_sent:
            # Generate simulated contact details from handle
            names = commenter_name.split(" ", 1)
            first_name = names[0] if names else "Social"
            last_name = names[1] if len(names) > 1 else "Lead"
            email = f"{commenter_handle.replace('@', '').lower()}@social-lead.com"
            phone = f"91{random.randint(7000000000, 9999999999)}"

            try:
                prospect_id = db_manager.create_prospect(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    funnel_stage="INQUIRY"
                )

                # Register platform identity
                db_manager.register_platform_identity(
                    prospect_id=prospect_id,
                    platform_name=platform,
                    external_id=commenter_id,
                    handle_name=commenter_handle
                )

                # Create Rhythm Academy lead
                lead_id = db_manager.create_lead(
                    prospect_id=prospect_id,
                    student_name=commenter_name,
                    whatsapp_number=phone,
                    target_program="6M_PRODUCTION",
                    source=f"SOCIAL_{platform}"
                )

                # Record split installments (₹15,000 + ₹15,000) inside ledger
                db_manager.record_installment(lead_id=lead_id, installment_number=1, amount=15000.00, due_days=1)
                db_manager.record_installment(lead_id=lead_id, installment_number=2, amount=15000.00, due_days=30)
            except Exception as e:
                print(f"[CAPTURE_ENGINE] CRM creation warning: {e}")

        # Step 5: Update capture status and content metrics
        db_manager.update_capture_status(
            capture_id=capture_id,
            dm_sent=dm_sent,
            dm_response_received=0,
            converted_to_lead=1 if lead_id else 0,
            prospect_id=prospect_id,
            lead_id=lead_id
        )

        # Increment content metrics
        metrics = db_manager.get_content_metrics(content_id)
        if metrics:
            current_dm_triggers = metrics.get("dm_triggers_fired", 0) + 1
            current_leads = metrics.get("leads_generated", 0) + (1 if lead_id else 0)
            db_manager.update_content_metrics(
                content_id=content_id,
                dm_triggers_fired=current_dm_triggers,
                leads_generated=current_leads
            )

        # Step 6: Return full capture result
        return {
            "status": "captured",
            "capture_id": capture_id,
            "keyword_matched": keyword,
            "dm_sent": bool(dm_sent),
            "dm_result": dm_result,
            "prospect_id": prospect_id,
            "lead_id": lead_id,
            "converted_to_lead": lead_id is not None,
            "platform": platform,
            "commenter_handle": commenter_handle,
            "comment_text": comment_text,
            "captured_at": datetime.now().isoformat()
        }

    async def simulate_social_capture(
        self,
        content_id: str,
        commenter_name: str = "@music_fan_99",
        comment_text: str = "I want to ENROLL in this course!",
        platform: str = "INSTAGRAM"
    ) -> Dict[str, Any]:
        """
        Demo simulation of the full comment-to-lead capture flow.
        Uses provided or randomized data to demonstrate the pipeline.
        """
        # Generate a simulated commenter ID
        commenter_id = f"{platform.lower()}_user_{uuid.uuid4().hex[:8]}"

        result = await self.process_capture(
            content_id=content_id,
            commenter_handle=commenter_name,
            commenter_id=commenter_id,
            comment_text=comment_text,
            platform=platform.upper()
        )

        result["simulation"] = True
        return result

    async def sync_content_metrics(self, content_id: str) -> Dict[str, Any]:
        """
        Pulls latest metrics from the appropriate platform connector
        and updates the database.
        """
        content = db_manager.get_content_post(content_id)
        if not content:
            return {"status": "error", "message": "Content not found"}

        platform = content["platform"]
        connector = self._get_connector(platform)
        if not connector:
            return {"status": "error", "message": f"No connector for platform: {platform}"}

        # Fetch metrics from platform
        if platform == "INSTAGRAM":
            metrics = await connector.fetch_reel_metrics(content_id)
        elif platform == "FACEBOOK":
            metrics = await connector.fetch_post_metrics(content_id)
        elif platform == "YOUTUBE":
            metrics = await connector.fetch_video_metrics(content_id)
        else:
            return {"status": "error", "message": f"Unsupported platform: {platform}"}

        # Ensure metrics record exists
        existing = db_manager.get_content_metrics(content_id)
        if not existing:
            db_manager.create_content_metrics(content_id)

        # Update with fresh data from the platform
        db_manager.update_content_metrics(
            content_id=content_id,
            views=metrics.get("views", 0),
            likes=metrics.get("likes", 0),
            comments=metrics.get("comments", 0),
            shares=metrics.get("shares", 0),
            saves=metrics.get("saves", 0),
            reach=metrics.get("reach", 0),
            impressions=metrics.get("impressions", 0),
            avg_watch_pct=metrics.get("avg_watch_pct", 0.0)
        )

        return {
            "status": "success",
            "content_id": content_id,
            "platform": platform,
            "metrics_synced": metrics,
            "synced_at": datetime.now().isoformat()
        }

    def get_aggregated_analytics(self) -> Dict[str, Any]:
        """
        Returns aggregated analytics across all tracked social content.
        Total views, comments, DMs sent, leads generated, students converted.
        """
        return db_manager.get_social_analytics()

    def get_top_performers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Returns the top performing content sorted by leads generated.
        """
        return db_manager.get_top_performing_content(limit=limit)


# Module-level engine instance
social_capture_engine = SocialCaptureEngine()
