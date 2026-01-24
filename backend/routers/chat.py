"""
Chat/Messaging routes for InfoPilot Explorer
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
import uuid

from services.database import db
from models.schemas import User
from routers.auth import require_auth

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations")
async def get_conversations(user: User = Depends(require_auth)):
    """Get user's conversations"""
    conversations = await db.conversations.find(
        {"participants": user.user_id},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(50)
    
    # Get participant info
    for conv in conversations:
        other_id = [p for p in conv["participants"] if p != user.user_id][0]
        other_user = await db.users.find_one(
            {"user_id": other_id},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "callsign": 1}
        )
        conv["other_user"] = other_user
    
    return {"conversations": conversations}


@router.post("/messages")
async def send_message(
    request: Request,
    user: User = Depends(require_auth)
):
    """Send a direct message"""
    data = await request.json()
    recipient_id = data.get("recipient_id")
    content = data.get("content")
    
    if not recipient_id or not content:
        raise HTTPException(status_code=400, detail="recipient_id and content required")
    
    # Find or create conversation
    conversation = await db.conversations.find_one({
        "participants": {"$all": [user.user_id, recipient_id]}
    }, {"_id": 0})
    
    if not conversation:
        conversation = {
            "conversation_id": f"conv_{uuid.uuid4().hex[:12]}",
            "participants": [user.user_id, recipient_id],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.conversations.insert_one(conversation)
        conversation.pop("_id", None)
    
    # Create message
    message = {
        "message_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conversation_id": conversation["conversation_id"],
        "sender_id": user.user_id,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message)
    message.pop("_id", None)
    
    # Update conversation timestamp
    await db.conversations.update_one(
        {"conversation_id": conversation["conversation_id"]},
        {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return message


@router.get("/messages/{conversation_id}")
async def get_messages(
    conversation_id: str,
    user: User = Depends(require_auth)
):
    """Get messages in a conversation"""
    # Verify user is participant
    conversation = await db.conversations.find_one({
        "conversation_id": conversation_id,
        "participants": user.user_id
    }, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return {"messages": messages}


@router.post("/rooms")
async def create_chat_room(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a chat room"""
    data = await request.json()
    
    room = {
        "room_id": f"room_{uuid.uuid4().hex[:12]}",
        "name": data.get("name"),
        "owner_id": user.user_id,
        "members": [user.user_id] + data.get("members", []),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_rooms.insert_one(room)
    room.pop("_id", None)
    return room


@router.get("/rooms")
async def get_chat_rooms(user: User = Depends(require_auth)):
    """Get user's chat rooms"""
    rooms = await db.chat_rooms.find(
        {"members": user.user_id},
        {"_id": 0}
    ).to_list(50)
    
    return {"rooms": rooms}


@router.get("/search")
async def search_messages(
    query: str,
    user: User = Depends(require_auth)
):
    """Search messages in user's conversations"""
    # Get user's conversations
    conversations = await db.conversations.find(
        {"participants": user.user_id},
        {"_id": 0, "conversation_id": 1}
    ).to_list(100)
    
    conv_ids = [c["conversation_id"] for c in conversations]
    
    # Search messages
    messages = await db.messages.find(
        {
            "conversation_id": {"$in": conv_ids},
            "content": {"$regex": query, "$options": "i"}
        },
        {"_id": 0}
    ).limit(50).to_list(50)
    
    return {"messages": messages}
