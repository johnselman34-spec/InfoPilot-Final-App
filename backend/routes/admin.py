"""
InfoPilot Explorer - Admin Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Any

from config import db, logger, PAYPAL_PAYMENT_LINK
from routes.auth import get_current_user
from services.email_service import EmailService

router = APIRouter(prefix="/admin", tags=["Admin"])


async def require_admin(user = Depends(get_current_user)):
    """Dependency to require admin access"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/stats", response_model=dict)
async def get_admin_stats(user = Depends(require_admin)):
    """Get admin dashboard statistics"""
    users = await db.users.count_documents({})
    categories = await db.categories.count_documents({})
    search_results = await db.search_results.count_documents({})
    marketplace_protocols = await db.marketplace_protocols.count_documents({"status": "active"})
    marketplace_sales = await db.marketplace_purchases.count_documents({})
    
    # Get recent activity
    recent_users = await db.users.find().sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "users": users,
        "categories": categories,
        "search_results": search_results,
        "marketplace_protocols": marketplace_protocols,
        "marketplace_sales": marketplace_sales,
        "recent_users": [{
            "email": u.get("email", ""),
            "username": u.get("username", ""),
            "created_at": u.get("created_at", datetime.utcnow()).isoformat()
        } for u in recent_users]
    }


@router.get("/settings", response_model=dict)
async def get_settings(user = Depends(require_admin)):
    """Get all admin settings"""
    settings = await db.settings.find().to_list(100)
    return {s["key"]: s.get("value") for s in settings}


@router.post("/settings", response_model=dict)
async def update_setting(data: dict, user = Depends(require_admin)):
    """Update an admin setting"""
    key = data.get("key")
    value = data.get("value")
    
    if not key:
        raise HTTPException(status_code=400, detail="Key is required")
    
    await db.settings.update_one(
        {"key": key},
        {"$set": {"value": value, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    
    return {"success": True, "key": key, "value": value}


@router.post("/settings/init", response_model=dict)
async def init_settings(user = Depends(require_admin)):
    """Initialize default settings"""
    default_settings = [
        {"key": "subscription_price", "value": 0.99, "description": "Subscription price in USD"},
        {"key": "results_per_page", "value": 20, "description": "Search results per page"},
        {"key": "max_search_pages", "value": 99, "description": "Max search pages (1-99)"},
        {"key": "unpaid_max_pages", "value": 1, "description": "Max pages for unpaid users"},
        {"key": "daily_collate_limit", "value": 100, "description": "Max collations per day"},
        {"key": "collation_limit", "value": 40, "description": "Results per Search and Collate (default: 40)"},
        {"key": "allow_multiple_categories", "value": True, "description": "Allow assigning to multiple categories"},
        {"key": "max_category_levels", "value": 100, "description": "Max category hierarchy depth"},
        {"key": "platform_fee_percent", "value": 15, "description": "Platform fee percentage (default: 15%)"},
        {"key": "min_payout_threshold", "value": 1.00, "description": "PayPal minimum payout ($1.00)"},
        {"key": "phd_min_words", "value": 1500, "description": "Min words for Ph.D. classification"},
        {"key": "phd_keyword_count", "value": 3, "description": "Min Ph.D. keywords required"},
        {"key": "tutorial_video_url", "value": "", "description": "YouTube tutorial video URL"},
        {"key": "paypal_link", "value": PAYPAL_PAYMENT_LINK, "description": "PayPal payment link"},
        {"key": "bundle_of_week_id", "value": "", "description": "Featured Bundle of the Week ID"},
        {"key": "maps_free_for_all", "value": True, "description": "Maps are FREE (no premium gate)"},
        # Newsletter Time Settings (Admin Controllable)
        {"key": "newsletter_time_1", "value": "05:42", "description": "Newsletter Time 1 (Morning - HH:MM UTC)"},
        {"key": "newsletter_time_2", "value": "08:37", "description": "Newsletter Time 2 (Mid-Morning - HH:MM UTC)"},
        {"key": "newsletter_time_3", "value": "16:41", "description": "Newsletter Time 3 (Afternoon - HH:MM UTC)"},
        {"key": "newsletter_ai_optimization", "value": True, "description": "AI-optimized newsletter timing for max revenue"},
        # Daily Laugh Goal Settings
        {"key": "default_daily_laugh_goal", "value": 10, "description": "Default daily laugh goal for new users"},
        {"key": "streak_bonus_multiplier", "value": 1.0, "description": "Multiplier for streak bonuses"},
    ]
    
    for setting in default_settings:
        existing = await db.settings.find_one({"key": setting["key"]})
        if not existing:
            await db.settings.insert_one(setting)
    
    return {"message": "Settings initialized", "count": len(default_settings)}


@router.get("/users", response_model=dict)
async def get_users(user = Depends(require_admin)):
    """Get all users"""
    users = await db.users.find().sort("created_at", -1).to_list(500)
    
    return {
        "users": [{
            "id": str(u["_id"]),
            "email": u.get("email", ""),
            "username": u.get("username", ""),
            "is_admin": u.get("is_admin", False),
            "subscription_active": u.get("subscription_active", False),
            "created_at": u.get("created_at", datetime.utcnow()).isoformat()
        } for u in users]
    }


@router.post("/users/{user_id}/admin", response_model=dict)
async def toggle_admin(user_id: str, user = Depends(require_admin)):
    """Toggle admin status for a user"""
    from bson import ObjectId
    
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not target_user.get("is_admin", False)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_admin": new_status}}
    )
    
    return {"success": True, "is_admin": new_status}


# ==================== NEWSLETTER ====================

@router.post("/newsletter/generate", response_model=dict)
async def generate_newsletter(user = Depends(require_admin)):
    """Generate newsletter content using AI"""
    content = await EmailService.generate_newsletter_content()
    return {"content": content}


@router.post("/newsletter/send", response_model=dict)
async def send_newsletter(data: dict, user = Depends(require_admin)):
    """Send newsletter to all users"""
    subject = data.get("subject", f"InfoPilot Weekly Update - {datetime.now().strftime('%B %d, %Y')}")
    content = data.get("content")
    
    if not content:
        content = await EmailService.generate_newsletter_content()
    
    emails = await EmailService.get_subscriber_emails()
    result = await EmailService.send_newsletter(subject, content, emails)
    
    return result


@router.post("/newsletter/test", response_model=dict)
async def send_test_newsletter(data: dict, user = Depends(require_admin)):
    """Send a test newsletter to admin"""
    recipient = data.get("email", user.get("email"))
    result = await EmailService.send_test_email(recipient)
    return result


@router.get("/newsletter/schedule", response_model=dict)
async def get_newsletter_schedule(user = Depends(require_admin)):
    """Get newsletter schedule settings"""
    schedule = await db.settings.find_one({"key": "newsletter_schedule"})
    return schedule.get("value", {
        "enabled": False,
        "day_of_week": 0,
        "hour": 9,
        "timezone": "UTC"
    }) if schedule else {
        "enabled": False,
        "day_of_week": 0,
        "hour": 9,
        "timezone": "UTC"
    }


@router.post("/newsletter/schedule", response_model=dict)
async def update_newsletter_schedule(data: dict, user = Depends(require_admin)):
    """Update newsletter schedule"""
    await db.settings.update_one(
        {"key": "newsletter_schedule"},
        {"$set": {"value": data, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return {"success": True, "schedule": data}
