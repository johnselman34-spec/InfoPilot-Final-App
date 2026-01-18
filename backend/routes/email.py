"""
InfoPilot Explorer - Email Routes
Newsletter and transactional email integration using Resend
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import resend

from utils.db import db
from utils.auth import get_current_user, require_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Resend configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

# Initialize Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
    logger.info("Resend API initialized")
else:
    logger.warning("RESEND_API_KEY not configured - emails will be mocked")


# Pydantic Models
class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    html_content: str


class NewsletterRequest(BaseModel):
    subject: str
    content: str  # HTML content
    target_audience: Optional[str] = "all"  # all, subscribers, premium


class NewsletterSubscription(BaseModel):
    email: EmailStr
    name: Optional[str] = None


# Email sending function
async def send_email(to_email: str, subject: str, html_content: str) -> Dict:
    """Send an email using Resend API."""
    if not RESEND_API_KEY:
        # Mock mode - log the email
        logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
        return {"status": "mocked", "message": "Email logged (no API key configured)", "to": to_email}
    
    params = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    
    try:
        # Run sync SDK in thread to keep FastAPI non-blocking
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {to_email}: {email.get('id')}")
        return {"status": "success", "email_id": email.get("id"), "to": to_email}
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


# Newsletter subscription endpoints
@router.post("/subscribe")
async def subscribe_to_newsletter(subscription: NewsletterSubscription):
    """Subscribe to InfoPilot newsletter."""
    # Check if already subscribed
    existing = await db.newsletter_subscribers.find_one({"email": subscription.email})
    if existing:
        return {"message": "Already subscribed!", "status": "exists"}
    
    # Add subscriber
    subscriber = {
        "email": subscription.email,
        "name": subscription.name,
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "source": "website"
    }
    await db.newsletter_subscribers.insert_one(subscriber)
    
    # Send welcome email
    welcome_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 30px; border-radius: 10px;">
            <h1 style="color: #fbbf24; margin: 0;">🚀 Welcome to InfoPilot Explorer!</h1>
            <p style="color: #e2e8f0; margin-top: 20px;">
                Hi {subscription.name or 'Explorer'},
            </p>
            <p style="color: #e2e8f0;">
                Thank you for subscribing to the InfoPilot newsletter! You'll now receive:
            </p>
            <ul style="color: #e2e8f0;">
                <li>🔍 Protocol tips and tricks</li>
                <li>📊 New feature announcements</li>
                <li>🎯 Search optimization guides</li>
                <li>🐻 Bear-sized updates!</li>
            </ul>
            <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">
                First in Flight with Monetization of Searches! 🦅
            </p>
        </div>
    </div>
    """
    
    try:
        await send_email(subscription.email, "Welcome to InfoPilot Explorer! 🚀", welcome_html)
    except Exception as e:
        logger.warning(f"Welcome email failed but subscription saved: {e}")
    
    return {"message": "Successfully subscribed!", "status": "subscribed"}


@router.delete("/unsubscribe")
async def unsubscribe_from_newsletter(email: EmailStr):
    """Unsubscribe from newsletter."""
    result = await db.newsletter_subscribers.update_one(
        {"email": email},
        {"$set": {"is_active": False, "unsubscribed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Email not found in subscribers")
    
    return {"message": "Successfully unsubscribed", "email": email}


@router.get("/subscribers")
async def get_subscribers(user: Dict = Depends(require_user)):
    """Get newsletter subscribers (admin only)."""
    # Simple admin check
    if user.get("email") != "admin@infopilot.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    subscribers = await db.newsletter_subscribers.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return {"subscribers": subscribers, "count": len(subscribers)}


@router.post("/send-newsletter")
async def send_newsletter(newsletter: NewsletterRequest, user: Dict = Depends(require_user)):
    """Send newsletter to subscribers (admin only)."""
    # Simple admin check
    if user.get("email") != "admin@infopilot.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get active subscribers
    query = {"is_active": True}
    subscribers = await db.newsletter_subscribers.find(query, {"_id": 0, "email": 1, "name": 1}).to_list(10000)
    
    if not subscribers:
        raise HTTPException(status_code=400, detail="No subscribers found")
    
    # Build newsletter HTML
    newsletter_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 30px; border-radius: 10px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #fbbf24; margin: 0;">🦅 InfoPilot Newsletter</h1>
                <p style="color: #94a3b8; font-size: 12px;">First in Flight with Monetization of Searches!</p>
            </div>
            <h2 style="color: #fbbf24;">{newsletter.subject}</h2>
            <div style="color: #e2e8f0; line-height: 1.6;">
                {newsletter.content}
            </div>
            <hr style="border: 1px solid #334155; margin: 30px 0;">
            <div style="text-align: center;">
                <a href="https://infopilotexplorer.com" style="background: #fbbf24; color: #0f172a; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                    Explore InfoPilot
                </a>
            </div>
            <p style="color: #64748b; font-size: 11px; text-align: center; margin-top: 30px;">
                © 2026 Top Pilot Enterprises, Inc. | Brunswick, Maine<br>
                <a href="{{{{unsubscribe_url}}}}" style="color: #64748b;">Unsubscribe</a>
            </p>
        </div>
    </div>
    """
    
    # Send emails (in production, use a queue like Celery)
    sent_count = 0
    failed_count = 0
    
    for subscriber in subscribers:
        try:
            await send_email(subscriber["email"], newsletter.subject, newsletter_html)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {subscriber['email']}: {e}")
            failed_count += 1
    
    # Log the newsletter send
    await db.newsletter_logs.insert_one({
        "subject": newsletter.subject,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "sent_count": sent_count,
        "failed_count": failed_count,
        "sent_by": user["id"]
    })
    
    return {
        "message": f"Newsletter sent to {sent_count} subscribers",
        "sent": sent_count,
        "failed": failed_count,
        "total_subscribers": len(subscribers)
    }


@router.post("/send-single")
async def send_single_email(request: EmailRequest, user: Dict = Depends(require_user)):
    """Send a single email (authenticated users)."""
    result = await send_email(request.recipient_email, request.subject, request.html_content)
    return result


# Test endpoint
@router.get("/test")
async def test_email_config():
    """Test email configuration status."""
    return {
        "configured": bool(RESEND_API_KEY),
        "sender_email": SENDER_EMAIL,
        "status": "ready" if RESEND_API_KEY else "mocked (no API key)"
    }
