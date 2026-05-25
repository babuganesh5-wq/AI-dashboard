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
        elif platform == "YOUTUBE":
            # Parsing PubSubHubbub subscription tags
            pass
    except Exception:
        pass
    return None
