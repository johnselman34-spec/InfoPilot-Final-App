"""
Search Router - InfoPilot Explorer
Handles search collation, results retrieval, and protocol matching
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import os
import re
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])

# Database connection - imported from main server
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_explorer')]


class SearchAggregation(str, Enum):
    AND_OR = "and_or"
    AND = "and"
    OR = "or"


class ProtocolParser:
    """InfoJet 2.0 Protocol Language Parser"""
    
    @staticmethod
    def parse_protocol(protocol: str) -> Dict:
        """Parse a protocol string into structured search terms"""
        protocol = re.sub(r'\band\b', '&', protocol, flags=re.IGNORECASE)
        groups = [g.strip() for g in protocol.split('&') if g.strip()]
        
        result = {
            "include_groups": [],
            "exclude_groups": [],
            "all_terms": []
        }
        
        for group in groups:
            is_exclude = False
            is_include = False
            
            if group.startswith('^') or group.endswith('^'):
                is_exclude = True
                group = group.replace('^', '').strip()
            elif group.startswith('+') or group.endswith('+'):
                is_include = True
                group = group.replace('+', '').strip()
            
            match = re.search(r'\(([^)]+)\)', group)
            if match:
                terms_str = match.group(1)
                terms = [t.strip() for t in terms_str.split(' or ')]
                
                if is_exclude:
                    result["exclude_groups"].append(terms)
                else:
                    result["include_groups"].append(terms)
                    result["all_terms"].extend(terms)
        
        return result
    
    @staticmethod
    def matches_protocol(text: str, protocol: str) -> bool:
        """Check if text matches the given protocol"""
        if not text or not protocol:
            return False
            
        text_lower = text.lower()
        parsed = ProtocolParser.parse_protocol(protocol)
        
        for exclude_group in parsed["exclude_groups"]:
            for term in exclude_group:
                if term.lower() in text_lower:
                    return False
        
        for include_group in parsed["include_groups"]:
            group_matched = False
            for term in include_group:
                if term.lower() in text_lower:
                    group_matched = True
                    break
            if not group_matched:
                return False
        
        return True


@router.get("/results")
async def get_search_results(
    category_ids: Optional[str] = None,
    document_type: Optional[str] = None,
    aggregation: SearchAggregation = SearchAggregation.AND_OR,
    year: Optional[int] = None,
    root_domain: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user_id: str = None  # Will be injected by auth
):
    """Get search results with filters"""
    query: Dict[str, Any] = {"user_id": user_id}
    
    if category_ids:
        cat_list = category_ids.split(",")
        if aggregation == SearchAggregation.AND:
            query["category_ids"] = {"$all": cat_list}
        elif aggregation == SearchAggregation.OR:
            query["category_ids"] = {"$in": cat_list}
        else:
            query["category_ids"] = {"$in": cat_list}
    
    if document_type:
        query["document_type"] = document_type
    
    if year:
        query["year"] = year
    
    if root_domain:
        query["root_domain"] = {"$regex": root_domain, "$options": "i"}
    
    if country:
        query["locations.country"] = country
    
    if state:
        query["locations.state"] = state
    
    skip = (page - 1) * limit
    
    results = await db.search_results.find(
        query,
        {"_id": 0}
    ).sort("collated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.search_results.count_documents(query)
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/results/{result_id}")
async def get_result_detail(result_id: str, user_id: str = None):
    """Get a single search result by ID"""
    result = await db.search_results.find_one(
        {"result_id": result_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return result


@router.delete("/results/{result_id}")
async def delete_result(result_id: str, user_id: str = None):
    """Delete a search result"""
    result = await db.search_results.delete_one({
        "result_id": result_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {"message": "Result deleted"}


@router.post("/clean-category")
async def clean_category(request: Request, user_id: str = None):
    """Remove all results from a category"""
    data = await request.json()
    category_id = data.get("category_id")
    
    if not category_id:
        raise HTTPException(status_code=400, detail="Category ID required")
    
    result = await db.search_results.update_many(
        {"user_id": user_id, "category_ids": category_id},
        {"$pull": {"category_ids": category_id}}
    )
    
    deleted = await db.search_results.delete_many({
        "user_id": user_id,
        "category_ids": {"$size": 0}
    })
    
    return {
        "message": f"Cleaned category. Modified {result.modified_count} results, deleted {deleted.deleted_count} orphans"
    }
