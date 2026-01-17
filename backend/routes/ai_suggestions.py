"""
InfoPilot Explorer - AI-Powered Protocol Suggestions
Uses GPT-5.2 to analyze user search history and suggest popular protocols
"""
from fastapi import APIRouter, HTTPException, Depends, Body
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


# ==================== A/B TESTING FOR AI RECOMMENDATIONS ====================

@router.post("/ai/recommendations/track", response_model=dict)
async def track_recommendation_interaction(
    category: str = Body(...),
    action: str = Body(...),  # 'view', 'copy', 'create', 'purchase'
    recommendation_name: str = Body(None),
    user = Depends(get_current_user)
):
    """
    Track user interactions with AI recommendations for A/B testing.
    This helps determine which recommendation categories are most effective.
    """
    user_id = str(user["_id"])
    
    await db.ai_recommendation_analytics.insert_one({
        "user_id": user_id,
        "category": category,
        "action": action,
        "recommendation_name": recommendation_name,
        "timestamp": datetime.now(timezone.utc)
    })
    
    # Update category performance stats
    await db.ai_recommendation_stats.update_one(
        {"category": category},
        {
            "$inc": {
                f"actions.{action}": 1,
                "total_interactions": 1
            },
            "$setOnInsert": {"category": category, "created_at": datetime.now(timezone.utc)}
        },
        upsert=True
    )
    
    return {"success": True, "tracked": {"category": category, "action": action}}


@router.get("/ai/recommendations/analytics", response_model=dict)
async def get_recommendation_analytics(user = Depends(get_current_user)):
    """
    Get A/B testing analytics for AI recommendation categories.
    Shows which categories are performing best.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get category stats
    stats = await db.ai_recommendation_stats.find().to_list(100)
    
    # Calculate conversion rates
    category_performance = []
    for stat in stats:
        views = stat.get("actions", {}).get("view", 0)
        copies = stat.get("actions", {}).get("copy", 0)
        creates = stat.get("actions", {}).get("create", 0)
        purchases = stat.get("actions", {}).get("purchase", 0)
        
        copy_rate = (copies / views * 100) if views > 0 else 0
        create_rate = (creates / views * 100) if views > 0 else 0
        purchase_rate = (purchases / views * 100) if views > 0 else 0
        
        category_performance.append({
            "category": stat.get("category"),
            "views": views,
            "copies": copies,
            "creates": creates,
            "purchases": purchases,
            "copy_rate": round(copy_rate, 2),
            "create_rate": round(create_rate, 2),
            "purchase_rate": round(purchase_rate, 2),
            "total_interactions": stat.get("total_interactions", 0)
        })
    
    # Sort by effectiveness (purchase rate)
    category_performance.sort(key=lambda x: x["purchase_rate"], reverse=True)
    
    return {
        "categories": category_performance,
        "best_performing": category_performance[0]["category"] if category_performance else "trending",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# ==================== AI-POWERED SMART SEARCH SUGGESTIONS ====================

@router.get("/ai/smart-suggestions", response_model=dict)
async def get_smart_search_suggestions(
    query: str = "",
    user = Depends(get_current_user)
):
    """
    AI-powered smart search suggestions based on user's search patterns and trending topics.
    Predicts what protocols users might want based on their behavior.
    """
    user_id = str(user["_id"])
    
    if not EMERGENT_LLM_KEY:
        return {"suggestions": get_fallback_smart_suggestions(query), "ai_powered": False}
    
    try:
        # Get user's search history
        user_searches = await db.search_history.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(20).to_list(20)
        
        recent_queries = [s.get("query", "") for s in user_searches if s.get("query")]
        
        # Get trending searches
        trending = await db.search_history.aggregate([
            {"$match": {"timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}}},
            {"$group": {"_id": "$query", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]).to_list(10)
        
        trending_queries = [t["_id"] for t in trending if t["_id"]]
        
        # Build AI prompt
        ai_prompt = f"""Generate 5 smart search suggestions for a user on InfoPilot Explorer.

Current query (if any): "{query}"
User's recent searches: {', '.join(recent_queries[:5]) or 'None'}
Trending searches: {', '.join(trending_queries[:5]) or 'General topics'}

Generate suggestions that:
1. Complete or enhance the current query (if provided)
2. Relate to user's search patterns
3. Include trending/popular topics
4. Are actionable and specific

Return ONLY a valid JSON array of suggestion objects:
[
  {{"suggestion": "search query here", "reason": "brief reason", "type": "completion|related|trending"}}
]"""

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"smart_suggestions_{user_id}_{datetime.now().timestamp()}",
            system_message="Generate smart, relevant search suggestions. Return only valid JSON."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=ai_prompt))
        
        # Parse response
        import json
        try:
            response_text = response.strip()
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            suggestions = json.loads(response_text)
        except:
            return {"suggestions": get_fallback_smart_suggestions(query), "ai_powered": False}
        
        return {
            "suggestions": suggestions[:5],
            "ai_powered": True,
            "query": query,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Smart suggestions error: {e}")
        return {"suggestions": get_fallback_smart_suggestions(query), "ai_powered": False}


def get_fallback_smart_suggestions(query: str) -> list:
    """Fallback suggestions when AI is unavailable"""
    base_suggestions = [
        {"suggestion": "artificial intelligence news 2026", "reason": "Trending topic", "type": "trending"},
        {"suggestion": "climate change solutions", "reason": "Popular search", "type": "trending"},
        {"suggestion": "remote work productivity tips", "reason": "High demand", "type": "related"},
        {"suggestion": "cryptocurrency market analysis", "reason": "Growing interest", "type": "trending"},
        {"suggestion": "space exploration updates", "reason": "Breaking news", "type": "trending"}
    ]
    
    if query:
        # Add query-specific completions
        completions = [
            {"suggestion": f"{query} latest news", "reason": "Get latest updates", "type": "completion"},
            {"suggestion": f"{query} best practices", "reason": "Learn best approaches", "type": "completion"},
            {"suggestion": f"{query} tutorial guide", "reason": "Step-by-step learning", "type": "completion"}
        ]
        return completions + base_suggestions[:2]
    
    return base_suggestions


class ProtocolCreationRequest(BaseModel):
    category: str = "trending"  # trending, similar, gaps, seasonal, premium


@router.post("/ai/protocol-recommendations", response_model=dict)
async def get_ai_protocol_creation_recommendations(
    request: ProtocolCreationRequest,
    user = Depends(get_current_user)
):
    """
    Get AI-powered recommendations for creating NEW protocols.
    Returns protocol ideas with names, InfoJet 2.0 syntax, pricing suggestions, and demand analysis.
    """
    user_id = str(user["_id"])
    category = request.category
    
    if not EMERGENT_LLM_KEY:
        logger.warning("EMERGENT_LLM_KEY not configured for AI recommendations")
        return {"recommendations": [], "ai_powered": False, "error": "AI not configured"}
    
    try:
        # Get user context for personalization
        context = await get_user_search_context(user_id)
        
        # Get existing marketplace protocols to avoid duplicates
        existing_protocols = await db.categories.find(
            {"is_marketplace": True}
        ).limit(50).to_list(50)
        
        existing_names = [p.get("name", "").lower() for p in existing_protocols]
        
        # Category-specific prompts
        category_prompts = {
            "trending": "Focus on currently trending topics in 2025-2026: AI, space exploration, climate tech, cryptocurrency regulation, remote work, mental health, emerging technologies.",
            "similar": f"Based on user's interests: {', '.join(context['search_terms'][:5]) or 'general topics'} and categories: {', '.join(context['category_names'][:3]) or 'various'}. Suggest protocols similar to what they already work with.",
            "gaps": "Focus on underserved niches with high demand but low supply: specialized professional topics, niche hobbies, regional interests, emerging industries.",
            "seasonal": "Focus on seasonal opportunities: tax season (Jan-Apr), summer travel (May-Aug), back to school (Aug-Sep), holiday shopping (Nov-Dec), New Year resolutions (Jan).",
            "premium": "Focus on high-value B2B or professional topics: executive insights, investment analysis, legal compliance, industry reports, enterprise solutions."
        }
        
        prompt_context = category_prompts.get(category, category_prompts["trending"])
        
        # Build the AI prompt
        ai_prompt = f"""You are an expert at creating search protocols for InfoPilot Explorer marketplace.
Generate 5 unique, marketable protocol ideas for the "{category}" category.

Context: {prompt_context}

Existing protocols to avoid (don't duplicate these names): {', '.join(existing_names[:20]) if existing_names else 'None'}

For each protocol, provide:
1. A catchy, marketable name
2. An InfoJet 2.0 protocol string using this syntax:
   - Use parentheses for word groups: (word1 or word2)
   - Use & to connect required groups: (group1) & (group2)
   - Use + at end for recency bias: (terms)+
   - Example: (artificial intelligence or AI) & (breakthrough or news) & (2025 or 2026)+

3. Estimated price range (consider: FREE, $0.99-$1.99, $2.99-$4.99, $5.99-$9.99, $14.99+)
4. Demand level: LOW, MEDIUM, MEDIUM-HIGH, HIGH, VERY HIGH
5. A brief note explaining why this is valuable (max 50 words)

Return ONLY a valid JSON array in this exact format:
[
  {{
    "name": "Protocol Name",
    "protocol": "(term1 or term2) & (term3 or term4)+",
    "estimated_value": "$2.99-$4.99",
    "demand": "HIGH",
    "note": "Brief explanation of value"
  }}
]

Make the protocols specific, actionable, and valuable to searchers. Focus on quality over generality."""

        # Call GPT-5.2
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"protocol_rec_{user_id}_{category}_{datetime.now().timestamp()}",
            system_message="You are an expert protocol marketplace analyst. Return only valid JSON arrays."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=ai_prompt))
        
        # Parse AI response
        import json
        try:
            response_text = response.strip()
            # Clean markdown code blocks if present
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            recommendations = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {response[:300]}")
            return {
                "recommendations": get_fallback_protocol_recommendations(category),
                "ai_powered": False,
                "category": category,
                "error": "Failed to parse AI response"
            }
        
        # Validate and clean recommendations
        validated = []
        for rec in recommendations:
            if isinstance(rec, dict) and "name" in rec and "protocol" in rec:
                validated.append({
                    "name": rec.get("name", "Unnamed Protocol"),
                    "protocol": rec.get("protocol", "(search) & (terms)+"),
                    "estimated_value": rec.get("estimated_value", "$1.99-$2.99"),
                    "demand": rec.get("demand", "MEDIUM"),
                    "note": rec.get("note", "AI-generated recommendation")
                })
        
        return {
            "recommendations": validated[:5],
            "ai_powered": True,
            "category": category,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI protocol recommendations error: {e}")
        return {
            "recommendations": get_fallback_protocol_recommendations(category),
            "ai_powered": False,
            "category": category,
            "error": str(e)
        }


def get_fallback_protocol_recommendations(category: str) -> list:
    """Return static fallback recommendations when AI is unavailable"""
    fallbacks = {
        "trending": [
            {"name": "AI News Tracker", "protocol": "(artificial intelligence or AI or machine learning) & (breakthrough or announcement) & (2025 or 2026)+", "estimated_value": "$2.99-$4.99", "demand": "HIGH", "note": "AI is consistently trending"},
            {"name": "Space Exploration Updates", "protocol": "(NASA or SpaceX or space mission) & (launch or discovery) & (Mars or Moon)+", "estimated_value": "$1.99-$3.99", "demand": "HIGH", "note": "Space news always attracts readers"},
            {"name": "Climate Tech Innovations", "protocol": "(climate or renewable energy) & (technology or innovation) & (solution or investment)+", "estimated_value": "$2.99-$4.99", "demand": "MEDIUM-HIGH", "note": "Growing interest in sustainability"},
        ],
        "gaps": [
            {"name": "Remote Work Productivity", "protocol": "(remote work or work from home) & (productivity or tips or tools)+", "estimated_value": "$1.99-$2.99", "demand": "HIGH", "note": "Underserved niche with high demand"},
            {"name": "Mental Health Resources", "protocol": "(mental health or wellness) & (resources or support) & (anxiety or stress)+", "estimated_value": "$2.99-$4.99", "demand": "HIGH", "note": "Growing demand for mental health content"},
        ],
        "seasonal": [
            {"name": "Tax Season Guide 2026", "protocol": "(tax or IRS or deduction) & (2026 or filing or deadline)+", "estimated_value": "$4.99-$9.99", "demand": "SEASONAL HIGH", "note": "Peak demand Jan-Apr"},
            {"name": "Summer Travel Deals", "protocol": "(travel or vacation) & (deal or discount) & (summer or 2026)+", "estimated_value": "$1.99-$3.99", "demand": "SEASONAL", "note": "Peak demand May-Aug"},
        ],
        "premium": [
            {"name": "Executive Leadership Insights", "protocol": "(CEO or executive or leadership) & (strategy or interview) & (Fortune 500)+", "estimated_value": "$9.99-$19.99", "demand": "NICHE-HIGH", "note": "Premium B2B audience"},
            {"name": "Investment Due Diligence", "protocol": "(investment or due diligence) & (analysis or risk) & (startup or fund)+", "estimated_value": "$14.99-$29.99", "demand": "NICHE-HIGH", "note": "High-value professional content"},
        ],
        "similar": [
            {"name": "Aviation Career Guide", "protocol": "(pilot or aviation) & (career or training or certification)+", "estimated_value": "$3.99-$5.99", "demand": "MEDIUM", "note": "Based on aviation interests"},
            {"name": "Memoir Writing Tips", "protocol": "(memoir or autobiography) & (writing or publishing) & (bestseller)+", "estimated_value": "$2.99-$4.99", "demand": "MEDIUM", "note": "Based on storytelling interests"},
        ]
    }
    return fallbacks.get(category, fallbacks["trending"])


# ==================== AI NEWS ARTICLES ====================

NEWS_TOPICS = [
    "Technology", "Science", "Business", "Health", "Politics", 
    "Environment", "Space", "Finance", "Education", "Sports"
]

@router.get("/ai/news", response_model=dict)
async def get_ai_news_articles():
    """
    Get AI-generated top 10 news headlines across different topics.
    Excludes entertainment news. Each article is about a different topic.
    """
    if not EMERGENT_LLM_KEY:
        logger.warning("EMERGENT_LLM_KEY not configured for AI news")
        return {"articles": get_fallback_news(), "ai_powered": False}
    
    try:
        # Build AI prompt
        ai_prompt = f"""Generate exactly 10 realistic, current news headlines about different global topics.
        
REQUIREMENTS:
1. Each headline MUST be about a DIFFERENT topic from this list: {', '.join(NEWS_TOPICS)}
2. NO entertainment or celebrity news
3. Headlines should feel like real breaking news from today
4. Include a brief 1-sentence summary for each
5. Assign a category/topic to each

Return ONLY a valid JSON array in this exact format (no other text):
[
  {{"headline": "Major headline here", "summary": "Brief summary of the news.", "topic": "Technology", "emoji": "🔬"}},
  ...
]

Make headlines diverse: include technology breakthroughs, scientific discoveries, business news, 
health updates, political developments, environmental news, space exploration, financial markets, 
education policy, and sports achievements. Each must be a DIFFERENT topic."""

        # Call GPT-5.2
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ai_news_{datetime.now().timestamp()}",
            system_message="You are a professional news editor. Generate realistic, diverse news headlines. Return only valid JSON."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=ai_prompt))
        
        # Parse AI response
        import json
        try:
            response_text = response.strip()
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            articles = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI news response: {response[:200]}")
            return {"articles": get_fallback_news(), "ai_powered": False}
        
        # Validate and ensure different topics
        validated = []
        seen_topics = set()
        
        for article in articles:
            if isinstance(article, dict) and "headline" in article:
                topic = article.get("topic", "General")
                if topic.lower() not in seen_topics:
                    seen_topics.add(topic.lower())
                    validated.append({
                        "headline": article.get("headline", ""),
                        "summary": article.get("summary", ""),
                        "topic": topic,
                        "emoji": article.get("emoji", "📰")
                    })
                    if len(validated) >= 10:
                        break
        
        return {
            "articles": validated,
            "ai_powered": True,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI news error: {e}")
        return {"articles": get_fallback_news(), "ai_powered": False, "error": str(e)}


def get_fallback_news() -> list:
    """Return static fallback news when AI is unavailable"""
    return [
        {"headline": "AI Breakthrough: New Model Achieves Human-Level Reasoning", "summary": "Researchers announce a major milestone in artificial intelligence development.", "topic": "Technology", "emoji": "🤖"},
        {"headline": "Mars Mission Update: First Samples Return to Earth", "summary": "NASA confirms successful retrieval of Martian soil samples for analysis.", "topic": "Space", "emoji": "🚀"},
        {"headline": "Global Markets Rally on Economic Recovery Signs", "summary": "Stock indices reach new highs as inflation concerns ease worldwide.", "topic": "Finance", "emoji": "📈"},
        {"headline": "Climate Summit Reaches Historic Agreement", "summary": "World leaders commit to ambitious emissions reduction targets.", "topic": "Environment", "emoji": "🌍"},
        {"headline": "Medical Breakthrough: New Treatment Shows Promise", "summary": "Clinical trials reveal effective therapy for previously untreatable condition.", "topic": "Health", "emoji": "🏥"},
        {"headline": "Education Reform Bill Passes Legislature", "summary": "New law aims to modernize curriculum and increase funding for schools.", "topic": "Education", "emoji": "📚"},
        {"headline": "Tech Giant Announces Revolutionary Product", "summary": "Company unveils device expected to transform the industry.", "topic": "Business", "emoji": "💼"},
        {"headline": "Scientific Discovery Rewrites History Books", "summary": "Archaeological findings challenge long-held theories about ancient civilizations.", "topic": "Science", "emoji": "🔬"},
        {"headline": "International Summit Addresses Global Security", "summary": "World leaders convene to discuss cooperative defense strategies.", "topic": "Politics", "emoji": "🏛️"},
        {"headline": "Historic Championship Victory Celebrated", "summary": "Underdog team achieves remarkable win in major sporting event.", "topic": "Sports", "emoji": "🏆"}
    ]


# ==================== RELEVANT HASHTAGS ====================

@router.post("/ai/generate-hashtags", response_model=dict)
async def generate_relevant_hashtags(
    content: str = Body(..., embed=True),
    category_name: str = Body(None, embed=True),
    protocol: str = Body(None, embed=True),
    user = Depends(get_current_user)
):
    """
    Generate hashtags that are relevant to both the content AND the category/protocol.
    """
    if not EMERGENT_LLM_KEY:
        return {"hashtags": extract_basic_hashtags(content), "ai_powered": False}
    
    try:
        context = f"Content: {content[:500]}"
        if category_name:
            context += f"\nCategory: {category_name}"
        if protocol:
            context += f"\nSearch Protocol: {protocol[:200]}"
        
        ai_prompt = f"""Generate 5-8 highly relevant hashtags for this search result.

{context}

REQUIREMENTS:
1. Hashtags must be directly relevant to BOTH the content AND the category/protocol
2. Include a mix of broad and specific hashtags
3. Use popular, searchable terms
4. No spaces in hashtags, use CamelCase for multi-word tags
5. Start each with # symbol

Return ONLY a JSON array of hashtags:
["#Hashtag1", "#Hashtag2", ...]"""

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"hashtags_{datetime.now().timestamp()}",
            system_message="Generate relevant, popular hashtags. Return only valid JSON array."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=ai_prompt))
        
        import json
        try:
            response_text = response.strip()
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            hashtags = json.loads(response_text)
            if isinstance(hashtags, list):
                return {"hashtags": hashtags[:8], "ai_powered": True}
        except:
            pass
        
        return {"hashtags": extract_basic_hashtags(content), "ai_powered": False}
        
    except Exception as e:
        logger.error(f"AI hashtags error: {e}")
        return {"hashtags": extract_basic_hashtags(content), "ai_powered": False}


def extract_basic_hashtags(content: str) -> list:
    """Extract basic hashtags from content"""
    import re
    words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', content)
    common_words = {'The', 'And', 'For', 'With', 'From', 'This', 'That', 'What', 'When', 'Where', 'How', 'Why'}
    hashtags = [f"#{w}" for w in words[:15] if w not in common_words and len(w) > 3]
    return hashtags[:8]
