"""
InfoPilot Explorer - Category Import/Export Routes
Enables users to export category structures and import on other accounts or share
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import List, Optional, Dict
from bson import ObjectId
import json
import io

from config import db, logger
from routes.auth import get_current_user

router = APIRouter(prefix="/category-transfer", tags=["Category Import/Export"])


# ==================== EXPORT ====================

@router.get("/export", response_model=dict)
async def export_categories(
    format: str = "json",
    include_private: bool = True,
    user = Depends(get_current_user)
):
    """
    Export user's categories as JSON or shareable format.
    Includes nested structure, protocols, and metadata.
    """
    user_id = str(user["_id"])
    
    # Build query
    query = {"user_id": user_id}
    if not include_private:
        query["is_public"] = True
    
    # Get all categories
    categories = await db.categories.find(query).to_list(1000)
    
    if not categories:
        return {
            "success": True,
            "message": "No categories to export",
            "data": {"categories": [], "metadata": {}}
        }
    
    # Build export structure
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exporter": {
            "username": user.get("username", "Unknown"),
            "user_id": user_id  # Useful for marketplace attribution
        },
        "metadata": {
            "total_categories": len(categories),
            "public_count": len([c for c in categories if c.get("is_public")]),
            "private_count": len([c for c in categories if not c.get("is_public")]),
            "max_depth": max((c.get("level", 0) for c in categories), default=0)
        },
        "categories": []
    }
    
    # Build category map for parent lookup
    cat_map = {str(c["_id"]): c for c in categories}
    
    # Process categories
    for cat in categories:
        parent_name = None
        if cat.get("parent_id") and cat["parent_id"] in cat_map:
            parent_name = cat_map[cat["parent_id"]].get("name")
        
        export_data["categories"].append({
            "id": str(cat["_id"]),
            "name": cat["name"],
            "protocol": cat.get("protocol", ""),
            "level": cat.get("level", 0),
            "parent_id": cat.get("parent_id"),
            "parent_name": parent_name,
            "is_public": cat.get("is_public", False),
            "price": cat.get("price", 0),
            "created_at": cat.get("created_at", datetime.now(timezone.utc)).isoformat() if cat.get("created_at") else None
        })
    
    if format == "download":
        # Return as downloadable JSON file
        content = json.dumps(export_data, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=infopilot_categories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )
    
    return {
        "success": True,
        "message": f"Exported {len(categories)} categories",
        "data": export_data
    }


@router.get("/export/download")
async def download_categories(
    include_private: bool = True,
    user = Depends(get_current_user)
):
    """Download categories as JSON file"""
    user_id = str(user["_id"])
    
    query = {"user_id": user_id}
    if not include_private:
        query["is_public"] = True
    
    categories = await db.categories.find(query).to_list(1000)
    
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exporter": user.get("username", "Unknown"),
        "categories": [{
            "name": c["name"],
            "protocol": c.get("protocol", ""),
            "level": c.get("level", 0),
            "parent_name": None,  # Will be resolved on import
            "is_public": c.get("is_public", False),
            "price": c.get("price", 0)
        } for c in categories]
    }
    
    content = json.dumps(export_data, indent=2)
    
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=infopilot_categories_{datetime.now().strftime('%Y%m%d')}.json"
        }
    )


# ==================== IMPORT ====================

@router.post("/import", response_model=dict)
async def import_categories(
    data: dict,
    merge_strategy: str = "skip",  # skip, replace, merge
    user = Depends(get_current_user)
):
    """
    Import categories from exported JSON.
    
    Merge strategies:
    - skip: Skip categories that already exist (by name)
    - replace: Replace existing categories with imported ones
    - merge: Create new categories with "(imported)" suffix if name exists
    """
    user_id = str(user["_id"])
    
    # Validate import data
    if "categories" not in data:
        raise HTTPException(status_code=400, detail="Invalid import format: 'categories' field required")
    
    import_cats = data.get("categories", [])
    
    if not import_cats:
        return {"success": True, "message": "No categories to import", "imported": 0}
    
    # Get existing categories
    existing = await db.categories.find({"user_id": user_id}).to_list(1000)
    existing_names = {c["name"].lower(): c for c in existing}
    
    # Track results
    imported = []
    skipped = []
    replaced = []
    errors = []
    
    # Build parent name -> id mapping for the new import
    parent_map = {}  # name -> new_id
    
    # Sort by level to import parents first
    import_cats.sort(key=lambda x: x.get("level", 0))
    
    for cat in import_cats:
        try:
            cat_name = cat.get("name", "").strip()
            if not cat_name:
                errors.append({"name": "(empty)", "error": "Category name required"})
                continue
            
            cat_name_lower = cat_name.lower()
            
            # Check if exists
            if cat_name_lower in existing_names:
                if merge_strategy == "skip":
                    skipped.append(cat_name)
                    # Still map for children
                    parent_map[cat_name] = str(existing_names[cat_name_lower]["_id"])
                    continue
                    
                elif merge_strategy == "replace":
                    # Update existing
                    existing_cat = existing_names[cat_name_lower]
                    await db.categories.update_one(
                        {"_id": existing_cat["_id"]},
                        {"$set": {
                            "protocol": cat.get("protocol", ""),
                            "is_public": cat.get("is_public", False),
                            "price": cat.get("price", 0),
                            "updated_at": datetime.now(timezone.utc)
                        }}
                    )
                    replaced.append(cat_name)
                    parent_map[cat_name] = str(existing_cat["_id"])
                    continue
                    
                elif merge_strategy == "merge":
                    # Create with suffix
                    cat_name = f"{cat_name} (imported)"
            
            # Resolve parent
            parent_id = None
            parent_name = cat.get("parent_name")
            if parent_name and parent_name in parent_map:
                parent_id = parent_map[parent_name]
            
            # Create new category
            new_cat = {
                "user_id": user_id,
                "name": cat_name,
                "protocol": cat.get("protocol", ""),
                "level": cat.get("level", 0),
                "parent_id": parent_id,
                "is_public": cat.get("is_public", False),
                "price": cat.get("price", 0),
                "created_at": datetime.now(timezone.utc),
                "imported_from": data.get("exporter", "unknown"),
                "imported_at": datetime.now(timezone.utc)
            }
            
            result = await db.categories.insert_one(new_cat)
            
            # Map for children
            original_name = cat.get("name", "").strip()
            parent_map[original_name] = str(result.inserted_id)
            parent_map[cat_name] = str(result.inserted_id)
            
            imported.append(cat_name)
            
        except Exception as e:
            errors.append({"name": cat.get("name", "unknown"), "error": str(e)})
    
    return {
        "success": True,
        "message": f"Import complete: {len(imported)} imported, {len(skipped)} skipped, {len(replaced)} replaced",
        "results": {
            "imported": imported,
            "skipped": skipped,
            "replaced": replaced,
            "errors": errors
        },
        "stats": {
            "total_processed": len(import_cats),
            "imported_count": len(imported),
            "skipped_count": len(skipped),
            "replaced_count": len(replaced),
            "error_count": len(errors)
        }
    }


@router.post("/import/file", response_model=dict)
async def import_categories_file(
    file: UploadFile = File(...),
    merge_strategy: str = "skip",
    user = Depends(get_current_user)
):
    """Import categories from uploaded JSON file"""
    
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")
    
    # Read and parse file
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Use the import function
    return await import_categories(data, merge_strategy, user)


# ==================== SHARE TO MARKETPLACE ====================

@router.post("/share-to-marketplace", response_model=dict)
async def share_categories_to_marketplace(
    data: dict,
    user = Depends(get_current_user)
):
    """
    Share selected categories to the marketplace as a bundle.
    Creates a new marketplace listing with the category bundle.
    """
    category_ids = data.get("category_ids", [])
    bundle_name = data.get("name", "Category Bundle")
    bundle_description = data.get("description", "")
    price = data.get("price", 0)
    
    if not category_ids:
        raise HTTPException(status_code=400, detail="No categories selected")
    
    user_id = str(user["_id"])
    
    # Get selected categories
    categories = await db.categories.find({
        "_id": {"$in": [ObjectId(cid) for cid in category_ids]},
        "user_id": user_id
    }).to_list(100)
    
    if not categories:
        raise HTTPException(status_code=404, detail="No valid categories found")
    
    # Build bundle data
    bundle_data = {
        "categories": [{
            "name": c["name"],
            "protocol": c.get("protocol", ""),
            "level": c.get("level", 0)
        } for c in categories]
    }
    
    # Create marketplace listing
    listing = {
        "name": bundle_name,
        "description": bundle_description or f"Bundle of {len(categories)} categories with protocols",
        "protocol": json.dumps(bundle_data),  # Store as JSON string
        "price": max(0, min(price, 99.99)),
        "category": "Category Bundle",
        "tags": ["bundle", "categories", "protocols"],
        "creator_id": user_id,
        "creator_name": user.get("username", user.get("callsign", "Anonymous")),
        "total_sales": 0,
        "total_revenue": 0,
        "creator_earnings": 0,
        "rating": 0,
        "review_count": 0,
        "preview_results": 3,
        "status": "active",
        "is_bundle": True,
        "bundle_category_count": len(categories),
        "is_free": price == 0,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.marketplace_protocols.insert_one(listing)
    
    return {
        "success": True,
        "message": "Category bundle listed on marketplace!",
        "listing_id": str(result.inserted_id),
        "name": bundle_name,
        "categories_included": len(categories),
        "price": price,
        "is_free": price == 0
    }


# ==================== TEMPLATES ====================

@router.get("/templates", response_model=dict)
async def get_category_templates():
    """Get pre-made category templates users can import"""
    templates = [
        {
            "id": "research",
            "name": "Research & Academia",
            "description": "Categories for academic research, papers, and educational content",
            "category_count": 5,
            "categories": [
                {"name": "PhD Research", "protocol": "(research or study or paper) & (PhD or doctoral or dissertation)", "level": 0},
                {"name": "Peer-Reviewed", "protocol": "(peer-reviewed or peer reviewed) & (journal or publication)", "level": 0},
                {"name": "Academic Papers", "protocol": "(academic or scholarly) & (paper or article or research)", "level": 0},
                {"name": "Educational", "protocol": "(educational or learning or teaching) & (material or resource or content)", "level": 0},
                {"name": "Scientific Studies", "protocol": "(scientific or science) & (study or research or findings)", "level": 0}
            ]
        },
        {
            "id": "news",
            "name": "News & Media",
            "description": "Categories for news tracking and media monitoring",
            "category_count": 4,
            "categories": [
                {"name": "Breaking News", "protocol": "(breaking or urgent or latest) & (news or update or report)", "level": 0},
                {"name": "Opinion Pieces", "protocol": "(opinion or editorial or commentary) & (article or piece or column)", "level": 0},
                {"name": "Investigative Reports", "protocol": "(investigative or investigation) & (report or journalism or exposé)", "level": 0},
                {"name": "Press Releases", "protocol": "(press release or announcement) & (official or company or organization)", "level": 0}
            ]
        },
        {
            "id": "business",
            "name": "Business & Finance",
            "description": "Categories for business intelligence and financial research",
            "category_count": 5,
            "categories": [
                {"name": "Market Analysis", "protocol": "(market or industry) & (analysis or report or trend)", "level": 0},
                {"name": "Company Reports", "protocol": "(company or corporate) & (report or filing or earnings)", "level": 0},
                {"name": "Investment Research", "protocol": "(investment or investing) & (research or analysis or opportunity)", "level": 0},
                {"name": "Economic Data", "protocol": "(economic or economy) & (data or statistics or indicators)", "level": 0},
                {"name": "Startup News", "protocol": "(startup or venture) & (funding or launch or news)", "level": 0}
            ]
        },
        {
            "id": "tech",
            "name": "Technology & Development",
            "description": "Categories for tech news, programming, and development",
            "category_count": 5,
            "categories": [
                {"name": "Programming Tutorials", "protocol": "(tutorial or guide or howto) & (programming or coding or development)", "level": 0},
                {"name": "Tech Reviews", "protocol": "(review or comparison or test) & (technology or gadget or device)", "level": 0},
                {"name": "AI & ML", "protocol": "(artificial intelligence or machine learning or AI or ML) & (research or application or model)", "level": 0},
                {"name": "Open Source", "protocol": "(open source or opensource) & (project or software or tool)", "level": 0},
                {"name": "Security Updates", "protocol": "(security or vulnerability or CVE) & (update or patch or advisory)", "level": 0}
            ]
        },
        {
            "id": "personal",
            "name": "Personal Reports",
            "description": "Categories for personal experiences and reviews",
            "category_count": 4,
            "categories": [
                {"name": "Personal Reviews", "protocol": "(my experience or personal review or i tried) & (review or opinion or thoughts)", "level": 0},
                {"name": "User Testimonials", "protocol": "(testimonial or customer review or user feedback) & (experience or result or outcome)", "level": 0},
                {"name": "Case Studies", "protocol": "(case study or success story) & (example or implementation or result)", "level": 0},
                {"name": "Community Reports", "protocol": "(community or forum or discussion) & (report or thread or post)", "level": 0}
            ]
        }
    ]
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/import-template/{template_id}", response_model=dict)
async def import_template(
    template_id: str,
    user = Depends(get_current_user)
):
    """Import a pre-made category template"""
    templates = {
        "research": [
            {"name": "PhD Research", "protocol": "(research or study or paper) & (PhD or doctoral or dissertation)", "level": 0},
            {"name": "Peer-Reviewed", "protocol": "(peer-reviewed or peer reviewed) & (journal or publication)", "level": 0},
            {"name": "Academic Papers", "protocol": "(academic or scholarly) & (paper or article or research)", "level": 0},
            {"name": "Educational", "protocol": "(educational or learning or teaching) & (material or resource or content)", "level": 0},
            {"name": "Scientific Studies", "protocol": "(scientific or science) & (study or research or findings)", "level": 0}
        ],
        "news": [
            {"name": "Breaking News", "protocol": "(breaking or urgent or latest) & (news or update or report)", "level": 0},
            {"name": "Opinion Pieces", "protocol": "(opinion or editorial or commentary) & (article or piece or column)", "level": 0},
            {"name": "Investigative Reports", "protocol": "(investigative or investigation) & (report or journalism or exposé)", "level": 0},
            {"name": "Press Releases", "protocol": "(press release or announcement) & (official or company or organization)", "level": 0}
        ],
        "business": [
            {"name": "Market Analysis", "protocol": "(market or industry) & (analysis or report or trend)", "level": 0},
            {"name": "Company Reports", "protocol": "(company or corporate) & (report or filing or earnings)", "level": 0},
            {"name": "Investment Research", "protocol": "(investment or investing) & (research or analysis or opportunity)", "level": 0},
            {"name": "Economic Data", "protocol": "(economic or economy) & (data or statistics or indicators)", "level": 0},
            {"name": "Startup News", "protocol": "(startup or venture) & (funding or launch or news)", "level": 0}
        ],
        "tech": [
            {"name": "Programming Tutorials", "protocol": "(tutorial or guide or howto) & (programming or coding or development)", "level": 0},
            {"name": "Tech Reviews", "protocol": "(review or comparison or test) & (technology or gadget or device)", "level": 0},
            {"name": "AI & ML", "protocol": "(artificial intelligence or machine learning or AI or ML) & (research or application or model)", "level": 0},
            {"name": "Open Source", "protocol": "(open source or opensource) & (project or software or tool)", "level": 0},
            {"name": "Security Updates", "protocol": "(security or vulnerability or CVE) & (update or patch or advisory)", "level": 0}
        ],
        "personal": [
            {"name": "Personal Reviews", "protocol": "(my experience or personal review or i tried) & (review or opinion or thoughts)", "level": 0},
            {"name": "User Testimonials", "protocol": "(testimonial or customer review or user feedback) & (experience or result or outcome)", "level": 0},
            {"name": "Case Studies", "protocol": "(case study or success story) & (example or implementation or result)", "level": 0},
            {"name": "Community Reports", "protocol": "(community or forum or discussion) & (report or thread or post)", "level": 0}
        ]
    }
    
    if template_id not in templates:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Import the template
    return await import_categories(
        {"categories": templates[template_id]},
        merge_strategy="skip",
        user=user
    )
