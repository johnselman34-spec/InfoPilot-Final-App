"""
InfoPilot Explorer - Video Tutorials System
Provides text, image, and YouTube video-based guides and tutorials for all application features
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel

from config import db, logger
from routes.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/tutorials", tags=["Tutorials"])


class VideoUrlUpdate(BaseModel):
    video_url: Optional[str] = None
    video_id: Optional[str] = None  # YouTube video ID


# Tutorial data - text, image, and video-based tutorials
# video_url and video_id can be updated by admins
TUTORIALS = [
    {
        "id": "getting-started",
        "title": "Getting Started with InfoPilot Explorer",
        "description": "Learn the basics of InfoPilot Explorer and set up your account for success!",
        "content": """
## Welcome to InfoPilot Explorer! 🚀

InfoPilot Explorer is your ultimate search companion. Here's how to get started:

### Step 1: Create Your Account
1. Click the **Register** button
2. Enter your email and create a password
3. You'll be automatically connected with our admin as your first friend!

### Step 2: Explore Ultimate Search
1. Navigate to **Ultimate Search** from the sidebar
2. Enter your search query in the search box
3. Use the map to visualize results geographically

### Step 3: Create Your First Protocol
1. Click **+ Add Category** to create a new search category
2. Give it a name and write your protocol
3. Use operators like `(word1 or word2)` for flexible searches

### Pro Tips:
- 💡 Use the voice search feature for hands-free searching
- 📊 Check the Statistics page to see community trends
- 🏆 Earn achievements by using different features!
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
        "video_url": None,  # YouTube URL - to be added by admin
        "video_id": None,   # YouTube video ID - to be added by admin
        "duration": "5 min read",
        "category": "basics",
        "order": 1
    },
    {
        "id": "ultimate-search",
        "title": "Mastering Ultimate Search",
        "description": "Discover how to create powerful search protocols and get the best results.",
        "content": """
## Ultimate Search Mastery 🔍

Learn to harness the full power of InfoPilot's search engine!

### Protocol Syntax Guide

**Basic Operators:**
- `(word1 or word2)` - Match ANY word (OR logic)
- `(word1 or word2)+` - Match ALL words (INCLUDE ALL)
- `(word1 or word2)^` - EXCLUDE ALL words
- `&` - Combine groups (AND between groups)
- `"multi word phrase"` - Match exact phrase

### Example Protocol:
```
(george or bush or president) & (career or biography) & (pilot or aviation)^
```
This searches for George Bush's career, excluding pilot/aviation content.

### Map Integration
- Results automatically appear on the interactive map
- Click markers for detailed information
- Use filters to narrow by category

### Voice Search
- Click the 🎤 icon to search by voice
- Speak naturally - our AI understands context!
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800",
        "duration": "8 min read",
        "category": "search",
        "order": 2
    },
    {
        "id": "protocol-marketplace",
        "title": "Buying & Selling in the Marketplace",
        "description": "Turn your search expertise into cash! Learn how to list and sell protocols.",
        "content": """
## Protocol Marketplace 💰

Turn your search expertise into revenue!

### Selling Your Protocols

1. **Create a Protocol**
   - Go to Ultimate Search
   - Create a useful search protocol
   
2. **Set Your Price**
   - Edit the category
   - Set a price ($1-$99) or leave free
   
3. **Connect PayPal**
   - If selling, connect your PayPal account
   - You receive 90% of each sale!

### Buying Protocols

1. Browse the marketplace
2. Preview protocol descriptions
3. Pay What You Want for most protocols
4. Instantly add to your collection

### Tips for Sellers:
- 📝 Write detailed descriptions
- 🏷️ Price competitively
- ⭐ Build your reputation with quality protocols
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800",
        "duration": "7 min read",
        "category": "marketplace",
        "order": 3
    },
    {
        "id": "social-features",
        "title": "Social Hub: Friends, Groups & Pages",
        "description": "Connect with fellow researchers and build your InfoPilot community.",
        "content": """
## Social Hub Guide 👥

Build your research community!

### Friends
- Search for users by email
- Send friend requests
- Chat directly with friends

### Groups
- Create or join topic-based groups
- Share protocols with group members
- Create polls to engage your community

### Pages
- Create pages for organizations
- Build a following
- Post updates and announcements

### Polls Feature
- Create engaging polls in groups/pages
- Multiple choice options
- Set expiration times
- View real-time results

### Moderation
- Group admins can add moderators
- Moderators can manage posts
- Keep your community healthy!
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800",
        "duration": "6 min read",
        "category": "social",
        "order": 4
    },
    {
        "id": "direct-messaging",
        "title": "Direct Messaging & Real-time Chat",
        "description": "Stay connected with your network through instant messaging.",
        "content": """
## Direct Messaging 💬

Real-time communication made easy!

### Starting a Conversation
1. Go to Messages from the sidebar
2. Click **New Message**
3. Select a friend to chat with

### Features
- ✉️ Text messages
- 🖼️ Image sharing
- 🔔 Push notifications when offline
- ✅ Read receipts

### Group Chat
- Join the community chat room
- Discuss protocols with everyone
- Share tips and tricks

### Privacy
- Only friends can message you
- Block unwanted contacts
- Report inappropriate behavior
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1611606063065-ee7946f0787a?w=800",
        "duration": "4 min read",
        "category": "social",
        "order": 5
    },
    {
        "id": "achievements",
        "title": "Gamification & Achievements",
        "description": "Level up your profile and unlock exclusive badges and rewards!",
        "content": """
## Achievements System 🏆

Level up and earn rewards!

### How Points Work
- 🔍 Search: 5 points per search
- 📝 Create Protocol: 25 points
- 💰 Sell Protocol: 50 points
- 👥 Make a Friend: 15 points

### Levels
1. **Beginner** (0-100 pts)
2. **Explorer** (100-500 pts)
3. **Researcher** (500-1000 pts)
4. **Expert** (1000-2500 pts)
5. **Master** (2500+ pts)

### Badges
- 🌟 First Search
- 💎 Protocol Master
- 🤝 Social Butterfly
- 💰 Money Maker
- And many more!

### Sharing
- Share badges on Twitter
- Show off on Facebook
- Build your reputation!
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1567427017947-545c5f8d16ad?w=800",
        "duration": "5 min read",
        "category": "gamification",
        "order": 6
    },
    {
        "id": "voice-search",
        "title": "Voice Search with AI",
        "description": "Search hands-free using our advanced voice recognition powered by AI.",
        "content": """
## Voice Search 🎤

Hands-free searching powered by OpenAI Whisper!

### How to Use
1. Click the microphone icon 🎤
2. Speak your search query clearly
3. Wait for transcription
4. Review and search!

### Tips for Best Results
- Speak clearly and naturally
- Reduce background noise
- Use specific keywords
- Shorter queries work better

### Supported Languages
- English (primary)
- Spanish
- French
- German
- And more!

### Pro Tips
- Combine voice with protocol selection
- Use for quick searches
- Perfect for mobile use
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1589254065878-42c9da997008?w=800",
        "duration": "4 min read",
        "category": "search",
        "order": 7
    },
    {
        "id": "polls",
        "title": "Creating Polls for Engagement",
        "description": "Boost engagement in your groups and pages with interactive polls.",
        "content": """
## Polls Feature 📊

Engage your community with polls!

### Creating a Poll
1. Navigate to a Group or Page you manage
2. Click the **📊 Poll** button
3. Enter your question
4. Add 2-10 options
5. Set duration (optional)
6. Publish!

### Poll Options
- **Duration**: 1 hour to 7 days
- **Multiple Choice**: Allow multiple selections
- **Anonymous**: Hide voter identities

### Viewing Results
- Real-time vote counts
- Percentage breakdown
- Visual progress bars
- Total participation stats

### Use Cases
- Community decisions
- Feedback collection
- Topic preferences
- Fun engagement
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=800",
        "duration": "4 min read",
        "category": "social",
        "order": 8
    },
    {
        "id": "admin-features",
        "title": "Group & Page Administration",
        "description": "Learn how to manage moderators, admins, and member permissions.",
        "content": """
## Administration Guide ⚙️

Manage your communities effectively!

### Group Roles

**Owner** (You, the creator)
- Full control
- Add/remove admins
- Delete group

**Admin**
- Add/remove moderators
- Remove members
- Edit group settings
- Manage polls

**Moderator**
- Delete posts
- Mute members
- Approve posts
- Manage polls

### Adding Roles
1. Go to your Group/Page
2. Click **Manage Roles**
3. Select a member
4. Choose their role
5. They'll be notified!

### Best Practices
- Have at least 2 admins
- Set clear community guidelines
- Be fair with moderation
- Engage with your community
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=800",
        "duration": "6 min read",
        "category": "admin",
        "order": 9
    },
    {
        "id": "mobile-extension",
        "title": "Mobile App & Browser Extension",
        "description": "Access InfoPilot on the go with our mobile app and browser extension.",
        "content": """
## Access Anywhere 📱

Use InfoPilot everywhere!

### Browser Extension (InfoJet)
1. Install from Chrome Web Store
2. Click extension icon
3. Search instantly from any page
4. Select text → Right-click → Search

### Mobile App
1. Download from App Store/Play Store
2. Log in with your account
3. All features available!
4. Offline protocol access

### Extension Features
- 🔍 Quick search popup
- 📋 Access your protocols
- 🖱️ Context menu integration
- ⌨️ Keyboard shortcuts

### Mobile Features
- 📍 Location-based search
- 🎤 Voice search
- 📊 Full statistics
- 💬 Real-time messaging

### Sync
- All devices stay in sync
- Protocols available everywhere
- Settings preserved
        """,
        "video_url": None, "video_id": None, "image_url": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800",
        "duration": "5 min read",
        "category": "basics",
        "order": 10
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
    """Get all tutorials with any admin-configured videos"""
    tutorials = await get_tutorials_with_videos()
    
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


# ==================== ADMIN VIDEO MANAGEMENT ====================

@router.put("/admin/{tutorial_id}/video", response_model=dict)
async def update_tutorial_video(
    tutorial_id: str,
    video_data: VideoUrlUpdate,
    user = Depends(get_current_user)
):
    """Admin-only: Update a tutorial's video URL"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate tutorial exists
    tutorial = next((t for t in TUTORIALS if t["id"] == tutorial_id), None)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    # Extract video ID from YouTube URL if provided
    video_id = video_data.video_id
    video_url = video_data.video_url
    
    if video_url and not video_id:
        # Parse YouTube URL to get video ID
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                video_id = match.group(1)
                break
    
    # Store in database (override static data)
    await db.tutorial_videos.update_one(
        {"tutorial_id": tutorial_id},
        {
            "$set": {
                "video_url": video_url,
                "video_id": video_id,
                "updated_by": str(user["_id"]),
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    logger.info(f"Tutorial video updated: {tutorial_id} -> {video_id}")
    
    return {
        "success": True,
        "tutorial_id": tutorial_id,
        "video_url": video_url,
        "video_id": video_id
    }


@router.delete("/admin/{tutorial_id}/video", response_model=dict)
async def remove_tutorial_video(
    tutorial_id: str,
    user = Depends(get_current_user)
):
    """Admin-only: Remove a tutorial's video"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.tutorial_videos.delete_one({"tutorial_id": tutorial_id})
    
    return {"success": True, "message": "Video removed"}


@router.get("/admin/videos", response_model=dict)
async def get_all_tutorial_videos(user = Depends(get_current_user)):
    """Admin-only: Get all tutorial video configurations"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    videos = await db.tutorial_videos.find({}).to_list(100)
    
    return {
        "videos": [
            {
                "tutorial_id": v["tutorial_id"],
                "video_url": v.get("video_url"),
                "video_id": v.get("video_id"),
                "updated_at": v.get("updated_at").isoformat() if v.get("updated_at") else None
            }
            for v in videos
        ],
        "total_tutorials": len(TUTORIALS),
        "with_videos": len(videos)
    }


# Helper to merge static tutorials with DB video data
async def get_tutorials_with_videos():
    """Get tutorials merged with any admin-configured videos"""
    # Get video configurations from DB
    db_videos = await db.tutorial_videos.find({}).to_list(100)
    video_map = {v["tutorial_id"]: v for v in db_videos}
    
    # Merge with static tutorials
    result = []
    for t in TUTORIALS:
        tutorial = t.copy()
        if t["id"] in video_map:
            tutorial["video_url"] = video_map[t["id"]].get("video_url")
            tutorial["video_id"] = video_map[t["id"]].get("video_id")
        result.append(tutorial)
    
    return result
