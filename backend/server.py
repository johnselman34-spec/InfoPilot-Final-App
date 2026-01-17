"""
InfoPilot Explorer - Main FastAPI Application
Refactored with modular routers
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Body, UploadFile, File
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
from routes.category_export import router as category_export_router

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
BING_API_KEY = os.environ.get('BING_API_KEY')

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
    async def search_bing(query: str, num_results: int = 50) -> List[Dict[str, Any]]:
        """Use Bing Web Search API"""
        results = []
        
        if not BING_API_KEY:
            return results
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Ocp-Apim-Subscription-Key": BING_API_KEY
                }
                params = {
                    "q": query,
                    "count": min(num_results, 50),
                    "offset": 0,
                    "mkt": "en-US",
                    "safesearch": "Moderate"
                }
                
                response = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    web_pages = data.get("webPages", {}).get("value", [])
                    
                    for r in web_pages:
                        url = r.get("url", "")
                        if not url:
                            continue
                        
                        try:
                            parsed = urllib.parse.urlparse(url)
                            root_domain = parsed.netloc
                        except Exception:
                            root_domain = ""
                        
                        results.append({
                            "url": url,
                            "title": r.get("name", ""),
                            "snippet": r.get("snippet", ""),
                            "content": r.get("snippet", ""),
                            "root_domain": root_domain,
                            "source": "bing",
                            "date_published": r.get("dateLastCrawled", "")
                        })
                    
                    logger.info(f"Bing Search returned {len(results)} results")
                else:
                    error_text = response.text
                    logger.warning(f"Bing Search API error: {response.status_code} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Bing Search error: {e}")
        
        return results
    
    @staticmethod
    async def search(query: str, num_results: int = 200) -> List[Dict[str, Any]]:
        """Aggregate search from multiple sources: Google (SerpAPI), Bing, DuckDuckGo, Brave"""
        all_results = []
        seen_urls = set()
        
        # Try SerpAPI first if available (Google)
        if SERPAPI_KEY and SERPAPI_AVAILABLE:
            serp_results = await ExtendedWebSearchService.search_serpapi(query, min(70, num_results))
            for r in serp_results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)
        
        # Bing Search (Microsoft's search engine)
        if BING_API_KEY and len(all_results) < num_results:
            bing_results = await ExtendedWebSearchService.search_bing(query, min(50, num_results - len(all_results)))
            for r in bing_results:
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
                "bing": {
                    "name": "Bing",
                    "available": bool(BING_API_KEY),
                    "description": "Microsoft Bing search engine"
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
                bool(BING_API_KEY),
                bool(BRAVE_API_KEY),
                DDGS_AVAILABLE,
                True  # Basic always available
            ])
        }



# ============== ARTICLE CLASSIFIER ==============

class ArticleClassifier:
    """
    Classify articles based on content with expanded document types.
    Uses Admin-controllable InfoJet 2.0 protocols for classification.
    
    Supported Types:
    - PhD Informative: Academic content by credentialed professionals
    - Informative: Educational content meeting protocol criteria
    - InfoPilot Exclusive: Content written by InfoPilot writers
    - InfoBook Exclusive: Content written by InfoBook writers
    - News Article: Current events and journalism (default fallback)
    - Blog Post: Personal blogs and opinion pieces
    - Forum: Discussion boards (forum in title)
    - Personal Report (Organic): First-hand reports by members
    - Personal Report (Collected): Extracted personal narratives
    - Academic Paper: Scholarly research
    - Government: Official government documents
    - Wiki: Wikipedia and wiki-based content  
    - Video: Video content
    - PDF Document: PDF files
    - Webpage: General web pages (catch-all)
    """
    
    # Default protocols (can be overridden by admin settings)
    DEFAULT_PHD_PROTOCOL = "(Ph.D. or PhD or D.Phil. or Dr.)"
    DEFAULT_INFORMATIVE_PROTOCOL = "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)"
    DEFAULT_NEWS_PROTOCOL = "(news) & (news or story or news story) & (news or story or news story)"
    DEFAULT_BLOG_PROTOCOL = "(blog)"
    DEFAULT_FORUM_PROTOCOL = "(forum)"
    DEFAULT_PERSONAL_PROTOCOL = "(I)"
    
    @classmethod
    async def get_settings(cls):
        """Get current document type settings from database"""
        settings = {}
        keys = [
            "doctype_phd_min_words", "doctype_phd_keyword_count", "doctype_phd_protocol",
            "doctype_informative_protocol", "doctype_news_protocol", "doctype_news_min_instances",
            "doctype_blog_protocol", "doctype_blog_min_instances", "doctype_forum_protocol",
            "doctype_personal_collected_protocol", "doctype_personal_min_i_count",
            "doctype_personal_min_paragraph_words", "doctype_auto_categorize"
        ]
        
        defaults = {
            "doctype_phd_min_words": 1500,
            "doctype_phd_keyword_count": 3,
            "doctype_phd_protocol": cls.DEFAULT_PHD_PROTOCOL,
            "doctype_informative_protocol": cls.DEFAULT_INFORMATIVE_PROTOCOL,
            "doctype_news_protocol": cls.DEFAULT_NEWS_PROTOCOL,
            "doctype_news_min_instances": 3,
            "doctype_blog_protocol": cls.DEFAULT_BLOG_PROTOCOL,
            "doctype_blog_min_instances": 3,
            "doctype_forum_protocol": cls.DEFAULT_FORUM_PROTOCOL,
            "doctype_personal_collected_protocol": cls.DEFAULT_PERSONAL_PROTOCOL,
            "doctype_personal_min_i_count": 3,
            "doctype_personal_min_paragraph_words": 75,
            "doctype_auto_categorize": True
        }
        
        for key in keys:
            setting = await db.settings.find_one({"key": key})
            if setting:
                settings[key] = setting.get("value")
            else:
                settings[key] = defaults.get(key)
        
        return settings
    
    @classmethod
    def _count_protocol_matches(cls, text: str, protocol: str) -> int:
        """
        Count how many times a protocol matches in text.
        Protocol format: (word1 or word2) & (word3 or word4)
        Returns count of matching groups.
        """
        if not protocol or not text:
            return 0
        
        text_lower = text.lower()
        groups = protocol.split('&')
        matches = 0
        
        for group in groups:
            group = group.strip().strip('()')
            terms = [t.strip().lower() for t in group.split(' or ')]
            if any(term in text_lower for term in terms):
                matches += 1
        
        return matches
    
    @classmethod
    def calculate_content_quality_score(cls, title: str, snippet: str, url: str = "") -> float:
        """
        Calculate a content quality score (0-100) to prioritize valuable, informative content.
        Higher scores indicate more extensive, well-written, informative content.
        
        Scoring factors:
        - Length of content (longer = more informative)
        - Presence of authoritative domains
        - Keywords indicating research/informative content
        - Structure indicators (numbers, statistics, quotes)
        """
        score = 50.0  # Base score
        
        full_text = f"{title} {snippet}".lower()
        text_length = len(full_text)
        
        # Length bonus (up to +20 points)
        if text_length > 500:
            score += 20
        elif text_length > 300:
            score += 15
        elif text_length > 150:
            score += 10
        elif text_length > 75:
            score += 5
        
        # Authoritative domain bonus (+10 points)
        authoritative_domains = [
            '.edu', '.gov', '.org', 'nature.com', 'science.org', 'springer.com',
            'pubmed', 'ncbi.nlm.nih.gov', 'reuters.com', 'apnews.com', 'bbc.com',
            'nytimes.com', 'washingtonpost.com', 'research', 'academic', 'journal',
            'harvard', 'stanford', 'mit.edu', 'oxford', 'cambridge'
        ]
        url_lower = url.lower()
        if any(domain in url_lower for domain in authoritative_domains):
            score += 10
        
        # Research/informative keyword bonus (+15 points max)
        informative_keywords = [
            'study', 'research', 'analysis', 'report', 'findings', 'data',
            'evidence', 'conclusion', 'methodology', 'experiment', 'results',
            'statistics', 'survey', 'investigation', 'peer-reviewed', 'published',
            'according to', 'experts say', 'scientists', 'researchers',
            'comprehensive', 'in-depth', 'detailed', 'extensive', 'thorough'
        ]
        keyword_matches = sum(1 for kw in informative_keywords if kw in full_text)
        score += min(15, keyword_matches * 3)
        
        # Structure indicators bonus (+10 points max)
        # Numbers/statistics suggest data-driven content
        number_count = len(re.findall(r'\d+(?:\.\d+)?%?', full_text))
        if number_count >= 5:
            score += 10
        elif number_count >= 3:
            score += 7
        elif number_count >= 1:
            score += 3
        
        # Credibility indicators (+5 points max)
        credibility_terms = ['dr.', 'ph.d', 'professor', 'expert', 'official', 'confirmed']
        if any(term in full_text for term in credibility_terms):
            score += 5
        
        # Penalty for clickbait/low-quality indicators (-10 points max)
        clickbait_terms = [
            'you won\'t believe', 'shocking', 'click here', 'free money',
            'miracle', 'secret revealed', 'one weird trick', 'doctors hate'
        ]
        if any(term in full_text for term in clickbait_terms):
            score -= 10
        
        # Ensure score is between 0-100
        return max(0, min(100, score))
    
    @classmethod
    def _count_i_outside_quotes(cls, text: str) -> tuple:
        """
        Count 'I' occurrences outside quotations and find longest paragraph with them.
        Returns (total_count, max_paragraph_word_count)
        """
        if not text:
            return 0, 0
        
        # Remove quoted text - use module-level re import
        text_no_quotes = re.sub(r'"[^"]*"', '', text)
        text_no_quotes = re.sub(r"'[^']*'", '', text_no_quotes)
        
        # Split into paragraphs
        paragraphs = text_no_quotes.split('\n')
        
        max_word_count = 0
        total_i_count = 0
        
        for para in paragraphs:
            # Count standalone 'I' (not part of another word)
            i_count = len(re.findall(r'\bI\b', para))
            total_i_count += i_count
            
            if i_count >= 3:  # Potential personal report paragraph
                word_count = len(para.split())
                max_word_count = max(max_word_count, word_count)
        
        return total_i_count, max_word_count
    
    @classmethod
    def classify(cls, title: str, content: str, url: str = "", settings: dict = None) -> str:
        """
        Classify article type based on content analysis using Admin-controlled protocols.
        """
        if not content and not title:
            return "Webpage"
        
        # Use default settings if none provided
        if settings is None:
            settings = {
                "doctype_phd_min_words": 1500,
                "doctype_phd_keyword_count": 3,
                "doctype_phd_protocol": cls.DEFAULT_PHD_PROTOCOL,
                "doctype_informative_protocol": cls.DEFAULT_INFORMATIVE_PROTOCOL,
                "doctype_news_protocol": cls.DEFAULT_NEWS_PROTOCOL,
                "doctype_news_min_instances": 3,
                "doctype_blog_protocol": cls.DEFAULT_BLOG_PROTOCOL,
                "doctype_blog_min_instances": 3,
                "doctype_forum_protocol": cls.DEFAULT_FORUM_PROTOCOL,
                "doctype_personal_collected_protocol": cls.DEFAULT_PERSONAL_PROTOCOL,
                "doctype_personal_min_i_count": 3,
                "doctype_personal_min_paragraph_words": 75,
            }
        
        title_lower = title.lower() if title else ""
        content_lower = content.lower() if content else ""
        url_lower = url.lower() if url else ""
        combined = f"{title_lower} {content_lower}"
        word_count = len(content.split()) if content else 0
        
        # 1. FORUM - Must contain 'forum' in title (checked first, simple rule)
        forum_protocol = settings.get("doctype_forum_protocol", "(forum)")
        if cls._count_protocol_matches(title_lower, forum_protocol) > 0:
            return "Forum"
        
        # 2. BLOG - Must contain 'blog' N times, one in title
        blog_min = settings.get("doctype_blog_min_instances", 3)
        blog_count = combined.count("blog")
        if blog_count >= blog_min and "blog" in title_lower:
            return "Blog Post"
        
        # 3. INFORMATIVE - Check if meets informative protocol
        informative_protocol = settings.get("doctype_informative_protocol", cls.DEFAULT_INFORMATIVE_PROTOCOL)
        informative_groups = informative_protocol.split('&')
        informative_matches = 0
        for group in informative_groups:
            group = group.strip().strip('()')
            terms = [t.strip().lower() for t in group.split(' or ')]
            if any(term in combined for term in terms):
                informative_matches += 1
        is_informative = informative_matches >= len(informative_groups)
        
        # 4. PhD INFORMATIVE - Must be Informative first + PhD keywords + word count
        if is_informative:
            phd_protocol = settings.get("doctype_phd_protocol", cls.DEFAULT_PHD_PROTOCOL)
            phd_min_words = settings.get("doctype_phd_min_words", 1500)
            phd_keyword_count = settings.get("doctype_phd_keyword_count", 3)
            
            phd_terms = phd_protocol.strip('()').split(' or ')
            phd_matches = sum(1 for term in phd_terms if term.strip().lower() in combined)
            
            if phd_matches >= phd_keyword_count and word_count >= phd_min_words:
                return "PhD Informative"
            
            return "Informative"
        
        # 5. PERSONAL REPORT (Collected) - 'I' outside quotes in paragraph with min words
        min_i_count = settings.get("doctype_personal_min_i_count", 3)
        min_para_words = settings.get("doctype_personal_min_paragraph_words", 75)
        
        total_i, max_para_words = cls._count_i_outside_quotes(content)
        if total_i >= min_i_count and max_para_words >= min_para_words:
            return "Personal Report (Collected)"
        
        # 6. URL-based classification
        if any(x in url_lower for x in ['wikipedia.org', 'wiki']):
            return 'Wiki'
        if any(x in url_lower for x in ['youtube.com', 'vimeo.com', 'video', 'dailymotion']):
            return 'Video'
        if any(x in url_lower for x in ['.gov', 'government']):
            return 'Government'
        if any(x in url_lower for x in ['.edu', 'academic', 'journal', 'research', 'scholar', 'arxiv', 'pubmed']):
            return 'Academic Paper'
        if any(x in url_lower for x in ['.pdf']):
            return 'PDF Document'
        if any(x in url_lower for x in ['.doc', '.docx']):
            return 'MS Word Document'
        
        # 7. NEWS ARTICLE - Protocol match or default fallback
        news_protocol = settings.get("doctype_news_protocol", cls.DEFAULT_NEWS_PROTOCOL)
        news_min = settings.get("doctype_news_min_instances", 3)
        news_matches = cls._count_protocol_matches(combined, news_protocol)
        
        if news_matches >= news_min or "news" in combined:
            return "News Article"
        
        # Default fallback
        return "News Article"
    
    @classmethod
    async def classify_async(cls, title: str, content: str, url: str = "") -> str:
        """Async version that fetches settings from database"""
        settings = await cls.get_settings()
        return cls.classify(title, content, url, settings)

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
    """
    DEEP Collate search results with STRICT protocol matching.
    
    This searches MULTIPLE times with different query variations derived from your protocol,
    then STRICTLY filters results to only include those that truly match your criteria.
    
    Features:
    - Deep Search: Generates 5-10 different search queries from your protocol
    - Multi-Engine: Searches Google, Bing, DuckDuckGo, Brave simultaneously
    - Strict Matching: Only accepts results matching 70%+ of protocol groups
    - Quality Scoring: Results ranked by how well they match your protocol
    """
    category = await db.categories.find_one({"_id": ObjectId(request.category_id)})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    protocol = category.get("protocol", "")
    if not protocol:
        raise HTTPException(status_code=400, detail="Category has no protocol")
    
    user_id = str(user["_id"])
    
    # Get settings
    settings_limit = await db.settings.find_one({"key": "search_collate_limit"})
    collate_limit = settings_limit.get("value", 100) if settings_limit else 100
    
    settings_threshold = await db.settings.find_one({"key": "match_threshold"})
    match_threshold = settings_threshold.get("value", 70) if settings_threshold else 70  # 70% default
    
    # Parse protocol
    groups = ProtocolParser.parse_protocol(protocol)
    
    # DEEP SEARCH: Generate multiple query variations
    search_queries = ProtocolParser.generate_deep_search_queries(protocol, max_queries=8)
    
    # Fallback to basic extraction if no queries generated
    if not search_queries:
        search_queries = [ProtocolParser.extract_search_query(protocol)]
    
    logger.info(f"Deep Collate: Executing {len(search_queries)} search queries for protocol")
    
    # Collect results from ALL query variations
    all_raw_results = []
    seen_urls = set()
    results_per_query = max(30, collate_limit // len(search_queries))
    
    for query in search_queries:
        if not query.strip():
            continue
        
        try:
            query_results = await ExtendedWebSearchService.search(query, results_per_query)
            for result in query_results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["source_query"] = query  # Track which query found this
                    all_raw_results.append(result)
        except Exception as e:
            logger.warning(f"Search query failed: {query} - {e}")
            continue
    
    logger.info(f"Deep Collate: Found {len(all_raw_results)} unique results from {len(search_queries)} queries")
    
    # STRICT MATCHING: Only accept results that truly match the protocol
    matched_results = []
    rejected_count = 0
    min_match_percent = match_threshold / 100.0  # Convert to decimal
    
    for result in all_raw_results:
        matches, score, details = ProtocolParser.strict_match_result(
            result, 
            groups,
            min_group_match_percent=min_match_percent,
            fuzzy_threshold=70
        )
        
        if matches and score > 0:
            result["match_score"] = score
            result["match_details"] = details
            result["article_type"] = ArticleClassifier.classify(
                result.get("title", ""), result.get("content", "")
            )
            result["root_domain"] = WebSearchService.extract_root_domain(result.get("url", ""))
            # Calculate content quality score for prioritizing valuable content
            result["content_quality_score"] = ArticleClassifier.calculate_content_quality_score(
                result.get("title", ""),
                result.get("snippet", result.get("content", "")),
                result.get("url", "")
            )
            matched_results.append(result)
        else:
            rejected_count += 1
    
    logger.info(f"Deep Collate: {len(matched_results)} results passed strict matching, {rejected_count} rejected")
    
    # Sort by combined score: 60% match_score + 40% content_quality_score
    # This prioritizes valuable, extensive content while still considering match relevance
    matched_results.sort(
        key=lambda x: (x.get("match_score", 0) * 0.6) + (x.get("content_quality_score", 50) * 0.4),
        reverse=True
    )
    
    # Apply collate limit
    matched_results = matched_results[:collate_limit]
    
    # Store results
    batch_id = str(ObjectId())
    stored_count = 0
    
    for result in matched_results:
        existing = await db.search_results.find_one({
            "url": result["url"],
            "user_id": user_id
        })
        
        if existing:
            await db.search_results.update_one(
                {"_id": existing["_id"]},
                {
                    "$addToSet": {"category_ids": request.category_id},
                    "$set": {
                        "match_score": max(existing.get("match_score", 0), result.get("match_score", 0)),
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
                "match_details": result.get("match_details", {}),
                "source_query": result.get("source_query", ""),
                "category_ids": [request.category_id],
                "user_id": user_id,
                "batch_id": batch_id,
                "created_at": datetime.utcnow()
            })
            stored_count += 1
    
    # Update category
    await db.categories.update_one(
        {"_id": ObjectId(request.category_id)},
        {"$set": {"last_collated": datetime.utcnow()}}
    )
    
    # Format response
    formatted = []
    for r in matched_results:
        match_details = r.get("match_details", {})
        formatted.append({
            "id": str(ObjectId()),
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "article_type": r.get("article_type", "Unknown"),
            "root_domain": r.get("root_domain", ""),
            "match_score": round(r.get("match_score", 0) * 100, 1),  # Convert to percentage
            "match_percent": round(match_details.get("match_percent", 0) * 100, 1),
            "groups_matched": match_details.get("groups_matched", 0),
            "total_groups": match_details.get("total_groups", 0),
            "categories": [category["name"]]
        })
    
    return {
        "results": formatted,
        "total": len(formatted),
        "category": category["name"],
        "batch_id": batch_id,
        "deep_search_stats": {
            "queries_executed": len(search_queries),
            "total_results_found": len(all_raw_results),
            "passed_strict_matching": len(matched_results),
            "rejected": rejected_count,
            "match_threshold": f"{match_threshold}%"
        },
        "message": f"🔍 Deep Collate: Found {len(formatted)} high-quality results from {len(all_raw_results)} searched (using {len(search_queries)} query variations)"
    }


@api_router.post("/auto-categorize", response_model=dict)
async def auto_categorize_search(request: dict, user = Depends(get_current_user_local)):
    """
    DEEP Auto-categorization: Search with STRICT protocol matching against ALL categories.
    
    Features:
    - Deep Search: Uses multiple query variations to find more relevant results
    - Strict Matching: Only accepts results matching 70%+ of protocol groups
    - Multi-Category: Each result can match multiple categories
    - Quality Scoring: Results ranked by match quality
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
    
    # Get settings
    settings_limit = await db.settings.find_one({"key": "search_collate_limit"})
    collate_limit = int(settings_limit.get("value", 100)) if settings_limit else 100
    collate_limit = min(max(1, collate_limit), 200)
    
    settings_threshold = await db.settings.find_one({"key": "match_threshold"})
    match_threshold = settings_threshold.get("value", 70) if settings_threshold else 70
    min_match_percent = match_threshold / 100.0
    
    # DEEP SEARCH: Generate additional search queries from category protocols
    all_search_queries = [search_query]
    
    # Add queries derived from each category's protocol (for deeper coverage)
    for category in all_categories[:5]:  # Limit to 5 categories for query generation
        protocol = category.get("protocol", "")
        if protocol:
            protocol_queries = ProtocolParser.generate_deep_search_queries(protocol, max_queries=2)
            # Combine user query with protocol terms
            for pq in protocol_queries[:2]:
                combined = f"{search_query} {pq}"
                if combined not in all_search_queries:
                    all_search_queries.append(combined)
    
    # Limit total queries
    all_search_queries = all_search_queries[:10]
    
    logger.info(f"Auto-Categorize: Executing {len(all_search_queries)} search queries")
    
    # Collect results from all queries
    all_raw_results = []
    seen_urls = set()
    
    for query in all_search_queries:
        try:
            results_per_query = max(20, collate_limit // len(all_search_queries))
            query_results = await ExtendedWebSearchService.search(query, results_per_query)
            for result in query_results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["source_query"] = query
                    all_raw_results.append(result)
        except Exception as e:
            logger.warning(f"Search query failed: {query} - {e}")
    
    if not all_raw_results:
        return {
            "results": [],
            "total": 0,
            "categories_matched": 0,
            "message": "No results found"
        }
    
    logger.info(f"Auto-Categorize: Found {len(all_raw_results)} unique results")
    
    batch_id = str(ObjectId())
    matched_results = []
    category_matches = {}
    rejected_count = 0
    
    # For each result, check against ALL categories with STRICT matching
    for result in all_raw_results:
        result_categories = []
        result_category_ids = []
        best_score = 0
        match_details_list = []
        
        for category in all_categories:
            protocol = category.get("protocol", "")
            if not protocol:
                continue
            
            # Parse protocol and check with STRICT matching
            groups = ProtocolParser.parse_protocol(protocol)
            matches, score, details = ProtocolParser.strict_match_result(
                result, 
                groups,
                min_group_match_percent=min_match_percent,
                fuzzy_threshold=70
            )
            
            if matches and score > 0:
                cat_id = str(category["_id"])
                cat_name = category["name"]
                result_categories.append(cat_name)
                result_category_ids.append(cat_id)
                best_score = max(best_score, score)
                match_details_list.append({
                    "category": cat_name,
                    "score": score,
                    "match_percent": details.get("match_percent", 0)
                })
                
                # Track category matches
                if cat_id not in category_matches:
                    category_matches[cat_id] = {"name": cat_name, "count": 0}
                category_matches[cat_id]["count"] += 1
        
        # Only include results that match at least one category
        if result_categories:
            result["match_score"] = best_score
            result["article_type"] = ArticleClassifier.classify(
                result.get("title", ""), result.get("content", "")
            )
            result["root_domain"] = WebSearchService.extract_root_domain(result.get("url", ""))
            # Calculate content quality score for prioritizing valuable content
            result["content_quality_score"] = ArticleClassifier.calculate_content_quality_score(
                result.get("title", ""),
                result.get("snippet", result.get("content", "")),
                result.get("url", "")
            )
            result["categories"] = result_categories
            result["category_ids"] = result_category_ids
            result["match_details_list"] = match_details_list
            matched_results.append(result)
        else:
            rejected_count += 1
    
    logger.info(f"Auto-Categorize: {len(matched_results)} results matched categories, {rejected_count} rejected")
    
    # Sort by combined score: 60% match_score + 40% content_quality_score
    # This prioritizes valuable, extensive content while still considering match relevance
    matched_results.sort(
        key=lambda x: (x.get("match_score", 0) * 0.6) + (x.get("content_quality_score", 50) * 0.4),
        reverse=True
    )
    
    # Apply limit
    matched_results = matched_results[:collate_limit]
    
    # Store results in database
    for result in matched_results:
        existing = await db.search_results.find_one({
            "url": result["url"],
            "user_id": user_id
        })
        
        if existing:
            await db.search_results.update_one(
                {"_id": existing["_id"]},
                {
                    "$addToSet": {"category_ids": {"$each": result["category_ids"]}},
                    "$set": {
                        "batch_id": batch_id, 
                        "updated_at": datetime.utcnow(),
                        "match_score": max(existing.get("match_score", 0), result.get("match_score", 0))
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
            "match_score": round(r.get("match_score", 0) * 100, 1),  # Convert to percentage
            "categories": r.get("categories", []),
            "category_ids": r.get("category_ids", []),
            "categories_count": len(r.get("categories", []))
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
        "deep_search_stats": {
            "queries_executed": len(all_search_queries),
            "total_results_found": len(all_raw_results),
            "passed_strict_matching": len(matched_results),
            "rejected": rejected_count,
            "match_threshold": f"{match_threshold}%"
        },
        "message": f"🎯 Deep Auto-Categorize: {len(formatted)} high-quality results across {len(category_matches)} categories (from {len(all_raw_results)} searched)"
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
    # Enhanced: Count parenthetical group matches for better scoring
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
            result_scores = []  # Track scores per category
            best_score = 0
            total_groups_matched = 0  # Count parenthetical groups matched
            
            for category in all_categories:
                protocol = category.get("protocol", "")
                if not protocol:
                    continue
                
                groups = ProtocolParser.parse_protocol(protocol)
                matches, score = ProtocolParser.match_result(result, groups)
                
                if matches:
                    result_categories.append(category["name"])
                    result_category_ids.append(str(category["_id"]))
                    result_scores.append(score)
                    best_score = max(best_score, score)
                    
                    # Count how many groups (parentheses) this result matches
                    combined_text = f"{result.get('title', '')} {result.get('snippet', '')} {result.get('content', '')}".lower()
                    groups_matched_count = 0
                    for group in groups:
                        if group.get("excluded"):
                            continue
                        for term in group["terms"]:
                            term_lower = term.lower().strip('"\'')
                            if term_lower in combined_text:
                                groups_matched_count += 1
                                break  # One match per group is enough
                    total_groups_matched = max(total_groups_matched, groups_matched_count)
            
            # Enhanced scoring: weight by number of groups matched (parentheses)
            # More groups matched = higher priority for auto-collation
            parentheses_bonus = total_groups_matched * 0.1
            combined_score = best_score + parentheses_bonus
            
            result["categories"] = result_categories
            result["category_ids"] = result_category_ids
            result["match_score"] = combined_score
            result["groups_matched"] = total_groups_matched
            result["should_auto_collate"] = combined_score >= 0.5 and len(result_category_ids) > 0  # Only auto-collate best matches
    
    # Classify and add metadata, calculate content quality
    for result in all_results:
        result["article_type"] = ArticleClassifier.classify(
            result.get("title", ""), result.get("content", "")
        )
        result["root_domain"] = WebSearchService.extract_root_domain(result.get("url", ""))
        # Calculate content quality score for prioritizing valuable content
        result["content_quality_score"] = ArticleClassifier.calculate_content_quality_score(
            result.get("title", ""),
            result.get("snippet", result.get("content", "")),
            result.get("url", "")
        )
    
    # Sort by combined score: 60% match_score + 40% content_quality_score
    # This prioritizes valuable, extensive content while still considering match relevance
    all_results.sort(
        key=lambda x: (x.get("match_score", 0) * 0.6) + (x.get("content_quality_score", 50) * 0.004),
        reverse=True
    )
    
    # Store results - Only auto-collate results that meet threshold
    auto_collated_count = 0
    for result in all_results[:max_results]:
        existing = await db.search_results.find_one({
            "url": result["url"],
            "user_id": user_id
        })
        
        # Only include category_ids if result should be auto-collated
        should_auto_collate = result.get("should_auto_collate", False)
        category_ids = result.get("category_ids", []) if should_auto_collate else []
        
        if should_auto_collate and category_ids:
            auto_collated_count += 1
        
        if existing:
            update_data = {
                "batch_id": batch_id,
                "ai_search": True,
                "updated_at": datetime.utcnow(),
                "groups_matched": result.get("groups_matched", 0),
                "content_quality_score": result.get("content_quality_score", 50)
            }
            if category_ids:
                await db.search_results.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$addToSet": {"category_ids": {"$each": category_ids}},
                        "$set": update_data
                    }
                )
            else:
                await db.search_results.update_one(
                    {"_id": existing["_id"]},
                    {"$set": update_data}
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
                "content_quality_score": result.get("content_quality_score", 50),
                "groups_matched": result.get("groups_matched", 0),
                "category_ids": category_ids,
                "user_id": user_id,
                "batch_id": batch_id,
                "ai_search": True,
                "auto_collated": should_auto_collate,
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
            "groups_matched": r.get("groups_matched", 0),
            "categories": r.get("categories", []),
            "category_ids": r.get("category_ids", []),
            "auto_collated": r.get("should_auto_collate", False),
            "search_engine": r.get("source", "multi-engine")
        })
    
    return {
        "results": formatted,
        "total": len(formatted),
        "auto_collated_count": auto_collated_count,
        "original_query": original_query,
        "expanded_queries": expanded_queries,
        "ai_suggestions": ai_suggestions,
        "batch_id": batch_id,
        "search_mode": search_mode,
        "auto_categorized": auto_categorize,
        "message": f"🤖 AI Search found {len(formatted)} results, auto-collated {auto_collated_count} to categories!"
    }


@api_router.post("/database-search", response_model=dict)
async def database_text_search(request: dict, user = Depends(get_current_user_local)):
    """
    Search within already collated results in the database.
    Uses AI-powered text matching against stored search results.
    Great for finding specific content within your existing research.
    """
    search_query = request.get("query", "").strip()
    category_ids = request.get("category_ids", [])
    article_types = request.get("article_types", [])
    search_mode = request.get("mode", "smart")  # smart, exact, fuzzy
    limit = min(request.get("limit", 100), 200)
    
    if not search_query:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    user_id = str(user["_id"])
    
    # Build base query for user's results
    base_query = {"user_id": user_id}
    
    # Filter by categories if specified
    if category_ids:
        base_query["category_ids"] = {"$in": category_ids}
    
    # Filter by article types if specified
    if article_types:
        base_query["article_type"] = {"$in": article_types}
    
    # Get all matching results
    all_results = await db.search_results.find(base_query).to_list(1000)
    
    if not all_results:
        return {
            "results": [],
            "total": 0,
            "query": search_query,
            "message": "No results in your database. Try running a search first!"
        }
    
    # Search within results based on mode
    search_terms = search_query.lower().split()
    matched_results = []
    
    for result in all_results:
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        content = result.get("content", "").lower()
        url = result.get("url", "").lower()
        
        combined_text = f"{title} {snippet} {content} {url}"
        
        if search_mode == "exact":
            # Exact phrase match
            if search_query.lower() in combined_text:
                result["relevance_score"] = 100
                matched_results.append(result)
        elif search_mode == "fuzzy":
            # Match if ANY term is found
            match_count = sum(1 for term in search_terms if term in combined_text)
            if match_count > 0:
                result["relevance_score"] = (match_count / len(search_terms)) * 100
                matched_results.append(result)
        else:
            # Smart mode: score based on term frequency and position
            score = 0
            for term in search_terms:
                if term in title:
                    score += 30  # Title match is most valuable
                if term in snippet:
                    score += 15
                if term in content:
                    score += 10
                if term in url:
                    score += 5
            
            if score > 0:
                result["relevance_score"] = min(score, 100)
                matched_results.append(result)
    
    # Sort by relevance score
    matched_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    matched_results = matched_results[:limit]
    
    # Format results
    formatted = []
    for r in matched_results:
        formatted.append({
            "id": str(r["_id"]),
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "article_type": r.get("article_type", "Unknown"),
            "root_domain": r.get("root_domain", ""),
            "relevance_score": r.get("relevance_score", 0),
            "category_ids": r.get("category_ids", []),
            "created_at": r.get("created_at").isoformat() if r.get("created_at") else None
        })
    
    return {
        "results": formatted,
        "total": len(formatted),
        "total_in_database": len(all_results),
        "query": search_query,
        "mode": search_mode,
        "filters": {
            "categories": len(category_ids) if category_ids else 0,
            "article_types": article_types
        },
        "message": f"📚 Found {len(formatted)} results in your database matching '{search_query}'"
    }


@api_router.get("/article-types", response_model=dict)
async def get_article_types():
    """Get list of all supported article/document types"""
    return {
        "types": [
            {"id": "phd_informative", "name": "PhD Informative", "description": "Academic content by credentialed professionals"},
            {"id": "personal_organic", "name": "Personal Report (Organic)", "description": "First-hand personal accounts and experiences"},
            {"id": "personal_collected", "name": "Personal Report (Collected)", "description": "Aggregated and curated personal reports"},
            {"id": "news_article", "name": "News Article", "description": "Current events and journalism"},
            {"id": "academic_paper", "name": "Academic Paper", "description": "Scholarly research and publications"},
            {"id": "government", "name": "Government", "description": "Official government documents"},
            {"id": "wiki", "name": "Wiki", "description": "Wikipedia and wiki-based content"},
            {"id": "blog_post", "name": "Blog Post", "description": "Personal blogs and opinion pieces"},
            {"id": "forum", "name": "Forum", "description": "Discussion boards and Q&A sites"},
            {"id": "video", "name": "Video", "description": "Video content from YouTube, Vimeo, etc."},
            {"id": "pdf_document", "name": "PDF Document", "description": "PDF files and documents"},
            {"id": "ms_word", "name": "MS Word Document", "description": "Microsoft Word documents"},
            {"id": "webpage", "name": "Webpage", "description": "General web pages"}
        ]
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
    
    # Sort by content_quality_score when filtering by category to prioritize valuable content
    if selected_category_ids or category_id:
        # When viewing category results, sort by quality_score (highest first) for best content
        results = await db.search_results.find(query).sort([
            ("content_quality_score", -1),  # Highest quality first
            ("match_score", -1),            # Then by match score
            ("created_at", -1)              # Finally by date
        ]).skip(skip).limit(limit).to_list(limit)
    else:
        # Default: sort by created_at for recent results
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
            "content_quality_score": r.get("content_quality_score", 50),
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


# ==================== SEARCH RESULT COMMENTS ====================

class SearchResultComment(BaseModel):
    """Model for creating a comment on a search result"""
    content: str
    parent_id: Optional[str] = None  # For nested replies

@api_router.get("/search-results/{result_id}/comments", response_model=dict)
async def get_search_result_comments(result_id: str, user = Depends(get_optional_user_local)):
    """Get comments for a search result"""
    comments = await db.result_comments.find({"result_id": result_id}).sort("created_at", 1).to_list(200)
    
    formatted = []
    for c in comments:
        author = await db.users.find_one({"_id": ObjectId(c["user_id"])}, {"_id": 0, "username": 1, "avatar_url": 1})
        formatted.append({
            "id": str(c["_id"]),
            "content": c["content"],
            "author": author or {"username": "Unknown"},
            "parent_id": c.get("parent_id"),
            "likes": c.get("likes", 0),
            "is_mine": user and str(user.get("_id")) == c["user_id"],
            "created_at": c["created_at"].isoformat() if c.get("created_at") else None
        })
    
    return {"comments": formatted, "count": len(formatted)}

@api_router.post("/search-results/{result_id}/comments", response_model=dict)
async def create_search_result_comment(result_id: str, comment: SearchResultComment, user = Depends(get_current_user_local)):
    """Create a comment on a search result"""
    # Verify result exists
    result = await db.search_results.find_one({"_id": ObjectId(result_id)})
    if not result:
        raise HTTPException(status_code=404, detail="Search result not found")
    
    comment_data = {
        "result_id": result_id,
        "user_id": str(user["_id"]),
        "content": comment.content,
        "parent_id": comment.parent_id,
        "likes": 0,
        "created_at": datetime.utcnow()
    }
    
    result_insert = await db.result_comments.insert_one(comment_data)
    
    # Update comment count on result
    await db.search_results.update_one(
        {"_id": ObjectId(result_id)},
        {"$inc": {"comment_count": 1}}
    )
    
    return {
        "id": str(result_insert.inserted_id),
        "message": "Comment added successfully"
    }

@api_router.delete("/search-results/{result_id}/comments/{comment_id}", response_model=dict)
async def delete_search_result_comment(result_id: str, comment_id: str, user = Depends(get_current_user_local)):
    """Delete a comment on a search result"""
    result = await db.result_comments.delete_one({
        "_id": ObjectId(comment_id),
        "user_id": str(user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found or not owned by you")
    
    # Update comment count on result
    await db.search_results.update_one(
        {"_id": ObjectId(result_id)},
        {"$inc": {"comment_count": -1}}
    )
    
    return {"deleted": True}

@api_router.post("/search-results/{result_id}/comments/{comment_id}/like", response_model=dict)
async def like_search_result_comment(result_id: str, comment_id: str, user = Depends(get_current_user_local)):
    """Like/unlike a comment"""
    user_id = str(user["_id"])
    
    # Check if already liked
    existing_like = await db.comment_likes.find_one({
        "comment_id": comment_id,
        "user_id": user_id
    })
    
    if existing_like:
        # Unlike
        await db.comment_likes.delete_one({"_id": existing_like["_id"]})
        await db.result_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {"$inc": {"likes": -1}}
        )
        return {"liked": False}
    else:
        # Like
        await db.comment_likes.insert_one({
            "comment_id": comment_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        await db.result_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {"$inc": {"likes": 1}}
        )
        return {"liked": True}


# ==================== PERSONAL REPORT (ORGANIC) ENDPOINTS ====================

class PersonalReportCreate(BaseModel):
    """Model for creating a Personal Report (Organic)"""
    title: str
    content: str
    topic: Optional[str] = ""
    location_name: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    category_ids: Optional[List[str]] = []


@api_router.post("/personal-reports", response_model=dict)
async def create_personal_report(report: PersonalReportCreate, user = Depends(get_current_user_local)):
    """
    Create a Personal Report (Organic) - written by members.
    Users can write their own first-hand reports about any topic.
    """
    user_id = str(user["_id"])
    
    # Create the report as a search result with special article_type
    report_data = {
        "title": report.title,
        "content": report.content,
        "snippet": report.content[:300] if report.content else "",
        "topic": report.topic,
        "url": f"infopilot://personal-report/{ObjectId()}",  # Internal URL
        "article_type": "Personal Report (Organic)",
        "root_domain": "infopilot.local",
        "is_personal_report": True,
        "is_organic": True,  # Written by member, not extracted
        "location_name": report.location_name,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "image_url": report.image_url,
        "category_ids": report.category_ids,
        "user_id": user_id,
        "author_id": user_id,
        "author_name": user.get("username") or user.get("email", "").split("@")[0],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.search_results.insert_one(report_data)
    
    # Update category result counts
    for cat_id in report.category_ids:
        await db.categories.update_one(
            {"_id": ObjectId(cat_id)},
            {"$inc": {"result_count": 1}}
        )
    
    return {
        "success": True,
        "report_id": str(result.inserted_id),
        "message": "Personal Report created successfully!",
        "report": {
            "id": str(result.inserted_id),
            "title": report.title,
            "article_type": "Personal Report (Organic)",
            "author": report_data["author_name"]
        }
    }


@api_router.get("/personal-reports", response_model=dict)
async def get_personal_reports(
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    user = Depends(get_current_user_local)
):
    """
    Get Personal Reports (Organic).
    If user_id is provided, get that user's reports. Otherwise, get current user's reports.
    """
    target_user_id = user_id or str(user["_id"])
    
    query = {
        "article_type": "Personal Report (Organic)",
        "is_personal_report": True
    }
    
    # If requesting own reports, show all. If requesting others', only show if public categories.
    if target_user_id == str(user["_id"]):
        query["user_id"] = target_user_id
    else:
        query["author_id"] = target_user_id
    
    total = await db.search_results.count_documents(query)
    reports = await db.search_results.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    formatted = []
    for r in reports:
        formatted.append({
            "id": str(r["_id"]),
            "title": r.get("title", ""),
            "content": r.get("content", ""),
            "snippet": r.get("snippet", ""),
            "topic": r.get("topic", ""),
            "article_type": "Personal Report (Organic)",
            "author_name": r.get("author_name", ""),
            "location_name": r.get("location_name", ""),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "image_url": r.get("image_url"),
            "category_ids": r.get("category_ids", []),
            "created_at": r.get("created_at", datetime.utcnow()).isoformat(),
            "updated_at": r.get("updated_at", datetime.utcnow()).isoformat()
        })
    
    return {
        "reports": formatted,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@api_router.get("/personal-reports/{report_id}", response_model=dict)
async def get_personal_report(report_id: str, user = Depends(get_current_user_local)):
    """Get a specific Personal Report by ID"""
    report = await db.search_results.find_one({
        "_id": ObjectId(report_id),
        "article_type": "Personal Report (Organic)"
    })
    
    if not report:
        raise HTTPException(status_code=404, detail="Personal Report not found")
    
    return {
        "report": {
            "id": str(report["_id"]),
            "title": report.get("title", ""),
            "content": report.get("content", ""),
            "snippet": report.get("snippet", ""),
            "topic": report.get("topic", ""),
            "article_type": "Personal Report (Organic)",
            "author_name": report.get("author_name", ""),
            "author_id": report.get("author_id", ""),
            "location_name": report.get("location_name", ""),
            "latitude": report.get("latitude"),
            "longitude": report.get("longitude"),
            "image_url": report.get("image_url"),
            "category_ids": report.get("category_ids", []),
            "created_at": report.get("created_at", datetime.utcnow()).isoformat(),
            "updated_at": report.get("updated_at", datetime.utcnow()).isoformat(),
            "is_owner": report.get("author_id") == str(user["_id"])
        }
    }


@api_router.put("/personal-reports/{report_id}", response_model=dict)
async def update_personal_report(report_id: str, data: dict, user = Depends(get_current_user_local)):
    """
    Update a Personal Report (Organic).
    Only the author can update their report.
    """
    user_id = str(user["_id"])
    
    # Find the report
    report = await db.search_results.find_one({
        "_id": ObjectId(report_id),
        "article_type": "Personal Report (Organic)"
    })
    
    if not report:
        raise HTTPException(status_code=404, detail="Personal Report not found")
    
    if report.get("author_id") != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own reports")
    
    # Allowed fields to update
    allowed_fields = ["title", "content", "topic", "location_name", "latitude", "longitude", "image_url", "category_ids"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if "content" in update_data:
        update_data["snippet"] = update_data["content"][:300]
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Handle category changes
    old_category_ids = set(report.get("category_ids", []))
    new_category_ids = set(update_data.get("category_ids", old_category_ids))
    
    # Decrement count for removed categories
    for cat_id in old_category_ids - new_category_ids:
        await db.categories.update_one(
            {"_id": ObjectId(cat_id)},
            {"$inc": {"result_count": -1}}
        )
    
    # Increment count for added categories
    for cat_id in new_category_ids - old_category_ids:
        await db.categories.update_one(
            {"_id": ObjectId(cat_id)},
            {"$inc": {"result_count": 1}}
        )
    
    await db.search_results.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": update_data}
    )
    
    return {
        "success": True,
        "message": "Personal Report updated successfully",
        "updated_fields": list(update_data.keys())
    }


@api_router.delete("/personal-reports/{report_id}", response_model=dict)
async def delete_personal_report(report_id: str, user = Depends(get_current_user_local)):
    """
    Delete a Personal Report (Organic).
    Only the author can delete their report.
    """
    user_id = str(user["_id"])
    
    # Find the report
    report = await db.search_results.find_one({
        "_id": ObjectId(report_id),
        "article_type": "Personal Report (Organic)"
    })
    
    if not report:
        raise HTTPException(status_code=404, detail="Personal Report not found")
    
    if report.get("author_id") != user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="You can only delete your own reports")
    
    # Decrement category counts
    for cat_id in report.get("category_ids", []):
        await db.categories.update_one(
            {"_id": ObjectId(cat_id)},
            {"$inc": {"result_count": -1}}
        )
    
    await db.search_results.delete_one({"_id": ObjectId(report_id)})
    
    return {
        "success": True,
        "message": "Personal Report deleted successfully"
    }


@api_router.post("/personal-reports/{report_id}/image", response_model=dict)
async def upload_personal_report_image(
    report_id: str,
    file: UploadFile = File(...),
    user = Depends(get_current_user_local)
):
    """
    Upload an image for a Personal Report (Organic).
    Supports up to 3 images per report (max 6.9MB each).
    """
    user_id = str(user["_id"])
    
    # Verify ownership
    report = await db.search_results.find_one({
        "_id": ObjectId(report_id),
        "author_id": user_id,
        "article_type": "Personal Report (Organic)"
    })
    
    if not report:
        raise HTTPException(status_code=404, detail="Personal Report not found or not owned by you")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, GIF, and WebP images are allowed")
    
    # Check file size (max 6.9MB)
    content = await file.read()
    if len(content) > 6.9 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be less than 6.9MB")
    
    # Check existing images count
    existing_images = report.get("image_urls", [])
    if report.get("image_url") and not existing_images:
        # Migrate legacy single image to array
        existing_images = [report.get("image_url")]
    
    if len(existing_images) >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 images allowed per report. Delete an existing image first.")
    
    # Save file
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"report_{report_id}_{len(existing_images) + 1}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{file_extension}"
    filepath = os.path.join(MESSAGE_UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Update report with image URL
    image_url = f"/api/uploads/messages/{filename}"
    new_images = existing_images + [image_url]
    
    await db.search_results.update_one(
        {"_id": ObjectId(report_id)},
        {
            "$set": {
                "image_url": new_images[0],  # Keep legacy field for compatibility
                "image_urls": new_images,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "success": True,
        "image_url": image_url,
        "image_urls": new_images,
        "images_count": len(new_images),
        "message": f"Image uploaded successfully ({len(new_images)}/3)"
    }


@api_router.delete("/personal-reports/{report_id}/image/{image_index}", response_model=dict)
async def delete_personal_report_image(
    report_id: str,
    image_index: int,
    user = Depends(get_current_user_local)
):
    """
    Delete a specific image from a Personal Report by index (0-2).
    """
    user_id = str(user["_id"])
    
    # Verify ownership
    report = await db.search_results.find_one({
        "_id": ObjectId(report_id),
        "author_id": user_id,
        "article_type": "Personal Report (Organic)"
    })
    
    if not report:
        raise HTTPException(status_code=404, detail="Personal Report not found or not owned by you")
    
    # Get existing images
    existing_images = report.get("image_urls", [])
    if report.get("image_url") and not existing_images:
        existing_images = [report.get("image_url")]
    
    if image_index < 0 or image_index >= len(existing_images):
        raise HTTPException(status_code=400, detail="Invalid image index")
    
    # Remove the image from array
    removed_url = existing_images.pop(image_index)
    
    # Try to delete the file
    try:
        filename = removed_url.split("/")[-1]
        filepath = os.path.join(MESSAGE_UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        logger.warning(f"Failed to delete image file: {e}")
    
    # Update report
    update_data = {
        "image_urls": existing_images,
        "updated_at": datetime.utcnow()
    }
    if existing_images:
        update_data["image_url"] = existing_images[0]
    else:
        update_data["image_url"] = None
    
    await db.search_results.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": update_data}
    )
    
    return {
        "success": True,
        "image_urls": existing_images,
        "images_count": len(existing_images),
        "message": f"Image deleted successfully ({len(existing_images)}/3 remaining)"
    }


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


# ==================== MAP EXPORT FEATURES ====================

@api_router.get("/map-data/export", response_model=dict)
async def export_map_data(
    format: str = "json",
    category_ids: Optional[str] = None,
    user = Depends(get_current_user_local)
):
    """
    Export map data in various formats (JSON, CSV, KML, GeoJSON).
    Supports filtering by category.
    """
    user_id = str(user["_id"])
    
    # Build query
    query = {
        "user_id": user_id,
        "latitude": {"$exists": True, "$ne": None},
        "longitude": {"$exists": True, "$ne": None}
    }
    
    # Filter by categories if provided
    if category_ids:
        cat_list = [c.strip() for c in category_ids.split(",")]
        query["category_ids"] = {"$in": cat_list}
    
    results = await db.search_results.find(query).to_list(1000)
    
    # Format based on export type
    if format == "geojson":
        # GeoJSON format for mapping applications
        features = []
        for r in results:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [r.get("longitude"), r.get("latitude")]
                },
                "properties": {
                    "id": str(r["_id"]),
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "article_type": r.get("article_type", "Unknown"),
                    "snippet": r.get("snippet", "")[:200]
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total": len(features),
                "exported_at": datetime.utcnow().isoformat()
            }
        }
    
    elif format == "kml":
        # KML format for Google Earth
        placemarks = []
        for r in results:
            placemarks.append({
                "name": r.get("title", "Untitled"),
                "description": r.get("snippet", "")[:300],
                "coordinates": f"{r.get('longitude')},{r.get('latitude')},0",
                "url": r.get("url", "")
            })
        
        return {
            "format": "kml",
            "placemarks": placemarks,
            "total": len(placemarks),
            "message": "Use this data to generate a KML file for Google Earth"
        }
    
    elif format == "csv":
        # CSV format
        rows = []
        rows.append(["id", "title", "url", "latitude", "longitude", "article_type", "snippet"])
        for r in results:
            rows.append([
                str(r["_id"]),
                r.get("title", ""),
                r.get("url", ""),
                str(r.get("latitude", "")),
                str(r.get("longitude", "")),
                r.get("article_type", "Unknown"),
                r.get("snippet", "")[:200].replace(",", ";")
            ])
        
        return {
            "format": "csv",
            "headers": rows[0],
            "rows": rows[1:],
            "total": len(rows) - 1
        }
    
    else:  # Default JSON
        formatted = []
        for r in results:
            formatted.append({
                "id": str(r["_id"]),
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
                "article_type": r.get("article_type", "Unknown"),
                "snippet": r.get("snippet", "")[:200],
                "category_ids": r.get("category_ids", [])
            })
        
        return {
            "format": "json",
            "results": formatted,
            "total": len(formatted),
            "exported_at": datetime.utcnow().isoformat()
        }


@api_router.get("/map-data/statistics", response_model=dict)
async def get_map_statistics(user = Depends(get_current_user_local)):
    """
    Get statistics about geolocated results.
    Includes country distribution, article types, and more.
    """
    user_id = str(user["_id"])
    
    # Get all geolocated results
    results = await db.search_results.find({
        "user_id": user_id,
        "latitude": {"$exists": True, "$ne": None},
        "longitude": {"$exists": True, "$ne": None}
    }).to_list(1000)
    
    # Calculate statistics
    total_geolocated = len(results)
    
    # Article type distribution
    article_types = {}
    for r in results:
        atype = r.get("article_type", "Unknown")
        article_types[atype] = article_types.get(atype, 0) + 1
    
    # Geographic distribution (rough estimate based on coordinates)
    regions = {
        "North America": 0,
        "South America": 0,
        "Europe": 0,
        "Asia": 0,
        "Africa": 0,
        "Oceania": 0,
        "Unknown": 0
    }
    
    for r in results:
        lat = r.get("latitude", 0)
        lng = r.get("longitude", 0)
        
        # Simple region detection based on coordinates
        if lat > 15 and lng < -30:
            regions["North America"] += 1
        elif lat < 15 and lat > -60 and lng < -30:
            regions["South America"] += 1
        elif lat > 35 and lng > -10 and lng < 40:
            regions["Europe"] += 1
        elif lat > 0 and lng > 40:
            regions["Asia"] += 1
        elif lat < 35 and lat > -35 and lng > -20 and lng < 55:
            regions["Africa"] += 1
        elif lat < 0 and lng > 100:
            regions["Oceania"] += 1
        else:
            regions["Unknown"] += 1
    
    # Calculate bounding box
    if results:
        lats = [r.get("latitude", 0) for r in results]
        lngs = [r.get("longitude", 0) for r in results]
        bounding_box = {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs)
        }
    else:
        bounding_box = None
    
    return {
        "total_geolocated": total_geolocated,
        "article_types": article_types,
        "regions": regions,
        "bounding_box": bounding_box,
        "export_formats": ["json", "geojson", "kml", "csv"],
        "message": f"You have {total_geolocated} geolocated results"
    }


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

# ============== THEME PRESETS ==============

class ThemePreset(BaseModel):
    """Model for creating a theme preset"""
    name: str
    is_dark: bool = True
    accent_color: str = "purple"
    description: Optional[str] = ""
    is_public: bool = False

@api_router.get("/theme-presets", response_model=dict)
async def get_theme_presets(user = Depends(get_optional_user_local)):
    """Get public theme presets and user's own presets"""
    public_presets = await db.theme_presets.find({"is_public": True}).sort("likes", -1).to_list(50)
    
    user_presets = []
    if user:
        user_presets = await db.theme_presets.find({"user_id": str(user["_id"])}).to_list(50)
    
    def format_preset(p):
        return {
            "id": str(p["_id"]),
            "name": p["name"],
            "is_dark": p.get("is_dark", True),
            "accent_color": p.get("accent_color", "purple"),
            "description": p.get("description", ""),
            "is_public": p.get("is_public", False),
            "likes": p.get("likes", 0),
            "author": p.get("author_name", "Anonymous"),
            "is_mine": user and str(user.get("_id")) == p.get("user_id"),
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        }
    
    return {
        "public_presets": [format_preset(p) for p in public_presets],
        "my_presets": [format_preset(p) for p in user_presets]
    }

@api_router.post("/theme-presets", response_model=dict)
async def create_theme_preset(preset: ThemePreset, user = Depends(get_current_user_local)):
    """Create a new theme preset"""
    preset_data = {
        "user_id": str(user["_id"]),
        "author_name": user.get("username", "Anonymous"),
        "name": preset.name,
        "is_dark": preset.is_dark,
        "accent_color": preset.accent_color,
        "description": preset.description,
        "is_public": preset.is_public,
        "likes": 0,
        "created_at": datetime.utcnow()
    }
    
    result = await db.theme_presets.insert_one(preset_data)
    
    return {
        "id": str(result.inserted_id),
        "message": "Theme preset created successfully"
    }

@api_router.post("/theme-presets/{preset_id}/like", response_model=dict)
async def like_theme_preset(preset_id: str, user = Depends(get_current_user_local)):
    """Like/unlike a theme preset"""
    user_id = str(user["_id"])
    
    # Check if already liked
    existing = await db.theme_preset_likes.find_one({
        "preset_id": preset_id,
        "user_id": user_id
    })
    
    if existing:
        await db.theme_preset_likes.delete_one({"_id": existing["_id"]})
        await db.theme_presets.update_one(
            {"_id": ObjectId(preset_id)},
            {"$inc": {"likes": -1}}
        )
        return {"liked": False}
    else:
        await db.theme_preset_likes.insert_one({
            "preset_id": preset_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        await db.theme_presets.update_one(
            {"_id": ObjectId(preset_id)},
            {"$inc": {"likes": 1}}
        )
        return {"liked": True}

@api_router.delete("/theme-presets/{preset_id}", response_model=dict)
async def delete_theme_preset(preset_id: str, user = Depends(get_current_user_local)):
    """Delete a theme preset"""
    result = await db.theme_presets.delete_one({
        "_id": ObjectId(preset_id),
        "user_id": str(user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Preset not found or not owned by you")
    
    return {"deleted": True}

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
    content_filter: Optional[str] = Body(None),  # "strict", "moderate", "off"
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
    if content_filter is not None and content_filter in ["strict", "moderate", "off"]:
        update_data["content_filter"] = content_filter
    
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

@api_router.get("/users/search", response_model=dict)
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user = Depends(get_current_user_local)
):
    """
    Search users by first name, last name, email, username, or Ultimate Search page name.
    Returns matching users with their profiles.
    """
    query = q.strip().lower()
    
    # Build search filter - search across multiple fields
    search_filter = {
        "$or": [
            {"username": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
            {"first_name": {"$regex": query, "$options": "i"}},
            {"last_name": {"$regex": query, "$options": "i"}},
            {"callsign": {"$regex": query, "$options": "i"}},  # Ultimate Search page name
            {"ultimate_search_name": {"$regex": query, "$options": "i"}},
            # Also search by full name combination
            {"$expr": {
                "$regexMatch": {
                    "input": {"$concat": ["$first_name", " ", "$last_name"]},
                    "regex": query,
                    "options": "i"
                }
            }}
        ]
    }
    
    # Get total count
    total = await db.users.count_documents(search_filter)
    
    # Get paginated results
    skip = (page - 1) * limit
    cursor = db.users.find(
        search_filter,
        {
            "_id": 0,
            "hashed_password": 0,  # Never return password
            "reset_token": 0,
            "reset_token_expiry": 0
        }
    ).skip(skip).limit(limit).sort("username", 1)
    
    users = []
    async for u in cursor:
        # Add display name logic
        display_name = u.get("callsign") or u.get("ultimate_search_name") or u.get("username")
        users.append({
            "id": u.get("id"),
            "username": u.get("username"),
            "email": u.get("email") if user.get("is_admin") else None,  # Only admin sees emails
            "first_name": u.get("first_name", ""),
            "last_name": u.get("last_name", ""),
            "display_name": display_name,
            "callsign": u.get("callsign"),
            "ultimate_search_name": u.get("ultimate_search_name"),
            "avatar_url": u.get("avatar_url"),
            "bio": u.get("bio", ""),
            "is_premium": u.get("is_premium", False),
            "created_at": u.get("created_at"),
            "ultimate_search_public": u.get("ultimate_search_public", False)
        })
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
        "query": q
    }

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
        # Admin Price Controls
        {"key": "unpaid_max_protocol_price", "value": 0},  # 0 = disabled (no limit), >0 = max price unpaid users can set
        {"key": "unpaid_max_protocol_price_enabled", "value": False},  # Feature toggle (off by default)
        # Document Type Protocol Controls
        {"key": "protocol_controls_enabled", "value": True},
        {"key": "allowed_document_types", "value": ["News Article", "Blog Post", "Academic Paper", "Wiki", "Forum", "Government", "Video", "Personal Report", "Informative Ph.D", "InfoPilot Exclusive", "Personal Report (Organic)", "Personal Report (Collected)"]},
        # Newsletter Timing (tri-weekly by default)
        {"key": "newsletter_enabled", "value": True},
        {"key": "newsletter_time_1", "value": "05:46"},  # 5:46 AM
        {"key": "newsletter_time_2", "value": "09:42"},  # 9:42 AM
        {"key": "newsletter_time_3", "value": "16:20"},  # 4:20 PM
        {"key": "newsletter_ai_optimize", "value": True},  # AI-optimized send times
        # Collation Settings
        {"key": "collation_limit_per_search", "value": 40},  # Default 40 results per Search & Collate
        {"key": "collation_limit_min", "value": 1},
        {"key": "collation_limit_max", "value": 100},
        {"key": "auto_categorize_multiple", "value": True},  # Allow multiple category assignment
        # Document Type Protocol Scripts (InfoJet 2.0 format)
        {"key": "protocol_informative_phd", "value": "(Ph.D. or PhD or D.Phil. or Dr.) & (research or study or findings)"},
        {"key": "protocol_informative", "value": "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)"},
        {"key": "protocol_news_article", "value": "(news or story or breaking) & (reported or announced or revealed)"},
        {"key": "protocol_blog", "value": "(blog or blogger or blogging) & (post or article or opinion)"},
        {"key": "protocol_forum", "value": "(forum or thread or discussion or reply)"},
        {"key": "protocol_personal_report_collected", "value": "(I or my or me) & (believe or think or feel or experienced)"},
        # Pay-As-You-Go Promotion Message
        {"key": "paygo_promo_message", "value": "Pay-as-you-go promotion available while supplies last! We're testing our business model sustainability."},
        {"key": "paygo_promo_enabled", "value": True},
        # Minimum Payment (PayPal requirement)
        {"key": "minimum_payment", "value": 1.00},
        {"key": "admin_commission_percent", "value": 15},  # 15% to admin
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
    user_ids = [ObjectId(leader["user_id"]) for leader in leaders]
    users_list = await db.users.find({"_id": {"$in": user_ids}}).to_list(len(user_ids)) if user_ids else []
    users_map = {str(u["_id"]): u for u in users_list}
    
    leaderboard = []
    for i, leader in enumerate(leaders):
        user = users_map.get(leader["user_id"])
        if user:
            level_info = calculate_level(leader.get("xp", 0))
            leaderboard.append({
                "rank": i + 1,
                "user_id": leader["user_id"],
                "username": user.get("username", "Unknown"),
                "callsign": user.get("callsign", user.get("username", "Unknown")),
                "xp": leader.get("xp", 0),
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
    user_ids = [ObjectId(wl["_id"]) for wl in weekly_leaders]
    users_list = await db.users.find({"_id": {"$in": user_ids}}).to_list(len(user_ids)) if user_ids else []
    users_map = {str(u["_id"]): u for u in users_list}
    
    leaderboard = []
    for i, wl in enumerate(weekly_leaders):
        user = users_map.get(wl["_id"])
        if user:
            leaderboard.append({
                "rank": i + 1,
                "user_id": wl["_id"],
                "username": user.get("username", "Unknown"),
                "weekly_xp": wl["weekly_xp"]
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
    user_ids = [ObjectId(ml["_id"]) for ml in monthly_leaders]
    users_list = await db.users.find({"_id": {"$in": user_ids}}).to_list(len(user_ids)) if user_ids else []
    users_map = {str(u["_id"]): u for u in users_list}
    
    leaderboard = []
    for i, ml in enumerate(monthly_leaders):
        user = users_map.get(ml["_id"])
        if user:
            leaderboard.append({
                "rank": i + 1,
                "user_id": ml["_id"],
                "username": user.get("username", "Unknown"),
                "monthly_xp": ml["monthly_xp"]
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
            "sent_at": h.get("sent_at", datetime.utcnow()).isoformat() if h.get("sent_at") else datetime.utcnow().isoformat(),
            "recipient_count": h.get("recipient_count", 0)
        } for h in history if h]
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


@api_router.get("/analytics/quality-scores")
async def get_quality_score_analytics(user = Depends(get_current_user_local)):
    """
    Get quality score analytics showing distribution of content quality scores.
    Admin only endpoint for content curation insights.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get total results count
    total_results = await db.search_results.count_documents({})
    
    # Get distribution by quality score ranges
    quality_ranges = [
        {"name": "Premium", "emoji": "📚", "min": 80, "max": 100, "color": "#10b981"},
        {"name": "High Quality", "emoji": "✨", "min": 65, "max": 79, "color": "#3b82f6"},
        {"name": "Good", "emoji": "📄", "min": 50, "max": 64, "color": "#f59e0b"},
        {"name": "Below Average", "emoji": "📝", "min": 25, "max": 49, "color": "#f97316"},
        {"name": "Low Quality", "emoji": "⚠️", "min": 0, "max": 24, "color": "#ef4444"}
    ]
    
    distribution = []
    for range_info in quality_ranges:
        count = await db.search_results.count_documents({
            "content_quality_score": {"$gte": range_info["min"], "$lte": range_info["max"]}
        })
        # Also count results without a score (default to 50)
        if range_info["min"] <= 50 <= range_info["max"]:
            no_score_count = await db.search_results.count_documents({
                "content_quality_score": {"$exists": False}
            })
            count += no_score_count
        
        percentage = round((count / total_results * 100), 1) if total_results > 0 else 0
        distribution.append({
            "name": range_info["name"],
            "emoji": range_info["emoji"],
            "min_score": range_info["min"],
            "max_score": range_info["max"],
            "color": range_info["color"],
            "count": count,
            "percentage": percentage
        })
    
    # Get average quality score
    avg_pipeline = [
        {"$match": {"content_quality_score": {"$exists": True}}},
        {"$group": {"_id": None, "avg_score": {"$avg": "$content_quality_score"}}}
    ]
    avg_result = await db.search_results.aggregate(avg_pipeline).to_list(1)
    avg_score = round(avg_result[0]["avg_score"], 1) if avg_result else 50.0
    
    # Get top domains by quality score
    top_domains_pipeline = [
        {"$match": {"content_quality_score": {"$exists": True}, "root_domain": {"$exists": True, "$ne": ""}}},
        {"$group": {
            "_id": "$root_domain",
            "avg_score": {"$avg": "$content_quality_score"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gte": 3}}},  # At least 3 results from domain
        {"$sort": {"avg_score": -1}},
        {"$limit": 10}
    ]
    top_domains = await db.search_results.aggregate(top_domains_pipeline).to_list(10)
    
    # Get bottom domains (for improvement opportunities)
    bottom_domains_pipeline = [
        {"$match": {"content_quality_score": {"$exists": True}, "root_domain": {"$exists": True, "$ne": ""}}},
        {"$group": {
            "_id": "$root_domain",
            "avg_score": {"$avg": "$content_quality_score"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gte": 3}}},
        {"$sort": {"avg_score": 1}},
        {"$limit": 10}
    ]
    bottom_domains = await db.search_results.aggregate(bottom_domains_pipeline).to_list(10)
    
    # Get quality score trend over time (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    trend_pipeline = [
        {"$match": {
            "created_at": {"$gte": seven_days_ago},
            "content_quality_score": {"$exists": True}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "avg_score": {"$avg": "$content_quality_score"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    quality_trend = await db.search_results.aggregate(trend_pipeline).to_list(7)
    
    # Get article type quality breakdown
    article_type_pipeline = [
        {"$match": {"content_quality_score": {"$exists": True}}},
        {"$group": {
            "_id": "$article_type",
            "avg_score": {"$avg": "$content_quality_score"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"avg_score": -1}},
        {"$limit": 10}
    ]
    article_type_quality = await db.search_results.aggregate(article_type_pipeline).to_list(10)
    
    return {
        "total_results": total_results,
        "average_score": avg_score,
        "distribution": distribution,
        "top_quality_domains": [
            {"domain": d["_id"], "avg_score": round(d["avg_score"], 1), "count": d["count"]}
            for d in top_domains
        ],
        "improvement_opportunities": [
            {"domain": d["_id"], "avg_score": round(d["avg_score"], 1), "count": d["count"]}
            for d in bottom_domains
        ],
        "quality_trend": [
            {"date": t["_id"], "avg_score": round(t["avg_score"], 1), "count": t["count"]}
            for t in quality_trend
        ],
        "article_type_quality": [
            {"type": a["_id"] or "Unknown", "avg_score": round(a["avg_score"], 1), "count": a["count"]}
            for a in article_type_quality
        ],
        "insights": {
            "premium_percentage": distribution[0]["percentage"] if distribution else 0,
            "high_quality_percentage": distribution[0]["percentage"] + distribution[1]["percentage"] if len(distribution) >= 2 else 0,
            "needs_improvement_count": sum(d["count"] for d in distribution if d["min_score"] < 50)
        },
        "last_updated": datetime.utcnow().isoformat()
    }



# ============== DOMAIN BLOCKLIST MANAGEMENT ==============

@api_router.get("/admin/blocked-domains")
async def get_blocked_domains(user = Depends(get_current_user_local)):
    """Get list of blocked domains"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    blocked = await db.blocked_domains.find({}).sort("blocked_at", -1).to_list(500)
    
    return {
        "blocked_domains": [
            {
                "id": str(d["_id"]),
                "domain": d["domain"],
                "reason": d.get("reason", "Low quality content"),
                "avg_score": d.get("avg_score", 0),
                "result_count": d.get("result_count", 0),
                "blocked_by": d.get("blocked_by", "admin"),
                "blocked_at": d.get("blocked_at", datetime.utcnow()).isoformat()
            }
            for d in blocked
        ],
        "total_blocked": len(blocked)
    }


@api_router.post("/admin/blocked-domains")
async def add_blocked_domain(
    domain: str = Body(..., embed=True),
    reason: str = Body("Low quality content", embed=True),
    avg_score: float = Body(0, embed=True),
    result_count: int = Body(0, embed=True),
    user = Depends(get_current_user_local)
):
    """Add a domain to the blocklist"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if domain already blocked
    existing = await db.blocked_domains.find_one({"domain": domain.lower()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Domain '{domain}' is already blocked")
    
    # Add to blocklist
    result = await db.blocked_domains.insert_one({
        "domain": domain.lower(),
        "reason": reason,
        "avg_score": avg_score,
        "result_count": result_count,
        "blocked_by": user.get("email", "admin"),
        "blocked_at": datetime.utcnow()
    })
    
    # Optionally remove existing results from this domain
    deleted = await db.search_results.delete_many({"root_domain": domain.lower()})
    
    logger.info(f"Domain blocked: {domain} by {user.get('email')}, removed {deleted.deleted_count} results")
    
    return {
        "success": True,
        "message": f"Domain '{domain}' added to blocklist",
        "results_removed": deleted.deleted_count,
        "blocked_domain": {
            "id": str(result.inserted_id),
            "domain": domain.lower(),
            "reason": reason,
            "blocked_at": datetime.utcnow().isoformat()
        }
    }


@api_router.delete("/admin/blocked-domains/{domain}")
async def remove_blocked_domain(domain: str, user = Depends(get_current_user_local)):
    """Remove a domain from the blocklist"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.blocked_domains.delete_one({"domain": domain.lower()})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found in blocklist")
    
    logger.info(f"Domain unblocked: {domain} by {user.get('email')}")
    
    return {
        "success": True,
        "message": f"Domain '{domain}' removed from blocklist"
    }


@api_router.post("/admin/blocked-domains/bulk")
async def bulk_block_domains(
    domains: list = Body(..., embed=True),
    user = Depends(get_current_user_local)
):
    """Block multiple domains at once from Quality Analytics improvement list"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    blocked_count = 0
    skipped_count = 0
    total_results_removed = 0
    
    for domain_info in domains:
        domain = domain_info.get("domain", "").lower() if isinstance(domain_info, dict) else str(domain_info).lower()
        if not domain:
            continue
            
        # Check if already blocked
        existing = await db.blocked_domains.find_one({"domain": domain})
        if existing:
            skipped_count += 1
            continue
        
        # Add to blocklist
        await db.blocked_domains.insert_one({
            "domain": domain,
            "reason": domain_info.get("reason", "Low quality content") if isinstance(domain_info, dict) else "Low quality content",
            "avg_score": domain_info.get("avg_score", 0) if isinstance(domain_info, dict) else 0,
            "result_count": domain_info.get("count", 0) if isinstance(domain_info, dict) else 0,
            "blocked_by": user.get("email", "admin"),
            "blocked_at": datetime.utcnow()
        })
        blocked_count += 1
        
        # Remove results from this domain
        deleted = await db.search_results.delete_many({"root_domain": domain})
        total_results_removed += deleted.deleted_count
    
    logger.info(f"Bulk domain block: {blocked_count} blocked, {skipped_count} skipped, {total_results_removed} results removed by {user.get('email')}")
    
    return {
        "success": True,
        "blocked_count": blocked_count,
        "skipped_count": skipped_count,
        "total_results_removed": total_results_removed,
        "message": f"Blocked {blocked_count} domains, removed {total_results_removed} results"
    }


# ============== AUTOMATIC DOMAIN SCORING & ALERTS ==============

@api_router.post("/admin/domain-scoring/run")
async def run_domain_scoring(user = Depends(get_current_user_local)):
    """
    Run automatic domain scoring analysis.
    Identifies domains with consistently low quality scores and creates alerts.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get domains with their average quality scores (minimum 5 results)
    domain_analysis_pipeline = [
        {"$match": {"root_domain": {"$exists": True, "$ne": ""}}},
        {"$group": {
            "_id": "$root_domain",
            "avg_score": {"$avg": {"$ifNull": ["$content_quality_score", 50]}},
            "result_count": {"$sum": 1},
            "min_score": {"$min": {"$ifNull": ["$content_quality_score", 50]}},
            "max_score": {"$max": {"$ifNull": ["$content_quality_score", 50]}},
            "latest_result": {"$max": "$created_at"}
        }},
        {"$match": {"result_count": {"$gte": 5}}},  # At least 5 results
        {"$sort": {"avg_score": 1}}
    ]
    
    all_domains = await db.search_results.aggregate(domain_analysis_pipeline).to_list(1000)
    
    # Get already blocked domains
    blocked = await db.blocked_domains.distinct("domain")
    blocked_set = set(blocked)
    
    # Define alert thresholds
    CRITICAL_THRESHOLD = 30  # Score < 30 is critical
    WARNING_THRESHOLD = 45   # Score < 45 is warning
    WATCH_THRESHOLD = 55     # Score < 55 is watch
    
    alerts_created = 0
    alerts_updated = 0
    
    for domain_data in all_domains:
        domain = domain_data["_id"]
        avg_score = domain_data["avg_score"]
        result_count = domain_data["result_count"]
        
        # Skip already blocked domains
        if domain in blocked_set:
            continue
        
        # Determine alert level
        if avg_score < CRITICAL_THRESHOLD:
            alert_level = "critical"
            alert_message = f"Critical: {domain} has very low quality (avg: {avg_score:.1f})"
        elif avg_score < WARNING_THRESHOLD:
            alert_level = "warning"
            alert_message = f"Warning: {domain} has below-average quality (avg: {avg_score:.1f})"
        elif avg_score < WATCH_THRESHOLD:
            alert_level = "watch"
            alert_message = f"Watch: {domain} quality is declining (avg: {avg_score:.1f})"
        else:
            # Remove any existing alert for this domain if quality improved
            await db.domain_alerts.delete_one({"domain": domain})
            continue
        
        # Check for existing alert
        existing_alert = await db.domain_alerts.find_one({"domain": domain})
        
        if existing_alert:
            # Update existing alert
            await db.domain_alerts.update_one(
                {"domain": domain},
                {"$set": {
                    "alert_level": alert_level,
                    "avg_score": round(avg_score, 1),
                    "result_count": result_count,
                    "min_score": round(domain_data["min_score"], 1),
                    "max_score": round(domain_data["max_score"], 1),
                    "message": alert_message,
                    "latest_result": domain_data.get("latest_result"),
                    "updated_at": datetime.utcnow()
                }}
            )
            alerts_updated += 1
        else:
            # Create new alert
            await db.domain_alerts.insert_one({
                "domain": domain,
                "alert_level": alert_level,
                "avg_score": round(avg_score, 1),
                "result_count": result_count,
                "min_score": round(domain_data["min_score"], 1),
                "max_score": round(domain_data["max_score"], 1),
                "message": alert_message,
                "latest_result": domain_data.get("latest_result"),
                "dismissed": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            alerts_created += 1
    
    # Get summary counts
    total_alerts = await db.domain_alerts.count_documents({"dismissed": False})
    critical_count = await db.domain_alerts.count_documents({"alert_level": "critical", "dismissed": False})
    warning_count = await db.domain_alerts.count_documents({"alert_level": "warning", "dismissed": False})
    watch_count = await db.domain_alerts.count_documents({"alert_level": "watch", "dismissed": False})
    
    logger.info(f"Domain scoring completed: {alerts_created} new alerts, {alerts_updated} updated")
    
    return {
        "success": True,
        "alerts_created": alerts_created,
        "alerts_updated": alerts_updated,
        "summary": {
            "total_alerts": total_alerts,
            "critical": critical_count,
            "warning": warning_count,
            "watch": watch_count
        },
        "thresholds": {
            "critical": f"< {CRITICAL_THRESHOLD}",
            "warning": f"< {WARNING_THRESHOLD}",
            "watch": f"< {WATCH_THRESHOLD}"
        },
        "last_run": datetime.utcnow().isoformat()
    }


@api_router.get("/admin/domain-alerts")
async def get_domain_alerts(
    include_dismissed: bool = Query(False),
    alert_level: Optional[str] = Query(None),
    user = Depends(get_current_user_local)
):
    """Get all domain quality alerts"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if not include_dismissed:
        query["dismissed"] = {"$ne": True}
    if alert_level:
        query["alert_level"] = alert_level
    
    alerts = await db.domain_alerts.find(query).sort([
        ("alert_level", 1),  # critical first
        ("avg_score", 1)     # then by score ascending
    ]).to_list(500)
    
    # Get summary counts
    total = await db.domain_alerts.count_documents({"dismissed": {"$ne": True}})
    critical = await db.domain_alerts.count_documents({"alert_level": "critical", "dismissed": {"$ne": True}})
    warning = await db.domain_alerts.count_documents({"alert_level": "warning", "dismissed": {"$ne": True}})
    watch = await db.domain_alerts.count_documents({"alert_level": "watch", "dismissed": {"$ne": True}})
    
    return {
        "alerts": [
            {
                "id": str(a["_id"]),
                "domain": a["domain"],
                "alert_level": a["alert_level"],
                "avg_score": a["avg_score"],
                "result_count": a["result_count"],
                "min_score": a.get("min_score", 0),
                "max_score": a.get("max_score", 100),
                "message": a.get("message", ""),
                "dismissed": a.get("dismissed", False),
                "created_at": a.get("created_at", datetime.utcnow()).isoformat(),
                "updated_at": a.get("updated_at", datetime.utcnow()).isoformat()
            }
            for a in alerts
        ],
        "summary": {
            "total": total,
            "critical": critical,
            "warning": warning,
            "watch": watch
        }
    }


@api_router.post("/admin/domain-alerts/{alert_id}/dismiss")
async def dismiss_domain_alert(alert_id: str, user = Depends(get_current_user_local)):
    """Dismiss a domain alert"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.domain_alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"dismissed": True, "dismissed_by": user.get("email"), "dismissed_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"success": True, "message": "Alert dismissed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.post("/admin/domain-alerts/{alert_id}/block")
async def block_from_alert(alert_id: str, user = Depends(get_current_user_local)):
    """Block domain directly from an alert"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        alert = await db.domain_alerts.find_one({"_id": ObjectId(alert_id)})
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        domain = alert["domain"]
        
        # Check if already blocked
        existing = await db.blocked_domains.find_one({"domain": domain})
        if existing:
            # Just dismiss the alert
            await db.domain_alerts.update_one(
                {"_id": ObjectId(alert_id)},
                {"$set": {"dismissed": True, "dismissed_by": user.get("email"), "dismissed_at": datetime.utcnow()}}
            )
            return {"success": True, "message": f"Domain '{domain}' already blocked, alert dismissed"}
        
        # Add to blocklist
        await db.blocked_domains.insert_one({
            "domain": domain,
            "reason": f"Auto-flagged: {alert.get('message', 'Low quality')}",
            "avg_score": alert.get("avg_score", 0),
            "result_count": alert.get("result_count", 0),
            "blocked_by": user.get("email", "admin"),
            "blocked_at": datetime.utcnow(),
            "from_alert": True
        })
        
        # Remove results
        deleted = await db.search_results.delete_many({"root_domain": domain})
        
        # Dismiss the alert
        await db.domain_alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"dismissed": True, "blocked": True, "dismissed_by": user.get("email"), "dismissed_at": datetime.utcnow()}}
        )
        
        logger.info(f"Domain blocked from alert: {domain} by {user.get('email')}, removed {deleted.deleted_count} results")
        
        return {
            "success": True,
            "message": f"Domain '{domain}' blocked",
            "results_removed": deleted.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.delete("/admin/domain-alerts/clear-dismissed")
async def clear_dismissed_alerts(user = Depends(get_current_user_local)):
    """Clear all dismissed alerts"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.domain_alerts.delete_many({"dismissed": True})
    
    return {
        "success": True,
        "deleted_count": result.deleted_count,
        "message": f"Cleared {result.deleted_count} dismissed alerts"
    }


@api_router.get("/admin/domain-scoring/schedule")
async def get_domain_scoring_schedule(user = Depends(get_current_user_local)):
    """Get domain scoring schedule configuration"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    config = await db.domain_scoring_config.find_one({"type": "schedule"})
    
    if not config:
        # Return default config
        return {
            "enabled": False,
            "schedule": "daily",
            "run_hour": 6,
            "email_notifications": True,
            "notification_emails": ["jjspilot24@gmail.com"],
            "last_run": None,
            "last_run_results": None,
            "next_run": None
        }
    
    # Calculate next run time
    next_run = None
    if config.get("enabled"):
        now = datetime.utcnow()
        run_hour = config.get("run_hour", 6)
        schedule = config.get("schedule", "daily")
        
        if schedule == "daily":
            next_run = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif schedule == "weekly":
            next_run = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            days_until_next = 7 - now.weekday()  # Next Monday
            if days_until_next == 0 and now.hour >= run_hour:
                days_until_next = 7
            next_run += timedelta(days=days_until_next)
        elif schedule == "hourly":
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    return {
        "enabled": config.get("enabled", False),
        "schedule": config.get("schedule", "daily"),
        "run_hour": config.get("run_hour", 6),
        "email_notifications": config.get("email_notifications", True),
        "notification_emails": config.get("notification_emails", ["jjspilot24@gmail.com"]),
        "last_run": config.get("last_run").isoformat() if config.get("last_run") else None,
        "last_run_results": config.get("last_run_results"),
        "next_run": next_run.isoformat() if next_run else None
    }


@api_router.post("/admin/domain-scoring/schedule")
async def update_domain_scoring_schedule(
    enabled: bool = Body(..., embed=True),
    schedule: str = Body("daily", embed=True),
    run_hour: int = Body(6, embed=True),
    email_notifications: bool = Body(True, embed=True),
    notification_emails: List[str] = Body(["jjspilot24@gmail.com"], embed=True),
    user = Depends(get_current_user_local)
):
    """Update domain scoring schedule configuration"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate schedule
    if schedule not in ["hourly", "daily", "weekly"]:
        raise HTTPException(status_code=400, detail="Schedule must be 'hourly', 'daily', or 'weekly'")
    
    # Validate run_hour
    if not 0 <= run_hour <= 23:
        raise HTTPException(status_code=400, detail="Run hour must be between 0 and 23")
    
    # Update or create config
    await db.domain_scoring_config.update_one(
        {"type": "schedule"},
        {"$set": {
            "type": "schedule",
            "enabled": enabled,
            "schedule": schedule,
            "run_hour": run_hour,
            "email_notifications": email_notifications,
            "notification_emails": notification_emails,
            "updated_at": datetime.utcnow(),
            "updated_by": user.get("email")
        }},
        upsert=True
    )
    
    logger.info(f"Domain scoring schedule updated: enabled={enabled}, schedule={schedule}, hour={run_hour}, email={email_notifications} by {user.get('email')}")
    
    return {
        "success": True,
        "message": f"Schedule updated: {'Enabled' if enabled else 'Disabled'} ({schedule} at {run_hour}:00 UTC)",
        "config": {
            "enabled": enabled,
            "schedule": schedule,
            "run_hour": run_hour,
            "email_notifications": email_notifications,
            "notification_emails": notification_emails
        }
    }


@api_router.post("/admin/domain-scoring/test-email")
async def test_domain_scoring_email(user = Depends(get_current_user_local)):
    """Send a test email notification for domain scoring alerts"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from services.domain_scoring_scheduler import send_alert_notification
        
        config = await db.domain_scoring_config.find_one({"type": "schedule"})
        if not config:
            config = {"notification_emails": [user.get("email", "jjspilot24@gmail.com")]}
        
        # Create test alerts
        test_alerts = [
            {"domain": "test-critical.example.com", "level": "critical", "score": 25.0},
            {"domain": "test-warning.example.com", "level": "warning", "score": 40.0}
        ]
        
        await send_alert_notification(config, 1, 1, test_alerts)
        
        return {
            "success": True,
            "message": f"Test email sent to {config.get('notification_emails', [])}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")


# ============== REVENUE DASHBOARD ==============

@api_router.get("/admin/revenue-dashboard")
async def get_revenue_dashboard(
    days: int = Query(30, ge=1, le=365),
    user = Depends(get_current_user_local)
):
    """
    Unified Revenue Dashboard showing:
    - Protocol sales revenue
    - Subscription revenue  
    - A/B test conversion rates
    - Performance trends
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from datetime import datetime, timedelta, timezone
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # 1. Protocol Sales Revenue
    protocol_sales = await db.protocol_purchases.aggregate([
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$price"},
            "total_sales": {"$sum": 1},
            "unique_buyers": {"$addToSet": "$buyer_id"}
        }}
    ]).to_list(1)
    
    protocol_revenue = protocol_sales[0] if protocol_sales else {"total_revenue": 0, "total_sales": 0, "unique_buyers": []}
    
    # Protocol sales by day
    protocol_by_day = await db.protocol_purchases.aggregate([
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "revenue": {"$sum": "$price"},
            "sales": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]).to_list(days)
    
    # Top selling protocols
    top_protocols = await db.protocol_purchases.aggregate([
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": "$protocol_id",
            "revenue": {"$sum": "$price"},
            "sales": {"$sum": 1}
        }},
        {"$sort": {"revenue": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get protocol names
    for p in top_protocols:
        if p["_id"]:
            try:
                protocol = await db.categories.find_one({"_id": ObjectId(p["_id"])})
                p["name"] = protocol.get("name", "Unknown") if protocol else "Unknown"
            except:
                p["name"] = "Unknown"
    
    # 2. Subscription Revenue
    subscription_revenue = await db.subscriptions.aggregate([
        {"$match": {"created_at": {"$gte": start_date}, "status": "active"}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount"},
            "total_subscriptions": {"$sum": 1},
            "monthly": {"$sum": {"$cond": [{"$eq": ["$plan", "monthly"]}, "$amount", 0]}},
            "yearly": {"$sum": {"$cond": [{"$eq": ["$plan", "yearly"]}, "$amount", 0]}}
        }}
    ]).to_list(1)
    
    sub_revenue = subscription_revenue[0] if subscription_revenue else {"total_revenue": 0, "total_subscriptions": 0, "monthly": 0, "yearly": 0}
    
    # Subscription by day
    sub_by_day = await db.subscriptions.aggregate([
        {"$match": {"created_at": {"$gte": start_date}, "status": "active"}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "revenue": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]).to_list(days)
    
    # 3. A/B Test Conversion Rates
    ab_test_stats = await db.ab_test_events.aggregate([
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": {"test": "$test_name", "variant": "$variant_id"},
            "impressions": {"$sum": {"$cond": [{"$eq": ["$event_type", "impression"]}, 1, 0]}},
            "conversions": {"$sum": {"$cond": [{"$eq": ["$event_type", "conversion"]}, 1, 0]}}
        }}
    ]).to_list(100)
    
    # Calculate conversion rates
    ab_performance = {}
    for stat in ab_test_stats:
        test_name = stat["_id"]["test"]
        if test_name not in ab_performance:
            ab_performance[test_name] = {"variants": [], "total_impressions": 0, "total_conversions": 0}
        
        impressions = stat.get("impressions", 0)
        conversions = stat.get("conversions", 0)
        rate = round((conversions / impressions * 100), 2) if impressions > 0 else 0
        
        ab_performance[test_name]["variants"].append({
            "variant_id": stat["_id"]["variant"],
            "impressions": impressions,
            "conversions": conversions,
            "conversion_rate": rate
        })
        ab_performance[test_name]["total_impressions"] += impressions
        ab_performance[test_name]["total_conversions"] += conversions
    
    # Calculate overall rate for each test
    for test_name, data in ab_performance.items():
        if data["total_impressions"] > 0:
            data["overall_conversion_rate"] = round((data["total_conversions"] / data["total_impressions"] * 100), 2)
        else:
            data["overall_conversion_rate"] = 0
    
    # 4. AI Recommendation Performance (from A/B testing)
    ai_rec_stats = await db.ai_recommendation_stats.find().to_list(100)
    ai_performance = []
    for stat in ai_rec_stats:
        views = stat.get("actions", {}).get("view", 0)
        copies = stat.get("actions", {}).get("copy", 0)
        creates = stat.get("actions", {}).get("create", 0)
        purchases = stat.get("actions", {}).get("purchase", 0)
        
        ai_performance.append({
            "category": stat.get("category"),
            "views": views,
            "copies": copies,
            "creates": creates,
            "purchases": purchases,
            "copy_rate": round((copies / views * 100), 2) if views > 0 else 0,
            "purchase_rate": round((purchases / views * 100), 2) if views > 0 else 0
        })
    
    # 5. Summary Metrics
    total_revenue = protocol_revenue.get("total_revenue", 0) + sub_revenue.get("total_revenue", 0)
    
    # User growth
    new_users = await db.users.count_documents({"created_at": {"$gte": start_date}})
    total_users = await db.users.count_documents({})
    
    # Active users (logged in last 7 days)
    active_users = await db.users.count_documents({
        "last_login": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
    })
    
    return {
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "protocol_revenue": round(protocol_revenue.get("total_revenue", 0), 2),
            "subscription_revenue": round(sub_revenue.get("total_revenue", 0), 2),
            "total_sales": protocol_revenue.get("total_sales", 0),
            "unique_buyers": len(protocol_revenue.get("unique_buyers", [])),
            "active_subscriptions": sub_revenue.get("total_subscriptions", 0),
            "new_users": new_users,
            "total_users": total_users,
            "active_users": active_users
        },
        "protocol_sales": {
            "total_revenue": round(protocol_revenue.get("total_revenue", 0), 2),
            "total_sales": protocol_revenue.get("total_sales", 0),
            "by_day": [{"date": d["_id"], "revenue": round(d["revenue"], 2), "sales": d["sales"]} for d in protocol_by_day],
            "top_sellers": [{"name": p.get("name", "Unknown"), "revenue": round(p["revenue"], 2), "sales": p["sales"]} for p in top_protocols]
        },
        "subscriptions": {
            "total_revenue": round(sub_revenue.get("total_revenue", 0), 2),
            "active_count": sub_revenue.get("total_subscriptions", 0),
            "monthly_revenue": round(sub_revenue.get("monthly", 0), 2),
            "yearly_revenue": round(sub_revenue.get("yearly", 0), 2),
            "by_day": [{"date": d["_id"], "revenue": round(d["revenue"], 2), "count": d["count"]} for d in sub_by_day]
        },
        "ab_testing": ab_performance,
        "ai_recommendations": ai_performance
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
app.include_router(category_export_router, prefix="/api")
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
    
    # Start the domain scoring scheduler
    try:
        from services.domain_scoring_scheduler import start_domain_scoring_scheduler
        start_domain_scoring_scheduler()
        logger.info("🔍 Domain scoring scheduler started successfully!")
    except Exception as e:
        logger.error(f"Failed to start domain scoring scheduler: {e}")

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
