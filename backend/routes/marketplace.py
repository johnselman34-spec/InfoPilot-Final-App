"""
InfoPilot Explorer - Protocol Marketplace Routes
Enables users to buy and sell search protocols
- Creators set their own prices ($0.99 - $99.99)
- Admin-controlled revenue split (default: 90% to creators, 10% platform fee)
- PayPal integration with minimum payout handling ($1.00 minimum)
- 100% FREE to browse and search!
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

from config import db, logger, MARKETPLACE_PLATFORM_FEE, MARKETPLACE_MIN_PRICE, MARKETPLACE_MAX_PRICE, PAYPAL_CLIENT_ID
from models.schemas import MarketplaceProtocolCreate, MarketplacePurchase, ProtocolReview
from routes.auth import get_current_user, get_optional_user
from services.protocol_service import ProtocolParser

router = APIRouter(prefix="/marketplace", tags=["Protocol Marketplace"])

# PayPal minimum payout threshold
PAYPAL_MIN_PAYOUT = 1.00


# ==================== ADMIN REVENUE SETTINGS ====================

@router.get("/admin/revenue-settings", response_model=dict)
async def get_revenue_settings(user = Depends(get_current_user)):
    """Get current revenue distribution settings (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await db.app_settings.find_one({"key": "marketplace_revenue"})
    
    if not settings:
        # Default settings
        return {
            "admin_percent": 10,
            "creator_percent": 90,
            "paypal_min_payout": PAYPAL_MIN_PAYOUT
        }
    
    return {
        "admin_percent": settings.get("admin_percent", 10),
        "creator_percent": 100 - settings.get("admin_percent", 10),
        "paypal_min_payout": PAYPAL_MIN_PAYOUT
    }


@router.put("/admin/revenue-settings", response_model=dict)
async def update_revenue_settings(settings: dict, user = Depends(get_current_user)):
    """Update revenue distribution settings (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    admin_percent = settings.get("admin_percent", 10)
    
    # Validate percentage (5-30%)
    if admin_percent < 5 or admin_percent > 30:
        raise HTTPException(status_code=400, detail="Admin percentage must be between 5% and 30%")
    
    await db.app_settings.update_one(
        {"key": "marketplace_revenue"},
        {"$set": {
            "key": "marketplace_revenue",
            "admin_percent": admin_percent,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    return {
        "success": True,
        "admin_percent": admin_percent,
        "creator_percent": 100 - admin_percent
    }


async def get_platform_fee():
    """Get current platform fee percentage"""
    settings = await db.app_settings.find_one({"key": "marketplace_revenue"})
    if settings:
        return settings.get("admin_percent", 10) / 100
    return MARKETPLACE_PLATFORM_FEE  # Default 10%


# ==================== PROTOCOL LISTINGS ====================

@router.get("/protocols", response_model=dict)
async def list_marketplace_protocols(
    category: Optional[str] = None,
    sort: str = Query("popular", regex="^(popular|newest|price_low|price_high|rating)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user = Depends(get_optional_user)
):
    """List all available protocols in the marketplace"""
    query = {"status": "active"}
    
    if category:
        query["category"] = category
    
    # Sorting
    sort_options = {
        "popular": [("total_sales", -1), ("created_at", -1)],
        "newest": [("created_at", -1)],
        "price_low": [("price", 1)],
        "price_high": [("price", -1)],
        "rating": [("rating", -1), ("review_count", -1)]
    }
    
    sort_by = sort_options.get(sort, [("total_sales", -1)])
    
    skip = (page - 1) * limit
    
    protocols = await db.marketplace_protocols.find(query).sort(sort_by).skip(skip).limit(limit).to_list(limit)
    total = await db.marketplace_protocols.count_documents(query)
    
    # Get user's purchases if logged in
    user_purchases = set()
    if user:
        purchases = await db.marketplace_purchases.find({"user_id": str(user["_id"])}).to_list(1000)
        user_purchases = {p["protocol_id"] for p in purchases}
    
    formatted = []
    for p in protocols:
        formatted.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "description": p["description"],
            "protocol": p["protocol"] if str(p["_id"]) in user_purchases or (user and str(user["_id"]) == p["creator_id"]) else None,
            "price": p["price"],
            "category": p["category"],
            "tags": p.get("tags", []),
            "creator_id": p["creator_id"],
            "creator_name": p["creator_name"],
            "total_sales": p.get("total_sales", 0),
            "rating": p.get("rating", 0),
            "review_count": p.get("review_count", 0),
            "created_at": p["created_at"].isoformat(),
            "is_featured": p.get("is_featured", False),
            "is_owned": str(p["_id"]) in user_purchases or (user and str(user["_id"]) == p["creator_id"]),
            "preview_results": p.get("preview_results", 3)
        })
    
    return {
        "protocols": formatted,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/protocols/{protocol_id}", response_model=dict)
async def get_marketplace_protocol(protocol_id: str, user = Depends(get_optional_user)):
    """Get details of a specific marketplace protocol"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check if user owns this protocol
    is_owned = False
    if user:
        purchase = await db.marketplace_purchases.find_one({
            "protocol_id": protocol_id,
            "user_id": str(user["_id"])
        })
        is_owned = purchase is not None or str(user["_id"]) == protocol["creator_id"]
    
    # Get reviews
    reviews = await db.marketplace_reviews.find({"protocol_id": protocol_id}).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "id": str(protocol["_id"]),
        "name": protocol["name"],
        "description": protocol["description"],
        "protocol": protocol["protocol"] if is_owned else None,
        "price": protocol["price"],
        "category": protocol["category"],
        "tags": protocol.get("tags", []),
        "creator_id": protocol["creator_id"],
        "creator_name": protocol["creator_name"],
        "total_sales": protocol.get("total_sales", 0),
        "total_revenue": protocol.get("total_revenue", 0) if is_owned and str(user["_id"]) == protocol["creator_id"] else None,
        "rating": protocol.get("rating", 0),
        "review_count": protocol.get("review_count", 0),
        "created_at": protocol["created_at"].isoformat(),
        "is_owned": is_owned,
        "reviews": [{
            "rating": r["rating"],
            "review": r.get("review", ""),
            "user_name": r.get("user_name", "Anonymous"),
            "created_at": r["created_at"].isoformat()
        } for r in reviews]
    }


@router.post("/protocols", response_model=dict)
async def create_marketplace_protocol(protocol: MarketplaceProtocolCreate, user = Depends(get_current_user)):
    """List a new protocol for sale in the marketplace"""
    # Validate price
    if protocol.price < MARKETPLACE_MIN_PRICE or protocol.price > MARKETPLACE_MAX_PRICE:
        raise HTTPException(
            status_code=400, 
            detail=f"Price must be between ${MARKETPLACE_MIN_PRICE} and ${MARKETPLACE_MAX_PRICE}"
        )
    
    # Validate protocol
    is_valid, message = ProtocolParser.validate_protocol(protocol.protocol)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid protocol: {message}")
    
    # Create listing
    listing = {
        "name": protocol.name,
        "description": protocol.description,
        "protocol": protocol.protocol,
        "price": protocol.price,
        "category": protocol.category,
        "tags": protocol.tags,
        "creator_id": str(user["_id"]),
        "creator_name": user.get("username", user.get("callsign", "Anonymous")),
        "total_sales": 0,
        "total_revenue": 0,
        "creator_earnings": 0,
        "rating": 0,
        "review_count": 0,
        "preview_results": protocol.preview_results,
        "status": "active",
        "is_featured": False,
        "created_at": datetime.utcnow()
    }
    
    result = await db.marketplace_protocols.insert_one(listing)
    listing["_id"] = result.inserted_id
    
    return {
        "id": str(listing["_id"]),
        "message": "Protocol listed successfully!",
        "name": listing["name"],
        "price": listing["price"]
    }


@router.put("/protocols/{protocol_id}", response_model=dict)
async def update_marketplace_protocol(protocol_id: str, update: dict, user = Depends(get_current_user)):
    """Update a marketplace protocol listing"""
    protocol = await db.marketplace_protocols.find_one({
        "_id": ObjectId(protocol_id),
        "creator_id": str(user["_id"])
    })
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or not owned by you")
    
    allowed_fields = ["name", "description", "price", "category", "tags"]
    update_data = {k: v for k, v in update.items() if k in allowed_fields}
    
    if "price" in update_data:
        if update_data["price"] < MARKETPLACE_MIN_PRICE or update_data["price"] > MARKETPLACE_MAX_PRICE:
            raise HTTPException(status_code=400, detail=f"Price must be between ${MARKETPLACE_MIN_PRICE} and ${MARKETPLACE_MAX_PRICE}")
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.marketplace_protocols.update_one(
            {"_id": ObjectId(protocol_id)},
            {"$set": update_data}
        )
    
    return {"success": True, "message": "Protocol updated"}


@router.delete("/protocols/{protocol_id}")
async def delete_marketplace_protocol(protocol_id: str, user = Depends(get_current_user)):
    """Remove a protocol from the marketplace"""
    protocol = await db.marketplace_protocols.find_one({
        "_id": ObjectId(protocol_id),
        "creator_id": str(user["_id"])
    })
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or not owned by you")
    
    # Soft delete - mark as inactive
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(protocol_id)},
        {"$set": {"status": "inactive", "deleted_at": datetime.utcnow()}}
    )
    
    return {"success": True, "message": "Protocol removed from marketplace"}


# ==================== PURCHASES ====================

@router.post("/purchase", response_model=dict)
async def purchase_protocol(purchase: MarketplacePurchase, user = Depends(get_current_user)):
    """Purchase a protocol from the marketplace"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(purchase.protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol["creator_id"] == str(user["_id"]):
        raise HTTPException(status_code=400, detail="You cannot purchase your own protocol")
    
    # Check if already purchased
    existing = await db.marketplace_purchases.find_one({
        "protocol_id": purchase.protocol_id,
        "user_id": str(user["_id"])
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You already own this protocol")
    
    # Calculate earnings (90% to creator, 10% platform)
    price = protocol["price"]
    creator_earnings = price * (1 - MARKETPLACE_PLATFORM_FEE)  # 90%
    platform_fee = price * MARKETPLACE_PLATFORM_FEE  # 10%
    
    # Record purchase
    purchase_record = {
        "protocol_id": purchase.protocol_id,
        "user_id": str(user["_id"]),
        "payment_id": purchase.payment_id,
        "price": price,
        "creator_earnings": creator_earnings,
        "platform_fee": platform_fee,
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.marketplace_purchases.insert_one(purchase_record)
    
    # Update protocol stats
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(purchase.protocol_id)},
        {
            "$inc": {
                "total_sales": 1,
                "total_revenue": price,
                "creator_earnings": creator_earnings
            }
        }
    )
    
    # Update creator's earnings balance
    await db.users.update_one(
        {"_id": ObjectId(protocol["creator_id"])},
        {"$inc": {"marketplace_earnings": creator_earnings}}
    )
    
    return {
        "success": True,
        "message": "Protocol purchased successfully!",
        "protocol": protocol["protocol"],
        "name": protocol["name"]
    }


@router.get("/purchases", response_model=dict)
async def get_my_purchases(user = Depends(get_current_user)):
    """Get all protocols purchased by the current user"""
    purchases = await db.marketplace_purchases.find({"user_id": str(user["_id"])}).to_list(1000)
    
    protocols = []
    for p in purchases:
        protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(p["protocol_id"])})
        if protocol:
            protocols.append({
                "id": str(protocol["_id"]),
                "name": protocol["name"],
                "protocol": protocol["protocol"],
                "category": protocol["category"],
                "purchased_at": p["created_at"].isoformat(),
                "price_paid": p["price"]
            })
    
    return {"purchases": protocols, "count": len(protocols)}


# ==================== REVIEWS ====================

@router.post("/reviews", response_model=dict)
async def create_review(review: ProtocolReview, user = Depends(get_current_user)):
    """Leave a review for a purchased protocol"""
    # Check if user purchased this protocol
    purchase = await db.marketplace_purchases.find_one({
        "protocol_id": review.protocol_id,
        "user_id": str(user["_id"])
    })
    
    if not purchase:
        raise HTTPException(status_code=400, detail="You must purchase a protocol before reviewing it")
    
    # Check for existing review
    existing = await db.marketplace_reviews.find_one({
        "protocol_id": review.protocol_id,
        "user_id": str(user["_id"])
    })
    
    if existing:
        # Update existing review
        await db.marketplace_reviews.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "rating": review.rating,
                "review": review.review,
                "updated_at": datetime.utcnow()
            }}
        )
    else:
        # Create new review
        await db.marketplace_reviews.insert_one({
            "protocol_id": review.protocol_id,
            "user_id": str(user["_id"]),
            "user_name": user.get("username", "Anonymous"),
            "rating": review.rating,
            "review": review.review,
            "created_at": datetime.utcnow()
        })
    
    # Update protocol rating
    reviews = await db.marketplace_reviews.find({"protocol_id": review.protocol_id}).to_list(1000)
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0
    
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(review.protocol_id)},
        {"$set": {"rating": avg_rating, "review_count": len(reviews)}}
    )
    
    return {"success": True, "message": "Review submitted"}


# ==================== SELLER DASHBOARD ====================

@router.get("/seller/dashboard", response_model=dict)
async def get_seller_dashboard(user = Depends(get_current_user)):
    """Get seller dashboard with sales stats"""
    # Get all protocols by this user
    protocols = await db.marketplace_protocols.find({"creator_id": str(user["_id"])}).to_list(1000)
    
    total_sales = 0
    total_revenue = 0
    total_earnings = 0
    
    listings = []
    for p in protocols:
        sales = p.get("total_sales", 0)
        revenue = p.get("total_revenue", 0)
        earnings = p.get("creator_earnings", 0)
        
        total_sales += sales
        total_revenue += revenue
        total_earnings += earnings
        
        listings.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "price": p["price"],
            "sales": sales,
            "revenue": revenue,
            "earnings": earnings,
            "rating": p.get("rating", 0),
            "status": p.get("status", "active"),
            "created_at": p["created_at"].isoformat()
        })
    
    return {
        "total_listings": len(protocols),
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_earnings": total_earnings,
        "platform_fee_rate": MARKETPLACE_PLATFORM_FEE * 100,  # 10%
        "listings": listings
    }


# ==================== SUBSCRIPTION ====================

@router.post("/subscription", response_model=dict)
async def create_subscription(subscription: dict, user = Depends(get_current_user)):
    """Subscribe to the marketplace for unlimited protocol access"""
    plan = subscription.get("plan", "monthly")
    payment_id = subscription.get("payment_id")
    
    if plan not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'monthly' or 'yearly'")
    
    prices = {"monthly": 9.99, "yearly": 99.99}
    
    # Create subscription record
    sub_record = {
        "user_id": str(user["_id"]),
        "plan": plan,
        "price": prices[plan],
        "payment_id": payment_id,
        "status": "active",
        "started_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + (
            timedelta(days=30) if plan == "monthly" else timedelta(days=365)
        )
    }
    
    await db.marketplace_subscriptions.insert_one(sub_record)
    
    # Update user
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"marketplace_subscription": True, "subscription_plan": plan}}
    )
    
    return {
        "success": True,
        "message": f"Subscribed to {plan} plan!",
        "plan": plan,
        "price": prices[plan]
    }


@router.get("/subscription/status", response_model=dict)
async def get_subscription_status(user = Depends(get_current_user)):
    """Get current subscription status"""
    sub = await db.marketplace_subscriptions.find_one({
        "user_id": str(user["_id"]),
        "status": "active"
    })
    
    return {
        "subscribed": sub is not None,
        "plan": sub.get("plan") if sub else None,
        "expires_at": sub["expires_at"].isoformat() if sub else None
    }


# ==================== CATEGORIES ====================

@router.get("/categories", response_model=dict)
async def get_marketplace_categories():
    """Get all marketplace categories with counts"""
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    result = await db.marketplace_protocols.aggregate(pipeline).to_list(100)
    
    return {
        "categories": [{"name": r["_id"], "count": r["count"]} for r in result]
    }


# ==================== PAYPAL CONFIG ====================

@router.get("/paypal-config", response_model=dict)
async def get_paypal_config():
    """Get PayPal client configuration"""
    return {
        "client_id": PAYPAL_CLIENT_ID,
        "currency": "USD"
    }


# Import timedelta at the top
from datetime import timedelta
