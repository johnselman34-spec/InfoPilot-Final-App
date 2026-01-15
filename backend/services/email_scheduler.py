"""
InfoPilot Explorer - Scheduled Email Reports with EXTREME HUMOR + AI INSIGHTS
Because data without laughter is just... sad numbers.
Now with GPT-5.2 powered recommendations!
"""
import os
import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

# Hilarious subject lines that maximize open rates
FUNNY_SUBJECT_LINES = [
    "🚀 Your A/B Tests Are CRUSHING IT (Unlike My Diet)",
    "📊 Weekly Stats: More Exciting Than Your Ex's Instagram",
    "💰 Money News: Your Protocols Are Making Bank!",
    "🎯 A/B Test Results: The Numbers Don't Lie (Unlike Politicians)",
    "📈 Your Conversion Rates Are Hotter Than My Coffee",
    "🏆 Winner Winner Chicken Dinner: This Week's A/B Champions",
    "🎪 Step Right Up! Your Weekly Data Circus Is Here!",
    "💎 Diamond-Tier Stats: You're Basically Warren Buffett Now",
    "🔥 These Numbers Are So Hot, They Need Sunscreen",
    "🎭 Plot Twist: Your A/B Tests Actually Worked!",
    "🤖 AI Says: Your Data Looks AMAZING (And AI Never Lies... Right?)",
    "📬 Your Weekly Dose of Revenue Dopamine Has Arrived!",
]

# Hilarious intro paragraphs
FUNNY_INTROS = [
    "Greetings, Data Wizard! 🧙‍♂️ Your weekly dose of numbers that actually make sense (unlike assembly instructions from IKEA).",
    "Hello, Revenue Rockstar! 🎸 Time to see how your A/B tests performed while you were busy pretending to work.",
    "Ahoy, Conversion Captain! ⚓ Your ship has sailed into the profitable waters of statistical significance!",
    "Salutations, Split-Test Sovereign! 👑 The kingdom of conversions has news for thee!",
    "Hey there, Growth Guru! 🧘 May your click-through rates be high and your bounce rates be as low as gas prices never are.",
    "What's up, Analytics Ace! 🃏 The cards have been dealt, and spoiler alert: you're winning!",
    "Bonjour, Optimization Overlord! 🥐 Your data croissants are fresh out of the statistical oven!",
]

# Hilarious closing lines
FUNNY_CLOSINGS = [
    "May your conversions be high and your coffee strong! ☕",
    "Remember: In the game of A/B testing, you either win or you learn. But mostly you win! 🏆",
    "Go forth and convert! (Users, not religions. We're marketers, not missionaries.) 🎯",
    "Stay optimizing, stay humble, stay caffeinated! 💪",
    "Until next time: May the Click-Through Rate be with you! 🌟",
    "Keep crushing it! (Metaphorically. Please don't crush anything literally.) 💥",
    "Your friendly neighborhood data bot, signing off! 🤖❤️",
]

# Revenue-focused motivational quotes
REVENUE_QUOTES = [
    "💰 Fun fact: Every 1% improvement in conversion rate is basically free money. You're welcome!",
    "📈 Remember: A/B testing isn't gambling, it's SCIENCE gambling. Much classier!",
    "🎰 Your protocols are slot machines that actually pay out. Vegas HATES this one weird trick!",
    "💎 Warren Buffett once said 'Be fearful when others are fearful.' He probably meant about A/B tests.",
    "🚀 To infinity and beyond! (Your revenue, not your marketing budget. Please be reasonable.)",
]


def get_random_subject() -> str:
    """Get a random hilarious subject line"""
    import random
    return random.choice(FUNNY_SUBJECT_LINES)


def get_random_intro() -> str:
    """Get a random funny intro"""
    import random
    return random.choice(FUNNY_INTROS)


def get_random_closing() -> str:
    """Get a random funny closing"""
    import random
    return random.choice(FUNNY_CLOSINGS)


def get_random_revenue_quote() -> str:
    """Get a random revenue-focused quote"""
    import random
    return random.choice(REVENUE_QUOTES)


async def generate_hilarious_report_html(days: int = 7) -> tuple[str, str]:
    """
    Generate an EXTREMELY FUNNY A/B test report that maximizes:
    - Revenue awareness
    - Laughter
    - Usefulness
    """
    from config import db
    from datetime import datetime, timezone, timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get all A/B tests
    tests = await db.ab_tests.find({}).to_list(100)
    
    # Get events from the period
    events = await db.ab_events.find({
        "timestamp": {"$gte": cutoff}
    }).to_list(10000)
    
    # Calculate stats per test
    test_stats = []
    total_impressions = 0
    total_conversions = 0
    
    for test in tests:
        test_id = test.get("test_id", "")
        test_events = [e for e in events if e.get("test_id") == test_id]
        
        impressions = len([e for e in test_events if e.get("event_type") == "impression"])
        conversions = len([e for e in test_events if e.get("event_type") == "conversion"])
        
        total_impressions += impressions
        total_conversions += conversions
        
        # Find winning variant
        variants = test.get("variants", [])
        variant_stats = []
        for v in variants:
            v_id = v.get("variant_id", "")
            v_impressions = len([e for e in test_events if e.get("variant_id") == v_id and e.get("event_type") == "impression"])
            v_conversions = len([e for e in test_events if e.get("variant_id") == v_id and e.get("event_type") == "conversion"])
            conv_rate = (v_conversions / v_impressions * 100) if v_impressions > 0 else 0
            variant_stats.append({
                "id": v_id,
                "impressions": v_impressions,
                "conversions": v_conversions,
                "rate": conv_rate
            })
        
        # Sort by conversion rate
        variant_stats.sort(key=lambda x: x["rate"], reverse=True)
        winner = variant_stats[0] if variant_stats else None
        
        test_stats.append({
            "name": test.get("name", test_id),
            "impressions": impressions,
            "conversions": conversions,
            "rate": (conversions / impressions * 100) if impressions > 0 else 0,
            "winner": winner,
            "variants": variant_stats
        })
    
    overall_rate = (total_conversions / total_impressions * 100) if total_impressions > 0 else 0
    
    # Generate the HTML
    subject = get_random_subject()
    intro = get_random_intro()
    closing = get_random_closing()
    revenue_quote = get_random_revenue_quote()
    
    # Performance emoji based on conversion rate
    if overall_rate >= 10:
        performance_emoji = "🔥🔥🔥 LEGENDARY"
        performance_color = "#10b981"
    elif overall_rate >= 5:
        performance_emoji = "🚀🚀 EXCELLENT"
        performance_color = "#3b82f6"
    elif overall_rate >= 2:
        performance_emoji = "📈 GOOD"
        performance_color = "#f59e0b"
    else:
        performance_emoji = "🌱 GROWING"
        performance_color = "#8b5cf6"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InfoPilot A/B Test Report</title>
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#1a1025;color:#e2e8f0;">
    <div style="max-width:650px;margin:0 auto;padding:20px;">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#7c3aed 0%,#ec4899 100%);border-radius:16px;padding:30px;text-align:center;margin-bottom:25px;">
            <h1 style="margin:0;color:white;font-size:28px;">🎯 InfoPilot Weekly Report</h1>
            <p style="margin:10px 0 0 0;color:rgba(255,255,255,0.9);font-size:14px;">
                {datetime.now().strftime('%B %d, %Y')} • Last {days} Days
            </p>
        </div>
        
        <!-- Funny Intro -->
        <div style="background:rgba(124,58,237,0.1);border-left:4px solid #7c3aed;padding:20px;border-radius:0 12px 12px 0;margin-bottom:25px;">
            <p style="margin:0;font-size:16px;line-height:1.6;color:#c4b5fd;">
                {intro}
            </p>
        </div>
        
        <!-- Performance Summary -->
        <div style="background:rgba(30,20,50,0.8);border-radius:16px;padding:25px;margin-bottom:25px;border:1px solid rgba(124,58,237,0.3);">
            <h2 style="margin:0 0 20px 0;color:#f472b6;font-size:20px;">📊 The Big Picture</h2>
            
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:15px;">
                <div style="flex:1;min-width:120px;background:rgba(124,58,237,0.2);border-radius:12px;padding:15px;text-align:center;">
                    <div style="font-size:28px;font-weight:bold;color:#a78bfa;">{total_impressions:,}</div>
                    <div style="font-size:12px;color:#a1a1aa;margin-top:5px;">Total Impressions</div>
                </div>
                <div style="flex:1;min-width:120px;background:rgba(16,185,129,0.2);border-radius:12px;padding:15px;text-align:center;">
                    <div style="font-size:28px;font-weight:bold;color:#10b981;">{total_conversions:,}</div>
                    <div style="font-size:12px;color:#a1a1aa;margin-top:5px;">Conversions</div>
                </div>
                <div style="flex:1;min-width:120px;background:rgba(236,72,153,0.2);border-radius:12px;padding:15px;text-align:center;">
                    <div style="font-size:28px;font-weight:bold;color:{performance_color};">{overall_rate:.2f}%</div>
                    <div style="font-size:12px;color:#a1a1aa;margin-top:5px;">Conversion Rate</div>
                </div>
            </div>
            
            <div style="margin-top:20px;padding:15px;background:rgba(0,0,0,0.3);border-radius:10px;text-align:center;">
                <span style="font-size:18px;color:{performance_color};">{performance_emoji}</span>
                <p style="margin:5px 0 0 0;color:#a1a1aa;font-size:13px;">
                    {"🎉 You're absolutely crushing it!" if overall_rate >= 5 else "📈 Keep optimizing - greatness awaits!"}
                </p>
            </div>
        </div>
        
        <!-- Individual Tests -->
        <div style="background:rgba(30,20,50,0.8);border-radius:16px;padding:25px;margin-bottom:25px;border:1px solid rgba(124,58,237,0.3);">
            <h2 style="margin:0 0 20px 0;color:#f472b6;font-size:20px;">🧪 Test-by-Test Breakdown</h2>
            
            {"".join([f'''
            <div style="background:rgba(124,58,237,0.1);border-radius:12px;padding:15px;margin-bottom:15px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <h3 style="margin:0;color:#e2e8f0;font-size:16px;">🎯 {t["name"]}</h3>
                    <span style="background:rgba(16,185,129,0.2);color:#10b981;padding:4px 10px;border-radius:20px;font-size:12px;">
                        {t["rate"]:.1f}% CVR
                    </span>
                </div>
                <div style="display:flex;gap:15px;font-size:13px;color:#a1a1aa;">
                    <span>👁️ {t["impressions"]:,} views</span>
                    <span>✅ {t["conversions"]:,} conversions</span>
                    {f'<span style="color:#10b981;">🏆 Winner: {t["winner"]["id"]}</span>' if t["winner"] and t["winner"]["rate"] > 0 else ''}
                </div>
            </div>
            ''' for t in test_stats])}
            
            {f'<p style="color:#71717a;font-style:italic;text-align:center;margin:15px 0 0 0;">No test data yet? Time to create some experiments! 🔬</p>' if not test_stats else ''}
        </div>
        
        <!-- Revenue Quote -->
        <div style="background:linear-gradient(135deg,rgba(245,158,11,0.2) 0%,rgba(236,72,153,0.2) 100%);border-radius:12px;padding:20px;margin-bottom:25px;text-align:center;">
            <p style="margin:0;font-size:15px;color:#fbbf24;line-height:1.6;">
                {revenue_quote}
            </p>
        </div>
        
        <!-- CTA -->
        <div style="text-align:center;margin-bottom:25px;">
            <a href="https://infoexplore.preview.emergentagent.com/#admin" 
               style="display:inline-block;background:linear-gradient(135deg,#7c3aed 0%,#ec4899 100%);color:white;text-decoration:none;padding:15px 35px;border-radius:30px;font-weight:bold;font-size:16px;">
                📊 View Full Dashboard
            </a>
        </div>
        
        <!-- Funny Closing -->
        <div style="background:rgba(124,58,237,0.1);border-radius:12px;padding:20px;margin-bottom:25px;">
            <p style="margin:0;color:#c4b5fd;font-size:14px;text-align:center;line-height:1.6;">
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
                You're receiving this because you're an admin who opted in. 
                <a href="https://infoexplore.preview.emergentagent.com/#settings" style="color:#7c3aed;">Manage preferences</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return subject, html


async def send_scheduled_report():
    """Send the scheduled A/B test report to all configured recipients"""
    from config import db
    from services.email_service import send_email, is_email_configured
    
    logger.info("🚀 Starting scheduled email report job...")
    
    if not is_email_configured():
        logger.warning("Email not configured - skipping scheduled report")
        return
    
    # Get report configuration
    config = await db.email_report_config.find_one({}) or {}
    
    if not config.get("enabled", False):
        logger.info("Scheduled reports disabled - skipping")
        return
    
    recipients = config.get("recipients", ["jjspilot24@gmail.com"])
    
    # Generate the hilarious report
    subject, html = await generate_hilarious_report_html(days=7)
    
    # Send to all recipients
    success_count = 0
    for recipient in recipients:
        try:
            result = await send_email(recipient, subject, html, is_html=True)
            if result.get("success"):
                success_count += 1
                logger.info(f"✅ Sent scheduled report to {recipient}")
                
                # Log the send
                await db.email_logs.insert_one({
                    "recipient": recipient,
                    "subject": subject,
                    "sent_at": datetime.now(timezone.utc),
                    "success": True,
                    "type": "scheduled",
                    "period_days": 7
                })
            else:
                logger.error(f"❌ Failed to send to {recipient}: {result.get('error')}")
        except Exception as e:
            logger.error(f"❌ Exception sending to {recipient}: {e}")
    
    logger.info(f"📧 Scheduled report complete: {success_count}/{len(recipients)} sent successfully")


def start_scheduler():
    """Start the background scheduler for email reports"""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    scheduler = AsyncIOScheduler(timezone="UTC")
    
    # Schedule weekly reports - every Monday at 9 AM UTC
    scheduler.add_job(
        send_scheduled_report,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_ab_report",
        name="Weekly A/B Test Report",
        replace_existing=True
    )
    
    # Also run daily at 9 AM for more frequent updates (optional - can be enabled via config)
    # scheduler.add_job(
    #     send_scheduled_report,
    #     CronTrigger(hour=9, minute=0),
    #     id="daily_ab_report",
    #     name="Daily A/B Test Report",
    #     replace_existing=True
    # )
    
    scheduler.start()
    logger.info("🚀 Email scheduler started! Weekly reports scheduled for Monday 9 AM UTC")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("📧 Email scheduler stopped")


async def trigger_immediate_report(recipient: str = None) -> dict:
    """Trigger an immediate report (for testing or manual sends)"""
    from services.email_service import send_email, is_email_configured
    from config import db
    
    if not is_email_configured():
        return {"success": False, "error": "Email not configured"}
    
    # Use provided recipient or default
    if not recipient:
        config = await db.email_report_config.find_one({}) or {}
        recipients = config.get("recipients", ["jjspilot24@gmail.com"])
        recipient = recipients[0] if recipients else "jjspilot24@gmail.com"
    
    # Generate and send
    subject, html = await generate_hilarious_report_html(days=7)
    result = await send_email(recipient, subject, html, is_html=True)
    
    if result.get("success"):
        await db.email_logs.insert_one({
            "recipient": recipient,
            "subject": subject,
            "sent_at": datetime.now(timezone.utc),
            "success": True,
            "type": "manual",
            "period_days": 7
        })
    
    return result
