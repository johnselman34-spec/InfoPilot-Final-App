"""
InfoPilot Explorer - Tri-Weekly AI Newsletter Scheduler
Sends EXTREMELY FUNNY AI-generated newsletters at 5:46 AM, 9:05 AM, and 4:20 PM
Promotes InfoPilot features and "Letters to Evelyn" book
"""
import os
import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
triweekly_scheduler: Optional[AsyncIOScheduler] = None

# EXTREMELY FUNNY subject lines
HILARIOUS_SUBJECTS = [
    "🚀 Did your search engine ever make you LOL? Ours will!",
    "😂 Warning: This newsletter may cause spontaneous workplace laughter",
    "🎭 Plot Twist: Your Boring Day Just Got HILARIOUS",
    "💀 I'm legally dead from laughing at these search results",
    "🤣 Your daily dose of humor (prescribed by Dr. InfoPilot)",
    "🎪 Step right up! The greatest search show on Earth!",
    "🌟 Breaking News: InfoPilot Users Report 47% More Laughter",
    "📚 Letters to Evelyn made me snort coffee through my nose",
    "🔥 Hot Take: InfoPilot is basically stand-up comedy with search",
    "🎉 This newsletter is 100% organic, free-range, and hilarious",
    "🧙‍♂️ Abracadabra! Your boring inbox is now MAGICAL",
    "🦄 Rare sighting: An email worth opening (you're welcome)",
]

# Funny intros for different times of day
MORNING_INTROS = [  # 5:46 AM
    "☀️ Rise and shine, you beautiful search maestro! While everyone else is hitting snooze, YOU'RE getting the early bird's guide to InfoPilot greatness!",
    "🌅 Good morning, legend! The sun is barely up and you're already ahead of the curve. That's the InfoPilot spirit!",
    "☕ Coffee's brewing, birds are chirping, and your inbox just got 100% more awesome. You're welcome!",
]

MIDMORNING_INTROS = [  # 9:05 AM
    "📊 It's 9:05 AM somewhere, and that somewhere is wherever you're reading this! Time for your mid-morning dose of search excellence!",
    "🚀 The work day has begun, but who says productivity can't be HILARIOUS? Not us!",
    "💼 While your coworkers are on their third coffee break, you're leveling up your search game. Smart move!",
]

AFTERNOON_INTROS = [  # 4:20 PM
    "🌆 It's 4:20 PM - the universal time for... uh... appreciating great search technology! Yeah, that's it!",
    "😎 The afternoon slump? Never heard of her. InfoPilot keeps you energized and searching like a BOSS!",
    "🎯 Almost time to clock out, but first... let's talk about how to search smarter, not harder!",
]

# Book promo sections
LETTERS_TO_EVELYN_PROMOS = [
    """
    <div style="background:linear-gradient(135deg,#ff6b6b 0%,#feca57 100%);border-radius:16px;padding:25px;margin:25px 0;text-align:center;">
        <h2 style="color:#fff;margin:0 0 15px 0;font-size:24px;">📚 LETTERS TO EVELYN</h2>
        <p style="color:rgba(255,255,255,0.95);font-size:16px;margin:0 0 15px 0;">
            <em>"The comical side is exceedingly brilliant... imagination off the charts!"</em><br/>
            — Professional Review, Readers' Favorite ⭐⭐⭐⭐⭐
        </p>
        <p style="color:#fff;font-size:14px;margin:0 0 20px 0;">
            🛸 Supernatural encounters<br/>
            ✈️ Navy pilot adventures<br/>
            😂 Comedy that creeps into your mind
        </p>
        <a href="https://a.co/d/gsRLapf" style="display:inline-block;background:#fff;color:#ff6b6b;padding:12px 30px;border-radius:25px;text-decoration:none;font-weight:bold;font-size:16px;">
            📖 Get it for $2.99 on Amazon!
        </a>
        <p style="color:rgba(255,255,255,0.8);font-size:12px;margin:15px 0 0 0;">
            🎬 OPTIONED FOR FILM by Voyage Media!
        </p>
    </div>
    """,
    """
    <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:16px;padding:25px;margin:25px 0;">
        <h2 style="color:#fff;margin:0 0 10px 0;font-size:22px;">🌟 READER ALERT!</h2>
        <p style="color:rgba(255,255,255,0.95);font-size:18px;margin:0 0 15px 0;">
            <strong>"Letters to Evelyn"</strong> by John Selman
        </p>
        <p style="color:rgba(255,255,255,0.9);font-size:14px;margin:0 0 15px 0;">
            A supernatural thriller comedy memoir that's been called<br/>
            <em>"A true story that defies belief!"</em>
        </p>
        <div style="display:flex;justify-content:center;gap:15px;flex-wrap:wrap;margin:15px 0;">
            <span style="background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:20px;color:#fff;font-size:13px;">✈️ Navy Pilot Author</span>
            <span style="background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:20px;color:#fff;font-size:13px;">🛸 Extraterrestrial Encounters</span>
            <span style="background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:20px;color:#fff;font-size:13px;">😂 19 Five-Star Reviews</span>
        </div>
        <a href="https://a.co/d/gsRLapf" style="display:inline-block;background:#fff;color:#764ba2;padding:12px 30px;border-radius:25px;text-decoration:none;font-weight:bold;">
            🔥 Only $2.99 - Read Now!
        </a>
    </div>
    """,
    """
    <div style="background:#1a1025;border:2px solid #f472b6;border-radius:16px;padding:25px;margin:25px 0;text-align:center;">
        <p style="color:#f472b6;font-size:14px;margin:0 0 10px 0;text-transform:uppercase;letter-spacing:2px;">
            ✨ From the Desk of Top Pilot Enterprises ✨
        </p>
        <h2 style="color:#fff;margin:0 0 15px 0;font-size:24px;">Letters to Evelyn</h2>
        <p style="color:#a1a1aa;font-size:15px;margin:0 0 15px 0;">
            By World Record Aviation Holder <strong style="color:#f472b6;">John Selman</strong>
        </p>
        <p style="color:#c4b5fd;font-style:italic;font-size:16px;margin:0 0 20px 0;">
            "Comedy that creeps into your mind and causes abrupt laughter"
        </p>
        <div style="background:rgba(244,114,182,0.2);border-radius:10px;padding:15px;margin:15px 0;">
            <p style="color:#f472b6;margin:0;font-size:14px;">
                🎬 <strong>OPTIONED FOR FILM!</strong><br/>
                <span style="color:#a1a1aa;font-size:12px;">Hollywood couldn't resist this supernatural thriller comedy memoir</span>
            </p>
        </div>
        <a href="https://a.co/d/gsRLapf" style="display:inline-block;background:linear-gradient(135deg,#f472b6 0%,#7c3aed 100%);color:#fff;padding:15px 35px;border-radius:25px;text-decoration:none;font-weight:bold;font-size:16px;">
            📚 Grab Your Copy - $2.99
        </a>
    </div>
    """,
]

# InfoPilot feature highlights
INFOPILOT_FEATURES = [
    """
    <div style="background:rgba(124,58,237,0.1);border-radius:12px;padding:20px;margin:15px 0;border-left:4px solid #7c3aed;">
        <h3 style="color:#a78bfa;margin:0 0 10px 0;">🔍 Did You Know?</h3>
        <p style="color:#e2e8f0;margin:0;font-size:14px;">
            InfoPilot's <strong>InfoJet 2.0™</strong> protocol language lets you create custom search patterns that are 
            <em>literally smarter than regular searches</em>. It's like giving your browser a PhD! 🎓
        </p>
    </div>
    """,
    """
    <div style="background:rgba(16,185,129,0.1);border-radius:12px;padding:20px;margin:15px 0;border-left:4px solid #10b981;">
        <h3 style="color:#10b981;margin:0 0 10px 0;">💰 Protocol Marketplace Alert!</h3>
        <p style="color:#e2e8f0;margin:0;font-size:14px;">
            Creators are earning HUNDREDS of dollars selling their search protocols! 
            You keep <strong>90%</strong> of every sale. That's better than most app stores! 🚀
        </p>
    </div>
    """,
    """
    <div style="background:rgba(245,158,11,0.1);border-radius:12px;padding:20px;margin:15px 0;border-left:4px solid #f59e0b;">
        <h3 style="color:#f59e0b;margin:0 0 10px 0;">🗺️ Interactive Maps Feature!</h3>
        <p style="color:#e2e8f0;margin:0;font-size:14px;">
            See your search results plotted on a beautiful world map! It's like Google Maps 
            met a search engine and had a really smart baby. 🗺️✨
        </p>
    </div>
    """,
    """
    <div style="background:rgba(236,72,153,0.1);border-radius:12px;padding:20px;margin:15px 0;border-left:4px solid #ec4899;">
        <h3 style="color:#ec4899;margin:0 0 10px 0;">🎮 Gamification is LIVE!</h3>
        <p style="color:#e2e8f0;margin:0;font-size:14px;">
            Earn XP, unlock badges, and climb the leaderboards! Because who said 
            searching the internet couldn't feel like winning a video game? 🏆
        </p>
    </div>
    """,
]

# Funny closing lines
HILARIOUS_CLOSINGS = [
    "May your searches be fruitful and your protocols be profitable! 🎯",
    "Remember: Every time you use InfoPilot, a search engine fairy gets its wings! 🧚",
    "Stay searching, stay winning, stay HILARIOUS! 💪",
    "Go forth and conquer the internet (responsibly, of course)! 🚀",
    "Until next time: May the protocol be with you! ⭐",
    "Your friendly neighborhood search enthusiast, signing off! 🦸",
    "Keep being awesome. It suits you! 😎",
]


async def generate_triweekly_newsletter(time_slot: str = "morning") -> tuple[str, str]:
    """
    Generate an EXTREMELY FUNNY newsletter for the tri-weekly schedule
    
    Args:
        time_slot: 'morning' (5:46 AM), 'midmorning' (9:05 AM), or 'afternoon' (4:20 PM)
    """
    from config import db
    
    # Select appropriate intro based on time slot
    if time_slot == "morning":
        intro = random.choice(MORNING_INTROS)
        time_greeting = "🌅 Early Bird Edition"
    elif time_slot == "midmorning":
        intro = random.choice(MIDMORNING_INTROS)
        time_greeting = "☕ Mid-Morning Boost"
    else:  # afternoon
        intro = random.choice(AFTERNOON_INTROS)
        time_greeting = "🌆 Afternoon Delight"
    
    # Get some stats for personalization
    total_users = await db.users.count_documents({})
    total_protocols = await db.marketplace_protocols.count_documents({})
    total_sales = await db.marketplace_purchases.count_documents({})
    
    subject = random.choice(HILARIOUS_SUBJECTS)
    book_promo = random.choice(LETTERS_TO_EVELYN_PROMOS)
    feature = random.choice(INFOPILOT_FEATURES)
    closing = random.choice(HILARIOUS_CLOSINGS)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InfoPilot Newsletter</title>
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#1a1025;color:#e2e8f0;">
    <div style="max-width:650px;margin:0 auto;padding:20px;">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#7c3aed 0%,#ec4899 100%);border-radius:16px;padding:30px;text-align:center;margin-bottom:25px;">
            <p style="color:rgba(255,255,255,0.8);font-size:12px;margin:0 0 10px 0;text-transform:uppercase;letter-spacing:2px;">
                {time_greeting}
            </p>
            <h1 style="margin:0;color:white;font-size:28px;">🚀 InfoPilot Newsletter</h1>
            <p style="margin:10px 0 0 0;color:rgba(255,255,255,0.9);font-size:14px;">
                {datetime.now().strftime('%B %d, %Y')} • Tri-Weekly Humor Injection
            </p>
        </div>
        
        <!-- Intro -->
        <div style="background:rgba(124,58,237,0.15);border-left:4px solid #7c3aed;padding:20px;border-radius:0 12px 12px 0;margin-bottom:25px;">
            <p style="margin:0;font-size:16px;line-height:1.6;color:#c4b5fd;">
                {intro}
            </p>
        </div>
        
        <!-- Stats Banner -->
        <div style="background:rgba(30,20,50,0.8);border-radius:16px;padding:20px;margin-bottom:25px;border:1px solid rgba(124,58,237,0.3);">
            <h2 style="margin:0 0 15px 0;color:#f472b6;font-size:18px;text-align:center;">📊 InfoPilot by the Numbers</h2>
            <div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:15px;text-align:center;">
                <div>
                    <div style="font-size:24px;font-weight:bold;color:#10b981;">{total_users:,}</div>
                    <div style="font-size:12px;color:#a1a1aa;">Happy Searchers</div>
                </div>
                <div>
                    <div style="font-size:24px;font-weight:bold;color:#f472b6;">{total_protocols:,}</div>
                    <div style="font-size:12px;color:#a1a1aa;">Protocols Created</div>
                </div>
                <div>
                    <div style="font-size:24px;font-weight:bold;color:#fbbf24;">{total_sales:,}</div>
                    <div style="font-size:12px;color:#a1a1aa;">Sales Made</div>
                </div>
            </div>
        </div>
        
        <!-- Feature Highlight -->
        {feature}
        
        <!-- Book Promotion -->
        {book_promo}
        
        <!-- CTA -->
        <div style="text-align:center;margin:25px 0;">
            <a href="https://info-pilot.preview.emergentagent.com/" 
               style="display:inline-block;background:linear-gradient(135deg,#7c3aed 0%,#ec4899 100%);color:white;text-decoration:none;padding:15px 35px;border-radius:30px;font-weight:bold;font-size:16px;">
                🔍 Start Searching Now!
            </a>
        </div>
        
        <!-- Closing -->
        <div style="background:rgba(124,58,237,0.1);border-radius:12px;padding:20px;margin-bottom:25px;text-align:center;">
            <p style="margin:0;color:#c4b5fd;font-size:14px;line-height:1.6;">
                {closing}
            </p>
        </div>
        
        <!-- Footer -->
        <div style="text-align:center;padding-top:20px;border-top:1px solid rgba(124,58,237,0.2);">
            <p style="color:#71717a;font-size:12px;margin:0;">
                🚀 Powered by <strong>InfoPilot Explorer</strong> • Top Pilot Enterprises, Inc.
            </p>
            <p style="color:#52525b;font-size:11px;margin:10px 0 0 0;">
                "Three ventures. One mission. Zero turbulence." ✈️
            </p>
            <p style="color:#52525b;font-size:10px;margin:10px 0 0 0;">
                You're receiving this tri-weekly newsletter because you're awesome!<br/>
                <a href="https://info-pilot.preview.emergentagent.com/#settings" style="color:#7c3aed;">Manage preferences</a> | 
                <a href="https://info-pilot.preview.emergentagent.com/api/newsletter/unsubscribe" style="color:#7c3aed;">Unsubscribe</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return subject, html


async def send_triweekly_newsletter(time_slot: str):
    """Send the tri-weekly newsletter to all subscribers"""
    from config import db
    from services.email_service import send_email, is_email_configured
    
    logger.info(f"🚀 Starting tri-weekly newsletter send ({time_slot})...")
    
    if not is_email_configured():
        logger.warning("Email not configured - skipping tri-weekly newsletter")
        return
    
    # Get all active subscribers
    subscribers = await db.newsletter_subscribers.find({"active": True}).to_list(1000)
    
    if not subscribers:
        logger.info("No active subscribers - skipping")
        return
    
    # Generate the newsletter
    subject, html = await generate_triweekly_newsletter(time_slot)
    
    # Send to all subscribers
    success_count = 0
    for subscriber in subscribers:
        try:
            email = subscriber.get("email")
            if not email:
                continue
                
            result = await send_email(email, subject, html, is_html=True)
            if result.get("success"):
                success_count += 1
                logger.info(f"✅ Sent tri-weekly newsletter to {email}")
            else:
                logger.error(f"❌ Failed to send to {email}: {result.get('error')}")
        except Exception as e:
            logger.error(f"❌ Exception sending to {email}: {e}")
    
    # Log the send
    await db.newsletter_sends.insert_one({
        "type": "triweekly",
        "time_slot": time_slot,
        "subject": subject,
        "sent_at": datetime.now(timezone.utc),
        "total_subscribers": len(subscribers),
        "successful_sends": success_count
    })
    
    logger.info(f"📧 Tri-weekly newsletter complete: {success_count}/{len(subscribers)} sent successfully")


# ==================== AI-DRIVEN SCHEDULING OPTIMIZATION ====================

async def get_newsletter_performance_data():
    """Gather newsletter performance data for AI analysis"""
    from config import db
    
    # Get last 30 days of newsletter sends
    sends = await db.newsletter_sends.find({
        "sent_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)}
    }).to_list(1000)
    
    # Calculate open rates and click rates by time slot
    performance_by_slot = {}
    for send in sends:
        slot = send.get("time_slot", "unknown")
        if slot not in performance_by_slot:
            performance_by_slot[slot] = {
                "sends": 0,
                "successful": 0,
                "total_subscribers": 0
            }
        performance_by_slot[slot]["sends"] += 1
        performance_by_slot[slot]["successful"] += send.get("successful_sends", 0)
        performance_by_slot[slot]["total_subscribers"] += send.get("total_subscribers", 0)
    
    return {
        "performance_by_slot": performance_by_slot,
        "total_sends": len(sends),
        "analysis_period": "30 days"
    }


async def ai_optimize_newsletter_times() -> dict:
    """Use AI to analyze performance data and suggest optimal send times"""
    try:
        from emergentintegrations.llm.chat import chat, ModelType
        import os
        
        emergent_key = os.environ.get("EMERGENT_MODEL_API_KEY", "")
        if not emergent_key:
            return {
                "success": False,
                "error": "Emergent LLM key not configured",
                "fallback_recommendation": {
                    "morning": "5:30 AM UTC",
                    "midmorning": "9:15 AM UTC", 
                    "afternoon": "4:30 PM UTC",
                    "reason": "Default times based on general email marketing best practices"
                }
            }
        
        # Gather performance data
        perf_data = await get_newsletter_performance_data()
        
        prompt = f"""You are an AI email marketing optimization expert. Analyze the following newsletter performance data and recommend the optimal send times for maximum engagement and revenue.

Performance Data (Last 30 Days):
{perf_data}

Current Schedule:
- Morning: 5:42 AM UTC
- Mid-Morning: 8:37 AM UTC  
- Afternoon: 4:41 PM UTC

Consider:
1. General email marketing best practices (high open rates typically 9-11 AM local time)
2. The target audience is global, so UTC times should balance US/EU/Asia engagement
3. Weekend vs weekday patterns
4. Avoiding spam filter triggers from unusual send times

Provide your recommendations in this exact JSON format:
{{
    "recommended_morning_time": "HH:MM UTC",
    "recommended_midmorning_time": "HH:MM UTC",
    "recommended_afternoon_time": "HH:MM UTC",
    "reasoning": "Brief explanation of recommendations",
    "expected_improvement": "Estimated percentage improvement in engagement"
}}

Be specific with times and provide actionable insights!"""

        response = await chat(
            api_key=emergent_key,
            model=ModelType.GPT_5_2,
            prompt=prompt
        )
        
        import json
        try:
            # Try to parse JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                recommendations = json.loads(response[json_start:json_end])
                return {
                    "success": True,
                    "ai_recommendations": recommendations,
                    "performance_data": perf_data,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
        except json.JSONDecodeError:
            pass
        
        return {
            "success": True,
            "ai_response": response,
            "performance_data": perf_data
        }
        
    except Exception as e:
        logger.error(f"AI optimization error: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_recommendation": {
                "morning": "5:30 AM UTC",
                "midmorning": "9:15 AM UTC",
                "afternoon": "4:30 PM UTC",
                "reason": "Default times based on general email marketing best practices"
            }
        }


async def apply_ai_optimized_schedule(recommendations: dict):
    """Apply AI-recommended schedule to the newsletter scheduler"""
    global triweekly_scheduler
    from config import db
    
    if not triweekly_scheduler:
        logger.warning("Scheduler not running - cannot apply AI optimizations")
        return {"success": False, "error": "Scheduler not running"}
    
    try:
        # Parse times from recommendations
        morning_time = recommendations.get("recommended_morning_time", "5:42 UTC").replace(" UTC", "")
        midmorning_time = recommendations.get("recommended_midmorning_time", "8:37 UTC").replace(" UTC", "")
        afternoon_time = recommendations.get("recommended_afternoon_time", "16:41 UTC").replace(" UTC", "")
        
        morning_parts = morning_time.split(":")
        midmorning_parts = midmorning_time.split(":")
        afternoon_parts = afternoon_time.split(":")
        
        # Update jobs with new times
        triweekly_scheduler.reschedule_job(
            "triweekly_morning",
            trigger=CronTrigger(hour=int(morning_parts[0]), minute=int(morning_parts[1]))
        )
        triweekly_scheduler.reschedule_job(
            "triweekly_midmorning", 
            trigger=CronTrigger(hour=int(midmorning_parts[0]), minute=int(midmorning_parts[1]))
        )
        triweekly_scheduler.reschedule_job(
            "triweekly_afternoon",
            trigger=CronTrigger(hour=int(afternoon_parts[0]), minute=int(afternoon_parts[1]))
        )
        
        # Save optimized times to database
        await db.app_settings.update_one(
            {"key": "newsletter_ai_schedule"},
            {"$set": {
                "key": "newsletter_ai_schedule",
                "morning_time": morning_time,
                "midmorning_time": midmorning_time,
                "afternoon_time": afternoon_time,
                "reasoning": recommendations.get("reasoning", ""),
                "applied_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        
        logger.info("🤖 AI-optimized newsletter schedule applied!")
        logger.info(f"   - Morning: {morning_time} UTC")
        logger.info(f"   - Mid-Morning: {midmorning_time} UTC")
        logger.info(f"   - Afternoon: {afternoon_time} UTC")
        
        return {
            "success": True,
            "new_schedule": {
                "morning": morning_time,
                "midmorning": midmorning_time,
                "afternoon": afternoon_time
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to apply AI schedule: {e}")
        return {"success": False, "error": str(e)}


def start_triweekly_scheduler():
    """Start the tri-weekly newsletter scheduler"""
    global triweekly_scheduler
    
    if triweekly_scheduler is not None:
        logger.warning("Tri-weekly scheduler already running")
        return
    
    triweekly_scheduler = AsyncIOScheduler(timezone="UTC")
    
    # Schedule 1: 5:46 AM UTC (Morning Edition) - Per user request
    triweekly_scheduler.add_job(
        lambda: asyncio.create_task(send_triweekly_newsletter("morning")),
        CronTrigger(hour=5, minute=46),
        id="triweekly_morning",
        name="Tri-Weekly Newsletter (5:46 AM)",
        replace_existing=True
    )
    
    # Schedule 2: 9:42 AM UTC (Mid-Morning Edition) - Per user request
    triweekly_scheduler.add_job(
        lambda: asyncio.create_task(send_triweekly_newsletter("midmorning")),
        CronTrigger(hour=9, minute=42),
        id="triweekly_midmorning",
        name="Tri-Weekly Newsletter (9:42 AM)",
        replace_existing=True
    )
    
    # Schedule 3: 4:20 PM UTC (Afternoon Edition) - Per user request
    triweekly_scheduler.add_job(
        lambda: asyncio.create_task(send_triweekly_newsletter("afternoon")),
        CronTrigger(hour=16, minute=20),
        id="triweekly_afternoon",
        name="Tri-Weekly Newsletter (4:20 PM)",
        replace_existing=True
    )
    
    triweekly_scheduler.start()
    logger.info("📬 Tri-weekly newsletter scheduler started!")
    logger.info("   - 5:46 AM UTC (Morning Edition)")
    logger.info("   - 9:42 AM UTC (Mid-Morning Edition)")
    logger.info("   - 4:20 PM UTC (Afternoon Edition)")


def stop_triweekly_scheduler():
    """Stop the tri-weekly newsletter scheduler"""
    global triweekly_scheduler
    
    if triweekly_scheduler is not None:
        triweekly_scheduler.shutdown(wait=False)
        triweekly_scheduler = None
        logger.info("📬 Tri-weekly newsletter scheduler stopped")


async def trigger_test_newsletter(time_slot: str = "morning", recipient: str = None) -> dict:
    """Trigger a test newsletter send"""
    from services.email_service import send_email, is_email_configured
    
    if not is_email_configured():
        return {"success": False, "error": "Email not configured"}
    
    subject, html = await generate_triweekly_newsletter(time_slot)
    
    target_email = recipient or "jjspilot24@gmail.com"
    result = await send_email(target_email, f"[TEST] {subject}", html, is_html=True)
    
    return result
