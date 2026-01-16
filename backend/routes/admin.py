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
        # Unpaid User Price Controls (NEW)
        {"key": "unpaid_price_control_enabled", "value": False, "description": "Enable price limits for unpaid users"},
        {"key": "unpaid_max_protocol_price", "value": 5.00, "description": "Max price unpaid users can charge per protocol ($)"},
        {"key": "unpaid_max_bundle_price", "value": 10.00, "description": "Max price unpaid users can charge per bundle ($)"},
        {"key": "unpaid_can_sell", "value": True, "description": "Allow unpaid users to sell at all"},
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


async def validate_listing_price(user: dict, price: float, is_bundle: bool = False) -> tuple:
    """
    Validate if a user can list at the given price.
    Returns (is_valid, error_message, max_allowed_price)
    """
    # Check if user is paid
    is_paid = user.get("subscription_active") or user.get("is_admin")
    
    if is_paid:
        return True, None, 99.99
    
    # Check if price controls are enabled
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
