"""
InfoPilot Explorer - Email Service
Handles newsletter generation and email sending via Resend
With EXTREMELY FUNNY supernatural comedy style like "Letters to Evelyn"
"""
import resend
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import db, logger, RESEND_API_KEY, SENDER_EMAIL, BOOK_PROMO, EMERGENT_LLM_KEY


# Funny subject lines for newsletters
FUNNY_SUBJECT_LINES = [
    "🔮 InfoPilot Weekly: The Ghosts Approved This Newsletter",
    "📰 Your Weekly Dose of Search Magic (No Séance Required!)",
    "🎭 InfoPilot Digest: Funnier Than Your Last Family Reunion",
    "✨ This Newsletter is Haunted... With GREAT DEALS!",
    "🚀 InfoPilot Update: We Promise No Ghosts Were Harmed",
    "📧 Breaking: Newsletter Escapes Email Prison, Finds Your Inbox!",
    "🎉 InfoPilot Weekly: Now With 50% More Supernatural Comedy!",
    "💡 Your Search Results Called. They Miss You. (So Does Our Book!)",
]

# Funny newsletter opening lines
FUNNY_OPENERS = [
    "Greetings, fellow information seekers! 👋 (Yes, we see you scrolling at 2 AM. We don't judge.)",
    "Welcome back, Protocol Pioneer! 🏆 Your keyboard has been lonely without you.",
    "Dear Valued Human, (unless you're a ghost reading this, in which case... we have a book for you!) 👻",
    "Hello there! You've opened this email, which means you either love us or accidentally clicked. Either way, welcome!",
    "Ahoy, Knowledge Navigator! 🧭 Ready to discover things even Google is jealous of?",
]

# Funny book promotion blurbs
FUNNY_BOOK_BLURBS = [
    "Speaking of supernatural comedy... have you met our book? It's like if your favorite sitcom had a baby with a ghost story. The baby is hilarious.",
    "Plot twist: There's a book that's funnier than this newsletter. Yes, we're jealous of ourselves. Get 'Letters to Evelyn' now!",
    "Need something to read while your protocols are searching? 'Letters to Evelyn' is like a warm hug from a very witty ghost. Only $2.99!",
    "Between searches, why not enjoy a supernatural thriller comedy that 19 professional reviewers gave 5 stars? (The ghosts gave it 6 stars, but that's not official.)",
    "Fun fact: Reading 'Letters to Evelyn' has been scientifically proven to make you 47% more interesting at parties. (Source: We made this up, but the book IS great!)",
]

# Funny closing lines
FUNNY_CLOSINGS = [
    "Happy searching! May your protocols always find what you seek (and may your coffee always be hot)! ☕",
    "Until next time, keep your searches smart and your humor supernatural! 👻",
    "Go forth and conquer the information world! (But maybe buy our book first? Pretty please?) 📚",
    "That's all for now! Remember: In a world of regular searches, be an InfoPilot! 🚀",
    "Signing off with love, laughs, and an unreasonable amount of search results! 💜",
]


class EmailService:
    """Email and newsletter service with supernatural comedy style"""
    
    @staticmethod
    async def generate_newsletter_content() -> str:
        """Generate AI-powered newsletter content using Emergent LLM"""
        if not EMERGENT_LLM_KEY:
            return await EmailService._generate_funny_fallback_newsletter()
        
        try:
            from emergentintegrations.llm.chat import chat
            
            # Get real stats
            total_users = await db.users.count_documents({})
            total_protocols = await db.marketplace_protocols.count_documents({})
            total_searches = await db.search_results.count_documents({})
            
            prompt = f"""Generate a HILARIOUS weekly newsletter for InfoPilot Explorer!

STATS THIS WEEK:
- {total_users} total users
- {total_protocols} protocols in marketplace
- {total_searches} searches performed

MANDATORY BOOK PROMOTION (make it EXTREMELY FUNNY):
Title: {BOOK_PROMO['title']}
Author: {BOOK_PROMO['author']}
Genre: {BOOK_PROMO['genre']} - Think ghost stories meets sitcom!
Price: Only {BOOK_PROMO['price']} on Amazon!
Review: "{BOOK_PROMO['featured_review']['quote']}" - {BOOK_PROMO['featured_review']['reviewer']}

MARKETPLACE PROMOTION:
- World Wide Marketplace with protocols from $0.00 (FREE!) to $99.99
- Pay What You Want feature
- Top sellers earn REAL money!

STYLE GUIDE:
- Write like a supernatural comedy - think ghosts with a sense of humor
- Use lots of emojis (but tastefully)
- Include puns, wordplay, and witty observations
- Make readers laugh AND want to buy the book
- Keep it under 600 words
- Format in clean HTML with purple/pink color scheme
- Include a "GHOST TIP OF THE WEEK" section (funny search advice)

Remember: The goal is to make this THE FUNNIEST newsletter they've ever read while promoting the book and marketplace!"""

            response = await chat(
                api_key=EMERGENT_LLM_KEY,
                prompt=prompt,
                model="gpt-4o-mini"
            )
            
            return response
        except Exception as e:
            logger.error(f"AI newsletter generation failed: {e}")
            return await EmailService._generate_funny_fallback_newsletter()
    
    @staticmethod
    async def _generate_funny_fallback_newsletter() -> str:
        """Generate funny fallback newsletter content without AI"""
        opener = random.choice(FUNNY_OPENERS)
        book_blurb = random.choice(FUNNY_BOOK_BLURBS)
        closing = random.choice(FUNNY_CLOSINGS)
        
        # Get real stats
        try:
            total_users = await db.users.count_documents({})
            total_protocols = await db.marketplace_protocols.count_documents({})
            total_searches = await db.search_results.count_documents({})
        except:
            total_users = 100
            total_protocols = 50
            total_searches = 1000
        
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 30px; border-radius: 20px;">
            
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #a78bfa; margin-bottom: 5px;">🔮 InfoPilot Weekly</h1>
                <p style="color: #f472b6; font-style: italic;">The newsletter that's more fun than a séance (and less spooky!)</p>
            </div>
            
            <div style="background: rgba(139, 92, 246, 0.2); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                <p style="color: #e0e0e0; font-size: 16px; line-height: 1.6;">{opener}</p>
            </div>
            
            <div style="margin-bottom: 25px;">
                <h2 style="color: #f472b6;">📊 This Week in Numbers</h2>
                <div style="display: flex; justify-content: space-around; text-align: center; flex-wrap: wrap;">
                    <div style="padding: 15px;">
                        <div style="font-size: 2.5rem; color: #10b981; font-weight: bold;">{total_users}</div>
                        <div style="color: #a1a1aa;">Happy Searchers</div>
                    </div>
                    <div style="padding: 15px;">
                        <div style="font-size: 2.5rem; color: #f59e0b; font-weight: bold;">{total_protocols}</div>
                        <div style="color: #a1a1aa;">Protocols Available</div>
                    </div>
                    <div style="padding: 15px;">
                        <div style="font-size: 2.5rem; color: #8b5cf6; font-weight: bold;">{total_searches}</div>
                        <div style="color: #a1a1aa;">Searches Performed</div>
                    </div>
                </div>
            </div>
            
            <div style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(139, 92, 246, 0.3)); padding: 25px; border-radius: 15px; margin-bottom: 25px; border: 2px solid #ec4899;">
                <h2 style="color: #fbbf24; margin-top: 0;">📚 Book Spotlight: Letters to Evelyn</h2>
                <p style="color: #e0e0e0; font-size: 15px; line-height: 1.6;">{book_blurb}</p>
                <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <p style="color: #f472b6; font-style: italic; margin: 0;">"{BOOK_PROMO['featured_review']['quote']}"</p>
                    <p style="color: #a1a1aa; margin: 5px 0 0 0; font-size: 14px;">- {BOOK_PROMO['featured_review']['reviewer']}</p>
                </div>
                <div style="text-align: center;">
                    <a href="{BOOK_PROMO['amazon_url']}" style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #ec4899, #f97316); color: white; text-decoration: none; border-radius: 30px; font-weight: bold; font-size: 16px;">🛒 Get It Now - Only {BOOK_PROMO['price']}!</a>
                </div>
            </div>
            
            <div style="background: rgba(16, 185, 129, 0.2); padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                <h2 style="color: #10b981; margin-top: 0;">👻 Ghost Tip of the Week</h2>
                <p style="color: #e0e0e0;">Did you know? Our World Wide Marketplace has protocols ranging from <strong style="color: #10b981;">FREE ($0.00)</strong> to $99.99! 
                That's right - FREE protocols exist! It's like finding money in your couch, except it's search power. 
                And the ghosts told us (via séance, obviously) that the FREE protocols are almost as good as the paid ones. Almost. 😉</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);">
                <p style="color: #a78bfa; font-size: 16px;">{closing}</p>
                <p style="color: #71717a; font-size: 12px; margin-top: 15px;">
                    Top Pilot Enterprises, Inc. • Brunswick, Maine<br/>
                    <a href="https://www.amazon.com/dp/B0DC735Q4W" style="color: #f472b6;">Buy the Book</a> • 
                    <a href="https://www.facebook.com/profile.php?id=61560950042481" style="color: #f472b6;">Visit Us</a>
                </p>
            </div>
            
        </div>
        """
    
    @staticmethod
    async def send_newsletter(subject: str, html_content: str, recipient_emails: List[str]) -> Dict[str, Any]:
        """Send newsletter to a list of recipients"""
        if not RESEND_API_KEY:
            return {"success": False, "error": "Resend API key not configured"}
        
        try:
            results = []
            for email in recipient_emails:
                response = resend.Emails.send({
                    "from": SENDER_EMAIL,
                    "to": email,
                    "subject": subject,
                    "html": html_content
                })
                results.append({"email": email, "id": response.get("id")})
            
            # Store newsletter record
            await db.newsletters.insert_one({
                "subject": subject,
                "content": html_content,
                "recipients": len(recipient_emails),
                "sent_at": datetime.utcnow(),
                "results": results
            })
            
            return {"success": True, "sent": len(results), "results": results}
        except Exception as e:
            logger.error(f"Newsletter send error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_subscriber_emails() -> List[str]:
        """Get all subscriber email addresses"""
        users = await db.users.find({}, {"email": 1}).to_list(1000)
        return [u["email"] for u in users if u.get("email")]
    
    @staticmethod
    async def send_weekly_newsletter() -> Dict[str, Any]:
        """Generate and send the weekly newsletter to all subscribers"""
        subject = random.choice(FUNNY_SUBJECT_LINES) + f" - {datetime.now().strftime('%B %d')}"
        content = await EmailService.generate_newsletter_content()
        subscribers = await EmailService.get_subscriber_emails()
        
        if not subscribers:
            return {"success": False, "error": "No subscribers found"}
        
        return await EmailService.send_newsletter(subject, content, subscribers)
    
    @staticmethod
    async def send_test_email(recipient: str) -> Dict[str, Any]:
        """Send a test newsletter email"""
        content = await EmailService.generate_newsletter_content()
        subject = random.choice(FUNNY_SUBJECT_LINES) + f" [TEST] - {datetime.now().strftime('%B %d')}"
        
        if not RESEND_API_KEY:
            return {"success": False, "error": "Resend API key not configured", "preview": content}
        
        try:
            response = resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": recipient,
                "subject": subject,
                "html": content
            })
            return {"success": True, "id": response.get("id"), "preview": content[:500]}
        except Exception as e:
            return {"success": False, "error": str(e), "preview": content}
    
    @staticmethod
    def get_random_funny_subject() -> str:
        """Get a random funny subject line"""
        return random.choice(FUNNY_SUBJECT_LINES)
