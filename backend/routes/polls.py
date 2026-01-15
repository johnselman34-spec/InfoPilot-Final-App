"""
InfoPilot Explorer - Polls Feature
Allows Group/Page/USP owners to create polls for visitors
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel

from config import db, logger
from routes.auth import get_current_user, get_optional_user

router = APIRouter(tags=["Polls"])


class PollOption(BaseModel):
    text: str


class PollCreate(BaseModel):
    question: str
    options: List[str]
    expires_in_hours: Optional[int] = 24
    allow_multiple: bool = False


class PollVote(BaseModel):
    option_index: int


# ==================== POLL CRUD ====================

@router.post("/polls", response_model=dict)
async def create_poll(
    poll: PollCreate,
    parent_type: str,  # 'group', 'page', or 'usp'
    parent_id: str,
    user = Depends(get_current_user)
):
    """Create a poll for a Group, Page, or Ultimate Search Page"""
    user_id = str(user["_id"])
    
    # Validate parent type
    if parent_type not in ['group', 'page', 'usp']:
        raise HTTPException(status_code=400, detail="Invalid parent type. Must be 'group', 'page', or 'usp'")
    
    # Verify ownership or admin status
    is_authorized = False
    
    if parent_type == 'group':
        group = await db.groups.find_one({"_id": ObjectId(parent_id)})
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        # Check if user is creator or admin of the group
        is_authorized = (
            group.get("created_by") == user_id or 
            user_id in group.get("admins", []) or
            user.get("is_admin")
        )
    elif parent_type == 'page':
        page = await db.pages.find_one({"_id": ObjectId(parent_id)})
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        is_authorized = (
            page.get("created_by") == user_id or
            user_id in page.get("admins", []) or
            user.get("is_admin")
        )
    elif parent_type == 'usp':
        # For USP, the parent_id is the user's own ID
        is_authorized = (parent_id == user_id or user.get("is_admin"))
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Only owners or admins can create polls")
    
    # Validate poll options (2-10 options)
    if len(poll.options) < 2:
        raise HTTPException(status_code=400, detail="Poll must have at least 2 options")
    if len(poll.options) > 10:
        raise HTTPException(status_code=400, detail="Poll cannot have more than 10 options")
    
    # Create poll
    expires_at = None
    if poll.expires_in_hours:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(hours=poll.expires_in_hours)
    
    poll_data = {
        "question": poll.question,
        "options": [{"text": opt, "votes": []} for opt in poll.options],
        "parent_type": parent_type,
        "parent_id": parent_id,
        "created_by": user_id,
        "allow_multiple": poll.allow_multiple,
        "expires_at": expires_at,
        "is_active": True,
        "total_votes": 0,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.polls.insert_one(poll_data)
    
    return {
        "id": str(result.inserted_id),
        "question": poll.question,
        "options": poll.options,
        "message": "Poll created successfully"
    }


@router.get("/polls/{poll_id}", response_model=dict)
async def get_poll(poll_id: str, user = Depends(get_optional_user)):
    """Get a poll by ID"""
    poll = await db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    user_id = str(user["_id"]) if user else None
    
    # Check if poll is expired (handle timezone-aware comparison)
    expires_at = poll.get("expires_at")
    is_expired = False
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        is_expired = expires_at < datetime.now(timezone.utc)
    
    # Get creator info
    creator = await db.users.find_one({"_id": ObjectId(poll["created_by"])})
    
    # Format options with vote counts
    options = []
    user_voted_options = []
    for i, opt in enumerate(poll.get("options", [])):
        vote_count = len(opt.get("votes", []))
        options.append({
            "index": i,
            "text": opt["text"],
            "vote_count": vote_count,
            "percentage": round((vote_count / poll["total_votes"] * 100) if poll["total_votes"] > 0 else 0, 1)
        })
        if user_id and user_id in opt.get("votes", []):
            user_voted_options.append(i)
    
    return {
        "id": str(poll["_id"]),
        "question": poll["question"],
        "options": options,
        "total_votes": poll["total_votes"],
        "allow_multiple": poll.get("allow_multiple", False),
        "is_active": poll.get("is_active", True) and not is_expired,
        "is_expired": is_expired,
        "expires_at": poll.get("expires_at").isoformat() if poll.get("expires_at") else None,
        "created_by": poll["created_by"],
        "creator_name": creator.get("username", "Unknown") if creator else "Unknown",
        "parent_type": poll["parent_type"],
        "parent_id": poll["parent_id"],
        "user_voted": len(user_voted_options) > 0,
        "user_voted_options": user_voted_options,
        "created_at": poll.get("created_at", datetime.now(timezone.utc)).isoformat()
    }


@router.get("/polls/parent/{parent_type}/{parent_id}", response_model=dict)
async def get_polls_for_parent(
    parent_type: str,
    parent_id: str,
    user = Depends(get_optional_user)
):
    """Get all polls for a Group, Page, or USP"""
    if parent_type not in ['group', 'page', 'usp']:
        raise HTTPException(status_code=400, detail="Invalid parent type")
    
    polls = await db.polls.find({
        "parent_type": parent_type,
        "parent_id": parent_id,
        "is_active": True
    }).sort("created_at", -1).to_list(50)
    
    user_id = str(user["_id"]) if user else None
    
    formatted = []
    for poll in polls:
        # Handle timezone-aware comparison
        expires_at = poll.get("expires_at")
        is_expired = False
        if expires_at:
            # Make the comparison timezone-aware
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            is_expired = expires_at < datetime.now(timezone.utc)
        
        options = []
        user_voted = False
        for i, opt in enumerate(poll.get("options", [])):
            vote_count = len(opt.get("votes", []))
            options.append({
                "index": i,
                "text": opt["text"],
                "vote_count": vote_count,
                "percentage": round((vote_count / poll["total_votes"] * 100) if poll["total_votes"] > 0 else 0, 1)
            })
            if user_id and user_id in opt.get("votes", []):
                user_voted = True
        
        formatted.append({
            "id": str(poll["_id"]),
            "question": poll["question"],
            "options": options,
            "total_votes": poll["total_votes"],
            "is_expired": is_expired,
            "user_voted": user_voted,
            "created_at": poll.get("created_at", datetime.now(timezone.utc)).isoformat()
        })
    
    return {"polls": formatted}


@router.post("/polls/{poll_id}/vote", response_model=dict)
async def vote_on_poll(poll_id: str, vote: PollVote, user = Depends(get_current_user)):
    """Vote on a poll option"""
    user_id = str(user["_id"])
    
    poll = await db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    # Check if poll is active and not expired
    if not poll.get("is_active"):
        raise HTTPException(status_code=400, detail="Poll is no longer active")
    
    # Handle timezone-aware comparison
    expires_at = poll.get("expires_at")
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Poll has expired")
    
    # Validate option index
    if vote.option_index < 0 or vote.option_index >= len(poll.get("options", [])):
        raise HTTPException(status_code=400, detail="Invalid option index")
    
    # Check if user already voted (if multiple not allowed)
    if not poll.get("allow_multiple"):
        for opt in poll.get("options", []):
            if user_id in opt.get("votes", []):
                raise HTTPException(status_code=400, detail="You have already voted on this poll")
    
    # Add vote
    await db.polls.update_one(
        {"_id": ObjectId(poll_id)},
        {
            "$addToSet": {f"options.{vote.option_index}.votes": user_id},
            "$inc": {"total_votes": 1}
        }
    )
    
    return {"success": True, "message": "Vote recorded"}


@router.delete("/polls/{poll_id}/vote", response_model=dict)
async def remove_vote(poll_id: str, option_index: int, user = Depends(get_current_user)):
    """Remove vote from a poll option"""
    user_id = str(user["_id"])
    
    poll = await db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    # Remove vote
    await db.polls.update_one(
        {"_id": ObjectId(poll_id)},
        {
            "$pull": {f"options.{option_index}.votes": user_id},
            "$inc": {"total_votes": -1}
        }
    )
    
    return {"success": True, "message": "Vote removed"}


@router.delete("/polls/{poll_id}", response_model=dict)
async def delete_poll(poll_id: str, user = Depends(get_current_user)):
    """Delete a poll (creator or admin only)"""
    user_id = str(user["_id"])
    
    poll = await db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    if poll["created_by"] != user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this poll")
    
    await db.polls.delete_one({"_id": ObjectId(poll_id)})
    
    return {"success": True, "message": "Poll deleted"}


@router.put("/polls/{poll_id}/close", response_model=dict)
async def close_poll(poll_id: str, user = Depends(get_current_user)):
    """Close a poll early (creator or admin only)"""
    user_id = str(user["_id"])
    
    poll = await db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    if poll["created_by"] != user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to close this poll")
    
    await db.polls.update_one(
        {"_id": ObjectId(poll_id)},
        {"$set": {"is_active": False, "closed_at": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "message": "Poll closed"}


# ==================== ADMIN POLL MANAGEMENT ====================

@router.get("/polls/admin/all", response_model=dict)
async def get_all_polls_admin(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,  # 'active', 'closed', 'expired'
    user = Depends(get_current_user)
):
    """Admin-only: Get all polls across the platform"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    now = datetime.now(timezone.utc)
    
    if status == 'active':
        query["is_active"] = True
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": now}}
        ]
    elif status == 'closed':
        query["is_active"] = False
    elif status == 'expired':
        query["expires_at"] = {"$lt": now}
        query["is_active"] = True
    
    skip = (page - 1) * limit
    total = await db.polls.count_documents(query)
    
    polls = await db.polls.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    formatted = []
    for poll in polls:
        creator = await db.users.find_one({"_id": ObjectId(poll["created_by"])})
        
        # Handle timezone-aware comparison
        expires_at = poll.get("expires_at")
        is_expired = False
        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            is_expired = expires_at < now
        
        formatted.append({
            "id": str(poll["_id"]),
            "question": poll["question"],
            "parent_type": poll["parent_type"],
            "parent_id": poll["parent_id"],
            "total_votes": poll.get("total_votes", 0),
            "options_count": len(poll.get("options", [])),
            "is_active": poll.get("is_active", True) and not is_expired,
            "is_expired": is_expired,
            "created_by": poll["created_by"],
            "creator_name": creator.get("username", "Unknown") if creator else "Unknown",
            "created_at": poll.get("created_at", datetime.now(timezone.utc)).isoformat(),
            "expires_at": poll.get("expires_at").isoformat() if poll.get("expires_at") else None
        })
    
    return {
        "polls": formatted,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/polls/admin/statistics", response_model=dict)
async def get_poll_statistics_admin(user = Depends(get_current_user)):
    """Admin-only: Get platform-wide poll statistics"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    
    # Total polls
    total_polls = await db.polls.count_documents({})
    
    # Active polls
    active_polls = await db.polls.count_documents({
        "is_active": True,
        "$or": [
            {"expires_at": None},
            {"expires_at": {"$gt": now}}
        ]
    })
    
    # Closed polls
    closed_polls = await db.polls.count_documents({"is_active": False})
    
    # Expired polls
    expired_polls = await db.polls.count_documents({
        "is_active": True,
        "expires_at": {"$lt": now}
    })
    
    # Total votes across all polls
    pipeline = [
        {"$group": {"_id": None, "total_votes": {"$sum": "$total_votes"}}}
    ]
    vote_result = await db.polls.aggregate(pipeline).to_list(1)
    total_votes = vote_result[0]["total_votes"] if vote_result else 0
    
    # Polls by parent type
    type_pipeline = [
        {"$group": {"_id": "$parent_type", "count": {"$sum": 1}}}
    ]
    type_breakdown = await db.polls.aggregate(type_pipeline).to_list(10)
    polls_by_type = {item["_id"]: item["count"] for item in type_breakdown}
    
    # Most active polls (by votes)
    top_polls = await db.polls.find({}).sort("total_votes", -1).limit(5).to_list(5)
    most_active = []
    for poll in top_polls:
        creator = await db.users.find_one({"_id": ObjectId(poll["created_by"])})
        most_active.append({
            "id": str(poll["_id"]),
            "question": poll["question"][:50] + "..." if len(poll.get("question", "")) > 50 else poll.get("question", ""),
            "votes": poll.get("total_votes", 0),
            "creator": creator.get("username", "Unknown") if creator else "Unknown"
        })
    
    # Recent polls (last 7 days)
    week_ago = now - timedelta(days=7)
    recent_count = await db.polls.count_documents({"created_at": {"$gte": week_ago}})
    
    return {
        "total_polls": total_polls,
        "active_polls": active_polls,
        "closed_polls": closed_polls,
        "expired_polls": expired_polls,
        "total_votes": total_votes,
        "polls_by_type": polls_by_type,
        "most_active_polls": most_active,
        "polls_this_week": recent_count,
        "avg_votes_per_poll": round(total_votes / total_polls, 1) if total_polls > 0 else 0
    }


@router.put("/polls/admin/{poll_id}", response_model=dict)
async def admin_update_poll(
    poll_id: str,
    question: Optional[str] = None,
    is_active: Optional[bool] = None,
    expires_in_hours: Optional[int] = None,
    user = Depends(get_current_user)
):
    """Admin-only: Update any poll's settings"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    poll = await db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    update_data = {}
    
    if question is not None:
        update_data["question"] = question
    
    if is_active is not None:
        update_data["is_active"] = is_active
        if not is_active:
            update_data["closed_at"] = datetime.now(timezone.utc)
            update_data["closed_by"] = str(user["_id"])
    
    if expires_in_hours is not None:
        if expires_in_hours > 0:
            update_data["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        else:
            update_data["expires_at"] = None  # Never expires
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = str(user["_id"])
        await db.polls.update_one({"_id": ObjectId(poll_id)}, {"$set": update_data})
    
    return {"success": True, "message": "Poll updated", "updated_fields": list(update_data.keys())}


@router.delete("/polls/admin/{poll_id}", response_model=dict)
async def admin_delete_poll(poll_id: str, user = Depends(get_current_user)):
    """Admin-only: Delete any poll"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    poll = await db.polls.find_one({"_id": ObjectId(poll_id)})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    await db.polls.delete_one({"_id": ObjectId(poll_id)})
    
    return {"success": True, "message": "Poll deleted by admin"}


# ==================== USER POLL STATISTICS ====================

@router.get("/polls/user/statistics", response_model=dict)
async def get_user_poll_statistics(user = Depends(get_current_user)):
    """Get poll statistics for the current user (their polls)"""
    user_id = str(user["_id"])
    now = datetime.now(timezone.utc)
    
    # User's polls
    user_polls = await db.polls.find({"created_by": user_id}).to_list(100)
    
    total_polls = len(user_polls)
    active_polls = 0
    total_votes_received = 0
    
    for poll in user_polls:
        expires_at = poll.get("expires_at")
        is_active = poll.get("is_active", True)
        
        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > now and is_active:
                active_polls += 1
        elif is_active:
            active_polls += 1
        
        total_votes_received += poll.get("total_votes", 0)
    
    # Polls user has voted on
    # Search through all polls for votes containing user_id
    voted_count = 0
    all_polls = await db.polls.find({}).to_list(500)
    for poll in all_polls:
        for opt in poll.get("options", []):
            if user_id in opt.get("votes", []):
                voted_count += 1
                break
    
    return {
        "polls_created": total_polls,
        "active_polls": active_polls,
        "total_votes_received": total_votes_received,
        "polls_voted_on": voted_count,
        "avg_votes_per_poll": round(total_votes_received / total_polls, 1) if total_polls > 0 else 0
    }
