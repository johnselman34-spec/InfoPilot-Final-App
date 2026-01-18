"""
InfoPilot Explorer - WebSocket Manager
Real-time chat using native FastAPI WebSocket
"""
import logging
from datetime import datetime, timezone
import uuid
import jwt
import os
import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

from utils.db import db

logger = logging.getLogger(__name__)

# Connection tracking
connected_users: Dict[str, dict] = {}  # connection_id -> {websocket, user_id, username, room_id}
room_connections: Dict[str, Set[str]] = {}  # room_id -> set of connection_ids


async def authenticate_token(token: str) -> dict:
    """Authenticate session token and return user data."""
    if not token:
        return None
    
    try:
        # Look up session in database (same as REST API auth)
        session = await db.sessions.find_one({"token": token})
        if not session:
            logger.error(f"Token auth error: Session not found")
            return None
        
        user_id = session.get("user_id")
        if user_id:
            user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0, "hashed_password": 0})
            return user
    except Exception as e:
        logger.error(f"Token auth error: {e}")
    
    return None


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_data: Dict[str, dict] = {}
        self.room_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user: dict):
        """Accept and register a new connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.user_data[connection_id] = {
            "user_id": user["id"],
            "username": user.get("username", "Unknown"),
            "room_id": None
        }
        logger.info(f"User {user['username']} connected with id {connection_id}")
    
    def disconnect(self, connection_id: str):
        """Remove a connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        user_data = self.user_data.pop(connection_id, None)
        if user_data and user_data.get("room_id"):
            room_id = user_data["room_id"]
            if room_id in self.room_connections:
                self.room_connections[room_id].discard(connection_id)
        
        return user_data
    
    async def join_room(self, connection_id: str, room_id: str) -> dict:
        """Join a chat room."""
        user_data = self.user_data.get(connection_id)
        if not user_data:
            return {"error": "Not authenticated"}
        
        # Leave old room if any
        old_room = user_data.get("room_id")
        if old_room and old_room in self.room_connections:
            self.room_connections[old_room].discard(connection_id)
            await self.broadcast_to_room(old_room, {
                "type": "user_left",
                "user_id": user_data["user_id"],
                "username": user_data["username"]
            }, exclude=connection_id)
        
        # Join new room
        user_data["room_id"] = room_id
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(connection_id)
        
        # Update room membership in DB
        await db.chat_rooms.update_one(
            {"id": room_id},
            {"$addToSet": {"members": user_data["user_id"]}}
        )
        
        # Get recent messages
        messages = await db.chat_messages.find(
            {"room_id": room_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(50).to_list(50)
        
        # Notify room
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "online_count": len(self.room_connections.get(room_id, set()))
        }, exclude=connection_id)
        
        logger.info(f"User {user_data['username']} joined room {room_id}")
        
        return {
            "type": "room_joined",
            "room_id": room_id,
            "messages": list(reversed(messages)),
            "online_count": len(self.room_connections.get(room_id, set()))
        }
    
    async def send_message(self, connection_id: str, content: str) -> dict:
        """Send a message to the current room."""
        user_data = self.user_data.get(connection_id)
        if not user_data:
            return {"error": "Not authenticated"}
        
        room_id = user_data.get("room_id")
        if not room_id:
            return {"error": "Not in a room"}
        
        content = content.strip()
        if not content:
            return {"error": "Message content required"}
        
        # Create message
        message = {
            "id": str(uuid.uuid4()),
            "room_id": room_id,
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to database
        await db.chat_messages.insert_one(message)
        
        # Remove MongoDB _id
        message_data = {k: v for k, v in message.items() if k != "_id"}
        
        # Broadcast to room
        await self.broadcast_to_room(room_id, {
            "type": "new_message",
            **message_data
        })
        
        logger.info(f"Message from {user_data['username']} in room {room_id}")
        
        return {"type": "message_sent", "message": message_data}
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude: str = None):
        """Broadcast a message to all users in a room."""
        if room_id not in self.room_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for conn_id in self.room_connections[room_id]:
            if conn_id == exclude:
                continue
            
            websocket = self.active_connections.get(conn_id)
            if websocket:
                try:
                    await websocket.send_text(message_json)
                except Exception:
                    disconnected.append(conn_id)
        
        # Clean up disconnected
        for conn_id in disconnected:
            self.disconnect(conn_id)
    
    async def send_personal(self, connection_id: str, message: dict):
        """Send a message to a specific user."""
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                self.disconnect(connection_id)
    
    def get_online_users(self, room_id: str) -> list:
        """Get list of online users in a room."""
        users = []
        if room_id in self.room_connections:
            for conn_id in self.room_connections[room_id]:
                user_data = self.user_data.get(conn_id)
                if user_data:
                    users.append({
                        "user_id": user_data["user_id"],
                        "username": user_data["username"]
                    })
        return users


# Global connection manager
manager = ConnectionManager()


async def websocket_handler(websocket: WebSocket, token: str):
    """Handle WebSocket connections."""
    # Authenticate
    user = await authenticate_token(token)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    connection_id = str(uuid.uuid4())
    
    try:
        await manager.connect(websocket, connection_id, user)
        
        # Send connected confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user["id"],
            "username": user.get("username")
        }))
        
        # Message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            
            if msg_type == "join_room":
                response = await manager.join_room(connection_id, message.get("room_id"))
                await websocket.send_text(json.dumps(response))
            
            elif msg_type == "send_message":
                response = await manager.send_message(connection_id, message.get("content", ""))
                if "error" in response:
                    await websocket.send_text(json.dumps(response))
            
            elif msg_type == "typing":
                user_data = manager.user_data.get(connection_id)
                if user_data and user_data.get("room_id"):
                    await manager.broadcast_to_room(user_data["room_id"], {
                        "type": "user_typing",
                        "user_id": user_data["user_id"],
                        "username": user_data["username"],
                        "is_typing": message.get("is_typing", True)
                    }, exclude=connection_id)
            
            elif msg_type == "get_online_users":
                room_id = message.get("room_id")
                users = manager.get_online_users(room_id)
                await websocket.send_text(json.dumps({
                    "type": "online_users",
                    "users": users,
                    "count": len(users)
                }))
            
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    
    except WebSocketDisconnect:
        user_data = manager.disconnect(connection_id)
        if user_data and user_data.get("room_id"):
            await manager.broadcast_to_room(user_data["room_id"], {
                "type": "user_left",
                "user_id": user_data["user_id"],
                "username": user_data["username"]
            })
        logger.info(f"User {user.get('username')} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)

