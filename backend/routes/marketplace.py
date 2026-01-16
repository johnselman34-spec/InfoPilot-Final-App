"""
InfoPilot Explorer - Protocol Marketplace Routes
Enables users to buy and sell search protocols
- Creators set their own prices ($0.99 - $99.99)
- Admin-controlled revenue split (default: 90% to creators, 10% platform fee)
- PayPal integration with minimum payout handling ($1.00 minimum)
- 100% FREE to browse and search!
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId

from config import db, logger, MARKETPLACE_PLATFORM_FEE, MARKETPLACE_MIN_PRICE, MARKETPLACE_MAX_PRICE, PAYPAL_CLIENT_ID
from models.schemas import MarketplaceProtocolCreate, MarketplacePurchase, ProtocolReview
from routes.auth import get_current_user, get_optional_user
from services.protocol_service import ProtocolParser

router = APIRouter(prefix="/marketplace", tags=["Protocol Marketplace"])

# PayPal Payment Configuration
# =============================
# PayPal requires minimum $1.00 for transactions
# For low-price protocols, the platform fee may be less than $1.00
# Solution: Accumulate creator earnings until threshold is met

PAYPAL_MIN_PAYOUT = 1.00  # Minimum accumulated before payout

# Minimum protocol price for paid protocols (free protocols allowed)
MINIMUM_PAID_PROTOCOL_PRICE = 0.99

# Platform fee configuration (admin configurable, default 15%)
# At 15% fee: $6.67 protocol = $1.00 fee
# Below this, fees accumulate until threshold is met
DEFAULT_PLATFORM_FEE_PERCENT = 15


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
        # Determine if protocol is free (either by is_free flag or price == 0)
        is_free = p.get("is_free", False) or p.get("price", 0) == 0
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
            "is_free": is_free,  # Include is_free flag for FREE badge display
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
    """List a new protocol for sale in the marketplace (or FREE!)"""
    # Validate price - allow $0.00 (FREE) up to $99.99
    if protocol.price < MARKETPLACE_MIN_PRICE or protocol.price > MARKETPLACE_MAX_PRICE:
        raise HTTPException(
            status_code=400, 
            detail=f"Price must be between ${MARKETPLACE_MIN_PRICE} and ${MARKETPLACE_MAX_PRICE}"
        )
    
    # Validate protocol
    is_valid, message = ProtocolParser.validate_protocol(protocol.protocol)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid protocol: {message}")
    
    # Determine if protocol is free
    is_free = protocol.price == 0 or protocol.price < 0.01
    
    # Validate price for unpaid users
    is_paid_user = user.get("subscription_active") or user.get("is_admin")
    if not is_paid_user and not is_free:
        # Check if price controls are enabled
        control_enabled = await db.settings.find_one({"key": "unpaid_price_control_enabled"})
        if control_enabled and control_enabled.get("value"):
            # Check if unpaid users can sell
            can_sell = await db.settings.find_one({"key": "unpaid_can_sell"})
            if can_sell and not can_sell.get("value"):
                raise HTTPException(
                    status_code=403, 
                    detail="Unpaid users are not currently allowed to sell. Please upgrade to Premium!"
                )
            
            # Check max price
            max_price_setting = await db.settings.find_one({"key": "unpaid_max_protocol_price"})
            max_price = max_price_setting.get("value", 5.00) if max_price_setting else 5.00
            
            if protocol.price > max_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unpaid users can only charge up to ${max_price:.2f}. Upgrade to Premium for higher prices!"
                )
    
    # Create listing
    listing = {
        "name": protocol.name,
        "description": protocol.description,
        "protocol": protocol.protocol,
        "price": 0.0 if is_free else protocol.price,
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
        "is_free": is_free,  # New field for FREE protocols
        "clipboard_copies": 0,  # Track clipboard copies
        "created_at": datetime.utcnow()
    }
    
    result = await db.marketplace_protocols.insert_one(listing)
    listing["_id"] = result.inserted_id
    
    free_message = " 🎉 Your protocol is FREE for everyone to copy!" if is_free else ""
    
    return {
        "id": str(listing["_id"]),
        "message": f"Protocol listed successfully!{free_message}",
        "name": listing["name"],
        "price": listing["price"],
        "is_free": is_free
    }


@router.post("/protocols/{protocol_id}/copy", response_model=dict)
async def copy_protocol_to_clipboard(protocol_id: str, user = Depends(get_optional_user)):
    """
    Track when a protocol is copied to clipboard.
    FREE protocols can be copied by anyone.
    Paid protocols require purchase.
    """
    protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    is_free = protocol.get("is_free", False) or protocol.get("price", 0) == 0
    
    # Check if user can copy
    if not is_free and user:
        # Check if user owns this protocol
        is_owner = protocol["creator_id"] == str(user["_id"])
        is_purchased = await db.marketplace_purchases.find_one({
            "protocol_id": protocol_id,
            "user_id": str(user["_id"])
        }) is not None
        
        if not is_owner and not is_purchased:
            raise HTTPException(
                status_code=403, 
                detail="Purchase this protocol to copy it, or check out our FREE protocols!"
            )
    elif not is_free and not user:
        raise HTTPException(
            status_code=401, 
            detail="Please log in to copy paid protocols, or browse our FREE protocols!"
        )
    
    # Track the copy
    await db.marketplace_protocols.update_one(
        {"_id": ObjectId(protocol_id)},
        {"$inc": {"clipboard_copies": 1}}
    )
    
    return {
        "success": True,
        "protocol": protocol["protocol"],
        "name": protocol["name"],
        "is_free": is_free,
        "message": "Protocol copied to clipboard! 📋" + (" (FREE!)" if is_free else "")
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
    
    # Bulk fetch all protocols at once (N+1 query optimization)
    protocol_ids = [ObjectId(p["protocol_id"]) for p in purchases if p.get("protocol_id")]
    protocols_map = {}
    
    if protocol_ids:
        protocols_cursor = db.marketplace_protocols.find({"_id": {"$in": protocol_ids}})
        async for protocol in protocols_cursor:
            protocols_map[str(protocol["_id"])] = protocol
    
    # Build response
    result = []
    for p in purchases:
        protocol = protocols_map.get(p["protocol_id"])
        if protocol:
            result.append({
                "id": str(protocol["_id"]),
                "name": protocol["name"],
                "protocol": protocol["protocol"],
                "protocol_string": protocol["protocol"],  # Also include as protocol_string for frontend
                "category": protocol["category"],
                "purchased_at": p["created_at"].isoformat(),
                "price_paid": p["price"],
                "price": p["price"]
            })
    
    return {"purchases": result, "count": len(result)}


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


@router.get("/my-protocols")
async def get_my_protocols(user = Depends(get_current_user)):
    """Get all protocols created by the current user for the ProtocolRecommendationEngine"""
    user_id = str(user["_id"])
    
    # Get all protocols by this user
    protocols = await db.marketplace_protocols.find({"creator_id": user_id}).to_list(1000)
    
    result = []
    for p in protocols:
        result.append({
            "id": str(p["_id"]),
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "price": p.get("price", 0),
            "category": p.get("category", "General"),
            "total_sales": p.get("total_sales", 0),
            "rating": p.get("rating", 0),
            "status": p.get("status", "active"),
            "created_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    return result


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


# ==================== BATCH PAYOUT SYSTEM ====================

@router.get("/admin/payout-batch", response_model=dict)
async def get_payout_batch(user = Depends(get_current_user)):
    """
    Get a batch of users ready for payout (admin only).
    Batches users with accumulated earnings >= $1.00 for efficient PayPal mass pay.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find all users ready for payout
    ready_users = await db.users.find({
        "accumulated_earnings": {"$gte": PAYPAL_MIN_PAYOUT},
        "paypal_email": {"$exists": True, "$nin": [None, ""]}
    }).to_list(1000)
    
    batch = []
    total_amount = 0
    
    for u in ready_users:
        amount = u.get("accumulated_earnings", 0)
        batch.append({
            "user_id": str(u["_id"]),
            "email": u.get("email"),
            "paypal_email": u.get("paypal_email", u.get("email")),
            "username": u.get("username", u.get("callsign", "Unknown")),
            "amount": round(amount, 2)
        })
        total_amount += amount
    
    # Generate batch ID
    batch_id = f"BATCH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "batch_id": batch_id,
        "users": batch,
        "total_users": len(batch),
        "total_amount": round(total_amount, 2),
        "min_payout_threshold": PAYPAL_MIN_PAYOUT,
        "created_at": datetime.utcnow().isoformat()
    }


@router.post("/admin/process-batch-payout", response_model=dict)
async def process_batch_payout(data: dict, user = Depends(get_current_user)):
    """
    Process a batch payout (admin only).
    Marks all users in the batch as paid and resets their accumulated earnings.
    """
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    batch_id = data.get("batch_id")
    paypal_batch_id = data.get("paypal_batch_id")  # PayPal's batch transaction ID
    user_ids = data.get("user_ids", [])
    
    if not user_ids:
        raise HTTPException(status_code=400, detail="No users in batch")
    
    processed = []
    errors = []
    total_amount = 0
    
    for uid in user_ids:
        try:
            target_user = await db.users.find_one({"_id": ObjectId(uid)})
            if not target_user:
                errors.append({"user_id": uid, "error": "User not found"})
                continue
            
            amount = target_user.get("accumulated_earnings", 0)
            
            if amount < PAYPAL_MIN_PAYOUT:
                errors.append({"user_id": uid, "error": f"Below minimum: ${amount:.2f}"})
                continue
            
            # Record payout
            payout_record = {
                "user_id": uid,
                "amount": amount,
                "paypal_batch_id": paypal_batch_id,
                "internal_batch_id": batch_id,
                "processed_by": str(user["_id"]),
                "status": "completed",
                "payout_type": "batch",
                "created_at": datetime.utcnow()
            }
            
            await db.payouts.insert_one(payout_record)
            
            # Reset accumulated earnings
            await db.users.update_one(
                {"_id": ObjectId(uid)},
                {"$set": {"accumulated_earnings": 0}}
            )
            
            # Update payout ledger
            await db.payout_ledger.update_many(
                {"creator_id": uid, "status": "accumulated"},
                {"$set": {"status": "paid", "paid_at": datetime.utcnow(), "batch_id": batch_id}}
            )
            
            processed.append({
                "user_id": uid,
                "amount": amount,
                "paypal_email": target_user.get("paypal_email", target_user.get("email"))
            })
            total_amount += amount
            
        except Exception as e:
            errors.append({"user_id": uid, "error": str(e)})
    
    return {
        "success": True,
        "batch_id": batch_id,
        "paypal_batch_id": paypal_batch_id,
        "processed": processed,
        "processed_count": len(processed),
        "total_amount": round(total_amount, 2),
        "errors": errors,
        "error_count": len(errors)
    }


@router.get("/admin/payout-settings", response_model=dict)
async def get_payout_settings(user = Depends(get_current_user)):
    """Get payout configuration settings (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await db.app_settings.find_one({"key": "payout_settings"})
    
    default_settings = {
        "min_payout_threshold": PAYPAL_MIN_PAYOUT,
        "auto_payout_enabled": False,
        "auto_payout_day": "friday",  # Day of week for auto payouts
        "auto_payout_hour": 14,  # 2 PM UTC
        "batch_limit": 100  # Max users per batch
    }
    
    if settings:
        # Exclude MongoDB _id from response
        settings_dict = {k: v for k, v in settings.items() if k != "_id"}
        default_settings.update(settings_dict)
    
    return default_settings


@router.put("/admin/payout-settings", response_model=dict)
async def update_payout_settings(data: dict, user = Depends(get_current_user)):
    """Update payout configuration settings (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    allowed_keys = ["auto_payout_enabled", "auto_payout_day", "auto_payout_hour", "batch_limit"]
    update_data = {k: v for k, v in data.items() if k in allowed_keys}
    update_data["key"] = "payout_settings"
    update_data["updated_at"] = datetime.utcnow()
    
    await db.app_settings.update_one(
        {"key": "payout_settings"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"success": True, "message": "Payout settings updated", "settings": update_data}


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


# ==================== TOP SELLERS LEADERBOARD ====================

@router.get("/leaderboard/sales", response_model=dict)
async def get_leaderboard_by_sales():
    """Get top sellers by total sales count"""
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": "$creator_id",
            "creator_name": {"$first": "$creator_name"},
            "total_sales": {"$sum": "$total_sales"},
            "protocol_count": {"$sum": 1},
            "avg_rating": {"$avg": "$rating"}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": 20}
    ]
    
    results = await db.marketplace_protocols.aggregate(pipeline).to_list(20)
    
    leaderboard = []
    for i, r in enumerate(results):
        user = await db.users.find_one({"_id": ObjectId(r["_id"])}) if r["_id"] else None
        leaderboard.append({
            "rank": i + 1,
            "creator_id": r["_id"],
            "creator_name": r["creator_name"] or (user.get("callsign") if user else "Unknown"),
            "total_sales": r["total_sales"],
            "protocol_count": r["protocol_count"],
            "avg_rating": round(r["avg_rating"] or 0, 1),
            "badge": _get_seller_badge(r["total_sales"]),
            "title": _get_seller_title(i + 1)
        })
    
    return {
        "leaderboard": leaderboard,
        "last_updated": datetime.utcnow().isoformat(),
        "type": "sales"
    }


@router.get("/leaderboard/revenue", response_model=dict)
async def get_leaderboard_by_revenue():
    """Get top sellers by total revenue earned"""
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": "$creator_id",
            "creator_name": {"$first": "$creator_name"},
            "total_revenue": {"$sum": "$total_revenue"},
            "creator_earnings": {"$sum": "$creator_earnings"},
            "total_sales": {"$sum": "$total_sales"},
            "protocol_count": {"$sum": 1}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 20}
    ]
    
    results = await db.marketplace_protocols.aggregate(pipeline).to_list(20)
    
    leaderboard = []
    for i, r in enumerate(results):
        user = await db.users.find_one({"_id": ObjectId(r["_id"])}) if r["_id"] else None
        leaderboard.append({
            "rank": i + 1,
            "creator_id": r["_id"],
            "creator_name": r["creator_name"] or (user.get("callsign") if user else "Unknown"),
            "total_revenue": round(r["total_revenue"], 2),
            "creator_earnings": round(r["creator_earnings"], 2),
            "total_sales": r["total_sales"],
            "protocol_count": r["protocol_count"],
            "badge": _get_revenue_badge(r["total_revenue"]),
            "title": _get_revenue_title(i + 1)
        })
    
    return {
        "leaderboard": leaderboard,
        "last_updated": datetime.utcnow().isoformat(),
        "type": "revenue"
    }


@router.get("/leaderboard", response_model=dict)
async def get_community_leaderboard(timeRange: str = Query("all", description="Time range: all, month, week")):
    """
    Get comprehensive community leaderboard data for the CommunityLeaderboard component.
    Returns top creators, top protocols, rising stars, and monthly champions.
    """
    # Calculate date filters based on timeRange
    now = datetime.utcnow()
    if timeRange == "week":
        start_date = now - timedelta(days=7)
    elif timeRange == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = None
    
    # Build match filter
    match_filter = {"status": "active"}
    if start_date:
        match_filter["created_at"] = {"$gte": start_date}
    
    # TOP CREATORS - by total sales and downloads
    creators_pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": "$creator_id",
            "creator_name": {"$first": "$creator_name"},
            "protocols": {"$sum": 1},
            "downloads": {"$sum": "$total_sales"},
            "revenue": {"$sum": "$creator_earnings"}
        }},
        {"$sort": {"downloads": -1}},
        {"$limit": 10}
    ]
    
    creators_results = await db.marketplace_protocols.aggregate(creators_pipeline).to_list(10)
    
    top_creators = []
    for i, r in enumerate(creators_results):
        badge = "🏆" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
        user = await db.users.find_one({"_id": ObjectId(r["_id"])}) if r["_id"] else None
        username = r["creator_name"] or (user.get("callsign") if user else "Unknown")
        top_creators.append({
            "rank": i + 1,
            "username": username,
            "protocols": r["protocols"],
            "downloads": r["downloads"],
            "revenue": round(r["revenue"], 2),
            "badge": badge
        })
    
    # TOP PROTOCOLS - by downloads/sales
    protocols_pipeline = [
        {"$match": {"status": "active"}},
        {"$sort": {"total_sales": -1}},
        {"$limit": 10}
    ]
    
    protocols_results = await db.marketplace_protocols.aggregate(protocols_pipeline).to_list(10)
    
    top_protocols = []
    for i, p in enumerate(protocols_results):
        top_protocols.append({
            "rank": i + 1,
            "name": p.get("name", "Unknown Protocol"),
            "creator": p.get("creator_name", "Unknown"),
            "downloads": p.get("total_sales", 0),
            "rating": round(p.get("rating", 0), 1),
            "price": p.get("price", 0)
        })
    
    # RISING STARS - new creators with good performance (joined in last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    
    rising_pipeline = [
        {"$match": {"status": "active", "created_at": {"$gte": thirty_days_ago}}},
        {"$group": {
            "_id": "$creator_id",
            "creator_name": {"$first": "$creator_name"},
            "protocols": {"$sum": 1},
            "downloads": {"$sum": "$total_sales"},
            "first_created": {"$min": "$created_at"}
        }},
        {"$match": {"downloads": {"$gt": 0}}},
        {"$sort": {"downloads": -1}},
        {"$limit": 5}
    ]
    
    rising_results = await db.marketplace_protocols.aggregate(rising_pipeline).to_list(5)
    
    rising_stars = []
    for i, r in enumerate(rising_results):
        joined_days = (now - r.get("first_created", now)).days if r.get("first_created") else 0
        badge = "🌟" if i == 0 else "⭐" if i == 1 else "✨"
        growth = f"+{min(999, r['downloads'] * 10)}%"  # Simulated growth percentage
        rising_stars.append({
            "rank": i + 1,
            "username": r["creator_name"] or "Unknown",
            "joinedDays": joined_days,
            "protocols": r["protocols"],
            "downloads": r["downloads"],
            "growth": growth,
            "badge": badge
        })
    
    # MONTHLY CHAMPIONS - Hall of Fame (top seller each month)
    # Get top sellers from recent months
    monthly_champions = []
    months = ["January 2026", "December 2025", "November 2025"]
    
    for i, month in enumerate(months):
        if i < len(top_creators):
            monthly_champions.append({
                "month": month,
                "username": top_creators[i]["username"],
                "downloads": top_creators[i]["downloads"],
                "revenue": top_creators[i]["revenue"]
            })
    
    return {
        "topCreators": top_creators,
        "topProtocols": top_protocols,
        "risingStars": rising_stars,
        "monthlyChampions": monthly_champions,
        "timeRange": timeRange,
        "last_updated": now.isoformat()
    }


def _get_seller_badge(sales: int) -> str:
    """Get badge emoji based on sales count"""
    if sales >= 500:
        return "👑"  # Legend
    elif sales >= 200:
        return "💎"  # Diamond
    elif sales >= 100:
        return "🏆"  # Champion
    elif sales >= 50:
        return "⭐"  # Star
    elif sales >= 20:
        return "🔥"  # Hot
    elif sales >= 10:
        return "✨"  # Rising
    return "🌱"  # Newbie


def _get_seller_title(rank: int) -> str:
    """Get funny title based on rank"""
    titles = {
        1: "The Protocol Overlord 🦁",
        2: "The Silver Searcher 🥈",
        3: "The Bronze Boolean 🥉",
        4: "The Query Wizard 🧙‍♂️",
        5: "The Data Dynamo 💪",
    }
    return titles.get(rank, f"Protocol Pioneer #{rank}")


def _get_revenue_badge(revenue: float) -> str:
    """Get badge emoji based on revenue"""
    if revenue >= 1000:
        return "💰"  # Money bags
    elif revenue >= 500:
        return "💵"  # Rich
    elif revenue >= 200:
        return "💲"  # Good earner
    elif revenue >= 100:
        return "🤑"  # Making money
    elif revenue >= 50:
        return "💸"  # Earning
    return "🪙"  # Starting out


def _get_revenue_title(rank: int) -> str:
    """Get funny revenue title based on rank"""
    titles = {
        1: "The Protocol Billionaire 🏦",
        2: "The Search Tycoon 🎩",
        3: "The Boolean Baron 🏰",
        4: "The Query Capitalist 📈",
        5: "The Data Investor 💼",
    }
    return titles.get(rank, f"Marketplace Mogul #{rank}")


# ==================== AUTO-SYNC PUBLIC CATEGORIES ====================

@router.post("/admin/sync-public-categories", response_model=dict)
async def sync_public_categories_to_marketplace(user = Depends(get_current_user)):
    """Auto-list all public categories to marketplace (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all public categories
    public_categories = await db.categories.find({"is_public": True}).to_list(1000)
    
    # Get existing marketplace protocols
    existing = await db.marketplace_protocols.find({}).to_list(1000)
    existing_names = set(p["name"].lower() for p in existing)
    
    added = []
    for cat in public_categories:
        cat_name_lower = cat["name"].lower()
        
        # Skip if already in marketplace (fuzzy match on first 3 words)
        first_words = " ".join(cat_name_lower.split()[:3])
        if any(first_words in e for e in existing_names):
            continue
        
        # Get category owner
        owner = await db.users.find_one({"_id": ObjectId(cat["user_id"])}) if cat.get("user_id") else None
        creator_name = owner.get("callsign", owner.get("username", "InfoPilot User")) if owner else "InfoPilot User"
        
        # Auto-generate price based on protocol complexity
        protocol_length = len(cat.get("protocol", ""))
        base_price = 1.99
        if protocol_length > 200:
            base_price = 4.99
        elif protocol_length > 100:
            base_price = 2.99
        
        # Create marketplace listing
        new_protocol = {
            "name": cat["name"],
            "description": f"Automatically listed from public category. Protocol: {cat.get('protocol', 'Custom search protocol')[:200]}...",
            "protocol": cat.get("protocol", ""),
            "price": base_price,
            "category": "User Created",
            "tags": ["auto-listed", "public", "community"],
            "creator_name": creator_name,
            "total_sales": 0,
            "total_revenue": 0,
            "creator_earnings": 0,
            "rating": 0,
            "review_count": 0,
            "is_featured": False,
            "creator_id": cat.get("user_id", ""),
            "category_id": str(cat["_id"]),
            "status": "active",
            "created_at": datetime.utcnow()
        }
        
        await db.marketplace_protocols.insert_one(new_protocol)
        added.append(cat["name"])
    
    return {
        "success": True,
        "message": f"Synced {len(added)} public categories to marketplace",
        "added": added,
        "total_in_marketplace": await db.marketplace_protocols.count_documents({})
    }


 
