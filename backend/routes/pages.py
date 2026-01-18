"""
InfoPilot Explorer - Pages Routes
Social pages feature
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict
from datetime import datetime, timezone
import uuid

from utils.db import db
from utils.auth import require_user

router = APIRouter(prefix="/pages", tags=["Pages"])


@router.post("")
async def create_page(name: str = Body(...), description: str = Body(...), category: str = Body(...), user: Dict = Depends(require_user)):
    """Create a new page."""
    page = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "owner_id": user["id"],
        "category": category,
        "followers": [],
        "cover_image": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.pages.insert_one(page)
    return {k: v for k, v in page.items() if k != "_id"}


@router.get("")
async def get_pages():
    """Get all public pages."""
    pages = await db.pages.find({}, {"_id": 0}).to_list(100)
    return {"pages": pages}


@router.get("/{page_id}")
async def get_page(page_id: str):
    """Get a specific page."""
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/{page_id}/follow")
async def follow_page(page_id: str, user: Dict = Depends(require_user)):
    """Follow a page."""
    page = await db.pages.find_one({"id": page_id})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if user["id"] not in page.get("followers", []):
        await db.pages.update_one({"id": page_id}, {"$push": {"followers": user["id"]}})
    
    return {"message": "Now following page"}


@router.post("/{page_id}/unfollow")
async def unfollow_page(page_id: str, user: Dict = Depends(require_user)):
    """Unfollow a page."""
    await db.pages.update_one({"id": page_id}, {"$pull": {"followers": user["id"]}})
    return {"message": "Unfollowed page"}
