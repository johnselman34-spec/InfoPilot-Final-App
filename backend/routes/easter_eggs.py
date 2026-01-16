"""
InfoPilot Explorer - Easter Egg Tracker Routes
Tracks hidden Easter eggs found by users and awards special badges
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId

from config import db, logger
from routes.auth import get_current_user

router = APIRouter(prefix="/easter-eggs", tags=["Easter Eggs"])


# ==================== EASTER EGG DEFINITIONS ====================

EASTER_EGGS = {
    "egg_hunter": {
        "id": "egg_hunter",
        "name": "🥚 Egg Hunter",
        "description": "Found your first Easter egg!",
        "xp": 100,
        "rarity": "rare",
        "icon": "🥚",
        "hint": "Keep exploring... Easter eggs are hidden everywhere!"
    },
    "night_owl_laugh": {
        "id": "night_owl_laugh",
        "name": "🦉 Night Owl Giggler",
        "description": "Found a joke after midnight!",
        "xp": 75,
        "rarity": "rare",
        "icon": "🦉",
        "hint": "Late night browsing has its rewards..."
    },
    "early_bird_smile": {
        "id": "early_bird_smile",
        "name": "🐦 Early Bird Smiler",
        "description": "Started the day with a laugh before 6 AM!",
        "xp": 75,
        "rarity": "rare",
        "icon": "🐦",
        "hint": "The early bird catches the worm... and the jokes!"
    },
    "rapid_fire": {
        "id": "rapid_fire",
        "name": "🔥 Rapid Fire Laugher",
        "description": "Saw 10 jokes in under a minute!",
        "xp": 150,
        "rarity": "rare",
        "icon": "🔥",
        "hint": "Speed reading through comedy gold..."
    },
    "joke_collector": {
        "id": "joke_collector",
        "name": "📚 Joke Collector",
        "description": "Copied a joke to share with friends!",
        "xp": 50,
        "rarity": "uncommon",
        "icon": "📚",
        "hint": "Good jokes deserve to be shared!"
    },
    "bundle_comedian": {
        "id": "bundle_comedian",
        "name": "📦 Bundle Comedian",
        "description": "Bought a bundle and laughed at the tagline!",
        "xp": 200,
        "rarity": "epic",
        "icon": "📦",
        "hint": "Our bundle descriptions are legendary..."
    },
    "evelyn_fan": {
        "id": "evelyn_fan",
        "name": "📖 Letters to Evelyn Fan",
        "description": "Clicked on a book promo!",
        "xp": 100,
        "rarity": "rare",
        "icon": "📖",
        "hint": "Supporting great literature... and ghosts!"
    },
    "konami_master": {
        "id": "konami_master",
        "name": "🎮 Konami Master",
        "description": "Entered the secret code!",
        "xp": 500,
        "rarity": "legendary",
        "icon": "🎮",
        "hint": "↑ ↑ ↓ ↓ ← → ← → B A"
    },
    "secret_search": {
        "id": "secret_search",
        "name": "🔍 Secret Searcher",
        "description": "Searched for 'letterstoeveelyn' or 'infopilot rocks'!",
        "xp": 150,
        "rarity": "epic",
        "icon": "🔍",
        "hint": "Try searching for something special..."
    },
    "map_explorer": {
        "id": "map_explorer",
        "name": "🗺️ Map Explorer",
        "description": "Viewed 50+ results on the interactive map!",
        "xp": 100,
        "rarity": "rare",
        "icon": "🗺️",
        "hint": "The world is full of information..."
    },
    "statistician": {
        "id": "statistician",
        "name": "📊 Statistician",
        "description": "Viewed every chart on the Statistics page!",
        "xp": 75,
        "rarity": "uncommon",
        "icon": "📊",
        "hint": "Data nerds unite!"
    },
    "social_butterfly": {
        "id": "social_butterfly",
        "name": "🦋 Social Butterfly",
        "description": "Made 10+ friends on InfoPilot!",
        "xp": 200,
        "rarity": "epic",
        "icon": "🦋",
        "hint": "Friendship is the best protocol!"
    },
    "midnight_message": {
        "id": "midnight_message",
        "name": "🌙 Midnight Messenger",
        "description": "Sent a message exactly at midnight!",
        "xp": 100,
        "rarity": "rare",
        "icon": "🌙",
        "hint": "Timing is everything..."
    },
    "tutorial_complete": {
        "id": "tutorial_complete",
        "name": "🎓 Tutorial Graduate",
        "description": "Completed all tutorials!",
        "xp": 250,
        "rarity": "epic",
        "icon": "🎓",
        "hint": "Knowledge is power!"
    },
    "voice_pioneer": {
        "id": "voice_pioneer",
        "name": "🎤 Voice Pioneer",
        "description": "Used voice search 25 times!",
        "xp": 150,
        "rarity": "rare",
        "icon": "🎤",
        "hint": "Talk to InfoPilot..."
    }
}


# ==================== ENDPOINTS ====================

@router.get("/all", response_model=dict)
async def get_all_easter_eggs():
    """Get list of all Easter eggs (hints only for undiscovered)"""
    eggs_list = []
    for egg_id, egg in EASTER_EGGS.items():
        eggs_list.append({
            "id": egg_id,
            "name": egg["name"],
            "description": egg["description"],
            "xp": egg["xp"],
            "rarity": egg["rarity"],
            "icon": egg["icon"],
            "hint": egg["hint"]
        })
    
    # Group by rarity
    by_rarity = {
        "common": [e for e in eggs_list if e["rarity"] == "common"],
        "uncommon": [e for e in eggs_list if e["rarity"] == "uncommon"],
        "rare": [e for e in eggs_list if e["rarity"] == "rare"],
        "epic": [e for e in eggs_list if e["rarity"] == "epic"],
        "legendary": [e for e in eggs_list if e["rarity"] == "legendary"]
    }
    
    return {
        "eggs": eggs_list,
        "by_rarity": by_rarity,
        "total": len(eggs_list),
        "total_xp_possible": sum(e["xp"] for e in eggs_list)
    }


@router.get("/my-discoveries", response_model=dict)
async def get_my_discoveries(user = Depends(get_current_user)):
    """Get user's discovered Easter eggs"""
    user_id = str(user["_id"])
    
    # Get discoveries from easter_egg_discoveries collection
    discoveries = await db.easter_egg_discoveries.find({"user_id": user_id}).to_list(1000)
    
    # Also check laugh_stats badges
    laugh_stats = await db.laugh_stats.find_one({"user_id": user_id})
    badge_eggs = laugh_stats.get("badges", []) if laugh_stats else []
    
    # Merge discoveries
    discovered_ids = set([d["egg_id"] for d in discoveries] + badge_eggs)
    
    discovered = []
    undiscovered = []
    
    for egg_id, egg in EASTER_EGGS.items():
        if egg_id in discovered_ids:
            # Get discovery time
            discovery = next((d for d in discoveries if d["egg_id"] == egg_id), None)
            discovered.append({
                **egg,
                "discovered_at": discovery["discovered_at"].isoformat() if discovery and discovery.get("discovered_at") else None,
                "xp_earned": discovery.get("xp_earned", egg["xp"]) if discovery else egg["xp"]
            })
        else:
            undiscovered.append({
                "id": egg_id,
                "name": "🔒 ???",
                "hint": egg["hint"],
                "rarity": egg["rarity"],
                "xp": egg["xp"]
            })
    
    return {
        "discovered": discovered,
        "undiscovered": undiscovered,
        "discovered_count": len(discovered),
        "total_eggs": len(EASTER_EGGS),
        "total_xp_earned": sum(e.get("xp_earned", e["xp"]) for e in discovered),
        "completion_percentage": round(len(discovered) / len(EASTER_EGGS) * 100, 1)
    }


@router.post("/discover", response_model=dict)
async def discover_easter_egg(data: dict, user = Depends(get_current_user)):
    """Record discovery of an Easter egg"""
    user_id = str(user["_id"])
    egg_id = data.get("egg_id")
    trigger = data.get("trigger", "manual")  # What triggered the discovery
    
    if not egg_id:
        raise HTTPException(status_code=400, detail="Easter egg ID required")
    
    if egg_id not in EASTER_EGGS:
        raise HTTPException(status_code=404, detail="Easter egg not found")
    
    egg = EASTER_EGGS[egg_id]
    
    # Check if already discovered
    existing = await db.easter_egg_discoveries.find_one({
        "user_id": user_id,
        "egg_id": egg_id
    })
    
    if existing:
        return {
            "success": False,
            "message": "You already discovered this Easter egg!",
            "already_discovered": True
        }
    
    # Record discovery
    discovery_record = {
        "user_id": user_id,
        "egg_id": egg_id,
        "xp_earned": egg["xp"],
        "trigger": trigger,
        "discovered_at": datetime.now(timezone.utc)
    }
    
    await db.easter_egg_discoveries.insert_one(discovery_record)
    
    # Update laugh_stats with badge
    await db.laugh_stats.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {"badges": egg_id},
            "$inc": {
                "easterEggsFound": 1,
                "xp": egg["xp"]
            },
            "$setOnInsert": {
                "totalLaughs": 0,
                "todayLaughs": 0,
                "level": 1,
                "title": "Giggle Rookie",
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    # Create notification
    await db.notifications.insert_one({
        "user_id": user_id,
        "type": "easter_egg",
        "title": "🥚 Easter Egg Discovered!",
        "message": f"You found {egg['name']}! +{egg['xp']} XP",
        "read": False,
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "egg": egg,
        "xp_earned": egg["xp"],
        "message": f"🎉 Congratulations! You discovered {egg['name']}! +{egg['xp']} XP!",
        "celebration": True
    }


@router.get("/leaderboard", response_model=dict)
async def get_easter_egg_leaderboard(limit: int = 20):
    """Get Easter egg discovery leaderboard"""
    # Aggregate discoveries by user
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "eggs_found": {"$sum": 1},
            "total_xp": {"$sum": "$xp_earned"},
            "first_discovery": {"$min": "$discovered_at"},
            "latest_discovery": {"$max": "$discovered_at"}
        }},
        {"$sort": {"eggs_found": -1, "total_xp": -1}},
        {"$limit": limit}
    ]
    
    results = await db.easter_egg_discoveries.aggregate(pipeline).to_list(limit)
    
    leaderboard = []
    for i, result in enumerate(results):
        # Get user info
        try:
            user = await db.users.find_one({"_id": ObjectId(result["_id"])})
            username = user.get("callsign", user.get("username", "Mystery Hunter")) if user else "Mystery Hunter"
        except Exception:
            username = "Mystery Hunter"
        
        # Determine title based on eggs found
        title = "Novice Hunter"
        if result["eggs_found"] >= 12:
            title = "Egg God 🏆"
        elif result["eggs_found"] >= 8:
            title = "Master Hunter 👑"
        elif result["eggs_found"] >= 5:
            title = "Expert Finder 🔍"
        elif result["eggs_found"] >= 3:
            title = "Rising Hunter 🌟"
        
        leaderboard.append({
            "rank": i + 1,
            "username": username,
            "eggs_found": result["eggs_found"],
            "total_xp": result.get("total_xp", 0),
            "title": title,
            "first_discovery": result.get("first_discovery").isoformat() if result.get("first_discovery") else None,
            "latest_discovery": result.get("latest_discovery").isoformat() if result.get("latest_discovery") else None
        })
    
    return {
        "leaderboard": leaderboard,
        "total_hunters": await db.easter_egg_discoveries.aggregate([{"$group": {"_id": "$user_id"}}]).to_list(1000).__len__(),
        "total_eggs_available": len(EASTER_EGGS),
        "funny_title": "🥚 Hall of Egg-cellent Hunters 🥚"
    }


@router.get("/stats", response_model=dict)
async def get_easter_egg_stats():
    """Get global Easter egg statistics"""
    total_discoveries = await db.easter_egg_discoveries.count_documents({})
    
    # Most discovered eggs
    most_discovered = await db.easter_egg_discoveries.aggregate([
        {"$group": {"_id": "$egg_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]).to_list(5)
    
    # Rarest discoveries (least found)
    all_eggs = list(EASTER_EGGS.keys())
    discovery_counts = {egg_id: 0 for egg_id in all_eggs}
    
    for disc in most_discovered:
        discovery_counts[disc["_id"]] = disc["count"]
    
    rarest = sorted(discovery_counts.items(), key=lambda x: x[1])[:5]
    
    return {
        "total_discoveries": total_discoveries,
        "total_eggs_available": len(EASTER_EGGS),
        "most_discovered": [
            {
                "egg_id": d["_id"],
                "name": EASTER_EGGS.get(d["_id"], {}).get("name", "Unknown"),
                "discovery_count": d["count"]
            }
            for d in most_discovered
        ],
        "rarest_eggs": [
            {
                "egg_id": egg_id,
                "name": EASTER_EGGS.get(egg_id, {}).get("name", "Unknown"),
                "discovery_count": count
            }
            for egg_id, count in rarest
        ]
    }
