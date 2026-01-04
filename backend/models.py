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
