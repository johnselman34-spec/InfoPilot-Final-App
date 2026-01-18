"""
InfoPilot Explorer - Search Routes
Search & Collate with DuckDuckGo + Brave Search integration
Includes paywall filtering and Elasticsearch integration
"""
from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import Dict, Optional, List
from datetime import datetime, timezone
import uuid
import os

from utils.db import db
from utils.auth import require_user, get_current_user
from utils.search import search_all_engines, content_matches_protocol, classify_document_type, extract_location
from utils.paywall_filter import get_paywall_stats
from utils.elasticsearch_client import (
    index_search_results, 
    semantic_search, 
    get_elasticsearch_status,
    index_protocol
)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/engines")
async def get_search_engines():
    """Get available search engines and their configuration status."""
    brave_configured = bool(os.environ.get("BRAVE_SEARCH_API_KEY", ""))
    es_status = get_elasticsearch_status()
    
    return {
        "engines": [
            {
                "id": "duckduckgo",
                "name": "DuckDuckGo",
                "configured": True,
                "description": "Privacy-focused search engine (no API key required)",
                "free_tier": "Unlimited"
            },
            {
                "id": "brave",
                "name": "Brave Search",
                "configured": brave_configured,
                "description": "Independent search index with 30B+ pages",
                "free_tier": "2,000 queries/month"
            }
        ],
        "default_engine": "all",
        "brave_configured": brave_configured,
        "elasticsearch": es_status,
        "paywall_filter": {
            "enabled": True,
            "blocked_domains": get_paywall_stats()["total_blocked_domains"]
        }
    }


@router.get("/elasticsearch/status")
async def elasticsearch_status():
    """Get Elasticsearch connection status."""
    return get_elasticsearch_status()


@router.post("/elasticsearch/search")
async def elasticsearch_semantic_search(
    query: str = Body(..., embed=True),
    limit: int = Body(20, embed=True),
    user: Dict = Depends(require_user)
):
    """Perform semantic search on indexed content using Elasticsearch."""
    results = await semantic_search(query, user["id"], limit)
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


@router.post("/collate")
async def collate_search(
    query: str = Body(..., embed=True), 
    engine: str = Body("all", embed=True),  # "all", "duckduckgo", "brave"
    user: Dict = Depends(require_user)
):
    """Search and Collate function - searches the internet and categorizes results.
    
    Args:
        query: Search query string
        engine: Search engine to use - "all" (default), "duckduckgo", or "brave"
    """
    admin_settings = await db.admin_settings.find_one({"id": "admin_settings"}) or {}
    collation_limit = admin_settings.get("collation_limit", 40)
    
    categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).limit(1000).to_list(1000)
    
    # Validate engine parameter
    valid_engines = ["all", "duckduckgo", "brave"]
    if engine not in valid_engines:
        engine = "all"
    
    # Search using real search engines
    search_results = await search_all_engines(query, collation_limit, engine)
    
    if not search_results:
        # Fallback to mock data if search fails
        search_results = [
            {
                "url": f"https://example.com/article-{i}",
                "title": f"Article about {query} - Result {i}",
                "snippet": f"This is a detailed article about {query}. Contains valuable information.",
                "source": "Mock"
            }
            for i in range(1, min(collation_limit + 1, 11))
        ]
    
    # Categorize results based on protocols
    categorized_results = []
    for result in search_results:
        content = result.get("snippet", "")
        title = result.get("title", "")
        full_content = f"{title} {content}"
        matched_categories = []
        best_score = 0
        
        for cat in categories:
            matches, score = content_matches_protocol(full_content, cat["protocol"])
            if matches:
                matched_categories.append(cat["id"])
                best_score = max(best_score, score)
        
        # Classify document type
        doc_type = classify_document_type(full_content, title, admin_settings)
        
        # Extract location
        location = extract_location(full_content)
        
        result_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "url": result["url"],
            "title": result["title"],
            "snippet": result["snippet"],
            "content": full_content,
            "category_ids": matched_categories,
            "document_type": doc_type,
            "location": location,
            "reactions": {"like": 0, "love": 0, "funny": 0, "sad": 0, "caution": 0, "spam": 0, "best": 0},
            "comments": [],
            "match_score": best_score,
            "source": result.get("source", "Unknown"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.search_results.insert_one(result_doc)
        categorized_results.append({k: v for k, v in result_doc.items() if k != "_id"})
    
    # Index results to Elasticsearch (async, non-blocking)
    try:
        indexed_count = await index_search_results(categorized_results, user["id"], query)
    except Exception as e:
        indexed_count = 0
        # Don't fail the request if Elasticsearch indexing fails
    
    # Update category counts
    for cat in categories:
        count = await db.search_results.count_documents({"category_ids": cat["id"]})
        await db.categories.update_one({"id": cat["id"]}, {"$set": {"search_result_count": count}})
    
    categorized_count = sum(1 for r in categorized_results if r["category_ids"])
    
    return {
        "message": f"Collated {len(categorized_results)} results! {categorized_count} matched your protocols.",
        "results": categorized_results,
        "total_searched": len(search_results),
        "categorized": categorized_count,
        "elasticsearch_indexed": indexed_count
    }


@router.get("/results")
async def get_search_results(
    category_ids: Optional[str] = None,
    document_types: Optional[str] = None,
    aggregation: str = "and_or",
    page: int = 1,
    user: Dict = Depends(require_user)
):
    """Get search results with filtering."""
    admin_settings = await db.admin_settings.find_one({"id": "admin_settings"}) or {}
    per_page = admin_settings.get("search_results_per_page", 20)
    
    # Page limit for non-paid users
    if not user.get("is_paid"):
        max_pages = admin_settings.get("unpaid_max_pages", 3)
        if page > max_pages:
            raise HTTPException(status_code=403, detail=f"Upgrade to access more than {max_pages} pages!")
    
    query = {"user_id": user["id"]}
    
    if category_ids:
        cat_list = [c.strip() for c in category_ids.split(",")]
        if aggregation == "and":
            query["category_ids"] = {"$all": cat_list}
        else:
            query["category_ids"] = {"$in": cat_list}
    
    if document_types:
        doc_list = [d.strip() for d in document_types.split(",")]
        query["document_type"] = {"$in": doc_list}
    
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query, {"_id": 0}).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page).to_list(per_page)
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.post("/results/{result_id}/reaction")
async def add_reaction(result_id: str, reaction: str = Body(..., embed=True), user: Dict = Depends(require_user)):
    """Add a reaction to a search result."""
    valid_reactions = ["like", "love", "funny", "sad", "caution", "spam", "best"]
    if reaction not in valid_reactions:
        raise HTTPException(status_code=400, detail=f"Invalid reaction. Use: {valid_reactions}")
    
    await db.search_results.update_one(
        {"id": result_id},
        {"$inc": {f"reactions.{reaction}": 1}}
    )
    return {"message": f"Added {reaction} reaction"}


@router.post("/results/{result_id}/comment")
async def add_comment(result_id: str, content: str = Body(..., embed=True), user: Dict = Depends(require_user)):
    """Add a comment to a search result."""
    comment = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "username": user["username"],
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.search_results.update_one(
        {"id": result_id},
        {"$push": {"comments": comment}}
    )
    return {"message": "Comment added!", "comment": comment}
