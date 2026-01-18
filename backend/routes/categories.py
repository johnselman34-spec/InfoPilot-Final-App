"""
InfoPilot Explorer - Categories Routes
Category CRUD and protocol management
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

from models.schemas import CategoryCreate, Category
from utils.db import db
from utils.auth import require_user

router = APIRouter(prefix="/categories", tags=["Categories"])

# Maximum price allowed in marketplace
MAX_PROTOCOL_PRICE = 24.99


@router.post("")
async def create_category(category_data: CategoryCreate, user: Dict = Depends(require_user)):
    """Create a new category with InfoJet 2.0 protocol."""
    # Validate price doesn't exceed maximum
    if category_data.price is not None and category_data.price > MAX_PROTOCOL_PRICE:
        raise HTTPException(
            status_code=400, 
            detail=f"Price cannot exceed ${MAX_PROTOCOL_PRICE}. Maximum allowed price is $24.99"
        )
    
    category = Category(
        user_id=user["id"],
        name=category_data.name,
        protocol=category_data.protocol,
        parent_id=category_data.parent_id,
        is_public=category_data.is_public,
        price=category_data.price
    )
    category_dict = category.model_dump()
    category_dict["created_at"] = category_dict["created_at"].isoformat()
    
    await db.categories.insert_one(category_dict)
    return {k: v for k, v in category_dict.items() if k != "_id"}


@router.get("")
async def get_categories(user: Dict = Depends(require_user)):
    """Get user's categories."""
    categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    return {"categories": categories}


@router.get("/{category_id}")
async def get_category(category_id: str, user: Dict = Depends(require_user)):
    """Get a specific category."""
    category = await db.categories.find_one({"id": category_id, "user_id": user["id"]}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}")
async def update_category(category_id: str, updates: Dict = Body(...), user: Dict = Depends(require_user)):
    """Update a category (Save Protocol)."""
    category = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    allowed = ["name", "protocol", "is_public", "price", "parent_id"]
    filtered = {k: v for k, v in updates.items() if k in allowed}
    
    if filtered:
        await db.categories.update_one({"id": category_id}, {"$set": filtered})
    
    updated = await db.categories.find_one({"id": category_id}, {"_id": 0})
    return updated


@router.delete("/{category_id}")
async def delete_category(category_id: str, user: Dict = Depends(require_user)):
    """Delete a category."""
    result = await db.categories.delete_one({"id": category_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}
