"""
InfoPilot Explorer - Admin Routes
System status, admin settings, and management
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict
from datetime import datetime, timezone
import os

from utils.db import db
from utils.auth import require_user

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(user: Dict = Depends(require_user)):
    """Require admin role."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/system-status")
async def get_system_status(user: Dict = Depends(require_admin)):
    """Get comprehensive system status for admin dashboard."""
    
    # Database status
    db_status = {"connected": True, "name": os.environ.get("DB_NAME", "unknown")}
    try:
        await db.users.find_one({})
    except Exception as e:
        db_status = {"connected": False, "error": str(e)}
    
    # Search engines status
    search_engines = []
    
    # DuckDuckGo (always available, no API key needed)
    search_engines.append({
        "id": "duckduckgo",
        "name": "DuckDuckGo",
        "status": "operational",
        "configured": True,
        "api_key_required": False
    })
    
    # Brave Search
    brave_key = os.environ.get("BRAVE_SEARCH_API_KEY", "")
    search_engines.append({
        "id": "brave",
        "name": "Brave Search",
        "status": "operational" if brave_key else "not_configured",
        "configured": bool(brave_key),
        "api_key_required": True,
        "api_key_set": bool(brave_key)
    })
    
    # Elasticsearch status
    es_status = {"connected": False, "configured": False}
    try:
        from utils.elasticsearch_client import get_elasticsearch_status
        es_status = get_elasticsearch_status()
    except Exception as e:
        es_status["error"] = str(e)
    
    # Email service status (Resend)
    resend_key = os.environ.get("RESEND_API_KEY", "")
    email_status = {
        "provider": "Resend",
        "configured": bool(resend_key),
        "sender_email": os.environ.get("SENDER_EMAIL", "not set")
    }
    
    # Payment service status (Stripe)
    stripe_key = os.environ.get("STRIPE_API_KEY", "")
    payment_status = {
        "provider": "Stripe",
        "configured": bool(stripe_key),
        "mode": "test" if stripe_key and "test" in stripe_key else "live" if stripe_key else "not_configured"
    }
    
    # PayPal status (blocked)
    paypal_id = os.environ.get("PAYPAL_CLIENT_ID", "")
    paypal_status = {
        "provider": "PayPal",
        "configured": bool(paypal_id),
        "status": "blocked",
        "note": "User account issues - Stripe is primary"
    }
    
    # Paywall filter status
    paywall_status = {"enabled": False, "blocked_domains": 0}
    try:
        from utils.paywall_filter import PAYWALL_DOMAINS
        paywall_status["enabled"] = True
        paywall_status["blocked_domains"] = len(PAYWALL_DOMAINS)
    except Exception:
        pass
    
    # Cache status
    cache_status = {"enabled": False}
    try:
        from utils.cache import marketplace_cache, leaderboard_cache, search_cache
        cache_status["enabled"] = True
        cache_status["entries"] = (
            marketplace_cache.stats().get("total_entries", 0) +
            leaderboard_cache.stats().get("total_entries", 0) +
            search_cache.stats().get("total_entries", 0)
        )
    except Exception:
        pass
    
    # Platform statistics
    stats = {
        "total_users": await db.users.count_documents({}),
        "total_categories": await db.categories.count_documents({}),
        "public_protocols": await db.categories.count_documents({"is_public": True, "price": {"$gt": 0}}),
        "total_search_results": await db.search_results.count_documents({}),
        "total_purchases": await db.purchases.count_documents({"status": "completed"})
    }
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy",
        "services": {
            "database": db_status,
            "search_engines": search_engines,
            "elasticsearch": es_status,
            "email": email_status,
            "payments": {
                "primary": payment_status,
                "secondary": paypal_status
            },
            "paywall_filter": paywall_status,
            "cache": cache_status
        },
        "statistics": stats
    }


@router.get("/settings")
async def get_admin_settings(user: Dict = Depends(require_admin)):
    """Get admin settings."""
    settings = await db.admin_settings.find_one({"id": "admin_settings"}, {"_id": 0})
    return settings or {}


@router.put("/settings")
async def update_admin_settings(updates: Dict = Body(...), user: Dict = Depends(require_admin)):
    """Update admin settings."""
    allowed_fields = [
        "collation_limit", "max_category_depth", "newsletter_times",
        "newsletter_enabled", "search_results_per_page", "unpaid_max_pages",
        "subscription_price_monthly", "subscription_price_yearly",
        "upgrade_message", "phd_min_occurrences", "phd_min_words",
        "personal_report_min_i", "personal_report_min_words", "banned_words"
    ]
    
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}
    if filtered:
        await db.admin_settings.update_one(
            {"id": "admin_settings"},
            {"$set": filtered},
            upsert=True
        )
    
    return {"message": "Settings updated", "updated_fields": list(filtered.keys())}


@router.get("/recent-activity")
async def get_recent_activity(user: Dict = Depends(require_admin)):
    """Get recent platform activity."""
    
    # Recent users (last 5)
    recent_users = await db.users.find(
        {},
        {"_id": 0, "id": 1, "username": 1, "email": 1, "is_paid": 1}
    ).sort("_id", -1).limit(5).to_list(5)
    
    # Recent purchases (last 5)
    recent_purchases = await db.purchases.find(
        {"status": "completed"},
        {"_id": 0, "id": 1, "amount": 1, "protocol_name": 1, "created_at": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Recent chat messages count (last 24 hours)
    from datetime import timedelta
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    chat_messages_24h = await db.chat_messages.count_documents(
        {"created_at": {"$gte": yesterday.isoformat()}}
    )
    
    return {
        "recent_users": recent_users,
        "recent_purchases": recent_purchases,
        "chat_messages_24h": chat_messages_24h
    }


@router.get("/maintenance")
async def get_maintenance_status(user: Dict = Depends(require_admin)):
    """Get current maintenance mode status."""
    from utils.service_monitor import get_maintenance_mode
    return await get_maintenance_mode()


@router.post("/maintenance")
async def set_maintenance_status(
    enabled: bool = Body(...),
    message: str = Body(None),
    end_time: str = Body(None),
    user: Dict = Depends(require_admin)
):
    """Enable or disable maintenance mode."""
    from utils.service_monitor import set_maintenance_mode
    result = await set_maintenance_mode(enabled, message, end_time)
    return {
        "message": f"Maintenance mode {'enabled' if enabled else 'disabled'}",
        "maintenance": result
    }


@router.post("/health-check")
async def run_health_check(
    send_alerts: bool = Body(False, embed=True),
    user: Dict = Depends(require_admin)
):
    """Run a manual health check and optionally send alerts."""
    from utils.service_monitor import monitor_services_once
    
    admin_email = user.get("email") if send_alerts else None
    result = await monitor_services_once(admin_email)
    
    return {
        "message": "Health check completed",
        "result": result
    }


@router.post("/test-alert")
async def send_test_alert(user: Dict = Depends(require_admin)):
    """Send a test alert email to the admin."""
    from utils.service_monitor import send_service_alert
    
    success = await send_service_alert(
        "Test Service",
        "test",
        "This is a test alert from InfoPilot Explorer",
        user.get("email")
    )
    
    if success:
        return {"message": f"Test alert sent to {user.get('email')}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test alert. Check email configuration.")
