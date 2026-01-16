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
        {"key": "search_collate_limit", "value": 100, "description": "Max results per Search & Collate (1-100)"},
        {"key": "match_threshold", "value": 70, "description": "Protocol match threshold % (50-100) - Higher = stricter matching"},
        {"key": "deep_search_queries", "value": 8, "description": "Number of query variations for deep search (3-15)"},
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
        # Promotional Messages
        {"key": "upgrade_promo_title", "value": "Limited Time Offer!", "description": "Title for upgrade promotion"},
        {"key": "upgrade_promo_message", "value": "Pay-as-you-go pricing while supplies last! We're testing our business model - Google Maps API, AI Search subscriptions, and server costs are expensive. Your support keeps InfoPilot running!", "description": "Promotional message near upgrade button"},
        {"key": "show_cost_disclaimer", "value": True, "description": "Show API cost disclaimer to users"},
        {"key": "cost_disclaimer_text", "value": "Maintaining this app is expensive - API subscriptions for Google, AI services, and map data cost real money. Thank you for supporting InfoPilot!", "description": "Cost disclaimer text"},
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


# ==================== ADMIN MODERATION ====================

@router.post("/users/{user_id}/ban", response_model=dict)
async def admin_ban_user(user_id: str, data: dict = {}, admin = Depends(require_admin)):
    """Admin: Ban a user from the entire platform"""
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    reason = data.get("reason", "Violation of User Agreement")
    personal_note = data.get("personal_note", "")
    
    # Update user status
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "is_banned": True,
            "banned_at": datetime.utcnow(),
            "banned_by": str(admin["_id"]),
            "ban_reason": reason,
            "ban_note": personal_note
        }}
    )
    
    # Remove from all groups
    await db.groups.update_many(
        {"members": user_id},
        {"$pull": {"members": user_id, "admins": user_id, "moderators": user_id}}
    )
    
    # Remove from all pages
    await db.pages.update_many(
        {"followers": user_id},
        {"$pull": {"followers": user_id, "admins": user_id}}
    )
    
    # Log the action
    await db.admin_actions.insert_one({
        "action": "ban_user",
        "target_user_id": user_id,
        "target_username": target_user.get("username"),
        "admin_id": str(admin["_id"]),
        "admin_username": admin.get("username"),
        "reason": reason,
        "personal_note": personal_note,
        "created_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "message": f"User {target_user.get('username')} has been banned from the platform",
        "reason": reason
    }


@router.post("/users/{user_id}/unban", response_model=dict)
async def admin_unban_user(user_id: str, admin = Depends(require_admin)):
    """Admin: Unban a user"""
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_banned": False}, "$unset": {"banned_at": "", "banned_by": "", "ban_reason": "", "ban_note": ""}}
    )
    
    await db.admin_actions.insert_one({
        "action": "unban_user",
        "target_user_id": user_id,
        "target_username": target_user.get("username"),
        "admin_id": str(admin["_id"]),
        "admin_username": admin.get("username"),
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": f"User {target_user.get('username')} has been unbanned"}


@router.post("/users/{user_id}/mute", response_model=dict)
async def admin_mute_user(user_id: str, data: dict = {}, admin = Depends(require_admin)):
    """Admin: Mute a user platform-wide (can't post, comment, or chat)"""
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    duration_hours = data.get("duration_hours", 24)
    reason = data.get("reason", "")
    personal_note = data.get("personal_note", "")
    
    muted_until = datetime.utcnow() + timedelta(hours=duration_hours)
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "is_muted": True,
            "muted_until": muted_until,
            "muted_by": str(admin["_id"]),
            "mute_reason": reason,
            "mute_note": personal_note
        }}
    )
    
    await db.admin_actions.insert_one({
        "action": "mute_user",
        "target_user_id": user_id,
        "target_username": target_user.get("username"),
        "admin_id": str(admin["_id"]),
        "admin_username": admin.get("username"),
        "duration_hours": duration_hours,
        "muted_until": muted_until,
        "reason": reason,
        "personal_note": personal_note,
        "created_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "message": f"User {target_user.get('username')} has been muted for {duration_hours} hours",
        "muted_until": muted_until.isoformat()
    }


@router.post("/users/{user_id}/unmute", response_model=dict)
async def admin_unmute_user(user_id: str, admin = Depends(require_admin)):
    """Admin: Unmute a user"""
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_muted": False}, "$unset": {"muted_until": "", "muted_by": "", "mute_reason": "", "mute_note": ""}}
    )
    
    return {"success": True, "message": f"User {target_user.get('username')} has been unmuted"}


@router.delete("/users/{user_id}", response_model=dict)
async def admin_delete_user(user_id: str, data: dict = {}, admin = Depends(require_admin)):
    """Admin: Delete a user and all their data"""
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Cannot delete admin users")
    
    reason = data.get("reason", "Account removed")
    personal_note = data.get("personal_note", "")
    
    # Log before deletion
    await db.admin_actions.insert_one({
        "action": "delete_user",
        "target_user_id": user_id,
        "target_username": target_user.get("username"),
        "target_email": target_user.get("email"),
        "admin_id": str(admin["_id"]),
        "admin_username": admin.get("username"),
        "reason": reason,
        "personal_note": personal_note,
        "created_at": datetime.utcnow()
    })
    
    # Remove from groups and pages
    await db.groups.update_many({}, {"$pull": {"members": user_id, "admins": user_id, "moderators": user_id}})
    await db.pages.update_many({}, {"$pull": {"followers": user_id, "admins": user_id}})
    
    # Delete user's content
    await db.search_results.delete_many({"user_id": user_id})
    await db.categories.delete_many({"user_id": user_id})
    await db.posts.delete_many({"user_id": user_id})
    
    # Finally delete the user
    await db.users.delete_one({"_id": ObjectId(user_id)})
    
    return {
        "success": True,
        "message": f"User {target_user.get('username')} and all their data have been deleted",
        "reason": reason
    }


@router.get("/moderation/actions", response_model=dict)
async def get_moderation_actions(limit: int = 50, admin = Depends(require_admin)):
    """Get recent admin moderation actions"""
    actions = await db.admin_actions.find().sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "actions": [{
            "id": str(a["_id"]),
            "action": a.get("action"),
            "target_user_id": a.get("target_user_id"),
            "target_username": a.get("target_username"),
            "admin_username": a.get("admin_username"),
            "reason": a.get("reason", ""),
            "personal_note": a.get("personal_note", ""),
            "created_at": a.get("created_at").isoformat() if a.get("created_at") else None
        } for a in actions]
    }


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



# ==================== AI NEWSLETTER OPTIMIZATION ====================

@router.get("/newsletter/ai-optimize", response_model=dict)
async def get_ai_newsletter_optimization(user = Depends(require_admin)):
    """Get AI-powered newsletter schedule optimization recommendations"""
    from services.triweekly_newsletter import ai_optimize_newsletter_times
    
    result = await ai_optimize_newsletter_times()
    return result


@router.post("/newsletter/apply-ai-schedule", response_model=dict)
async def apply_ai_newsletter_schedule(data: dict, user = Depends(require_admin)):
    """Apply AI-recommended newsletter schedule"""
    from services.triweekly_newsletter import apply_ai_optimized_schedule
    
    recommendations = data.get("recommendations", {})
    if not recommendations:
        raise HTTPException(status_code=400, detail="No recommendations provided")
    
    result = await apply_ai_optimized_schedule(recommendations)
    return result


@router.get("/newsletter/performance", response_model=dict)
async def get_newsletter_performance(user = Depends(require_admin)):
    """Get newsletter performance data for analysis"""
    from services.triweekly_newsletter import get_newsletter_performance_data
    
    data = await get_newsletter_performance_data()
    return data
