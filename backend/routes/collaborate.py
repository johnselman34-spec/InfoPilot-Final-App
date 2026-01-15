"""
InfoPilot Explorer - Collaborative Protocol Editing
Real-time collaborative editing of search protocols
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
from typing import Optional, Dict, List
from bson import ObjectId
import json
import logging

from config import db, logger
from routes.auth import get_current_user

router = APIRouter(tags=["Collaborative Editing"])

# Active editing sessions
editing_sessions: Dict[str, Dict] = {}  # protocol_id -> {users: [], content: "", version: 0}
protocol_connections: Dict[str, List[WebSocket]] = {}  # protocol_id -> [websockets]


# ==================== COLLABORATION SESSIONS ====================

@router.post("/protocols/{protocol_id}/collaborate/start", response_model=dict)
async def start_collaboration(protocol_id: str, user = Depends(get_current_user)):
    """Start or join a collaborative editing session"""
    user_id = str(user["_id"])
    
    # Check if protocol exists and user has access
    protocol = await db.categories.find_one({"_id": ObjectId(protocol_id)})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check ownership or public status
    if protocol.get("created_by") != user_id and not protocol.get("is_public"):
        raise HTTPException(status_code=403, detail="Not authorized to edit this protocol")
    
    # Initialize or get session
    if protocol_id not in editing_sessions:
        editing_sessions[protocol_id] = {
            "users": [],
            "content": protocol.get("protocol", ""),
            "name": protocol.get("name", ""),
            "version": 0,
            "history": [],
            "locks": {}  # section locks
        }
    
    session = editing_sessions[protocol_id]
    
    # Add user to session if not already present
    user_info = {
        "id": user_id,
        "username": user.get("username", "Unknown"),
        "color": _get_user_color(len(session["users"])),
        "cursor_position": 0
    }
    
    if user_id not in [u["id"] for u in session["users"]]:
        session["users"].append(user_info)
    
    return {
        "session_id": protocol_id,
        "content": session["content"],
        "name": session["name"],
        "version": session["version"],
        "users": session["users"],
        "your_color": user_info["color"]
    }


@router.post("/protocols/{protocol_id}/collaborate/save", response_model=dict)
async def save_protocol(
    protocol_id: str,
    content: str,
    name: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Save collaborative changes to database"""
    user_id = str(user["_id"])
    
    protocol = await db.categories.find_one({"_id": ObjectId(protocol_id)})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol.get("created_by") != user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {
        "protocol": content,
        "updated_at": datetime.now(timezone.utc),
        "last_edited_by": user_id
    }
    
    if name:
        update_data["name"] = name
    
    # Save to history
    await db.protocol_history.insert_one({
        "protocol_id": protocol_id,
        "content": protocol.get("protocol", ""),
        "name": protocol.get("name", ""),
        "edited_by": user_id,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Update protocol
    await db.categories.update_one(
        {"_id": ObjectId(protocol_id)},
        {"$set": update_data}
    )
    
    # Update session if exists
    if protocol_id in editing_sessions:
        editing_sessions[protocol_id]["content"] = content
        if name:
            editing_sessions[protocol_id]["name"] = name
        editing_sessions[protocol_id]["version"] += 1
    
    return {"success": True, "message": "Protocol saved"}


@router.get("/protocols/{protocol_id}/collaborate/history", response_model=dict)
async def get_protocol_history(protocol_id: str, user = Depends(get_current_user)):
    """Get edit history for a protocol"""
    history = await db.protocol_history.find({
        "protocol_id": protocol_id
    }).sort("created_at", -1).limit(50).to_list(50)
    
    formatted = []
    for h in history:
        editor = await db.users.find_one({"_id": ObjectId(h["edited_by"])})
        formatted.append({
            "id": str(h["_id"]),
            "content": h["content"],
            "name": h.get("name"),
            "edited_by": h["edited_by"],
            "editor_name": editor.get("username", "Unknown") if editor else "Unknown",
            "created_at": h.get("created_at", datetime.now(timezone.utc)).isoformat()
        })
    
    return {"history": formatted}


@router.post("/protocols/{protocol_id}/collaborate/restore/{history_id}", response_model=dict)
async def restore_version(
    protocol_id: str,
    history_id: str,
    user = Depends(get_current_user)
):
    """Restore a previous version of the protocol"""
    user_id = str(user["_id"])
    
    protocol = await db.categories.find_one({"_id": ObjectId(protocol_id)})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol.get("created_by") != user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    history_item = await db.protocol_history.find_one({"_id": ObjectId(history_id)})
    if not history_item:
        raise HTTPException(status_code=404, detail="History item not found")
    
    # Save current version to history first
    await db.protocol_history.insert_one({
        "protocol_id": protocol_id,
        "content": protocol.get("protocol", ""),
        "name": protocol.get("name", ""),
        "edited_by": user_id,
        "created_at": datetime.now(timezone.utc),
        "note": "Auto-saved before restore"
    })
    
    # Restore
    await db.categories.update_one(
        {"_id": ObjectId(protocol_id)},
        {
            "$set": {
                "protocol": history_item["content"],
                "name": history_item.get("name", protocol.get("name")),
                "updated_at": datetime.now(timezone.utc),
                "last_edited_by": user_id
            }
        }
    )
    
    return {"success": True, "message": "Version restored"}


@router.post("/protocols/{protocol_id}/collaborate/leave", response_model=dict)
async def leave_session(protocol_id: str, user = Depends(get_current_user)):
    """Leave collaborative editing session"""
    user_id = str(user["_id"])
    
    if protocol_id in editing_sessions:
        session = editing_sessions[protocol_id]
        session["users"] = [u for u in session["users"] if u["id"] != user_id]
        
        # Clean up empty sessions
        if not session["users"]:
            del editing_sessions[protocol_id]
    
    return {"success": True}


# ==================== WEBSOCKET FOR REAL-TIME COLLABORATION ====================

async def get_user_from_token_collab(token: str):
    """Get user from token"""
    try:
        session = await db.sessions.find_one({"token": token})
        if session:
            return await db.users.find_one({"_id": ObjectId(session.get("user_id"))})
    except:
        pass
    return None


@router.websocket("/protocols/{protocol_id}/collaborate/ws")
async def collaborate_websocket(
    websocket: WebSocket,
    protocol_id: str,
    token: str = None
):
    """WebSocket for real-time collaborative editing"""
    await websocket.accept()
    
    user = None
    if token:
        user = await get_user_from_token_collab(token)
    
    if not user:
        await websocket.send_json({"error": "Authentication required"})
        await websocket.close()
        return
    
    user_id = str(user["_id"])
    username = user.get("username", "Unknown")
    
    # Initialize connections list for protocol
    if protocol_id not in protocol_connections:
        protocol_connections[protocol_id] = []
    protocol_connections[protocol_id].append(websocket)
    
    # Initialize session if needed
    if protocol_id not in editing_sessions:
        protocol = await db.categories.find_one({"_id": ObjectId(protocol_id)})
        if protocol:
            editing_sessions[protocol_id] = {
                "users": [],
                "content": protocol.get("protocol", ""),
                "name": protocol.get("name", ""),
                "version": 0,
                "history": [],
                "locks": {}
            }
    
    session = editing_sessions.get(protocol_id, {})
    user_color = _get_user_color(len(session.get("users", [])))
    
    # Add user to session
    user_info = {
        "id": user_id,
        "username": username,
        "color": user_color,
        "cursor_position": 0
    }
    
    if user_id not in [u["id"] for u in session.get("users", [])]:
        session.setdefault("users", []).append(user_info)
    
    # Notify others of join
    await broadcast_to_protocol(protocol_id, {
        "type": "user_joined",
        "user": user_info,
        "users": session.get("users", [])
    }, exclude=websocket)
    
    # Send current state to new user
    await websocket.send_json({
        "type": "init",
        "content": session.get("content", ""),
        "name": session.get("name", ""),
        "version": session.get("version", 0),
        "users": session.get("users", []),
        "your_color": user_color
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "edit":
                # Handle edit operation
                content = message.get("content", "")
                cursor_pos = message.get("cursor_position", 0)
                
                session["content"] = content
                session["version"] += 1
                
                # Update user cursor
                for u in session["users"]:
                    if u["id"] == user_id:
                        u["cursor_position"] = cursor_pos
                        break
                
                # Broadcast to others
                await broadcast_to_protocol(protocol_id, {
                    "type": "edit",
                    "content": content,
                    "version": session["version"],
                    "edited_by": user_id,
                    "cursor_position": cursor_pos
                }, exclude=websocket)
            
            elif message.get("type") == "cursor":
                # Handle cursor movement
                cursor_pos = message.get("position", 0)
                selection = message.get("selection")
                
                for u in session["users"]:
                    if u["id"] == user_id:
                        u["cursor_position"] = cursor_pos
                        break
                
                await broadcast_to_protocol(protocol_id, {
                    "type": "cursor",
                    "user_id": user_id,
                    "position": cursor_pos,
                    "selection": selection
                }, exclude=websocket)
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Collaboration WebSocket error: {e}")
    finally:
        # Remove from connections
        if protocol_id in protocol_connections:
            if websocket in protocol_connections[protocol_id]:
                protocol_connections[protocol_id].remove(websocket)
        
        # Remove user from session
        if protocol_id in editing_sessions:
            session = editing_sessions[protocol_id]
            session["users"] = [u for u in session["users"] if u["id"] != user_id]
            
            # Notify others
            await broadcast_to_protocol(protocol_id, {
                "type": "user_left",
                "user_id": user_id,
                "users": session["users"]
            })
            
            # Clean up empty sessions
            if not session["users"]:
                del editing_sessions[protocol_id]
        
        logger.info(f"User {user_id} left collaboration on protocol {protocol_id}")


async def broadcast_to_protocol(protocol_id: str, message: dict, exclude: WebSocket = None):
    """Broadcast message to all users in a protocol editing session"""
    if protocol_id not in protocol_connections:
        return
    
    for ws in protocol_connections[protocol_id]:
        if ws != exclude:
            try:
                await ws.send_json(message)
            except:
                pass


def _get_user_color(index: int) -> str:
    """Get a unique color for a user based on index"""
    colors = [
        "#f472b6",  # pink
        "#8b5cf6",  # purple
        "#3b82f6",  # blue
        "#10b981",  # green
        "#f59e0b",  # amber
        "#ef4444",  # red
        "#06b6d4",  # cyan
        "#ec4899",  # fuchsia
        "#84cc16",  # lime
        "#a855f7",  # violet
    ]
    return colors[index % len(colors)]


# ==================== PROTOCOL COMMENTS ====================

@router.get("/protocols/{protocol_id}/comments", response_model=dict)
async def get_protocol_comments(protocol_id: str, user = Depends(get_current_user)):
    """Get comments on a protocol"""
    comments = await db.protocol_comments.find({
        "protocol_id": protocol_id
    }).sort("created_at", -1).to_list(100)
    
    formatted = []
    for c in comments:
        author = await db.users.find_one({"_id": ObjectId(c["author_id"])})
        formatted.append({
            "id": str(c["_id"]),
            "content": c["content"],
            "line_number": c.get("line_number"),
            "author_id": c["author_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "resolved": c.get("resolved", False),
            "created_at": c.get("created_at", datetime.now(timezone.utc)).isoformat()
        })
    
    return {"comments": formatted}


@router.post("/protocols/{protocol_id}/comments", response_model=dict)
async def add_protocol_comment(
    protocol_id: str,
    content: str,
    line_number: Optional[int] = None,
    user = Depends(get_current_user)
):
    """Add a comment to a protocol"""
    user_id = str(user["_id"])
    
    comment = {
        "protocol_id": protocol_id,
        "author_id": user_id,
        "content": content,
        "line_number": line_number,
        "resolved": False,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.protocol_comments.insert_one(comment)
    
    # Broadcast to collaborators
    if protocol_id in editing_sessions:
        await broadcast_to_protocol(protocol_id, {
            "type": "new_comment",
            "comment": {
                "id": str(result.inserted_id),
                "content": content,
                "line_number": line_number,
                "author_id": user_id,
                "author_name": user.get("username", "Unknown")
            }
        })
    
    return {"id": str(result.inserted_id), "message": "Comment added"}


@router.post("/protocols/{protocol_id}/comments/{comment_id}/resolve", response_model=dict)
async def resolve_comment(
    protocol_id: str,
    comment_id: str,
    user = Depends(get_current_user)
):
    """Mark a comment as resolved"""
    await db.protocol_comments.update_one(
        {"_id": ObjectId(comment_id)},
        {
            "$set": {
                "resolved": True,
                "resolved_by": str(user["_id"]),
                "resolved_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"success": True, "message": "Comment resolved"}
