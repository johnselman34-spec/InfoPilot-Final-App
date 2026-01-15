"""
InfoPilot Explorer - Protocol Bundles Router
Allows users to create and purchase curated collections of protocols at a discount
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
import logging

from routes.auth import get_current_user, get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bundles", tags=["bundles"])

# Database will be injected
db = None

def init_router(database):
    global db
    db = database
    return router

class BundleCreate(BaseModel):
    name: str
    description: str
    protocol_ids: List[str]
    discount_percent: int = 15  # Default 15% discount
    category: str = "General"
    
class BundlePurchase(BaseModel):
    bundle_id: str
    transaction_id: Optional[str] = None


@router.get("")
async def list_bundles(category: str = None, sort: str = "popular"):
    """List all available protocol bundles"""
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    sort_options = {
        "popular": [("total_sales", -1)],
        "newest": [("created_at", -1)],
        "price_low": [("bundle_price", 1)],
        "price_high": [("bundle_price", -1)],
        "discount": [("discount_percent", -1)]
    }
    
    bundles = await db.protocol_bundles.find(query).sort(sort_options.get(sort, [("total_sales", -1)])).to_list(100)
    
    result = []
    for bundle in bundles:
        # Get protocol details
        protocol_ids = [ObjectId(pid) for pid in bundle.get("protocol_ids", [])]
        protocols = await db.marketplace_protocols.find({"_id": {"$in": protocol_ids}}).to_list(100)
        
        original_price = sum(p.get("price", 0) for p in protocols)
        bundle_price = original_price * (1 - bundle.get("discount_percent", 15) / 100)
        
        result.append({
            "id": str(bundle["_id"]),
            "name": bundle.get("name"),
            "description": bundle.get("description"),
            "category": bundle.get("category"),
            "protocol_count": len(protocols),
            "protocols": [{"id": str(p["_id"]), "name": p.get("name"), "price": p.get("price")} for p in protocols],
            "original_price": round(original_price, 2),
            "bundle_price": round(bundle_price, 2),
            "discount_percent": bundle.get("discount_percent", 15),
            "savings": round(original_price - bundle_price, 2),
            "total_sales": bundle.get("total_sales", 0),
            "creator_name": bundle.get("creator_name"),
            "created_at": bundle.get("created_at").isoformat() if bundle.get("created_at") else None
        })
    
    return {"bundles": result, "count": len(result)}


@router.post("")
async def create_bundle(bundle: BundleCreate, user = Depends(get_current_user)):
    """Create a new protocol bundle (sellers only)"""
    # Verify all protocols exist
    protocol_ids = [ObjectId(pid) for pid in bundle.protocol_ids]
    protocols = await db.marketplace_protocols.find({
        "_id": {"$in": protocol_ids}
    }).to_list(100)
    
    if len(protocols) < 2:
        raise HTTPException(status_code=400, detail="Bundle must contain at least 2 protocols")
    
    if len(protocols) != len(bundle.protocol_ids):
        raise HTTPException(status_code=400, detail="Some protocols not found")
    
    # Calculate prices
    original_price = sum(p.get("price", 0) for p in protocols)
    bundle_price = original_price * (1 - bundle.discount_percent / 100)
    
    new_bundle = {
        "name": bundle.name,
        "description": bundle.description,
        "protocol_ids": bundle.protocol_ids,
        "discount_percent": min(max(bundle.discount_percent, 5), 50),  # 5-50% discount
        "category": bundle.category,
        "original_price": original_price,
        "bundle_price": bundle_price,
        "creator_id": str(user["_id"]),
        "creator_name": user.get("username") or user.get("callsign") or user.get("email"),
        "is_active": True,
        "total_sales": 0,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.protocol_bundles.insert_one(new_bundle)
    
    return {
        "id": str(result.inserted_id),
        "message": "Bundle created successfully",
        "bundle_price": round(bundle_price, 2),
        "savings": round(original_price - bundle_price, 2)
    }


@router.get("/featured")
async def get_featured_bundle():
    """Get the Bundle of the Week (featured bundle)"""
    # Check if there's a manually set bundle of the week
    setting = await db.settings.find_one({"key": "bundle_of_week_id"})
    featured_id = setting.get("value") if setting and setting.get("value") else None
    
    bundle = None
    
    if featured_id and featured_id.strip():
        try:
            bundle = await db.protocol_bundles.find_one({
                "_id": ObjectId(featured_id),
                "is_active": True
            })
        except Exception:
            pass
    
    # If no featured bundle set, get the most popular one
    if not bundle:
        bundles = await db.protocol_bundles.find({"is_active": True}).sort("total_sales", -1).limit(1).to_list(1)
        if bundles:
            bundle = bundles[0]
    
    if not bundle:
        return {"featured": None, "message": "No bundles available yet! Create one to be featured! 🏆"}
    
    # Get protocol details
    protocol_ids = [ObjectId(pid) for pid in bundle.get("protocol_ids", [])]
    protocols = await db.marketplace_protocols.find({"_id": {"$in": protocol_ids}}).to_list(100)
    
    original_price = sum(p.get("price", 0) for p in protocols)
    bundle_price = original_price * (1 - bundle.get("discount_percent", 15) / 100)
    
    return {
        "featured": {
            "id": str(bundle["_id"]),
            "name": bundle.get("name"),
            "description": bundle.get("description"),
            "category": bundle.get("category"),
            "protocol_count": len(protocols),
            "protocols": [{"id": str(p["_id"]), "name": p.get("name")} for p in protocols],
            "original_price": round(original_price, 2),
            "bundle_price": round(bundle_price, 2),
            "discount_percent": bundle.get("discount_percent", 15),
            "savings": round(original_price - bundle_price, 2),
            "total_sales": bundle.get("total_sales", 0),
            "is_bundle_of_week": True
        },
        "funny_tagline": "🏆 This week's HOTTEST bundle! Grab it before it's gone! 🔥"
    }


@router.get("/my/purchases")
async def get_my_bundle_purchases(user = Depends(get_current_user)):
    """Get user's bundle purchase history"""
    purchases = await db.bundle_purchases.find(
        {"user_id": str(user["_id"])}
    ).sort("purchased_at", -1).to_list(100)
    
    return {
        "purchases": [{
            "id": str(p["_id"]),
            "bundle_name": p.get("bundle_name"),
            "protocols_count": len(p.get("protocol_ids", [])),
            "amount_paid": p.get("amount_paid"),
            "savings": p.get("savings"),
            "purchased_at": p.get("purchased_at").isoformat() if p.get("purchased_at") else None
        } for p in purchases]
    }


@router.get("/{bundle_id}")
async def get_bundle(bundle_id: str):
    """Get bundle details"""
    try:
        bundle = await db.protocol_bundles.find_one({"_id": ObjectId(bundle_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid bundle ID")
    
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Get full protocol details
    protocol_ids = [ObjectId(pid) for pid in bundle.get("protocol_ids", [])]
    protocols = await db.marketplace_protocols.find({"_id": {"$in": protocol_ids}}).to_list(100)
    
    original_price = sum(p.get("price", 0) for p in protocols)
    bundle_price = original_price * (1 - bundle.get("discount_percent", 15) / 100)
    
    return {
        "id": str(bundle["_id"]),
        "name": bundle.get("name"),
        "description": bundle.get("description"),
        "category": bundle.get("category"),
        "protocols": [{
            "id": str(p["_id"]),
            "name": p.get("name"),
            "description": p.get("description"),
            "price": p.get("price"),
            "protocol_string": p.get("protocol")
        } for p in protocols],
        "original_price": round(original_price, 2),
        "bundle_price": round(bundle_price, 2),
        "discount_percent": bundle.get("discount_percent", 15),
        "savings": round(original_price - bundle_price, 2),
        "total_sales": bundle.get("total_sales", 0),
        "creator_name": bundle.get("creator_name")
    }


@router.post("/purchase")
async def purchase_bundle(purchase: BundlePurchase, user = Depends(get_current_user)):
    """Initiate a protocol bundle purchase"""
    from config import PAYPAL_PAYMENT_LINK
    
    bundle_id = purchase.bundle_id
    
    try:
        bundle = await db.protocol_bundles.find_one({"_id": ObjectId(bundle_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid bundle ID")
    
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Check if user already owns this bundle
    existing_purchase = await db.bundle_purchases.find_one({
        "user_id": str(user["_id"]),
        "bundle_id": bundle_id
    })
    
    if existing_purchase:
        raise HTTPException(status_code=400, detail="You already own this bundle")
    
    # Calculate price
    protocol_ids = [ObjectId(pid) for pid in bundle.get("protocol_ids", [])]
    protocols = await db.marketplace_protocols.find({"_id": {"$in": protocol_ids}}).to_list(100)
    
    original_price = sum(p.get("price", 0) for p in protocols)
    bundle_price = original_price * (1 - bundle.get("discount_percent", 15) / 100)
    
    # If free bundle, complete immediately
    if bundle_price <= 0:
        purchase_record = {
            "user_id": str(user["_id"]),
            "bundle_id": bundle_id,
            "bundle_name": bundle.get("name"),
            "protocol_ids": bundle.get("protocol_ids"),
            "amount_paid": 0,
            "original_price": original_price,
            "savings": original_price,
            "transaction_id": f"FREE-{bundle_id}-{datetime.now().timestamp()}",
            "is_free": True,
            "purchased_at": datetime.now(timezone.utc)
        }
        
        await db.bundle_purchases.insert_one(purchase_record)
        
        # Update bundle sales count
        await db.protocol_bundles.update_one(
            {"_id": ObjectId(bundle_id)},
            {"$inc": {"total_sales": 1}}
        )
        
        return {
            "message": "Bundle acquired for FREE!",
            "protocols_unlocked": len(bundle.get("protocol_ids", [])),
            "is_free": True
        }
    
    # Create pending purchase and return payment URL
    pending = {
        "user_id": str(user["_id"]),
        "bundle_id": bundle_id,
        "bundle_name": bundle.get("name"),
        "amount": round(bundle_price, 2),
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.pending_bundle_purchases.insert_one(pending)
    pending_id = str(result.inserted_id)
    
    # PayPal payment link
    payment_url = PAYPAL_PAYMENT_LINK or f"https://www.paypal.com/paypalme/TopPilotEnterprises/{bundle_price:.2f}"
    
    return {
        "success": True,
        "pending_id": pending_id,
        "payment_url": payment_url,
        "amount": round(bundle_price, 2),
        "bundle_name": bundle.get("name"),
        "message": f"Complete payment of ${bundle_price:.2f} via PayPal, then confirm your purchase."
    }


@router.post("/confirm-payment")
async def confirm_bundle_payment(data: dict, user = Depends(get_current_user)):
    """Confirm PayPal payment for bundle purchase"""
    bundle_id = data.get("bundle_id")
    transaction_id = data.get("transaction_id")
    
    if not bundle_id or not transaction_id:
        raise HTTPException(status_code=400, detail="Bundle ID and Transaction ID required")
    
    try:
        bundle = await db.protocol_bundles.find_one({"_id": ObjectId(bundle_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid bundle ID")
    
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Check if already purchased
    existing = await db.bundle_purchases.find_one({
        "user_id": str(user["_id"]),
        "bundle_id": bundle_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You already own this bundle")
    
    # Calculate prices
    protocol_ids = [ObjectId(pid) for pid in bundle.get("protocol_ids", [])]
    protocols = await db.marketplace_protocols.find({"_id": {"$in": protocol_ids}}).to_list(100)
    
    original_price = sum(p.get("price", 0) for p in protocols)
    bundle_price = original_price * (1 - bundle.get("discount_percent", 15) / 100)
    
    # Record purchase
    purchase_record = {
        "user_id": str(user["_id"]),
        "bundle_id": bundle_id,
        "bundle_name": bundle.get("name"),
        "protocol_ids": bundle.get("protocol_ids"),
        "amount_paid": bundle_price,
        "original_price": original_price,
        "savings": original_price - bundle_price,
        "transaction_id": transaction_id,
        "purchased_at": datetime.now(timezone.utc)
    }
    
    await db.bundle_purchases.insert_one(purchase_record)
    
    # Update bundle sales count
    await db.protocol_bundles.update_one(
        {"_id": ObjectId(bundle_id)},
        {"$inc": {"total_sales": 1}}
    )
    
    # Award XP
    try:
        await db.gamification.update_one(
            {"user_id": str(user["_id"])},
            {"$inc": {"xp": 20}},  # Bonus XP for bundle purchase
            upsert=True
        )
    except Exception:
        pass
    
    return {
        "success": True,
        "message": "Bundle purchased successfully!",
        "protocols_unlocked": len(bundle.get("protocol_ids", [])),
        "savings": round(original_price - bundle_price, 2),
        "xp_earned": 20
    }


@router.get("/my/purchases")
async def get_my_bundle_purchases(user = Depends(get_current_user)):
    """Get user's bundle purchase history"""
    purchases = await db.bundle_purchases.find(
        {"user_id": str(user["_id"])}
    ).sort("purchased_at", -1).to_list(100)
    
    return {
        "purchases": [{
            "id": str(p["_id"]),
            "bundle_name": p.get("bundle_name"),
            "protocols_count": len(p.get("protocol_ids", [])),
            "amount_paid": p.get("amount_paid"),
            "savings": p.get("savings"),
            "purchased_at": p.get("purchased_at").isoformat() if p.get("purchased_at") else None
        } for p in purchases]
    }


@router.delete("/{bundle_id}")
async def delete_bundle(bundle_id: str, user = Depends(get_current_user)):
    """Delete a bundle (creator or admin only)"""
    try:
        bundle = await db.protocol_bundles.find_one({"_id": ObjectId(bundle_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid bundle ID")
    
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Check if user is creator or admin
    is_creator = bundle.get("creator_id") == str(user["_id"])
    is_admin = user.get("is_admin", False)
    
    if not is_creator and not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this bundle")
    
    # Soft delete - mark as inactive
    await db.protocol_bundles.update_one(
        {"_id": ObjectId(bundle_id)},
        {"$set": {"is_active": False, "deleted_at": datetime.now(timezone.utc)}}
    )
    
    return {"success": True, "message": "Bundle deleted"}


@router.get("/cross-sell/{protocol_id}")
async def get_cross_sell_recommendations(protocol_id: str, user = Depends(get_optional_user)):
    """Get cross-sell recommendations for a protocol during checkout"""
    # Get the protocol being purchased
    try:
        protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(protocol_id)})
    except Exception:
        return {"recommendations": [], "message": "Invalid protocol"}
    
    if not protocol:
        return {"recommendations": [], "message": "Protocol not found"}
    
    # Find related protocols in the same category
    category = protocol.get("category", "General")
    
    related_protocols = await db.marketplace_protocols.find({
        "_id": {"$ne": ObjectId(protocol_id)},
        "category": category,
        "is_active": {"$ne": False}
    }).sort("total_sales", -1).limit(3).to_list(3)
    
    # Also find bundles containing this protocol
    bundles_with_protocol = await db.protocol_bundles.find({
        "protocol_ids": protocol_id,
        "is_active": True
    }).limit(2).to_list(2)
    
    # Random funny cross-sell messages
    import random
    funny_messages = [
        "🎯 People who bought this also bought these beauties!",
        "🚀 Level up your search game with these related protocols!",
        "💡 Your search IQ would skyrocket with these additions!",
        "🔥 Hot picks that go PERFECTLY with your selection!",
        "✨ Complete the set! Your future self will thank you!",
        "🏆 Champions bundle these together - just sayin'!",
    ]
    
    recommendations = []
    for p in related_protocols:
        recommendations.append({
            "type": "protocol",
            "id": str(p["_id"]),
            "name": p.get("name"),
            "price": p.get("price", 0),
            "is_free": p.get("price", 0) == 0,
            "category": p.get("category")
        })
    
    for b in bundles_with_protocol:
        recommendations.append({
            "type": "bundle",
            "id": str(b["_id"]),
            "name": b.get("name"),
            "discount_percent": b.get("discount_percent", 15),
            "protocol_count": len(b.get("protocol_ids", [])),
            "category": b.get("category")
        })
    
    return {
        "recommendations": recommendations,
        "funny_message": random.choice(funny_messages),
        "cross_sell_count": len(recommendations)
    }


@router.post("/admin/set-featured")
async def set_featured_bundle(data: dict, user = Depends(get_current_user)):
    """Set the Bundle of the Week (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    bundle_id = data.get("bundle_id")
    
    if bundle_id:
        # Verify bundle exists
        try:
            bundle = await db.protocol_bundles.find_one({"_id": ObjectId(bundle_id), "is_active": True})
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid bundle ID")
        
        if not bundle:
            raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Update the setting
    await db.settings.update_one(
        {"key": "bundle_of_week_id"},
        {"$set": {"value": bundle_id or ""}},
        upsert=True
    )
    
    return {
        "success": True,
        "message": f"Bundle of the Week {'set' if bundle_id else 'cleared'}!",
        "bundle_id": bundle_id
    }


