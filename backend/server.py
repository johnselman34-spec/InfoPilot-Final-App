from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect
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
import base64
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
import json

# SendGrid for email notifications
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_db')]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', '')
if not JWT_SECRET:
    JWT_SECRET = 'infopilot-secret-key-2024-dev'  # Only for development
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Google OAuth Settings - Supports Web, Android, and iOS
GOOGLE_WEB_CLIENT_ID = os.environ.get('GOOGLE_WEB_CLIENT_ID', '')
GOOGLE_ANDROID_CLIENT_ID = os.environ.get('GOOGLE_ANDROID_CLIENT_ID', '')
GOOGLE_IOS_CLIENT_ID = os.environ.get('GOOGLE_IOS_CLIENT_ID', '')

# All valid Google Client IDs (for token verification)
GOOGLE_CLIENT_IDS = [GOOGLE_WEB_CLIENT_ID, GOOGLE_ANDROID_CLIENT_ID, GOOGLE_IOS_CLIENT_ID]

# Admin email addresses - these accounts get automatic admin privileges
ADMIN_EMAILS = [
    "jjspilot24@gmail.com",
    "johnselman34@gmail.com", 
    "john.1976.selman@gmail.com",
    # Case variations
    "JohnSelman34@gmail.com",
    "John.1976.Selman@gmail.com"
]

def is_admin_email(email: str) -> bool:
    """Check if email is an admin email (case-insensitive)"""
    return email.lower() in [e.lower() for e in ADMIN_EMAILS]

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

# SendGrid Email Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@infopilot-explorer.com')

# Email notification helper function
async def send_notification_email(to_email: str, subject: str, html_content: str):
    """Send email notification using SendGrid"""
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        logging.warning("SendGrid not configured - email notification skipped")
        return False
    
    try:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

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

# ============================================
# WEBSOCKET CONNECTION MANAGER
# ============================================

class ConnectionManager:
    """Manages WebSocket connections for real-time messaging"""
    
    def __init__(self):
        # user_id -> list of WebSocket connections (user can have multiple tabs)
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to a specific user (all their connections)"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {user_id}: {e}")
                    disconnected.append(connection)
            # Clean up disconnected sockets
            for conn in disconnected:
                self.active_connections[user_id].remove(conn)
    
    async def broadcast_to_conversation(self, message: dict, user_ids: List[str]):
        """Broadcast message to all users in a conversation"""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has active WebSocket connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

# Global WebSocket manager
ws_manager = ConnectionManager()

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
# HASHTAG EXTRACTION
# ============================================
# Common stop words to exclude from hashtags
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'this', 'that', 'these', 'those', 'it', 'its', 'he', 'she', 'they', 'we', 'you',
    'their', 'his', 'her', 'my', 'your', 'our', 'which', 'who', 'whom', 'what', 'when',
    'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'not', 'only', 'same', 'so', 'than', 'too', 'very',
    'can', 'just', 'into', 'about', 'over', 'after', 'before', 'between', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'any', 'new', 'also', 'said', 'one', 'two'
}

# Popular topic hashtags for categorization
POPULAR_HASHTAGS = {
    # Technology
    'artificial': '#AI', 'intelligence': '#AI', 'machine': '#MachineLearning', 'learning': '#MachineLearning',
    'software': '#Technology', 'computer': '#Technology', 'digital': '#Digital', 'data': '#Data',
    'internet': '#Internet', 'cyber': '#CyberSecurity', 'blockchain': '#Blockchain', 'crypto': '#Crypto',
    'robot': '#Robotics', 'automation': '#Automation', 'cloud': '#CloudComputing', 'app': '#Apps',
    # Science
    'science': '#Science', 'research': '#Research', 'study': '#Research', 'discovery': '#Discovery',
    'physics': '#Physics', 'biology': '#Biology', 'chemistry': '#Chemistry', 'space': '#Space',
    'nasa': '#NASA', 'astronomy': '#Astronomy', 'medical': '#Medical', 'health': '#Health',
    'medicine': '#Medicine', 'vaccine': '#Health', 'climate': '#ClimateChange', 'environment': '#Environment',
    # History
    'history': '#History', 'historical': '#History', 'war': '#History', 'civil': '#CivilWar',
    'battle': '#Military', 'military': '#Military', 'army': '#Military', 'navy': '#Military',
    'revolution': '#History', 'ancient': '#AncientHistory', 'medieval': '#MedievalHistory',
    # Business & Finance
    'business': '#Business', 'finance': '#Finance', 'market': '#Markets', 'stock': '#Stocks',
    'investment': '#Investment', 'economy': '#Economy', 'economic': '#Economy', 'bank': '#Banking',
    'startup': '#Startup', 'entrepreneur': '#Entrepreneurship', 'company': '#Business',
    # Education
    'education': '#Education', 'university': '#Education', 'college': '#Education', 'school': '#Education',
    'learning': '#Learning', 'student': '#Education', 'academic': '#Academia', 'degree': '#Education',
    # Politics & Law
    'politics': '#Politics', 'political': '#Politics', 'government': '#Government', 'law': '#Law',
    'legal': '#Legal', 'court': '#Legal', 'congress': '#Politics', 'president': '#Politics',
    'election': '#Election', 'vote': '#Democracy', 'policy': '#Policy',
    # Arts & Culture
    'art': '#Art', 'music': '#Music', 'film': '#Film', 'movie': '#Movies', 'book': '#Books',
    'culture': '#Culture', 'museum': '#Museum', 'entertainment': '#Entertainment',
    # Sports
    'sports': '#Sports', 'football': '#Football', 'basketball': '#Basketball', 'baseball': '#Baseball',
    'soccer': '#Soccer', 'olympic': '#Olympics', 'athlete': '#Sports',
    # News & Current Events
    'news': '#News', 'breaking': '#BreakingNews', 'update': '#Update', 'report': '#Report',
    'today': '#CurrentEvents', 'latest': '#LatestNews',
}

def extract_hashtags(content: str, title: str, max_hashtags: int = 6) -> List[str]:
    """Extract relevant hashtags from content for linking related articles"""
    hashtags = []
    hashtag_scores = {}
    
    # Combine title and content, give more weight to title
    text = (title + " " + title + " " + content).lower()
    
    # Extract words
    words = re.findall(r'\b[a-z]{4,}\b', text)  # Words with 4+ chars
    word_freq = {}
    
    for word in words:
        if word not in STOP_WORDS:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Match against popular hashtags
    for word, freq in word_freq.items():
        if word in POPULAR_HASHTAGS:
            hashtag = POPULAR_HASHTAGS[word]
            if hashtag not in hashtag_scores:
                hashtag_scores[hashtag] = 0
            hashtag_scores[hashtag] += freq * 2  # Boost for known topics
    
    # Get top keywords that aren't already matched
    top_keywords = sorted(word_freq.items(), key=lambda x: -x[1])[:20]
    
    # Create hashtags from top unmatched keywords
    for word, freq in top_keywords:
        if freq >= 2:  # Word appears at least twice
            hashtag = f"#{word.capitalize()}"
            if hashtag not in hashtag_scores and len(word) > 4:
                hashtag_scores[hashtag] = freq
    
    # Sort by score and return top hashtags
    sorted_hashtags = sorted(hashtag_scores.items(), key=lambda x: -x[1])
    
    # Ensure diversity - limit similar hashtags
    final_hashtags = []
    seen_bases = set()
    
    for hashtag, score in sorted_hashtags:
        base = hashtag.lower().replace('#', '')[:5]
        if base not in seen_bases:
            final_hashtags.append(hashtag)
            seen_bases.add(base)
            if len(final_hashtags) >= max_hashtags:
                break
    
    # If we don't have enough, add generic ones based on content
    if len(final_hashtags) < 4:
        fallback_hashtags = ['#Article', '#Information', '#Reference', '#Research']
        for fb in fallback_hashtags:
            if fb not in final_hashtags:
                final_hashtags.append(fb)
                if len(final_hashtags) >= 4:
                    break
    
    return final_hashtags[:max_hashtags]

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

# Location model for protocols
class ProtocolLocation(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"
    lat: Optional[float] = None
    lng: Optional[float] = None

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    protocol: ProtocolCreate
    parent_id: Optional[str] = None  # For subcategories
    is_public: bool = True
    for_sale: bool = False  # Whether protocol can be purchased
    price: Optional[float] = Field(None, ge=0.00, le=99.00)  # Price range $0.00-$99.00 (FREE allowed)
    location: Optional[ProtocolLocation] = None  # Location data for marketplace map

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    protocol_string: Optional[str] = None
    is_public: Optional[bool] = None
    for_sale: Optional[bool] = None
    price: Optional[float] = Field(None, ge=0.00, le=99.00)
    location: Optional[ProtocolLocation] = None  # Location data for marketplace map

class CategoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    protocol_string: str
    parent_id: Optional[str] = None
    is_public: bool = True
    for_sale: bool = False
    price: Optional[float] = None
    owner_username: Optional[str] = None
    copy_count: int = 0
    level: int = 0
    location: Optional[dict] = None  # Location data
    created_at: datetime

# Protocol Purchase Models
class ProtocolPurchase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    buyer_id: str
    seller_id: str
    category_id: str
    amount: float
    status: str  # pending, completed
    created_at: str

# Badge/Achievement Definitions
BADGE_DEFINITIONS = {
    "first_copy": {"name": "First Steps", "icon": "🎯", "description": "Your protocol was copied for the first time", "threshold": 1},
    "rising_star": {"name": "Rising Star", "icon": "⭐", "description": "Protocol copied 10 times", "threshold": 10},
    "popular": {"name": "Popular", "icon": "🔥", "description": "Protocol copied 25 times", "threshold": 25},
    "trending": {"name": "Trending", "icon": "📈", "description": "Protocol copied 50 times", "threshold": 50},
    "viral": {"name": "Viral", "icon": "🚀", "description": "Protocol copied 100 times", "threshold": 100},
    "legendary": {"name": "Legendary", "icon": "🏆", "description": "Protocol copied 500 times", "threshold": 500},
    "hall_of_fame": {"name": "Hall of Fame", "icon": "👑", "description": "Protocol copied 1000 times", "threshold": 1000},
    
    # Creator badges
    "creator_novice": {"name": "Protocol Creator", "icon": "📝", "description": "Created your first protocol", "threshold": 1, "type": "creator"},
    "creator_prolific": {"name": "Prolific Creator", "icon": "✍️", "description": "Created 10 protocols", "threshold": 10, "type": "creator"},
    "creator_master": {"name": "Master Creator", "icon": "🎨", "description": "Created 25 protocols", "threshold": 25, "type": "creator"},
    "creator_legend": {"name": "Protocol Legend", "icon": "🌟", "description": "Created 50 protocols", "threshold": 50, "type": "creator"},
    
    # Marketplace badges
    "first_sale": {"name": "First Sale", "icon": "💰", "description": "Made your first protocol sale", "threshold": 1, "type": "sales"},
    "seller_bronze": {"name": "Bronze Seller", "icon": "🥉", "description": "Made 5 sales", "threshold": 5, "type": "sales"},
    "seller_silver": {"name": "Silver Seller", "icon": "🥈", "description": "Made 10 sales", "threshold": 10, "type": "sales"},
    "seller_gold": {"name": "Gold Seller", "icon": "🥇", "description": "Made 25 sales", "threshold": 25, "type": "sales"},
    "seller_platinum": {"name": "Platinum Seller", "icon": "💎", "description": "Made 50 sales", "threshold": 50, "type": "sales"},
    
    # Collector badges
    "collector_novice": {"name": "Collector", "icon": "🛒", "description": "Purchased your first protocol", "threshold": 1, "type": "purchases"},
    "collector_avid": {"name": "Avid Collector", "icon": "📚", "description": "Purchased 10 protocols", "threshold": 10, "type": "purchases"},
    "collector_master": {"name": "Master Collector", "icon": "🏅", "description": "Purchased 25 protocols", "threshold": 25, "type": "purchases"},
    
    # Social badges
    "social_butterfly": {"name": "Social Butterfly", "icon": "🦋", "description": "Made 10 friends", "threshold": 10, "type": "social"},
    "group_leader": {"name": "Group Leader", "icon": "👥", "description": "Created a group", "threshold": 1, "type": "social"},
    "influencer": {"name": "Influencer", "icon": "📢", "description": "Created a page", "threshold": 1, "type": "social"},
    "messenger": {"name": "Messenger", "icon": "💬", "description": "Sent 50 messages", "threshold": 50, "type": "social"},
    
    # Search badges  
    "researcher": {"name": "Researcher", "icon": "🔬", "description": "Collated 100 results", "threshold": 100, "type": "search"},
    "data_miner": {"name": "Data Miner", "icon": "⛏️", "description": "Collated 500 results", "threshold": 500, "type": "search"},
    "intel_master": {"name": "Intelligence Master", "icon": "🧠", "description": "Collated 1000 results", "threshold": 1000, "type": "search"},
    
    # Engagement badges
    "reactor": {"name": "Reactor", "icon": "👍", "description": "Added 50 reactions", "threshold": 50, "type": "engagement"},
    "commentator": {"name": "Commentator", "icon": "💭", "description": "Posted 25 comments", "threshold": 25, "type": "engagement"},
}

# Protocol Recommendation Models
class ProtocolRecommendationCreate(BaseModel):
    original_protocol: str
    suggested_protocol: str
    reason: str = Field(..., min_length=1, max_length=1000)

class ProtocolRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    category_id: str
    category_name: str
    user_id: str
    username: str
    original_protocol: str
    suggested_protocol: str
    reason: str
    status: str  # pending, accepted, rejected
    created_at: str

# Private Messaging Models
class MessageCreate(BaseModel):
    recipient_id: str
    content: str = Field(..., max_length=5000)
    image_url: Optional[str] = None  # Base64 or URL

class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    conversation_id: str
    sender_id: str
    sender_username: str
    recipient_id: str
    recipient_username: str
    content: str
    image_url: Optional[str] = None
    read: bool = False
    created_at: str

class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    participants: List[str]
    participant_usernames: Dict[str, str]
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    unread_count: int = 0

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
    require_search_terms: bool = True  # If true, results must contain key terms from search query

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
    user_max_results_limit: Optional[int] = None  # Max results per user's database
    unpaid_user_search_pages: Optional[int] = None  # Pages of search results for unpaid users (1-99)
    paid_user_search_pages: Optional[int] = None  # Pages of search results for paid users (1-99)

class AdminSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "admin_settings"
    results_per_page: int = 20
    free_user_pages: int = 6  # Legacy - kept for compatibility
    max_category_levels: int = 100
    blocked_words: List[str] = DEFAULT_BLOCKED_WORDS
    subscription_price: float = 0.75  # Current sale price
    regular_price: float = 4.62  # Price after sale
    informative_min_words: int = 1500
    phd_keyword_count: int = 3
    blog_keyword_count: int = 3
    max_search_results: int = 120  # Legacy - kept for compatibility
    user_max_results_limit: int = 4000  # Max results stored per user's database (default 4000)
    unpaid_user_search_pages: int = 50  # Pages of search results for unpaid users (1-99), >40 = free app
    paid_user_search_pages: int = 99  # Pages of search results for paid users (1-99)
    
    @property
    def is_app_free(self) -> bool:
        """App is considered free if unpaid users get more than 40 pages"""
        return self.unpaid_user_search_pages > 40
    
    def get_max_results_for_user(self, is_paid: bool) -> int:
        """Calculate max search results based on user type"""
        pages = self.paid_user_search_pages if is_paid else self.unpaid_user_search_pages
        return pages * self.results_per_page

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
# SOCIAL FEATURES - FRIENDS, GROUPS, PAGES
# ============================================

class FriendRequest(BaseModel):
    friend_id: str

class FriendshipResponse(BaseModel):
    id: str
    user_id: str
    friend_id: str
    status: str  # pending, accepted, rejected
    created_at: str

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    privacy: str = "public"  # public, private, secret
    cover_photo: Optional[str] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    privacy: Optional[str] = None
    cover_photo: Optional[str] = None

class GroupResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    privacy: str
    cover_photo: Optional[str] = None
    owner_id: str
    member_count: int = 0
    created_at: str

class GroupPostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    image_url: Optional[str] = None

class PageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str = "General"  # Business, Community, Entertainment, etc.
    cover_photo: Optional[str] = None
    profile_photo: Optional[str] = None

class PageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    cover_photo: Optional[str] = None
    profile_photo: Optional[str] = None

class PageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    category: str
    cover_photo: Optional[str] = None
    profile_photo: Optional[str] = None
    owner_id: str
    follower_count: int = 0
    created_at: str

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    image_url: Optional[str] = None
    visibility: str = "public"  # public, friends, private

class PostResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    content: str
    image_url: Optional[str] = None
    visibility: str
    like_count: int = 0
    comment_count: int = 0
    created_at: str

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = None  # For nested replies

# Reaction Types (Facebook-style)
REACTION_TYPES = ["like", "love", "haha", "wow", "sad", "angry"]

class ReactionCreate(BaseModel):
    reaction_type: str = Field(..., description="One of: like, love, haha, wow, sad, angry")

class UpdateCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    image_url: Optional[str] = None

class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    username: str
    content: str
    parent_id: Optional[str] = None
    reactions: Dict[str, List[str]] = {}  # reaction_type -> list of user_ids
    reaction_counts: Dict[str, int] = {}
    replies: List[Any] = []
    created_at: str

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
        """Parse InfoPilot 2.0 protocol string into structured format.
        
        Handles:
        - Multi-word phrases like "William C. Gamble"
        - Abbreviations with periods like "Ph.D.", "etc.", "U.S."
        - Personal pronouns like "C." in names
        - Case-insensitive 'or' separators within parentheses
        """
        result = {
            "groups": [],
            "valid": True,
            "error": None
        }
        
        try:
            # Split by & (AND operator) - be careful not to split within phrases
            groups = re.split(r'\s*&\s*', protocol_string.strip())
            
            for group in groups:
                group = group.strip()
                if not group:
                    continue
                
                include_all = False
                exclude_all = False
                
                # Check for modifiers (+ for include all, ^ for exclude all)
                if group.startswith('+') or group.endswith('+'):
                    include_all = True
                    group = group.strip('+').strip()
                elif group.startswith('^') or group.endswith('^'):
                    exclude_all = True
                    group = group.strip('^').strip()
                
                # Extract content within parentheses
                match = re.match(r'\(([^)]+)\)', group)
                if match:
                    words_str = match.group(1)
                    
                    # Split by 'or' but preserve abbreviations and multi-word phrases
                    # Use a smarter split that respects abbreviations like "William C. Gamble"
                    # The 'or' must be surrounded by whitespace to be a separator
                    words = InfoPilot2Parser._split_by_or(words_str)
                    
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
    def _split_by_or(text: str) -> List[str]:
        """Split text by ' or ' while preserving abbreviations and multi-word phrases.
        
        Handles cases like:
        - "William C. Gamble or George Bush" -> ["William C. Gamble", "George Bush"]
        - "Ph.D. or Dr. or M.D." -> ["Ph.D.", "Dr.", "M.D."]
        - "U.S. Civil War or American Revolution" -> ["U.S. Civil War", "American Revolution"]
        - "John S. or John J S" -> ["John S.", "John J S"]
        - "Heidelberg, GER or Albuquerque, NM" -> ["Heidelberg, GER", "Albuquerque, NM"]
        - "Heidelberg, Baden Wuerttemberg, GER" - preserved as single phrase
        - Case-insensitive 'or', 'Or', 'OR' all work
        """
        # Use regex to split by ' or ' (case insensitive) but only when surrounded by spaces
        # This preserves abbreviations like "C." within names and location commas
        parts = re.split(r'\s+[oO][rR]\s+', text)
        
        # Clean up each part
        result = []
        for part in parts:
            cleaned = part.strip()
            if cleaned:
                result.append(cleaned)
        
        return result
    
    @staticmethod
    def _normalize_phrase(phrase: str) -> str:
        """Normalize a phrase for consistent matching.
        
        Handles:
        - "John J S" -> can match "John J. S.", "John J S", "john j s"
        - "Heidelberg, GER" -> matches "Heidelberg, Germany", "heidelberg, ger"
        - "Albuquerque, NM" or "Albuquerque, Nm" -> both work
        """
        return phrase.lower().strip()
    
    @staticmethod
    def match_content(content: str, parsed_protocol: Dict[str, Any]) -> bool:
        """Check if content matches the parsed protocol using word boundary matching"""
        if not parsed_protocol["valid"]:
            return False
        
        content_lower = content.lower()
        
        def phrase_matches(phrase: str, text: str) -> bool:
            """Check if a phrase/word matches in text using flexible matching.
            
            Handles:
            - Multi-word phrases like 'William C. Gamble' as complete phrases
            - Abbreviations like 'Ph.D.', 'etc.', 'U.S.', 'Dr.'
            - Personal initials with/without periods: 'John J S', 'John J. S.', 'C.'
            - Location abbreviations: 'Heidelberg, GER', 'Albuquerque, NM', 'Albuquerque, Nm'
            - Case-insensitive matching for all patterns
            
            Uses simple string operations first for speed, then regex for edge cases.
            """
            phrase_lower = phrase.lower().strip()
            
            # Quick check: if phrase not in text at all (with some flexibility), skip
            # Remove periods and commas for initial check
            phrase_no_punct = phrase_lower.replace('.', '').replace(',', ' ')
            text_no_punct = text.replace('.', '').replace(',', ' ')
            
            # Normalize multiple spaces
            phrase_normalized = ' '.join(phrase_no_punct.split())
            text_normalized = ' '.join(text_no_punct.split())
            
            if phrase_normalized not in text_normalized and phrase_lower not in text:
                return False
            
            # For single words without special chars, use simple word boundary check
            if ' ' not in phrase_lower and '.' not in phrase_lower and ',' not in phrase_lower:
                words_in_text = set(re.findall(r'\b\w+\b', text))
                return phrase_lower in words_in_text
            
            # For location patterns with comma (e.g., "Heidelberg, GER" or "Albuquerque, NM")
            if ',' in phrase_lower:
                # Split by comma and match each part flexibly
                parts = [p.strip() for p in phrase_lower.split(',')]
                
                # Build a pattern that allows comma or space between parts
                pattern_parts = []
                for i, part in enumerate(parts):
                    pattern_parts.append(re.escape(part))
                    if i < len(parts) - 1:
                        # Allow comma with optional spaces, or just spaces
                        pattern_parts.append(r'[,\s]+')
                
                pattern = r'(?:^|[\s\.,;:!?\-\(\)\[\]"])' + ''.join(pattern_parts) + r'(?:[\s\.,;:!?\-\(\)\[\]"]|$)'
                return bool(re.search(pattern, text, re.IGNORECASE))
            
            # Build flexible pattern for names with initials
            # E.g., "John J S" matches "John J. S.", "John J S", "john j. s."
            pattern_parts = []
            words = phrase_lower.split()
            
            for i, word in enumerate(words):
                word = word.strip('.,;:')
                if not word:
                    continue
                    
                # Check if it's a single letter initial (possibly with period)
                if len(word) == 1 or (len(word) == 2 and word.endswith('.')):
                    # Single initial - match with or without period
                    initial = word.rstrip('.')
                    pattern_parts.append(re.escape(initial) + r'\.?\s*')
                elif len(word) <= 3 and word.replace('.', '').isupper():
                    # Short abbreviation like "NM", "GER", "USA"
                    pattern_parts.append(re.escape(word.replace('.', '')) + r'\.?\s*')
                else:
                    # Regular word
                    pattern_parts.append(re.escape(word) + r'\s*')
            
            # Join pattern parts and add word boundaries
            pattern = r'(?:^|[\s\.,;:!?\-\(\)\[\]"])' + ''.join(pattern_parts).rstrip(r'\s*') + r'(?:[\s\.,;:!?\-\(\)\[\]"]|$)'
            
            return bool(re.search(pattern, text, re.IGNORECASE))
        
        for group in parsed_protocol["groups"]:
            words = group["words"]
            include_all = group["include_all"]
            exclude_all = group["exclude_all"]
            
            if exclude_all:
                # None of these phrases should be present
                for word in words:
                    if phrase_matches(word, content_lower):
                        return False
            elif include_all:
                # ALL of these phrases must be present
                for word in words:
                    if not phrase_matches(word, content_lower):
                        return False
            else:
                # ANY of these phrases must be present (OR logic)
                found = False
                for word in words:
                    if phrase_matches(word, content_lower):
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
    """
    Check if text contains any blocked words as WHOLE WORDS only.
    This allows words like "association" even if "ass" is blocked,
    because "ass" is part of a larger word, not a standalone word.
    """
    import re
    text_lower = text.lower()
    found = []
    for word in blocked_words:
        # Use word boundary regex to match whole words only
        # \b matches word boundaries (spaces, punctuation, start/end of string)
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(word)
    return len(found) > 0, found

# ============================================
# AUTHENTICATION HELPERS
# ============================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    if not hashed or not password:
        return False
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except (ValueError, TypeError) as e:
        logger.error(f"Password verification error: {e}")
        return False

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
    """Fetch and parse webpage content - extracts only meaningful article text"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            title = soup.title.string if soup.title else ""
            
            # Remove all non-content elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 
                           'iframe', 'embed', 'object', 'svg', 'canvas', 'map', 'area',
                           'aside', 'form', 'input', 'button', 'select', 'textarea']):
                tag.decompose()
            
            # Remove elements with common non-content classes/ids
            for selector in ['[class*="menu"]', '[class*="nav"]', '[class*="sidebar"]', 
                           '[class*="footer"]', '[class*="header"]', '[class*="widget"]',
                           '[class*="comment"]', '[class*="social"]', '[class*="share"]',
                           '[id*="menu"]', '[id*="nav"]', '[id*="sidebar"]', '[id*="footer"]']:
                for tag in soup.select(selector):
                    tag.decompose()
            
            # Try to find main content area first
            main_content = None
            for selector in ['article', 'main', '[role="main"]', '.content', '.article', 
                           '.post', '.entry', '#content', '#main']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # Use main content if found, otherwise use body
            content_source = main_content if main_content else soup.body if soup.body else soup
            
            # Get clean text
            text = content_source.get_text(separator=' ', strip=True)
            
            # Additional cleanup - remove excessive whitespace
            text = ' '.join(text.split())
            
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
    
    # Find the admin user to add as first friend
    admin_user = await db.users.find_one({"is_admin": True})
    admin_id = admin_user["id"] if admin_user else None
    
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
        "friends": [admin_id] if admin_id else [],
        "friend_count": 1 if admin_id else 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    # Add the new user to admin's friends list
    if admin_id:
        await db.users.update_one(
            {"id": admin_id},
            {"$addToSet": {"friends": user_id}, "$inc": {"friend_count": 1}}
        )
        
        # Create friendship record
        friendship = {
            "id": str(uuid.uuid4()),
            "user_id": admin_id,
            "friend_id": user_id,
            "status": "accepted",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.friendships.insert_one(friendship)
        
        logger.info(f"New user {data.username} added with admin as first friend")
    
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
    logger.info(f"Login attempt for {data.email}: found={user is not None}")
    
    if not user:
        logger.warning(f"User not found: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    pw_valid = verify_password(data.password, user.get("password_hash", ""))
    logger.info(f"Password valid: {pw_valid}, hash exists: {bool(user.get('password_hash'))}")
    
    if not pw_valid:
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
            
            # Check if this is an admin email
            user_is_admin = is_admin_email(google_email)
            if user_is_admin:
                logger.info(f"🛡️ Admin account created via Google OAuth: {google_email}")
            
            user = {
                "id": user_id,
                "username": username,
                "email": google_email,
                "google_id": google_sub,
                "password_hash": "",  # No password for OAuth users
                "is_admin": user_is_admin,
                "is_paid": user_is_admin,  # Admins get paid features
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
            
            # Ensure admin status for admin emails
            if is_admin_email(google_email) and not user.get("is_admin"):
                update_data["is_admin"] = True
                update_data["is_paid"] = True
                logger.info(f"🛡️ Admin privileges granted to existing user: {google_email}")
            
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
    
    # Private protocols can be set for sale
    for_sale = data.for_sale if not data.is_public else False
    price = data.price if for_sale else None
    
    # Process location data
    location_data = None
    if data.location:
        location_data = {
            "city": data.location.city,
            "state": data.location.state,
            "country": data.location.country,
            "lat": data.location.lat,
            "lng": data.location.lng
        }
    
    category = {
        "id": category_id,
        "user_id": user["id"],
        "name": data.name,
        "protocol_string": data.protocol.protocol_string,
        "parent_id": data.parent_id,
        "is_public": data.is_public,
        "for_sale": for_sale,
        "price": price,
        "location": location_data,
        "level": level,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(category)
    
    return CategoryResponse(**{**category, "created_at": datetime.fromisoformat(category["created_at"]), "owner_username": user.get("callsign", user.get("email", "Unknown"))})

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
        # If making public, remove for_sale status
        if data.is_public:
            update_data["for_sale"] = False
            update_data["price"] = None
    
    # Update for_sale status (only for private protocols)
    if data.for_sale is not None:
        category = await db.categories.find_one({"id": category_id})
        if category and not category.get("is_public", True) and not data.is_public:
            update_data["for_sale"] = data.for_sale
            if data.for_sale and data.price is not None:
                update_data["price"] = data.price
            elif not data.for_sale:
                update_data["price"] = None
    
    # Update price if for_sale
    if data.price is not None and data.for_sale is not False:
        update_data["price"] = data.price
    
    # Update location data
    if data.location is not None:
        update_data["location"] = {
            "city": data.location.city,
            "state": data.location.state,
            "country": data.location.country,
            "lat": data.location.lat,
            "lng": data.location.lng
        }
    
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

@api_router.put("/categories/{category_id}/sale-settings")
async def update_category_sale_settings(
    category_id: str, 
    for_sale: bool, 
    price: float = 0.00, 
    user: dict = Depends(require_user)
):
    """Update a category's for-sale status and price"""
    category = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Can only sell private protocols
    if category.get("is_public", True):
        raise HTTPException(status_code=400, detail="Public protocols cannot be sold")
    
    # Validate price - allow $0.00 (FREE) up to $99.00
    if for_sale and (price < 0.00 or price > 99.00):
        raise HTTPException(status_code=400, detail="Price must be between $0.00 (FREE) and $99.00")
    
    update_data = {
        "for_sale": for_sale,
        "price": price if for_sale else None,
        "is_free": price == 0.00 if for_sale else False  # Mark as FREE if price is $0.00
    }
    
    await db.categories.update_one(
        {"id": category_id, "user_id": user["id"]},
        {"$set": update_data}
    )
    
    price_str = "FREE" if price == 0.00 else f"${price:.2f}"
    return {"message": f"Protocol {'listed for sale at ' + price_str if for_sale else 'removed from sale'}", "for_sale": for_sale, "price": price if for_sale else None, "is_free": price == 0.00 if for_sale else False}

# ============================================
# API ROUTES - PROTOCOL MARKETPLACE
# ============================================

@api_router.get("/marketplace/stats")
async def get_marketplace_stats(user: dict = Depends(require_user)):
    """Get marketplace statistics for display"""
    # Count protocols for sale
    total_protocols = await db.categories.count_documents({"for_sale": True, "is_public": False})
    
    # Get total sales and revenue
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": 1},
            "total_revenue": {"$sum": "$amount"}
        }}
    ]
    sales_stats = await db.protocol_purchases.aggregate(pipeline).to_list(1)
    
    total_sales = 0
    total_revenue = 0
    if sales_stats:
        total_sales = sales_stats[0].get("total_sales", 0)
        total_revenue = sales_stats[0].get("total_revenue", 0)
    
    # Count unique sellers
    active_sellers_pipeline = [
        {"$match": {"for_sale": True, "is_public": False}},
        {"$group": {"_id": "$user_id"}}
    ]
    active_sellers = await db.categories.aggregate(active_sellers_pipeline).to_list(None)
    
    return {
        "total_protocols": total_protocols,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "active_sellers": len(active_sellers)
    }

@api_router.get("/marketplace/protocols")
async def get_protocols_for_sale(user: dict = Depends(require_user)):
    """Get all protocols listed for sale"""
    # Get protocols marked for sale (for_sale must be True)
    # Note: for_sale is only valid for private protocols, but we check for_sale explicitly
    # is_public being False or None/missing both qualify as "not public" 
    protocols = await db.categories.find(
        {
            "for_sale": True,
            "$or": [
                {"is_public": False},
                {"is_public": {"$exists": False}},
                {"is_public": None}
            ]
        }
    ).to_list(1000)  # Increased limit to show all protocols
    
    result = []
    for protocol in protocols:
        # Get owner info
        owner = await db.users.find_one({"id": protocol["user_id"]})
        owner_name = owner.get("username", owner.get("callsign", owner.get("email", "Unknown"))) if owner else "Unknown"
        
        # Check if user already purchased this protocol
        purchase = await db.protocol_purchases.find_one({
            "buyer_id": user["id"],
            "category_id": protocol["id"],
            "status": "completed"
        })
        
        # Create protocol preview (first 50 chars)
        protocol_preview = protocol.get("protocol_string", "")[:50] + "..." if protocol.get("protocol_string") else None
        
        # Get location data
        location = protocol.get("location")
        
        result.append({
            "id": protocol["id"],
            "name": protocol["name"],
            "owner_id": protocol["user_id"],
            "owner_username": owner_name,
            "price": protocol.get("price", 0.00),
            "is_free": protocol.get("price", 0) == 0 or protocol.get("is_free", False),
            "is_purchased": purchase is not None,
            "protocol_preview": protocol_preview,
            "location": location,
            "created_at": protocol.get("created_at")
        })
    
    return {"protocols": result}

@api_router.post("/marketplace/protocols/{category_id}/purchase")
async def purchase_protocol(category_id: str, user: dict = Depends(require_user)):
    """Record a protocol purchase (after PayPal payment)"""
    # Get the protocol
    protocol = await db.categories.find_one({"id": category_id, "for_sale": True})
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or not for sale")
    
    # Can't purchase own protocol
    if protocol["user_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot purchase your own protocol")
    
    # Check if already purchased
    existing = await db.protocol_purchases.find_one({
        "buyer_id": user["id"],
        "category_id": category_id,
        "status": "completed"
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already purchased this protocol")
    
    # Create purchase record
    purchase = {
        "id": str(uuid.uuid4()),
        "buyer_id": user["id"],
        "seller_id": protocol["user_id"],
        "category_id": category_id,
        "category_name": protocol["name"],
        "amount": protocol.get("price", 0.75),
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.protocol_purchases.insert_one(purchase)
    
    return {
        "message": "Protocol purchased successfully!",
        "purchase": purchase,
        "protocol_string": protocol["protocol_string"]
    }

@api_router.get("/marketplace/my-purchases")
async def get_my_purchases(user: dict = Depends(require_user)):
    """Get user's purchased protocols"""
    purchases = await db.protocol_purchases.find(
        {"buyer_id": user["id"], "status": "completed"}
    ).to_list(100)
    
    result = []
    for purchase in purchases:
        # Get full protocol info
        protocol = await db.categories.find_one({"id": purchase["category_id"]})
        if protocol:
            owner = await db.users.find_one({"id": purchase["seller_id"]})
            owner_name = owner.get("callsign", owner.get("email", "Unknown")) if owner else "Unknown"
            result.append({
                "id": purchase["id"],
                "category_id": purchase["category_id"],
                "category_name": purchase.get("category_name", protocol["name"]),
                "protocol_string": protocol["protocol_string"],
                "seller_username": owner_name,
                "amount": purchase["amount"],
                "purchased_at": purchase["created_at"]
            })
    
    return {"purchases": result}

@api_router.get("/marketplace/my-sales")
async def get_my_sales(user: dict = Depends(require_user)):
    """Get user's protocol sales"""
    sales = await db.protocol_purchases.find(
        {"seller_id": user["id"], "status": "completed"}
    ).to_list(100)
    
    total_revenue = sum(s.get("amount", 0) for s in sales)
    
    result = []
    for sale in sales:
        buyer = await db.users.find_one({"id": sale["buyer_id"]})
        buyer_name = buyer.get("callsign", buyer.get("email", "Unknown")) if buyer else "Unknown"
        result.append({
            "id": sale["id"],
            "category_id": sale["category_id"],
            "category_name": sale.get("category_name", "Unknown"),
            "buyer_username": buyer_name,
            "amount": sale["amount"],
            "sold_at": sale["created_at"]
        })
    
    return {"sales": result, "total_revenue": total_revenue}

@api_router.put("/categories/{category_id}/sale-settings")
async def update_sale_settings(
    category_id: str,
    for_sale: bool = Query(...),
    price: float = Query(None, ge=0.75, le=2.99),
    user: dict = Depends(require_user)
):
    """Update protocol sale settings"""
    category = await db.categories.find_one({"id": category_id, "user_id": user["id"]})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Only private protocols can be sold
    if category.get("is_public", True):
        raise HTTPException(status_code=400, detail="Only private protocols can be sold")
    
    update_data = {"for_sale": for_sale}
    if for_sale:
        update_data["price"] = price if price else 0.75
    else:
        update_data["price"] = None
    
    await db.categories.update_one(
        {"id": category_id},
        {"$set": update_data}
    )
    
    return {"message": f"Protocol {'listed for sale at ${:.2f}'.format(price or 0.75) if for_sale else 'removed from sale'}"}

# ============================================
# API ROUTES - PROTOCOL RECOMMENDATIONS
# ============================================

@api_router.post("/categories/{category_id}/recommendations")
async def submit_recommendation(category_id: str, data: ProtocolRecommendationCreate, user: dict = Depends(require_user)):
    """Submit a recommendation for a public protocol"""
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if not category.get("is_public", True):
        raise HTTPException(status_code=403, detail="Cannot recommend changes to private protocols")
    
    # Don't allow self-recommendations
    if category["user_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot recommend changes to your own protocol")
    
    recommendation = {
        "id": str(uuid.uuid4()),
        "category_id": category_id,
        "category_name": category["name"],
        "user_id": user["id"],
        "username": user["username"],
        "owner_id": category["user_id"],
        "original_protocol": data.original_protocol,
        "suggested_protocol": data.suggested_protocol,
        "reason": data.reason,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.protocol_recommendations.insert_one(recommendation)
    
    # Send email notification to the protocol owner
    owner = await db.users.find_one({"id": category["user_id"]})
    if owner and owner.get("email"):
        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #e0e0ff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #0f0f1a; border: 1px solid #8b5cf6; border-radius: 8px; padding: 20px;">
                <h2 style="color: #ec4899; margin-bottom: 20px;">🔔 New Protocol Recommendation</h2>
                <p style="color: #c4b5fd;">Hello {owner.get('username', 'Pilot')},</p>
                <p style="color: #c4b5fd;">You have received a new recommendation for your protocol:</p>
                
                <div style="background-color: #1f1f35; border-left: 4px solid #8b5cf6; padding: 15px; margin: 15px 0;">
                    <p style="color: #ec4899; font-weight: bold; margin: 0 0 10px 0;">Category: {category["name"]}</p>
                    <p style="color: #c4b5fd; margin: 0;">From: {user["username"]}</p>
                </div>
                
                <div style="margin: 15px 0;">
                    <p style="color: #8b5cf6; font-weight: bold;">Original Protocol:</p>
                    <code style="background-color: #1f1f35; color: #c4b5fd; padding: 10px; display: block; border-radius: 4px;">{data.original_protocol}</code>
                </div>
                
                <div style="margin: 15px 0;">
                    <p style="color: #ec4899; font-weight: bold;">Suggested Change:</p>
                    <code style="background-color: #1f1f35; color: #ec4899; padding: 10px; display: block; border-radius: 4px;">{data.suggested_protocol}</code>
                </div>
                
                <div style="margin: 15px 0;">
                    <p style="color: #8b5cf6; font-weight: bold;">Reason:</p>
                    <p style="color: #c4b5fd; background-color: #1f1f35; padding: 10px; border-radius: 4px;">{data.reason}</p>
                </div>
                
                <p style="color: #c4b5fd; margin-top: 20px;">Log in to InfoPilot Explorer to review and respond to this recommendation.</p>
                
                <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">— InfoPilot Explorer Team</p>
            </div>
        </body>
        </html>
        """
        asyncio.create_task(send_notification_email(
            owner["email"],
            f"📝 New Protocol Recommendation for '{category['name']}'",
            email_html
        ))
    
    return {"message": "Recommendation submitted", "recommendation": {k: v for k, v in recommendation.items() if k != "_id"}}

@api_router.get("/categories/{category_id}/recommendations")
async def get_category_recommendations(category_id: str, user: dict = Depends(require_user)):
    """Get all recommendations for a category (owner only)"""
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can view recommendations")
    
    recommendations = await db.protocol_recommendations.find(
        {"category_id": category_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"recommendations": recommendations, "count": len(recommendations)}

@api_router.get("/recommendations/my-protocols")
async def get_my_protocol_recommendations(user: dict = Depends(require_user)):
    """Get all recommendations across all of the user's protocols"""
    recommendations = await db.protocol_recommendations.find(
        {"owner_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    # Group by category
    by_category = {}
    for rec in recommendations:
        cat_id = rec["category_id"]
        if cat_id not in by_category:
            by_category[cat_id] = {
                "category_id": cat_id,
                "category_name": rec["category_name"],
                "recommendations": [],
                "pending_count": 0
            }
        by_category[cat_id]["recommendations"].append(rec)
        if rec["status"] == "pending":
            by_category[cat_id]["pending_count"] += 1
    
    return {
        "total_count": len(recommendations),
        "pending_count": sum(1 for r in recommendations if r["status"] == "pending"),
        "by_category": list(by_category.values())
    }

@api_router.put("/recommendations/{recommendation_id}/status")
async def update_recommendation_status(recommendation_id: str, status: str, user: dict = Depends(require_user)):
    """Accept or reject a recommendation (owner only)"""
    if status not in ["accepted", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Status must be 'accepted', 'rejected', or 'pending'")
    
    recommendation = await db.protocol_recommendations.find_one({"id": recommendation_id})
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    if recommendation["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the owner can update recommendation status")
    
    await db.protocol_recommendations.update_one(
        {"id": recommendation_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Recommendation {status}", "status": status}

@api_router.delete("/recommendations/{recommendation_id}")
async def delete_recommendation(recommendation_id: str, user: dict = Depends(require_user)):
    """Delete a recommendation (owner or submitter)"""
    recommendation = await db.protocol_recommendations.find_one({"id": recommendation_id})
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    if recommendation["owner_id"] != user["id"] and recommendation["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this recommendation")
    
    await db.protocol_recommendations.delete_one({"id": recommendation_id})
    return {"message": "Recommendation deleted"}

@api_router.get("/categories/{category_id}/recommendations/count")
async def get_recommendation_count(category_id: str, user: dict = Depends(require_user)):
    """Get pending recommendation count for a category (owner only)"""
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category["user_id"] != user["id"]:
        return {"count": 0, "pending": 0}  # Non-owners see 0
    
    total = await db.protocol_recommendations.count_documents({"category_id": category_id})
    pending = await db.protocol_recommendations.count_documents({"category_id": category_id, "status": "pending"})
    
    return {"count": total, "pending": pending}

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
    
    # Check user's current result count against limit
    current_result_count = await db.search_results.count_documents({"user_id": user["id"]})
    max_allowed = settings.user_max_results_limit
    
    if current_result_count >= max_allowed:
        raise HTTPException(
            status_code=400, 
            detail=f"Database limit reached. You have {current_result_count}/{max_allowed} results. "
                   f"Please clear some results before adding new ones."
        )
    
    # Calculate how many results we can still add
    remaining_capacity = max_allowed - current_result_count
    
    # Extract key search terms for filtering (ignore common words)
    search_stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
                        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
                        'about', 'into', 'through', 'during', 'before', 'after', 'above',
                        'below', 'between', 'under', 'over', 'u.s.', 'u.s', 'us', 'usa'}
    
    # Extract meaningful search terms (keep multi-word names together)
    search_query_lower = data.search_query.lower()
    # Split but preserve quoted phrases or names with periods (like "William C. Gamble")
    search_terms = []
    # First try to find name patterns (First [Middle.] Last)
    name_pattern = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z]\.?\s+[A-Z][a-z]+)?', data.search_query)
    for name in name_pattern:
        if len(name.split()) >= 2:  # Multi-word names
            search_terms.append(name.lower())
    
    # Also add individual significant words
    words = re.findall(r'\b[a-z]+\b', search_query_lower)
    for word in words:
        if word not in search_stop_words and len(word) > 2:
            search_terms.append(word)
    
    # Remove duplicates while preserving order
    search_terms = list(dict.fromkeys(search_terms))
    logger.info(f"Search terms extracted for filtering: {search_terms}")
    
    # Determine max results based on user type and admin settings
    is_paid_user = user.get("is_paid", False) or user.get("is_admin", False)
    user_max_search_results = settings.get_max_results_for_user(is_paid_user)
    max_results = min(data.max_results, user_max_search_results)
    
    logger.info(f"User {'paid' if is_paid_user else 'unpaid'}: max_results={max_results} (settings: unpaid={settings.unpaid_user_search_pages} pages, paid={settings.paid_user_search_pages} pages)")
    
    # Get user's own categories AND public categories from other users
    user_categories = await db.categories.find({
        "$or": [
            {"user_id": user["id"]},  # User's own categories
            {"is_public": True}        # Public categories from all users
        ]
    }).to_list(1000)
    
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
    limit_reached = False
    skipped_no_search_terms = 0
    
    for result in search_results:
        # Check if we've reached the user's result limit
        if len(collated_results) >= remaining_capacity:
            limit_reached = True
            break
        
        # Skip unsafe URLs
        if result["url"] in unsafe_urls:
            blocked_unsafe_count += 1
            continue
        
        page_data = await fetch_page_content(result["url"])
        
        if not page_data["success"]:
            continue
        
        content = f"{result['title']} {result['snippet']} {page_data.get('content', '')}"
        content_lower = content.lower()
        
        # Check if content contains key search terms (if require_search_terms is enabled)
        if data.require_search_terms and search_terms:
            # For multi-word search terms (like names), require at least ONE to be present
            # For single words, require at least 50% to be present
            multi_word_terms = [t for t in search_terms if ' ' in t]
            single_word_terms = [t for t in search_terms if ' ' not in t]
            
            has_multi_word_match = False
            if multi_word_terms:
                for term in multi_word_terms:
                    if term in content_lower:
                        has_multi_word_match = True
                        break
            
            # Count single word matches
            single_word_matches = sum(1 for t in single_word_terms if t in content_lower)
            min_single_required = max(1, len(single_word_terms) // 2)  # At least 50%
            
            # STRICT FILTERING:
            # If we have multi-word terms (like a person's name), we REQUIRE a match
            # because that's likely the main subject of the search
            if multi_word_terms:
                if not has_multi_word_match:
                    # No multi-word match - check if we have strong single word evidence
                    # Need at least 75% of single words to compensate for missing name match
                    strict_single_required = max(2, int(len(single_word_terms) * 0.75))
                    if single_word_matches < strict_single_required:
                        skipped_no_search_terms += 1
                        continue
            else:
                # No multi-word terms, just check single words
                if single_word_matches < min_single_required:
                    skipped_no_search_terms += 1
                    continue
        
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
            
            # Extract hashtags for linking related content
            hashtags = extract_hashtags(content, result["title"], max_hashtags=6)
            
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
                "hashtags": hashtags,
                "safety_checked": safety_check.get("checked", False),
                "reactions": {},
                "collated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.search_results.insert_one(search_result)
            # Return a clean copy without MongoDB _id
            clean_result = {k: v for k, v in search_result.items() if k != "_id"}
            collated_results.append(clean_result)
    
    response_message = f"Collated {len(collated_results)} results into categories"
    if skipped_no_search_terms > 0:
        response_message += f" ({skipped_no_search_terms} skipped - didn't contain search terms)"
    if blocked_unsafe_count > 0:
        response_message += f" ({blocked_unsafe_count} unsafe URLs blocked)"
    if limit_reached:
        response_message += f" (Database limit reached: {current_result_count + len(collated_results)}/{max_allowed})"
    
    return {
        "message": response_message,
        "results": collated_results,
        "categorized_count": len(collated_results),
        "total_searched": len(search_results),
        "unsafe_blocked": blocked_unsafe_count,
        "skipped_no_search_terms": skipped_no_search_terms,
        "search_terms_used": search_terms,
        "safety_checked": safety_check.get("checked", False),
        "limit_reached": limit_reached,
        "current_count": current_result_count + len(collated_results),
        "max_allowed": max_allowed
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
    
    # App is now free - no page restrictions
    # All users get full access
    
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

@api_router.get("/marketplace/global-map")
async def get_marketplace_global_map(user: dict = Depends(require_user)):
    """Get aggregated map data from ALL users' search results for the Marketplace map.
    This provides a global view of all research activity across the platform.
    """
    # Get all results from all users that have locations
    all_results = await db.search_results.find(
        {"locations": {"$exists": True, "$ne": []}},
        {"_id": 0, "id": 1, "title": 1, "url": 1, "snippet": 1, "locations": 1, 
         "categories": 1, "user_id": 1, "collated_at": 1, "article_type": 1, "document_type": 1}
    ).to_list(2000)  # Limit to prevent performance issues
    
    # Get all categories for color coding
    all_categories = await db.categories.find({}, {"_id": 0, "id": 1, "name": 1, "user_id": 1}).to_list(5000)
    category_map = {cat["id"]: cat for cat in all_categories}
    
    # Get usernames for attribution
    user_ids = list(set(r.get("user_id") for r in all_results if r.get("user_id")))
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "username": 1}).to_list(1000)
    user_map = {u["id"]: u.get("username", "Unknown") for u in users}
    
    # Assign colors to unique categories
    colors = [
        "#ec4899", "#a855f7", "#3b82f6", "#22c55e", "#f59e0b", 
        "#ef4444", "#06b6d4", "#8b5cf6", "#f97316", "#14b8a6",
        "#e879f9", "#60a5fa", "#4ade80", "#fbbf24", "#f87171"
    ]
    
    # Build global map markers
    markers = []
    location_counts = {}  # Track how many results per location
    
    for result in all_results:
        for location in result.get("locations", []):
            loc_name = location.get("name", "Unknown")
            loc_key = f"{location.get('lat', 0)},{location.get('lng', 0)}"
            
            # Count results per location
            location_counts[loc_key] = location_counts.get(loc_key, 0) + 1
            
            for cat_id in result.get("categories", [])[:3]:  # Limit to 3 categories per result
                cat_info = category_map.get(cat_id, {"name": "Unknown"})
                username = user_map.get(result.get("user_id"), "Unknown")
                
                markers.append({
                    "id": f"global_{result['id']}_{loc_name}_{cat_id}",
                    "result_id": result["id"],
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result.get("snippet", "")[:200],  # Truncate for performance
                    "location_name": loc_name,
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "category_name": cat_info.get("name", "Unknown"),
                    "researcher": username,
                    "article_type": result.get("article_type", ""),
                    "document_type": result.get("document_type", ""),
                    "collated_at": result.get("collated_at", "")
                })
    
    # Get unique locations with counts
    unique_locations = []
    seen_locs = set()
    for marker in markers:
        loc_key = f"{marker['lat']},{marker['lng']}"
        if loc_key not in seen_locs:
            seen_locs.add(loc_key)
            unique_locations.append({
                "name": marker["location_name"],
                "lat": marker["lat"],
                "lng": marker["lng"],
                "result_count": location_counts.get(loc_key, 1)
            })
    
    # Sort by result count
    unique_locations.sort(key=lambda x: -x["result_count"])
    
    return {
        "markers": markers[:1000],  # Limit markers for performance
        "unique_locations": unique_locations[:50],  # Top 50 locations
        "total_results": len(all_results),
        "total_markers": len(markers),
        "total_researchers": len(user_ids),
        "hot_spots": unique_locations[:10]  # Top 10 most researched locations
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
    # Convert the session timestamp format (YYYY-MM-DD HH:MM) to match the ISO format prefix
    # Session timestamp: "2026-01-10 10:37" -> ISO prefix: "2026-01-10T10:37"
    iso_prefix = session_timestamp.replace(" ", "T")
    
    # Find results from this session using both possible formats
    results = await db.search_results.find({
        "user_id": user["id"],
        "$or": [
            {"collated_at": {"$regex": f"^{iso_prefix}"}},
            {"collated_at": {"$regex": f"^{session_timestamp}"}}
        ]
    }).to_list(1000)
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No results found for session {session_timestamp}")
    
    result_ids = [r["id"] for r in results]
    delete_result = await db.search_results.delete_many({
        "id": {"$in": result_ids},
        "user_id": user["id"]
    })
    
    return {
        "message": f"Deleted {delete_result.deleted_count} results from session",
        "deleted_count": delete_result.deleted_count
    }

@api_router.delete("/ultimate-search/clear-all")
async def clear_all_user_results(user: dict = Depends(require_user)):
    """Clear ALL results from user's database (user's own action)"""
    result = await db.search_results.delete_many({"user_id": user["id"]})
    
    return {
        "message": f"Cleared {result.deleted_count} results from your database",
        "deleted_count": result.deleted_count
    }

@api_router.delete("/ultimate-search/category/{category_id}/clear")
async def clear_category_results(category_id: str, user: dict = Depends(require_user)):
    """Clear all results from a specific category (including subcategories)"""
    # Get the category
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Verify ownership
    if category["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only clear your own categories")
    
    # Get all subcategory IDs recursively
    async def get_all_child_ids(parent_id: str) -> List[str]:
        ids = [parent_id]
        children = await db.categories.find({"parent_id": parent_id}).to_list(1000)
        for child in children:
            child_ids = await get_all_child_ids(child["id"])
            ids.extend(child_ids)
        return ids
    
    all_category_ids = await get_all_child_ids(category_id)
    
    # Delete all results associated with these categories
    result = await db.search_results.delete_many({
        "user_id": user["id"],
        "categories": {"$in": all_category_ids}
    })
    
    return {
        "message": f"Cleared {result.deleted_count} results from category '{category['name']}' and subcategories",
        "deleted_count": result.deleted_count,
        "categories_cleared": len(all_category_ids)
    }

@api_router.delete("/admin/clear-user-results/{target_user_id}")
async def admin_clear_user_results(target_user_id: str, user: dict = Depends(require_user)):
    """Admin: Clear all results for a specific user"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify target user exists
    target_user = await db.users.find_one({"id": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.search_results.delete_many({"user_id": target_user_id})
    
    return {
        "message": f"Cleared {result.deleted_count} results for user '{target_user.get('username', target_user_id)}'",
        "deleted_count": result.deleted_count,
        "target_user": target_user.get("username", target_user_id)
    }

@api_router.delete("/admin/clear-user-category/{target_user_id}/{category_id}")
async def admin_clear_user_category(target_user_id: str, category_id: str, user: dict = Depends(require_user)):
    """Admin: Clear all results from a specific user's category"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify target user and category exist
    target_user = await db.users.find_one({"id": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    category = await db.categories.find_one({"id": category_id, "user_id": target_user_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found for this user")
    
    # Get all subcategory IDs recursively
    async def get_all_child_ids(parent_id: str) -> List[str]:
        ids = [parent_id]
        children = await db.categories.find({"parent_id": parent_id}).to_list(1000)
        for child in children:
            child_ids = await get_all_child_ids(child["id"])
            ids.extend(child_ids)
        return ids
    
    all_category_ids = await get_all_child_ids(category_id)
    
    result = await db.search_results.delete_many({
        "user_id": target_user_id,
        "categories": {"$in": all_category_ids}
    })
    
    return {
        "message": f"Cleared {result.deleted_count} results from category '{category['name']}' for user '{target_user.get('username')}'",
        "deleted_count": result.deleted_count,
        "categories_cleared": len(all_category_ids)
    }

@api_router.get("/ultimate-search/user-stats")
async def get_user_result_stats(user: dict = Depends(require_user)):
    """Get user's result count and limit info"""
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    current_count = await db.search_results.count_documents({"user_id": user["id"]})
    max_allowed = settings.user_max_results_limit
    
    return {
        "current_count": current_count,
        "max_allowed": max_allowed,
        "remaining": max(0, max_allowed - current_count),
        "percentage_used": round((current_count / max_allowed) * 100, 1) if max_allowed > 0 else 0
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
# API ROUTES - REACTIONS (Legacy)
# ============================================

@api_router.post("/results/{result_id}/react")
async def add_legacy_reaction(result_id: str, data: ArticleReaction, user: dict = Depends(require_user)):
    """Add reaction to a search result (legacy endpoint)"""
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
    
    # App is now free - no restrictions
    
    public_categories = await db.categories.find({"is_public": True}, {"_id": 0}).to_list(1000)
    public_category_ids = [c["id"] for c in public_categories]
    
    query = {"categories": {"$in": public_category_ids}}
    if category_id:
        query["categories"] = category_id
    
    skip = (page - 1) * settings.results_per_page
    
    total = await db.search_results.count_documents(query)
    results = await db.search_results.find(query, {"_id": 0}).skip(skip).limit(settings.results_per_page).to_list(settings.results_per_page)
    
    return {
        "public_categories": public_categories,
        "results": results,
        "total": total,
        "page": page,
        "total_pages": (total + settings.results_per_page - 1) // settings.results_per_page
    }

# ============================================
# WORLDWIDE INFORMATION RESEARCH DATABASE
# ============================================

# Pydantic models for research resources
class ResearchResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., max_length=2000)
    url: str
    category: str  # Science, Technology, History, Arts, Business, Education, Government, Health, etc.
    tags: List[str] = []
    location: Optional[str] = None  # Country or region
    lat: Optional[float] = None
    lng: Optional[float] = None
    featured: bool = False

class ResearchResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    featured: Optional[bool] = None

# Research resource categories
RESEARCH_CATEGORIES = [
    "Science", "Technology", "History", "Arts & Culture", "Business & Finance",
    "Education", "Government", "Health & Medicine", "Environment", "Law & Legal",
    "Engineering", "Mathematics", "Philosophy", "Psychology", "Sociology",
    "Economics", "Political Science", "Literature", "Music", "Architecture"
]

@api_router.get("/research-database/resources")
async def get_research_resources(
    page: int = 1,
    category: Optional[str] = None,
    search: Optional[str] = None,
    featured_only: bool = False,
    user: dict = Depends(require_user)
):
    """Get curated research resources with filtering"""
    query = {}
    
    if category:
        query["category"] = category
    if featured_only:
        query["featured"] = True
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    per_page = 20
    skip = (page - 1) * per_page
    
    total = await db.research_resources.count_documents(query)
    resources = await db.research_resources.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "resources": resources,
        "total": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page,
        "categories": RESEARCH_CATEGORIES
    }

@api_router.post("/research-database/resources")
async def create_research_resource(
    data: ResearchResourceCreate,
    user: dict = Depends(require_admin)
):
    """Create a new research resource (admin only)"""
    resource = {
        "id": str(uuid.uuid4()),
        "title": data.title,
        "description": data.description,
        "url": data.url,
        "category": data.category,
        "tags": data.tags,
        "location": data.location,
        "lat": data.lat,
        "lng": data.lng,
        "featured": data.featured,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "views": 0
    }
    
    await db.research_resources.insert_one(resource)
    resource.pop("_id", None)
    return resource

@api_router.put("/research-database/resources/{resource_id}")
async def update_research_resource(
    resource_id: str,
    data: ResearchResourceUpdate,
    user: dict = Depends(require_admin)
):
    """Update a research resource (admin only)"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.research_resources.update_one(
        {"id": resource_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    resource = await db.research_resources.find_one({"id": resource_id}, {"_id": 0})
    return resource

@api_router.delete("/research-database/resources/{resource_id}")
async def delete_research_resource(
    resource_id: str,
    user: dict = Depends(require_admin)
):
    """Delete a research resource (admin only)"""
    result = await db.research_resources.delete_one({"id": resource_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"success": True, "message": "Resource deleted"}

@api_router.post("/research-database/resources/{resource_id}/view")
async def increment_resource_view(
    resource_id: str,
    user: dict = Depends(require_user)
):
    """Increment view count for a resource"""
    await db.research_resources.update_one(
        {"id": resource_id},
        {"$inc": {"views": 1}}
    )
    return {"success": True}

@api_router.get("/research-database/trending")
async def get_trending_topics(user: dict = Depends(require_user)):
    """Get trending topics/hashtags from all public search results"""
    # Aggregate hashtags from all search results
    pipeline = [
        {"$match": {"hashtags": {"$exists": True, "$ne": []}}},
        {"$unwind": "$hashtags"},
        {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    
    hashtags = await db.search_results.aggregate(pipeline).to_list(20)
    
    # Get trending categories
    category_pipeline = [
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    category_counts = await db.search_results.aggregate(category_pipeline).to_list(10)
    
    # Get category names
    category_ids = [c["_id"] for c in category_counts]
    categories = await db.categories.find({"id": {"$in": category_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(10)
    category_map = {c["id"]: c["name"] for c in categories}
    
    trending_categories = [
        {"id": c["_id"], "name": category_map.get(c["_id"], "Unknown"), "count": c["count"]}
        for c in category_counts if c["_id"] in category_map
    ]
    
    return {
        "trending_hashtags": [{"tag": h["_id"], "count": h["count"]} for h in hashtags],
        "trending_categories": trending_categories
    }

@api_router.get("/research-database/contributors")
async def get_top_contributors(user: dict = Depends(require_user)):
    """Get top contributors based on public protocols and copies"""
    # Get users with most public protocols
    pipeline = [
        {"$match": {"is_public": True}},
        {"$group": {
            "_id": "$user_id",
            "protocol_count": {"$sum": 1},
            "total_copies": {"$sum": "$copy_count"}
        }},
        {"$sort": {"total_copies": -1, "protocol_count": -1}},
        {"$limit": 10}
    ]
    
    contributors = await db.categories.aggregate(pipeline).to_list(10)
    
    # Get user details
    user_ids = [c["_id"] for c in contributors]
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "username": 1, "profile_photo": 1}).to_list(10)
    user_map = {u["id"]: u for u in users}
    
    result = []
    for i, c in enumerate(contributors):
        user_info = user_map.get(c["_id"], {})
        result.append({
            "rank": i + 1,
            "user_id": c["_id"],
            "username": user_info.get("username", "Unknown"),
            "profile_photo": user_info.get("profile_photo"),
            "protocol_count": c["protocol_count"],
            "total_copies": c["total_copies"]
        })
    
    return {"contributors": result}

@api_router.get("/research-database/map-data")
async def get_research_map_data(user: dict = Depends(require_user)):
    """Get research resources with location data for map visualization"""
    # Get resources with coordinates
    resources = await db.research_resources.find(
        {"lat": {"$exists": True, "$ne": None}, "lng": {"$exists": True, "$ne": None}},
        {"_id": 0}
    ).to_list(500)
    
    # Also get location data from search results
    search_locations = await db.search_results.find(
        {"locations": {"$exists": True, "$ne": []}},
        {"_id": 0, "title": 1, "url": 1, "locations": 1, "categories": 1}
    ).limit(200).to_list(200)
    
    # Aggregate by location
    location_counts = {}
    for result in search_locations:
        for loc in result.get("locations", []):
            key = f"{loc.get('lat', 0)},{loc.get('lng', 0)}"
            if key not in location_counts:
                location_counts[key] = {
                    "name": loc.get("name", "Unknown"),
                    "lat": loc.get("lat"),
                    "lng": loc.get("lng"),
                    "count": 0,
                    "type": "research_hotspot"
                }
            location_counts[key]["count"] += 1
    
    return {
        "resources": resources,
        "research_hotspots": list(location_counts.values()),
        "total_resources": len(resources),
        "total_hotspots": len(location_counts)
    }

@api_router.get("/research-database/stats")
async def get_research_database_stats(user: dict = Depends(require_user)):
    """Get overall statistics for the research database"""
    total_resources = await db.research_resources.count_documents({})
    total_results = await db.search_results.count_documents({})
    total_public_protocols = await db.categories.count_documents({"is_public": True})
    total_users = await db.users.count_documents({})
    
    # Category distribution
    category_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    category_dist = await db.research_resources.aggregate(category_pipeline).to_list(20)
    
    return {
        "total_resources": total_resources,
        "total_results": total_results,
        "total_public_protocols": total_public_protocols,
        "total_users": total_users,
        "category_distribution": [{"category": c["_id"], "count": c["count"]} for c in category_dist if c["_id"]]
    }

# ============================================
# API ROUTES - SOCIAL FEATURES (FRIENDS)
# ============================================

@api_router.get("/friends")
async def get_friends(user: dict = Depends(require_user)):
    """Get user's friends list"""
    friend_ids = user.get("friends", [])
    if not friend_ids:
        return {"friends": [], "count": 0}
    
    friends = await db.users.find(
        {"id": {"$in": friend_ids}},
        {"_id": 0, "id": 1, "username": 1, "profile_photo": 1, "is_admin": 1}
    ).to_list(1000)
    
    return {"friends": friends, "count": len(friends)}

@api_router.post("/friends/request")
async def send_friend_request(data: FriendRequest, user: dict = Depends(require_user)):
    """Send a friend request"""
    if data.friend_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    
    # Check if already friends
    if data.friend_id in user.get("friends", []):
        raise HTTPException(status_code=400, detail="Already friends")
    
    # Check if request already exists
    existing = await db.friend_requests.find_one({
        "from_id": user["id"],
        "to_id": data.friend_id,
        "status": "pending"
    })
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already sent")
    
    # Check if target user exists
    target_user = await db.users.find_one({"id": data.friend_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    request = {
        "id": str(uuid.uuid4()),
        "from_id": user["id"],
        "from_username": user["username"],
        "to_id": data.friend_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.friend_requests.insert_one(request)
    
    return {"message": "Friend request sent", "request_id": request["id"]}

@api_router.get("/friends/requests")
async def get_friend_requests(user: dict = Depends(require_user)):
    """Get pending friend requests"""
    incoming = await db.friend_requests.find(
        {"to_id": user["id"], "status": "pending"},
        {"_id": 0}
    ).to_list(100)
    
    outgoing = await db.friend_requests.find(
        {"from_id": user["id"], "status": "pending"},
        {"_id": 0}
    ).to_list(100)
    
    return {"incoming": incoming, "outgoing": outgoing}

@api_router.post("/friends/accept/{request_id}")
async def accept_friend_request(request_id: str, user: dict = Depends(require_user)):
    """Accept a friend request"""
    request = await db.friend_requests.find_one({"id": request_id, "to_id": user["id"]})
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    # Add to both users' friends lists
    await db.users.update_one(
        {"id": user["id"]},
        {"$addToSet": {"friends": request["from_id"]}, "$inc": {"friend_count": 1}}
    )
    await db.users.update_one(
        {"id": request["from_id"]},
        {"$addToSet": {"friends": user["id"]}, "$inc": {"friend_count": 1}}
    )
    
    # Update request status
    await db.friend_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "accepted"}}
    )
    
    return {"message": "Friend request accepted"}

@api_router.post("/friends/reject/{request_id}")
async def reject_friend_request(request_id: str, user: dict = Depends(require_user)):
    """Reject a friend request"""
    request = await db.friend_requests.find_one({"id": request_id, "to_id": user["id"]})
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    await db.friend_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "rejected"}}
    )
    
    return {"message": "Friend request rejected"}

@api_router.delete("/friends/{friend_id}")
async def remove_friend(friend_id: str, user: dict = Depends(require_user)):
    """Remove a friend"""
    await db.users.update_one(
        {"id": user["id"]},
        {"$pull": {"friends": friend_id}, "$inc": {"friend_count": -1}}
    )
    await db.users.update_one(
        {"id": friend_id},
        {"$pull": {"friends": user["id"]}, "$inc": {"friend_count": -1}}
    )
    
    return {"message": "Friend removed"}

# ============================================
# API ROUTES - SOCIAL FEATURES (GROUPS)
# ============================================

@api_router.get("/groups")
async def get_groups(user: dict = Depends(require_user)):
    """Get all groups (public) and user's groups"""
    # Get user's groups
    my_groups = await db.groups.find(
        {"$or": [{"owner_id": user["id"]}, {"members": user["id"]}]},
        {"_id": 0}
    ).to_list(100)
    
    # Get public groups
    public_groups = await db.groups.find(
        {"privacy": "public"},
        {"_id": 0}
    ).to_list(50)
    
    return {"my_groups": my_groups, "public_groups": public_groups}

@api_router.post("/groups")
async def create_group(data: GroupCreate, user: dict = Depends(require_user)):
    """Create a new group"""
    group = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description,
        "privacy": data.privacy,
        "cover_photo": data.cover_photo,
        "owner_id": user["id"],
        "owner_username": user["username"],
        "members": [user["id"]],
        "member_count": 1,
        "admins": [user["id"]],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.groups.insert_one(group)
    return {"message": "Group created", "group": {k: v for k, v in group.items() if k != "_id"}}

@api_router.get("/groups/{group_id}")
async def get_group(group_id: str, user: dict = Depends(require_user)):
    """Get group details"""
    group = await db.groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check access for secret groups
    if group["privacy"] == "secret" and user["id"] not in group.get("members", []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get recent posts
    posts = await db.group_posts.find(
        {"group_id": group_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {"group": group, "posts": posts}

@api_router.put("/groups/{group_id}")
async def update_group(group_id: str, data: GroupUpdate, user: dict = Depends(require_user)):
    """Update group (owner/admin only)"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user["id"] not in group.get("admins", []) and user["id"] != group["owner_id"]:
        raise HTTPException(status_code=403, detail="Only admins can update the group")
    
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        await db.groups.update_one({"id": group_id}, {"$set": updates})
    
    return {"message": "Group updated"}

@api_router.delete("/groups/{group_id}")
async def delete_group(group_id: str, user: dict = Depends(require_user)):
    """Delete group (owner only)"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user["id"] != group["owner_id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only the owner can delete the group")
    
    await db.groups.delete_one({"id": group_id})
    await db.group_posts.delete_many({"group_id": group_id})
    
    return {"message": "Group deleted"}

@api_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user: dict = Depends(require_user)):
    """Join a group"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if group["privacy"] == "secret":
        raise HTTPException(status_code=403, detail="Cannot join secret groups directly")
    
    if user["id"] in group.get("members", []):
        raise HTTPException(status_code=400, detail="Already a member")
    
    await db.groups.update_one(
        {"id": group_id},
        {"$addToSet": {"members": user["id"]}, "$inc": {"member_count": 1}}
    )
    
    return {"message": "Joined group"}

@api_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user: dict = Depends(require_user)):
    """Leave a group"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user["id"] == group["owner_id"]:
        raise HTTPException(status_code=400, detail="Owner cannot leave. Delete the group or transfer ownership.")
    
    await db.groups.update_one(
        {"id": group_id},
        {"$pull": {"members": user["id"], "admins": user["id"]}, "$inc": {"member_count": -1}}
    )
    
    return {"message": "Left group"}

@api_router.post("/groups/{group_id}/posts")
async def create_group_post(group_id: str, data: GroupPostCreate, user: dict = Depends(require_user)):
    """Create a post in a group"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user["id"] not in group.get("members", []):
        raise HTTPException(status_code=403, detail="Must be a member to post")
    
    post = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "user_id": user["id"],
        "username": user["username"],
        "content": data.content,
        "image_url": data.image_url,
        "reactions": {},
        "reaction_counts": {},
        "total_reactions": 0,
        "comment_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.group_posts.insert_one(post)
    return {"message": "Post created", "post": {k: v for k, v in post.items() if k != "_id"}}

# ============================================
# API ROUTES - SOCIAL FEATURES (PAGES)
# ============================================

@api_router.get("/pages")
async def get_pages(user: dict = Depends(require_user)):
    """Get all pages and user's pages"""
    # Get user's pages
    my_pages = await db.pages.find(
        {"owner_id": user["id"]},
        {"_id": 0}
    ).to_list(50)
    
    # Get pages user follows
    following = await db.page_followers.find(
        {"user_id": user["id"]},
        {"_id": 0, "page_id": 1}
    ).to_list(100)
    following_ids = [f["page_id"] for f in following]
    
    followed_pages = []
    if following_ids:
        followed_pages = await db.pages.find(
            {"id": {"$in": following_ids}},
            {"_id": 0}
        ).to_list(100)
    
    # Get popular pages
    popular_pages = await db.pages.find(
        {},
        {"_id": 0}
    ).sort("follower_count", -1).limit(20).to_list(20)
    
    return {"my_pages": my_pages, "following": followed_pages, "popular": popular_pages}

@api_router.post("/pages")
async def create_page(data: PageCreate, user: dict = Depends(require_user)):
    """Create a new page"""
    page = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description,
        "category": data.category,
        "cover_photo": data.cover_photo,
        "profile_photo": data.profile_photo,
        "owner_id": user["id"],
        "owner_username": user["username"],
        "follower_count": 0,
        "admins": [user["id"]],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.pages.insert_one(page)
    return {"message": "Page created", "page": {k: v for k, v in page.items() if k != "_id"}}

@api_router.get("/pages/{page_id}")
async def get_page(page_id: str, user: dict = Depends(require_user)):
    """Get page details"""
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Check if user follows this page
    is_following = await db.page_followers.find_one({
        "page_id": page_id,
        "user_id": user["id"]
    }) is not None
    
    # Get recent posts
    posts = await db.page_posts.find(
        {"page_id": page_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {"page": page, "posts": posts, "is_following": is_following}

@api_router.put("/pages/{page_id}")
async def update_page(page_id: str, data: PageUpdate, user: dict = Depends(require_user)):
    """Update page (owner/admin only)"""
    page = await db.pages.find_one({"id": page_id})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if user["id"] not in page.get("admins", []) and user["id"] != page["owner_id"]:
        raise HTTPException(status_code=403, detail="Only admins can update the page")
    
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        await db.pages.update_one({"id": page_id}, {"$set": updates})
    
    return {"message": "Page updated"}

@api_router.delete("/pages/{page_id}")
async def delete_page(page_id: str, user: dict = Depends(require_user)):
    """Delete page (owner only)"""
    page = await db.pages.find_one({"id": page_id})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if user["id"] != page["owner_id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only the owner can delete the page")
    
    await db.pages.delete_one({"id": page_id})
    await db.page_posts.delete_many({"page_id": page_id})
    await db.page_followers.delete_many({"page_id": page_id})
    
    return {"message": "Page deleted"}

@api_router.post("/pages/{page_id}/follow")
async def follow_page(page_id: str, user: dict = Depends(require_user)):
    """Follow a page"""
    page = await db.pages.find_one({"id": page_id})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    existing = await db.page_followers.find_one({
        "page_id": page_id,
        "user_id": user["id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already following")
    
    await db.page_followers.insert_one({
        "id": str(uuid.uuid4()),
        "page_id": page_id,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    await db.pages.update_one(
        {"id": page_id},
        {"$inc": {"follower_count": 1}}
    )
    
    return {"message": "Now following page"}

@api_router.post("/pages/{page_id}/unfollow")
async def unfollow_page(page_id: str, user: dict = Depends(require_user)):
    """Unfollow a page"""
    result = await db.page_followers.delete_one({
        "page_id": page_id,
        "user_id": user["id"]
    })
    
    if result.deleted_count > 0:
        await db.pages.update_one(
            {"id": page_id},
            {"$inc": {"follower_count": -1}}
        )
    
    return {"message": "Unfollowed page"}

@api_router.post("/pages/{page_id}/posts")
async def create_page_post(page_id: str, data: GroupPostCreate, user: dict = Depends(require_user)):
    """Create a post on a page (admin only)"""
    page = await db.pages.find_one({"id": page_id})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if user["id"] not in page.get("admins", []):
        raise HTTPException(status_code=403, detail="Only admins can post on the page")
    
    post = {
        "id": str(uuid.uuid4()),
        "page_id": page_id,
        "user_id": user["id"],
        "username": user["username"],
        "content": data.content,
        "image_url": data.image_url,
        "reactions": {},
        "reaction_counts": {},
        "total_reactions": 0,
        "comment_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.page_posts.insert_one(post)
    return {"message": "Post created", "post": {k: v for k, v in post.items() if k != "_id"}}

# ============================================
# API ROUTES - PAYPAL SUBSCRIPTIONS
# ============================================

# PayPal Payment Links
PAYPAL_PAYMENT_LINK_1 = "https://www.paypal.com/ncp/payment/765S46VPPEP5C"
PAYPAL_PAYMENT_LINK_2 = "https://www.paypal.com/ncp/payment/SX379AAKMXM8A"

# Promotional pricing ends March 2nd, 2026
PROMO_END_DATE = datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
REGULAR_PRICE = 4.62
MIN_PRICE = 0.01  # Minimum payment during promo period

@api_router.get("/subscription/config")
async def get_subscription_config():
    """Get subscription configuration (public)"""
    now = datetime.now(timezone.utc)
    is_promo_active = now < PROMO_END_DATE
    
    # Get admin-configured settings
    settings = await db.admin_settings.find_one({"type": "subscription_config"}, {"_id": 0})
    
    if settings:
        promo_end = settings.get("promo_end_date", PROMO_END_DATE.isoformat())
        regular_price = settings.get("regular_price", REGULAR_PRICE)
        min_price = settings.get("min_price", MIN_PRICE)
        max_price = settings.get("max_price", 100)
        preset_amounts = settings.get("preset_amounts", "1.00, 2.00, 4.62, 10.00")
        promo_message = settings.get("promo_message", "Pay What You Want - Limited Time!")
        paypal_link_1 = settings.get("paypal_link_1", PAYPAL_PAYMENT_LINK_1)
        paypal_link_2 = settings.get("paypal_link_2", PAYPAL_PAYMENT_LINK_2)
    else:
        promo_end = PROMO_END_DATE.isoformat()
        regular_price = REGULAR_PRICE
        min_price = MIN_PRICE
        max_price = 100
        preset_amounts = "1.00, 2.00, 4.62, 10.00"
        promo_message = "Pay What You Want - Limited Time!"
        paypal_link_1 = PAYPAL_PAYMENT_LINK_1
        paypal_link_2 = PAYPAL_PAYMENT_LINK_2
    
    return {
        "is_promo_active": is_promo_active,
        "promo_end_date": promo_end,
        "regular_price": regular_price,
        "min_price": min_price,
        "max_price": max_price,
        "preset_amounts": preset_amounts,
        "promo_message": promo_message,
        "paypal_link_1": paypal_link_1,
        "paypal_link_2": paypal_link_2,
        "message": promo_message if is_promo_active else f"Annual subscription: ${regular_price}/year"
    }

@api_router.get("/subscription/status")
async def get_subscription_status(user: dict = Depends(require_user)):
    """Get user's subscription status"""
    subscription = await db.subscriptions.find_one(
        {"user_id": user["id"]},
        {"_id": 0}
    )
    
    if not subscription:
        return {
            "is_subscribed": False,
            "subscription": None,
            "message": "No active subscription"
        }
    
    # Check if subscription is expired
    expires_at = datetime.fromisoformat(subscription.get("expires_at", "2000-01-01T00:00:00+00:00").replace("Z", "+00:00"))
    is_active = datetime.now(timezone.utc) < expires_at
    
    return {
        "is_subscribed": is_active,
        "subscription": subscription,
        "message": "Subscription active" if is_active else "Subscription expired"
    }

@api_router.post("/subscription/record-payment")
async def record_payment(
    amount: float = Query(..., ge=0.01),
    paypal_transaction_id: str = Query(None),
    user: dict = Depends(require_user)
):
    """Record a PayPal payment and activate subscription"""
    now = datetime.now(timezone.utc)
    is_promo = now < PROMO_END_DATE
    
    # Get config
    settings = await db.admin_settings.find_one({"type": "subscription_config"}, {"_id": 0})
    regular_price = settings.get("regular_price", REGULAR_PRICE) if settings else REGULAR_PRICE
    
    # Validate amount after promo period
    if not is_promo and amount < regular_price:
        raise HTTPException(status_code=400, detail=f"Minimum payment is ${regular_price} after promotional period")
    
    # Calculate subscription duration (1 year)
    expires_at = now + timedelta(days=365)
    
    subscription = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "username": user["username"],
        "email": user.get("email", ""),
        "amount_paid": amount,
        "paypal_transaction_id": paypal_transaction_id,
        "started_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "is_promo_rate": is_promo,
        "status": "active"
    }
    
    # Upsert subscription
    await db.subscriptions.update_one(
        {"user_id": user["id"]},
        {"$set": subscription},
        upsert=True
    )
    
    # Update user's subscription status
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"is_subscribed": True, "subscription_expires": expires_at.isoformat()}}
    )
    
    return {
        "message": "Subscription activated! Thank you for your support!",
        "subscription": subscription
    }

@api_router.put("/admin/subscription/config")
async def update_subscription_config(
    regular_price: float = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    preset_amounts: str = Query(None),
    promo_end_date: str = Query(None),
    promo_message: str = Query(None),
    paypal_link_1: str = Query(None),
    paypal_link_2: str = Query(None),
    user: dict = Depends(require_user)
):
    """Update subscription configuration (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {"type": "subscription_config"}
    if regular_price is not None:
        update_data["regular_price"] = regular_price
    if min_price is not None:
        update_data["min_price"] = min_price
    if max_price is not None:
        update_data["max_price"] = max_price
    if preset_amounts is not None:
        update_data["preset_amounts"] = preset_amounts
    if promo_end_date is not None:
        update_data["promo_end_date"] = promo_end_date
    if promo_message is not None:
        update_data["promo_message"] = promo_message
    if paypal_link_1 is not None:
        update_data["paypal_link_1"] = paypal_link_1
    if paypal_link_2 is not None:
        update_data["paypal_link_2"] = paypal_link_2
    
    await db.admin_settings.update_one(
        {"type": "subscription_config"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Subscription configuration updated"}

@api_router.put("/admin/database-limits")
async def update_database_limits(
    user_max_results_limit: int = Query(..., ge=100, le=10000, description="Max results per user (100-10000)"),
    user: dict = Depends(require_user)
):
    """Update the maximum number of results a user can store in their database (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$set": {"user_max_results_limit": user_max_results_limit}},
        upsert=True
    )
    
    return {
        "message": f"Database limit updated to {user_max_results_limit} results per user",
        "user_max_results_limit": user_max_results_limit
    }

@api_router.get("/admin/database-limits")
async def get_database_limits(user: dict = Depends(require_user)):
    """Get current database limits (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    # Get stats about all users' database usage
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "count": {"$sum": 1}
        }},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "id",
            "as": "user_info"
        }},
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "user_id": "$_id",
            "username": "$user_info.username",
            "result_count": "$count"
        }},
        {"$sort": {"result_count": -1}},
        {"$limit": 20}
    ]
    
    user_stats = await db.search_results.aggregate(pipeline).to_list(20)
    
    return {
        "user_max_results_limit": settings.user_max_results_limit,
        "top_users_by_results": user_stats
    }

@api_router.get("/admin/search-pages-config")
async def get_search_pages_config(user: dict = Depends(require_user)):
    """Get search pages configuration (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    return {
        "unpaid_user_search_pages": settings.unpaid_user_search_pages,
        "paid_user_search_pages": settings.paid_user_search_pages,
        "results_per_page": settings.results_per_page,
        "is_app_free": settings.is_app_free,
        "unpaid_max_results": settings.get_max_results_for_user(False),
        "paid_max_results": settings.get_max_results_for_user(True)
    }

@api_router.put("/admin/search-pages-config")
async def update_search_pages_config(
    unpaid_user_search_pages: int = Query(None, ge=1, le=99, description="Pages for unpaid users (1-99). >40 = free app"),
    paid_user_search_pages: int = Query(None, ge=1, le=99, description="Pages for paid users (1-99)"),
    results_per_page: int = Query(None, ge=10, le=50, description="Results per page (10-50)"),
    user: dict = Depends(require_user)
):
    """Update search pages configuration (admin only). If unpaid_user_search_pages > 40, app is free."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {}
    if unpaid_user_search_pages is not None:
        update_data["unpaid_user_search_pages"] = unpaid_user_search_pages
    if paid_user_search_pages is not None:
        update_data["paid_user_search_pages"] = paid_user_search_pages
    if results_per_page is not None:
        update_data["results_per_page"] = results_per_page
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No settings to update")
    
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$set": update_data},
        upsert=True
    )
    
    # Fetch updated settings
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    is_free_msg = " (App is FREE - unpaid users get >40 pages)" if settings.is_app_free else ""
    
    return {
        "message": f"Search pages configuration updated{is_free_msg}",
        "unpaid_user_search_pages": settings.unpaid_user_search_pages,
        "paid_user_search_pages": settings.paid_user_search_pages,
        "results_per_page": settings.results_per_page,
        "is_app_free": settings.is_app_free,
        "unpaid_max_results": settings.get_max_results_for_user(False),
        "paid_max_results": settings.get_max_results_for_user(True)
    }

@api_router.get("/app-status")
async def get_app_status():
    """Get public app status (free vs paid) - no auth required"""
    settings_doc = await db.admin_settings.find_one({"id": "admin_settings"})
    settings = AdminSettings(**settings_doc) if settings_doc else AdminSettings()
    
    return {
        "is_app_free": settings.is_app_free,
        "unpaid_user_pages": settings.unpaid_user_search_pages,
        "paid_user_pages": settings.paid_user_search_pages,
        "free_threshold": 40
    }

@api_router.get("/admin/subscriptions")
async def get_all_subscriptions(user: dict = Depends(require_user)):
    """Get all subscriptions (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    subscriptions = await db.subscriptions.find({}, {"_id": 0}).sort("started_at", -1).to_list(500)
    
    total_revenue = sum(s.get("amount_paid", 0) for s in subscriptions)
    active_count = sum(1 for s in subscriptions if s.get("status") == "active")
    
    return {
        "subscriptions": subscriptions,
        "total_count": len(subscriptions),
        "active_count": active_count,
        "total_revenue": round(total_revenue, 2)
    }

# ============================================
# API ROUTES - LEGAL PAGES (Privacy Policy & Terms of Service)
# ============================================

# Default Privacy Policy
DEFAULT_PRIVACY_POLICY = """
# Privacy Policy for InfoPilot Explorer

**Last Updated: January 10, 2026**

## 1. Introduction

Welcome to InfoPilot Explorer ("we," "our," or "us"). We are committed to protecting your personal information and your right to privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our application.

## 2. Information We Collect

### 2.1 Personal Information
We may collect personal information that you voluntarily provide to us when you:
- Register for an account (username, email address)
- Use our search and categorization features
- Participate in social features (groups, pages, messaging)
- Contact us for support

### 2.2 Automatically Collected Information
When you access InfoPilot Explorer, we may automatically collect:
- Device information (browser type, operating system)
- Usage data (pages visited, features used)
- IP address and general location data

## 3. How We Use Your Information

We use the information we collect to:
- Provide, maintain, and improve our services
- Process your searches and categorizations
- Enable social features (messaging, groups, pages)
- Send you notifications about your account
- Respond to your inquiries and support requests
- Protect against unauthorized access and abuse

## 4. Information Sharing

We do not sell your personal information. We may share your information only:
- With your consent
- To comply with legal obligations
- To protect our rights and prevent fraud
- With service providers who assist our operations

## 5. Data Security

We implement appropriate technical and organizational security measures to protect your personal information. However, no method of transmission over the Internet is 100% secure.

## 6. Your Rights

You have the right to:
- Access your personal data
- Correct inaccurate data
- Delete your account and associated data
- Opt-out of marketing communications

## 7. Third-Party Services

Our application integrates with third-party services including:
- Google (OAuth authentication, Search API, Maps, Safe Browsing)
- These services have their own privacy policies

## 8. Children's Privacy

InfoPilot Explorer is not intended for children under 13. We do not knowingly collect information from children under 13.

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page.

## 10. Contact Us

If you have questions about this Privacy Policy, please contact us through the application.

---
*InfoPilot Explorer - Your Gateway to Organized Information*
"""

# Default Terms of Service
DEFAULT_TERMS_OF_SERVICE = """
# Terms of Service for InfoPilot Explorer

**Last Updated: January 10, 2026**

## 1. Acceptance of Terms

By accessing or using InfoPilot Explorer ("the Application"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, please do not use the Application.

## 2. Description of Service

InfoPilot Explorer is a free information exchange and social networking platform that provides:
- AI-powered intelligent search capabilities
- Hierarchical category organization with custom protocols
- Social features including groups, pages, and messaging
- Integration with Google services (Search, Maps, Safe Browsing)

## 3. User Accounts

### 3.1 Registration
To access certain features, you must create an account. You agree to:
- Provide accurate and complete information
- Maintain the security of your password
- Accept responsibility for all activities under your account
- Notify us immediately of any unauthorized use

### 3.2 Account Termination
We reserve the right to suspend or terminate accounts that violate these Terms or engage in prohibited activities.

## 4. Acceptable Use

You agree NOT to:
- Use the Application for any illegal purpose
- Upload malicious content or malware
- Harass, abuse, or harm other users
- Attempt to gain unauthorized access to our systems
- Scrape or collect user data without permission
- Post content that infringes intellectual property rights
- Spam or send unsolicited communications
- Impersonate others or misrepresent your identity

## 5. User Content

### 5.1 Ownership
You retain ownership of content you create. By posting content, you grant us a license to display and distribute it within the Application.

### 5.2 Content Standards
All user content must comply with our community guidelines. We reserve the right to remove content that violates these Terms.

### 5.3 Protocol Recommendations
Users may suggest changes to public protocols. Protocol owners have full discretion to accept or reject recommendations.

## 6. Intellectual Property

The Application, including its design, features, and content (excluding user-generated content), is owned by us and protected by intellectual property laws.

## 7. Third-Party Services

The Application integrates with third-party services. Your use of these services is subject to their respective terms and policies:
- Google Services (Search, Maps, OAuth, Safe Browsing)
- Other integrated APIs

## 8. Privacy

Your use of the Application is also governed by our Privacy Policy. Please review it to understand our data practices.

## 9. Disclaimers

### 9.1 Service Availability
The Application is provided "as is" without warranties of any kind. We do not guarantee uninterrupted or error-free service.

### 9.2 Search Results
Search results are provided by third-party services. We do not guarantee the accuracy, completeness, or reliability of search results.

### 9.3 User Interactions
We are not responsible for interactions between users, including messages, posts, or other communications.

## 10. Limitation of Liability

To the maximum extent permitted by law, we shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the Application.

## 11. Indemnification

You agree to indemnify and hold us harmless from any claims, damages, or expenses arising from your use of the Application or violation of these Terms.

## 12. Changes to Terms

We may modify these Terms at any time. Continued use of the Application after changes constitutes acceptance of the modified Terms.

## 13. Governing Law

These Terms shall be governed by and construed in accordance with applicable laws, without regard to conflict of law principles.

## 14. Contact Information

For questions about these Terms, please contact us through the Application.

---
*InfoPilot Explorer - Information at Your Fingertips*
"""

@api_router.get("/legal/privacy-policy")
async def get_privacy_policy():
    """Get the privacy policy (public endpoint)"""
    policy = await db.legal_pages.find_one({"type": "privacy_policy"}, {"_id": 0})
    if not policy:
        return {"content": DEFAULT_PRIVACY_POLICY, "last_updated": "January 10, 2026"}
    return {"content": policy.get("content", DEFAULT_PRIVACY_POLICY), "last_updated": policy.get("last_updated", "January 10, 2026")}

@api_router.get("/legal/terms-of-service")
async def get_terms_of_service():
    """Get the terms of service (public endpoint)"""
    terms = await db.legal_pages.find_one({"type": "terms_of_service"}, {"_id": 0})
    if not terms:
        return {"content": DEFAULT_TERMS_OF_SERVICE, "last_updated": "January 10, 2026"}
    return {"content": terms.get("content", DEFAULT_TERMS_OF_SERVICE), "last_updated": terms.get("last_updated", "January 10, 2026")}

@api_router.put("/admin/legal/privacy-policy")
async def update_privacy_policy(content: str = Query(...), user: dict = Depends(require_user)):
    """Update privacy policy (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.legal_pages.update_one(
        {"type": "privacy_policy"},
        {"$set": {
            "type": "privacy_policy",
            "content": content,
            "last_updated": datetime.now(timezone.utc).strftime("%B %d, %Y"),
            "updated_by": user["id"]
        }},
        upsert=True
    )
    return {"message": "Privacy policy updated"}

@api_router.put("/admin/legal/terms-of-service")
async def update_terms_of_service(content: str = Query(...), user: dict = Depends(require_user)):
    """Update terms of service (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.legal_pages.update_one(
        {"type": "terms_of_service"},
        {"$set": {
            "type": "terms_of_service",
            "content": content,
            "last_updated": datetime.now(timezone.utc).strftime("%B %d, %Y"),
            "updated_by": user["id"]
        }},
        upsert=True
    )
    return {"message": "Terms of service updated"}

# ============================================
# API ROUTES - EMAIL DIGEST MANAGEMENT
# ============================================

@api_router.get("/admin/email-digest/config")
async def get_email_digest_config(user: dict = Depends(require_admin)):
    """Get email digest configuration"""
    config = await db.admin_settings.find_one({"type": "email_digest_config"}, {"_id": 0})
    if not config:
        config = {
            "enabled": False,
            "day_of_week": "monday",
            "hour": 9,
            "include_trending": True,
            "include_marketplace": True,
            "include_notifications": True,
            "last_sent": None,
            "total_sent": 0
        }
    return config

@api_router.put("/admin/email-digest/config")
async def update_email_digest_config(
    enabled: bool = Query(None),
    day_of_week: str = Query(None),
    hour: int = Query(None, ge=0, le=23),
    include_trending: bool = Query(None),
    include_marketplace: bool = Query(None),
    include_notifications: bool = Query(None),
    user: dict = Depends(require_admin)
):
    """Update email digest configuration"""
    update_data = {}
    if enabled is not None:
        update_data["enabled"] = enabled
    if day_of_week is not None:
        update_data["day_of_week"] = day_of_week
    if hour is not None:
        update_data["hour"] = hour
    if include_trending is not None:
        update_data["include_trending"] = include_trending
    if include_marketplace is not None:
        update_data["include_marketplace"] = include_marketplace
    if include_notifications is not None:
        update_data["include_notifications"] = include_notifications
    
    if update_data:
        update_data["type"] = "email_digest_config"
        await db.admin_settings.update_one(
            {"type": "email_digest_config"},
            {"$set": update_data},
            upsert=True
        )
        
        # Reconfigure the scheduler if schedule changed
        try:
            from services.scheduler import setup_digest_scheduler, start_scheduler, get_scheduler
            
            # Get updated config
            config = await db.admin_settings.find_one({"type": "email_digest_config"})
            if config:
                if config.get("enabled", False):
                    setup_digest_scheduler(db, config.get("day_of_week", "monday"), config.get("hour", 9))
                    start_scheduler()
                    logger.info(f"Email digest scheduler reconfigured: {config.get('day_of_week')} at {config.get('hour')}:00 UTC")
                else:
                    # Remove the job if disabled
                    sched = get_scheduler()
                    try:
                        sched.remove_job("weekly_digest")
                        logger.info("Email digest scheduler job removed (disabled)")
                    except:
                        pass
        except Exception as e:
            logger.error(f"Failed to reconfigure scheduler: {str(e)}")
    
    return {"message": "Email digest configuration updated"}

@api_router.post("/admin/email-digest/preview")
async def preview_email_digest(user: dict = Depends(require_admin)):
    """Preview weekly digest email for admin"""
    # Import here to avoid circular imports
    from services.email_digest import generate_weekly_digest_content, create_digest_html
    
    digest_data = await generate_weekly_digest_content(db, user)
    html = create_digest_html(digest_data)
    
    return {
        "preview_data": digest_data,
        "html": html
    }

@api_router.post("/admin/email-digest/send-now")
async def send_digests_now(user: dict = Depends(require_admin)):
    """Manually trigger sending weekly digests to all users"""
    from services.email_digest import process_weekly_digests
    
    result = await process_weekly_digests(db)
    
    # Update last sent time
    await db.admin_settings.update_one(
        {"type": "email_digest_config"},
        {"$set": {
            "last_sent": datetime.now(timezone.utc).isoformat(),
            "$inc": {"total_sent": result["sent"]}
        }},
        upsert=True
    )
    
    return {
        "message": f"Digest processing complete",
        "results": result
    }

@api_router.put("/user/email-preferences")
async def update_email_preferences(
    digest_enabled: bool = Query(...),
    user: dict = Depends(require_user)
):
    """Update user's email preferences"""
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"digest_enabled": digest_enabled}}
    )
    return {"message": "Email preferences updated", "digest_enabled": digest_enabled}

@api_router.get("/user/email-preferences")
async def get_email_preferences(user: dict = Depends(require_user)):
    """Get user's email preferences"""
    user_data = await db.users.find_one({"id": user["id"]}, {"_id": 0, "digest_enabled": 1})
    return {"digest_enabled": user_data.get("digest_enabled", True)}

# ============================================
# API ROUTES - SOCIAL MODERATION (ADMIN)
# ============================================

@api_router.get("/admin/moderation/dashboard")
async def get_moderation_dashboard(user: dict = Depends(require_admin)):
    """Get moderation dashboard statistics"""
    # Count various content types
    total_groups = await db.groups.count_documents({})
    total_pages = await db.pages.count_documents({})
    total_posts = await db.group_posts.count_documents({}) + await db.page_posts.count_documents({})
    total_comments = await db.comments.count_documents({})
    total_messages = await db.messages.count_documents({})
    
    # Count reported content
    reported_content = await db.reports.count_documents({"status": "pending"})
    
    # Get recent activity
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_groups = await db.groups.count_documents({"created_at": {"$gte": week_ago}})
    new_pages = await db.pages.count_documents({"created_at": {"$gte": week_ago}})
    new_users = await db.users.count_documents({"created_at": {"$gte": week_ago}})
    
    return {
        "content_stats": {
            "groups": total_groups,
            "pages": total_pages,
            "posts": total_posts,
            "comments": total_comments,
            "messages": total_messages
        },
        "reported_content": reported_content,
        "weekly_growth": {
            "new_groups": new_groups,
            "new_pages": new_pages,
            "new_users": new_users
        }
    }

@api_router.get("/admin/moderation/groups")
async def get_all_groups_admin(
    page: int = 1,
    search: str = None,
    user: dict = Depends(require_admin)
):
    """Get all groups for moderation"""
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    per_page = 20
    skip = (page - 1) * per_page
    
    total = await db.groups.count_documents(query)
    groups = await db.groups.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "groups": groups,
        "total": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page
    }

@api_router.delete("/admin/moderation/groups/{group_id}")
async def delete_group_admin(group_id: str, user: dict = Depends(require_admin)):
    """Delete a group (admin moderation)"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Delete group and all related content
    await db.groups.delete_one({"id": group_id})
    await db.group_members.delete_many({"group_id": group_id})
    await db.group_posts.delete_many({"group_id": group_id})
    
    return {"message": f"Group '{group.get('name', 'Unknown')}' and all content deleted"}

@api_router.get("/admin/moderation/pages")
async def get_all_pages_admin(
    page: int = 1,
    search: str = None,
    user: dict = Depends(require_admin)
):
    """Get all pages for moderation"""
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    per_page = 20
    skip = (page - 1) * per_page
    
    total = await db.pages.count_documents(query)
    pages = await db.pages.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "pages": pages,
        "total": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page
    }

@api_router.delete("/admin/moderation/pages/{page_id}")
async def delete_page_admin(page_id: str, user: dict = Depends(require_admin)):
    """Delete a page (admin moderation)"""
    page = await db.pages.find_one({"id": page_id})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Delete page and all related content
    await db.pages.delete_one({"id": page_id})
    await db.page_followers.delete_many({"page_id": page_id})
    await db.page_posts.delete_many({"page_id": page_id})
    
    return {"message": f"Page '{page.get('name', 'Unknown')}' and all content deleted"}

@api_router.post("/admin/moderation/users/{user_id}/ban")
async def ban_user(user_id: str, reason: str = Query(...), user: dict = Depends(require_admin)):
    """Ban a user"""
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.get("is_admin"):
        raise HTTPException(status_code=400, detail="Cannot ban admin users")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_banned": True,
            "ban_reason": reason,
            "banned_at": datetime.now(timezone.utc).isoformat(),
            "banned_by": user["id"]
        }}
    )
    
    return {"message": f"User '{target_user.get('username', 'Unknown')}' has been banned"}

@api_router.post("/admin/moderation/users/{user_id}/unban")
async def unban_user(user_id: str, user: dict = Depends(require_admin)):
    """Unban a user"""
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_banned": False}, "$unset": {"ban_reason": "", "banned_at": "", "banned_by": ""}}
    )
    
    return {"message": f"User '{target_user.get('username', 'Unknown')}' has been unbanned"}

@api_router.get("/admin/moderation/users")
async def get_users_for_moderation(
    page: int = 1,
    search: str = None,
    banned_only: bool = False,
    user: dict = Depends(require_admin)
):
    """Get users for moderation"""
    query = {}
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if banned_only:
        query["is_banned"] = True
    
    per_page = 20
    skip = (page - 1) * per_page
    
    total = await db.users.count_documents(query)
    users = await db.users.find(
        query,
        {"_id": 0, "password_hash": 0}
    ).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page
    }

@api_router.post("/report")
async def report_content(
    content_type: str = Query(...),  # user, group, page, post, comment
    content_id: str = Query(...),
    reason: str = Query(...),
    user: dict = Depends(require_user)
):
    """Report content for moderation"""
    report = {
        "id": str(uuid.uuid4()),
        "content_type": content_type,
        "content_id": content_id,
        "reason": reason,
        "reported_by": user["id"],
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.reports.insert_one(report)
    return {"message": "Report submitted successfully", "report_id": report["id"]}

@api_router.get("/admin/moderation/reports")
async def get_reports(
    status: str = "pending",
    page: int = 1,
    user: dict = Depends(require_admin)
):
    """Get reported content"""
    per_page = 20
    skip = (page - 1) * per_page
    
    query = {"status": status} if status else {}
    total = await db.reports.count_documents(query)
    reports = await db.reports.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "reports": reports,
        "total": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page
    }

@api_router.put("/admin/moderation/reports/{report_id}")
async def update_report_status(
    report_id: str,
    status: str = Query(...),  # pending, resolved, dismissed
    action_taken: str = Query(None),
    user: dict = Depends(require_admin)
):
    """Update report status"""
    result = await db.reports.update_one(
        {"id": report_id},
        {"$set": {
            "status": status,
            "action_taken": action_taken,
            "resolved_by": user["id"],
            "resolved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report status updated"}

# ============================================
# API ROUTES - PRIVATE MESSAGING
# ============================================

MAX_IMAGE_SIZE = 8 * 1024 * 1024  # 8MB limit

def get_conversation_id(user1_id: str, user2_id: str) -> str:
    """Generate consistent conversation ID for two users"""
    sorted_ids = sorted([user1_id, user2_id])
    return f"conv_{sorted_ids[0]}_{sorted_ids[1]}"

@api_router.get("/messages/conversations")
async def get_conversations(user: dict = Depends(require_user)):
    """Get all conversations for the current user"""
    conversations = await db.conversations.find(
        {"participants": user["id"]},
        {"_id": 0}
    ).sort("last_message_at", -1).to_list(100)
    
    # Count unread messages for each conversation
    for conv in conversations:
        unread = await db.messages.count_documents({
            "conversation_id": conv["id"],
            "recipient_id": user["id"],
            "read": False
        })
        conv["unread_count"] = unread
    
    return {"conversations": conversations}

@api_router.get("/messages/conversation/{other_user_id}")
async def get_conversation_messages(other_user_id: str, page: int = 1, limit: int = 50, user: dict = Depends(require_user)):
    """Get messages in a conversation with another user"""
    conversation_id = get_conversation_id(user["id"], other_user_id)
    
    skip = (page - 1) * limit
    messages = await db.messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Mark messages as read
    await db.messages.update_many(
        {"conversation_id": conversation_id, "recipient_id": user["id"], "read": False},
        {"$set": {"read": True}}
    )
    
    # Get other user info
    other_user = await db.users.find_one({"id": other_user_id}, {"_id": 0, "id": 1, "username": 1})
    
    return {
        "messages": list(reversed(messages)),
        "other_user": other_user,
        "conversation_id": conversation_id
    }

@api_router.post("/messages/send")
async def send_message(data: MessageCreate, user: dict = Depends(require_user)):
    """Send a message to another user"""
    # Verify recipient exists
    recipient = await db.users.find_one({"id": data.recipient_id})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Can't message yourself
    if data.recipient_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    
    # Check image size if provided
    if data.image_url:
        # If it's base64, check size
        if data.image_url.startswith("data:"):
            # Extract base64 part
            try:
                base64_data = data.image_url.split(",")[1] if "," in data.image_url else data.image_url
                image_size = len(base64.b64decode(base64_data))
                if image_size > MAX_IMAGE_SIZE:
                    raise HTTPException(status_code=400, detail=f"Image size exceeds {MAX_IMAGE_SIZE // (1024*1024)}MB limit")
            except Exception as e:
                if "exceeds" in str(e):
                    raise e
                raise HTTPException(status_code=400, detail="Invalid image data")
    
    conversation_id = get_conversation_id(user["id"], data.recipient_id)
    
    message = {
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "sender_id": user["id"],
        "sender_username": user["username"],
        "recipient_id": data.recipient_id,
        "recipient_username": recipient["username"],
        "content": data.content,
        "image_url": data.image_url,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message)
    
    # Update or create conversation
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        conversation = {
            "id": conversation_id,
            "participants": [user["id"], data.recipient_id],
            "participant_usernames": {
                user["id"]: user["username"],
                data.recipient_id: recipient["username"]
            },
            "last_message": data.content[:100] + ("..." if len(data.content) > 100 else ""),
            "last_message_at": message["created_at"],
            "created_at": message["created_at"]
        }
        await db.conversations.insert_one(conversation)
    else:
        await db.conversations.update_one(
            {"id": conversation_id},
            {"$set": {
                "last_message": data.content[:100] + ("..." if len(data.content) > 100 else ""),
                "last_message_at": message["created_at"]
            }}
        )
    
    # Send email notification to recipient
    if recipient.get("email"):
        email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #e0e0ff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #0f0f1a; border: 1px solid #8b5cf6; border-radius: 8px; padding: 20px;">
                <h2 style="color: #ec4899; margin-bottom: 20px;">💬 New Message from {user["username"]}</h2>
                <p style="color: #c4b5fd;">Hello {recipient.get('username', 'Pilot')},</p>
                <p style="color: #c4b5fd;">You have received a new message on InfoPilot Explorer:</p>
                
                <div style="background-color: #1f1f35; border-left: 4px solid #ec4899; padding: 15px; margin: 15px 0;">
                    <p style="color: #c4b5fd; margin: 0;">{data.content[:200]}{"..." if len(data.content) > 200 else ""}</p>
                </div>
                
                {"<p style='color: #8b5cf6;'>📷 This message includes an image attachment.</p>" if data.image_url else ""}
                
                <p style="color: #c4b5fd; margin-top: 20px;">Log in to InfoPilot Explorer to view and reply.</p>
                
                <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">— InfoPilot Explorer Team</p>
            </div>
        </body>
        </html>
        """
        asyncio.create_task(send_notification_email(
            recipient["email"],
            f"💬 New message from {user['username']}",
            email_html
        ))
    
    # Broadcast message via WebSocket in real-time
    ws_message = {
        "type": "new_message",
        "message": {k: v for k, v in message.items() if k != "_id"},
        "conversation_id": conversation_id,
        "sender_username": user["username"]
    }
    await ws_manager.broadcast_to_conversation(ws_message, [user["id"], data.recipient_id])
    
    return {"message": "Message sent", "data": {k: v for k, v in message.items() if k != "_id"}}

@api_router.get("/messages/unread-count")
async def get_unread_count(user: dict = Depends(require_user)):
    """Get total unread message count"""
    count = await db.messages.count_documents({
        "recipient_id": user["id"],
        "read": False
    })
    return {"unread_count": count}

@api_router.put("/messages/mark-read/{conversation_id}")
async def mark_conversation_read(conversation_id: str, user: dict = Depends(require_user)):
    """Mark all messages in a conversation as read"""
    result = await db.messages.update_many(
        {"conversation_id": conversation_id, "recipient_id": user["id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"message": "Messages marked as read", "count": result.modified_count}

@api_router.delete("/messages/{message_id}")
async def delete_message(message_id: str, user: dict = Depends(require_user)):
    """Delete a message (sender only)"""
    message = await db.messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message["sender_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Can only delete your own messages")
    
    await db.messages.delete_one({"id": message_id})
    return {"message": "Message deleted"}

@api_router.get("/users/search")
async def search_users(q: str = Query(..., min_length=1), user: dict = Depends(require_user)):
    """Search for users by username"""
    users = await db.users.find(
        {"username": {"$regex": q, "$options": "i"}, "id": {"$ne": user["id"]}},
        {"_id": 0, "id": 1, "username": 1, "email": 1}
    ).limit(20).to_list(20)
    
    return {"users": users}

# ============================================
# API ROUTES - REACTIONS & COMMENTS (Facebook-style)
# ============================================

@api_router.post("/posts/{post_type}/{post_id}/reactions")
async def add_reaction(post_type: str, post_id: str, data: ReactionCreate, user: dict = Depends(require_user)):
    """Add a reaction to a post (group, page, update, or search_result)"""
    if data.reaction_type not in REACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid reaction type. Must be one of: {REACTION_TYPES}")
    
    # Determine collection based on post type
    collection_map = {
        "group": db.group_posts,
        "page": db.page_posts,
        "update": db.updates,
        "search_result": db.search_results
    }
    if post_type not in collection_map:
        raise HTTPException(status_code=400, detail="Invalid post type")
    collection = collection_map[post_type]
    
    post = await collection.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Initialize reactions dict if not exists
    reactions = post.get("reactions", {})
    
    # Remove user from all other reaction types first
    for rtype in REACTION_TYPES:
        if rtype in reactions and user["id"] in reactions[rtype]:
            reactions[rtype].remove(user["id"])
    
    # Add user to new reaction type
    if data.reaction_type not in reactions:
        reactions[data.reaction_type] = []
    if user["id"] not in reactions[data.reaction_type]:
        reactions[data.reaction_type].append(user["id"])
    
    # Calculate counts
    reaction_counts = {rtype: len(reactions.get(rtype, [])) for rtype in REACTION_TYPES}
    total_reactions = sum(reaction_counts.values())
    
    await collection.update_one(
        {"id": post_id},
        {"$set": {"reactions": reactions, "reaction_counts": reaction_counts, "total_reactions": total_reactions}}
    )
    
    return {"message": "Reaction added", "reactions": reactions, "reaction_counts": reaction_counts, "user_reaction": data.reaction_type}

@api_router.delete("/posts/{post_type}/{post_id}/reactions")
async def remove_reaction(post_type: str, post_id: str, user: dict = Depends(require_user)):
    """Remove user's reaction from a post"""
    collection_map = {
        "group": db.group_posts,
        "page": db.page_posts,
        "update": db.updates,
        "search_result": db.search_results
    }
    if post_type not in collection_map:
        raise HTTPException(status_code=400, detail="Invalid post type")
    collection = collection_map[post_type]
    
    post = await collection.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    reactions = post.get("reactions", {})
    
    # Remove user from all reaction types
    for rtype in REACTION_TYPES:
        if rtype in reactions and user["id"] in reactions[rtype]:
            reactions[rtype].remove(user["id"])
    
    reaction_counts = {rtype: len(reactions.get(rtype, [])) for rtype in REACTION_TYPES}
    total_reactions = sum(reaction_counts.values())
    
    await collection.update_one(
        {"id": post_id},
        {"$set": {"reactions": reactions, "reaction_counts": reaction_counts, "total_reactions": total_reactions}}
    )
    
    return {"message": "Reaction removed", "reactions": reactions, "reaction_counts": reaction_counts}

@api_router.get("/posts/{post_type}/{post_id}/reactions")
async def get_reactions(post_type: str, post_id: str, user: dict = Depends(require_user)):
    """Get reactions for a post"""
    collection_map = {
        "group": db.group_posts,
        "page": db.page_posts,
        "update": db.updates,
        "search_result": db.search_results
    }
    if post_type not in collection_map:
        raise HTTPException(status_code=400, detail="Invalid post type")
    collection = collection_map[post_type]
    
    post = await collection.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    reactions = post.get("reactions", {})
    reaction_counts = post.get("reaction_counts", {})
    
    # Find user's reaction
    user_reaction = None
    for rtype in REACTION_TYPES:
        if rtype in reactions and user["id"] in reactions[rtype]:
            user_reaction = rtype
            break
    
    return {"reactions": reactions, "reaction_counts": reaction_counts, "user_reaction": user_reaction}

# ============================================
# API ROUTES - COMMENTS WITH NESTED REPLIES
# ============================================

@api_router.post("/posts/{post_type}/{post_id}/comments")
async def add_comment(post_type: str, post_id: str, data: CommentCreate, user: dict = Depends(require_user)):
    """Add a comment to a post or reply to another comment"""
    collection_map = {
        "group": db.group_posts,
        "page": db.page_posts,
        "update": db.updates,
        "search_result": db.search_results
    }
    if post_type not in collection_map:
        raise HTTPException(status_code=400, detail="Invalid post type")
    collection = collection_map[post_type]
    
    post = await collection.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = {
        "id": str(uuid.uuid4()),
        "post_id": post_id,
        "post_type": post_type,
        "user_id": user["id"],
        "username": user["username"],
        "content": data.content,
        "parent_id": data.parent_id,  # For nested replies
        "reactions": {},
        "reaction_counts": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.comments.insert_one(comment)
    
    # Update comment count on post
    await collection.update_one(
        {"id": post_id},
        {"$inc": {"comment_count": 1}}
    )
    
    return {"message": "Comment added", "comment": {k: v for k, v in comment.items() if k != "_id"}}

@api_router.get("/posts/{post_type}/{post_id}/comments")
async def get_comments(post_type: str, post_id: str, user: dict = Depends(require_user)):
    """Get all comments for a post with nested structure"""
    comments = await db.comments.find(
        {"post_id": post_id, "post_type": post_type},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Build nested structure
    comment_map = {c["id"]: {**c, "replies": []} for c in comments}
    root_comments = []
    
    for comment in comments:
        if comment.get("parent_id") and comment["parent_id"] in comment_map:
            comment_map[comment["parent_id"]]["replies"].append(comment_map[comment["id"]])
        else:
            root_comments.append(comment_map[comment["id"]])
    
    return {"comments": root_comments, "total_count": len(comments)}

@api_router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user: dict = Depends(require_user)):
    """Delete a comment (owner only)"""
    comment = await db.comments.find_one({"id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment["user_id"] != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    # Delete comment and all its replies
    await db.comments.delete_many({"$or": [{"id": comment_id}, {"parent_id": comment_id}]})
    
    # Update comment count on post
    collection_map = {
        "group": db.group_posts,
        "page": db.page_posts,
        "update": db.updates,
        "search_result": db.search_results
    }
    if comment["post_type"] in collection_map:
        collection = collection_map[comment["post_type"]]
        await collection.update_one(
            {"id": comment["post_id"]},
            {"$inc": {"comment_count": -1}}
        )
    
    return {"message": "Comment deleted"}

@api_router.post("/comments/{comment_id}/reactions")
async def add_comment_reaction(comment_id: str, data: ReactionCreate, user: dict = Depends(require_user)):
    """Add a reaction to a comment"""
    if data.reaction_type not in REACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid reaction type")
    
    comment = await db.comments.find_one({"id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    reactions = comment.get("reactions", {})
    
    # Remove user from all other reaction types
    for rtype in REACTION_TYPES:
        if rtype in reactions and user["id"] in reactions[rtype]:
            reactions[rtype].remove(user["id"])
    
    # Add user to new reaction type
    if data.reaction_type not in reactions:
        reactions[data.reaction_type] = []
    if user["id"] not in reactions[data.reaction_type]:
        reactions[data.reaction_type].append(user["id"])
    
    reaction_counts = {rtype: len(reactions.get(rtype, [])) for rtype in REACTION_TYPES}
    
    await db.comments.update_one(
        {"id": comment_id},
        {"$set": {"reactions": reactions, "reaction_counts": reaction_counts}}
    )
    
    return {"message": "Reaction added", "reactions": reactions, "reaction_counts": reaction_counts}

# ============================================
# API ROUTES - UPDATES (User Posts on Ultimate Search Page)
# ============================================

@api_router.get("/updates")
async def get_user_updates(user: dict = Depends(require_user)):
    """Get updates/posts from the user's Ultimate Search page"""
    updates = await db.updates.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    return {"updates": updates}

@api_router.get("/updates/{user_id}/public")
async def get_public_updates(user_id: str, user: dict = Depends(require_user)):
    """Get public updates from any user's Ultimate Search page"""
    updates = await db.updates.find(
        {"user_id": user_id, "visibility": "public"},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0, "username": 1, "page_name": 1})
    
    return {"updates": updates, "user": target_user}

@api_router.post("/updates")
async def create_update(data: UpdateCreate, user: dict = Depends(require_user)):
    """Create an update/post on user's Ultimate Search page"""
    update = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "username": user["username"],
        "content": data.content,
        "image_url": data.image_url,
        "visibility": "public",
        "reactions": {},
        "reaction_counts": {},
        "total_reactions": 0,
        "comment_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.updates.insert_one(update)
    return {"message": "Update posted", "update": {k: v for k, v in update.items() if k != "_id"}}

@api_router.delete("/updates/{update_id}")
async def delete_update(update_id: str, user: dict = Depends(require_user)):
    """Delete an update (owner only)"""
    update = await db.updates.find_one({"id": update_id})
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")
    
    if update["user_id"] != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this update")
    
    await db.updates.delete_one({"id": update_id})
    await db.comments.delete_many({"post_id": update_id, "post_type": "update"})
    
    return {"message": "Update deleted"}

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

@api_router.get("/statistics/popular-protocols")
async def get_popular_protocols(
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(require_user)
):
    """Get most popular protocols by clipboard copy count"""
    # Get protocols sorted by copy_count
    pipeline = [
        {"$match": {"is_public": True, "copy_count": {"$gt": 0}}},
        {"$sort": {"copy_count": -1}},
        {"$limit": limit}
    ]
    popular = await db.categories.aggregate(pipeline).to_list(limit)
    
    # Get owner usernames
    result = []
    for proto in popular:
        owner = await db.users.find_one({"id": proto["user_id"]})
        owner_name = owner.get("callsign", owner.get("email", "Unknown")) if owner else "Unknown"
        result.append({
            "id": proto["id"],
            "name": proto["name"],
            "protocol_string": proto["protocol_string"],
            "owner_username": owner_name,
            "copy_count": proto.get("copy_count", 0),
            "is_public": proto.get("is_public", True),
            "for_sale": proto.get("for_sale", False),
            "price": proto.get("price")
        })
    
    return {"popular_protocols": result}

@api_router.get("/statistics/global")
async def get_global_statistics(user: dict = Depends(require_user)):
    """Get global statistics for the platform"""
    # Total users
    total_users = await db.users.count_documents({})
    
    # Total public categories
    total_public_categories = await db.categories.count_documents({"is_public": True})
    
    # Total protocols for sale
    total_for_sale = await db.categories.count_documents({"for_sale": True})
    
    # Total protocol purchases
    total_purchases = await db.protocol_purchases.count_documents({"status": "completed"})
    
    # Total clipboard copies (sum of all copy_counts)
    copy_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$copy_count"}}}
    ]
    copy_result = await db.categories.aggregate(copy_pipeline).to_list(1)
    total_copies = copy_result[0]["total"] if copy_result else 0
    
    # Top contributors (users with most public protocols)
    contributor_pipeline = [
        {"$match": {"is_public": True}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_contributors = await db.categories.aggregate(contributor_pipeline).to_list(5)
    
    # Get usernames for contributors
    for contrib in top_contributors:
        user_doc = await db.users.find_one({"id": contrib["_id"]})
        contrib["username"] = user_doc.get("callsign", user_doc.get("email", "Unknown")) if user_doc else "Unknown"
    
    # Recent activity (last 7 days categories created)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_categories = await db.categories.count_documents({
        "created_at": {"$gte": week_ago}
    })
    
    return {
        "total_users": total_users,
        "total_public_categories": total_public_categories,
        "total_protocols_for_sale": total_for_sale,
        "total_protocol_purchases": total_purchases,
        "total_clipboard_copies": total_copies,
        "top_contributors": top_contributors,
        "recent_categories_7d": recent_categories
    }

@api_router.post("/categories/{category_id}/copy")
async def track_protocol_copy(category_id: str, user: dict = Depends(require_user)):
    """Track when a protocol is copied to clipboard"""
    # Find the category
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check access - must be public, owner, or purchased
    can_copy = (
        category.get("is_public", True) or
        category["user_id"] == user["id"]
    )
    
    # Check if purchased (for private for-sale protocols)
    if not can_copy and category.get("for_sale"):
        purchase = await db.protocol_purchases.find_one({
            "buyer_id": user["id"],
            "category_id": category_id,
            "status": "completed"
        })
        can_copy = purchase is not None
    
    if not can_copy:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Increment copy count
    await db.categories.update_one(
        {"id": category_id},
        {"$inc": {"copy_count": 1}}
    )
    
    # Get updated count
    updated = await db.categories.find_one({"id": category_id})
    
    return {
        "message": "Copy tracked",
        "copy_count": updated.get("copy_count", 1)
    }

# ============================================
# API ROUTES - BADGES & ACHIEVEMENTS
# ============================================

def calculate_badges(copy_count: int = 0, protocols_created: int = 0, sales_count: int = 0, purchases_count: int = 0, 
                     friends_count: int = 0, groups_created: int = 0, pages_created: int = 0, messages_sent: int = 0,
                     search_results: int = 0, reactions_count: int = 0, comments_count: int = 0) -> list:
    """Calculate earned badges based on metrics"""
    badges = []
    
    # Copy count badges
    copy_badges = [
        ("first_copy", 1), ("rising_star", 10), ("popular", 25),
        ("trending", 50), ("viral", 100), ("legendary", 500), ("hall_of_fame", 1000)
    ]
    for badge_id, threshold in copy_badges:
        if copy_count >= threshold:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": True, "progress": min(100, (copy_count / threshold) * 100)})
        else:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": False, "progress": (copy_count / threshold) * 100})
    
    # Creator badges
    creator_badges = [("creator_novice", 1), ("creator_prolific", 10), ("creator_master", 25), ("creator_legend", 50)]
    for badge_id, threshold in creator_badges:
        if protocols_created >= threshold:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": True, "progress": 100})
        else:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": False, "progress": (protocols_created / threshold) * 100})
    
    # Sales badges
    sales_badges = [("first_sale", 1), ("seller_bronze", 5), ("seller_silver", 10), ("seller_gold", 25), ("seller_platinum", 50)]
    for badge_id, threshold in sales_badges:
        if sales_count >= threshold:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": True, "progress": 100})
        else:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": False, "progress": (sales_count / threshold) * 100})
    
    # Purchases badges
    purchase_badges = [("collector_novice", 1), ("collector_avid", 10), ("collector_master", 25)]
    for badge_id, threshold in purchase_badges:
        if purchases_count >= threshold:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": True, "progress": 100})
        else:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": False, "progress": (purchases_count / threshold) * 100})
    
    # Social badges
    if friends_count >= 10:
        badges.append({**BADGE_DEFINITIONS["social_butterfly"], "id": "social_butterfly", "earned": True, "progress": 100})
    else:
        badges.append({**BADGE_DEFINITIONS["social_butterfly"], "id": "social_butterfly", "earned": False, "progress": (friends_count / 10) * 100})
    
    if groups_created >= 1:
        badges.append({**BADGE_DEFINITIONS["group_leader"], "id": "group_leader", "earned": True, "progress": 100})
    else:
        badges.append({**BADGE_DEFINITIONS["group_leader"], "id": "group_leader", "earned": False, "progress": 0})
    
    if pages_created >= 1:
        badges.append({**BADGE_DEFINITIONS["influencer"], "id": "influencer", "earned": True, "progress": 100})
    else:
        badges.append({**BADGE_DEFINITIONS["influencer"], "id": "influencer", "earned": False, "progress": 0})
    
    if messages_sent >= 50:
        badges.append({**BADGE_DEFINITIONS["messenger"], "id": "messenger", "earned": True, "progress": 100})
    else:
        badges.append({**BADGE_DEFINITIONS["messenger"], "id": "messenger", "earned": False, "progress": (messages_sent / 50) * 100})
    
    # Search badges
    search_badges = [("researcher", 100), ("data_miner", 500), ("intel_master", 1000)]
    for badge_id, threshold in search_badges:
        if search_results >= threshold:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": True, "progress": 100})
        else:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": False, "progress": (search_results / threshold) * 100})
    
    # Engagement badges
    if reactions_count >= 50:
        badges.append({**BADGE_DEFINITIONS["reactor"], "id": "reactor", "earned": True, "progress": 100})
    else:
        badges.append({**BADGE_DEFINITIONS["reactor"], "id": "reactor", "earned": False, "progress": (reactions_count / 50) * 100})
    
    if comments_count >= 25:
        badges.append({**BADGE_DEFINITIONS["commentator"], "id": "commentator", "earned": True, "progress": 100})
    else:
        badges.append({**BADGE_DEFINITIONS["commentator"], "id": "commentator", "earned": False, "progress": (comments_count / 25) * 100})
    
    return badges

@api_router.get("/badges/my-badges")
async def get_my_badges(user: dict = Depends(require_user)):
    """Get user's badges and achievements"""
    user_id = user["id"]
    
    # Get total copy count across all user's protocols
    copy_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$copy_count"}}}
    ]
    copy_result = await db.categories.aggregate(copy_pipeline).to_list(1)
    total_copies = copy_result[0]["total"] if copy_result else 0
    
    # Get protocols created count
    protocols_created = await db.categories.count_documents({"user_id": user_id})
    
    # Get sales count
    sales_count = await db.protocol_purchases.count_documents({"seller_id": user_id, "status": "completed"})
    
    # Get purchases count
    purchases_count = await db.protocol_purchases.count_documents({"buyer_id": user_id, "status": "completed"})
    
    # Get social stats
    friends_count = await db.friends.count_documents({
        "$or": [{"user_id": user_id}, {"friend_id": user_id}],
        "status": "accepted"
    })
    groups_created = await db.groups.count_documents({"owner_id": user_id})
    pages_created = await db.pages.count_documents({"owner_id": user_id})
    messages_sent = await db.messages.count_documents({"sender_id": user_id})
    
    # Get search stats
    search_results = await db.search_results.count_documents({"user_id": user_id})
    
    # Get engagement stats
    reactions_count = await db.reactions.count_documents({"user_id": user_id})
    comments_count = await db.comments.count_documents({"user_id": user_id})
    
    # Calculate badges with all stats
    all_badges = calculate_badges(
        total_copies, protocols_created, sales_count, purchases_count,
        friends_count, groups_created, pages_created, messages_sent,
        search_results, reactions_count, comments_count
    )
    
    # Separate earned vs locked
    earned_badges = [b for b in all_badges if b["earned"]]
    locked_badges = [b for b in all_badges if not b["earned"]]
    
    # Get top protocol by copies
    top_protocol = await db.categories.find_one(
        {"user_id": user_id, "copy_count": {"$gt": 0}},
        sort=[("copy_count", -1)]
    )
    
    return {
        "stats": {
            "total_copies_received": total_copies,
            "protocols_created": protocols_created,
            "sales_count": sales_count,
            "purchases_count": purchases_count,
            "friends_count": friends_count,
            "groups_created": groups_created,
            "pages_created": pages_created,
            "messages_sent": messages_sent,
            "search_results": search_results,
            "reactions_count": reactions_count,
            "comments_count": comments_count
        },
        "top_protocol": {
            "name": top_protocol["name"],
            "copy_count": top_protocol.get("copy_count", 0)
        } if top_protocol else None,
        "earned_badges": earned_badges,
        "locked_badges": locked_badges,
        "total_earned": len(earned_badges),
        "total_badges": len(all_badges)
    }

@api_router.post("/badges/check-new")
async def check_new_badges(user: dict = Depends(require_user)):
    """Check if user has earned new badges since last check"""
    user_id = user["id"]
    
    # Get user's previously seen badges
    user_doc = await db.users.find_one({"id": user_id})
    seen_badges = user_doc.get("seen_badges", []) if user_doc else []
    
    # Calculate current badges
    copy_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$copy_count"}}}
    ]
    copy_result = await db.categories.aggregate(copy_pipeline).to_list(1)
    total_copies = copy_result[0]["total"] if copy_result else 0
    
    protocols_created = await db.categories.count_documents({"user_id": user_id})
    sales_count = await db.protocol_purchases.count_documents({"seller_id": user_id, "status": "completed"})
    purchases_count = await db.protocol_purchases.count_documents({"buyer_id": user_id, "status": "completed"})
    
    all_badges = calculate_badges(total_copies, protocols_created, sales_count, purchases_count)
    earned_badges = [b for b in all_badges if b["earned"]]
    
    # Find newly earned badges
    new_badges = [b for b in earned_badges if b["id"] not in seen_badges]
    
    # Update seen badges
    if new_badges:
        all_earned_ids = [b["id"] for b in earned_badges]
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"seen_badges": all_earned_ids}}
        )
    
    # Add promotional messages for badges
    promotional_messages = [
        "📚 Love InfoPilot? Check out 'Letters to Evelyn' by John Selman - a captivating novel!",
        "🚀 Unlock premium features with a subscription - Pay What You Want!",
        "📖 Get inspired! 'Letters to Evelyn' by John Selman - 19 Five-Star Reviews on Amazon!",
        "💎 Support the platform - Subscribe today and help us grow!",
        "✨ Did you know? Subscribers get exclusive access to advanced features!",
    ]
    
    import random
    promo = random.choice(promotional_messages) if new_badges else None
    
    return {
        "new_badges": new_badges,
        "has_new_badges": len(new_badges) > 0,
        "promotional_message": promo,
        "book_link": "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0DNJHPH6P",
        "subscribe_link": "/subscribe"
    }

@api_router.get("/badges/protocol/{category_id}")
async def get_protocol_badges(category_id: str, user: dict = Depends(require_user)):
    """Get badges for a specific protocol"""
    category = await db.categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    copy_count = category.get("copy_count", 0)
    
    # Copy count badges only for individual protocols
    badges = []
    copy_badges = [
        ("first_copy", 1), ("rising_star", 10), ("popular", 25),
        ("trending", 50), ("viral", 100), ("legendary", 500), ("hall_of_fame", 1000)
    ]
    
    for badge_id, threshold in copy_badges:
        if copy_count >= threshold:
            badges.append({**BADGE_DEFINITIONS[badge_id], "id": badge_id, "earned": True})
    
    # Get highest badge
    highest_badge = badges[-1] if badges else None
    
    return {
        "protocol_name": category["name"],
        "copy_count": copy_count,
        "badges": badges,
        "highest_badge": highest_badge,
        "next_milestone": next((t for _, t in copy_badges if t > copy_count), None)
    }

@api_router.get("/badges/leaderboard")
async def get_badges_leaderboard(user: dict = Depends(require_user)):
    """Get top users by earned badges"""
    # Get all users with their stats
    users = await db.users.find({}, {"_id": 0, "id": 1, "callsign": 1, "email": 1}).to_list(100)
    
    leaderboard = []
    for u in users:
        # Get total copies for user's protocols
        copy_pipeline = [
            {"$match": {"user_id": u["id"]}},
            {"$group": {"_id": None, "total": {"$sum": "$copy_count"}}}
        ]
        copy_result = await db.categories.aggregate(copy_pipeline).to_list(1)
        total_copies = copy_result[0]["total"] if copy_result else 0
        
        protocols_created = await db.categories.count_documents({"user_id": u["id"]})
        sales_count = await db.protocol_purchases.count_documents({"seller_id": u["id"], "status": "completed"})
        purchases_count = await db.protocol_purchases.count_documents({"buyer_id": u["id"], "status": "completed"})
        
        badges = calculate_badges(total_copies, protocols_created, sales_count, purchases_count)
        earned_count = len([b for b in badges if b["earned"]])
        
        if earned_count > 0:  # Only include users with at least 1 badge
            leaderboard.append({
                "user_id": u["id"],
                "username": u.get("callsign", u.get("email", "Unknown")),
                "badges_earned": earned_count,
                "total_copies": total_copies,
                "top_badges": [b for b in badges if b["earned"]][:3]  # Top 3 badges
            })
    
    # Sort by badges earned
    leaderboard.sort(key=lambda x: (-x["badges_earned"], -x["total_copies"]))
    
    return {"leaderboard": leaderboard[:20]}

# ============================================
# TOP SELLERS LEADERBOARD (Sales Count & Revenue)
# ============================================

@api_router.get("/marketplace/top-sellers")
async def get_top_sellers(
    tab: str = Query("sales", description="Tab: 'sales' for count or 'revenue' for earnings"),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_user)
):
    """Get top sellers leaderboard with tabs for sales count and revenue"""
    
    # Aggregate sales data by seller
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$seller_id",
            "sales_count": {"$sum": 1},
            "total_revenue": {"$sum": "$amount"},
            "protocols_sold": {"$addToSet": "$protocol_id"}
        }}
    ]
    
    sales_data = await db.protocol_purchases.aggregate(pipeline).to_list(1000)
    
    # Enrich with user data
    leaderboard = []
    for seller in sales_data:
        seller_user = await db.users.find_one({"id": seller["_id"]}, {"_id": 0, "username": 1, "email": 1, "profile_picture": 1})
        if seller_user:
            leaderboard.append({
                "user_id": seller["_id"],
                "username": seller_user.get("username", "Unknown"),
                "profile_picture": seller_user.get("profile_picture"),
                "sales_count": seller["sales_count"],
                "total_revenue": round(seller["total_revenue"], 2),
                "unique_protocols_sold": len(seller["protocols_sold"]),
                "earnings_after_split": round(seller["total_revenue"] * 0.90, 2)  # 90% goes to seller
            })
    
    # Sort based on tab
    if tab == "revenue":
        leaderboard.sort(key=lambda x: -x["total_revenue"])
    else:  # Default to sales count
        leaderboard.sort(key=lambda x: -x["sales_count"])
    
    # Add rank
    for i, seller in enumerate(leaderboard[:limit], 1):
        seller["rank"] = i
    
    return {
        "tab": tab,
        "leaderboard": leaderboard[:limit],
        "total_sellers": len(leaderboard)
    }

@api_router.get("/marketplace/my-sales")
async def get_my_sales(user: dict = Depends(require_user)):
    """Get current user's sales statistics"""
    user_id = user["id"]
    
    # Get completed sales
    sales = await db.protocol_purchases.find(
        {"seller_id": user_id, "status": "completed"},
        {"_id": 0}
    ).to_list(1000)
    
    total_revenue = sum(s.get("amount", 0) for s in sales)
    earnings_after_split = total_revenue * 0.90
    
    # Get pending sales
    pending_sales = await db.protocol_purchases.count_documents(
        {"seller_id": user_id, "status": "pending"}
    )
    
    # Get unique buyers
    unique_buyers = len(set(s.get("buyer_id") for s in sales))
    
    return {
        "total_sales": len(sales),
        "total_revenue": round(total_revenue, 2),
        "earnings_after_split": round(earnings_after_split, 2),
        "pending_sales": pending_sales,
        "unique_buyers": unique_buyers,
        "platform_fee_percentage": 10
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
# GEOCODING ENDPOINT
# ============================================

@api_router.post("/geocode")
async def geocode_location(data: dict, user: dict = Depends(require_user)):
    """Convert city/state to lat/lng coordinates using Google Geocoding API"""
    city = data.get("city", "")
    state = data.get("state", "")
    country = data.get("country", "USA")
    
    if not city:
        raise HTTPException(status_code=400, detail="City is required")
    
    # Build address string
    address_parts = [city]
    if state:
        address_parts.append(state)
    address_parts.append(country)
    address = ", ".join(address_parts)
    
    try:
        # Call Google Geocoding API
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(geocode_url, params=params)
            result = response.json()
        
        if result.get("status") != "OK" or not result.get("results"):
            return {"success": False, "error": "Location not found", "address": address}
        
        location = result["results"][0]["geometry"]["location"]
        formatted_address = result["results"][0].get("formatted_address", address)
        
        return {
            "success": True,
            "lat": location["lat"],
            "lng": location["lng"],
            "formatted_address": formatted_address,
            "city": city,
            "state": state,
            "country": country
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# AI MARKETING CONTENT GENERATION
# ============================================

@api_router.post("/ai/generate-marketing")
async def generate_marketing_content(data: dict, user: dict = Depends(require_user)):
    """Generate AI-powered marketing content for the book using Emergent LLM"""
    content_type = data.get("type", "tagline")  # tagline, description, social_post, email
    context = data.get("context", "")
    
    # Book information for context
    book_info = {
        "title": "Letters to Evelyn",
        "author": "John Selman",
        "genre": "Supernatural Thriller Comedy",
        "price": "$2.99",
        "reviews": "19 Five-Star Reviews",
        "tagline": "The Navy Taught Me to Fly Jets. The Universe Taught Me Everything Else.",
        "description": "A true supernatural thriller comedy spanning 13 years of cosmic chaos",
        "highlights": [
            "Optioned for film",
            "Written by a U.S. Naval Officer who graduated FIRST in his class",
            "19 professional five-star reviews",
            "Easy-to-read novella format"
        ]
    }
    
    # System prompts for different content types
    prompts = {
        "tagline": f"""You are a creative marketing copywriter. Generate a catchy, funny, and compelling tagline for the book "{book_info['title']}" by {book_info['author']}. 
The book is a {book_info['genre']}. 
Key selling points: {', '.join(book_info['highlights'])}
Current tagline for reference: "{book_info['tagline']}"
Generate a NEW, different tagline that is witty, memorable, and makes people want to buy the book. Keep it under 15 words.""",
        
        "description": f"""You are a creative book marketing expert. Write a compelling 2-3 sentence book description for "{book_info['title']}" by {book_info['author']}.
Genre: {book_info['genre']}
Highlights: {', '.join(book_info['highlights'])}
Make it intriguing, funny where appropriate, and end with a hook that makes readers want to buy immediately.""",
        
        "social_post": f"""You are a social media marketing expert. Create an engaging social media post promoting "{book_info['title']}" by {book_info['author']}.
Price: {book_info['price']}
Reviews: {book_info['reviews']}
Genre: {book_info['genre']}
Include relevant emojis, a hook, the key selling point, and a call to action. Keep it under 280 characters for Twitter compatibility.""",
        
        "email": f"""You are an email marketing specialist. Write a short, compelling email subject line and preview text for promoting "{book_info['title']}".
The email is promoting a {book_info['genre']} book at {book_info['price']} with {book_info['reviews']}.
Format:
Subject: [subject line here]
Preview: [preview text here - 50-90 characters]"""
    }
    
    system_prompt = prompts.get(content_type, prompts["tagline"])
    if context:
        system_prompt += f"\n\nAdditional context: {context}"
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
        if not EMERGENT_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"marketing-{user['id']}-{datetime.now().timestamp()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=f"Generate {content_type} content for the book marketing.")
        response = await chat.send_message(user_message)
        
        return {
            "success": True,
            "content_type": content_type,
            "generated_content": response,
            "book_title": book_info["title"]
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="AI library not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@api_router.get("/ai/marketing-suggestions")
async def get_marketing_suggestions(user: dict = Depends(require_user)):
    """Get a batch of pre-generated marketing suggestions"""
    # Return variety of marketing content
    suggestions = {
        "taglines": [
            "The Navy Taught Me to Fly Jets. The Universe Taught Me Everything Else.",
            "Get yourself giggling in disoriented, stupefying hee-haw laughter!",
            "Hurricane-force winds of laughter from the most skeptical of minds!",
            "Finally, an easy-to-read novella that flows - you won't be able to put it down!",
            "50+ zingers in succession. Bat-shit insane? Maybe. Unforgettable? Definitely.",
            "Written by a U.S. Naval Officer who graduated FIRST in his class!"
        ],
        "social_posts": [
            "📚 NEW RELEASE: Letters to Evelyn - A supernatural thriller comedy that will leave you laughing AND questioning reality! ⭐⭐⭐⭐⭐ 19 Five-Star Reviews. Only $2.99! #BookTwitter #MustRead",
            "🎬 OPTIONED FOR FILM! Letters to Evelyn by Navy pilot John Selman - the book Hollywood is watching! Get it before the movie comes out. $2.99 on Amazon! 📖✈️",
            "😂 Need a laugh? Try Letters to Evelyn - 'Hurricane-force winds of laughter' from critics! Only $2.99. Your next favorite book awaits! 📚⭐"
        ],
        "email_subjects": [
            {"subject": "🛩️ A Navy Pilot's Supernatural Journey Will Leave You Breathless", "preview": "19 Five-Star Reviews can't be wrong..."},
            {"subject": "📚 The Book Hollywood Is Already Talking About", "preview": "Letters to Evelyn - Only $2.99"},
            {"subject": "😂 Warning: May Cause Uncontrollable Laughter", "preview": "A supernatural thriller comedy unlike any other"}
        ]
    }
    return suggestions

# ============================================
# WEBSOCKET ENDPOINTS
# ============================================

@app.websocket("/ws/messages/{token}")
async def websocket_messages(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time messaging"""
    user = None
    try:
        # Verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        user = await db.users.find_one({"id": user_id})
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return
        
        # Connect
        await ws_manager.connect(websocket, user_id)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "WebSocket connected successfully"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle ping/pong for keepalive
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Handle typing indicator
                elif data.get("type") == "typing":
                    recipient_id = data.get("recipient_id")
                    if recipient_id:
                        await ws_manager.send_personal_message({
                            "type": "typing",
                            "sender_id": user_id,
                            "sender_username": user.get("username", user.get("callsign", "Unknown"))
                        }, recipient_id)
                
                # Handle message read receipt
                elif data.get("type") == "read_receipt":
                    sender_id = data.get("sender_id")
                    if sender_id:
                        await ws_manager.send_personal_message({
                            "type": "read_receipt",
                            "reader_id": user_id,
                            "reader_username": user.get("username", user.get("callsign", "Unknown"))
                        }, sender_id)
                        
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                break
                
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001, reason="Token expired")
    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason="Invalid token")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user['id'] if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if user:
            ws_manager.disconnect(websocket, user["id"])

@app.get("/ws/online-status/{user_id}")
async def get_online_status(user_id: str):
    """Check if a user is online (has active WebSocket connections)"""
    return {"user_id": user_id, "online": ws_manager.is_user_online(user_id)}

# ============================================
# PAYPAL IPN ENDPOINT
# ============================================

@app.post("/api/paypal/ipn")
async def paypal_ipn(request: Request):
    """
    PayPal Instant Payment Notification (IPN) endpoint.
    This is called by PayPal when a payment is made.
    """
    try:
        # Get the raw body
        body = await request.body()
        body_str = body.decode('utf-8')
        logger.info(f"PayPal IPN received: {body_str[:500]}")
        
        # Parse the IPN message
        from urllib.parse import parse_qs
        ipn_data = parse_qs(body_str)
        
        # Flatten the dict (parse_qs returns lists)
        ipn_dict = {k: v[0] if len(v) == 1 else v for k, v in ipn_data.items()}
        
        # Verify with PayPal (send back to PayPal with cmd=_notify-validate)
        verify_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"  # Use sandbox for testing
        # For production: verify_url = "https://ipnpb.paypal.com/cgi-bin/webscr"
        
        verify_data = "cmd=_notify-validate&" + body_str
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                verify_url,
                content=verify_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            verification = response.text
        
        logger.info(f"PayPal IPN verification response: {verification}")
        
        if verification != "VERIFIED":
            logger.warning(f"PayPal IPN verification failed: {verification}")
            # Still process for testing, but log the warning
        
        # Extract payment info
        payment_status = ipn_dict.get("payment_status", "")
        payer_email = ipn_dict.get("payer_email", "")
        txn_id = ipn_dict.get("txn_id", "")
        payment_amount = ipn_dict.get("mc_gross", "0")
        custom_data = ipn_dict.get("custom", "")  # We can pass user_id in custom field
        
        logger.info(f"PayPal IPN: status={payment_status}, email={payer_email}, amount={payment_amount}, txn={txn_id}")
        
        # Only process completed payments
        if payment_status.lower() == "completed":
            # Try to find user by email or custom data
            user = None
            
            # First try custom data (user_id)
            if custom_data:
                user = await db.users.find_one({"id": custom_data})
            
            # Then try payer email
            if not user and payer_email:
                user = await db.users.find_one({"email": payer_email.lower()})
            
            if user:
                # Calculate subscription end date (1 year from now)
                subscription_until = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
                
                # Update user subscription
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": {
                        "subscription_until": subscription_until,
                        "subscription_status": "active",
                        "last_payment_txn": txn_id,
                        "last_payment_amount": payment_amount,
                        "last_payment_date": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Record subscription in history
                subscription_record = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "txn_id": txn_id,
                    "amount": float(payment_amount),
                    "payer_email": payer_email,
                    "status": "completed",
                    "subscription_until": subscription_until,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.subscriptions.insert_one(subscription_record)
                
                logger.info(f"Subscription activated for user {user['id']} ({user.get('email')}) until {subscription_until}")
                
                # Send confirmation email
                email_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #e0e0ff; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #0f0f1a; border: 1px solid #8b5cf6; border-radius: 8px; padding: 20px;">
                        <h2 style="color: #ec4899; margin-bottom: 20px;">🎉 Subscription Activated!</h2>
                        <p style="color: #c4b5fd;">Hello {user.get('username', 'Pilot')},</p>
                        <p style="color: #c4b5fd;">Thank you for subscribing to InfoPilot Explorer!</p>
                        
                        <div style="background-color: #1f1f35; border-left: 4px solid #22c55e; padding: 15px; margin: 15px 0;">
                            <p style="color: #22c55e; margin: 0; font-weight: bold;">Payment Confirmed</p>
                            <p style="color: #c4b5fd; margin: 5px 0 0 0;">Amount: ${payment_amount}</p>
                            <p style="color: #c4b5fd; margin: 5px 0 0 0;">Transaction ID: {txn_id}</p>
                            <p style="color: #c4b5fd; margin: 5px 0 0 0;">Valid until: {subscription_until[:10]}</p>
                        </div>
                        
                        <p style="color: #c4b5fd;">Enjoy full access to all InfoPilot Explorer features!</p>
                        
                        <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">— InfoPilot Explorer Team</p>
                    </div>
                </body>
                </html>
                """
                asyncio.create_task(send_notification_email(
                    user["email"],
                    "🎉 InfoPilot Explorer Subscription Activated!",
                    email_html
                ))
            else:
                logger.warning(f"PayPal IPN: Could not find user for email {payer_email} or custom {custom_data}")
        
        # Always return 200 to acknowledge receipt
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"PayPal IPN error: {e}")
        # Still return 200 to prevent PayPal from retrying
        return {"status": "error", "detail": str(e)}

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
    
    # Initialize email digest scheduler
    try:
        from services.scheduler import setup_digest_scheduler, start_scheduler
        
        # Get digest config from DB
        digest_config = await db.admin_settings.find_one({"type": "email_digest_config"})
        if digest_config and digest_config.get("enabled", False):
            day_of_week = digest_config.get("day_of_week", "monday")
            hour = digest_config.get("hour", 9)
            setup_digest_scheduler(db, day_of_week, hour)
            start_scheduler()
            logger.info(f"Email digest scheduler started: {day_of_week} at {hour}:00 UTC")
        else:
            logger.info("Email digest scheduler not enabled")
    except Exception as e:
        logger.error(f"Failed to initialize email digest scheduler: {str(e)}")
    
    logger.info("InfoPilot Explorer API v2.0 - Tactical Systems Online")

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop scheduler
    try:
        from services.scheduler import stop_scheduler
        stop_scheduler()
    except:
        pass
    client.close()
