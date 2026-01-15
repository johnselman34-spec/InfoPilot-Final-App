"""
InfoPilot Explorer - Web Push Notifications Service
Implements VAPID-based push notifications
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from pywebpush import webpush, WebPushException
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/push", tags=["push"])

# Database will be injected
db = None

# VAPID keys - loaded from environment variables
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "jjspilot24@gmail.com")
VAPID_CLAIMS = {"sub": f"mailto:{VAPID_CLAIMS_EMAIL}"}

def init_router(database):
    global db
    db = database
    return router

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # p256dh and auth keys

class PushMessage(BaseModel):
    title: str
    body: str
    icon: Optional[str] = "/logo192.png"
    badge: Optional[str] = "/logo192.png"
    url: Optional[str] = "/"
    user_ids: Optional[list] = None  # If None, send to all subscribers

@router.get("/vapid-key")
async def get_vapid_public_key():
    """Get the VAPID public key for push subscription"""
    return {"publicKey": VAPID_PUBLIC_KEY}

@router.post("/subscribe")
async def subscribe_to_push(
    subscription: PushSubscription,
    authorization: str = Header(None)
):
    """Subscribe a user to push notifications"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    
    # Get user from token
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id = session.get("user_id")
    
    # Store or update subscription
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "endpoint": subscription.endpoint,
                "keys": subscription.keys,
                "subscribed_at": datetime.now(timezone.utc),
                "is_active": True
            }
        },
        upsert=True
    )
    
    logger.info(f"Push subscription registered for user {user_id}")
    
    return {"message": "Successfully subscribed to push notifications"}

@router.delete("/unsubscribe")
async def unsubscribe_from_push(authorization: str = Header(None)):
    """Unsubscribe a user from push notifications"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id = session.get("user_id")
    
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {"is_active": False}}
    )
    
    return {"message": "Successfully unsubscribed from push notifications"}

@router.post("/send")
async def send_push_notification(
    message: PushMessage,
    authorization: str = Header(None)
):
    """Send push notification (admin only)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"_id": ObjectId(session.get("user_id"))})
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get subscriptions
    query = {"is_active": True}
    if message.user_ids:
        query["user_id"] = {"$in": message.user_ids}
    
    subscriptions = await db.push_subscriptions.find(query).to_list(1000)
    
    if not subscriptions:
        return {"message": "No active subscriptions found", "sent": 0}
    
    # Prepare notification payload
    payload = json.dumps({
        "title": message.title,
        "body": message.body,
        "icon": message.icon,
        "badge": message.badge,
        "data": {"url": message.url}
    })
    
    sent_count = 0
    failed_count = 0
    
    for sub in subscriptions:
        try:
            subscription_info = {
                "endpoint": sub.get("endpoint"),
                "keys": sub.get("keys")
            }
            
            if VAPID_PRIVATE_KEY:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS
                )
                sent_count += 1
            else:
                # Simulation mode if no VAPID key
                logger.info(f"[SIMULATION] Push notification to {sub.get('user_id')}: {message.title}")
                sent_count += 1
                
        except WebPushException as e:
            logger.error(f"Push notification failed: {e}")
            failed_count += 1
            
            # Mark subscription as inactive if it's gone
            if e.response and e.response.status_code in [404, 410]:
                await db.push_subscriptions.update_one(
                    {"_id": sub["_id"]},
                    {"$set": {"is_active": False}}
                )
    
    # Log notification
    await db.push_logs.insert_one({
        "title": message.title,
        "body": message.body,
        "sent_by": str(user["_id"]),
        "sent_count": sent_count,
        "failed_count": failed_count,
        "sent_at": datetime.now(timezone.utc)
    })
    
    return {
        "message": "Push notifications sent",
        "sent": sent_count,
        "failed": failed_count
    }

@router.get("/stats")
async def get_push_stats(authorization: str = Header(None)):
    """Get push notification statistics (admin only)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"_id": ObjectId(session.get("user_id"))})
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_subscriptions = await db.push_subscriptions.count_documents({})
    active_subscriptions = await db.push_subscriptions.count_documents({"is_active": True})
    
    # Get recent logs
    recent_logs = await db.push_logs.find().sort("sent_at", -1).limit(10).to_list(10)
    
    return {
        "total_subscriptions": total_subscriptions,
        "active_subscriptions": active_subscriptions,
        "recent_notifications": [{
            "title": log.get("title"),
            "sent_count": log.get("sent_count"),
            "sent_at": log.get("sent_at").isoformat() if log.get("sent_at") else None
        } for log in recent_logs]
    }
