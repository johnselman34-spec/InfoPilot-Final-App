"""
InfoPilot Explorer - Gamification Routes
User achievements, badges, and leaderboards
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
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

Join me on InfoPilot and start your journey: https://protocol-market-1.preview.emergentagent.com

#InfoPilot #Achievement #{achievement['category'].replace(' ', '')}"""

    return {
        "share_message": share_message,
        "achievement": achievement,
        "platforms": {
            "twitter": f"https://twitter.com/intent/tweet?text={share_message[:280]}",
            "facebook": "https://www.facebook.com/sharer/sharer.php?u=https://protocol-market-1.preview.emergentagent.com",
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



# ==================== LAUGH-O-METER ENDPOINTS ====================

@router.get("/laugh-stats", response_model=dict)
async def get_laugh_stats(user = Depends(get_current_user)):
    """Get user's Laugh-O-Meter statistics"""
    user_id = str(user["_id"])
    
    # Get or create laugh stats
    stats = await db.laugh_stats.find_one({"user_id": user_id})
    
    if not stats:
        # Initialize stats
        stats = {
            "user_id": user_id,
            "totalLaughs": 0,
            "todayLaughs": 0,
            "easterEggsFound": 0,
            "badges": [],
            "xp": 0,
            "level": 1,
            "title": "Giggle Rookie",
            "lastLaugh": None,
            "created_at": datetime.utcnow()
        }
        await db.laugh_stats.insert_one(stats)
    
    # Reset today's count if it's a new day
    if stats.get("lastLaugh"):
        last_date = stats["lastLaugh"].date() if isinstance(stats["lastLaugh"], datetime) else None
        if last_date and last_date < datetime.utcnow().date():
            await db.laugh_stats.update_one(
                {"user_id": user_id},
                {"$set": {"todayLaughs": 0}}
            )
            stats["todayLaughs"] = 0
    
    return {
        "totalLaughs": stats.get("totalLaughs", 0),
        "todayLaughs": stats.get("todayLaughs", 0),
        "easterEggsFound": stats.get("easterEggsFound", 0),
        "badges": stats.get("badges", []),
        "xp": stats.get("xp", 0),
        "level": stats.get("level", 1),
        "title": stats.get("title", "Giggle Rookie"),
        "lastLaugh": stats.get("lastLaugh").isoformat() if stats.get("lastLaugh") else None
    }


@router.post("/record-laugh", response_model=dict)
async def record_laugh(data: dict, user = Depends(get_current_user)):
    """Record a laugh/funny message encounter for Laugh-O-Meter"""
    user_id = str(user["_id"])
    source = data.get("source", "general")
    
    # Update stats
    await db.laugh_stats.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "totalLaughs": 1,
                "todayLaughs": 1,
                "xp": 1
            },
            "$set": {
                "lastLaugh": datetime.utcnow()
            },
            "$setOnInsert": {
                "badges": [],
                "easterEggsFound": 0,
                "level": 1,
                "title": "Giggle Rookie",
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Log the laugh
    await db.laugh_log.insert_one({
        "user_id": user_id,
        "source": source,
        "timestamp": datetime.utcnow()
    })
    
    return {"success": True, "message": "😂 Laugh recorded!"}


@router.post("/record-easter-egg", response_model=dict)
async def record_easter_egg(data: dict, user = Depends(get_current_user)):
    """Record an Easter egg discovery for Laugh-O-Meter"""
    user_id = str(user["_id"])
    egg_id = data.get("eggId")
    
    if not egg_id:
        raise HTTPException(status_code=400, detail="Easter egg ID required")
    
    # XP values for Easter eggs
    EGG_XP = {
        "egg_hunter": 100,
        "night_owl_laugh": 75,
        "early_bird_smile": 75,
        "rapid_fire": 150,
        "joke_collector": 50,
        "bundle_comedian": 200,
        "evelyn_fan": 100,
        "konami_master": 500
    }
    
    xp_earned = EGG_XP.get(egg_id, 50)
    
    # Update stats
    await db.laugh_stats.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {"badges": egg_id},
            "$inc": {
                "easterEggsFound": 1,
                "xp": xp_earned
            },
            "$setOnInsert": {
                "totalLaughs": 0,
                "todayLaughs": 0,
                "level": 1,
                "title": "Giggle Rookie",
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Log the discovery
    await db.easter_egg_discoveries.insert_one({
        "user_id": user_id,
        "egg_id": egg_id,
        "xp_earned": xp_earned,
        "discovered_at": datetime.utcnow()
    })
    
    return {
        "success": True,
        "egg_id": egg_id,
        "xp_earned": xp_earned,
        "message": f"🥚 Easter egg discovered! +{xp_earned} XP!"
    }


@router.get("/laugh-leaderboard", response_model=dict)
async def get_laugh_leaderboard(limit: int = 20):
    """Get the Laugh-O-Meter leaderboard"""
    top_laughers = await db.laugh_stats.find({}).sort("xp", -1).limit(limit).to_list(limit)
    
    leaderboard = []
    for i, stats in enumerate(top_laughers):
        # Get username
        user = await db.users.find_one({"_id": ObjectId(stats["user_id"])})
        username = "Anonymous Laugher"
        if user:
            username = user.get("callsign", user.get("username", user.get("email", "Unknown")))
        
        leaderboard.append({
            "rank": i + 1,
            "username": username,
            "totalLaughs": stats.get("totalLaughs", 0),
            "xp": stats.get("xp", 0),
            "level": stats.get("level", 1),
            "title": stats.get("title", "Giggle Rookie"),
            "badges_count": len(stats.get("badges", []))
        })
    
    return {
        "leaderboard": leaderboard,
        "total_participants": await db.laugh_stats.count_documents({})
    }


# ==================== DAILY LAUGH GOAL ENDPOINTS ====================

# Streak bonus XP values
STREAK_BONUSES = {
    3: 25,    # 3-day streak
    7: 75,    # 1-week streak
    14: 150,  # 2-week streak
    30: 400,  # Monthly streak
    100: 1000 # 100-day streak (LEGENDARY!)
}

@router.get("/daily-laugh-goal", response_model=dict)
async def get_daily_laugh_goal(user = Depends(get_current_user)):
    """Get user's daily laugh goal settings and progress"""
    user_id = str(user["_id"])
    
    goal_data = await db.daily_laugh_goals.find_one({"user_id": user_id})
    
    if not goal_data:
        # Create default goal
        goal_data = {
            "user_id": user_id,
            "daily_goal": 10,  # Default: 10 laughs per day
            "current_progress": 0,
            "streak_days": 0,
            "longest_streak": 0,
            "total_goals_completed": 0,
            "last_goal_date": None,
            "streak_xp_earned": 0,
            "created_at": datetime.utcnow()
        }
        await db.daily_laugh_goals.insert_one(goal_data)
    
    # Check if it's a new day and reset progress
    today = datetime.utcnow().date()
    last_goal_date = goal_data.get("last_goal_date")
    
    if last_goal_date:
        last_date = last_goal_date.date() if isinstance(last_goal_date, datetime) else last_goal_date
        if last_date < today:
            # Check if goal was completed yesterday (maintain streak)
            yesterday = today - timedelta(days=1)
            if last_date == yesterday and goal_data.get("current_progress", 0) >= goal_data.get("daily_goal", 10):
                # Streak continues!
                pass
            elif last_date < yesterday:
                # Streak broken!
                await db.daily_laugh_goals.update_one(
                    {"user_id": user_id},
                    {"$set": {"streak_days": 0, "current_progress": 0}}
                )
                goal_data["streak_days"] = 0
                goal_data["current_progress"] = 0
    
    return {
        "daily_goal": goal_data.get("daily_goal", 10),
        "current_progress": goal_data.get("current_progress", 0),
        "streak_days": goal_data.get("streak_days", 0),
        "longest_streak": goal_data.get("longest_streak", 0),
        "total_goals_completed": goal_data.get("total_goals_completed", 0),
        "streak_xp_earned": goal_data.get("streak_xp_earned", 0),
        "goal_completed_today": goal_data.get("current_progress", 0) >= goal_data.get("daily_goal", 10),
        "next_streak_bonus": next((days for days in sorted(STREAK_BONUSES.keys()) if days > goal_data.get("streak_days", 0)), None)
    }


@router.post("/daily-laugh-goal/set", response_model=dict)
async def set_daily_laugh_goal(data: dict, user = Depends(get_current_user)):
    """Set user's daily laugh goal (5-100 laughs)"""
    user_id = str(user["_id"])
    new_goal = data.get("goal", 10)
    
    # Validate goal (5-100 range)
    new_goal = max(5, min(100, int(new_goal)))
    
    await db.daily_laugh_goals.update_one(
        {"user_id": user_id},
        {
            "$set": {"daily_goal": new_goal},
            "$setOnInsert": {
                "current_progress": 0,
                "streak_days": 0,
                "longest_streak": 0,
                "total_goals_completed": 0,
                "streak_xp_earned": 0,
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {
        "success": True,
        "daily_goal": new_goal,
        "message": f"🎯 Daily laugh goal set to {new_goal}! Let the giggles begin!"
    }


@router.post("/daily-laugh-goal/record-progress", response_model=dict)
async def record_daily_laugh_progress(user = Depends(get_current_user)):
    """Record progress toward daily laugh goal"""
    user_id = str(user["_id"])
    today = datetime.utcnow()
    
    goal_data = await db.daily_laugh_goals.find_one({"user_id": user_id})
    
    if not goal_data:
        goal_data = {
            "user_id": user_id,
            "daily_goal": 10,
            "current_progress": 0,
            "streak_days": 0,
            "longest_streak": 0,
            "total_goals_completed": 0,
            "streak_xp_earned": 0
        }
        await db.daily_laugh_goals.insert_one(goal_data)
    
    daily_goal = goal_data.get("daily_goal", 10)
    current_progress = goal_data.get("current_progress", 0) + 1
    streak_days = goal_data.get("streak_days", 0)
    longest_streak = goal_data.get("longest_streak", 0)
    total_completed = goal_data.get("total_goals_completed", 0)
    streak_xp = goal_data.get("streak_xp_earned", 0)
    
    goal_just_completed = False
    streak_bonus_earned = 0
    
    # Check if goal just completed
    if current_progress >= daily_goal and (goal_data.get("current_progress", 0) < daily_goal):
        goal_just_completed = True
        streak_days += 1
        total_completed += 1
        
        # Update longest streak
        if streak_days > longest_streak:
            longest_streak = streak_days
        
        # Check for streak bonuses
        if streak_days in STREAK_BONUSES:
            streak_bonus_earned = STREAK_BONUSES[streak_days]
            streak_xp += streak_bonus_earned
            
            # Award XP to laugh stats
            await db.laugh_stats.update_one(
                {"user_id": user_id},
                {"$inc": {"xp": streak_bonus_earned}},
                upsert=True
            )
    
    # Update goal data
    await db.daily_laugh_goals.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "current_progress": current_progress,
                "streak_days": streak_days,
                "longest_streak": longest_streak,
                "total_goals_completed": total_completed,
                "last_goal_date": today,
                "streak_xp_earned": streak_xp
            }
        }
    )
    
    response = {
        "success": True,
        "current_progress": current_progress,
        "daily_goal": daily_goal,
        "goal_completed": current_progress >= daily_goal,
        "streak_days": streak_days
    }
    
    if goal_just_completed:
        response["celebration"] = "🎉 DAILY GOAL COMPLETE! You're on FIRE!"
        response["streak_message"] = f"🔥 {streak_days}-day streak! Keep it going!"
    
    if streak_bonus_earned > 0:
        response["streak_bonus"] = {
            "days": streak_days,
            "xp_earned": streak_bonus_earned,
            "message": f"🏆 STREAK BONUS! +{streak_bonus_earned} XP for {streak_days}-day streak!"
        }
    
    return response


@router.get("/daily-laugh-goal/leaderboard", response_model=dict)
async def get_streak_leaderboard(limit: int = 20):
    """Get the streak leaderboard - who has the longest laugh goal streak!"""
    top_streakers = await db.daily_laugh_goals.find({}).sort("streak_days", -1).limit(limit).to_list(limit)
    
    leaderboard = []
    for i, goal_data in enumerate(top_streakers):
        # Get username
        try:
            user = await db.users.find_one({"_id": ObjectId(goal_data["user_id"])})
            username = "Mystery Laugher"
            if user:
                username = user.get("callsign", user.get("username", user.get("email", "Unknown")))
        except Exception:
            username = "Mystery Laugher"
        
        leaderboard.append({
            "rank": i + 1,
            "username": username,
            "streak_days": goal_data.get("streak_days", 0),
            "longest_streak": goal_data.get("longest_streak", 0),
            "total_goals_completed": goal_data.get("total_goals_completed", 0),
            "daily_goal": goal_data.get("daily_goal", 10),
            "streak_xp_earned": goal_data.get("streak_xp_earned", 0)
        })
    
    return {
        "leaderboard": leaderboard,
        "total_participants": await db.daily_laugh_goals.count_documents({"streak_days": {"$gt": 0}}),
        "funny_title": "🏆 Hall of Hilarious Habits 🏆"
    }

