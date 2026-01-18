"""
InfoPilot Explorer - Misc Routes
Easter eggs, news, stats, legal pages
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
from typing import Dict
from datetime import datetime, timezone
import random
import uuid

from utils.db import db, UPLOADS_DIR
from utils.auth import require_user, get_current_user

router = APIRouter(tags=["Misc"])

# Easter Eggs - Funny content about stepmother
EASTER_EGGS = [
    {
        "id": "egg1",
        "joke": "My stepmother tried to vacuum the lawn... She said the grass looked 'dusty'! 🌱",
        "protocol_idea": "(vacuum or cleaning) & (lawn or grass or outdoor)",
        "pricing_suggestion": "$2.99 - People love gardening fails!",
        "map_tip": "Toggle between Personal and Worldwide views using the switch at the top!"
    },
    {
        "id": "egg2",
        "joke": "My stepmother put the TV remote in the refrigerator... She wanted to 'cool down' the argument! 📺❄️",
        "protocol_idea": "(remote or lost items) & (refrigerator or fridge or cold)",
        "pricing_suggestion": "$1.99 - Everyone loses remotes!",
        "map_tip": "Hover over dots on the map to see quick previews of search results!"
    },
    {
        "id": "egg3",
        "joke": "My stepmother asked why I was 'installing updates' on the garden hose. She saw me unwinding it! 🚿",
        "protocol_idea": "(technology or updates) & (garden or hose or outdoor) & (confusion)",
        "pricing_suggestion": "$3.49 - Tech humor is gold!",
        "map_tip": "Click on any dot to see the full search result with all details!"
    },
    {
        "id": "egg4",
        "joke": "She tried to take a screenshot of her sandwich. For the 'memories folder' she said! 🥪",
        "protocol_idea": "(screenshot or photo) & (food or sandwich or meal)",
        "pricing_suggestion": "$2.49 - Food photography protocols!",
        "map_tip": "Use the category filters on the left to show only specific types of results!"
    },
    {
        "id": "egg5",
        "joke": "My stepmother watered the artificial plants for a month. Said they were 'looking thirsty'! 🌺",
        "protocol_idea": "(artificial or fake) & (plants or flowers) & (watering or care)",
        "pricing_suggestion": "$1.49 - Home decor fails!",
        "map_tip": "Results with locations appear as colored dots based on their categories!"
    },
    {
        "id": "egg6",
        "joke": "She put sunscreen on the computer. Said the screen was 'too bright' for its own good! ☀️💻",
        "protocol_idea": "(sunscreen or protection) & (computer or screen or device)",
        "pricing_suggestion": "$2.99 - Tech protection tips!",
        "map_tip": "The map shows results from around the world - zoom out to see the big picture!"
    },
    {
        "id": "egg7",
        "joke": "My stepmother called tech support about her 'wireless' candles. They weren't lighting up! 🕯️",
        "protocol_idea": "(wireless or LED) & (candles or lighting) & (tech support)",
        "pricing_suggestion": "$3.99 - Smart home gone wrong!",
        "map_tip": "Personal view shows only YOUR results, Worldwide shows everyone's!"
    },
    {
        "id": "egg8",
        "joke": "She returned the 'broken' sundial because it 'only worked during the day'. Customer service was confused! ⏰",
        "protocol_idea": "(sundial or time) & (broken or returned) & (daytime)",
        "pricing_suggestion": "$1.99 - Time-telling tech!",
        "map_tip": "Click 'View Stats' on any result to see how many people found it useful!"
    }
]

# AI Headlines
AI_HEADLINES = [
    {"title": "AI Predicts Weather Patterns with 99.7% Accuracy", "category": "Science", "summary": "New machine learning model revolutionizes meteorology"},
    {"title": "Brunswick, Maine Hosts Annual Lobster Festival", "category": "Local", "summary": "Thousands gather for the 75th annual celebration"},
    {"title": "Tech Giants Report Record Quarter", "category": "Business", "summary": "Apple, Google, and Microsoft exceed expectations"},
    {"title": "New Study Links Coffee to Longevity", "category": "Health", "summary": "Researchers find 3 cups a day optimal"},
    {"title": "Mars Rover Discovers Ancient River Bed", "category": "Space", "summary": "NASA confirms water once flowed on Mars"},
    {"title": "Letters to Evelyn Becomes Bestseller", "category": "Books", "summary": "John Selman's supernatural thriller tops charts"},
    {"title": "Electric Vehicles Outsell Gas Cars in Europe", "category": "Auto", "summary": "Historic shift in automotive industry"},
    {"title": "New InfoPilot Feature Launches Today", "category": "Tech", "summary": "Enhanced search protocols available to all users"},
    {"title": "Climate Summit Reaches Historic Agreement", "category": "World", "summary": "195 nations commit to net-zero by 2050"},
    {"title": "Maestro Bistro Named Best Food Truck in Maine", "category": "Food", "summary": "German cuisine wins hearts in Brunswick"}
]


@router.get("/easter-eggs/random")
async def get_random_easter_egg():
    """Get a random Easter egg."""
    return {"egg": random.choice(EASTER_EGGS)}


@router.post("/laughter-points/catch")
async def catch_easter_egg(egg_id: str = Body(..., embed=True), user: Dict = Depends(require_user)):
    """Catch an Easter egg and earn laughter points."""
    points = random.randint(5, 25)
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$inc": {"laughter_points": points, "easter_eggs_caught": 1}}
    )
    
    return {
        "message": f"You caught the Easter Egg! +{points} Laughter Points! 🎉",
        "points_earned": points
    }


@router.get("/news/headlines")
async def get_headlines():
    """Get AI-curated news headlines."""
    return {"headlines": AI_HEADLINES}


@router.get("/stats")
async def get_stats(user: Dict = Depends(get_current_user)):
    """Get platform statistics."""
    total_users = await db.users.count_documents({})
    total_categories = await db.categories.count_documents({})
    total_results = await db.search_results.count_documents({})
    total_reports = await db.personal_reports.count_documents({})
    
    user_stats = {}
    if user:
        user_stats = {
            "my_categories": await db.categories.count_documents({"user_id": user["id"]}),
            "my_results": await db.search_results.count_documents({"user_id": user["id"]}),
            "my_reports": await db.personal_reports.count_documents({"user_id": user["id"]}),
            "laughter_points": user.get("laughter_points", 0),
            "easter_eggs_caught": user.get("easter_eggs_caught", 0)
        }
    
    return {
        "global": {
            "total_users": total_users,
            "total_categories": total_categories,
            "total_results": total_results,
            "total_reports": total_reports
        },
        "user": user_stats
    }


@router.get("/legal/user-agreement")
async def get_user_agreement():
    """Get user agreement text."""
    return {
        "title": "InfoPilot Explorer User Agreement",
        "content": """
FIRST IN FLIGHT WITH MONETIZATION OF SEARCHES!

Welcome to InfoPilot Explorer by Top Pilot Enterprises, Inc.

By using this service, you agree to:
1. Use the InfoJet 2.0 protocol system responsibly
2. Not sell misleading or fraudulent protocols
3. Respect other users' intellectual property
4. Pay the 15% platform fee on marketplace sales
5. Maintain a minimum $1.00 price for sold protocols (PayPal requirement)

The code and algorithms of InfoPilot Explorer are proprietary and may not be emulated, copied, or reverse-engineered.

"It's a Bear!" - Our commitment to powerful, dangerous-level search capabilities!

© 2024-2026 Top Pilot Enterprises, Inc. All Rights Reserved.
        """,
        "version": "1.0",
        "effective_date": "2024-01-01"
    }


@router.get("/legal/privacy")
async def get_privacy_policy():
    """Get privacy policy text."""
    return {
        "title": "Privacy Policy",
        "content": """
InfoPilot Explorer Privacy Policy

We collect:
- Account information (email, username)
- Search protocols and results
- Usage statistics

We do NOT sell your data to third parties.
We use PayPal for secure payment processing.

Contact: JJSpilot24@gmail.com
        """,
        "version": "1.0"
    }


# Serve uploaded images
@router.get("/uploads/{filename}")
async def serve_upload(filename: str):
    """Serve uploaded files."""
    filepath = UPLOADS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    ext = filename.split(".")[-1].lower()
    content_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    
    return StreamingResponse(open(filepath, "rb"), media_type=content_types.get(ext, "application/octet-stream"))
