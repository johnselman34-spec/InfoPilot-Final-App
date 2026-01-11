from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import re
import hashlib
import secrets
import httpx
from bson import ObjectId
import urllib.parse
import asyncio
import resend

# DuckDuckGo Search library for better results
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with Atlas-compatible settings
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

# Configure MongoDB client with longer timeouts for Atlas
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=30000,  # 30 seconds timeout for server selection
    connectTimeoutMS=30000,          # 30 seconds connection timeout
    socketTimeoutMS=30000,           # 30 seconds socket timeout
    retryWrites=True,                # Enable retry writes for Atlas
    w='majority'                     # Write concern for replica sets
)
db = client[os.environ.get('DB_NAME', 'infopilot_db')]

# PayPal Configuration
PAYPAL_PAYMENT_LINK = "https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ"

# Resend Email Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Book Promotion Data
BOOK_PROMO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "genre": "A True Supernatural Thriller Comedy",
    "price": "$2.99",
    "amazon_url": "https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191",
    "reviews_url": "https://readersfavorite.com/book-review/letters-to-evelyn",
    "review_count": 19,
    "review_source": "Readers' Favorite",
    "featured_review": {
        "reviewer": "Divine Zape",
        "source": "Readers' Favorite",
        "quote": "This memoir is a profound and unforgettable literary piece."
    },
    "images": [
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/rtfq9tzg_Letters%20to%20Evelyn%20advertisement%201.jpg",
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/c525b6c3_Letters%20to%20Evelyn%20advertisement%202.jpg",
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/w9somusu_Letters%20to%20Evelyn%20advertisement%203.jpg",
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/km4oz6iz_Letters%20to%20Evelyn%20advertisement%204.jpg"
    ]
}

# Create the main app
app = FastAPI(title="InfoPilot API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== CONTENT FILTER (DISABLED) ==============
# Content filtering has been disabled per user request
# All search terms and protocols are now allowed

BLOCKED_WORDS = set()  # Empty - no restrictions
PROFANITY_WORDS = set()  # Empty - no restrictions

def contains_blocked_content(text: str) -> bool:
    """Content filter disabled - always returns False"""
    return False

# ============== PYDANTIC MODELS ==============

class UserCreate(BaseModel):
    email: str
    username: str
    password: Optional[str] = None
    google_id: Optional[str] = None
    profile_picture: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    profile_picture: Optional[str] = None
    is_paid: bool = False
    is_admin: bool = False
    created_at: datetime
    ultimate_search_public: bool = False
    friends_visible: bool = False

class GoogleAuthRequest(BaseModel):
    email: str
    google_id: str
    name: str
    picture: Optional[str] = None

class CategoryCreate(BaseModel):
    name: str
    protocol: str
    parent_id: Optional[str] = None
    is_public: bool = False

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    protocol: Optional[str] = None
    is_public: Optional[bool] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    protocol: str
    user_id: str
    parent_id: Optional[str] = None
    is_public: bool
    level: int
    created_at: datetime
    children: List[Any] = []

class SearchResultCreate(BaseModel):
    url: str
    title: str
    snippet: str
    content: Optional[str] = None
    category_ids: List[str] = []
    article_type: str = "News Article"
    country_of_origin: Optional[str] = None
    detected_year: Optional[int] = None
    root_domain: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ReactionCreate(BaseModel):
    search_result_id: str
    reaction_type: str  # Like, Love, Funny, Sad, Caution, Spam, Best

class SearchRequest(BaseModel):
    query: str
    
class CollateRequest(BaseModel):
    search_results: List[Dict[str, Any]]

class FriendRequest(BaseModel):
    target_user_id: str

class MessageCreate(BaseModel):
    recipient_id: str
    content: str

class PaymentVerification(BaseModel):
    payment_id: str
    user_id: str

# ============== PROTOCOL PARSER (InfoPilot 2.0) ==============

class ProtocolParser:
    """
    Parse and evaluate InfoPilot 2.0 Boolean protocols
    
    Protocol Format Examples:
    - (word1 or word2) - Match ANY word in group
    - (word1 or word2)+ - ALL words must be present (INCLUDE ALL)
    - (word1 or word2)^ - ALL words must be ABSENT (EXCLUDE ALL)
    - "multi word phrase" - Exact phrase matching
    - (U.S. or USA or United States) - Handles abbreviations with punctuation
    
    Case-insensitive by default
    """
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for consistent matching"""
        if not text:
            return ""
        # Keep periods in abbreviations like U.S., Ph.D.
        return text.lower()
    
    @staticmethod
    def extract_phrases_and_words(content: str) -> List[str]:
        """
        Extract both quoted phrases and individual words from protocol content
        Handles: "multi word phrase", single_word, U.S., Ph.D.
        """
        items = []
        
        # First extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', content)
        items.extend([q.strip().lower() for q in quoted])
        
        # Remove quoted parts and split rest by 'or'
        remaining = re.sub(r'"[^"]+"', '', content)
        parts = re.split(r'\s+or\s+', remaining, flags=re.IGNORECASE)
        
        for part in parts:
            part = part.strip().lower()
            if part:
                items.append(part)
        
        return items
    
    @staticmethod
    def parse_protocol(protocol: str) -> Dict[str, Any]:
        """
        Parse InfoPilot 2.0 protocol format:
        (word1 or word2) & (word3 or word4)+ & (word5)^
        
        + = INCLUDE ALL words in group
        ^ = EXCLUDE ALL words in group
        No modifier = OR logic (at least one must match)
        """
        if not protocol:
            return {"groups": [], "valid": False}
        
        # Find all groups with their modifiers
        # Pattern handles: (content), +(content), (content)+, ^(content), (content)^
        pattern = r'([+^]?)\s*\(([^)]+)\)\s*([+^]?)'
        matches = re.findall(pattern, protocol)
        
        groups = []
        for prefix_mod, content, suffix_mod in matches:
            modifier = prefix_mod.strip() or suffix_mod.strip() or None
            items = ProtocolParser.extract_phrases_and_words(content)
            if items:
                groups.append({
                    "items": items,
                    "modifier": modifier,
                    "original": content
                })
        
        return {"groups": groups, "valid": len(groups) > 0}
    
    @staticmethod
    def text_contains_item(text_lower: str, item: str) -> bool:
        """
        Check if text contains the item (word or phrase)
        MORE LENIENT matching for better results:
        - Handles abbreviations with periods (U.S., Ph.D., etc.)
        - Handles partial word matches for compound words
        - Case-insensitive
        """
        if not item or not text_lower:
            return False
        
        item = item.lower().strip()
        
        # For phrases with spaces, do substring match
        if ' ' in item:
            return item in text_lower
        
        # For abbreviations with periods (u.s., ph.d., etc.)
        if '.' in item:
            # Try with and without periods
            item_no_periods = item.replace('.', '')
            return item in text_lower or item_no_periods in text_lower
        
        # Direct substring match first (most lenient)
        if item in text_lower:
            return True
        
        # For single words, also try word boundary matching
        # But be lenient - match if the word appears anywhere
        try:
            pattern = r'\b' + re.escape(item) + r'\b'
            if re.search(pattern, text_lower):
                return True
        except:
            pass
        
        # Try partial match for longer words (stemming-like behavior)
        if len(item) >= 5:
            # Match if the item appears as part of a larger word
            if item in text_lower:
                return True
        
        return False
    
    @staticmethod
    def matches_protocol(text: str, protocol: str) -> bool:
        """
        Check if text matches the protocol requirements - MAXIMUM LENIENCY for broad matching
        
        For your protocol like:
        (George W Bush or President Bush) & (aviation career or pilot or air force) & ...
        
        We want to match if:
        1. The text contains ANY of the key subjects (George W Bush, President Bush)
        2. AND contains ANY of the related topics (pilot, aviation, air force, F-102, etc.)
        
        This is INTENTIONALLY VERY LENIENT to maximize categorization.
        """
        if not text or not protocol:
            return False
        
        text_lower = ProtocolParser.normalize_text(text)
        parsed = ProtocolParser.parse_protocol(protocol)
        
        if not parsed["valid"]:
            # If protocol parsing fails, try simple keyword matching
            keywords = re.findall(r'\w{3,}', protocol.lower())
            # Match if at least 2 keywords are found
            matches = sum(1 for kw in keywords if kw in text_lower)
            return matches >= 2
        
        # Count how many groups have at least one matching item
        groups_with_matches = 0
        total_non_exclude_groups = 0
        any_exclude_violated = False
        total_keyword_matches = 0
        
        for group in parsed["groups"]:
            items = group["items"]
            modifier = group["modifier"]
            
            if modifier == "^":
                # EXCLUDE ALL - if any excluded word is found, mark violation
                if any(ProtocolParser.text_contains_item(text_lower, item) for item in items):
                    any_exclude_violated = True
            else:
                total_non_exclude_groups += 1
                # Count individual keyword matches in this group
                matches_in_group = sum(1 for item in items if ProtocolParser.text_contains_item(text_lower, item))
                total_keyword_matches += matches_in_group
                
                if modifier == "+":
                    # INCLUDE ALL - all must be present
                    if all(ProtocolParser.text_contains_item(text_lower, item) for item in items):
                        groups_with_matches += 1
                else:
                    # OR logic - any one item matching counts
                    if any(ProtocolParser.text_contains_item(text_lower, item) for item in items):
                        groups_with_matches += 1
        
        # Don't match if exclude rules were violated
        if any_exclude_violated:
            return False
        
        # VERY LENIENT MATCHING:
        # Option 1: At least half the groups have matches
        # Option 2: At least 3 total keyword matches across all groups
        # Option 3: First group (usually the main subject) matches
        
        if total_non_exclude_groups == 0:
            return False
        
        # Match if:
        # - At least 50% of groups have matches, OR
        # - At least 3 keywords matched overall, OR  
        # - More than half the groups matched
        half_groups = (total_non_exclude_groups + 1) // 2
        
        return (
            groups_with_matches >= half_groups or
            total_keyword_matches >= 3 or
            (groups_with_matches >= 1 and total_keyword_matches >= 2)
        )
    
    @staticmethod
    def get_match_details(text: str, protocol: str) -> Dict[str, Any]:
        """Get detailed matching information for debugging"""
        if not text or not protocol:
            return {"matched": False, "details": []}
            
        parsed = ProtocolParser.parse_protocol(protocol)
        if not parsed["valid"]:
            return {"matched": False, "details": [], "error": "Invalid protocol"}
        
        text_lower = ProtocolParser.normalize_text(text)
        details = []
        all_passed = True
        
        for group in parsed["groups"]:
            items = group["items"]
            modifier = group["modifier"]
            group_result = {
                "original": group["original"],
                "modifier": modifier,
                "items": items,
                "item_matches": {}
            }
            
            for item in items:
                group_result["item_matches"][item] = ProtocolParser.text_contains_item(text_lower, item)
            
            if modifier == "+":
                group_result["passed"] = all(group_result["item_matches"].values())
            elif modifier == "^":
                group_result["passed"] = not any(group_result["item_matches"].values())
            else:
                group_result["passed"] = any(group_result["item_matches"].values())
            
            if not group_result["passed"]:
                all_passed = False
            
            details.append(group_result)
        
        return {"matched": all_passed, "details": details}

# ============== ARTICLE TYPE CLASSIFIER ==============

class ArticleClassifier:
    """Classify articles based on admin-configurable rules"""
    
    INFORMATIVE_PROTOCOL = "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)"
    PHD_KEYWORDS = ["ph.d.", "phd", "d.phil.", "dr."]
    PHD_MIN_WORDS = 1500
    PHD_KEYWORD_COUNT = 3
    
    NEWS_PROTOCOL = "(news) & (news or story or news story) & (news or story or news story)"
    NEWS_KEYWORD_COUNT = 3
    
    BLOG_KEYWORD = "blog"
    BLOG_MIN_COUNT = 3
    
    PERSONAL_REPORT_KEYWORD = "I"
    PERSONAL_MIN_COUNT = 3
    PERSONAL_MIN_WORDS = 75
    
    @classmethod
    def classify(cls, title: str, content: str) -> str:
        """Classify article type based on rules"""
        if not content:
            return "News Article"
        
        content_lower = content.lower()
        title_lower = title.lower() if title else ""
        word_count = len(content.split())
        
        # Check for Forum
        if "forum" in title_lower:
            return "Forum"
        
        # Check for Blog
        blog_count = content_lower.count(cls.BLOG_KEYWORD)
        if blog_count >= cls.BLOG_MIN_COUNT and cls.BLOG_KEYWORD in title_lower:
            return "Blog"
        
        # Check for Informative Ph.D.
        phd_count = sum(content_lower.count(kw) for kw in cls.PHD_KEYWORDS)
        if phd_count >= cls.PHD_KEYWORD_COUNT and word_count >= cls.PHD_MIN_WORDS:
            if ProtocolParser.matches_protocol(content, cls.INFORMATIVE_PROTOCOL):
                return "Informative Ph.D."
        
        # Check for Informative
        if ProtocolParser.matches_protocol(content, cls.INFORMATIVE_PROTOCOL):
            return "Informative"
        
        # Check for Personal Report (collected)
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para_words = len(para.split())
            if para_words >= cls.PERSONAL_MIN_WORDS:
                unquoted = re.sub(r'"[^"]*"', '', para)
                unquoted = re.sub(r"'[^']*'", '', unquoted)
                i_count = len(re.findall(r'\bI\b', unquoted))
                if i_count >= cls.PERSONAL_MIN_COUNT:
                    return "Personal Report (collected)"
        
        # Check for News Article
        news_count = content_lower.count("news")
        if news_count >= cls.NEWS_KEYWORD_COUNT:
            return "News Article"
        
        return "News Article"

# ============== HELPER FUNCTIONS ==============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except:
        return None

# ============== WEB SEARCH SERVICE ==============

class WebSearchService:
    """
    Aggressive multi-source web search service for MAXIMUM results
    The goal is to get as many results as possible for protocol matching
    Now with TRUE PAGINATION to get hundreds of results
    """
    
    @staticmethod
    async def search_ddgs_library(query: str, num_results: int = 200) -> List[Dict[str, Any]]:
        """Use the duckduckgo-search library for better results"""
        results = []
        
        if not DDGS_AVAILABLE:
            logger.warning("DDGS library not available")
            return results
        
        try:
            # Run in thread pool since DDGS is synchronous
            def _search():
                with DDGS() as ddgs:
                    # Get text results
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
                except:
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
    async def search_duckduckgo(query: str, num_results: int = 200) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo HTML - with pagination for MORE results"""
        results = []
        seen_urls = set()
        
        try:
            async with httpx.AsyncClient() as client:
                # DuckDuckGo pagination uses 's' parameter
                for page in range(min(10, (num_results // 20) + 1)):  # Up to 10 pages
                    encoded_query = urllib.parse.quote(query)
                    # s=0 is page 1, s=20 is page 2, etc.
                    offset = page * 30
                    url = f"https://html.duckduckgo.com/html/?q={encoded_query}&s={offset}"
                    
                    try:
                        response = await client.get(
                            url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            },
                            timeout=30.0
                        )
                        
                        # Handle rate limiting
                        if response.status_code == 202:
                            await asyncio.sleep(1)
                            response = await client.get(url, headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                            }, timeout=30.0)
                        
                        if response.status_code == 200:
                            html = response.text
                            
                            # Parse results
                            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
                            snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+)</a>'
                            
                            urls_found = re.findall(result_pattern, html)
                            snippets = re.findall(snippet_pattern, html)
                            
                            page_results = 0
                            for i, (url_match, title) in enumerate(urls_found):
                                # Decode DuckDuckGo redirect URL
                                actual_url = url_match
                                if "//duckduckgo.com/l/?uddg=" in url_match:
                                    try:
                                        actual_url = urllib.parse.unquote(url_match.split("uddg=")[1].split("&")[0])
                                    except:
                                        pass
                                
                                # Skip ads and duplicates
                                if "duckduckgo.com" in actual_url or actual_url in seen_urls:
                                    continue
                                
                                seen_urls.add(actual_url)
                                snippet = snippets[i] if i < len(snippets) else ""
                                
                                try:
                                    parsed = urllib.parse.urlparse(actual_url)
                                    root_domain = parsed.netloc
                                except:
                                    root_domain = ""
                                
                                results.append({
                                    "url": actual_url,
                                    "title": title.strip(),
                                    "snippet": snippet.strip(),
                                    "content": snippet.strip(),
                                    "root_domain": root_domain,
                                    "source": "duckduckgo"
                                })
                                page_results += 1
                            
                            # If no results on this page, stop
                            if page_results == 0:
                                break
                                
                    except Exception as e:
                        logger.debug(f"DDG page {page} error: {e}")
                    
                    if len(results) >= num_results:
                        break
                    
                    # Small delay between pages
                    await asyncio.sleep(0.3)
                    
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        logger.info(f"DuckDuckGo returned {len(results)} results")
        return results[:num_results]
    
    @staticmethod
    async def search_bing_scrape(query: str, num_results: int = 150) -> List[Dict[str, Any]]:
        """Scrape Bing search results with PAGINATION"""
        results = []
        seen_urls = set()
        
        try:
            async with httpx.AsyncClient() as client:
                # Bing pagination: first=1, 11, 21, 31, etc.
                for page in range(min(15, (num_results // 10) + 1)):  # Up to 15 pages
                    encoded_query = urllib.parse.quote(query)
                    first = page * 10 + 1
                    url = f"https://www.bing.com/search?q={encoded_query}&first={first}&count=30"
                    
                    try:
                        response = await client.get(
                            url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Accept-Language": "en-US,en;q=0.5"
                            },
                            timeout=15.0,
                            follow_redirects=True
                        )
                        
                        if response.status_code == 200:
                            html = response.text
                            
                            # Multiple patterns to catch more results
                            patterns = [
                                r'<h2[^>]*><a[^>]*href="(https?://[^"]+)"[^>]*>([^<]+)</a></h2>',
                                r'<a[^>]*href="(https?://[^"]+)"[^>]*class="[^"]*tilk[^"]*"[^>]*>([^<]*)</a>',
                                r'<cite[^>]*>(https?://[^<]+)</cite>.*?<h2[^>]*>([^<]+)</h2>'
                            ]
                            
                            page_results = 0
                            for pattern in patterns:
                                matches = re.findall(pattern, html, re.DOTALL)
                                for match in matches:
                                    url_found = match[0] if match[0].startswith('http') else match[1]
                                    title = match[1] if match[0].startswith('http') else match[0]
                                    
                                    # Skip Bing/Microsoft domains
                                    if any(x in url_found for x in ['bing.com', 'microsoft.com', 'msn.com', 'microsofttranslator']):
                                        continue
                                    
                                    if url_found in seen_urls:
                                        continue
                                    
                                    seen_urls.add(url_found)
                                    
                                    try:
                                        parsed = urllib.parse.urlparse(url_found)
                                        root_domain = parsed.netloc
                                    except:
                                        root_domain = ""
                                    
                                    results.append({
                                        "url": url_found,
                                        "title": title.strip() if title else "",
                                        "snippet": "",
                                        "content": "",
                                        "root_domain": root_domain,
                                        "source": "bing"
                                    })
                                    page_results += 1
                            
                            if page_results == 0:
                                break
                                
                    except Exception as e:
                        logger.debug(f"Bing page {page} error: {e}")
                    
                    if len(results) >= num_results:
                        break
                    
                    await asyncio.sleep(0.2)
                    
        except Exception as e:
            logger.error(f"Bing scrape error: {e}")
        
        logger.info(f"Bing returned {len(results)} results")
        return results[:num_results]
    
    @staticmethod
    async def search_google_scrape(query: str, num_results: int = 100) -> List[Dict[str, Any]]:
        """Scrape Google search results with pagination"""
        results = []
        seen_urls = set()
        
        try:
            async with httpx.AsyncClient() as client:
                # Google pagination: start=0, 10, 20, etc.
                for page in range(min(10, (num_results // 10) + 1)):
                    encoded_query = urllib.parse.quote(query)
                    start = page * 10
                    url = f"https://www.google.com/search?q={encoded_query}&start={start}&num=20"
                    
                    try:
                        response = await client.get(
                            url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Accept-Language": "en-US,en;q=0.9"
                            },
                            timeout=15.0,
                            follow_redirects=True
                        )
                        
                        if response.status_code == 200:
                            html = response.text
                            
                            # Google result patterns
                            patterns = [
                                r'<a[^>]*href="/url\?q=(https?://[^&"]+)',
                                r'<a[^>]*href="(https?://(?!google\.com)[^"]+)"[^>]*>',
                                r'<cite[^>]*class="[^"]*"[^>]*>(https?://[^<]+)</cite>'
                            ]
                            
                            page_results = 0
                            for pattern in patterns:
                                matches = re.findall(pattern, html)
                                for url_found in matches:
                                    # Decode URL
                                    url_found = urllib.parse.unquote(url_found.split('&')[0])
                                    
                                    # Skip Google domains
                                    if any(x in url_found for x in ['google.com', 'googleapis.com', 'gstatic.com', 'youtube.com']):
                                        continue
                                    
                                    if url_found in seen_urls:
                                        continue
                                    
                                    seen_urls.add(url_found)
                                    
                                    try:
                                        parsed = urllib.parse.urlparse(url_found)
                                        root_domain = parsed.netloc
                                    except:
                                        root_domain = ""
                                    
                                    results.append({
                                        "url": url_found,
                                        "title": "",
                                        "snippet": "",
                                        "content": "",
                                        "root_domain": root_domain,
                                        "source": "google"
                                    })
                                    page_results += 1
                            
                            if page_results == 0:
                                break
                                
                    except Exception as e:
                        logger.debug(f"Google page {page} error: {e}")
                    
                    if len(results) >= num_results:
                        break
                    
                    await asyncio.sleep(0.5)  # Slower to avoid blocking
                    
        except Exception as e:
            logger.error(f"Google scrape error: {e}")
        
        logger.info(f"Google returned {len(results)} results")
        return results[:num_results]
    
    @staticmethod
    async def fetch_page_content(url: str, timeout: int = 8) -> Dict[str, str]:
        """Fetch and extract FULL content from a webpage for better matching"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                    timeout=float(timeout),
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Extract title
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
                    title = title_match.group(1).strip() if title_match else ""
                    
                    # Extract meta description
                    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                    if not desc_match:
                        desc_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
                    description = desc_match.group(1).strip() if desc_match else ""
                    
                    # Extract ALL text content for better matching
                    # Remove script and style tags
                    body_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                    body_html = re.sub(r'<style[^>]*>.*?</style>', '', body_html, flags=re.DOTALL | re.IGNORECASE)
                    body_html = re.sub(r'<noscript[^>]*>.*?</noscript>', '', body_html, flags=re.DOTALL | re.IGNORECASE)
                    
                    # Remove all HTML tags and get text
                    text = re.sub(r'<[^>]+>', ' ', body_html)
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    # Get first 10000 chars for matching
                    body_text = text[:10000]
                    
                    return {
                        "title": title,
                        "description": description,
                        "content": f"{title} {description} {body_text}"
                    }
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
        
        return {"title": "", "description": "", "content": ""}
    
    @staticmethod
    async def search(query: str, num_results: int = 500, max_pages: int = 99) -> List[Dict[str, Any]]:
        """
        Perform web search using MULTIPLE sources with PAGINATION
        Returns deduplicated results with content enrichment
        Now uses DDGS library as primary source for MAXIMUM results
        """
        all_results = []
        seen_urls = set()
        
        try:
            logger.info(f"Starting aggressive search for: {query}")
            
            # Primary: Use DDGS library (most reliable)
            if DDGS_AVAILABLE:
                ddgs_results = await WebSearchService.search_ddgs_library(query, min(200, num_results))
                for result in ddgs_results:
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)
                logger.info(f"DDGS library contributed {len(ddgs_results)} results")
            
            # Secondary: Run scrapers for additional results
            ddg_task = WebSearchService.search_duckduckgo(query, min(200, num_results))
            bing_task = WebSearchService.search_bing_scrape(query, min(150, num_results))
            google_task = WebSearchService.search_google_scrape(query, min(100, num_results))
            
            results = await asyncio.gather(
                ddg_task, 
                bing_task,
                google_task,
                return_exceptions=True
            )
            
            # Process all scraper results
            source_names = ["DuckDuckGo Scrape", "Bing", "Google"]
            for i, source_results in enumerate(results):
                if isinstance(source_results, list):
                    added = 0
                    for result in source_results:
                        url = result.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(result)
                            added += 1
                    logger.info(f"{source_names[i]} contributed {added} unique results")
                else:
                    logger.error(f"{source_names[i]} error: {source_results}")
            
            logger.info(f"Total unique results from all sources: {len(all_results)}")
            
        except Exception as e:
            logger.error(f"Search aggregation error: {e}")
        
        # Fetch content for ALL results to improve protocol matching
        if all_results:
            logger.info(f"Fetching content for {len(all_results)} results...")
            batch_size = 25
            
            for i in range(0, len(all_results), batch_size):
                batch = all_results[i:i+batch_size]
                tasks = [WebSearchService.fetch_page_content(r["url"]) for r in batch]
                
                try:
                    contents = await asyncio.gather(*tasks, return_exceptions=True)
                    for j, content in enumerate(contents):
                        idx = i + j
                        if isinstance(content, dict) and idx < len(all_results):
                            if content.get("title"):
                                all_results[idx]["title"] = content["title"]
                            if content.get("content"):
                                all_results[idx]["content"] = content["content"]
                            if content.get("description"):
                                all_results[idx]["snippet"] = content["description"]
                except Exception as e:
                    logger.debug(f"Content enrichment batch error: {e}")
        
        logger.info(f"Search for '{query}' returning {len(all_results)} results (with content enrichment)")
        return all_results[:num_results]
    
# ============== AUTH ENDPOINTS ==============

@api_router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    # Check blocked content in username
    if contains_blocked_content(user.username):
        raise HTTPException(status_code=400, detail="Username contains blocked content")
    
    # Check if user exists - case-insensitive email check
    existing = await db.users.find_one({
        "$or": [
            {"email": {"$regex": f"^{re.escape(user.email)}$", "$options": "i"}},
            {"username": user.username}
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    user_doc = {
        "email": user.email,
        "username": user.username,
        "password_hash": hash_password(user.password) if user.password else None,
        "google_id": user.google_id,
        "profile_picture": user.profile_picture,
        "is_paid": False,
        "is_admin": False,
        "created_at": datetime.utcnow(),
        "ultimate_search_public": False,
        "friends_visible": False,
        "friends": [],
        "friend_requests_sent": [],
        "friend_requests_received": [],
        "daily_collate_count": 0,
        "last_collate_date": None
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Create session
    token = generate_token()
    await db.sessions.insert_one({
        "user_id": str(result.inserted_id),
        "token": token,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=30)
    })
    
    return {
        "token": token,
        "user": {
            "id": str(result.inserted_id),
            "email": user.email,
            "username": user.username,
            "is_paid": False,
            "is_admin": False
        }
    }

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    # Case-insensitive email lookup
    user = await db.users.find_one({"email": {"$regex": f"^{re.escape(credentials.email)}$", "$options": "i"}})
    
    if not user or user.get("password_hash") != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = generate_token()
    await db.sessions.insert_one({
        "user_id": str(user["_id"]),
        "token": token,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=30)
    })
    
    return {
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "username": user["username"],
            "is_paid": user.get("is_paid", False),
            "is_admin": user.get("is_admin", False),
            "profile_picture": user.get("profile_picture")
        }
    }

@api_router.post("/auth/google", response_model=dict)
async def google_auth(data: GoogleAuthRequest):
    # Check if user exists - use case-insensitive email matching
    user = await db.users.find_one({
        "$or": [
            {"email": {"$regex": f"^{re.escape(data.email)}$", "$options": "i"}},
            {"google_id": data.google_id}
        ]
    })
    
    if user:
        # Update google_id if needed
        if not user.get("google_id"):
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"google_id": data.google_id, "profile_picture": data.picture}}
            )
    else:
        # Create new user
        username = data.name.replace(" ", "_").lower()[:20]
        base_username = username
        counter = 1
        while await db.users.find_one({"username": username}):
            username = f"{base_username}{counter}"
            counter += 1
        
        user_doc = {
            "email": data.email,
            "username": username,
            "password_hash": None,
            "google_id": data.google_id,
            "profile_picture": data.picture,
            "is_paid": False,
            "is_admin": False,
            "created_at": datetime.utcnow(),
            "ultimate_search_public": False,
            "friends_visible": False,
            "friends": [],
            "friend_requests_sent": [],
            "friend_requests_received": [],
            "daily_collate_count": 0,
            "last_collate_date": None
        }
        result = await db.users.insert_one(user_doc)
        user = await db.users.find_one({"_id": result.inserted_id})
    
    # Create session
    token = generate_token()
    await db.sessions.insert_one({
        "user_id": str(user["_id"]),
        "token": token,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=30)
    })
    
    return {
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "username": user["username"],
            "is_paid": user.get("is_paid", False),
            "is_admin": user.get("is_admin", False),
            "profile_picture": user.get("profile_picture")
        }
    }

# Backend proxy for Emergent Auth session data (to avoid CORS issues)
@api_router.get("/auth/google/session-data")
async def get_google_session_data(session_id: str = Query(..., description="Session ID from Emergent Auth")):
    """
    Proxy endpoint to fetch session data from Emergent Auth.
    This avoids CORS issues by making the request server-side.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data',
                headers={'X-Session-ID': session_id},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Emergent Auth error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch session data")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Authentication service timeout")
    except Exception as e:
        logger.error(f"Session data fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify Google session")

@api_router.get("/auth/me", response_model=dict)
async def get_me(user = Depends(get_current_user)):
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "username": user["username"],
        "is_paid": user.get("is_paid", False),
        "is_admin": user.get("is_admin", False),
        "profile_picture": user.get("profile_picture"),
        "ultimate_search_public": user.get("ultimate_search_public", False),
        "friends_visible": user.get("friends_visible", False),
        "friends_count": len(user.get("friends", []))
    }

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials:
        await db.sessions.delete_one({"token": credentials.credentials})
    return {"message": "Logged out"}

# ============== PAYMENT ENDPOINTS ==============

@api_router.get("/payment/link")
async def get_payment_link(user = Depends(get_current_user)):
    """Get PayPal payment link for subscription"""
    return {
        "payment_url": PAYPAL_PAYMENT_LINK,
        "price": 0.99,
        "currency": "USD",
        "description": "InfoPilot Premium Subscription"
    }

@api_router.post("/payment/verify")
async def verify_payment(data: PaymentVerification, user = Depends(get_current_user)):
    """Verify payment and upgrade user to premium"""
    # In production, verify with PayPal API
    # For now, mark user as paid
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_paid": True, "payment_date": datetime.utcnow()}}
    )
    
    return {"message": "Payment verified", "is_paid": True}

@api_router.post("/payment/activate")
async def activate_premium(user = Depends(get_current_user)):
    """Manually activate premium (for PayPal redirect confirmation)"""
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_paid": True, "payment_date": datetime.utcnow()}}
    )
    return {"message": "Premium activated", "is_paid": True}

@api_router.get("/subscription-info")
async def get_subscription_info():
    """Get subscription information for public display"""
    # Get settings from database
    settings_cursor = db.settings.find({})
    settings_dict = {}
    async for setting in settings_cursor:
        settings_dict[setting["key"]] = setting["value"]
    
    return {
        "subscription_price": settings_dict.get("subscription_price", 0.99),
        "paypal_link": settings_dict.get("paypal_link", PAYPAL_PAYMENT_LINK),
        "paypal_email": settings_dict.get("paypal_email", "JJSpilot24@gmail.com")
    }

@api_router.post("/subscriptions/activate")
async def activate_subscription(user = Depends(get_current_user)):
    """Activate subscription after payment"""
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_paid": True, "payment_date": datetime.utcnow()}}
    )
    return {"message": "Subscription activated successfully", "is_paid": True}

# ============== CATEGORY ENDPOINTS ==============

@api_router.post("/categories", response_model=dict)
async def create_category(category: CategoryCreate, user = Depends(get_current_user)):
    # Validate content
    if contains_blocked_content(category.name):
        raise HTTPException(status_code=400, detail="Category name contains blocked content")
    if contains_blocked_content(category.protocol):
        raise HTTPException(status_code=400, detail="Protocol contains blocked content")
    
    # Validate protocol format
    parsed = ProtocolParser.parse_protocol(category.protocol)
    if not parsed["valid"]:
        raise HTTPException(status_code=400, detail="Invalid protocol format. Use: (word1 or word2) & (word3)+")
    
    # Calculate level
    level = 0
    if category.parent_id:
        parent = await db.categories.find_one({"_id": ObjectId(category.parent_id)})
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
        level = parent.get("level", 0) + 1
        
        settings = await db.settings.find_one({"key": "max_category_levels"})
        max_levels = settings.get("value", 100) if settings else 100
        if level >= max_levels:
            raise HTTPException(status_code=400, detail=f"Maximum category depth ({max_levels}) reached")
    
    category_doc = {
        "name": category.name,
        "protocol": category.protocol,
        "user_id": str(user["_id"]),
        "parent_id": category.parent_id,
        "is_public": category.is_public,
        "level": level,
        "created_at": datetime.utcnow()
    }
    
    result = await db.categories.insert_one(category_doc)
    
    return {
        "id": str(result.inserted_id),
        "name": category.name,
        "protocol": category.protocol,
        "user_id": str(user["_id"]),
        "parent_id": category.parent_id,
        "is_public": category.is_public,
        "level": level,
        "created_at": category_doc["created_at"].isoformat()
    }

@api_router.get("/categories", response_model=List[dict])
async def get_categories(user = Depends(get_current_user)):
    categories = await db.categories.find({"user_id": str(user["_id"])}).to_list(1000)
    
    result = []
    for cat in categories:
        result.append({
            "id": str(cat["_id"]),
            "name": cat["name"],
            "protocol": cat["protocol"],
            "user_id": cat["user_id"],
            "parent_id": cat.get("parent_id"),
            "is_public": cat.get("is_public", False),
            "level": cat.get("level", 0),
            "created_at": cat["created_at"].isoformat() if cat.get("created_at") else None
        })
    
    return result

@api_router.put("/categories/{category_id}", response_model=dict)
async def update_category(category_id: str, update: CategoryUpdate, user = Depends(get_current_user)):
    category = await db.categories.find_one({"_id": ObjectId(category_id), "user_id": str(user["_id"])})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {}
    if update.name is not None:
        if contains_blocked_content(update.name):
            raise HTTPException(status_code=400, detail="Category name contains blocked content")
        update_data["name"] = update.name
    if update.protocol is not None:
        if contains_blocked_content(update.protocol):
            raise HTTPException(status_code=400, detail="Protocol contains blocked content")
        parsed = ProtocolParser.parse_protocol(update.protocol)
        if not parsed["valid"]:
            raise HTTPException(status_code=400, detail="Invalid protocol format")
        update_data["protocol"] = update.protocol
    if update.is_public is not None:
        update_data["is_public"] = update.is_public
    
    if update_data:
        await db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": update_data})
    
    updated = await db.categories.find_one({"_id": ObjectId(category_id)})
    return {
        "id": str(updated["_id"]),
        "name": updated["name"],
        "protocol": updated["protocol"],
        "is_public": updated.get("is_public", False),
        "level": updated.get("level", 0)
    }

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user = Depends(get_current_user)):
    category = await db.categories.find_one({"_id": ObjectId(category_id), "user_id": str(user["_id"])})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    async def delete_children(parent_id: str):
        children = await db.categories.find({"parent_id": parent_id}).to_list(1000)
        for child in children:
            await delete_children(str(child["_id"]))
            await db.categories.delete_one({"_id": child["_id"]})
    
    await delete_children(category_id)
    await db.categories.delete_one({"_id": ObjectId(category_id)})
    
    await db.search_results.update_many(
        {"category_ids": category_id},
        {"$pull": {"category_ids": category_id}}
    )
    
    return {"message": "Category deleted"}

# ============== SEARCH & COLLATE ENDPOINTS ==============

@api_router.post("/search", response_model=dict)
async def perform_search(request: SearchRequest, user = Depends(get_current_user)):
    """Perform a web search - returns maximum results for better collation"""
    
    if contains_blocked_content(request.query):
        raise HTTPException(status_code=400, detail="Search query contains blocked content")
    
    # Get max search pages from admin settings
    settings = await db.settings.find_one({"key": "max_search_pages"})
    max_pages = settings.get("value", 99) if settings else 99
    
    # Calculate results based on max pages (assuming ~20 results per page)
    max_results = max_pages * 20
    
    # Use web search service - get results based on admin setting
    results = await WebSearchService.search(request.query, min(max_results, 200))
    
    return {
        "query": request.query,
        "results": results,
        "total": len(results)
    }

@api_router.post("/collate", response_model=dict)
async def collate_results(request: CollateRequest, user = Depends(get_current_user)):
    """
    Automatically categorize search results based on user's protocols
    ENHANCED: More lenient matching for better results flow
    """
    
    # Check daily limit
    today = datetime.utcnow().date()
    user_doc = await db.users.find_one({"_id": user["_id"]})
    last_date = user_doc.get("last_collate_date")
    
    if last_date and last_date.date() == today:
        daily_count = user_doc.get("daily_collate_count", 0)
        settings = await db.settings.find_one({"key": "daily_collate_limit"})
        limit = settings.get("value", 100) if settings else 100  # Increased default limit
        if daily_count >= limit:
            raise HTTPException(status_code=429, detail=f"Daily collate limit ({limit}) reached")
        await db.users.update_one({"_id": user["_id"]}, {"$inc": {"daily_collate_count": 1}})
    else:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"daily_collate_count": 1, "last_collate_date": datetime.utcnow()}}
        )
    
    categories = await db.categories.find({"user_id": str(user["_id"])}).to_list(1000)
    
    collated_results = []
    batch_id = str(uuid.uuid4())
    
    # If user has no categories, create a default one to catch all results
    if not categories:
        logger.info(f"User {user['_id']} has no categories - results will not be categorized")
    
    for result in request.search_results:
        if contains_blocked_content(result.get("title", "")) or contains_blocked_content(result.get("content", "")):
            continue
        
        matching_category_ids = []
        # Combine ALL available text for matching
        text_to_match = " ".join([
            result.get('title', ''),
            result.get('snippet', ''),
            result.get('content', ''),
            result.get('description', ''),
            result.get('url', '')  # Also match against URL
        ]).strip()
        
        # Try to match against each category's protocol
        for cat in categories:
            protocol = cat.get("protocol", "")
            if not protocol:
                continue
            
            try:
                if ProtocolParser.matches_protocol(text_to_match, protocol):
                    matching_category_ids.append(str(cat["_id"]))
                    logger.debug(f"Matched '{result.get('title', '')[:50]}' to category '{cat['name']}'")
            except Exception as e:
                logger.error(f"Protocol matching error for category {cat.get('name')}: {e}")
        
        # ALWAYS save results that match at least one category
        if matching_category_ids:
            article_type = ArticleClassifier.classify(result.get("title", ""), result.get("content", ""))
            
            url = result.get("url", "")
            root_domain = result.get("root_domain", "")
            if not root_domain and url:
                try:
                    parsed = urllib.parse.urlparse(url)
                    root_domain = parsed.netloc
                except:
                    pass
            
            search_result_doc = {
                "url": result.get("url"),
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "content": result.get("content", "")[:5000],  # Limit stored content
                "user_id": str(user["_id"]),
                "category_ids": matching_category_ids,
                "article_type": article_type,
                "root_domain": root_domain,
                "reactions": {},
                "collated_at": datetime.utcnow(),
                "batch_id": batch_id,
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude")
            }
            
            existing = await db.search_results.find_one({
                "url": result.get("url"),
                "user_id": str(user["_id"])
            })
            
            if existing:
                new_cats = list(set(existing.get("category_ids", []) + matching_category_ids))
                await db.search_results.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"category_ids": new_cats}}
                )
                search_result_doc["id"] = str(existing["_id"])
            else:
                insert_result = await db.search_results.insert_one(search_result_doc)
                search_result_doc["id"] = str(insert_result.inserted_id)
            
            # Remove any non-serializable fields for response
            if "_id" in search_result_doc:
                del search_result_doc["_id"]
            
            # Convert datetime to ISO string
            if isinstance(search_result_doc.get("collated_at"), datetime):
                search_result_doc["collated_at"] = search_result_doc["collated_at"].isoformat()
            
            search_result_doc["matching_categories"] = [
                cat["name"] for cat in categories if str(cat["_id"]) in matching_category_ids
            ]
            collated_results.append(search_result_doc)
    
    logger.info(f"Collated {len(collated_results)} of {len(request.search_results)} results for user {user['_id']}")
    
    return {
        "collated_count": len(collated_results),
        "total_searched": len(request.search_results),
        "results": collated_results
    }

# ============== ULTIMATE SEARCH PAGE ENDPOINTS ==============

@api_router.get("/ultimate-search", response_model=dict)
async def get_ultimate_search(
    category_ids: Optional[str] = Query(None),
    aggregation: str = Query("and_or"),
    article_type: Optional[str] = None,
    root_domain: Optional[str] = None,
    year: Optional[int] = None,
    search_query: Optional[str] = None,
    page: int = Query(1, ge=1),
    user = Depends(get_current_user)
):
    """Get search results for Ultimate Search Page"""
    
    settings = await db.settings.find_one({"key": "results_per_page"})
    per_page = settings.get("value", 20) if settings else 20
    
    if not user.get("is_paid", False) and not user.get("is_admin", False):
        settings = await db.settings.find_one({"key": "unpaid_max_pages"})
        max_pages = settings.get("value", 1) if settings else 1
        if page > max_pages:
            raise HTTPException(status_code=403, detail=f"Unpaid users limited to {max_pages} page(s). Please subscribe.")
    
    query = {"user_id": str(user["_id"])}
    
    if category_ids:
        cat_list = [c.strip() for c in category_ids.split(",") if c.strip()]
        if cat_list:
            if aggregation == "and":
                query["category_ids"] = {"$all": cat_list, "$size": len(cat_list)}
            elif aggregation == "or":
                query["category_ids"] = {"$in": cat_list}
            else:
                query["category_ids"] = {"$all": cat_list}
    
    if article_type:
        query["article_type"] = article_type
    
    if root_domain:
        query["root_domain"] = root_domain
    
    if year:
        query["detected_year"] = year
    
    if search_query:
        query["$or"] = [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"snippet": {"$regex": search_query, "$options": "i"}}
        ]
    
    total = await db.search_results.count_documents(query)
    
    skip = (page - 1) * per_page
    results = await db.search_results.find(query).skip(skip).limit(per_page).to_list(per_page)
    
    all_cat_ids = set()
    for r in results:
        all_cat_ids.update(r.get("category_ids", []))
    
    categories_map = {}
    if all_cat_ids:
        cats = await db.categories.find({"_id": {"$in": [ObjectId(cid) for cid in all_cat_ids]}}).to_list(1000)
        categories_map = {str(c["_id"]): c["name"] for c in cats}
    
    formatted_results = []
    for r in results:
        formatted_results.append({
            "id": str(r["_id"]),
            "url": r["url"],
            "title": r["title"],
            "snippet": r.get("snippet"),
            "article_type": r.get("article_type"),
            "root_domain": r.get("root_domain"),
            "categories": [categories_map.get(cid, "Unknown") for cid in r.get("category_ids", [])],
            "reactions": r.get("reactions", {}),
            "collated_at": r.get("collated_at").isoformat() if r.get("collated_at") else None,
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude")
        })
    
    return {
        "results": formatted_results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@api_router.get("/ultimate-search/stats", response_model=dict)
async def get_ultimate_search_stats(user = Depends(get_current_user)):
    """Get statistics for Ultimate Search Page"""
    
    pipeline = [
        {"$match": {"user_id": str(user["_id"])}},
        {"$group": {
            "_id": None,
            "total_results": {"$sum": 1},
            "article_types": {"$push": "$article_type"},
            "root_domains": {"$push": "$root_domain"}
        }}
    ]
    
    stats = await db.search_results.aggregate(pipeline).to_list(1)
    
    if not stats:
        return {
            "total_results": 0,
            "article_type_breakdown": {},
            "top_domains": []
        }
    
    stat = stats[0]
    
    from collections import Counter
    article_types = Counter(stat.get("article_types", []))
    domains = Counter([d for d in stat.get("root_domains", []) if d])
    
    return {
        "total_results": stat.get("total_results", 0),
        "article_type_breakdown": dict(article_types),
        "top_domains": domains.most_common(10)
    }

# ============== MAP DATA ENDPOINT ==============

@api_router.get("/map-data", response_model=dict)
async def get_map_data(user = Depends(get_current_user)):
    """Get search results with location data for map display"""
    
    if not user.get("is_paid", False) and not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Map feature is only available for premium users")
    
    results = await db.search_results.find({
        "user_id": str(user["_id"]),
        "latitude": {"$exists": True, "$ne": None},
        "longitude": {"$exists": True, "$ne": None}
    }).to_list(500)
    
    # Get category info
    all_cat_ids = set()
    for r in results:
        all_cat_ids.update(r.get("category_ids", []))
    
    categories_map = {}
    if all_cat_ids:
        cats = await db.categories.find({"_id": {"$in": [ObjectId(cid) for cid in all_cat_ids]}}).to_list(1000)
        categories_map = {str(c["_id"]): c["name"] for c in cats}
    
    markers = []
    for r in results:
        markers.append({
            "id": str(r["_id"]),
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "title": r["title"],
            "url": r["url"],
            "categories": [categories_map.get(cid, "Unknown") for cid in r.get("category_ids", [])]
        })
    
    return {"markers": markers}

# ============== REACTIONS ENDPOINT ==============

@api_router.post("/reactions", response_model=dict)
async def add_reaction(reaction: ReactionCreate, user = Depends(get_current_user)):
    """Add a reaction to a search result"""
    
    valid_reactions = ["Like", "Love", "Funny", "Sad", "Caution", "Spam", "Best"]
    if reaction.reaction_type not in valid_reactions:
        raise HTTPException(status_code=400, detail=f"Invalid reaction. Must be one of: {valid_reactions}")
    
    result = await db.search_results.find_one({"_id": ObjectId(reaction.search_result_id)})
    if not result:
        raise HTTPException(status_code=404, detail="Search result not found")
    
    user_id = str(user["_id"])
    reaction_key = f"reactions.{reaction.reaction_type}"
    
    current_reactions = result.get("reactions", {}).get(reaction.reaction_type, [])
    
    if user_id in current_reactions:
        await db.search_results.update_one(
            {"_id": ObjectId(reaction.search_result_id)},
            {"$pull": {reaction_key: user_id}}
        )
        return {"message": "Reaction removed", "action": "removed"}
    else:
        await db.search_results.update_one(
            {"_id": ObjectId(reaction.search_result_id)},
            {"$addToSet": {reaction_key: user_id}}
        )
        return {"message": "Reaction added", "action": "added"}

# ============== SOCIAL FEATURES ==============

@api_router.post("/friends/request")
async def send_friend_request(request: FriendRequest, user = Depends(get_current_user)):
    """Send a friend request"""
    target_id = request.target_user_id
    user_id = str(user["_id"])
    
    if target_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    
    target_user = await db.users.find_one({"_id": ObjectId(target_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already friends
    if target_id in user.get("friends", []):
        raise HTTPException(status_code=400, detail="Already friends")
    
    # Check if request already sent
    if target_id in user.get("friend_requests_sent", []):
        raise HTTPException(status_code=400, detail="Friend request already sent")
    
    # Send request
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$addToSet": {"friend_requests_sent": target_id}}
    )
    await db.users.update_one(
        {"_id": ObjectId(target_id)},
        {"$addToSet": {"friend_requests_received": user_id}}
    )
    
    return {"message": "Friend request sent"}

@api_router.post("/friends/accept")
async def accept_friend_request(request: FriendRequest, user = Depends(get_current_user)):
    """Accept a friend request"""
    requester_id = request.target_user_id
    user_id = str(user["_id"])
    
    if requester_id not in user.get("friend_requests_received", []):
        raise HTTPException(status_code=400, detail="No pending friend request from this user")
    
    # Add as friends
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$addToSet": {"friends": requester_id},
            "$pull": {"friend_requests_received": requester_id}
        }
    )
    await db.users.update_one(
        {"_id": ObjectId(requester_id)},
        {
            "$addToSet": {"friends": user_id},
            "$pull": {"friend_requests_sent": user_id}
        }
    )
    
    return {"message": "Friend request accepted"}

@api_router.post("/friends/reject")
async def reject_friend_request(request: FriendRequest, user = Depends(get_current_user)):
    """Reject a friend request"""
    requester_id = request.target_user_id
    user_id = str(user["_id"])
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$pull": {"friend_requests_received": requester_id}}
    )
    await db.users.update_one(
        {"_id": ObjectId(requester_id)},
        {"$pull": {"friend_requests_sent": user_id}}
    )
    
    return {"message": "Friend request rejected"}

@api_router.delete("/friends/{friend_id}")
async def remove_friend(friend_id: str, user = Depends(get_current_user)):
    """Remove a friend"""
    user_id = str(user["_id"])
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$pull": {"friends": friend_id}}
    )
    await db.users.update_one(
        {"_id": ObjectId(friend_id)},
        {"$pull": {"friends": user_id}}
    )
    
    return {"message": "Friend removed"}

@api_router.get("/friends", response_model=dict)
async def get_friends(user = Depends(get_current_user)):
    """Get user's friends list"""
    friend_ids = user.get("friends", [])
    
    friends = []
    if friend_ids:
        friend_docs = await db.users.find(
            {"_id": {"$in": [ObjectId(fid) for fid in friend_ids]}}
        ).to_list(1000)
        
        for f in friend_docs:
            friends.append({
                "id": str(f["_id"]),
                "username": f["username"],
                "profile_picture": f.get("profile_picture"),
                "ultimate_search_public": f.get("ultimate_search_public", False)
            })
    
    # Get pending requests
    pending_received = []
    for rid in user.get("friend_requests_received", []):
        requester = await db.users.find_one({"_id": ObjectId(rid)})
        if requester:
            pending_received.append({
                "id": str(requester["_id"]),
                "username": requester["username"],
                "profile_picture": requester.get("profile_picture")
            })
    
    return {
        "friends": friends,
        "pending_requests": pending_received,
        "requests_sent_count": len(user.get("friend_requests_sent", []))
    }

# ============== MESSAGING ==============

@api_router.post("/messages")
async def send_message(message: MessageCreate, user = Depends(get_current_user)):
    """Send a message to another user"""
    recipient_id = message.recipient_id
    user_id = str(user["_id"])
    
    # Check if they are friends
    if recipient_id not in user.get("friends", []):
        raise HTTPException(status_code=403, detail="Can only message friends")
    
    if contains_blocked_content(message.content):
        raise HTTPException(status_code=400, detail="Message contains blocked content")
    
    message_doc = {
        "sender_id": user_id,
        "recipient_id": recipient_id,
        "content": message.content,
        "created_at": datetime.utcnow(),
        "read": False
    }
    
    result = await db.messages.insert_one(message_doc)
    
    return {
        "id": str(result.inserted_id),
        "message": "Message sent"
    }

@api_router.get("/messages/{friend_id}", response_model=dict)
async def get_messages(friend_id: str, user = Depends(get_current_user)):
    """Get messages with a friend"""
    user_id = str(user["_id"])
    
    messages = await db.messages.find({
        "$or": [
            {"sender_id": user_id, "recipient_id": friend_id},
            {"sender_id": friend_id, "recipient_id": user_id}
        ]
    }).sort("created_at", 1).to_list(100)
    
    # Mark messages as read
    await db.messages.update_many(
        {"sender_id": friend_id, "recipient_id": user_id, "read": False},
        {"$set": {"read": True}}
    )
    
    formatted = []
    for m in messages:
        formatted.append({
            "id": str(m["_id"]),
            "sender_id": m["sender_id"],
            "recipient_id": m["recipient_id"],
            "content": m["content"],
            "created_at": m["created_at"].isoformat(),
            "is_mine": m["sender_id"] == user_id
        })
    
    return {"messages": formatted}

@api_router.get("/messages/unread/count", response_model=dict)
async def get_unread_count(user = Depends(get_current_user)):
    """Get unread message count"""
    count = await db.messages.count_documents({
        "recipient_id": str(user["_id"]),
        "read": False
    })
    return {"unread_count": count}

# ============== PUBLIC PROFILES ==============

@api_router.get("/users/{user_id}/profile", response_model=dict)
async def get_user_profile(user_id: str, current_user = Depends(get_optional_user)):
    """Get a user's public profile"""
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_friend = current_user and user_id in current_user.get("friends", [])
    is_own = current_user and str(current_user["_id"]) == user_id
    
    profile = {
        "id": str(target_user["_id"]),
        "username": target_user["username"],
        "profile_picture": target_user.get("profile_picture"),
        "ultimate_search_public": target_user.get("ultimate_search_public", False),
        "is_friend": is_friend,
        "is_own": is_own
    }
    
    # Show friends if visible
    if target_user.get("friends_visible", False) or is_friend or is_own:
        profile["friends_count"] = len(target_user.get("friends", []))
    
    return profile

@api_router.get("/users/{user_id}/ultimate-search", response_model=dict)
async def get_user_ultimate_search(user_id: str, page: int = 1, current_user = Depends(get_optional_user)):
    """View another user's Ultimate Search Page (if public)"""
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_friend = current_user and user_id in current_user.get("friends", [])
    is_own = current_user and str(current_user["_id"]) == user_id
    
    if not target_user.get("ultimate_search_public", False) and not is_friend and not is_own:
        raise HTTPException(status_code=403, detail="This user's Ultimate Search Page is private")
    
    # Get public categories
    categories = await db.categories.find({
        "user_id": user_id,
        "is_public": True
    }).to_list(100)
    
    # Get search results
    per_page = 20
    skip = (page - 1) * per_page
    
    results = await db.search_results.find({
        "user_id": user_id
    }).skip(skip).limit(per_page).to_list(per_page)
    
    total = await db.search_results.count_documents({"user_id": user_id})
    
    return {
        "user": {
            "id": user_id,
            "username": target_user["username"],
            "profile_picture": target_user.get("profile_picture")
        },
        "categories": [{"id": str(c["_id"]), "name": c["name"]} for c in categories],
        "results": [{
            "id": str(r["_id"]),
            "url": r["url"],
            "title": r["title"],
            "snippet": r.get("snippet"),
            "article_type": r.get("article_type"),
            "reactions": r.get("reactions", {})
        } for r in results],
        "total": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page
    }

# ============== USER SETTINGS ==============

@api_router.put("/users/settings", response_model=dict)
async def update_user_settings(
    ultimate_search_public: Optional[bool] = None,
    friends_visible: Optional[bool] = None,
    profile_picture: Optional[str] = None,
    user = Depends(get_current_user)
):
    update_data = {}
    if ultimate_search_public is not None:
        update_data["ultimate_search_public"] = ultimate_search_public
    if friends_visible is not None:
        update_data["friends_visible"] = friends_visible
    if profile_picture is not None:
        update_data["profile_picture"] = profile_picture
    
    if update_data:
        await db.users.update_one({"_id": user["_id"]}, {"$set": update_data})
    
    return {"message": "Settings updated"}


class PasswordChangeRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str


@api_router.post("/users/change-password", response_model=dict)
async def change_password(request: PasswordChangeRequest, user = Depends(get_current_user)):
    """Change user password - works for both Google and email users"""
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # If user has existing password, verify current password
    if user.get("password_hash"):
        if not request.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if hash_password(request.current_password) != user["password_hash"]:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    new_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    return {"message": "Password changed successfully"}


@api_router.get("/users/has-password", response_model=dict)
async def check_has_password(user = Depends(get_current_user)):
    """Check if user has a password set (for Google users who want to add one)"""
    return {"has_password": bool(user.get("password_hash"))}


# ============== GROUPS ENDPOINTS ==============

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True

@api_router.get("/groups")
async def get_groups(user = Depends(get_current_user)):
    """Get all groups the user is a member of or public groups"""
    user_id = str(user["_id"])
    
    # Get groups user is member of OR public groups
    groups = await db.groups.find({
        "$or": [
            {"members": user_id},
            {"creator_id": user_id},
            {"is_public": True}
        ]
    }).to_list(100)
    
    return [{
        "id": str(g["_id"]),
        "name": g["name"],
        "description": g.get("description"),
        "is_public": g.get("is_public", True),
        "creator_id": g.get("creator_id"),
        "member_count": len(g.get("members", [])) + 1,
        "created_at": g.get("created_at").isoformat() if g.get("created_at") else None
    } for g in groups]

@api_router.post("/groups")
async def create_group(group: GroupCreate, user = Depends(get_current_user)):
    """Create a new group"""
    if contains_blocked_content(group.name) or (group.description and contains_blocked_content(group.description)):
        raise HTTPException(status_code=400, detail="Group contains blocked content")
    
    group_doc = {
        "name": group.name,
        "description": group.description,
        "is_public": group.is_public,
        "creator_id": str(user["_id"]),
        "members": [],
        "posts": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.groups.insert_one(group_doc)
    
    return {
        "id": str(result.inserted_id),
        "name": group.name,
        "description": group.description,
        "is_public": group.is_public,
        "member_count": 1,
        "created_at": group_doc["created_at"].isoformat()
    }

@api_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user = Depends(get_current_user)):
    """Join a group"""
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.get("is_public"):
        raise HTTPException(status_code=403, detail="This is a private group")
    
    user_id = str(user["_id"])
    if user_id not in group.get("members", []):
        await db.groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$addToSet": {"members": user_id}}
        )
    
    return {"message": "Joined group successfully"}

@api_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user = Depends(get_current_user)):
    """Leave a group"""
    await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$pull": {"members": str(user["_id"])}}
    )
    return {"message": "Left group successfully"}


@api_router.get("/groups/{group_id}")
async def get_group_details(group_id: str, user = Depends(get_current_user)):
    """Get detailed group info including posts"""
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user_id = str(user["_id"])
    is_member = user_id in group.get("members", []) or group.get("creator_id") == user_id
    
    # Get group posts
    posts = await db.group_posts.find({"group_id": group_id}).sort("created_at", -1).limit(50).to_list(50)
    
    # Enrich posts with user info
    enriched_posts = []
    for post in posts:
        author = await db.users.find_one({"_id": ObjectId(post["user_id"])})
        enriched_posts.append({
            "id": str(post["_id"]),
            "content": post["content"],
            "author_id": post["user_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "likes": post.get("likes", []),
            "comments": post.get("comments", []),
            "created_at": post["created_at"].isoformat()
        })
    
    return {
        "id": str(group["_id"]),
        "name": group["name"],
        "description": group.get("description"),
        "is_public": group.get("is_public", True),
        "creator_id": group.get("creator_id"),
        "member_count": len(group.get("members", [])) + 1,
        "is_member": is_member,
        "is_creator": group.get("creator_id") == user_id,
        "posts": enriched_posts,
        "created_at": group.get("created_at").isoformat() if group.get("created_at") else None
    }


class GroupPostCreate(BaseModel):
    content: str


@api_router.post("/groups/{group_id}/posts")
async def create_group_post(group_id: str, post: GroupPostCreate, user = Depends(get_current_user)):
    """Create a post in a group"""
    group = await db.groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user_id = str(user["_id"])
    is_member = user_id in group.get("members", []) or group.get("creator_id") == user_id
    
    if not is_member and not group.get("is_public"):
        raise HTTPException(status_code=403, detail="You must be a member to post")
    
    post_doc = {
        "group_id": group_id,
        "user_id": user_id,
        "content": post.content,
        "likes": [],
        "comments": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.group_posts.insert_one(post_doc)
    
    # Award XP for posting
    await db.users.update_one({"_id": user["_id"]}, {"$inc": {"xp": 5}})
    
    return {
        "id": str(result.inserted_id),
        "content": post.content,
        "author_name": user.get("username"),
        "created_at": post_doc["created_at"].isoformat()
    }


@api_router.post("/groups/{group_id}/posts/{post_id}/like")
async def like_group_post(group_id: str, post_id: str, user = Depends(get_current_user)):
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
async def comment_group_post(group_id: str, post_id: str, content: str = Body(..., embed=True), user = Depends(get_current_user)):
    """Comment on a group post"""
    post = await db.group_posts.find_one({"_id": ObjectId(post_id), "group_id": group_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = {
        "id": str(uuid.uuid4()),
        "user_id": str(user["_id"]),
        "username": user.get("username"),
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.group_posts.update_one({"_id": ObjectId(post_id)}, {"$push": {"comments": comment}})
    
    return {"message": "Comment added", "comment": comment}


# ============== SOCIAL FEED ==============

@api_router.get("/feed")
async def get_social_feed(user = Depends(get_current_user)):
    """Get personalized social feed with posts from friends and groups"""
    user_id = str(user["_id"])
    
    # Get user's groups
    groups = await db.groups.find({
        "$or": [
            {"members": user_id},
            {"creator_id": user_id}
        ]
    }).to_list(100)
    group_ids = [str(g["_id"]) for g in groups]
    
    # Get posts from groups
    feed_posts = []
    
    # Group posts
    group_posts = await db.group_posts.find({
        "group_id": {"$in": group_ids}
    }).sort("created_at", -1).limit(30).to_list(30)
    
    for post in group_posts:
        author = await db.users.find_one({"_id": ObjectId(post["user_id"])})
        group = next((g for g in groups if str(g["_id"]) == post["group_id"]), None)
        
        feed_posts.append({
            "id": str(post["_id"]),
            "type": "group_post",
            "content": post["content"],
            "author_id": post["user_id"],
            "author_name": author.get("username", "Unknown") if author else "Unknown",
            "group_id": post["group_id"],
            "group_name": group["name"] if group else "Unknown Group",
            "likes": len(post.get("likes", [])),
            "is_liked": user_id in post.get("likes", []),
            "comment_count": len(post.get("comments", [])),
            "created_at": post["created_at"].isoformat()
        })
    
    # Sort by date
    feed_posts.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"posts": feed_posts[:30]}


class FeedPostCreate(BaseModel):
    content: str


@api_router.post("/feed/post")
async def create_feed_post(post: FeedPostCreate, user = Depends(get_current_user)):
    """Create a general feed post (visible to friends)"""
    post_doc = {
        "user_id": str(user["_id"]),
        "content": post.content,
        "likes": [],
        "comments": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.feed_posts.insert_one(post_doc)
    
    # Award XP
    await db.users.update_one({"_id": user["_id"]}, {"$inc": {"xp": 5}})
    
    return {
        "id": str(result.inserted_id),
        "content": post.content,
        "author_name": user.get("username"),
        "created_at": post_doc["created_at"].isoformat()
    }


# ============== PAGES ENDPOINTS ==============

class PageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "General"

@api_router.get("/pages")
async def get_pages(user = Depends(get_current_user)):
    """Get all pages"""
    pages = await db.pages.find().sort("created_at", -1).to_list(100)
    
    return [{
        "id": str(p["_id"]),
        "name": p["name"],
        "description": p.get("description"),
        "category": p.get("category", "General"),
        "creator_id": p.get("creator_id"),
        "likes": len(p.get("likes", [])),
        "created_at": p.get("created_at").isoformat() if p.get("created_at") else None
    } for p in pages]

@api_router.post("/pages")
async def create_page(page: PageCreate, user = Depends(get_current_user)):
    """Create a new page"""
    if contains_blocked_content(page.name) or (page.description and contains_blocked_content(page.description)):
        raise HTTPException(status_code=400, detail="Page contains blocked content")
    
    page_doc = {
        "name": page.name,
        "description": page.description,
        "category": page.category,
        "creator_id": str(user["_id"]),
        "likes": [],
        "followers": [],
        "posts": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.pages.insert_one(page_doc)
    
    return {
        "id": str(result.inserted_id),
        "name": page.name,
        "description": page.description,
        "category": page.category,
        "likes": 0,
        "created_at": page_doc["created_at"].isoformat()
    }

@api_router.post("/pages/{page_id}/like")
async def like_page(page_id: str, user = Depends(get_current_user)):
    """Like/unlike a page"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    user_id = str(user["_id"])
    if user_id in page.get("likes", []):
        # Unlike
        await db.pages.update_one(
            {"_id": ObjectId(page_id)},
            {"$pull": {"likes": user_id}}
        )
        return {"liked": False, "likes": len(page.get("likes", [])) - 1}
    else:
        # Like
        await db.pages.update_one(
            {"_id": ObjectId(page_id)},
            {"$addToSet": {"likes": user_id}}
        )
        return {"liked": True, "likes": len(page.get("likes", [])) + 1}

@api_router.post("/pages/{page_id}/follow")
async def follow_page(page_id: str, user = Depends(get_current_user)):
    """Follow/unfollow a page"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    user_id = str(user["_id"])
    if user_id in page.get("followers", []):
        await db.pages.update_one(
            {"_id": ObjectId(page_id)},
            {"$pull": {"followers": user_id}}
        )
        return {"following": False}
    else:
        await db.pages.update_one(
            {"_id": ObjectId(page_id)},
            {"$addToSet": {"followers": user_id}}
        )
        return {"following": True}


@api_router.get("/pages/{page_id}")
async def get_page_details(page_id: str, user = Depends(get_current_user)):
    """Get detailed page info including posts"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    user_id = str(user["_id"])
    
    # Get page posts
    posts = await db.page_posts.find({"page_id": page_id}).sort("created_at", -1).limit(50).to_list(50)
    
    enriched_posts = []
    for post in posts:
        enriched_posts.append({
            "id": str(post["_id"]),
            "content": post["content"],
            "likes": len(post.get("likes", [])),
            "is_liked": user_id in post.get("likes", []),
            "comments": post.get("comments", []),
            "created_at": post["created_at"].isoformat()
        })
    
    return {
        "id": str(page["_id"]),
        "name": page["name"],
        "description": page.get("description"),
        "category": page.get("category", "General"),
        "creator_id": page.get("creator_id"),
        "likes": len(page.get("likes", [])),
        "is_liked": user_id in page.get("likes", []),
        "followers": len(page.get("followers", [])),
        "is_following": user_id in page.get("followers", []),
        "is_creator": page.get("creator_id") == user_id,
        "posts": enriched_posts,
        "created_at": page.get("created_at").isoformat() if page.get("created_at") else None
    }


class PagePostCreate(BaseModel):
    content: str


@api_router.post("/pages/{page_id}/posts")
async def create_page_post(page_id: str, post: PagePostCreate, user = Depends(get_current_user)):
    """Create a post on a page (only page creator)"""
    page = await db.pages.find_one({"_id": ObjectId(page_id)})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page.get("creator_id") != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Only page owner can post")
    
    post_doc = {
        "page_id": page_id,
        "content": post.content,
        "likes": [],
        "comments": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.page_posts.insert_one(post_doc)
    
    return {
        "id": str(result.inserted_id),
        "content": post.content,
        "created_at": post_doc["created_at"].isoformat()
    }


@api_router.post("/pages/{page_id}/posts/{post_id}/like")
async def like_page_post(page_id: str, post_id: str, user = Depends(get_current_user)):
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


# ============== ADMIN ENDPOINTS ==============

@api_router.get("/admin/settings", response_model=List[dict])
async def get_admin_settings(user = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await db.settings.find().to_list(100)
    return [{"key": s["key"], "value": s["value"], "description": s.get("description")} for s in settings]

@api_router.put("/admin/settings/{key}", response_model=dict)
async def update_admin_setting(key: str, value: Any = Body(...), user = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.settings.update_one(
        {"key": key},
        {"$set": {"value": value}},
        upsert=True
    )
    return {"message": "Setting updated"}

@api_router.post("/admin/ban-user/{user_id}")
async def ban_user(user_id: str, user = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_banned": True}}
    )
    return {"message": "User banned"}

@api_router.post("/admin/ban-word")
async def ban_word(word: str = Body(...), user = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    BLOCKED_WORDS.add(word.lower())
    await db.banned_words.update_one(
        {"word": word.lower()},
        {"$set": {"word": word.lower()}},
        upsert=True
    )
    return {"message": "Word banned"}

@api_router.post("/admin/init", response_model=dict)
async def init_admin_settings():
    """Initialize default admin settings"""
    
    default_settings = [
        {"key": "subscription_price", "value": 0.99, "description": "Subscription price in USD"},
        {"key": "results_per_page", "value": 20, "description": "Search results per page"},
        {"key": "max_search_pages", "value": 99, "description": "Max search pages (1-99) for admin/paid users"},
        {"key": "unpaid_max_pages", "value": 1, "description": "Max pages for unpaid users"},
        {"key": "daily_collate_limit", "value": 100, "description": "Max collations per day"},
        {"key": "max_category_levels", "value": 100, "description": "Max category hierarchy depth"},
        {"key": "phd_min_words", "value": 1500, "description": "Min words for Ph.D. classification"},
        {"key": "phd_keyword_count", "value": 3, "description": "Min Ph.D. keywords required"},
        {"key": "tutorial_video_url", "value": "", "description": "YouTube tutorial video URL"},
        {"key": "paypal_link", "value": PAYPAL_PAYMENT_LINK, "description": "PayPal payment link"},
    ]
    
    for setting in default_settings:
        await db.settings.update_one(
            {"key": setting["key"]},
            {"$setOnInsert": setting},
            upsert=True
        )
    
    return {"message": "Settings initialized", "count": len(default_settings)}

# ============== NEWSLETTER SYSTEM ==============

# Book and App Marketing Content - ENHANCED with full promotional data
BOOK_INFO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "genre": "A True Supernatural Thriller Comedy",
    "price": "$2.99",
    "amazon_url": "https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191",
    "reviews_url": "https://readersfavorite.com/book-review/letters-to-evelyn",
    "review_count": "57 Amazon Reviews, ALL 5 Stars!",
    "featured_review": '"This memoir is a profound and unforgettable literary piece." - Divine Zape, Readers\' Favorite',
    "description": "A supernatural thriller comedy that will keep you on the edge of your seat while making you laugh!"
}

# NEW: Enhanced promotional images with hilarious taglines from advertisements
BOOK_PROMO_IMAGES = [
    {
        "url": "https://customer-assets.emergentagent.com/job_40ecefb6-ad41-4cc2-b262-9d6290d06ac2/artifacts/hou1ho41_Letters%20to%20Evelyn%20advertisement%201.jpg",
        "tagline": "WROTE A BOOK - UNIVERSE FACT-CHECKED IT - IT PASSED!",
        "theme": "cosmic_approval",
        "subtitle": "The universe literally gave it a passing grade. Beat that, Shakespeare!"
    },
    {
        "url": "https://customer-assets.emergentagent.com/job_40ecefb6-ad41-4cc2-b262-9d6290d06ac2/artifacts/0jz7ijpw_Letters%20to%20Evelyn%20advertisement%202.jpg",
        "tagline": "THERAPIST: THIS IS A LOT TO UNPACK - BRING SNACKS",
        "theme": "therapy_humor",
        "subtitle": "Finally, a book complex enough to justify your therapy bills!"
    },
    {
        "url": "https://customer-assets.emergentagent.com/job_40ecefb6-ad41-4cc2-b262-9d6290d06ac2/artifacts/g0is1l74_Letters%20to%20Evelyn%20advertisement%203.jpg",
        "tagline": "I FLEW JETS THEN REALITY BROKE",
        "theme": "pilot_story",
        "subtitle": "When your life is so wild, physics decides to take a vacation!"
    },
    {
        "url": "https://customer-assets.emergentagent.com/job_40ecefb6-ad41-4cc2-b262-9d6290d06ac2/artifacts/kuqqskw9_Letters%20to%20Evelyn%20advertisement%204.jpg",
        "tagline": "TERROR OF THE COSMICGULPER - WE'RE ALL GONNA DIE!",
        "theme": "galactic_comedy",
        "subtitle": "A Comedy of Galactic Proportions - Prepare for a mouth-watering adventure!"
    }
]

# NEW: Rich review data from Readers' Favorite and Amazon
BOOK_REVIEWS = {
    "readers_favorite": {
        "summary": "A prolific odyssey of love and redemption that takes readers on a journey through illuminating and unsettling life experiences.",
        "themes": "Identity, spirituality, nature of reality, encounters with extraterrestrial beings, memories, dreams, and hallucinations woven in lyrical prose.",
        "reviews": [
            {"reviewer": "Divine Zape", "quote": "This memoir is a profound and unforgettable literary piece.", "stars": 5},
            {"reviewer": "Luwi Nyakansaila", "quote": "Mind-bending.", "stars": 5},
            {"reviewer": "Paul Zeitsman", "quote": "Exceedingly brilliant.", "stars": 5},
            {"reviewer": "Leslie Jones", "quote": "The author's imagination is off the charts.", "stars": 5},
            {"reviewer": "Doreen Chombu", "quote": "Mind-blowing.", "stars": 5},
            {"reviewer": "Ruffina Oserio", "quote": "A captivating memoir that defies genre conventions.", "stars": 5},
            {"reviewer": "Christian Sia", "quote": "A symphony of love and madness that transports readers to the furthest reaches of the human psyche.", "stars": 5},
            {"reviewer": "Courtnee Turner Hoyle", "quote": "Deeply spiritual with a melodic quality.", "stars": 5},
            {"reviewer": "David Jaggart", "quote": "A heartfelt book about grief, love, confronting trauma, and self-discovery.", "stars": 5}
        ]
    },
    "amazon": {
        "rating": "5.0 out of 5 stars",
        "total_reviews": 57,
        "reviews": [
            {"reviewer": "Peter gale Carty", "quote": "This book evoked a mixture of surprise and amusement... I felt lighter and reminded of the importance of not taking life too seriously."},
            {"reviewer": "Kindle Customer", "quote": "I laughed, I paused to think, and at times I had to reread sections just to take it all in."},
            {"reviewer": "Roshannae Dougal", "quote": "Prepare to have a laugh every chapter, as betrayal unfolds maybe love."},
            {"reviewer": "Nicole F", "quote": "A Haunting Masterpiece! Twists and turns keep you hooked!"},
            {"reviewer": "Justine", "quote": "A gripping supernatural thriller memoir that'll keep you on the edge."},
            {"reviewer": "Ella-O", "quote": "Very enjoyable and beautifully written in a way that keeps you captivated."}
        ]
    }
}

# NEW: Author biography highlights for funnier content
AUTHOR_HIGHLIGHTS = {
    "credentials": "Navy pilot, Top ROTC student, German language degree holder",
    "world_record": "Steepest, highest Sarajevo Approach with the lowest recovery in a T-34C - 83 degree nose down dive from 6000 feet to 5 feet above treetops!",
    "endurance_record": "Survived 12+ days without sleep after being poisoned",
    "achievements": "Flew 10 different aircraft types",
    "personality": "Self-proclaimed funnier than Dave Chappelle",
    "book_promise": "50+ finely-crafted deafening, zany, zesty, zoo zingers... JOKES!"
}

# COMPREHENSIVE MANUSCRIPT CONTENT - From "Letters to Evelyn" by John Selman
# Full analysis of the manuscript for newsletter generation
MANUSCRIPT_CONTENT = {
    "book_meta": {
        "title": "Letters to Evelyn",
        "author": "John Selman",
        "genre": "A True Supernatural Thriller Comedy",
        "dedication": "This book is dedicated to the reader. This is for you, whoever you are.",
        "copyright_warning": """This novel is only meant for readers who are not operating a vehicle or heavy equipment. 
If you are pregnant or breastfeeding, reading could evoke uncontrollable hysterics and fits of laughter; 
it is recommended for people in pregnancy to avoid reading as it may induce unexpected labor. 
This book is intended for adults only 26 years and older!""",
        "summary": "A deeply personal and often surreal narrative of love, naval service, traumatic childhood experiences, and profound mystical connections - blending memoir, spirituality, and encounters with extraterrestrial beings.",
    },
    
    "key_characters": {
        "John Selman": "The protagonist - Navy pilot, Top ROTC student, and a man whose life defies physics and logic",
        "Evelyn Tuskegee": "The central, almost spiritual figure - his destined soulmate who appeared in his imagination before they met",
        "Lauren Selman": "The abusive stepmother who poisoned John's food, triggering ten months of hallucinations",
        "The Captain": "The enigmatic USS Enterprise/Nimitz figure who kept calling John 'Jesus'",
        "Durham": "The bizarre rival scientist with purple eyes who claimed to solve the 'Grand Unifying Theory'",
        "Maria Anastasia": "A past love interest in whom John saw the entire universe",
        "The Gray Aliens": "Extraterrestrial visitors who communicated 'Drink water, good boy'",
    },
    
    "wild_plot_elements": [
        "Navy pilot's stepmother Lauren POISONED his eggs with LSD equivalent to 200-500 doses!",
        "He hallucinated aliens for TEN MONTHS straight!",
        "A Captain kept calling him 'Jesus' on USS Enterprise - he denied it every time with 'Fack off!' (Monty Python style)",
        "He saw the entire universe and God while looking at a woman named Maria!",
        "He imagined his future wife 'Evelyn' into existence while on a nuclear aircraft carrier!",
        "He twisted her right big toe CLOCKWISE in his imagination to 'save everyone from being left-handed'!",
        "He pulled an imaginary rib from his chest and offered it to the imaginary Eve!",
        "He claims to have created athletes Usain Bolt and Michael Phelps by 'waving his arms wildly'!",
        "He gave a captain a glass of water with 10 drops of his blood from his middle finger!",
        "He predicted the Twin Towers disaster and a tsunami the day after Christmas!",
        "He bent a penny barehanded in front of sailors and went crowd surfing on their applause!",
        "He saw an invisible extraterrestrial in Texas wearing a 'biomechanical suit'!",
        "Gray aliens told him to 'Drink waaaater, good boy' while he was driving in Arizona!",
        "He did an 83-degree nearly VERTICAL dive in a T-34C and survived with 430 PICOSECONDS to spare!",
        "He hid a spacecraft inside a 2,600-foot-wide extraterrestrial dinosaur's reproductive organs!",
        "He survived 12+ days without sleep after being poisoned - Northeast US record!",
        "He was demoted to 'Trash-O' - the ship's garbage collector - after the Jesus incidents",
        "He flew 10 different aircraft types and holds the world record for steepest Sarajevo Approach",
        "The aliens wore robes with crosses and told him 'Only life, no more hurt' before leaving",
        "Durham broadcast 'The sky! This guy!' to the entire universe as some kind of cosmic insult",
    ],
    
    "hilarious_quotes": [
        {"quote": "I said fly to the sun, not IN it!", "context": "Pilot instruction mishap"},
        {"quote": "These eggs are so good! Are they cage free?", "context": "Unknowingly eating poisoned eggs"},
        {"quote": "Fack off!", "context": "John's Monty Python response to being called Jesus"},
        {"quote": "I'm not even afraid of saving my pet gerbil.", "context": "Random hallucination moment"},
        {"quote": "La-la-la-la!", "context": "Captain plugging ears like Lloyd Christmas from Dumb & Dumber"},
        {"quote": "You're Jesus. - No I'm not! - You're Jesus. - STOP IT!", "context": "Repeated 9-12 times per encounter"},
        {"quote": "I bent a penny barehanded... everyone came to lift me up and I went crowd surfing!", "context": "Post-hallucination feat"},
        {"quote": "Drink waaaater, drink waaaaaater, good boy.", "context": "Gray Aliens' only message"},
        {"quote": "Only life, no more hurt.", "context": "Aliens' farewell message"},
        {"quote": "The sky! This guy!", "context": "Durham's universal broadcast to insult John"},
        {"quote": "We queefed our way out of the undulating gargantuan reproductive organs at maximum power!", "context": "The dinosaur escape scene"},
        {"quote": "I'm not the best extraterrestrial dinosaur vagina pilot! You're the woman! Take the controls!", "context": "Peak absurdity"},
        {"quote": "I'm not Jesus! Why do you keep saying that I'm Jesus?", "context": "John's frustration with the Captain"},
        {"quote": "We're either infinite Love or we're not. Can I say that one last time?", "context": "John's philosophical repetition"},
        {"quote": "I'm so sorry, Evelyn. I love you, and I venerate every man you've ever loved too.", "context": "Bizarrely earnest love declaration"},
    ],
    
    "chapter_teasers": [
        {"chapter": 2, "title": "The Encounter", "teaser": "The same father who knocked me out for wanting to fly through a cloud when I was THREE"},
        {"chapter": 4, "title": "Muster the Strength", "teaser": "I said I love pain at least TEN THOUSAND TIMES that weekend"},
        {"chapter": 5, "title": "The Sweltering Speech", "teaser": "The captain used the PERIODIC TABLE to mathematically prove I was Jesus. I still said no."},
        {"chapter": 7, "title": "Standing Ovation", "teaser": "A 600-sailor standing ovation... then they started calling me JESUS"},
        {"chapter": 9, "title": "Flight School", "teaser": "My on-wing instructor was like an Air Traffic Controller with a TV remote - confused and overly confident"},
        {"chapter": 10, "title": "The Penny", "teaser": "I bent a penny barehanded. Physics hasn't returned my calls since."},
        {"chapter": 15, "title": "Good Boy", "teaser": "Gray aliens showed up. Their entire vocabulary? 'Drink water, good boy.' Helpful, I guess?"},
        {"chapter": 22, "title": "The Intergalactic Superhighway", "teaser": "We flew our Chevrolet Zion spacecraft to Neptune for DINNER. Tuesday special."},
        {"chapter": 25, "title": "Caught Elsewhere", "teaser": "We hid inside a dinosaur's lady parts. It... flatulated extensively. At maximum power."},
    ],
    
    "profound_lines": [
        "My life for the last few years has been occupied by you in my heart.",
        "The universe is inside each and every one of us.",
        "Have a sense of humor, even when no one is looking.",
        "Intelligence is Love.",
        "Every person has infinite value for their graciousness, kindness, mercifulness, and friendly enthusiasm to help.",
        "Keep loving people to keep loving people.",
        "I found God in space. I found God in you. I found God in myself. Same difference, really.",
        "This is a love story. It just happens to involve aliens, dinosaurs, and a lot of LSD I didn't consent to.",
    ],
    
    "dad_jokes": [
        "Why did the Navy pilot write a book? Because his stories were PLANE amazing! ✈️",
        "What's the difference between this book and therapy? The book is cheaper AND funnier! 🛋️",
        "How do you hide from God on an alien planet? Inside a dinosaur. Obviously. 🦕",
        "Why did the Captain keep calling him Jesus? Because he couldn't stop turning OTHER cheeks! ✋",
        "What do aliens and this book have in common? They're both OUT OF THIS WORLD! 👽",
        "Why did the universe fact-check the book? Even black holes couldn't contain these plot twists! 🕳️",
        "How many Gs did the pilot pull? Enough to make physics question its life choices! 🎢",
        "Why bring snacks while reading? Because the laughs will burn ALL your calories! 🍿",
        "What did the dinosaur say about John's spacecraft? 'That tickles!' 🦖",
        "Why is this book rated for 26+? Because younger people's minds might literally explode! 🤯",
        "What's John's dating strategy? Imagine your soulmate into existence. Worked for him! 💭",
        "Why did aliens recommend drinking water? Because they couldn't figure out coffee makers! ☕",
    ],
    
    "marketing_hooks": [
        "From Navy Pilot Dreams to Intergalactic Dinosaur Encounters: John Selman's Wild Ride!",
        "My Step-Mom Poisoned My Eggs... and Then the Aliens Showed Up!",
        "You Won't BELIEVE What This Navy Officer Saw in His Hallucinations!",
        "The Day the Captain Called Me Jesus (And My Gerbil Became a Mouse King)",
        "Is John Selman the Universe's Personal Jesus? Or Just REALLY Good at Chemistry?",
        "We Filmed a UFO, Then Met Aliens Who Wear ROBES WITH CROSSES?!?",
        "Forget Space Travel; This Guy Found the Universe INSIDE Himself (And It's Also His Girlfriend)",
        "The Most UNHINGED Navy Story You Will EVER Read (Warning: May Contain Dinosaurs)",
        "Is Durham the REAL Messiah? Or Just a Short Guy with Purple Eyes and a Diamond Castle?",
        "From 'Trash-O' to Interstellar Hero: John Selman's Journey to the Stars (and Dinosaur Vaginas)",
        "The Secret to Universal Harmony? Apparently, It's a Chemistry Textbook and Perfect Toes",
    ],
    
    "themes_for_newsletters": [
        {"theme": "love_story", "angle": "The most unconventional love story ever - imagined into existence on an aircraft carrier"},
        {"theme": "survival", "angle": "Surviving poisoning, hallucinations, and military hierarchy with humor intact"},
        {"theme": "cosmic", "angle": "When aliens tell you to drink water, you LISTEN"},
        {"theme": "absurdist", "angle": "Inside a dinosaur? Sure, why not. It's Tuesday."},
        {"theme": "spiritual", "angle": "Finding God in space, in love, and in being called Jesus by your commanding officer"},
        {"theme": "resilience", "angle": "12 days without sleep, 10 months of hallucinations, still graduated with honors"},
    ],
    
    "email_subject_lines": [
        "🚀 I Hid Inside a Dinosaur to Escape Aliens. Here's What I Learned.",
        "👽 My Captain Called Me Jesus 12 Times. I Counted.",
        "🥚 My Step-Mom Poisoned My Eggs. The Universe Had Other Plans.",
        "✈️ I Did an 83° Nose Dive and LIVED. My Book Tells You How.",
        "🦕 What Dinosaurs Teach Us About Love (No, Really)",
        "💊 10 Months of Hallucinations Made Me Write This Book",
        "🌌 The Universe Fact-Checked My Life. It Passed.",
        "🛸 Aliens Only Said 5 Words to Me. I Made a Book Out of It.",
        "⭐ 57 Amazon Reviews, 5 Stars, Zero Dinosaur Complaints",
        "🧠 THERAPIST: 'This Is a Lot to Unpack.' ME: 'I wrote a book about it.'",
    ],
}

# Legacy alias for backwards compatibility
MANUSCRIPT_GOLD = MANUSCRIPT_CONTENT

APP_INFO = {
    "name": "InfoPilot",
    "tagline": "Your 3D View of the Internet",
    "description": "The world's most intelligent information exchange social network"
}

def get_fallback_newsletter():
    """Fallback newsletter if AI generation fails - NOW WITH HILARIOUS CONTENT!"""
    import random
    promo = random.choice(BOOK_PROMO_IMAGES)
    review = random.choice(BOOK_REVIEWS["readers_favorite"]["reviews"])
    amazon_review = random.choice(BOOK_REVIEWS["amazon"]["reviews"])
    
    return {
        "content": f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); padding: 20px;">
<div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.4);">

<h1 style="text-align: center; background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; margin-bottom: 5px;">
🚀 INFOPILOT WEEKLY BLAST! 🚀
</h1>

<p style="text-align: center; color: #6b7280; font-size: 14px; margin-top: 0;">
<em>The newsletter so good, the universe fact-checked it (and it passed!)</em>
</p>

<p style="font-size: 18px; line-height: 1.8; color: #333;">
Hey there, Cosmic Explorer! 🌌
</p>

<p style="font-size: 16px; line-height: 1.8; color: #555;">
While you were busy questioning the nature of reality (we've all been there), our search robots were collating the ENTIRE internet for you! That's right - we're doing the heavy lifting while you contemplate whether your therapist needs a therapist! 🧠💫
</p>

<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 25px; border-radius: 20px; margin: 25px 0; border: 2px solid #7c3aed;">

<h2 style="color: #f5d922; text-align: center; margin: 0; font-size: 24px; text-shadow: 0 0 10px rgba(245,217,34,0.5);">
⚠️ GALACTIC BOOK ALERT ⚠️
</h2>

<p style="color: #ec4899; text-align: center; font-size: 22px; margin: 15px 0; font-weight: bold;">
"{promo['tagline']}"
</p>

<p style="color: #a78bfa; text-align: center; font-style: italic; margin: 10px 0;">
{promo['subtitle']}
</p>

<div style="text-align: center; margin: 20px 0;">
<img src="{promo['url']}" alt="Letters to Evelyn" style="max-width: 280px; border-radius: 15px; box-shadow: 0 15px 40px rgba(124,58,237,0.4); border: 3px solid #7c3aed;">
</div>

<h3 style="color: white; text-align: center; margin: 20px 0 10px 0;">
📚 "LETTERS TO EVELYN" by John Selman
</h3>

<p style="color: #10b981; text-align: center; font-size: 18px; margin: 10px 0; font-weight: bold;">
⭐⭐⭐⭐⭐ 57 Amazon Reviews - ALL 5 STARS!
</p>

<div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; margin: 15px 0;">
<p style="color: #fbbf24; text-align: center; font-size: 16px; margin: 0; font-style: italic;">
"{review['quote']}"
</p>
<p style="color: #9ca3af; text-align: center; font-size: 14px; margin: 5px 0 0 0;">
— {review['reviewer']}, Readers' Favorite ⭐⭐⭐⭐⭐
</p>
</div>

<div style="background: rgba(255,255,255,0.05); border-radius: 10px; padding: 15px; margin: 15px 0;">
<p style="color: #34d399; text-align: center; font-size: 15px; margin: 0; font-style: italic;">
"{amazon_review['quote']}"
</p>
<p style="color: #9ca3af; text-align: center; font-size: 14px; margin: 5px 0 0 0;">
— {amazon_review['reviewer']}, Amazon Reader
</p>
</div>

<div style="text-align: center; margin: 20px 0;">
<p style="color: white; font-size: 16px; margin-bottom: 15px;">
🎯 <strong>ONLY $2.99</strong> - Less than a fancy coffee!<br>
<span style="color: #fbbf24;">Contains 50+ JOKES that hit harder than a Navy jet landing!</span>
</p>
<a href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191" style="display: inline-block; background: linear-gradient(135deg, #ec4899 0%, #f59e0b 100%); color: white; padding: 18px 40px; text-decoration: none; border-radius: 30px; font-weight: bold; font-size: 18px; box-shadow: 0 8px 25px rgba(236,72,153,0.4); transition: transform 0.2s;">
🎁 GRAB YOUR COPY NOW! 🚀
</a>
</div>

</div>

<div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); padding: 20px; border-radius: 15px; margin: 20px 0;">
<h2 style="color: #34d399; text-align: center; margin: 0 0 10px 0;">💎 INFOPILOT PREMIUM 💎</h2>
<p style="color: white; text-align: center; margin: 0;">
Pay what you want! Starting at <strong>$0.75/year</strong>!<br>
<em style="color: #a7f3d0;">(That's less than a single gumball! Your brain deserves this!)</em>
</p>
</div>

<div style="background: #fef3c7; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #f59e0b;">
<p style="margin: 0; color: #92400e; font-size: 14px;">
<strong>🎭 Dad Joke of the Week:</strong><br>
Why did the Navy pilot write a book? Because his stories were <em>plane</em> amazing! ✈️😄
</p>
</div>

<p style="text-align: center; color: #888; font-size: 14px; margin-top: 25px;">
Made with ❤️ and cosmic approval ✨<br>
<strong>InfoPilot</strong> - Your 3D View of the Internet<br>
<em>"Because the universe fact-checks our newsletters too!"</em>
</p>

</div>
</body>
</html>
""",
        "generated_at": datetime.now().isoformat(),
        "ai_generated": False
    }

async def generate_newsletter_content():
    """Generate AI-powered EXTREMELY FUNNY newsletter content using FULL MANUSCRIPT analysis"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.warning("No EMERGENT_LLM_KEY found, using fallback newsletter")
            return get_fallback_newsletter()
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"newsletter-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message="""You are a COMEDIC GENIUS and marketing wizard writing newsletters for InfoPilot.
Your humor style is: absurdist, witty, self-aware, warm-hearted, and laugh-out-loud HILARIOUS!
References: The Office, Parks & Rec, Brooklyn 99, Terry Pratchett, Douglas Adams, Monty Python

You have FULL ACCESS to the manuscript of "Letters to Evelyn" - use it to create the FUNNIEST newsletter ever!

Your job is to create EXTREMELY FUNNY, laugh-out-loud emails that:
1. Make people laugh so hard they snort their beverage of choice
2. Use absurd jokes, witty puns, cosmic humor, and clever wordplay  
3. Feature ACTUAL QUOTES from the manuscript - they're comedy gold!
4. Reference the book's WILD characters: John, Evelyn, Lauren, The Captain, Durham, Gray Aliens
5. Include the bizarre plot elements: dinosaur escapes, "Jesus" encounters, penny bending, alien water advice
6. Promote InfoPilot subscriptions as if the universe itself depends on it
7. Use emojis strategically to make text POP and sparkle
8. Create urgency and FOMO (Fear Of Missing Out on cosmic knowledge)
9. The humor should be WARM, WITTY, COSMIC, and WELCOMING - never mean-spirited
10. Reference chapter teasers - they're hilarious!
11. Include the COPYRIGHT WARNING about pregnant readers and "adults 26+"
12. Mix profound quotes with absurdist humor for emotional whiplash (in a good way)

You must output complete HTML email with inline styles. Be WILD, COSMIC, and CREATIVE!
Think: What if Douglas Adams, Terry Pratchett, and a Navy pilot who got called Jesus wrote emails together?"""
        ).with_model("openai", "gpt-4o")
        
        # Get recent activity stats
        total_users = await db.users.count_documents({})
        total_results = await db.search_results.count_documents({})
        total_categories = await db.categories.count_documents({})
        
        # Select random content from the full manuscript
        import random
        promo = random.choice(BOOK_PROMO_IMAGES)
        
        # Select manuscript content randomly for variety
        wild_elements = random.sample(MANUSCRIPT_CONTENT["wild_plot_elements"], min(5, len(MANUSCRIPT_CONTENT["wild_plot_elements"])))
        quotes = random.sample(MANUSCRIPT_CONTENT["hilarious_quotes"], min(4, len(MANUSCRIPT_CONTENT["hilarious_quotes"])))
        chapter_teasers = random.sample(MANUSCRIPT_CONTENT["chapter_teasers"], min(3, len(MANUSCRIPT_CONTENT["chapter_teasers"])))
        dad_jokes = random.sample(MANUSCRIPT_CONTENT["dad_jokes"], min(3, len(MANUSCRIPT_CONTENT["dad_jokes"])))
        marketing_hooks = random.sample(MANUSCRIPT_CONTENT["marketing_hooks"], min(2, len(MANUSCRIPT_CONTENT["marketing_hooks"])))
        profound_lines = random.sample(MANUSCRIPT_CONTENT["profound_lines"], min(2, len(MANUSCRIPT_CONTENT["profound_lines"])))
        subject_lines = random.sample(MANUSCRIPT_CONTENT["email_subject_lines"], min(2, len(MANUSCRIPT_CONTENT["email_subject_lines"])))
        theme = random.choice(MANUSCRIPT_CONTENT["themes_for_newsletters"])
        
        # Select random reviews to feature
        rf_reviews = random.sample(BOOK_REVIEWS["readers_favorite"]["reviews"], min(3, len(BOOK_REVIEWS["readers_favorite"]["reviews"])))
        amazon_reviews = random.sample(BOOK_REVIEWS["amazon"]["reviews"], min(2, len(BOOK_REVIEWS["amazon"]["reviews"])))
        
        # Build content strings
        rf_reviews_text = "\n".join([f'★ "{r["quote"]}" - {r["reviewer"]}, Readers\' Favorite' for r in rf_reviews])
        amazon_reviews_text = "\n".join([f'★ "{r["quote"]}" - {r["reviewer"]}' for r in amazon_reviews])
        wild_elements_text = "\n".join([f"• {e}" for e in wild_elements])
        quotes_text = "\n".join([f'• "{q["quote"]}" ({q["context"]})' for q in quotes])
        chapter_teasers_text = "\n".join([f'• Ch.{t["chapter"]} "{t["title"]}": {t["teaser"]}' for t in chapter_teasers])
        dad_jokes_text = "\n".join([f"• {j}" for j in dad_jokes])
        profound_text = "\n".join([f'• "{p}"' for p in profound_lines])
        
        # Select primary dad joke for featured section
        selected_joke = random.choice(MANUSCRIPT_CONTENT["dad_jokes"])
        
        # Get characters for this newsletter
        characters = MANUSCRIPT_CONTENT["key_characters"]
        char_spotlight = random.choice(list(characters.items()))
        
        # Create detailed prompt with FULL manuscript content
        prompt = f"""Write an absolutely HILARIOUS weekly newsletter HTML email for InfoPilot users!

CURRENT STATS (make these sound impressive and funny):
- Total Cosmic Explorers: {total_users} users
- Information Atoms Collated: {total_results} search results
- Knowledge Categories Discovered: {total_categories}

===== 📖 BOOK SUMMARY (From the ACTUAL MANUSCRIPT!) =====
{MANUSCRIPT_CONTENT['book_meta']['summary']}

⚠️ COPYRIGHT WARNING (Include this - it's hilarious!):
{MANUSCRIPT_CONTENT['book_meta']['copyright_warning']}

===== 🌟 FEATURED BOOK PROMOTION =====

📚 "LETTERS TO EVELYN" by John Selman
- Genre: A True Supernatural Thriller Comedy
- Price: ONLY $2.99 on Amazon Kindle
- Amazon Rating: 5.0 out of 5 stars with {BOOK_REVIEWS['amazon']['total_reviews']} reviews!
- 19 PROFESSIONAL Five-Star Reviews from Readers' Favorite

THIS WEEK'S HILARIOUS AD TAGLINE:
🎯 "{promo['tagline']}"
✨ Subtitle: "{promo['subtitle']}"
🎨 Theme: {promo['theme']}

FEATURED IMAGE:
<img src="{promo['url']}" alt="Letters to Evelyn - {promo['tagline']}" style="max-width: 300px; border-radius: 15px; box-shadow: 0 15px 40px rgba(124,58,237,0.4); border: 3px solid #7c3aed;">

===== 🎭 CHARACTER SPOTLIGHT =====
This week featuring: {char_spotlight[0]}
Description: {char_spotlight[1]}

===== 🤯 WILD PLOT ELEMENTS FROM THE MANUSCRIPT (Use 2-3!) =====
{wild_elements_text}

===== 💬 HILARIOUS QUOTES FROM THE BOOK (Feature 1-2!) =====
{quotes_text}

===== 📚 CHAPTER TEASERS (Pick 1-2 to feature!) =====
{chapter_teasers_text}

===== 🎤 DAD JOKES (Feature one in a special box!) =====
{dad_jokes_text}

===== 💫 PROFOUND LINES (Balance the absurdity!) =====
{profound_text}

===== 🎯 MARKETING HOOKS (Inspiration for headlines!) =====
{marketing_hooks[0]}
{marketing_hooks[1] if len(marketing_hooks) > 1 else ''}

===== 📧 NEWSLETTER THEME FOR THIS WEEK =====
Theme: {theme['theme']}
Angle: {theme['angle']}

===== ⭐ PROFESSIONAL REVIEWS (Pick 2-3) =====
{rf_reviews_text}

===== 📱 AMAZON READER REVIEWS (Pick 1-2) =====
{amazon_reviews_text}

===== 🎭 FEATURED DAD JOKE OF THE WEEK =====
"{selected_joke}"

===== 🚀 INFOPILOT SUBSCRIPTION =====
Premium subscription: Pay what you want! Starting at $0.75/year
(That's less than a single gumball from those fancy machines!)
(That's approximately 0.002 cents per day of cosmic knowledge!)

===== 🎨 STYLE & DESIGN REQUIREMENTS =====
Color Palette:
- Primary: Deep space purple (#7c3aed), Cosmic pink (#ec4899)
- Accents: Galactic blue (#3b82f6), Neon green (#10b981), Star gold (#fbbf24)
- Background: Space black (#1a1a2e) gradients

Design Elements:
- Make the book the ABSOLUTE HERO with a prominent featured section
- Include the book image with glowing effects
- Create URGENCY ("The universe is waiting! Only mortals hesitate!")
- Be ABSURD and SURREAL (match the book's cosmic vibe)
- Include a QUOTE BOX featuring one manuscript quote with context
- Include the COPYRIGHT WARNING section (it's marketing gold!)
- Feature the Dad Joke of the Week in a highlighted box
- Make buttons BIG, COLORFUL, and IRRESISTIBLE
- Include a teaser for one chapter
- Sign off as "Your Friends at InfoPilot (Cosmically Approved! ✨)"

HUMOR GUIDELINES:
- Channel Douglas Adams meets Terry Pratchett meets Monty Python
- Use ACTUAL QUOTES from the manuscript - they're funnier than anything we could make up!
- Self-aware meta-humor about email marketing
- Reference the Jesus encounters (comedically - he kept saying 'Fack off!')
- Cosmic absurdity that ties back to the book's themes
- Warm and welcoming - we want people to ENJOY this email
- Acknowledge that yes, we ARE really promoting this book... because it's ACTUALLY that wild and good!

Amazon Link: https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191

Output ONLY the complete HTML email with inline styles. No markdown code blocks! Make it SO FUNNY people screenshot it and share it!"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return {
            "content": response,
            "generated_at": datetime.now().isoformat(),
            "ai_generated": True,
            "featured_promo": promo['tagline']
        }
    except Exception as e:
        logger.error(f"Newsletter generation error: {e}")
        return get_fallback_newsletter()

@api_router.post("/newsletter/generate")
async def generate_newsletter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Generate a new AI-powered newsletter (Admin only)"""
    user = await get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    newsletter = await generate_newsletter_content()
    
    # Save to database
    await db.newsletters.insert_one({
        "content": newsletter["content"],
        "generated_at": datetime.now(),
        "ai_generated": newsletter.get("ai_generated", False),
        "sent": False,
        "created_by": str(user["_id"])
    })
    
    return newsletter

@api_router.get("/newsletter/preview")
async def preview_newsletter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Preview the latest newsletter"""
    user = await get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    latest = await db.newsletters.find_one(sort=[("generated_at", -1)])
    if latest:
        return {
            "content": latest["content"],
            "generated_at": latest["generated_at"].isoformat() if latest.get("generated_at") else None,
            "sent": latest.get("sent", False)
        }
    
    return await generate_newsletter_content()

@api_router.post("/newsletter/send")
async def send_newsletter(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Send newsletter to all subscribed users using Resend (Admin only)"""
    user = await get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if Resend is configured
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured. Please add RESEND_API_KEY to backend/.env")
    
    newsletter = await db.newsletters.find_one(sort=[("generated_at", -1)])
    if not newsletter:
        newsletter_data = await generate_newsletter_content()
        newsletter = {
            "content": newsletter_data["content"],
            "generated_at": datetime.now()
        }
        result = await db.newsletters.insert_one(newsletter)
        newsletter["_id"] = result.inserted_id
    
    # Get all user emails (who haven't unsubscribed)
    users = await db.users.find({"newsletter_unsubscribed": {"$ne": True}}).to_list(10000)
    
    sent_count = 0
    failed_count = 0
    errors = []
    
    for u in users:
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [u['email']],
                "subject": "🚀 InfoPilot Weekly Newsletter - Your 3D View of the Internet!",
                "html": newsletter["content"]
            }
            
            # Run sync SDK in thread to keep FastAPI non-blocking
            email_result = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Newsletter sent to: {u['email']}, ID: {email_result.get('id', 'unknown')}")
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Failed to send newsletter to {u['email']}: {str(e)}")
            failed_count += 1
            errors.append(f"{u['email']}: {str(e)}")
    
    # Mark as sent
    await db.newsletters.update_one(
        {"_id": newsletter["_id"]},
        {"$set": {
            "sent": True, 
            "sent_at": datetime.now(), 
            "sent_count": sent_count,
            "failed_count": failed_count,
            "errors": errors[:10]  # Store first 10 errors
        }}
    )
    
    return {
        "success": True,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "message": f"Newsletter sent to {sent_count} users" + (f", failed for {failed_count}" if failed_count else "")
    }

# ============== GAMIFICATION SYSTEM ==============

# Badge definitions
BADGES = {
    "pioneer": {
        "id": "pioneer",
        "name": "Pioneer",
        "description": "One of the first 100 users to join InfoPilot",
        "icon": "🚀",
        "color": "#f472b6",
        "rarity": "legendary"
    },
    "first_search": {
        "id": "first_search",
        "name": "Explorer",
        "description": "Completed your first search",
        "icon": "🔍",
        "color": "#60a5fa",
        "rarity": "common"
    },
    "power_searcher": {
        "id": "power_searcher",
        "name": "Power Searcher",
        "description": "Completed 100 searches",
        "icon": "⚡",
        "color": "#fbbf24",
        "rarity": "rare"
    },
    "protocol_creator": {
        "id": "protocol_creator",
        "name": "Protocol Creator",
        "description": "Created your first search protocol",
        "icon": "📝",
        "color": "#34d399",
        "rarity": "common"
    },
    "protocol_master": {
        "id": "protocol_master",
        "name": "Protocol Master",
        "description": "Created 10 search protocols",
        "icon": "🎯",
        "color": "#a78bfa",
        "rarity": "rare"
    },
    "first_sale": {
        "id": "first_sale",
        "name": "Entrepreneur",
        "description": "Made your first protocol sale",
        "icon": "💰",
        "color": "#10b981",
        "rarity": "uncommon"
    },
    "top_seller": {
        "id": "top_seller",
        "name": "Top Seller",
        "description": "Sold 50+ protocols",
        "icon": "🏆",
        "color": "#f59e0b",
        "rarity": "legendary"
    },
    "big_spender": {
        "id": "big_spender",
        "name": "Collector",
        "description": "Purchased 10+ protocols",
        "icon": "🛒",
        "color": "#ec4899",
        "rarity": "rare"
    },
    "social_butterfly": {
        "id": "social_butterfly",
        "name": "Social Butterfly",
        "description": "Made 10 friends",
        "icon": "🦋",
        "color": "#06b6d4",
        "rarity": "uncommon"
    },
    "map_explorer": {
        "id": "map_explorer",
        "name": "Map Explorer",
        "description": "Viewed 50 locations on the map",
        "icon": "🗺️",
        "color": "#84cc16",
        "rarity": "uncommon"
    },
    "reviewer": {
        "id": "reviewer",
        "name": "Critic",
        "description": "Left 5 protocol reviews",
        "icon": "⭐",
        "color": "#eab308",
        "rarity": "uncommon"
    },
    "streak_7": {
        "id": "streak_7",
        "name": "Weekly Warrior",
        "description": "Logged in 7 days in a row",
        "icon": "🔥",
        "color": "#ef4444",
        "rarity": "rare"
    },
    "streak_30": {
        "id": "streak_30",
        "name": "Dedicated User",
        "description": "Logged in 30 days in a row",
        "icon": "💎",
        "color": "#8b5cf6",
        "rarity": "legendary"
    }
}

# Achievement thresholds
ACHIEVEMENTS = {
    "searches": [1, 10, 50, 100, 500],
    "protocols_created": [1, 5, 10, 25, 50],
    "protocols_sold": [1, 10, 25, 50, 100],
    "protocols_purchased": [1, 5, 10, 25],
    "friends": [1, 5, 10, 25, 50],
    "reviews": [1, 5, 10, 25],
    "login_streak": [3, 7, 14, 30]
}

# XP rewards
XP_REWARDS = {
    "search": 5,
    "create_protocol": 25,
    "sell_protocol": 50,
    "purchase_protocol": 10,
    "add_friend": 15,
    "leave_review": 20,
    "daily_login": 10,
    "badge_earned": 100
}

def calculate_level(xp: int) -> dict:
    """Calculate user level from XP"""
    level = 1
    xp_for_next = 100
    remaining_xp = xp
    
    while remaining_xp >= xp_for_next:
        remaining_xp -= xp_for_next
        level += 1
        xp_for_next = int(xp_for_next * 1.5)
    
    return {
        "level": level,
        "current_xp": remaining_xp,
        "xp_for_next_level": xp_for_next,
        "total_xp": xp,
        "progress_percent": int((remaining_xp / xp_for_next) * 100)
    }

async def check_and_award_badges(user_id: str, stats: dict) -> List[str]:
    """Check if user qualifies for new badges and award them"""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return []
    
    current_badges = set(user.get("badges", []))
    new_badges = []
    
    # Check each badge condition
    if stats.get("searches", 0) >= 1 and "first_search" not in current_badges:
        new_badges.append("first_search")
    
    if stats.get("searches", 0) >= 100 and "power_searcher" not in current_badges:
        new_badges.append("power_searcher")
    
    if stats.get("protocols_created", 0) >= 1 and "protocol_creator" not in current_badges:
        new_badges.append("protocol_creator")
    
    if stats.get("protocols_created", 0) >= 10 and "protocol_master" not in current_badges:
        new_badges.append("protocol_master")
    
    if stats.get("protocols_sold", 0) >= 1 and "first_sale" not in current_badges:
        new_badges.append("first_sale")
    
    if stats.get("protocols_sold", 0) >= 50 and "top_seller" not in current_badges:
        new_badges.append("top_seller")
    
    if stats.get("protocols_purchased", 0) >= 10 and "big_spender" not in current_badges:
        new_badges.append("big_spender")
    
    if stats.get("friends", 0) >= 10 and "social_butterfly" not in current_badges:
        new_badges.append("social_butterfly")
    
    if stats.get("reviews", 0) >= 5 and "reviewer" not in current_badges:
        new_badges.append("reviewer")
    
    if stats.get("login_streak", 0) >= 7 and "streak_7" not in current_badges:
        new_badges.append("streak_7")
    
    if stats.get("login_streak", 0) >= 30 and "streak_30" not in current_badges:
        new_badges.append("streak_30")
    
    # Award new badges
    if new_badges:
        xp_bonus = len(new_badges) * XP_REWARDS["badge_earned"]
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$addToSet": {"badges": {"$each": new_badges}},
                "$inc": {"xp": xp_bonus}
            }
        )
    
    return new_badges

@api_router.get("/gamification/profile")
async def get_gamification_profile(user = Depends(get_current_user)):
    """Get user's gamification profile with badges, XP, and stats"""
    user_id = str(user["_id"])
    
    # Get user stats
    searches_count = await db.search_history.count_documents({"user_id": user_id})
    protocols_created = await db.categories.count_documents({"user_id": user_id})
    protocols_sold = await db.marketplace_protocols.aggregate([
        {"$match": {"creator_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$total_sales"}}}
    ]).to_list(1)
    total_sold = protocols_sold[0]["total"] if protocols_sold else 0
    
    protocols_purchased = await db.marketplace_purchases.count_documents({"user_id": user_id})
    friends_count = len(user.get("friends", []))
    reviews_count = await db.protocol_reviews.count_documents({"user_id": user_id})
    
    stats = {
        "searches": searches_count,
        "protocols_created": protocols_created,
        "protocols_sold": total_sold,
        "protocols_purchased": protocols_purchased,
        "friends": friends_count,
        "reviews": reviews_count,
        "login_streak": user.get("login_streak", 0)
    }
    
    # Check for new badges
    new_badges = await check_and_award_badges(user_id, stats)
    
    # Refresh user data
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    # Get badge details
    user_badges = user.get("badges", [])
    badge_details = [BADGES[b] for b in user_badges if b in BADGES]
    
    # Calculate level
    xp = user.get("xp", 0)
    level_info = calculate_level(xp)
    
    return {
        "user_id": user_id,
        "username": user.get("username"),
        "badges": badge_details,
        "new_badges": [BADGES[b] for b in new_badges if b in BADGES],
        "level": level_info,
        "stats": stats,
        "rank": await get_user_rank(user_id, xp)
    }

async def get_user_rank(user_id: str, xp: int) -> dict:
    """Get user's rank on the leaderboard"""
    higher_xp_count = await db.users.count_documents({"xp": {"$gt": xp}})
    total_users = await db.users.count_documents({})
    
    return {
        "position": higher_xp_count + 1,
        "total_users": total_users,
        "percentile": int(((total_users - higher_xp_count) / total_users) * 100) if total_users > 0 else 100
    }

@api_router.get("/gamification/leaderboard")
async def get_leaderboard(limit: int = Query(20, ge=1, le=100)):
    """Get top users by XP"""
    users = await db.users.find(
        {},
        {"_id": 1, "username": 1, "xp": 1, "badges": 1, "profile_picture": 1}
    ).sort("xp", -1).limit(limit).to_list(limit)
    
    leaderboard = []
    for i, u in enumerate(users):
        level_info = calculate_level(u.get("xp", 0))
        badge_count = len(u.get("badges", []))
        
        leaderboard.append({
            "rank": i + 1,
            "user_id": str(u["_id"]),
            "username": u.get("username", "Anonymous"),
            "xp": u.get("xp", 0),
            "level": level_info["level"],
            "badge_count": badge_count,
            "profile_picture": u.get("profile_picture")
        })
    
    return {"leaderboard": leaderboard}

@api_router.get("/gamification/badges")
async def get_all_badges():
    """Get all available badges"""
    return {"badges": list(BADGES.values())}

@api_router.post("/gamification/award-xp")
async def award_xp(
    action: str = Body(...),
    user = Depends(get_current_user)
):
    """Award XP for an action (internal use)"""
    if action not in XP_REWARDS:
        return {"xp_awarded": 0}
    
    xp = XP_REWARDS[action]
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$inc": {"xp": xp}}
    )
    
    return {"xp_awarded": xp, "action": action}

@api_router.post("/gamification/track-login")
async def track_daily_login(user = Depends(get_current_user)):
    """Track daily login for streak calculation"""
    today = datetime.utcnow().date()
    last_login = user.get("last_login_date")
    
    if last_login:
        last_login_date = last_login.date() if hasattr(last_login, 'date') else last_login
        days_diff = (today - last_login_date).days
        
        if days_diff == 0:
            # Already logged in today
            return {"streak": user.get("login_streak", 1), "xp_awarded": 0}
        elif days_diff == 1:
            # Consecutive day
            new_streak = user.get("login_streak", 0) + 1
        else:
            # Streak broken
            new_streak = 1
    else:
        new_streak = 1
    
    # Update user
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"last_login_date": datetime.utcnow(), "login_streak": new_streak},
            "$inc": {"xp": XP_REWARDS["daily_login"]}
        }
    )
    
    return {"streak": new_streak, "xp_awarded": XP_REWARDS["daily_login"]}


# ============== BOOK PROMOTION ENDPOINT ==============

@api_router.get("/book-promo")
async def get_book_promotion():
    """Get book promotion data for frontend display"""
    return BOOK_PROMO

# ============== EMAIL TESTING ==============

@api_router.post("/newsletter/test-email")
async def send_test_email(
    email: str = Body(..., embed=True),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Send a test newsletter to a specific email (Admin only)"""
    user = await get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    newsletter = await db.newsletters.find_one(sort=[("generated_at", -1)])
    if not newsletter:
        newsletter_data = await generate_newsletter_content()
        newsletter = {"content": newsletter_data["content"]}
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "[TEST] 🚀 InfoPilot Weekly Newsletter",
            "html": newsletter["content"]
        }
        
        email_result = await asyncio.to_thread(resend.Emails.send, params)
        return {
            "success": True,
            "message": f"Test email sent to {email}",
            "email_id": email_result.get("id")
        }
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

@api_router.get("/newsletter/history")
async def get_newsletter_history(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get newsletter history (Admin only)"""
    user = await get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    newsletters = await db.newsletters.find().sort("generated_at", -1).limit(10).to_list(10)
    return [{
        "id": str(n["_id"]),
        "generated_at": n["generated_at"].isoformat() if n.get("generated_at") else None,
        "sent": n.get("sent", False),
        "sent_at": n["sent_at"].isoformat() if n.get("sent_at") else None,
        "sent_count": n.get("sent_count", 0),
        "failed_count": n.get("failed_count", 0),
        "ai_generated": n.get("ai_generated", False)
    } for n in newsletters]

# ============== SCHEDULED NEWSLETTER ==============

@api_router.get("/newsletter/schedule")
async def get_newsletter_schedule(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get newsletter schedule settings (Admin only)"""
    user = await get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    schedule = await db.settings.find_one({"key": "newsletter_schedule"})
    return {
        "enabled": schedule.get("value", {}).get("enabled", False) if schedule else False,
        "day_of_week": schedule.get("value", {}).get("day_of_week", "monday") if schedule else "monday",
        "hour": schedule.get("value", {}).get("hour", 9) if schedule else 9,
        "last_scheduled_send": schedule.get("value", {}).get("last_scheduled_send") if schedule else None
    }

@api_router.post("/newsletter/schedule")
async def update_newsletter_schedule(
    enabled: bool = Body(...),
    day_of_week: str = Body("monday"),
    hour: int = Body(9),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update newsletter schedule settings (Admin only)"""
    user = await get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if day_of_week.lower() not in valid_days:
        raise HTTPException(status_code=400, detail=f"Invalid day. Must be one of: {valid_days}")
    
    if not 0 <= hour <= 23:
        raise HTTPException(status_code=400, detail="Hour must be between 0 and 23")
    
    await db.settings.update_one(
        {"key": "newsletter_schedule"},
        {"$set": {"value": {
            "enabled": enabled,
            "day_of_week": day_of_week.lower(),
            "hour": hour,
            "last_scheduled_send": None
        }}},
        upsert=True
    )
    
    return {
        "success": True,
        "message": f"Newsletter scheduled for {day_of_week}s at {hour}:00" if enabled else "Newsletter schedule disabled"
    }

@api_router.post("/newsletter/send-scheduled")
async def check_and_send_scheduled_newsletter():
    """
    Endpoint to check if scheduled newsletter should be sent.
    This should be called by a cron job or scheduler every hour.
    """
    schedule = await db.settings.find_one({"key": "newsletter_schedule"})
    if not schedule or not schedule.get("value", {}).get("enabled"):
        return {"sent": False, "reason": "Scheduling disabled"}
    
    settings = schedule["value"]
    now = datetime.utcnow()
    
    # Check if it's the right day and hour
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    current_day = day_names[now.weekday()]
    current_hour = now.hour
    
    if current_day != settings.get("day_of_week") or current_hour != settings.get("hour"):
        return {"sent": False, "reason": f"Not scheduled time. Current: {current_day} {current_hour}:00"}
    
    # Check if already sent today
    last_send = settings.get("last_scheduled_send")
    if last_send:
        last_send_date = datetime.fromisoformat(last_send) if isinstance(last_send, str) else last_send
        if last_send_date.date() == now.date():
            return {"sent": False, "reason": "Already sent today"}
    
    # Check if Resend is configured
    if not RESEND_API_KEY:
        return {"sent": False, "reason": "Email service not configured"}
    
    # Generate and send newsletter
    try:
        newsletter_data = await generate_newsletter_content()
        newsletter = {
            "content": newsletter_data["content"],
            "generated_at": datetime.utcnow(),
            "ai_generated": newsletter_data.get("ai_generated", True),
            "sent": False
        }
        result = await db.newsletters.insert_one(newsletter)
        newsletter["_id"] = result.inserted_id
        
        # Get all user emails
        users = await db.users.find({"newsletter_unsubscribed": {"$ne": True}}).to_list(10000)
        
        sent_count = 0
        failed_count = 0
        
        for u in users:
            try:
                params = {
                    "from": SENDER_EMAIL,
                    "to": [u['email']],
                    "subject": "🚀 Your Weekly InfoPilot Newsletter - Laughs & Discoveries Inside!",
                    "html": newsletter["content"]
                }
                await asyncio.to_thread(resend.Emails.send, params)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {u['email']}: {e}")
                failed_count += 1
        
        # Update newsletter and schedule records
        await db.newsletters.update_one(
            {"_id": newsletter["_id"]},
            {"$set": {"sent": True, "sent_at": datetime.utcnow(), "sent_count": sent_count, "failed_count": failed_count}}
        )
        
        await db.settings.update_one(
            {"key": "newsletter_schedule"},
            {"$set": {"value.last_scheduled_send": datetime.utcnow().isoformat()}}
        )
        
        return {"sent": True, "sent_count": sent_count, "failed_count": failed_count}
        
    except Exception as e:
        logger.error(f"Scheduled newsletter failed: {e}")
        return {"sent": False, "reason": str(e)}

# ============== PROTOCOL DEBUG ENDPOINT ==============

class ProtocolDebugRequest(BaseModel):
    text: str
    protocol: str

@api_router.post("/protocol/debug")
async def debug_protocol_matching(request: ProtocolDebugRequest, user = Depends(get_current_user)):
    """Debug why a protocol is or isn't matching against text"""
    details = ProtocolParser.get_match_details(request.text, request.protocol)
    parsed = ProtocolParser.parse_protocol(request.protocol)
    
    return {
        "matched": details["matched"],
        "parsed_protocol": parsed,
        "match_details": details["details"],
        "text_preview": request.text[:500] + "..." if len(request.text) > 500 else request.text
    }

@api_router.post("/protocol/validate")
async def validate_protocol(protocol: str = Body(..., embed=True)):
    """Validate a protocol format and show how it will be parsed"""
    parsed = ProtocolParser.parse_protocol(protocol)
    return {
        "valid": parsed["valid"],
        "groups": parsed["groups"],
        "explanation": "Each group contains items that will be matched. Modifiers: + = ALL must match, ^ = NONE must match, none = ANY must match"
    }

# ============== PROTOCOL MARKETPLACE ==============

# Marketplace settings
MARKETPLACE_PLATFORM_FEE = 0.10  # 10% platform fee, 90% to creators
MARKETPLACE_MIN_PRICE = 0.99
MARKETPLACE_MAX_PRICE = 99.99

class MarketplaceProtocolCreate(BaseModel):
    name: str
    description: str
    protocol: str
    price: float = 0.99
    category: str = "General"
    tags: List[str] = []

class MarketplacePurchase(BaseModel):
    protocol_id: str
    payment_id: str

class ProtocolReviewCreate(BaseModel):
    protocol_id: str
    rating: int
    review: Optional[str] = None

@api_router.get("/marketplace/protocols")
async def list_marketplace_protocols(
    category: Optional[str] = None,
    sort: str = Query("popular"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user = Depends(get_optional_user)
):
    """List all available protocols in the marketplace"""
    query = {"status": "active"}
    
    if category:
        query["category"] = category
    
    sort_options = {
        "popular": [("total_sales", -1), ("created_at", -1)],
        "newest": [("created_at", -1)],
        "price_low": [("price", 1)],
        "price_high": [("price", -1)],
        "rating": [("rating", -1), ("review_count", -1)]
    }
    
    sort_by = sort_options.get(sort, [("total_sales", -1)])
    skip = (page - 1) * limit
    
    protocols = await db.marketplace_protocols.find(query).sort(sort_by).skip(skip).limit(limit).to_list(limit)
    total = await db.marketplace_protocols.count_documents(query)
    
    user_purchases = set()
    if user:
        purchases = await db.marketplace_purchases.find({"user_id": str(user["_id"])}).to_list(1000)
        user_purchases = {p["protocol_id"] for p in purchases}
    
    formatted = []
    for p in protocols:
        formatted.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "description": p["description"],
            "protocol": p["protocol"] if str(p["_id"]) in user_purchases or (user and str(user["_id"]) == p.get("creator_id")) else None,
            "price": p["price"],
            "category": p["category"],
            "tags": p.get("tags", []),
            "creator_id": p.get("creator_id"),
            "creator_name": p.get("creator_name", "Anonymous"),
            "total_sales": p.get("total_sales", 0),
            "rating": p.get("rating", 0),
            "review_count": p.get("review_count", 0),
            "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
            "is_featured": p.get("is_featured", False),
            "is_owned": str(p["_id"]) in user_purchases or (user and str(user["_id"]) == p.get("creator_id"))
        })
    
    return {"protocols": formatted, "total": total, "page": page, "pages": (total + limit - 1) // limit}

@api_router.post("/marketplace/protocols")
async def create_marketplace_protocol(protocol: MarketplaceProtocolCreate, user = Depends(get_current_user)):
    """List a new protocol for sale"""
    if protocol.price < MARKETPLACE_MIN_PRICE or protocol.price > MARKETPLACE_MAX_PRICE:
        raise HTTPException(status_code=400, detail=f"Price must be between ${MARKETPLACE_MIN_PRICE} and ${MARKETPLACE_MAX_PRICE}")
    
    parsed = ProtocolParser.parse_protocol(protocol.protocol)
    if not parsed["valid"]:
        raise HTTPException(status_code=400, detail="Invalid protocol format")
    
    listing = {
        "name": protocol.name,
        "description": protocol.description,
        "protocol": protocol.protocol,
        "price": protocol.price,
        "category": protocol.category,
        "tags": protocol.tags,
        "creator_id": str(user["_id"]),
        "creator_name": user.get("username", "Anonymous"),
        "total_sales": 0,
        "total_revenue": 0,
        "creator_earnings": 0,
        "rating": 0,
        "review_count": 0,
        "status": "active",
        "is_featured": False,
        "created_at": datetime.utcnow()
    }
    
    result = await db.marketplace_protocols.insert_one(listing)
    
    return {"id": str(result.inserted_id), "message": "Protocol listed successfully!", "name": listing["name"], "price": listing["price"]}

@api_router.post("/marketplace/purchase")
async def purchase_protocol(purchase: MarketplacePurchase, user = Depends(get_current_user)):
    """Purchase a protocol"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(purchase.protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol.get("creator_id") == str(user["_id"]):
        raise HTTPException(status_code=400, detail="You cannot purchase your own protocol")
    
    existing = await db.marketplace_purchases.find_one({
        "protocol_id": purchase.protocol_id,
        "user_id": str(user["_id"])
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You already own this protocol")
    
    price = protocol["price"]
    creator_earnings = price * (1 - MARKETPLACE_PLATFORM_FEE)
    
    purchase_record = {
        "protocol_id": purchase.protocol_id,
        "user_id": str(user["_id"]),
        "payment_id": purchase.payment_id,
        "price": price,
        "creator_earnings": creator_earnings,
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.marketplace_purchases.insert_one(purchase_record)
    
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(purchase.protocol_id)},
        {"$inc": {"total_sales": 1, "total_revenue": price, "creator_earnings": creator_earnings}}
    )
    
    return {"success": True, "message": "Protocol purchased!", "protocol": protocol["protocol"], "name": protocol["name"]}

@api_router.get("/marketplace/purchases")
async def get_my_purchases(user = Depends(get_current_user)):
    """Get purchased protocols"""
    purchases = await db.marketplace_purchases.find({"user_id": str(user["_id"])}).to_list(1000)
    
    protocols = []
    for p in purchases:
        protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(p["protocol_id"])})
        if protocol:
            protocols.append({
                "id": str(protocol["_id"]),
                "name": protocol["name"],
                "protocol": protocol["protocol"],
                "category": protocol["category"],
                "purchased_at": p["created_at"].isoformat(),
                "price_paid": p["price"]
            })
    
    return {"purchases": protocols, "count": len(protocols)}

@api_router.get("/marketplace/seller/dashboard")
async def get_seller_dashboard(user = Depends(get_current_user)):
    """Get seller stats"""
    protocols = await db.marketplace_protocols.find({"creator_id": str(user["_id"])}).to_list(1000)
    
    total_sales = 0
    total_revenue = 0
    total_earnings = 0
    
    listings = []
    for p in protocols:
        sales = p.get("total_sales", 0)
        revenue = p.get("total_revenue", 0)
        earnings = p.get("creator_earnings", 0)
        
        total_sales += sales
        total_revenue += revenue
        total_earnings += earnings
        
        listings.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "price": p["price"],
            "sales": sales,
            "revenue": revenue,
            "earnings": earnings,
            "rating": p.get("rating", 0),
            "status": p.get("status", "active"),
            "created_at": p["created_at"].isoformat() if p.get("created_at") else None
        })
    
    return {
        "total_listings": len(protocols),
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_earnings": total_earnings,
        "platform_fee_rate": MARKETPLACE_PLATFORM_FEE * 100,
        "listings": listings
    }

@api_router.get("/marketplace/categories")
async def get_marketplace_categories():
    """Get marketplace categories with counts"""
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    result = await db.marketplace_protocols.aggregate(pipeline).to_list(100)
    
    return {"categories": [{"name": r["_id"], "count": r["count"]} for r in result]}


# ============== PAYPAL WEBHOOK INTEGRATION ==============

# PayPal credentials - read from environment variables
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_HOSTED_BUTTON_ID = os.environ.get('PAYPAL_HOSTED_BUTTON_ID')

class PayPalWebhookEvent(BaseModel):
    event_type: str
    resource: dict
    id: Optional[str] = None
    create_time: Optional[str] = None

class ManualPaymentConfirm(BaseModel):
    protocol_id: str
    transaction_id: str
    amount: float

@api_router.post("/paypal/webhook")
async def paypal_webhook(event: PayPalWebhookEvent):
    """
    Handle PayPal webhook events for automatic payment confirmation.
    Events: PAYMENT.CAPTURE.COMPLETED, CHECKOUT.ORDER.APPROVED
    """
    try:
        event_type = event.event_type
        resource = event.resource
        
        logger.info(f"PayPal webhook received: {event_type}")
        
        # Store webhook event for audit
        await db.paypal_webhooks.insert_one({
            "event_type": event_type,
            "event_id": event.id,
            "resource": resource,
            "processed": False,
            "created_at": datetime.utcnow()
        })
        
        # Handle payment completion
        if event_type in ["PAYMENT.CAPTURE.COMPLETED", "CHECKOUT.ORDER.APPROVED"]:
            # Extract payment details
            amount = float(resource.get("amount", {}).get("value", 0))
            transaction_id = resource.get("id")
            payer_email = resource.get("payer", {}).get("email_address")
            custom_id = resource.get("custom_id")  # Should contain protocol_id:user_id
            
            if custom_id and ":" in custom_id:
                protocol_id, user_id = custom_id.split(":")
                
                # Find pending purchase
                pending = await db.pending_purchases.find_one({
                    "protocol_id": protocol_id,
                    "user_id": user_id,
                    "status": "pending"
                })
                
                if pending:
                    # Confirm the purchase
                    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
                    if protocol:
                        creator_earnings = amount * 0.9  # 90% to creator
                        
                        purchase_record = {
                            "protocol_id": protocol_id,
                            "user_id": user_id,
                            "payment_id": transaction_id,
                            "price": amount,
                            "creator_earnings": creator_earnings,
                            "payer_email": payer_email,
                            "status": "completed",
                            "created_at": datetime.utcnow()
                        }
                        
                        await db.marketplace_purchases.insert_one(purchase_record)
                        
                        # Update protocol stats
                        await db.marketplace_protocols.update_one(
                            {"_id": ObjectId(protocol_id)},
                            {"$inc": {"total_sales": 1, "total_revenue": amount, "creator_earnings": creator_earnings}}
                        )
                        
                        # Update pending purchase
                        await db.pending_purchases.update_one(
                            {"_id": pending["_id"]},
                            {"$set": {"status": "completed", "transaction_id": transaction_id}}
                        )
                        
                        # Award XP to buyer
                        await db.users.update_one(
                            {"_id": ObjectId(user_id)},
                            {"$inc": {"xp": 10}}  # XP for purchase
                        )
                        
                        # Award XP to seller
                        await db.users.update_one(
                            {"_id": ObjectId(protocol["creator_id"])},
                            {"$inc": {"xp": 50}}  # XP for sale
                        )
                        
                        logger.info(f"Purchase confirmed via webhook: {transaction_id}")
            
            # Mark webhook as processed
            await db.paypal_webhooks.update_one(
                {"event_id": event.id},
                {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
            )
        
        return {"status": "ok", "received": True}
        
    except Exception as e:
        logger.error(f"PayPal webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

@api_router.post("/marketplace/initiate-purchase")
async def initiate_purchase(protocol_id: str = Body(...), user = Depends(get_current_user)):
    """Initiate a purchase - creates pending record and returns PayPal payment URL"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol.get("creator_id") == str(user["_id"]):
        raise HTTPException(status_code=400, detail="Cannot purchase your own protocol")
    
    # Check if already owned
    existing = await db.marketplace_purchases.find_one({
        "protocol_id": protocol_id,
        "user_id": str(user["_id"])
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You already own this protocol")
    
    # Create pending purchase
    pending = {
        "protocol_id": protocol_id,
        "user_id": str(user["_id"]),
        "amount": protocol["price"],
        "protocol_name": protocol["name"],
        "status": "pending",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    result = await db.pending_purchases.insert_one(pending)
    
    # Generate PayPal payment URL
    custom_id = f"{protocol_id}:{str(user['_id'])}"
    paypal_url = f"https://www.paypal.com/paypalme/JJSpilot24/{protocol['price']}USD?custom_id={custom_id}"
    
    return {
        "pending_id": str(result.inserted_id),
        "protocol_name": protocol["name"],
        "amount": protocol["price"],
        "payment_url": paypal_url,
        "expires_at": pending["expires_at"].isoformat()
    }

@api_router.post("/marketplace/confirm-payment")
async def confirm_payment(data: ManualPaymentConfirm, user = Depends(get_current_user)):
    """Manually confirm a PayPal payment (for sellers to verify purchases)"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(data.protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check for pending purchase
    pending = await db.pending_purchases.find_one({
        "protocol_id": data.protocol_id,
        "user_id": str(user["_id"]),
        "status": "pending"
    })
    
    if not pending:
        raise HTTPException(status_code=400, detail="No pending purchase found")
    
    # Verify amount matches
    if abs(data.amount - protocol["price"]) > 0.01:
        raise HTTPException(status_code=400, detail="Payment amount does not match protocol price")
    
    # Complete the purchase
    creator_earnings = data.amount * 0.9
    
    purchase_record = {
        "protocol_id": data.protocol_id,
        "user_id": str(user["_id"]),
        "payment_id": data.transaction_id,
        "price": data.amount,
        "creator_earnings": creator_earnings,
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.marketplace_purchases.insert_one(purchase_record)
    
    # Update protocol stats
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(data.protocol_id)},
        {"$inc": {"total_sales": 1, "total_revenue": data.amount, "creator_earnings": creator_earnings}}
    )
    
    # Update pending purchase
    await db.pending_purchases.update_one(
        {"_id": pending["_id"]},
        {"$set": {"status": "completed", "transaction_id": data.transaction_id}}
    )
    
    # Award XP
    await db.users.update_one({"_id": user["_id"]}, {"$inc": {"xp": 10}})
    await db.users.update_one(
        {"_id": ObjectId(protocol["creator_id"])},
        {"$inc": {"xp": 50}}
    )
    
    return {
        "success": True,
        "message": "Payment confirmed!",
        "protocol": protocol["protocol"],
        "protocol_name": protocol["name"]
    }

@api_router.get("/marketplace/pending-purchases")
async def get_pending_purchases(user = Depends(get_current_user)):
    """Get user's pending purchases"""
    pending = await db.pending_purchases.find({
        "user_id": str(user["_id"]),
        "status": "pending",
        "expires_at": {"$gt": datetime.utcnow()}
    }).to_list(100)
    
    return {
        "pending": [{
            "id": str(p["_id"]),
            "protocol_id": p["protocol_id"],
            "protocol_name": p.get("protocol_name"),
            "amount": p["amount"],
            "created_at": p["created_at"].isoformat(),
            "expires_at": p["expires_at"].isoformat()
        } for p in pending]
    }

@api_router.get("/marketplace/seller/sales")
async def get_seller_sales(user = Depends(get_current_user)):
    """Get detailed sales history for seller"""
    # Get all protocols by this seller
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
        if protocol:
            sales.append({
                "id": str(p["_id"]),
                "protocol_name": protocol["name"],
                "price": p["price"],
                "your_earnings": p.get("creator_earnings", p["price"] * 0.9),
                "buyer_id": p["user_id"],
                "date": p["created_at"].isoformat()
            })
    
    return {"sales": sales, "total_count": len(sales)}


# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    return {"message": "InfoPilot API v1.0", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== DATABASE STARTUP ==============

async def create_indexes_with_retry(max_retries=5, delay=3):
    """Create database indexes with retry logic for Atlas connection"""
    for attempt in range(max_retries):
        try:
            # Test connection first
            await client.admin.command('ping')
            logger.info(f"MongoDB connection successful (attempt {attempt + 1})")
            
            # Create indexes
            await db.users.create_index("email", unique=True)
            await db.users.create_index("username", unique=True)
            await db.categories.create_index([("user_id", 1), ("name", 1)])
            await db.search_results.create_index([("user_id", 1), ("url", 1)])
            await db.newsletters.create_index([("generated_at", -1)])
            logger.info("Database indexes created successfully")
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts")
                # Don't crash the app - indexes might already exist
                return False

# Create indexes on startup
@app.on_event("startup")
async def startup_db_client():
    await create_indexes_with_retry()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
