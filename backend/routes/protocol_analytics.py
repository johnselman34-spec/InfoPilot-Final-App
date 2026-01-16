"""
InfoPilot Explorer - Protocol Analytics Routes
API endpoints for protocol creator analytics dashboard
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from config import db, logger
from routes.auth import get_current_user
from services.protocol_analytics import (
    get_protocol_analytics,
    get_protocol_forecast,
    get_marketplace_protocol_forecast,
    track_protocol_view
)

router = APIRouter(prefix="/protocol-analytics", tags=["Protocol Analytics"])


@router.get("/my-protocols", response_model=dict)
async def get_my_protocol_analytics(
    days: int = 30,
    user = Depends(get_current_user)
):
    """Get analytics for current user's protocols"""
    user_id = str(user["_id"])
    
    try:
        analytics = await get_protocol_analytics(user_id, days=days)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get protocol analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/my-protocols/{protocol_id}", response_model=dict)
async def get_single_protocol_analytics(
    protocol_id: str,
    days: int = 30,
    user = Depends(get_current_user)
):
    """Get analytics for a specific protocol"""
    user_id = str(user["_id"])
    
    # Verify ownership
    protocol = await db.marketplace_protocols.find_one({
        "_id": ObjectId(protocol_id),
        "creator_id": user_id
    })
    
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found or not owned by you")
    
    try:
        analytics = await get_protocol_analytics(user_id, protocol_id=protocol_id, days=days)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get protocol analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/my-forecast", response_model=dict)
async def get_my_forecast(
    days: int = 30,
    user = Depends(get_current_user)
):
    """Get performance forecast for current user's protocols"""
    user_id = str(user["_id"])
    
    try:
        forecast = await get_protocol_forecast(user_id, days=days)
        return forecast
    except Exception as e:
        logger.error(f"Failed to get forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to get forecast")


@router.post("/track-view/{protocol_id}", response_model=dict)
async def track_view(
    protocol_id: str,
    authorization: str = Header(None)
):
    """Track a protocol view (can be anonymous)"""
    viewer_id = None
    
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            session = await db.sessions.find_one({"token": token})
            if session:
                viewer_id = session.get("user_id")
        except Exception:
            pass
    
    try:
        await track_protocol_view(protocol_id, viewer_id)
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to track view: {e}")
        return {"success": False}


@router.get("/admin/marketplace-forecast", response_model=dict)
async def get_admin_marketplace_forecast(user = Depends(get_current_user)):
    """Admin: Get marketplace-wide protocol forecast"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        forecast = await get_marketplace_protocol_forecast()
        return forecast
    except Exception as e:
        logger.error(f"Failed to get marketplace forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to get forecast")


@router.get("/admin/top-creators", response_model=dict)
async def get_top_creators(
    limit: int = 10,
    user = Depends(get_current_user)
):
    """Admin: Get top protocol creators by revenue"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        pipeline = [
            {"$match": {"status": "completed"}},
            {"$lookup": {
                "from": "marketplace_protocols",
                "localField": "protocol_id",
                "foreignField": "_id",
                "as": "protocol"
            }},
            {"$unwind": "$protocol"},
            {"$group": {
                "_id": "$protocol.creator_id",
                "total_sales": {"$sum": 1},
                "total_revenue": {"$sum": "$amount"},
                "protocols_sold": {"$addToSet": "$protocol._id"}
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": limit}
        ]
        
        top_creators = await db.marketplace_purchases.aggregate(pipeline).to_list(limit)
        
        # Get creator details
        result = []
        for creator in top_creators:
            user_doc = await db.users.find_one({"_id": ObjectId(creator["_id"])})
            if user_doc:
                result.append({
                    "user_id": creator["_id"],
                    "username": user_doc.get("username", "Unknown"),
                    "email": user_doc.get("email", ""),
                    "total_sales": creator["total_sales"],
                    "total_revenue": round(creator["total_revenue"], 2),
                    "protocols_count": len(creator["protocols_sold"])
                })
        
        return {"success": True, "top_creators": result}
    except Exception as e:
        logger.error(f"Failed to get top creators: {e}")
        raise HTTPException(status_code=500, detail="Failed to get top creators")
