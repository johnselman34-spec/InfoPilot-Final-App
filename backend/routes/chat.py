"""
InfoPilot Explorer - Chat Routes
Chat rooms and messaging
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict
from datetime import datetime, timezone
import uuid

from utils.db import db
from utils.auth import require_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/rooms")
async def create_chat_room(name: str = Body(...), description: str = Body(None), is_public: bool = Body(True), user: Dict = Depends(require_user)):
    """Create a new chat room."""
    room = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "creator_id": user["id"],
        "members": [user["id"]],
        "is_public": is_public,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_rooms.insert_one(room)
    return {k: v for k, v in room.items() if k != "_id"}


@router.get("/rooms")
async def get_chat_rooms(user: Dict = Depends(require_user)):
    """Get available chat rooms."""
    query = {"$or": [{"is_public": True}, {"members": user["id"]}]}
    rooms = await db.chat_rooms.find(query, {"_id": 0}).to_list(100)
    return {"rooms": rooms}


@router.get("/rooms/{room_id}")
async def get_chat_room(room_id: str, user: Dict = Depends(require_user)):
    """Get a specific chat room."""
    room = await db.chat_rooms.find_one({"id": room_id}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.post("/rooms/{room_id}/join")
async def join_chat_room(room_id: str, user: Dict = Depends(require_user)):
    """Join a chat room."""
    room = await db.chat_rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if user["id"] not in room.get("members", []):
        await db.chat_rooms.update_one({"id": room_id}, {"$push": {"members": user["id"]}})
    
    return {"message": "Joined room"}


@router.post("/rooms/{room_id}/message")
async def send_message(room_id: str, content: str = Body(..., embed=True), user: Dict = Depends(require_user)):
    """Send a message to a chat room."""
    room = await db.chat_rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    message = {
        "id": str(uuid.uuid4()),
        "room_id": room_id,
        "user_id": user["id"],
        "username": user["username"],
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(message)
    return {k: v for k, v in message.items() if k != "_id"}


@router.get("/rooms/{room_id}/messages")
async def get_messages(room_id: str, limit: int = 50, user: Dict = Depends(require_user)):
    """Get messages from a chat room."""
    messages = await db.chat_messages.find({"room_id": room_id}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"messages": list(reversed(messages))}
