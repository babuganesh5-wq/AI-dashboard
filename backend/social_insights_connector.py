# backend/social_insights_connector.py
# Antigravity AI - Social Media Platform Insights Connectors
# Provides Instagram, Facebook, and YouTube API integrations with simulation mode
# Returns realistic mock data for demo/development environments

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Trigger keywords used across all platform connectors for comment matching
TRIGGER_KEYWORDS = [
    "GROWTH", "LEAD", "SCALE", "MUSIC", "ENROLL",
    "COURSE", "PRODUCTION", "RHYTHM", "DIPLOMA", "JOIN"
]

# Realistic commenter profiles for simulation mode
SIMULATED_COMMENTERS = [
    {"handle": "@music_fan_99", "platform_id": "ig_user_100001", "name": "Aarav Sharma"},
    {"handle": "@beat_maker_pro", "platform_id": "ig_user_100002", "name": "Priya Nair"},
    {"handle": "@dj_aspirant_22", "platform_id": "ig_user_100003", "name": "Rahul Verma"},
    {"handle": "@sound_designer_x", "platform_id": "ig_user_100004", "name": "Sneha Patel"},
    {"handle": "@indie_producer_01", "platform_id": "ig_user_100005", "name": "Karthik Iyer"},
    {"handle": "@studio_dreamer", "platform_id": "ig_user_100006", "name": "Meera Joshi"},
    {"handle": "@future_dj_star", "platform_id": "ig_user_100007", "name": "Arjun Reddy"},
    {"handle": "@rhythm_lover_88", "platform_id": "ig_user_100008", "name": "Deepika Rao"},
    {"handle": "@ableton_kid", "platform_id": "ig_user_100009", "name": "Varun Kumar"},
    {"handle": "@vocal_queen_in", "platform_id": "ig_user_100010", "name": "Ananya Gupta"},
]

# Simulated comment templates — some contain trigger keywords, some don't
SIMULATED_COMMENTS_POOL = [
    "This is amazing! How do I ENROLL in your COURSE? 🎵",
    "Can I JOIN the next batch for MUSIC PRODUCTION?",
    "I want to SCALE my career in audio! Where do I sign up?",
    "Awesome track PRODUCTION quality! 🔥",
    "Tell me about the DIPLOMA program at RHYTHM Academy!",
    "GROWTH in the music industry starts here! Love this content!",
    "How much is the COURSE fee?",
    "I'm interested in the MUSIC school! Any LEAD form?",
    "Great video, keep it up! 👏",
    "Nice beats bro 🎧",
    "Love the visuals in this reel 😍",
    "Can someone share the link to ENROLL?",
    "I want to learn PRODUCTION from scratch!",
    "RHYTHM Academy is the best! Already a student 🙌",
    "How do I JOIN the online batch?",
    "Looking for GROWTH opportunities in EDM production",
    "What a great tutorial!",
    "This reel is fire 🔥🔥🔥",
    "Can I get a LEAD magnet for the free workshop?",
    "I want to SCALE my beats to the next level!",
]


def _match_keyword(text: str) -> Optional[str]:
    """Checks comment text against trigger keywords and returns the first match."""
    text_upper = text.upper()
    for keyword in TRIGGER_KEYWORDS:
        if keyword in text_upper:
            return keyword
    return None


class InstagramInsightsConnector:
    """
    Instagram Graph API connector with full simulation mode.
    Fetches reel/post metrics, comments, and sends auto-DMs.
    """

    def __init__(self, access_token: str = None):
        self.access_token = access_token or "simulated_ig_token_credential"
        self.is_simulated = (access_token is None or "simulated" in self.access_token)
        self.api_base = "https://graph.facebook.com/v18.0"

    async def fetch_reel_metrics(self, reel_id: str) -> Dict[str, Any]:
        """
        Fetches engagement metrics for an Instagram Reel.
        In simulation mode, returns realistic randomized metrics.
        """
        if self.is_simulated:
            views = random.randint(8000, 250000)
            likes = int(views * random.uniform(0.03, 0.12))
            comments = int(views * random.uniform(0.005, 0.025))
            shares = int(views * random.uniform(0.008, 0.04))
            saves = int(views * random.uniform(0.01, 0.05))
            reach = int(views * random.uniform(0.7, 0.95))
            impressions = int(views * random.uniform(1.1, 1.8))
            avg_watch_pct = round(random.uniform(35.0, 85.0), 1)

            return {
                "reel_id": reel_id,
                "platform": "INSTAGRAM",
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "reach": reach,
                "impressions": impressions,
                "avg_watch_pct": avg_watch_pct,
                "simulated": True,
                "synced_at": datetime.now().isoformat()
            }

        # Production API call (placeholder)
        # response = await httpx.AsyncClient().get(f"{self.api_base}/{reel_id}/insights", ...)
        return {"error": "Production API not configured", "reel_id": reel_id}

    async def fetch_reel_comments(self, reel_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches comments on an Instagram Reel with keyword matching.
        In simulation mode, returns a realistic set of randomized comments.
        """
        if self.is_simulated:
            num_comments = random.randint(5, min(limit, 15))
            comments = []
            used_commenters = random.sample(
                SIMULATED_COMMENTERS,
                min(num_comments, len(SIMULATED_COMMENTERS))
            )

            for i, commenter in enumerate(used_commenters):
                comment_text = random.choice(SIMULATED_COMMENTS_POOL)
                keyword = _match_keyword(comment_text)
                posted_minutes_ago = random.randint(5, 1440)

                comments.append({
                    "comment_id": f"ig_comment_{uuid.uuid4().hex[:8]}",
                    "reel_id": reel_id,
                    "commenter_handle": commenter["handle"],
                    "commenter_platform_id": commenter["platform_id"],
                    "commenter_name": commenter["name"],
                    "text": comment_text,
                    "keyword_matched": keyword,
                    "is_trigger": keyword is not None,
                    "posted_at": (datetime.now() - timedelta(minutes=posted_minutes_ago)).isoformat(),
                    "simulated": True
                })

            return comments

        return []

    async def send_dm(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a Direct Message to an Instagram user via the Messenger API.
        In simulation mode, logs the DM and returns a success response.
        """
        if self.is_simulated:
            print(f"[IG_DM_SIMULATOR] DM to {user_id}: {message[:80]}...")
            return {
                "status": "success",
                "message_id": f"ig_dm_{uuid.uuid4().hex[:8]}",
                "recipient": user_id,
                "simulated": True,
                "delivered_at": datetime.now().isoformat()
            }

        return {"error": "Production API not configured"}


class FacebookInsightsConnector:
    """
    Facebook Graph API connector with full simulation mode.
    Fetches post metrics, comments, and sends Messenger messages.
    """

    def __init__(self, access_token: str = None, page_id: str = None):
        self.access_token = access_token or "simulated_fb_token_credential"
        self.page_id = page_id or "simulated_page_id"
        self.is_simulated = (access_token is None or "simulated" in self.access_token)
        self.api_base = "https://graph.facebook.com/v18.0"

    async def fetch_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """
        Fetches engagement metrics for a Facebook post.
        In simulation mode, returns realistic randomized metrics.
        """
        if self.is_simulated:
            views = random.randint(3000, 120000)
            likes = int(views * random.uniform(0.02, 0.08))
            comments = int(views * random.uniform(0.003, 0.015))
            shares = int(views * random.uniform(0.01, 0.06))
            saves = int(views * random.uniform(0.005, 0.02))
            reach = int(views * random.uniform(0.6, 0.9))
            impressions = int(views * random.uniform(1.0, 1.5))
            avg_watch_pct = round(random.uniform(20.0, 65.0), 1)

            return {
                "post_id": post_id,
                "platform": "FACEBOOK",
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "reach": reach,
                "impressions": impressions,
                "avg_watch_pct": avg_watch_pct,
                "simulated": True,
                "synced_at": datetime.now().isoformat()
            }

        return {"error": "Production API not configured", "post_id": post_id}

    async def fetch_post_comments(self, post_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches comments on a Facebook post with keyword matching.
        In simulation mode, returns a realistic set of randomized comments.
        """
        if self.is_simulated:
            num_comments = random.randint(3, min(limit, 10))
            comments = []
            used_commenters = random.sample(
                SIMULATED_COMMENTERS,
                min(num_comments, len(SIMULATED_COMMENTERS))
            )

            for commenter in used_commenters:
                comment_text = random.choice(SIMULATED_COMMENTS_POOL)
                keyword = _match_keyword(comment_text)
                posted_minutes_ago = random.randint(10, 2880)

                comments.append({
                    "comment_id": f"fb_comment_{uuid.uuid4().hex[:8]}",
                    "post_id": post_id,
                    "commenter_handle": commenter["handle"],
                    "commenter_platform_id": commenter["platform_id"],
                    "commenter_name": commenter["name"],
                    "text": comment_text,
                    "keyword_matched": keyword,
                    "is_trigger": keyword is not None,
                    "posted_at": (datetime.now() - timedelta(minutes=posted_minutes_ago)).isoformat(),
                    "simulated": True
                })

            return comments

        return []

    async def send_messenger_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a Messenger message to a Facebook user.
        In simulation mode, logs the message and returns a success response.
        """
        if self.is_simulated:
            print(f"[FB_MESSENGER_SIMULATOR] Message to {user_id}: {message[:80]}...")
            return {
                "status": "success",
                "message_id": f"fb_msg_{uuid.uuid4().hex[:8]}",
                "recipient": user_id,
                "simulated": True,
                "delivered_at": datetime.now().isoformat()
            }

        return {"error": "Production API not configured"}


class YouTubeInsightsConnector:
    """
    YouTube Data API v3 connector with full simulation mode.
    Fetches video/short metrics and comments.
    YouTube does not support DMs — redirects to WhatsApp for follow-up.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "simulated_yt_api_key"
        self.is_simulated = (api_key is None or "simulated" in self.api_key)
        self.api_base = "https://www.googleapis.com/youtube/v3"

    async def fetch_video_metrics(self, video_id: str) -> Dict[str, Any]:
        """
        Fetches engagement metrics for a YouTube video or Short.
        In simulation mode, returns realistic randomized metrics.
        """
        if self.is_simulated:
            views = random.randint(5000, 500000)
            likes = int(views * random.uniform(0.02, 0.10))
            comments = int(views * random.uniform(0.002, 0.01))
            shares = int(views * random.uniform(0.005, 0.03))
            saves = int(views * random.uniform(0.003, 0.015))
            reach = int(views * random.uniform(0.5, 0.85))
            impressions = int(views * random.uniform(1.2, 2.5))
            avg_watch_pct = round(random.uniform(25.0, 75.0), 1)

            return {
                "video_id": video_id,
                "platform": "YOUTUBE",
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "reach": reach,
                "impressions": impressions,
                "avg_watch_pct": avg_watch_pct,
                "simulated": True,
                "synced_at": datetime.now().isoformat()
            }

        return {"error": "Production API not configured", "video_id": video_id}

    async def fetch_video_comments(self, video_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches comments on a YouTube video with keyword matching.
        In simulation mode, returns a realistic set of randomized comments.
        """
        if self.is_simulated:
            num_comments = random.randint(4, min(limit, 12))
            comments = []
            used_commenters = random.sample(
                SIMULATED_COMMENTERS,
                min(num_comments, len(SIMULATED_COMMENTERS))
            )

            for commenter in used_commenters:
                comment_text = random.choice(SIMULATED_COMMENTS_POOL)
                keyword = _match_keyword(comment_text)
                posted_minutes_ago = random.randint(15, 4320)

                comments.append({
                    "comment_id": f"yt_comment_{uuid.uuid4().hex[:8]}",
                    "video_id": video_id,
                    "commenter_handle": commenter["handle"],
                    "commenter_platform_id": commenter["platform_id"],
                    "commenter_name": commenter["name"],
                    "text": comment_text,
                    "keyword_matched": keyword,
                    "is_trigger": keyword is not None,
                    "posted_at": (datetime.now() - timedelta(minutes=posted_minutes_ago)).isoformat(),
                    "simulated": True
                })

            return comments

        return []


# Module-level connector instances (simulation mode by default)
instagram_connector = InstagramInsightsConnector()
facebook_connector = FacebookInsightsConnector()
youtube_connector = YouTubeInsightsConnector()
