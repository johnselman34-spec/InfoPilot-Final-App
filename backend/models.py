from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: Optional[str] = None
    password_hash: str
    profile_photo: Optional[str] = None  # base64 encoded
    subscription_status: str = "free"  # free, paid
    is_public: bool = False
    friends_public: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    friends: List[str] = []  # list of user IDs
    banned: bool = False

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    profile_photo: Optional[str] = None
    is_public: Optional[bool] = None
    friends_public: Optional[bool] = None

# Category Models
class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    protocol: str  # InfoJet 2.0 format
    parent_id: Optional[str] = None
    level: int = 0
    is_public: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class CategoryCreate(BaseModel):
    name: str
    protocol: str
    parent_id: Optional[str] = None
    is_public: bool = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    protocol: Optional[str] = None
    is_public: Optional[bool] = None

# Search Result Models
class SearchResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category_ids: List[str] = []
    url: str
    title: str
    snippet: str
    article_type: str  # Informative, PhD, Blog, Forum, News, Personal Report
    root_domain: str
    year: Optional[int] = None
    country: Optional[str] = None
    state: Optional[str] = None
    content_metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes: int = 0
    loves: int = 0
    funnys: int = 0
    sads: int = 0
    cautions: int = 0
    spams: int = 0
    bests: int = 0

class ReactionUpdate(BaseModel):
    reaction_type: str  # like, love, funny, sad, caution, spam, best

# Admin Settings Models
class AdminSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    search_results_per_page: int = 20
    unpaid_page_limit: int = 1
    daily_collate_limit: int = 10
    informative_protocol: str = "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)"
    news_protocol: str = "(news) & (news or story or news story) & (news or story or news story)"
    phd_min_words: int = 1500
    phd_occurrences: int = 3
    blog_occurrences: int = 3
    personal_report_occurrences: int = 3
    personal_report_min_words: int = 75
    banned_words: List[str] = []
    banned_users: List[str] = []
    banned_urls: List[str] = []
    youtube_tutorial_url: str = ""
    protocol_examples: List[str] = []

class AdminSettingsUpdate(BaseModel):
    search_results_per_page: Optional[int] = None
    unpaid_page_limit: Optional[int] = None
    daily_collate_limit: Optional[int] = None
    banned_words: Optional[List[str]] = None
    banned_users: Optional[List[str]] = None
    banned_urls: Optional[List[str]] = None

# Collate Request Models
class CollateRequest(BaseModel):
    category_id: str
    search_query: str  # from Google search bar

# Message Models
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False

class MessageCreate(BaseModel):
    receiver_id: str
    content: str

# Newsletter Models
class NewsletterArticle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NewsletterArticleCreate(BaseModel):
    title: str
    content: str

# Marketplace Models - Updated price range $1.00 to $99.00
class MarketplaceProtocol(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category_id: str
    user_id: str
    price: float = Field(ge=0, le=99.00)  # 0 = Pay What You Want
    description: Optional[str] = None
    is_for_sale: bool = True
    purchase_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[Dict[str, Any]] = None  # {latitude, longitude, city, country}
    pay_what_you_want: bool = False

class MarketplaceSell(BaseModel):
    category_id: str
    price: float = Field(ge=0, le=99.00)  # 0 = Pay What You Want
    description: Optional[str] = None
    pay_what_you_want: bool = False

class MarketplacePurchase(BaseModel):
    protocol_id: str
    offer_price: Optional[float] = None  # For Pay What You Want

class PayoutRequest(BaseModel):
    paypal_email: str

# Transaction Models
class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    buyer_id: str
    seller_id: str
    protocol_id: str
    amount: float
    seller_amount: float  # 90%
    platform_amount: float  # 10%
    status: str = "pending"  # pending, completed, failed
    paypal_transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Statistics Models
class StatisticsData(BaseModel):
    total_users: int = 0
    total_protocols: int = 0
    total_searches: int = 0
    total_sales: int = 0
    total_revenue: float = 0.0
    top_sellers: List[Dict[str, Any]] = []
    top_protocols: List[Dict[str, Any]] = []
    country_breakdown: Dict[str, int] = {}
    content_type_breakdown: Dict[str, int] = {}

# Gamification Models
class Badge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: str
    category: str  # sales, searches, social, milestone
    requirement: int  # Number needed to earn
    rarity: str = "common"  # common, rare, epic, legendary

class UserBadge(BaseModel):
    user_id: str
    badge_id: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)

class LeaderboardEntry(BaseModel):
    user_id: str
    username: str
    profile_photo: Optional[str] = None
    sales_count: int = 0
    revenue: float = 0.0
    protocols_created: int = 0
    badges_count: int = 0

# Poll Models - For Groups, Pages, and Ultimate Search
class PollOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    image_url: Optional[str] = None  # Optional image for the option
    votes: int = 0

class Poll(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str
    title: str
    description: Optional[str] = None
    options: List[PollOption] = []
    context_type: str  # "group", "page", "ultimate_search"
    context_id: str  # ID of the group, page, or user's ultimate search
    is_active: bool = True
    allows_multiple: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    voters: List[str] = []  # List of user IDs who have voted

class PollCreate(BaseModel):
    title: str
    description: Optional[str] = None
    options: List[Dict[str, Any]]  # [{text: str, image_url: Optional[str]}]
    context_type: str
    context_id: str
    allows_multiple: bool = False
    expires_in_hours: Optional[int] = None

class PollVote(BaseModel):
    poll_id: str
    option_ids: List[str]

# Clipboard Copy Tracking
class ClipboardCopy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: str
    user_id: Optional[str] = None
    copied_at: datetime = Field(default_factory=datetime.utcnow)

# Group/Page Admin Privileges
class AdminPrivilege(BaseModel):
    user_id: str
    granted_by: str
    privileges: List[str] = []  # ["create_polls", "moderate_comments", "approve_posts", "manage_members"]
    granted_at: datetime = Field(default_factory=datetime.utcnow)

class Group(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    cover_image: Optional[str] = None
    creator_id: str
    admins: List[AdminPrivilege] = []
    member_ids: List[str] = []
    is_public: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GroupCreate(BaseModel):
    name: str
    description: str
    cover_image: Optional[str] = None
    is_public: bool = True

class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    cover_image: Optional[str] = None
    owner_id: str
    admins: List[AdminPrivilege] = []
    follower_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PageCreate(BaseModel):
    name: str
    description: str
    category: str
    cover_image: Optional[str] = None

# Newsletter with AI Generation
class Newsletter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    content: str  # HTML content
    funny_intro: str  # AI-generated funny intro
    book_promo: str  # Letters to Evelyn promotion
    marketplace_highlights: List[Dict[str, Any]] = []
    sent_to: List[str] = []  # User IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None

# Achievement Badges with Share Feature
class AchievementBadge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    funny_tagline: str  # Funny description for sharing
    icon: str  # Emoji or icon name
    category: str  # "sales", "protocols", "social", "searches", "special"
    requirement_type: str  # "count", "milestone", "special"
    requirement_value: int
    rarity: str = "common"  # common, rare, epic, legendary, mythic
    share_text: str  # Pre-filled text for sharing

class UserAchievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    badge_id: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    shared: bool = False
    share_count: int = 0
