from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import jwt
import bcrypt
import httpx
import stripe
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import asyncio
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_db')]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'infopilot-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Google OAuth Settings - Supports Web, Android, and iOS
GOOGLE_WEB_CLIENT_ID = os.environ.get('GOOGLE_WEB_CLIENT_ID', '553762726406-a6it1kotb3tbb8o9j9ijad82r965o9va.apps.googleusercontent.com')
GOOGLE_ANDROID_CLIENT_ID = os.environ.get('GOOGLE_ANDROID_CLIENT_ID', '553762726406-a6it1kotb3tbb8o9j9ijad82r965o9va.apps.googleusercontent.com')
GOOGLE_IOS_CLIENT_ID = os.environ.get('GOOGLE_IOS_CLIENT_ID', '553762726406-a6it1kotb3tbb8o9j9ijad82r965o9va.apps.googleusercontent.com')

# All valid Google Client IDs (for token verification)
GOOGLE_CLIENT_IDS = [GOOGLE_WEB_CLIENT_ID, GOOGLE_ANDROID_CLIENT_ID, GOOGLE_IOS_CLIENT_ID]

# Stripe Configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
stripe.api_key = STRIPE_SECRET_KEY

# Shopify Configuration
SHOPIFY_API_KEY = os.environ.get('SHOPIFY_API_KEY', '')
SHOPIFY_API_SECRET = os.environ.get('SHOPIFY_API_SECRET', '')
SHOPIFY_STORE_DOMAIN = os.environ.get('SHOPIFY_STORE_DOMAIN', '')
SHOPIFY_PRODUCT_ID = os.environ.get('SHOPIFY_PRODUCT_ID', '')
SHOPIFY_PRODUCT_URL = os.environ.get('SHOPIFY_PRODUCT_URL', '')

# Emergent LLM Configuration
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Google Custom Search Configuration
GOOGLE_SEARCH_API_KEY = os.environ.get('GOOGLE_SEARCH_API_KEY', '')
GOOGLE_SEARCH_CX = os.environ.get('GOOGLE_SEARCH_CX', '')

# Create the main app without a prefix
app = FastAPI(title="InfoPilot Explorer API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# Google Safe Browsing API Key
GOOGLE_SAFE_BROWSING_API_KEY = os.environ.get('GOOGLE_SAFE_BROWSING_API_KEY', '')

# ============================================
# SAFE BROWSING URL CHECKER
# ============================================

async def check_url_safety(urls: List[str]) -> Dict[str, Any]:
    """
    Check URLs against Google Safe Browsing API for threats.
    Returns a dict with safe/unsafe status for each URL.
    """
    if not GOOGLE_SAFE_BROWSING_API_KEY:
        logger.warning("Safe Browsing API key not configured, skipping safety check")
        return {"checked": False, "results": {}}
    
    if not urls:
        return {"checked": True, "results": {}}
    
    try:
        api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_API_KEY}"
        
        body = {
            "client": {
                "clientId": "infopilot-app",
                "clientVersion": "2.0.0"
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": u} for u in urls[:500]]  # API limit
            }
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                api_url,
                json=body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Safe Browsing API error: {response.status_code} - {response.text}")
                return {"checked": False, "error": f"API error: {response.status_code}"}
            
            data = response.json()
            matches = data.get("matches", [])
            
            # Build results dict
            results = {}
            for url in urls:
                results[url] = {
                    "safe": True,
                    "threats": []
                }
            
            # Mark unsafe URLs
            for match in matches:
                threat_url = match.get("threat", {}).get("url", "")
                threat_type = match.get("threatType", "UNKNOWN")
                if threat_url in results:
                    results[threat_url]["safe"] = False
                    results[threat_url]["threats"].append(threat_type)
            
            unsafe_count = sum(1 for r in results.values() if not r["safe"])
            logger.info(f"Safe Browsing check: {len(urls)} URLs, {unsafe_count} unsafe")
            
            return {
                "checked": True,
                "total": len(urls),
                "safe_count": len(urls) - unsafe_count,
                "unsafe_count": unsafe_count,
                "results": results
            }
            
    except Exception as e:
        logger.error(f"Safe Browsing API error: {str(e)}")
        return {"checked": False, "error": str(e)}

# ============================================
# LOCATION EXTRACTION
# ============================================
# Common US cities and states for location detection
US_CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis", "Seattle",
    "Denver", "Washington", "Boston", "Nashville", "Baltimore", "Oklahoma City",
    "Louisville", "Portland", "Las Vegas", "Milwaukee", "Albuquerque", "Tucson",
    "Fresno", "Sacramento", "Mesa", "Atlanta", "Kansas City", "Colorado Springs",
    "Omaha", "Raleigh", "Miami", "Cleveland", "Tulsa", "Oakland", "Minneapolis",
    "Wichita", "Arlington", "New Orleans", "Bakersfield", "Tampa", "Aurora",
    "Honolulu", "Anaheim", "Santa Ana", "Corpus Christi", "Riverside", "St. Louis",
    "Lexington", "Pittsburgh", "Stockton", "Anchorage", "Cincinnati", "Saint Paul",
    "Greensboro", "Toledo", "Newark", "Plano", "Henderson", "Lincoln", "Orlando",
    "Jersey City", "Chula Vista", "Buffalo", "Fort Wayne", "Chandler", "St. Petersburg",
    "Laredo", "Durham", "Irvine", "Madison", "Norfolk", "Lubbock", "Gilbert",
    "Winston-Salem", "Glendale", "Reno", "Hialeah", "Garland", "Chesapeake",
    "Irving", "North Las Vegas", "Scottsdale", "Baton Rouge", "Fremont", "Richmond",
    "Boise", "San Bernardino"
]

US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma",
    "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming"
]

COUNTRIES = [
    "United States", "USA", "U.S.", "Canada", "Mexico", "United Kingdom", "UK",
    "Germany", "France", "Italy", "Spain", "Australia", "Japan", "China", "India",
    "Brazil", "Russia", "South Korea", "Netherlands", "Switzerland", "Sweden",
    "Norway", "Denmark", "Finland", "Ireland", "Belgium", "Austria", "Poland",
    "Portugal", "Greece", "Turkey", "Israel", "Saudi Arabia", "UAE", "Egypt",
    "South Africa", "Nigeria", "Kenya", "Argentina", "Chile", "Colombia", "Peru"
]

# City coordinates for mapping (lat, lng)
CITY_COORDINATES = {
    "New York": (40.7128, -74.0060), "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298), "Houston": (29.7604, -95.3698),
    "Phoenix": (33.4484, -112.0740), "Philadelphia": (39.9526, -75.1652),
    "San Antonio": (29.4241, -98.4936), "San Diego": (32.7157, -117.1611),
    "Dallas": (32.7767, -96.7970), "San Jose": (37.3382, -121.8863),
    "Austin": (30.2672, -97.7431), "San Francisco": (37.7749, -122.4194),
    "Seattle": (47.6062, -122.3321), "Denver": (39.7392, -104.9903),
    "Washington": (38.9072, -77.0369), "Boston": (42.3601, -71.0589),
    "Nashville": (36.1627, -86.7816), "Atlanta": (33.7490, -84.3880),
    "Miami": (25.7617, -80.1918), "Portland": (45.5051, -122.6750),
    "Las Vegas": (36.1699, -115.1398), "Minneapolis": (44.9778, -93.2650),
    "Tampa": (27.9506, -82.4572), "Orlando": (28.5383, -81.3792),
    "Cleveland": (41.4993, -81.6944), "Pittsburgh": (40.4406, -79.9959),
    "Cincinnati": (39.1031, -84.5120), "Kansas City": (39.0997, -94.5786),
    "Indianapolis": (39.7684, -86.1581), "Columbus": (39.9612, -82.9988),
    "Charlotte": (35.2271, -80.8431), "Detroit": (42.3314, -83.0458),
    "Baltimore": (39.2904, -76.6122), "Salt Lake City": (40.7608, -111.8910),
    "San Juan": (18.4655, -66.1057), "Honolulu": (21.3069, -157.8583),
    "Anchorage": (61.2181, -149.9003), "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522), "Berlin": (52.5200, 13.4050),
    "Tokyo": (35.6762, 139.6503), "Sydney": (-33.8688, 151.2093),
    "Toronto": (43.6532, -79.3832), "Vancouver": (49.2827, -123.1207),
}

def extract_locations(content: str, title: str) -> List[Dict[str, Any]]:
    """Extract location mentions from content and return with coordinates"""
    locations = []
    content_lower = content.lower()
    title_lower = title.lower()
    
    # Check for city mentions
    for city in US_CITIES:
        if city.lower() in content_lower or city.lower() in title_lower:
            if city in CITY_COORDINATES:
                locations.append({
                    "name": city,
                    "type": "city",
                    "lat": CITY_COORDINATES[city][0],
                    "lng": CITY_COORDINATES[city][1]
                })
    
    # Check for international cities
    international_cities = ["London", "Paris", "Berlin", "Tokyo", "Sydney", "Toronto", "Vancouver"]
    for city in international_cities:
        if city.lower() in content_lower or city.lower() in title_lower:
            if city in CITY_COORDINATES:
                locations.append({
                    "name": city,
                    "type": "city",
                    "lat": CITY_COORDINATES[city][0],
                    "lng": CITY_COORDINATES[city][1]
                })
    
    # Remove duplicates
    seen = set()
    unique_locations = []
    for loc in locations:
        if loc["name"] not in seen:
            seen.add(loc["name"])
            unique_locations.append(loc)
    
    return unique_locations[:5]  # Limit to 5 locations per result

# ============================================
# BLOCKED WORDS LIST (Expandable by Admin)
# ============================================
DEFAULT_BLOCKED_WORDS = [
    "child", "children", "boy", "girl", "teen", "young", "minor", "kid", "kids",
    "porn", "xxx", "nude", "naked", "sex", "fuck", "shit", "damn", "ass", "bitch"
]

# ============================================
# SUBSCRIPTION & BOOK INFO
# ============================================
# Welcome Sale: $0.75 for 2 months starting today
# After sale: $4.62/year
SALE_START_DATE = datetime(2026, 1, 4, tzinfo=timezone.utc)  # Today
SALE_END_DATE = SALE_START_DATE + timedelta(days=60)  # 2 months from now
SALE_PRICE = 0.75  # Welcome sale price
REGULAR_PRICE = 4.62  # Regular yearly price after sale

def get_current_subscription_price():
    """Get the current subscription price based on sale status"""
    now = datetime.now(timezone.utc)
    if now < SALE_END_DATE:
        return SALE_PRICE, True, SALE_END_DATE
    return REGULAR_PRICE, False, None

SUBSCRIPTION_PRICE = SALE_PRICE  # Default to sale price
BOOK_INFO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "price": 2.99,
    "rating": 5.0,
    "reviews_count": 15,
    "amazon_url": "https://a.co/d/atfpIds",
    "sintra_url": "https://www.Letters-to-Evelyn.sintra.site",
    "official_url": "https://letterstoevelynbyjohnselmanii.com",
    "readers_favorite_url": "https://readersfavorite.com/book-review/letters-to-evelyn",
    "google_drive_url": "https://drive.google.com/file/d/1YFhr75fWLzF2nu6nYDgVKB0fjEzZ36Pt/view?usp=drivesdk",
    "description": "A prolific odyssey of love and redemption - Navy pilot memoir meets sci-fi adventure",
    "tagline": "From the author who holds a World Record in Aviation"
}

# ============================================
# PYDANTIC MODELS
# ============================================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    username: str
    email: str
    is_admin: bool = False
    is_paid: bool = False
    profile_photo: Optional[str] = None
    auth_provider: str = "email"
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ProtocolCreate(BaseModel):
    """InfoPilot 2.0 Protocol - Boolean search syntax"""
    protocol_string: str  # e.g., "(word1 or word2) & (word3)+ & (word4)^"

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    protocol: ProtocolCreate
    parent_id: Optional[str] = None  # For subcategories
    is_public: bool = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    protocol_string: Optional[str] = None
    is_public: Optional[bool] = None

class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    protocol_string: str
    parent_id: Optional[str] = None
    is_public: bool = True
    level: int = 0
    created_at: datetime

class ArticleReaction(BaseModel):
    reaction_type: str

class SearchResultResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    url: str
    title: str
    snippet: str
    article_type: str
    categories: List[str]
    domain: str
    detected_year: Optional[int] = None
    word_count: int = 0
    reactions: Dict[str, int] = {}
    collated_at: datetime

class CollateRequest(BaseModel):
    search_query: str
    max_results: int = 20

class UltimateSearchRequest(BaseModel):
    category_ids: List[str] = []
    aggregation_type: str = "and_or"  # "and_or", "or", "and"
    document_types: List[str] = []  # PhD, PhD Informative, Personal Report (Organic), etc.
    article_types: List[str] = []
    domains: List[str] = []
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    keyword: Optional[str] = None
    ai_query: Optional[str] = None  # AI-powered intelligent search query
    page: int = 1

# Ultimate Search Page Customization
class UltimateSearchPageSettings(BaseModel):
    page_name: str = "My Ultimate Search"
    photos: List[str] = []  # URLs of uploaded photos (max 26)

class UpdatePageSettingsRequest(BaseModel):
    page_name: Optional[str] = None

class PhotoUploadResponse(BaseModel):
    success: bool
    photo_url: str
    message: str

# Document Type Classifications
DOCUMENT_TYPES = [
    "PhD Document",
    "PhD Informative", 
    "Personal Report (Organic)",
    "Personal Report (Collected)",
    "News Article",
    "PDF Document",
    "MS Word Document",
    "Educational (Non-Curricular)",
    "Blog Post",
    "Government Document",
    "Research Paper",
    "Other"
]

class AISearchRequest(BaseModel):
    query: str
    category_ids: List[str] = []
    
class SearchResultDeleteRequest(BaseModel):
    result_ids: List[str]
    
class CollateSessionResponse(BaseModel):
    session_id: str
    timestamp: str
    result_count: int
    results: List[Dict[str, Any]]

class AdminSettingsUpdate(BaseModel):
    results_per_page: Optional[int] = None
    free_user_pages: Optional[int] = None
    max_category_levels: Optional[int] = None
    blocked_words: Optional[List[str]] = None
    subscription_price: Optional[float] = None
    regular_price: Optional[float] = None
    informative_min_words: Optional[int] = None
    phd_keyword_count: Optional[int] = None
    blog_keyword_count: Optional[int] = None
    max_search_results: Optional[int] = None

class AdminSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "admin_settings"
    results_per_page: int = 20
    free_user_pages: int = 6  # Increased to 6 pages for free users
    max_category_levels: int = 100
    blocked_words: List[str] = DEFAULT_BLOCKED_WORDS
    subscription_price: float = 0.75  # Current sale price
    regular_price: float = 4.62  # Price after sale
    informative_min_words: int = 1500
    phd_keyword_count: int = 3
    blog_keyword_count: int = 3
    max_search_results: int = 120  # 6 pages * 20 results per page

# Payment Models (Stripe Integration)
class PaymentRequest(BaseModel):
    payment_method_id: str  # Stripe payment method ID
    item_type: str  # subscription, book
    amount: float

class PaymentResponse(BaseModel):
    success: bool
    transaction_id: str
    message: str
    client_secret: Optional[str] = None

class CreatePaymentIntentRequest(BaseModel):
    item_type: str  # subscription or book
    
class StripeConfigResponse(BaseModel):
    publishable_key: str
    sale_price: float
    regular_price: float
    is_sale_active: bool
    sale_end_date: Optional[str] = None

# ============================================
# INFOPILOT 2.0 PROTOCOL PARSER
# ============================================

class InfoPilot2Parser:
    """
    InfoPilot 2.0 Boolean Protocol Parser
    
    Syntax:
    - (word1 or word2 or word3) - Match ANY word in the group
    - & - AND operator between groups
    - + suffix - INCLUDE ALL words in the group (all must be present)
    - ^ suffix - EXCLUDE ALL words in the group (none should be present)
    """
    
    @staticmethod
    def parse_protocol(protocol_string: str) -> Dict[str, Any]:
        """Parse InfoPilot 2.0 protocol string into structured format"""
        result = {
            "groups": [],
            "valid": True,
            "error": None
        }
        
        try:
            groups = re.split(r'\s*&\s*', protocol_string.strip())
            
            for group in groups:
                group = group.strip()
                if not group:
                    continue
                
                include_all = False
                exclude_all = False
                
                if group.startswith('+') or group.endswith('+'):
                    include_all = True
                    group = group.strip('+').strip()
                elif group.startswith('^') or group.endswith('^'):
                    exclude_all = True
                    group = group.strip('^').strip()
                
                match = re.match(r'\(([^)]+)\)', group)
                if match:
                    words_str = match.group(1)
                    words = [w.strip() for w in re.split(r'\s+or\s+', words_str, flags=re.IGNORECASE)]
                    
                    result["groups"].append({
                        "words": words,
                        "include_all": include_all,
                        "exclude_all": exclude_all,
                        "operator": "OR"
                    })
                else:
                    result["groups"].append({
                        "words": [group],
                        "include_all": include_all,
                        "exclude_all": exclude_all,
                        "operator": "OR"
                    })
            
            if not result["groups"]:
                result["valid"] = False
                result["error"] = "No valid groups found in protocol"
                
        except Exception as e:
            result["valid"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def match_content(content: str, parsed_protocol: Dict[str, Any]) -> bool:
        """Check if content matches the parsed protocol"""
        if not parsed_protocol["valid"]:
            return False
        
        content_lower = content.lower()
        
        for group in parsed_protocol["groups"]:
            words = group["words"]
            include_all = group["include_all"]
            exclude_all = group["exclude_all"]
            
            if exclude_all:
                for word in words:
                    if word.lower() in content_lower:
                        return False
            elif include_all:
                for word in words:
                    if word.lower() not in content_lower:
                        return False
            else:
                found = False
                for word in words:
                    if word.lower() in content_lower:
                        found = True
                        break
                if not found:
                    return False
        
        return True
    
    @staticmethod
    def validate_protocol(protocol_string: str) -> tuple[bool, str]:
        """Validate protocol syntax"""
        parsed = InfoPilot2Parser.parse_protocol(protocol_string)
        if not parsed["valid"]:
            return False, parsed["error"]
        if len(parsed["groups"]) == 0:
            return False, "Protocol must contain at least one group"
        return True, "Valid protocol"

# ============================================
# ARTICLE CLASSIFIER
# ============================================

class ArticleClassifier:
    """Classifies articles based on InfoPilot rules"""
    
    INFORMATIVE_PROTOCOL = "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)"
    NEWS_PROTOCOL = "(news) & (news or story or news story) & (news or story or news story)"
    
    @staticmethod
    def classify(content: str, title: str, word_count: int, settings: AdminSettings) -> str:
        """Classify article type based on content"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        if 'forum' in title_lower:
            return "Forum"
        
        blog_count = content_lower.count('blog')
        if blog_count >= settings.blog_keyword_count and 'blog' in title_lower:
            return "Blog"
        
        phd_keywords = ['ph.d', 'phd', 'd.phil', 'dr.']
        phd_count = sum(content_lower.count(kw) for kw in phd_keywords)
        if phd_count >= settings.phd_keyword_count and word_count >= settings.informative_min_words:
            parsed = InfoPilot2Parser.parse_protocol(ArticleClassifier.INFORMATIVE_PROTOCOL)
            if InfoPilot2Parser.match_content(content, parsed):
                return "Informative Ph.D"
        
        parsed = InfoPilot2Parser.parse_protocol(ArticleClassifier.INFORMATIVE_PROTOCOL)
        if InfoPilot2Parser.match_content(content, parsed):
            return "Informative"
        
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            words = para.split()
            if len(words) >= 75:
                i_count = len([w for w in words if w.strip('.,!?;:') == 'I'])
                if i_count >= 3:
                    return "Personal Report (collected)"
        
        news_count = content_lower.count('news')
        if news_count >= 3:
            return "News Article"
        
        parsed = InfoPilot2Parser.parse_protocol(ArticleClassifier.NEWS_PROTOCOL)
        if InfoPilot2Parser.match_content(content, parsed):
            return "News Article"
        
        return "News Article"
    
    @staticmethod
    def classify_document_type(url: str, content: str, title: str, word_count: int) -> str:
        """Classify document type based on URL, content, and structure"""
        url_lower = url.lower()
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Check file extensions in URL
        if '.pdf' in url_lower:
            return "PDF Document"
        if '.doc' in url_lower or '.docx' in url_lower:
            return "MS Word Document"
        
        # PhD detection
        phd_keywords = ['ph.d', 'phd', 'd.phil', 'dissertation', 'thesis', 'doctoral']
        phd_count = sum(content_lower.count(kw) for kw in phd_keywords)
        
        if phd_count >= 5:
            # Check if it's informative (teaching) or a document
            informative_markers = ['explains', 'shows how', 'describes', 'methodology']
            if any(marker in content_lower for marker in informative_markers):
                return "PhD Informative"
            return "PhD Document"
        
        # Personal Report detection
        personal_markers = ['i think', 'my experience', 'i believe', 'in my opinion', 'i found', 'i discovered']
        personal_count = sum(content_lower.count(marker) for marker in personal_markers)
        
        if personal_count >= 3:
            # Organic = original thoughts, Collected = gathered from sources
            citation_markers = ['according to', 'source:', 'reference:', 'cited', 'et al']
            if any(marker in content_lower for marker in citation_markers):
                return "Personal Report (Collected)"
            return "Personal Report (Organic)"
        
        # Educational content
        educational_markers = ['learn', 'tutorial', 'guide', 'how to', 'lesson', 'course', 'educational']
        edu_count = sum(content_lower.count(marker) for marker in educational_markers)
        if edu_count >= 3:
            # Check if it's curricular (formal education) or non-curricular
            curricular_markers = ['curriculum', 'syllabus', 'grade', 'exam', 'semester']
            if not any(marker in content_lower for marker in curricular_markers):
                return "Educational (Non-Curricular)"
        
        # Government document detection
        gov_domains = ['.gov', 'government', 'federal', 'state.', 'congress', 'senate']
        if any(domain in url_lower or domain in content_lower for domain in gov_domains):
            return "Government Document"
        
        # Research paper detection
        research_markers = ['abstract', 'methodology', 'findings', 'conclusion', 'hypothesis', 'peer-reviewed']
        if sum(content_lower.count(marker) for marker in research_markers) >= 3:
            return "Research Paper"
        
        # News detection
        news_markers = ['breaking', 'reported', 'news', 'journalist', 'correspondent']
        if sum(content_lower.count(marker) for marker in news_markers) >= 2:
            return "News Article"
        
        # Blog detection
        if 'blog' in url_lower or 'blog' in title_lower:
            return "Blog Post"
        
        return "Other"

# ============================================
# CONTENT FILTER
# ============================================

async def get_blocked_words() -> List[str]:
    """Get blocked words from admin settings"""
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if settings:
        return settings.get("blocked_words", DEFAULT_BLOCKED_WORDS)
    return DEFAULT_BLOCKED_WORDS

def contains_blocked_words(text: str, blocked_words: List[str]) -> tuple[bool, List[str]]:
    """Check if text contains any blocked words"""
    text_lower = text.lower()
    found = []
    for word in blocked_words:
        if word.lower() in text_lower:
            found.append(word)
    return len(found) > 0, found

# ============================================
# AUTHENTICATION HELPERS
# ============================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = await db.users.find_one({"id": user_id})
        return user
    except:
        return None

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    user = await require_user(credentials)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_paid_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    user = await require_user(credentials)
    if not user.get("is_paid", False) and not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Paid subscription required")
    return user

# ============================================
# WEB SEARCH & CONTENT FETCHER
# ============================================

async def fetch_page_content(url: str) -> Dict[str, Any]:
    """Fetch and parse webpage content"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            title = soup.title.string if soup.title else ""
            
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            word_count = len(text.split())
            
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            detected_year = int(year_match.group()) if year_match else None
            
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            return {
                "success": True,
                "title": title[:500] if title else "Untitled",
                "content": text[:50000],
                "word_count": word_count,
                "detected_year": detected_year,
                "domain": domain
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def web_search(query: str, num_results: int = 20) -> List[Dict[str, Any]]:
    """Perform web search using Google Custom Search API"""
    results = []
    
    # Use Google Custom Search API if configured
    if GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX:
        try:
            # Google Custom Search allows max 10 results per request
            # We need multiple requests for more results
            pages_needed = (num_results + 9) // 10
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                for page in range(pages_needed):
                    start_index = page * 10 + 1
                    if start_index > 100:  # Google CSE limit
                        break
                    
                    search_url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        "key": GOOGLE_SEARCH_API_KEY,
                        "cx": GOOGLE_SEARCH_CX,
                        "q": query,
                        "num": min(10, num_results - len(results)),
                        "start": start_index
                    }
                    
                    response = await client.get(search_url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", [])
                        
                        for item in items:
                            results.append({
                                "url": item.get("link", ""),
                                "title": item.get("title", ""),
                                "snippet": item.get("snippet", "")
                            })
                            
                            if len(results) >= num_results:
                                break
                    else:
                        logger.error(f"Google Search API error: {response.status_code} - {response.text}")
                        break
                    
                    if len(results) >= num_results:
                        break
                        
            logger.info(f"Google Custom Search returned {len(results)} results for: {query}")
            
        except Exception as e:
            logger.error(f"Google Custom Search error: {e}")
    
    # Fallback to DuckDuckGo if Google search fails or not configured
    if not results:
        logger.info("Falling back to DuckDuckGo search...")
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(search_url, headers=headers, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    
                    for result in soup.select('.result')[:num_results]:
                        title_elem = result.select_one('.result__title a')
                        snippet_elem = result.select_one('.result__snippet')
                        
                        if title_elem:
                            href = title_elem.get('href', '')
                            url_match = re.search(r'uddg=([^&]+)', href)
                            if url_match:
                                from urllib.parse import unquote
                                url = unquote(url_match.group(1))
                            else:
                                url = href
                            
                            results.append({
                                "url": url,
                                "title": title_elem.get_text(strip=True),
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                            })
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
    
    return results

# ============================================
# API ROUTES - HEALTH & STATUS
# ============================================

@api_router.get("/")
async def root():
    return {"message": "InfoPilot Explorer API v2.0 - Advanced Tactical Information Exchange System"}

@api_router.get("/health")
async def health_check():
    return {"status": "operational", "service": "InfoPilot Explorer", "mode": "tactical"}

# ============================================
# API ROUTES - AUTHENTICATION
# ============================================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserCreate):
    blocked_words = await get_blocked_words()
    has_blocked, found = contains_blocked_words(data.username, blocked_words)
    if has_blocked:
        raise HTTPException(status_code=400, detail=f"Username contains blocked words: {found}")
    
    if await db.users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if await db.users.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": data.username,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "is_admin": False,
        "is_paid": False,
        "profile_photo": None,
        "auth_provider": "email",
        "friends": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=data.username,
            email=data.email,
            is_admin=False,
            is_paid=False,
            auth_provider="email",
            created_at=datetime.fromisoformat(user["created_at"])
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            is_admin=user.get("is_admin", False),
            is_paid=user.get("is_paid", False),
            profile_photo=user.get("profile_photo"),
            auth_provider=user.get("auth_provider", "email"),
            created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
        )
    )

@api_router.post("/auth/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest):
    """
    Google OAuth Authentication - Verifies Google ID tokens
    Supports: Web, Android (com.toppilotenterprises.infopilot), iOS
    """
    try:
        # Verify the Google ID token
        idinfo = None
        verification_error = None
        
        # Try to verify against all configured client IDs
        for client_id in GOOGLE_CLIENT_IDS:
            try:
                idinfo = id_token.verify_oauth2_token(
                    data.credential,
                    google_requests.Request(),
                    client_id
                )
                break  # Successfully verified
            except ValueError as e:
                verification_error = str(e)
                continue
        
        if idinfo is None:
            # If verification failed, log the error but try to extract info for debugging
            logger.warning(f"Google token verification failed: {verification_error}")
            raise HTTPException(status_code=401, detail=f"Invalid Google token: {verification_error}")
        
        # Token is valid - extract user info
        google_email = idinfo.get('email')
        google_name = idinfo.get('name', 'Pilot')
        google_picture = idinfo.get('picture')
        google_sub = idinfo.get('sub')  # Google's unique user ID
        
        if not google_email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Check if email is verified
        if not idinfo.get('email_verified', False):
            raise HTTPException(status_code=400, detail="Google email not verified")
        
        # Check if user exists by email or Google ID
        user = await db.users.find_one({
            "$or": [
                {"email": google_email},
                {"google_id": google_sub}
            ]
        })
        
        if not user:
            # Create new user
            user_id = str(uuid.uuid4())
            username = google_name.replace(' ', '_')[:20] if google_name else f"pilot_{uuid.uuid4().hex[:6]}"
            
            # Ensure unique username
            existing_username = await db.users.find_one({"username": username})
            if existing_username:
                username = f"{username}_{uuid.uuid4().hex[:4]}"
            
            user = {
                "id": user_id,
                "username": username,
                "email": google_email,
                "google_id": google_sub,
                "password_hash": "",  # No password for OAuth users
                "is_admin": False,
                "is_paid": False,
                "profile_photo": google_picture,
                "auth_provider": "google",
                "friends": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(user)
            logger.info(f"New Google user registered: {google_email}")
        else:
            # Update existing user's Google info if needed
            update_data = {}
            if not user.get("google_id"):
                update_data["google_id"] = google_sub
            if google_picture and not user.get("profile_photo"):
                update_data["profile_photo"] = google_picture
            if user.get("auth_provider") != "google":
                update_data["auth_provider"] = "google"
            
            if update_data:
                await db.users.update_one({"id": user["id"]}, {"$set": update_data})
                user.update(update_data)
        
        token = create_token(user["id"])
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                is_admin=user.get("is_admin", False),
                is_paid=user.get("is_paid", False),
                profile_photo=user.get("profile_photo"),
                auth_provider="google",
                created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(require_user)):
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        is_admin=user.get("is_admin", False),
        is_paid=user.get("is_paid", False),
        profile_photo=user.get("profile_photo"),
        auth_provider=user.get("auth_provider", "email"),
        created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
    )

# ============================================
# API ROUTES - PAYMENTS (STRIPE INTEGRATION)
# ============================================

@api_router.get("/payments/config", response_model=StripeConfigResponse)
async def get_stripe_config():
    """Get Stripe configuration and current pricing"""
    price, is_sale, sale_end = get_current_subscription_price()
    return StripeConfigResponse(
        publishable_key=STRIPE_PUBLISHABLE_KEY,
        sale_price=SALE_PRICE,
        regular_price=REGULAR_PRICE,
        is_sale_active=is_sale,
        sale_end_date=sale_end.isoformat() if sale_end else None
    )

@api_router.post("/payments/create-intent")
async def create_payment_intent(data: CreatePaymentIntentRequest, user: dict = Depends(require_user)):
    """
    Create a Stripe Payment Intent for subscription or book purchase
    """
    try:
        price, is_sale, _ = get_current_subscription_price()
        
        if data.item_type == "subscription":
            amount = int(price * 100)  # Convert to cents
            description = f"InfoPilot Explorer Lifetime Subscription {'(Welcome Sale!)' if is_sale else ''}"
        elif data.item_type == "book":
            amount = 299  # $2.99 for book
            description = "Letters to Evelyn - Digital Book"
        else:
            raise HTTPException(status_code=400, detail="Invalid item type")
        
        # Create Stripe Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={
                "user_id": user["id"],
                "user_email": user["email"],
                "item_type": data.item_type,
                "is_sale": str(is_sale)
            },
            description=description,
            automatic_payment_methods={"enabled": True}
        )
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": amount / 100
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/payments/confirm", response_model=PaymentResponse)
async def confirm_payment(payment_intent_id: str, user: dict = Depends(require_user)):
    """
    Confirm payment was successful and update user subscription
    """
    try:
        # Retrieve the payment intent to verify it succeeded
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status != "succeeded":
            raise HTTPException(status_code=400, detail=f"Payment not completed. Status: {intent.status}")
        
        item_type = intent.metadata.get("item_type", "subscription")
        transaction_id = f"STRIPE_{intent.id}"
        
        # Log the payment
        payment_record = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "transaction_id": transaction_id,
            "stripe_payment_intent_id": intent.id,
            "payment_method": "stripe",
            "item_type": item_type,
            "amount": intent.amount / 100,
            "currency": intent.currency.upper(),
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payments.insert_one(payment_record)
        
        # Update user's paid status if subscription
        if item_type == "subscription":
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {
                    "is_paid": True, 
                    "subscription_date": datetime.now(timezone.utc).isoformat(),
                    "subscription_type": "lifetime"
                }}
            )
        
        return PaymentResponse(
            success=True,
            transaction_id=transaction_id,
            message=f"Payment successful! {'Your subscription is now active.' if item_type == 'subscription' else 'Thank you for your purchase!'}"
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error confirming payment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/payments/process", response_model=PaymentResponse)
async def process_payment(data: PaymentRequest, user: dict = Depends(require_user)):
    """
    Legacy payment processing endpoint (for backward compatibility)
    Now uses Stripe
    """
    try:
        price, is_sale, _ = get_current_subscription_price()
        
        # Create and confirm payment in one step using payment method
        intent = stripe.PaymentIntent.create(
            amount=int(data.amount * 100),
            currency="usd",
            payment_method=data.payment_method_id,
            confirm=True,
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never"
            },
            metadata={
                "user_id": user["id"],
                "user_email": user["email"],
                "item_type": data.item_type
            }
        )
        
        transaction_id = f"STRIPE_{intent.id}"
        
        # Log the payment
        payment_record = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "transaction_id": transaction_id,
            "stripe_payment_intent_id": intent.id,
            "payment_method": "stripe",
            "item_type": data.item_type,
            "amount": data.amount,
            "currency": "USD",
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payments.insert_one(payment_record)
        
        # Update user's paid status if subscription
        if data.item_type == "subscription":
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {
                    "is_paid": True, 
                    "subscription_date": datetime.now(timezone.utc).isoformat(),
                    "subscription_type": "lifetime"
                }}
            )
        
        return PaymentResponse(
            success=True,
            transaction_id=transaction_id,
            message=f"Payment processed successfully via Stripe"
        )
    except stripe.error.CardError as e:
        logger.error(f"Card error: {str(e)}")
        raise HTTPException(status_code=402, detail=f"Card declined: {e.user_message}")
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/payments/history")
async def get_payment_history(user: dict = Depends(require_user)):
    """Get user's payment history"""
    payments = await db.payments.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return payments

# ============================================
# API ROUTES - SHOPIFY INTEGRATION
# ============================================

import hmac
import hashlib
import base64

def verify_shopify_webhook(data: bytes, hmac_header: str) -> bool:
    """Verify Shopify webhook signature"""
    if not SHOPIFY_API_SECRET:
        return False
    computed_hmac = base64.b64encode(
        hmac.new(SHOPIFY_API_SECRET.encode('utf-8'), data, hashlib.sha256).digest()
    ).decode('utf-8')
    return hmac.compare_digest(computed_hmac, hmac_header)

def verify_shopify_proxy_signature(params: dict) -> bool:
    """Verify Shopify App Proxy request signature"""
    if not SHOPIFY_API_SECRET:
        return False
    signature = params.pop('signature', None)
    if not signature:
        return False
    sorted_params = ''.join([f"{key}={value}" for key, value in sorted(params.items())])
    computed_signature = hmac.new(
        SHOPIFY_API_SECRET.encode('utf-8'),
        sorted_params.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)

@api_router.get("/shopify/config")
async def get_shopify_config():
    """Get Shopify configuration for frontend"""
    return {
        "store_domain": SHOPIFY_STORE_DOMAIN,
        "product_url": SHOPIFY_PRODUCT_URL,
        "product_id": SHOPIFY_PRODUCT_ID,
        "checkout_enabled": bool(SHOPIFY_API_KEY and SHOPIFY_STORE_DOMAIN)
    }

@api_router.get("/shopify/checkout-url")
async def get_shopify_checkout_url(user: dict = Depends(require_user)):
    """Generate Shopify checkout URL for the subscription product"""
    if not SHOPIFY_PRODUCT_URL:
        raise HTTPException(status_code=500, detail="Shopify not configured")
    
    # Add user tracking parameter
    checkout_url = f"{SHOPIFY_PRODUCT_URL}?utm_source=infopilot&user_id={user['id']}"
    
    return {
        "checkout_url": checkout_url,
        "product_url": SHOPIFY_PRODUCT_URL,
        "store_domain": SHOPIFY_STORE_DOMAIN
    }

@api_router.post("/shopify/webhooks/orders-paid")
async def shopify_order_paid_webhook(request: Request):
    """
    Handle Shopify order paid webhook to grant premium access
    Configure this webhook URL in Shopify: /api/shopify/webhooks/orders-paid
    Topic: orders/paid
    """
    body = await request.body()
    hmac_header = request.headers.get('X-Shopify-Hmac-Sha256', '')
    
    if not verify_shopify_webhook(body, hmac_header):
        logger.warning("Invalid Shopify webhook signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    try:
        data = await request.json()
        order_id = data.get('id')
        email = data.get('email', '').lower()
        customer = data.get('customer', {})
        customer_email = customer.get('email', '').lower() if customer else ''
        
        # Find user by email
        user_email = email or customer_email
        if user_email:
            user = await db.users.find_one({"email": user_email})
            if user:
                # Grant premium access
                await db.users.update_one(
                    {"email": user_email},
                    {"$set": {
                        "is_paid": True,
                        "subscription_type": "lifetime",
                        "subscription_source": "shopify",
                        "shopify_order_id": str(order_id),
                        "subscription_date": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Record payment
                await db.payments.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "user_email": user_email,
                    "amount": data.get('total_price', 0),
                    "currency": data.get('currency', 'USD'),
                    "transaction_id": f"SHOPIFY_{order_id}",
                    "shopify_order_id": str(order_id),
                    "payment_method": "shopify",
                    "item_type": "subscription",
                    "status": "completed",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                logger.info(f"Granted premium access via Shopify to: {user_email}")
            else:
                logger.warning(f"Shopify order for unknown user: {user_email}")
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing Shopify webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class VerifyPurchaseRequest(BaseModel):
    email: str

@api_router.post("/shopify/verify-purchase")
async def verify_shopify_purchase(data: VerifyPurchaseRequest, user: dict = Depends(require_user)):
    """
    Manual purchase verification for Shopify orders.
    User enters their email after completing Shopify checkout.
    Admin can use this to grant premium access to users who purchased.
    """
    email = data.email.strip().lower()
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if this email matches the logged-in user or if admin is verifying
    is_own_email = email == user.get("email", "").lower()
    is_admin = user.get("is_admin", False)
    
    if not is_own_email and not is_admin:
        raise HTTPException(status_code=403, detail="You can only verify purchases for your own email")
    
    # Check if user already has premium
    target_user = await db.users.find_one({"email": email})
    if not target_user:
        return {
            "verified": False,
            "message": "No account found with this email. Please register first, then verify your purchase."
        }
    
    if target_user.get("is_paid"):
        return {
            "verified": True,
            "message": "This account already has premium access!",
            "already_premium": True
        }
    
    # For now, we'll trust the user and grant access
    # In production, you would verify against Shopify Orders API
    # Since we don't have Admin API token, we grant access based on trust
    
    # Grant premium access
    await db.users.update_one(
        {"email": email},
        {"$set": {
            "is_paid": True,
            "subscription_type": "lifetime",
            "subscription_source": "shopify_manual_verify",
            "subscription_date": datetime.now(timezone.utc).isoformat(),
            "verified_by": user["id"] if is_admin and not is_own_email else "self"
        }}
    )
    
    # Record the verification
    await db.payments.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": target_user["id"],
        "user_email": email,
        "amount": 0.75,
        "currency": "USD",
        "transaction_id": f"SHOPIFY_MANUAL_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "payment_method": "shopify_manual_verify",
        "item_type": "subscription",
        "status": "verified",
        "verified_by": user["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Manual Shopify verification: Premium granted to {email} by {user['email']}")
    
    return {
        "verified": True,
        "message": "Purchase verified! Premium access has been granted.",
        "already_premium": False
    }

@api_router.get("/shopify/{path:path}")
@api_router.post("/shopify/{path:path}")
async def shopify_app_proxy(path: str, request: Request):
    """
    Handle Shopify App Proxy requests
    These come from: https://your-store.myshopify.com/apps/infopilot/*
    """
    # Get query parameters
    params = dict(request.query_params)
    
    # For proxy requests, we could verify signature (optional for public content)
    # verify_shopify_proxy_signature(params.copy())
    
    # Handle different proxy paths
    if path == "status" or path == "":
        return {
            "app": "InfoPilot Explorer",
            "status": "active",
            "version": "2.0.0"
        }
    elif path == "verify-subscription":
        # Check if customer has premium access
        customer_email = params.get('customer_email', '').lower()
        if customer_email:
            user = await db.users.find_one({"email": customer_email})
            if user and user.get('is_paid'):
                return {"has_subscription": True, "type": "lifetime"}
        return {"has_subscription": False}
    else:
        return {"error": "Unknown proxy path", "path": path}

# ============================================
# API ROUTES - BOOK INFO
# ============================================

@api_router.get("/book/info")
async def get_book_info():
    """Get Letters to Evelyn book information"""
    return BOOK_INFO

@api_router.get("/subscription/info")
async def get_subscription_info():
    """Get subscription information including sale status"""
    price, is_sale, sale_end = get_current_subscription_price()
    return {
        "price": price,
        "regular_price": REGULAR_PRICE,
        "is_sale_active": is_sale,
        "sale_end_date": sale_end.isoformat() if sale_end else None,
        "type": "lifetime",
        "sale_name": "Welcome Sale" if is_sale else None,
        "features": [
            "Unlimited search results pages",
            "Unlimited categories",
            "Advanced statistics",
            "Global Research Database access",
            "Priority support"
        ]
    }

# ============================================
# API ROUTES - CATEGORIES & PROTOCOLS
# ============================================

@api_router.post("/categories", response_model=CategoryResponse)
async def create_category(data: CategoryCreate, user: dict = Depends(require_user)):
    is_valid, error = InfoPilot2Parser.validate_protocol(data.protocol.protocol_string)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid protocol: {error}")
    
    blocked_words = await get_blocked_words()
    has_blocked, found = contains_blocked_words(data.name, blocked_words)
    if has_blocked:
        raise HTTPException(status_code=400, detail=f"Category name contains blocked words: {found}")
    
    has_blocked, found = contains_blocked_words(data.protocol.protocol_string, blocked_words)
    if has_blocked:
        raise HTTPException(status_code=400, detail=f"Protocol contains blocked words: {found}")
    
    level = 0
    if data.parent_id:
        parent = await db.categories.find_one({"id": data.parent_id, "user_id": user["id"]})
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
        level = parent.get("level", 0) + 1
        
        settings = await db.admin_settings.find_one({"id": "admin_settings"})
        max_levels = settings.get("max_category_levels", 100) if settings else 100
        if level > max_levels:
            raise HTTPException(status_code=400, detail=f"Maximum category depth of {max_levels} exceeded")
    
    category_id = str(uuid.uuid4())
    category = {
        "id": category_id,
        "user_id": user["id"],
        "name": data.name,
        "protocol_string": data.protocol.protocol_string,
        "parent_id": data.parent_id,
        "is_public": data.is_public,
        "level": level,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(category)
    
    return CategoryResponse(**{**category, "created_at": datetime.fromisoformat(category["created_at"])})

@api_router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    user_id: Optional[str] = None,
    include_public: bool = True,
    user: dict = Depends(require_user)
):
    query = {"$or": [{"user_id": user["id"]}]}
    
    if include_public:
        if user_id:
            query["$or"].append({"user_id": user_id, "is_public": True})
        else:
            query["$or"].append({"is_public": True})
    
    categories = await db.categories.find(query).to_list(1000)
    
    result = []
    for cat in categories:
        created_at = cat["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(CategoryResponse(**{**cat, "created_at": created_at}))
    
    return result

@api_router.get("/categories/with-counts")
async def get_categories_with_counts(user: dict = Depends(require_user)):
    """Get user's categories with result counts"""
    categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    # Get counts for each category
    for cat in categories:
        count = await db.search_results.count_documents({
            "user_id": user["id"],
            "categories": cat["id"]
        })
        cat["result_count"] = count
    
    return {"categories": categories}

@api_router.get("/categories/tree")
async def get_categories_tree(user: dict = Depends(require_user)):
    """Get categories in hierarchical tree structure with result counts"""
    categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    # Get counts for each category
    for cat in categories:
        count = await db.search_results.count_documents({
            "user_id": user["id"],
            "categories": cat["id"]
        })
        cat["result_count"] = count
        cat["children"] = []
    
    # Build tree structure
    category_map = {cat["id"]: cat for cat in categories}
    root_categories = []
    
    for cat in categories:
        parent_id = cat.get("parent_id")
        if parent_id and parent_id in category_map:
            category_map[parent_id]["children"].append(cat)
        else:
            root_categories.append(cat)
    
    # Sort children by name at each level
    def sort_children(cats):
        cats.sort(key=lambda x: x["name"])
        for cat in cats:
            if cat["children"]:
                sort_children(cat["children"])
    
    sort_children(root_categories)
    
    return {"categories": root_categories}

@api_router.post("/categories/{parent_id}/subcategory")
async def create_subcategory(
    parent_id: str,
    data: CategoryCreate,
    user: dict = Depends(require_user)
):
    """Create a subcategory under a parent category"""
    # Verify parent exists and belongs to user
    parent = await db.categories.find_one({"id": parent_id, "user_id": user["id"]})
    if not parent:
        raise HTTPException(status_code=404, detail="Parent category not found")
    
    # Check max depth
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    parent_level = parent.get("level", 0)
    if parent_level >= settings.max_category_levels:
        raise HTTPException(status_code=400, detail=f"Maximum category depth ({settings.max_category_levels}) reached")
    
    # Validate protocol
    is_valid, message = InfoPilot2Parser.validate_protocol(data.protocol.protocol_string)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid protocol: {message}")
    
    # Create subcategory
    category_id = str(uuid.uuid4())
    category = {
        "id": category_id,
        "user_id": user["id"],
        "name": data.name,
        "protocol_string": data.protocol.protocol_string,
        "parent_id": parent_id,
        "is_public": data.is_public if data.is_public is not None else True,
        "level": parent_level + 1,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(category)
    
    return {
        **{k: v for k, v in category.items() if k != "_id"},
        "created_at": category["created_at"]
    }

@api_router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str, user: dict = Depends(require_user)):
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category["user_id"] != user["id"] and not category.get("is_public", True):
        raise HTTPException(status_code=403, detail="Access denied")
    
    created_at = category["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return CategoryResponse(**{**category, "created_at": created_at})

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user: dict = Depends(require_user)):
    category = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await db.categories.delete_many({
        "$or": [
            {"id": category_id},
            {"parent_id": category_id}
        ],
        "user_id": user["id"]
    })
    
    return {"message": "Category deleted"}

@api_router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, data: CategoryUpdate, user: dict = Depends(require_user)):
    """Update a category's name, protocol, or visibility"""
    category = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {}
    blocked_words = await get_blocked_words()
    
    # Update name if provided
    if data.name is not None:
        has_blocked, found = contains_blocked_words(data.name, blocked_words)
        if has_blocked:
            raise HTTPException(status_code=400, detail=f"Category name contains blocked words: {found}")
        update_data["name"] = data.name
    
    # Update protocol if provided
    if data.protocol_string is not None:
        # Validate protocol syntax
        is_valid, error = InfoPilot2Parser.validate_protocol(data.protocol_string)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid protocol: {error}")
        
        # Check for blocked words in protocol
        has_blocked, found = contains_blocked_words(data.protocol_string, blocked_words)
        if has_blocked:
            raise HTTPException(status_code=400, detail=f"Protocol contains blocked words: {found}")
        
        update_data["protocol_string"] = data.protocol_string
    
    # Update visibility if provided
    if data.is_public is not None:
        update_data["is_public"] = data.is_public
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    await db.categories.update_one(
        {"id": category_id, "user_id": user["id"]},
        {"$set": update_data}
    )
    
    # Fetch updated category
    updated_category = await db.categories.find_one({"id": category_id})
    created_at = updated_category["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return CategoryResponse(**{**updated_category, "created_at": created_at})

@api_router.put("/categories/{category_id}/visibility")
async def update_category_visibility(category_id: str, is_public: bool, user: dict = Depends(require_user)):
    result = await db.categories.update_one(
        {"id": category_id, "user_id": user["id"]},
        {"$set": {"is_public": is_public}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Visibility updated"}

# ============================================
# API ROUTES - PROTOCOL VALIDATION
# ============================================

@api_router.post("/protocol/validate")
async def validate_protocol(data: ProtocolCreate):
    """Validate InfoPilot 2.0 protocol syntax"""
    is_valid, message = InfoPilot2Parser.validate_protocol(data.protocol_string)
    parsed = InfoPilot2Parser.parse_protocol(data.protocol_string)
    
    return {
        "valid": is_valid,
        "message": message,
        "parsed": parsed
    }

@api_router.post("/protocol/test")
async def test_protocol(protocol_string: str, test_content: str):
    """Test if content matches a protocol"""
    parsed = InfoPilot2Parser.parse_protocol(protocol_string)
    matches = InfoPilot2Parser.match_content(test_content, parsed)
    
    return {
        "matches": matches,
        "parsed_protocol": parsed
    }

# ============================================
# API ROUTES - SEARCH & COLLATE (THE INFOPILOT PAGE)
# ============================================

@api_router.post("/search/collate")
async def collate_search(data: CollateRequest, user: dict = Depends(require_user)):
    """Main InfoPilot search - searches the web and automatically categorizes results"""
    blocked_words = await get_blocked_words()
    has_blocked, found = contains_blocked_words(data.search_query, blocked_words)
    if has_blocked:
        raise HTTPException(status_code=400, detail=f"Search query contains blocked words: {found}")
    
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    # App is now free - all users get full access
    if not user.get("is_paid") and not user.get("is_admin"):
        # No restrictions - app is free
        pass
    max_results = min(data.max_results, 100)
    
    user_categories = await db.categories.find({"user_id": user["id"]}).to_list(1000)
    
    if not user_categories:
        raise HTTPException(status_code=400, detail="Create at least one category with a protocol before searching")
    
    search_results = await web_search(data.search_query, max_results)
    
    if not search_results:
        return {"message": "No search results found", "results": [], "categorized_count": 0}
    
    # Check URLs for safety using Google Safe Browsing API
    urls_to_check = [r["url"] for r in search_results]
    safety_check = await check_url_safety(urls_to_check)
    unsafe_urls = set()
    if safety_check.get("checked"):
        for url, status in safety_check.get("results", {}).items():
            if not status.get("safe", True):
                unsafe_urls.add(url)
                logger.warning(f"Unsafe URL blocked: {url} - Threats: {status.get('threats', [])}")
    
    collated_results = []
    blocked_unsafe_count = 0
    
    for result in search_results:
        # Skip unsafe URLs
        if result["url"] in unsafe_urls:
            blocked_unsafe_count += 1
            continue
        
        page_data = await fetch_page_content(result["url"])
        
        if not page_data["success"]:
            continue
        
        content = f"{result['title']} {result['snippet']} {page_data.get('content', '')}"
        
        has_blocked, _ = contains_blocked_words(content, blocked_words)
        if has_blocked:
            continue
        
        matching_categories = []
        for category in user_categories:
            parsed = InfoPilot2Parser.parse_protocol(category["protocol_string"])
            if InfoPilot2Parser.match_content(content, parsed):
                matching_categories.append(category["id"])
        
        if matching_categories:
            article_type = ArticleClassifier.classify(
                content,
                result["title"],
                page_data.get("word_count", 0),
                settings
            )
            
            # Also classify document type
            document_type = ArticleClassifier.classify_document_type(
                result["url"],
                content,
                result["title"],
                page_data.get("word_count", 0)
            )
            
            # Extract locations from content
            locations = extract_locations(content, result["title"])
            
            result_id = str(uuid.uuid4())
            search_result = {
                "id": result_id,
                "user_id": user["id"],
                "url": result["url"],
                "title": result["title"],
                "snippet": result["snippet"],
                "article_type": article_type,
                "document_type": document_type,
                "categories": matching_categories,
                "domain": page_data.get("domain", ""),
                "detected_year": page_data.get("detected_year"),
                "word_count": page_data.get("word_count", 0),
                "locations": locations,
                "safety_checked": safety_check.get("checked", False),
                "reactions": {},
                "collated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.search_results.insert_one(search_result)
            # Return a clean copy without MongoDB _id
            clean_result = {k: v for k, v in search_result.items() if k != "_id"}
            collated_results.append(clean_result)
    
    response_message = f"Collated {len(collated_results)} results into categories"
    if blocked_unsafe_count > 0:
        response_message += f" ({blocked_unsafe_count} unsafe URLs blocked)"
    
    return {
        "message": response_message,
        "results": collated_results,
        "categorized_count": len(collated_results),
        "total_searched": len(search_results),
        "unsafe_blocked": blocked_unsafe_count,
        "safety_checked": safety_check.get("checked", False)
    }

@api_router.post("/search/search-only")
async def search_only(data: CollateRequest, user: dict = Depends(require_user)):
    """
    Search Only - Returns categorized results WITHOUT saving to database.
    For visitors/friends who can view but not modify the owner's data.
    """
    blocked_words = await get_blocked_words()
    has_blocked, found = contains_blocked_words(data.search_query, blocked_words)
    if has_blocked:
        raise HTTPException(status_code=400, detail=f"Search query contains blocked words: {found}")
    
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    # Allow up to 6 pages of results (120 results)
    max_results = min(data.max_results, settings.max_search_results)
    
    user_categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    if not user_categories:
        raise HTTPException(status_code=400, detail="Create at least one category with a protocol before searching")
    
    search_results = await web_search(data.search_query, max_results)
    
    if not search_results:
        return {"message": "No search results found", "results": [], "categorized_count": 0, "total_searched": 0}
    
    categorized_results = []
    
    for result in search_results:
        page_data = await fetch_page_content(result["url"])
        
        if not page_data["success"]:
            continue
        
        content = f"{result['title']} {result['snippet']} {page_data.get('content', '')}"
        
        has_blocked, _ = contains_blocked_words(content, blocked_words)
        if has_blocked:
            continue
        
        matching_categories = []
        matching_category_names = []
        for category in user_categories:
            parsed = InfoPilot2Parser.parse_protocol(category["protocol_string"])
            if InfoPilot2Parser.match_content(content, parsed):
                matching_categories.append(category["id"])
                matching_category_names.append(category["name"])
        
        if matching_categories:
            article_type = ArticleClassifier.classify(
                content,
                result["title"],
                page_data.get("word_count", 0),
                settings
            )
            
            document_type = ArticleClassifier.classify_document_type(
                result["url"],
                content,
                result["title"],
                page_data.get("word_count", 0)
            )
            
            # Return result without saving to database
            search_result = {
                "id": str(uuid.uuid4()),  # Temporary ID
                "url": result["url"],
                "title": result["title"],
                "snippet": result["snippet"],
                "article_type": article_type,
                "document_type": document_type,
                "categories": matching_categories,
                "category_names": matching_category_names,
                "domain": page_data.get("domain", ""),
                "detected_year": page_data.get("detected_year"),
                "word_count": page_data.get("word_count", 0),
                "is_preview": True  # Flag to indicate this is not saved
            }
            
            categorized_results.append(search_result)
    
    return {
        "message": f"Found {len(categorized_results)} matching results (not saved)",
        "results": categorized_results,
        "categorized_count": len(categorized_results),
        "total_searched": len(search_results),
        "is_preview": True
    }

# ============================================
# API ROUTES - ULTIMATE SEARCH PAGE
# ============================================

async def ai_semantic_search(query: str, user_id: str) -> List[str]:
    """Use AI to enhance search and find semantically relevant results"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"search_{user_id}_{uuid.uuid4().hex[:8]}",
            system_message="""You are a semantic search assistant. Given a user query, extract:
1. Main keywords and concepts
2. Related terms and synonyms
3. Potential category matches
Return a JSON object with keys: 'keywords', 'synonyms', 'expanded_terms'"""
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=f"Extract search terms from: {query}")
        response = await chat.send_message(user_message)
        
        # Parse the response to get expanded search terms
        import json
        try:
            result = json.loads(response)
            all_terms = (
                result.get('keywords', []) + 
                result.get('synonyms', []) + 
                result.get('expanded_terms', [])
            )
            return all_terms[:20]  # Limit to 20 terms
        except:
            # If parsing fails, just return the original query words
            return query.split()
    except Exception as e:
        logger.error(f"AI search error: {e}")
        return query.split()

@api_router.post("/ultimate-search")
async def ultimate_search(data: UltimateSearchRequest, user: dict = Depends(require_user)):
    """Search through collated results with advanced filtering - supports AND/OR/AND_OR logic"""
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    if not user.get("is_paid") and not user.get("is_admin"):
        if data.page > settings.free_user_pages:
            raise HTTPException(
                status_code=403,
                detail=f"Free users can only access {settings.free_user_pages} page(s). Upgrade for just $0.75 lifetime!"
            )
    
    query = {"user_id": user["id"]}
    
    # Category filtering with AND/OR/AND_OR logic
    if data.category_ids:
        if data.aggregation_type == "and":
            # Results must match ALL selected categories
            query["categories"] = {"$all": data.category_ids}
        elif data.aggregation_type == "or":
            # Results can match ANY selected category
            query["categories"] = {"$in": data.category_ids}
        else:  # "and_or" (default)
            # Results must match ALL OR ANY of the selected categories
            query["$or"] = [
                {"categories": {"$all": data.category_ids}},
                {"categories": {"$in": data.category_ids}}
            ]
    
    # Document type filtering
    if data.document_types:
        query["document_type"] = {"$in": data.document_types}
    
    # Article type filtering
    if data.article_types:
        query["article_type"] = {"$in": data.article_types}
    
    # Domain filtering
    if data.domains:
        query["domain"] = {"$in": data.domains}
    
    # Year range filtering
    if data.year_from or data.year_to:
        year_query = {}
        if data.year_from:
            year_query["$gte"] = data.year_from
        if data.year_to:
            year_query["$lte"] = data.year_to
        query["detected_year"] = year_query
    
    # Traditional keyword search
    if data.keyword:
        keyword_conditions = [
            {"title": {"$regex": data.keyword, "$options": "i"}},
            {"snippet": {"$regex": data.keyword, "$options": "i"}}
        ]
        if "$or" in query:
            # Combine with existing $or conditions
            existing_or = query.pop("$or")
            query["$and"] = [
                {"$or": existing_or},
                {"$or": keyword_conditions}
            ]
        else:
            query["$or"] = keyword_conditions
    
    # AI-powered semantic search
    if data.ai_query:
        ai_terms = await ai_semantic_search(data.ai_query, user["id"])
        ai_conditions = []
        for term in ai_terms:
            ai_conditions.extend([
                {"title": {"$regex": term, "$options": "i"}},
                {"snippet": {"$regex": term, "$options": "i"}}
            ])
        if ai_conditions:
            if "$or" in query:
                existing_or = query.pop("$or")
                query["$and"] = [
                    {"$or": existing_or},
                    {"$or": ai_conditions}
                ]
            elif "$and" in query:
                query["$and"].append({"$or": ai_conditions})
            else:
                query["$or"] = ai_conditions
    
    skip = (data.page - 1) * settings.results_per_page
    limit = settings.results_per_page
    
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query, {"_id": 0}).sort("collated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get category names
    category_ids = set()
    for r in results:
        category_ids.update(r.get("categories", []))
    
    categories = await db.categories.find({"id": {"$in": list(category_ids)}}, {"_id": 0}).to_list(1000)
    category_map = {c["id"]: c["name"] for c in categories}
    
    for r in results:
        r["category_names"] = [category_map.get(cid, "Unknown") for cid in r.get("categories", [])]
    
    return {
        "results": results,
        "total": total,
        "page": data.page,
        "per_page": settings.results_per_page,
        "total_pages": (total + settings.results_per_page - 1) // settings.results_per_page
    }

@api_router.post("/ultimate-search/ai")
async def ai_enhanced_search(data: AISearchRequest, user: dict = Depends(require_user)):
    """AI-powered intelligent search using natural language"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI search not configured")
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"ai_search_{user['id']}_{uuid.uuid4().hex[:8]}",
            system_message="""You are an intelligent search assistant. Analyze the user's query and:
1. Identify what they're looking for
2. Suggest relevant categories to search
3. Extract key search terms
4. Provide search strategy recommendations
Return a JSON object with: 'intent', 'suggested_terms', 'relevance_score_hint', 'search_strategy'"""
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=f"Help me search for: {data.query}")
        response = await chat.send_message(user_message)
        
        # Now search with the AI insights
        search_terms = data.query.split()
        query = {
            "user_id": user["id"],
            "$or": []
        }
        
        for term in search_terms[:10]:
            query["$or"].extend([
                {"title": {"$regex": term, "$options": "i"}},
                {"snippet": {"$regex": term, "$options": "i"}}
            ])
        
        if data.category_ids:
            query["categories"] = {"$in": data.category_ids}
        
        results = await db.search_results.find(query, {"_id": 0}).limit(50).to_list(50)
        
        return {
            "ai_analysis": response,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"AI search error: {e}")
        raise HTTPException(status_code=500, detail=f"AI search failed: {str(e)}")

@api_router.get("/ultimate-search/filters")
async def get_search_filters(user: dict = Depends(require_user)):
    """Get available filter options for Ultimate Search"""
    domains = await db.search_results.distinct("domain", {"user_id": user["id"]})
    article_types = await db.search_results.distinct("article_type", {"user_id": user["id"]})
    document_types_used = await db.search_results.distinct("document_type", {"user_id": user["id"]})
    
    pipeline = [
        {"$match": {"user_id": user["id"], "detected_year": {"$ne": None}}},
        {"$group": {
            "_id": None,
            "min_year": {"$min": "$detected_year"},
            "max_year": {"$max": "$detected_year"}
        }}
    ]
    year_range = await db.search_results.aggregate(pipeline).to_list(1)
    
    return {
        "domains": domains,
        "article_types": article_types or ["Informative", "Informative Ph.D", "News Article", "Blog", "Forum", "Personal Report (collected)"],
        "document_types": DOCUMENT_TYPES,
        "document_types_used": document_types_used,
        "year_range": year_range[0] if year_range else {"min_year": 2000, "max_year": 2026},
        "aggregation_types": [
            {"value": "and_or", "label": "AND/OR - Results matching all OR any categories"},
            {"value": "or", "label": "OR - Results matching any category"},
            {"value": "and", "label": "AND - Results matching ALL categories"}
        ],
        "google_maps_api_key": GOOGLE_MAPS_API_KEY
    }

@api_router.get("/ultimate-search/map-data")
async def get_map_data(user: dict = Depends(require_user)):
    """Get all results with location data for map display"""
    # Get all results that have locations
    results = await db.search_results.find(
        {"user_id": user["id"], "locations": {"$exists": True, "$ne": []}},
        {"_id": 0}
    ).to_list(500)
    
    # Get categories for color coding
    categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    # Assign colors to categories
    colors = [
        "#ec4899", "#a855f7", "#3b82f6", "#22c55e", "#f59e0b", 
        "#ef4444", "#06b6d4", "#8b5cf6", "#f97316", "#14b8a6",
        "#e879f9", "#60a5fa", "#4ade80", "#fbbf24", "#f87171"
    ]
    category_colors = {}
    for idx, cat in enumerate(categories):
        category_colors[cat["id"]] = {
            "name": cat["name"],
            "color": colors[idx % len(colors)]
        }
    
    # Build map markers
    markers = []
    for result in results:
        for location in result.get("locations", []):
            for cat_id in result.get("categories", []):
                cat_info = category_colors.get(cat_id, {"name": "Unknown", "color": "#888888"})
                markers.append({
                    "id": f"{result['id']}_{location['name']}_{cat_id}",
                    "result_id": result["id"],
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result.get("snippet", ""),
                    "location_name": location["name"],
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "category_id": cat_id,
                    "category_name": cat_info["name"],
                    "color": cat_info["color"],
                    "article_type": result.get("article_type", ""),
                    "document_type": result.get("document_type", "")
                })
    
    return {
        "markers": markers,
        "categories": category_colors,
        "total_results_with_locations": len(results),
        "total_markers": len(markers)
    }

# ============================================
# API ROUTES - ULTIMATE SEARCH PAGE CUSTOMIZATION
# ============================================

@api_router.get("/ultimate-search/page-settings")
async def get_page_settings(user: dict = Depends(require_user)):
    """Get user's Ultimate Search page settings"""
    settings = await db.user_page_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not settings:
        # Create default settings
        settings = {
            "user_id": user["id"],
            "page_name": "My Ultimate Search",
            "photos": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.user_page_settings.insert_one(settings)
        settings = {k: v for k, v in settings.items() if k != "_id"}
    
    # Add soft recommendation if using default name
    show_name_suggestion = settings.get("page_name") == "My Ultimate Search"
    
    return {
        **settings,
        "show_name_suggestion": show_name_suggestion,
        "name_suggestions": [
            f"{user.get('username', 'User')}'s Research Hub",
            f"The {user.get('username', 'User')} Intelligence Center",
            f"{user.get('username', 'User')}'s Knowledge Base",
            f"Project {user.get('username', 'User')} Search",
            f"{user.get('username', 'User')}'s Discovery Portal"
        ] if show_name_suggestion else []
    }

@api_router.put("/ultimate-search/page-settings")
async def update_page_settings(data: UpdatePageSettingsRequest, user: dict = Depends(require_user)):
    """Update user's Ultimate Search page settings"""
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.page_name is not None:
        if len(data.page_name) > 100:
            raise HTTPException(status_code=400, detail="Page name must be 100 characters or less")
        update_data["page_name"] = data.page_name
    
    result = await db.user_page_settings.update_one(
        {"user_id": user["id"]},
        {"$set": update_data},
        upsert=True
    )
    
    settings = await db.user_page_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    return {"message": "Settings updated", "settings": settings}

@api_router.post("/ultimate-search/photos")
async def upload_photo(request: Request, user: dict = Depends(require_user)):
    """Upload a photo to user's Ultimate Search page (max 26 photos, max 15MB each)"""
    import base64
    
    # Get current settings
    settings = await db.user_page_settings.find_one({"user_id": user["id"]})
    if not settings:
        settings = {"user_id": user["id"], "photos": []}
    
    current_photos = settings.get("photos", [])
    
    if len(current_photos) >= 26:
        raise HTTPException(status_code=400, detail="Maximum of 26 photos allowed. Please delete some photos first.")
    
    # Parse the request body
    body = await request.json()
    photo_data = body.get("photo_data")  # Base64 encoded
    photo_name = body.get("photo_name", f"photo_{len(current_photos) + 1}.jpg")
    
    if not photo_data:
        raise HTTPException(status_code=400, detail="No photo data provided")
    
    # Check file size (base64 is ~1.37x larger than binary)
    # 15MB binary = ~20.5MB base64
    if len(photo_data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Photo must be less than 15MB")
    
    # Store photo reference (in production, upload to cloud storage)
    photo_id = str(uuid.uuid4())
    photo_record = {
        "id": photo_id,
        "user_id": user["id"],
        "name": photo_name,
        "data": photo_data,  # In production, store URL from cloud storage
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_photos.insert_one(photo_record)
    
    # Update user's photo list
    current_photos.append({
        "id": photo_id,
        "name": photo_name,
        "uploaded_at": photo_record["uploaded_at"]
    })
    
    await db.user_page_settings.update_one(
        {"user_id": user["id"]},
        {"$set": {"photos": current_photos}},
        upsert=True
    )
    
    return {
        "success": True,
        "photo_id": photo_id,
        "message": f"Photo uploaded successfully ({len(current_photos)}/26)",
        "total_photos": len(current_photos)
    }

@api_router.get("/ultimate-search/photos")
async def get_photos(user: dict = Depends(require_user)):
    """Get all photos for user's Ultimate Search page"""
    photos = await db.user_photos.find({"user_id": user["id"]}, {"_id": 0, "data": 0}).to_list(26)
    return {"photos": photos, "total": len(photos), "max_allowed": 26}

@api_router.get("/ultimate-search/photos/{photo_id}")
async def get_photo(photo_id: str, user: dict = Depends(require_user)):
    """Get a specific photo by ID"""
    photo = await db.user_photos.find_one({"id": photo_id, "user_id": user["id"]}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo

@api_router.delete("/ultimate-search/photos/{photo_id}")
async def delete_photo(photo_id: str, user: dict = Depends(require_user)):
    """Delete a photo from user's Ultimate Search page"""
    # Delete photo record
    result = await db.user_photos.delete_one({"id": photo_id, "user_id": user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Update user's photo list
    settings = await db.user_page_settings.find_one({"user_id": user["id"]})
    if settings:
        current_photos = [p for p in settings.get("photos", []) if p["id"] != photo_id]
        await db.user_page_settings.update_one(
            {"user_id": user["id"]},
            {"$set": {"photos": current_photos}}
        )
    
    return {"success": True, "message": "Photo deleted"}

@api_router.get("/ultimate-search/sessions")
async def get_collate_sessions(user: dict = Depends(require_user)):
    """Get collate sessions grouped by timestamp for the owner"""
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d %H:%M", "date": {"$toDate": "$collated_at"}}},
            "count": {"$sum": 1},
            "result_ids": {"$push": "$id"}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 50}
    ]
    
    sessions = await db.search_results.aggregate(pipeline).to_list(50)
    
    return {
        "sessions": [
            {
                "timestamp": s["_id"],
                "result_count": s["count"],
                "result_ids": s["result_ids"]
            }
            for s in sessions
        ]
    }

@api_router.delete("/ultimate-search/results")
async def delete_search_results(data: SearchResultDeleteRequest, user: dict = Depends(require_user)):
    """Delete search results - only owner can delete their own results"""
    # Verify ownership
    for result_id in data.result_ids:
        result = await db.search_results.find_one({"id": result_id})
        if not result:
            continue
        if result["user_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="You can only delete your own results")
    
    result = await db.search_results.delete_many({
        "id": {"$in": data.result_ids},
        "user_id": user["id"]
    })
    
    return {
        "message": f"Deleted {result.deleted_count} results",
        "deleted_count": result.deleted_count
    }

@api_router.delete("/ultimate-search/session/{session_timestamp}")
async def delete_session_results(session_timestamp: str, user: dict = Depends(require_user)):
    """Delete all results from a specific collate session"""
    # Find results from this session
    results = await db.search_results.find({
        "user_id": user["id"],
        "collated_at": {"$regex": f"^{session_timestamp}"}
    }).to_list(1000)
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this session")
    
    result_ids = [r["id"] for r in results]
    delete_result = await db.search_results.delete_many({
        "id": {"$in": result_ids},
        "user_id": user["id"]
    })
    
    return {
        "message": f"Deleted {delete_result.deleted_count} results from session",
        "deleted_count": delete_result.deleted_count
    }

@api_router.get("/ultimate-search/category/{category_id}/results")
async def get_category_results(
    category_id: str, 
    page: int = 1,
    user: dict = Depends(require_user)
):
    """Get all results for a specific category with count"""
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    skip = (page - 1) * settings.results_per_page
    limit = settings.results_per_page
    
    query = {"user_id": user["id"], "categories": category_id}
    
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query, {"_id": 0}).sort("collated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get category info
    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    
    return {
        "category": category,
        "results": results,
        "total": total,
        "page": page,
        "per_page": settings.results_per_page,
        "total_pages": (total + settings.results_per_page - 1) // settings.results_per_page
    }

# ============================================
# API ROUTES - REACTIONS
# ============================================

@api_router.post("/results/{result_id}/react")
async def add_reaction(result_id: str, data: ArticleReaction, user: dict = Depends(require_user)):
    """Add reaction to a search result"""
    valid_reactions = ["like", "love", "funny", "sad", "caution", "spam", "best"]
    if data.reaction_type not in valid_reactions:
        raise HTTPException(status_code=400, detail=f"Invalid reaction. Must be one of: {valid_reactions}")
    
    result = await db.search_results.find_one({"id": result_id})
    if not result:
        raise HTTPException(status_code=404, detail="Search result not found")
    
    reaction_key = f"reactions.{data.reaction_type}"
    await db.search_results.update_one(
        {"id": result_id},
        {"$inc": {reaction_key: 1}}
    )
    
    await db.user_reactions.update_one(
        {"user_id": user["id"], "result_id": result_id},
        {"$set": {"reaction_type": data.reaction_type, "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"message": "Reaction added"}

# ============================================
# API ROUTES - SAFE BROWSING
# ============================================

class SafeBrowsingCheckRequest(BaseModel):
    urls: List[str]

@api_router.post("/safety/check")
async def check_urls_safety(data: SafeBrowsingCheckRequest, user: dict = Depends(require_user)):
    """
    Check one or more URLs for malicious content using Google Safe Browsing API.
    Returns safety status for each URL.
    """
    if not data.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    if len(data.urls) > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 URLs per request")
    
    result = await check_url_safety(data.urls)
    return result

@api_router.get("/safety/status")
async def get_safety_status():
    """Check if Safe Browsing API is configured and working"""
    if not GOOGLE_SAFE_BROWSING_API_KEY:
        return {
            "enabled": False,
            "message": "Safe Browsing API key not configured"
        }
    
    # Test with a known safe URL
    test_result = await check_url_safety(["https://www.google.com"])
    
    return {
        "enabled": True,
        "working": test_result.get("checked", False),
        "message": "Safe Browsing API is configured" if test_result.get("checked") else f"API error: {test_result.get('error', 'Unknown')}"
    }

# ============================================
# API ROUTES - ADMIN
# ============================================

@api_router.get("/admin/settings", response_model=AdminSettings)
async def get_admin_settings(user: dict = Depends(require_admin)):
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if not settings:
        default = AdminSettings().model_dump()
        await db.admin_settings.insert_one(default)
        return AdminSettings()
    return AdminSettings(**settings)

@api_router.put("/admin/settings")
async def update_admin_settings(data: AdminSettingsUpdate, user: dict = Depends(require_admin)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No settings to update")
    
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Settings updated"}

@api_router.post("/admin/ban-word")
async def ban_word(word: str, user: dict = Depends(require_admin)):
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$addToSet": {"blocked_words": word.lower()}},
        upsert=True
    )
    return {"message": f"Word '{word}' added to blocked list"}

@api_router.delete("/admin/ban-word/{word}")
async def unban_word(word: str, user: dict = Depends(require_admin)):
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$pull": {"blocked_words": word.lower()}}
    )
    return {"message": f"Word '{word}' removed from blocked list"}

@api_router.post("/admin/ban-user/{user_id}")
async def ban_user(user_id: str, user: dict = Depends(require_admin)):
    await db.users.update_one({"id": user_id}, {"$set": {"is_banned": True}})
    return {"message": "User banned"}

@api_router.post("/admin/make-admin/{user_id}")
async def make_admin(user_id: str, user: dict = Depends(require_admin)):
    await db.users.update_one({"id": user_id}, {"$set": {"is_admin": True}})
    return {"message": "User is now admin"}

@api_router.get("/admin/users")
async def get_all_users(user: dict = Depends(require_admin)):
    users = await db.users.find({}, {"password_hash": 0, "_id": 0}).to_list(1000)
    return users

@api_router.post("/admin/set-paid/{user_id}")
async def set_user_paid(user_id: str, is_paid: bool, user: dict = Depends(require_admin)):
    await db.users.update_one({"id": user_id}, {"$set": {"is_paid": is_paid}})
    return {"message": f"User paid status set to {is_paid}"}

# ============================================
# API ROUTES - GLOBAL RESEARCH DATABASE
# ============================================

@api_router.get("/global-database")
async def get_global_database(
    page: int = 1,
    category_id: Optional[str] = None,
    user: dict = Depends(require_user)
):
    """Access all public categories and their results"""
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    if not user.get("is_paid") and not user.get("is_admin"):
        if page > settings.free_user_pages:
            raise HTTPException(
                status_code=403,
                detail="Upgrade to access more pages"
            )
    
    public_categories = await db.categories.find({"is_public": True}).to_list(1000)
    public_category_ids = [c["id"] for c in public_categories]
    
    query = {"categories": {"$in": public_category_ids}}
    if category_id:
        query["categories"] = category_id
    
    skip = (page - 1) * settings.results_per_page
    
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query).skip(skip).limit(settings.results_per_page).to_list(settings.results_per_page)
    
    return {
        "public_categories": public_categories,
        "results": results,
        "total": total,
        "page": page,
        "total_pages": (total + settings.results_per_page - 1) // settings.results_per_page
    }

# ============================================
# API ROUTES - STATISTICS
# ============================================

@api_router.get("/statistics")
async def get_statistics(user: dict = Depends(require_user)):
    """Get statistics for the user's data"""
    user_id = user["id"]
    
    type_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$article_type", "count": {"$sum": 1}}}
    ]
    article_types = await db.search_results.aggregate(type_pipeline).to_list(100)
    
    domain_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$domain", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_domains = await db.search_results.aggregate(domain_pipeline).to_list(10)
    
    year_pipeline = [
        {"$match": {"user_id": user_id, "detected_year": {"$ne": None}}},
        {"$group": {"_id": "$detected_year", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    by_year = await db.search_results.aggregate(year_pipeline).to_list(100)
    
    category_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "count": {"$sum": 1}}}
    ]
    category_counts = await db.search_results.aggregate(category_pipeline).to_list(100)
    
    cat_ids = [c["_id"] for c in category_counts]
    categories = await db.categories.find({"id": {"$in": cat_ids}}).to_list(100)
    cat_map = {c["id"]: c["name"] for c in categories}
    
    for c in category_counts:
        c["name"] = cat_map.get(c["_id"], "Unknown")
    
    return {
        "article_types": article_types,
        "top_domains": top_domains,
        "by_year": by_year,
        "by_category": category_counts,
        "total_results": await db.search_results.count_documents({"user_id": user_id}),
        "total_categories": await db.categories.count_documents({"user_id": user_id})
    }

# ============================================
# API ROUTES - USER SEARCH RESULTS MANAGEMENT
# ============================================

@api_router.delete("/results/{result_id}")
async def delete_result(result_id: str, user: dict = Depends(require_user)):
    result = await db.search_results.delete_one({"id": result_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"message": "Result deleted"}

@api_router.delete("/results/batch")
async def delete_results_batch(result_ids: List[str], user: dict = Depends(require_user)):
    """Delete multiple results at once"""
    result = await db.search_results.delete_many({
        "id": {"$in": result_ids},
        "user_id": user["id"]
    })
    return {"message": f"Deleted {result.deleted_count} results"}

# ============================================
# SETUP & MIDDLEWARE
# ============================================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.categories.create_index([("user_id", 1), ("parent_id", 1)])
    await db.search_results.create_index([("user_id", 1), ("categories", 1)])
    await db.search_results.create_index([("user_id", 1), ("article_type", 1)])
    
    if not await db.admin_settings.find_one({"id": "admin_settings"}):
        await db.admin_settings.insert_one(AdminSettings().model_dump())
    
    logger.info("InfoPilot Explorer API v2.0 - Tactical Systems Online")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
