"""
Easter Eggs routes for InfoPilot Explorer
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone

from services.database import db
from models.schemas import User
from routers.auth import require_auth

router = APIRouter(prefix="/easter-eggs", tags=["Easter Eggs"])


EASTER_EGG_JOKES = [
    "Why did the protocol cross the search engine? To get to the other database!",
    "I told my protocol it was looking sharp today. It replied with a perfectly parsed boolean.",
    "My stepmother tried to poison me, but jokes on her - I became a bestselling author!",
    "What do you call a protocol that tells jokes? A fun-ction!",
    "I asked the Internet Robot for advice. It said 'Have you tried turning your search strategy off and on again?'",
    "Why don't protocols ever get invited to parties? They're too exclusive... or inclusive... depends on the modifier!",
    "My search results were so good, even Google was jealous.",
    "InfoPilot: Because sometimes you need a pilot to navigate the information superhighway.",
    "What's a protocol's favorite music? Boolean beats!",
    "I wrote a protocol so good, it collated itself."
]


@router.get("")
async def get_easter_eggs(user: User = Depends(require_auth)):
    """Get available easter eggs"""
    eggs = await db.easter_eggs.find({}, {"_id": 0}).to_list(50)
    
    if not eggs:
        # Initialize default easter eggs
        default_eggs = [
            {
                "egg_id": f"egg_{i}",
                "type": "joke",
                "content": joke,
                "reward_type": "xp",
                "reward_amount": 5,
                "times_found": 0
            }
            for i, joke in enumerate(EASTER_EGG_JOKES)
        ]
        await db.easter_eggs.insert_many(default_eggs)
        # Remove _id from eggs for JSON serialization
        for egg in default_eggs:
            egg.pop("_id", None)
        eggs = default_eggs
    
    return {"easter_eggs": eggs}


@router.post("/discover")
async def discover_easter_egg(
    request: Request,
    user: User = Depends(require_auth)
):
    """Discover an easter egg"""
    data = await request.json()
    egg_id = data.get("egg_id")
    
    # Check if already discovered
    existing = await db.user_discoveries.find_one({
        "user_id": user.user_id,
        "egg_id": egg_id
    })
    
    if existing:
        return {"message": "Already discovered", "first_time": False}
    
    # Record discovery
    await db.user_discoveries.insert_one({
        "user_id": user.user_id,
        "egg_id": egg_id,
        "discovered_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Update egg count
    await db.easter_eggs.update_one(
        {"egg_id": egg_id},
        {"$inc": {"times_found": 1}}
    )
    
    # Get egg and reward user
    egg = await db.easter_eggs.find_one({"egg_id": egg_id}, {"_id": 0})
    
    if egg and egg.get("reward_type") == "xp":
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$inc": {"xp": egg.get("reward_amount", 5)}}
        )
    
    return {"message": "Easter egg discovered!", "egg": egg, "first_time": True}


@router.get("/laugh-stats")
async def get_laugh_stats(user: User = Depends(require_auth)):
    """Get laugh-o-meter stats"""
    stats = await db.laugh_stats.aggregate([
        {"$group": {
            "_id": "$egg_id",
            "total_laughs": {"$sum": 1},
            "avg_rating": {"$avg": "$rating"}
        }},
        {"$sort": {"total_laughs": -1}}
    ]).to_list(50)
    
    return {"stats": stats}


@router.post("/laugh")
async def record_laugh(
    request: Request,
    user: User = Depends(require_auth)
):
    """Record a laugh for the laugh-o-meter"""
    data = await request.json()
    
    await db.laugh_stats.insert_one({
        "user_id": user.user_id,
        "egg_id": data.get("egg_id"),
        "rating": data.get("rating", 5),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Laugh recorded!"}


@router.post("/laugh-submit")
async def submit_laugh(
    request: Request,
    user: User = Depends(require_auth)
):
    """Submit a laugh rating with XP reward"""
    data = await request.json()
    egg_id = data.get("egg_id")
    laugh_type = data.get("laugh_type", "chuckle")  # chuckle, laugh, rofl
    
    # XP rewards by laugh type
    xp_rewards = {
        "chuckle": 1,
        "laugh": 3,
        "rofl": 5
    }
    
    # Record the laugh
    await db.laugh_stats.insert_one({
        "user_id": user.user_id,
        "egg_id": egg_id,
        "laugh_type": laugh_type,
        "rating": xp_rewards.get(laugh_type, 1),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Award XP
    xp_earned = xp_rewards.get(laugh_type, 1)
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"xp": xp_earned}}
    )
    
    return {"message": f"Laugh recorded! +{xp_earned} XP", "xp_earned": xp_earned}


@router.get("/laugh-leaderboard")
async def get_laugh_leaderboard():
    """Get laugh-o-meter leaderboard"""
    # Most laughed at jokes
    funniest_jokes = await db.laugh_stats.aggregate([
        {"$group": {
            "_id": "$egg_id",
            "total_laughs": {"$sum": 1},
            "rofl_count": {"$sum": {"$cond": [{"$eq": ["$laugh_type", "rofl"]}, 1, 0]}},
            "laugh_count": {"$sum": {"$cond": [{"$eq": ["$laugh_type", "laugh"]}, 1, 0]}},
            "chuckle_count": {"$sum": {"$cond": [{"$eq": ["$laugh_type", "chuckle"]}, 1, 0]}}
        }},
        {"$sort": {"total_laughs": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get joke content
    for joke_stat in funniest_jokes:
        egg = await db.easter_eggs.find_one({"egg_id": joke_stat["_id"]}, {"_id": 0})
        joke_stat["joke"] = egg
    
    # Biggest laughers
    top_laughers = await db.laugh_stats.aggregate([
        {"$group": {
            "_id": "$user_id",
            "total_laughs": {"$sum": 1},
            "total_xp": {"$sum": "$rating"}
        }},
        {"$sort": {"total_laughs": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Get user info
    for laugher in top_laughers:
        user = await db.users.find_one(
            {"user_id": laugher["_id"]},
            {"_id": 0, "name": 1, "picture": 1, "callsign": 1}
        )
        laugher["user"] = user
    
    return {
        "funniest_jokes": funniest_jokes,
        "top_laughers": top_laughers
    }
