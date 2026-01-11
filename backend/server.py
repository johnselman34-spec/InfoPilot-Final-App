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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
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

# ============== BLOCKED WORDS FILTER ==============
BLOCKED_WORDS = {
    # Children-related (any language patterns)
    'child', 'children', 'kid', 'kids', 'boy', 'girl', 'teen', 'teenager',
    'young', 'minor', 'juvenile', 'youth', 'infant', 'toddler', 'baby',
    'underage', 'preteen', 'adolescent',
}

PROFANITY_WORDS = set()  # Admin can populate this

def contains_blocked_content(text: str) -> bool:
    """Check if text contains blocked words"""
    if not text:
        return False
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))
    return bool(words & BLOCKED_WORDS) or bool(words & PROFANITY_WORDS)

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
        """Check if text matches the protocol requirements - MORE LENIENT"""
        if not text or not protocol:
            return False
            
        parsed = ProtocolParser.parse_protocol(protocol)
        if not parsed["valid"]:
            # If protocol parsing fails, try simple keyword matching
            keywords = re.findall(r'\w+', protocol.lower())
            text_lower = text.lower()
            return any(kw in text_lower for kw in keywords if len(kw) >= 3)
        
        text_lower = ProtocolParser.normalize_text(text)
        
        for group in parsed["groups"]:
            items = group["items"]
            modifier = group["modifier"]
            
            if modifier == "+":
                # ALL items must be present (INCLUDE ALL)
                if not all(ProtocolParser.text_contains_item(text_lower, item) for item in items):
                    return False
            elif modifier == "^":
                # ALL items must be ABSENT (EXCLUDE ALL)
                if any(ProtocolParser.text_contains_item(text_lower, item) for item in items):
                    return False
            else:
                # At least ONE item must be present (OR logic)
                if not any(ProtocolParser.text_contains_item(text_lower, item) for item in items):
                    return False
        
        return True
    
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
    """
    
    @staticmethod
    async def search_duckduckgo(query: str, num_results: int = 50) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo HTML - with rate limit handling"""
        results = []
        try:
            # Just get first page to avoid rate limiting
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                    timeout=30.0
                )
                
                # Handle rate limiting - 202 means we need to wait
                if response.status_code == 202:
                    await asyncio.sleep(2)
                    response = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }, timeout=30.0)
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Parse results - improved regex
                    result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
                    snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+)</a>'
                    
                    urls = re.findall(result_pattern, html)
                    snippets = re.findall(snippet_pattern, html)
                    
                    for i, (url_match, title) in enumerate(urls):
                        # Decode DuckDuckGo redirect URL
                        actual_url = url_match
                        if "//duckduckgo.com/l/?uddg=" in url_match:
                            try:
                                actual_url = urllib.parse.unquote(url_match.split("uddg=")[1].split("&")[0])
                            except:
                                pass
                        
                        # Skip ads and duplicates
                        if "duckduckgo.com" in actual_url or any(r["url"] == actual_url for r in results):
                            continue
                        
                        snippet = snippets[i] if i < len(snippets) else ""
                        
                        # Extract root domain
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
                        
                        if len(results) >= num_results:
                            break
                    
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        return results[:num_results]
    
    @staticmethod
    async def search_bing_scrape(query: str, num_results: int = 30) -> List[Dict[str, Any]]:
        """Scrape Bing search results"""
        results = []
        try:
            for page in range(2):  # Get 2 pages
                encoded_query = urllib.parse.quote(query)
                first = page * 10 + 1
                url = f"https://www.bing.com/search?q={encoded_query}&first={first}"
                
                async with httpx.AsyncClient() as client:
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
                        
                        # Extract Bing result links
                        link_pattern = r'<a href="(https?://[^"]+)"[^>]*class="[^"]*tilk[^"]*"'
                        links = re.findall(link_pattern, html)
                        
                        # Also try alternative pattern
                        alt_pattern = r'<cite>([^<]+)</cite>'
                        cites = re.findall(alt_pattern, html)
                        
                        # Try to get titles
                        title_pattern = r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>([^<]+)</a></h2>'
                        titles = re.findall(title_pattern, html)
                        
                        for url, title in titles:
                            if not any(x in url for x in ['bing.com', 'microsoft.com', 'msn.com']):
                                if not any(r["url"] == url for r in results):
                                    try:
                                        parsed = urllib.parse.urlparse(url)
                                        root_domain = parsed.netloc
                                    except:
                                        root_domain = ""
                                    
                                    results.append({
                                        "url": url,
                                        "title": title.strip(),
                                        "snippet": "",
                                        "content": "",
                                        "root_domain": root_domain,
                                        "source": "bing"
                                    })
                
                if len(results) >= num_results:
                    break
                    
        except Exception as e:
            logger.error(f"Bing scrape error: {e}")
        
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
    async def search(query: str, num_results: int = 100) -> List[Dict[str, Any]]:
        """
        Perform web search using multiple sources
        Returns deduplicated results with content enrichment
        """
        all_results = []
        seen_urls = set()
        
        try:
            # Run primary searches in parallel
            ddg_task = WebSearchService.search_duckduckgo(query, 50)
            bing_task = WebSearchService.search_bing_scrape(query, 30)
            
            ddg_results, bing_results = await asyncio.gather(
                ddg_task, 
                bing_task,
                return_exceptions=True
            )
            
            # Process DuckDuckGo results
            if isinstance(ddg_results, list):
                for result in ddg_results:
                    if result["url"] not in seen_urls:
                        seen_urls.add(result["url"])
                        all_results.append(result)
                logger.info(f"DuckDuckGo returned {len(ddg_results)} results")
            else:
                logger.error(f"DuckDuckGo error: {ddg_results}")
            
            # Process Bing results
            if isinstance(bing_results, list):
                for result in bing_results:
                    if result["url"] not in seen_urls:
                        seen_urls.add(result["url"])
                        all_results.append(result)
                logger.info(f"Bing returned {len(bing_results)} results")
            else:
                logger.error(f"Bing error: {bing_results}")
            
        except Exception as e:
            logger.error(f"Search aggregation error: {e}")
        
        # Fetch content for results to improve protocol matching
        if all_results:
            batch_size = 10
            for i in range(0, min(len(all_results), 30), batch_size):
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
                    logger.debug(f"Content enrichment error: {e}")
        
        logger.info(f"Search for '{query}' returned {len(all_results)} results (with content enrichment)")
        return all_results[:num_results]
        
        return {"title": "", "description": "", "content": ""}
    
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
    
    # Use web search service - get LOTS of results for better protocol matching
    results = await WebSearchService.search(request.query, 100)
    
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
        {"key": "unpaid_max_pages", "value": 1, "description": "Max pages for unpaid users"},
        {"key": "daily_collate_limit", "value": 10, "description": "Max collations per day"},
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

# Book and App Marketing Content
BOOK_INFO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "genre": "Supernatural Thriller Comedy",
    "price": "$2.99",
    "amazon_url": "https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191",
    "reviews_url": "https://readersfavorite.com/book-review/letters-to-evelyn",
    "review_count": "19 Five-Star Professional Reviews",
    "featured_review": '"This memoir is a profound and unforgettable literary piece." - Dvine Zape, Readers\' Favorite',
    "description": "A supernatural thriller comedy that will keep you on the edge of your seat while making you laugh!"
}

APP_INFO = {
    "name": "InfoPilot",
    "tagline": "Your 3D View of the Internet",
    "description": "The world's most intelligent information exchange social network"
}

def get_fallback_newsletter():
    """Fallback newsletter if AI generation fails"""
    return {
        "content": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;">
<div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">

<h1 style="text-align: center; color: #764ba2; font-size: 32px;">
🚀 INFOPILOT WEEKLY BLAST! 🚀
</h1>

<p style="font-size: 18px; line-height: 1.8; color: #333;">
Hey there, Internet Explorer! (Not the browser, you're way cooler than that! 😎)
</p>

<p style="font-size: 16px; line-height: 1.8; color: #555;">
Did you know that while you were busy living your life, our robots were busy collating the ENTIRE internet for you? That's right - we're basically doing your homework while you Netflix and chill! 📺
</p>

<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; margin: 20px 0;">
<h2 style="color: white; text-align: center; margin: 0;">📚 BOOK OF THE CENTURY ALERT! 📚</h2>
<p style="color: white; text-align: center; font-size: 18px; margin: 10px 0;">
<strong>"Letters to Evelyn"</strong> by John Selman
</p>
<p style="color: white; text-align: center; font-style: italic;">
"This memoir is a profound and unforgettable literary piece." - Readers' Favorite
</p>
<p style="text-align: center;">
<a href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191" style="display: inline-block; background: white; color: #f5576c; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 18px;">
🎁 GET IT FOR JUST $2.99! 🎁
</a>
</p>
</div>

<div style="background: #1a1a2e; padding: 20px; border-radius: 15px; margin: 20px 0;">
<h2 style="color: #00ff88; text-align: center;">💎 PREMIUM MEMBERSHIP 💎</h2>
<p style="color: white; text-align: center;">
Pay what you want! Starting at just $0.75/year!<br>
<em>(That's less than a candy bar! And WAY better for your brain!)</em>
</p>
</div>

<p style="text-align: center; color: #888; font-size: 14px;">
Made with ❤️ and probably too much coffee ☕<br>
InfoPilot - Your 3D View of the Internet
</p>

</div>
</body>
</html>
""",
        "generated_at": datetime.now().isoformat(),
        "ai_generated": False
    }

async def generate_newsletter_content():
    """Generate AI-powered funny newsletter content using rich book data from manuscript"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.warning("No EMERGENT_LLM_KEY found, using fallback newsletter")
            return get_fallback_newsletter()
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"newsletter-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message="""You are a HYSTERICALLY FUNNY marketing genius writing newsletters for InfoPilot.
Your job is to create EXTREMELY FUNNY, laugh-out-loud emails that:
1. Make people laugh so hard they snort their coffee
2. Use absurd jokes, witty puns, and clever wordplay  
3. Sell the book "Letters to Evelyn" using the ACTUAL review quotes and manuscript content provided
4. Promote InfoPilot subscriptions
5. Be so entertaining people FORWARD it to friends
6. Use emojis liberally to make text POP
7. Create urgency and FOMO (Fear Of Missing Out)
8. Reference the book's wild plot: Navy pilot, hallucinations, aliens, love story, supernatural comedy
9. The humor should be WARM, WITTY, and WELCOMING - not mean-spirited
You must output complete HTML email with inline styles. Be WILD and CREATIVE!"""
        ).with_model("openai", "gpt-4o")
        
        # Get recent activity stats
        total_users = await db.users.count_documents({})
        total_results = await db.search_results.count_documents({})
        total_categories = await db.categories.count_documents({})
        
        # Rotate through different book advertisement images
        import random
        book_images = [
            "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/3wggnw99_Letters%20to%20Evelyn%20advertisement%201.jpg",
            "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/obecjep4_Letters%20to%20Evelyn%20advertisement%202.jpg",
            "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/63ydb5j8_Letters%20to%20Evelyn%20advertisement%203.jpg",
            "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/8ss0c1fe_Letters%20to%20Evelyn%20advertisement%204.jpg"
        ]
        selected_image = random.choice(book_images)
        
        # Funny taglines to rotate
        funny_taglines = [
            "The book that makes your therapist jealous!",
            "50+ jokes that hit harder than a Navy jet landing!",
            "Warning: May cause uncontrollable giggling in public places",
            "Finally, a love story with ACTUAL aliens! Take that, romance novels!",
            "Part Navy memoir, part alien encounter, ALL hilarious!",
            "The only book where you'll laugh, cry, AND question reality!",
            "Dave Chappelle wishes he wrote this! (The author's words, not ours... okay maybe ours too)",
        ]
        selected_tagline = random.choice(funny_taglines)
        
        prompt = f"""Write an absolutely HILARIOUS weekly newsletter HTML email for InfoPilot users!

STATS THIS WEEK:
- Total Users: {total_users}
- Search Results Collated: {total_results}  
- Categories Created: {total_categories}

===== BOOK PROMOTION (THIS IS THE STAR!) =====
📚 "LETTERS TO EVELYN" by John Selman
- A True Supernatural Thriller Comedy Memoir
- Price: ONLY $2.99 on Amazon Kindle (cheaper than a fancy coffee!)
- Has 57 reviews on Amazon, 5.0 out of 5 stars!
- 19 PROFESSIONAL Five-Star Reviews from Readers' Favorite
- "{selected_tagline}"

FROM THE ACTUAL MANUSCRIPT (use these for authenticity!):
- The author was a Navy ROTC top student who dreamed of flying like his father
- His stepmother Lauren poisoned his food with LSD, causing 10+ months of hallucinations
- He holds a WORLD RECORD for the steepest Sarajevo Approach in a T-34C aircraft!
- He writes beautiful love letters to a mysterious woman named Evelyn Tuskegee
- The book contains "upwards of 50 finely-crafted deafening, zany, zesty, zoo zingers... JOKES!"
- Author's own claim: "More funny than Dave Chappelle or your money back!"
- Contains extraterrestrial encounters and a "phantasmagoria of disconnected thoughts"
- The author survived a U.S. Northeast endurance record of 12+ days without sleep after being poisoned!

ACTUAL PROFESSIONAL REVIEW QUOTES (use 2-3):
★ "This memoir is a profound and unforgettable literary piece." - Divine Zape, Readers' Favorite
★ "Mind-bending." - Luwi Nyakansaila, Readers' Favorite
★ "Exceedingly brilliant." - Paul Zeitsman, Readers' Favorite
★ "The author's imagination is off the charts." - Leslie Jones, Readers' Favorite
★ "Mind-blowing." - Doreen Chombu, Readers' Favorite
★ "Resonates on a visceral level." - Divine Zape
★ "Bold, strange, and very human." - Kindle Customer
★ "A captivating and thought-provoking memoir that defies genre conventions." - Ruffina Oserio
★ "A symphony of love and madness that transports readers to the furthest reaches of the human psyche." - Christian Sia

READER TESTIMONIALS FROM AMAZON:
★ "This book evoked a mixture of surprise and amusement... I felt lighter and reminded of the importance of not taking life too seriously." - Peter gale Carty
★ "I laughed, I paused to think, and at times I had to reread sections just to take it all in." - Kindle Customer
★ "Prepare to have a laugh every chapter, as betrayal unfolds maybe love." - Roshannae Dougal

BOOK THEMES TO REFERENCE:
- Love and cosmic connection to Evelyn
- Military service and following dreams
- Overcoming trauma with humor
- The search for meaning in a chaotic world
- Blending reality with the extraordinary

BOOK IMAGE TO INCLUDE:
<img src="{selected_image}" alt="Letters to Evelyn" style="max-width: 300px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">

Amazon Link: https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191

===== INFOPILOT SUBSCRIPTION =====
App subscription: Pay what you want! Starting at $0.75/year
(That's less than a single gumball from those fancy machines!)

===== STYLE REQUIREMENTS =====
- Use gradient backgrounds: purple (#7c3aed), pink (#ec4899), blue (#3b82f6)
- Make the book the HERO with a big featured section
- Include the book image prominently
- Create URGENCY ("Only a few people have discovered this gem!")
- Be ABSURD and SURREAL (match the book's vibe)
- Add a "Dad joke of the week" or fun recurring element
- Make buttons big and colorful
- Sign off as "Your Friends at InfoPilot"
- Keep it fun and warm - we want people to ENJOY opening these emails!

Output ONLY the complete HTML email with inline styles. No markdown code blocks!"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return {
            "content": response,
            "generated_at": datetime.now().isoformat(),
            "ai_generated": True
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

# Create indexes
@app.on_event("startup")
async def startup_db_client():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.categories.create_index([("user_id", 1), ("name", 1)])
    await db.search_results.create_index([("user_id", 1), ("url", 1)])
    await db.newsletters.create_index([("generated_at", -1)])
    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
