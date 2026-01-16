"""
InfoPilot Explorer - Main FastAPI Application
Refactored with modular routers
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
import asyncio
import re
import os
import logging

# Import configuration
from config import (
    db, client, logger, 
    PAYPAL_PAYMENT_LINK, PAYPAL_CLIENT_ID, PAYPAL_SECRET,
    RESEND_API_KEY, SENDER_EMAIL, BOOK_PROMO,
    MARKETPLACE_PLATFORM_FEE, MARKETPLACE_MIN_PRICE, MARKETPLACE_MAX_PRICE
)

# Import services
from services.auth_service import AuthService
from services.search_service import WebSearchService
from services.protocol_service import ProtocolParser

# Import modular routers
from routes.auth import router as auth_router, get_current_user, get_optional_user
from routes.categories import router as categories_router
from routes.social import router as social_router
from routes.marketplace import router as marketplace_router
from routes.admin import router as admin_router
from routes.bundles import router as bundles_router, init_router as init_bundles_router
from routes.push_notifications import router as push_router, init_router as init_push_router
from routes.chat import router as chat_router, init_router as init_chat_router
from routes.statistics import router as statistics_router
from routes.gamification import router as gamification_router
from routes.messages import router as messages_router
from routes.newsletter import router as newsletter_router
from routes.voice import router as voice_router
from routes.collaborate import router as collaborate_router
from routes.polls import router as polls_router
from routes.tutorials import router as tutorials_router
from routes.rate_limiting import router as rate_limiting_router
from routes.webhooks import router as webhooks_router
from routes.ai_suggestions import router as ai_suggestions_router
from routes.protocol_analytics import router as protocol_analytics_router
from routes.ab_testing import router as ab_testing_router
from routes.ab_optimizer import router as ab_optimizer_router
from routes.revenue_forecast import router as revenue_forecast_router
from routes.email_reports import router as email_reports_router
from routes.unified_chat import router as unified_chat_router
from routes.easter_eggs import router as easter_eggs_router
from routes.legal import router as legal_router

# Import services
from services.location_service import LocationService

# DuckDuckGo Search library
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False

# SerpAPI
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

# Resend for emails
import resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# SerpAPI Key
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
BRAVE_API_KEY = os.environ.get('BRAVE_API_KEY')

# Create the main app
app = FastAPI(title="InfoPilot API", version="2.0.0")

# Create a router with the /api prefix for endpoints not in modular files
api_router = APIRouter(prefix="/api")

# Static file serving for uploads
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Create upload directories
PHOTO_UPLOAD_DIR = "/app/backend/uploads/photos"
MESSAGE_UPLOAD_DIR = "/app/backend/uploads/messages"
os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)
os.makedirs(MESSAGE_UPLOAD_DIR, exist_ok=True)

@app.get("/api/uploads/photos/{filename}")
async def serve_photo(filename: str):
    """Serve uploaded photos"""
    filepath = os.path.join(PHOTO_UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)

@app.get("/api/uploads/messages/{filename}")
async def serve_message_image(filename: str):
    """Serve message images"""
    filepath = os.path.join(MESSAGE_UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)

# Security
security = HTTPBearer(auto_error=False)

# ============== PYDANTIC MODELS (for endpoints not in models/schemas.py) ==============

class PaymentVerification(BaseModel):
    payment_id: str
    user_id: str

class FriendRequest(BaseModel):
    target_user_id: str

class MessageCreate(BaseModel):
    recipient_id: str
    content: str

class ReactionCreate(BaseModel):
    search_result_id: str
    reaction_type: str

class GroupPostCreate(BaseModel):
    content: str

class FeedPostCreate(BaseModel):
    content: str
    group_id: Optional[str] = None
    page_id: Optional[str] = None

class PagePostCreate(BaseModel):
    content: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class ProtocolDebugRequest(BaseModel):
    protocol: str
    test_text: Optional[str] = None

class ProtocolTemplate(BaseModel):
    name: str
    description: Optional[str] = ""
    protocol: str
    category: Optional[str] = "General"
    tags: Optional[List[str]] = []
    is_public: bool = False

class PayPalWebhookEvent(BaseModel):
    event_type: str
    resource: Dict[str, Any]

class ManualPaymentConfirm(BaseModel):
    protocol_id: str
    transaction_id: str

class SearchRequest(BaseModel):
    query: str

class CollateRequest(BaseModel):
    category_id: str
    aggregation: str = "default"
    page: int = 1

# ============== AUTHENTICATION DEPENDENCY (local copy for this file) ==============

async def get_current_user_local(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    session = await db.sessions.find_one({"token": token})
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if session.get("expires_at") and session["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token expired")
    
    user = await db.users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def get_optional_user_local(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    try:
        return await get_current_user_local(credentials)
    except Exception:
        return None

# ============== HELPER FUNCTIONS ==============

import hashlib
import secrets
import urllib.parse
import httpx

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

# ============== WEB SEARCH SERVICE (Extended) ==============

class ExtendedWebSearchService:
    """Extended search service with SerpAPI and DDGS support"""
    
    @staticmethod
    async def search_serpapi(query: str, num_results: int = 100) -> List[Dict[str, Any]]:
        """Use SerpAPI for premium Google search results"""
        results = []
        
        if not SERPAPI_KEY:
            return results
        
        try:
            def _search():
                all_results = []
                pages_needed = min(7, (num_results // 10) + 1)
                
                for page in range(pages_needed):
                    params = {
                        "engine": "google",
                        "q": query,
                        "api_key": SERPAPI_KEY,
                        "num": 10,
                        "start": page * 10,
                        "gl": "us",
                        "hl": "en"
                    }
                    
                    try:
                        search = GoogleSearch(params)
                        data = search.get_dict()
                        
                        organic = data.get("organic_results", [])
                        for r in organic:
                            url = r.get("link", "")
                            if not url:
                                continue
                            
                            try:
                                parsed = urllib.parse.urlparse(url)
                                root_domain = parsed.netloc
                            except Exception:
                                root_domain = ""
                            
                            all_results.append({
                                "url": url,
                                "title": r.get("title", ""),
                                "snippet": r.get("snippet", ""),
                                "content": r.get("snippet", ""),
                                "root_domain": root_domain,
                                "source": "serpapi",
                                "position": r.get("position", 0)
                            })
                        
                        if len(organic) < 8:
                            break
                            
                    except Exception as e:
                        logger.warning(f"SerpAPI page {page} error: {e}")
                        break
                
                return all_results
            
            results = await asyncio.get_event_loop().run_in_executor(None, _search)
            logger.info(f"SerpAPI returned {len(results)} results")
            
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
        
        return results
    
    @staticmethod
    async def search_ddgs_library(query: str, num_results: int = 200) -> List[Dict[str, Any]]:
        """Use duckduckgo-search library"""
        results = []
        
        if not DDGS_AVAILABLE:
            return results
        
        try:
            def _search():
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=num_results))
                    return search_results
            
            search_results = await asyncio.get_event_loop().run_in_executor(None, _search)
            
            for r in search_results:
                url = r.get('href', r.get('link', ''))
                if not url:
                    continue
                
                try:
                    parsed = urllib.parse.urlparse(url)
                    root_domain = parsed.netloc
                except Exception:
                    root_domain = ""
                
                results.append({
                    "url": url,
                    "title": r.get('title', ''),
                    "snippet": r.get('body', r.get('snippet', '')),
                    "content": r.get('body', r.get('snippet', '')),
                    "root_domain": root_domain,
                    "source": "ddgs_library"
                })
            
            logger.info(f"DDGS library returned {len(results)} results")
            
        except Exception as e:
            logger.error(f"DDGS library search error: {e}")
        
        return results
    
    @staticmethod
    async def search_brave(query: str, num_results: int = 20) -> List[Dict[str, Any]]:
        """Use Brave Search API for privacy-focused search results"""
        results = []
        
        if not BRAVE_API_KEY:
            return results
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Accept": "application/json",
                    "X-Subscription-Token": BRAVE_API_KEY
                }
                params = {
                    "q": query,
                    "count": min(num_results, 20),  # Brave API max is 20 per request
                    "search_lang": "en",
                    "country": "us",
                    "safesearch": "moderate",
                    "text_decorations": False,
                    "extra_snippets": True
                }
                
                async with session.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        web_results = data.get("web", {}).get("results", [])
                        for r in web_results:
                            url = r.get("url", "")
                            if not url:
                                continue
                            
                            try:
                                parsed = urllib.parse.urlparse(url)
                                root_domain = parsed.netloc
                            except Exception:
                                root_domain = ""
                            
                            # Combine main snippet with extra snippets
                            snippet = r.get("description", "")
                            extra_snippets = r.get("extra_snippets", [])
                            if extra_snippets:
                                snippet += " " + " ".join(extra_snippets[:2])
                            
                            results.append({
                                "url": url,
                                "title": r.get("title", ""),
                                "snippet": snippet,
                                "content": snippet,
                                "root_domain": root_domain,
                                "source": "brave",
                                "age": r.get("age", ""),
                                "language": r.get("language", "en")
                            })
                        
                        logger.info(f"Brave Search returned {len(results)} results")
                    else:
                        error_text = await response.text()
                        logger.warning(f"Brave Search API error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Brave Search error: {e}")
        
        return results
    
    @staticmethod
    async def search(query: str, num_results: int = 200) -> List[Dict[str, Any]]:
        """Aggregate search from multiple sources: Google (SerpAPI), DuckDuckGo, Brave"""
        all_results = []
        seen_urls = set()
        
        # Try SerpAPI first if available (Google)
        if SERPAPI_KEY and SERPAPI_AVAILABLE:
            serp_results = await ExtendedWebSearchService.search_serpapi(query, min(70, num_results))
            for r in serp_results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)
        
        # Brave Search (privacy-focused, high quality)
        if BRAVE_API_KEY and len(all_results) < num_results:
            brave_results = await ExtendedWebSearchService.search_brave(query, min(20, num_results - len(all_results)))
            for r in brave_results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)
        
        # DuckDuckGo (always available, no API key needed)
        if DDGS_AVAILABLE and len(all_results) < num_results:
            ddgs_results = await ExtendedWebSearchService.search_ddgs_library(query, num_results - len(all_results))
            for r in ddgs_results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)
        
        # Fallback to basic search service
        if len(all_results) < num_results:
            basic_results = await WebSearchService.search(query, num_results - len(all_results))
            for r in basic_results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)
        
        logger.info(f"Total search results from all engines: {len(all_results)}")
        return all_results[:num_results]

    @staticmethod
    async def get_available_engines() -> dict:
        """Return status of all available search engines"""
        return {
            "engines": {
                "serpapi": {
                    "name": "Google (SerpAPI)",
                    "available": bool(SERPAPI_KEY and SERPAPI_AVAILABLE),
                    "description": "Premium Google search via SerpAPI"
                },
                "brave": {
                    "name": "Brave Search",
                    "available": bool(BRAVE_API_KEY),
                    "description": "Privacy-focused search engine"
                },
                "duckduckgo": {
                    "name": "DuckDuckGo",
                    "available": DDGS_AVAILABLE,
                    "description": "Privacy-focused, no API key required"
                },
                "basic": {
                    "name": "Basic Web Search",
                    "available": True,
                    "description": "Fallback web scraping"
                }
            },
            "total_available": sum([
                bool(SERPAPI_KEY and SERPAPI_AVAILABLE),
                bool(BRAVE_API_KEY),
                DDGS_AVAILABLE,
                True  # Basic always available
            ])
        }



# ============== ARTICLE CLASSIFIER ==============

class ArticleClassifier:
    """Classify articles based on content"""
    
    INFORMATIVE_PROTOCOL = "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)"
    PHD_KEYWORDS = ["ph.d.", "phd", "d.phil.", "dr."]
    
    @classmethod
    def classify(cls, title: str, content: str) -> str:
        """Classify article type"""
        if not content:
            return "News Article"
        
        content_lower = content.lower()
        title_lower = title.lower() if title else ""
        word_count = len(content.split())
        
        if "forum" in title_lower:
            return "Forum"
        
        if content_lower.count("blog") >= 3 and "blog" in title_lower:
            return "Blog"
        
        phd_count = sum(content_lower.count(kw) for kw in cls.PHD_KEYWORDS)
        if phd_count >= 3 and word_count >= 1500:
            return "Informative Ph.D."
        
        if content_lower.count("news") >= 3:
            return "News Article"
        
        return "News Article"

# ============== PAYMENT ENDPOINTS ==============

@api_router.get("/payment/link")
async def get_payment_link(user = Depends(get_current_user_local)):
    """Get PayPal payment link"""
    return {
        "link": PAYPAL_PAYMENT_LINK,
        "message": "Complete payment to activate your account"
    }

@api_router.post("/payment/verify")
async def verify_payment(data: PaymentVerification, user = Depends(get_current_user_local)):
    """Verify a payment"""
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"subscription_active": True, "subscription_date": datetime.utcnow()}}
    )
    return {"success": True, "message": "Payment verified"}

@api_router.post("/payment/activate")
async def activate_premium(user = Depends(get_current_user_local)):
    """Activate premium subscription"""
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"subscription_active": True}}
    )
    return {"success": True}

@api_router.get("/subscription-info")
async def get_subscription_info():
    """Get subscription information"""
    settings = await db.settings.find_one({"key": "subscription_price"})
    price = settings.get("value", 0.99) if settings else 0.99
    
    return {
        "price": price,
        "payment_link": PAYPAL_PAYMENT_LINK,
        "features": [
            "Unlimited searches",
            "Protocol marketplace access",
            "Premium support"
        ]
    }

@api_router.post("/subscriptions/activate")
async def activate_subscription(user = Depends(get_current_user_local)):
    """Activate user subscription"""
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"subscription_active": True, "subscription_date": datetime.utcnow()}}
    )
    return {"success": True, "message": "Subscription activated"}

# ============== SEARCH ENDPOINTS ==============

@api_router.post("/search", response_model=dict)
async def perform_search(request: SearchRequest, user = Depends(get_current_user_local)):
    """Perform a web search"""
    settings = await db.settings.find_one({"key": "max_search_pages"})
    max_pages = settings.get("value", 99) if settings else 99
    max_results = max_pages * 20
    
    results = await ExtendedWebSearchService.search(request.query, min(max_results, 200))
    
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

@api_router.post("/collate", response_model=dict)
async def collate_results(request: CollateRequest, user = Depends(get_current_user_local)):
    """Collate search results with protocol matching"""
    category = await db.categories.find_one({"_id": ObjectId(request.category_id)})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    protocol = category.get("protocol", "")
    if not protocol:
        raise HTTPException(status_code=400, detail="Category has no protocol")
    
    # Get search query from protocol
    search_query = ProtocolParser.extract_search_query(protocol)
    
    # Get settings
    settings = await db.settings.find_one({"key": "max_search_pages"})
    max_pages = settings.get("value", 99) if settings else 99
    max_results = max_pages * 20
    
    # Perform search
    raw_results = await ExtendedWebSearchService.search(search_query, min(max_results, 200))
    
    # Parse protocol and match results
    groups = ProtocolParser.parse_protocol(protocol)
    matched_results = []
    batch_id = str(ObjectId())
    
    for result in raw_results:
        matches, score = ProtocolParser.match_result(result, groups)
        if matches:
            result["match_score"] = score
            result["article_type"] = ArticleClassifier.classify(
                result.get("title", ""), result.get("content", "")
            )
            result["root_domain"] = WebSearchService.extract_root_domain(result.get("url", ""))
            matched_results.append(result)
    
    # Sort by score
    matched_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Store results
    for result in matched_results:
        existing = await db.search_results.find_one({
            "url": result["url"],
            "user_id": str(user["_id"])
        })
        
        if existing:
            await db.search_results.update_one(
                {"_id": existing["_id"]},
                {"$addToSet": {"category_ids": request.category_id}}
            )
        else:
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
                "batch_id": batch_id,
                "created_at": datetime.utcnow()
            })
    
    # Update category
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
        "batch_id": batch_id
    }


@api_router.post("/auto-categorize", response_model=dict)
async def auto_categorize_search(request: dict, user = Depends(get_current_user_local)):
    """
    One-click auto-categorization: Search and automatically match results against ALL user's categories.
    Each result can match multiple categories based on their protocols.
    """
    search_query = request.get("query", "").strip()
    if not search_query:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    user_id = str(user["_id"])
    
    # Get all user's categories
    all_categories = await db.categories.find({
        "$or": [
            {"user_id": user_id},
            {"is_public": True}
        ]
    }).to_list(500)
    
    if not all_categories:
        raise HTTPException(status_code=400, detail="No categories available. Create categories first.")
    
    # Get collation limit from settings
    settings = await db.settings.find_one({"key": "collation_limit"})
    max_results = int(settings.get("value", 40)) if settings else 40
    max_results = min(max(1, max_results), 100)  # Enforce 1-100 range
    
    # Perform search across multiple engines
    raw_results = await ExtendedWebSearchService.search(search_query, max_results)
    
    if not raw_results:
        return {
            "results": [],
            "total": 0,
            "categories_matched": 0,
            "message": "No results found"
        }
    
    batch_id = str(ObjectId())
    matched_results = []
    category_matches = {}  # Track which categories matched which results
    
    # For each result, check against ALL categories
    for result in raw_results:
        result_categories = []
        result_category_ids = []
        best_score = 0
        
        for category in all_categories:
            protocol = category.get("protocol", "")
            if not protocol:
                continue
            
            # Parse protocol and check if result matches
            groups = ProtocolParser.parse_protocol(protocol)
            matches, score = ProtocolParser.match_result(result, groups)
            
            if matches:
                cat_id = str(category["_id"])
                cat_name = category["name"]
                result_categories.append(cat_name)
                result_category_ids.append(cat_id)
                best_score = max(best_score, score)
                
                # Track category matches
                if cat_id not in category_matches:
                    category_matches[cat_id] = {
                        "name": cat_name,
                        "count": 0
                    }
                category_matches[cat_id]["count"] += 1
        
        # Only include results that match at least one category
        if result_categories:
            result["match_score"] = best_score
            result["article_type"] = ArticleClassifier.classify(
                result.get("title", ""), result.get("content", "")
            )
            result["root_domain"] = WebSearchService.extract_root_domain(result.get("url", ""))
            result["categories"] = result_categories
            result["category_ids"] = result_category_ids
            matched_results.append(result)
    
    # Sort by score
    matched_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Store results in database
    for result in matched_results:
        existing = await db.search_results.find_one({
            "url": result["url"],
            "user_id": user_id
        })
        
        if existing:
            # Update existing result with new categories
            await db.search_results.update_one(
                {"_id": existing["_id"]},
                {
                    "$addToSet": {"category_ids": {"$each": result["category_ids"]}},
                    "$set": {"batch_id": batch_id, "updated_at": datetime.utcnow()}
                }
            )
        else:
            await db.search_results.insert_one({
                "url": result["url"],
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "content": result.get("content", ""),
                "article_type": result.get("article_type", "Unknown"),
                "root_domain": result.get("root_domain", ""),
                "match_score": result.get("match_score", 0),
                "category_ids": result["category_ids"],
                "user_id": user_id,
                "batch_id": batch_id,
                "created_at": datetime.utcnow()
            })
    
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
            "categories": r.get("categories", []),
            "category_ids": r.get("category_ids", [])
        })
    
    # Build category summary
    categories_summary = [
        {"id": cat_id, "name": data["name"], "result_count": data["count"]}
        for cat_id, data in category_matches.items()
    ]
    categories_summary.sort(key=lambda x: x["result_count"], reverse=True)
    
    return {
        "results": formatted,
        "total": len(formatted),
        "categories_matched": len(category_matches),
        "category_summary": categories_summary,
        "batch_id": batch_id,
        "message": f"Auto-categorized {len(formatted)} results across {len(category_matches)} categories!"
    }


@api_router.post("/ai-search", response_model=dict)
async def ai_intelligent_search(request: dict, user = Depends(get_current_user_local)):
    """
    AI-powered intelligent keyword search across multiple search engines.
    Uses GPT to expand keywords and optimize search queries for better results.
    Searches Google, DuckDuckGo, Bing, and other connected databases.
    """
    original_query = request.get("query", "").strip()
    search_mode = request.get("mode", "comprehensive")  # comprehensive, news, research
    auto_categorize = request.get("auto_categorize", True)
    
    if not original_query:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    user_id = str(user["_id"])
    
    # Get collation limit from settings
    settings = await db.settings.find_one({"key": "collation_limit"})
    max_results = int(settings.get("value", 40)) if settings else 40
    max_results = min(max(1, max_results), 100)
    
    # Use AI to expand and optimize the search query
    expanded_queries = [original_query]
    ai_suggestions = []
    
    try:
        from emergentintegrations.llm.chat import chat, ModelType
        import os
        
        emergent_key = os.environ.get("EMERGENT_MODEL_API_KEY", "")
        if emergent_key:
            mode_context = {
                "comprehensive": "general web search covering all aspects",
                "news": "recent news and current events",
                "research": "academic, research papers, and in-depth analysis"
            }.get(search_mode, "general web search")
            
            ai_prompt = f"""You are a search optimization expert. Given the user's search query, generate 3 optimized search queries that will find the most relevant and diverse results for {mode_context}.

Original query: "{original_query}"

Provide 3 alternative search queries that:
1. First query: Include synonyms and related terms
2. Second query: Focus on specific aspects or subtopics
3. Third query: Use different phrasing or question format

Return ONLY a JSON array of 3 strings, no other text:
["query1", "query2", "query3"]"""

            ai_response = await chat(
                api_key=emergent_key,
                model=ModelType.GPT_5_2,
                prompt=ai_prompt
            )
            
            # Parse AI response
            import json
            try:
                json_start = ai_response.find('[')
                json_end = ai_response.rfind(']') + 1
                if json_start != -1 and json_end > json_start:
                    ai_suggestions = json.loads(ai_response[json_start:json_end])
                    expanded_queries.extend(ai_suggestions[:3])
            except json.JSONDecodeError:
                pass
    except Exception as e:
        logger.warning(f"AI query expansion failed: {e}")
    
    # Search across multiple engines with all queries
    all_results = []
    seen_urls = set()
    
    for query in expanded_queries:
        try:
            # ExtendedWebSearchService already searches multiple engines
            results = await ExtendedWebSearchService.search(query, max_results // len(expanded_queries))
            
            for result in results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["search_query"] = query
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"Search failed for query '{query}': {e}")
    
    if not all_results:
        return {
            "results": [],
            "total": 0,
            "original_query": original_query,
            "expanded_queries": expanded_queries,
            "message": "No results found"
        }
    
    batch_id = str(ObjectId())
    
    # If auto_categorize is enabled, match against categories
    if auto_categorize:
        all_categories = await db.categories.find({
            "$or": [
                {"user_id": user_id},
                {"is_public": True}
            ]
        }).to_list(500)
        
        for result in all_results:
            result_categories = []
            result_category_ids = []
            best_score = 0
            
            for category in all_categories:
                protocol = category.get("protocol", "")
                if not protocol:
                    continue
                
                groups = ProtocolParser.parse_protocol(protocol)
                matches, score = ProtocolParser.match_result(result, groups)
                
                if matches:
                    result_categories.append(category["name"])
                    result_category_ids.append(str(category["_id"]))
                    best_score = max(best_score, score)
            
            result["categories"] = result_categories
            result["category_ids"] = result_category_ids
            result["match_score"] = best_score
    
    # Classify and add metadata
    for result in all_results:
        result["article_type"] = ArticleClassifier.classify(
            result.get("title", ""), result.get("content", "")
        )
        result["root_domain"] = WebSearchService.extract_root_domain(result.get("url", ""))
    
    # Sort by match score (if categorized) or by search engine ranking
    all_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Store results
    for result in all_results[:max_results]:
        existing = await db.search_results.find_one({
            "url": result["url"],
            "user_id": user_id
        })
        
        category_ids = result.get("category_ids", [])
        
        if existing:
            if category_ids:
                await db.search_results.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$addToSet": {"category_ids": {"$each": category_ids}},
                        "$set": {
                            "batch_id": batch_id,
                            "ai_search": True,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
        else:
            await db.search_results.insert_one({
                "url": result["url"],
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "content": result.get("content", ""),
                "article_type": result.get("article_type", "Unknown"),
                "root_domain": result.get("root_domain", ""),
                "match_score": result.get("match_score", 0),
                "category_ids": category_ids,
                "user_id": user_id,
                "batch_id": batch_id,
                "ai_search": True,
                "search_query": result.get("search_query", original_query),
                "created_at": datetime.utcnow()
            })
    
    # Format response
    formatted = []
    for r in all_results[:max_results]:
        formatted.append({
            "id": str(ObjectId()),
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "article_type": r.get("article_type", "Unknown"),
            "root_domain": r.get("root_domain", ""),
            "match_score": r.get("match_score", 0),
            "categories": r.get("categories", []),
            "category_ids": r.get("category_ids", []),
            "search_engine": r.get("source", "multi-engine")
        })
    
    return {
        "results": formatted,
        "total": len(formatted),
        "original_query": original_query,
        "expanded_queries": expanded_queries,
        "ai_suggestions": ai_suggestions,
        "batch_id": batch_id,
        "search_mode": search_mode,
        "auto_categorized": auto_categorize,
        "message": f"🤖 AI Search found {len(formatted)} results using {len(expanded_queries)} optimized queries!"
    }



@api_router.get("/search-engines", response_model=dict)
async def get_search_engines():
    """Get list of available search engines and their status"""
    return await ExtendedWebSearchService.get_available_engines()



@api_router.get("/ultimate-search", response_model=dict)
async def get_ultimate_search(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    category_id: Optional[str] = None,
    category_ids: Optional[str] = Query(None, description="Comma-separated category IDs to filter by"),
    aggregation: str = Query("and_or", description="Search logic: and_or, and, or"),
    batch_id: Optional[str] = None,
    user = Depends(get_optional_user_local)
):
    """Get stored search results with category filtering"""
    query = {}
    
    if user:
        query["user_id"] = str(user["_id"])
    
    # Parse category_ids (comma-separated) for multi-category filtering
    selected_category_ids = []
    if category_ids:
        selected_category_ids = [cid.strip() for cid in category_ids.split(",") if cid.strip()]
    
    # Apply category filtering based on aggregation mode
    if selected_category_ids:
        if aggregation == "and":
            # AND: Results must contain ALL selected categories
            query["category_ids"] = {"$all": selected_category_ids}
        elif aggregation == "or":
            # OR: Results must contain ANY of the selected categories
            query["category_ids"] = {"$in": selected_category_ids}
        else:
            # AND/OR (default): Same as OR - results matching any category
            query["category_ids"] = {"$in": selected_category_ids}
    elif category_id:
        # Backward compatibility: single category_id parameter
        query["category_ids"] = category_id
    
    if batch_id:
        query["batch_id"] = batch_id
    
    skip = (page - 1) * limit
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Collect all unique category IDs for bulk fetch (N+1 query optimization)
    all_category_ids = set()
    for r in results:
        for cat_id in r.get("category_ids", []):
            try:
                all_category_ids.add(ObjectId(cat_id))
            except Exception:
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
            "match_score": r.get("match_score", 0),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "created_at": r.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {
        "results": formatted,
        "total": total,
        "count": len(formatted),
        "page": page,
        "pages": (total + limit - 1) // limit,
        "filter_applied": len(selected_category_ids) > 0,
        "aggregation_mode": aggregation
    }

@api_router.get("/ultimate-search/stats", response_model=dict)
async def get_ultimate_search_stats(user = Depends(get_current_user_local)):
    """Get search statistics"""
    user_id = str(user["_id"])
    
    total_results = await db.search_results.count_documents({"user_id": user_id})
    total_categories = await db.categories.count_documents({"user_id": user_id})
    
    # Get article type breakdown
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$article_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    article_types = await db.search_results.aggregate(pipeline).to_list(20)
    
    return {
        "total_results": total_results,
        "total_categories": total_categories,
        "article_types": [{"type": a["_id"] or "Unknown", "count": a["count"]} for a in article_types]
    }

@api_router.get("/ultimate-search/batches", response_model=dict)
async def get_search_batches(user = Depends(get_current_user_local)):
    """Get all search batches"""
    user_id = str(user["_id"])
    
    pipeline = [
        {"$match": {"user_id": user_id, "batch_id": {"$exists": True}}},
        {"$group": {
            "_id": "$batch_id",
            "count": {"$sum": 1},
            "created_at": {"$min": "$created_at"}
        }},
        {"$sort": {"created_at": -1}},
        {"$limit": 50}
    ]
    
    batches = await db.search_results.aggregate(pipeline).to_list(50)
    
    return {
        "batches": [{
            "id": b["_id"],
            "count": b["count"],
            "created_at": b["created_at"].isoformat() if b.get("created_at") else None
        } for b in batches]
    }

@api_router.delete("/ultimate-search/batch/{batch_id}", response_model=dict)
async def delete_search_batch(batch_id: str, user = Depends(get_current_user_local)):
    """Delete a search batch"""
    result = await db.search_results.delete_many({
        "batch_id": batch_id,
        "user_id": str(user["_id"])
    })
    
    return {"deleted": result.deleted_count}

@api_router.delete("/ultimate-search/result/{result_id}", response_model=dict)
async def delete_single_result(result_id: str, user = Depends(get_current_user_local)):
    """Delete a single search result"""
    result = await db.search_results.delete_one({
        "_id": ObjectId(result_id),
        "user_id": str(user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {"deleted": True}

@api_router.get("/map-data", response_model=dict)
async def get_map_data(user = Depends(get_current_user_local)):
    """Get geolocated search results for map display"""
    user_id = str(user["_id"])
    
    results = await db.search_results.find({
        "user_id": user_id,
        "latitude": {"$exists": True, "$ne": None},
        "longitude": {"$exists": True, "$ne": None}
    }).to_list(500)
    
    formatted = []
    for r in results:
        formatted.append({
            "id": str(r["_id"]),
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "article_type": r.get("article_type", "Unknown")
        })
    
    return {"results": formatted, "count": len(formatted)}

@api_router.post("/reactions", response_model=dict)
async def add_reaction(reaction: ReactionCreate, user = Depends(get_current_user_local)):
    """Add a reaction to a search result"""
    await db.reactions.update_one(
        {
            "result_id": reaction.search_result_id,
            "user_id": str(user["_id"])
        },
        {
            "$set": {
                "reaction": reaction.reaction_type,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {"success": True}

# ============== FRIENDS & MESSAGING ==============

@api_router.post("/friends/request")
async def send_friend_request(request: FriendRequest, user = Depends(get_current_user_local)):
    """Send a friend request"""
    target = await db.users.find_one({"_id": ObjectId(request.target_user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already friends or pending
    existing = await db.friendships.find_one({
        "$or": [
            {"user_id": str(user["_id"]), "friend_id": request.target_user_id},
            {"user_id": request.target_user_id, "friend_id": str(user["_id"])}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already exists")
    
    await db.friendships.insert_one({
        "user_id": str(user["_id"]),
        "friend_id": request.target_user_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "Friend request sent"}

@api_router.post("/friends/accept")
async def accept_friend_request(request: FriendRequest, user = Depends(get_current_user_local)):
    """Accept a friend request"""
    friendship = await db.friendships.find_one({
        "user_id": request.target_user_id,
        "friend_id": str(user["_id"]),
        "status": "pending"
    })
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    await db.friendships.update_one(
        {"_id": friendship["_id"]},
        {"$set": {"status": "accepted", "accepted_at": datetime.utcnow()}}
    )
    
    return {"success": True, "message": "Friend request accepted"}

@api_router.post("/friends/reject")
async def reject_friend_request(request: FriendRequest, user = Depends(get_current_user_local)):
    """Reject a friend request"""
    result = await db.friendships.delete_one({
        "user_id": request.target_user_id,
        "friend_id": str(user["_id"]),
        "status": "pending"
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    return {"success": True}

@api_router.delete("/friends/{friend_id}")
async def remove_friend(friend_id: str, user = Depends(get_current_user_local)):
    """Remove a friend"""
    await db.friendships.delete_one({
        "$or": [
            {"user_id": str(user["_id"]), "friend_id": friend_id},
            {"user_id": friend_id, "friend_id": str(user["_id"])}
        ]
    })
    
    return {"success": True}

@api_router.get("/friends", response_model=dict)
async def get_friends(user = Depends(get_current_user_local)):
    """Get all friends and pending requests"""
    user_id = str(user["_id"])
    
    friendships = await db.friendships.find({
        "$or": [
            {"user_id": user_id},
            {"friend_id": user_id}
        ]
    }).to_list(500)
    
    # Bulk fetch all related users to avoid N+1 queries
    user_ids = set()
    for f in friendships:
        other_id = f["friend_id"] if f["user_id"] == user_id else f["user_id"]
        user_ids.add(ObjectId(other_id))
    
    users_list = await db.users.find({"_id": {"$in": list(user_ids)}}).to_list(len(user_ids))
    users_map = {str(u["_id"]): u for u in users_list}
    
    friends = []
    pending_sent = []
    pending_received = []
    
    for f in friendships:
        other_id = f["friend_id"] if f["user_id"] == user_id else f["user_id"]
        other_user = users_map.get(other_id)
        
        if not other_user:
            continue
        
        user_data = {
            "id": other_id,
            "username": other_user.get("username", ""),
            "callsign": other_user.get("callsign", other_user.get("username", ""))
        }
        
        if f["status"] == "accepted":
            friends.append(user_data)
        elif f["status"] == "pending":
            if f["user_id"] == user_id:
                pending_sent.append(user_data)
            else:
                pending_received.append(user_data)
    
    return {
        "friends": friends,
        "pending_sent": pending_sent,
        "pending_received": pending_received
    }

@api_router.post("/messages")
async def send_message(message: MessageCreate, user = Depends(get_current_user_local)):
    """Send a message to a friend"""
    # Verify friendship
    friendship = await db.friendships.find_one({
        "$or": [
            {"user_id": str(user["_id"]), "friend_id": message.recipient_id, "status": "accepted"},
            {"user_id": message.recipient_id, "friend_id": str(user["_id"]), "status": "accepted"}
        ]
    })
    
    if not friendship:
        raise HTTPException(status_code=403, detail="You can only message friends")
    
    msg = {
        "sender_id": str(user["_id"]),
        "recipient_id": message.recipient_id,
        "content": message.content,
        "read": False,
        "created_at": datetime.utcnow()
    }
    
    result = await db.messages.insert_one(msg)
    
    return {"id": str(result.inserted_id), "message": "Message sent"}

@api_router.get("/messages/{friend_id}", response_model=dict)
async def get_messages(friend_id: str, user = Depends(get_current_user_local)):
    """Get messages with a friend"""
    user_id = str(user["_id"])
    
    messages = await db.messages.find({
        "$or": [
            {"sender_id": user_id, "recipient_id": friend_id},
            {"sender_id": friend_id, "recipient_id": user_id}
        ]
    }).sort("created_at", 1).to_list(100)
    
    # Mark as read
    await db.messages.update_many(
        {"sender_id": friend_id, "recipient_id": user_id, "read": False},
        {"$set": {"read": True}}
    )
    
    return {
        "messages": [{
            "id": str(m["_id"]),
            "sender_id": m["sender_id"],
            "content": m["content"],
            "is_mine": m["sender_id"] == user_id,
            "created_at": m["created_at"].isoformat()
        } for m in messages]
    }

@api_router.get("/messages/unread/count", response_model=dict)
async def get_unread_count(user = Depends(get_current_user_local)):
    """Get count of unread messages"""
    count = await db.messages.count_documents({
        "recipient_id": str(user["_id"]),
        "read": False
    })
    
    return {"count": count}

# ============== USER PROFILE ENDPOINTS ==============

@api_router.get("/users/{user_id}/profile", response_model=dict)
async def get_user_profile(user_id: str, current_user = Depends(get_optional_user_local)):
    """Get a user's public profile"""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "username": user.get("username", ""),
        "callsign": user.get("callsign", user.get("username", "")),
        "created_at": user.get("created_at", datetime.utcnow()).isoformat(),
        "ultimate_search_public": user.get("ultimate_search_public", False),
        "friends_visible": user.get("friends_visible", False)
    }

@api_router.get("/users/{user_id}/ultimate-search", response_model=dict)
async def get_user_ultimate_search(user_id: str, page: int = 1, current_user = Depends(get_optional_user_local)):
    """Get a user's public search results"""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if public
    is_owner = current_user and str(current_user["_id"]) == user_id
    if not is_owner and not user.get("ultimate_search_public", False):
        raise HTTPException(status_code=403, detail="Search results are private")
    
    limit = 50
    skip = (page - 1) * limit
    
    results = await db.search_results.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.search_results.count_documents({"user_id": user_id})
    
    formatted = []
    for r in results:
        formatted.append({
            "id": str(r["_id"]),
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "article_type": r.get("article_type", "Unknown")
        })
    
    return {
        "results": formatted,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.put("/users/settings", response_model=dict)
async def update_user_settings(
    ultimate_search_public: Optional[bool] = Body(None),
    friends_visible: Optional[bool] = Body(None),
    callsign: Optional[str] = Body(None),
    user = Depends(get_current_user_local)
):
    """Update user settings"""
    update_data = {}
    
    if ultimate_search_public is not None:
        update_data["ultimate_search_public"] = ultimate_search_public
    if friends_visible is not None:
        update_data["friends_visible"] = friends_visible
    if callsign is not None:
        update_data["callsign"] = callsign
    
    if update_data:
        await db.users.update_one({"_id": user["_id"]}, {"$set": update_data})
    
    return {"success": True}

@api_router.post("/users/change-password", response_model=dict)
async def change_password(request: PasswordChangeRequest, user = Depends(get_current_user_local)):
    """Change user password"""
    if not user.get("hashed_password"):
        raise HTTPException(status_code=400, detail="Cannot change password for Google-only accounts")
    
    if hash_password(request.current_password) != user["hashed_password"]:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": hash_password(request.new_password)}}
    )
    
    return {"success": True, "message": "Password changed successfully"}

@api_router.get("/users/has-password", response_model=dict)
async def check_has_password(user = Depends(get_current_user_local)):
    """Check if user has a password set"""
    return {"has_password": bool(user.get("hashed_password"))}

# ============== EXTENDED GROUP ENDPOINTS ==============

@api_router.get("/groups/{group_id}")
async def get_group_details(group_id: str, user = Depends(get_current_user_local)):
    """Get detailed group info with posts"""
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get posts
    posts = await db.group_posts.find({"group_id": group_id}).sort("created_at", -1).limit(50).to_list(50)
    
    # Bulk fetch all authors to avoid N+1 queries
    author_ids = list(set([ObjectId(p["author_id"]) for p in posts]))
    authors_list = await db.users.find({"_id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
    authors_map = {str(a["_id"]): a for a in authors_list}
    
    formatted_posts = []
    for p in posts:
        author = authors_map.get(p["author_id"])
        formatted_posts.append({
            "id": str(p["_id"]),
            "content": p["content"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "likes": len(p.get("likes", [])),
            "is_liked": str(user["_id"]) in p.get("likes", []),
            "comment_count": p.get("comment_count", 0),
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {
        "id": str(group["_id"]),
        "name": group["name"],
        "description": group["description"],
        "is_private": group.get("is_private", False),
        "member_count": len(group.get("members", [])),
        "is_member": str(user["_id"]) in group.get("members", []),
        "is_creator": group.get("created_by") == str(user["_id"]),
        "posts": formatted_posts
    }

@api_router.post("/groups/{group_id}/posts")
async def create_group_post(group_id: str, post: GroupPostCreate, user = Depends(get_current_user_local)):
    """Create a post in a group"""
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if str(user["_id"]) not in group.get("members", []):
        raise HTTPException(status_code=403, detail="You must be a member to post")
    
    post_data = {
        "group_id": group_id,
        "author_id": str(user["_id"]),
        "content": post.content,
        "likes": [],
        "comment_count": 0,
        "created_at": datetime.utcnow()
    }
    
    result = await db.group_posts.insert_one(post_data)
    
    return {"id": str(result.inserted_id), "message": "Post created"}

@api_router.post("/groups/{group_id}/posts/{post_id}/like")
async def like_group_post(group_id: str, post_id: str, user = Depends(get_current_user_local)):
    """Like/unlike a group post"""
    post = await db.group_posts.find_one({"_id": ObjectId(post_id), "group_id": group_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user_id = str(user["_id"])
    if user_id in post.get("likes", []):
        await db.group_posts.update_one({"_id": ObjectId(post_id)}, {"$pull": {"likes": user_id}})
        return {"liked": False}
    else:
        await db.group_posts.update_one({"_id": ObjectId(post_id)}, {"$addToSet": {"likes": user_id}})
        return {"liked": True}

@api_router.post("/groups/{group_id}/posts/{post_id}/comment")
async def comment_group_post(group_id: str, post_id: str, content: str = Body(..., embed=True), user = Depends(get_current_user_local)):
    """Add a comment to a group post"""
    post = await db.group_posts.find_one({"_id": ObjectId(post_id), "group_id": group_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = {
        "post_id": post_id,
        "author_id": str(user["_id"]),
        "content": content,
        "created_at": datetime.utcnow()
    }
    
    await db.comments.insert_one(comment)
    await db.group_posts.update_one({"_id": ObjectId(post_id)}, {"$inc": {"comment_count": 1}})
    
    return {"success": True}

# ============== FEED ENDPOINTS ==============

@api_router.get("/feed")
async def get_social_feed(user = Depends(get_current_user_local)):
    """Get social feed with posts from groups and pages"""
    user_id = str(user["_id"])
    
    # Get user's groups
    groups = await db.groups.find({"members": user_id}).to_list(100)
    group_ids = [str(g["_id"]) for g in groups]
    
    # Get posts from groups
    posts = []
    if group_ids:
        group_posts = await db.group_posts.find({"group_id": {"$in": group_ids}}).sort("created_at", -1).limit(30).to_list(30)
        
        # Bulk fetch all authors to avoid N+1 queries
        author_ids = list(set([ObjectId(p["author_id"]) for p in group_posts]))
        authors_list = await db.users.find({"_id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
        authors_map = {str(a["_id"]): a for a in authors_list}
        
        for p in group_posts:
            author = authors_map.get(p["author_id"])
            group = next((g for g in groups if str(g["_id"]) == p["group_id"]), None)
            posts.append({
                "id": str(p["_id"]),
                "type": "group",
                "content": p["content"],
                "author_name": author.get("username", "Unknown") if author else "Unknown",
                "source_name": group["name"] if group else "Unknown Group",
                "source_id": p["group_id"],
                "likes": len(p.get("likes", [])),
                "is_liked": user_id in p.get("likes", []),
                "created_at": p.get("created_at", datetime.utcnow()).isoformat()
            })
    
    # Get feed posts
    friends_data = await get_friends(user)
    friend_ids = [f["id"] for f in friends_data["friends"]]
    feed_posts = await db.feed_posts.find({"author_id": {"$in": [user_id] + friend_ids}}).sort("created_at", -1).limit(20).to_list(20)
    
    # Bulk fetch feed post authors
    feed_author_ids = list(set([ObjectId(p["author_id"]) for p in feed_posts]))
    feed_authors_list = await db.users.find({"_id": {"$in": feed_author_ids}}).to_list(len(feed_author_ids)) if feed_author_ids else []
    feed_authors_map = {str(a["_id"]): a for a in feed_authors_list}
    
    for p in feed_posts:
        author = feed_authors_map.get(p["author_id"])
        posts.append({
            "id": str(p["_id"]),
            "type": "feed",
            "content": p["content"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "source_name": "Feed",
            "likes": len(p.get("likes", [])),
            "is_liked": user_id in p.get("likes", []),
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    # Sort by date
    posts.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"posts": posts[:50]}

@api_router.post("/feed/post")
async def create_feed_post(post: FeedPostCreate, user = Depends(get_current_user_local)):
    """Create a post in the feed"""
    post_data = {
        "author_id": str(user["_id"]),
        "content": post.content,
        "group_id": post.group_id,
        "page_id": post.page_id,
        "likes": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.feed_posts.insert_one(post_data)
    
    return {"id": str(result.inserted_id), "message": "Post created"}

# ============== EXTENDED PAGE ENDPOINTS ==============

@api_router.post("/pages/{page_id}/like")
async def like_page(page_id: str, user = Depends(get_current_user_local)):
    """Like a page"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    user_id = str(user["_id"])
    if user_id in page.get("likes", []):
        await db.pages.update_one({"_id": ObjectId(page_id)}, {"$pull": {"likes": user_id}})
        return {"liked": False}
    else:
        await db.pages.update_one({"_id": ObjectId(page_id)}, {"$addToSet": {"likes": user_id}})
        return {"liked": True}

@api_router.get("/pages/{page_id}")
async def get_page_details(page_id: str, user = Depends(get_current_user_local)):
    """Get page details with posts"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get posts
    posts = await db.page_posts.find({"page_id": page_id}).sort("created_at", -1).limit(50).to_list(50)
    
    # Bulk fetch all authors to avoid N+1 queries
    author_ids = list(set([ObjectId(p["author_id"]) for p in posts]))
    authors_list = await db.users.find({"_id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
    authors_map = {str(a["_id"]): a for a in authors_list}
    
    formatted_posts = []
    for p in posts:
        author = authors_map.get(p["author_id"])
        formatted_posts.append({
            "id": str(p["_id"]),
            "content": p["content"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "likes": len(p.get("likes", [])),
            "is_liked": str(user["_id"]) in p.get("likes", []),
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {
        "id": str(page["_id"]),
        "name": page["name"],
        "description": page["description"],
        "category": page.get("category", "General"),
        "follower_count": len(page.get("followers", [])),
        "like_count": len(page.get("likes", [])),
        "is_following": str(user["_id"]) in page.get("followers", []),
        "is_liked": str(user["_id"]) in page.get("likes", []),
        "is_creator": page.get("created_by") == str(user["_id"]),
        "posts": formatted_posts
    }

@api_router.post("/pages/{page_id}/posts")
async def create_page_post(page_id: str, post: PagePostCreate, user = Depends(get_current_user_local)):
    """Create a post on a page"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    post_data = {
        "page_id": page_id,
        "author_id": str(user["_id"]),
        "content": post.content,
        "likes": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.page_posts.insert_one(post_data)
    
    return {"id": str(result.inserted_id), "message": "Post created"}

@api_router.post("/pages/{page_id}/posts/{post_id}/like")
async def like_page_post(page_id: str, post_id: str, user = Depends(get_current_user_local)):
    """Like/unlike a page post"""
    post = await db.page_posts.find_one({"_id": ObjectId(post_id), "page_id": page_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user_id = str(user["_id"])
    if user_id in post.get("likes", []):
        await db.page_posts.update_one({"_id": ObjectId(post_id)}, {"$pull": {"likes": user_id}})
        return {"liked": False}
    else:
        await db.page_posts.update_one({"_id": ObjectId(post_id)}, {"$addToSet": {"likes": user_id}})
        return {"liked": True}

# ============== ADMIN SETTINGS EXTENSION ==============

@api_router.get("/admin/settings", response_model=List[dict])
async def get_admin_settings(user = Depends(get_current_user_local)):
    """Get admin settings"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await db.settings.find().to_list(100)
    return [{"key": s["key"], "value": s.get("value")} for s in settings]

@api_router.put("/admin/settings/{key}", response_model=dict)
async def update_admin_setting(key: str, value: Any = Body(...), user = Depends(get_current_user_local)):
    """Update an admin setting"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.settings.update_one(
        {"key": key},
        {"$set": {"value": value, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    
    return {"success": True}

@api_router.post("/admin/ban-user/{user_id}")
async def ban_user(user_id: str, user = Depends(get_current_user_local)):
    """Ban a user"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_banned": True}})
    
    return {"success": True}

@api_router.post("/admin/ban-word")
async def ban_word(word: str = Body(...), user = Depends(get_current_user_local)):
    """Ban a word"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.banned_words.update_one(
        {"word": word.lower()},
        {"$set": {"word": word.lower(), "banned_at": datetime.utcnow()}},
        upsert=True
    )
    
    return {"success": True}

@api_router.post("/admin/init", response_model=dict)
async def init_admin_settings():
    """Initialize default admin settings"""
    default_settings = [
        {"key": "subscription_price", "value": 0.99},
        {"key": "results_per_page", "value": 20},
        {"key": "max_search_pages", "value": 99},
        {"key": "unpaid_max_pages", "value": 1},
        {"key": "daily_collate_limit", "value": 100},
        {"key": "max_category_levels", "value": 100},
        {"key": "phd_min_words", "value": 1500},
        {"key": "phd_keyword_count", "value": 3},
        {"key": "tutorial_video_url", "value": ""},
        {"key": "paypal_link", "value": PAYPAL_PAYMENT_LINK},
    ]
    
    for setting in default_settings:
        existing = await db.settings.find_one({"key": setting["key"]})
        if not existing:
            await db.settings.insert_one(setting)
    
    return {"message": "Settings initialized", "count": len(default_settings)}

# ============== GAMIFICATION ENDPOINTS ==============

BADGES = {
    "first_search": {"name": "First Search", "description": "Performed your first search", "icon": "🔍", "xp": 10},
    "explorer": {"name": "Explorer", "description": "Searched 10 times", "icon": "🗺️", "xp": 50},
    "researcher": {"name": "Researcher", "description": "Searched 50 times", "icon": "📚", "xp": 100},
    "protocol_master": {"name": "Protocol Master", "description": "Created 5 protocols", "icon": "⚙️", "xp": 75},
    "social_butterfly": {"name": "Social Butterfly", "description": "Made 5 friends", "icon": "🦋", "xp": 50},
    "contributor": {"name": "Contributor", "description": "Shared a public protocol", "icon": "🤝", "xp": 100},
    "loyal_user": {"name": "Loyal User", "description": "7-day login streak", "icon": "🔥", "xp": 150},
}

def calculate_level(xp: int) -> dict:
    """Calculate user level from XP"""
    level = 1
    xp_for_next = 100
    total_xp_needed = 100
    
    while xp >= total_xp_needed:
        level += 1
        xp_for_next = int(xp_for_next * 1.5)
        total_xp_needed += xp_for_next
    
    progress = (xp - (total_xp_needed - xp_for_next)) / xp_for_next * 100
    
    return {
        "level": level,
        "xp": xp,
        "xp_for_next_level": xp_for_next,
        "progress": min(100, max(0, progress))
    }

@api_router.get("/gamification/profile")
async def get_gamification_profile(user = Depends(get_current_user_local)):
    """Get user's gamification profile"""
    user_id = str(user["_id"])
    
    # Get or create gamification profile
    profile = await db.gamification.find_one({"user_id": user_id})
    if not profile:
        profile = {
            "user_id": user_id,
            "xp": 0,
            "badges": [],
            "login_streak": 0,
            "last_login": None,
            "created_at": datetime.utcnow()
        }
        await db.gamification.insert_one(profile)
    
    level_info = calculate_level(profile.get("xp", 0))
    
    return {
        "xp": profile.get("xp", 0),
        "level": level_info["level"],
        "progress": level_info["progress"],
        "xp_for_next_level": level_info["xp_for_next_level"],
        "badges": profile.get("badges", []),
        "login_streak": profile.get("login_streak", 0)
    }

@api_router.get("/gamification/leaderboard")
async def get_leaderboard(limit: int = Query(20, ge=1, le=100)):
    """Get XP leaderboard"""
    leaders = await db.gamification.find().sort("xp", -1).limit(limit).to_list(limit)
    
    # Bulk fetch all users to avoid N+1 queries
    user_ids = [ObjectId(l["user_id"]) for l in leaders]
    users_list = await db.users.find({"_id": {"$in": user_ids}}).to_list(len(user_ids)) if user_ids else []
    users_map = {str(u["_id"]): u for u in users_list}
    
    leaderboard = []
    for i, l in enumerate(leaders):
        user = users_map.get(l["user_id"])
        if user:
            level_info = calculate_level(l.get("xp", 0))
            leaderboard.append({
                "rank": i + 1,
                "user_id": l["user_id"],
                "username": user.get("username", "Unknown"),
                "callsign": user.get("callsign", user.get("username", "Unknown")),
                "xp": l.get("xp", 0),
                "level": level_info["level"]
            })
    
    return {"leaderboard": leaderboard}

@api_router.get("/gamification/badges")
async def get_all_badges():
    """Get all available badges"""
    return {"badges": BADGES}

@api_router.post("/gamification/award-xp")
async def award_xp(
    amount: int = Body(..., embed=True),
    reason: str = Body("activity", embed=True),
    user = Depends(get_current_user_local)
):
    """Award XP to user"""
    await db.gamification.update_one(
        {"user_id": str(user["_id"])},
        {"$inc": {"xp": amount}},
        upsert=True
    )
    
    return {"success": True, "awarded": amount}

@api_router.post("/gamification/track-login")
async def track_daily_login(user = Depends(get_current_user_local)):
    """Track daily login for streak"""
    user_id = str(user["_id"])
    profile = await db.gamification.find_one({"user_id": user_id})
    
    today = datetime.utcnow().date()
    
    if profile:
        last_login = profile.get("last_login")
        if last_login:
            last_date = last_login.date()
            if last_date == today:
                return {"streak": profile.get("login_streak", 1), "xp_awarded": 0}
            elif (today - last_date).days == 1:
                new_streak = profile.get("login_streak", 0) + 1
            else:
                new_streak = 1
        else:
            new_streak = 1
        
        xp_award = min(new_streak * 5, 50)
        
        await db.gamification.update_one(
            {"user_id": user_id},
            {
                "$set": {"login_streak": new_streak, "last_login": datetime.utcnow()},
                "$inc": {"xp": xp_award}
            }
        )
        
        return {"streak": new_streak, "xp_awarded": xp_award}
    else:
        await db.gamification.insert_one({
            "user_id": user_id,
            "xp": 5,
            "badges": [],
            "login_streak": 1,
            "last_login": datetime.utcnow()
        })
        
        return {"streak": 1, "xp_awarded": 5}

@api_router.get("/gamification/leaderboard/weekly")
async def get_weekly_leaderboard():
    """Get weekly XP leaderboard"""
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": one_week_ago}}},
        {"$group": {"_id": "$user_id", "weekly_xp": {"$sum": "$xp_earned"}}},
        {"$sort": {"weekly_xp": -1}},
        {"$limit": 20}
    ]
    
    weekly_leaders = await db.xp_history.aggregate(pipeline).to_list(20)
    
    # Bulk fetch all users to avoid N+1 queries
    user_ids = [ObjectId(l["_id"]) for l in weekly_leaders]
    users_list = await db.users.find({"_id": {"$in": user_ids}}).to_list(len(user_ids)) if user_ids else []
    users_map = {str(u["_id"]): u for u in users_list}
    
    leaderboard = []
    for i, l in enumerate(weekly_leaders):
        user = users_map.get(l["_id"])
        if user:
            leaderboard.append({
                "rank": i + 1,
                "user_id": l["_id"],
                "username": user.get("username", "Unknown"),
                "weekly_xp": l["weekly_xp"]
            })
    
    return {"leaderboard": leaderboard, "period": "weekly"}

@api_router.get("/gamification/leaderboard/monthly")
async def get_monthly_leaderboard():
    """Get monthly XP leaderboard"""
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": one_month_ago}}},
        {"$group": {"_id": "$user_id", "monthly_xp": {"$sum": "$xp_earned"}}},
        {"$sort": {"monthly_xp": -1}},
        {"$limit": 20}
    ]
    
    monthly_leaders = await db.xp_history.aggregate(pipeline).to_list(20)
    
    # Bulk fetch all users to avoid N+1 queries
    user_ids = [ObjectId(l["_id"]) for l in monthly_leaders]
    users_list = await db.users.find({"_id": {"$in": user_ids}}).to_list(len(user_ids)) if user_ids else []
    users_map = {str(u["_id"]): u for u in users_list}
    
    leaderboard = []
    for i, l in enumerate(monthly_leaders):
        user = users_map.get(l["_id"])
        if user:
            leaderboard.append({
                "rank": i + 1,
                "user_id": l["_id"],
                "username": user.get("username", "Unknown"),
                "monthly_xp": l["monthly_xp"]
            })
    
    return {"leaderboard": leaderboard, "period": "monthly"}

@api_router.post("/gamification/share-badge")
async def share_badge(badge_id: str = Body(..., embed=True), user = Depends(get_current_user_local)):
    """Generate a shareable badge link"""
    if badge_id not in BADGES:
        raise HTTPException(status_code=404, detail="Badge not found")
    
    badge = BADGES[badge_id]
    
    share_record = {
        "user_id": str(user["_id"]),
        "badge_id": badge_id,
        "share_id": generate_token()[:12],
        "created_at": datetime.utcnow()
    }
    
    await db.badge_shares.insert_one(share_record)
    
    return {
        "share_url": f"/badge/{share_record['share_id']}",
        "badge_name": badge["name"],
        "badge_icon": badge["icon"]
    }

# ============== BOOK PROMO ==============

@api_router.get("/book-promo")
async def get_book_promotion():
    """Get book promotion data"""
    return BOOK_PROMO

# ============== NEWSLETTER ENDPOINTS ==============

def get_fallback_newsletter():
    """Generate fallback newsletter content"""
    return f"""
    <h1>InfoPilot Weekly Update</h1>
    <p>Welcome to this week's InfoPilot newsletter!</p>
    <h2>Featured Book: {BOOK_PROMO['title']}</h2>
    <p>By {BOOK_PROMO['author']}</p>
    <p>{BOOK_PROMO['genre']}</p>
    <p>Available for {BOOK_PROMO['price']} on <a href="{BOOK_PROMO['amazon_url']}">Amazon</a></p>
    """

@api_router.post("/newsletter/generate")
async def generate_newsletter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Generate newsletter content"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_current_user_local(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    content = get_fallback_newsletter()
    
    return {"content": content}

@api_router.get("/newsletter/preview")
async def preview_newsletter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Preview newsletter"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_current_user_local(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {"content": get_fallback_newsletter()}

@api_router.post("/newsletter/send")
async def send_newsletter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Send newsletter to all users"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_current_user_local(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    # Get all user emails
    users = await db.users.find({"email": {"$exists": True}}).to_list(1000)
    emails = [u["email"] for u in users if u.get("email")]
    
    content = get_fallback_newsletter()
    
    try:
        for email in emails[:100]:  # Limit to 100 for safety
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": email,
                "subject": f"InfoPilot Weekly - {datetime.now().strftime('%B %d, %Y')}",
                "html": content
            })
        
        await db.newsletters.insert_one({
            "sent_at": datetime.utcnow(),
            "recipient_count": len(emails),
            "content": content
        })
        
        return {"success": True, "sent_to": len(emails)}
    except Exception as e:
        logger.error(f"Newsletter send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/newsletter/test-email")
async def send_test_email(
    email: str = Body(..., embed=True),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Send test newsletter email"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_current_user_local(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": email,
            "subject": "InfoPilot Test Newsletter",
            "html": get_fallback_newsletter()
        })
        
        return {"success": True, "sent_to": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/newsletter/history")
async def get_newsletter_history(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get newsletter history"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_current_user_local(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    history = await db.newsletters.find().sort("sent_at", -1).limit(20).to_list(20)
    
    return {
        "history": [{
            "sent_at": h["sent_at"].isoformat(),
            "recipient_count": h.get("recipient_count", 0)
        } for h in history]
    }

@api_router.get("/newsletter/schedule")
async def get_newsletter_schedule(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get newsletter schedule"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_current_user_local(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    schedule = await db.settings.find_one({"key": "newsletter_schedule"})
    
    return schedule.get("value", {
        "enabled": False,
        "day_of_week": 0,
        "hour": 9,
        "timezone": "UTC"
    }) if schedule else {"enabled": False, "day_of_week": 0, "hour": 9, "timezone": "UTC"}

@api_router.post("/newsletter/schedule")
async def update_newsletter_schedule(
    schedule: dict = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update newsletter schedule"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_current_user_local(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.settings.update_one(
        {"key": "newsletter_schedule"},
        {"$set": {"value": schedule, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    
    return {"success": True, "schedule": schedule}

@api_router.post("/newsletter/send-scheduled")
async def check_and_send_scheduled_newsletter():
    """Check and send scheduled newsletter (called by cron)"""
    schedule = await db.settings.find_one({"key": "newsletter_schedule"})
    if not schedule or not schedule.get("value", {}).get("enabled"):
        return {"sent": False, "reason": "Scheduling disabled"}
    
    # For now, just return - actual scheduling would need a job scheduler
    return {"sent": False, "reason": "Manual trigger only"}

# ============== PROTOCOL VALIDATION ==============

@api_router.post("/protocol/validate")
async def validate_protocol(protocol: str = Body(..., embed=True)):
    """Validate a protocol string"""
    return ProtocolParser.debug_protocol(protocol)

@api_router.post("/protocol/debug")
async def debug_protocol(request: ProtocolDebugRequest, user = Depends(get_current_user_local)):
    """Debug a protocol with test text"""
    result = ProtocolParser.debug_protocol(request.protocol)
    
    if request.test_text and result["valid"]:
        groups = ProtocolParser.parse_protocol(request.protocol)
        matches, score = ProtocolParser.match_result({"content": request.test_text, "title": "", "snippet": ""}, groups)
        result["test_result"] = {
            "matches": matches,
            "score": score,
            "test_text_length": len(request.test_text)
        }
    
    return result

# ============== PAYPAL WEBHOOK ==============

@api_router.post("/paypal/webhook")
async def paypal_webhook(event: PayPalWebhookEvent):
    """Handle PayPal webhook events"""
    logger.info(f"PayPal webhook: {event.event_type}")
    
    if event.event_type == "PAYMENT.CAPTURE.COMPLETED":
        resource = event.resource
        
        # Extract custom data if available
        custom_id = resource.get("custom_id", "")
        
        if custom_id:
            # Parse custom_id (format: "protocol_purchase:user_id:protocol_id")
            parts = custom_id.split(":")
            if len(parts) == 3 and parts[0] == "protocol_purchase":
                user_id = parts[1]
                protocol_id = parts[2]
                
                # Complete the purchase
                protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
                if protocol:
                    price = protocol["price"]
                    creator_earnings = price * (1 - MARKETPLACE_PLATFORM_FEE)
                    
                    # Record purchase
                    await db.marketplace_purchases.insert_one({
                        "protocol_id": protocol_id,
                        "user_id": user_id,
                        "payment_id": resource.get("id", ""),
                        "price": price,
                        "creator_earnings": creator_earnings,
                        "status": "completed",
                        "created_at": datetime.utcnow()
                    })
                    
                    # Update protocol stats
                    await db.marketplace_protocols.update_one(
                        {"_id": ObjectId(protocol_id)},
                        {"$inc": {"total_sales": 1, "total_revenue": price, "creator_earnings": creator_earnings}}
                    )
                    
                    # Update creator earnings
                    await db.users.update_one(
                        {"_id": ObjectId(protocol["creator_id"])},
                        {"$inc": {"marketplace_earnings": creator_earnings}}
                    )
    
    return {"status": "received"}

@api_router.post("/marketplace/initiate-purchase")
async def initiate_purchase(protocol_id: str = Body(...), user = Depends(get_current_user_local)):
    """Initiate a protocol purchase"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol["creator_id"] == str(user["_id"]):
        raise HTTPException(status_code=400, detail="Cannot purchase your own protocol")
    
    # Check if already owned
    existing = await db.marketplace_purchases.find_one({
        "protocol_id": protocol_id,
        "user_id": str(user["_id"])
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already purchased")
    
    # Create pending purchase
    pending = {
        "protocol_id": protocol_id,
        "user_id": str(user["_id"]),
        "price": protocol["price"],
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = await db.pending_purchases.insert_one(pending)
    
    return {
        "pending_id": str(result.inserted_id),
        "protocol_name": protocol["name"],
        "price": protocol["price"],
        "paypal_link": PAYPAL_PAYMENT_LINK
    }

@api_router.post("/marketplace/confirm-payment")
async def confirm_payment(data: ManualPaymentConfirm, user = Depends(get_current_user_local)):
    """Manually confirm a payment"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(data.protocol_id)})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check not already purchased
    existing = await db.marketplace_purchases.find_one({
        "protocol_id": data.protocol_id,
        "user_id": str(user["_id"])
    })
    if existing:
        return {"success": True, "protocol": protocol["protocol"], "already_owned": True}
    
    price = protocol["price"]
    creator_earnings = price * (1 - MARKETPLACE_PLATFORM_FEE)
    
    # Record purchase
    await db.marketplace_purchases.insert_one({
        "protocol_id": data.protocol_id,
        "user_id": str(user["_id"]),
        "payment_id": data.transaction_id,
        "price": price,
        "creator_earnings": creator_earnings,
        "status": "completed",
        "created_at": datetime.utcnow()
    })
    
    # Update stats
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(data.protocol_id)},
        {"$inc": {"total_sales": 1, "total_revenue": price, "creator_earnings": creator_earnings}}
    )
    
    await db.users.update_one(
        {"_id": ObjectId(protocol["creator_id"])},
        {"$inc": {"marketplace_earnings": creator_earnings}}
    )
    
    return {"success": True, "protocol": protocol["protocol"]}

@api_router.get("/marketplace/pending-purchases")
async def get_pending_purchases(user = Depends(get_current_user_local)):
    """Get user's pending purchases"""
    pending = await db.pending_purchases.find({
        "user_id": str(user["_id"]),
        "status": "pending"
    }).to_list(100)
    
    return {
        "pending": [{
            "id": str(p["_id"]),
            "protocol_id": p["protocol_id"],
            "price": p["price"],
            "created_at": p["created_at"].isoformat()
        } for p in pending]
    }

@api_router.get("/marketplace/seller/sales")
async def get_seller_sales(user = Depends(get_current_user_local)):
    """Get seller's sales history"""
    # Get all protocols by this user
    protocols = await db.marketplace_protocols.find({"creator_id": str(user["_id"])}).to_list(100)
    protocol_ids = [str(p["_id"]) for p in protocols]
    
    # Get all purchases of these protocols
    purchases = await db.marketplace_purchases.find({
        "protocol_id": {"$in": protocol_ids},
        "status": "completed"
    }).sort("created_at", -1).to_list(100)
    
    sales = []
    for p in purchases:
        protocol = next((pr for pr in protocols if str(pr["_id"]) == p["protocol_id"]), None)
        sales.append({
            "protocol_name": protocol["name"] if protocol else "Unknown",
            "price": p["price"],
            "earnings": p["creator_earnings"],
            "sold_at": p["created_at"].isoformat()
        })
    
    return {"sales": sales}

# ============== QUOTES GALLERY ==============

@api_router.get("/quotes/gallery")
async def get_quote_gallery():
    """Get quotes from the book for the gallery with categories"""
    quotes = [
        # Hilarious quotes
        {"quote": "I told my therapist about the alien. She said, 'That's a lot to unpack.' I said, 'You should see my garage.'", "category": "hilarious", "context": "John's first therapy session after the encounter"},
        {"quote": "The extraterrestrial looked at my tax returns and said, 'Even we don't understand this.'", "category": "hilarious", "context": "When cosmic beings meet earthly bureaucracy"},
        {"quote": "My wife asked if the alien was male or female. I said, 'Honey, it's from another dimension. It doesn't have a gender, it has a vibe.'", "category": "hilarious", "context": "Explaining interdimensional beings to your spouse"},
        {"quote": "The Navy taught me to fly jets. Nothing prepares you for explaining to your kids why daddy talks to the ceiling.", "category": "hilarious", "context": "Parenting after supernatural experiences"},
        {"quote": "I've flown 10 types of aircraft. The hardest landing? Telling my mother-in-law about Evelyn.", "category": "hilarious", "context": "Family dynamics meet the supernatural"},
        {"quote": "The cosmic entity said I was chosen. I asked if there was a return policy.", "category": "hilarious", "context": "When destiny comes knocking"},
        {"quote": "My dog saw the apparition before I did. He's been sleeping with one eye open ever since.", "category": "hilarious", "context": "Pets and the paranormal"},
        {"quote": "I asked the universe for a sign. It sent me a 7-foot glowing being. Next time I'll be more specific.", "category": "hilarious", "context": "Be careful what you wish for"},
        {"quote": "The alien's first words to me were 'We've been watching you.' I said, 'So has the IRS. Get in line.'", "category": "hilarious", "context": "First contact priorities"},
        {"quote": "My psychiatrist retired after our sessions. Said he needed to 'reassess his understanding of reality.'", "category": "hilarious", "context": "The impact of truth on professionals"},
        {"quote": "Evelyn communicates through dreams. My wife says I talk in my sleep. Apparently, I'm bilingual now.", "category": "hilarious", "context": "Supernatural side effects"},
        {"quote": "The being said time is an illusion. I said, 'Tell that to my mortgage company.'", "category": "hilarious", "context": "Cosmic wisdom meets earthly obligations"},
        {"quote": "I've seen things that would make a horror movie director quit. But nothing scarier than my wife when I forget our anniversary.", "category": "hilarious", "context": "Perspective on fear"},
        {"quote": "The entity showed me the secrets of the universe. I still can't figure out why socks disappear in the dryer.", "category": "hilarious", "context": "The real mysteries of life"},
        {"quote": "My neighbor thinks I'm crazy. I think he's crazy for paying $7 for coffee. We're both probably right.", "category": "hilarious", "context": "Suburban philosophy"},
        
        # Profound quotes
        {"quote": "Sometimes the most extraordinary journeys begin with the simplest questions.", "category": "profound", "context": "The beginning of John's journey"},
        {"quote": "In the silence between words, I found the loudest truths.", "category": "profound", "context": "Learning to listen to the universe"},
        {"quote": "Evelyn taught me that love doesn't require understanding—just acceptance.", "category": "profound", "context": "The nature of unconditional love"},
        {"quote": "The supernatural isn't always about ghosts and spirits. Sometimes it's about the inexplicable bond between souls.", "category": "profound", "context": "Redefining the paranormal"},
        {"quote": "Every letter was a prayer, every response a miracle.", "category": "profound", "context": "The sacred nature of communication"},
        {"quote": "In the end, it wasn't about proving anything. It was about living authentically.", "category": "profound", "context": "The ultimate lesson"},
        {"quote": "We're either infinite Love or we're not. Can I say that one last time?", "category": "profound", "context": "John's philosophical repetition"},
        {"quote": "The truth is stranger than fiction, but funnier too if you look at it right.", "category": "profound", "context": "Finding humor in the impossible"},
        
        # Dad jokes
        {"quote": "Why did the alien go to therapy? Because it had too many space issues.", "category": "dad_joke", "context": "John's attempt at cosmic humor"},
        {"quote": "I told Evelyn a joke about time travel. She didn't laugh. She will yesterday.", "category": "dad_joke", "context": "Interdimensional comedy"},
        {"quote": "What do you call a supernatural being who tells bad jokes? A groan-ost.", "category": "dad_joke", "context": "Peak dad humor"},
        {"quote": "Why don't aliens eat clowns? Because they taste funny.", "category": "dad_joke", "context": "Classic with a twist"},
        {"quote": "I asked the cosmic entity for wisdom. It said, 'Don't eat yellow snow.' Even the universe has dad jokes.", "category": "dad_joke", "context": "Universal humor"},
        {"quote": "What's an alien's favorite key on the keyboard? The space bar.", "category": "dad_joke", "context": "Tech-savvy extraterrestrials"},
        {"quote": "Why did the ghost go to the bar? For the boos.", "category": "dad_joke", "context": "Supernatural refreshments"},
        {"quote": "I told my wife I communicate with beings from another dimension. She said, 'That explains why you never hear me.'", "category": "dad_joke", "context": "Marriage humor"},
        {"quote": "What do you call a lazy extraterrestrial? An unidentified lying object.", "category": "dad_joke", "context": "UFO wordplay"},
        {"quote": "Why don't secrets work in space? Because there's no atmosphere.", "category": "dad_joke", "context": "Cosmic confidentiality"},
        {"quote": "I asked Evelyn about the meaning of life. She said '42.' Even interdimensional beings read Douglas Adams.", "category": "dad_joke", "context": "Literary references across dimensions"},
        {"quote": "What's a ghost's favorite dessert? I scream.", "category": "dad_joke", "context": "Supernatural sweets"},
        
        # Chapter teasers
        {"quote": "Chapter 7 changed everything. Not because of what I saw, but because of what I finally understood.", "category": "chapter_teaser", "context": "A pivotal moment"},
        {"quote": "The night of the first contact, I was just trying to fix a leaky faucet. The universe had other plans.", "category": "chapter_teaser", "context": "How it all began"},
        {"quote": "When you've seen what I've seen, comedy becomes a survival mechanism.", "category": "chapter_teaser", "context": "Coping with the impossible"},
        {"quote": "The letters started arriving before I sent them. That's when I knew time wasn't what I thought it was.", "category": "chapter_teaser", "context": "Temporal anomalies"},
        {"quote": "My Navy training prepared me for combat. Nothing prepares you for a conversation with eternity.", "category": "chapter_teaser", "context": "Military meets metaphysical"},
        {"quote": "The day I stopped trying to explain and started trying to understand—that's when the real journey began.", "category": "chapter_teaser", "context": "A shift in perspective"},
        {"quote": "Evelyn's first message was three words. Those three words rewrote my entire existence.", "category": "chapter_teaser", "context": "The power of words"},
        {"quote": "I've flown through storms that would terrify most pilots. But nothing compared to the storm inside my own mind.", "category": "chapter_teaser", "context": "Internal battles"},
        {"quote": "The photograph changed everything. Not because of what it showed, but because of what it proved.", "category": "chapter_teaser", "context": "Evidence of the impossible"},
        
        # Wild elements
        {"quote": "The being materialized in my living room at 3 AM. My first thought was, 'I should have vacuumed.'", "category": "wild_element", "context": "Priorities during first contact"},
        {"quote": "It spoke in colors I'd never seen and sounds I'd never heard. My brain did its best.", "category": "wild_element", "context": "Sensory overload"},
        {"quote": "The entity showed me the birth of stars. I showed it my stamp collection. Fair trade.", "category": "wild_element", "context": "Cultural exchange"},
        {"quote": "Time folded like origami. I experienced my entire life in what felt like a sneeze.", "category": "wild_element", "context": "Temporal distortion"},
        {"quote": "The cosmic being had no face, yet I knew it was smiling. Don't ask me how.", "category": "wild_element", "context": "Intuitive understanding"},
        {"quote": "I touched infinity. It was warm and smelled like my grandmother's kitchen.", "category": "wild_element", "context": "The comfort of the cosmos"},
        {"quote": "The alien showed me parallel universes. In one of them, I'm a dentist. I prefer this reality.", "category": "wild_element", "context": "Multiverse preferences"},
        {"quote": "Evelyn exists outside of time. She's seen my birth and my death. She still thinks I'm funny.", "category": "wild_element", "context": "Eternal perspective"},
        {"quote": "The being communicated through my dreams for months. My sleep schedule has never recovered.", "category": "wild_element", "context": "Supernatural side effects"},
        {"quote": "I asked to see the future. It showed me a world where people are kind to each other. I cried.", "category": "wild_element", "context": "Hope for humanity"},
        {"quote": "The entity's ship wasn't metal or light. It was made of pure intention. Try explaining that to the FAA.", "category": "wild_element", "context": "Unconventional aircraft"},
        {"quote": "My consciousness left my body and toured the galaxy. The in-flight movie was my own memories.", "category": "wild_element", "context": "Astral travel"},
        {"quote": "The being said humans are 'adorably confused.' I couldn't argue.", "category": "wild_element", "context": "Cosmic perspective on humanity"},
        {"quote": "I've seen the edge of the universe. It's not what you'd expect. It's more like a suggestion.", "category": "wild_element", "context": "The nature of reality"},
        {"quote": "Evelyn showed me that death isn't an ending. It's more like changing channels.", "category": "wild_element", "context": "Redefining mortality"},
        {"quote": "The alien's goodbye gift was the ability to see auras. Now I know why my neighbor is always angry.", "category": "wild_element", "context": "Supernatural abilities"},
        {"quote": "I asked the cosmic being about God. It laughed—not mockingly, but like a parent watching a child discover something obvious.", "category": "wild_element", "context": "Divine revelations"},
        {"quote": "The entity folded space to show me Earth from a million light-years away. We looked so small. So precious.", "category": "wild_element", "context": "Perspective on our planet"},
        {"quote": "My DNA was 'upgraded' during the encounter. I still can't do math, but I can feel emotions from plants.", "category": "wild_element", "context": "Unexpected enhancements"},
        {"quote": "The being's final message was written in light across my ceiling. My wife thought I'd installed new fixtures.", "category": "wild_element", "context": "Supernatural home improvement"},
        
        # Marketing quotes
        {"quote": "If you've ever wondered what happens when a Navy pilot meets an interdimensional being, this book has answers.", "category": "marketing", "context": "Book pitch"},
        {"quote": "Part memoir, part cosmic adventure, all heart. This is the story I never planned to tell.", "category": "marketing", "context": "Genre description"},
        {"quote": "19 five-star reviews can't be wrong. Unless they're all from parallel universes.", "category": "marketing", "context": "Review humor"},
        {"quote": "The comical side is exceedingly brilliant... imagination off the charts. A true story that defies belief!", "category": "marketing", "context": "Professional review quote"},
        {"quote": "This memoir is a profound and unforgettable literary piece.", "category": "marketing", "context": "Readers' Favorite review"},
        {"quote": "Comedy that creeps into your mind and causes abrupt laughter.", "category": "marketing", "context": "Reader testimonial"},
        {"quote": "Written by a Navy pilot who flew 10 aircraft types. Verified by the universe.", "category": "marketing", "context": "Author credentials"},
        {"quote": "Available for $2.99. That's less than a coffee and infinitely more mind-expanding.", "category": "marketing", "context": "Value proposition"},
        {"quote": "Hollywood couldn't resist. OPTIONED FOR FILM!", "category": "marketing", "context": "Industry recognition"},
        {"quote": "Extraterrestrial encounters & cosmic visions. Also, really good dad jokes.", "category": "marketing", "context": "Content summary"},
        {"quote": "The truth is out there. And it's hilarious.", "category": "marketing", "context": "Tagline"},
    ]
    
    # Define categories with counts
    categories = [
        {"id": "hilarious", "name": "Hilarious", "count": len([q for q in quotes if q["category"] == "hilarious"])},
        {"id": "profound", "name": "Profound", "count": len([q for q in quotes if q["category"] == "profound"])},
        {"id": "dad_joke", "name": "Dad Jokes", "count": len([q for q in quotes if q["category"] == "dad_joke"])},
        {"id": "chapter_teaser", "name": "Chapter Teasers", "count": len([q for q in quotes if q["category"] == "chapter_teaser"])},
        {"id": "wild_element", "name": "Wild Elements", "count": len([q for q in quotes if q["category"] == "wild_element"])},
        {"id": "marketing", "name": "Marketing", "count": len([q for q in quotes if q["category"] == "marketing"])},
    ]
    
    return {
        "quotes": quotes,
        "categories": categories,
        "book": BOOK_PROMO
    }

# ============== ANALYTICS DASHBOARD ==============

@api_router.get("/analytics/dashboard")
async def get_analytics_dashboard(user = Depends(get_current_user_local)):
    """Get analytics dashboard data (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # User stats
    total_users = await db.users.count_documents({})
    active_users_24h = await db.sessions.count_documents({
        "created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
    })
    new_users_today = await db.users.count_documents({
        "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
    })
    new_users_week = await db.users.count_documents({
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    })
    
    # Search stats
    total_searches = await db.search_results.count_documents({})
    searches_today = await db.search_results.count_documents({
        "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
    })
    searches_week = await db.search_results.count_documents({
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    })
    
    # Protocol stats
    total_protocols = await db.categories.count_documents({})
    public_protocols = await db.categories.count_documents({"is_public": True})
    
    # Marketplace stats
    active_listings = await db.marketplace_protocols.count_documents({"status": "active"})
    total_purchases = await db.marketplace_purchases.count_documents({})
    
    # Revenue
    revenue_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]
    revenue_result = await db.marketplace_purchases.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Social/Engagement stats
    total_groups = await db.groups.count_documents({})
    total_pages = await db.pages.count_documents({})
    total_posts = await db.group_posts.count_documents({}) + await db.feed_posts.count_documents({})
    
    # Popular search terms (from recent searches)
    popular_terms = []
    try:
        terms_pipeline = [
            {"$match": {"created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}}},
            {"$group": {"_id": "$query", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        terms_result = await db.search_queries.aggregate(terms_pipeline).to_list(10)
        popular_terms = [{"term": t["_id"], "count": t["count"]} for t in terms_result if t["_id"]]
    except Exception:
        pass
    
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "users": {
            "total": total_users,
            "active_24h": active_users_24h,
            "new_today": new_users_today,
            "new_this_week": new_users_week
        },
        "searches": {
            "total": total_searches,
            "today": searches_today,
            "this_week": searches_week
        },
        "protocols": {
            "total": total_protocols,
            "public": public_protocols
        },
        "marketplace": {
            "active_listings": active_listings,
            "total_purchases": total_purchases,
            "revenue": total_revenue
        },
        "engagement": {
            "total_groups": total_groups,
            "total_pages": total_pages,
            "total_posts": total_posts
        },
        "popular_search_terms": popular_terms
    }

@api_router.get("/analytics/search-trends")
async def get_search_trends(days: int = Query(7, ge=1, le=30), user = Depends(get_current_user_local)):
    """Get search trends over time"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    trends = await db.search_results.aggregate(pipeline).to_list(days)
    
    return {
        "trends": [{"date": t["_id"], "searches": t["count"]} for t in trends]
    }

# ============== PROTOCOL TEMPLATES ==============

@api_router.get("/protocol-templates")
async def get_protocol_templates(
    category: Optional[str] = None,
    public_only: bool = Query(False),
    user = Depends(get_optional_user_local)
):
    """Get protocol templates"""
    query = {}
    
    if public_only:
        query["is_public"] = True
    elif user:
        query["$or"] = [
            {"user_id": str(user["_id"])},
            {"is_public": True}
        ]
    else:
        query["is_public"] = True
    
    if category:
        query["category"] = category
    
    templates = await db.protocol_templates.find(query).sort("use_count", -1).to_list(100)
    
    return {
        "templates": [{
            "id": str(t["_id"]),
            "name": t["name"],
            "description": t.get("description", ""),
            "protocol": t["protocol"],
            "category": t.get("category", "General"),
            "tags": t.get("tags", []),
            "is_public": t.get("is_public", False),
            "use_count": t.get("use_count", 0),
            "creator_name": t.get("creator_name", "Unknown"),
            "is_owner": user and t["user_id"] == str(user["_id"])
        } for t in templates]
    }

@api_router.post("/protocol-templates")
async def create_protocol_template(template: ProtocolTemplate, user = Depends(get_current_user_local)):
    """Create a protocol template"""
    is_valid, message = ProtocolParser.validate_protocol(template.protocol)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid protocol: {message}")
    
    template_data = {
        "name": template.name,
        "description": template.description,
        "protocol": template.protocol,
        "category": template.category or "General",
        "tags": template.tags or [],
        "is_public": template.is_public,
        "user_id": str(user["_id"]),
        "creator_name": user.get("username", "Unknown"),
        "use_count": 0,
        "created_at": datetime.utcnow()
    }
    
    result = await db.protocol_templates.insert_one(template_data)
    
    return {"id": str(result.inserted_id), "message": "Template created"}

@api_router.put("/protocol-templates/{template_id}")
async def update_protocol_template(
    template_id: str,
    template: ProtocolTemplate,
    user = Depends(get_current_user_local)
):
    """Update a protocol template"""
    existing = await db.protocol_templates.find_one({"_id": ObjectId(template_id)})
    
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if existing["user_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not your template")
    
    is_valid, message = ProtocolParser.validate_protocol(template.protocol)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid protocol: {message}")
    
    await db.protocol_templates.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": {
            "name": template.name,
            "description": template.description,
            "protocol": template.protocol,
            "category": template.category or "General",
            "tags": template.tags or [],
            "is_public": template.is_public,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Template updated"}

@api_router.delete("/protocol-templates/{template_id}")
async def delete_protocol_template(template_id: str, user = Depends(get_current_user_local)):
    """Delete a protocol template"""
    existing = await db.protocol_templates.find_one({"_id": ObjectId(template_id)})
    
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if existing["user_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not your template")
    
    await db.protocol_templates.delete_one({"_id": ObjectId(template_id)})
    
    return {"message": "Template deleted"}

@api_router.post("/protocol-templates/{template_id}/use")
async def use_protocol_template(template_id: str, user = Depends(get_current_user_local)):
    """Use a protocol template"""
    template = await db.protocol_templates.find_one({"_id": ObjectId(template_id)})
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template["user_id"] != str(user["_id"]) and not template.get("is_public"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.protocol_templates.update_one(
        {"_id": ObjectId(template_id)},
        {"$inc": {"use_count": 1}}
    )
    
    return {"protocol": template["protocol"], "name": template["name"]}

@api_router.get("/protocol-templates/categories")
async def get_template_categories():
    """Get template categories"""
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    categories = await db.protocol_templates.aggregate(pipeline).to_list(50)
    
    return {
        "categories": [{"name": c["_id"] or "General", "count": c["count"]} for c in categories]
    }

@api_router.get("/protocol-templates/popular")
async def get_popular_templates(limit: int = Query(10, ge=1, le=50)):
    """Get popular templates"""
    templates = await db.protocol_templates.find({"is_public": True}).sort("use_count", -1).limit(limit).to_list(limit)
    
    return {
        "templates": [{
            "id": str(t["_id"]),
            "name": t["name"],
            "description": t.get("description", ""),
            "protocol": t["protocol"],
            "category": t.get("category", "General"),
            "creator_name": t.get("creator_name", "Unknown"),
            "use_count": t.get("use_count", 0)
        } for t in templates]
    }

# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    return {"message": "InfoPilot API v2.0", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ============== INCLUDE ROUTERS ==============

# Import new routers
from routes.notifications import router as notifications_router
from routes.export import router as export_router

# Initialize routers that need database
init_bundles_router(db)
init_push_router(db)
init_chat_router(db)

# Include modular routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(social_router, prefix="/api")
app.include_router(marketplace_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")
app.include_router(gamification_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(newsletter_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(collaborate_router, prefix="/api")
app.include_router(polls_router, prefix="/api")
app.include_router(tutorials_router, prefix="/api")
app.include_router(rate_limiting_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(ai_suggestions_router, prefix="/api")
app.include_router(protocol_analytics_router, prefix="/api")
app.include_router(ab_testing_router, prefix="/api")
app.include_router(ab_optimizer_router, prefix="/api")
app.include_router(revenue_forecast_router, prefix="/api")
app.include_router(email_reports_router, prefix="/api")
app.include_router(unified_chat_router, prefix="/api")
app.include_router(easter_eggs_router, prefix="/api")
app.include_router(legal_router, prefix="/api")
app.include_router(bundles_router)
app.include_router(push_router)
app.include_router(chat_router)

# Include the local api_router
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== DATABASE STARTUP ==============

async def create_indexes_with_retry(max_retries=5, delay=3):
    """Create database indexes with retry logic"""
    for attempt in range(max_retries):
        try:
            await client.admin.command('ping')
            logger.info(f"MongoDB connection successful (attempt {attempt + 1})")
            
            await db.users.create_index("email", unique=True)
            await db.users.create_index("username", unique=True)
            await db.categories.create_index([("user_id", 1), ("name", 1)])
            await db.search_results.create_index([("user_id", 1), ("url", 1)])
            await db.newsletters.create_index([("generated_at", -1)])
            await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
            await db.notifications.create_index([("user_id", 1), ("read", 1)])
            logger.info("Database indexes created successfully")
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts")
                return False

@app.on_event("startup")
async def startup_db_client():
    await create_indexes_with_retry()
    # Start the email scheduler for automated reports
    try:
        from services.email_scheduler import start_scheduler
        start_scheduler()
        logger.info("🚀 Email scheduler started successfully!")
    except Exception as e:
        logger.error(f"Failed to start email scheduler: {e}")
    
    # Start the A/B optimizer scheduler
    try:
        from services.ab_optimizer import start_optimizer_scheduler
        start_optimizer_scheduler()
        logger.info("🤖 A/B Optimizer scheduler started successfully!")
    except Exception as e:
        logger.error(f"Failed to start A/B optimizer scheduler: {e}")
    
    # Start the tri-weekly newsletter scheduler
    try:
        from services.triweekly_newsletter import start_triweekly_scheduler
        start_triweekly_scheduler()
        logger.info("📬 Tri-weekly newsletter scheduler started successfully!")
    except Exception as e:
        logger.error(f"Failed to start tri-weekly newsletter scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop the email scheduler
    try:
        from services.email_scheduler import stop_scheduler
        stop_scheduler()
        logger.info("📧 Email scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop email scheduler: {e}")
    
    # Stop the A/B optimizer scheduler
    try:
        from services.ab_optimizer import stop_optimizer_scheduler
        stop_optimizer_scheduler()
        logger.info("🤖 A/B Optimizer scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop A/B optimizer scheduler: {e}")
    
    # Stop the tri-weekly newsletter scheduler
    try:
        from services.triweekly_newsletter import stop_triweekly_scheduler
        stop_triweekly_scheduler()
        logger.info("📬 Tri-weekly newsletter scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop tri-weekly newsletter scheduler: {e}")
    
    client.close()
