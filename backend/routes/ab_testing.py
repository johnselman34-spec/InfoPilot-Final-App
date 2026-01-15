"""
InfoPilot Explorer - A/B Testing System
Tracks and analyzes different variants of UI elements for conversion optimization
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel
import random
import hashlib

from config import db, logger
from routes.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/ab-testing", tags=["A/B Testing"])


# ==================== MODELS ====================

class ABTestConfig(BaseModel):
    name: str  # e.g., "book_promo_cta", "search_button_style"
    description: Optional[str] = None
    variants: List[dict]  # [{id: "A", name: "Original", weight: 50}, ...]
    is_active: bool = True
    target_element: str  # e.g., "BookPromoBanner", "SearchButton"


class ABTestEvent(BaseModel):
    test_id: str
    variant_id: str
    event_type: str  # 'impression', 'click', 'conversion'
    metadata: Optional[dict] = None


# ==================== PREDEFINED TESTS ====================

# Default A/B tests for "Letters to Evelyn" and other elements
DEFAULT_TESTS = [
    {
        "name": "book_promo_headline",
        "description": "Test different headlines for Letters to Evelyn promo",
        "target_element": "BookPromoBanner",
        "variants": [
            {"id": "A", "name": "Limited Time", "weight": 25, 
             "content": {"headline": "⚡ LIMITED TIME: $2.99 - Less Than Your Coffee! ☕", 
                        "subtext": "19 Five-Star Reviews • Optioned for Film • Read It Before Hollywood Does!"}},
            {"id": "B", "name": "Social Proof", "weight": 25,
             "content": {"headline": "🔥 Over 10,000 Readers Can't Be Wrong!", 
                        "subtext": "Join the phenomenon that Hollywood couldn't ignore!"}},
            {"id": "C", "name": "Urgency", "weight": 25,
             "content": {"headline": "🎬 Film Production Starting Soon - Read It First!", 
                        "subtext": "Experience the original before the Hollywood adaptation!"}},
            {"id": "D", "name": "Mystery", "weight": 25,
             "content": {"headline": "WROTE A BOOK. UNIVERSE FACT-CHECKED IT. IT PASSED.", 
                        "subtext": "Navy pilot meets cosmic chaos. Now a bestseller."}}
        ],
        "is_active": True
    },
    {
        "name": "book_promo_cta_button",
        "description": "Test different CTA button styles for book purchase",
        "target_element": "BookPromoBanner",
        "variants": [
            {"id": "A", "name": "GET IT NOW", "weight": 33,
             "content": {"text": "🛒 GET IT NOW - Only $2.99!", "style": "gradient_pink_orange"}},
            {"id": "B", "name": "BUY NOW", "weight": 33,
             "content": {"text": "💰 BUY NOW - Save 70%!", "style": "gradient_green"}},
            {"id": "C", "name": "READ TODAY", "weight": 34,
             "content": {"text": "📖 READ TODAY - Instant Download!", "style": "gradient_purple"}}
        ],
        "is_active": True
    },
    {
        "name": "search_cta_style",
        "description": "Test different search button styles",
        "target_element": "SearchButton",
        "variants": [
            {"id": "A", "name": "Purple Gradient", "weight": 50,
             "content": {"text": "🔍 Search", "style": "gradient_purple"}},
            {"id": "B", "name": "Blue Solid", "weight": 50,
             "content": {"text": "Search Now →", "style": "solid_blue"}}
        ],
        "is_active": True
    },
    {
        "name": "marketplace_cta",
        "description": "Test marketplace browse button",
        "target_element": "MarketplaceButton",
        "variants": [
            {"id": "A", "name": "Browse Protocols", "weight": 50,
             "content": {"text": "Browse Protocols", "style": "default"}},
            {"id": "B", "name": "Explore Market", "weight": 50,
             "content": {"text": "🏪 Explore Marketplace", "style": "highlighted"}}
        ],
        "is_active": True
    },
    {
        "name": "signup_incentive",
        "description": "Test different signup incentives",
        "target_element": "SignupPrompt",
        "variants": [
            {"id": "A", "name": "Free Features", "weight": 33,
             "content": {"text": "Sign up FREE - Unlock all features!", "highlight": "FREE"}},
            {"id": "B", "name": "Community", "weight": 33,
             "content": {"text": "Join 5,000+ researchers today!", "highlight": "5,000+"}},
            {"id": "C", "name": "AI Features", "weight": 34,
             "content": {"text": "Get AI-powered search suggestions!", "highlight": "AI-powered"}}
        ],
        "is_active": True
    }
]


# ==================== HELPER FUNCTIONS ====================

def get_user_hash(user_id: str = None, session_id: str = None) -> str:
    """Generate consistent hash for user to ensure same variant assignment"""
    identifier = user_id or session_id or str(random.random())
    return hashlib.md5(identifier.encode()).hexdigest()


def select_variant(variants: List[dict], user_hash: str) -> dict:
    """Select variant based on weights and user hash for consistency"""
    # Convert hash to number for deterministic selection
    hash_num = int(user_hash[:8], 16) % 100
    
    cumulative = 0
    for variant in variants:
        cumulative += variant.get("weight", 0)
        if hash_num < cumulative:
            return variant
    
    return variants[-1]  # Fallback to last variant


# ==================== ENDPOINTS ====================

@router.get("/tests", response_model=dict)
async def get_active_tests():
    """Get all active A/B tests"""
    # Check for tests in database first
    db_tests = await db.ab_tests.find({"is_active": True}).to_list(50)
    
    if db_tests:
        tests = []
        for t in db_tests:
            tests.append({
                "id": str(t["_id"]),
                "name": t["name"],
                "description": t.get("description"),
                "target_element": t["target_element"],
                "variant_count": len(t.get("variants", []))
            })
        return {"tests": tests, "source": "database"}
    
    # Return default tests if no database tests
    return {
        "tests": [
            {
                "id": t["name"],
                "name": t["name"],
                "description": t.get("description"),
                "target_element": t["target_element"],
                "variant_count": len(t.get("variants", []))
            }
            for t in DEFAULT_TESTS if t.get("is_active", True)
        ],
        "source": "defaults"
    }


@router.get("/variant/{test_name}", response_model=dict)
async def get_variant(
    test_name: str,
    request: Request,
    user = Depends(get_optional_user)
):
    """Get assigned variant for a specific test"""
    # Get user identifier
    user_id = str(user["_id"]) if user else None
    session_id = request.headers.get("X-Session-ID", request.client.host if request.client else "anonymous")
    user_hash = get_user_hash(user_id, session_id)
    
    # Find test (database first, then defaults)
    test = await db.ab_tests.find_one({"name": test_name, "is_active": True})
    
    if not test:
        # Check defaults
        test = next((t for t in DEFAULT_TESTS if t["name"] == test_name and t.get("is_active", True)), None)
    
    if not test:
        raise HTTPException(status_code=404, detail=f"Test '{test_name}' not found or inactive")
    
    # Select variant
    variant = select_variant(test.get("variants", []), user_hash)
    
    # Log assignment (for analytics)
    await db.ab_assignments.update_one(
        {"user_hash": user_hash, "test_name": test_name},
        {
            "$set": {
                "variant_id": variant["id"],
                "user_id": user_id,
                "assigned_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    return {
        "test_name": test_name,
        "variant_id": variant["id"],
        "variant_name": variant.get("name"),
        "content": variant.get("content", {}),
        "user_hash": user_hash[:8]  # Partial hash for debugging
    }


@router.get("/variants/batch", response_model=dict)
async def get_batch_variants(
    test_names: str,  # Comma-separated list
    request: Request,
    user = Depends(get_optional_user)
):
    """Get variants for multiple tests at once"""
    user_id = str(user["_id"]) if user else None
    session_id = request.headers.get("X-Session-ID", request.client.host if request.client else "anonymous")
    user_hash = get_user_hash(user_id, session_id)
    
    names = [n.strip() for n in test_names.split(",")]
    results = {}
    
    for test_name in names:
        test = await db.ab_tests.find_one({"name": test_name, "is_active": True})
        if not test:
            test = next((t for t in DEFAULT_TESTS if t["name"] == test_name and t.get("is_active", True)), None)
        
        if test:
            variant = select_variant(test.get("variants", []), user_hash)
            results[test_name] = {
                "variant_id": variant["id"],
                "content": variant.get("content", {})
            }
            
            # Log assignment
            await db.ab_assignments.update_one(
                {"user_hash": user_hash, "test_name": test_name},
                {
                    "$set": {
                        "variant_id": variant["id"],
                        "user_id": user_id,
                        "assigned_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
    
    return {"variants": results, "user_hash": user_hash[:8]}


@router.post("/event", response_model=dict)
async def track_event(
    event: ABTestEvent,
    request: Request,
    user = Depends(get_optional_user)
):
    """Track an A/B test event (impression, click, conversion)"""
    user_id = str(user["_id"]) if user else None
    session_id = request.headers.get("X-Session-ID", request.client.host if request.client else "anonymous")
    user_hash = get_user_hash(user_id, session_id)
    
    # Validate event type
    valid_events = ['impression', 'click', 'conversion', 'hover', 'scroll_to']
    if event.event_type not in valid_events:
        raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of: {valid_events}")
    
    # Store event
    event_data = {
        "test_id": event.test_id,
        "variant_id": event.variant_id,
        "event_type": event.event_type,
        "user_id": user_id,
        "user_hash": user_hash,
        "metadata": event.metadata or {},
        "timestamp": datetime.now(timezone.utc),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", "")[:200]
    }
    
    await db.ab_events.insert_one(event_data)
    
    return {"success": True, "tracked": event.event_type}


@router.get("/results/{test_name}", response_model=dict)
async def get_test_results(
    test_name: str,
    days: int = 30,
    user = Depends(get_current_user)
):
    """Get A/B test results and analytics (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get test info
    test = await db.ab_tests.find_one({"name": test_name})
    if not test:
        test = next((t for t in DEFAULT_TESTS if t["name"] == test_name), None)
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    variants = test.get("variants", [])
    
    # Aggregate events by variant
    pipeline = [
        {
            "$match": {
                "test_id": test_name,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "variant_id": "$variant_id",
                    "event_type": "$event_type"
                },
                "count": {"$sum": 1},
                "unique_users": {"$addToSet": "$user_hash"}
            }
        }
    ]
    
    events = await db.ab_events.aggregate(pipeline).to_list(100)
    
    # Build results per variant
    variant_results = {}
    for v in variants:
        variant_results[v["id"]] = {
            "variant_id": v["id"],
            "variant_name": v.get("name"),
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "unique_impressions": 0,
            "unique_clicks": 0,
            "click_rate": 0,
            "conversion_rate": 0
        }
    
    for e in events:
        vid = e["_id"]["variant_id"]
        etype = e["_id"]["event_type"]
        if vid in variant_results:
            if etype == "impression":
                variant_results[vid]["impressions"] = e["count"]
                variant_results[vid]["unique_impressions"] = len(e["unique_users"])
            elif etype == "click":
                variant_results[vid]["clicks"] = e["count"]
                variant_results[vid]["unique_clicks"] = len(e["unique_users"])
            elif etype == "conversion":
                variant_results[vid]["conversions"] = e["count"]
    
    # Calculate rates
    for vid, data in variant_results.items():
        if data["impressions"] > 0:
            data["click_rate"] = round(data["clicks"] / data["impressions"] * 100, 2)
            data["conversion_rate"] = round(data["conversions"] / data["impressions"] * 100, 2)
    
    # Determine winner (highest conversion rate with statistical significance)
    sorted_variants = sorted(variant_results.values(), key=lambda x: x["conversion_rate"], reverse=True)
    winner = sorted_variants[0] if sorted_variants else None
    
    # Calculate statistical significance (simplified)
    total_impressions = sum(v["impressions"] for v in variant_results.values())
    is_significant = total_impressions >= 1000  # Minimum sample size
    
    return {
        "test_name": test_name,
        "description": test.get("description"),
        "period_days": days,
        "variants": list(variant_results.values()),
        "total_impressions": total_impressions,
        "winner": winner["variant_id"] if winner and is_significant else None,
        "winner_name": winner["variant_name"] if winner and is_significant else None,
        "is_statistically_significant": is_significant,
        "recommendation": f"Variant {winner['variant_id']} ({winner['variant_name']}) performs best with {winner['conversion_rate']}% conversion rate" if winner and is_significant else "Need more data for conclusive results"
    }


@router.get("/dashboard", response_model=dict)
async def get_ab_dashboard(
    days: int = 30,
    user = Depends(get_current_user)
):
    """Get A/B testing dashboard with all active tests (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get all tests
    db_tests = await db.ab_tests.find({}).to_list(50)
    all_tests = db_tests + [t for t in DEFAULT_TESTS if not any(d["name"] == t["name"] for d in db_tests)]
    
    # Get summary for each test
    test_summaries = []
    for test in all_tests:
        test_name = test["name"]
        
        # Count total events
        total_events = await db.ab_events.count_documents({
            "test_id": test_name,
            "timestamp": {"$gte": start_date}
        })
        
        # Get top variant
        pipeline = [
            {
                "$match": {
                    "test_id": test_name,
                    "event_type": "conversion",
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$variant_id",
                    "conversions": {"$sum": 1}
                }
            },
            {"$sort": {"conversions": -1}},
            {"$limit": 1}
        ]
        
        top_variant = await db.ab_events.aggregate(pipeline).to_list(1)
        
        test_summaries.append({
            "name": test_name,
            "description": test.get("description"),
            "target_element": test.get("target_element"),
            "is_active": test.get("is_active", True),
            "variant_count": len(test.get("variants", [])),
            "total_events": total_events,
            "leading_variant": top_variant[0]["_id"] if top_variant else None
        })
    
    # Overall stats
    total_impressions = await db.ab_events.count_documents({
        "event_type": "impression",
        "timestamp": {"$gte": start_date}
    })
    
    total_conversions = await db.ab_events.count_documents({
        "event_type": "conversion",
        "timestamp": {"$gte": start_date}
    })
    
    return {
        "period_days": days,
        "tests": test_summaries,
        "active_tests": sum(1 for t in test_summaries if t["is_active"]),
        "total_impressions": total_impressions,
        "total_conversions": total_conversions,
        "overall_conversion_rate": round(total_conversions / total_impressions * 100, 2) if total_impressions > 0 else 0
    }


# ==================== ADMIN ENDPOINTS ====================

@router.post("/tests", response_model=dict)
async def create_test(
    test: ABTestConfig,
    user = Depends(get_current_user)
):
    """Create a new A/B test (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check for duplicate
    existing = await db.ab_tests.find_one({"name": test.name})
    if existing:
        raise HTTPException(status_code=400, detail="Test with this name already exists")
    
    # Validate weights sum to 100
    total_weight = sum(v.get("weight", 0) for v in test.variants)
    if total_weight != 100:
        raise HTTPException(status_code=400, detail=f"Variant weights must sum to 100, got {total_weight}")
    
    test_data = {
        "name": test.name,
        "description": test.description,
        "target_element": test.target_element,
        "variants": test.variants,
        "is_active": test.is_active,
        "created_by": str(user["_id"]),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.ab_tests.insert_one(test_data)
    
    return {
        "success": True,
        "test_id": str(result.inserted_id),
        "name": test.name
    }


@router.put("/tests/{test_name}", response_model=dict)
async def update_test(
    test_name: str,
    is_active: Optional[bool] = None,
    user = Depends(get_current_user)
):
    """Update an A/B test (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    if is_active is not None:
        update_data["is_active"] = is_active
    
    result = await db.ab_tests.update_one(
        {"name": test_name},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return {"success": True, "updated": test_name}


@router.delete("/tests/{test_name}", response_model=dict)
async def delete_test(
    test_name: str,
    user = Depends(get_current_user)
):
    """Delete an A/B test (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.ab_tests.delete_one({"name": test_name})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return {"success": True, "deleted": test_name}
