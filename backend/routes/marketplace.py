"""
InfoPilot Explorer - Marketplace Routes
Protocol marketplace with PayPal integration
Optimized with aggregation pipelines and caching
"""
from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import Dict, Optional, List
from datetime import datetime, timezone
import uuid
import os

from utils.db import db
from utils.auth import require_user
from utils.cache import cached_marketplace, invalidate_marketplace_cache

# PayPal configuration - read from environment
PAYPAL_BUSINESS_EMAIL = os.environ.get("PAYPAL_BUSINESS_EMAIL", "JJspilot24@gmail.com")

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/protocols")
async def get_marketplace_protocols(category: Optional[str] = None):
    """Get protocols available in the marketplace.
    
    Optimized: Uses aggregation pipeline with $lookup and caching.
    """
    protocols = await cached_marketplace(category)
    return {"protocols": protocols, "total": len(protocols)}


@router.get("/check-purchase/{protocol_id}")
async def check_protocol_purchase(protocol_id: str, user: Dict = Depends(require_user)):
    """Check if user has purchased a specific protocol or owns it."""
    # Check if user owns the protocol
    owned = await db.categories.find_one(
        {"id": protocol_id, "user_id": user["id"]},
        {"_id": 0, "id": 1}
    )
    if owned:
        return {"has_access": True, "reason": "owner"}
    
    # Check if user has completed a purchase for this protocol
    purchase = await db.purchases.find_one(
        {"buyer_id": user["id"], "protocol_id": protocol_id, "status": "completed"},
        {"_id": 0, "id": 1}
    )
    if purchase:
        return {"has_access": True, "reason": "purchased"}
    
    return {"has_access": False, "reason": "not_purchased"}


@router.get("/my-purchases")
async def get_my_purchased_protocols(user: Dict = Depends(require_user)):
    """Get list of protocol IDs that the user has purchased."""
    purchases = await db.purchases.find(
        {"buyer_id": user["id"], "status": "completed"},
        {"_id": 0, "protocol_id": 1}
    ).to_list(1000)
    
    # Also get user's own protocols
    owned = await db.categories.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    purchased_ids = [p["protocol_id"] for p in purchases]
    owned_ids = [o["id"] for o in owned]
    
    return {
        "purchased_protocol_ids": purchased_ids,
        "owned_protocol_ids": owned_ids,
        "all_accessible_ids": list(set(purchased_ids + owned_ids))
    }


@router.post("/copy-protocol/{protocol_id}")
async def copy_protocol_content(protocol_id: str, user: Dict = Depends(require_user)):
    """Get protocol content for copying - only if user has access."""
    # Get the protocol
    protocol = await db.categories.find_one(
        {"id": protocol_id},
        {"_id": 0, "id": 1, "user_id": 1, "protocol": 1, "is_public": 1, "price": 1, "name": 1}
    )
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check if protocol is for sale (has price > 0 and is public)
    is_for_sale = protocol.get("is_public") and protocol.get("price", 0) > 0
    
    # Check if user owns the protocol
    if protocol["user_id"] == user["id"]:
        return {"protocol": protocol["protocol"], "access_type": "owner"}
    
    # If not for sale, allow copying (free templates)
    if not is_for_sale:
        return {"protocol": protocol["protocol"], "access_type": "free"}
    
    # Protocol is for sale - check if user purchased it
    purchase = await db.purchases.find_one(
        {"buyer_id": user["id"], "protocol_id": protocol_id, "status": "completed"},
        {"_id": 0, "id": 1}
    )
    
    if purchase:
        return {"protocol": protocol["protocol"], "access_type": "purchased"}
    
    # User has not purchased - deny access
    raise HTTPException(
        status_code=403, 
        detail=f"You must purchase this protocol (${protocol.get('price', 0):.2f}) to copy it"
    )


@router.post("/buy/{protocol_id}")
async def buy_protocol(protocol_id: str, user: Dict = Depends(require_user)):
    """Initiate purchase of a protocol."""
    category = await db.categories.find_one(
        {"id": protocol_id, "is_public": True, "price": {"$gt": 0}},
        {"_id": 0}
    )
    if not category:
        raise HTTPException(status_code=404, detail="Protocol not found or not for sale")
    
    if category["user_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot buy your own protocol")
    
    # Create PayPal payment URL using environment variable for frontend URL
    price = category["price"]
    frontend_url = os.environ.get("FRONTEND_URL", "https://infopilot.com")
    paypal_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={PAYPAL_BUSINESS_EMAIL}&item_name=InfoPilot Protocol: {category['name']}&amount={price}&currency_code=USD&return={frontend_url}/purchase/success&cancel_return={frontend_url}/purchase/cancel"
    
    # Record purchase attempt
    purchase = {
        "id": str(uuid.uuid4()),
        "buyer_id": user["id"],
        "seller_id": category["user_id"],
        "protocol_id": protocol_id,
        "protocol_name": category["name"],
        "price": price,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.purchases.insert_one(purchase)
    
    return {"paypal_url": paypal_url, "purchase_id": purchase["id"]}


@router.post("/purchase/complete/{purchase_id}")
async def complete_purchase(purchase_id: str, user: Dict = Depends(require_user)):
    """Complete a purchase and copy protocol to buyer."""
    purchase = await db.purchases.find_one(
        {"id": purchase_id, "buyer_id": user["id"], "status": "pending"},
        {"_id": 0}
    )
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Get original category
    original = await db.categories.find_one({"id": purchase["protocol_id"]}, {"_id": 0})
    if not original:
        raise HTTPException(status_code=404, detail="Original protocol not found")
    
    # Copy to buyer
    new_category = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": f"{original['name']} (Purchased)",
        "protocol": original["protocol"],
        "parent_id": None,
        "is_public": False,
        "price": None,
        "search_result_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.categories.insert_one(new_category)
    
    # Update purchase status
    await db.purchases.update_one({"id": purchase_id}, {"$set": {"status": "completed"}})
    
    # Update seller wallet (85% to seller)
    seller_share = purchase["price"] * 0.85
    await db.users.update_one(
        {"id": purchase["seller_id"]},
        {"$inc": {"wallet_balance": seller_share}}
    )
    
    # Invalidate caches
    await invalidate_marketplace_cache()
    
    return {"message": "Purchase completed!", "new_category_id": new_category["id"]}
