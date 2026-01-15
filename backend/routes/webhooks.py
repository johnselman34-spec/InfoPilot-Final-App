"""
InfoPilot Explorer - Webhook Integrations
Send notifications to external services (Slack, Discord)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
import httpx
import json

from config import db, logger
from routes.auth import get_current_user

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ==================== PYDANTIC MODELS ====================

class WebhookCreate(BaseModel):
    name: str
    url: str  # Changed from HttpUrl to str for flexibility
    service: str  # slack, discord, custom
    events: List[str]  # protocol_purchase, new_follower, new_message, etc.
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ==================== EVENT TYPES ====================

EVENT_TYPES = {
    "protocol_purchase": {
        "name": "Protocol Purchase",
        "description": "When someone purchases your protocol",
        "icon": "💰"
    },
    "protocol_copy": {
        "name": "Protocol Copied",
        "description": "When someone copies your free protocol",
        "icon": "📋"
    },
    "new_follower": {
        "name": "New Follower",
        "description": "When someone follows your page",
        "icon": "👥"
    },
    "new_friend": {
        "name": "New Friend",
        "description": "When a friend request is accepted",
        "icon": "🤝"
    },
    "new_message": {
        "name": "New Message",
        "description": "When you receive a direct message",
        "icon": "💬"
    },
    "group_join": {
        "name": "Group Join",
        "description": "When someone joins your group",
        "icon": "🎉"
    },
    "poll_vote": {
        "name": "Poll Vote",
        "description": "When someone votes on your poll",
        "icon": "📊"
    },
    "achievement_unlock": {
        "name": "Achievement Unlocked",
        "description": "When you unlock an achievement",
        "icon": "🏆"
    }
}


# ==================== WEBHOOK CRUD ====================

@router.get("/event-types", response_model=dict)
async def get_event_types():
    """Get all available webhook event types"""
    return {"event_types": EVENT_TYPES}


@router.get("", response_model=dict)
async def get_webhooks(user = Depends(get_current_user)):
    """Get user's webhooks"""
    user_id = str(user["_id"])
    
    webhooks = await db.webhooks.find({"user_id": user_id}).to_list(50)
    
    return {
        "webhooks": [{
            "id": str(w["_id"]),
            "name": w["name"],
            "url": w["url"][:50] + "..." if len(w["url"]) > 50 else w["url"],
            "service": w["service"],
            "events": w["events"],
            "is_active": w.get("is_active", True),
            "last_triggered": w.get("last_triggered", {}).get("timestamp"),
            "trigger_count": w.get("trigger_count", 0),
            "created_at": w.get("created_at", datetime.now(timezone.utc)).isoformat()
        } for w in webhooks]
    }


@router.post("", response_model=dict)
async def create_webhook(webhook: WebhookCreate, user = Depends(get_current_user)):
    """Create a new webhook"""
    user_id = str(user["_id"])
    
    # Validate service
    if webhook.service not in ["slack", "discord", "custom"]:
        raise HTTPException(status_code=400, detail="Invalid service. Use: slack, discord, or custom")
    
    # Validate events
    invalid_events = [e for e in webhook.events if e not in EVENT_TYPES]
    if invalid_events:
        raise HTTPException(status_code=400, detail=f"Invalid events: {invalid_events}")
    
    # Limit webhooks per user
    existing_count = await db.webhooks.count_documents({"user_id": user_id})
    if existing_count >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 webhooks allowed")
    
    webhook_data = {
        "user_id": user_id,
        "name": webhook.name,
        "url": webhook.url,
        "service": webhook.service,
        "events": webhook.events,
        "is_active": webhook.is_active,
        "trigger_count": 0,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.webhooks.insert_one(webhook_data)
    
    return {
        "id": str(result.inserted_id),
        "message": "Webhook created successfully"
    }


@router.put("/{webhook_id}", response_model=dict)
async def update_webhook(webhook_id: str, update: WebhookUpdate, user = Depends(get_current_user)):
    """Update a webhook"""
    user_id = str(user["_id"])
    
    webhook = await db.webhooks.find_one({
        "_id": ObjectId(webhook_id),
        "user_id": user_id
    })
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    update_data = {}
    if update.name:
        update_data["name"] = update.name
    if update.url:
        update_data["url"] = update.url
    if update.events:
        invalid_events = [e for e in update.events if e not in EVENT_TYPES]
        if invalid_events:
            raise HTTPException(status_code=400, detail=f"Invalid events: {invalid_events}")
        update_data["events"] = update.events
    if update.is_active is not None:
        update_data["is_active"] = update.is_active
    
    if update_data:
        await db.webhooks.update_one(
            {"_id": ObjectId(webhook_id)},
            {"$set": update_data}
        )
    
    return {"success": True, "message": "Webhook updated"}


@router.delete("/{webhook_id}", response_model=dict)
async def delete_webhook(webhook_id: str, user = Depends(get_current_user)):
    """Delete a webhook"""
    user_id = str(user["_id"])
    
    result = await db.webhooks.delete_one({
        "_id": ObjectId(webhook_id),
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {"success": True, "message": "Webhook deleted"}


@router.post("/{webhook_id}/test", response_model=dict)
async def test_webhook(webhook_id: str, user = Depends(get_current_user)):
    """Test a webhook by sending a test payload"""
    user_id = str(user["_id"])
    
    webhook = await db.webhooks.find_one({
        "_id": ObjectId(webhook_id),
        "user_id": user_id
    })
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Create test payload based on service
    payload = format_webhook_payload(
        service=webhook["service"],
        event_type="test",
        data={
            "message": "🧪 This is a test notification from InfoPilot Explorer!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user.get("username", "Unknown")
        }
    )
    
    # Send test
    success, error = await send_webhook(webhook["url"], payload, webhook["service"])
    
    if success:
        return {"success": True, "message": "Test webhook sent successfully!"}
    else:
        return {"success": False, "message": f"Failed to send: {error}"}


# ==================== WEBHOOK DELIVERY ====================

def format_webhook_payload(service: str, event_type: str, data: dict) -> dict:
    """Format payload based on service type"""
    event_info = EVENT_TYPES.get(event_type, {"name": event_type, "icon": "📣"})
    
    if service == "slack":
        return {
            "text": f"{event_info.get('icon', '📣')} *{event_info.get('name', event_type)}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{event_info.get('icon', '📣')} *{event_info.get('name', event_type)}*\n{data.get('message', 'New event from InfoPilot Explorer')}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🚀 InfoPilot Explorer • {data.get('timestamp', datetime.now(timezone.utc).isoformat())}"
                        }
                    ]
                }
            ]
        }
    
    elif service == "discord":
        return {
            "content": f"{event_info.get('icon', '📣')} **{event_info.get('name', event_type)}**",
            "embeds": [{
                "title": event_info.get("name", event_type),
                "description": data.get("message", "New event from InfoPilot Explorer"),
                "color": 8388863,  # Purple
                "footer": {
                    "text": "🚀 InfoPilot Explorer"
                },
                "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat())
            }]
        }
    
    else:  # custom
        return {
            "event": event_type,
            "event_name": event_info.get("name", event_type),
            "data": data,
            "source": "infopilot_explorer",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def send_webhook(url: str, payload: dict, service: str) -> tuple:
    """Send webhook payload to URL"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201, 204]:
                return True, None
            else:
                return False, f"HTTP {response.status_code}"
    
    except httpx.TimeoutException:
        return False, "Request timed out"
    except Exception as e:
        logger.error(f"Webhook delivery failed: {e}")
        return False, str(e)


async def trigger_webhooks(user_id: str, event_type: str, data: dict):
    """Trigger all webhooks for a user and event type"""
    webhooks = await db.webhooks.find({
        "user_id": user_id,
        "events": event_type,
        "is_active": True
    }).to_list(50)
    
    for webhook in webhooks:
        payload = format_webhook_payload(webhook["service"], event_type, data)
        success, error = await send_webhook(webhook["url"], payload, webhook["service"])
        
        # Update webhook stats
        update = {
            "$inc": {"trigger_count": 1},
            "$set": {
                "last_triggered": {
                    "timestamp": datetime.now(timezone.utc),
                    "event": event_type,
                    "success": success,
                    "error": error
                }
            }
        }
        await db.webhooks.update_one({"_id": webhook["_id"]}, update)


@router.get("/{webhook_id}/logs", response_model=dict)
async def get_webhook_logs(webhook_id: str, user = Depends(get_current_user)):
    """Get delivery logs for a webhook"""
    user_id = str(user["_id"])
    
    webhook = await db.webhooks.find_one({
        "_id": ObjectId(webhook_id),
        "user_id": user_id
    })
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    logs = await db.webhook_logs.find({
        "webhook_id": webhook_id
    }).sort("timestamp", -1).limit(50).to_list(50)
    
    return {
        "logs": [{
            "timestamp": log.get("timestamp", datetime.now(timezone.utc)).isoformat(),
            "event": log.get("event"),
            "success": log.get("success"),
            "error": log.get("error"),
            "response_time_ms": log.get("response_time_ms")
        } for log in logs]
    }
