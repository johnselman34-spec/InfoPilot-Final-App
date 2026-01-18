"""
InfoPilot Explorer - Reports Routes
Personal reports with image upload
"""
from fastapi import APIRouter, HTTPException, Body, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

from utils.db import db, UPLOADS_DIR
from utils.auth import require_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), user: Dict = Depends(require_user)):
    """Upload an image and return its URL."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB allowed")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = UPLOADS_DIR / filename
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Return URL (relative path)
    image_url = f"/api/uploads/{filename}"
    
    return {"url": image_url, "filename": filename, "size": len(contents)}


@router.get("/uploads/{filename}")
async def get_uploaded_image(filename: str):
    """Serve uploaded images."""
    filepath = UPLOADS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    ext = filename.split(".")[-1].lower()
    content_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    content_type = content_types.get(ext, "image/jpeg")
    
    return StreamingResponse(open(filepath, "rb"), media_type=content_type)


@router.post("")
async def create_personal_report(
    title: str = Body(...),
    content: str = Body(...),
    images: List[str] = Body(default=[]),
    location: Optional[Dict] = Body(default=None),
    category_ids: List[str] = Body(default=[]),
    user: Dict = Depends(require_user)
):
    """Create a Personal Report (Organic)."""
    if len(images) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 images allowed")
    
    report = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "title": title,
        "content": content,
        "images": images[:3],
        "location": location,
        "category_ids": category_ids,
        "document_type": "Personal Report (Organic)",
        "reactions": {"like": 0, "love": 0, "funny": 0, "sad": 0, "caution": 0, "spam": 0, "best": 0},
        "comments": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.personal_reports.insert_one(report)
    return {k: v for k, v in report.items() if k != "_id"}


@router.get("")
async def get_personal_reports(user: Dict = Depends(require_user)):
    """Get user's personal reports."""
    reports = await db.personal_reports.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return {"reports": reports}


@router.put("/{report_id}")
async def update_personal_report(report_id: str, updates: Dict = Body(...), user: Dict = Depends(require_user)):
    """Update a personal report."""
    report = await db.personal_reports.find_one({"id": report_id, "user_id": user["id"]})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    allowed = ["title", "content", "images", "location", "category_ids"]
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if filtered:
        await db.personal_reports.update_one({"id": report_id}, {"$set": filtered})
    
    updated = await db.personal_reports.find_one({"id": report_id}, {"_id": 0})
    return updated


@router.delete("/{report_id}")
async def delete_personal_report(report_id: str, user: Dict = Depends(require_user)):
    """Delete a personal report."""
    result = await db.personal_reports.delete_one({"id": report_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted"}
