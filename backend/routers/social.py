"""
Social routes for InfoPilot Explorer (Friends, Reactions, Comments, Leaderboard)
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
import uuid

from services.database import db
from models.schemas import User
from models.enums import ReactionType
from routers.auth import require_auth

router = APIRouter(prefix="/social", tags=["Social"])


@router.post("/friends/request")
async def send_friend_request(
    request: Request,
    user: User = Depends(require_auth)
):
    """Send friend request"""
    data = await request.json()
    friend_user_id = data.get("user_id")
    
    if not friend_user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    if friend_user_id == user.user_id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    
    # Check if already friends or pending
    existing = await db.friends.find_one({
        "$or": [
            {"user_id_1": user.user_id, "user_id_2": friend_user_id},
            {"user_id_1": friend_user_id, "user_id_2": user.user_id}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already exists")
    
    await db.friends.insert_one({
        "friendship_id": f"friend_{uuid.uuid4().hex[:12]}",
        "user_id_1": user.user_id,
        "user_id_2": friend_user_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Friend request sent"}


@router.post("/friends/accept")
async def accept_friend_request(
    request: Request,
    user: User = Depends(require_auth)
):
    """Accept friend request"""
    data = await request.json()
    friendship_id = data.get("friendship_id")
    
    result = await db.friends.update_one(
        {"friendship_id": friendship_id, "user_id_2": user.user_id, "status": "pending"},
        {"$set": {"status": "accepted"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    return {"message": "Friend request accepted"}


@router.get("/friends")
async def get_friends(user: User = Depends(require_auth)):
    """Get user's friends"""
    friends = await db.friends.find(
        {
            "$or": [
                {"user_id_1": user.user_id},
                {"user_id_2": user.user_id}
            ],
            "status": "accepted"
        },
        {"_id": 0}
    ).to_list(500)
    
    # Get friend user details
    friend_ids = []
    for f in friends:
        if f["user_id_1"] == user.user_id:
            friend_ids.append(f["user_id_2"])
        else:
            friend_ids.append(f["user_id_1"])
    
    friend_users = await db.users.find(
        {"user_id": {"$in": friend_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "callsign": 1}
    ).to_list(500)
    
    return {"friends": friend_users}


@router.post("/reactions")
async def add_reaction(
    request: Request,
    user: User = Depends(require_auth)
):
    """Add reaction to search result"""
    data = await request.json()
    result_id = data.get("result_id")
    reaction_type = data.get("reaction_type")
    
    if reaction_type not in [r.value for r in ReactionType]:
        raise HTTPException(status_code=400, detail="Invalid reaction type")
    
    await db.search_results.update_one(
        {"result_id": result_id},
        {"$inc": {f"reactions.{reaction_type}": 1}}
    )
    
    # Store individual reaction
    await db.reactions.insert_one({
        "reaction_id": f"react_{uuid.uuid4().hex[:12]}",
        "result_id": result_id,
        "user_id": user.user_id,
        "reaction_type": reaction_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Reaction added"}


@router.post("/comments")
async def add_comment(
    request: Request,
    user: User = Depends(require_auth)
):
    """Add comment to search result"""
    data = await request.json()
    result_id = data.get("result_id")
    content = data.get("content")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content required")
    
    comment = {
        "comment_id": f"com_{uuid.uuid4().hex[:12]}",
        "result_id": result_id,
        "user_id": user.user_id,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.comments.insert_one(comment)
    comment.pop("_id", None)
    
    # Update comment count
    await db.search_results.update_one(
        {"result_id": result_id},
        {"$inc": {"comments_count": 1}}
    )
    
    return comment


@router.get("/comments/{result_id}")
async def get_comments(result_id: str):
    """Get comments for a search result"""
    comments = await db.comments.find(
        {"result_id": result_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"comments": comments}


@router.get("/leaderboard")
async def get_community_leaderboard():
    """Get community leaderboard with various categories"""
    # XP Leaders
    xp_leaders = await db.users.find(
        {},
        {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "xp": 1, "level": 1, "callsign": 1}
    ).sort("xp", -1).limit(10).to_list(10)
    
    # Protocol Sellers
    top_sellers = await db.categories.aggregate([
        {"$match": {"price": {"$gt": 0}, "sales_count": {"$gt": 0}}},
        {"$group": {
            "_id": "$user_id",
            "total_sales": {"$sum": "$sales_count"},
            "protocols": {"$sum": 1}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get user info for sellers
    for seller in top_sellers:
        user = await db.users.find_one(
            {"user_id": seller["_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        seller["user"] = user
    
    # Most Active (by search results)
    most_active = await db.search_results.aggregate([
        {"$group": {"_id": "$user_id", "search_count": {"$sum": 1}}},
        {"$sort": {"search_count": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    for active in most_active:
        user = await db.users.find_one(
            {"user_id": active["_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        active["user"] = user
    
    # Top Reactors
    top_reactors = await db.reactions.aggregate([
        {"$group": {"_id": "$user_id", "reactions_given": {"$sum": 1}}},
        {"$sort": {"reactions_given": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    for reactor in top_reactors:
        user = await db.users.find_one(
            {"user_id": reactor["_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        reactor["user"] = user
    
    return {
        "xp_leaders": xp_leaders,
        "top_sellers": top_sellers,
        "most_active": most_active,
        "top_reactors": top_reactors
    }
