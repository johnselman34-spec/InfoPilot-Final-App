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
    
    # Get recent map locations from search results
    map_locations = await db.search_results.find(
        {
            "locations": {"$exists": True, "$ne": []},
            "collated_at": {"$gte": week_ago}
        },
        {"_id": 0, "title": 1, "locations": 1, "url": 1, "categories": 1}
    ).sort("collated_at", -1).limit(5).to_list(5)
    
    # Get subscription pricing from admin settings
    admin_settings = await db.admin_settings.find_one({"id": "admin_settings"})
    subscription_price = admin_settings.get("subscription_price", 0.75) if admin_settings else 0.75
    regular_price = admin_settings.get("regular_price", 4.62) if admin_settings else 4.62
    
    # Get featured research resources
    featured_resources = await db.research_resources.find(
        {"featured": True},
        {"_id": 0}
    ).limit(3).to_list(3)
    
    return {
        "username": user["username"],
        "email": user.get("email", ""),
        "new_results": new_results,
        "trending_hashtags": [t["_id"] for t in trending],
        "new_protocols": new_protocols,
        "new_listings": new_listings,
        "popular_protocols": [{"name": p.get("name", "Unknown"), "copies": p.get("copy_count", 0)} for p in popular_protocols],
        "unread_messages": unread_messages,
        "friend_requests": friend_requests,
        "map_locations": map_locations,
        "subscription_price": subscription_price,
        "regular_price": regular_price,
        "featured_resources": featured_resources,
        "is_paid": user.get("is_paid", False)
    }


def create_digest_html(digest_data: Dict[str, Any]) -> str:
    """Create beautiful HTML email for weekly digest with stunning visuals"""
    
    # Trending hashtags section
    trending_html = ""
    if digest_data["trending_hashtags"]:
        trending_html = "".join([
            f'<span style="background: linear-gradient(135deg, #ec4899, #8b5cf6); color: white; padding: 8px 16px; border-radius: 25px; margin: 4px; display: inline-block; font-size: 14px; font-weight: bold; box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4);">#{tag}</span>' 
            for tag in digest_data["trending_hashtags"]
        ])
    else:
        trending_html = '<span style="color: #9ca3af;">Explore new topics today!</span>'
    
    # Popular protocols section
    popular_html = ""
    if digest_data["popular_protocols"]:
        popular_html = "".join([
            f'''<div style="padding: 12px 16px; background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(236, 72, 153, 0.1)); border-left: 4px solid #ec4899; border-radius: 8px; margin: 8px 0;">
                <span style="color: #f472b6; font-weight: bold; font-size: 16px;">📁 {p["name"]}</span>
                <span style="color: #a78bfa; font-size: 14px; float: right;">🔥 {p["copies"]} copies</span>
            </div>''' 
            for p in digest_data["popular_protocols"]
        ])
    else:
        popular_html = '<div style="color: #9ca3af; text-align: center; padding: 20px;">Create your first protocol today!</div>'
    
    # Map locations section - STUNNING FEATURE HIGHLIGHT
    map_html = ""
    if digest_data.get("map_locations"):
        locations_list = ""
        for loc_data in digest_data["map_locations"][:3]:
            title = loc_data.get("title", "Discovery")[:50]
            locations = loc_data.get("locations", [])
            if locations:
                loc_name = locations[0].get("name", "Unknown Location")
                locations_list += f'''
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(59, 130, 246, 0.1); border-radius: 12px; margin: 8px 0; border: 1px solid rgba(59, 130, 246, 0.3);">
                    <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #3b82f6, #06b6d4); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0;">📍</div>
                    <div style="flex: 1;">
                        <div style="color: #60a5fa; font-weight: bold; font-size: 14px;">{loc_name}</div>
                        <div style="color: #94a3b8; font-size: 12px;">{title}...</div>
                    </div>
                </div>'''
        
        map_html = f'''
        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); border-radius: 16px; padding: 24px; margin: 24px 0; border: 2px solid #3b82f6; box-shadow: 0 0 30px rgba(59, 130, 246, 0.3);">
            <div style="text-align: center; margin-bottom: 16px;">
                <span style="font-size: 48px;">🗺️</span>
                <h3 style="color: #60a5fa; font-size: 22px; margin: 8px 0 4px 0; font-weight: bold;">GLOBAL RESEARCH HOTSPOTS</h3>
                <p style="color: #94a3b8; font-size: 14px; margin: 0;">Discovered by InfoPilot's Automated Search & Collate</p>
            </div>
            {locations_list}
            <div style="text-align: center; margin-top: 16px;">
                <a href="https://social-research.preview.emergentagent.com/global-database" style="display: inline-block; background: linear-gradient(135deg, #3b82f6, #06b6d4); color: white; text-decoration: none; padding: 12px 32px; border-radius: 25px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);">🌍 EXPLORE WORLD MAP →</a>
            </div>
        </div>'''
    
    # Notifications section
    notifications_html = ""
    if digest_data["unread_messages"] > 0 or digest_data["friend_requests"] > 0:
        if digest_data["unread_messages"] > 0:
            notifications_html += f'<div style="padding: 12px 16px; background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.1)); border-radius: 12px; margin: 8px 0; border-left: 4px solid #22c55e;">💬 <strong style="color: #22c55e;">{digest_data["unread_messages"]}</strong> <span style="color: #86efac;">unread message(s) waiting</span></div>'
        if digest_data["friend_requests"] > 0:
            notifications_html += f'<div style="padding: 12px 16px; background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(139, 92, 246, 0.1)); border-radius: 12px; margin: 8px 0; border-left: 4px solid #a855f7;">👥 <strong style="color: #a855f7;">{digest_data["friend_requests"]}</strong> <span style="color: #c4b5fd;">friend request(s) pending</span></div>'
    else:
        notifications_html = '<div style="color: #9ca3af; text-align: center; padding: 12px;">✨ All caught up!</div>'
    
    # SUBSCRIPTION SALES SECTION - Make it POP!
    subscription_html = ""
    if not digest_data.get("is_paid", False):
        price = digest_data.get("subscription_price", 0.75)
        regular = digest_data.get("regular_price", 4.62)
        savings = round(((regular - price) / regular) * 100)
        
        subscription_html = f'''
        <div style="background: linear-gradient(135deg, #f59e0b, #ef4444, #ec4899); padding: 4px; border-radius: 20px; margin: 24px 0; box-shadow: 0 0 40px rgba(239, 68, 68, 0.4);">
            <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border-radius: 16px; padding: 32px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 8px;">🚀⚡🎯</div>
                <h2 style="color: white; font-size: 28px; margin: 0 0 8px 0; text-shadow: 0 0 20px rgba(236, 72, 153, 0.5);">UNLOCK FULL POWER!</h2>
                <p style="color: #fbbf24; font-size: 18px; margin: 0 0 16px 0; font-weight: bold;">LIMITED TIME: {savings}% OFF!</p>
                
                <div style="display: inline-block; background: linear-gradient(135deg, #22c55e, #10b981); padding: 20px 40px; border-radius: 16px; margin: 16px 0;">
                    <div style="color: white; font-size: 14px; text-decoration: line-through; opacity: 0.7;">${regular:.2f}/year</div>
                    <div style="color: white; font-size: 42px; font-weight: bold; text-shadow: 0 4px 15px rgba(0,0,0,0.3);">${price:.2f}</div>
                    <div style="color: #bbf7d0; font-size: 14px;">PER YEAR</div>
                </div>
                
                <div style="color: #94a3b8; font-size: 14px; margin: 16px 0;">
                    ✅ Unlimited Search Results &nbsp;&nbsp; ✅ Priority Support<br>
                    ✅ Exclusive Protocols &nbsp;&nbsp; ✅ Advanced Features
                </div>
                
                <a href="https://social-research.preview.emergentagent.com/subscribe" style="display: inline-block; background: linear-gradient(135deg, #f59e0b, #ef4444); color: white; text-decoration: none; padding: 16px 48px; border-radius: 30px; font-weight: bold; font-size: 18px; margin-top: 16px; box-shadow: 0 8px 25px rgba(239, 68, 68, 0.5); text-transform: uppercase; letter-spacing: 1px;">🔓 SUBSCRIBE NOW →</a>
                
                <p style="color: #6b7280; font-size: 12px; margin-top: 16px;">💳 Secure PayPal payment • Cancel anytime</p>
            </div>
        </div>'''
    
    # BOOK PROMOTION SECTION - STUNNING!
    book_html = f'''
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81, #4c1d95); padding: 32px; border-radius: 20px; margin: 24px 0; border: 2px solid #8b5cf6; box-shadow: 0 0 50px rgba(139, 92, 246, 0.4); position: relative; overflow: hidden;">
        <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%);"></div>
        <div style="position: absolute; bottom: -50px; left: -50px; width: 200px; height: 200px; background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%);"></div>
        
        <table style="width: 100%; position: relative; z-index: 1;">
            <tr>
                <td style="width: 140px; vertical-align: top; padding-right: 24px;">
                    <div style="background: linear-gradient(135deg, #ec4899, #8b5cf6); padding: 4px; border-radius: 12px; box-shadow: 0 8px 30px rgba(236, 72, 153, 0.5);">
                        <img src="https://customer-assets.emergentagent.com/job_5fdf2820-b9a7-4458-b1a2-1b10e8aac7a0/artifacts/sz2m7z1e_ebook-1.jpg" alt="Letters to Evelyn" style="width: 132px; height: auto; border-radius: 8px; display: block;">
                    </div>
                </td>
                <td style="vertical-align: top;">
                    <div style="margin-bottom: 8px;">
                        <span style="background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #1a1a2e; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">📚 FROM THE CREATOR</span>
                    </div>
                    <h2 style="color: white; font-size: 26px; margin: 8px 0; font-weight: bold; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">LETTERS TO EVELYN</h2>
                    <p style="color: #c4b5fd; font-size: 14px; margin: 4px 0;">By John Selman</p>
                    
                    <div style="margin: 12px 0;">
                        <span style="color: #fbbf24; font-size: 20px;">★★★★★</span>
                        <span style="color: #fbbf24; font-size: 14px; margin-left: 8px; font-weight: bold;">19 Five-Star Reviews</span>
                    </div>
                    
                    <p style="color: #e0e7ff; font-style: italic; font-size: 15px; line-height: 1.5; margin: 12px 0; border-left: 3px solid #8b5cf6; padding-left: 12px;">
                        "The Navy Taught Me to Fly Jets. The Universe Taught Me Everything Else."
                    </p>
                    
                    <p style="color: #a5b4fc; font-size: 13px; margin: 8px 0;">
                        🎭 A True Supernatural Thriller Comedy<br>
                        📖 13 Years of Cosmic Chaos
                    </p>
                    
                    <div style="margin-top: 16px;">
                        <span style="background: linear-gradient(135deg, #22c55e, #10b981); color: white; padding: 8px 20px; border-radius: 8px; font-size: 24px; font-weight: bold; display: inline-block; box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);">$2.99</span>
                    </div>
                    
                    <div style="margin-top: 16px;">
                        <a href="https://a.co/d/atfpIds" style="display: inline-block; background: linear-gradient(135deg, #f59e0b, #ef4444); color: white; text-decoration: none; padding: 14px 32px; border-radius: 25px; font-weight: bold; font-size: 16px; box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4); margin-right: 8px;">📱 GET ON AMAZON</a>
                    </div>
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(139, 92, 246, 0.3);">
            <p style="color: #c4b5fd; font-size: 14px; text-align: center; margin: 0; font-style: italic;">
                "A profound and unforgettable literary piece... poetic prose and introspective storytelling create an immersive reading experience."
                <br><span style="color: #a78bfa; font-size: 12px;">— Divine Zape, Readers' Favorite ⭐⭐⭐⭐⭐</span>
            </p>
        </div>
    </div>'''
    
    # MAIN EMAIL HTML
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InfoPilot Explorer Weekly Digest</title>
</head>
<body style="margin: 0; padding: 0; background: linear-gradient(135deg, #0f0f23, #1a1a3e); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <div style="max-width: 650px; margin: 0 auto; padding: 20px;">
        
        <!-- HEADER - STUNNING GRADIENT -->
        <div style="background: linear-gradient(135deg, #ec4899, #8b5cf6, #3b82f6, #06b6d4); padding: 4px; border-radius: 20px; box-shadow: 0 0 40px rgba(139, 92, 246, 0.4);">
            <div style="background: linear-gradient(135deg, #1a1a2e, #0f0f23); border-radius: 16px; padding: 40px; text-align: center;">
                <div style="font-size: 56px; margin-bottom: 12px;">✈️</div>
                <h1 style="margin: 0; color: white; font-size: 32px; letter-spacing: 3px; text-shadow: 0 0 30px rgba(236, 72, 153, 0.5);">INFOPILOT EXPLORER</h1>
                <p style="margin: 8px 0 0 0; color: #a78bfa; font-size: 16px; letter-spacing: 2px;">WEEKLY INTELLIGENCE BRIEFING</p>
                <div style="margin-top: 16px; padding: 8px 24px; background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(139, 92, 246, 0.2)); border-radius: 20px; display: inline-block;">
                    <span style="color: #f472b6; font-size: 14px;">📅 {datetime.now(timezone.utc).strftime("%B %d, %Y")}</span>
                </div>
            </div>
        </div>
        
        <!-- MAIN CONTENT -->
        <div style="background: linear-gradient(180deg, #1a1a2e, #0f172a); padding: 32px; border-radius: 20px; margin-top: 20px; border: 1px solid rgba(139, 92, 246, 0.3);">
            
            <!-- GREETING -->
            <h2 style="color: #f472b6; margin: 0 0 24px 0; font-size: 24px;">
                Hello, <span style="color: white;">{digest_data["username"]}</span>! 👋
            </h2>
            
            <p style="color: #a5b4fc; line-height: 1.7; font-size: 16px; margin: 0 0 24px 0;">
                Your weekly intelligence report is ready! Here's what's been happening across the InfoPilot network. Stay informed, stay ahead of the curve! 🚀
            </p>
            
            <!-- STATS GRID - VISUALLY STUNNING -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 24px 0;">
                <div style="background: linear-gradient(135deg, #ec4899, #f472b6); padding: 24px; border-radius: 16px; text-align: center; box-shadow: 0 8px 25px rgba(236, 72, 153, 0.3);">
                    <div style="font-size: 40px; font-weight: bold; color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">{digest_data["new_results"]}</div>
                    <div style="color: rgba(255,255,255,0.9); font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">New Results</div>
                </div>
                <div style="background: linear-gradient(135deg, #8b5cf6, #a78bfa); padding: 24px; border-radius: 16px; text-align: center; box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);">
                    <div style="font-size: 40px; font-weight: bold; color: white; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">{digest_data["new_protocols"]}</div>
                    <div style="color: rgba(255,255,255,0.9); font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">New Protocols</div>
                </div>
            </div>
            
            <!-- TRENDING HASHTAGS -->
            <div style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.1), rgba(139, 92, 246, 0.1)); padding: 24px; border-radius: 16px; margin: 24px 0; border: 1px solid rgba(236, 72, 153, 0.3);">
                <h3 style="color: #f472b6; margin: 0 0 16px 0; font-size: 18px;">🔥 TRENDING NOW</h3>
                <div style="line-height: 2.2;">{trending_html}</div>
            </div>
            
            <!-- MAP LOCATIONS SECTION -->
            {map_html}
            
            <!-- POPULAR PROTOCOLS -->
            <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1)); padding: 24px; border-radius: 16px; margin: 24px 0; border: 1px solid rgba(139, 92, 246, 0.3);">
                <h3 style="color: #a78bfa; margin: 0 0 16px 0; font-size: 18px;">📁 HOT PROTOCOLS</h3>
                {popular_html}
            </div>
            
            <!-- NOTIFICATIONS -->
            <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.1)); padding: 24px; border-radius: 16px; margin: 24px 0; border: 1px solid rgba(34, 197, 94, 0.3);">
                <h3 style="color: #22c55e; margin: 0 0 16px 0; font-size: 18px;">🔔 YOUR NOTIFICATIONS</h3>
                {notifications_html}
            </div>
            
            <!-- MARKETPLACE ALERT -->
            {f'<div style="background: linear-gradient(135deg, #f59e0b, #ef4444); padding: 24px; border-radius: 16px; margin: 24px 0; text-align: center; box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);"><h3 style="color: white; margin: 0; font-size: 20px;">🛒 {digest_data["new_listings"]} NEW MARKETPLACE LISTINGS!</h3><p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">Discover new protocols for sale from top contributors</p></div>' if digest_data["new_listings"] > 0 else ''}
            
            <!-- CTA BUTTON -->
            <div style="text-align: center; margin: 32px 0;">
                <a href="https://social-research.preview.emergentagent.com/" style="display: inline-block; background: linear-gradient(135deg, #ec4899, #8b5cf6); color: white; text-decoration: none; padding: 18px 48px; border-radius: 30px; font-weight: bold; letter-spacing: 1px; font-size: 16px; box-shadow: 0 8px 25px rgba(236, 72, 153, 0.4); text-transform: uppercase;">🚀 LAUNCH INFOPILOT →</a>
            </div>
            
            <!-- SUBSCRIPTION SALES -->
            {subscription_html}
            
            <!-- BOOK PROMOTION -->
            {book_html}
            
        </div>
        
        <!-- FOOTER -->
        <div style="text-align: center; padding: 32px 20px; margin-top: 20px;">
            <p style="color: #6b7280; font-size: 13px; margin: 0 0 8px 0;">
                You're receiving this because you're subscribed to InfoPilot Explorer weekly updates.
            </p>
            <p style="color: #6b7280; font-size: 12px; margin: 0;">
                © 2026 InfoPilot Explorer • Tactical Research v2.0
            </p>
            <p style="margin-top: 16px;">
                <a href="https://social-research.preview.emergentagent.com/settings" style="color: #8b5cf6; font-size: 12px; text-decoration: none;">Manage email preferences</a>
            </p>
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
            subject="🚀 Your Weekly InfoPilot Intel Briefing - New Discoveries Await!",
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
        {"_id": 0, "id": 1, "username": 1, "email": 1, "is_paid": 1}
    ).to_list(None)
    
    sent = 0
    failed = 0
    skipped = 0
    
    for user in users:
        try:
            # Generate digest content
            digest_data = await generate_weekly_digest_content(db, user)
            
            # Skip if no activity (but still include users without results to promote features)
            if (digest_data["new_results"] == 0 and 
                digest_data["new_protocols"] == 0 and 
                digest_data["unread_messages"] == 0 and
                digest_data["new_listings"] == 0):
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
