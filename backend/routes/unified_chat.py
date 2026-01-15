"""
InfoPilot Explorer - Unified Chat Module
Consolidates Group Chat and Direct Messages into a unified interface
"""
from fastapi import APIRouter, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from typing import Optional, Dict, List
from bson import ObjectId
import json
import logging

from config import db, logger

# Import existing routers
from routes.chat import router as group_chat_router, active_connections, user_connections
from routes.messages import router as dm_router, dm_connections

router = APIRouter(prefix="/unified-chat", tags=["Unified Chat"])


# ==================== UNIFIED CHAT OVERVIEW ====================

@router.get("/overview", response_model=dict)
async def get_chat_overview(authorization: str = Header(None)):
    """Get unified overview of all chats (groups + DMs)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = session.get("user_id")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Get group chats
    group_rooms = await db.chat_rooms.find({"member_ids": user_id}).sort("last_message_at", -1).to_list(50)
    
    group_chats = []
    for room in group_rooms:
        last_message = await db.chat_messages.find_one(
            {"room_id": str(room["_id"])},
            sort=[("created_at", -1)]
        )
        
        unread_count = await db.chat_messages.count_documents({
            "room_id": str(room["_id"]),
            "user_id": {"$ne": user_id},
            "read_by": {"$nin": [user_id]}
        })
        
        group_chats.append({
            "id": str(room["_id"]),
            "type": "group",
            "name": room.get("name", "Group Chat"),
            "member_count": len(room.get("member_ids", [])),
            "last_message": {
                "content": last_message.get("content", "")[:50] if last_message else None,
                "sender": last_message.get("username") if last_message else None,
                "timestamp": last_message.get("created_at").isoformat() if last_message and last_message.get("created_at") else None
            } if last_message else None,
            "unread_count": unread_count,
            "online_count": len(active_connections.get(str(room["_id"]), []))
        })
    
    # Get DM conversations
    dm_convos = await db.dm_conversations.find({
        "participants": user_id,
        "deleted_by": {"$nin": [user_id]}
    }).sort("last_message_at", -1).to_list(50)
    
    direct_messages = []
    for conv in dm_convos:
        other_id = [p for p in conv["participants"] if p != user_id][0]
        other_user = await db.users.find_one({"_id": ObjectId(other_id)})
        
        unread_count = await db.dm_messages.count_documents({
            "conversation_id": str(conv["_id"]),
            "sender_id": {"$ne": user_id},
            "read": False
        })
        
        direct_messages.append({
            "id": str(conv["_id"]),
            "type": "dm",
            "name": other_user.get("username", "Unknown") if other_user else "Unknown",
            "participant_id": other_id,
            "avatar_url": other_user.get("avatar_url") if other_user else None,
            "is_online": other_id in dm_connections,
            "last_message": {
                "content": conv.get("last_message", "")[:50] if conv.get("last_message") else None,
                "timestamp": conv.get("last_message_at").isoformat() if conv.get("last_message_at") else None
            },
            "unread_count": unread_count
        })
    
    # Calculate totals
    total_unread = sum(g["unread_count"] for g in group_chats) + sum(d["unread_count"] for d in direct_messages)
    
    return {
        "success": True,
        "total_unread": total_unread,
        "group_chats": {
            "count": len(group_chats),
            "chats": group_chats
        },
        "direct_messages": {
            "count": len(direct_messages),
            "conversations": direct_messages
        },
        "online_status": {
            "total_online_users": len(user_connections),
            "you_are_online": user_id in user_connections or user_id in dm_connections
        }
    }


@router.get("/search", response_model=dict)
async def search_chats(
    q: str,
    authorization: str = Header(None)
):
    """Search across all chats and messages"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = session.get("user_id")
    
    if len(q) < 2:
        return {"success": True, "results": []}
    
    results = []
    
    # Search group messages
    user_rooms = await db.chat_rooms.find({"member_ids": user_id}).to_list(100)
    room_ids = [str(r["_id"]) for r in user_rooms]
    
    group_messages = await db.chat_messages.find({
        "room_id": {"$in": room_ids},
        "content": {"$regex": q, "$options": "i"}
    }).sort("created_at", -1).limit(20).to_list(20)
    
    for msg in group_messages:
        room = next((r for r in user_rooms if str(r["_id"]) == msg["room_id"]), None)
        results.append({
            "type": "group_message",
            "chat_id": msg["room_id"],
            "chat_name": room.get("name", "Group") if room else "Group",
            "message_id": str(msg["_id"]),
            "content": msg.get("content", "")[:100],
            "sender": msg.get("username", "Unknown"),
            "timestamp": msg.get("created_at").isoformat() if msg.get("created_at") else None
        })
    
    # Search DM messages
    dm_convos = await db.dm_conversations.find({"participants": user_id}).to_list(100)
    conv_ids = [str(c["_id"]) for c in dm_convos]
    
    dm_messages = await db.dm_messages.find({
        "conversation_id": {"$in": conv_ids},
        "content": {"$regex": q, "$options": "i"}
    }).sort("created_at", -1).limit(20).to_list(20)
    
    for msg in dm_messages:
        conv = next((c for c in dm_convos if str(c["_id"]) == msg["conversation_id"]), None)
        other_id = [p for p in conv["participants"] if p != user_id][0] if conv else None
        other_user = await db.users.find_one({"_id": ObjectId(other_id)}) if other_id else None
        
        results.append({
            "type": "dm_message",
            "chat_id": msg["conversation_id"],
            "chat_name": other_user.get("username", "Unknown") if other_user else "Unknown",
            "message_id": str(msg["_id"]),
            "content": msg.get("content", "")[:100],
            "is_mine": msg.get("sender_id") == user_id,
            "timestamp": msg.get("created_at").isoformat() if msg.get("created_at") else None
        })
    
    # Sort by timestamp
    results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "success": True,
        "query": q,
        "total_results": len(results),
        "results": results[:30]
    }


@router.get("/stats", response_model=dict)
async def get_chat_stats(authorization: str = Header(None)):
    """Get user's chat statistics"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = session.get("user_id")
    
    # Group chat stats
    group_rooms = await db.chat_rooms.count_documents({"member_ids": user_id})
    
    user_room_list = await db.chat_rooms.find({"member_ids": user_id}).to_list(100)
    room_ids = [str(r["_id"]) for r in user_room_list]
    
    group_messages_sent = await db.chat_messages.count_documents({
        "room_id": {"$in": room_ids},
        "user_id": user_id
    })
    
    # DM stats
    dm_convos = await db.dm_conversations.count_documents({"participants": user_id})
    dm_messages_sent = await db.dm_messages.count_documents({"sender_id": user_id})
    dm_messages_received = await db.dm_messages.count_documents({
        "conversation_id": {"$in": [str(c["_id"]) for c in await db.dm_conversations.find({"participants": user_id}).to_list(100)]},
        "sender_id": {"$ne": user_id}
    })
    
    return {
        "success": True,
        "stats": {
            "group_chats": {
                "rooms_joined": group_rooms,
                "messages_sent": group_messages_sent
            },
            "direct_messages": {
                "conversations": dm_convos,
                "messages_sent": dm_messages_sent,
                "messages_received": dm_messages_received
            },
            "total_messages": group_messages_sent + dm_messages_sent,
            "online_status": user_id in user_connections or user_id in dm_connections
        }
    }


# ==================== QUICK ACTIONS ====================

@router.post("/mark-all-read", response_model=dict)
async def mark_all_as_read(authorization: str = Header(None)):
    """Mark all messages as read across all chats"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    session = await db.sessions.find_one({"token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = session.get("user_id")
    
    # Mark group messages as read
    user_rooms = await db.chat_rooms.find({"member_ids": user_id}).to_list(100)
    room_ids = [str(r["_id"]) for r in user_rooms]
    
    group_result = await db.chat_messages.update_many(
        {"room_id": {"$in": room_ids}, "read_by": {"$nin": [user_id]}},
        {"$addToSet": {"read_by": user_id}}
    )
    
    # Mark DM messages as read
    dm_convos = await db.dm_conversations.find({"participants": user_id}).to_list(100)
    conv_ids = [str(c["_id"]) for c in dm_convos]
    
    dm_result = await db.dm_messages.update_many(
        {"conversation_id": {"$in": conv_ids}, "sender_id": {"$ne": user_id}, "read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}}
    )
    
    return {
        "success": True,
        "marked_read": {
            "group_messages": group_result.modified_count,
            "direct_messages": dm_result.modified_count
        }
    }
