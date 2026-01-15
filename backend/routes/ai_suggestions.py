"""
InfoPilot Explorer - AI-Powered Protocol Suggestions
Uses GPT-5.2 to analyze user search history and suggest popular protocols
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel
import os

from config import db, logger
from routes.auth import get_current_user

# Initialize emergentintegrations for GPT-5.2
from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter(tags=["AI Suggestions"])

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


class ProtocolSuggestion(BaseModel):
    protocol_id: str
    title: str
    description: str
    match_score: float
    reason: str
    price: float
    creator: str
    category: str


async def get_user_search_context(user_id: str, limit: int = 20) -> dict:
    """Get user's recent search history and category usage"""
    # Get recent searches
    recent_searches = await db.search_results.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get user's categories
    user_categories = await db.categories.find(
        {"user_id": user_id}
    ).to_list(100)
    
    # Get user's purchase history
    purchases = await db.purchases.find(
        {"user_id": user_id}
    ).to_list(50)
    
    purchased_protocol_ids = [p.get("protocol_id") for p in purchases]
    
    # Extract search terms and patterns
    search_terms = []
    search_locations = []
    
    for search in recent_searches:
        if search.get("title"):
            search_terms.append(search["title"])
        if search.get("location"):
            search_locations.append(search["location"])
    
    # Get category names
    category_names = [c.get("name", "") for c in user_categories]
    category_protocols = [c.get("protocol", "")[:200] for c in user_categories if c.get("protocol")]
    
    return {
        "search_terms": search_terms[:15],
        "search_locations": list(set(search_locations))[:10],
        "category_names": category_names,
        "category_protocols": category_protocols[:5],
        "purchased_ids": purchased_protocol_ids
    }


async def get_popular_protocols(exclude_ids: List[str] = [], limit: int = 20) -> List[dict]:
    """Get popular marketplace protocols"""
    # Aggregate protocols with sales/copy data
    pipeline = [
        {"$match": {"is_marketplace": True}},
        {"$lookup": {
            "from": "purchases",
            "localField": "_id",
            "foreignField": "protocol_id",
            "as": "sales"
        }},
        {"$lookup": {
            "from": "protocol_copies",
            "localField": "_id",
            "foreignField": "protocol_id",
            "as": "copies"
        }},
        {"$addFields": {
            "popularity_score": {
                "$add": [
                    {"$multiply": [{"$size": "$sales"}, 2]},
                    {"$size": "$copies"}
                ]
            }
        }},
        {"$sort": {"popularity_score": -1}},
        {"$limit": limit * 2}  # Get more to filter
    ]
    
    protocols = await db.categories.aggregate(pipeline).to_list(limit * 2)
    
    # Filter out already purchased
    filtered = []
    for p in protocols:
        pid = str(p.get("_id"))
        if pid not in exclude_ids:
            filtered.append(p)
            if len(filtered) >= limit:
                break
    
    return filtered


@router.get("/ai/suggestions", response_model=dict)
async def get_ai_protocol_suggestions(
    limit: int = 5,
    user = Depends(get_current_user)
):
    """Get AI-powered protocol suggestions based on user's search history"""
    user_id = str(user["_id"])
    
    if not EMERGENT_LLM_KEY:
        logger.warning("EMERGENT_LLM_KEY not configured for AI suggestions")
        # Return basic suggestions without AI
        return await get_fallback_suggestions(user_id, limit)
    
    try:
        # Get user context
        context = await get_user_search_context(user_id)
        
        # Get popular protocols
        popular_protocols = await get_popular_protocols(
            exclude_ids=context["purchased_ids"],
            limit=15
        )
        
        if not popular_protocols:
            return {
                "suggestions": [],
                "message": "No protocols available in marketplace yet",
                "ai_powered": False
            }
        
        # Prepare protocol data for AI
        protocol_summaries = []
        for i, p in enumerate(popular_protocols):
            creator = await db.users.find_one({"_id": ObjectId(p.get("user_id", ""))})
            creator_name = creator.get("username", "Unknown") if creator else "Unknown"
            
            protocol_summaries.append({
                "index": i,
                "id": str(p["_id"]),
                "title": p.get("name", ""),
                "protocol_snippet": (p.get("protocol", "") or "")[:300],
                "price": p.get("price", 0),
                "creator": creator_name,
                "popularity": p.get("popularity_score", 0)
            })
        
        # Build AI prompt
        user_profile = f"""
User Search Interests:
- Recent search terms: {', '.join(context['search_terms'][:10]) or 'None'}
- Search locations: {', '.join(context['search_locations'][:5]) or 'Various'}
- Categories created: {', '.join(context['category_names'][:5]) or 'None'}
"""
        
        protocols_text = "\n".join([
            f"{p['index']}. '{p['title']}' by {p['creator']} (${p['price']:.2f}) - Snippet: {p['protocol_snippet'][:150]}..."
            for p in protocol_summaries
        ])
        
        ai_prompt = f"""Based on this user's search history and interests, recommend the top {limit} most relevant protocols from the marketplace.

{user_profile}

Available Protocols:
{protocols_text}

Return ONLY a JSON array of recommendations in this exact format (no other text):
[
  {{"index": 0, "reason": "Brief explanation why this matches user interests", "match_score": 0.95}},
  ...
]

Consider:
1. How well protocol topics match user's search history
2. How protocol purposes align with user's categories
3. Overall value and popularity
4. Avoid protocols similar to what user already has

Return exactly {limit} recommendations, sorted by relevance."""

        # Call GPT-5.2
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ai_suggestions_{user_id}_{datetime.now().timestamp()}",
            system_message="You are an expert at analyzing search patterns and matching users with relevant marketplace protocols. Return only valid JSON."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=ai_prompt))
        
        # Parse AI response
        import json
        try:
            # Clean response - extract JSON array
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            recommendations = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {response[:200]}")
            return await get_fallback_suggestions(user_id, limit)
        
        # Build final suggestions
        suggestions = []
        for rec in recommendations[:limit]:
            idx = rec.get("index", 0)
            if idx < len(protocol_summaries):
                p = protocol_summaries[idx]
                protocol_doc = popular_protocols[idx]
                
                suggestions.append({
                    "protocol_id": p["id"],
                    "title": p["title"],
                    "description": (protocol_doc.get("protocol", "") or "")[:200],
                    "match_score": rec.get("match_score", 0.8),
                    "reason": rec.get("reason", "Popular protocol"),
                    "price": p["price"],
                    "creator": p["creator"],
                    "category": protocol_doc.get("name", "General"),
                    "popularity": p["popularity"]
                })
        
        return {
            "suggestions": suggestions,
            "message": f"Found {len(suggestions)} personalized recommendations",
            "ai_powered": True
        }
        
    except Exception as e:
        logger.error(f"AI suggestions error: {e}")
        return await get_fallback_suggestions(user_id, limit)


async def get_fallback_suggestions(user_id: str, limit: int = 5) -> dict:
    """Return non-AI suggestions based on popularity"""
    # Get user's purchased protocols
    purchases = await db.purchases.find({"user_id": user_id}).to_list(100)
    purchased_ids = [p.get("protocol_id") for p in purchases]
    
    # Get popular protocols
    protocols = await get_popular_protocols(exclude_ids=purchased_ids, limit=limit)
    
    suggestions = []
    for p in protocols:
        creator = await db.users.find_one({"_id": ObjectId(p.get("user_id", ""))})
        creator_name = creator.get("username", "Unknown") if creator else "Unknown"
        
        suggestions.append({
            "protocol_id": str(p["_id"]),
            "title": p.get("name", ""),
            "description": (p.get("protocol", "") or "")[:200],
            "match_score": 0.7,
            "reason": "Popular in marketplace",
            "price": p.get("price", 0),
            "creator": creator_name,
            "category": p.get("name", "General"),
            "popularity": p.get("popularity_score", 0)
        })
    
    return {
        "suggestions": suggestions,
        "message": "Showing popular protocols",
        "ai_powered": False
    }


@router.get("/ai/suggestions/refresh", response_model=dict)
async def refresh_suggestions(user = Depends(get_current_user)):
    """Force refresh AI suggestions (bypasses cache)"""
    return await get_ai_protocol_suggestions(limit=5, user=user)
