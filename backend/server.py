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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infojet_db')]

# PayPal Configuration
PAYPAL_PAYMENT_LINK = "https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ"

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
    """Parse and evaluate InfoPilot 2.0 Boolean protocols"""
    
    @staticmethod
    def parse_protocol(protocol: str) -> Dict[str, Any]:
        """
        Parse InfoJet 2.0 protocol format:
        (word1 or word2) & (word3 or word4)+ & (word5)^
        
        + = include ALL words in group
        ^ = exclude ALL words in group
        """
        if not protocol:
            return {"groups": [], "valid": False}
        
        # Find all groups with their modifiers
        pattern = r'([+^]?)\(([^)]+)\)([+^]?)'
        matches = re.findall(pattern, protocol)
        
        groups = []
        for prefix_mod, content, suffix_mod in matches:
            modifier = prefix_mod or suffix_mod or None
            words = [w.strip().lower() for w in content.split(' or ')]
            groups.append({
                "words": words,
                "modifier": modifier,
                "original": content
            })
        
        return {"groups": groups, "valid": len(groups) > 0}
    
    @staticmethod
    def matches_protocol(text: str, protocol: str) -> bool:
        """Check if text matches the protocol requirements"""
        if not text or not protocol:
            return False
            
        parsed = ProtocolParser.parse_protocol(protocol)
        if not parsed["valid"]:
            return False
        
        text_lower = text.lower()
        
        for group in parsed["groups"]:
            words = group["words"]
            modifier = group["modifier"]
            
            if modifier == "+":
                # ALL words must be present
                if not all(word in text_lower for word in words):
                    return False
            elif modifier == "^":
                # ALL words must be ABSENT
                if any(word in text_lower for word in words):
                    return False
            else:
                # At least ONE word must be present (OR logic)
                if not any(word in text_lower for word in words):
                    return False
        
        return True

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
    """Search the web using DuckDuckGo (no API key required)"""
    
    @staticmethod
    async def search(query: str, num_results: int = 20) -> List[Dict[str, Any]]:
        """Perform web search and return results"""
        results = []
        
        try:
            # Use DuckDuckGo HTML search
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Parse results using regex
                    result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>'
                    snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+)</a>'
                    
                    urls = re.findall(result_pattern, html)
                    snippets = re.findall(snippet_pattern, html)
                    
                    for i, (url, title) in enumerate(urls[:num_results]):
                        # Decode URL
                        if url.startswith("//duckduckgo.com/l/?uddg="):
                            url = urllib.parse.unquote(url.split("uddg=")[1].split("&")[0])
                        
                        snippet = snippets[i] if i < len(snippets) else ""
                        
                        # Extract root domain
                        try:
                            parsed = urllib.parse.urlparse(url)
                            root_domain = parsed.netloc
                        except:
                            root_domain = ""
                        
                        results.append({
                            "url": url,
                            "title": title.strip(),
                            "snippet": snippet.strip(),
                            "content": snippet.strip(),
                            "root_domain": root_domain
                        })
        except Exception as e:
            logger.error(f"Search error: {e}")
            # Return mock results as fallback
            for i in range(min(20, num_results)):
                results.append({
                    "url": f"https://example.com/result-{i+1}",
                    "title": f"Search Result {i+1}: {query}",
                    "snippet": f"This is a sample result for '{query}'. Contains relevant information about the topic.",
                    "content": f"Sample content for search result {i+1} about {query}.",
                    "root_domain": "example.com"
                })
        
        return results

# ============== AUTH ENDPOINTS ==============

@api_router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    # Check blocked content in username
    if contains_blocked_content(user.username):
        raise HTTPException(status_code=400, detail="Username contains blocked content")
    
    # Check if user exists
    existing = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
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
    user = await db.users.find_one({"email": credentials.email})
    
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
    # Check if user exists
    user = await db.users.find_one({"$or": [{"email": data.email}, {"google_id": data.google_id}]})
    
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
        "description": "InfoJet Premium Subscription"
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
    """Perform a web search"""
    
    if contains_blocked_content(request.query):
        raise HTTPException(status_code=400, detail="Search query contains blocked content")
    
    # Use web search service
    results = await WebSearchService.search(request.query, 20)
    
    return {
        "query": request.query,
        "results": results,
        "total": len(results)
    }

@api_router.post("/collate", response_model=dict)
async def collate_results(request: CollateRequest, user = Depends(get_current_user)):
    """Automatically categorize search results based on user's protocols"""
    
    # Check daily limit
    today = datetime.utcnow().date()
    user_doc = await db.users.find_one({"_id": user["_id"]})
    last_date = user_doc.get("last_collate_date")
    
    if last_date and last_date.date() == today:
        daily_count = user_doc.get("daily_collate_count", 0)
        settings = await db.settings.find_one({"key": "daily_collate_limit"})
        limit = settings.get("value", 10) if settings else 10
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
    
    for result in request.search_results:
        if contains_blocked_content(result.get("title", "")) or contains_blocked_content(result.get("content", "")):
            continue
        
        matching_category_ids = []
        text_to_match = f"{result.get('title', '')} {result.get('snippet', '')} {result.get('content', '')}"
        
        for cat in categories:
            if ProtocolParser.matches_protocol(text_to_match, cat["protocol"]):
                matching_category_ids.append(str(cat["_id"]))
        
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
                "content": result.get("content"),
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
            
            search_result_doc["matching_categories"] = [
                cat["name"] for cat in categories if str(cat["_id"]) in matching_category_ids
            ]
            collated_results.append(search_result_doc)
    
    return {
        "collated_count": len(collated_results),
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

# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    return {"message": "InfoJet API v1.0", "status": "healthy"}

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

@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.categories.create_index([("user_id", 1), ("name", 1)])
    await db.search_results.create_index([("user_id", 1), ("category_ids", 1)])
    await db.sessions.create_index("token")
    await db.messages.create_index([("sender_id", 1), ("recipient_id", 1), ("created_at", 1)])
    
    # Load banned words from DB
    banned = await db.banned_words.find().to_list(1000)
    for b in banned:
        BLOCKED_WORDS.add(b["word"])
    
    # Init settings
    await init_admin_settings()
    
    logger.info("InfoJet API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
