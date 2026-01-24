"""
InfoPilot Explorer - Complete Backend Server
A worldwide web information exchange social network providing users a 3D view of the internet.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import uuid
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import hashlib
from bs4 import BeautifulSoup

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_explorer')]

# Create the main app
app = FastAPI(title="InfoPilot Explorer API", version="1.0.0")

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
categories_router = APIRouter(prefix="/categories", tags=["Categories"])
search_router = APIRouter(prefix="/search", tags=["Search"])
social_router = APIRouter(prefix="/social", tags=["Social"])
marketplace_router = APIRouter(prefix="/marketplace", tags=["Marketplace"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
stats_router = APIRouter(prefix="/stats", tags=["Statistics"])
chat_router = APIRouter(prefix="/chat", tags=["Chat"])
groups_router = APIRouter(prefix="/groups", tags=["Groups"])
pages_router = APIRouter(prefix="/pages", tags=["Pages"])
easter_eggs_router = APIRouter(prefix="/easter-eggs", tags=["Easter Eggs"])
newsletter_router = APIRouter(prefix="/newsletter", tags=["Newsletter"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= ENUMS =============
class DocumentType(str, Enum):
    INFORMATIVE_PHD = "Informative Ph.D"
    INFORMATIVE = "Informative"
    NEWS_ARTICLE = "News Article"
    BLOG = "Blog"
    FORUM = "Forum"
    PERSONAL_REPORT_ORGANIC = "Personal Report (Organic)"
    PERSONAL_REPORT_COLLECTED = "Personal Report (Collected)"
    INFOPILOT_EXCLUSIVE = "InfoPilot Exclusive"

class ReactionType(str, Enum):
    LIKE = "Like"
    LOVE = "Love"
    FUNNY = "Funny"
    SAD = "Sad"
    CAUTION = "Caution"
    SPAM = "Spam"
    BEST = "Best"

class SearchAggregation(str, Enum):
    AND_OR = "and_or"
    AND = "and"
    OR = "or"

# ============= MODELS =============

# User Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    picture: Optional[str] = None
    callsign: Optional[str] = None
    is_paid: bool = False
    is_admin: bool = False
    subscription_until: Optional[datetime] = None
    xp: int = 0
    level: int = 1
    streak: int = 0
    badges: List[Dict] = []
    stats: Dict = {}
    content_filter: str = "moderate"  # strict, moderate, off
    usp_public: bool = True
    friends_visible: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None

# Category Models
class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    category_id: str = Field(default_factory=lambda: f"cat_{uuid.uuid4().hex[:12]}")
    user_id: str
    name: str
    protocol: str
    parent_id: Optional[str] = None
    is_public: bool = True
    price: float = 0.0
    sales_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CategoryCreate(BaseModel):
    name: str
    protocol: str
    parent_id: Optional[str] = None
    is_public: bool = True
    price: float = 0.0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    protocol: Optional[str] = None
    is_public: Optional[bool] = None
    price: Optional[float] = None

# Search Result Models
class SearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    result_id: str = Field(default_factory=lambda: f"res_{uuid.uuid4().hex[:12]}")
    user_id: str
    url: str
    title: str
    snippet: str
    content: Optional[str] = None
    document_type: DocumentType = DocumentType.NEWS_ARTICLE
    category_ids: List[str] = []
    location: Optional[Dict] = None  # {city, state, country, lat, lng}
    year: Optional[int] = None
    root_domain: Optional[str] = None
    reactions: Dict[str, int] = {}
    comments_count: int = 0
    collated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Protocol Parser
class ProtocolParser:
    """InfoJet 2.0 Protocol Language Parser"""
    
    @staticmethod
    def parse_protocol(protocol: str) -> Dict:
        """Parse a protocol string into structured search terms"""
        # Replace 'and' with '&' for consistency
        protocol = re.sub(r'\band\b', '&', protocol, flags=re.IGNORECASE)
        
        # Split by & to get groups
        groups = [g.strip() for g in protocol.split('&') if g.strip()]
        
        result = {
            "include_groups": [],
            "exclude_groups": [],
            "all_terms": []
        }
        
        for group in groups:
            is_exclude = False
            is_include = False
            
            # Check for modifiers
            if group.startswith('^') or group.endswith('^'):
                is_exclude = True
                group = group.replace('^', '').strip()
            elif group.startswith('+') or group.endswith('+'):
                is_include = True
                group = group.replace('+', '').strip()
            
            # Extract terms from parentheses
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
        
        # Check exclusions first
        for exclude_group in parsed["exclude_groups"]:
            for term in exclude_group:
                if term.lower() in text_lower:
                    return False
        
        # Check inclusions - all groups must have at least one match
        for include_group in parsed["include_groups"]:
            group_matched = False
            for term in include_group:
                if term.lower() in text_lower:
                    group_matched = True
                    break
            if not group_matched:
                return False
        
        return True

# Document Type Classifier
class DocumentClassifier:
    """Classify documents based on content"""
    
    @staticmethod
    async def get_settings():
        """Get classification settings from admin"""
        settings = await db.settings.find_one({"key": "doc_classification"}, {"_id": 0})
        return settings.get("value", {}) if settings else {}
    
    @staticmethod
    async def classify(content: str, title: str = "", url: str = "") -> DocumentType:
        """Classify document type based on content and rules"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        settings = await DocumentClassifier.get_settings()
        
        # Check for Ph.D indicators
        phd_count = sum([
            content_lower.count(term) for term in ['ph.d.', 'phd', 'd.phil.', 'dr.']
        ])
        word_count = len(content.split())
        min_phd_words = settings.get("phd_min_words", 1500)
        min_phd_mentions = settings.get("phd_min_mentions", 3)
        
        if phd_count >= min_phd_mentions and word_count >= min_phd_words:
            return DocumentType.INFORMATIVE_PHD
        
        # Check for Forum
        if 'forum' in title_lower:
            return DocumentType.FORUM
        
        # Check for Blog
        blog_count = content_lower.count('blog')
        if blog_count >= 3 and 'blog' in title_lower:
            return DocumentType.BLOG
        
        # Check for News Article
        news_terms = ['news', 'story', 'news story']
        news_count = sum([content_lower.count(term) for term in news_terms])
        if news_count > 3:
            return DocumentType.NEWS_ARTICLE
        
        # Check for Personal Report (Collected)
        # Count 'I' outside of quotes
        i_count = len(re.findall(r'\bI\b(?!["\'])', content))
        if i_count >= 3:
            # Check paragraph length
            paragraphs = content.split('\n\n')
            for p in paragraphs:
                if len(p.split()) >= 75 and p.count('I ') >= 3:
                    return DocumentType.PERSONAL_REPORT_COLLECTED
        
        # Check for Informative content
        informative_protocol = settings.get("informative_protocol", 
            "(there are or there is) & (may have or might have or that are)")
        if ProtocolParser.matches_protocol(content, informative_protocol):
            return DocumentType.INFORMATIVE
        
        return DocumentType.NEWS_ARTICLE

# Location Extractor
class LocationExtractor:
    """Extract location information from text"""
    
    US_STATES = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming"
    ]
    
    COUNTRIES = [
        "United States", "USA", "UK", "United Kingdom", "Canada", "Australia",
        "Germany", "France", "Italy", "Spain", "Japan", "China", "India",
        "Brazil", "Mexico", "Russia", "South Korea", "Netherlands", "Sweden",
        "Switzerland", "Nicaragua", "Costa Rica", "Panama"
    ]
    
    @staticmethod
    def extract_locations(text: str) -> List[Dict]:
        """Extract all locations found in text"""
        locations = []
        text_lower = text.lower()
        
        # Check for US states
        for state in LocationExtractor.US_STATES:
            if state.lower() in text_lower:
                locations.append({
                    "type": "state",
                    "name": state,
                    "country": "United States"
                })
        
        # Check for countries
        for country in LocationExtractor.COUNTRIES:
            if country.lower() in text_lower:
                locations.append({
                    "type": "country",
                    "name": country
                })
        
        # Check for partial locations like "Northern Virginia"
        partial_patterns = [
            (r'northern\s+(\w+)', 'Northern'),
            (r'southern\s+(\w+)', 'Southern'),
            (r'eastern\s+(\w+)', 'Eastern'),
            (r'western\s+(\w+)', 'Western')
        ]
        
        for pattern, prefix in partial_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if match.title() in LocationExtractor.US_STATES:
                    locations.append({
                        "type": "region",
                        "name": f"{prefix} {match.title()}",
                        "state": match.title(),
                        "country": "United States"
                    })
        
        return locations

# ============= AUTHENTICATION =============

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token"""
    # Try cookie first
    session_token = request.cookies.get("session_token")
    
    # Then try Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        return None
    
    # Find session
    session = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session:
        return None
    
    # Check expiry
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        return None
    
    # Get user
    user_doc = await db.users.find_one(
        {"user_id": session["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(request: Request) -> User:
    """Require authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(request: Request) -> User:
    """Require admin user"""
    user = await require_auth(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ============= AUTH ROUTES =============

@auth_router.post("/session")
async def create_session(request: Request, response: Response):
    """Create session from Emergent OAuth session_id"""
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Exchange session_id for user data
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            user_data = resp.json()
        except Exception as e:
            logger.error(f"OAuth error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Create or update user
    existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": user_data["name"],
                "picture": user_data.get("picture")
            }}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "is_paid": False,
            "is_admin": user_data["email"] == "jjspilot24@gmail.com",
            "xp": 0,
            "level": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
    
    # Create session
    session_token = user_data.get("session_token", f"sess_{uuid.uuid4().hex}")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@auth_router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current user"""
    return user.model_dump()

@auth_router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}

# ============= CATEGORIES ROUTES =============

@categories_router.get("")
async def get_categories(
    user_id: Optional[str] = None,
    public_only: bool = False,
    request: Request = None
):
    """Get categories"""
    query = {}
    
    if user_id:
        query["user_id"] = user_id
    elif public_only:
        query["is_public"] = True
    
    categories = await db.categories.find(query, {"_id": 0}).to_list(1000)
    return {"categories": categories}

@categories_router.post("")
async def create_category(
    category: CategoryCreate,
    user: User = Depends(require_auth)
):
    """Create a new category"""
    # Validate protocol syntax
    if not category.protocol:
        raise HTTPException(status_code=400, detail="Protocol required")
    
    # Check for banned words
    banned = await db.settings.find_one({"key": "banned_words"}, {"_id": 0})
    banned_words = banned.get("value", []) if banned else []
    
    for word in banned_words:
        if word.lower() in category.name.lower() or word.lower() in category.protocol.lower():
            raise HTTPException(status_code=400, detail=f"Content contains banned word: {word}")
    
    cat_dict = category.model_dump()
    cat_dict["category_id"] = f"cat_{uuid.uuid4().hex[:12]}"
    cat_dict["user_id"] = user.user_id
    cat_dict["sales_count"] = 0
    cat_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    cat_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.categories.insert_one(cat_dict)
    
    # Add XP for creating category
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"xp": 10}}
    )
    
    # Return without the MongoDB _id
    cat_dict.pop("_id", None)
    return cat_dict

@categories_router.put("/{category_id}")
async def update_category(
    category_id: str,
    update: CategoryUpdate,
    user: User = Depends(require_auth)
):
    """Update a category"""
    category = await db.categories.find_one(
        {"category_id": category_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.categories.update_one(
        {"category_id": category_id},
        {"$set": update_dict}
    )
    
    updated = await db.categories.find_one({"category_id": category_id}, {"_id": 0})
    return updated

@categories_router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Delete a category"""
    result = await db.categories.delete_one({
        "category_id": category_id,
        "user_id": user.user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted"}

@categories_router.post("/{category_id}/clean")
async def clean_category(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Delete all search results for a category"""
    result = await db.search_results.delete_many({
        "user_id": user.user_id,
        "category_ids": category_id
    })
    
    return {"message": f"Deleted {result.deleted_count} results"}

# ============= SEARCH ROUTES =============

@search_router.post("/collate")
async def search_and_collate(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_auth)
):
    """Search using DuckDuckGo and collate results into categories"""
    data = await request.json()
    query = data.get("query", "")
    category_ids = data.get("category_ids", [])
    max_results = min(data.get("max_results", 40), 100)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query required")
    
    # Get user's categories
    categories = await db.categories.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(500)
    
    if category_ids:
        categories = [c for c in categories if c["category_id"] in category_ids]
    
    # Search using DuckDuckGo
    try:
        from ddgs import DDGS
        ddgs = DDGS(timeout=20)
        search_results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=503, detail="Search service temporarily unavailable")
    
    # Process and collate results
    collated_results = []
    
    for result in search_results:
        url = result.get("href", "")
        title = result.get("title", "")
        snippet = result.get("body", "")
        combined_text = f"{title} {snippet}"
        
        # Extract domain
        domain_match = re.search(r'https?://([^/]+)', url)
        root_domain = domain_match.group(1) if domain_match else ""
        
        # Find matching categories
        matching_cats = []
        for cat in categories:
            if ProtocolParser.matches_protocol(combined_text, cat["protocol"]):
                matching_cats.append(cat["category_id"])
        
        if matching_cats:
            # Classify document type
            doc_type = await DocumentClassifier.classify(snippet, title, url)
            
            # Extract locations
            locations = LocationExtractor.extract_locations(combined_text)
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', combined_text)
            year = int(year_match.group()) if year_match else None
            
            result_doc = {
                "result_id": f"res_{uuid.uuid4().hex[:12]}",
                "user_id": user.user_id,
                "url": url,
                "title": title,
                "snippet": snippet,
                "document_type": doc_type.value,
                "category_ids": matching_cats,
                "locations": locations,
                "year": year,
                "root_domain": root_domain,
                "reactions": {},
                "collated_at": datetime.now(timezone.utc).isoformat()
            }
            
            collated_results.append(result_doc)
    
    # Save to database
    if collated_results:
        await db.search_results.insert_many(collated_results)
        # Remove _id from results for JSON serialization
        for r in collated_results:
            r.pop("_id", None)
    
    # Add XP
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"xp": len(collated_results)}}
    )
    
    return {
        "total_searched": len(search_results),
        "total_collated": len(collated_results),
        "results": collated_results
    }

@search_router.get("/results")
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
    user: User = Depends(require_auth)
):
    """Get search results with filters"""
    query: Dict[str, Any] = {"user_id": user.user_id}
    
    if category_ids:
        cat_list = category_ids.split(",")
        if aggregation == SearchAggregation.AND:
            query["category_ids"] = {"$all": cat_list}
        elif aggregation == SearchAggregation.OR:
            query["category_ids"] = {"$in": cat_list}
        else:  # AND_OR
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
    
    results = await db.search_results.find(query, {"_id": 0})\
        .sort("collated_at", -1)\
        .skip(skip)\
        .limit(limit)\
        .to_list(limit)
    
    total = await db.search_results.count_documents(query)
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@search_router.get("/quick")
async def quick_search(
    q: str,
    user: User = Depends(require_auth)
):
    """Quick text search in collated database"""
    results = await db.search_results.find(
        {
            "user_id": user.user_id,
            "$text": {"$search": q}
        },
        {"_id": 0, "score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(50).to_list(50)
    
    return {"results": results}

# ============= SOCIAL ROUTES =============

@social_router.post("/friends/request")
async def send_friend_request(
    request: Request,
    user: User = Depends(require_auth)
):
    """Send friend request"""
    data = await request.json()
    friend_user_id = data.get("user_id")
    
    if not friend_user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    
    if friend_user_id == user.user_id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    
    # Check if already friends or pending
    existing = await db.friends.find_one({
        "$or": [
            {"user_id_1": user.user_id, "user_id_2": friend_user_id},
            {"user_id_1": friend_user_id, "user_id_2": user.user_id}
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already exists")
    
    await db.friends.insert_one({
        "friendship_id": f"friend_{uuid.uuid4().hex[:12]}",
        "user_id_1": user.user_id,
        "user_id_2": friend_user_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Friend request sent"}

@social_router.post("/friends/accept")
async def accept_friend_request(
    request: Request,
    user: User = Depends(require_auth)
):
    """Accept friend request"""
    data = await request.json()
    friendship_id = data.get("friendship_id")
    
    result = await db.friends.update_one(
        {"friendship_id": friendship_id, "user_id_2": user.user_id, "status": "pending"},
        {"$set": {"status": "accepted"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    return {"message": "Friend request accepted"}

@social_router.get("/friends")
async def get_friends(user: User = Depends(require_auth)):
    """Get user's friends"""
    friends = await db.friends.find(
        {
            "$or": [
                {"user_id_1": user.user_id},
                {"user_id_2": user.user_id}
            ],
            "status": "accepted"
        },
        {"_id": 0}
    ).to_list(500)
    
    # Get friend user details
    friend_ids = []
    for f in friends:
        if f["user_id_1"] == user.user_id:
            friend_ids.append(f["user_id_2"])
        else:
            friend_ids.append(f["user_id_1"])
    
    friend_users = await db.users.find(
        {"user_id": {"$in": friend_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "callsign": 1}
    ).to_list(500)
    
    return {"friends": friend_users}

@social_router.post("/reactions")
async def add_reaction(
    request: Request,
    user: User = Depends(require_auth)
):
    """Add reaction to search result"""
    data = await request.json()
    result_id = data.get("result_id")
    reaction_type = data.get("reaction_type")
    
    if reaction_type not in [r.value for r in ReactionType]:
        raise HTTPException(status_code=400, detail="Invalid reaction type")
    
    await db.search_results.update_one(
        {"result_id": result_id},
        {"$inc": {f"reactions.{reaction_type}": 1}}
    )
    
    # Store individual reaction
    await db.reactions.insert_one({
        "reaction_id": f"react_{uuid.uuid4().hex[:12]}",
        "result_id": result_id,
        "user_id": user.user_id,
        "reaction_type": reaction_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Reaction added"}

@social_router.post("/comments")
async def add_comment(
    request: Request,
    user: User = Depends(require_auth)
):
    """Add comment to search result"""
    data = await request.json()
    result_id = data.get("result_id")
    content = data.get("content")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content required")
    
    comment = {
        "comment_id": f"com_{uuid.uuid4().hex[:12]}",
        "result_id": result_id,
        "user_id": user.user_id,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.comments.insert_one(comment)
    comment.pop("_id", None)
    
    # Update comment count
    await db.search_results.update_one(
        {"result_id": result_id},
        {"$inc": {"comments_count": 1}}
    )
    
    return comment

@social_router.get("/comments/{result_id}")
async def get_comments(result_id: str):
    """Get comments for a search result"""
    comments = await db.comments.find(
        {"result_id": result_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"comments": comments}

# ============= MARKETPLACE ROUTES =============

@marketplace_router.get("/protocols")
async def get_marketplace_protocols(
    page: int = 1,
    limit: int = 20
):
    """Get public protocols for sale"""
    skip = (page - 1) * limit
    
    protocols = await db.categories.find(
        {"is_public": True, "price": {"$gt": 0}},
        {"_id": 0}
    ).sort("sales_count", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get creator info
    for protocol in protocols:
        creator = await db.users.find_one(
            {"user_id": protocol["user_id"]},
            {"_id": 0, "name": 1, "callsign": 1}
        )
        protocol["creator"] = creator
    
    total = await db.categories.count_documents({"is_public": True, "price": {"$gt": 0}})
    
    return {
        "protocols": protocols,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@marketplace_router.post("/purchase")
async def purchase_protocol(
    request: Request,
    user: User = Depends(require_auth)
):
    """Purchase a protocol"""
    data = await request.json()
    category_id = data.get("category_id")
    
    protocol = await db.categories.find_one(
        {"category_id": category_id, "is_public": True},
        {"_id": 0}
    )
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check if already purchased
    existing = await db.purchases.find_one({
        "user_id": user.user_id,
        "category_id": category_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already purchased")
    
    # Record purchase
    purchase = {
        "purchase_id": f"pur_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "category_id": category_id,
        "price": protocol["price"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.purchases.insert_one(purchase)
    
    # Update sales count
    await db.categories.update_one(
        {"category_id": category_id},
        {"$inc": {"sales_count": 1}}
    )
    
    return {"message": "Protocol purchased", "purchase": purchase}

@marketplace_router.post("/copy")
async def copy_protocol(
    request: Request,
    user: User = Depends(require_auth)
):
    """Copy a free protocol to user's categories"""
    data = await request.json()
    category_id = data.get("category_id")
    
    protocol = await db.categories.find_one(
        {"category_id": category_id, "is_public": True},
        {"_id": 0}
    )
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol["price"] > 0:
        raise HTTPException(status_code=400, detail="Protocol requires purchase")
    
    # Create copy for user
    new_category = {
        "category_id": f"cat_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "name": f"{protocol['name']} (Copy)",
        "protocol": protocol["protocol"],
        "parent_id": None,
        "is_public": False,
        "price": 0,
        "sales_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(new_category)
    
    # Track copy for leaderboard
    await db.protocol_copies.insert_one({
        "original_id": category_id,
        "copied_by": user.user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Protocol copied", "category": new_category}

@marketplace_router.get("/leaderboard")
async def get_leaderboard():
    """Get marketplace leaderboard"""
    # Top sellers
    top_sellers = await db.categories.aggregate([
        {"$match": {"is_public": True, "sales_count": {"$gt": 0}}},
        {"$group": {
            "_id": "$user_id",
            "total_sales": {"$sum": "$sales_count"},
            "total_revenue": {"$sum": {"$multiply": ["$price", "$sales_count"]}}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get user info for sellers
    for seller in top_sellers:
        user = await db.users.find_one(
            {"user_id": seller["_id"]},
            {"_id": 0, "name": 1, "callsign": 1}
        )
        seller["user"] = user
    
    # Most copied protocols
    most_copied = await db.protocol_copies.aggregate([
        {"$group": {"_id": "$original_id", "copy_count": {"$sum": 1}}},
        {"$sort": {"copy_count": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    for item in most_copied:
        protocol = await db.categories.find_one(
            {"category_id": item["_id"]},
            {"_id": 0, "name": 1, "user_id": 1}
        )
        item["protocol"] = protocol
    
    return {
        "top_sellers": top_sellers,
        "most_copied": most_copied
    }

# ============= STATISTICS ROUTES =============

@stats_router.get("/overview")
async def get_stats_overview(user: User = Depends(require_auth)):
    """Get statistics overview"""
    # Count results by document type
    doc_type_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user.user_id}},
        {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
    ]).to_list(20)
    
    # Count results by country
    country_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user.user_id}},
        {"$unwind": "$locations"},
        {"$match": {"locations.country": {"$exists": True}}},
        {"$group": {"_id": "$locations.country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # Count results by state
    state_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user.user_id}},
        {"$unwind": "$locations"},
        {"$match": {"locations.state": {"$exists": True}}},
        {"$group": {"_id": "$locations.state", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # Count results by root domain
    domain_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user.user_id}},
        {"$group": {"_id": "$root_domain", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # Top 10 most used words (basic word frequency)
    # This is simplified - real implementation would use text analysis
    
    # Count by year
    year_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user.user_id, "year": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(50)
    
    total_results = await db.search_results.count_documents({"user_id": user.user_id})
    total_categories = await db.categories.count_documents({"user_id": user.user_id})
    
    return {
        "total_results": total_results,
        "total_categories": total_categories,
        "by_document_type": doc_type_stats,
        "by_country": country_stats,
        "by_state": state_stats,
        "by_domain": domain_stats,
        "by_year": year_stats
    }

@stats_router.get("/map-data")
async def get_map_data(
    category_ids: Optional[str] = None,
    worldwide: bool = False,
    user: User = Depends(require_auth)
):
    """Get location data for map visualization"""
    query: Dict[str, Any] = {}
    
    if not worldwide:
        query["user_id"] = user.user_id
    
    if category_ids:
        query["category_ids"] = {"$in": category_ids.split(",")}
    
    results = await db.search_results.find(
        {**query, "locations": {"$exists": True, "$ne": []}},
        {"_id": 0, "result_id": 1, "title": 1, "url": 1, "locations": 1, "category_ids": 1}
    ).limit(1000).to_list(1000)
    
    return {"locations": results}

# ============= GROUPS ROUTES =============

@groups_router.get("")
async def get_groups(
    search: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Get groups"""
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    groups = await db.groups.find(query, {"_id": 0}).to_list(100)
    return {"groups": groups}

@groups_router.post("")
async def create_group(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a group"""
    data = await request.json()
    
    group = {
        "group_id": f"grp_{uuid.uuid4().hex[:12]}",
        "name": data.get("name"),
        "description": data.get("description", ""),
        "owner_id": user.user_id,
        "members": [user.user_id],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.groups.insert_one(group)
    return group

@groups_router.post("/{group_id}/join")
async def join_group(
    group_id: str,
    user: User = Depends(require_auth)
):
    """Join a group"""
    result = await db.groups.update_one(
        {"group_id": group_id},
        {"$addToSet": {"members": user.user_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "Joined group"}

@groups_router.post("/{group_id}/post")
async def create_group_post(
    group_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a post in a group"""
    data = await request.json()
    
    # Verify membership
    group = await db.groups.find_one(
        {"group_id": group_id, "members": user.user_id},
        {"_id": 0}
    )
    
    if not group:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    post = {
        "post_id": f"post_{uuid.uuid4().hex[:12]}",
        "group_id": group_id,
        "author_id": user.user_id,
        "content": data.get("content"),
        "reactions": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.posts.insert_one(post)
    return post

@groups_router.get("/{group_id}/posts")
async def get_group_posts(
    group_id: str,
    user: User = Depends(require_auth)
):
    """Get posts in a group"""
    posts = await db.posts.find(
        {"group_id": group_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get author info
    for post in posts:
        author = await db.users.find_one(
            {"user_id": post["author_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        post["author"] = author
    
    return {"posts": posts}

# ============= PAGES ROUTES =============

@pages_router.get("")
async def get_pages(
    search: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Get pages"""
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    pages = await db.pages.find(query, {"_id": 0}).to_list(100)
    return {"pages": pages}

@pages_router.post("")
async def create_page(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a page"""
    data = await request.json()
    
    page = {
        "page_id": f"page_{uuid.uuid4().hex[:12]}",
        "name": data.get("name"),
        "description": data.get("description", ""),
        "owner_id": user.user_id,
        "followers": [user.user_id],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.pages.insert_one(page)
    return page

@pages_router.post("/{page_id}/follow")
async def follow_page(
    page_id: str,
    user: User = Depends(require_auth)
):
    """Follow a page"""
    result = await db.pages.update_one(
        {"page_id": page_id},
        {"$addToSet": {"followers": user.user_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return {"message": "Following page"}

# ============= CHAT ROUTES =============

@chat_router.get("/conversations")
async def get_conversations(user: User = Depends(require_auth)):
    """Get user's conversations"""
    conversations = await db.conversations.find(
        {"user_ids": user.user_id},
        {"_id": 0}
    ).sort("last_message_at", -1).to_list(50)
    
    # Get other user info
    for conv in conversations:
        other_ids = [uid for uid in conv["user_ids"] if uid != user.user_id]
        if other_ids:
            other_user = await db.users.find_one(
                {"user_id": other_ids[0]},
                {"_id": 0, "name": 1, "picture": 1}
            )
            conv["other_user"] = other_user
    
    return {"conversations": conversations}

@chat_router.post("/messages")
async def send_message(
    request: Request,
    user: User = Depends(require_auth)
):
    """Send a message"""
    data = await request.json()
    recipient_id = data.get("recipient_id")
    content = data.get("content")
    
    if not recipient_id or not content:
        raise HTTPException(status_code=400, detail="recipient_id and content required")
    
    # Find or create conversation
    user_ids = sorted([user.user_id, recipient_id])
    conversation = await db.conversations.find_one(
        {"user_ids": {"$all": user_ids}},
        {"_id": 0}
    )
    
    if not conversation:
        conversation = {
            "conversation_id": f"conv_{uuid.uuid4().hex[:12]}",
            "user_ids": user_ids,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_message_at": datetime.now(timezone.utc).isoformat()
        }
        await db.conversations.insert_one(conversation)
    
    # Create message
    message = {
        "message_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conversation_id": conversation["conversation_id"],
        "sender_id": user.user_id,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message)
    
    # Update conversation
    await db.conversations.update_one(
        {"conversation_id": conversation["conversation_id"]},
        {"$set": {"last_message_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return message

@chat_router.get("/messages/{conversation_id}")
async def get_messages(
    conversation_id: str,
    user: User = Depends(require_auth)
):
    """Get messages in a conversation"""
    # Verify access
    conversation = await db.conversations.find_one(
        {"conversation_id": conversation_id, "user_ids": user.user_id},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)
    
    return {"messages": messages}

@chat_router.post("/rooms")
async def create_chat_room(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a chat room"""
    data = await request.json()
    
    room = {
        "room_id": f"room_{uuid.uuid4().hex[:12]}",
        "name": data.get("name"),
        "description": data.get("description", ""),
        "owner_id": user.user_id,
        "members": [user.user_id],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_rooms.insert_one(room)
    return room

@chat_router.get("/rooms")
async def get_chat_rooms(
    search: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Get chat rooms"""
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    rooms = await db.chat_rooms.find(query, {"_id": 0}).to_list(100)
    return {"rooms": rooms}

# ============= EASTER EGGS ROUTES =============

EASTER_EGG_JOKES = [
    "Why did the protocol cross the search engine? To get to the other database!",
    "I told my protocol it was looking sharp today. It replied with a perfectly parsed boolean.",
    "My stepmother tried to poison me, but jokes on her - I became a bestselling author!",
    "What do you call a protocol that tells jokes? A fun-ction!",
    "I asked the Internet Robot for advice. It said 'Have you tried turning your search strategy off and on again?'",
    "Why don't protocols ever get invited to parties? They're too exclusive... or inclusive... depends on the modifier!",
    "My search results were so good, even Google was jealous.",
    "InfoPilot: Because sometimes you need a pilot to navigate the information superhighway.",
    "What's a protocol's favorite music? Boolean beats!",
    "I wrote a protocol so good, it collated itself."
]

@easter_eggs_router.get("")
async def get_easter_eggs(user: User = Depends(require_auth)):
    """Get available easter eggs"""
    eggs = await db.easter_eggs.find({}, {"_id": 0}).to_list(50)
    
    if not eggs:
        # Initialize default easter eggs
        default_eggs = [
            {
                "egg_id": f"egg_{i}",
                "type": "joke",
                "content": joke,
                "reward_type": "xp",
                "reward_amount": 5,
                "times_found": 0
            }
            for i, joke in enumerate(EASTER_EGG_JOKES)
        ]
        await db.easter_eggs.insert_many(default_eggs)
        eggs = default_eggs
    
    return {"easter_eggs": eggs}

@easter_eggs_router.post("/discover")
async def discover_easter_egg(
    request: Request,
    user: User = Depends(require_auth)
):
    """Discover an easter egg"""
    data = await request.json()
    egg_id = data.get("egg_id")
    
    # Check if already discovered
    existing = await db.user_discoveries.find_one({
        "user_id": user.user_id,
        "egg_id": egg_id
    })
    
    if existing:
        return {"message": "Already discovered", "first_time": False}
    
    # Record discovery
    await db.user_discoveries.insert_one({
        "user_id": user.user_id,
        "egg_id": egg_id,
        "discovered_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Update egg count
    await db.easter_eggs.update_one(
        {"egg_id": egg_id},
        {"$inc": {"times_found": 1}}
    )
    
    # Get egg and reward user
    egg = await db.easter_eggs.find_one({"egg_id": egg_id}, {"_id": 0})
    
    if egg and egg.get("reward_type") == "xp":
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$inc": {"xp": egg.get("reward_amount", 5)}}
        )
    
    return {"message": "Easter egg discovered!", "egg": egg, "first_time": True}

@easter_eggs_router.get("/laugh-stats")
async def get_laugh_stats(user: User = Depends(require_auth)):
    """Get laugh-o-meter stats"""
    stats = await db.laugh_stats.aggregate([
        {"$group": {
            "_id": "$egg_id",
            "total_laughs": {"$sum": 1},
            "avg_rating": {"$avg": "$rating"}
        }},
        {"$sort": {"total_laughs": -1}}
    ]).to_list(50)
    
    return {"stats": stats}

@easter_eggs_router.post("/laugh")
async def record_laugh(
    request: Request,
    user: User = Depends(require_auth)
):
    """Record a laugh for the laugh-o-meter"""
    data = await request.json()
    
    await db.laugh_stats.insert_one({
        "user_id": user.user_id,
        "egg_id": data.get("egg_id"),
        "rating": data.get("rating", 5),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Laugh recorded!"}

# ============= ADMIN ROUTES =============

@admin_router.get("/settings")
async def get_admin_settings(user: User = Depends(require_admin)):
    """Get all admin settings"""
    settings = await db.settings.find({}, {"_id": 0}).to_list(100)
    return {"settings": settings}

@admin_router.put("/settings/{key}")
async def update_setting(
    key: str,
    request: Request,
    user: User = Depends(require_admin)
):
    """Update an admin setting"""
    data = await request.json()
    
    await db.settings.update_one(
        {"key": key},
        {"$set": {"value": data.get("value"), "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"message": "Setting updated"}

@admin_router.get("/analytics")
async def get_analytics(user: User = Depends(require_admin)):
    """Get application analytics"""
    total_users = await db.users.count_documents({})
    paid_users = await db.users.count_documents({"is_paid": True})
    total_categories = await db.categories.count_documents({})
    total_results = await db.search_results.count_documents({})
    total_purchases = await db.purchases.count_documents({})
    
    # User signups over time
    user_signups = await db.users.aggregate([
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$toDate": "$created_at"}}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 30}
    ]).to_list(30)
    
    return {
        "total_users": total_users,
        "paid_users": paid_users,
        "total_categories": total_categories,
        "total_results": total_results,
        "total_purchases": total_purchases,
        "user_signups": user_signups
    }

@admin_router.post("/ban-user")
async def ban_user(
    request: Request,
    user: User = Depends(require_admin)
):
    """Ban a user"""
    data = await request.json()
    user_id = data.get("user_id")
    reason = data.get("reason", "")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_banned": True, "ban_reason": reason}}
    )
    
    # End their sessions
    await db.user_sessions.delete_many({"user_id": user_id})
    
    return {"message": "User banned"}

@admin_router.post("/ban-word")
async def ban_word(
    request: Request,
    user: User = Depends(require_admin)
):
    """Add a banned word"""
    data = await request.json()
    word = data.get("word")
    
    await db.settings.update_one(
        {"key": "banned_words"},
        {"$addToSet": {"value": word.lower()}},
        upsert=True
    )
    
    return {"message": "Word banned"}

@admin_router.get("/users")
async def get_users(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    user: User = Depends(require_admin)
):
    """Get all users"""
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"callsign": {"$regex": search, "$options": "i"}}
        ]
    
    skip = (page - 1) * limit
    users = await db.users.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents(query)
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@admin_router.put("/doc-type-settings")
async def update_doc_type_settings(
    request: Request,
    user: User = Depends(require_admin)
):
    """Update document classification settings"""
    data = await request.json()
    
    await db.settings.update_one(
        {"key": "doc_classification"},
        {"$set": {"value": data, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"message": "Document type settings updated"}

# ============= NEWSLETTER ROUTES =============

@newsletter_router.get("/headlines")
async def get_headlines():
    """Get latest AI-generated headlines"""
    headlines = await db.headlines.find({}, {"_id": 0})\
        .sort("created_at", -1)\
        .limit(10)\
        .to_list(10)
    
    return {"headlines": headlines}

@newsletter_router.post("/subscribe")
async def subscribe_newsletter(
    request: Request,
    user: User = Depends(require_auth)
):
    """Subscribe to newsletter"""
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"newsletter_subscribed": True}}
    )
    
    return {"message": "Subscribed to newsletter"}

# ============= PERSONAL REPORTS =============

@api_router.post("/personal-reports")
async def create_personal_report(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a personal report"""
    data = await request.json()
    
    report = {
        "report_id": f"rep_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "title": data.get("title"),
        "content": data.get("content"),
        "images": data.get("images", [])[:3],  # Max 3 images
        "location": data.get("location"),
        "category_ids": data.get("category_ids", []),
        "document_type": DocumentType.PERSONAL_REPORT_ORGANIC.value,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.personal_reports.insert_one(report)
    
    # Add XP
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"xp": 20}}
    )
    
    return report

@api_router.get("/personal-reports")
async def get_personal_reports(
    user_id: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_auth)
):
    """Get personal reports"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    
    skip = (page - 1) * limit
    reports = await db.personal_reports.find(query, {"_id": 0})\
        .sort("created_at", -1)\
        .skip(skip)\
        .limit(limit)\
        .to_list(limit)
    
    total = await db.personal_reports.count_documents(query)
    
    return {
        "reports": reports,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

# ============= USER SEARCH =============

@api_router.get("/users/search")
async def search_users(
    q: str,
    user: User = Depends(require_auth)
):
    """Search for users"""
    # Only paid users are searchable
    users = await db.users.find(
        {
            "is_paid": True,
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
                {"callsign": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "callsign": 1}
    ).limit(20).to_list(20)
    
    return {"users": users}

# ============= PROTOCOL TEMPLATES =============

@api_router.get("/templates")
async def get_templates(user: User = Depends(require_auth)):
    """Get protocol templates"""
    templates = await db.protocol_templates.find(
        {"$or": [{"user_id": user.user_id}, {"is_public": True}]},
        {"_id": 0}
    ).to_list(100)
    
    return {"templates": templates}

@api_router.post("/templates")
async def create_template(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a protocol template"""
    data = await request.json()
    
    template = {
        "template_id": f"tmpl_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "name": data.get("name"),
        "protocol": data.get("protocol"),
        "is_public": data.get("is_public", False),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.protocol_templates.insert_one(template)
    return template

# ============= PROTOCOL DEBUGGER =============

@api_router.post("/debug-protocol")
async def debug_protocol(request: Request):
    """Debug a protocol string"""
    data = await request.json()
    protocol = data.get("protocol", "")
    test_text = data.get("test_text", "")
    
    parsed = ProtocolParser.parse_protocol(protocol)
    matches = ProtocolParser.matches_protocol(test_text, protocol)
    
    return {
        "parsed": parsed,
        "matches": matches,
        "protocol": protocol,
        "test_text": test_text[:200] if test_text else ""
    }

# ============= RECOMMENDATIONS =============

@api_router.get("/recommendations/protocols")
async def get_protocol_recommendations(user: User = Depends(require_auth)):
    """Get AI-powered protocol recommendations"""
    # Get user's existing categories
    user_categories = await db.categories.find(
        {"user_id": user.user_id},
        {"_id": 0, "name": 1, "protocol": 1}
    ).to_list(50)
    
    # Get popular public protocols the user doesn't have
    user_protocols = [c["protocol"] for c in user_categories]
    
    recommendations = await db.categories.find(
        {
            "is_public": True,
            "protocol": {"$nin": user_protocols},
            "sales_count": {"$gt": 0}
        },
        {"_id": 0}
    ).sort("sales_count", -1).limit(10).to_list(10)
    
    return {"recommendations": recommendations}

# ============= ROOT ENDPOINT =============

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "InfoPilot Explorer API",
        "version": "1.0.0",
        "description": "World Wide Web Information Exchange Social Network"
    }

@api_router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ============= INCLUDE ROUTERS =============

api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(search_router)
api_router.include_router(social_router)
api_router.include_router(marketplace_router)
api_router.include_router(admin_router)
api_router.include_router(stats_router)
api_router.include_router(chat_router)
api_router.include_router(groups_router)
api_router.include_router(pages_router)
api_router.include_router(easter_eggs_router)
api_router.include_router(newsletter_router)

app.include_router(api_router)

# ============= CORS =============

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= STARTUP/SHUTDOWN =============

@app.on_event("startup")
async def startup_db():
    """Initialize database indexes"""
    try:
        # Create text index for search
        await db.search_results.create_index([
            ("title", "text"),
            ("snippet", "text")
        ])
        
        # Create other indexes
        await db.users.create_index("user_id", unique=True)
        await db.users.create_index("email", unique=True)
        await db.categories.create_index("category_id", unique=True)
        await db.categories.create_index("user_id")
        await db.search_results.create_index("user_id")
        await db.search_results.create_index("category_ids")
        
        # Initialize default settings
        default_settings = [
            {"key": "subscription_price", "value": 0.99},
            {"key": "results_per_page", "value": 20},
            {"key": "unpaid_page_limit", "value": 3},
            {"key": "max_collation_results", "value": 40},
            {"key": "max_subcategory_levels", "value": 10},
            {"key": "banned_words", "value": []},
            {"key": "doc_classification", "value": {
                "phd_min_words": 1500,
                "phd_min_mentions": 3,
                "informative_protocol": "(there are or there is) & (may have or might have)"
            }}
        ]
        
        for setting in default_settings:
            await db.settings.update_one(
                {"key": setting["key"]},
                {"$setOnInsert": setting},
                upsert=True
            )
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection"""
    client.close()
