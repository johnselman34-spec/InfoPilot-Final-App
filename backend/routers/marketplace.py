"""
Marketplace routes for InfoPilot Explorer
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
import uuid

from services.database import db
from models.schemas import User
from routers.auth import require_auth

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/protocols")
async def get_marketplace_protocols(
    page: int = 1,
    limit: int = 20
):
    """Get public protocols for sale"""
    skip = (page - 1) * limit
    
    protocols = await db.categories.find(
        {"is_public": True, "price": {"$gt": 0}},
        {"_id": 0}
    ).sort("sales_count", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get creator info
    for protocol in protocols:
        creator = await db.users.find_one(
            {"user_id": protocol["user_id"]},
            {"_id": 0, "name": 1, "callsign": 1}
        )
        protocol["creator"] = creator
    
    total = await db.categories.count_documents({"is_public": True, "price": {"$gt": 0}})
    
    return {
        "protocols": protocols,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.post("/purchase")
async def purchase_protocol(
    request: Request,
    user: User = Depends(require_auth)
):
    """Purchase a protocol"""
    data = await request.json()
    category_id = data.get("category_id")
    
    protocol = await db.categories.find_one(
        {"category_id": category_id, "is_public": True},
        {"_id": 0}
    )
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    # Check if already purchased
    existing = await db.purchases.find_one({
        "user_id": user.user_id,
        "category_id": category_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already purchased")
    
    # Record purchase
    purchase = {
        "purchase_id": f"pur_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "category_id": category_id,
        "price": protocol["price"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.purchases.insert_one(purchase)
    
    # Update sales count
    await db.categories.update_one(
        {"category_id": category_id},
        {"$inc": {"sales_count": 1}}
    )
    
    return {"message": "Protocol purchased", "purchase": purchase}


@router.post("/copy")
async def copy_protocol(
    request: Request,
    user: User = Depends(require_auth)
):
    """Copy a free protocol to user's categories"""
    data = await request.json()
    category_id = data.get("category_id")
    
    protocol = await db.categories.find_one(
        {"category_id": category_id, "is_public": True},
        {"_id": 0}
    )
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    if protocol["price"] > 0:
        raise HTTPException(status_code=400, detail="Protocol requires purchase")
    
    # Create copy for user
    new_category = {
        "category_id": f"cat_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "name": f"{protocol['name']} (Copy)",
        "protocol": protocol["protocol"],
        "parent_id": None,
        "is_public": False,
        "price": 0,
        "sales_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(new_category)
    new_category.pop("_id", None)
    
    # Track copy for leaderboard
    await db.protocol_copies.insert_one({
        "original_id": category_id,
        "copied_by": user.user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Protocol copied", "category": new_category}


@router.get("/leaderboard")
async def get_leaderboard():
    """Get marketplace leaderboard"""
    # Top sellers
    top_sellers = await db.categories.aggregate([
        {"$match": {"is_public": True, "sales_count": {"$gt": 0}}},
        {"$group": {
            "_id": "$user_id",
            "total_sales": {"$sum": "$sales_count"},
            "total_revenue": {"$sum": {"$multiply": ["$price", "$sales_count"]}}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get user info for sellers
    for seller in top_sellers:
        user = await db.users.find_one(
            {"user_id": seller["_id"]},
            {"_id": 0, "name": 1, "callsign": 1}
        )
        seller["user"] = user
    
    # Most copied protocols
    most_copied = await db.protocol_copies.aggregate([
        {"$group": {"_id": "$original_id", "copy_count": {"$sum": 1}}},
        {"$sort": {"copy_count": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    for item in most_copied:
        protocol = await db.categories.find_one(
            {"category_id": item["_id"]},
            {"_id": 0, "name": 1, "user_id": 1}
        )
        item["protocol"] = protocol
    
    return {
        "top_sellers": top_sellers,
        "most_copied": most_copied
    }


@router.get("/headlines")
async def get_marketplace_headlines():
    """Get marketplace headlines/news"""
    # Get latest headlines from database or generate defaults
    headlines = await db.marketplace_headlines.find({}, {"_id": 0})\
        .sort("created_at", -1)\
        .limit(5)\
        .to_list(5)
    
    if not headlines:
        # Default headlines
        headlines = [
            {"title": "New protocols added daily!", "category": "Platform News"},
            {"title": "Top seller of the week announced", "category": "Community"},
            {"title": "AI-powered search matching now available", "category": "Features"},
            {"title": "Protocol templates feature launched", "category": "Updates"},
            {"title": "Share your protocols and earn 90% revenue", "category": "Monetization"}
        ]
    
    return {"headlines": headlines}


@router.get("/recommended")
async def get_recommended_protocols(user: User = Depends(require_auth)):
    """Get recommended protocols based on user activity"""
    # Get user's recent searches to understand interests
    recent_results = await db.search_results.find(
        {"user_id": user.user_id},
        {"_id": 0, "document_type": 1, "category_id": 1}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    # Get categories user has interacted with
    user_categories = set()
    for r in recent_results:
        if r.get("category_id"):
            user_categories.add(r["category_id"])
    
    # Find popular protocols user hasn't used yet
    query = {"is_public": True}
    if user_categories:
        query["category_id"] = {"$nin": list(user_categories)}
    
    recommended = await db.categories.find(query, {"_id": 0})\
        .sort("sales_count", -1)\
        .limit(6)\
        .to_list(6)
    
    # If no recommendations, get top protocols
    if not recommended:
        recommended = await db.categories.find(
            {"is_public": True},
            {"_id": 0}
        ).sort("sales_count", -1).limit(6).to_list(6)
    
    return {"protocols": recommended}
