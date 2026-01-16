"""
InfoPilot Explorer - Real-time Chat Router
WebSocket-based chat functionality
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, List
from bson import ObjectId
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Database will be injected
db = None

# Active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}  # room_id -> [connections]
user_connections: Dict[str, WebSocket] = {}  # user_id -> connection

def init_router(database):
    global db
    db = database
    return router

class MessageCreate(BaseModel):
    room_id: str
    content: str
    message_type: str = "text"  # text, image, file

class RoomCreate(BaseModel):
    name: str
    room_type: str = "group"  # group, direct
    member_ids: List[str] = []

async def get_user_from_token(token: str):
    """Helper to get user from token"""
    session = await db.sessions.find_one({"token": token})
    if not session:
        return None
    user = await db.users.find_one({"_id": ObjectId(session.get("user_id"))})
    return user

@router.websocket("/ws/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: str, token: str = None):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    # Authenticate
    user = None
    if token:
        user = await get_user_from_token(token)
    
    if not user:
        await websocket.send_json({"error": "Authentication required"})
        await websocket.close()
        return
    
    user_id = str(user["_id"])
    username = user.get("username") or user.get("email", "").split("@")[0]
    
    # Add to room connections
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)
    user_connections[user_id] = websocket
    
    # Notify room of new user
    await broadcast_to_room(room_id, {
        "type": "user_joined",
        "user_id": user_id,
        "username": username,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, exclude=websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                # Save message to database
                message = {
                    "room_id": room_id,
                    "user_id": user_id,
                    "username": username,
                    "content": message_data.get("content", ""),
                    "message_type": message_data.get("message_type", "text"),
                    "created_at": datetime.now(timezone.utc)
                }
                result = await db.chat_messages.insert_one(message)
                
                # Broadcast to room
                await broadcast_to_room(room_id, {
                    "type": "message",
                    "id": str(result.inserted_id),
                    "user_id": user_id,
                    "username": username,
                    "content": message_data.get("content"),
                    "message_type": message_data.get("message_type", "text"),
                    "timestamp": message["created_at"].isoformat()
                })
                
            elif message_data.get("type") == "typing":
                # Broadcast typing indicator
                await broadcast_to_room(room_id, {
                    "type": "typing",
                    "user_id": user_id,
                    "username": username,
                    "is_typing": message_data.get("is_typing", False)
                }, exclude=websocket)
                
    except WebSocketDisconnect:
        # Remove from connections
        if room_id in active_connections:
            active_connections[room_id].remove(websocket)
            if not active_connections[room_id]:
                del active_connections[room_id]
        
        if user_id in user_connections:
            del user_connections[user_id]
        
        # Notify room of user leaving
        await broadcast_to_room(room_id, {
            "type": "user_left",
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

async def broadcast_to_room(room_id: str, message: dict, exclude: WebSocket = None):
    """Broadcast message to all users in a room"""
    if room_id not in active_connections:
        return
    
    for connection in active_connections[room_id]:
        if connection != exclude:
            try:
                await connection.send_json(message)
            except Exception:
                pass

@router.post("/rooms")
async def create_room(room: RoomCreate, authorization: str = Header(None)):
    """Create a new chat room"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = str(user["_id"])
    
    # Add creator to members
    member_ids = list(set([user_id] + room.member_ids))
    
    new_room = {
        "name": room.name,
        "room_type": room.room_type,
        "member_ids": member_ids,
        "creator_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "last_message_at": datetime.now(timezone.utc)
    }
    
    result = await db.chat_rooms.insert_one(new_room)
    
    return {
        "id": str(result.inserted_id),
        "name": room.name,
        "room_type": room.room_type,
        "member_count": len(member_ids)
    }

@router.get("/rooms")
async def get_rooms(authorization: str = Header(None)):
    """Get user's chat rooms"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = str(user["_id"])
    
    rooms = await db.chat_rooms.find({
        "member_ids": user_id
    }).sort("last_message_at", -1).to_list(50)
    
    result = []
    for room in rooms:
        # Get last message
        last_message = await db.chat_messages.find_one(
            {"room_id": str(room["_id"])},
            sort=[("created_at", -1)]
        )
        
        # Get unread count
        unread_count = await db.chat_messages.count_documents({
            "room_id": str(room["_id"]),
            "user_id": {"$ne": user_id},
            "read_by": {"$nin": [user_id]}
        })
        
        result.append({
            "id": str(room["_id"]),
            "name": room.get("name"),
            "room_type": room.get("room_type"),
            "member_count": len(room.get("member_ids", [])),
            "last_message": {
                "content": last_message.get("content")[:50] if last_message else None,
                "username": last_message.get("username") if last_message else None,
                "timestamp": last_message.get("created_at").isoformat() if last_message and last_message.get("created_at") else None
            } if last_message else None,
            "unread_count": unread_count,
            "online_count": len(active_connections.get(str(room["_id"]), []))
        })
    
    return {"rooms": result}

@router.get("/rooms/{room_id}/messages")
async def get_room_messages(
    room_id: str,
    limit: int = 50,
    before: str = None,
    authorization: str = Header(None)
):
    """Get messages for a chat room"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = str(user["_id"])
    
    # Verify user is in room
    room = await db.chat_rooms.find_one({"_id": ObjectId(room_id)})
    if not room or user_id not in room.get("member_ids", []):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    query = {"room_id": room_id}
    if before:
        query["_id"] = {"$lt": ObjectId(before)}
    
    messages = await db.chat_messages.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Mark as read
    await db.chat_messages.update_many(
        {"room_id": room_id, "read_by": {"$nin": [user_id]}},
        {"$addToSet": {"read_by": user_id}}
    )
    
    return {
        "messages": [{
            "id": str(m["_id"]),
            "user_id": m.get("user_id"),
            "username": m.get("username"),
            "content": m.get("content"),
            "message_type": m.get("message_type", "text"),
            "timestamp": m.get("created_at").isoformat() if m.get("created_at") else None,
            "is_own": m.get("user_id") == user_id
        } for m in reversed(messages)],
        "room": {
            "id": str(room["_id"]),
            "name": room.get("name"),
            "member_count": len(room.get("member_ids", []))
        }
    }

@router.get("/online")
async def get_online_users():
    """Get list of online users"""
    online_user_ids = list(user_connections.keys())
    
    if not online_user_ids:
        return {"online_users": [], "count": 0}
    
    users = await db.users.find({
        "_id": {"$in": [ObjectId(uid) for uid in online_user_ids]}
    }).to_list(100)
    
    return {
        "online_users": [{
            "id": str(u["_id"]),
            "username": u.get("username") or u.get("email", "").split("@")[0],
            "callsign": u.get("callsign")
        } for u in users],
        "count": len(users)
    }
