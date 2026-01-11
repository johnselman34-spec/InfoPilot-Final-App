"""
InfoPilot Explorer - Social Routes (Groups & Pages)
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
from bson import ObjectId

from config import db, logger
from models.schemas import GroupCreate, PageCreate, PostCreate, CommentCreate
from routes.auth import get_current_user, get_optional_user

router = APIRouter(tags=["Social"])


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
            "member_count": len(g.get("members", [])),
            "is_member": user and str(user["_id"]) in g.get("members", []),
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
        "created_at": datetime.utcnow()
    }
    
    result = await db.groups.insert_one(group_data)
    
    return {
        "id": str(result.inserted_id),
        "name": group.name,
        "message": "Group created successfully"
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
        {"$pull": {"members": str(user["_id"])}}
    )
    
    return {"success": True, "message": "Left group"}


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
            "follower_count": len(p.get("followers", [])),
            "is_following": user and str(user["_id"]) in p.get("followers", []),
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


# ==================== POSTS ====================

@router.get("/posts", response_model=dict)
async def get_posts(
    group_id: Optional[str] = None,
    page_id: Optional[str] = None,
    user = Depends(get_optional_user)
):
    """Get posts for a group, page, or feed"""
    query = {}
    if group_id:
        query["group_id"] = group_id
    if page_id:
        query["page_id"] = page_id
    
    posts = await db.posts.find(query).sort("created_at", -1).limit(50).to_list(50)
    
    formatted = []
    for p in posts:
        # Get author info
        author = await db.users.find_one({"_id": ObjectId(p["author_id"])})
        
        # Get comment count
        comment_count = await db.comments.count_documents({"post_id": str(p["_id"])})
        
        formatted.append({
            "id": str(p["_id"]),
            "content": p["content"],
            "author_id": p["author_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "group_id": p.get("group_id"),
            "page_id": p.get("page_id"),
            "likes": len(p.get("likes", [])),
            "is_liked": user and str(user["_id"]) in p.get("likes", []),
            "comment_count": comment_count,
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {"posts": formatted}


@router.post("/posts", response_model=dict)
async def create_post(post: PostCreate, user = Depends(get_current_user)):
    """Create a new post"""
    post_data = {
        "content": post.content,
        "author_id": str(user["_id"]),
        "group_id": post.group_id,
        "page_id": post.page_id,
        "likes": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.posts.insert_one(post_data)
    
    return {
        "id": str(result.inserted_id),
        "message": "Post created"
    }


@router.post("/posts/{post_id}/like", response_model=dict)
async def like_post(post_id: str, user = Depends(get_current_user)):
    """Like or unlike a post"""
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user_id = str(user["_id"])
    if user_id in post.get("likes", []):
        # Unlike
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"likes": user_id}}
        )
        return {"liked": False}
    else:
        # Like
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$addToSet": {"likes": user_id}}
        )
        return {"liked": True}


# ==================== COMMENTS ====================

@router.get("/posts/{post_id}/comments", response_model=dict)
async def get_comments(post_id: str, user = Depends(get_optional_user)):
    """Get comments for a post"""
    comments = await db.comments.find({"post_id": post_id}).sort("created_at", 1).to_list(100)
    
    formatted = []
    for c in comments:
        author = await db.users.find_one({"_id": ObjectId(c["author_id"])})
        formatted.append({
            "id": str(c["_id"]),
            "content": c["content"],
            "author_id": c["author_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
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
        "created_at": datetime.utcnow()
    }
    
    result = await db.comments.insert_one(comment_data)
    
    return {
        "id": str(result.inserted_id),
        "message": "Comment added"
    }
