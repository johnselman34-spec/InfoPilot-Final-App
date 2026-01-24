"""
Pydantic models for InfoPilot Explorer
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid

from .enums import DocumentType


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


# Group Models
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupPost(BaseModel):
    content: str


# Page Models
class PageCreate(BaseModel):
    name: str
    description: Optional[str] = None


# Chat Models
class MessageCreate(BaseModel):
    recipient_id: str
    content: str


class RoomCreate(BaseModel):
    name: str
    members: List[str] = []


# Poll Models
class PollCreate(BaseModel):
    question: str
    options: List[str]
    context: str = "usp"  # usp, groups, pages
    context_id: Optional[str] = None


# Report Models
class ReportCreate(BaseModel):
    title: str
    content: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    images: List[str] = []
    category_id: Optional[str] = None


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    images: Optional[List[str]] = None


# Template Models
class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    protocol: str
    is_public: bool = True


# Session Models
class SessionCreate(BaseModel):
    name: str
    description: Optional[str] = None


# Subscription Models
class SubscriptionVerify(BaseModel):
    payment_id: str
    amount: float


# Stripe Models
class CheckoutRequest(BaseModel):
    price: float
    plan_type: str = "monthly"
