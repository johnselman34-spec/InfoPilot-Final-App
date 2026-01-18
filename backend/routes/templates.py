"""
InfoPilot Explorer - Templates Routes
Protocol templates gallery
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

from utils.db import db
from utils.auth import require_user

router = APIRouter(prefix="/templates", tags=["Templates"])

# Official templates
OFFICIAL_TEMPLATES = [
    {
        "id": "civil-war-heroes",
        "name": "American Civil War Heroes",
        "description": "Find articles about American Civil War heroes and battles",
        "protocol": "(Civil War or Confederate or Union) & (hero or heroes or general or battle) & (American or USA or United States)",
        "category_suggestion": "History",
        "is_official": True,
        "usage_count": 1250,
        "rating": 4.8
    },
    {
        "id": "tech-innovations",
        "name": "Technology Innovations",
        "description": "Discover breakthrough technology and innovation news",
        "protocol": "(technology or tech or innovation) & (breakthrough or new or latest or cutting-edge) & (AI or software or hardware or digital)",
        "category_suggestion": "Technology",
        "is_official": True,
        "usage_count": 2340,
        "rating": 4.9
    },
    {
        "id": "medical-research",
        "name": "Medical Research Papers",
        "description": "Find peer-reviewed medical and health research",
        "protocol": "(medical or medicine or health) & (research or study or trial) & (peer-reviewed or journal or published)",
        "category_suggestion": "Science",
        "is_official": True,
        "usage_count": 1890,
        "rating": 4.7
    },
    {
        "id": "climate-science",
        "name": "Climate Science Updates",
        "description": "Stay updated on climate change and environmental science",
        "protocol": "(climate or environment or global warming) & (science or research or study) & (data or findings or report)",
        "category_suggestion": "Science",
        "is_official": True,
        "usage_count": 1456,
        "rating": 4.6
    },
    {
        "id": "business-news",
        "name": "Business & Finance News",
        "description": "Track business news and financial markets",
        "protocol": "(business or finance or market) & (news or report or update) & (stock or company or investment)",
        "category_suggestion": "Business",
        "is_official": True,
        "usage_count": 3210,
        "rating": 4.5
    },
    {
        "id": "space-exploration",
        "name": "Space Exploration News",
        "description": "Follow NASA, SpaceX, and space exploration updates",
        "protocol": "(space or NASA or SpaceX or rocket) & (launch or mission or exploration) & (Mars or Moon or satellite)",
        "category_suggestion": "Science",
        "is_official": True,
        "usage_count": 2100,
        "rating": 4.9
    },
    {
        "id": "sports-updates",
        "name": "Sports News & Scores",
        "description": "Get the latest sports news and game scores",
        "protocol": "(sports or game or match) & (score or win or championship) & (team or player or season)",
        "category_suggestion": "Sports",
        "is_official": True,
        "usage_count": 4500,
        "rating": 4.4
    },
    {
        "id": "education-resources",
        "name": "Education Resources",
        "description": "Find educational content and learning resources",
        "protocol": "(education or learning or tutorial) & (course or lesson or guide) & (free or online or resource)",
        "category_suggestion": "Education",
        "is_official": True,
        "usage_count": 1780,
        "rating": 4.6
    }
]


@router.get("")
async def get_protocol_templates():
    """Get protocol templates gallery."""
    # Get community templates
    community = await db.protocol_templates.find({"is_official": False}, {"_id": 0}).sort("usage_count", -1).limit(20).to_list(20)
    
    return {
        "official_templates": OFFICIAL_TEMPLATES,
        "community_templates": community
    }


@router.post("")
async def create_template(
    name: str = Body(...),
    description: str = Body(...),
    protocol: str = Body(...),
    category_suggestion: str = Body(...),
    price: Optional[float] = Body(None),
    user: Dict = Depends(require_user)
):
    """Create a new protocol template."""
    template = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "protocol": protocol,
        "category_suggestion": category_suggestion,
        "creator_id": user["id"],
        "creator_username": user["username"],
        "is_official": False,
        "usage_count": 0,
        "rating": 0.0,
        "price": price,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.protocol_templates.insert_one(template)
    return {k: v for k, v in template.items() if k != "_id"}


@router.post("/{template_id}/use")
async def use_template(template_id: str, user: Dict = Depends(require_user)):
    """Mark a template as used (increment counter)."""
    # Check official templates first
    for t in OFFICIAL_TEMPLATES:
        if t["id"] == template_id:
            return {"message": "Template used", "template": t}
    
    # Check community templates
    template = await db.protocol_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.protocol_templates.update_one({"id": template_id}, {"$inc": {"usage_count": 1}})
    return {"message": "Template used"}
