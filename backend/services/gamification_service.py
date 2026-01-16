"""
InfoPilot Explorer - Gamification Service
User achievements, badges, and gamification features
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bson import ObjectId
from config import db, logger


# Achievement Definitions
ACHIEVEMENTS = {
    # Search Achievements
    "first_search": {
        "id": "first_search",
        "name": "Search Pioneer 🔍",
        "description": "Performed your first search",
        "icon": "🔍",
        "category": "search",
        "points": 10,
        "requirement": {"type": "search_count", "value": 1}
    },
    "search_10": {
        "id": "search_10",
        "name": "Search Enthusiast 🎯",
        "description": "Performed 10 searches",
        "icon": "🎯",
        "category": "search",
        "points": 25,
        "requirement": {"type": "search_count", "value": 10}
    },
    "search_50": {
        "id": "search_50",
        "name": "Search Master 🏆",
        "description": "Performed 50 searches",
        "icon": "🏆",
        "category": "search",
        "points": 50,
        "requirement": {"type": "search_count", "value": 50}
    },
    "search_100": {
        "id": "search_100",
        "name": "Search Legend 👑",
        "description": "Performed 100 searches - You're unstoppable!",
        "icon": "👑",
        "category": "search",
        "points": 100,
        "requirement": {"type": "search_count", "value": 100}
    },
    
    # Protocol Achievements
    "first_protocol": {
        "id": "first_protocol",
        "name": "Protocol Creator 📝",
        "description": "Created your first category/protocol",
        "icon": "📝",
        "category": "protocol",
        "points": 15,
        "requirement": {"type": "protocol_count", "value": 1}
    },
    "protocol_5": {
        "id": "protocol_5",
        "name": "Protocol Builder 🔧",
        "description": "Created 5 categories/protocols",
        "icon": "🔧",
        "category": "protocol",
        "points": 40,
        "requirement": {"type": "protocol_count", "value": 5}
    },
    "protocol_10": {
        "id": "protocol_10",
        "name": "Protocol Architect 🏗️",
        "description": "Created 10 categories/protocols - You're building empires!",
        "icon": "🏗️",
        "category": "protocol",
        "points": 75,
        "requirement": {"type": "protocol_count", "value": 10}
    },
    
    # Marketplace Achievements
    "first_sale": {
        "id": "first_sale",
        "name": "First Sale 💵",
        "description": "Sold your first protocol - Cha-ching!",
        "icon": "💵",
        "category": "marketplace",
        "points": 50,
        "requirement": {"type": "sales_count", "value": 1}
    },
    "sales_10": {
        "id": "sales_10",
        "name": "Rising Seller ⭐",
        "description": "Sold 10 protocols",
        "icon": "⭐",
        "category": "marketplace",
        "points": 100,
        "requirement": {"type": "sales_count", "value": 10}
    },
    "sales_50": {
        "id": "sales_50",
        "name": "Top Seller 🔥",
        "description": "Sold 50 protocols - You're on fire!",
        "icon": "🔥",
        "category": "marketplace",
        "points": 200,
        "requirement": {"type": "sales_count", "value": 50}
    },
    "sales_100": {
        "id": "sales_100",
        "name": "Protocol Mogul 💰",
        "description": "Sold 100 protocols - The marketplace bows to you!",
        "icon": "💰",
        "category": "marketplace",
        "points": 500,
        "requirement": {"type": "sales_count", "value": 100}
    },
    "revenue_100": {
        "id": "revenue_100",
        "name": "First $100 💸",
        "description": "Earned $100 in marketplace revenue",
        "icon": "💸",
        "category": "marketplace",
        "points": 150,
        "requirement": {"type": "revenue", "value": 100}
    },
    "revenue_1000": {
        "id": "revenue_1000",
        "name": "Protocol Millionaire 🤑",
        "description": "Earned $1,000 in marketplace revenue - You're practically royalty!",
        "icon": "🤑",
        "category": "marketplace",
        "points": 1000,
        "requirement": {"type": "revenue", "value": 1000}
    },
    
    # Social Achievements
    "first_friend": {
        "id": "first_friend",
        "name": "Social Butterfly 🦋",
        "description": "Made your first friend",
        "icon": "🦋",
        "category": "social",
        "points": 15,
        "requirement": {"type": "friend_count", "value": 1}
    },
    "friends_10": {
        "id": "friends_10",
        "name": "Popular Kid 🎉",
        "description": "Made 10 friends - You're the life of the party!",
        "icon": "🎉",
        "category": "social",
        "points": 50,
        "requirement": {"type": "friend_count", "value": 10}
    },
    "first_post": {
        "id": "first_post",
        "name": "Voice Heard 📢",
        "description": "Created your first post",
        "icon": "📢",
        "category": "social",
        "points": 10,
        "requirement": {"type": "post_count", "value": 1}
    },
    
    # Special Achievements
    "early_adopter": {
        "id": "early_adopter",
        "name": "Early Adopter 🚀",
        "description": "Joined InfoPilot during the early days",
        "icon": "🚀",
        "category": "special",
        "points": 100,
        "requirement": {"type": "special", "value": "early_adopter"}
    },
    "book_buyer": {
        "id": "book_buyer",
        "name": "Literary Connoisseur 📚",
        "description": "Purchased 'Letters to Evelyn' - Excellent taste!",
        "icon": "📚",
        "category": "special",
        "points": 50,
        "requirement": {"type": "special", "value": "book_buyer"}
    },
    "free_giver": {
        "id": "free_giver",
        "name": "Generous Soul 💝",
        "description": "Listed a FREE protocol for the community",
        "icon": "💝",
        "category": "special",
        "points": 25,
        "requirement": {"type": "special", "value": "free_protocol"}
    },
    "weekly_top_seller": {
        "id": "weekly_top_seller",
        "name": "Weekly Champion 🏅",
        "description": "Became the #1 seller of the week!",
        "icon": "🏅",
        "category": "special",
        "points": 200,
        "requirement": {"type": "special", "value": "weekly_top"}
    },
    
    # Consistency Achievements
    "login_streak_7": {
        "id": "login_streak_7",
        "name": "Week Warrior 📅",
        "description": "Logged in 7 days in a row",
        "icon": "📅",
        "category": "consistency",
        "points": 30,
        "requirement": {"type": "login_streak", "value": 7}
    },
    "login_streak_30": {
        "id": "login_streak_30",
        "name": "Month Master 🗓️",
        "description": "Logged in 30 days in a row - Dedication!",
        "icon": "🗓️",
        "category": "consistency",
        "points": 100,
        "requirement": {"type": "login_streak", "value": 30}
    },
    
    # Document Classification Achievements
    "first_personal_report": {
        "id": "first_personal_report",
        "name": "Storyteller 📝",
        "description": "Created your first Personal Report (Organic)",
        "icon": "📝",
        "category": "content",
        "points": 25,
        "requirement": {"type": "personal_report_count", "value": 1}
    },
    "personal_reports_10": {
        "id": "personal_reports_10",
        "name": "Prolific Writer ✍️",
        "description": "Created 10 Personal Reports - Your voice matters!",
        "icon": "✍️",
        "category": "content",
        "points": 75,
        "requirement": {"type": "personal_report_count", "value": 10}
    },
    "phd_finder": {
        "id": "phd_finder",
        "name": "Academic Hunter 🎓",
        "description": "Found 10 PhD Informative articles",
        "icon": "🎓",
        "category": "search",
        "points": 50,
        "requirement": {"type": "phd_articles_found", "value": 10}
    },
    "news_junkie": {
        "id": "news_junkie",
        "name": "News Junkie 📰",
        "description": "Collected 50 News Articles",
        "icon": "📰",
        "category": "search",
        "points": 40,
        "requirement": {"type": "news_articles_found", "value": 50}
    },
    
    # Map & Location Achievements
    "first_location": {
        "id": "first_location",
        "name": "Cartographer 🗺️",
        "description": "Added your first geotagged result",
        "icon": "🗺️",
        "category": "map",
        "points": 20,
        "requirement": {"type": "geotagged_count", "value": 1}
    },
    "world_traveler": {
        "id": "world_traveler",
        "name": "World Traveler 🌍",
        "description": "Results from 5 different countries!",
        "icon": "🌍",
        "category": "map",
        "points": 75,
        "requirement": {"type": "countries_count", "value": 5}
    },
    "globe_trotter": {
        "id": "globe_trotter",
        "name": "Globe Trotter ✈️",
        "description": "Results from 10 different countries - You're everywhere!",
        "icon": "✈️",
        "category": "map",
        "points": 150,
        "requirement": {"type": "countries_count", "value": 10}
    },
    
    # Collection Achievements
    "collector_100": {
        "id": "collector_100",
        "name": "Collector 📦",
        "description": "Collected 100 search results",
        "icon": "📦",
        "category": "collection",
        "points": 50,
        "requirement": {"type": "result_count", "value": 100}
    },
    "collector_500": {
        "id": "collector_500",
        "name": "Archivist 🏛️",
        "description": "Collected 500 search results - Building a library!",
        "icon": "🏛️",
        "category": "collection",
        "points": 150,
        "requirement": {"type": "result_count", "value": 500}
    },
    "collector_1000": {
        "id": "collector_1000",
        "name": "Knowledge Keeper 📜",
        "description": "Collected 1000 search results - Legendary!",
        "icon": "📜",
        "category": "collection",
        "points": 300,
        "requirement": {"type": "result_count", "value": 1000}
    },
    
    # Premium/Subscription Achievements  
    "premium_member": {
        "id": "premium_member",
        "name": "Premium Pioneer 💎",
        "description": "Upgraded to Premium membership",
        "icon": "💎",
        "category": "special",
        "points": 50,
        "requirement": {"type": "special", "value": "premium_upgrade"}
    },
    "annual_subscriber": {
        "id": "annual_subscriber",
        "name": "Committed Fan 🌟",
        "description": "Subscribed for a full year - We appreciate you!",
        "icon": "🌟",
        "category": "special",
        "points": 200,
        "requirement": {"type": "special", "value": "annual_subscription"}
    },
    
    # Fun/Easter Egg Achievements
    "midnight_owl": {
        "id": "midnight_owl",
        "name": "Night Owl 🦉",
        "description": "Searched between midnight and 4 AM",
        "icon": "🦉",
        "category": "fun",
        "points": 15,
        "requirement": {"type": "special", "value": "midnight_search"}
    },
    "early_bird": {
        "id": "early_bird",
        "name": "Early Bird 🐦",
        "description": "Searched before 6 AM - Rise and shine!",
        "icon": "🐦",
        "category": "fun",
        "points": 15,
        "requirement": {"type": "special", "value": "early_search"}
    },
    "weekend_warrior": {
        "id": "weekend_warrior",
        "name": "Weekend Warrior ⚔️",
        "description": "Active on both Saturday and Sunday",
        "icon": "⚔️",
        "category": "fun",
        "points": 20,
        "requirement": {"type": "special", "value": "weekend_activity"}
    }
}


class GamificationService:
    """Service for managing user achievements and gamification"""
    
    @staticmethod
    async def get_user_achievements(user_id: str) -> Dict[str, Any]:
        """Get all achievements for a user"""
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"achievements": [], "total_points": 0, "level": 1}
        
        earned_achievements = user.get("achievements", [])
        total_points = sum(ACHIEVEMENTS[a["id"]]["points"] for a in earned_achievements if a["id"] in ACHIEVEMENTS)
        level = GamificationService._calculate_level(total_points)
        
        return {
            "achievements": earned_achievements,
            "total_points": total_points,
            "level": level,
            "level_name": GamificationService._get_level_name(level),
            "next_level_points": GamificationService._points_for_level(level + 1),
            "progress_to_next": total_points - GamificationService._points_for_level(level)
        }
    
    @staticmethod
    async def check_and_award_achievements(user_id: str) -> List[Dict[str, Any]]:
        """Check all achievements and award any newly earned ones"""
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return []
        
        earned = user.get("achievements", [])
        earned_ids = set(a["id"] for a in earned)
        new_achievements = []
        
        # Get user stats
        stats = await GamificationService._get_user_stats(user_id)
        
        for achievement_id, achievement in ACHIEVEMENTS.items():
            if achievement_id in earned_ids:
                continue
            
            req = achievement["requirement"]
            earned_it = False
            
            if req["type"] == "search_count":
                earned_it = stats["search_count"] >= req["value"]
            elif req["type"] == "protocol_count":
                earned_it = stats["protocol_count"] >= req["value"]
            elif req["type"] == "sales_count":
                earned_it = stats["sales_count"] >= req["value"]
            elif req["type"] == "revenue":
                earned_it = stats["revenue"] >= req["value"]
            elif req["type"] == "friend_count":
                earned_it = stats["friend_count"] >= req["value"]
            elif req["type"] == "post_count":
                earned_it = stats["post_count"] >= req["value"]
            elif req["type"] == "login_streak":
                earned_it = stats["login_streak"] >= req["value"]
            elif req["type"] == "special":
                # Special achievements are awarded manually
                pass
            
            if earned_it:
                new_achievement = {
                    "id": achievement_id,
                    "earned_at": datetime.utcnow(),
                    "notified": False
                }
                new_achievements.append({**achievement, **new_achievement})
                earned.append(new_achievement)
        
        # Update user achievements
        if new_achievements:
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"achievements": earned}}
            )
        
        return new_achievements
    
    @staticmethod
    async def award_special_achievement(user_id: str, achievement_id: str) -> Optional[Dict[str, Any]]:
        """Manually award a special achievement"""
        if achievement_id not in ACHIEVEMENTS:
            return None
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        
        earned = user.get("achievements", [])
        if any(a["id"] == achievement_id for a in earned):
            return None  # Already earned
        
        achievement = ACHIEVEMENTS[achievement_id]
        new_achievement = {
            "id": achievement_id,
            "earned_at": datetime.utcnow(),
            "notified": False
        }
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"achievements": new_achievement}}
        )
        
        return {**achievement, **new_achievement}
    
    @staticmethod
    async def _get_user_stats(user_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a user"""
        search_count = await db.search_results.count_documents({"user_id": user_id})
        protocol_count = await db.categories.count_documents({"user_id": user_id})
        
        # Marketplace stats
        sales_pipeline = [
            {"$match": {"creator_id": user_id}},
            {"$group": {
                "_id": None,
                "total_sales": {"$sum": "$total_sales"},
                "total_revenue": {"$sum": "$creator_earnings"}
            }}
        ]
        sales_result = await db.marketplace_protocols.aggregate(sales_pipeline).to_list(1)
        sales_count = sales_result[0]["total_sales"] if sales_result else 0
        revenue = sales_result[0]["total_revenue"] if sales_result else 0
        
        # Social stats
        friend_count = len((await db.users.find_one({"_id": ObjectId(user_id)})).get("friends", []))
        post_count = await db.posts.count_documents({"user_id": user_id})
        
        # Login streak
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        login_streak = user.get("login_streak", 0)
        
        return {
            "search_count": search_count,
            "protocol_count": protocol_count,
            "sales_count": sales_count,
            "revenue": revenue,
            "friend_count": friend_count,
            "post_count": post_count,
            "login_streak": login_streak
        }
    
    @staticmethod
    def _calculate_level(points: int) -> int:
        """Calculate user level based on points"""
        if points < 50:
            return 1
        elif points < 150:
            return 2
        elif points < 300:
            return 3
        elif points < 500:
            return 4
        elif points < 800:
            return 5
        elif points < 1200:
            return 6
        elif points < 1800:
            return 7
        elif points < 2500:
            return 8
        elif points < 3500:
            return 9
        else:
            return 10
    
    @staticmethod
    def _points_for_level(level: int) -> int:
        """Get points required for a level"""
        levels = [0, 0, 50, 150, 300, 500, 800, 1200, 1800, 2500, 3500]
        return levels[min(level, 10)]
    
    @staticmethod
    def _get_level_name(level: int) -> str:
        """Get fun name for a level"""
        names = {
            1: "Search Newbie 🌱",
            2: "Protocol Apprentice 📖",
            3: "Data Explorer 🔍",
            4: "Info Seeker 🎯",
            5: "Knowledge Hunter 🏹",
            6: "Search Wizard 🧙‍♂️",
            7: "Data Master 🎓",
            8: "Protocol Sage 📜",
            9: "Info Legend 🌟",
            10: "InfoPilot Supreme 👑"
        }
        return names.get(level, "InfoPilot Supreme 👑")
    
    @staticmethod
    async def get_weekly_leaderboard() -> List[Dict[str, Any]]:
        """Get weekly leaderboard based on activity"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get top users by marketplace sales this week
        pipeline = [
            {"$match": {"created_at": {"$gte": week_ago}}},
            {"$group": {
                "_id": "$creator_id",
                "weekly_sales": {"$sum": 1},
                "weekly_revenue": {"$sum": "$price"}
            }},
            {"$sort": {"weekly_sales": -1}},
            {"$limit": 10}
        ]
        
        results = await db.marketplace_purchases.aggregate(pipeline).to_list(10)
        
        leaderboard = []
        for i, r in enumerate(results):
            user = await db.users.find_one({"_id": ObjectId(r["_id"])}) if r["_id"] else None
            leaderboard.append({
                "rank": i + 1,
                "user_id": r["_id"],
                "username": user.get("callsign", user.get("username", "Unknown")) if user else "Unknown",
                "weekly_sales": r["weekly_sales"],
                "weekly_revenue": round(r["weekly_revenue"], 2),
                "is_top": i == 0
            })
        
        return leaderboard
    
    @staticmethod
    async def award_weekly_top_seller():
        """Award the weekly top seller achievement"""
        leaderboard = await GamificationService.get_weekly_leaderboard()
        if leaderboard and leaderboard[0]["weekly_sales"] > 0:
            top_user_id = leaderboard[0]["user_id"]
            await GamificationService.award_special_achievement(top_user_id, "weekly_top_seller")
            
            # Create notification
            await db.notifications.insert_one({
                "user_id": top_user_id,
                "type": "achievement",
                "title": "🏅 Weekly Champion!",
                "message": "Congratulations! You're the #1 seller this week! The ghosts of InfoPilot salute you! 👻",
                "read": False,
                "created_at": datetime.utcnow()
            })
            
            return top_user_id
        return None


# Achievement routes will be added to the router
