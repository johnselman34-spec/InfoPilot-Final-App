"""
InfoPilot Explorer - Video Tutorials System
Provides video guides and tutorials for all application features
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
from bson import ObjectId

from config import db, logger
from routes.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/tutorials", tags=["Tutorials"])

# Video tutorial data - embedded YouTube videos
TUTORIALS = [
    {
        "id": "getting-started",
        "title": "Getting Started with InfoPilot Explorer",
        "description": "Learn the basics of InfoPilot Explorer and set up your account for success!",
        "youtube_id": "dQw4w9WgXcQ",  # Placeholder - replace with actual tutorial
        "duration": "5:30",
        "category": "basics",
        "order": 1,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "ultimate-search",
        "title": "Mastering Ultimate Search",
        "description": "Discover how to create powerful search protocols and get the best results.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "8:45",
        "category": "search",
        "order": 2,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "protocol-marketplace",
        "title": "Buying & Selling in the Marketplace",
        "description": "Turn your search expertise into cash! Learn how to list and sell protocols.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "7:15",
        "category": "marketplace",
        "order": 3,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "social-features",
        "title": "Social Hub: Friends, Groups & Pages",
        "description": "Connect with fellow researchers and build your InfoPilot community.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "6:30",
        "category": "social",
        "order": 4,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "direct-messaging",
        "title": "Direct Messaging & Real-time Chat",
        "description": "Stay connected with your network through instant messaging.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "4:00",
        "category": "social",
        "order": 5,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "achievements",
        "title": "Gamification & Achievements",
        "description": "Level up your profile and unlock exclusive badges and rewards!",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "5:00",
        "category": "gamification",
        "order": 6,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "voice-search",
        "title": "Voice Search with AI",
        "description": "Search hands-free using our advanced voice recognition powered by AI.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "3:45",
        "category": "search",
        "order": 7,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "polls",
        "title": "Creating Polls for Engagement",
        "description": "Boost engagement in your groups and pages with interactive polls.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "4:30",
        "category": "social",
        "order": 8,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "admin-features",
        "title": "Group & Page Administration",
        "description": "Learn how to manage moderators, admins, and member permissions.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "6:00",
        "category": "admin",
        "order": 9,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    },
    {
        "id": "mobile-extension",
        "title": "Mobile App & Browser Extension",
        "description": "Access InfoPilot on the go with our mobile app and browser extension.",
        "youtube_id": "dQw4w9WgXcQ",
        "duration": "5:15",
        "category": "basics",
        "order": 10,
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    }
]

CATEGORIES = [
    {"id": "basics", "name": "Getting Started", "icon": "🚀", "color": "#8b5cf6"},
    {"id": "search", "name": "Search & Protocols", "icon": "🔍", "color": "#3b82f6"},
    {"id": "marketplace", "name": "Marketplace", "icon": "💰", "color": "#10b981"},
    {"id": "social", "name": "Social Features", "icon": "👥", "color": "#f472b6"},
    {"id": "gamification", "name": "Achievements", "icon": "🏆", "color": "#f59e0b"},
    {"id": "admin", "name": "Administration", "icon": "⚙️", "color": "#ef4444"}
]


@router.get("", response_model=dict)
async def get_tutorials(category: Optional[str] = None):
    """Get all video tutorials"""
    tutorials = TUTORIALS.copy()
    
    if category:
        tutorials = [t for t in tutorials if t["category"] == category]
    
    # Sort by order
    tutorials.sort(key=lambda x: x["order"])
    
    return {
        "tutorials": tutorials,
        "categories": CATEGORIES,
        "total": len(tutorials)
    }


@router.get("/{tutorial_id}", response_model=dict)
async def get_tutorial(tutorial_id: str):
    """Get a specific tutorial"""
    tutorial = next((t for t in TUTORIALS if t["id"] == tutorial_id), None)
    
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    # Get related tutorials in same category
    related = [t for t in TUTORIALS if t["category"] == tutorial["category"] and t["id"] != tutorial_id][:3]
    
    return {
        "tutorial": tutorial,
        "related": related
    }


@router.post("/{tutorial_id}/progress", response_model=dict)
async def track_progress(tutorial_id: str, progress: int, user = Depends(get_current_user)):
    """Track user's tutorial progress"""
    user_id = str(user["_id"])
    
    # Validate tutorial exists
    tutorial = next((t for t in TUTORIALS if t["id"] == tutorial_id), None)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    # Update or insert progress
    await db.tutorial_progress.update_one(
        {"user_id": user_id, "tutorial_id": tutorial_id},
        {
            "$set": {
                "progress": min(progress, 100),
                "completed": progress >= 100,
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {
                "user_id": user_id,
                "tutorial_id": tutorial_id,
                "started_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Award achievement if completed first tutorial
    if progress >= 100:
        completed_count = await db.tutorial_progress.count_documents({
            "user_id": user_id,
            "completed": True
        })
        
        if completed_count == 1:
            # First tutorial completed - could award achievement here
            pass
    
    return {"success": True, "progress": progress}


@router.get("/user/progress", response_model=dict)
async def get_user_progress(user = Depends(get_current_user)):
    """Get user's tutorial progress"""
    user_id = str(user["_id"])
    
    progress = await db.tutorial_progress.find({"user_id": user_id}).to_list(100)
    
    completed = sum(1 for p in progress if p.get("completed"))
    total = len(TUTORIALS)
    
    return {
        "progress": {p["tutorial_id"]: p["progress"] for p in progress},
        "completed_count": completed,
        "total_count": total,
        "completion_percentage": round((completed / total * 100) if total > 0 else 0, 1)
    }
