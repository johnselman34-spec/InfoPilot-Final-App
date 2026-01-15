"""
InfoPilot Explorer - API Rate Limiting & Dashboard
Track and manage API usage with rate limiting
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timedelta, timezone
from typing import Optional
from collections import defaultdict
import time

from config import db, logger
from routes.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/rate-limit", tags=["Rate Limiting"])

# In-memory rate limit tracking (would use Redis in production)
rate_limits = defaultdict(lambda: {"requests": 0, "window_start": time.time()})

# Rate limit tiers
RATE_TIERS = {
    "free": {
        "requests_per_minute": 30,
        "requests_per_hour": 500,
        "requests_per_day": 5000,
        "search_per_minute": 10,
        "ai_per_hour": 20
    },
    "premium": {
        "requests_per_minute": 100,
        "requests_per_hour": 2000,
        "requests_per_day": 20000,
        "search_per_minute": 50,
        "ai_per_hour": 100
    },
    "admin": {
        "requests_per_minute": 1000,
        "requests_per_hour": 50000,
        "requests_per_day": 500000,
        "search_per_minute": 500,
        "ai_per_hour": 1000
    }
}


def get_user_tier(user: dict) -> str:
    """Determine user's rate limit tier"""
    if user.get("is_admin"):
        return "admin"
    if user.get("subscription_active"):
        return "premium"
    return "free"


async def track_api_usage(user_id: str, endpoint: str, method: str):
    """Track API usage for a user"""
    await db.api_usage.insert_one({
        "user_id": user_id,
        "endpoint": endpoint,
        "method": method,
        "timestamp": datetime.now(timezone.utc)
    })


@router.get("/status", response_model=dict)
async def get_rate_limit_status(user = Depends(get_current_user)):
    """Get current rate limit status for the user"""
    user_id = str(user["_id"])
    tier = get_user_tier(user)
    limits = RATE_TIERS[tier]
    
    now = datetime.now(timezone.utc)
    
    # Count requests in different time windows
    minute_ago = now - timedelta(minutes=1)
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    
    requests_minute = await db.api_usage.count_documents({
        "user_id": user_id,
        "timestamp": {"$gte": minute_ago}
    })
    
    requests_hour = await db.api_usage.count_documents({
        "user_id": user_id,
        "timestamp": {"$gte": hour_ago}
    })
    
    requests_day = await db.api_usage.count_documents({
        "user_id": user_id,
        "timestamp": {"$gte": day_ago}
    })
    
    # Search-specific limits
    search_minute = await db.api_usage.count_documents({
        "user_id": user_id,
        "endpoint": {"$regex": "search"},
        "timestamp": {"$gte": minute_ago}
    })
    
    # AI-specific limits
    ai_hour = await db.api_usage.count_documents({
        "user_id": user_id,
        "endpoint": {"$regex": "(voice|newsletter|ai)"},
        "timestamp": {"$gte": hour_ago}
    })
    
    return {
        "tier": tier,
        "limits": limits,
        "usage": {
            "requests_minute": {
                "used": requests_minute,
                "limit": limits["requests_per_minute"],
                "remaining": max(0, limits["requests_per_minute"] - requests_minute),
                "percentage": round((requests_minute / limits["requests_per_minute"]) * 100, 1)
            },
            "requests_hour": {
                "used": requests_hour,
                "limit": limits["requests_per_hour"],
                "remaining": max(0, limits["requests_per_hour"] - requests_hour),
                "percentage": round((requests_hour / limits["requests_per_hour"]) * 100, 1)
            },
            "requests_day": {
                "used": requests_day,
                "limit": limits["requests_per_day"],
                "remaining": max(0, limits["requests_per_day"] - requests_day),
                "percentage": round((requests_day / limits["requests_per_day"]) * 100, 1)
            },
            "search_minute": {
                "used": search_minute,
                "limit": limits["search_per_minute"],
                "remaining": max(0, limits["search_per_minute"] - search_minute),
                "percentage": round((search_minute / limits["search_per_minute"]) * 100, 1)
            },
            "ai_hour": {
                "used": ai_hour,
                "limit": limits["ai_per_hour"],
                "remaining": max(0, limits["ai_per_hour"] - ai_hour),
                "percentage": round((ai_hour / limits["ai_per_hour"]) * 100, 1)
            }
        },
        "reset_times": {
            "minute": (now + timedelta(minutes=1)).isoformat(),
            "hour": (now + timedelta(hours=1)).isoformat(),
            "day": (now + timedelta(days=1)).isoformat()
        }
    }


@router.get("/history", response_model=dict)
async def get_usage_history(
    days: int = 7,
    user = Depends(get_current_user)
):
    """Get API usage history for the user"""
    user_id = str(user["_id"])
    
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Aggregate by day
    pipeline = [
        {"$match": {
            "user_id": user_id,
            "timestamp": {"$gte": since}
        }},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "endpoint": {"$arrayElemAt": [{"$split": ["$endpoint", "/"]}, 2]}
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    
    results = await db.api_usage.aggregate(pipeline).to_list(1000)
    
    # Format for chart
    daily_data = defaultdict(lambda: {"total": 0, "endpoints": {}})
    for r in results:
        date = r["_id"]["date"]
        endpoint = r["_id"]["endpoint"] or "other"
        count = r["count"]
        
        daily_data[date]["total"] += count
        daily_data[date]["endpoints"][endpoint] = \
            daily_data[date]["endpoints"].get(endpoint, 0) + count
    
    # Convert to list
    history = []
    for date, data in sorted(daily_data.items()):
        history.append({
            "date": date,
            "total": data["total"],
            "breakdown": data["endpoints"]
        })
    
    return {
        "history": history,
        "period_days": days,
        "total_requests": sum(d["total"] for d in history)
    }


@router.get("/admin/overview", response_model=dict)
async def get_admin_overview(user = Depends(get_current_user)):
    """Admin-only: Get system-wide rate limit overview"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    
    # Total requests
    total_hour = await db.api_usage.count_documents({"timestamp": {"$gte": hour_ago}})
    total_day = await db.api_usage.count_documents({"timestamp": {"$gte": day_ago}})
    
    # Unique users
    unique_hour = len(await db.api_usage.distinct("user_id", {"timestamp": {"$gte": hour_ago}}))
    unique_day = len(await db.api_usage.distinct("user_id", {"timestamp": {"$gte": day_ago}}))
    
    # Top endpoints
    top_endpoints_pipeline = [
        {"$match": {"timestamp": {"$gte": hour_ago}}},
        {"$group": {"_id": "$endpoint", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_endpoints = await db.api_usage.aggregate(top_endpoints_pipeline).to_list(10)
    
    # Top users by requests
    top_users_pipeline = [
        {"$match": {"timestamp": {"$gte": hour_ago}}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_users = await db.api_usage.aggregate(top_users_pipeline).to_list(10)
    
    # Get user details
    for u in top_users:
        user_doc = await db.users.find_one({"_id": ObjectId(u["_id"])})
        u["username"] = user_doc.get("username", "Unknown") if user_doc else "Unknown"
        u["tier"] = get_user_tier(user_doc) if user_doc else "free"
    
    return {
        "requests_last_hour": total_hour,
        "requests_last_day": total_day,
        "unique_users_hour": unique_hour,
        "unique_users_day": unique_day,
        "top_endpoints": [{"endpoint": e["_id"], "count": e["count"]} for e in top_endpoints],
        "top_users": [{"user_id": u["_id"], "username": u["username"], "tier": u["tier"], "count": u["count"]} for u in top_users],
        "tier_definitions": RATE_TIERS
    }
