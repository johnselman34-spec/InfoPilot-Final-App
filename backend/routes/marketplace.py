"""
InfoPilot Explorer - Marketplace Routes
Protocol marketplace with PayPal integration
"""
from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

from utils.db import db
from utils.auth import require_user

# PayPal configuration
PAYPAL_BUSINESS_EMAIL = "JJspilot24@gmail.com"

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/protocols")
async def get_marketplace_protocols(category: Optional[str] = None):
    """Get protocols available in the marketplace."""
    query = {"is_public": True, "price": {"$gt": 0}}
    
    if category and category != "all":
        query["$or"] = [
            {"name": {"$regex": category, "$options": "i"}},
            {"protocol": {"$regex": category, "$options": "i"}}
        ]
    
    categories = await db.categories.find(query, {"_id": 0}).to_list(100)
    
    # Enrich with owner info
    for cat in categories:
        owner = await db.users.find_one({"id": cat["user_id"]}, {"_id": 0, "username": 1})
        cat["owner"] = owner
    
    return {"protocols": categories, "total": len(categories)}


@router.post("/buy/{protocol_id}")
async def buy_protocol(protocol_id: str, user: Dict = Depends(require_user)):
    """Initiate purchase of a protocol."""
    category = await db.categories.find_one({"id": protocol_id, "is_public": True, "price": {"$gt": 0}})
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
    purchase = await db.purchases.find_one({"id": purchase_id, "buyer_id": user["id"], "status": "pending"})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Get original category
    original = await db.categories.find_one({"id": purchase["protocol_id"]})
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
    
    return {"message": "Purchase completed!", "new_category_id": new_category["id"]}
