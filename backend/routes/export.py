"""
InfoPilot Explorer - User Data Export Routes
Export user data as JSON or CSV
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Optional
from bson import ObjectId
import json
import csv
import io

from config import db, logger

router = APIRouter(prefix="/export", tags=["Data Export"])
security = HTTPBearer(auto_error=False)


async def get_user_from_token(token: str):
    """Validate token and return user"""
    if not token:
        return None
    
    session = await db.sessions.find_one({"token": token})
    if not session:
        return None
    
    if session.get("expires_at") and session["expires_at"] < datetime.utcnow():
        return None
    
    user = await db.users.find_one({"_id": ObjectId(session["user_id"])})
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user


@router.get("/summary")
async def get_export_summary(user = Depends(get_current_user)):
    """Get summary of exportable data"""
    user_id = str(user["_id"])
    
    # Count all exportable data
    categories_count = await db.categories.count_documents({"user_id": user_id})
    search_results_count = await db.search_results.count_documents({"user_id": user_id})
    protocol_templates_count = await db.protocol_templates.count_documents({"user_id": user_id})
    marketplace_purchases_count = await db.marketplace_purchases.count_documents({"user_id": user_id})
    marketplace_protocols_count = await db.marketplace_protocols.count_documents({"creator_id": user_id})
    friendships_count = await db.friendships.count_documents({
        "$or": [{"user_id": user_id}, {"friend_id": user_id}],
        "status": "accepted"
    })
    messages_count = await db.messages.count_documents({
        "$or": [{"sender_id": user_id}, {"recipient_id": user_id}]
    })
    group_memberships = await db.groups.count_documents({"members": user_id})
    gamification = await db.gamification.find_one({"user_id": user_id})
    
    return {
        "summary": {
            "categories": categories_count,
            "search_results": search_results_count,
            "protocol_templates": protocol_templates_count,
            "marketplace_purchases": marketplace_purchases_count,
            "marketplace_listings": marketplace_protocols_count,
            "friends": friendships_count,
            "messages": messages_count,
            "groups": group_memberships,
            "xp": gamification.get("xp", 0) if gamification else 0,
            "badges": len(gamification.get("badges", [])) if gamification else 0
        },
        "export_formats": ["json", "csv"],
        "available_exports": [
            "all",
            "profile",
            "categories",
            "search_results",
            "protocols",
            "social",
            "gamification"
        ]
    }


@router.get("/all")
async def export_all_data(
    format: str = "json",
    user = Depends(get_current_user)
):
    """Export all user data as JSON or CSV"""
    user_id = str(user["_id"])
    
    # Gather all data
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "user": {
            "id": user_id,
            "email": user.get("email", ""),
            "username": user.get("username", ""),
            "callsign": user.get("callsign", ""),
            "created_at": user.get("created_at", datetime.utcnow()).isoformat()
        },
        "categories": [],
        "search_results": [],
        "protocol_templates": [],
        "marketplace": {
            "purchases": [],
            "listings": []
        },
        "social": {
            "friends": [],
            "groups": []
        },
        "gamification": {}
    }
    
    # Categories
    categories = await db.categories.find({"user_id": user_id}).to_list(1000)
    export_data["categories"] = [{
        "id": str(c["_id"]),
        "name": c["name"],
        "protocol": c["protocol"],
        "is_public": c.get("is_public", False),
        "created_at": c.get("created_at", datetime.utcnow()).isoformat()
    } for c in categories]
    
    # Search Results
    search_results = await db.search_results.find({"user_id": user_id}).to_list(5000)
    export_data["search_results"] = [{
        "id": str(r["_id"]),
        "url": r.get("url", ""),
        "title": r.get("title", ""),
        "snippet": r.get("snippet", ""),
        "article_type": r.get("article_type", "Unknown"),
        "match_score": r.get("match_score", 0),
        "created_at": r.get("created_at", datetime.utcnow()).isoformat()
    } for r in search_results]
    
    # Protocol Templates
    templates = await db.protocol_templates.find({"user_id": user_id}).to_list(500)
    export_data["protocol_templates"] = [{
        "id": str(t["_id"]),
        "name": t["name"],
        "description": t.get("description", ""),
        "protocol": t["protocol"],
        "category": t.get("category", "General"),
        "is_public": t.get("is_public", False),
        "use_count": t.get("use_count", 0)
    } for t in templates]
    
    # Marketplace Purchases
    purchases = await db.marketplace_purchases.find({"user_id": user_id}).to_list(500)
    for p in purchases:
        protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(p["protocol_id"])})
        export_data["marketplace"]["purchases"].append({
            "protocol_name": protocol["name"] if protocol else "Unknown",
            "protocol_string": protocol["protocol"] if protocol else "",
            "price_paid": p.get("price", 0),
            "purchased_at": p.get("created_at", datetime.utcnow()).isoformat()
        })
    
    # Marketplace Listings
    listings = await db.marketplace_protocols.find({"creator_id": user_id}).to_list(500)
    export_data["marketplace"]["listings"] = [{
        "id": str(l["_id"]),
        "name": l["name"],
        "description": l["description"],
        "protocol": l["protocol"],
        "price": listing["price"],
        "total_sales": listing.get("total_sales", 0),
        "total_earnings": listing.get("creator_earnings", 0),
        "rating": listing.get("rating", 0)
    } for listing in listings]
    
    # Friends
    friendships = await db.friendships.find({
        "$or": [{"user_id": user_id}, {"friend_id": user_id}],
        "status": "accepted"
    }).to_list(500)
    for f in friendships:
        friend_id = f["friend_id"] if f["user_id"] == user_id else f["user_id"]
        friend = await db.users.find_one({"_id": ObjectId(friend_id)})
        if friend:
            export_data["social"]["friends"].append({
                "username": friend.get("username", "Unknown"),
                "since": f.get("accepted_at", f.get("created_at", datetime.utcnow())).isoformat()
            })
    
    # Groups
    groups = await db.groups.find({"members": user_id}).to_list(100)
    export_data["social"]["groups"] = [{
        "name": g["name"],
        "description": g.get("description", ""),
        "is_creator": g.get("created_by") == user_id
    } for g in groups]
    
    # Gamification
    gamification = await db.gamification.find_one({"user_id": user_id})
    if gamification:
        export_data["gamification"] = {
            "xp": gamification.get("xp", 0),
            "badges": gamification.get("badges", []),
            "login_streak": gamification.get("login_streak", 0)
        }
    
    if format == "csv":
        return await export_as_csv(export_data, user.get("username", "user"))
    else:
        return await export_as_json(export_data, user.get("username", "user"))


async def export_as_json(data: dict, username: str):
    """Export data as JSON file"""
    json_str = json.dumps(data, indent=2, default=str)
    
    return StreamingResponse(
        io.BytesIO(json_str.encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=infopilot_export_{username}_{datetime.utcnow().strftime('%Y%m%d')}.json"
        }
    )


async def export_as_csv(data: dict, username: str):
    """Export data as CSV files in a structured format"""
    output = io.StringIO()
    
    # Write header
    output.write(f"# InfoPilot Data Export for {username}\n")
    output.write(f"# Exported: {data['export_date']}\n\n")
    
    # User info
    output.write("## USER INFO\n")
    output.write(f"Username,{data['user']['username']}\n")
    output.write(f"Email,{data['user']['email']}\n")
    output.write(f"Callsign,{data['user']['callsign']}\n\n")
    
    # Categories
    if data['categories']:
        output.write("## CATEGORIES\n")
        output.write("Name,Protocol,Is Public,Created At\n")
        for cat in data['categories']:
            output.write(f"\"{cat['name']}\",\"{cat['protocol']}\",{cat['is_public']},{cat['created_at']}\n")
        output.write("\n")
    
    # Search Results
    if data['search_results']:
        output.write("## SEARCH RESULTS\n")
        output.write("Title,URL,Article Type,Match Score,Created At\n")
        for r in data['search_results'][:500]:  # Limit for CSV
            title = r['title'].replace('"', '""')
            output.write(f"\"{title}\",\"{r['url']}\",{r['article_type']},{r['match_score']},{r['created_at']}\n")
        output.write("\n")
    
    # Protocol Templates
    if data['protocol_templates']:
        output.write("## PROTOCOL TEMPLATES\n")
        output.write("Name,Protocol,Category,Use Count,Is Public\n")
        for t in data['protocol_templates']:
            name = t['name'].replace('"', '""')
            protocol = t['protocol'].replace('"', '""')
            output.write(f"\"{name}\",\"{protocol}\",{t['category']},{t['use_count']},{t['is_public']}\n")
        output.write("\n")
    
    # Marketplace
    if data['marketplace']['purchases']:
        output.write("## MARKETPLACE PURCHASES\n")
        output.write("Protocol Name,Price Paid,Purchased At\n")
        for p in data['marketplace']['purchases']:
            name = p['protocol_name'].replace('"', '""')
            output.write(f"\"{name}\",${p['price_paid']},{p['purchased_at']}\n")
        output.write("\n")
    
    if data['marketplace']['listings']:
        output.write("## MARKETPLACE LISTINGS\n")
        output.write("Name,Price,Total Sales,Total Earnings,Rating\n")
        for listing in data['marketplace']['listings']:
            name = listing['name'].replace('"', '""')
            output.write(f"\"{name}\",${listing['price']},{listing['total_sales']},${listing['total_earnings']},{listing['rating']}\n")
        output.write("\n")
    
    # Gamification
    if data['gamification']:
        output.write("## GAMIFICATION\n")
        output.write(f"XP,{data['gamification'].get('xp', 0)}\n")
        output.write(f"Login Streak,{data['gamification'].get('login_streak', 0)}\n")
        output.write(f"Badges,{' | '.join(data['gamification'].get('badges', []))}\n")
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=infopilot_export_{username}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/categories")
async def export_categories(format: str = "json", user = Depends(get_current_user)):
    """Export only categories"""
    user_id = str(user["_id"])
    
    categories = await db.categories.find({"user_id": user_id}).to_list(1000)
    data = [{
        "name": c["name"],
        "protocol": c["protocol"],
        "is_public": c.get("is_public", False),
        "created_at": c.get("created_at", datetime.utcnow()).isoformat()
    } for c in categories]
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "protocol", "is_public", "created_at"])
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=infopilot_categories.csv"}
        )
    
    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=infopilot_categories.json"}
    )


@router.get("/search-results")
async def export_search_results(
    format: str = "json",
    limit: int = 1000,
    user = Depends(get_current_user)
):
    """Export search results"""
    user_id = str(user["_id"])
    
    results = await db.search_results.find({"user_id": user_id}).limit(limit).to_list(limit)
    data = [{
        "url": r.get("url", ""),
        "title": r.get("title", ""),
        "snippet": r.get("snippet", ""),
        "article_type": r.get("article_type", "Unknown"),
        "root_domain": r.get("root_domain", ""),
        "match_score": r.get("match_score", 0),
        "created_at": r.get("created_at", datetime.utcnow()).isoformat()
    } for r in results]
    
    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=infopilot_search_results.csv"}
        )
    
    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2, default=str).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=infopilot_search_results.json"}
    )


@router.get("/protocols")
async def export_protocols(format: str = "json", user = Depends(get_current_user)):
    """Export all protocols (templates and marketplace)"""
    user_id = str(user["_id"])
    
    # Templates
    templates = await db.protocol_templates.find({"user_id": user_id}).to_list(500)
    
    # Purchased protocols
    purchases = await db.marketplace_purchases.find({"user_id": user_id}).to_list(500)
    purchased_protocols = []
    for p in purchases:
        protocol = await db.marketplace_protocols.find_one({"_id": ObjectId(p["protocol_id"])})
        if protocol:
            purchased_protocols.append({
                "name": protocol["name"],
                "protocol": protocol["protocol"],
                "source": "purchased"
            })
    
    data = {
        "templates": [{
            "name": t["name"],
            "protocol": t["protocol"],
            "category": t.get("category", "General"),
            "source": "template"
        } for t in templates],
        "purchased": purchased_protocols
    }
    
    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=infopilot_protocols.json"}
    )
