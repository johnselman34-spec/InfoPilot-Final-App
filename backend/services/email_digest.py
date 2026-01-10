"""Weekly Email Digest Service for InfoPilot Explorer"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

# SendGrid configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@infopilot-explorer.com')

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, To
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid not installed - email digest disabled")


async def generate_weekly_digest_content(db, user: Dict[str, Any]) -> Dict[str, Any]:
    """Generate personalized weekly digest content for a user"""
    user_id = user["id"]
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    # Get user's new search results this week
    new_results = await db.search_results.count_documents({
        "user_id": user_id,
        "collated_at": {"$gte": week_ago}
    })
    
    # Get trending hashtags
    pipeline = [
        {"$match": {"hashtags": {"$exists": True, "$ne": []}}},
        {"$unwind": "$hashtags"},
        {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    trending = await db.search_results.aggregate(pipeline).to_list(5)
    
    # Get new public protocols
    new_protocols = await db.categories.count_documents({
        "is_public": True,
        "created_at": {"$gte": week_ago}
    })
    
    # Get new marketplace listings
    new_listings = await db.categories.count_documents({
        "for_sale": True,
        "created_at": {"$gte": week_ago}
    })
    
    # Get popular protocols (most copied this week)
    popular_pipeline = [
        {"$match": {"is_public": True, "copy_count": {"$gt": 0}}},
        {"$sort": {"copy_count": -1}},
        {"$limit": 3}
    ]
    popular_protocols = await db.categories.aggregate(popular_pipeline).to_list(3)
    
    # Get unread messages count
    unread_messages = await db.messages.count_documents({
        "recipient_id": user_id,
        "read": False
    })
    
    # Get friend requests
    friend_requests = await db.friendships.count_documents({
        "friend_id": user_id,
        "status": "pending"
    })
    
    return {
        "username": user["username"],
        "new_results": new_results,
        "trending_hashtags": [t["_id"] for t in trending],
        "new_protocols": new_protocols,
        "new_listings": new_listings,
        "popular_protocols": [{"name": p.get("name", "Unknown"), "copies": p.get("copy_count", 0)} for p in popular_protocols],
        "unread_messages": unread_messages,
        "friend_requests": friend_requests
    }


def create_digest_html(digest_data: Dict[str, Any]) -> str:
    """Create beautiful HTML email for weekly digest"""
    trending_html = ""
    if digest_data["trending_hashtags"]:
        trending_html = "".join([f'<span style="background: linear-gradient(135deg, #ec4899, #8b5cf6); color: white; padding: 4px 12px; border-radius: 20px; margin: 4px; display: inline-block; font-size: 14px;">{tag}</span>' for tag in digest_data["trending_hashtags"]])
    else:
        trending_html = '<span style="color: #9ca3af;">No trending hashtags this week</span>'
    
    popular_html = ""
    if digest_data["popular_protocols"]:
        popular_html = "".join([f'<div style="padding: 8px 0; border-bottom: 1px solid #374151;"><span style="color: #f472b6;">📁 {p["name"]}</span> <span style="color: #9ca3af; font-size: 12px;">({p["copies"]} copies)</span></div>' for p in digest_data["popular_protocols"]])
    else:
        popular_html = '<span style="color: #9ca3af;">No popular protocols this week</span>'
    
    notifications_html = ""
    if digest_data["unread_messages"] > 0:
        notifications_html += f'<div style="padding: 8px 12px; background: #1e3a5f; border-radius: 8px; margin: 4px 0;">💬 {digest_data["unread_messages"]} unread message(s)</div>'
    if digest_data["friend_requests"] > 0:
        notifications_html += f'<div style="padding: 8px 12px; background: #1e3a5f; border-radius: 8px; margin: 4px 0;">👥 {digest_data["friend_requests"]} friend request(s)</div>'
    if not notifications_html:
        notifications_html = '<div style="color: #9ca3af;">No new notifications</div>'
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background: linear-gradient(135deg, #0f0f23, #1a1a3e); font-family: 'Courier New', monospace;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <!-- Header -->
        <div style="text-align: center; padding: 30px 0; background: linear-gradient(135deg, #ec4899, #8b5cf6, #3b82f6); border-radius: 16px 16px 0 0;">
            <h1 style="margin: 0; color: white; font-size: 28px; letter-spacing: 2px;">✈️ INFOPILOT EXPLORER</h1>
            <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.8); font-size: 14px;">WEEKLY INTEL BRIEFING</p>
        </div>
        
        <!-- Main Content -->
        <div style="background: #1a1a2e; padding: 30px; border-radius: 0 0 16px 16px;">
            <h2 style="color: #f472b6; margin: 0 0 20px 0;">Hello, {digest_data["username"]}! 👋</h2>
            
            <p style="color: #a5b4fc; line-height: 1.6;">Here's your weekly intelligence report from InfoPilot Explorer. Stay informed, stay ahead!</p>
            
            <!-- Stats Grid -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 20px 0;">
                <div style="background: linear-gradient(135deg, #ec4899, #8b5cf6); padding: 20px; border-radius: 12px; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: white;">{digest_data["new_results"]}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 12px;">NEW RESULTS</div>
                </div>
                <div style="background: linear-gradient(135deg, #8b5cf6, #3b82f6); padding: 20px; border-radius: 12px; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: white;">{digest_data["new_protocols"]}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 12px;">NEW PROTOCOLS</div>
                </div>
            </div>
            
            <!-- Trending Hashtags -->
            <div style="background: #0f0f23; padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #374151;">
                <h3 style="color: #f472b6; margin: 0 0 12px 0;">🔥 TRENDING HASHTAGS</h3>
                <div>{trending_html}</div>
            </div>
            
            <!-- Popular Protocols -->
            <div style="background: #0f0f23; padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #374151;">
                <h3 style="color: #a78bfa; margin: 0 0 12px 0;">📁 POPULAR PROTOCOLS</h3>
                {popular_html}
            </div>
            
            <!-- Notifications -->
            <div style="background: #0f0f23; padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #374151;">
                <h3 style="color: #60a5fa; margin: 0 0 12px 0;">🔔 YOUR NOTIFICATIONS</h3>
                {notifications_html}
            </div>
            
            <!-- Marketplace Alert -->
            {f'<div style="background: linear-gradient(135deg, #f59e0b, #ef4444); padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center;"><h3 style="color: white; margin: 0;">🛒 {digest_data["new_listings"]} NEW MARKETPLACE LISTINGS!</h3><p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">Check out new protocols for sale</p></div>' if digest_data["new_listings"] > 0 else ''}
            
            <!-- CTA Button -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://explorer-app-3.preview.emergentagent.com/" style="display: inline-block; background: linear-gradient(135deg, #ec4899, #8b5cf6); color: white; text-decoration: none; padding: 16px 40px; border-radius: 30px; font-weight: bold; letter-spacing: 1px;">LAUNCH INFOPILOT →</a>
            </div>
            
            <!-- Book Promo -->
            <div style="background: linear-gradient(135deg, #1e1e3f, #2d1b4e); padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #8b5cf6; text-align: center;">
                <p style="color: #f472b6; margin: 0 0 8px 0; font-size: 16px;">📚 FROM THE CREATOR</p>
                <h3 style="color: white; margin: 0;">LETTERS TO EVELYN</h3>
                <p style="color: #a5b4fc; font-size: 14px; margin: 8px 0;">A Supernatural Thriller Comedy • 19 Five-Star Reviews</p>
                <a href="https://a.co/d/atfpIds" style="display: inline-block; background: linear-gradient(135deg, #f59e0b, #ef4444); color: white; text-decoration: none; padding: 10px 24px; border-radius: 20px; font-size: 14px; margin-top: 8px;">GET ON AMAZON</a>
            </div>
            
            <!-- Footer -->
            <div style="text-align: center; padding-top: 20px; border-top: 1px solid #374151; margin-top: 20px;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">You're receiving this because you're subscribed to InfoPilot Explorer weekly updates.</p>
                <p style="color: #6b7280; font-size: 12px; margin: 8px 0 0 0;">© 2026 InfoPilot Explorer • Tactical Research v2.0</p>
            </div>
        </div>
    </div>
</body>
</html>
'''
    return html


async def send_weekly_digest(db, user_email: str, digest_html: str) -> bool:
    """Send weekly digest email via SendGrid"""
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        logger.warning(f"SendGrid not configured - would send digest to {user_email}")
        return False
    
    try:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=user_email,
            subject="🚀 Your Weekly InfoPilot Intel Briefing",
            html_content=digest_html
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Weekly digest sent to {user_email}: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send weekly digest to {user_email}: {str(e)}")
        return False


async def process_weekly_digests(db) -> Dict[str, Any]:
    """Process and send weekly digests to all subscribed users"""
    # Get all users who have digest enabled (default: all users)
    users = await db.users.find(
        {"digest_enabled": {"$ne": False}},  # Include users without the field
        {"_id": 0, "id": 1, "username": 1, "email": 1}
    ).to_list(None)
    
    sent = 0
    failed = 0
    skipped = 0
    
    for user in users:
        try:
            # Generate digest content
            digest_data = await generate_weekly_digest_content(db, user)
            
            # Skip if no activity
            if (digest_data["new_results"] == 0 and 
                digest_data["new_protocols"] == 0 and 
                digest_data["unread_messages"] == 0):
                skipped += 1
                continue
            
            # Create and send email
            html = create_digest_html(digest_data)
            success = await send_weekly_digest(db, user["email"], html)
            
            if success:
                sent += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Error processing digest for {user.get('email', 'unknown')}: {str(e)}")
            failed += 1
    
    return {
        "total_users": len(users),
        "sent": sent,
        "failed": failed,
        "skipped": skipped
    }
