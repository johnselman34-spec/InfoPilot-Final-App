from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Body, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import secrets
import re
import io
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import asyncio
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="InfoPilot Explorer API", description="Complete Information Exchange Platform - Top Pilot Enterprises, Inc.")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# Scheduler for newsletters
scheduler = AsyncIOScheduler()

# ============ MODELS ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    ultimate_search_name: Optional[str] = None
    is_admin: bool = False
    is_paid: bool = False
    subscription_type: Optional[str] = None
    laughter_points: int = 0
    easter_eggs_caught: int = 0
    theme_settings: Dict = Field(default_factory=lambda: {"mode": "dark", "preset": "cosmic"})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CategoryCreate(BaseModel):
    name: str
    protocol: str
    parent_id: Optional[str] = None
    is_public: bool = True
    price: Optional[float] = None

class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    protocol: str
    parent_id: Optional[str] = None
    is_public: bool = True
    price: Optional[float] = None
    search_result_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    url: str
    title: str
    snippet: str
    content: Optional[str] = None
    category_ids: List[str] = []
    document_type: str = "News Article"
    location: Optional[Dict[str, float]] = None
    reactions: Dict[str, int] = Field(default_factory=lambda: {"like": 0, "love": 0, "funny": 0, "sad": 0, "caution": 0, "spam": 0, "best": 0})
    comments: List[Dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PersonalReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    images: List[str] = []
    location: Optional[Dict[str, float]] = None
    category_ids: List[str] = []
    document_type: str = "Personal Report (Organic)"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRoom(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    creator_id: str
    members: List[str] = []
    is_public: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    user_id: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Group(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    creator_id: str
    members: List[str] = []
    admins: List[str] = []
    is_public: bool = True
    cover_image: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Page(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    owner_id: str
    category: str
    followers: List[str] = []
    cover_image: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProtocolTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    protocol: str
    category_suggestion: str
    creator_id: Optional[str] = None
    is_official: bool = False
    usage_count: int = 0
    rating: float = 0.0
    price: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "admin_settings"
    collation_limit: int = 40
    max_category_depth: int = 100
    newsletter_times: List[str] = ["05:42", "08:37", "16:41"]
    newsletter_enabled: bool = True
    unpaid_user_max_price: Optional[float] = None
    price_controls_enabled: bool = False
    search_results_per_page: int = 20
    unpaid_max_pages: int = 3
    subscription_price_monthly: float = 1.00
    subscription_price_yearly: float = 9.98
    upgrade_message: str = "🚨 Pay-as-you-go promotion is only while supplies last! We're testing to see if our Business Model can sustain this incredible service. Google Maps API and AI Search subscriptions are expensive - thank you for supporting InfoPilot!"
    phd_protocol: str = "(Ph.D. or PhD or D.Phil. or Dr.)"
    phd_min_occurrences: int = 3
    phd_min_words: int = 1500
    informative_protocol: str = "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)"
    news_protocol: str = "(news) & (news or story or news story) & (news or story or news story)"
    news_min_occurrences: int = 3
    blog_min_occurrences: int = 3
    personal_report_min_i: int = 3
    personal_report_min_words: int = 75
    banned_words: List[str] = []
    theme_presets: Dict = Field(default_factory=lambda: {
        "cosmic": {"primary": "#fbbf24", "secondary": "#8b5cf6", "background": "#0f172a"},
        "royal": {"primary": "#3b82f6", "secondary": "#6366f1", "background": "#1e1b4b"},
        "hot": {"primary": "#ef4444", "secondary": "#f97316", "background": "#1c1917"},
        "ocean": {"primary": "#06b6d4", "secondary": "#0ea5e9", "background": "#0c4a6e"},
        "forest": {"primary": "#22c55e", "secondary": "#10b981", "background": "#14532d"},
        "sunset": {"primary": "#f59e0b", "secondary": "#ec4899", "background": "#431407"},
        "ruby": {"primary": "#dc2626", "secondary": "#be123c", "background": "#450a0a"}
    })

class NewsletterSignup(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    signup_type: str = "general"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    if not credentials:
        return None
    token = credentials.credentials
    session = await db.sessions.find_one({"token": token}, {"_id": 0})
    if not session:
        return None
    user = await db.users.find_one({"id": session["user_id"]}, {"_id": 0, "password_hash": 0})
    return user

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    user = await require_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ============ INFOJET 2.0 PROTOCOL PARSER ============

def parse_infojet_protocol(protocol: str) -> Dict:
    """Parse InfoJet 2.0 protocol string into structured format."""
    protocol = re.sub(r'\)\s+and\s+\(', ') & (', protocol, flags=re.IGNORECASE)
    protocol = re.sub(r'\)\s+AND\s+\(', ') & (', protocol)
    
    groups = []
    current_pos = 0
    
    while current_pos < len(protocol):
        start = protocol.find('(', current_pos)
        if start == -1:
            break
        end = protocol.find(')', start)
        if end == -1:
            break
        
        group_content = protocol[start+1:end]
        include_all = False
        exclude_all = False
        
        if start > 0 and protocol[start-1] in ['+', '^']:
            if protocol[start-1] == '+':
                include_all = True
            else:
                exclude_all = True
        
        if end + 1 < len(protocol) and protocol[end+1] in ['+', '^']:
            if protocol[end+1] == '+':
                include_all = True
            else:
                exclude_all = True
        
        words = [w.strip() for w in re.split(r'\s+or\s+', group_content, flags=re.IGNORECASE)]
        
        groups.append({
            "words": words,
            "include_all": include_all,
            "exclude_all": exclude_all
        })
        
        current_pos = end + 1
    
    return {"groups": groups}

def content_matches_protocol(content: str, protocol: str) -> tuple:
    """Check if content matches InfoJet 2.0 protocol. Returns (matches, score)."""
    content_lower = content.lower()
    parsed = parse_infojet_protocol(protocol)
    
    score = 0
    total_groups = len(parsed["groups"])
    matched_groups = 0
    
    for group in parsed["groups"]:
        if group["exclude_all"]:
            found_any = any(word.lower() in content_lower for word in group["words"])
            if found_any:
                return (False, 0)
            matched_groups += 1
        elif group["include_all"]:
            all_found = all(word.lower() in content_lower for word in group["words"])
            if not all_found:
                return (False, 0)
            matched_groups += 1
            score += len(group["words"])
        else:
            matches = [word for word in group["words"] if word.lower() in content_lower]
            if matches:
                matched_groups += 1
                score += len(matches)
    
    if matched_groups == total_groups and total_groups > 0:
        return (True, score)
    return (False, 0)

def classify_document_type(content: str, title: str, admin_settings: Dict) -> str:
    """Classify document type based on admin-defined protocols."""
    content_lower = content.lower()
    title_lower = title.lower()
    word_count = len(content.split())
    
    if 'forum' in title_lower:
        return "Forum"
    
    blog_count = content_lower.count('blog') + title_lower.count('blog')
    if blog_count >= admin_settings.get("blog_min_occurrences", 3) and 'blog' in title_lower:
        return "Blog"
    
    phd_protocol = admin_settings.get("phd_protocol", "(Ph.D. or PhD or D.Phil. or Dr.)")
    phd_matches, _ = content_matches_protocol(content, phd_protocol)
    phd_count = sum(1 for pattern in ['ph.d.', 'phd', 'd.phil.', 'dr.'] if pattern in content_lower)
    if phd_matches and phd_count >= admin_settings.get("phd_min_occurrences", 3) and word_count >= admin_settings.get("phd_min_words", 1500):
        return "PhD Informative"
    
    info_protocol = admin_settings.get("informative_protocol", "(there are or there is) & (may have or might have)")
    info_matches, _ = content_matches_protocol(content, info_protocol)
    if info_matches:
        return "Informative"
    
    i_count = len(re.findall(r'\bI\b', content))
    if i_count >= admin_settings.get("personal_report_min_i", 3) and word_count >= admin_settings.get("personal_report_min_words", 75):
        return "Personal Report (Collected)"
    
    news_protocol = admin_settings.get("news_protocol", "(news) & (news or story)")
    news_matches, _ = content_matches_protocol(content, news_protocol)
    news_count = content_lower.count('news')
    if news_matches or news_count >= admin_settings.get("news_min_occurrences", 3):
        return "News Article"
    
    return "News Article"

# ============ SEARCH ENGINE INTEGRATION ============

async def search_duckduckgo(query: str, max_results: int = 20) -> List[Dict]:
    """Search using DuckDuckGo via ddgs package."""
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "source": "DuckDuckGo"
                })
        logging.info(f"DuckDuckGo returned {len(results)} results for '{query}'")
        return results
    except Exception as e:
        logging.error(f"DuckDuckGo search error: {e}")
        return []

async def search_brave(query: str, max_results: int = 20) -> List[Dict]:
    """Search using Brave Search (requires API key in future)."""
    # Mock implementation - would need API key
    return []

async def search_all_engines(query: str, max_results: int = 40) -> List[Dict]:
    """Search across all available search engines."""
    all_results = []
    
    # DuckDuckGo (free, no API key needed)
    ddg_results = await search_duckduckgo(query, max_results)
    all_results.extend(ddg_results)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r["url"] and r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_results.append(r)
    
    return unique_results[:max_results]

# ============ LOCATION EXTRACTION ============

LOCATION_PATTERNS = {
    "New York": {"lat": 40.7128, "lng": -74.0060},
    "Los Angeles": {"lat": 34.0522, "lng": -118.2437},
    "Chicago": {"lat": 41.8781, "lng": -87.6298},
    "Houston": {"lat": 29.7604, "lng": -95.3698},
    "Phoenix": {"lat": 33.4484, "lng": -112.0740},
    "Philadelphia": {"lat": 39.9526, "lng": -75.1652},
    "San Antonio": {"lat": 29.4241, "lng": -98.4936},
    "San Diego": {"lat": 32.7157, "lng": -117.1611},
    "Dallas": {"lat": 32.7767, "lng": -96.7970},
    "San Francisco": {"lat": 37.7749, "lng": -122.4194},
    "Washington": {"lat": 38.9072, "lng": -77.0369},
    "Boston": {"lat": 42.3601, "lng": -71.0589},
    "Seattle": {"lat": 47.6062, "lng": -122.3321},
    "Denver": {"lat": 39.7392, "lng": -104.9903},
    "Atlanta": {"lat": 33.7490, "lng": -84.3880},
    "Miami": {"lat": 25.7617, "lng": -80.1918},
    "Brunswick": {"lat": 43.9145, "lng": -69.9653},
    "Maine": {"lat": 45.2538, "lng": -69.4455},
    "London": {"lat": 51.5074, "lng": -0.1278},
    "Paris": {"lat": 48.8566, "lng": 2.3522},
    "Tokyo": {"lat": 35.6762, "lng": 139.6503},
    "Berlin": {"lat": 52.5200, "lng": 13.4050},
    "Sydney": {"lat": -33.8688, "lng": 151.2093},
    "Gettysburg": {"lat": 39.8309, "lng": -77.2311},
    "Princeton": {"lat": 40.3573, "lng": -74.6672},
}

def extract_location(content: str) -> Optional[Dict[str, float]]:
    """Extract location from content using pattern matching."""
    content_lower = content.lower()
    for city, coords in LOCATION_PATTERNS.items():
        if city.lower() in content_lower:
            return coords
    return None

# ============ NEWSLETTER SYSTEM ============

async def send_newsletter():
    """Send newsletter to all subscribers."""
    try:
        subscribers = await db.newsletter_signups.find({}, {"_id": 0}).to_list(1000)
        if not subscribers:
            logging.info("No subscribers for newsletter")
            return
        
        # Get latest headlines
        headlines = await get_news_headlines_internal()
        
        # Log newsletter sending (actual email sending would require SMTP/SendGrid integration)
        newsletter_log = {
            "id": str(uuid.uuid4()),
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "subscriber_count": len(subscribers),
            "headlines_count": len(headlines),
            "status": "logged"  # Would be "sent" with real email integration
        }
        await db.newsletter_logs.insert_one(newsletter_log)
        
        logging.info(f"Newsletter logged for {len(subscribers)} subscribers")
    except Exception as e:
        logging.error(f"Newsletter error: {e}")

async def get_news_headlines_internal():
    """Get news headlines for newsletter."""
    return [
        {"title": "Global Climate Summit Reaches Historic Agreement", "category": "Environment"},
        {"title": "Breakthrough in Quantum Computing Achieved", "category": "Technology"},
        {"title": "New Economic Policy Announced by Federal Reserve", "category": "Economy"},
        {"title": "Medical Researchers Develop Revolutionary Treatment", "category": "Health"},
        {"title": "Space Agency Confirms New Exoplanet Discovery", "category": "Science"},
    ]

def schedule_newsletters():
    """Schedule newsletters based on admin settings."""
    # Default times: 5:42am, 8:37am, 4:41pm
    default_times = [("05", "42"), ("08", "37"), ("16", "41")]
    
    for hour, minute in default_times:
        scheduler.add_job(
            send_newsletter,
            CronTrigger(hour=int(hour), minute=int(minute)),
            id=f"newsletter_{hour}_{minute}",
            replace_existing=True
        )
    
    logging.info("Newsletter scheduler configured")

# ============ PAYPAL CONFIGURATION ============
PAYPAL_BUSINESS_EMAIL = "JJspilot24@gmail.com"
PAYPAL_INFOPILOT_LINK = "https://www.paypal.com/ncp/payment/LZDBN3SQU4NWQ"
PAYPAL_BOOK_LINK = "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU"
AMAZON_BOOK_LINK = "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J"

# ============ BOOK INFO ============
BOOK_INFO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "publisher": "John Selman Publications (A Top Pilot Enterprises, Inc. Company)",
    "genre": "True Supernatural Thriller Comedy",
    "description": "A True unbelievable Story! A True even more unforgettable Story! Man saves Universe with his Memoir!",
    "long_description": "Letters to Evelyn is a hysterically heartwarming journey on a hilarious roller coaster ride to the unwitting heavens! This Naval Aviation autobiography is just the ticket to profusely jocose 'entertainment value' involved with a flight student's hysterical quest, averting jealous murder attempts from his stepmother, to find his one true soulmate. With 70 finely-crafted, deafening, zany, zesty zoo zingers causing hurricane-force winds of laughter from the most skeptical of minds!",
    "isbn_ebook": "979-8-9985974-4-2",
    "isbn_paperback": "979-8-9985974-8-0",
    "isbn_hardcover": "979-8-9985974-9-7",
    "copyright": "© 2014 John Selman",
    "amazon_link": AMAZON_BOOK_LINK,
    "paypal_link": PAYPAL_BOOK_LINK,
    "review_count": 19,
    "review_source": "Readers' Favorite - 5 Star Reviews",
    "film_news": "Recently accepted by Voyage Media producer Ryan Heppe for production into a film. Heppe previously worked with Arnold Schwarzenegger and Bruce Willis!",
    "warnings": [
        "Not intended for use while operating a vehicle or heavy equipment - may cause distraction!",
        "Pregnant or breastfeeding individuals should avoid due to potential for 'uncontrollable hysterics and fits of laughter'",
        "Intended for adults only (26 years and older)",
        "Author is not responsible for health problems or damages associated with humor or profound material",
        "Contains 70+ jokes that may cause hurricane-force winds of laughter!"
    ],
    "professional_reviews": [
        {"quote": "Letters to Evelyn by John Selman is an extraordinary book with a unique plot that captivated me from the first chapter.", "author": "L. Jones", "source": "Readers' Favorite - 5 Stars"},
        {"quote": "The comical side of it is exceedingly brilliant, to the point that even when I wasn't busy reading, the story would creep into my mind, and I would start laughing abruptly.", "author": "Professional Reviewer", "source": "Readers' Favorite - 5 Stars"},
        {"quote": "John Selman delivers one of the most remarkable works I have ever read... Mind-bending. Exceedingly brilliant.", "author": "Professional Reviewer", "source": "Readers' Favorite - 5 Stars"}
    ]
}

BOOK_PRICES = {"ebook": 4.99, "paperback": 17.90, "hardcover": 24.99}

# ============ FOOD MENU ============
FOOD_MENU = [
    {
        "id": "beef-rouladen",
        "name": "German Beef Rouladen",
        "description": "deLectaBLe thin slices of tender beef rolled around pickles, onions, and mustard, slow-braised in rich dark brown gravy. Served with red cabbage and spätzle. The rolls feature bacon and dijon mustard inside, with noodles covered in dark brown gravy, peas and carrots!",
        "price": 18.99,
        "category": "main",
        "image": "beef-rouladen",
        "funny_tagline": "So luscious and tender, your grandmother in Germany will call to apologize!"
    },
    {
        "id": "veggie-rouladen",
        "name": "Vegetable Rouladen",
        "description": "Magnificent rolled vegetables stuffed with savory goodness, perfectly spiced and braised in dark brown/reddish gravy. Even carnivores will consider switching sides!",
        "price": 15.99,
        "category": "main",
        "image": "veggie-rouladen",
        "funny_tagline": "Plants have feelings too – delicious ones!"
    },
    {
        "id": "fish-chowder",
        "name": "Perfectly Spiced Fish Chowder",
        "description": "Fresh Atlantic white fish swimming in a creamy, perfectly spiced chowder with potatoes, bacon, and yellow onions. Straight from the Maine coast. Served with crusty bread!",
        "price": 14.99,
        "category": "soup",
        "image": "fish-chowder",
        "funny_tagline": "The only fish story that is 100% true and delicious!"
    },
    {
        "id": "pretzel",
        "name": "Giant Bavarian Pretzel",
        "description": "Freshly baked twisted beauty served with beer cheese and mustard. Warning: Size may cause jaw unhinging!",
        "price": 8.99,
        "category": "appetizer",
        "image": "pretzel",
        "funny_tagline": "Twisted like our sense of humor!"
    },
    {
        "id": "apple-strudel",
        "name": "Oma's Apple Strudel",
        "description": "Grandma's secret recipe with crispy phyllo, tender apples, and cinnamon. Served warm with vanilla sauce. May induce nostalgic tears!",
        "price": 7.99,
        "category": "dessert",
        "image": "apple-strudel",
        "funny_tagline": "Warning: Grandmother not included!"
    }
]

# ============ EASTER EGG JOKES ============
EASTER_EGG_CONTENT = [
    {
        "joke": "Why did John's stepmother put narcotics in his eggs? Because she couldn't stand the thought of him flying higher than her expectations! Spoiler: He survived, wrote a bestseller, and now SHE'S the one with egg on her face! 🥚",
        "protocol_idea": "(survival or resilience) & (family or relatives) & (triumph or success)",
        "pricing_suggestion": "$2.99 - Because surviving attempted murder by gourmet breakfast is priceless!"
    },
    {
        "joke": "January 3rd, 2000 - the day that proved eggs aren't just for breakfast anymore! Two and a half ounces of 'special seasoning' couldn't keep this pilot grounded. Now he's flying, writing, AND producing movies! Talk about a revenge served with a side of scrambled!",
        "protocol_idea": "(millennium or 2000 or new year) & (poisoning or narcotics or drugs)",
        "pricing_suggestion": "$1.99 - Cheaper than the therapy John didn't need!"
    },
    {
        "joke": "My stepmother tried military-grade psychological warfare narcotics on me. I responded by becoming a Hollywood movie producer. Who's laughing now? (Hint: It's me, all the way to the bank!) 💰",
        "protocol_idea": "(military or psychological or warfare) & (hollywood or movie or producer)",
        "pricing_suggestion": "$3.99 - Premium content for premium survivors!"
    },
    {
        "joke": "Pro tip: If someone serves you 'gourmet' eggs that taste completely normal but come from a spiteful stepmother, maybe grab a McMuffin instead. Just saying! 🍳",
        "protocol_idea": "(cooking or food or breakfast) & (safety or caution or warning)",
        "pricing_suggestion": "$0.99 - Safety tips should be accessible!"
    },
    {
        "joke": "The eggs were tasteless. The narcotics were military-grade. My survival was miraculous. My book sales? DELICIOUS! Check out 'Letters to Evelyn' - now with 100% less poisoning! 📚",
        "protocol_idea": "(book or memoir or autobiography) & (survival or recovery)",
        "pricing_suggestion": "$4.99 - The same price as the ebook that tells the whole story!"
    },
    {
        "joke": "Fun fact: John's stepmother failed at murder multiple times. He now has a 5-star reviewed book, a movie deal with Voyage Media, and this app. Some people just can't take a hint! 🌟",
        "protocol_idea": "(success or achievement or accomplishment) & (revenge or karma or justice)",
        "pricing_suggestion": "$2.49 - One for each failed attempt!"
    },
    {
        "joke": "What do you call surviving 2.5 ounces of concentrated military-grade narcotics hidden in eggs? A bad breakfast. What do you call turning it into a bestselling memoir? GENIUS! 🧠",
        "protocol_idea": "(genius or intelligent or smart) & (writing or memoir or story)",
        "pricing_suggestion": "$1.49 - Affordable inspiration!"
    },
    {
        "joke": "They say the best revenge is living well. John Selman said 'hold my beer' and added: bestselling author, movie producer, app developer, and food truck owner. His stepmother is still explaining herself! 🎬",
        "protocol_idea": "(revenge or success or living well) & (entrepreneur or business or ventures)",
        "pricing_suggestion": "$5.99 - For the full entrepreneurial protocol bundle!"
    }
]

MAP_INSTRUCTIONS = [
    "🗺️ Click on colored dots to see search results from around the world!",
    "🔍 Zoom in to discover local information categorized by your protocols!",
    "📍 Each dot color represents a different category - hover to preview!",
    "🌍 The Statistics screen shows ALL users' public results worldwide!",
    "👤 Your Ultimate Search page shows only YOUR categorized results!",
    "✅ Check multiple categories to filter combined results!"
]

# ============ PROTOCOL TEMPLATES ============
PROTOCOL_TEMPLATES = [
    {
        "id": "civil-war-heroes",
        "name": "American Civil War Heroes",
        "description": "Find articles about heroic figures from the American Civil War",
        "protocol": "(American civil war) & (hero or heroes or heroic) & (Gettysburg or battle or victory)",
        "category_suggestion": "History / American Civil War / Heroes",
        "is_official": True,
        "usage_count": 1250
    },
    {
        "id": "tech-innovations",
        "name": "Technology Innovations",
        "description": "Discover breakthrough technology and innovation news",
        "protocol": "(technology or tech) & (innovation or breakthrough or revolutionary) & (AI or artificial intelligence or machine learning or quantum)",
        "category_suggestion": "Technology / Innovations",
        "is_official": True,
        "usage_count": 2340
    },
    {
        "id": "health-research",
        "name": "Medical Research Papers",
        "description": "Find academic medical and health research",
        "protocol": "(medical or health or medicine) & (research or study or clinical trial) & (results or findings or conclusion)",
        "category_suggestion": "Science / Medical Research",
        "is_official": True,
        "usage_count": 1890
    },
    {
        "id": "climate-science",
        "name": "Climate Science Articles",
        "description": "Track climate change and environmental science news",
        "protocol": "(climate or environment or global warming) & (science or research or data) & (impact or effect or change)",
        "category_suggestion": "Science / Climate",
        "is_official": True,
        "usage_count": 1567
    },
    {
        "id": "space-exploration",
        "name": "Space Exploration News",
        "description": "Follow the latest in space exploration and astronomy",
        "protocol": "(space or NASA or SpaceX) & (mission or launch or discovery) & (Mars or Moon or asteroid or planet)",
        "category_suggestion": "Science / Space",
        "is_official": True,
        "usage_count": 2100
    },
    {
        "id": "business-startups",
        "name": "Startup & Business News",
        "description": "Track startup funding and business developments",
        "protocol": "(startup or company or business) & (funding or investment or valuation) & (million or billion or raised)",
        "category_suggestion": "Business / Startups",
        "is_official": True,
        "usage_count": 1780
    },
    {
        "id": "cooking-recipes",
        "name": "Recipe Finder",
        "description": "Find cooking recipes and culinary guides",
        "protocol": "(recipe or cooking or chef) & (ingredients or instructions or steps) & (minutes or hours or prep time)",
        "category_suggestion": "Lifestyle / Recipes",
        "is_official": True,
        "usage_count": 3200
    },
    {
        "id": "aviation-news",
        "name": "Aviation Industry News",
        "description": "Track aviation and aerospace industry developments",
        "protocol": "(aviation or airline or aircraft) & (flight or pilot or airport) & (Boeing or Airbus or FAA)",
        "category_suggestion": "Industry / Aviation",
        "is_official": True,
        "usage_count": 890
    }
]

# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {
        "message": "Welcome to InfoPilot Explorer API! 🚀",
        "app_name": "InfoPilot Explorer",
        "tagline": "First in Flight with Monetization of Searches! It's a Bear! 🐻",
        "company": "Top Pilot Enterprises, Inc.",
        "version": "2.0.0",
        "features": ["InfoJet 2.0 Protocol Search", "Ultimate Search Pages", "Interactive Maps", "Marketplace", "Easter Eggs", "Laughter Points"]
    }

# ============ AUTH ROUTES ============

@api_router.post("/auth/register")
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "username": user.username,
        "password_hash": hash_password(user.password),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "ultimate_search_name": user.username,
        "is_admin": False,
        "is_paid": False,
        "subscription_type": None,
        "laughter_points": 0,
        "easter_eggs_caught": 0,
        "friends": [],
        "theme_settings": {"mode": "dark", "preset": "cosmic"},
        "wallet_balance": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = generate_token()
    await db.sessions.insert_one({
        "token": token,
        "user_id": user_doc["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "token": token,
        "user": {k: v for k, v in user_doc.items() if k not in ["password_hash", "_id"]}
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or user.get("password_hash") != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = generate_token()
    await db.sessions.insert_one({
        "token": token,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "token": token,
        "user": {k: v for k, v in user.items() if k != "password_hash"}
    }

@api_router.get("/auth/me")
async def get_me(user: Dict = Depends(require_user)):
    return user

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials:
        await db.sessions.delete_one({"token": credentials.credentials})
    return {"message": "Logged out successfully"}

# ============ USER ROUTES ============

@api_router.get("/users/search")
async def search_users(q: str = Query(..., min_length=1), user: Dict = Depends(require_user)):
    """Search users by name, email, or username."""
    query = {
        "$or": [
            {"username": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"first_name": {"$regex": q, "$options": "i"}},
            {"last_name": {"$regex": q, "$options": "i"}},
            {"ultimate_search_name": {"$regex": q, "$options": "i"}}
        ]
    }
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(50)
    return {"users": users}

@api_router.put("/users/profile")
async def update_profile(updates: Dict = Body(...), user: Dict = Depends(require_user)):
    allowed_fields = ["first_name", "last_name", "ultimate_search_name"]
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}
    if filtered:
        await db.users.update_one({"id": user["id"]}, {"$set": filtered})
    updated = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    return updated

@api_router.put("/users/theme")
async def update_theme(theme_settings: Dict = Body(...), user: Dict = Depends(require_user)):
    """Update user's theme settings."""
    await db.users.update_one({"id": user["id"]}, {"$set": {"theme_settings": theme_settings}})
    return {"message": "Theme updated", "theme_settings": theme_settings}

@api_router.get("/users/{user_id}/public")
async def get_public_profile(user_id: str):
    """Get public profile of a user."""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0, "email": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ============ CATEGORY ROUTES ============

@api_router.post("/categories")
async def create_category(category: CategoryCreate, user: Dict = Depends(require_user)):
    cat_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": category.name,
        "protocol": category.protocol,
        "parent_id": category.parent_id,
        "is_public": category.is_public,
        "price": category.price,
        "search_result_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.categories.insert_one(cat_doc)
    return {k: v for k, v in cat_doc.items() if k != "_id"}

@api_router.get("/categories")
async def get_categories(user: Dict = Depends(require_user)):
    """Get user's categories with search result counts."""
    categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    for cat in categories:
        count = await db.search_results.count_documents({
            "user_id": user["id"],
            "category_ids": cat["id"]
        })
        cat["search_result_count"] = count
    
    return {"categories": categories}

@api_router.get("/categories/public")
async def get_public_categories():
    """Get all public categories for marketplace/statistics."""
    categories = await db.categories.find({"is_public": True}, {"_id": 0}).to_list(1000)
    return {"categories": categories}

@api_router.put("/categories/{category_id}")
async def update_category(category_id: str, updates: Dict = Body(...), user: Dict = Depends(require_user)):
    cat = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    
    allowed = ["name", "protocol", "is_public", "price", "parent_id"]
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if filtered:
        await db.categories.update_one({"id": category_id}, {"$set": filtered})
    
    updated = await db.categories.find_one({"id": category_id}, {"_id": 0})
    return updated

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user: Dict = Depends(require_user)):
    result = await db.categories.delete_one({"id": category_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await db.search_results.update_many(
        {"category_ids": category_id},
        {"$pull": {"category_ids": category_id}}
    )
    
    return {"message": "Category deleted"}

@api_router.post("/categories/{category_id}/clean")
async def clean_category(category_id: str, user: Dict = Depends(require_user)):
    """Delete all search results in a category."""
    cat = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await db.search_results.update_many(
        {"user_id": user["id"], "category_ids": category_id},
        {"$pull": {"category_ids": category_id}}
    )
    
    return {"message": f"Cleaned category: {cat['name']}"}

# ============ SEARCH & COLLATE ROUTES ============

@api_router.post("/search/collate")
async def collate_search(query: str = Body(..., embed=True), user: Dict = Depends(require_user)):
    """Search and Collate function - searches the internet and categorizes results."""
    admin_settings = await db.admin_settings.find_one({"id": "admin_settings"}) or {}
    collation_limit = admin_settings.get("collation_limit", 40)
    
    categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    # Search using real search engines
    search_results = await search_all_engines(query, collation_limit)
    
    if not search_results:
        # Fallback to mock data if search fails
        search_results = [
            {
                "url": f"https://example.com/article-{i}",
                "title": f"Article about {query} - Result {i}",
                "snippet": f"This is a detailed article about {query}. Contains valuable information about the topic including research, analysis, and expert opinions.",
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
    
    # Count categorized results
    categorized_count = sum(1 for r in categorized_results if r["category_ids"])
    
    return {
        "message": f"Collated {len(categorized_results)} results! {categorized_count} matched your protocols.",
        "results": categorized_results,
        "total_searched": len(search_results),
        "categorized": categorized_count
    }

@api_router.get("/search/results")
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
    
    if not user.get("is_paid"):
        max_pages = admin_settings.get("unpaid_max_pages", 3)
        if page > max_pages:
            raise HTTPException(status_code=403, detail=f"Upgrade to access more than {max_pages} pages!")
    
    query = {"user_id": user["id"]}
    
    if category_ids:
        cat_list = category_ids.split(",")
        if aggregation == "and":
            query["category_ids"] = {"$all": cat_list, "$size": len(cat_list)}
        elif aggregation == "or":
            query["category_ids"] = {"$in": cat_list}
        else:
            query["category_ids"] = {"$all": cat_list}
    
    if document_types:
        type_list = document_types.split(",")
        query["document_type"] = {"$in": type_list}
    
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query, {"_id": 0})\
        .sort("match_score", -1)\
        .skip((page - 1) * per_page)\
        .limit(per_page)\
        .to_list(per_page)
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@api_router.post("/search/results/{result_id}/react")
async def react_to_result(result_id: str, reaction: str = Body(..., embed=True), user: Dict = Depends(require_user)):
    """React to a search result."""
    valid_reactions = ["like", "love", "funny", "sad", "caution", "spam", "best"]
    if reaction not in valid_reactions:
        raise HTTPException(status_code=400, detail="Invalid reaction")
    
    await db.search_results.update_one(
        {"id": result_id},
        {"$inc": {f"reactions.{reaction}": 1}}
    )
    
    return {"message": f"Added {reaction} reaction!"}

@api_router.post("/search/results/{result_id}/comment")
async def comment_on_result(result_id: str, content: str = Body(..., embed=True), user: Dict = Depends(require_user)):
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

# ============ PERSONAL REPORTS ============

# Image upload directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

@api_router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), user: Dict = Depends(require_user)):
    """Upload an image and return its URL."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB allowed")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = UPLOADS_DIR / filename
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Return URL (relative path)
    image_url = f"/api/uploads/{filename}"
    
    return {"url": image_url, "filename": filename, "size": len(contents)}

@api_router.get("/uploads/{filename}")
async def get_uploaded_image(filename: str):
    """Serve uploaded images."""
    filepath = UPLOADS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    ext = filename.split(".")[-1].lower()
    content_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    content_type = content_types.get(ext, "image/jpeg")
    
    return StreamingResponse(open(filepath, "rb"), media_type=content_type)

@api_router.post("/reports")
async def create_personal_report(
    title: str = Body(...),
    content: str = Body(...),
    images: List[str] = Body(default=[]),
    location: Optional[Dict] = Body(default=None),
    category_ids: List[str] = Body(default=[]),
    user: Dict = Depends(require_user)
):
    """Create a Personal Report (Organic)."""
    if len(images) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 images allowed")
    
    report = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "title": title,
        "content": content,
        "images": images[:3],
        "location": location,
        "category_ids": category_ids,
        "document_type": "Personal Report (Organic)",
        "reactions": {"like": 0, "love": 0, "funny": 0, "sad": 0, "caution": 0, "spam": 0, "best": 0},
        "comments": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.personal_reports.insert_one(report)
    return {k: v for k, v in report.items() if k != "_id"}

@api_router.get("/reports")
async def get_personal_reports(user: Dict = Depends(require_user)):
    """Get user's personal reports."""
    reports = await db.personal_reports.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return {"reports": reports}

@api_router.put("/reports/{report_id}")
async def update_personal_report(report_id: str, updates: Dict = Body(...), user: Dict = Depends(require_user)):
    """Update a personal report."""
    report = await db.personal_reports.find_one({"id": report_id, "user_id": user["id"]})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    allowed = ["title", "content", "images", "location", "category_ids"]
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if filtered:
        await db.personal_reports.update_one({"id": report_id}, {"$set": filtered})
    
    updated = await db.personal_reports.find_one({"id": report_id}, {"_id": 0})
    return updated

@api_router.delete("/reports/{report_id}")
async def delete_personal_report(report_id: str, user: Dict = Depends(require_user)):
    """Delete a personal report."""
    result = await db.personal_reports.delete_one({"id": report_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted"}

# ============ CHAT ROOMS ============

@api_router.post("/chat/rooms")
async def create_chat_room(name: str = Body(...), description: str = Body(None), is_public: bool = Body(True), user: Dict = Depends(require_user)):
    """Create a new chat room."""
    room = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "creator_id": user["id"],
        "members": [user["id"]],
        "is_public": is_public,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_rooms.insert_one(room)
    return {k: v for k, v in room.items() if k != "_id"}

@api_router.get("/chat/rooms")
async def get_chat_rooms(user: Dict = Depends(require_user)):
    """Get available chat rooms."""
    query = {"$or": [{"is_public": True}, {"members": user["id"]}]}
    rooms = await db.chat_rooms.find(query, {"_id": 0}).to_list(100)
    return {"rooms": rooms}

@api_router.post("/chat/rooms/{room_id}/join")
async def join_chat_room(room_id: str, user: Dict = Depends(require_user)):
    """Join a chat room."""
    room = await db.chat_rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if user["id"] not in room.get("members", []):
        await db.chat_rooms.update_one({"id": room_id}, {"$push": {"members": user["id"]}})
    
    return {"message": "Joined room successfully"}

@api_router.post("/chat/rooms/{room_id}/messages")
async def send_chat_message(room_id: str, content: str = Body(..., embed=True), user: Dict = Depends(require_user)):
    """Send a message to a chat room."""
    room = await db.chat_rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    message = {
        "id": str(uuid.uuid4()),
        "room_id": room_id,
        "user_id": user["id"],
        "username": user.get("ultimate_search_name") or user["username"],
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one(message)
    return {k: v for k, v in message.items() if k != "_id"}

@api_router.get("/chat/rooms/{room_id}/messages")
async def get_chat_messages(room_id: str, limit: int = 50, user: Dict = Depends(require_user)):
    """Get messages from a chat room."""
    messages = await db.chat_messages.find({"room_id": room_id}, {"_id": 0})\
        .sort("created_at", -1)\
        .limit(limit)\
        .to_list(limit)
    return {"messages": list(reversed(messages))}

# ============ GROUPS ============

@api_router.post("/groups")
async def create_group(name: str = Body(...), description: str = Body(...), is_public: bool = Body(True), user: Dict = Depends(require_user)):
    """Create a new group."""
    group = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "creator_id": user["id"],
        "members": [user["id"]],
        "admins": [user["id"]],
        "is_public": is_public,
        "cover_image": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.groups.insert_one(group)
    return {k: v for k, v in group.items() if k != "_id"}

@api_router.get("/groups")
async def get_groups(user: Optional[Dict] = Depends(get_current_user)):
    """Get available groups."""
    query = {"is_public": True}
    if user:
        query = {"$or": [{"is_public": True}, {"members": user["id"]}]}
    groups = await db.groups.find(query, {"_id": 0}).to_list(100)
    return {"groups": groups}

@api_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user: Dict = Depends(require_user)):
    """Join a group."""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user["id"] not in group.get("members", []):
        await db.groups.update_one({"id": group_id}, {"$push": {"members": user["id"]}})
    
    return {"message": "Joined group successfully"}

@api_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user: Dict = Depends(require_user)):
    """Leave a group."""
    await db.groups.update_one({"id": group_id}, {"$pull": {"members": user["id"], "admins": user["id"]}})
    return {"message": "Left group"}

# ============ PAGES ============

@api_router.post("/pages")
async def create_page(name: str = Body(...), description: str = Body(...), category: str = Body(...), user: Dict = Depends(require_user)):
    """Create a new page."""
    page = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "owner_id": user["id"],
        "category": category,
        "followers": [],
        "cover_image": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.pages.insert_one(page)
    return {k: v for k, v in page.items() if k != "_id"}

@api_router.get("/pages")
async def get_pages():
    """Get all public pages."""
    pages = await db.pages.find({}, {"_id": 0}).to_list(100)
    return {"pages": pages}

@api_router.post("/pages/{page_id}/follow")
async def follow_page(page_id: str, user: Dict = Depends(require_user)):
    """Follow a page."""
    page = await db.pages.find_one({"id": page_id})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if user["id"] not in page.get("followers", []):
        await db.pages.update_one({"id": page_id}, {"$push": {"followers": user["id"]}})
    
    return {"message": "Now following page"}

# ============ PROTOCOL TEMPLATES ============

@api_router.get("/templates")
async def get_protocol_templates():
    """Get protocol templates gallery."""
    # Combine official templates with user-created ones
    official_templates = PROTOCOL_TEMPLATES
    
    user_templates = await db.protocol_templates.find({"is_official": False}, {"_id": 0}).to_list(100)
    
    return {
        "official_templates": official_templates,
        "community_templates": user_templates
    }

@api_router.post("/templates")
async def create_protocol_template(
    name: str = Body(...),
    description: str = Body(...),
    protocol: str = Body(...),
    category_suggestion: str = Body(...),
    price: Optional[float] = Body(None),
    user: Dict = Depends(require_user)
):
    """Create a new protocol template."""
    template = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "protocol": protocol,
        "category_suggestion": category_suggestion,
        "creator_id": user["id"],
        "creator_name": user["username"],
        "is_official": False,
        "usage_count": 0,
        "rating": 0.0,
        "price": price,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.protocol_templates.insert_one(template)
    return {k: v for k, v in template.items() if k != "_id"}

@api_router.post("/templates/{template_id}/use")
async def use_protocol_template(template_id: str, user: Dict = Depends(require_user)):
    """Track usage of a protocol template."""
    # Check official templates first
    official = next((t for t in PROTOCOL_TEMPLATES if t["id"] == template_id), None)
    if official:
        return {"template": official, "message": "Template retrieved"}
    
    # Check user templates
    template = await db.protocol_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.protocol_templates.update_one({"id": template_id}, {"$inc": {"usage_count": 1}})
    return {"template": template, "message": "Template usage tracked"}

# ============ EASTER EGGS ============

@api_router.get("/easter-eggs/random")
async def get_random_easter_egg(user: Optional[Dict] = Depends(get_current_user)):
    """Get a random Easter egg."""
    import random
    egg = random.choice(EASTER_EGG_CONTENT)
    instruction = random.choice(MAP_INSTRUCTIONS)
    
    return {"egg": {**egg, "map_instruction": instruction}}

@api_router.post("/easter-eggs/catch")
async def catch_easter_egg(egg_index: int = Body(..., embed=True), user: Dict = Depends(require_user)):
    """Catch an Easter egg and earn laughter points!"""
    if egg_index < 0 or egg_index >= len(EASTER_EGG_CONTENT):
        egg_index = 0
    
    egg = EASTER_EGG_CONTENT[egg_index]
    points = 10 + (egg_index * 5)
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$inc": {"laughter_points": points, "easter_eggs_caught": 1}}
    )
    
    catch_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "joke": egg["joke"],
        "protocol_idea": egg.get("protocol_idea"),
        "pricing_suggestion": egg.get("pricing_suggestion"),
        "laughter_points_earned": points,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.easter_egg_catches.insert_one(catch_doc)
    
    updated_user = await db.users.find_one({"id": user["id"]})
    
    return {
        "message": f"🥚 Easter Egg caught! +{points} Laughter Points!",
        "total_points": updated_user["laughter_points"],
        "egg": egg
    }

@api_router.get("/easter-eggs/catches")
async def get_user_catches(user: Dict = Depends(require_user)):
    """Get user's Easter egg catch history."""
    catches = await db.easter_egg_catches.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return {"catches": catches}

# ============ MARKETPLACE ============

@api_router.get("/marketplace/protocols")
async def get_marketplace_protocols(page: int = 1, category: Optional[str] = None):
    """Get protocols for sale in the marketplace."""
    query = {"is_public": True, "price": {"$ne": None, "$gt": 0}}
    if category:
        query["name"] = {"$regex": category, "$options": "i"}
    
    total = await db.categories.count_documents(query)
    protocols = await db.categories.find(query, {"_id": 0})\
        .sort("search_result_count", -1)\
        .skip((page - 1) * 20)\
        .limit(20)\
        .to_list(20)
    
    for p in protocols:
        owner = await db.users.find_one({"id": p["user_id"]}, {"_id": 0, "password_hash": 0, "email": 0})
        p["owner"] = owner
    
    return {"protocols": protocols, "total": total, "page": page}

@api_router.post("/marketplace/buy/{protocol_id}")
async def buy_protocol(protocol_id: str, user: Dict = Depends(require_user)):
    """Purchase a protocol from the marketplace."""
    protocol = await db.categories.find_one({"id": protocol_id, "is_public": True})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if not protocol.get("price") or protocol["price"] <= 0:
        raise HTTPException(status_code=400, detail="Protocol is not for sale")
    
    purchase = {
        "id": str(uuid.uuid4()),
        "buyer_id": user["id"],
        "seller_id": protocol["user_id"],
        "protocol_id": protocol_id,
        "protocol_name": protocol["name"],
        "price": protocol["price"],
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.purchases.insert_one(purchase)
    
    return {
        "message": "Redirecting to PayPal for payment...",
        "purchase_id": purchase["id"],
        "paypal_url": f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={PAYPAL_BUSINESS_EMAIL}&item_name={protocol['name']}&amount={protocol['price']}&currency_code=USD"
    }

# ============ REVENUE DASHBOARD ============

@api_router.get("/revenue/dashboard")
async def get_revenue_dashboard(user: Dict = Depends(require_user)):
    """Get revenue dashboard data."""
    # Get user's sales
    sales = await db.purchases.find({"seller_id": user["id"], "status": "completed"}, {"_id": 0}).to_list(1000)
    
    total_revenue = sum(s.get("price", 0) * 0.85 for s in sales)  # 85% to seller
    
    # Get monthly breakdown
    monthly_revenue = {}
    for sale in sales:
        month = sale["created_at"][:7]  # YYYY-MM
        monthly_revenue[month] = monthly_revenue.get(month, 0) + (sale["price"] * 0.85)
    
    # Get top selling protocols
    protocol_sales = {}
    for sale in sales:
        pid = sale["protocol_id"]
        if pid not in protocol_sales:
            protocol_sales[pid] = {"name": sale["protocol_name"], "count": 0, "revenue": 0}
        protocol_sales[pid]["count"] += 1
        protocol_sales[pid]["revenue"] += sale["price"] * 0.85
    
    top_protocols = sorted(protocol_sales.values(), key=lambda x: x["revenue"], reverse=True)[:10]
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_sales": len(sales),
        "monthly_revenue": monthly_revenue,
        "top_protocols": top_protocols,
        "wallet_balance": user.get("wallet_balance", 0)
    }

@api_router.get("/revenue/export")
async def export_revenue_pdf(format: str = "pdf", user: Dict = Depends(require_user)):
    """Export revenue report as PDF or CSV."""
    sales = await db.purchases.find({"seller_id": user["id"], "status": "completed"}, {"_id": 0}).to_list(1000)
    
    total_revenue = sum(s.get("price", 0) * 0.85 for s in sales)
    
    if format == "csv":
        # Create CSV content
        csv_content = "Date,Protocol,Price,Your Share (85%)\n"
        for sale in sales:
            csv_content += f"{sale['created_at'][:10]},{sale['protocol_name']},{sale['price']},{round(sale['price'] * 0.85, 2)}\n"
        csv_content += f"\n,TOTAL,{sum(s.get('price', 0) for s in sales)},{round(total_revenue, 2)}\n"
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=revenue_report_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    
    # Generate PDF using reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFillColor(HexColor("#fbbf24"))
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)
    
    c.setFillColor(HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "InfoPilot Explorer")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Revenue Report - {user['username']}")
    
    # Date
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 10)
    c.drawString(width - 150, height - 50, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Summary section
    y = height - 120
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Revenue Summary")
    
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Total Sales: {len(sales)}")
    y -= 20
    c.drawString(50, y, f"Gross Revenue: ${sum(s.get('price', 0) for s in sales):.2f}")
    y -= 20
    c.drawString(50, y, f"Your Earnings (85%): ${total_revenue:.2f}")
    y -= 20
    c.drawString(50, y, f"Platform Fee (15%): ${sum(s.get('price', 0) for s in sales) * 0.15:.2f}")
    
    # Sales table
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Sales Details")
    
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Date")
    c.drawString(150, y, "Protocol")
    c.drawString(400, y, "Price")
    c.drawString(480, y, "Your Share")
    
    c.line(50, y - 5, width - 50, y - 5)
    
    y -= 20
    c.setFont("Helvetica", 10)
    for sale in sales[-20:]:  # Last 20 sales
        if y < 100:
            c.showPage()
            y = height - 50
        c.drawString(50, y, sale.get("created_at", "")[:10])
        c.drawString(150, y, sale.get("protocol_name", "Unknown")[:35])
        c.drawString(400, y, f"${sale.get('price', 0):.2f}")
        c.drawString(480, y, f"${sale.get('price', 0) * 0.85:.2f}")
        y -= 18
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(50, 30, "Top Pilot Enterprises, Inc. - First in Flight with Monetization of Searches!")
    c.drawString(width - 100, 30, "It's a Bear! 🐻")
    
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=revenue_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )

# ============ MAP DATA ============

@api_router.get("/map/data")
async def get_map_data(scope: str = "personal", user: Optional[Dict] = Depends(get_current_user)):
    """Get location data for map visualization."""
    query = {"location": {"$ne": None}}
    
    if scope == "personal" and user:
        query["user_id"] = user["id"]
    
    results = await db.search_results.find(query, {"_id": 0}).to_list(1000)
    
    # Also include personal reports
    if user:
        report_query = {"location": {"$ne": None}}
        if scope == "personal":
            report_query["user_id"] = user["id"]
        reports = await db.personal_reports.find(report_query, {"_id": 0}).to_list(500)
        results.extend(reports)
    
    # Group by approximate location
    locations = {}
    for r in results:
        loc = r.get("location")
        if loc:
            key = f"{loc['lat']:.2f},{loc['lng']:.2f}"
            if key not in locations:
                locations[key] = {
                    "lat": loc["lat"],
                    "lng": loc["lng"],
                    "results": [],
                    "categories": set()
                }
            locations[key]["results"].append({
                "id": r.get("id"),
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": r.get("snippet", r.get("content", ""))[:200],
                "document_type": r.get("document_type"),
                "category_ids": r.get("category_ids", [])
            })
            locations[key]["categories"].update(r.get("category_ids", []))
    
    # Convert to list with category colors
    category_colors = {}
    color_palette = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899"]
    
    map_points = []
    for key, data in locations.items():
        # Assign color based on first category
        cat_ids = list(data["categories"])
        color = "#6b7280"  # Default gray
        if cat_ids:
            first_cat = cat_ids[0]
            if first_cat not in category_colors:
                category_colors[first_cat] = color_palette[len(category_colors) % len(color_palette)]
            color = category_colors[first_cat]
        
        map_points.append({
            "lat": data["lat"],
            "lng": data["lng"],
            "result_count": len(data["results"]),
            "category_count": len(data["categories"]),
            "category_ids": list(data["categories"]),
            "color": color,
            "results": data["results"][:10]  # First 10 for preview
        })
    
    return {"points": map_points, "category_colors": category_colors}

# ============ LEADERBOARD ============

@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get community leaderboard."""
    top_laughter = await db.users.find({}, {"_id": 0, "password_hash": 0, "email": 0})\
        .sort("laughter_points", -1)\
        .limit(10)\
        .to_list(10)
    
    pipeline = [
        {"$match": {"is_public": True}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "total_results": {"$sum": "$search_result_count"}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_creators_agg = await db.categories.aggregate(pipeline).to_list(10)
    
    top_creators = []
    for tc in top_creators_agg:
        user = await db.users.find_one({"id": tc["_id"]}, {"_id": 0, "password_hash": 0, "email": 0})
        if user:
            top_creators.append({
                "user": user,
                "protocol_count": tc["count"],
                "total_results": tc["total_results"]
            })
    
    return {
        "top_laughter_points": top_laughter,
        "top_protocol_creators": top_creators
    }

# ============ ADMIN ROUTES ============

@api_router.get("/admin/settings")
async def get_admin_settings(user: Dict = Depends(require_admin)):
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if not settings:
        default = AdminSettings().model_dump()
        await db.admin_settings.insert_one(default)
        return default
    return {k: v for k, v in settings.items() if k != "_id"}

@api_router.put("/admin/settings")
async def update_admin_settings(updates: Dict = Body(...), user: Dict = Depends(require_admin)):
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$set": updates},
        upsert=True
    )
    return await get_admin_settings(user)

@api_router.post("/admin/ban-word")
async def ban_word(word: str = Body(..., embed=True), user: Dict = Depends(require_admin)):
    """Ban a word or phrase."""
    forbidden = ["or", "and", "&", "(", ")"]
    if word.lower() in forbidden:
        raise HTTPException(status_code=400, detail="Cannot ban protocol operators")
    
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$addToSet": {"banned_words": word}},
        upsert=True
    )
    return {"message": f"Banned word: {word}"}

@api_router.post("/admin/users/{user_id}/action")
async def admin_user_action(user_id: str, action: str = Body(...), note: Optional[str] = Body(None), admin: Dict = Depends(require_admin)):
    """Admin action on user."""
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    if action == "delete":
        await db.users.delete_one({"id": user_id})
        await db.sessions.delete_many({"user_id": user_id})
        await db.categories.delete_many({"user_id": user_id})
        await db.search_results.delete_many({"user_id": user_id})
    elif action in ["ban", "boot", "mute"]:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {f"is_{action}ned": True, "admin_note": note}}
        )
    
    return {"message": f"User {action} successful", "note": note}

@api_router.get("/admin/newsletter/logs")
async def get_newsletter_logs(user: Dict = Depends(require_admin)):
    """Get newsletter sending logs."""
    logs = await db.newsletter_logs.find({}, {"_id": 0}).sort("sent_at", -1).to_list(100)
    return {"logs": logs}

# ============ THEME GALLERY ============

@api_router.get("/themes")
async def get_themes():
    """Get available theme presets."""
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    presets = settings.get("theme_presets", {}) if settings else {}
    
    default_presets = {
        "cosmic": {"primary": "#fbbf24", "secondary": "#8b5cf6", "background": "#0f172a", "name": "Cosmic"},
        "royal": {"primary": "#3b82f6", "secondary": "#6366f1", "background": "#1e1b4b", "name": "Royal"},
        "hot": {"primary": "#ef4444", "secondary": "#f97316", "background": "#1c1917", "name": "Hot"},
        "ocean": {"primary": "#06b6d4", "secondary": "#0ea5e9", "background": "#0c4a6e", "name": "Ocean"},
        "forest": {"primary": "#22c55e", "secondary": "#10b981", "background": "#14532d", "name": "Forest"},
        "sunset": {"primary": "#f59e0b", "secondary": "#ec4899", "background": "#431407", "name": "Sunset"},
        "ruby": {"primary": "#dc2626", "secondary": "#be123c", "background": "#450a0a", "name": "Ruby"},
        "light": {"primary": "#3b82f6", "secondary": "#8b5cf6", "background": "#f8fafc", "name": "Light Mode", "mode": "light"}
    }
    
    return {"themes": {**default_presets, **presets}}

@api_router.post("/themes/custom")
async def create_custom_theme(theme_data: Dict = Body(...), user: Dict = Depends(require_user)):
    """Create a custom theme preset."""
    theme_id = str(uuid.uuid4())[:8]
    theme = {
        "id": theme_id,
        "creator_id": user["id"],
        "name": theme_data.get("name", f"Custom {theme_id}"),
        "primary": theme_data.get("primary", "#fbbf24"),
        "secondary": theme_data.get("secondary", "#8b5cf6"),
        "background": theme_data.get("background", "#0f172a"),
        "mode": theme_data.get("mode", "dark"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.custom_themes.insert_one(theme)
    return {k: v for k, v in theme.items() if k != "_id"}

# ============ NEWSLETTER ROUTES ============

@api_router.post("/newsletter/signup")
async def newsletter_signup(email: EmailStr = Body(...), name: str = Body(...), signup_type: str = Body("general")):
    existing = await db.newsletter_signups.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already subscribed!")
    
    signup = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": name,
        "signup_type": signup_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.newsletter_signups.insert_one(signup)
    return {"message": "Welcome aboard! 🚀 Newsletter subscription confirmed!"}

# ============ CONTACT ROUTES ============

@api_router.post("/contact")
async def create_contact(name: str = Body(...), email: EmailStr = Body(...), subject: str = Body(...), message: str = Body(...)):
    contact = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contact_messages.insert_one(contact)
    return {"message": "Message sent! We'll respond faster than a Navy jet! 🛩️"}

# ============ BOOK & FOOD ROUTES ============

@api_router.get("/book")
async def get_book_info():
    return BOOK_INFO

@api_router.get("/book/prices")
async def get_book_prices():
    return BOOK_PRICES

@api_router.get("/food/menu")
async def get_food_menu():
    return {
        "restaurant_name": "Maestro Bistro",
        "parent_company": "Top Pilot Enterprises, Inc.",
        "tagline": "Where Every Bite is a Symphony of Flavor!",
        "location": "The Mall, Brunswick, Maine",
        "description": "Your friendly neighborhood food truck serving up deLectaBLe German delicacies with a side of laughs!",
        "menu": FOOD_MENU
    }

@api_router.get("/infopilot/plans")
async def get_infopilot_plans():
    admin_settings = await db.admin_settings.find_one({"id": "admin_settings"}) or {}
    return {
        "monthly": {
            "price": admin_settings.get("subscription_price_monthly", 1.00),
            "description": "InfoPilot Explorer Monthly - Boolean search and categorization for scholars and tradesmen",
            "features": ["Unlimited Boolean Searches", "Category Organization", "Collaboration Tools", "Priority Support"],
            "paypal_link": PAYPAL_INFOPILOT_LINK
        },
        "yearly": {
            "price": admin_settings.get("subscription_price_yearly", 9.98),
            "description": "InfoPilot Explorer Yearly - Save 17%!",
            "features": ["All Monthly Features", "Advanced Analytics", "Custom Categories", "API Access"],
            "paypal_link": PAYPAL_INFOPILOT_LINK
        },
        "upgrade_message": admin_settings.get("upgrade_message", "")
    }

# ============ STATISTICS ============

@api_router.get("/stats")
async def get_stats(user: Optional[Dict] = Depends(get_current_user)):
    """Get global and user statistics."""
    total_users = await db.users.count_documents({})
    total_categories = await db.categories.count_documents({"is_public": True})
    total_results = await db.search_results.count_documents({})
    
    user_stats = None
    if user:
        user_categories = await db.categories.count_documents({"user_id": user["id"]})
        user_results = await db.search_results.count_documents({"user_id": user["id"]})
        user_stats = {
            "categories": user_categories,
            "search_results": user_results,
            "laughter_points": user.get("laughter_points", 0),
            "easter_eggs_caught": user.get("easter_eggs_caught", 0)
        }
    
    return {
        "global": {
            "total_users": total_users,
            "public_categories": total_categories,
            "total_search_results": total_results
        },
        "user": user_stats
    }

# ============ NEWS HEADLINES ============

@api_router.get("/news/headlines")
async def get_news_headlines():
    """Get AI-powered news headlines."""
    headlines = [
        {"title": "Global Climate Summit Reaches Historic Agreement", "category": "Environment", "url": "#"},
        {"title": "Breakthrough in Quantum Computing Achieved", "category": "Technology", "url": "#"},
        {"title": "New Economic Policy Announced by Federal Reserve", "category": "Economy", "url": "#"},
        {"title": "Medical Researchers Develop Revolutionary Treatment", "category": "Health", "url": "#"},
        {"title": "Space Agency Confirms New Exoplanet Discovery", "category": "Science", "url": "#"},
        {"title": "International Trade Agreement Signed", "category": "Business", "url": "#"},
        {"title": "Education Reform Bill Passes Legislature", "category": "Politics", "url": "#"},
        {"title": "Renewable Energy Milestone Achieved", "category": "Energy", "url": "#"},
        {"title": "Archaeological Discovery Rewrites History", "category": "History", "url": "#"},
        {"title": "Agricultural Innovation Promises Food Security", "category": "Agriculture", "url": "#"}
    ]
    return {"headlines": headlines, "last_updated": datetime.now(timezone.utc).isoformat()}

# ============ TESTIMONIALS ============

@api_router.get("/testimonials")
async def get_testimonials():
    professional_reviews = [
        {
            "id": str(uuid.uuid4()),
            "name": "L. Jones",
            "location": "Readers' Favorite",
            "rating": 5,
            "review": "Letters to Evelyn by John Selman is an extraordinary book with a unique plot that captivated me from the first chapter. The author takes quite horrific and disturbing events and turns them into great learning experiences.",
            "review_type": "book",
            "featured": True,
            "source": "Readers' Favorite - 5 Star Professional Review"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Professional Reviewer",
            "location": "Readers' Favorite",
            "rating": 5,
            "review": "The comical side of it is exceedingly brilliant, to the point that even when I wasn't busy reading, the story would creep into my mind, and I would start laughing abruptly.",
            "review_type": "book",
            "featured": True,
            "source": "Readers' Favorite - 5 Star Professional Review"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hans the Hungry",
            "location": "Brunswick, ME",
            "rating": 5,
            "review": "The beef rouladen at Maestro Bistro made me call my grandmother in Germany to apologize. It's THAT good! So luscious and tender with the dark brown gravy!",
            "review_type": "food",
            "featured": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Chowder Charlie",
            "location": "Maine Coast",
            "rating": 5,
            "review": "The fish chowder with potatoes, bacon, and white fish made me emotional. My lobster pot is jealous. 11/10!",
            "review_type": "food",
            "featured": True
        }
    ]
    
    db_testimonials = await db.testimonials.find({}, {"_id": 0}).to_list(100)
    return {"testimonials": professional_reviews + db_testimonials}

# ============ QUOTES GALLERY ============

@api_router.get("/quotes/gallery")
async def get_quotes_gallery():
    """Get memorable quotes from Letters to Evelyn."""
    quotes = [
        {"quote": "The eggs were tasteless. The narcotics were military-grade. My survival was miraculous.", "chapter": "New Year's 2000"},
        {"quote": "70 finely-crafted, deafening, zany, zesty zoo zingers causing hurricane-force winds of laughter!", "chapter": "Introduction"},
        {"quote": "A flight student's hysterical quest, averting jealous murder attempts from his stepmother.", "chapter": "The Selman Chronicles"},
        {"quote": "Man saves Universe with his Memoir!", "chapter": "Cover"},
        {"quote": "A hysterically heartwarming journey on a hilarious roller coaster ride to the unwitting heavens!", "chapter": "Prologue"},
        {"quote": "Not intended for use while operating a vehicle or heavy equipment.", "chapter": "Warning Label"},
        {"quote": "May cause uncontrollable hysterics and fits of laughter.", "chapter": "Warning Label"},
        {"quote": "The tour along the Intergalactic Superhighway to Neptune was one of the best stories!", "chapter": "Chapter 15"},
        {"quote": "Two and a half ounces of military-grade psychological warfare narcotics.", "chapter": "January 3rd, 2000"},
        {"quote": "Graduated first in NROTC at the University of Maine with a B.A. in German.", "chapter": "Author Bio"},
    ]
    return {"quotes": quotes}

# ============ LEGAL PAGES ============

@api_router.get("/legal/user-agreement")
async def get_user_agreement():
    return {
        "title": "User Agreement - Top Pilot Enterprises, Inc.",
        "content": """
# User Agreement for InfoPilot Explorer

**Effective Date: 2025**

Welcome to InfoPilot Explorer, a product of Top Pilot Enterprises, Inc.

## 1. First in Flight with Monetization of Searches

InfoPilot Explorer is FIRST IN FLIGHT with Monetization of Searches! So much time is spent searching for valuable information. Why can't it be worth anything? If it's valuable to businesses, then it should be valuable to YOU!

## 2. Intellectual Property

The code, design, and functionality of InfoPilot Explorer are copyrighted and proprietary to Top Pilot Enterprises, Inc. This application and its underlying technology MAY NOT be emulated, copied, reproduced, or reverse-engineered by any person or entity without explicit written permission.

## 3. User Conduct

Users agree to:
- Use the platform for lawful purposes only
- Not upload prohibited content (pornographic, harmful to children, hate speech)
- Respect other users and their content
- Not attempt to circumvent payment systems

## 4. Payment Terms

- Minimum payment amount: $1.00 USD (PayPal requirement)
- Protocol sellers receive 85% of sale price
- Platform fee: 15% of transactions

## 5. Content Guidelines

All categories, protocols, and content must be appropriate. The following are prohibited:
- Pornographic content
- Content harmful to or depicting minors
- Hate speech or discriminatory content
- Illegal content

## 6. Termination

Top Pilot Enterprises, Inc. reserves the right to terminate accounts that violate these terms.

## 7. Contact

For questions about this agreement:
- Email: john.1976.selman@gmail.com
- Phone: 207-522-0894

---
© 2025 Top Pilot Enterprises, Inc. - "It's a Bear!" 🐻
        """
    }

@api_router.get("/legal/privacy-policy")
async def get_privacy_policy():
    return {
        "title": "Privacy Policy - Top Pilot Enterprises, Inc.",
        "content": """
# Privacy Policy for InfoPilot Explorer

**Effective Date: 2025**

## Information We Collect

- Account information (email, username, name)
- Search categories and protocols you create
- Usage data and interactions

## How We Use Your Information

- To provide and improve our services
- To process transactions
- To send newsletters (if opted in)

## First in Flight with Monetization of Searches

Your search patterns and categorization efforts have VALUE. InfoPilot Explorer is the first platform to monetize this effort. Your protocols and categories remain YOUR intellectual property.

## Data Protection

We implement industry-standard security measures to protect your data.

## Contact

john.1976.selman@gmail.com
207-522-0894

© 2025 Top Pilot Enterprises, Inc.
        """
    }

# ============ COMPANY INFO ============

@api_router.get("/company")
async def get_company_info():
    return {
        "corporation": "Top Pilot Enterprises, Inc.",
        "founded": "2025",
        "tagline": "It's a Bear! 🐻 - Where Every Flight Leads to Flavor and Every Page Leads to Laughter!",
        "marketplace_power": "InfoPilot Explorer's Marketplace is as dangerous to the app market as a Kodiak Bear! Experience the power of monetized searches!",
        "subsidiaries": [
            {"name": "InfoPilot Explorer, LLC", "description": "Mobile and desktop application for information exchange - First in Flight with Monetization of Searches!"},
            {"name": "Maestro Bistro", "description": "Food truck serving deLectaBLe German cuisine in Brunswick, Maine"},
            {"name": "John Selman Publications", "description": "Publishing arm featuring Letters to Evelyn - a True Supernatural Thriller Comedy"}
        ],
        "contact": {
            "email": "john.1976.selman@gmail.com",
            "phone": "207-522-0894",
            "location": "Brunswick, Maine"
        }
    }

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.categories.create_index("user_id")
    await db.search_results.create_index("user_id")
    await db.search_results.create_index("category_ids")
    await db.chat_messages.create_index("room_id")
    
    # Create default admin if not exists
    admin = await db.users.find_one({"email": "admin@infopilot.com"})
    if not admin:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": "admin@infopilot.com",
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "first_name": "Admin",
            "last_name": "User",
            "ultimate_search_name": "Admin Dashboard",
            "is_admin": True,
            "is_paid": True,
            "subscription_type": "yearly",
            "laughter_points": 1000,
            "easter_eggs_caught": 50,
            "friends": [],
            "theme_settings": {"mode": "dark", "preset": "cosmic"},
            "wallet_balance": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create default admin settings if not exists
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if not settings:
        await db.admin_settings.insert_one(AdminSettings().model_dump())
    
    # Start newsletter scheduler
    schedule_newsletters()
    scheduler.start()
    
    logger.info("InfoPilot Explorer API started! 🚀 It's a Bear! 🐻")

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    client.close()
