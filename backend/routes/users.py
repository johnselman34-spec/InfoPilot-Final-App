"""
InfoPilot Explorer - Users Routes
User profile management
"""
from fastapi import APIRouter, Body, Depends
from typing import Dict

from utils.db import db
from utils.auth import require_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/profile")
async def update_profile(updates: Dict = Body(...), user: Dict = Depends(require_user)):
    """Update user profile."""
    allowed = ["first_name", "last_name", "ultimate_search_name"]
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if filtered:
        await db.users.update_one({"id": user["id"]}, {"$set": filtered})
    return {"message": "Profile updated"}


@router.put("/theme")
async def update_theme(mode: str = Body(...), preset: str = Body(...), user: Dict = Depends(require_user)):
    """Update user theme settings."""
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"theme_settings": {"mode": mode, "preset": preset}}}
    )
    return {"message": "Theme updated"}


@router.get("/search")
async def search_users(query: str, user: Dict = Depends(require_user)):
    """Search for users."""
    users = await db.users.find(
        {"$or": [
            {"username": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
            {"first_name": {"$regex": query, "$options": "i"}}
        ]},
        {"_id": 0, "hashed_password": 0}
    ).limit(20).to_list(20)
    return {"users": users}


@router.get("/leaderboard")
async def get_leaderboard():
    """Get laughter points leaderboard."""
    users = await db.users.find({}, {"_id": 0, "username": 1, "laughter_points": 1, "easter_eggs_caught": 1}).sort("laughter_points", -1).limit(10).to_list(10)
    return {"leaderboard": users}
