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

# Stripe Integration
try:
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

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
polls_router = APIRouter(prefix="/polls", tags=["Polls"])
reports_router = APIRouter(prefix="/reports", tags=["Personal Reports"])
quotes_router = APIRouter(prefix="/quotes", tags=["Quote Gallery"])
themes_router = APIRouter(prefix="/themes", tags=["Themes"])
analytics_router = APIRouter(prefix="/protocol-analytics", tags=["Protocol Analytics"])
promotions_router = APIRouter(prefix="/promotions", tags=["Promotions"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])
legal_router = APIRouter(prefix="/legal", tags=["Legal"])
templates_router = APIRouter(prefix="/templates", tags=["Protocol Templates"])
heatmap_router = APIRouter(prefix="/heatmaps", tags=["Heatmaps"])
collab_router = APIRouter(prefix="/collab", tags=["Collaborative Sessions"])
versioning_router = APIRouter(prefix="/versioning", tags=["Protocol Versioning"])
branding_router = APIRouter(prefix="/branding", tags=["App Branding"])

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
    """Extract location information from text with enhanced geolocation support"""
    
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
    
    # State abbreviations
    STATE_ABBREV = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
    }
    
    COUNTRIES = [
        "United States", "USA", "UK", "United Kingdom", "Canada", "Australia",
        "Germany", "France", "Italy", "Spain", "Japan", "China", "India",
        "Brazil", "Mexico", "Russia", "South Korea", "Netherlands", "Sweden",
        "Switzerland", "Nicaragua", "Costa Rica", "Panama", "Ireland", "Scotland",
        "Norway", "Denmark", "Finland", "Belgium", "Austria", "Portugal",
        "Greece", "Poland", "Czech Republic", "Hungary", "Romania", "Ukraine",
        "Turkey", "Israel", "Egypt", "South Africa", "Argentina", "Chile",
        "Colombia", "Peru", "Venezuela", "Cuba", "Puerto Rico", "Philippines",
        "Thailand", "Vietnam", "Indonesia", "Malaysia", "Singapore", "New Zealand",
        "Honduras", "Guatemala", "El Salvador", "Belize", "Ecuador", "Bolivia",
        "Paraguay", "Uruguay", "Jamaica", "Haiti", "Dominican Republic",
        "Kenya", "Nigeria", "Ghana", "Tanzania", "Ethiopia", "Morocco", "Algeria",
        "Tunisia", "Libya", "Sudan", "Congo", "Cameroon", "Zimbabwe", "Zambia"
    ]
    
    # Major US cities
    MAJOR_US_CITIES = [
        "New York City", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
        "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington",
        "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City",
        "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore",
        "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Mesa",
        "Sacramento", "Atlanta", "Kansas City", "Colorado Springs", "Miami",
        "Raleigh", "Omaha", "Long Beach", "Virginia Beach", "Oakland",
        "Minneapolis", "Tulsa", "Tampa", "Arlington", "New Orleans",
        "Brunswick", "Bath", "Bangor", "Augusta", "Lewiston",  # Maine cities
        "Honolulu", "Anchorage", "Salt Lake City", "Boise", "Richmond",
        "Newark", "Jersey City", "Trenton", "Camden", "Hartford", "New Haven",
        "Providence", "Worcester", "Springfield", "Buffalo", "Rochester",
        "Syracuse", "Albany", "Yonkers", "Pittsburgh", "Erie", "Scranton"
    ]
    
    # International cities by country
    INTERNATIONAL_CITIES = {
        "Nicaragua": ["Managua", "León", "Granada", "Masaya", "Chinandega", "Matagalpa", 
                      "Estelí", "Tipitapa", "Virgin Bay", "San Juan del Sur", "Bluefields",
                      "Puerto Cabezas", "Jinotega", "Rivas", "Corinto"],
        "Costa Rica": ["San José", "Limón", "Alajuela", "Heredia", "Cartago", "Puntarenas"],
        "Panama": ["Panama City", "Colón", "David", "Santiago", "Chitré"],
        "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Tijuana", "Cancún", "Puebla",
                   "León", "Juárez", "Mérida", "Acapulco", "Veracruz", "Oaxaca"],
        "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton",
                   "Winnipeg", "Quebec City", "Halifax", "Victoria", "Saskatoon"],
        "UK": ["London", "Birmingham", "Manchester", "Glasgow", "Liverpool", "Edinburgh",
               "Bristol", "Leeds", "Sheffield", "Newcastle", "Belfast", "Cardiff"],
        "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne", "Stuttgart",
                    "Düsseldorf", "Leipzig", "Dresden", "Hanover"],
        "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Bordeaux"],
        "Italy": ["Rome", "Milan", "Naples", "Turin", "Florence", "Venice", "Bologna"],
        "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao", "Málaga"],
        "Japan": ["Tokyo", "Osaka", "Kyoto", "Yokohama", "Nagoya", "Sapporo", "Fukuoka"],
        "China": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hong Kong", "Chengdu"],
        "India": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata"],
        "Brazil": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza"],
        "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra"],
        "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata"],
        "South Africa": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth"]
    }
    
    # Regional descriptors
    REGIONAL_PREFIXES = ["Northern", "Southern", "Eastern", "Western", "Central",
                         "North", "South", "East", "West", "Upper", "Lower",
                         "Greater", "Metro", "Downtown", "Uptown", "Suburban"]
    
    @staticmethod
    def extract_locations(text: str) -> List[Dict]:
        """Extract all locations found in text with enhanced detection for city+state and city+country"""
        locations = []
        text_lower = text.lower()
        
        # PATTERN 1: City, Country format (e.g., "Virgin Bay, Nicaragua")
        for country, cities in LocationExtractor.INTERNATIONAL_CITIES.items():
            for city in cities:
                # Pattern: "City, Country" or "City in Country" or "City (Country)"
                patterns = [
                    rf'\b{re.escape(city)}\s*,\s*{re.escape(country)}\b',
                    rf'\b{re.escape(city)}\s+in\s+{re.escape(country)}\b',
                    rf'\b{re.escape(city)}\s*\({re.escape(country)}\)',
                    rf'\b{re.escape(city)}\b.*\b{re.escape(country)}\b'
                ]
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        locations.append({
                            "type": "city_country",
                            "city": city,
                            "country": country
                        })
                        break
        
        # PATTERN 2: City, State format (e.g., "Portland, Maine")
        for city in LocationExtractor.MAJOR_US_CITIES:
            for state in LocationExtractor.US_STATES:
                patterns = [
                    rf'\b{re.escape(city)}\s*,\s*{re.escape(state)}\b',
                    rf'\b{re.escape(city)}\s+in\s+{re.escape(state)}\b',
                    rf'\b{re.escape(city)}\s*\({re.escape(state)}\)'
                ]
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        locations.append({
                            "type": "city_state",
                            "city": city,
                            "state": state,
                            "country": "United States"
                        })
                        break
        
        # PATTERN 3: City, State Abbreviation (e.g., "Portland, ME")
        for city in LocationExtractor.MAJOR_US_CITIES:
            for abbrev, state in LocationExtractor.STATE_ABBREV.items():
                pattern = rf'\b{re.escape(city)}\s*,\s*{abbrev}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    locations.append({
                        "type": "city_state",
                        "city": city,
                        "state": state,
                        "country": "United States"
                    })
        
        # PATTERN 4: International cities mentioned alone (check if country is also in text)
        for country, cities in LocationExtractor.INTERNATIONAL_CITIES.items():
            country_lower = country.lower()
            if country_lower in text_lower:
                for city in cities:
                    if city.lower() in text_lower:
                        # Check we haven't already added this city+country
                        exists = any(
                            loc.get("city") == city and loc.get("country") == country
                            for loc in locations
                        )
                        if not exists:
                            locations.append({
                                "type": "city_country",
                                "city": city,
                                "country": country
                            })
        
        # PATTERN 4B: International cities mentioned WITHOUT country in text
        # This catches cases like "Virgin Bay" appearing in an article about Nicaragua
        # where the country may not be explicitly mentioned near the city name
        for country, cities in LocationExtractor.INTERNATIONAL_CITIES.items():
            for city in cities:
                # Use word boundary to avoid partial matches
                city_pattern = rf'\b{re.escape(city)}\b'
                if re.search(city_pattern, text, re.IGNORECASE):
                    # Check we haven't already added this city
                    exists = any(
                        loc.get("city") == city and loc.get("country") == country
                        for loc in locations
                    )
                    if not exists:
                        locations.append({
                            "type": "city_country",
                            "city": city,
                            "country": country
                        })
        
        # PATTERN 5: US States alone
        for state in LocationExtractor.US_STATES:
            if state.lower() in text_lower:
                exists = any(loc.get("state") == state for loc in locations)
                if not exists:
                    locations.append({
                        "type": "state",
                        "state": state,
                        "country": "United States"
                    })
        
        # PATTERN 6: State abbreviations with context
        for abbrev, state in LocationExtractor.STATE_ABBREV.items():
            patterns = [
                rf',\s*{abbrev}\b',
                rf'\b{abbrev},',
                rf'\b{abbrev}\s+\d{{5}}',
                rf'\({abbrev}\)'
            ]
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    exists = any(loc.get("state") == state for loc in locations)
                    if not exists:
                        locations.append({
                            "type": "state",
                            "state": state,
                            "country": "United States"
                        })
                    break
        
        # PATTERN 7: Countries alone
        for country in LocationExtractor.COUNTRIES:
            if country.lower() in text_lower:
                exists = any(loc.get("country") == country and loc.get("type") == "country" for loc in locations)
                if not exists:
                    locations.append({
                        "type": "country",
                        "country": country
                    })
        
        # PATTERN 8: US cities mentioned with state context
        for city in LocationExtractor.MAJOR_US_CITIES:
            if city.lower() in text_lower:
                exists = any(loc.get("city") == city for loc in locations)
                if not exists:
                    locations.append({
                        "type": "city",
                        "city": city,
                        "country": "United States"
                    })
        
        # PATTERN 9: Regional prefixes (Northern Virginia, Greater Boston)
        for prefix in LocationExtractor.REGIONAL_PREFIXES:
            pattern = rf'\b{prefix}\s+(\w+(?:\s+\w+)?)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match_title = match.title()
                if match_title in LocationExtractor.US_STATES:
                    locations.append({
                        "type": "region",
                        "region": f"{prefix} {match_title}",
                        "state": match_title,
                        "country": "United States"
                    })
                elif match_title in LocationExtractor.MAJOR_US_CITIES:
                    locations.append({
                        "type": "metro_area",
                        "region": f"{prefix} {match_title}",
                        "city": match_title,
                        "country": "United States"
                    })
        
        # PATTERN 10: Street addresses (multiple per article)
        street_types = r'(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Circle|Cir|Highway|Hwy|Route|Rt|Pike|Parkway|Pkwy)'
        address_pattern = rf'\b(\d+)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+({street_types})\b'
        address_matches = re.findall(address_pattern, text)
        for number, street_name, street_type in address_matches:
            locations.append({
                "type": "street_address",
                "address": f"{number} {street_name} {street_type.title()}",
                "country": "United States"
            })
        
        # PATTERN 11: Full addresses with city, state, ZIP
        full_address_pattern = rf'(\d+)\s+([A-Za-z\s]+?)\s+({street_types})\s*,?\s*([A-Za-z\s]+?)\s*,?\s*([A-Z]{{2}})\s*(\d{{5}}(?:-\d{{4}})?)?'
        full_matches = re.findall(full_address_pattern, text)
        for match in full_matches:
            number, street, st_type, city, state_abbrev, zipcode = match
            state = LocationExtractor.STATE_ABBREV.get(state_abbrev, state_abbrev)
            locations.append({
                "type": "full_address",
                "address": f"{number} {street.strip()} {st_type}",
                "city": city.strip(),
                "state": state,
                "zip": zipcode if zipcode else None,
                "country": "United States"
            })
        
        # PATTERN 12: ZIP codes
        zip_pattern = r'\b(\d{5})(?:-\d{4})?\b'
        zip_matches = re.findall(zip_pattern, text)
        for zip_code in zip_matches:
            zip_regions = {
                '0': 'Northeast', '1': 'Northeast', '2': 'Mid-Atlantic',
                '3': 'Southeast', '4': 'Midwest', '5': 'Midwest',
                '6': 'Central', '7': 'South', '8': 'West', '9': 'West'
            }
            if zip_code[0] in zip_regions:
                locations.append({
                    "type": "zip_code",
                    "zip": zip_code,
                    "region": zip_regions[zip_code[0]],
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
    fetch_full_content = data.get("fetch_full_content", False)
    
    for result in search_results:
        url = result.get("href", "")
        title = result.get("title", "")
        snippet = result.get("body", "")
        full_content = ""
        
        # Optionally fetch full page content for better location extraction
        if fetch_full_content:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code == 200:
                        # Extract text from HTML
                        html_content = resp.text
                        # Remove script and style tags
                        import re as re_mod
                        html_content = re_mod.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re_mod.DOTALL | re_mod.IGNORECASE)
                        html_content = re_mod.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re_mod.DOTALL | re_mod.IGNORECASE)
                        # Remove HTML tags
                        html_content = re_mod.sub(r'<[^>]+>', ' ', html_content)
                        # Clean up whitespace
                        full_content = ' '.join(html_content.split())[:10000]  # Limit to 10K chars
            except Exception as e:
                logger.debug(f"Could not fetch full content for {url}: {e}")
        
        # Use full content if available, otherwise use title + snippet
        combined_text = f"{title} {snippet} {full_content}" if full_content else f"{title} {snippet}"
        
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
            
            # Extract locations - now includes full content if fetched
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
                "content_preview": full_content[:500] if full_content else None,
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
    new_category.pop("_id", None)
    
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

@marketplace_router.get("/headlines")
async def get_marketplace_headlines():
    """Get marketplace headlines/news"""
    # Get latest headlines from database or generate defaults
    headlines = await db.marketplace_headlines.find({}, {"_id": 0})\
        .sort("created_at", -1)\
        .limit(5)\
        .to_list(5)
    
    if not headlines:
        # Default headlines
        headlines = [
            {"title": "New protocols added daily!", "category": "Platform News"},
            {"title": "Top seller of the week announced", "category": "Community"},
            {"title": "AI-powered search matching now available", "category": "Features"},
            {"title": "Protocol templates feature launched", "category": "Updates"},
            {"title": "Share your protocols and earn 90% revenue", "category": "Monetization"}
        ]
    
    return {"headlines": headlines}

@marketplace_router.get("/recommended")
async def get_recommended_protocols(user: User = Depends(require_auth)):
    """Get recommended protocols based on user activity"""
    # Get user's recent searches to understand interests
    recent_results = await db.search_results.find(
        {"user_id": user.user_id},
        {"_id": 0, "document_type": 1, "category_id": 1}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    # Get categories user has interacted with
    user_categories = set()
    for r in recent_results:
        if r.get("category_id"):
            user_categories.add(r["category_id"])
    
    # Find popular protocols user hasn't used yet
    query = {"is_public": True}
    if user_categories:
        query["category_id"] = {"$nin": list(user_categories)}
    
    recommended = await db.categories.find(query, {"_id": 0})\
        .sort("sales_count", -1)\
        .limit(6)\
        .to_list(6)
    
    # If no recommendations, get top protocols
    if not recommended:
        recommended = await db.categories.find(
            {"is_public": True},
            {"_id": 0}
        ).sort("sales_count", -1).limit(6).to_list(6)
    
    return {"protocols": recommended}

@stats_router.get("/overview")
async def get_stats_overview(user: User = Depends(require_auth)):
    """Get comprehensive statistics overview with 14+ aspects"""
    user_id = user.user_id
    
    # 1. Document Type Distribution
    doc_type_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
    ]).to_list(20)
    
    # 2. Results by Country
    country_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$unwind": "$locations"},
        {"$match": {"locations.country": {"$exists": True}}},
        {"$group": {"_id": "$locations.country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # 3. Results by State
    state_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$unwind": "$locations"},
        {"$match": {"locations.state": {"$exists": True}}},
        {"$group": {"_id": "$locations.state", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # 4. Results by City
    city_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$unwind": "$locations"},
        {"$match": {"locations.city": {"$exists": True}}},
        {"$group": {"_id": "$locations.city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # 5. Top Domains
    domain_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$root_domain", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # 6. Results by Year (publication/reference year)
    year_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "year": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(50)
    
    # 7. Age of Subjects (estimated from year mentions in content)
    current_year = datetime.now().year
    age_brackets = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "year": {"$exists": True, "$ne": None}}},
        {"$addFields": {
            "age": {"$subtract": [current_year, "$year"]}
        }},
        {"$bucket": {
            "groupBy": "$age",
            "boundaries": [0, 5, 10, 20, 50, 100, 200, 500],
            "default": "500+",
            "output": {"count": {"$sum": 1}}
        }}
    ]).to_list(10)
    
    # 8. Results by Category
    category_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$category_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 15}
    ]).to_list(15)
    
    # Enrich with category names
    for cat_stat in category_stats:
        if cat_stat["_id"]:
            cat = await db.categories.find_one({"category_id": cat_stat["_id"]}, {"_id": 0, "name": 1})
            cat_stat["name"] = cat["name"] if cat else "Unknown"
    
    # 9. Content Source Types (webpage, news, academic, etc.)
    source_type_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {
            "source_type": {
                "$switch": {
                    "branches": [
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "news|cnn|bbc|nytimes|washingtonpost|reuters"}}, "then": "News"},
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "edu|academic|scholar|jstor|pubmed"}}, "then": "Academic"},
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "gov|government|state"}}, "then": "Government"},
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "wikipedia|wiki"}}, "then": "Wiki"},
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "blog|medium|wordpress|blogger"}}, "then": "Blog"},
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "forum|reddit|quora|stackexchange"}}, "then": "Forum"},
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "youtube|video|vimeo"}}, "then": "Video"},
                        {"case": {"$regexMatch": {"input": {"$ifNull": ["$root_domain", ""]}, "regex": "pdf"}}, "then": "PDF/Document"}
                    ],
                    "default": "Webpage"
                }
            }
        }},
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(15)
    
    # 10. Results by Day of Week (when collated)
    day_of_week_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {
            "day_of_week": {"$dayOfWeek": {"$dateFromString": {"dateString": "$created_at", "onError": None}}}
        }},
        {"$match": {"day_of_week": {"$ne": None}}},
        {"$group": {"_id": "$day_of_week", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(7)
    
    # Map day numbers to names
    day_names = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 7: "Saturday"}
    for d in day_of_week_stats:
        d["name"] = day_names.get(d["_id"], "Unknown")
    
    # 11. Results by Month
    month_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {
            "month": {"$month": {"$dateFromString": {"dateString": "$created_at", "onError": None}}}
        }},
        {"$match": {"month": {"$ne": None}}},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(12)
    
    month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
    for m in month_stats:
        m["name"] = month_names.get(m["_id"], "Unknown")
    
    # 12. Top Level Domain Distribution (.com, .org, .edu, etc.)
    tld_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "root_domain": {"$exists": True}}},
        {"$addFields": {
            "tld": {"$arrayElemAt": [{"$split": ["$root_domain", "."]}, -1]}
        }},
        {"$group": {"_id": "$tld", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 15}
    ]).to_list(15)
    
    # 13. Region Distribution (US regions)
    us_regions = {
        "Northeast": ["Maine", "New Hampshire", "Vermont", "Massachusetts", "Rhode Island", "Connecticut", "New York", "New Jersey", "Pennsylvania"],
        "Southeast": ["Delaware", "Maryland", "Virginia", "West Virginia", "North Carolina", "South Carolina", "Georgia", "Florida", "Kentucky", "Tennessee", "Alabama", "Mississippi", "Arkansas", "Louisiana"],
        "Midwest": ["Ohio", "Michigan", "Indiana", "Illinois", "Wisconsin", "Minnesota", "Iowa", "Missouri", "North Dakota", "South Dakota", "Nebraska", "Kansas"],
        "Southwest": ["Texas", "Oklahoma", "New Mexico", "Arizona"],
        "West": ["Colorado", "Wyoming", "Montana", "Idaho", "Utah", "Nevada", "California", "Oregon", "Washington", "Alaska", "Hawaii"]
    }
    
    region_counts = {"Northeast": 0, "Southeast": 0, "Midwest": 0, "Southwest": 0, "West": 0, "International": 0}
    for state_item in state_stats:
        state_name = state_item["_id"]
        found_region = False
        for region, states in us_regions.items():
            if state_name in states:
                region_counts[region] += state_item["count"]
                found_region = True
                break
        if not found_region:
            region_counts["International"] += state_item["count"]
    
    region_stats = [{"_id": k, "count": v} for k, v in region_counts.items() if v > 0]
    
    # 14. Content Length Distribution (short, medium, long snippets)
    length_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {
            "snippet_length": {"$strLenCP": {"$ifNull": ["$snippet", ""]}}
        }},
        {"$bucket": {
            "groupBy": "$snippet_length",
            "boundaries": [0, 100, 300, 500, 1000],
            "default": "1000+",
            "output": {"count": {"$sum": 1}}
        }}
    ]).to_list(10)
    
    # 15. Protocol Match Quality (if tracked)
    match_quality_stats = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "match_score": {"$exists": True}}},
        {"$bucket": {
            "groupBy": "$match_score",
            "boundaries": [0, 0.25, 0.5, 0.75, 1.0],
            "default": "Unknown",
            "output": {"count": {"$sum": 1}}
        }}
    ]).to_list(10)
    
    # 16. Reaction Distribution
    reaction_stats = await db.reactions.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$reaction_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(10)
    
    total_results = await db.search_results.count_documents({"user_id": user_id})
    total_categories = await db.categories.count_documents({"user_id": user_id})
    total_locations = len(country_stats) + len(state_stats) + len(city_stats)
    
    return {
        "total_results": total_results,
        "total_categories": total_categories,
        "total_locations": total_locations,
        "by_document_type": doc_type_stats,
        "by_country": country_stats,
        "by_state": state_stats,
        "by_city": city_stats,
        "by_domain": domain_stats,
        "by_year": year_stats,
        "by_age_bracket": age_brackets,
        "by_category": category_stats,
        "by_source_type": source_type_stats,
        "by_day_of_week": day_of_week_stats,
        "by_month": month_stats,
        "by_tld": tld_stats,
        "by_region": region_stats,
        "by_content_length": length_stats,
        "by_match_quality": match_quality_stats,
        "by_reaction": reaction_stats
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

@groups_router.get("/search")
async def search_groups(
    name: Optional[str] = None,
    content: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Search groups by name and/or content"""
    query = {}
    
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    
    groups = await db.groups.find(query, {"_id": 0}).to_list(100)
    
    # If content search is specified, filter by posts content
    if content:
        filtered_groups = []
        for group in groups:
            # Check description
            if group.get("description") and content.lower() in group["description"].lower():
                filtered_groups.append(group)
                continue
            
            # Check posts
            posts = await db.group_posts.find(
                {"group_id": group["group_id"], "content": {"$regex": content, "$options": "i"}},
                {"_id": 0}
            ).limit(1).to_list(1)
            
            if posts:
                filtered_groups.append(group)
        
        return {"groups": filtered_groups}
    
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
    group.pop("_id", None)
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
    post.pop("_id", None)
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
    page.pop("_id", None)
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
        conversation.pop("_id", None)
    
    # Create message
    message = {
        "message_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conversation_id": conversation["conversation_id"],
        "sender_id": user.user_id,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message)
    message.pop("_id", None)
    
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
    room.pop("_id", None)
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
        # Remove _id from eggs for JSON serialization
        for egg in default_eggs:
            egg.pop("_id", None)
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
        "version": "2.0.0",
        "description": "World Wide Web Information Exchange Social Network"
    }

@api_router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ============= POLLS ROUTES =============

@polls_router.get("")
async def get_polls(
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """Get polls"""
    query = {}
    if target_type:
        query["target_type"] = target_type
    if target_id:
        query["target_id"] = target_id
    
    polls = await db.polls.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"polls": polls}

@polls_router.post("")
async def create_poll(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a poll on USP, Group, or Page"""
    data = await request.json()
    
    poll = {
        "poll_id": f"poll_{uuid.uuid4().hex[:12]}",
        "creator_id": user.user_id,
        "question": data.get("question"),
        "options": [{"text": opt, "votes": 0} for opt in data.get("options", [])],
        "target_type": data.get("target_type", "usp"),  # usp, group, page
        "target_id": data.get("target_id"),
        "voters": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": data.get("expires_at")
    }
    
    await db.polls.insert_one(poll)
    poll.pop("_id", None)
    return poll

@polls_router.post("/{poll_id}/vote")
async def vote_on_poll(
    poll_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Vote on a poll"""
    data = await request.json()
    option_index = data.get("option_index")
    
    # Check if already voted
    poll = await db.polls.find_one({"poll_id": poll_id}, {"_id": 0})
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    if user.user_id in poll.get("voters", []):
        raise HTTPException(status_code=400, detail="Already voted")
    
    # Record vote
    await db.polls.update_one(
        {"poll_id": poll_id},
        {
            "$inc": {f"options.{option_index}.votes": 1},
            "$push": {"voters": user.user_id}
        }
    )
    
    return {"message": "Vote recorded"}

# ============= QUOTE GALLERY ROUTES =============

QUOTES_GALLERY = [
    "The search for truth is the noblest pursuit of humanity.",
    "In the vast ocean of information, protocols are your compass.",
    "Every category is a window into someone's curiosity.",
    "The best researchers are those who ask the right questions.",
    "Information is power, but organized information is unstoppable.",
    "Your Ultimate Search Page is your digital fingerprint on the web.",
    "Collate today, discover tomorrow.",
    "Behind every great protocol is a mind seeking knowledge.",
    "The internet is a library - InfoPilot is your librarian.",
    "Share your protocols, multiply your impact.",
    "In a world of noise, filters create clarity.",
    "One person's search result is another's treasure.",
    "Categories don't limit thinking - they organize it.",
    "The best ideas come from connecting unrelated searches.",
    "Research is formalized curiosity. Protocols make it efficient.",
    "Every click teaches the system; every search refines your world.",
    "Your 3D view of the internet starts with a single protocol.",
    "Information wants to be organized. Help it along.",
    "The marketplace of ideas now has a marketplace of protocols.",
    "True discovery happens at the intersection of categories.",
    "Your searches tell a story. Make it a good one.",
    "Protocols are recipes for knowledge.",
    "The more precise your protocol, the more valuable your results.",
    "In the age of information, curation is the new creation.",
    "Every subcategory is a path deeper into understanding.",
    "The best searchers don't just find - they filter.",
    "Your research is your legacy. Organize it well.",
    "Protocols connect minds across time and space.",
    "The internet remembers; your protocols help you remember what matters.",
    "Every great discovery started with a simple search.",
    "Categories are the scaffolding of knowledge.",
    "Share a protocol, change a perspective.",
    "The robot searches, but you decide what's valuable.",
    "Your USP is your intellectual home base.",
    "Great minds search alike - literally, with protocols.",
    "Information without organization is just noise.",
    "The best protocols are born from necessity.",
    "Your categories reflect your priorities.",
    "Search smarter, not harder.",
    "Every protocol tells a story of curiosity.",
    "The marketplace rewards expertise.",
    "Your 3D view is uniquely yours.",
    "Protocols: because bookmarks aren't enough.",
    "The best researchers share their methods.",
    "Information exchange is civilization's backbone.",
    "Your searches shape your worldview.",
    "Categories are mental models made visible.",
    "The robot works while you sleep.",
    "Great protocols stand the test of time.",
    "Your Ultimate Search Page: curated by you, for you."
]

@quotes_router.get("")
async def get_quotes(count: int = 10):
    """Get random quotes from the gallery"""
    import random
    selected = random.sample(QUOTES_GALLERY, min(count, len(QUOTES_GALLERY)))
    return {"quotes": selected}

@quotes_router.get("/all")
async def get_all_quotes():
    """Get all quotes"""
    return {"quotes": QUOTES_GALLERY, "total": len(QUOTES_GALLERY)}

# ============= THEMES ROUTES =============

THEME_PRESETS = {
    "default": {
        "name": "InfoPilot Classic",
        "background": "#FFFFF0",
        "primary": "#007AFF",
        "secondary": "#34C759",
        "accent": "#FFD60A"
    },
    "royal": {
        "name": "Royal",
        "background": "#1A1A2E",
        "primary": "#6B5B95",
        "secondary": "#9B59B6",
        "accent": "#E8D5B7"
    },
    "hot": {
        "name": "Hot",
        "background": "#FFFFFF",
        "primary": "#FF4444",
        "secondary": "#FF6B6B",
        "accent": "#FFB347"
    },
    "ocean": {
        "name": "Ocean",
        "background": "#F0F8FF",
        "primary": "#0077B6",
        "secondary": "#00B4D8",
        "accent": "#90E0EF"
    },
    "forest": {
        "name": "Forest",
        "background": "#F5F5DC",
        "primary": "#228B22",
        "secondary": "#32CD32",
        "accent": "#90EE90"
    },
    "sunset": {
        "name": "Sunset",
        "background": "#FFF8DC",
        "primary": "#FF6347",
        "secondary": "#FF7F50",
        "accent": "#FFD700"
    },
    "ruby": {
        "name": "Ruby",
        "background": "#FFF0F5",
        "primary": "#DC143C",
        "secondary": "#FF69B4",
        "accent": "#FFB6C1"
    },
    "dark": {
        "name": "Dark Mode",
        "background": "#121212",
        "primary": "#BB86FC",
        "secondary": "#03DAC6",
        "accent": "#CF6679"
    }
}

@themes_router.get("/presets")
async def get_theme_presets():
    """Get available theme presets"""
    return {"presets": THEME_PRESETS}

@themes_router.get("/user")
async def get_user_theme(user: User = Depends(require_auth)):
    """Get user's current theme"""
    user_theme = await db.user_themes.find_one(
        {"user_id": user.user_id},
        {"_id": 0}
    )
    return {"theme": user_theme or THEME_PRESETS["default"]}

@themes_router.post("/save")
async def save_user_theme(
    request: Request,
    user: User = Depends(require_auth)
):
    """Save user's custom theme"""
    data = await request.json()
    
    theme_data = {
        "user_id": user.user_id,
        "preset": data.get("preset"),
        "custom": data.get("custom", {}),
        "dark_mode": data.get("dark_mode", False),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_themes.update_one(
        {"user_id": user.user_id},
        {"$set": theme_data},
        upsert=True
    )
    
    return {"message": "Theme saved"}

@themes_router.post("/share")
async def share_theme(
    request: Request,
    user: User = Depends(require_auth)
):
    """Share a custom theme to the gallery"""
    data = await request.json()
    
    shared_theme = {
        "theme_id": f"theme_{uuid.uuid4().hex[:12]}",
        "creator_id": user.user_id,
        "name": data.get("name"),
        "colors": data.get("colors"),
        "downloads": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shared_themes.insert_one(shared_theme)
    shared_theme.pop("_id", None)
    return shared_theme

# ============= PROTOCOL ANALYTICS ROUTES =============

@analytics_router.get("/my-protocols")
async def get_my_protocol_analytics(user: User = Depends(require_auth)):
    """Get analytics for user's protocols"""
    # Get user's categories with stats
    categories = await db.categories.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    
    analytics = []
    for cat in categories:
        # Get views
        views = await db.protocol_views.count_documents({"category_id": cat["category_id"]})
        
        # Get copies
        copies = await db.protocol_copies.count_documents({"original_id": cat["category_id"]})
        
        # Get purchases
        purchases = await db.purchases.count_documents({"category_id": cat["category_id"]})
        
        # Calculate conversion rate
        conversion = (purchases / views * 100) if views > 0 else 0
        
        analytics.append({
            "category_id": cat["category_id"],
            "name": cat["name"],
            "views": views,
            "copies": copies,
            "sales": purchases,
            "revenue": purchases * cat.get("price", 0),
            "conversion_rate": round(conversion, 2)
        })
    
    return {"analytics": analytics}

@analytics_router.post("/track-view")
async def track_protocol_view(
    request: Request,
    user: User = Depends(require_auth)
):
    """Track a protocol view"""
    data = await request.json()
    category_id = data.get("category_id")
    
    await db.protocol_views.insert_one({
        "category_id": category_id,
        "viewer_id": user.user_id,
        "viewed_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "View tracked"}

@analytics_router.get("/admin/marketplace-forecast")
async def get_marketplace_forecast(user: User = Depends(require_admin)):
    """Get marketplace-wide forecast (admin only)"""
    # Get total revenue
    total_purchases = await db.purchases.find({}, {"_id": 0, "price": 1}).to_list(10000)
    total_revenue = sum(p.get("price", 0) for p in total_purchases)
    
    # Get trending categories
    trending = await db.protocol_copies.aggregate([
        {"$group": {"_id": "$original_id", "copies": {"$sum": 1}}},
        {"$sort": {"copies": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get top creators
    top_creators = await db.purchases.aggregate([
        {"$lookup": {
            "from": "categories",
            "localField": "category_id",
            "foreignField": "category_id",
            "as": "category"
        }},
        {"$unwind": "$category"},
        {"$group": {
            "_id": "$category.user_id",
            "total_sales": {"$sum": 1},
            "total_revenue": {"$sum": "$price"}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    return {
        "total_revenue": total_revenue,
        "trending_protocols": trending,
        "top_creators": top_creators
    }

@analytics_router.get("/admin/top-creators")
async def get_top_creators(user: User = Depends(require_admin)):
    """Get top protocol creators"""
    creators = await db.categories.aggregate([
        {"$match": {"is_public": True}},
        {"$group": {
            "_id": "$user_id",
            "protocol_count": {"$sum": 1},
            "total_sales": {"$sum": "$sales_count"}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    # Get user info
    for creator in creators:
        user_info = await db.users.find_one(
            {"user_id": creator["_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        creator["user"] = user_info
    
    return {"creators": creators}

# ============= LAUGH-O-METER ROUTES =============

@easter_eggs_router.post("/laugh-submit")
async def submit_laugh(
    request: Request,
    user: User = Depends(require_auth)
):
    """Submit a laugh rating for the laugh-o-meter"""
    data = await request.json()
    
    laugh_entry = {
        "laugh_id": f"laugh_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "egg_id": data.get("egg_id"),
        "rating": min(max(data.get("rating", 5), 1), 10),  # 1-10 scale
        "laugh_type": data.get("laugh_type", "chuckle"),  # chuckle, laugh, rofl
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.laugh_entries.insert_one(laugh_entry)
    
    # Award XP for laughing
    xp_awards = {"chuckle": 1, "laugh": 3, "rofl": 5}
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"xp": xp_awards.get(data.get("laugh_type", "chuckle"), 1)}}
    )
    
    return {"message": "Laugh recorded!", "xp_earned": xp_awards.get(data.get("laugh_type", "chuckle"), 1)}

@easter_eggs_router.get("/laugh-leaderboard")
async def get_laugh_leaderboard():
    """Get laugh-o-meter leaderboard"""
    # Top laughers
    top_laughers = await db.laugh_entries.aggregate([
        {"$group": {
            "_id": "$user_id",
            "total_laughs": {"$sum": 1},
            "avg_rating": {"$avg": "$rating"}
        }},
        {"$sort": {"total_laughs": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    for entry in top_laughers:
        user_info = await db.users.find_one(
            {"user_id": entry["_id"]},
            {"_id": 0, "name": 1, "picture": 1}
        )
        entry["user"] = user_info
    
    # Funniest jokes
    funniest = await db.laugh_entries.aggregate([
        {"$group": {
            "_id": "$egg_id",
            "avg_rating": {"$avg": "$rating"},
            "total_laughs": {"$sum": 1}
        }},
        {"$sort": {"avg_rating": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    return {
        "top_laughers": top_laughers,
        "funniest_jokes": funniest
    }

# ============= PROTOCOL RECOMMENDATIONS =============

@api_router.post("/protocol-recommendations")
async def submit_protocol_recommendation(
    request: Request,
    user: User = Depends(require_auth)
):
    """Submit a recommendation for a public protocol"""
    data = await request.json()
    category_id = data.get("category_id")
    recommendation = data.get("recommendation")
    
    if not category_id or not recommendation:
        raise HTTPException(status_code=400, detail="category_id and recommendation required")
    
    # Verify it's a public protocol
    category = await db.categories.find_one(
        {"category_id": category_id, "is_public": True},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Public protocol not found")
    
    rec_entry = {
        "recommendation_id": f"rec_{uuid.uuid4().hex[:12]}",
        "category_id": category_id,
        "owner_id": category["user_id"],
        "recommender_id": user.user_id,
        "recommendation": recommendation,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.protocol_recommendations.insert_one(rec_entry)
    rec_entry.pop("_id", None)
    
    return {"message": "Recommendation submitted", "recommendation": rec_entry}

@api_router.get("/protocol-recommendations/{category_id}")
async def get_protocol_recommendations(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Get recommendations for a protocol (owner only)"""
    # Verify ownership
    category = await db.categories.find_one(
        {"category_id": category_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    recommendations = await db.protocol_recommendations.find(
        {"category_id": category_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Get recommender info
    for rec in recommendations:
        recommender = await db.users.find_one(
            {"user_id": rec["recommender_id"]},
            {"_id": 0, "name": 1, "picture": 1}
        )
        rec["recommender"] = recommender
    
    return {"recommendations": recommendations}

# ============= COPY PROTOCOL TO CLIPBOARD =============

@api_router.post("/copy-protocol")
async def copy_protocol(
    request: Request,
    user: User = Depends(require_auth)
):
    """Copy a protocol to clipboard (track the copy)"""
    data = await request.json()
    category_id = data.get("category_id")
    
    category = await db.categories.find_one(
        {"category_id": category_id},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check if public or user owns it
    if not category.get("is_public") and category.get("user_id") != user.user_id:
        raise HTTPException(status_code=403, detail="Protocol is private")
    
    # Track the copy
    await db.protocol_copies.insert_one({
        "original_id": category_id,
        "copied_by": user.user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "protocol": category.get("protocol"),
        "name": category.get("name"),
        "message": "Protocol copied to clipboard"
    }

# ============= CLEAN CATEGORY =============

@categories_router.post("/{category_id}/clean")
async def clean_category(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Delete all search results for a category"""
    # Verify ownership
    category = await db.categories.find_one(
        {"category_id": category_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    result = await db.search_results.delete_many({
        "user_id": user.user_id,
        "category_ids": category_id
    })
    
    return {"message": f"Deleted {result.deleted_count} results from category"}

# ============= TOP WORDS/PHRASES ANALYTICS =============

@stats_router.get("/top-words")
async def get_top_words(user: User = Depends(require_auth)):
    """Get top 10 most used words in user's search results"""
    # Get all user's search result snippets
    results = await db.search_results.find(
        {"user_id": user.user_id},
        {"_id": 0, "snippet": 1, "title": 1}
    ).to_list(1000)
    
    # Common words to exclude
    exclude_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
        'just', 'should', 'now', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would',
        'could', 'might', 'must', 'shall', 'this', 'that', 'these', 'those', 'i',
        'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
        'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
        'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
        'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'as', 'if', 'while'
    }
    
    word_counts = {}
    for result in results:
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        words = re.findall(r'\b[a-z]{4,}\b', text)  # Words with 4+ letters
        for word in words:
            if word not in exclude_words:
                word_counts[word] = word_counts.get(word, 0) + 1
    
    # Get top 10
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {"top_words": [{"word": w, "count": c} for w, c in top_words]}

@stats_router.get("/top-protocol-words")
async def get_top_protocol_words(user: User = Depends(require_auth)):
    """Get top 10 most used words in user's protocols"""
    categories = await db.categories.find(
        {"user_id": user.user_id},
        {"_id": 0, "protocol": 1}
    ).to_list(500)
    
    word_counts = {}
    for cat in categories:
        protocol = cat.get("protocol", "")
        # Extract words from parentheses groups
        groups = re.findall(r'\(([^)]+)\)', protocol)
        for group in groups:
            terms = [t.strip().lower() for t in group.split(' or ')]
            for term in terms:
                if term and len(term) > 2:
                    word_counts[term] = word_counts.get(term, 0) + 1
    
    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {"top_protocol_words": [{"term": w, "count": c} for w, c in top_words]}

# ============= AI NEWS HEADLINES =============

@newsletter_router.get("/ai-headlines")
async def get_ai_headlines():
    """Get AI-generated news headlines"""
    # Return stored headlines or generate simple ones
    headlines = await db.ai_headlines.find({}, {"_id": 0})\
        .sort("created_at", -1)\
        .limit(10)\
        .to_list(10)
    
    if not headlines:
        # Default headlines
        default_headlines = [
            {"title": "InfoPilot Users Collate Record 1M Documents This Week", "category": "Platform"},
            {"title": "New Protocol Marketplace Feature Launched", "category": "Features"},
            {"title": "Top 10 Most Popular Protocols of the Month", "category": "Trending"},
            {"title": "Community Reaches 10,000 Active Researchers", "category": "Milestone"},
            {"title": "AI-Powered Search Coming Soon", "category": "Technology"},
            {"title": "Best Practices for Writing Effective Protocols", "category": "Tips"},
            {"title": "Introducing Theme Customization", "category": "Features"},
            {"title": "How One User Found Their Research Breakthrough", "category": "Stories"},
            {"title": "Weekly Protocol Challenge Winners Announced", "category": "Community"},
            {"title": "Security Updates Keep Your Research Safe", "category": "Security"}
        ]
        headlines = [
            {**h, "headline_id": f"hl_{i}", "created_at": datetime.now(timezone.utc).isoformat()}
            for i, h in enumerate(default_headlines)
        ]
    
    return {"headlines": headlines}

@newsletter_router.post("/refresh-headlines")
async def refresh_headlines(user: User = Depends(require_admin)):
    """Refresh AI headlines (admin only)"""
    # In production, this would call an AI service
    new_headlines = [
        {"title": f"Breaking: New Feature Announcement - {datetime.now().strftime('%B %d')}", "category": "News"},
        {"title": "Community Highlight: Top Protocol Creators This Week", "category": "Community"},
        {"title": "Research Tips from Power Users", "category": "Tips"},
        {"title": "Platform Updates and Improvements", "category": "Updates"},
        {"title": "Trending Categories to Explore", "category": "Trending"}
    ]
    
    for h in new_headlines:
        h["headline_id"] = f"hl_{uuid.uuid4().hex[:8]}"
        h["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.ai_headlines.insert_one(h)
    
    return {"message": "Headlines refreshed", "count": len(new_headlines)}

# ============= COMMUNITY LEADERBOARD =============

@social_router.get("/leaderboard")
async def get_community_leaderboard():
    """Get community leaderboard"""
    # Top protocol creators by sales
    top_sellers = await db.categories.aggregate([
        {"$match": {"is_public": True, "sales_count": {"$gt": 0}}},
        {"$group": {
            "_id": "$user_id",
            "total_sales": {"$sum": "$sales_count"},
            "protocol_count": {"$sum": 1}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    for seller in top_sellers:
        user_info = await db.users.find_one(
            {"user_id": seller["_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1, "xp": 1, "level": 1}
        )
        seller["user"] = user_info
    
    # Rising stars (most copies)
    rising_stars = await db.protocol_copies.aggregate([
        {"$group": {"_id": "$original_id", "copies": {"$sum": 1}}},
        {"$lookup": {
            "from": "categories",
            "localField": "_id",
            "foreignField": "category_id",
            "as": "category"
        }},
        {"$unwind": "$category"},
        {"$group": {
            "_id": "$category.user_id",
            "total_copies": {"$sum": "$copies"}
        }},
        {"$sort": {"total_copies": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    for star in rising_stars:
        user_info = await db.users.find_one(
            {"user_id": star["_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        star["user"] = user_info
    
    # Top XP earners
    top_xp = await db.users.find(
        {},
        {"_id": 0, "user_id": 1, "name": 1, "picture": 1, "xp": 1, "level": 1}
    ).sort("xp", -1).limit(10).to_list(10)
    
    return {
        "top_sellers": top_sellers,
        "rising_stars": rising_stars,
        "top_xp": top_xp
    }

# ============= PROMOTIONS & BOOK SALES =============

BOOK_INFO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "tagline": "A Supernatural Thriller Comedy",
    "description": "A true love story, a scientific journey past the edge of interest, an ethical standard to live and love by. Join aspiring pilot John Selman on an extraordinary journey through the U.S. Navy, hallucinations revealing alien life, and the pursuit of his beloved Evelyn.",
    "features": [
        "Over 20 five-star reviews from Readers' Favorite",
        "Part memoir, part sci-fi, part rom-com",
        "Contains the partial solution to the Grand Unifying Theory",
        "50 hilarious jokes included",
        "Currently in development for film production"
    ],
    "purchase_links": {
        "amazon_paperback": "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J",
        "amazon_kindle": "https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J",
        "barnes_noble": "https://www.barnesandnoble.com",
        "google_play": "https://play.google.com/store/books",
        "paypal": "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU"
    },
    "prices": {
        "ebook": 5.99,
        "paperback": 17.90,
        "hardcover": 22.90
    },
    "reviews": [
        {"reviewer": "Olga Markova", "rating": 5, "text": "A captivating blend of memoir and fantasy!"},
        {"reviewer": "P. Zeitsman", "rating": 5, "text": "Thought-provoking and emotionally resonant."},
        {"reviewer": "K.C. Finn", "rating": 5, "text": "A unique literary experience that defies genre."},
        {"reviewer": "Christian Sia", "rating": 5, "text": "Lyrical prose with deep spiritual themes."},
        {"reviewer": "Ruffina Oserio", "rating": 5, "text": "A journey through love, trauma, and redemption."}
    ]
}

MAESTRO_BISTRO_INFO = {
    "name": "Maestro Bistro",
    "tagline": "Fine Dining on Wheels",
    "location": "Brunswick, Maine",
    "menu": [
        {"name": "Fish Chowder", "description": "Rich, creamy New England fish chowder", "price": 12.99},
        {"name": "German Beef Rouladen", "description": "Traditional German rolled beef with savory filling", "price": 18.99}
    ],
    "description": "A food truck by John Selman Productions, serving authentic New England fish chowder and German beef rouladen in Brunswick, Maine."
}

@promotions_router.get("/book")
async def get_book_info():
    """Get Letters to Evelyn book information"""
    return BOOK_INFO

@promotions_router.get("/food")
async def get_food_info():
    """Get Maestro Bistro food truck information"""
    return MAESTRO_BISTRO_INFO

@promotions_router.get("/all")
async def get_all_promotions():
    """Get all promotional content"""
    return {
        "book": BOOK_INFO,
        "food": MAESTRO_BISTRO_INFO,
        "company": {
            "name": "Top Pilot Enterprises, Inc.",
            "ceo": "John Selman",
            "location": "Brunswick, Maine",
            "founded": 2025,
            "subsidiaries": ["John Selman Productions", "Maestro Bistro"],
            "tagline": "First in Flight with Monetization of Searches"
        }
    }

# ============= PERSONAL REPORTS ROUTES =============

@reports_router.get("")
async def get_personal_reports(
    page: int = 1,
    limit: int = 20,
    user_id: Optional[str] = None,
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

@reports_router.post("")
async def create_personal_report(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a personal report with up to 3 images"""
    data = await request.json()
    
    # Validate images (max 3)
    images = data.get("images", [])[:3]
    
    report = {
        "report_id": f"rep_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "title": data.get("title"),
        "content": data.get("content"),
        "images": images,
        "location": data.get("location"),  # {city, state, country, lat, lng}
        "category_ids": data.get("category_ids", []),
        "document_type": "Personal Report (Organic)",
        "reactions": {},
        "comments_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.personal_reports.insert_one(report)
    report.pop("_id", None)
    
    # Award XP for creating report
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"xp": 25}}
    )
    
    return report

@reports_router.put("/{report_id}")
async def update_personal_report(
    report_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Update a personal report"""
    data = await request.json()
    
    # Verify ownership
    report = await db.personal_reports.find_one(
        {"report_id": report_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    update_data = {}
    if "title" in data:
        update_data["title"] = data["title"]
    if "content" in data:
        update_data["content"] = data["content"]
    if "images" in data:
        update_data["images"] = data["images"][:3]
    if "location" in data:
        update_data["location"] = data["location"]
    if "category_ids" in data:
        update_data["category_ids"] = data["category_ids"]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.personal_reports.update_one(
        {"report_id": report_id},
        {"$set": update_data}
    )
    
    updated = await db.personal_reports.find_one({"report_id": report_id}, {"_id": 0})
    return updated

@reports_router.delete("/{report_id}")
async def delete_personal_report(
    report_id: str,
    user: User = Depends(require_auth)
):
    """Delete a personal report"""
    result = await db.personal_reports.delete_one({
        "report_id": report_id,
        "user_id": user.user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted"}

# ============= SUBSCRIPTION & PAYPAL =============

@api_router.get("/subscription/info")
async def get_subscription_info():
    """Get subscription information"""
    price_setting = await db.settings.find_one({"key": "subscription_price"}, {"_id": 0})
    price = price_setting.get("value", 0.99) if price_setting else 0.99
    
    return {
        "price": price,
        "period": "monthly",
        "features": [
            "Unlimited search results",
            "Access to Map View",
            "Create unlimited categories",
            "Sell protocols in marketplace",
            "Real-time messaging",
            "Priority support"
        ],
        "paypal_link": "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU",
        "paypal_email": "JJspilot24@gmail.com",
        "first_in_flight": "InfoPilot Explorer is First in Flight with Monetization of Searches! Your time is valuable.",
        "pay_what_you_want": {
            "enabled": True,
            "minimum": 0.75,
            "suggested": 0.99,
            "yearly_intro": 0.75,
            "yearly_regular": 4.62
        }
    }

@api_router.post("/subscription/verify")
async def verify_subscription(
    request: Request,
    user: User = Depends(require_auth)
):
    """Verify a PayPal subscription payment"""
    data = await request.json()
    payment_id = data.get("payment_id")
    amount = data.get("amount", 0.99)
    
    # In production, verify with PayPal API
    # For now, mark user as paid
    subscription_until = datetime.now(timezone.utc) + timedelta(days=30)
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "is_paid": True,
            "subscription_until": subscription_until.isoformat()
        }}
    )
    
    # Record payment
    await db.payments.insert_one({
        "payment_id": payment_id or f"pay_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "amount": amount,
        "type": "subscription",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Subscription activated", "until": subscription_until.isoformat()}

# ============= DOCUMENT TYPE FILTERS =============

@api_router.get("/document-types")
async def get_document_types():
    """Get all document types for filtering"""
    return {
        "types": [
            {"id": "informative_phd", "name": "Informative Ph.D.", "description": "Academic papers with Ph.D. references"},
            {"id": "informative", "name": "Informative", "description": "Educational and informative content"},
            {"id": "news_article", "name": "News Article", "description": "News and current events"},
            {"id": "blog", "name": "Blog", "description": "Blog posts and personal opinions"},
            {"id": "forum", "name": "Forum", "description": "Discussion forum posts"},
            {"id": "personal_report_organic", "name": "Personal Report (Organic)", "description": "User-created reports"},
            {"id": "personal_report_collected", "name": "Personal Report (Collected)", "description": "First-person narrative articles"},
            {"id": "infopilot_exclusive", "name": "InfoPilot Exclusive", "description": "Content created by InfoPilot"}
        ]
    }

# ============= STRIPE PAYMENTS =============

@payments_router.post("/checkout/session")
async def create_checkout_session(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a Stripe checkout session for subscription"""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe integration not available")
    
    data = await request.json()
    origin_url = data.get("origin_url", "")
    package_type = data.get("package_type", "monthly")  # monthly, yearly_intro, yearly_regular
    
    # Define fixed packages on backend (security)
    PACKAGES = {
        "monthly": {"amount": 0.99, "description": "Monthly Subscription"},
        "yearly_intro": {"amount": 0.75, "description": "Yearly Intro ($0.75/year until March 2026)"},
        "yearly_regular": {"amount": 4.62, "description": "Yearly Regular Subscription"},
        "pay_what_you_want": {"amount": float(data.get("custom_amount", 0.99)), "description": "Pay What You Want"}
    }
    
    if package_type not in PACKAGES:
        package_type = "monthly"
    
    package = PACKAGES[package_type]
    amount = max(0.75, package["amount"])  # Minimum $0.75
    
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")
        
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/payments/webhook/stripe"
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        success_url = f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/settings"
        
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user.user_id,
                "package_type": package_type,
                "description": package["description"]
            }
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        await db.payment_transactions.insert_one({
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "session_id": session.session_id,
            "user_id": user.user_id,
            "amount": amount,
            "currency": "usd",
            "package_type": package_type,
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"url": session.url, "session_id": session.session_id}
    
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@payments_router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    user: User = Depends(require_auth)
):
    """Get the status of a checkout session"""
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe integration not available")
    
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        host_url = os.environ.get("BACKEND_URL", str(request.base_url).rstrip('/'))
        webhook_url = f"{host_url}/api/payments/webhook/stripe"
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        if status.payment_status == "paid":
            # Check if already processed
            existing = await db.payment_transactions.find_one({
                "session_id": session_id,
                "payment_status": "completed"
            })
            
            if not existing:
                # Update transaction
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "payment_status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Activate subscription
                subscription_until = datetime.now(timezone.utc) + timedelta(days=30)
                await db.users.update_one(
                    {"user_id": user.user_id},
                    {"$set": {
                        "is_paid": True,
                        "subscription_until": subscription_until.isoformat()
                    }}
                )
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency
        }
    
    except Exception as e:
        logger.error(f"Stripe status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@payments_router.post("/webhook/stripe")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    if not STRIPE_AVAILABLE:
        return {"status": "ignored"}
    
    try:
        body = await request.body()
        stripe_signature = request.headers.get("Stripe-Signature")
        
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        host_url = os.environ.get("BACKEND_URL", str(request.base_url).rstrip('/'))
        webhook_url = f"{host_url}/api/payments/webhook/stripe"
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        webhook_response = await stripe_checkout.handle_webhook(body, stripe_signature)
        
        if webhook_response.payment_status == "paid":
            # Get user from metadata
            user_id = webhook_response.metadata.get("user_id")
            if user_id:
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "payment_status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                subscription_until = datetime.now(timezone.utc) + timedelta(days=30)
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "is_paid": True,
                        "subscription_until": subscription_until.isoformat()
                    }}
                )
        
        return {"status": "received"}
    
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"status": "error", "detail": str(e)}

@payments_router.get("/packages")
async def get_subscription_packages():
    """Get available subscription packages"""
    return {
        "packages": [
            {"id": "monthly", "name": "Monthly", "price": 0.99, "period": "month", "description": "Full access monthly"},
            {"id": "yearly_intro", "name": "Yearly Intro", "price": 0.75, "period": "year", "description": "Introductory rate until March 2026"},
            {"id": "yearly_regular", "name": "Yearly", "price": 4.62, "period": "year", "description": "Annual subscription"},
            {"id": "pay_what_you_want", "name": "Pay What You Want", "price": 0.75, "period": "month", "description": "Minimum $0.75", "custom": True}
        ],
        "stripe_enabled": STRIPE_AVAILABLE,
        "paypal_link": "https://www.paypal.com/ncp/payment/LGXMXSG3D2MXU"
    }

# ============= LEGAL PAGES =============

LEGAL_DOCUMENTS = {
    "privacy-policy": {
        "title": "Privacy Policy",
        "last_updated": "January 2026",
        "content": """
# Privacy Policy

**InfoPilot Explorer** - Top Pilot Enterprises, Inc.

*Last Updated: January 2026*

*Effective Date: January 1, 2026*

---

## INTRODUCTION AND ACCEPTANCE

By clicking "Continue with Google" or otherwise accessing InfoPilot Explorer, you acknowledge that you have read, understood, and agree to be bound by this Privacy Policy. This Privacy Policy constitutes a legally binding agreement between you ("User," "you," or "your") and Top Pilot Enterprises, Inc. ("Company," "we," "us," or "our").

**InfoPilot Explorer is First in Flight with Monetization of Searches** - pioneering the future of information exchange and search monetization.

---

## 1. AGE REQUIREMENTS AND ELIGIBILITY

### 1.1 Minimum Age Requirement
**YOU MUST BE AT LEAST TWENTY-ONE (21) YEARS OF AGE TO USE INFOPILOT EXPLORER.** By accessing or using our services, you represent and warrant that you are at least 21 years old. We do not knowingly collect, use, or disclose personal information from individuals under 21 years of age.

### 1.2 Age Verification
We reserve the right to request proof of age at any time. If we discover or have reason to believe that a user is under 21 years of age, we will immediately terminate that user's account and delete all associated personal information.

### 1.3 Parental/Guardian Notice
If you are a parent or guardian and believe your child under 21 has provided us with personal information, please contact us immediately at JJSpilot24@gmail.com. We will take steps to remove such information from our systems.

---

## 2. INFORMATION WE COLLECT

### 2.1 Information You Provide Directly

**Account Information:**
- Email address (obtained via Google OAuth authentication)
- Display name and profile picture (from your Google account)
- Username/callsign you create
- Account preferences and settings
- Payment information (processed through secure third-party providers)

**User-Generated Content:**
- Search protocols you create using InfoJet 2.0 language
- Categories and organizational structures
- Comments, reactions, and social interactions
- Personal reports and submissions
- Messages sent through our platform

### 2.2 Information Collected Automatically

**Usage Data:**
- Search queries and collated results
- Pages visited and features used
- Time spent on the platform
- Click patterns and navigation paths
- Device information (browser type, operating system, device identifiers)

**Technical Data:**
- IP address and approximate geographic location
- Browser type and version
- Operating system
- Referring URLs
- Access times and dates
- Error logs and performance data

**Cookies and Tracking Technologies:**
- Session cookies (essential for platform functionality)
- Preference cookies (to remember your settings)
- Analytics cookies (to understand usage patterns)
- Authentication tokens

### 2.3 Information from Third Parties

**Google OAuth:**
- Basic profile information from your Google account
- Email address for account creation and communication

**Payment Processors (Stripe and PayPal):**
- Transaction confirmations
- Payment status updates
- We do NOT receive or store your full credit card numbers

---

## 3. HOW WE USE YOUR INFORMATION

### 3.1 Primary Uses

We use your information to:
- Provide, maintain, and improve InfoPilot Explorer services
- Process your account registration and authentication
- Enable your use of the Ultimate Search Page and protocol features
- Facilitate social networking features (friends, groups, messaging)
- Process payments and manage subscriptions
- Send service-related communications

### 3.2 Personalization

We use your data to:
- Customize your Ultimate Search Page experience
- Recommend protocols and categories based on your interests
- Display relevant content in your feed
- Remember your preferences and settings

### 3.3 Communication

We may contact you to:
- Send our tri-weekly newsletter (if subscribed)
- Notify you of important service updates
- Respond to your inquiries and support requests
- Inform you of changes to our policies
- Send promotional materials (with your consent)

### 3.4 Safety and Security

We use information to:
- Detect and prevent fraud, abuse, and security incidents
- Enforce our User Agreement and community guidelines
- Protect the rights and safety of our users
- Comply with legal obligations

### 3.5 Analytics and Improvement

We analyze data to:
- Understand how users interact with our platform
- Identify areas for improvement
- Develop new features and services
- Measure the effectiveness of our services

---

## 4. INFORMATION SHARING AND DISCLOSURE

### 4.1 Public Information

The following may be visible to other users:
- Your display name and profile picture
- Public protocols and categories you create
- Your activity on public content (reactions, comments)
- Your position on leaderboards
- Information you choose to make public in your settings

### 4.2 Service Providers

We share information with trusted third parties who assist us in:
- Payment processing (Stripe, PayPal)
- Cloud hosting and data storage
- Analytics and performance monitoring
- Customer support services
- Email delivery services

These providers are contractually obligated to protect your information and use it only for the services they provide to us.

### 4.3 Legal Requirements

We may disclose your information if required to:
- Comply with applicable laws, regulations, or legal processes
- Respond to lawful requests from government authorities
- Protect our rights, privacy, safety, or property
- Enforce our User Agreement
- Protect against legal liability

### 4.4 Business Transfers

In the event of a merger, acquisition, reorganization, or sale of assets, your information may be transferred to the acquiring entity. We will notify you of any such change and any choices you may have regarding your information.

### 4.5 With Your Consent

We may share your information for other purposes with your explicit consent.

---

## 5. DATA SECURITY

### 5.1 Security Measures

We implement comprehensive security measures including:
- Encryption of data in transit using TLS/SSL (HTTPS)
- Secure authentication via Google OAuth 2.0
- Regular security assessments and audits
- Access controls and authentication for our systems
- Secure data storage with industry-standard protections
- Regular backup procedures
- Incident response procedures

### 5.2 Your Responsibilities

You are responsible for:
- Maintaining the security of your Google account
- Not sharing your account credentials
- Logging out of shared devices
- Reporting any suspected unauthorized access

### 5.3 Security Limitations

While we strive to protect your information, no method of transmission over the Internet or electronic storage is 100% secure. We cannot guarantee absolute security.

---

## 6. DATA RETENTION

### 6.1 Retention Periods

We retain your information for as long as:
- Your account remains active
- Necessary to provide our services
- Required by applicable laws
- Needed for legitimate business purposes

### 6.2 Account Deletion

Upon account deletion:
- Your personal profile information will be removed
- Your public content may be anonymized or retained
- Some information may be retained for legal compliance
- Backup copies may persist for a limited time

---

## 7. YOUR RIGHTS AND CHOICES

### 7.1 Access and Portability

You have the right to:
- Access the personal information we hold about you
- Request a copy of your data in a portable format
- Review your account information at any time

### 7.2 Correction

You may:
- Update your profile information through your account settings
- Request correction of inaccurate information

### 7.3 Deletion

You may:
- Delete your account through the settings page
- Request deletion of specific content you've created
- Request removal of your personal information

### 7.4 Opt-Out Rights

You may opt out of:
- Marketing communications (via unsubscribe links or settings)
- Newsletter subscriptions
- Non-essential cookies (through browser settings)

### 7.5 Do Not Track

Our platform does not currently respond to "Do Not Track" browser signals.

---

## 8. CHILDREN AND MINORS

### 8.1 Age Restriction

**InfoPilot Explorer is strictly for users 21 years of age and older.** We do not knowingly collect personal information from anyone under 21.

### 8.2 Discovery of Underage Users

If we learn that we have collected personal information from a user under 21, we will:
- Immediately terminate the account
- Delete all associated personal information
- Take steps to prevent future access

### 8.3 Reporting

If you believe a user is under 21, please report this to JJSpilot24@gmail.com.

---

## 9. INTERNATIONAL DATA TRANSFERS

### 9.1 Data Location

Your information may be transferred to and processed in the United States and other countries where our service providers operate.

### 9.2 Safeguards

We implement appropriate safeguards for international data transfers, including contractual protections with our service providers.

---

## 10. CALIFORNIA PRIVACY RIGHTS

### 10.1 California Consumer Privacy Act (CCPA)

California residents have additional rights including:
- Right to know what personal information is collected
- Right to know if personal information is sold or disclosed
- Right to opt out of the sale of personal information
- Right to request deletion of personal information
- Right to non-discrimination for exercising privacy rights

### 10.2 Shine the Light

California residents may request information about disclosure of personal information to third parties for direct marketing purposes.

---

## 11. EUROPEAN PRIVACY RIGHTS (GDPR)

### 11.1 Legal Basis for Processing

For users in the European Economic Area, we process personal data based on:
- Your consent
- Performance of our contract with you
- Our legitimate business interests
- Compliance with legal obligations

### 11.2 Additional Rights

EEA users have additional rights including:
- Right to restrict processing
- Right to object to processing
- Right to lodge a complaint with a supervisory authority

---

## 12. CHANGES TO THIS PRIVACY POLICY

### 12.1 Updates

We may update this Privacy Policy from time to time. We will notify you of material changes by:
- Posting the updated policy on our platform
- Sending an email notification
- Displaying a prominent notice on our website

### 12.2 Continued Use

Your continued use of InfoPilot Explorer after changes become effective constitutes acceptance of the updated Privacy Policy.

---

## 13. CONTACT INFORMATION

For questions, concerns, or requests regarding this Privacy Policy, please contact:

**Top Pilot Enterprises, Inc.**
Brunswick, Maine, USA
Email: JJSpilot24@gmail.com
Phone: (207) 522-0894

**Data Protection Inquiries:**
Email: JJSpilot24@gmail.com
Subject Line: "Privacy Inquiry"

---

## 14. CONSENT

**BY CLICKING "CONTINUE WITH GOOGLE" OR OTHERWISE ACCESSING INFOPILOT EXPLORER, YOU ACKNOWLEDGE THAT:**

1. You have read and understood this Privacy Policy in its entirety
2. You are at least 21 years of age
3. You consent to the collection, use, and disclosure of your information as described herein
4. You understand your rights and how to exercise them
5. You agree to be bound by this Privacy Policy and any future updates

---

*Copyright © 2025-2026 Top Pilot Enterprises, Inc. All rights reserved.*

*InfoPilot Explorer - First in Flight with Monetization of Searches*
"""
    },
    "terms-of-service": {
        "title": "User Agreement / Terms of Service",
        "last_updated": "January 2026",
        "content": """
# User Agreement / Terms of Service

**InfoPilot Explorer** - Top Pilot Enterprises, Inc.

*Last Updated: January 2026*

*Effective Date: January 1, 2026*

---

## IMPORTANT: PLEASE READ THIS AGREEMENT CAREFULLY

This User Agreement ("Agreement") is a legally binding contract between you ("User," "you," or "your") and Top Pilot Enterprises, Inc. ("Company," "we," "us," or "our") governing your use of InfoPilot Explorer and all related services.

**BY CLICKING "CONTINUE WITH GOOGLE," CREATING AN ACCOUNT, OR USING INFOPILOT EXPLORER, YOU AGREE TO BE BOUND BY THIS AGREEMENT AND OUR PRIVACY POLICY.**

**InfoPilot Explorer is First in Flight with Monetization of Searches** - pioneering the future of information exchange.

---

## SECTION 1: ELIGIBILITY AND AGE REQUIREMENTS

### 1.1 Minimum Age Requirement

**YOU MUST BE AT LEAST TWENTY-ONE (21) YEARS OF AGE TO USE INFOPILOT EXPLORER.**

By accessing or using InfoPilot Explorer, you represent and warrant that:
- You are at least 21 years of age
- You have the legal capacity to enter into this Agreement
- You are not prohibited from using our services under applicable law

### 1.2 Age Verification

We reserve the right to:
- Request proof of age at any time
- Verify your age through third-party services
- Suspend or terminate accounts suspected of being underage

### 1.3 Consequences of Misrepresentation

If you misrepresent your age:
- Your account will be immediately terminated
- All associated data will be deleted
- You may be permanently banned from the platform
- We reserve the right to pursue legal action

---

## SECTION 2: ACCOUNT REGISTRATION AND SECURITY

### 2.1 Account Creation

To use InfoPilot Explorer, you must:
- Authenticate via Google OAuth
- Provide accurate and complete information
- Maintain one account per person (no multiple accounts)
- Choose an appropriate callsign/username

### 2.2 Account Security

You are responsible for:
- Maintaining the confidentiality of your account
- All activities that occur under your account
- Immediately notifying us of any unauthorized access
- Ensuring your Google account remains secure

### 2.3 Account Restrictions

You may NOT:
- Share your account with others
- Transfer your account to another person
- Create accounts on behalf of others
- Use automated methods to create accounts

---

## SECTION 3: DESCRIPTION OF SERVICES

### 3.1 Platform Overview

InfoPilot Explorer provides:
- **Ultimate Search Page (USP)**: Personalized search collation and categorization
- **InfoJet 2.0 Protocol Language**: Custom search protocol creation
- **Protocol Marketplace**: Buy and sell search protocols
- **Social Features**: Friends, groups, messaging, reactions
- **Leaderboards**: Competitive rankings and achievements
- **Personal Reports**: User-generated content submissions
- **Newsletter**: Tri-weekly information updates

### 3.2 Service Availability

We strive to maintain continuous service but do not guarantee:
- Uninterrupted access to the platform
- Error-free operation
- Compatibility with all devices or browsers
- Availability of specific features

### 3.3 Service Modifications

We reserve the right to:
- Modify, suspend, or discontinue any feature
- Update the platform without prior notice
- Change pricing and subscription terms
- Limit access to certain features

---

## SECTION 4: CHILD SAFETY AND PROTECTION POLICY

### 4.1 Strict Prohibition on Contact with Minors

**USERS ARE STRICTLY PROHIBITED FROM:**
- Attempting to contact, communicate with, or interact with any person under 21 years of age through InfoPilot Explorer
- Using the platform to arrange meetings with minors
- Sharing personal information with the intent of contacting minors
- Using the platform to groom, exploit, or harm minors in any way

### 4.2 Category Title Restrictions

**USERS MAY NOT include references to children, minors, or persons under 21 in any Category Title.** This includes but is not limited to:
- Words such as "child," "children," "kid," "kids," "minor," "minors," "youth," "juvenile," "teen," "teenager," "adolescent," "underage," "baby," "infant," "toddler"
- Age references indicating persons under 21
- School-related terms that imply minor involvement (e.g., "elementary," "middle school," "high school students")
- Any euphemisms or coded language referring to minors

### 4.3 Protocol Content Guidelines

References to children within protocol search strings (InfoJet 2.0 syntax) are permitted ONLY when:
- The content is educational, historical, or informational in nature
- The context is entirely non-sexual and non-exploitative
- The purpose is legitimate research or information gathering
- Examples include: child development research, pediatric health information, educational policy, historical events, family-related topics

### 4.4 Prohibited Protocol Content

Protocols may NOT be used to search for:
- Any sexual content involving minors
- Content that sexualizes, exploits, or endangers children
- Methods to contact or locate minors
- Content promoting harm to children
- Child abuse material of any kind

### 4.5 Reporting and Enforcement

- We actively monitor for violations of child safety policies
- Violations will result in immediate account termination
- We will report suspected illegal activity to law enforcement
- We cooperate fully with investigations involving child safety

### 4.6 Zero Tolerance

**WE MAINTAIN A ZERO-TOLERANCE POLICY FOR ANY CONTENT OR BEHAVIOR THAT ENDANGERS CHILDREN. VIOLATIONS WILL RESULT IN IMMEDIATE AND PERMANENT ACCOUNT TERMINATION AND MAY BE REPORTED TO APPROPRIATE AUTHORITIES.**

---

## SECTION 5: USER CONDUCT AND PROHIBITED ACTIVITIES

### 5.1 General Conduct Standards

You agree to:
- Use InfoPilot Explorer lawfully and ethically
- Respect other users and their content
- Provide accurate information
- Comply with all applicable laws and regulations

### 5.2 Prohibited Content

You may NOT post, share, or create content that:
- Is illegal, harmful, threatening, abusive, or harassing
- Is defamatory, libelous, or invades privacy
- Contains hate speech or discrimination
- Is sexually explicit or pornographic
- Promotes violence or illegal activities
- Infringes intellectual property rights
- Contains malware, viruses, or harmful code
- Is spam, phishing, or fraudulent
- Violates our Child Safety Policy (Section 4)

### 5.3 Prohibited Activities

You may NOT:
- Attempt to hack, exploit, or compromise the platform
- Use automated tools without authorization
- Scrape or harvest user data
- Impersonate others or misrepresent your identity
- Interfere with other users' enjoyment of the platform
- Circumvent security measures or access restrictions
- Use the platform for commercial purposes without authorization
- Engage in any activity that violates this Agreement

### 5.4 Enforcement

Violations may result in:
- Content removal
- Account suspension
- Permanent account termination
- Legal action
- Reporting to law enforcement

---

## SECTION 6: INTELLECTUAL PROPERTY

### 6.1 Company Intellectual Property

Top Pilot Enterprises, Inc. owns all rights to:
- The InfoPilot Explorer platform and software
- The InfoJet 2.0 protocol language and syntax
- All trademarks, logos, and branding
- Platform design, layout, and user interface
- Documentation and educational materials

### 6.2 Your Content

You retain ownership of:
- Protocols you create
- Categories you organize
- Personal reports you submit
- Comments and reactions you post

### 6.3 License Grant to Company

By posting content on InfoPilot Explorer, you grant us a:
- Non-exclusive, worldwide, royalty-free license
- Right to use, display, reproduce, and distribute your content
- Right to modify content for platform functionality
- Right to sublicense to service providers

This license continues even after account deletion for content that has been shared publicly or with other users.

### 6.4 Marketplace Content

For protocols sold in the Marketplace:
- You warrant you have the right to sell the content
- You grant buyers a license to use the protocol
- Revenue sharing applies as specified in Section 8

---

## SECTION 7: PRIVACY AND DATA PROTECTION

### 7.1 Privacy Policy

Your use of InfoPilot Explorer is also governed by our Privacy Policy, which is incorporated into this Agreement by reference.

### 7.2 Data Collection

By using our services, you consent to:
- Collection of information as described in our Privacy Policy
- Use of cookies and tracking technologies
- Processing of your data for service provision

### 7.3 Communication

You agree to receive:
- Service-related communications
- Security alerts and notifications
- Marketing communications (with opt-out option)
- Newsletter (if subscribed)

---

## SECTION 8: PAYMENTS AND SUBSCRIPTIONS

### 8.1 Subscription Plans

InfoPilot Explorer offers:
- **Monthly Subscription**: $0.99/month
- **Yearly Intro Rate**: $0.75/year (available until March 2026)
- **Yearly Regular**: $4.62/year
- **Pay What You Want**: Minimum $0.75

### 8.2 Payment Processing

- Payments are processed through Stripe and PayPal
- You authorize recurring charges for subscriptions
- All prices are in US Dollars
- Taxes may apply based on your location

### 8.3 Billing and Renewal

- Subscriptions auto-renew unless cancelled
- You may cancel at any time through account settings
- Cancellation takes effect at the end of the billing period
- No refunds for partial billing periods

### 8.4 Protocol Marketplace Revenue

For protocol sales:
- **Creator receives**: 90% of sale price
- **Platform fee**: 10% of sale price
- Payments processed monthly for balances over $10
- You are responsible for applicable taxes

### 8.5 Refund Policy

- Subscription refunds are handled case-by-case
- Protocol purchases are generally non-refundable
- Contact support for refund requests

---

## SECTION 9: DISCLAIMERS AND LIMITATIONS

### 9.1 Service Provided "As Is"

INFOPILOT EXPLORER IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
- MERCHANTABILITY
- FITNESS FOR A PARTICULAR PURPOSE
- NON-INFRINGEMENT
- ACCURACY OR RELIABILITY OF CONTENT

### 9.2 No Guarantee of Results

We do not guarantee:
- Accuracy of search results
- Availability of specific content
- Success in the marketplace
- Any particular outcome from using our services

### 9.3 Third-Party Content

We are not responsible for:
- Content created by users
- External websites linked from our platform
- Third-party services integrated with our platform
- Accuracy of information from external sources

### 9.4 Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW:
- We are not liable for indirect, incidental, special, consequential, or punitive damages
- Our total liability shall not exceed the amount you paid us in the past 12 months
- We are not liable for loss of data, profits, or business opportunities

### 9.5 Indemnification

You agree to indemnify and hold harmless Top Pilot Enterprises, Inc. from any claims, damages, or expenses arising from:
- Your use of InfoPilot Explorer
- Your violation of this Agreement
- Your violation of any third-party rights
- Content you create or share

---

## SECTION 10: DISPUTE RESOLUTION

### 10.1 Governing Law

This Agreement is governed by the laws of the State of Maine, United States, without regard to conflict of law principles.

### 10.2 Informal Resolution

Before filing any claim, you agree to attempt informal resolution by contacting us at JJSpilot24@gmail.com.

### 10.3 Arbitration Agreement

Any disputes not resolved informally shall be resolved through binding arbitration in Brunswick, Maine, under the rules of the American Arbitration Association.

### 10.4 Class Action Waiver

YOU AGREE TO RESOLVE DISPUTES INDIVIDUALLY AND WAIVE ANY RIGHT TO PARTICIPATE IN CLASS ACTIONS OR CLASS ARBITRATIONS.

### 10.5 Exceptions

The following may be brought in court:
- Claims for injunctive relief
- Intellectual property disputes
- Small claims court matters

---

## SECTION 11: TERMINATION

### 11.1 Termination by You

You may terminate your account at any time by:
- Using the account deletion feature in settings
- Contacting support at JJSpilot24@gmail.com

### 11.2 Termination by Us

We may suspend or terminate your account for:
- Violation of this Agreement
- Violation of our Child Safety Policy
- Illegal activity
- Extended inactivity
- Any reason at our sole discretion

### 11.3 Effect of Termination

Upon termination:
- Your right to use the platform ceases immediately
- Your account data may be deleted
- Certain provisions of this Agreement survive termination
- You remain liable for any prior violations

---

## SECTION 12: GENERAL PROVISIONS

### 12.1 Entire Agreement

This Agreement, together with our Privacy Policy, constitutes the entire agreement between you and Top Pilot Enterprises, Inc.

### 12.2 Severability

If any provision is found unenforceable, the remaining provisions continue in effect.

### 12.3 Waiver

Our failure to enforce any provision does not waive our right to enforce it later.

### 12.4 Assignment

You may not assign this Agreement. We may assign our rights and obligations without restriction.

### 12.5 Modifications

We may modify this Agreement at any time. Material changes will be notified via:
- Email notification
- Platform announcement
- Updated posting date

Continued use after changes constitutes acceptance.

### 12.6 Contact Information

**Top Pilot Enterprises, Inc.**
Brunswick, Maine, USA
Email: JJSpilot24@gmail.com
Phone: (207) 522-0894

---

## SECTION 13: ACKNOWLEDGMENT AND CONSENT

**BY CLICKING "CONTINUE WITH GOOGLE" OR USING INFOPILOT EXPLORER, YOU ACKNOWLEDGE THAT:**

1. You have read this Agreement in its entirety
2. You understand and agree to all terms and conditions
3. You are at least 21 years of age
4. You agree to comply with our Child Safety Policy
5. You consent to our Privacy Policy
6. You understand the consequences of violating this Agreement
7. This Agreement is legally binding

---

*Copyright © 2025-2026 Top Pilot Enterprises, Inc. All rights reserved.*

*InfoPilot Explorer - First in Flight with Monetization of Searches*
"""
    }
}

@legal_router.get("/{doc_type}")
async def get_legal_document(doc_type: str):
    """Get a legal document (privacy-policy or terms-of-service)"""
    if doc_type not in LEGAL_DOCUMENTS:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check for admin-customized version first
    custom_doc = await db.legal_documents.find_one({"doc_type": doc_type}, {"_id": 0})
    if custom_doc:
        return custom_doc
    
    return LEGAL_DOCUMENTS[doc_type]

@legal_router.put("/{doc_type}")
async def update_legal_document(
    doc_type: str,
    request: Request,
    user: User = Depends(require_admin)
):
    """Update a legal document (admin only)"""
    if doc_type not in ["privacy-policy", "terms-of-service"]:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    data = await request.json()
    
    await db.legal_documents.update_one(
        {"doc_type": doc_type},
        {"$set": {
            "doc_type": doc_type,
            "title": data.get("title", LEGAL_DOCUMENTS[doc_type]["title"]),
            "content": data.get("content"),
            "last_updated": datetime.now(timezone.utc).strftime("%B %Y")
        }},
        upsert=True
    )
    
    return {"message": "Document updated"}

# ============= PROTOCOL TEMPLATES =============

@templates_router.get("")
async def get_protocol_templates(
    is_public: Optional[bool] = None,
    user: User = Depends(require_auth)
):
    """Get protocol templates"""
    query = {}
    
    if is_public is True:
        query["is_public"] = True
    elif is_public is False:
        query["$or"] = [
            {"user_id": user.user_id},
            {"is_public": True}
        ]
    else:
        query["$or"] = [
            {"user_id": user.user_id},
            {"is_public": True}
        ]
    
    templates = await db.protocol_templates.find(query, {"_id": 0})\
        .sort("created_at", -1)\
        .to_list(100)
    
    # Get creator info
    for t in templates:
        creator = await db.users.find_one(
            {"user_id": t.get("user_id")},
            {"_id": 0, "name": 1, "picture": 1}
        )
        t["creator"] = creator
    
    return {"templates": templates}

@templates_router.post("")
async def create_protocol_template(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a protocol template"""
    data = await request.json()
    
    template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).isoformat()
    user_id = user.user_id
    
    template_doc = {
        "template_id": template_id,
        "user_id": user_id,
        "name": data.get("name"),
        "description": data.get("description", ""),
        "protocol_string": data.get("protocol_string"),
        "category": data.get("category", "General"),
        "is_public": data.get("is_public", False),
        "usage_count": 0,
        "created_at": created_at
    }
    
    await db.protocol_templates.insert_one(template_doc)
    
    # Return clean response without MongoDB _id
    response_data = {
        "template_id": template_id,
        "user_id": user_id,
        "name": str(data.get("name", "")),
        "description": str(data.get("description", "")),
        "protocol_string": str(data.get("protocol_string", "")),
        "category": str(data.get("category", "General")),
        "is_public": bool(data.get("is_public", False)),
        "usage_count": 0,
        "created_at": created_at
    }
    return JSONResponse(content=response_data)

@templates_router.get("/{template_id}")
async def get_protocol_template(
    template_id: str,
    user: User = Depends(require_auth)
):
    """Get a specific protocol template"""
    template = await db.protocol_templates.find_one(
        {"template_id": template_id},
        {"_id": 0}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not template.get("is_public") and template.get("user_id") != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return template

@templates_router.post("/{template_id}/use")
async def use_protocol_template(
    template_id: str,
    user: User = Depends(require_auth)
):
    """Use a template to create a new category"""
    template = await db.protocol_templates.find_one(
        {"template_id": template_id},
        {"_id": 0}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create category from template
    category = {
        "category_id": f"cat_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "name": template["name"],
        "protocol": template["protocol_string"],
        "parent_id": None,
        "is_public": True,
        "price": 0.0,
        "sales_count": 0,
        "from_template": template_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(category)
    category.pop("_id", None)
    
    # Increment usage count
    await db.protocol_templates.update_one(
        {"template_id": template_id},
        {"$inc": {"usage_count": 1}}
    )
    
    return {"message": "Category created from template", "category": category}

@templates_router.delete("/{template_id}")
async def delete_protocol_template(
    template_id: str,
    user: User = Depends(require_auth)
):
    """Delete a protocol template"""
    result = await db.protocol_templates.delete_one({
        "template_id": template_id,
        "user_id": user.user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found or access denied")
    
    return {"message": "Template deleted"}

# ============= ENHANCED MAP DATA =============

@stats_router.get("/map-data-detailed")
async def get_detailed_map_data(user: User = Depends(require_auth)):
    """Get detailed map data with all results per location"""
    # Get all search results with location data
    results = await db.search_results.find(
        {"user_id": user.user_id, "locations": {"$exists": True, "$ne": []}},
        {"_id": 0}
    ).to_list(1000)
    
    # Group results by location
    location_groups = {}
    for result in results:
        for loc in result.get("locations", []):
            key = f"{loc.get('country', 'Unknown')}_{loc.get('state', '')}_{loc.get('city', '')}"
            if key not in location_groups:
                location_groups[key] = {
                    "location": loc,
                    "results": [],
                    "count": 0
                }
            location_groups[key]["results"].append({
                "result_id": result.get("result_id"),
                "title": result.get("title"),
                "url": result.get("url"),
                "document_type": result.get("document_type"),
                "snippet": result.get("snippet", "")[:200]
            })
            location_groups[key]["count"] += 1
    
    return {
        "locations": list(location_groups.values()),
        "total_locations": len(location_groups),
        "total_results": len(results)
    }

@stats_router.get("/map-location/{location_key}")
async def get_results_by_location(
    location_key: str,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_auth)
):
    """Get all search results for a specific map location"""
    # Parse location key (format: country_state_city)
    parts = location_key.split("_")
    country = parts[0] if len(parts) > 0 else None
    state = parts[1] if len(parts) > 1 else None
    city = parts[2] if len(parts) > 2 else None
    
    query = {"user_id": user.user_id}
    
    if country:
        query["locations.country"] = country
    if state:
        query["locations.state"] = state
    if city:
        query["locations.city"] = city
    
    skip = (page - 1) * limit
    results = await db.search_results.find(query, {"_id": 0})\
        .skip(skip)\
        .limit(limit)\
        .to_list(limit)
    
    total = await db.search_results.count_documents(query)
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "location": {"country": country, "state": state, "city": city}
    }

# ============= APP DOWNLOAD LINKS =============

@api_router.get("/app-downloads")
async def get_app_download_links():
    """Get app download links for mobile and desktop"""
    return {
        "android": {
            "name": "InfoPilot Explorer",
            "store": "Google Play Store",
            "url": "https://play.google.com/store/apps/details?id=com.infopilot.explorer",
            "icon": "android"
        },
        "ios": {
            "name": "InfoJet",
            "store": "Apple App Store",
            "url": "https://apps.apple.com/app/infojet",
            "icon": "apple"
        },
        "desktop": {
            "name": "InfoPilot Desktop",
            "platforms": ["Windows", "macOS", "Linux"],
            "url": "https://www.infopilotexplorer.biz/download",
            "icon": "monitor"
        },
        "browser_extension": {
            "name": "InfoPilot Browser Extension",
            "browsers": ["Chrome", "Firefox", "Edge"],
            "url": "https://chrome.google.com/webstore/detail/infopilot",
            "icon": "globe"
        }
    }

# ============= SEARCH RESULT HEATMAPS =============

@heatmap_router.get("/activity")
async def get_activity_heatmap(
    period: str = "month",  # week, month, year
    user: User = Depends(require_auth)
):
    """Get search activity heatmap data"""
    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == "week":
        days = 7
    elif period == "year":
        days = 365
    else:
        days = 30
    
    start_date = now - timedelta(days=days)
    
    # Get activity by hour and day
    pipeline = [
        {"$match": {
            "user_id": user.user_id,
            "created_at": {"$gte": start_date.isoformat()}
        }},
        {"$addFields": {
            "parsed_date": {"$dateFromString": {"dateString": "$created_at", "onError": None}}
        }},
        {"$match": {"parsed_date": {"$ne": None}}},
        {"$group": {
            "_id": {
                "day": {"$dayOfWeek": "$parsed_date"},
                "hour": {"$hour": "$parsed_date"}
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.day": 1, "_id.hour": 1}}
    ]
    
    results = await db.search_results.aggregate(pipeline).to_list(200)
    
    # Format for heatmap (7 days x 24 hours)
    heatmap_data = [[0 for _ in range(24)] for _ in range(7)]
    for r in results:
        day = r["_id"]["day"] - 1  # 0-indexed
        hour = r["_id"]["hour"]
        if 0 <= day < 7 and 0 <= hour < 24:
            heatmap_data[day][hour] = r["count"]
    
    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    return {
        "period": period,
        "heatmap": heatmap_data,
        "days": day_names,
        "hours": list(range(24)),
        "max_value": max(max(row) for row in heatmap_data) if any(any(row) for row in heatmap_data) else 0
    }

@heatmap_router.get("/location")
async def get_location_heatmap(user: User = Depends(require_auth)):
    """Get location-based heatmap data"""
    pipeline = [
        {"$match": {"user_id": user.user_id}},
        {"$unwind": "$locations"},
        {"$group": {
            "_id": {
                "country": "$locations.country",
                "state": "$locations.state"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 50}
    ]
    
    results = await db.search_results.aggregate(pipeline).to_list(50)
    
    return {
        "locations": [
            {
                "country": r["_id"].get("country", "Unknown"),
                "state": r["_id"].get("state", ""),
                "count": r["count"],
                "intensity": min(r["count"] / 10, 1.0)  # Normalize 0-1
            }
            for r in results
        ]
    }

@heatmap_router.get("/domain")
async def get_domain_heatmap(user: User = Depends(require_auth)):
    """Get domain activity heatmap"""
    pipeline = [
        {"$match": {"user_id": user.user_id}},
        {"$group": {
            "_id": "$root_domain",
            "count": {"$sum": 1},
            "last_accessed": {"$max": "$created_at"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 30}
    ]
    
    results = await db.search_results.aggregate(pipeline).to_list(30)
    max_count = results[0]["count"] if results else 1
    
    return {
        "domains": [
            {
                "domain": r["_id"],
                "count": r["count"],
                "intensity": r["count"] / max_count,
                "last_accessed": r["last_accessed"]
            }
            for r in results if r["_id"]
        ]
    }

# ============= COLLABORATIVE SEARCH SESSIONS =============

# In-memory store for active sessions (in production, use Redis)
active_collab_sessions = {}

@collab_router.post("/sessions")
async def create_collab_session(
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a new collaborative search session"""
    data = await request.json()
    
    session_id = f"collab_{uuid.uuid4().hex[:12]}"
    session = {
        "session_id": session_id,
        "name": data.get("name", "Untitled Session"),
        "description": data.get("description", ""),
        "host_id": user.user_id,
        "host_name": user.name,
        "participants": [{"user_id": user.user_id, "name": user.name, "role": "host"}],
        "search_query": "",
        "results": [],
        "chat_messages": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "invite_code": uuid.uuid4().hex[:8].upper()
    }
    
    # Store in database
    await db.collab_sessions.insert_one(session)
    session.pop("_id", None)
    
    # Also store in memory for real-time updates
    active_collab_sessions[session_id] = session
    
    return session

@collab_router.get("/sessions")
async def get_collab_sessions(user: User = Depends(require_auth)):
    """Get user's collaborative sessions"""
    sessions = await db.collab_sessions.find(
        {"$or": [
            {"host_id": user.user_id},
            {"participants.user_id": user.user_id}
        ]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"sessions": sessions}

@collab_router.post("/sessions/join")
async def join_collab_session(
    request: Request,
    user: User = Depends(require_auth)
):
    """Join a collaborative session by invite code"""
    data = await request.json()
    invite_code = data.get("invite_code", "").upper()
    
    session = await db.collab_sessions.find_one(
        {"invite_code": invite_code, "is_active": True},
        {"_id": 0}
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inactive")
    
    # Add participant if not already in
    if not any(p["user_id"] == user.user_id for p in session["participants"]):
        await db.collab_sessions.update_one(
            {"session_id": session["session_id"]},
            {"$push": {"participants": {"user_id": user.user_id, "name": user.name, "role": "participant"}}}
        )
    
    return session

@collab_router.get("/sessions/{session_id}")
async def get_collab_session(
    session_id: str,
    user: User = Depends(require_auth)
):
    """Get a specific collaborative session"""
    session = await db.collab_sessions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user is participant
    if not any(p["user_id"] == user.user_id for p in session["participants"]):
        raise HTTPException(status_code=403, detail="Not a participant in this session")
    
    return session

@collab_router.post("/sessions/{session_id}/search")
async def collab_search(
    session_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Perform a search in collaborative session"""
    data = await request.json()
    query = data.get("query", "")
    
    # Update session with query
    await db.collab_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"search_query": query, "last_search_by": user.name}}
    )
    
    # Perform search (reuse existing search logic)
    # This is simplified - in production, you'd call your actual search function
    return {"message": "Search initiated", "query": query, "by": user.name}

@collab_router.post("/sessions/{session_id}/message")
async def collab_message(
    session_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Send a message in collaborative session"""
    data = await request.json()
    
    message = {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "user_id": user.user_id,
        "user_name": user.name,
        "content": data.get("content", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.collab_sessions.update_one(
        {"session_id": session_id},
        {"$push": {"chat_messages": message}}
    )
    
    return message

@collab_router.delete("/sessions/{session_id}")
async def end_collab_session(
    session_id: str,
    user: User = Depends(require_auth)
):
    """End a collaborative session (host only)"""
    session = await db.collab_sessions.find_one({"session_id": session_id})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["host_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Only the host can end the session")
    
    await db.collab_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"is_active": False, "ended_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Session ended"}

# ============= PROTOCOL VERSIONING =============

@versioning_router.get("/protocols/{category_id}/versions")
async def get_protocol_versions(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Get all versions of a protocol"""
    versions = await db.protocol_versions.find(
        {"category_id": category_id, "user_id": user.user_id},
        {"_id": 0}
    ).sort("version", -1).to_list(50)
    
    return {"versions": versions}

@versioning_router.post("/protocols/{category_id}/versions")
async def create_protocol_version(
    category_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Create a new version of a protocol"""
    # Get current protocol
    category = await db.categories.find_one(
        {"category_id": category_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Get latest version number
    latest = await db.protocol_versions.find_one(
        {"category_id": category_id},
        sort=[("version", -1)]
    )
    
    new_version = (latest["version"] + 1) if latest else 1
    
    data = await request.json()
    
    version_doc = {
        "version_id": f"ver_{uuid.uuid4().hex[:12]}",
        "category_id": category_id,
        "user_id": user.user_id,
        "version": new_version,
        "protocol": data.get("protocol", category["protocol"]),
        "name": data.get("name", category["name"]),
        "changelog": data.get("changelog", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.protocol_versions.insert_one(version_doc)
    version_doc.pop("_id", None)
    
    # Update main protocol if requested
    if data.get("update_main", True):
        await db.categories.update_one(
            {"category_id": category_id},
            {"$set": {
                "protocol": version_doc["protocol"],
                "name": version_doc["name"],
                "current_version": new_version,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    return version_doc

@versioning_router.post("/protocols/{category_id}/revert/{version}")
async def revert_protocol_version(
    category_id: str,
    version: int,
    user: User = Depends(require_auth)
):
    """Revert a protocol to a specific version"""
    version_doc = await db.protocol_versions.find_one(
        {"category_id": category_id, "version": version, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not version_doc:
        raise HTTPException(status_code=404, detail="Version not found")
    
    await db.categories.update_one(
        {"category_id": category_id},
        {"$set": {
            "protocol": version_doc["protocol"],
            "name": version_doc["name"],
            "current_version": version,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": f"Reverted to version {version}"}

@versioning_router.get("/protocols/export/{category_id}")
async def export_protocol(
    category_id: str,
    user: User = Depends(require_auth)
):
    """Export a protocol with all versions"""
    category = await db.categories.find_one(
        {"category_id": category_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not category:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    versions = await db.protocol_versions.find(
        {"category_id": category_id},
        {"_id": 0}
    ).sort("version", 1).to_list(100)
    
    export_data = {
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "protocol": category,
        "versions": versions
    }
    
    return export_data

@versioning_router.post("/protocols/import")
async def import_protocol(
    request: Request,
    user: User = Depends(require_auth)
):
    """Import a protocol from export data"""
    data = await request.json()
    
    protocol_data = data.get("protocol", {})
    
    # Create new category
    new_category_id = f"cat_{uuid.uuid4().hex[:12]}"
    new_category = {
        "category_id": new_category_id,
        "user_id": user.user_id,
        "name": protocol_data.get("name", "Imported Protocol"),
        "protocol": protocol_data.get("protocol", ""),
        "parent_id": None,
        "is_public": False,
        "price": 0.0,
        "sales_count": 0,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(new_category)
    new_category.pop("_id", None)
    
    # Import versions if present
    versions = data.get("versions", [])
    for v in versions:
        v["version_id"] = f"ver_{uuid.uuid4().hex[:12]}"
        v["category_id"] = new_category_id
        v["user_id"] = user.user_id
        await db.protocol_versions.insert_one(v)
    
    return {"message": "Protocol imported", "category": new_category}

# ============= APP BRANDING =============

@branding_router.get("/info")
async def get_app_branding():
    """Get app branding information"""
    return {
        "app_name": "InfoPilot Explorer",
        "tagline": "First in Flight with Monetization of Searches",
        "company": "Top Pilot Enterprises, Inc.",
        "ceo": "John Selman",
        "location": "Brunswick, Maine",
        "contact": {
            "email": "JJSpilot24@gmail.com",
            "phone": "(207) 522-0894"
        },
        "icon_description": {
            "primary": "F/A-18C Hornet schematic (top-down view)",
            "secondary": "S-3 Viking side view",
            "colors": ["#007AFF", "#34C759", "#FFD60A"],
            "style": "Military aviation technical drawing with modern gradient overlays"
        },
        "app_stores": {
            "ios": {
                "name": "InfoJet",
                "store": "Apple App Store",
                "icon": "F/A-18C Hornet silhouette",
                "url": "https://apps.apple.com/app/infojet"
            },
            "android": {
                "name": "InfoPilot Explorer",
                "store": "Google Play Store", 
                "icon": "S-3 Viking with data streams",
                "url": "https://play.google.com/store/apps/details?id=com.infopilot.explorer"
            }
        },
        "slogan_variants": [
            "First in Flight with Monetization of Searches",
            "Your 3D View of the Internet",
            "Search Smarter, Discover More",
            "The Information Exchange Social Network"
        ],
        "legal_notices": {
            "copyright": "© 2025-2026 Top Pilot Enterprises, Inc.",
            "age_requirement": "21+ years old",
            "trademark": "InfoPilot Explorer™, InfoJet™, InfoJet 2.0™ are trademarks of Top Pilot Enterprises, Inc."
        }
    }

@branding_router.get("/icons")
async def get_app_icons():
    """Get app icon specifications"""
    return {
        "primary_icon": {
            "name": "FA-18C Hornet",
            "description": "Top-down schematic view of F/A-18C Hornet fighter jet",
            "style": "Technical blueprint with gradient overlay",
            "colors": {
                "primary": "#007AFF",
                "secondary": "#34C759",
                "accent": "#FFD60A",
                "background": "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)"
            },
            "symbolism": "Speed, precision, cutting-edge technology"
        },
        "secondary_icon": {
            "name": "S-3 Viking",
            "description": "Side profile of S-3 Viking aircraft",
            "style": "Minimalist silhouette with data visualization elements",
            "colors": {
                "primary": "#007AFF",
                "glow": "#34C759"
            },
            "symbolism": "Information gathering, surveillance, data collection"
        },
        "favicon": {
            "description": "Simplified jet silhouette",
            "sizes": [16, 32, 48, 64, 128, 256],
            "format": "SVG with PNG fallbacks"
        },
        "app_store_icons": {
            "ios": {
                "size": "1024x1024",
                "corners": "rounded",
                "background": "gradient"
            },
            "android": {
                "size": "512x512",
                "adaptive": True,
                "foreground": "jet silhouette",
                "background": "gradient"
            }
        }
    }

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
api_router.include_router(polls_router)
api_router.include_router(quotes_router)
api_router.include_router(themes_router)
api_router.include_router(analytics_router)
api_router.include_router(promotions_router)
api_router.include_router(reports_router)
api_router.include_router(payments_router)
api_router.include_router(legal_router)
api_router.include_router(templates_router)
api_router.include_router(heatmap_router)
api_router.include_router(collab_router)
api_router.include_router(versioning_router)
api_router.include_router(branding_router)

app.include_router(api_router)

# ============= CORS =============

# Get allowed origins from environment or use defaults
cors_origins_env = os.environ.get("CORS_ORIGINS", "")
if cors_origins_env == "*":
    # For wildcard, we need to dynamically allow origins when credentials are used
    allowed_origins = [
        "https://search-companion-1.preview.emergentagent.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
else:
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] or [
        "https://search-companion-1.preview.emergentagent.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
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
