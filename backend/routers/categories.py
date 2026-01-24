"""
Categories routes for InfoPilot Explorer
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid

from services.database import db
from models.schemas import User, CategoryCreate, CategoryUpdate
from routers.auth import require_auth

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
async def get_categories(
    user_id: Optional[str] = None,
    public_only: bool = False,
    request: Request = None
):
    """Get categories"""
    query = {}
    
    if user_id:
        query["user_id"] = user_id
    elif public_only:
        query["is_public"] = True
    
    categories = await db.categories.find(query, {"_id": 0}).to_list(1000)
    return {"categories": categories}


@router.post("")
async def create_category(
    category: CategoryCreate,
    user: User = Depends(require_auth)
):
    """Create a new category"""
    # Validate protocol syntax
    if not category.protocol:
        raise HTTPException(status_code=400, detail="Protocol required")
    
    # Check for banned words
    banned = await db.settings.find_one({"key": "banned_words"}, {"_id": 0})
    banned_words = banned.get("value", []) if banned else []
    
    for word in banned_words:
        if word.lower() in category.name.lower() or word.lower() in category.protocol.lower():
            raise HTTPException(status_code=400, detail=f"Content contains banned word: {word}")
    
    cat_dict = category.model_dump()
    cat_dict["category_id"] = f"cat_{uuid.uuid4().hex[:12]}"
    cat_dict["user_id"] = user.user_id
    cat_dict["sales_count"] = 0
    cat_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    cat_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.categories.insert_one(cat_dict)
    
    # Add XP for creating category
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"xp": 10}}
    )
    
    # Return without the MongoDB _id
    cat_dict.pop("_id", None)
    return cat_dict


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    update: CategoryUpdate,
    user: User = Depends(require_auth)
):
    """Update a category"""
    category = await db.categories.find_one(
        {"category_id": category_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.categories.update_one(
        {"category_id": category_id},
        {"$set": update_dict}
    )
    
    updated = await db.categories.find_one({"category_id": category_id}, {"_id": 0})
    return updated


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Delete a category"""
    result = await db.categories.delete_one({
        "category_id": category_id,
        "user_id": user.user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted"}


@router.post("/{category_id}/clean")
async def clean_category(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Delete all search results for a category"""
    result = await db.search_results.delete_many({
        "user_id": user.user_id,
        "category_ids": category_id
    })
    
    return {"message": f"Deleted {result.deleted_count} results"}
