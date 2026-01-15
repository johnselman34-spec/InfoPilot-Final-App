"""
InfoPilot Explorer - Protocol Analytics
Tracks views, copies, and conversions for marketplace protocols
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel

from config import db, logger
from routes.auth import get_current_user, get_optional_user

router = APIRouter(tags=["Protocol Analytics"])


class AnalyticsEvent(BaseModel):
    protocol_id: str
    event_type: str  # 'view', 'copy', 'purchase', 'share'


# ==================== TRACKING ENDPOINTS ====================

@router.post("/analytics/track", response_model=dict)
async def track_event(
    event: AnalyticsEvent,
    request: Request,
    user = Depends(get_optional_user)
):
    """Track a protocol analytics event (view, copy, purchase, share)"""
    user_id = str(user["_id"]) if user else None
    
    # Validate event type
    valid_events = ['view', 'copy', 'purchase', 'share', 'click']
    if event.event_type not in valid_events:
        raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of: {valid_events}")
    
    # Validate protocol exists
    try:
        protocol = await db.categories.find_one({"_id": ObjectId(event.protocol_id)})
    except:
        protocol = None
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Create analytics event
    event_data = {
        "protocol_id": event.protocol_id,
        "event_type": event.event_type,
        "user_id": user_id,
        "client_ip": client_ip,
        "user_agent": user_agent[:200] if user_agent else None,
        "timestamp": datetime.now(timezone.utc),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }
    
    await db.protocol_analytics.insert_one(event_data)
    
    # Update protocol's aggregate stats
    update_field = f"analytics.{event.event_type}_count"
    await db.categories.update_one(
        {"_id": ObjectId(event.protocol_id)},
        {
            "$inc": {update_field: 1},
            "$set": {f"analytics.last_{event.event_type}": datetime.now(timezone.utc)}
        }
    )
    
    return {"success": True, "tracked": event.event_type}


@router.get("/analytics/protocol/{protocol_id}", response_model=dict)
async def get_protocol_analytics(
    protocol_id: str,
    days: int = 30,
    user = Depends(get_current_user)
):
    """Get analytics for a specific protocol (owner or admin only)"""
    user_id = str(user["_id"])
    
    # Get protocol
    try:
        protocol = await db.categories.find_one({"_id": ObjectId(protocol_id)})
    except:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check authorization
    if protocol.get("user_id") != user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view analytics")
    
    # Get date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Aggregate events by type
    pipeline = [
        {
            "$match": {
                "protocol_id": protocol_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$event_type",
                "count": {"$sum": 1}
            }
        }
    ]
    
    event_counts = await db.protocol_analytics.aggregate(pipeline).to_list(10)
    counts = {item["_id"]: item["count"] for item in event_counts}
    
    # Get daily breakdown
    daily_pipeline = [
        {
            "$match": {
                "protocol_id": protocol_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "date": "$date",
                    "event_type": "$event_type"
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.date": 1}}
    ]
    
    daily_data = await db.protocol_analytics.aggregate(daily_pipeline).to_list(500)
    
    # Format daily data for charts
    daily_stats = {}
    for item in daily_data:
        date = item["_id"]["date"]
        event_type = item["_id"]["event_type"]
        if date not in daily_stats:
            daily_stats[date] = {"date": date, "views": 0, "copies": 0, "purchases": 0, "shares": 0}
        daily_stats[date][f"{event_type}s" if event_type != "copy" else "copies"] = item["count"]
    
    # Calculate conversion rates
    views = counts.get("view", 0)
    copies = counts.get("copy", 0)
    purchases = counts.get("purchase", 0)
    
    conversion_rate = round((purchases / views * 100) if views > 0 else 0, 2)
    copy_rate = round((copies / views * 100) if views > 0 else 0, 2)
    
    # Get unique visitors
    unique_visitors = await db.protocol_analytics.distinct(
        "user_id",
        {
            "protocol_id": protocol_id,
            "timestamp": {"$gte": start_date, "$lte": end_date},
            "user_id": {"$ne": None}
        }
    )
    
    return {
        "protocol_id": protocol_id,
        "protocol_name": protocol.get("name", "Unknown"),
        "period_days": days,
        "summary": {
            "total_views": views,
            "total_copies": copies,
            "total_purchases": purchases,
            "total_shares": counts.get("share", 0),
            "unique_visitors": len(unique_visitors),
            "conversion_rate": conversion_rate,
            "copy_rate": copy_rate
        },
        "daily_data": list(daily_stats.values()),
        "aggregated": protocol.get("analytics", {})
    }


@router.get("/analytics/creator/dashboard", response_model=dict)
async def get_creator_analytics_dashboard(
    days: int = 30,
    user = Depends(get_current_user)
):
    """Get analytics dashboard for all protocols owned by the user"""
    user_id = str(user["_id"])
    
    # Get all user's marketplace protocols
    protocols = await db.categories.find({
        "user_id": user_id,
        "is_marketplace": True
    }).to_list(100)
    
    if not protocols:
        return {
            "total_protocols": 0,
            "summary": {
                "total_views": 0,
                "total_copies": 0,
                "total_purchases": 0,
                "total_revenue": 0,
                "avg_conversion_rate": 0
            },
            "protocols": [],
            "top_performing": [],
            "daily_overview": []
        }
    
    protocol_ids = [str(p["_id"]) for p in protocols]
    
    # Get date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Aggregate all events for user's protocols
    pipeline = [
        {
            "$match": {
                "protocol_id": {"$in": protocol_ids},
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "protocol_id": "$protocol_id",
                    "event_type": "$event_type"
                },
                "count": {"$sum": 1}
            }
        }
    ]
    
    events = await db.protocol_analytics.aggregate(pipeline).to_list(500)
    
    # Build protocol stats
    protocol_stats = {}
    for p in protocols:
        pid = str(p["_id"])
        protocol_stats[pid] = {
            "id": pid,
            "name": p.get("name", "Unknown"),
            "price": p.get("price", 0),
            "views": 0,
            "copies": 0,
            "purchases": 0,
            "shares": 0
        }
    
    for event in events:
        pid = event["_id"]["protocol_id"]
        event_type = event["_id"]["event_type"]
        if pid in protocol_stats:
            key = f"{event_type}s" if event_type != "copy" else "copies"
            protocol_stats[pid][key] = event["count"]
    
    # Calculate totals
    total_views = sum(p["views"] for p in protocol_stats.values())
    total_copies = sum(p["copies"] for p in protocol_stats.values())
    total_purchases = sum(p["purchases"] for p in protocol_stats.values())
    
    # Get revenue from purchases
    purchases = await db.purchases.find({
        "seller_id": user_id,
        "created_at": {"$gte": start_date, "$lte": end_date}
    }).to_list(1000)
    total_revenue = sum(p.get("seller_amount", 0) for p in purchases)
    
    # Calculate conversion rates per protocol
    for pid, stats in protocol_stats.items():
        if stats["views"] > 0:
            stats["conversion_rate"] = round(stats["purchases"] / stats["views"] * 100, 2)
        else:
            stats["conversion_rate"] = 0
    
    # Get top performing protocols
    protocol_list = list(protocol_stats.values())
    top_by_views = sorted(protocol_list, key=lambda x: x["views"], reverse=True)[:5]
    top_by_conversion = sorted([p for p in protocol_list if p["views"] >= 5], 
                               key=lambda x: x["conversion_rate"], reverse=True)[:5]
    
    # Daily overview
    daily_pipeline = [
        {
            "$match": {
                "protocol_id": {"$in": protocol_ids},
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "date": "$date",
                    "event_type": "$event_type"
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.date": 1}}
    ]
    
    daily_data = await db.protocol_analytics.aggregate(daily_pipeline).to_list(500)
    
    daily_overview = {}
    for item in daily_data:
        date = item["_id"]["date"]
        event_type = item["_id"]["event_type"]
        if date not in daily_overview:
            daily_overview[date] = {"date": date, "views": 0, "copies": 0, "purchases": 0}
        key = f"{event_type}s" if event_type != "copy" else "copies"
        if key in daily_overview[date]:
            daily_overview[date][key] = item["count"]
    
    avg_conversion = round(
        (total_purchases / total_views * 100) if total_views > 0 else 0, 2
    )
    
    return {
        "total_protocols": len(protocols),
        "period_days": days,
        "summary": {
            "total_views": total_views,
            "total_copies": total_copies,
            "total_purchases": total_purchases,
            "total_revenue": round(total_revenue, 2),
            "avg_conversion_rate": avg_conversion
        },
        "protocols": protocol_list,
        "top_by_views": top_by_views,
        "top_by_conversion": top_by_conversion,
        "daily_overview": list(daily_overview.values())
    }


@router.get("/analytics/admin/overview", response_model=dict)
async def get_admin_analytics_overview(
    days: int = 30,
    user = Depends(get_current_user)
):
    """Admin-only: Get platform-wide protocol analytics"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Total events by type
    pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$event_type",
                "count": {"$sum": 1}
            }
        }
    ]
    
    event_totals = await db.protocol_analytics.aggregate(pipeline).to_list(10)
    totals = {item["_id"]: item["count"] for item in event_totals}
    
    # Most viewed protocols
    top_viewed_pipeline = [
        {
            "$match": {
                "event_type": "view",
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$protocol_id",
                "views": {"$sum": 1}
            }
        },
        {"$sort": {"views": -1}},
        {"$limit": 10}
    ]
    
    top_viewed = await db.protocol_analytics.aggregate(top_viewed_pipeline).to_list(10)
    
    # Enrich with protocol names
    for item in top_viewed:
        try:
            protocol = await db.categories.find_one({"_id": ObjectId(item["_id"])})
            item["name"] = protocol.get("name", "Unknown") if protocol else "Deleted"
        except:
            item["name"] = "Unknown"
    
    # Daily trend
    daily_pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": "$date",
                "total_events": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    daily_trend = await db.protocol_analytics.aggregate(daily_pipeline).to_list(100)
    
    return {
        "period_days": days,
        "totals": {
            "views": totals.get("view", 0),
            "copies": totals.get("copy", 0),
            "purchases": totals.get("purchase", 0),
            "shares": totals.get("share", 0)
        },
        "top_viewed_protocols": top_viewed,
        "daily_trend": [{"date": d["_id"], "events": d["total_events"]} for d in daily_trend]
    }
