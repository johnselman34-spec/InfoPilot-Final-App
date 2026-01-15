"""
InfoPilot Explorer - Pydantic Schemas
All data models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== USER MODELS ====================

class UserCreate(BaseModel):
    email: str
    username: str
    password: Optional[str] = None
    callsign: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    callsign: Optional[str] = None
    is_admin: bool = False
    subscription_active: bool = False

class GoogleAuthRequest(BaseModel):
    email: str
    google_id: str
    name: Optional[str] = None
    picture: Optional[str] = None


# ==================== CATEGORY MODELS ====================

class CategoryCreate(BaseModel):
    name: str
    protocol: str
    parent_id: Optional[str] = None
    is_public: bool = False

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    protocol: Optional[str] = None
    is_public: Optional[bool] = None
    price: Optional[float] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    protocol: str
    user_id: str
    parent_id: Optional[str] = None
    is_public: bool = False
    price: Optional[float] = None
    level: int = 0
    created_at: datetime


# ==================== SEARCH MODELS ====================

class SearchRequest(BaseModel):
    query: str

class CollateRequest(BaseModel):
    category_id: str
    aggregation: str = "default"
    page: int = 1

class ProtocolValidateRequest(BaseModel):
    protocol: str


# ==================== MARKETPLACE MODELS ====================

class MarketplaceProtocolCreate(BaseModel):
    name: str
    description: str
    protocol: str
    price: float = Field(ge=0.0, le=99.99)  # Allow FREE ($0.00) protocols!
    category: str = "General"
    tags: List[str] = []
    preview_results: int = 3  # Number of sample results to show

class MarketplaceProtocolResponse(BaseModel):
    id: str
    name: str
    description: str
    protocol: str
    price: float
    category: str
    tags: List[str]
    creator_id: str
    creator_name: str
    total_sales: int = 0
    total_revenue: float = 0.0
    rating: float = 0.0
    review_count: int = 0
    created_at: datetime
    is_featured: bool = False

class MarketplacePurchase(BaseModel):
    protocol_id: str
    payment_id: str  # PayPal transaction ID

class MarketplaceSubscription(BaseModel):
    plan: str  # "monthly" or "yearly"
    payment_id: str

class ProtocolReview(BaseModel):
    protocol_id: str
    rating: int = Field(ge=1, le=5)
    review: Optional[str] = None


# ==================== NEWSLETTER MODELS ====================

class NewsletterRequest(BaseModel):
    subject: Optional[str] = None
    content_type: str = "auto"  # auto, book_promo, app_features, custom
    custom_content: Optional[str] = None

class NewsletterSchedule(BaseModel):
    enabled: bool
    day_of_week: int = 0  # 0=Monday
    hour: int = 9
    timezone: str = "UTC"


# ==================== SETTINGS MODELS ====================

class SettingUpdate(BaseModel):
    key: str
    value: Any


# ==================== SOCIAL MODELS ====================

class GroupCreate(BaseModel):
    name: str
    description: str
    is_private: bool = False

class PageCreate(BaseModel):
    name: str
    description: str
    category: str = "General"

class PostCreate(BaseModel):
    content: str
    group_id: Optional[str] = None
    page_id: Optional[str] = None

class CommentCreate(BaseModel):
    content: str
    post_id: str


# ==================== ARTICLE MODELS ====================

class ArticleResponse(BaseModel):
    id: str
    url: str
    title: str
    snippet: Optional[str] = None
    content: Optional[str] = None
    article_type: str = "Unknown"
    root_domain: Optional[str] = None
    categories: List[str] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
