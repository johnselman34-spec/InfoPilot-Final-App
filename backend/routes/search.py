"""
InfoPilot Explorer - Search Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

from config import db, logger
from models.schemas import SearchRequest, CollateRequest
from routes.auth import get_current_user, get_optional_user
from services.search_service import WebSearchService
from services.protocol_service import ProtocolParser

router = APIRouter(tags=["Search"])


@router.post("/search/web", response_model=dict)
async def web_search(request: SearchRequest, user = Depends(get_current_user)):
    """Perform a web search"""
    # Get max search pages from admin settings
    settings = await db.settings.find_one({"key": "max_search_pages"})
    max_pages = settings.get("value", 99) if settings else 99
    
    # Calculate results based on max pages
    max_results = max_pages * 20
    
    results = await WebSearchService.search(request.query, min(max_results, 200))
    
    # Format and classify results
    formatted = []
    for r in results:
        formatted.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("snippet", ""),
            "article_type": WebSearchService.classify_article_type(
                r.get("url", ""), r.get("title", ""), r.get("content", "")
            ),
            "root_domain": WebSearchService.extract_root_domain(r.get("url", ""))
        })
    
    return {"results": formatted, "count": len(formatted)}


@router.post("/ultimate-search/collate", response_model=dict)
async def collate_search(request: CollateRequest, user = Depends(get_current_user)):
    """Search and collate results based on category protocol"""
    # Get category
    category = await db.categories.find_one({"_id": ObjectId(request.category_id)})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Parse protocol
    groups = ProtocolParser.parse_protocol(category["protocol"])
    if not groups:
        raise HTTPException(status_code=400, detail="Invalid protocol")
    
    # Extract search query from protocol
    search_query = ProtocolParser.extract_search_query(category["protocol"])
    
    # Get max pages setting
    settings = await db.settings.find_one({"key": "max_search_pages"})
    max_pages = settings.get("value", 99) if settings else 99
    max_results = max_pages * 20
    
    # Perform search
    raw_results = await WebSearchService.search(search_query, min(max_results, 200))
    
    # Match results against protocol
    matched_results = []
    for result in raw_results:
        matches, score = ProtocolParser.match_result(result, groups)
        if matches:
            result["match_score"] = score
            result["article_type"] = WebSearchService.classify_article_type(
                result.get("url", ""), result.get("title", ""), result.get("content", "")
            )
            result["root_domain"] = WebSearchService.extract_root_domain(result.get("url", ""))
            matched_results.append(result)
    
    # Sort by match score
    matched_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Store results
    for result in matched_results:
        existing = await db.search_results.find_one({
            "url": result["url"],
            "user_id": str(user["_id"])
        })
        
        if existing:
            # Add category to existing result
            await db.search_results.update_one(
                {"_id": existing["_id"]},
                {"$addToSet": {"category_ids": request.category_id}}
            )
        else:
            # Create new result
            await db.search_results.insert_one({
                "url": result["url"],
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "content": result.get("content", ""),
                "article_type": result.get("article_type", "Unknown"),
                "root_domain": result.get("root_domain", ""),
                "match_score": result.get("match_score", 0),
                "category_ids": [request.category_id],
                "user_id": str(user["_id"]),
                "created_at": datetime.utcnow()
            })
    
    # Update category last_collated
    await db.categories.update_one(
        {"_id": ObjectId(request.category_id)},
        {"$set": {"last_collated": datetime.utcnow()}}
    )
    
    # Format response
    formatted = []
    for r in matched_results:
        formatted.append({
            "id": str(ObjectId()),
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "article_type": r.get("article_type", "Unknown"),
            "root_domain": r.get("root_domain", ""),
            "match_score": r.get("match_score", 0),
            "categories": [category["name"]]
        })
    
    return {
        "results": formatted,
        "total": len(formatted),
        "category": category["name"],
        "protocol_groups": len(groups)
    }


@router.get("/ultimate-search", response_model=dict)
async def get_search_results(
    limit: int = Query(100, ge=1, le=500),
    user = Depends(get_optional_user)
):
    """Get stored search results for map and display"""
    query = {}
    if user:
        query["user_id"] = str(user["_id"])
    
    results = await db.search_results.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Collect all unique category IDs for bulk fetch (N+1 query optimization)
    all_category_ids = set()
    for r in results:
        for cat_id in r.get("category_ids", []):
            try:
                all_category_ids.add(ObjectId(cat_id))
            except:
                pass
    
    # Bulk fetch all categories at once
    categories_map = {}
    if all_category_ids:
        categories_cursor = db.categories.find({"_id": {"$in": list(all_category_ids)}})
        async for cat in categories_cursor:
            categories_map[str(cat["_id"])] = cat["name"]
    
    formatted = []
    for r in results:
        # Get category names from pre-fetched map
        category_names = []
        for cat_id in r.get("category_ids", []):
            cat_name = categories_map.get(str(cat_id))
            if cat_name:
                category_names.append(cat_name)
        
        formatted.append({
            "id": str(r["_id"]),
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "article_type": r.get("article_type", "Unknown"),
            "root_domain": r.get("root_domain", ""),
            "categories": category_names,
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude")
        })
    
    return {"results": formatted, "count": len(formatted)}


@router.post("/search/reaction", response_model=dict)
async def add_reaction(reaction_data: dict, user = Depends(get_current_user)):
    """Add a reaction to a search result"""
    result_id = reaction_data.get("result_id")
    reaction_type = reaction_data.get("reaction")
    
    if not result_id or not reaction_type:
        raise HTTPException(status_code=400, detail="Missing result_id or reaction")
    
    await db.reactions.update_one(
        {"result_id": result_id, "user_id": str(user["_id"])},
        {"$set": {"reaction": reaction_type, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    
    return {"success": True}
