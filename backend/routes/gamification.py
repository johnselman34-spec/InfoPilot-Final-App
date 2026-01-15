"""
InfoPilot Explorer - Gamification Routes
User achievements, badges, and leaderboards
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from bson import ObjectId

from config import db
from routes.auth import get_current_user, get_optional_user
from services.gamification_service import GamificationService, ACHIEVEMENTS

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/achievements", response_model=dict)
async def get_all_achievements():
    """Get list of all available achievements"""
    achievements_list = []
    for achievement_id, achievement in ACHIEVEMENTS.items():
        achievements_list.append({
            "id": achievement_id,
            "name": achievement["name"],
            "description": achievement["description"],
            "icon": achievement["icon"],
            "category": achievement["category"],
            "points": achievement["points"]
        })
    
    # Group by category
    categories = {}
    for a in achievements_list:
        cat = a["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(a)
    
    return {
        "achievements": achievements_list,
        "by_category": categories,
        "total_achievements": len(achievements_list),
        "total_points_possible": sum(a["points"] for a in achievements_list)
    }


@router.get("/my-achievements", response_model=dict)
async def get_my_achievements(user = Depends(get_current_user)):
    """Get current user's achievements and progress"""
    user_achievements = await GamificationService.get_user_achievements(str(user["_id"]))
    
    # Add full achievement details
    earned_ids = set(a["id"] for a in user_achievements["achievements"])
    detailed_achievements = []
    
    for a in user_achievements["achievements"]:
        if a["id"] in ACHIEVEMENTS:
            full_achievement = ACHIEVEMENTS[a["id"]]
            detailed_achievements.append({
                **full_achievement,
                "earned_at": a["earned_at"].isoformat() if isinstance(a["earned_at"], datetime) else a["earned_at"]
            })
    
    # Get unearned achievements
    unearned = [
        {**ACHIEVEMENTS[aid], "id": aid}
        for aid in ACHIEVEMENTS.keys()
        if aid not in earned_ids
    ]
    
    return {
        "earned": detailed_achievements,
        "unearned": unearned,
        "total_points": user_achievements["total_points"],
        "level": user_achievements["level"],
        "level_name": user_achievements["level_name"],
        "next_level_points": user_achievements["next_level_points"],
        "progress_to_next": user_achievements["progress_to_next"],
        "completion_percentage": round(len(detailed_achievements) / len(ACHIEVEMENTS) * 100, 1)
    }


@router.post("/check-achievements", response_model=dict)
async def check_achievements(user = Depends(get_current_user)):
    """Check and award any new achievements for the current user"""
    new_achievements = await GamificationService.check_and_award_achievements(str(user["_id"]))
    
    if new_achievements:
        # Create notifications for new achievements
        for achievement in new_achievements:
            await db.notifications.insert_one({
                "user_id": str(user["_id"]),
                "type": "achievement",
                "title": "🏆 Achievement Unlocked!",
                "message": f"You earned: {achievement['name']} - {achievement['description']}",
                "read": False,
                "created_at": datetime.utcnow()
            })
    
    return {
        "new_achievements": new_achievements,
        "count": len(new_achievements),
        "message": f"🎉 You earned {len(new_achievements)} new achievement(s)!" if new_achievements else "Keep going! More achievements await!"
    }


@router.get("/leaderboard/weekly", response_model=dict)
async def get_weekly_leaderboard():
    """Get the weekly activity leaderboard"""
    leaderboard = await GamificationService.get_weekly_leaderboard()
    
    # Add fun commentary
    commentary = "The ghosts are watching... 👻" if not leaderboard else \
        f"🏆 {leaderboard[0]['username']} is dominating this week!" if leaderboard[0]["weekly_sales"] > 5 else \
        "It's anyone's game this week!"
    
    return {
        "leaderboard": leaderboard,
        "period": "This Week",
        "commentary": commentary,
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/leaderboard/all-time", response_model=dict)
async def get_all_time_leaderboard():
    """Get the all-time points leaderboard"""
    # Get users with most points
    users = await db.users.find({"achievements": {"$exists": True, "$ne": []}}).to_list(100)
    
    leaderboard = []
    for user in users:
        total_points = sum(
            ACHIEVEMENTS[a["id"]]["points"] 
            for a in user.get("achievements", []) 
            if a["id"] in ACHIEVEMENTS
        )
        leaderboard.append({
            "user_id": str(user["_id"]),
            "username": user.get("callsign", user.get("username", "Unknown")),
            "total_points": total_points,
            "achievement_count": len(user.get("achievements", [])),
            "level": GamificationService._calculate_level(total_points),
            "level_name": GamificationService._get_level_name(GamificationService._calculate_level(total_points))
        })
    
    # Sort by points
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    # Add ranks
    for i, entry in enumerate(leaderboard[:20]):
        entry["rank"] = i + 1
    
    return {
        "leaderboard": leaderboard[:20],
        "period": "All Time",
        "last_updated": datetime.utcnow().isoformat()
    }


@router.post("/share-achievement/{achievement_id}", response_model=dict)
async def share_achievement(achievement_id: str, user = Depends(get_current_user)):
    """Generate a shareable link/message for an achievement"""
    if achievement_id not in ACHIEVEMENTS:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    achievement = ACHIEVEMENTS[achievement_id]
    
    # Check if user has earned this achievement
    user_achievements = user.get("achievements", [])
    if not any(a["id"] == achievement_id for a in user_achievements):
        raise HTTPException(status_code=403, detail="You haven't earned this achievement yet!")
    
    share_message = f"""🏆 I just earned the "{achievement['name']}" achievement on InfoPilot Explorer!

{achievement['icon']} {achievement['description']}

Join me on InfoPilot and start your journey: https://explorer-hub-7.preview.emergentagent.com

#InfoPilot #Achievement #{achievement['category'].replace(' ', '')}"""

    return {
        "share_message": share_message,
        "achievement": achievement,
        "platforms": {
            "twitter": f"https://twitter.com/intent/tweet?text={share_message[:280]}",
            "facebook": "https://www.facebook.com/sharer/sharer.php?u=https://explorer-hub-7.preview.emergentagent.com",
        }
    }


@router.get("/user/{user_id}/achievements", response_model=dict)
async def get_user_achievements(user_id: str, current_user = Depends(get_optional_user)):
    """Get achievements for a specific user (public profile)"""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_achievements = await GamificationService.get_user_achievements(user_id)
    
    return {
        "username": user.get("callsign", user.get("username", "Unknown")),
        "total_points": user_achievements["total_points"],
        "level": user_achievements["level"],
        "level_name": user_achievements["level_name"],
        "achievement_count": len(user_achievements["achievements"]),
        "achievements": [
            {**ACHIEVEMENTS[a["id"]], "earned_at": a["earned_at"].isoformat() if isinstance(a["earned_at"], datetime) else a["earned_at"]}
            for a in user_achievements["achievements"]
            if a["id"] in ACHIEVEMENTS
        ]
    }
