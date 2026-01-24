"""
Pages routes for InfoPilot Explorer (Company pages like Facebook Pages)
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid

from services.database import db
from models.schemas import User
from routers.auth import require_auth

router = APIRouter(prefix="/pages", tags=["Pages"])


@router.get("")
async def get_pages(
    search: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Get pages"""
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    pages = await db.pages.find(query, {"_id": 0}).to_list(100)
    return {"pages": pages}


@router.post("")
async def create_page(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a page"""
    data = await request.json()
    
    page = {
        "page_id": f"page_{uuid.uuid4().hex[:12]}",
        "name": data.get("name"),
        "description": data.get("description", ""),
        "owner_id": user.user_id,
        "followers": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.pages.insert_one(page)
    page.pop("_id", None)
    return page


@router.post("/{page_id}/follow")
async def follow_page(
    page_id: str,
    user: User = Depends(require_auth)
):
    """Follow a page"""
    result = await db.pages.update_one(
        {"page_id": page_id},
        {"$addToSet": {"followers": user.user_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return {"message": "Now following page"}


@router.get("/{page_id}")
async def get_page(
    page_id: str,
    user: User = Depends(require_auth)
):
    """Get a specific page"""
    page = await db.pages.find_one({"page_id": page_id}, {"_id": 0})
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get owner info
    owner = await db.users.find_one(
        {"user_id": page["owner_id"]},
        {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
    )
    page["owner"] = owner
    
    return page


@router.post("/{page_id}/post")
async def create_page_post(
    page_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a post on a page (owner only)"""
    data = await request.json()
    
    # Verify ownership
    page = await db.pages.find_one(
        {"page_id": page_id, "owner_id": user.user_id},
        {"_id": 0}
    )
    
    if not page:
        raise HTTPException(status_code=403, detail="Not the page owner")
    
    post = {
        "post_id": f"post_{uuid.uuid4().hex[:12]}",
        "page_id": page_id,
        "author_id": user.user_id,
        "content": data.get("content"),
        "reactions": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.page_posts.insert_one(post)
    post.pop("_id", None)
    return post


@router.get("/{page_id}/posts")
async def get_page_posts(
    page_id: str,
    user: User = Depends(require_auth)
):
    """Get posts from a page"""
    posts = await db.page_posts.find(
        {"page_id": page_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"posts": posts}
