"""
InfoPilot Explorer - Newsletter Routes
AI-generated funny marketing newsletters using GPT-5.2
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
import logging

from config import db, logger
from routes.auth import get_current_user
from services.ai_service import AIService
from services.email_service import EmailService

router = APIRouter(tags=["Newsletter"])


# ==================== SUBSCRIBER MANAGEMENT ====================

@router.get("/newsletter/subscribers", response_model=dict)
async def get_subscribers(user = Depends(get_current_user)):
    """Get newsletter subscribers (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    subscribers = await db.newsletter_subscribers.find({"active": True}).to_list(1000)
    
    return {
        "subscribers": [{
            "id": str(s["_id"]),
            "email": s["email"],
            "subscribed_at": s.get("subscribed_at", datetime.now(timezone.utc)).isoformat(),
            "preferences": s.get("preferences", {})
        } for s in subscribers],
        "total": len(subscribers)
    }


@router.post("/newsletter/subscribe", response_model=dict)
async def subscribe(email: str, user = Depends(get_current_user)):
    """Subscribe to newsletter"""
    # Check if already subscribed
    existing = await db.newsletter_subscribers.find_one({"email": email.lower()})
    
    if existing:
        if existing.get("active"):
            return {"success": True, "message": "Already subscribed"}
        else:
            # Reactivate
            await db.newsletter_subscribers.update_one(
                {"_id": existing["_id"]},
                {"$set": {"active": True, "resubscribed_at": datetime.now(timezone.utc)}}
            )
            return {"success": True, "message": "Subscription reactivated"}
    
    # Create new subscription
    await db.newsletter_subscribers.insert_one({
        "email": email.lower(),
        "user_id": str(user["_id"]),
        "active": True,
        "subscribed_at": datetime.now(timezone.utc),
        "preferences": {
            "weekly_digest": True,
            "special_offers": True,
            "book_updates": True
        }
    })
    
    return {"success": True, "message": "Subscribed successfully"}


@router.post("/newsletter/unsubscribe", response_model=dict)
async def unsubscribe(email: str):
    """Unsubscribe from newsletter"""
    result = await db.newsletter_subscribers.update_one(
        {"email": email.lower()},
        {"$set": {"active": False, "unsubscribed_at": datetime.now(timezone.utc)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {"success": True, "message": "Unsubscribed successfully"}


# ==================== NEWSLETTER GENERATION ====================

@router.post("/newsletter/generate", response_model=dict)
async def generate_newsletter(
    topic: str = "weekly update",
    user = Depends(get_current_user)
):
    """Generate AI-powered newsletter content (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Gather stats for context
    total_users = await db.users.count_documents({})
    total_protocols = await db.marketplace_protocols.count_documents({})
    
    # Get top seller
    pipeline = [
        {"$group": {"_id": "$seller_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    top_seller_result = await db.marketplace_purchases.aggregate(pipeline).to_list(1)
    top_seller_name = "Our amazing community"
    if top_seller_result:
        seller = await db.users.find_one({"_id": ObjectId(top_seller_result[0]["_id"])})
        if seller:
            top_seller_name = seller.get("username", "A mystery genius")
    
    context = {
        "total_users": total_users,
        "new_protocols": total_protocols,
        "top_seller": top_seller_name,
        "book_sales": "trending upward 📈"
    }
    
    # Generate content using AI
    content = await AIService.generate_newsletter_content(topic, context)
    
    # Save draft
    draft = {
        "topic": topic,
        "content": content,
        "status": "draft",
        "created_by": str(user["_id"]),
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.newsletter_drafts.insert_one(draft)
    
    return {
        "id": str(result.inserted_id),
        "content": content,
        "status": "draft"
    }


@router.get("/newsletter/drafts", response_model=dict)
async def get_drafts(user = Depends(get_current_user)):
    """Get newsletter drafts (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    drafts = await db.newsletter_drafts.find().sort("created_at", -1).limit(20).to_list(20)
    
    return {
        "drafts": [{
            "id": str(d["_id"]),
            "topic": d["topic"],
            "subject_line": d["content"].get("subject_line", "No subject"),
            "status": d["status"],
            "created_at": d.get("created_at", datetime.now(timezone.utc)).isoformat()
        } for d in drafts]
    }


@router.get("/newsletter/drafts/{draft_id}", response_model=dict)
async def get_draft(draft_id: str, user = Depends(get_current_user)):
    """Get a specific draft"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    draft = await db.newsletter_drafts.find_one({"_id": ObjectId(draft_id)})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return {
        "id": str(draft["_id"]),
        "topic": draft["topic"],
        "content": draft["content"],
        "status": draft["status"],
        "created_at": draft.get("created_at", datetime.now(timezone.utc)).isoformat()
    }


@router.put("/newsletter/drafts/{draft_id}", response_model=dict)
async def update_draft(
    draft_id: str,
    subject_line: Optional[str] = None,
    full_html: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Update a newsletter draft"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    draft = await db.newsletter_drafts.find_one({"_id": ObjectId(draft_id)})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    if subject_line:
        update_data["content.subject_line"] = subject_line
    if full_html:
        update_data["content.full_html"] = full_html
    
    await db.newsletter_drafts.update_one(
        {"_id": ObjectId(draft_id)},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Draft updated"}


# ==================== NEWSLETTER SENDING ====================

async def send_newsletter_background(draft_id: str, subscriber_emails: List[str]):
    """Background task to send newsletter to all subscribers"""
    try:
        draft = await db.newsletter_drafts.find_one({"_id": ObjectId(draft_id)})
        if not draft:
            logger.error(f"Draft {draft_id} not found for sending")
            return
        
        content = draft["content"]
        subject = content.get("subject_line", "InfoPilot Weekly Update")
        html_content = content.get("full_html", "")
        
        # Create campaign record
        campaign = {
            "draft_id": draft_id,
            "subject": subject,
            "total_recipients": len(subscriber_emails),
            "sent_count": 0,
            "failed_count": 0,
            "status": "sending",
            "started_at": datetime.now(timezone.utc)
        }
        campaign_result = await db.newsletter_campaigns.insert_one(campaign)
        campaign_id = str(campaign_result.inserted_id)
        
        sent_count = 0
        failed_count = 0
        
        for email in subscriber_emails:
            try:
                # Add unsubscribe link
                unsubscribe_link = f"https://infopilot-explorer.preview.emergentagent.com/unsubscribe?email={email}"
                html_with_footer = html_content + f"""
                <hr style="margin-top: 40px; border-color: #333;">
                <p style="color: #888; font-size: 12px; text-align: center;">
                    You're receiving this because you subscribed to InfoPilot Explorer updates.<br>
                    <a href="{unsubscribe_link}" style="color: #f472b6;">Unsubscribe</a> | 
                    Top Pilot Enterprises, Inc. | Brunswick, Maine
                </p>
                """
                
                await EmailService.send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_with_footer
                )
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send to {email}: {e}")
                failed_count += 1
        
        # Update campaign record
        await db.newsletter_campaigns.update_one(
            {"_id": ObjectId(campaign_id)},
            {
                "$set": {
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Update draft status
        await db.newsletter_drafts.update_one(
            {"_id": ObjectId(draft_id)},
            {"$set": {"status": "sent", "sent_at": datetime.now(timezone.utc)}}
        )
        
        logger.info(f"Newsletter campaign {campaign_id} completed: {sent_count} sent, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Newsletter sending failed: {e}")


@router.post("/newsletter/send/{draft_id}", response_model=dict)
async def send_newsletter(
    draft_id: str,
    background_tasks: BackgroundTasks,
    test_email: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Send newsletter to all subscribers or test email (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    draft = await db.newsletter_drafts.find_one({"_id": ObjectId(draft_id)})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if test_email:
        # Send test email only
        content = draft["content"]
        try:
            await EmailService.send_email(
                to_email=test_email,
                subject=f"[TEST] {content.get('subject_line', 'Newsletter')}",
                html_content=content.get("full_html", "")
            )
            return {"success": True, "message": f"Test sent to {test_email}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send: {e}")
    
    # Get all active subscribers
    subscribers = await db.newsletter_subscribers.find({"active": True}).to_list(10000)
    emails = [s["email"] for s in subscribers]
    
    if not emails:
        raise HTTPException(status_code=400, detail="No active subscribers")
    
    # Send in background
    background_tasks.add_task(send_newsletter_background, draft_id, emails)
    
    return {
        "success": True,
        "message": f"Newsletter queued for {len(emails)} subscribers",
        "recipient_count": len(emails)
    }


# ==================== CAMPAIGN HISTORY ====================

@router.get("/newsletter/campaigns", response_model=dict)
async def get_campaigns(user = Depends(get_current_user)):
    """Get newsletter campaign history (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    campaigns = await db.newsletter_campaigns.find().sort("started_at", -1).limit(50).to_list(50)
    
    return {
        "campaigns": [{
            "id": str(c["_id"]),
            "subject": c.get("subject", "Unknown"),
            "total_recipients": c.get("total_recipients", 0),
            "sent_count": c.get("sent_count", 0),
            "failed_count": c.get("failed_count", 0),
            "status": c.get("status", "unknown"),
            "started_at": c.get("started_at").isoformat() if c.get("started_at") else None,
            "completed_at": c.get("completed_at").isoformat() if c.get("completed_at") else None
        } for c in campaigns]
    }
