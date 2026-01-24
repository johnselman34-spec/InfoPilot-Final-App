"""
Users Router - InfoPilot Explorer
Handles user profiles, settings, and user-related operations
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict
from datetime import datetime, timezone
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_explorer')]


@router.get("/me")
async def get_current_user(user_id: str = None):
    """Get current user profile"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str, requesting_user_id: str = None):
    """Get a user's public profile"""
    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "email": 0}  # Don't expose email
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only show full profile if it's the user's own or if public
    if user.get("usp_public", False) or user_id == requesting_user_id:
        return user
    else:
        return {
            "user_id": user.get("user_id"),
            "name": user.get("name"),
            "usp_handle": user.get("usp_handle"),
            "level": user.get("level", 1),
            "badges": user.get("badges", []),
            "picture": user.get("picture")
        }


@router.put("/settings")
async def update_user_settings(request: Request, user_id: str = None):
    """Update user settings"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    
    # Allowed settings to update
    allowed_fields = [
        "usp_public", "friends_visible", "content_filter",
        "newsletter_subscribed", "email_notifications", "search_alerts",
        "preferred_engines", "theme"
    ]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Settings updated", "updated": list(update_data.keys())}


@router.get("/search")
async def search_users(q: str, limit: int = 20, user_id: str = None):
    """Search for users by name or USP handle"""
    if len(q) < 2:
        return {"users": []}
    
    users = await db.users.find(
        {
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"usp_handle": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "email": 0}
    ).limit(limit).to_list(limit)
    
    return {"users": users}


@router.get("/leaderboard")
async def get_leaderboard(category: str = "xp", limit: int = 20):
    """Get user leaderboard by category"""
    sort_field = {
        "xp": "total_xp",
        "level": "level",
        "protocols": "protocols_created",
        "categories": "categories_count",
        "results": "results_count"
    }.get(category, "total_xp")
    
    users = await db.users.find(
        {},
        {"_id": 0, "email": 0}
    ).sort(sort_field, -1).limit(limit).to_list(limit)
    
    return {
        "category": category,
        "leaderboard": [
            {
                "rank": i + 1,
                "user_id": u.get("user_id"),
                "name": u.get("name"),
                "usp_handle": u.get("usp_handle"),
                "picture": u.get("picture"),
                "level": u.get("level", 1),
                "value": u.get(sort_field, 0)
            }
            for i, u in enumerate(users)
        ]
    }


@router.get("/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get statistics for a user"""
    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count user's items
    categories_count = await db.categories.count_documents({"user_id": user_id})
    results_count = await db.search_results.count_documents({"user_id": user_id})
    protocols_count = await db.protocols.count_documents({"creator_id": user_id})
    
    return {
        "user_id": user_id,
        "categories_count": categories_count,
        "results_count": results_count,
        "protocols_count": protocols_count,
        "level": user.get("level", 1),
        "total_xp": user.get("total_xp", 0),
        "badges": user.get("badges", []),
        "member_since": user.get("created_at")
    }


@router.post("/{user_id}/follow")
async def follow_user(user_id: str, requesting_user_id: str = None):
    """Follow another user"""
    if not requesting_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user_id == requesting_user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Add to following list
    await db.users.update_one(
        {"user_id": requesting_user_id},
        {"$addToSet": {"following": user_id}}
    )
    
    # Add to followers list
    await db.users.update_one(
        {"user_id": user_id},
        {"$addToSet": {"followers": requesting_user_id}}
    )
    
    return {"message": f"Now following user {user_id}"}


@router.delete("/{user_id}/follow")
async def unfollow_user(user_id: str, requesting_user_id: str = None):
    """Unfollow a user"""
    if not requesting_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Remove from following list
    await db.users.update_one(
        {"user_id": requesting_user_id},
        {"$pull": {"following": user_id}}
    )
    
    # Remove from followers list
    await db.users.update_one(
        {"user_id": user_id},
        {"$pull": {"followers": requesting_user_id}}
    )
    
    return {"message": f"Unfollowed user {user_id}"}


@router.get("/{user_id}/followers")
async def get_user_followers(user_id: str, limit: int = 50):
    """Get a user's followers"""
    user = await db.users.find_one(
        {"user_id": user_id},
        {"followers": 1}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    follower_ids = user.get("followers", [])[:limit]
    
    followers = await db.users.find(
        {"user_id": {"$in": follower_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "usp_handle": 1, "picture": 1, "level": 1}
    ).to_list(limit)
    
    return {"followers": followers, "total": len(user.get("followers", []))}


@router.get("/{user_id}/following")
async def get_user_following(user_id: str, limit: int = 50):
    """Get users that a user is following"""
    user = await db.users.find_one(
        {"user_id": user_id},
        {"following": 1}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following_ids = user.get("following", [])[:limit]
    
    following = await db.users.find(
        {"user_id": {"$in": following_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "usp_handle": 1, "picture": 1, "level": 1}
    ).to_list(limit)
    
    return {"following": following, "total": len(user.get("following", []))}
