"""
InfoPilot Explorer - Groups Routes
Social groups feature
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict
from datetime import datetime, timezone
import uuid

from utils.db import db
from utils.auth import require_user, get_current_user

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("")
async def create_group(name: str = Body(...), description: str = Body(...), is_public: bool = Body(True), user: Dict = Depends(require_user)):
    """Create a new group."""
    group = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "creator_id": user["id"],
        "members": [user["id"]],
        "admins": [user["id"]],
        "is_public": is_public,
        "cover_image": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.groups.insert_one(group)
    return {k: v for k, v in group.items() if k != "_id"}


@router.get("")
async def get_groups(user: Dict = Depends(get_current_user)):
    """Get available groups."""
    if user:
        query = {"$or": [{"is_public": True}, {"members": user["id"]}]}
    else:
        query = {"is_public": True}
    groups = await db.groups.find(query, {"_id": 0}).to_list(100)
    return {"groups": groups}


@router.get("/{group_id}")
async def get_group(group_id: str):
    """Get a specific group."""
    group = await db.groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.post("/{group_id}/join")
async def join_group(group_id: str, user: Dict = Depends(require_user)):
    """Join a group."""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user["id"] not in group.get("members", []):
        await db.groups.update_one({"id": group_id}, {"$push": {"members": user["id"]}})
    
    return {"message": "Joined group successfully"}


@router.post("/{group_id}/leave")
async def leave_group(group_id: str, user: Dict = Depends(require_user)):
    """Leave a group."""
    await db.groups.update_one({"id": group_id}, {"$pull": {"members": user["id"], "admins": user["id"]}})
    return {"message": "Left group"}
