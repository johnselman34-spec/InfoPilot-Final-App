"""
InfoPilot Explorer - Database Optimization
Database indexes and query optimization utilities
"""
import logging
from utils.db import db

logger = logging.getLogger(__name__)


async def create_indexes():
    """Create database indexes for optimal query performance."""
    try:
        # Users collection indexes
        await db.users.create_index("id", unique=True)
        await db.users.create_index("email", unique=True)
        await db.users.create_index("laughter_points")
        await db.users.create_index("subscription_active")
        
        # Categories collection indexes
        await db.categories.create_index("id", unique=True)
        await db.categories.create_index("user_id")
        await db.categories.create_index("is_public")
        await db.categories.create_index("price")
        await db.categories.create_index([("is_public", 1), ("price", 1)])  # Compound index for marketplace
        await db.categories.create_index("parent_id")
        
        # Search results collection indexes
        await db.search_results.create_index("id", unique=True)
        await db.search_results.create_index("user_id")
        await db.search_results.create_index("category_ids")
        await db.search_results.create_index("created_at")
        await db.search_results.create_index("url")
        await db.search_results.create_index([("user_id", 1), ("created_at", -1)])  # Compound
        
        # Purchases collection indexes
        await db.purchases.create_index("id", unique=True)
        await db.purchases.create_index("buyer_id")
        await db.purchases.create_index("seller_id")
        await db.purchases.create_index("status")
        await db.purchases.create_index([("seller_id", 1), ("status", 1)])  # Compound
        
        # Sessions collection indexes
        await db.sessions.create_index("token", unique=True)
        await db.sessions.create_index("user_id")
        await db.sessions.create_index("expires_at")
        
        # Chat rooms and messages indexes
        await db.chat_rooms.create_index("id", unique=True)
        await db.chat_messages.create_index("room_id")
        await db.chat_messages.create_index([("room_id", 1), ("created_at", -1)])  # Compound
        
        # Groups and pages indexes
        await db.groups.create_index("id", unique=True)
        await db.groups.create_index("owner_id")
        await db.pages.create_index("id", unique=True)
        await db.pages.create_index("owner_id")
        
        # Newsletter subscribers
        await db.newsletter_subscribers.create_index("email", unique=True)
        await db.newsletter_subscribers.create_index("is_active")
        
        # Payment transactions
        await db.payment_transactions.create_index("id", unique=True)
        await db.payment_transactions.create_index("user_id")
        await db.payment_transactions.create_index([("user_id", 1), ("created_at", -1)])
        
        logger.info("Database indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        return False


async def batch_fetch_users(user_ids: list) -> dict:
    """Batch fetch users by IDs to avoid N+1 queries.
    
    Args:
        user_ids: List of user IDs to fetch
        
    Returns:
        Dictionary mapping user_id to user data
    """
    if not user_ids:
        return {}
    
    # Remove duplicates
    unique_ids = list(set(user_ids))
    
    # Batch fetch all users
    users = await db.users.find(
        {"id": {"$in": unique_ids}},
        {"_id": 0, "id": 1, "username": 1, "email": 1}
    ).to_list(len(unique_ids))
    
    # Create lookup dictionary
    return {user["id"]: user for user in users}


async def batch_fetch_categories(category_ids: list) -> dict:
    """Batch fetch categories by IDs.
    
    Args:
        category_ids: List of category IDs to fetch
        
    Returns:
        Dictionary mapping category_id to category data
    """
    if not category_ids:
        return {}
    
    unique_ids = list(set(category_ids))
    
    categories = await db.categories.find(
        {"id": {"$in": unique_ids}},
        {"_id": 0}
    ).to_list(len(unique_ids))
    
    return {cat["id"]: cat for cat in categories}


async def get_marketplace_protocols_optimized(category_filter: str = None, limit: int = 100):
    """Optimized marketplace protocols query using aggregation pipeline.
    
    This avoids N+1 queries by using $lookup to join with users collection.
    """
    pipeline = [
        # Match public protocols with price
        {"$match": {"is_public": True, "price": {"$gt": 0}}},
    ]
    
    # Add category filter if specified
    if category_filter and category_filter != "all":
        pipeline.append({
            "$match": {
                "$or": [
                    {"name": {"$regex": category_filter, "$options": "i"}},
                    {"protocol": {"$regex": category_filter, "$options": "i"}}
                ]
            }
        })
    
    # Join with users collection to get owner info
    pipeline.extend([
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "owner_info",
                "pipeline": [
                    {"$project": {"_id": 0, "username": 1, "id": 1}}
                ]
            }
        },
        {
            "$addFields": {
                "owner": {"$arrayElemAt": ["$owner_info", 0]}
            }
        },
        {"$project": {"owner_info": 0, "_id": 0}},
        {"$limit": limit}
    ])
    
    return await db.categories.aggregate(pipeline).to_list(limit)


async def get_leaderboard_optimized():
    """Optimized leaderboard query using aggregation pipelines."""
    
    # Top laughter points - single query with projection
    top_laughter = await db.users.find(
        {},
        {"_id": 0, "id": 1, "username": 1, "laughter_points": 1}
    ).sort("laughter_points", -1).limit(10).to_list(10)
    
    # Top protocol creators with user info in single aggregation
    pipeline = [
        {"$match": {"is_public": True}},
        {"$group": {"_id": "$user_id", "protocol_count": {"$sum": 1}}},
        {"$sort": {"protocol_count": -1}},
        {"$limit": 10},
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "id",
                "as": "user_info",
                "pipeline": [
                    {"$project": {"_id": 0, "id": 1, "username": 1}}
                ]
            }
        },
        {
            "$project": {
                "user": {"$arrayElemAt": ["$user_info", 0]},
                "protocol_count": 1,
                "_id": 0
            }
        }
    ]
    
    top_creators = await db.categories.aggregate(pipeline).to_list(10)
    
    return {
        "top_laughter_points": top_laughter,
        "top_protocol_creators": top_creators
    }


async def get_user_revenue_optimized(user_id: str):
    """Optimized revenue calculation using aggregation pipeline."""
    
    pipeline = [
        {"$match": {"seller_id": user_id, "status": "completed"}},
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": 1},
                "gross_revenue": {"$sum": "$price"},
                "sales": {"$push": {
                    "protocol_id": "$protocol_id",
                    "protocol_name": "$protocol_name",
                    "price": "$price",
                    "created_at": "$created_at"
                }}
            }
        }
    ]
    
    result = await db.purchases.aggregate(pipeline).to_list(1)
    
    if not result:
        return {
            "total_revenue": 0,
            "total_sales": 0,
            "monthly_revenue": {},
            "top_protocols": []
        }
    
    data = result[0]
    gross = data.get("gross_revenue", 0)
    seller_share = gross * 0.85  # 85% to seller
    
    # Calculate monthly breakdown in Python (more flexible)
    monthly_revenue = {}
    protocol_sales = {}
    
    for sale in data.get("sales", []):
        # Monthly breakdown
        month = sale["created_at"][:7]
        monthly_revenue[month] = monthly_revenue.get(month, 0) + (sale["price"] * 0.85)
        
        # Protocol breakdown
        pid = sale["protocol_id"]
        if pid not in protocol_sales:
            protocol_sales[pid] = {"name": sale["protocol_name"], "count": 0, "revenue": 0}
        protocol_sales[pid]["count"] += 1
        protocol_sales[pid]["revenue"] += sale["price"] * 0.85
    
    top_protocols = sorted(protocol_sales.values(), key=lambda x: x["revenue"], reverse=True)[:10]
    
    return {
        "total_revenue": round(seller_share, 2),
        "total_sales": data.get("total_sales", 0),
        "monthly_revenue": monthly_revenue,
        "top_protocols": top_protocols
    }
