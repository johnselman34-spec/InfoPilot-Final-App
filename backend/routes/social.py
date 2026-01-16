"""
InfoPilot Explorer - Enhanced Social Routes
Friends, Groups, Pages, Posts, Comments, Reactions, Photo Uploads
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
import os
import uuid
import shutil

from config import db, logger
from models.schemas import GroupCreate, PageCreate, PostCreate, CommentCreate
from routes.auth import get_current_user, get_optional_user

router = APIRouter(tags=["Social"])

# Photo upload directory
UPLOAD_DIR = "/app/backend/uploads/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_PHOTO_SIZE = 6.9 * 1024 * 1024  # 6.9MB limit

# Reaction types
REACTION_TYPES = ["like", "love", "haha", "wow", "sad", "angry"]


# ==================== FRIENDS SYSTEM ====================

@router.get("/friends", response_model=dict)
async def get_friends(user = Depends(get_current_user)):
    """Get user's friends list"""
    user_id = str(user["_id"])
    
    # Get accepted friendships where user is either sender or receiver
    friendships = await db.friendships.find({
        "$and": [
            {"status": "accepted"},
            {"$or": [{"user_id": user_id}, {"friend_id": user_id}]}
        ]
    }).to_list(500)
    
    friends = []
    for f in friendships:
        # Get the other user's ID
        friend_id = f["friend_id"] if f["user_id"] == user_id else f["user_id"]
        friend = await db.users.find_one({"_id": ObjectId(friend_id)})
        
        if friend:
            friends.append({
                "id": str(friend["_id"]),
                "username": friend.get("username", "Unknown"),
                "email": friend.get("email", ""),
                "avatar_url": friend.get("avatar_url"),
                "is_online": friend.get("is_online", False),
                "last_seen": friend.get("last_seen", datetime.utcnow()).isoformat() if friend.get("last_seen") else None,
                "friendship_date": f.get("accepted_at", f.get("created_at", datetime.utcnow())).isoformat()
            })
    
    return {"friends": friends, "count": len(friends)}


@router.get("/friends/requests", response_model=dict)
async def get_friend_requests(user = Depends(get_current_user)):
    """Get pending friend requests"""
    user_id = str(user["_id"])
    
    # Incoming requests
    incoming = await db.friendships.find({
        "friend_id": user_id,
        "status": "pending"
    }).to_list(100)
    
    # Outgoing requests
    outgoing = await db.friendships.find({
        "user_id": user_id,
        "status": "pending"
    }).to_list(100)
    
    incoming_formatted = []
    for req in incoming:
        sender = await db.users.find_one({"_id": ObjectId(req["user_id"])})
        if sender:
            incoming_formatted.append({
                "id": str(req["_id"]),
                "from_user_id": req["user_id"],
                "from_username": sender.get("username", "Unknown"),
                "avatar_url": sender.get("avatar_url"),
                "sent_at": req.get("created_at", datetime.utcnow()).isoformat()
            })
    
    outgoing_formatted = []
    for req in outgoing:
        receiver = await db.users.find_one({"_id": ObjectId(req["friend_id"])})
        if receiver:
            outgoing_formatted.append({
                "id": str(req["_id"]),
                "to_user_id": req["friend_id"],
                "to_username": receiver.get("username", "Unknown"),
                "avatar_url": receiver.get("avatar_url"),
                "sent_at": req.get("created_at", datetime.utcnow()).isoformat()
            })
    
    return {
        "incoming": incoming_formatted,
        "outgoing": outgoing_formatted
    }


@router.post("/friends/request/{friend_id}", response_model=dict)
async def send_friend_request(friend_id: str, user = Depends(get_current_user)):
    """Send a friend request"""
    user_id = str(user["_id"])
    
    if user_id == friend_id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    
    # Check if friend exists
    friend = await db.users.find_one({"_id": ObjectId(friend_id)})
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if friendship already exists
    existing = await db.friendships.find_one({
        "$or": [
            {"user_id": user_id, "friend_id": friend_id},
            {"user_id": friend_id, "friend_id": user_id}
        ]
    })
    
    if existing:
        if existing["status"] == "accepted":
            raise HTTPException(status_code=400, detail="Already friends")
        elif existing["status"] == "pending":
            raise HTTPException(status_code=400, detail="Friend request already pending")
    
    # Create friend request
    await db.friendships.insert_one({
        "user_id": user_id,
        "friend_id": friend_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    })
    
    # Create notification
    await db.notifications.insert_one({
        "user_id": friend_id,
        "type": "friend_request",
        "from_user_id": user_id,
        "message": f"{user.get('username', 'Someone')} sent you a friend request",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "Friend request sent"}


@router.post("/friends/accept/{request_id}", response_model=dict)
async def accept_friend_request(request_id: str, user = Depends(get_current_user)):
    """Accept a friend request"""
    user_id = str(user["_id"])
    
    request = await db.friendships.find_one({
        "_id": ObjectId(request_id),
        "friend_id": user_id,
        "status": "pending"
    })
    
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    # Accept the request
    await db.friendships.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "accepted", "accepted_at": datetime.utcnow()}}
    )
    
    # Notify the sender
    await db.notifications.insert_one({
        "user_id": request["user_id"],
        "type": "friend_accepted",
        "from_user_id": user_id,
        "message": f"{user.get('username', 'Someone')} accepted your friend request",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "Friend request accepted"}


@router.post("/friends/reject/{request_id}", response_model=dict)
async def reject_friend_request(request_id: str, user = Depends(get_current_user)):
    """Reject a friend request"""
    user_id = str(user["_id"])
    
    result = await db.friendships.delete_one({
        "_id": ObjectId(request_id),
        "friend_id": user_id,
        "status": "pending"
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    return {"success": True, "message": "Friend request rejected"}


@router.delete("/friends/{friend_id}", response_model=dict)
async def remove_friend(friend_id: str, user = Depends(get_current_user)):
    """Remove a friend"""
    user_id = str(user["_id"])
    
    result = await db.friendships.delete_one({
        "$or": [
            {"user_id": user_id, "friend_id": friend_id, "status": "accepted"},
            {"user_id": friend_id, "friend_id": user_id, "status": "accepted"}
        ]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    return {"success": True, "message": "Friend removed"}


@router.get("/friends/search", response_model=dict)
async def search_users(q: str, user = Depends(get_current_user)):
    """Search for users to add as friends"""
    user_id = str(user["_id"])
    
    if len(q) < 2:
        return {"users": []}
    
    # Search by username or email
    users = await db.users.find({
        "$and": [
            {"_id": {"$ne": user["_id"]}},
            {"$or": [
                {"username": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ]}
        ]
    }).limit(20).to_list(20)
    
    # Get friendship status for each user
    results = []
    for u in users:
        u_id = str(u["_id"])
        
        friendship = await db.friendships.find_one({
            "$or": [
                {"user_id": user_id, "friend_id": u_id},
                {"user_id": u_id, "friend_id": user_id}
            ]
        })
        
        status = "none"
        if friendship:
            if friendship["status"] == "accepted":
                status = "friends"
            elif friendship["status"] == "pending":
                if friendship["user_id"] == user_id:
                    status = "pending_sent"
                else:
                    status = "pending_received"
        
        results.append({
            "id": u_id,
            "username": u.get("username", "Unknown"),
            "email": u.get("email", ""),
            "avatar_url": u.get("avatar_url"),
            "friendship_status": status
        })
    
    return {"users": results}


# ==================== GROUPS ====================

@router.get("/groups", response_model=dict)
async def get_groups(user = Depends(get_optional_user)):
    """Get all public groups"""
    query = {"$or": [{"is_private": False}]}
    if user:
        query["$or"].append({"members": str(user["_id"])})
        query["$or"].append({"created_by": str(user["_id"])})
    
    groups = await db.groups.find(query).sort("created_at", -1).to_list(100)
    
    return {
        "groups": [{
            "id": str(g["_id"]),
            "name": g["name"],
            "description": g["description"],
            "cover_photo": g.get("cover_photo"),
            "member_count": len(g.get("members", [])),
            "is_member": user and str(user["_id"]) in g.get("members", []),
            "is_admin": user and str(user["_id"]) == g.get("created_by"),
            "is_private": g.get("is_private", False),
            "created_at": g.get("created_at", datetime.utcnow()).isoformat()
        } for g in groups]
    }


@router.post("/groups", response_model=dict)
async def create_group(group: GroupCreate, user = Depends(get_current_user)):
    """Create a new group"""
    group_data = {
        "name": group.name,
        "description": group.description,
        "is_private": group.is_private,
        "created_by": str(user["_id"]),
        "members": [str(user["_id"])],
        "admins": [str(user["_id"])],
        "created_at": datetime.utcnow()
    }
    
    result = await db.groups.insert_one(group_data)
    
    return {
        "id": str(result.inserted_id),
        "name": group.name,
        "message": "Group created successfully"
    }


@router.get("/groups/{group_id}", response_model=dict)
async def get_group(group_id: str, user = Depends(get_optional_user)):
    """Get group details"""
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get member details
    members = []
    for member_id in group.get("members", [])[:20]:
        member = await db.users.find_one({"_id": ObjectId(member_id)})
        if member:
            members.append({
                "id": str(member["_id"]),
                "username": member.get("username", "Unknown"),
                "avatar_url": member.get("avatar_url"),
                "is_admin": member_id in group.get("admins", [])
            })
    
    return {
        "id": str(group["_id"]),
        "name": group["name"],
        "description": group["description"],
        "cover_photo": group.get("cover_photo"),
        "member_count": len(group.get("members", [])),
        "members": members,
        "is_member": user and str(user["_id"]) in group.get("members", []),
        "is_admin": user and str(user["_id"]) in group.get("admins", []),
        "is_private": group.get("is_private", False),
        "created_at": group.get("created_at", datetime.utcnow()).isoformat()
    }


@router.post("/groups/{group_id}/join", response_model=dict)
async def join_group(group_id: str, user = Depends(get_current_user)):
    """Join a group"""
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if group.get("is_private"):
        raise HTTPException(status_code=400, detail="This is a private group")
    
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$addToSet": {"members": str(user["_id"])}}
    )
    
    return {"success": True, "message": "Joined group"}


@router.post("/groups/{group_id}/leave", response_model=dict)
async def leave_group(group_id: str, user = Depends(get_current_user)):
    """Leave a group"""
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$pull": {"members": str(user["_id"]), "admins": str(user["_id"]), "moderators": str(user["_id"])}}
    )
    
    return {"success": True, "message": "Left group"}


# ==================== GROUP ADMIN ROLES ====================

# Role definitions
GROUP_ROLES = {
    "moderator": {
        "can_delete_posts": True,
        "can_mute_members": True,
        "can_approve_posts": True,
        "can_manage_polls": True,
        "can_add_moderators": False,
        "can_remove_members": False,
        "can_edit_group": False
    },
    "admin": {
        "can_delete_posts": True,
        "can_mute_members": True,
        "can_approve_posts": True,
        "can_manage_polls": True,
        "can_add_moderators": True,
        "can_remove_members": True,
        "can_edit_group": True
    }
}


@router.post("/groups/{group_id}/moderators", response_model=dict)
async def add_moderator(group_id: str, member_id: str, user = Depends(get_current_user)):
    """Add a moderator to the group (admin only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Only admins can add moderators
    if user_id not in group.get("admins", []) and group.get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Only admins can add moderators")
    
    # Check if member exists in group
    if member_id not in group.get("members", []):
        raise HTTPException(status_code=400, detail="User is not a member of this group")
    
    # Add to moderators
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$addToSet": {"moderators": member_id}}
    )
    
    # Notify the new moderator
    await db.notifications.insert_one({
        "user_id": member_id,
        "type": "group_role",
        "group_id": group_id,
        "message": f"You are now a moderator of {group['name']}",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "Moderator added successfully"}


@router.delete("/groups/{group_id}/moderators/{member_id}", response_model=dict)
async def remove_moderator(group_id: str, member_id: str, user = Depends(get_current_user)):
    """Remove a moderator from the group (admin only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Only admins can remove moderators
    if user_id not in group.get("admins", []) and group.get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Only admins can remove moderators")
    
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$pull": {"moderators": member_id}}
    )
    
    return {"success": True, "message": "Moderator removed"}


@router.post("/groups/{group_id}/admins", response_model=dict)
async def add_admin(group_id: str, member_id: str, user = Depends(get_current_user)):
    """Promote a member to admin (owner only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Only owner can add admins
    if group.get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Only the group owner can add admins")
    
    if member_id not in group.get("members", []):
        raise HTTPException(status_code=400, detail="User is not a member of this group")
    
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$addToSet": {"admins": member_id}}
    )
    
    await db.notifications.insert_one({
        "user_id": member_id,
        "type": "group_role",
        "group_id": group_id,
        "message": f"You are now an admin of {group['name']}",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "Admin added successfully"}


@router.delete("/groups/{group_id}/members/{member_id}", response_model=dict)
async def remove_member(group_id: str, member_id: str, user = Depends(get_current_user)):
    """Remove a member from the group (admin only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Only admins can remove members
    if user_id not in group.get("admins", []) and group.get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    
    # Cannot remove the owner
    if member_id == group.get("created_by"):
        raise HTTPException(status_code=400, detail="Cannot remove the group owner")
    
    # Cannot remove yourself (use leave instead)
    if member_id == user_id:
        raise HTTPException(status_code=400, detail="Use leave endpoint to leave the group")
    
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$pull": {"members": member_id, "admins": member_id, "moderators": member_id}}
    )
    
    return {"success": True, "message": "Member removed"}



# ==================== GROUP MODERATION ====================

@router.post("/groups/{group_id}/ban/{member_id}", response_model=dict)
async def ban_group_member(group_id: str, member_id: str, reason: str = "", user = Depends(get_current_user)):
    """Ban a member from the group (admin/moderator only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check permissions
    is_admin = user_id in group.get("admins", []) or group.get("created_by") == user_id
    is_mod = user_id in group.get("moderators", [])
    
    if not is_admin and not is_mod:
        raise HTTPException(status_code=403, detail="Only admins and moderators can ban members")
    
    # Cannot ban the owner or yourself
    if member_id == group.get("created_by"):
        raise HTTPException(status_code=400, detail="Cannot ban the group owner")
    if member_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    
    # Moderators cannot ban admins
    if not is_admin and member_id in group.get("admins", []):
        raise HTTPException(status_code=403, detail="Moderators cannot ban admins")
    
    # Remove from group and add to ban list
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {
            "$pull": {"members": member_id, "admins": member_id, "moderators": member_id},
            "$addToSet": {"banned_members": {
                "user_id": member_id,
                "banned_by": user_id,
                "reason": reason,
                "banned_at": datetime.utcnow()
            }}
        }
    )
    
    # Notify the banned user
    await db.notifications.insert_one({
        "user_id": member_id,
        "type": "group_ban",
        "group_id": group_id,
        "message": f"You have been banned from {group['name']}" + (f": {reason}" if reason else ""),
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "Member banned from group"}


@router.post("/groups/{group_id}/unban/{member_id}", response_model=dict)
async def unban_group_member(group_id: str, member_id: str, user = Depends(get_current_user)):
    """Unban a member from the group (admin only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user_id not in group.get("admins", []) and group.get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Only admins can unban members")
    
    # Remove from ban list
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$pull": {"banned_members": {"user_id": member_id}}}
    )
    
    return {"success": True, "message": "Member unbanned"}


@router.post("/groups/{group_id}/mute/{member_id}", response_model=dict)
async def mute_group_member(group_id: str, member_id: str, duration_hours: int = 24, reason: str = "", user = Depends(get_current_user)):
    """Mute a member in the group (admin/moderator only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check permissions
    is_admin = user_id in group.get("admins", []) or group.get("created_by") == user_id
    is_mod = user_id in group.get("moderators", [])
    
    if not is_admin and not is_mod:
        raise HTTPException(status_code=403, detail="Only admins and moderators can mute members")
    
    # Cannot mute the owner
    if member_id == group.get("created_by"):
        raise HTTPException(status_code=400, detail="Cannot mute the group owner")
    
    # Moderators cannot mute admins
    if not is_admin and member_id in group.get("admins", []):
        raise HTTPException(status_code=403, detail="Moderators cannot mute admins")
    
    from datetime import timedelta
    mute_until = datetime.utcnow() + timedelta(hours=duration_hours)
    
    # Add to muted list
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$set": {f"muted_members.{member_id}": {
            "muted_by": user_id,
            "reason": reason,
            "muted_at": datetime.utcnow(),
            "muted_until": mute_until
        }}}
    )
    
    # Notify the muted user
    await db.notifications.insert_one({
        "user_id": member_id,
        "type": "group_mute",
        "group_id": group_id,
        "message": f"You have been muted in {group['name']} for {duration_hours} hours" + (f": {reason}" if reason else ""),
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": f"Member muted for {duration_hours} hours", "muted_until": mute_until.isoformat()}


@router.post("/groups/{group_id}/unmute/{member_id}", response_model=dict)
async def unmute_group_member(group_id: str, member_id: str, user = Depends(get_current_user)):
    """Unmute a member in the group (admin/moderator only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    is_admin = user_id in group.get("admins", []) or group.get("created_by") == user_id
    is_mod = user_id in group.get("moderators", [])
    
    if not is_admin and not is_mod:
        raise HTTPException(status_code=403, detail="Only admins and moderators can unmute members")
    
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$unset": {f"muted_members.{member_id}": ""}}
    )
    
    return {"success": True, "message": "Member unmuted"}


@router.get("/groups/{group_id}/banned", response_model=dict)
async def get_banned_members(group_id: str, user = Depends(get_current_user)):
    """Get list of banned members (admin only)"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user_id not in group.get("admins", []) and group.get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Only admins can view banned members")
    
    banned = group.get("banned_members", [])
    
    # Get user details for banned members
    banned_with_details = []
    for ban in banned:
        banned_user = await db.users.find_one({"_id": ObjectId(ban["user_id"])})
        if banned_user:
            banned_with_details.append({
                "user_id": ban["user_id"],
                "username": banned_user.get("username", "Unknown"),
                "reason": ban.get("reason", ""),
                "banned_at": ban.get("banned_at").isoformat() if ban.get("banned_at") else None,
                "banned_by": ban.get("banned_by")
            })
    
    return {"banned_members": banned_with_details}


# ==================== PAGE MODERATION ====================

@router.post("/pages/{page_id}/ban/{user_id_to_ban}", response_model=dict)
async def ban_page_follower(page_id: str, user_id_to_ban: str, reason: str = "", user = Depends(get_current_user)):
    """Ban a user from the page (admin only)"""
    current_user_id = str(user["_id"])
    
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Only owner or admins can ban
    if page.get("created_by") != current_user_id and current_user_id not in page.get("admins", []):
        raise HTTPException(status_code=403, detail="Only page admins can ban users")
    
    # Cannot ban the owner
    if user_id_to_ban == page.get("created_by"):
        raise HTTPException(status_code=400, detail="Cannot ban the page owner")
    
    # Remove from followers and add to ban list
    await db.pages.update_one(
        {"_id": ObjectId(page_id)},
        {
            "$pull": {"followers": user_id_to_ban, "admins": user_id_to_ban},
            "$addToSet": {"banned_users": {
                "user_id": user_id_to_ban,
                "banned_by": current_user_id,
                "reason": reason,
                "banned_at": datetime.utcnow()
            }}
        }
    )
    
    # Notify the banned user
    await db.notifications.insert_one({
        "user_id": user_id_to_ban,
        "type": "page_ban",
        "page_id": page_id,
        "message": f"You have been banned from {page['name']}" + (f": {reason}" if reason else ""),
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "User banned from page"}


@router.post("/pages/{page_id}/unban/{user_id_to_unban}", response_model=dict)
async def unban_page_user(page_id: str, user_id_to_unban: str, user = Depends(get_current_user)):
    """Unban a user from the page (admin only)"""
    current_user_id = str(user["_id"])
    
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page.get("created_by") != current_user_id and current_user_id not in page.get("admins", []):
        raise HTTPException(status_code=403, detail="Only page admins can unban users")
    
    await db.pages.update_one(
        {"_id": ObjectId(page_id)},
        {"$pull": {"banned_users": {"user_id": user_id_to_unban}}}
    )
    
    return {"success": True, "message": "User unbanned from page"}



@router.get("/groups/{group_id}/roles", response_model=dict)
async def get_group_roles(group_id: str, user = Depends(get_current_user)):
    """Get all roles and members in a group"""
    user_id = str(user["_id"])
    
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Build roles structure
    owner = await db.users.find_one({"_id": ObjectId(group.get("created_by"))})
    
    admins = []
    for admin_id in group.get("admins", []):
        if admin_id != group.get("created_by"):
            admin = await db.users.find_one({"_id": ObjectId(admin_id)})
            if admin:
                admins.append({
                    "id": str(admin["_id"]),
                    "username": admin.get("username", "Unknown"),
                    "avatar_url": admin.get("avatar_url")
                })
    
    moderators = []
    for mod_id in group.get("moderators", []):
        mod = await db.users.find_one({"_id": ObjectId(mod_id)})
        if mod:
            moderators.append({
                "id": str(mod["_id"]),
                "username": mod.get("username", "Unknown"),
                "avatar_url": mod.get("avatar_url")
            })
    
    return {
        "owner": {
            "id": str(owner["_id"]) if owner else None,
            "username": owner.get("username", "Unknown") if owner else "Unknown",
            "avatar_url": owner.get("avatar_url") if owner else None
        },
        "admins": admins,
        "moderators": moderators,
        "role_definitions": GROUP_ROLES,
        "your_role": "owner" if group.get("created_by") == user_id else (
            "admin" if user_id in group.get("admins", []) else (
                "moderator" if user_id in group.get("moderators", []) else "member"
            )
        )
    }


# ==================== PAGE ADMIN ROLES ====================

@router.post("/pages/{page_id}/admins", response_model=dict)
async def add_page_admin(page_id: str, user_id_to_add: str, user = Depends(get_current_user)):
    """Add an admin to the page (owner only)"""
    current_user_id = str(user["_id"])
    
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page.get("created_by") != current_user_id:
        raise HTTPException(status_code=403, detail="Only the page owner can add admins")
    
    await db.pages.update_one(
        {"_id": ObjectId(page_id)},
        {"$addToSet": {"admins": user_id_to_add}}
    )
    
    await db.notifications.insert_one({
        "user_id": user_id_to_add,
        "type": "page_role",
        "page_id": page_id,
        "message": f"You are now an admin of {page['name']}",
        "read": False,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "Admin added successfully"}


@router.delete("/pages/{page_id}/admins/{admin_id}", response_model=dict)
async def remove_page_admin(page_id: str, admin_id: str, user = Depends(get_current_user)):
    """Remove an admin from the page (owner only)"""
    current_user_id = str(user["_id"])
    
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page.get("created_by") != current_user_id:
        raise HTTPException(status_code=403, detail="Only the page owner can remove admins")
    
    await db.pages.update_one(
        {"_id": ObjectId(page_id)},
        {"$pull": {"admins": admin_id}}
    )
    
    return {"success": True, "message": "Admin removed"}


# ==================== PAGES ====================

@router.get("/pages", response_model=dict)
async def get_pages(user = Depends(get_optional_user)):
    """Get all pages"""
    pages = await db.pages.find().sort("created_at", -1).to_list(100)
    
    return {
        "pages": [{
            "id": str(p["_id"]),
            "name": p["name"],
            "description": p["description"],
            "category": p.get("category", "General"),
            "cover_photo": p.get("cover_photo"),
            "profile_photo": p.get("profile_photo"),
            "follower_count": len(p.get("followers", [])),
            "is_following": user and str(user["_id"]) in p.get("followers", []),
            "is_admin": user and str(user["_id"]) == p.get("created_by"),
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        } for p in pages]
    }


@router.post("/pages", response_model=dict)
async def create_page(page: PageCreate, user = Depends(get_current_user)):
    """Create a new page"""
    page_data = {
        "name": page.name,
        "description": page.description,
        "category": page.category,
        "created_by": str(user["_id"]),
        "followers": [str(user["_id"])],
        "created_at": datetime.utcnow()
    }
    
    result = await db.pages.insert_one(page_data)
    
    return {
        "id": str(result.inserted_id),
        "name": page.name,
        "message": "Page created successfully"
    }


@router.get("/pages/{page_id}", response_model=dict)
async def get_page(page_id: str, user = Depends(get_optional_user)):
    """Get page details"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    owner = await db.users.find_one({"_id": ObjectId(page["created_by"])})
    
    return {
        "id": str(page["_id"]),
        "name": page["name"],
        "description": page["description"],
        "category": page.get("category", "General"),
        "cover_photo": page.get("cover_photo"),
        "profile_photo": page.get("profile_photo"),
        "follower_count": len(page.get("followers", [])),
        "is_following": user and str(user["_id"]) in page.get("followers", []),
        "is_admin": user and str(user["_id"]) == page.get("created_by"),
        "owner_name": owner.get("username", "Unknown") if owner else "Unknown",
        "created_at": page.get("created_at", datetime.utcnow()).isoformat()
    }


@router.post("/pages/{page_id}/follow", response_model=dict)
async def follow_page(page_id: str, user = Depends(get_current_user)):
    """Follow a page"""
    await db.pages.update_one(
        {"_id": ObjectId(page_id)},
        {"$addToSet": {"followers": str(user["_id"])}}
    )
    
    return {"success": True, "message": "Following page"}


@router.post("/pages/{page_id}/unfollow", response_model=dict)
async def unfollow_page(page_id: str, user = Depends(get_current_user)):
    """Unfollow a page"""
    await db.pages.update_one(
        {"_id": ObjectId(page_id)},
        {"$pull": {"followers": str(user["_id"])}}
    )
    
    return {"success": True, "message": "Unfollowed page"}


# ==================== POSTS WITH PHOTOS ====================

@router.get("/posts", response_model=dict)
async def get_posts(
    group_id: Optional[str] = None,
    page_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user = Depends(get_optional_user)
):
    """Get posts for a group, page, user profile, or feed"""
    query = {}
    if group_id:
        query["group_id"] = group_id
    if page_id:
        query["page_id"] = page_id
    if user_id:
        query["author_id"] = user_id
    
    posts = await db.posts.find(query).sort("created_at", -1).limit(50).to_list(50)
    
    formatted = []
    for p in posts:
        # Get author info
        author = await db.users.find_one({"_id": ObjectId(p["author_id"])})
        
        # Get comment count
        comment_count = await db.comments.count_documents({"post_id": str(p["_id"])})
        
        # Get reactions summary
        reactions = p.get("reactions", {})
        reaction_counts = {rt: len(reactions.get(rt, [])) for rt in REACTION_TYPES}
        total_reactions = sum(reaction_counts.values())
        
        # Get user's reaction if logged in
        user_reaction = None
        if user:
            user_id_str = str(user["_id"])
            for rt in REACTION_TYPES:
                if user_id_str in reactions.get(rt, []):
                    user_reaction = rt
                    break
        
        formatted.append({
            "id": str(p["_id"]),
            "content": p["content"],
            "photos": p.get("photos", []),
            "author_id": p["author_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "author_avatar": author.get("avatar_url") if author else None,
            "group_id": p.get("group_id"),
            "page_id": p.get("page_id"),
            "reaction_counts": reaction_counts,
            "total_reactions": total_reactions,
            "user_reaction": user_reaction,
            "comment_count": comment_count,
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {"posts": formatted}


@router.post("/posts", response_model=dict)
async def create_post(post: PostCreate, user = Depends(get_current_user)):
    """Create a new post (without photos)"""
    post_data = {
        "content": post.content,
        "photos": [],
        "author_id": str(user["_id"]),
        "group_id": post.group_id,
        "page_id": post.page_id,
        "reactions": {rt: [] for rt in REACTION_TYPES},
        "created_at": datetime.utcnow()
    }
    
    result = await db.posts.insert_one(post_data)
    
    return {
        "id": str(result.inserted_id),
        "message": "Post created"
    }


@router.post("/posts/with-photos", response_model=dict)
async def create_post_with_photos(
    content: str = Form(...),
    group_id: Optional[str] = Form(None),
    page_id: Optional[str] = Form(None),
    photos: List[UploadFile] = File(default=[]),
    user = Depends(get_current_user)
):
    """Create a post with photo uploads (max 6.9MB per photo)"""
    photo_urls = []
    
    # Process uploaded photos
    for photo in photos[:10]:  # Max 10 photos
        if photo.size > MAX_PHOTO_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"Photo {photo.filename} exceeds 6.9MB limit"
            )
        
        # Generate unique filename
        ext = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        # Store relative URL
        photo_urls.append(f"/api/uploads/photos/{filename}")
    
    post_data = {
        "content": content,
        "photos": photo_urls,
        "author_id": str(user["_id"]),
        "group_id": group_id,
        "page_id": page_id,
        "reactions": {rt: [] for rt in REACTION_TYPES},
        "created_at": datetime.utcnow()
    }
    
    result = await db.posts.insert_one(post_data)
    
    return {
        "id": str(result.inserted_id),
        "photos": photo_urls,
        "message": "Post created with photos"
    }


@router.post("/posts/{post_id}/react", response_model=dict)
async def react_to_post(post_id: str, reaction_type: str, user = Depends(get_current_user)):
    """Add or change reaction to a post"""
    if reaction_type not in REACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid reaction. Must be one of: {REACTION_TYPES}")
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user_id = str(user["_id"])
    reactions = post.get("reactions", {rt: [] for rt in REACTION_TYPES})
    
    # Remove user from all reaction types first
    for rt in REACTION_TYPES:
        if user_id in reactions.get(rt, []):
            reactions[rt].remove(user_id)
    
    # Add to new reaction type
    if reaction_type not in reactions:
        reactions[reaction_type] = []
    reactions[reaction_type].append(user_id)
    
    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"reactions": reactions}}
    )
    
    return {"success": True, "reaction": reaction_type}


@router.delete("/posts/{post_id}/react", response_model=dict)
async def remove_reaction(post_id: str, user = Depends(get_current_user)):
    """Remove reaction from a post"""
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user_id = str(user["_id"])
    reactions = post.get("reactions", {})
    
    # Remove user from all reaction types
    for rt in REACTION_TYPES:
        if user_id in reactions.get(rt, []):
            reactions[rt].remove(user_id)
    
    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"reactions": reactions}}
    )
    
    return {"success": True}


@router.delete("/posts/{post_id}", response_model=dict)
async def delete_post(post_id: str, user = Depends(get_current_user)):
    """Delete a post"""
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check ownership or admin
    if post["author_id"] != str(user["_id"]) and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    # Delete associated photos
    for photo_url in post.get("photos", []):
        try:
            filename = photo_url.split("/")[-1]
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
    
    # Delete comments
    await db.comments.delete_many({"post_id": post_id})
    
    # Delete post
    await db.posts.delete_one({"_id": ObjectId(post_id)})
    
    return {"success": True, "message": "Post deleted"}


# ==================== COMMENTS ====================

@router.get("/posts/{post_id}/comments", response_model=dict)
async def get_comments(post_id: str, user = Depends(get_optional_user)):
    """Get comments for a post"""
    comments = await db.comments.find({"post_id": post_id}).sort("created_at", 1).to_list(100)
    
    formatted = []
    for c in comments:
        author = await db.users.find_one({"_id": ObjectId(c["author_id"])})
        
        # Get reactions for comment
        reactions = c.get("reactions", {})
        reaction_counts = {rt: len(reactions.get(rt, [])) for rt in REACTION_TYPES}
        
        user_reaction = None
        if user:
            user_id_str = str(user["_id"])
            for rt in REACTION_TYPES:
                if user_id_str in reactions.get(rt, []):
                    user_reaction = rt
                    break
        
        formatted.append({
            "id": str(c["_id"]),
            "content": c["content"],
            "author_id": c["author_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "author_avatar": author.get("avatar_url") if author else None,
            "reaction_counts": reaction_counts,
            "user_reaction": user_reaction,
            "created_at": c.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {"comments": formatted}


@router.post("/comments", response_model=dict)
async def create_comment(comment: CommentCreate, user = Depends(get_current_user)):
    """Create a comment on a post"""
    comment_data = {
        "post_id": comment.post_id,
        "content": comment.content,
        "author_id": str(user["_id"]),
        "reactions": {rt: [] for rt in REACTION_TYPES},
        "created_at": datetime.utcnow()
    }
    
    result = await db.comments.insert_one(comment_data)
    
    # Notify post author
    post = await db.posts.find_one({"_id": ObjectId(comment.post_id)})
    if post and post["author_id"] != str(user["_id"]):
        await db.notifications.insert_one({
            "user_id": post["author_id"],
            "type": "comment",
            "from_user_id": str(user["_id"]),
            "post_id": comment.post_id,
            "message": f"{user.get('username', 'Someone')} commented on your post",
            "read": False,
            "created_at": datetime.utcnow()
        })
    
    return {
        "id": str(result.inserted_id),
        "message": "Comment added"
    }


@router.post("/comments/{comment_id}/react", response_model=dict)
async def react_to_comment(comment_id: str, reaction_type: str, user = Depends(get_current_user)):
    """Add reaction to a comment"""
    if reaction_type not in REACTION_TYPES:
        raise HTTPException(status_code=400, detail="Invalid reaction")
    
    comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    user_id = str(user["_id"])
    reactions = comment.get("reactions", {rt: [] for rt in REACTION_TYPES})
    
    # Remove user from all reaction types first
    for rt in REACTION_TYPES:
        if user_id in reactions.get(rt, []):
            reactions[rt].remove(user_id)
    
    # Add to new reaction type
    if reaction_type not in reactions:
        reactions[reaction_type] = []
    reactions[reaction_type].append(user_id)
    
    await db.comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"reactions": reactions}}
    )
    
    return {"success": True, "reaction": reaction_type}


@router.delete("/comments/{comment_id}", response_model=dict)
async def delete_comment(comment_id: str, user = Depends(get_current_user)):
    """Delete a comment"""
    comment = await db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment["author_id"] != str(user["_id"]) and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.comments.delete_one({"_id": ObjectId(comment_id)})
    
    return {"success": True, "message": "Comment deleted"}


# ==================== FEED ====================

@router.get("/feed", response_model=dict)
async def get_feed(user = Depends(get_current_user)):
    """Get personalized feed for user"""
    user_id = str(user["_id"])
    
    # Get user's friends
    friendships = await db.friendships.find({
        "status": "accepted",
        "$or": [{"user_id": user_id}, {"friend_id": user_id}]
    }).to_list(500)
    
    friend_ids = []
    for f in friendships:
        friend_ids.append(f["friend_id"] if f["user_id"] == user_id else f["user_id"])
    
    # Get groups user is member of
    groups = await db.groups.find({"members": user_id}).to_list(100)
    group_ids = [str(g["_id"]) for g in groups]
    
    # Get pages user follows
    pages = await db.pages.find({"followers": user_id}).to_list(100)
    page_ids = [str(p["_id"]) for p in pages]
    
    # Build feed query
    query = {
        "$or": [
            {"author_id": {"$in": friend_ids + [user_id]}},
            {"group_id": {"$in": group_ids}},
            {"page_id": {"$in": page_ids}}
        ]
    }
    
    posts = await db.posts.find(query).sort("created_at", -1).limit(50).to_list(50)
    
    formatted = []
    for p in posts:
        author = await db.users.find_one({"_id": ObjectId(p["author_id"])})
        comment_count = await db.comments.count_documents({"post_id": str(p["_id"])})
        
        reactions = p.get("reactions", {})
        reaction_counts = {rt: len(reactions.get(rt, [])) for rt in REACTION_TYPES}
        
        user_reaction = None
        for rt in REACTION_TYPES:
            if user_id in reactions.get(rt, []):
                user_reaction = rt
                break
        
        # Get group/page name if applicable
        context_name = None
        if p.get("group_id"):
            group = await db.groups.find_one({"_id": ObjectId(p["group_id"])})
            context_name = f"in {group['name']}" if group else None
        elif p.get("page_id"):
            page = await db.pages.find_one({"_id": ObjectId(p["page_id"])})
            context_name = f"on {page['name']}" if page else None
        
        formatted.append({
            "id": str(p["_id"]),
            "content": p["content"],
            "photos": p.get("photos", []),
            "author_id": p["author_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "author_avatar": author.get("avatar_url") if author else None,
            "context": context_name,
            "group_id": p.get("group_id"),
            "page_id": p.get("page_id"),
            "reaction_counts": reaction_counts,
            "total_reactions": sum(reaction_counts.values()),
            "user_reaction": user_reaction,
            "comment_count": comment_count,
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {"posts": formatted}
