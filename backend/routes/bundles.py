"""
InfoPilot Explorer - Protocol Bundles Router
Allows users to create and purchase curated collections of protocols at a discount
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
import logging

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
    transaction_id: str

# Helper to get current user from token
async def get_current_user(token: str):
    from backend.services.auth_service import AuthService
    return await AuthService.get_user_from_token(token)

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
async def create_bundle(bundle: BundleCreate, authorization: str = None):
    """Create a new protocol bundle (sellers only)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Verify all protocols exist and belong to the user
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
        "creator_name": user.get("username") or user.get("email"),
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

@router.get("/{bundle_id}")
async def get_bundle(bundle_id: str):
    """Get bundle details"""
    try:
        bundle = await db.protocol_bundles.find_one({"_id": ObjectId(bundle_id)})
    except:
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
            "protocol_string": p.get("protocol_string")
        } for p in protocols],
        "original_price": round(original_price, 2),
        "bundle_price": round(bundle_price, 2),
        "discount_percent": bundle.get("discount_percent", 15),
        "savings": round(original_price - bundle_price, 2),
        "total_sales": bundle.get("total_sales", 0),
        "creator_name": bundle.get("creator_name")
    }

@router.post("/{bundle_id}/purchase")
async def purchase_bundle(bundle_id: str, purchase: BundlePurchase, authorization: str = None):
    """Purchase a protocol bundle"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        bundle = await db.protocol_bundles.find_one({"_id": ObjectId(bundle_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid bundle ID")
    
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Record purchase
    purchase_record = {
        "user_id": str(user["_id"]),
        "bundle_id": bundle_id,
        "bundle_name": bundle.get("name"),
        "protocol_ids": bundle.get("protocol_ids"),
        "amount_paid": bundle.get("bundle_price"),
        "original_price": bundle.get("original_price"),
        "savings": bundle.get("original_price", 0) - bundle.get("bundle_price", 0),
        "transaction_id": purchase.transaction_id,
        "purchased_at": datetime.now(timezone.utc)
    }
    
    await db.bundle_purchases.insert_one(purchase_record)
    
    # Update bundle sales count
    await db.protocol_bundles.update_one(
        {"_id": ObjectId(bundle_id)},
        {"$inc": {"total_sales": 1}}
    )
    
    # Award XP
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$inc": {"xp": 20}}  # Bonus XP for bundle purchase
    )
    
    return {
        "message": "Bundle purchased successfully!",
        "protocols_unlocked": len(bundle.get("protocol_ids", [])),
        "savings": round(bundle.get("original_price", 0) - bundle.get("bundle_price", 0), 2),
        "xp_earned": 20
    }

@router.get("/my/purchases")
async def get_my_bundle_purchases(authorization: str = None):
    """Get user's bundle purchase history"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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
