"""
InfoPilot Explorer - Protocol Analytics Dashboard Service
Provides performance metrics for protocol creators
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


async def get_protocol_analytics(user_id: str, protocol_id: Optional[str] = None, days: int = 30) -> Dict:
    """Get comprehensive analytics for a protocol creator's protocols"""
    from config import db
    
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Base query for user's protocols
    protocol_query = {"creator_id": user_id}
    if protocol_id:
        protocol_query["_id"] = ObjectId(protocol_id)
    
    protocols = await db.marketplace_protocols.find(protocol_query).to_list(100)
    
    if not protocols:
        return {
            "success": True,
            "total_protocols": 0,
            "analytics": [],
            "summary": {
                "total_views": 0,
                "total_copies": 0,
                "total_sales": 0,
                "total_revenue": 0,
                "avg_rating": 0
            }
        }
    
    protocol_ids = [str(p["_id"]) for p in protocols]
    
    # Get views (from search impressions)
    views_pipeline = [
        {"$match": {
            "protocol_id": {"$in": protocol_ids},
            "timestamp": {"$gte": since}
        }},
        {"$group": {
            "_id": "$protocol_id",
            "views": {"$sum": 1}
        }}
    ]
    views_data = {v["_id"]: v["views"] for v in await db.protocol_views.aggregate(views_pipeline).to_list(100)}
    
    # Get copies
    copies_pipeline = [
        {"$match": {
            "protocol_id": {"$in": protocol_ids},
            "created_at": {"$gte": since}
        }},
        {"$group": {
            "_id": "$protocol_id",
            "copies": {"$sum": 1}
        }}
    ]
    copies_data = {c["_id"]: c["copies"] for c in await db.protocol_copies.aggregate(copies_pipeline).to_list(100)}
    
    # Get sales
    sales_pipeline = [
        {"$match": {
            "protocol_id": {"$in": protocol_ids},
            "status": "completed",
            "created_at": {"$gte": since}
        }},
        {"$group": {
            "_id": "$protocol_id",
            "sales": {"$sum": 1},
            "revenue": {"$sum": "$amount"}
        }}
    ]
    sales_data = {s["_id"]: {"sales": s["sales"], "revenue": s["revenue"]} for s in await db.marketplace_purchases.aggregate(sales_pipeline).to_list(100)}
    
    # Get daily trends
    daily_pipeline = [
        {"$match": {
            "protocol_id": {"$in": protocol_ids},
            "timestamp": {"$gte": since}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "views": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_views = await db.protocol_views.aggregate(daily_pipeline).to_list(100)
    
    # Build analytics for each protocol
    analytics = []
    total_views = 0
    total_copies = 0
    total_sales = 0
    total_revenue = 0
    total_rating_sum = 0
    rated_count = 0
    
    for protocol in protocols:
        pid = str(protocol["_id"])
        views = views_data.get(pid, 0)
        copies = copies_data.get(pid, 0)
        sales_info = sales_data.get(pid, {"sales": 0, "revenue": 0})
        
        # Calculate conversion rate
        conversion_rate = 0
        if views > 0:
            if protocol.get("price", 0) == 0:
                conversion_rate = (copies / views) * 100
            else:
                conversion_rate = (sales_info["sales"] / views) * 100
        
        rating = protocol.get("rating", 0)
        if rating > 0:
            total_rating_sum += rating
            rated_count += 1
        
        analytics.append({
            "id": pid,
            "name": protocol.get("name", "Unknown"),
            "category": protocol.get("category", "General"),
            "price": protocol.get("price", 0),
            "is_free": protocol.get("price", 0) == 0,
            "views": views,
            "copies": copies,
            "sales": sales_info["sales"],
            "revenue": sales_info["revenue"],
            "rating": rating,
            "review_count": protocol.get("review_count", 0),
            "conversion_rate": round(conversion_rate, 2),
            "created_at": protocol.get("created_at", datetime.now(timezone.utc)).isoformat()
        })
        
        total_views += views
        total_copies += copies
        total_sales += sales_info["sales"]
        total_revenue += sales_info["revenue"]
    
    # Sort by revenue/copies
    analytics.sort(key=lambda x: (x["revenue"], x["copies"]), reverse=True)
    
    return {
        "success": True,
        "total_protocols": len(protocols),
        "period_days": days,
        "analytics": analytics,
        "summary": {
            "total_views": total_views,
            "total_copies": total_copies,
            "total_sales": total_sales,
            "total_revenue": round(total_revenue, 2),
            "avg_rating": round(total_rating_sum / rated_count, 2) if rated_count > 0 else 0,
            "avg_conversion_rate": round((total_copies + total_sales) / total_views * 100, 2) if total_views > 0 else 0
        },
        "trends": {
            "daily_views": [{"date": d["_id"], "views": d["views"]} for d in daily_views]
        }
    }


async def get_protocol_forecast(user_id: str, days: int = 30) -> Dict:
    """Forecast future performance based on historical data"""
    from config import db
    
    analytics = await get_protocol_analytics(user_id, days=days)
    
    if analytics["total_protocols"] == 0:
        return {
            "success": True,
            "forecast": {
                "next_week_revenue": 0,
                "next_month_revenue": 0,
                "top_performer": None,
                "growth_potential": []
            }
        }
    
    # Calculate daily averages
    daily_revenue = analytics["summary"]["total_revenue"] / days if days > 0 else 0
    daily_copies = analytics["summary"]["total_copies"] / days if days > 0 else 0
    
    # Forecast next periods
    next_week_revenue = daily_revenue * 7
    next_month_revenue = daily_revenue * 30
    
    # Find top performer and growth potential
    top_performer = analytics["analytics"][0] if analytics["analytics"] else None
    
    # Identify protocols with high views but low conversion (growth potential)
    growth_potential = []
    for p in analytics["analytics"]:
        if p["views"] > 10 and p["conversion_rate"] < 5:
            growth_potential.append({
                "id": p["id"],
                "name": p["name"],
                "current_conversion": p["conversion_rate"],
                "potential_increase": f"Could increase to {min(p['conversion_rate'] * 2, 15):.1f}% with optimization",
                "suggestions": [
                    "Improve protocol description",
                    "Add more tags for discoverability",
                    "Consider adjusting price point"
                ]
            })
    
    return {
        "success": True,
        "forecast": {
            "next_week_revenue": round(next_week_revenue, 2),
            "next_month_revenue": round(next_month_revenue, 2),
            "daily_average_copies": round(daily_copies, 1),
            "top_performer": {
                "id": top_performer["id"],
                "name": top_performer["name"],
                "revenue": top_performer["revenue"],
                "conversion_rate": top_performer["conversion_rate"]
            } if top_performer else None,
            "growth_potential": growth_potential[:5]  # Top 5 with potential
        }
    }


async def track_protocol_view(protocol_id: str, viewer_id: Optional[str] = None):
    """Track a protocol view for analytics"""
    from config import db
    
    await db.protocol_views.insert_one({
        "protocol_id": protocol_id,
        "viewer_id": viewer_id,
        "timestamp": datetime.now(timezone.utc)
    })


async def get_marketplace_protocol_forecast() -> Dict:
    """Admin: Get marketplace-wide protocol performance forecast"""
    from config import db
    
    # Get all protocols with sales data
    pipeline = [
        {"$lookup": {
            "from": "marketplace_purchases",
            "localField": "_id",
            "foreignField": "protocol_id",
            "as": "purchases"
        }},
        {"$addFields": {
            "purchase_count": {"$size": "$purchases"},
            "total_revenue": {"$sum": "$purchases.amount"}
        }},
        {"$match": {"purchase_count": {"$gt": 0}}},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 20}
    ]
    
    try:
        top_protocols = await db.marketplace_protocols.aggregate(pipeline).to_list(20)
    except:
        top_protocols = []
    
    # Calculate trends
    now = datetime.now(timezone.utc)
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    week_sales = await db.marketplace_purchases.count_documents({
        "status": "completed",
        "created_at": {"$gte": last_week}
    })
    
    month_sales = await db.marketplace_purchases.count_documents({
        "status": "completed",
        "created_at": {"$gte": last_month}
    })
    
    # Revenue calculations
    week_revenue_pipeline = [
        {"$match": {"status": "completed", "created_at": {"$gte": last_week}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    week_revenue_result = await db.marketplace_purchases.aggregate(week_revenue_pipeline).to_list(1)
    week_revenue = week_revenue_result[0]["total"] if week_revenue_result else 0
    
    month_revenue_pipeline = [
        {"$match": {"status": "completed", "created_at": {"$gte": last_month}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    month_revenue_result = await db.marketplace_purchases.aggregate(month_revenue_pipeline).to_list(1)
    month_revenue = month_revenue_result[0]["total"] if month_revenue_result else 0
    
    # Forecast next month based on trends
    daily_avg = month_revenue / 30 if month_revenue > 0 else 0
    projected_next_month = daily_avg * 30
    
    # Week over week growth
    prev_week_start = last_week - timedelta(days=7)
    prev_week_revenue_pipeline = [
        {"$match": {"status": "completed", "created_at": {"$gte": prev_week_start, "$lt": last_week}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    prev_week_result = await db.marketplace_purchases.aggregate(prev_week_revenue_pipeline).to_list(1)
    prev_week_revenue = prev_week_result[0]["total"] if prev_week_result else 0
    
    wow_growth = ((week_revenue - prev_week_revenue) / prev_week_revenue * 100) if prev_week_revenue > 0 else 0
    
    return {
        "success": True,
        "marketplace_forecast": {
            "week_sales": week_sales,
            "week_revenue": round(week_revenue, 2),
            "month_sales": month_sales,
            "month_revenue": round(month_revenue, 2),
            "projected_next_month": round(projected_next_month, 2),
            "wow_growth_percent": round(wow_growth, 1),
            "top_performing_protocols": [
                {
                    "id": str(p["_id"]),
                    "name": p.get("name", "Unknown"),
                    "category": p.get("category", "General"),
                    "sales": p.get("purchase_count", 0),
                    "revenue": round(p.get("total_revenue", 0), 2),
                    "creator_id": p.get("creator_id")
                }
                for p in top_protocols[:10]
            ]
        }
    }
