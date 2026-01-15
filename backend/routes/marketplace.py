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

@router.post("/initiate-purchase", response_model=dict)
async def initiate_purchase(data: dict, user = Depends(get_current_user)):
    """
    Initiate a Pay-What-You-Want purchase flow.
    Returns PayPal payment URL for the user to complete.
    """
    from config import PAYPAL_PAYMENT_LINK
    
    protocol_id = data.get("protocol_id")
    custom_amount = data.get("amount")  # For Pay-What-You-Want
    
    if not protocol_id:
        raise HTTPException(status_code=400, detail="Protocol ID required")
    
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol["creator_id"] == str(user["_id"]):
        raise HTTPException(status_code=400, detail="You cannot purchase your own protocol")
    
    # Check if already purchased
    existing = await db.marketplace_purchases.find_one({
        "protocol_id": protocol_id,
        "user_id": str(user["_id"])
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You already own this protocol")
    
    # Pay-What-You-Want: Use custom amount or minimum price
    # Allow $0.00 (free) or any amount >= minimum price
    min_price = protocol.get("min_price", 0)  # Allow $0 for "Pay What You Want"
    suggested_price = protocol["price"]
    
    if custom_amount is not None:
        if custom_amount < 0:
            raise HTTPException(status_code=400, detail="Amount cannot be negative")
        final_amount = custom_amount
    else:
        final_amount = suggested_price
    
    # Create pending purchase record
    pending = {
        "protocol_id": protocol_id,
        "user_id": str(user["_id"]),
        "amount": final_amount,
        "suggested_price": suggested_price,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = await db.pending_purchases.insert_one(pending)
    pending_id = str(result.inserted_id)
    
    # Generate PayPal payment URL
    # If amount is 0, skip payment and complete immediately
    if final_amount == 0:
        # Free purchase - complete immediately
        return await complete_free_purchase(protocol_id, str(user["_id"]), pending_id)
    
    # PayPal payment link with amount
    payment_url = PAYPAL_PAYMENT_LINK or f"https://www.paypal.com/paypalme/TopPilotEnterprises/{final_amount}"
    
    return {
        "success": True,
        "pending_id": pending_id,
        "payment_url": payment_url,
        "amount": final_amount,
        "protocol_name": protocol["name"],
        "message": f"Complete payment of ${final_amount:.2f} via PayPal, then confirm your purchase."
    }


async def complete_free_purchase(protocol_id: str, user_id: str, pending_id: str):
    """Complete a free ($0) purchase"""
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    
    # Record purchase
    purchase_record = {
        "protocol_id": protocol_id,
        "user_id": user_id,
        "payment_id": f"FREE-{pending_id}",
        "price": 0,
        "creator_earnings": 0,
        "platform_fee": 0,
        "status": "completed",
        "is_free": True,
        "created_at": datetime.utcnow()
    }
    
    await db.marketplace_purchases.insert_one(purchase_record)
    
    # Update protocol stats
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(protocol_id)},
        {"$inc": {"total_sales": 1}}
    )
    
    # Mark pending as completed
    await db.pending_purchases.update_one(
        {"_id": ObjectId(pending_id)},
        {"$set": {"status": "completed"}}
    )
    
    return {
        "success": True,
        "message": "Protocol acquired for FREE! You're amazing!",
        "protocol": protocol["protocol"],
        "name": protocol["name"],
        "is_free": True
    }


@router.post("/confirm-payment", response_model=dict)
async def confirm_payment(data: dict, user = Depends(get_current_user)):
    """
    Confirm PayPal payment and complete purchase.
    Handles revenue splitting and accumulated payouts for amounts < $1.00.
    """
    protocol_id = data.get("protocol_id")
    transaction_id = data.get("transaction_id")
    amount = data.get("amount", 0)
    
    if not protocol_id or not transaction_id:
        raise HTTPException(status_code=400, detail="Protocol ID and Transaction ID required")
    
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check if already purchased
    existing = await db.marketplace_purchases.find_one({
        "protocol_id": protocol_id,
        "user_id": str(user["_id"])
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You already own this protocol")
    
    # Get current platform fee rate
    platform_fee_rate = await get_platform_fee()
    
    # Calculate revenue split
    creator_share = amount * (1 - platform_fee_rate)
    platform_share = amount * platform_fee_rate
    
    # Record purchase
    purchase_record = {
        "protocol_id": protocol_id,
        "user_id": str(user["_id"]),
        "payment_id": transaction_id,
        "price": amount,
        "creator_earnings": creator_share,
        "platform_fee": platform_share,
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.marketplace_purchases.insert_one(purchase_record)
    
    # Update protocol stats
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(protocol_id)},
        {
            "$inc": {
                "total_sales": 1,
                "total_revenue": amount,
                "creator_earnings": creator_share
            }
        }
    )
    
    # Update creator's accumulated earnings (for PayPal minimum payout handling)
    creator_id = protocol["creator_id"]
    await db.users.update_one(
        {"_id": ObjectId(creator_id)},
        {"$inc": {"accumulated_earnings": creator_share}}
    )
    
    # Update admin's accumulated platform fees
    admin_users = await db.users.find({"is_admin": True}).to_list(10)
    if admin_users:
        per_admin_share = platform_share / len(admin_users)
        for admin in admin_users:
            await db.users.update_one(
                {"_id": admin["_id"]},
                {"$inc": {"accumulated_platform_fees": per_admin_share}}
            )
    
    # Record in payout ledger for tracking
    await db.payout_ledger.insert_one({
        "purchase_id": str(purchase_record.get("_id", transaction_id)),
        "protocol_id": protocol_id,
        "creator_id": creator_id,
        "creator_share": creator_share,
        "platform_share": platform_share,
        "total_amount": amount,
        "status": "accumulated",  # Will change to "paid" when threshold met
        "created_at": datetime.utcnow()
    })
    
    # Check if creator has reached payout threshold
    creator = await db.users.find_one({"_id": ObjectId(creator_id)})
    accumulated = creator.get("accumulated_earnings", 0) if creator else 0
    payout_message = ""
    
    if accumulated >= PAYPAL_MIN_PAYOUT:
        payout_message = f" Creator has ${accumulated:.2f} ready for payout!"
    else:
        remaining = PAYPAL_MIN_PAYOUT - accumulated
        payout_message = f" Creator earnings: ${accumulated:.2f} (${remaining:.2f} more to reach payout threshold)"
    
    return {
        "success": True,
        "message": f"Protocol purchased successfully!{payout_message}",
        "protocol": protocol["protocol"],
        "name": protocol["name"],
        "amount_paid": amount,
        "creator_earned": creator_share,
        "platform_fee": platform_share
    }


@router.post("/purchase", response_model=dict)
async def purchase_protocol(purchase: MarketplacePurchase, user = Depends(get_current_user)):
    """Purchase a protocol from the marketplace (legacy endpoint)"""
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
    
    # Get current platform fee rate
    platform_fee_rate = await get_platform_fee()
    
    # Calculate earnings
    price = protocol["price"]
    creator_earnings = price * (1 - platform_fee_rate)
    platform_fee = price * platform_fee_rate
    
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
    
    # Update creator's accumulated earnings
    await db.users.update_one(
        {"_id": ObjectId(protocol["creator_id"])},
        {"$inc": {"accumulated_earnings": creator_earnings}}
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


# ==================== PAYOUT MANAGEMENT ====================

@router.get("/admin/payouts", response_model=dict)
async def get_pending_payouts(user = Depends(get_current_user)):
    """Get all users with accumulated earnings ready for payout (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find users with accumulated earnings >= minimum payout
    users_ready = await db.users.find({
        "accumulated_earnings": {"$gte": PAYPAL_MIN_PAYOUT}
    }).to_list(1000)
    
    # Find users with accumulated earnings < minimum (for reporting)
    users_accumulating = await db.users.find({
        "accumulated_earnings": {"$gt": 0, "$lt": PAYPAL_MIN_PAYOUT}
    }).to_list(1000)
    
    ready_for_payout = []
    accumulating = []
    
    for u in users_ready:
        ready_for_payout.append({
            "user_id": str(u["_id"]),
            "email": u.get("email", "Unknown"),
            "username": u.get("username", u.get("callsign", "Unknown")),
            "accumulated_earnings": u.get("accumulated_earnings", 0),
            "paypal_email": u.get("paypal_email", u.get("email", ""))
        })
    
    for u in users_accumulating:
        accumulating.append({
            "user_id": str(u["_id"]),
            "email": u.get("email", "Unknown"),
            "username": u.get("username", u.get("callsign", "Unknown")),
            "accumulated_earnings": u.get("accumulated_earnings", 0),
            "remaining_to_payout": PAYPAL_MIN_PAYOUT - u.get("accumulated_earnings", 0)
        })
    
    # Get admin's accumulated platform fees
    admin_fees = sum(a.get("accumulated_platform_fees", 0) for a in await db.users.find({"is_admin": True}).to_list(10))
    
    return {
        "ready_for_payout": ready_for_payout,
        "total_ready_amount": sum(u["accumulated_earnings"] for u in ready_for_payout),
        "accumulating": accumulating,
        "total_accumulating_amount": sum(u.get("accumulated_earnings", 0) for u in users_accumulating),
        "admin_platform_fees": admin_fees,
        "min_payout_threshold": PAYPAL_MIN_PAYOUT
    }


@router.post("/admin/process-payout", response_model=dict)
async def process_payout(data: dict, user = Depends(get_current_user)):
    """Mark a user's payout as processed (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user_id = data.get("user_id")
    paypal_transaction_id = data.get("paypal_transaction_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    amount = target_user.get("accumulated_earnings", 0)
    
    if amount < PAYPAL_MIN_PAYOUT:
        raise HTTPException(
            status_code=400, 
            detail=f"User has ${amount:.2f}, below minimum payout of ${PAYPAL_MIN_PAYOUT:.2f}"
        )
    
    # Record payout
    payout_record = {
        "user_id": user_id,
        "amount": amount,
        "paypal_transaction_id": paypal_transaction_id,
        "processed_by": str(user["_id"]),
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.payouts.insert_one(payout_record)
    
    # Reset user's accumulated earnings
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"accumulated_earnings": 0}}
    )
    
    # Update payout ledger entries
    await db.payout_ledger.update_many(
        {"creator_id": user_id, "status": "accumulated"},
        {"$set": {"status": "paid", "paid_at": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "message": f"Payout of ${amount:.2f} processed for user",
        "amount": amount,
        "user_id": user_id
    }


@router.get("/my-earnings", response_model=dict)
async def get_my_earnings(user = Depends(get_current_user)):
    """Get current user's accumulated earnings and payout status"""
    accumulated = user.get("accumulated_earnings", 0)
    
    # Get payout history
    payouts = await db.payouts.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(50)
    
    total_paid_out = sum(p.get("amount", 0) for p in payouts)
    
    return {
        "accumulated_earnings": accumulated,
        "ready_for_payout": accumulated >= PAYPAL_MIN_PAYOUT,
        "remaining_to_payout": max(0, PAYPAL_MIN_PAYOUT - accumulated),
        "min_payout_threshold": PAYPAL_MIN_PAYOUT,
        "total_paid_out": total_paid_out,
        "payout_history": [{
            "amount": p["amount"],
            "date": p["created_at"].isoformat(),
            "transaction_id": p.get("paypal_transaction_id", "N/A")
        } for p in payouts]
    }


@router.put("/my-paypal-email", response_model=dict)
async def update_paypal_email(data: dict, user = Depends(get_current_user)):
    """Update user's PayPal email for payouts"""
    paypal_email = data.get("paypal_email")
    
    if not paypal_email:
        raise HTTPException(status_code=400, detail="PayPal email required")
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"paypal_email": paypal_email}}
    )
    
    return {"success": True, "message": "PayPal email updated"}


# ==================== MAP DATA ====================

@router.get("/map-data", response_model=dict)
async def get_map_data():
    """Get all protocols with location data for the world map"""
    protocols = await db.marketplace_protocols.find({"status": "active"}).to_list(1000)
    
    # Generate location data for map display
    locations = [
        {"lat": 40.7128, "lng": -74.0060, "city": "New York", "country": "USA"},
        {"lat": 34.0522, "lng": -118.2437, "city": "Los Angeles", "country": "USA"},
        {"lat": 51.5074, "lng": -0.1278, "city": "London", "country": "UK"},
        {"lat": 48.8566, "lng": 2.3522, "city": "Paris", "country": "France"},
        {"lat": 35.6762, "lng": 139.6503, "city": "Tokyo", "country": "Japan"},
        {"lat": -33.8688, "lng": 151.2093, "city": "Sydney", "country": "Australia"},
        {"lat": 43.9108, "lng": -69.9669, "city": "Brunswick, ME", "country": "USA"},
        {"lat": 55.7558, "lng": 37.6173, "city": "Moscow", "country": "Russia"},
        {"lat": 19.4326, "lng": -99.1332, "city": "Mexico City", "country": "Mexico"},
        {"lat": -23.5505, "lng": -46.6333, "city": "São Paulo", "country": "Brazil"},
        {"lat": 52.5200, "lng": 13.4050, "city": "Berlin", "country": "Germany"},
        {"lat": 37.7749, "lng": -122.4194, "city": "San Francisco", "country": "USA"},
        {"lat": 1.3521, "lng": 103.8198, "city": "Singapore", "country": "Singapore"},
        {"lat": 22.3193, "lng": 114.1694, "city": "Hong Kong", "country": "China"},
        {"lat": 41.9028, "lng": 12.4964, "city": "Rome", "country": "Italy"},
    ]
    
    map_data = []
    for i, p in enumerate(protocols):
        loc = locations[i % len(locations)]
        map_data.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "lat": loc["lat"],
            "lng": loc["lng"],
            "city": loc["city"],
            "country": loc["country"],
            "total_sales": p.get("total_sales", 0)
        })
    
    return {
        "protocols": map_data,
        "total": len(map_data)
    }


# Import timedelta at the top
from datetime import timedelta
