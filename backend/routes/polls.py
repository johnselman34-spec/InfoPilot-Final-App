"""
InfoPilot Explorer - Polls Feature
Allows Group/Page/USP owners to create polls for visitors
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
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
    
    # Check if poll is expired
    is_expired = False
    if poll.get("expires_at") and poll["expires_at"] < datetime.now(timezone.utc):
        is_expired = True
    
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
    
    if poll.get("expires_at") and poll["expires_at"] < datetime.now(timezone.utc):
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
