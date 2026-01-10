"""Search and Ultimate Search routes"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

from utils.database import db
from utils.auth import require_user, get_current_user
from services.protocol_parser import InfoPilot2Parser

router = APIRouter(tags=["Search"])

# ============================================
# PYDANTIC MODELS
# ============================================

class UltimateSearchRequest(BaseModel):
    category_ids: List[str] = []
    aggregation_type: str = "and_or"
    document_types: List[str] = []
    article_types: List[str] = []
    domains: List[str] = []
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    keyword: Optional[str] = None
    ai_query: Optional[str] = None
    page: int = 1

class SearchResultDeleteRequest(BaseModel):
    result_ids: List[str]

# ============================================
# SEARCH ROUTES
# ============================================

@router.get("/ultimate-search/user-stats")
async def get_user_search_stats(user: dict = Depends(require_user)):
    """Get user's search result statistics"""
    total_results = await db.search_results.count_documents({"user_id": user["id"]})
    
    # Get settings for limit
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    max_limit = settings.get("user_max_results_limit", 4000) if settings else 4000
    
    return {
        "total_results": total_results,
        "max_limit": max_limit,
        "usage_percentage": round((total_results / max_limit) * 100, 1) if max_limit > 0 else 0,
        "remaining": max(0, max_limit - total_results)
    }

@router.get("/ultimate-search/sessions")
async def get_search_sessions(user: dict = Depends(require_user)):
    """Get user's collation sessions"""
    # Group results by collated_at timestamp (rounded to minute for grouping)
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$addFields": {
            "session_key": {"$substr": ["$collated_at", 0, 16]}  # YYYY-MM-DDTHH:MM
        }},
        {"$group": {
            "_id": "$session_key",
            "count": {"$sum": 1},
            "first_result": {"$first": "$$ROOT"}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 50}
    ]
    
    sessions = await db.search_results.aggregate(pipeline).to_list(50)
    
    return {
        "sessions": [
            {
                "timestamp": s["_id"],
                "result_count": s["count"],
                "sample_title": s["first_result"].get("title", "Unknown")[:50]
            }
            for s in sessions
        ]
    }

@router.delete("/ultimate-search/session/{timestamp}")
async def delete_collation_session(timestamp: str, user: dict = Depends(require_user)):
    """Delete all results from a specific collation session"""
    # Match results that start with the given timestamp
    result = await db.search_results.delete_many({
        "user_id": user["id"],
        "collated_at": {"$regex": f"^{timestamp}"}
    })
    
    return {
        "message": f"Deleted {result.deleted_count} results from session",
        "deleted_count": result.deleted_count
    }

@router.delete("/ultimate-search/clear-all")
async def clear_all_results(user: dict = Depends(require_user)):
    """Clear all search results for the current user"""
    result = await db.search_results.delete_many({"user_id": user["id"]})
    return {
        "message": f"Cleared all {result.deleted_count} results",
        "deleted_count": result.deleted_count
    }

@router.delete("/ultimate-search/category/{category_id}/clear")
async def clear_category_results(category_id: str, user: dict = Depends(require_user)):
    """Clear all results in a specific category and its subcategories"""
    # Get all subcategory IDs recursively
    async def get_all_subcategory_ids(parent_id: str) -> List[str]:
        ids = [parent_id]
        children = await db.categories.find(
            {"parent_id": parent_id, "user_id": user["id"]},
            {"_id": 0, "id": 1}
        ).to_list(100)
        
        for child in children:
            child_ids = await get_all_subcategory_ids(child["id"])
            ids.extend(child_ids)
        
        return ids
    
    all_category_ids = await get_all_subcategory_ids(category_id)
    
    # Delete results matching any of these categories
    result = await db.search_results.delete_many({
        "user_id": user["id"],
        "categories": {"$in": all_category_ids}
    })
    
    return {
        "message": f"Cleared {result.deleted_count} results from category and subcategories",
        "deleted_count": result.deleted_count,
        "categories_affected": len(all_category_ids)
    }

@router.get("/ultimate-search/category/{category_id}/results")
async def get_category_results(
    category_id: str,
    page: int = 1,
    user: dict = Depends(require_user)
):
    """Get results filtered by a specific category"""
    per_page = 20
    skip = (page - 1) * per_page
    
    # Get all subcategory IDs recursively
    async def get_all_subcategory_ids(parent_id: str) -> List[str]:
        ids = [parent_id]
        children = await db.categories.find(
            {"parent_id": parent_id, "user_id": user["id"]},
            {"_id": 0, "id": 1}
        ).to_list(100)
        
        for child in children:
            child_ids = await get_all_subcategory_ids(child["id"])
            ids.extend(child_ids)
        
        return ids
    
    all_category_ids = await get_all_subcategory_ids(category_id)
    
    query = {
        "user_id": user["id"],
        "categories": {"$in": all_category_ids}
    }
    
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query, {"_id": 0}).sort("collated_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    # Get category names
    category_ids_in_results = set()
    for r in results:
        category_ids_in_results.update(r.get("categories", []))
    
    categories = await db.categories.find(
        {"id": {"$in": list(category_ids_in_results)}},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(100)
    category_map = {c["id"]: c["name"] for c in categories}
    
    # Add category names to results
    for r in results:
        r["category_names"] = [category_map.get(cid, "Unknown") for cid in r.get("categories", [])]
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page
    }

@router.delete("/results/{result_id}")
async def delete_result(result_id: str, user: dict = Depends(require_user)):
    """Delete a single search result"""
    result = await db.search_results.delete_one({
        "id": result_id,
        "user_id": user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {"message": "Result deleted"}

@router.delete("/results/batch")
async def delete_results_batch(data: SearchResultDeleteRequest, user: dict = Depends(require_user)):
    """Delete multiple search results"""
    result = await db.search_results.delete_many({
        "id": {"$in": data.result_ids},
        "user_id": user["id"]
    })
    
    return {
        "message": f"Deleted {result.deleted_count} results",
        "deleted_count": result.deleted_count
    }
