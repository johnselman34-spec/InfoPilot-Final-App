"""
InfoPilot Explorer - Direct Messaging Routes
Real-time private messaging with WebSocket support
Text, Images, Typing Indicators, Read Receipts
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from typing import Optional, List, Dict
from bson import ObjectId
import os
import uuid
import shutil
import json
import logging

from config import db, logger
from routes.auth import get_current_user

router = APIRouter(tags=["Direct Messages"])


# ==================== PUSH NOTIFICATION HELPER ====================

async def send_dm_push_notification(recipient_id: str, sender_name: str, message_preview: str, conversation_id: str):
    """Send push notification for new DM to offline users"""
    try:
        from pywebpush import webpush, WebPushException
        import json
        
        VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
        # VAPID_PUBLIC_KEY used by client, private key used for signing
        VAPID_CLAIMS = {"sub": "mailto:admin@infopilot.com"}
        
        # Get user's push subscription
        subscription = await db.push_subscriptions.find_one({
            "user_id": recipient_id,
            "is_active": True
        })
        
        if not subscription:
            logger.info(f"No active push subscription for user {recipient_id}")
            return
        
        # Prepare notification payload
        payload = json.dumps({
            "title": f"📬 New message from {sender_name}",
            "body": message_preview,
            "icon": "/logo192.png",
            "badge": "/logo192.png",
            "data": {
                "url": f"/messages?conversation={conversation_id}",
                "type": "direct_message",
                "conversation_id": conversation_id
            }
        })
        
        subscription_info = {
            "endpoint": subscription.get("endpoint"),
            "keys": subscription.get("keys")
        }
        
        if VAPID_PRIVATE_KEY:
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS
                )
                logger.info(f"Push notification sent to {recipient_id} for DM from {sender_name}")
            except WebPushException as e:
                logger.error(f"Push notification failed: {e}")
                # Mark subscription as inactive if it's gone
                if e.response and e.response.status_code in [404, 410]:
                    await db.push_subscriptions.update_one(
                        {"_id": subscription["_id"]},
                        {"$set": {"is_active": False}}
                    )
        else:
            # Simulation mode if no VAPID key
            logger.info(f"[SIMULATION] Push notification to {recipient_id}: New message from {sender_name}")
            
    except Exception as e:
        logger.error(f"Error sending DM push notification: {e}")

# Upload directory for message images
DM_UPLOAD_DIR = "/app/backend/uploads/messages"
os.makedirs(DM_UPLOAD_DIR, exist_ok=True)

MAX_IMAGE_SIZE = 6.9 * 1024 * 1024  # 6.9MB

# Active WebSocket connections for DMs
dm_connections: Dict[str, WebSocket] = {}  # user_id -> websocket
typing_status: Dict[str, Dict[str, datetime]] = {}  # conversation_id -> {user_id: timestamp}


def get_conversation_id(user1_id: str, user2_id: str) -> str:
    """Generate consistent conversation ID for two users"""
    ids = sorted([user1_id, user2_id])
    return f"{ids[0]}_{ids[1]}"


# ==================== CONVERSATIONS ====================

@router.get("/dm/conversations", response_model=dict)
async def get_conversations(user = Depends(get_current_user)):
    """Get all conversations for current user"""
    user_id = str(user["_id"])
    
    # Find all conversations where user is a participant
    conversations = await db.dm_conversations.find({
        "participants": user_id
    }).sort("last_message_at", -1).to_list(100)
    
    formatted = []
    for conv in conversations:
        # Get the other participant
        other_id = [p for p in conv["participants"] if p != user_id][0]
        other_user = await db.users.find_one({"_id": ObjectId(other_id)})
        
        # Get unread count
        unread_count = await db.dm_messages.count_documents({
            "conversation_id": str(conv["_id"]),
            "sender_id": {"$ne": user_id},
            "read": False
        })
        
        formatted.append({
            "id": str(conv["_id"]),
            "participant": {
                "id": other_id,
                "username": other_user.get("username", "Unknown") if other_user else "Unknown",
                "avatar_url": other_user.get("avatar_url") if other_user else None,
                "is_online": other_id in dm_connections
            },
            "last_message": conv.get("last_message"),
            "last_message_at": conv.get("last_message_at").isoformat() if conv.get("last_message_at") else None,
            "unread_count": unread_count
        })
    
    return {"conversations": formatted}


@router.post("/dm/conversations/{recipient_id}", response_model=dict)
async def create_or_get_conversation(recipient_id: str, user = Depends(get_current_user)):
    """Create or get existing conversation with a user"""
    user_id = str(user["_id"])
    
    if user_id == recipient_id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    
    # Check if recipient exists
    recipient = await db.users.find_one({"_id": ObjectId(recipient_id)})
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for existing conversation
    existing = await db.dm_conversations.find_one({
        "participants": {"$all": [user_id, recipient_id]}
    })
    
    if existing:
        return {
            "id": str(existing["_id"]),
            "is_new": False
        }
    
    # Create new conversation
    conv_data = {
        "participants": sorted([user_id, recipient_id]),
        "created_at": datetime.now(timezone.utc),
        "last_message_at": datetime.now(timezone.utc)
    }
    
    result = await db.dm_conversations.insert_one(conv_data)
    
    return {
        "id": str(result.inserted_id),
        "is_new": True
    }


# ==================== MESSAGES ====================

@router.get("/dm/conversations/{conversation_id}/messages", response_model=dict)
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    before: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get messages for a conversation"""
    user_id = str(user["_id"])
    
    # Verify user is participant
    conv = await db.dm_conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conv or user_id not in conv.get("participants", []):
        raise HTTPException(status_code=403, detail="Not a participant")
    
    query = {"conversation_id": conversation_id}
    if before:
        query["_id"] = {"$lt": ObjectId(before)}
    
    messages = await db.dm_messages.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Mark messages as read
    await db.dm_messages.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": user_id},
            "read": False
        },
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}}
    )
    
    # Get other participant for read receipts
    other_id = [p for p in conv["participants"] if p != user_id][0]
    
    formatted = []
    for m in reversed(messages):
        formatted.append({
            "id": str(m["_id"]),
            "content": m.get("content", ""),
            "image_url": m.get("image_url"),
            "sender_id": m["sender_id"],
            "is_mine": m["sender_id"] == user_id,
            "read": m.get("read", False),
            "read_at": m.get("read_at").isoformat() if m.get("read_at") else None,
            "created_at": m.get("created_at", datetime.now(timezone.utc)).isoformat()
        })
    
    return {
        "messages": formatted,
        "has_more": len(messages) == limit
    }


@router.post("/dm/conversations/{conversation_id}/messages", response_model=dict)
async def send_message(
    conversation_id: str,
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user = Depends(get_current_user)
):
    """Send a message (text and/or image)"""
    user_id = str(user["_id"])
    
    # Verify user is participant
    conv = await db.dm_conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conv or user_id not in conv.get("participants", []):
        raise HTTPException(status_code=403, detail="Not a participant")
    
    image_url = None
    
    # Handle image upload
    if image:
        if image.size > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="Image exceeds 6.9MB limit")
        
        ext = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(DM_UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        image_url = f"/api/uploads/messages/{filename}"
    
    # Create message
    message_data = {
        "conversation_id": conversation_id,
        "sender_id": user_id,
        "content": content,
        "image_url": image_url,
        "read": False,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.dm_messages.insert_one(message_data)
    
    # Update conversation
    preview = content[:50] + "..." if len(content) > 50 else content
    if image_url and not content:
        preview = "📷 Image"
    
    await db.dm_conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$set": {
                "last_message": preview,
                "last_message_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Get recipient for notification
    other_id = [p for p in conv["participants"] if p != user_id][0]
    
    # Send real-time notification if recipient is connected
    if other_id in dm_connections:
        try:
            await dm_connections[other_id].send_json({
                "type": "new_message",
                "conversation_id": conversation_id,
                "message": {
                    "id": str(result.inserted_id),
                    "content": content,
                    "image_url": image_url,
                    "sender_id": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            })
        except Exception:
            pass
    
    # Create notification
    await db.notifications.insert_one({
        "user_id": other_id,
        "type": "direct_message",
        "from_user_id": user_id,
        "conversation_id": conversation_id,
        "message": f"New message from {user.get('username', 'Someone')}",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send push notification if recipient is offline
    if other_id not in dm_connections:
        await send_dm_push_notification(
            recipient_id=other_id,
            sender_name=user.get('username', 'Someone'),
            message_preview=preview,
            conversation_id=conversation_id
        )
    
    return {
        "id": str(result.inserted_id),
        "image_url": image_url,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/dm/conversations/{conversation_id}/typing", response_model=dict)
async def send_typing_indicator(conversation_id: str, user = Depends(get_current_user)):
    """Send typing indicator"""
    user_id = str(user["_id"])
    
    conv = await db.dm_conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conv or user_id not in conv.get("participants", []):
        raise HTTPException(status_code=403, detail="Not a participant")
    
    other_id = [p for p in conv["participants"] if p != user_id][0]
    
    # Send typing indicator to recipient
    if other_id in dm_connections:
        try:
            await dm_connections[other_id].send_json({
                "type": "typing",
                "conversation_id": conversation_id,
                "user_id": user_id
            })
        except Exception:
            pass
    
    return {"success": True}


@router.post("/dm/conversations/{conversation_id}/read", response_model=dict)
async def mark_as_read(conversation_id: str, user = Depends(get_current_user)):
    """Mark all messages in conversation as read"""
    user_id = str(user["_id"])
    
    conv = await db.dm_conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conv or user_id not in conv.get("participants", []):
        raise HTTPException(status_code=403, detail="Not a participant")
    
    result = await db.dm_messages.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": user_id},
            "read": False
        },
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}}
    )
    
    # Send read receipt to other participant
    other_id = [p for p in conv["participants"] if p != user_id][0]
    if other_id in dm_connections:
        try:
            await dm_connections[other_id].send_json({
                "type": "read_receipt",
                "conversation_id": conversation_id,
                "read_by": user_id,
                "read_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception:
            pass
    
    return {"success": True, "marked_count": result.modified_count}


@router.delete("/dm/conversations/{conversation_id}", response_model=dict)
async def delete_conversation(conversation_id: str, user = Depends(get_current_user)):
    """Delete a conversation (for current user only)"""
    user_id = str(user["_id"])
    
    conv = await db.dm_conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conv or user_id not in conv.get("participants", []):
        raise HTTPException(status_code=403, detail="Not a participant")
    
    # Mark as deleted for this user (soft delete)
    await db.dm_conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$addToSet": {"deleted_by": user_id}}
    )
    
    return {"success": True}


# ==================== WEBSOCKET ====================

async def get_user_from_token_ws(token: str):
    """Get user from token for WebSocket"""
    try:
        session = await db.sessions.find_one({"token": token})
        if session:
            return await db.users.find_one({"_id": ObjectId(session.get("user_id"))})
    except Exception:
        pass
    return None


@router.websocket("/dm/ws")
async def dm_websocket(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for real-time DM updates"""
    await websocket.accept()
    
    user = None
    if token:
        user = await get_user_from_token_ws(token)
    
    if not user:
        await websocket.send_json({"error": "Authentication required"})
        await websocket.close()
        return
    
    user_id = str(user["_id"])
    dm_connections[user_id] = websocket
    
    # Update online status
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_online": True, "last_seen": datetime.now(timezone.utc)}}
    )
    
    logger.info(f"DM WebSocket connected for user {user_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif message.get("type") == "typing":
                conv_id = message.get("conversation_id")
                conv = await db.dm_conversations.find_one({"_id": ObjectId(conv_id)})
                if conv and user_id in conv.get("participants", []):
                    other_id = [p for p in conv["participants"] if p != user_id][0]
                    if other_id in dm_connections:
                        await dm_connections[other_id].send_json({
                            "type": "typing",
                            "conversation_id": conv_id,
                            "user_id": user_id
                        })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"DM WebSocket error: {e}")
    finally:
        if user_id in dm_connections:
            del dm_connections[user_id]
        
        # Update offline status
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"is_online": False, "last_seen": datetime.now(timezone.utc)}}
        )
        
        logger.info(f"DM WebSocket disconnected for user {user_id}")


# ==================== ONLINE STATUS ====================

@router.get("/dm/online", response_model=dict)
async def get_online_friends(user = Depends(get_current_user)):
    """Get list of online friends"""
    user_id = str(user["_id"])
    
    # Get friends
    friendships = await db.friendships.find({
        "status": "accepted",
        "$or": [{"user_id": user_id}, {"friend_id": user_id}]
    }).to_list(500)
    
    friend_ids = []
    for f in friendships:
        friend_ids.append(f["friend_id"] if f["user_id"] == user_id else f["user_id"])
    
    online_friends = []
    for fid in friend_ids:
        if fid in dm_connections:
            friend = await db.users.find_one({"_id": ObjectId(fid)})
            if friend:
                online_friends.append({
                    "id": fid,
                    "username": friend.get("username", "Unknown"),
                    "avatar_url": friend.get("avatar_url")
                })
    
    return {"online_friends": online_friends, "count": len(online_friends)}
