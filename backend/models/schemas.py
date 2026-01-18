"""
InfoPilot Explorer - Pydantic Models/Schemas
All data models used across the application
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid


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
    upgrade_message: str = "🚨 Pay-as-you-go promotion is only while supplies last!"
    phd_protocol: str = "(Ph.D. or PhD or D.Phil. or Dr.)"
    phd_min_occurrences: int = 3
    phd_min_words: int = 1500
    informative_protocol: str = "(there are or there is) & (may have or might have)"
    news_protocol: str = "(news) & (news or story)"
    news_min_occurrences: int = 3
    blog_min_occurrences: int = 3
    personal_report_min_i: int = 3
    personal_report_min_words: int = 75
    banned_words: List[str] = []
