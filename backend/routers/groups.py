"""
Groups routes for InfoPilot Explorer
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid

from services.database import db
from models.schemas import User
from routers.auth import require_auth

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("")
async def get_groups(
    search: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Get groups"""
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    groups = await db.groups.find(query, {"_id": 0}).to_list(100)
    return {"groups": groups}


@router.get("/search")
async def search_groups(
    name: Optional[str] = None,
    content: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Search groups by name and/or content"""
    query = {}
    
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    
    groups = await db.groups.find(query, {"_id": 0}).to_list(100)
    
    # If content search is specified, filter by posts content
    if content:
        filtered_groups = []
        for group in groups:
            # Check description
            if group.get("description") and content.lower() in group["description"].lower():
                filtered_groups.append(group)
                continue
            
            # Check posts
            posts = await db.group_posts.find(
                {"group_id": group["group_id"], "content": {"$regex": content, "$options": "i"}},
                {"_id": 0}
            ).limit(1).to_list(1)
            
            if posts:
                filtered_groups.append(group)
        
        return {"groups": filtered_groups}
    
    return {"groups": groups}


@router.post("")
async def create_group(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a group"""
    data = await request.json()
    
    group = {
        "group_id": f"grp_{uuid.uuid4().hex[:12]}",
        "name": data.get("name"),
        "description": data.get("description", ""),
        "owner_id": user.user_id,
        "members": [user.user_id],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.groups.insert_one(group)
    group.pop("_id", None)
    return group


@router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    user: User = Depends(require_auth)
):
    """Join a group"""
    result = await db.groups.update_one(
        {"group_id": group_id},
        {"$addToSet": {"members": user.user_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "Joined group"}


@router.post("/{group_id}/post")
async def create_group_post(
    group_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a post in a group"""
    data = await request.json()
    
    # Verify membership
    group = await db.groups.find_one(
        {"group_id": group_id, "members": user.user_id},
        {"_id": 0}
    )
    
    if not group:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    post = {
        "post_id": f"post_{uuid.uuid4().hex[:12]}",
        "group_id": group_id,
        "author_id": user.user_id,
        "content": data.get("content"),
        "reactions": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.posts.insert_one(post)
    post.pop("_id", None)
    return post


@router.get("/{group_id}/posts")
async def get_group_posts(
    group_id: str,
    user: User = Depends(require_auth)
):
    """Get posts in a group"""
    posts = await db.posts.find(
        {"group_id": group_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get author info
    for post in posts:
        author = await db.users.find_one(
            {"user_id": post["author_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        post["author"] = author
    
    return {"posts": posts}
