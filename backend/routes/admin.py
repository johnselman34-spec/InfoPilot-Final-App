"""
InfoPilot Explorer - Admin Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import Any
from bson import ObjectId

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
        {"key": "search_collate_limit", "value": 40, "description": "Max results per Search & Collate (1-100)"},
        {"key": "collation_limit", "value": 40, "description": "Default collations per search (1-100)"},
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
        # Newsletter Time Settings (Admin Controllable) - Tri-weekly at 5:46am, 9:42am, 4:20pm UTC
        {"key": "newsletter_time_1", "value": "05:46", "description": "Newsletter Time 1 (Morning - HH:MM UTC)"},
        {"key": "newsletter_time_2", "value": "09:42", "description": "Newsletter Time 2 (Mid-Morning - HH:MM UTC)"},
        {"key": "newsletter_time_3", "value": "16:20", "description": "Newsletter Time 3 (Afternoon 4:20pm - HH:MM UTC)"},
        {"key": "newsletter_ai_optimization", "value": True, "description": "AI-optimized newsletter timing for max revenue"},
        # Daily Laugh Goal Settings
        {"key": "default_daily_laugh_goal", "value": 10, "description": "Default daily laugh goal for new users"},
        {"key": "streak_bonus_multiplier", "value": 1.0, "description": "Multiplier for streak bonuses"},
        # Unpaid User Price Controls (NEW)
        {"key": "unpaid_price_control_enabled", "value": False, "description": "Enable price limits for unpaid users"},
        {"key": "unpaid_max_protocol_price", "value": 5.00, "description": "Max price unpaid users can charge per protocol ($)"},
        {"key": "unpaid_max_bundle_price", "value": 10.00, "description": "Max price unpaid users can charge per bundle ($)"},
        {"key": "unpaid_can_sell", "value": True, "description": "Allow unpaid users to sell at all"},
        # Global Price Controls (for ALL users)
        {"key": "global_price_control_enabled", "value": False, "description": "Enable price limits for ALL users"},
        {"key": "global_max_protocol_price", "value": 99.99, "description": "Max price ANY user can charge per protocol ($)"},
        {"key": "global_max_bundle_price", "value": 199.99, "description": "Max price ANY user can charge per bundle ($)"},
        {"key": "global_min_protocol_price", "value": 0.00, "description": "Min price for protocols (0 = free allowed)"},
        # Document Type Classification Settings (Admin Controllable)
        {"key": "doctype_phd_min_words", "value": 1500, "description": "Min words for PhD classification"},
        {"key": "doctype_phd_keyword_count", "value": 3, "description": "Min PhD keywords (Ph.D., PhD, D.Phil., Dr.)"},
        {"key": "doctype_phd_protocol", "value": "(Ph.D. or PhD or D.Phil. or Dr.)", "description": "PhD detection protocol"},
        {"key": "doctype_informative_protocol", "value": "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)", "description": "Informative article protocol"},
        {"key": "doctype_news_protocol", "value": "(news) & (news or story or news story) & (news or story or news story)", "description": "News Article detection protocol"},
        {"key": "doctype_news_min_instances", "value": 3, "description": "Min instances for News classification"},
        {"key": "doctype_blog_protocol", "value": "(blog)", "description": "Blog detection protocol"},
        {"key": "doctype_blog_min_instances", "value": 3, "description": "Min 'blog' instances (1 must be in title)"},
        {"key": "doctype_forum_protocol", "value": "(forum)", "description": "Forum detection protocol (must be in title)"},
        {"key": "doctype_personal_collected_protocol", "value": "(I)", "description": "Personal Report detection protocol"},
        {"key": "doctype_personal_min_i_count", "value": 3, "description": "Min 'I' occurrences outside quotes"},
        {"key": "doctype_personal_min_paragraph_words", "value": 75, "description": "Min words in paragraph for Personal Report"},
        {"key": "doctype_auto_categorize", "value": True, "description": "Auto-categorize by document type"},
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



# ==================== UNPAID USER PRICE CONTROLS ====================

@router.get("/unpaid-price-controls", response_model=dict)
async def get_unpaid_price_controls(user = Depends(require_admin)):
    """
    Get current price control settings for unpaid users.
    Feature is OFF by default - must be enabled by admin.
    """
    settings = {}
    keys = ["unpaid_price_control_enabled", "unpaid_max_protocol_price", 
            "unpaid_max_bundle_price", "unpaid_can_sell"]
    
    for key in keys:
        setting = await db.settings.find_one({"key": key})
        if setting:
            settings[key] = setting.get("value")
        else:
            # Defaults
            defaults = {
                "unpaid_price_control_enabled": False,
                "unpaid_max_protocol_price": 5.00,
                "unpaid_max_bundle_price": 10.00,
                "unpaid_can_sell": True
            }
            settings[key] = defaults.get(key)
    
    # Get stats
    unpaid_sellers = await db.users.count_documents({
        "subscription_active": {"$ne": True},
        "marketplace_listings": {"$gt": 0}
    })
    
    return {
        "settings": settings,
        "stats": {
            "unpaid_sellers": unpaid_sellers
        },
        "description": {
            "unpaid_price_control_enabled": "Master toggle for price controls (OFF by default)",
            "unpaid_max_protocol_price": "Maximum price unpaid users can charge per protocol",
            "unpaid_max_bundle_price": "Maximum price unpaid users can charge per bundle",
            "unpaid_can_sell": "Whether unpaid users can sell at all"
        }
    }


@router.put("/unpaid-price-controls", response_model=dict)
async def update_unpaid_price_controls(data: dict, user = Depends(require_admin)):
    """
    Update price control settings for unpaid users.
    """
    allowed_keys = ["unpaid_price_control_enabled", "unpaid_max_protocol_price", 
                    "unpaid_max_bundle_price", "unpaid_can_sell"]
    
    updated = []
    
    for key in allowed_keys:
        if key in data:
            value = data[key]
            
            # Validate price values
            if key in ["unpaid_max_protocol_price", "unpaid_max_bundle_price"]:
                try:
                    value = float(value)
                    if value < 0:
                        raise HTTPException(status_code=400, detail=f"{key} must be >= 0")
                    if value > 99.99:
                        raise HTTPException(status_code=400, detail=f"{key} must be <= 99.99")
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail=f"{key} must be a valid number")
            
            await db.settings.update_one(
                {"key": key},
                {"$set": {"value": value, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            updated.append({"key": key, "value": value})
    
    # Log the change
    await db.admin_audit_log.insert_one({
        "action": "update_unpaid_price_controls",
        "admin_id": str(user["_id"]),
        "admin_email": user.get("email"),
        "changes": updated,
        "created_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "message": "Unpaid user price controls updated",
        "updated": updated
    }


# ==================== GLOBAL PRICE CONTROLS ====================

@router.get("/global-price-controls", response_model=dict)
async def get_global_price_controls(user = Depends(require_admin)):
    """
    Get global price control settings (applies to ALL users).
    """
    keys = ["global_price_control_enabled", "global_max_protocol_price", 
            "global_max_bundle_price", "global_min_protocol_price"]
    
    settings = {}
    defaults = {
        "global_price_control_enabled": False,
        "global_max_protocol_price": 99.99,
        "global_max_bundle_price": 199.99,
        "global_min_protocol_price": 0.00
    }
    
    for key in keys:
        setting = await db.settings.find_one({"key": key})
        if setting:
            settings[key] = setting.get("value")
        else:
            settings[key] = defaults.get(key)
    
    return {
        "settings": settings,
        "description": {
            "global_price_control_enabled": "Master toggle for global price controls (applies to EVERYONE)",
            "global_max_protocol_price": "Maximum price ANY user can charge per protocol",
            "global_max_bundle_price": "Maximum price ANY user can charge per bundle",
            "global_min_protocol_price": "Minimum price for protocols (0 = free allowed)"
        }
    }


@router.put("/global-price-controls", response_model=dict)
async def update_global_price_controls(data: dict, user = Depends(require_admin)):
    """
    Update global price control settings (applies to ALL users).
    """
    allowed_keys = ["global_price_control_enabled", "global_max_protocol_price", 
                    "global_max_bundle_price", "global_min_protocol_price"]
    
    updated = []
    
    for key in allowed_keys:
        if key in data:
            value = data[key]
            
            # Validate price values
            if key in ["global_max_protocol_price", "global_max_bundle_price", "global_min_protocol_price"]:
                try:
                    value = float(value)
                    if value < 0:
                        raise HTTPException(status_code=400, detail=f"{key} must be >= 0")
                    if value > 999.99:
                        raise HTTPException(status_code=400, detail=f"{key} must be <= 999.99")
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail=f"{key} must be a valid number")
            
            await db.settings.update_one(
                {"key": key},
                {"$set": {"value": value, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            updated.append({"key": key, "value": value})
    
    # Log the change
    await db.admin_audit_log.insert_one({
        "action": "update_global_price_controls",
        "admin_id": str(user["_id"]),
        "admin_email": user.get("email"),
        "changes": updated,
        "created_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "message": "Global price controls updated",
        "updated": updated
    }


# ==================== DOCUMENT TYPE CLASSIFICATION SETTINGS ====================

@router.get("/doctype-settings", response_model=dict)
async def get_doctype_settings(user = Depends(require_admin)):
    """
    Get document type classification settings (Admin controllable protocols).
    """
    keys = [
        "doctype_phd_min_words", "doctype_phd_keyword_count", "doctype_phd_protocol",
        "doctype_informative_protocol", "doctype_news_protocol", "doctype_news_min_instances",
        "doctype_blog_protocol", "doctype_blog_min_instances", "doctype_forum_protocol",
        "doctype_personal_collected_protocol", "doctype_personal_min_i_count",
        "doctype_personal_min_paragraph_words", "doctype_auto_categorize"
    ]
    
    defaults = {
        "doctype_phd_min_words": 1500,
        "doctype_phd_keyword_count": 3,
        "doctype_phd_protocol": "(Ph.D. or PhD or D.Phil. or Dr.)",
        "doctype_informative_protocol": "(there are or there is) & (may have or might have or that are) & (this kind or these kinds or this type or these types or it is) & (is easily or of each or less than the or more than or greater than or is more or is less) & (it is)",
        "doctype_news_protocol": "(news) & (news or story or news story) & (news or story or news story)",
        "doctype_news_min_instances": 3,
        "doctype_blog_protocol": "(blog)",
        "doctype_blog_min_instances": 3,
        "doctype_forum_protocol": "(forum)",
        "doctype_personal_collected_protocol": "(I)",
        "doctype_personal_min_i_count": 3,
        "doctype_personal_min_paragraph_words": 75,
        "doctype_auto_categorize": True
    }
    
    settings = {}
    for key in keys:
        setting = await db.settings.find_one({"key": key})
        if setting:
            settings[key] = setting.get("value")
        else:
            settings[key] = defaults.get(key)
    
    return {
        "settings": settings,
        "document_types": [
            {"type": "PhD Informative", "description": "Academic content by credentialed professionals (Ph.D., D.Phil., Dr.)"},
            {"type": "Informative", "description": "Educational content meeting informative protocol criteria"},
            {"type": "InfoPilot Exclusive", "description": "Content written by InfoPilot writers (no rules)"},
            {"type": "InfoBook Exclusive", "description": "Content written by InfoBook writers (no rules)"},
            {"type": "News Article", "description": "Current events and journalism (default fallback)"},
            {"type": "Blog Post", "description": "Personal blogs and opinion pieces"},
            {"type": "Forum", "description": "Discussion boards (forum in title)"},
            {"type": "Personal Report (Organic)", "description": "First-hand reports written by members"},
            {"type": "Personal Report (Collected)", "description": "Extracted personal narratives from articles"},
            {"type": "Academic Paper", "description": "Scholarly research (.edu, journal, research)"},
            {"type": "Government", "description": "Official government documents (.gov)"},
            {"type": "Wiki", "description": "Wikipedia and wiki-based content"},
            {"type": "Video", "description": "Video content (YouTube, Vimeo)"},
            {"type": "PDF Document", "description": "PDF files"},
            {"type": "Webpage", "description": "General web pages (catch-all)"}
        ],
        "description": {
            "doctype_phd_min_words": "Minimum word count for PhD classification",
            "doctype_phd_keyword_count": "Minimum PhD keyword occurrences (Ph.D., PhD, D.Phil., Dr.)",
            "doctype_phd_protocol": "Protocol for detecting PhD credentials",
            "doctype_informative_protocol": "Protocol for detecting Informative articles",
            "doctype_news_protocol": "Protocol for detecting News Articles",
            "doctype_news_min_instances": "Minimum protocol matches for News classification",
            "doctype_blog_protocol": "Protocol for detecting Blog posts (must be in title)",
            "doctype_blog_min_instances": "Minimum 'blog' instances (1 must be in title)",
            "doctype_forum_protocol": "Protocol for detecting Forums (must be in title)",
            "doctype_personal_collected_protocol": "Protocol for detecting Personal Reports",
            "doctype_personal_min_i_count": "Minimum 'I' occurrences outside quotes",
            "doctype_personal_min_paragraph_words": "Minimum words in paragraph for Personal Report",
            "doctype_auto_categorize": "Auto-categorize search results by document type"
        }
    }


@router.put("/doctype-settings", response_model=dict)
async def update_doctype_settings(data: dict, user = Depends(require_admin)):
    """
    Update document type classification settings.
    """
    allowed_keys = [
        "doctype_phd_min_words", "doctype_phd_keyword_count", "doctype_phd_protocol",
        "doctype_informative_protocol", "doctype_news_protocol", "doctype_news_min_instances",
        "doctype_blog_protocol", "doctype_blog_min_instances", "doctype_forum_protocol",
        "doctype_personal_collected_protocol", "doctype_personal_min_i_count",
        "doctype_personal_min_paragraph_words", "doctype_auto_categorize"
    ]
    
    updated = []
    
    for key in allowed_keys:
        if key in data:
            value = data[key]
            
            # Validate numeric values
            if key in ["doctype_phd_min_words", "doctype_phd_keyword_count", 
                       "doctype_news_min_instances", "doctype_blog_min_instances",
                       "doctype_personal_min_i_count", "doctype_personal_min_paragraph_words"]:
                try:
                    value = int(value)
                    if value < 1:
                        raise HTTPException(status_code=400, detail=f"{key} must be >= 1")
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail=f"{key} must be a valid integer")
            
            await db.settings.update_one(
                {"key": key},
                {"$set": {"value": value, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            updated.append({"key": key, "value": value})
    
    # Log the change
    await db.admin_audit_log.insert_one({
        "action": "update_doctype_settings",
        "admin_id": str(user["_id"]),
        "admin_email": user.get("email"),
        "changes": updated,
        "created_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "message": "Document type classification settings updated",
        "updated": updated
    }


# ==================== BULK DOCUMENT TYPE TESTING ====================

@router.post("/doctype-test", response_model=dict)
async def test_document_classification(
    data: dict,
    user = Depends(require_admin)
):
    """
    Test document classification with sample text.
    Paste sample text and see which document type it classifies as.
    Helps verify InfoJet 2.0 protocols before production use.
    """
    title = data.get("title", "")
    content = data.get("content", "")
    url = data.get("url", "")
    
    if not content and not title:
        raise HTTPException(status_code=400, detail="Please provide title and/or content to test")
    
    # Import ArticleClassifier from server
    from server import ArticleClassifier
    
    # Get current settings
    settings = await ArticleClassifier.get_settings()
    
    # Classify the document
    doc_type = ArticleClassifier.classify(title, content, url, settings)
    
    # Provide detailed analysis
    combined = f"{title.lower() if title else ''} {content.lower() if content else ''}"
    word_count = len(content.split()) if content else 0
    
    # Check which protocols match
    protocol_matches = []
    
    # PhD check
    phd_protocol = settings.get("doctype_phd_protocol", "(Ph.D. or PhD or D.Phil. or Dr.)")
    phd_terms = phd_protocol.strip("()").split(" or ")
    phd_matches = sum(1 for term in phd_terms if term.strip().lower() in combined)
    if phd_matches > 0:
        protocol_matches.append({
            "type": "PhD Keywords",
            "matches": phd_matches,
            "required": settings.get("doctype_phd_keyword_count", 3),
            "passed": phd_matches >= settings.get("doctype_phd_keyword_count", 3)
        })
    
    # Informative check
    informative_protocol = settings.get("doctype_informative_protocol", "")
    if informative_protocol:
        groups = informative_protocol.split("&")
        informative_matches = 0
        for group in groups:
            group = group.strip().strip("()")
            terms = [t.strip().lower() for t in group.split(" or ")]
            if any(term in combined for term in terms):
                informative_matches += 1
        protocol_matches.append({
            "type": "Informative",
            "matches": informative_matches,
            "required": len(groups),
            "passed": informative_matches >= len(groups)
        })
    
    # Blog check
    blog_count = combined.count("blog")
    blog_in_title = "blog" in (title.lower() if title else "")
    protocol_matches.append({
        "type": "Blog",
        "matches": blog_count,
        "in_title": blog_in_title,
        "required": settings.get("doctype_blog_min_instances", 3),
        "passed": blog_count >= settings.get("doctype_blog_min_instances", 3) and blog_in_title
    })
    
    # Forum check
    forum_in_title = "forum" in (title.lower() if title else "")
    protocol_matches.append({
        "type": "Forum",
        "in_title": forum_in_title,
        "passed": forum_in_title
    })
    
    # Personal Report check
    import re
    text_no_quotes = re.sub(r'"[^"]*"', '', content) if content else ""
    text_no_quotes = re.sub(r"'[^']*'", '', text_no_quotes)
    i_count = len(re.findall(r'\bI\b', text_no_quotes))
    protocol_matches.append({
        "type": "Personal Report (Collected)",
        "i_count": i_count,
        "required": settings.get("doctype_personal_min_i_count", 3),
        "passed": i_count >= settings.get("doctype_personal_min_i_count", 3)
    })
    
    # News check
    news_count = combined.count("news")
    protocol_matches.append({
        "type": "News Article",
        "matches": news_count,
        "passed": news_count >= settings.get("doctype_news_min_instances", 3) or doc_type == "News Article"
    })
    
    return {
        "classification": doc_type,
        "analysis": {
            "title_provided": bool(title),
            "content_length": len(content) if content else 0,
            "word_count": word_count,
            "url_provided": bool(url)
        },
        "protocol_matches": protocol_matches,
        "settings_used": {
            "phd_min_words": settings.get("doctype_phd_min_words", 1500),
            "phd_keyword_count": settings.get("doctype_phd_keyword_count", 3),
            "blog_min_instances": settings.get("doctype_blog_min_instances", 3),
            "personal_min_i_count": settings.get("doctype_personal_min_i_count", 3),
            "personal_min_paragraph_words": settings.get("doctype_personal_min_paragraph_words", 75),
            "news_min_instances": settings.get("doctype_news_min_instances", 3)
        },
        "message": f"Document classified as: {doc_type}"
    }


# ==================== PAYPAL WALLET ACCUMULATION ====================

@router.get("/paypal-wallets", response_model=dict)
async def get_paypal_wallets(user = Depends(require_admin)):
    """
    Get all PayPal wallets with accumulated balances.
    Wallets accumulate earnings until they reach the minimum payout threshold.
    """
    wallets = await db.paypal_wallets.find().to_list(500)
    
    # Get minimum payout threshold setting
    min_payout_setting = await db.settings.find_one({"key": "paypal_min_payout"})
    min_payout = min_payout_setting.get("value", 1.00) if min_payout_setting else 1.00
    
    formatted = []
    total_accumulated = 0
    ready_for_payout = 0
    
    for wallet in wallets:
        balance = wallet.get("balance", 0)
        total_accumulated += balance
        if balance >= min_payout:
            ready_for_payout += balance
        
        formatted.append({
            "id": str(wallet["_id"]),
            "user_id": wallet.get("user_id"),
            "paypal_email": wallet.get("paypal_email", "Not set"),
            "balance": balance,
            "ready_for_payout": balance >= min_payout,
            "transactions": wallet.get("transaction_count", 0),
            "last_transaction": wallet.get("last_transaction", None),
            "created_at": wallet.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return {
        "wallets": formatted,
        "total_wallets": len(formatted),
        "total_accumulated": total_accumulated,
        "ready_for_payout": ready_for_payout,
        "min_payout_threshold": min_payout,
        "message": f"{len([w for w in formatted if w['ready_for_payout']])} wallets ready for payout"
    }


@router.post("/paypal-wallets/process-payouts", response_model=dict)
async def process_wallet_payouts(user = Depends(require_admin)):
    """
    Process all wallets that have reached the minimum payout threshold.
    Creates batch payout for all eligible wallets.
    """
    min_payout_setting = await db.settings.find_one({"key": "paypal_min_payout"})
    min_payout = min_payout_setting.get("value", 1.00) if min_payout_setting else 1.00
    
    # Find all wallets ready for payout
    eligible_wallets = await db.paypal_wallets.find({
        "balance": {"$gte": min_payout},
        "paypal_email": {"$exists": True, "$ne": ""}
    }).to_list(500)
    
    if not eligible_wallets:
        return {
            "success": False,
            "message": f"No wallets have reached the minimum payout threshold (${min_payout:.2f})",
            "processed": 0
        }
    
    # Create payout records
    payout_batch_id = str(ObjectId())
    processed = []
    total_amount = 0
    
    for wallet in eligible_wallets:
        balance = wallet.get("balance", 0)
        
        # Create payout record
        payout_record = {
            "batch_id": payout_batch_id,
            "user_id": wallet.get("user_id"),
            "paypal_email": wallet.get("paypal_email"),
            "amount": balance,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        await db.paypal_payouts.insert_one(payout_record)
        
        # Reset wallet balance
        await db.paypal_wallets.update_one(
            {"_id": wallet["_id"]},
            {
                "$set": {"balance": 0, "last_payout": datetime.utcnow()},
                "$inc": {"payout_count": 1}
            }
        )
        
        processed.append({
            "user_id": wallet.get("user_id"),
            "paypal_email": wallet.get("paypal_email"),
            "amount": balance
        })
        total_amount += balance
    
    # Log the batch payout
    await db.admin_audit_log.insert_one({
        "action": "process_wallet_payouts",
        "admin_id": str(user["_id"]),
        "admin_email": user.get("email"),
        "batch_id": payout_batch_id,
        "total_amount": total_amount,
        "wallet_count": len(processed),
        "created_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "batch_id": payout_batch_id,
        "total_amount": total_amount,
        "wallets_processed": len(processed),
        "payouts": processed,
        "message": f"Processed ${total_amount:.2f} in payouts to {len(processed)} wallets"
    }


async def validate_listing_price(user: dict, price: float, is_bundle: bool = False) -> tuple:
    """
    Validate if a user can list at the given price.
    Returns (is_valid, error_message, max_allowed_price)
    Checks both global limits (for ALL users) and unpaid user limits.
    """
    # First check global price controls (applies to EVERYONE)
    global_control_enabled = await db.settings.find_one({"key": "global_price_control_enabled"})
    if global_control_enabled and global_control_enabled.get("value"):
        # Check global max price
        global_price_key = "global_max_bundle_price" if is_bundle else "global_max_protocol_price"
        global_max_setting = await db.settings.find_one({"key": global_price_key})
        global_max = global_max_setting.get("value", 99.99) if global_max_setting else 99.99
        
        if price > global_max:
            return False, f"Maximum allowed price is ${global_max:.2f} (set by admin).", global_max
        
        # Check global min price
        global_min_setting = await db.settings.find_one({"key": "global_min_protocol_price"})
        global_min = global_min_setting.get("value", 0.00) if global_min_setting else 0.00
        
        if price < global_min:
            return False, f"Minimum allowed price is ${global_min:.2f} (set by admin).", global_max
    
    # Check if user is paid (admins and paid users skip unpaid restrictions)
    is_paid = user.get("subscription_active") or user.get("is_admin")
    
    if is_paid:
        # Paid users only subject to global limits
        global_max = 99.99
        if global_control_enabled and global_control_enabled.get("value"):
            global_price_key = "global_max_bundle_price" if is_bundle else "global_max_protocol_price"
            global_max_setting = await db.settings.find_one({"key": global_price_key})
            global_max = global_max_setting.get("value", 99.99) if global_max_setting else 99.99
        return True, None, global_max
    
    # Check if unpaid price controls are enabled
    control_enabled = await db.settings.find_one({"key": "unpaid_price_control_enabled"})
    if not control_enabled or not control_enabled.get("value"):
        return True, None, 99.99  # Controls disabled, allow any price
    
    # Check if unpaid users can sell at all
    can_sell = await db.settings.find_one({"key": "unpaid_can_sell"})
    if can_sell and not can_sell.get("value"):
        return False, "Unpaid users are not allowed to sell. Please upgrade to Premium.", 0
    
    # Get max price setting
    price_key = "unpaid_max_bundle_price" if is_bundle else "unpaid_max_protocol_price"
    max_price_setting = await db.settings.find_one({"key": price_key})
    max_price = max_price_setting.get("value", 5.00) if max_price_setting else 5.00
    
    if price > max_price:
        return False, f"Unpaid users can only charge up to ${max_price:.2f}. Upgrade to Premium for higher prices!", max_price
    
    return True, None, max_price


# ==================== CATEGORY ANALYTICS DASHBOARD ====================

@router.get("/category-analytics", response_model=dict)
async def get_category_analytics(
    days: int = 30,
    user = Depends(require_admin)
):
    """
    Get comprehensive category analytics for admin dashboard.
    """
    # Note: cutoff variable available for future time-based filtering
    # cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get all categories
    categories = await db.categories.find().to_list(1000)
    
    # Get search results counts per category
    pipeline = [
        {"$unwind": "$categories"},
        {"$group": {
            "_id": "$categories",
            "result_count": {"$sum": 1},
            "with_location": {"$sum": {"$cond": [{"$and": [{"$ne": ["$latitude", None]}, {"$ne": ["$longitude", None]}]}, 1, 0]}}
        }},
        {"$sort": {"result_count": -1}}
    ]
    
    category_results = await db.search_results.aggregate(pipeline).to_list(100)
    results_by_category = {r["_id"]: r for r in category_results}
    
    # Build category analytics
    analytics = []
    total_results = 0
    total_with_location = 0
    
    for cat in categories:
        cat_name = cat["name"]
        cat_data = results_by_category.get(cat_name, {})
        result_count = cat_data.get("result_count", 0)
        with_location = cat_data.get("with_location", 0)
        
        total_results += result_count
        total_with_location += with_location
        
        # Get child count
        child_count = len([c for c in categories if c.get("parent_id") == str(cat["_id"])])
        
        analytics.append({
            "id": str(cat["_id"]),
            "name": cat_name,
            "level": cat.get("level", 0),
            "is_public": cat.get("is_public", False),
            "price": cat.get("price", 0),
            "protocol_length": len(cat.get("protocol", "")),
            "result_count": result_count,
            "results_with_location": with_location,
            "location_rate": round((with_location / result_count * 100) if result_count > 0 else 0, 1),
            "child_count": child_count,
            "created_at": cat.get("created_at", datetime.utcnow()).isoformat() if cat.get("created_at") else None
        })
    
    # Sort by result count
    analytics.sort(key=lambda x: x["result_count"], reverse=True)
    
    # Get template popularity from marketplace
    template_pipeline = [
        {"$match": {"is_bundle": True, "status": "active"}},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "total_sales": {"$sum": "$total_sales"}
        }},
        {"$sort": {"total_sales": -1}}
    ]
    
    template_popularity = await db.marketplace_protocols.aggregate(template_pipeline).to_list(20)
    
    return {
        "period_days": days,
        "summary": {
            "total_categories": len(categories),
            "total_results": total_results,
            "results_with_location": total_with_location,
            "avg_results_per_category": round(total_results / len(categories), 1) if categories else 0,
            "categories_by_level": {
                "level_0": len([c for c in categories if c.get("level", 0) == 0]),
                "level_1": len([c for c in categories if c.get("level", 0) == 1]),
                "level_2": len([c for c in categories if c.get("level", 0) == 2]),
                "level_3_plus": len([c for c in categories if c.get("level", 0) >= 3])
            },
            "public_categories": len([c for c in categories if c.get("is_public")]),
            "paid_categories": len([c for c in categories if c.get("price", 0) > 0])
        },
        "top_categories": analytics[:20],
        "empty_categories": [a for a in analytics if a["result_count"] == 0][:10],
        "template_popularity": template_popularity,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/category-analytics/trends", response_model=dict)
async def get_category_trends(
    days: int = 30,
    user = Depends(require_admin)
):
    """Get category growth trends over time"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Categories created over time
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    daily_categories = await db.categories.aggregate(pipeline).to_list(days)
    
    # Results added over time
    results_pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    daily_results = await db.search_results.aggregate(results_pipeline).to_list(days)
    
    return {
        "period_days": days,
        "daily_categories_created": daily_categories,
        "daily_results_added": daily_results
    }
