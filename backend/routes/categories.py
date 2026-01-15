"""
InfoPilot Explorer - Categories Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List
from bson import ObjectId

from config import db, logger
from models.schemas import CategoryCreate, CategoryUpdate
from routes.auth import get_current_user
from services.protocol_service import ProtocolParser

router = APIRouter(tags=["Categories"])


async def format_category_with_count(cat: dict, user_id: str = None) -> dict:
    """Format category for API response with result count"""
    cat_id = str(cat["_id"])
    
    # Count search results in this category
    result_count = await db.search_results.count_documents({
        "category_ids": cat_id
    })
    
    # Count subcategories
    subcategory_count = await db.categories.count_documents({
        "parent_id": cat_id
    })
    
    return {
        "id": cat_id,
        "name": cat["name"],
        "protocol": cat["protocol"],
        "user_id": cat["user_id"],
        "parent_id": cat.get("parent_id"),
        "is_public": cat.get("is_public", False),
        "price": cat.get("price"),
        "level": cat.get("level", 0),
        "result_count": result_count,
        "subcategory_count": subcategory_count,
        "created_at": cat.get("created_at", datetime.utcnow()).isoformat()
    }


def format_category(cat: dict) -> dict:
    """Format category for API response (sync version without count)"""
    return {
        "id": str(cat["_id"]),
        "name": cat["name"],
        "protocol": cat["protocol"],
        "user_id": cat["user_id"],
        "parent_id": cat.get("parent_id"),
        "is_public": cat.get("is_public", False),
        "price": cat.get("price"),
        "level": cat.get("level", 0),
        "created_at": cat.get("created_at", datetime.utcnow()).isoformat()
    }


@router.get("/categories", response_model=List[dict])
async def get_categories(user = Depends(get_current_user), include_counts: bool = True):
    """Get all categories for the current user with result counts"""
    categories = await db.categories.find({
        "$or": [
            {"user_id": str(user["_id"])},
            {"is_public": True}
        ]
    }).to_list(1000)
    
    if include_counts:
        return [await format_category_with_count(cat, str(user["_id"])) for cat in categories]
    else:
        return [format_category(cat) for cat in categories]


@router.post("/categories", response_model=dict)
async def create_category(category: CategoryCreate, user = Depends(get_current_user)):
    """Create a new category"""
    # Validate protocol
    is_valid, message = ProtocolParser.validate_protocol(category.protocol)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid protocol format. {message}")
    
    # Calculate level
    level = 0
    if category.parent_id:
        parent = await db.categories.find_one({"_id": ObjectId(category.parent_id)})
        if parent:
            level = parent.get("level", 0) + 1
    
    cat_data = {
        "name": category.name,
        "protocol": category.protocol,
        "user_id": str(user["_id"]),
        "parent_id": category.parent_id,
        "is_public": category.is_public,
        "level": level,
        "created_at": datetime.utcnow()
    }
    
    result = await db.categories.insert_one(cat_data)
    cat_data["_id"] = result.inserted_id
    
    return format_category(cat_data)


@router.put("/categories/{category_id}", response_model=dict)
async def update_category(category_id: str, update: CategoryUpdate, user = Depends(get_current_user)):
    """Update a category"""
    # Admin can edit any category, regular users can only edit their own
    if user.get("is_admin"):
        category = await db.categories.find_one({"_id": ObjectId(category_id)})
    else:
        category = await db.categories.find_one({
            "_id": ObjectId(category_id),
            "user_id": str(user["_id"])
        })
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.protocol is not None:
        is_valid, message = ProtocolParser.validate_protocol(update.protocol)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid protocol format. {message}")
        update_data["protocol"] = update.protocol
    if update.is_public is not None:
        update_data["is_public"] = update.is_public
    if update.price is not None:
        # Validate price range ($0-$99)
        if update.price < 0 or update.price > 99:
            raise HTTPException(status_code=400, detail="Price must be between $0 and $99")
        update_data["price"] = update.price
    
    if update_data:
        await db.categories.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": update_data}
        )
    
    updated = await db.categories.find_one({"_id": ObjectId(category_id)})
    return format_category(updated)


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user = Depends(get_current_user)):
    """Delete a category and its children"""
    # Admin can delete any category, regular users can only delete their own
    if user.get("is_admin"):
        category = await db.categories.find_one({"_id": ObjectId(category_id)})
    else:
        category = await db.categories.find_one({
            "_id": ObjectId(category_id),
            "user_id": str(user["_id"])
        })
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Delete children recursively
    async def delete_children(parent_id: str):
        children = await db.categories.find({"parent_id": parent_id}).to_list(1000)
        for child in children:
            await delete_children(str(child["_id"]))
            await db.categories.delete_one({"_id": child["_id"]})
    
    await delete_children(category_id)
    await db.categories.delete_one({"_id": ObjectId(category_id)})
    
    return {"message": "Category deleted"}


@router.post("/protocol/validate", response_model=dict)
async def validate_protocol(request: dict):
    """Validate a protocol string"""
    protocol = request.get("protocol", "")
    return ProtocolParser.debug_protocol(protocol)
