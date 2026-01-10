"""Admin routes for InfoPilot Explorer"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

from utils.database import db
from utils.auth import require_admin
from models.schemas import AdminSettings, DEFAULT_BLOCKED_WORDS

router = APIRouter(prefix="/admin", tags=["Admin"])

# ============================================
# PYDANTIC MODELS
# ============================================

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
    user_max_results_limit: Optional[int] = None
    unpaid_user_search_pages: Optional[int] = None
    paid_user_search_pages: Optional[int] = None

class DatabaseLimitsUpdate(BaseModel):
    user_max_results_limit: int = Field(..., ge=100, le=10000)

class SearchPagesConfigUpdate(BaseModel):
    unpaid_user_search_pages: int = Field(..., ge=1, le=99)
    paid_user_search_pages: int = Field(..., ge=1, le=99)

class SubscriptionConfigUpdate(BaseModel):
    subscription_price: float = Field(..., ge=0.01)
    regular_price: float = Field(..., ge=0.01)

# ============================================
# HELPER FUNCTIONS
# ============================================

async def get_admin_settings() -> AdminSettings:
    """Get admin settings from database or return defaults"""
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if settings:
        settings.pop("_id", None)
        return AdminSettings(**settings)
    return AdminSettings()

async def save_admin_settings(settings: AdminSettings):
    """Save admin settings to database"""
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$set": settings.model_dump()},
        upsert=True
    )

# ============================================
# ADMIN ROUTES
# ============================================

@router.get("/settings")
async def get_settings(user: dict = Depends(require_admin)):
    """Get all admin settings"""
    settings = await get_admin_settings()
    return settings.model_dump()

@router.put("/settings")
async def update_settings(data: AdminSettingsUpdate, user: dict = Depends(require_admin)):
    """Update admin settings"""
    settings = await get_admin_settings()
    
    for field, value in data.model_dump().items():
        if value is not None:
            setattr(settings, field, value)
    
    await save_admin_settings(settings)
    return {"message": "Settings updated", "settings": settings.model_dump()}

@router.get("/database-limits")
async def get_database_limits(user: dict = Depends(require_admin)):
    """Get database limits configuration"""
    settings = await get_admin_settings()
    return {
        "user_max_results_limit": settings.user_max_results_limit,
        "current_default": 4000,
        "min": 100,
        "max": 10000
    }

@router.put("/database-limits")
async def update_database_limits(data: DatabaseLimitsUpdate, user: dict = Depends(require_admin)):
    """Update database limits"""
    settings = await get_admin_settings()
    settings.user_max_results_limit = data.user_max_results_limit
    await save_admin_settings(settings)
    return {
        "message": "Database limits updated",
        "user_max_results_limit": settings.user_max_results_limit
    }

@router.get("/search-pages-config")
async def get_search_pages_config(user: dict = Depends(require_admin)):
    """Get search pages configuration for paid/unpaid users"""
    settings = await get_admin_settings()
    return {
        "unpaid_user_search_pages": settings.unpaid_user_search_pages,
        "paid_user_search_pages": settings.paid_user_search_pages,
        "is_app_free": settings.is_app_free,
        "free_threshold": 40,
        "min_pages": 1,
        "max_pages": 99
    }

@router.put("/search-pages-config")
async def update_search_pages_config(data: SearchPagesConfigUpdate, user: dict = Depends(require_admin)):
    """Update search pages configuration"""
    settings = await get_admin_settings()
    settings.unpaid_user_search_pages = data.unpaid_user_search_pages
    settings.paid_user_search_pages = data.paid_user_search_pages
    await save_admin_settings(settings)
    
    return {
        "message": "Search pages configuration updated",
        "unpaid_user_search_pages": settings.unpaid_user_search_pages,
        "paid_user_search_pages": settings.paid_user_search_pages,
        "is_app_free": settings.is_app_free
    }

@router.get("/subscription/config")
async def get_subscription_config(user: dict = Depends(require_admin)):
    """Get subscription pricing configuration"""
    settings = await get_admin_settings()
    return {
        "subscription_price": settings.subscription_price,
        "regular_price": settings.regular_price
    }

@router.put("/subscription/config")
async def update_subscription_config(data: SubscriptionConfigUpdate, user: dict = Depends(require_admin)):
    """Update subscription pricing"""
    settings = await get_admin_settings()
    settings.subscription_price = data.subscription_price
    settings.regular_price = data.regular_price
    await save_admin_settings(settings)
    
    return {
        "message": "Subscription pricing updated",
        "subscription_price": settings.subscription_price,
        "regular_price": settings.regular_price
    }

@router.get("/users")
async def get_all_users(user: dict = Depends(require_admin)):
    """Get all users for admin management"""
    users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0}
    ).to_list(500)
    return {"users": users}

@router.post("/users/{user_id}/make-admin")
async def make_user_admin(user_id: str, user: dict = Depends(require_admin)):
    """Make a user an admin"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_admin": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User is now an admin"}

@router.post("/users/{user_id}/remove-admin")
async def remove_user_admin(user_id: str, user: dict = Depends(require_admin)):
    """Remove admin status from a user"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_admin": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Admin status removed"}

@router.post("/users/{user_id}/set-paid")
async def set_user_paid(user_id: str, user: dict = Depends(require_admin)):
    """Set a user as paid subscriber"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_paid": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User is now a paid subscriber"}

@router.post("/users/{user_id}/remove-paid")
async def remove_user_paid(user_id: str, user: dict = Depends(require_admin)):
    """Remove paid status from a user"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_paid": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Paid status removed"}

@router.delete("/users/{user_id}/clear-results")
async def clear_user_results(user_id: str, user: dict = Depends(require_admin)):
    """Clear all search results for a specific user"""
    result = await db.search_results.delete_many({"user_id": user_id})
    return {
        "message": f"Cleared {result.deleted_count} results for user",
        "deleted_count": result.deleted_count
    }

@router.get("/statistics")
async def get_admin_statistics(user: dict = Depends(require_admin)):
    """Get comprehensive admin statistics"""
    total_users = await db.users.count_documents({})
    paid_users = await db.users.count_documents({"is_paid": True})
    total_categories = await db.categories.count_documents({})
    public_categories = await db.categories.count_documents({"is_public": True})
    total_results = await db.search_results.count_documents({})
    total_messages = await db.messages.count_documents({})
    total_groups = await db.groups.count_documents({})
    total_pages = await db.pages.count_documents({})
    
    return {
        "users": {
            "total": total_users,
            "paid": paid_users,
            "free": total_users - paid_users
        },
        "categories": {
            "total": total_categories,
            "public": public_categories,
            "private": total_categories - public_categories
        },
        "content": {
            "search_results": total_results,
            "messages": total_messages,
            "groups": total_groups,
            "pages": total_pages
        }
    }
