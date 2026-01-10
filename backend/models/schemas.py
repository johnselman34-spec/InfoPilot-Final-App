"""Pydantic models for InfoPilot Explorer API"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============================================
# USER MODELS
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

# ============================================
# PROTOCOL/CATEGORY MODELS
# ============================================

class ProtocolCreate(BaseModel):
    """InfoPilot 2.0 Protocol - Boolean search syntax"""
    protocol_string: str  # e.g., "(word1 or word2) & (word3)+ & (word4)^"

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    protocol: ProtocolCreate
    parent_id: Optional[str] = None  # For subcategories
    is_public: bool = True
    for_sale: bool = False  # Whether protocol can be purchased
    price: Optional[float] = Field(None, ge=0.75, le=2.99)  # Price range $0.75-$2.99

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    protocol_string: Optional[str] = None
    is_public: Optional[bool] = None
    for_sale: Optional[bool] = None
    price: Optional[float] = Field(None, ge=0.75, le=2.99)

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
    created_at: datetime

# ============================================
# PROTOCOL PURCHASE MODELS
# ============================================

class ProtocolPurchase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    buyer_id: str
    seller_id: str
    category_id: str
    amount: float
    status: str  # pending, completed
    created_at: str

# ============================================
# RECOMMENDATION MODELS
# ============================================

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

# ============================================
# MESSAGING MODELS
# ============================================

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

# ============================================
# SEARCH MODELS
# ============================================

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

class UltimateSearchPageSettings(BaseModel):
    page_name: str = "My Ultimate Search"
    photos: List[str] = []  # URLs of uploaded photos (max 26)

class UpdatePageSettingsRequest(BaseModel):
    page_name: Optional[str] = None

class PhotoUploadResponse(BaseModel):
    success: bool
    photo_url: str
    message: str

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

# ============================================
# ADMIN MODELS
# ============================================

# Blocked words list
DEFAULT_BLOCKED_WORDS = [
    "child", "children", "boy", "girl", "teen", "young", "minor", "kid", "kids",
    "porn", "xxx", "nude", "naked", "sex", "fuck", "shit", "damn", "ass", "bitch"
]

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

# ============================================
# PAYMENT MODELS
# ============================================

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
# SOCIAL FEATURES MODELS
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
# CONSTANTS
# ============================================

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
    
    # Marketplace badges
    "first_sale": {"name": "First Sale", "icon": "💰", "description": "Made your first protocol sale", "threshold": 1, "type": "sales"},
    "seller_bronze": {"name": "Bronze Seller", "icon": "🥉", "description": "Made 5 sales", "threshold": 5, "type": "sales"},
    "seller_silver": {"name": "Silver Seller", "icon": "🥈", "description": "Made 10 sales", "threshold": 10, "type": "sales"},
    "seller_gold": {"name": "Gold Seller", "icon": "🥇", "description": "Made 25 sales", "threshold": 25, "type": "sales"},
    
    # Collector badges
    "collector_novice": {"name": "Collector", "icon": "🛒", "description": "Purchased your first protocol", "threshold": 1, "type": "purchases"},
    "collector_avid": {"name": "Avid Collector", "icon": "📚", "description": "Purchased 10 protocols", "threshold": 10, "type": "purchases"},
}

# Shopify verification model
class VerifyPurchaseRequest(BaseModel):
    order_confirmation: str
