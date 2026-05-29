# app/ingest/ingest_router.py
# Antigravity AI High-Throughput Comment-to-DM Ingest Router
# Extracts Instagram/YouTube comments triggers, normalizes payloads, and routes triggers to Redis

import hmac
import hashlib
import json
import redis.asyncio as aioredis
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1")

class Settings:
    REDIS_URL: str = "redis://localhost:6379/0"
    META_APP_SECRET: str = "meta_app_secret_credential_hash"
    
settings = Settings()
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

class InboundSocialEvent(BaseModel):
    platform: str = Field(..., description="Platform trigger: INSTAGRAM_COMMENT, YOUTUBE_REPLY, WHATSAPP, TELEGRAM")
    sender_platform_id: str = Field(..., description="External handle ID / chat room identifier")
    text_content: str = Field(..., description="Raw text / comment body")
    keyword_matched: Optional[str] = Field(None, description="Highed-intent keyword matched: e.g. GROWTH, LEAD, SCALE")
    attribution_click_id: Optional[str] = Field(None, description="gclid or fbclid parameters")

@router.post("/webhooks/meta")
async def handle_meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None)
):
    """
    Unified ingestion for Instagram & Facebook comments and messages
    """
    raw_body = await request.body()
    
    # Cryptographic signature validation
    if not verify_meta_signature(raw_body, x_hub_signature_256, settings.META_APP_SECRET):
        raise HTTPException(status_code=403, detail="Invalid hub signature.")

    payload = json.loads(raw_body.decode('utf-8'))
    background_tasks.add_task(enqueue_social_event, "META", payload)
    return {"status": "accepted", "code": 200}

@router.post("/webhooks/youtube")
async def handle_youtube_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Ingests YouTube comments webhooks
    """
    raw_body = await request.body()
    background_tasks.add_task(enqueue_social_event, "YOUTUBE", {"xml_content": raw_body.decode('utf-8')})
    return {"status": "ok"}

def verify_meta_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature:
        return False
    sha256_hash = signature.replace("sha256=", "")
    expected_sign = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sha256_hash, expected_sign)

async def enqueue_social_event(platform: str, payload: dict):
    normalized = normalize_payload(platform, payload)
    if normalized:
        # Publish event to the Redis queue which wakes downstream SMM & Content agents
        await redis_client.publish("social_events_stream", normalized.json())

def normalize_payload(platform: str, payload: dict) -> Optional[InboundSocialEvent]:
    try:
        if platform == "META":
            # Extract Meta comment or DM webhooks details
            entry = payload.get("entry", [])[0]
            changes = entry.get("changes", [])
            if changes:
                value = changes[0].get("value", {})
                
                # Check if it is a comment hook
                if "comment_id" in value:
                    text = value.get("text", "")
                    sender = value.get("from", {}).get("id", "")
                    
                    # Match high-engagement trigger keywords
                    matched_keyword = None
                    text_upper = text.upper()
                    for keyword in ["GROWTH", "LEAD", "SCALE"]:
                        if keyword in text_upper:
                            matched_keyword = keyword
                            break
                            
                    click_id = value.get("metadata", {}).get("fbclid", None)
                    return InboundSocialEvent(
                        platform="INSTAGRAM_COMMENT",
                        sender_platform_id=sender,
                        text_content=text,
                        keyword_matched=matched_keyword,
                        attribution_click_id=click_id
                    )
                    click_id = value.get("metadata", {}).get("fbclid", None)
                    return InboundSocialEvent(
                        platform="INSTAGRAM_COMMENT",
                        sender_platform_id=sender,
                        text_content=text,
                        keyword_matched=matched_keyword,
                        attribution_click_id=click_id
                    )
        elif platform == "YOUTUBE":
            # Parsing PubSubHubbub subscription tags
            pass
    except Exception:
        pass
    return None

# --- NEW Rhythm Academy CRM & Live Telemetry APIs ---

@router.get("/leads")
async def get_all_leads():
    """Retrieves all Rhythm Academy leads, installments, and program statuses from SQL."""
    from backend.db_manager import db_manager
    try:
        leads = db_manager.get_all_leads_with_details()
        # For each lead, append its installments from the ledger
        with db_manager.get_connection() as conn:
            for lead in leads:
                cursor = conn.execute(
                    "SELECT installment_id, installment_number, amount, status, due_date, reminder_sent_count FROM Rhythm_Installments_Ledger WHERE lead_id = ? ORDER BY installment_number",
                    (lead["lead_id"],)
                )
                lead["installments"] = [dict(row) for row in cursor.fetchall()]
        return {"status": "success", "leads": leads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/simulate")
async def simulate_inbound_lead(
    name: str = "Tushar Dev", 
    whatsapp: str = "919988776655", 
    text: str = "I want to enroll in the music PRODUCTION course!",
    fbclid: str = "fb_click_id_99999"
):
    """
    Simulates an inbound ad click / WhatsApp message.
    Executes the entire multi-agent LangGraph workflow.
    """
    from backend.workflow import AgentWorkflowState
    try:
        workflow = AgentWorkflowState()
        event = InboundSocialEvent(
            platform="WHATSAPP",
            sender_platform_id=whatsapp,
            text_content=text,
            attribution_click_id=fbclid
        )
        
        initial_state = {
            "event": event,
            "sender_name": name
        }
        
        final_state = await workflow.runtime.ainvoke(initial_state)
        
        # Pull latest details for return
        from backend.db_manager import db_manager
        prospect = db_manager.get_prospect_by_identity("WHATSAPP", whatsapp)
        
        return {
            "status": "success",
            "message": "Full LangGraph pipeline executed successfully.",
            "workflow_milestone": final_state.get("milestone"),
            "capi_value_lift": final_state.get("value_lift_metrics", {}).get("value_lifted"),
            "prospect_id": prospect["prospect_id"] if prospect else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/installments/{number}/pay")
async def pay_split_installment(lead_id: str, number: int):
    """Processes split installment payments, promoting student profiles to CUSTOMER."""
    from backend.db_manager import db_manager
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT installment_id FROM Rhythm_Installments_Ledger WHERE lead_id = ? AND installment_number = ?",
            (lead_id, number)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Installment record not found.")
        
        db_manager.update_installment_status(row["installment_id"], "PAID")
        return {"status": "success", "message": f"Installment #{number} paid successfully."}

@router.post("/leads/{lead_id}/remind")
async def send_whatsapp_installment_reminder(lead_id: str):
    """Outbounds automated WhatsApp split fee recovery warnings and logs reminders counts."""
    from backend.db_manager import db_manager
    from backend.workflow import RhythmWhatsAppClient
    
    lead = db_manager.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")
        
    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT installment_id, amount FROM Rhythm_Installments_Ledger WHERE lead_id = ? AND status != 'PAID'",
            (lead_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        if not rows:
            return {"status": "success", "message": "No pending installments found."}
            
        # Send WhatsApp alert for the first pending installment
        target = rows[0]
        await RhythmWhatsAppClient.send_installment_escalation(
            whatsapp_number=lead["whatsapp_number"],
            student_id=lead["prospect_id"],
            balance=target["amount"]
        )
        
        db_manager.increment_installment_reminder(target["installment_id"])
        return {"status": "success", "message": f"Reminder dispatched for ₹{target['amount']} balance."}

# --- Social Media Insights & Capture Endpoints ---

@router.get("/social/content")
async def get_social_content():
    """Returns all tracked social content posts with their engagement metrics."""
    from backend.db_manager import db_manager
    try:
        content = db_manager.get_all_content_with_metrics()
        return {"status": "success", "content": content, "total": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social/content")
async def register_social_content(
    platform: str = "INSTAGRAM",
    content_type: str = "REEL",
    title: str = "New Social Content",
    caption: str = "",
    post_url: str = "",
    media_url: str = ""
):
    """Registers a new social content post for tracking and metric collection."""
    from backend.db_manager import db_manager
    try:
        valid_platforms = ("INSTAGRAM", "FACEBOOK", "YOUTUBE")
        valid_types = ("REEL", "STORY", "POST", "SHORT", "VIDEO")

        if platform.upper() not in valid_platforms:
            raise HTTPException(status_code=400, detail=f"Invalid platform. Must be one of: {valid_platforms}")
        if content_type.upper() not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid content_type. Must be one of: {valid_types}")

        content_id = db_manager.create_content_post(
            platform=platform,
            content_type=content_type,
            title=title,
            caption=caption,
            post_url=post_url,
            media_url=media_url
        )
        return {
            "status": "success",
            "content_id": content_id,
            "message": f"Content registered on {platform.upper()} as {content_type.upper()}."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social/content/{content_id}/metrics")
async def get_content_metrics(content_id: str):
    """Returns detailed engagement metrics for a specific piece of content."""
    from backend.db_manager import db_manager
    try:
        post = db_manager.get_content_post(content_id)
        if not post:
            raise HTTPException(status_code=404, detail="Content not found.")

        metrics = db_manager.get_content_metrics(content_id)
        captures = db_manager.get_captures_by_content(content_id)

        return {
            "status": "success",
            "content": post,
            "metrics": metrics,
            "captures": captures,
            "captures_count": len(captures)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social/content/{content_id}/sync")
async def sync_content_metrics(content_id: str):
    """Force-refreshes engagement metrics from the platform API (simulation mode)."""
    from backend.social_capture_engine import social_capture_engine
    try:
        result = await social_capture_engine.sync_content_metrics(content_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message", "Sync failed."))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social/captures")
async def get_social_captures():
    """Returns all comment-to-lead captures across all tracked content."""
    from backend.db_manager import db_manager
    try:
        captures = db_manager.get_all_captures()
        return {"status": "success", "captures": captures, "total": len(captures)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social/captures/simulate")
async def simulate_social_capture(
    content_id: str = "",
    commenter: str = "@music_fan_99",
    text: str = "I want to ENROLL in this course!",
    platform: str = "INSTAGRAM"
):
    """
    Simulates the full comment-to-lead capture pipeline.
    If no content_id is provided, uses the first available content post.
    """
    from backend.db_manager import db_manager
    from backend.social_capture_engine import social_capture_engine
    try:
        # If no content_id provided, use the first available
        if not content_id:
            all_content = db_manager.get_all_content_posts()
            if not all_content:
                raise HTTPException(
                    status_code=404,
                    detail="No content posts found. Register content first via POST /social/content."
                )
            content_id = all_content[0]["content_id"]

        result = await social_capture_engine.simulate_social_capture(
            content_id=content_id,
            commenter_name=commenter,
            comment_text=text,
            platform=platform
        )
        return {"status": "success", "capture_result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social/analytics")
async def get_social_analytics():
    """Returns aggregated social funnel analytics across all platforms and content."""
    from backend.social_capture_engine import social_capture_engine
    try:
        analytics = social_capture_engine.get_aggregated_analytics()
        return {"status": "success", "analytics": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social/top-performers")
async def get_top_performers(limit: int = 10):
    """Returns the top-performing content sorted by lead conversions."""
    from backend.social_capture_engine import social_capture_engine
    try:
        top = social_capture_engine.get_top_performers(limit=limit)
        return {"status": "success", "top_performers": top, "total": len(top)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
