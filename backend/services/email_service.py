"""
InfoPilot Explorer - Email Service
Handles newsletter generation and email sending via Resend
"""
import resend
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import db, logger, RESEND_API_KEY, SENDER_EMAIL, BOOK_PROMO, EMERGENT_LLM_KEY


class EmailService:
    """Email and newsletter service"""
    
    @staticmethod
    async def generate_newsletter_content() -> str:
        """Generate AI-powered newsletter content using Emergent LLM"""
        if not EMERGENT_LLM_KEY:
            return EmailService._fallback_newsletter_content()
        
        try:
            from litellm import completion
            
            prompt = f"""Generate a fun, engaging weekly newsletter for InfoPilot Explorer users!

STATS THIS WEEK:
- Include placeholder stats about searches and discoveries

BOOK SPOTLIGHT:
Title: {BOOK_PROMO['title']}
Author: {BOOK_PROMO['author']}
Genre: {BOOK_PROMO['genre']}
Price: {BOOK_PROMO['price']}
Amazon: {BOOK_PROMO['amazon_url']}
Featured Review: "{BOOK_PROMO['featured_review']['quote']}" - {BOOK_PROMO['featured_review']['reviewer']}

Make it EXTREMELY FUNNY with witty observations and jokes! Use emojis liberally.
Include a section promoting the book with humor.
Keep it under 500 words. Format in HTML with inline styles."""

            response = completion(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                api_key=EMERGENT_LLM_KEY,
                api_base="https://api.emergentmethods.ai/v1"
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI newsletter generation failed: {e}")
            return EmailService._fallback_newsletter_content()
    
    @staticmethod
    def _fallback_newsletter_content() -> str:
        """Fallback newsletter content when AI is unavailable"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #7c3aed;">🚀 InfoPilot Weekly Update</h1>
            
            <h2 style="color: #ec4899;">📚 Book of the Week</h2>
            <p>Check out <strong>{BOOK_PROMO['title']}</strong> by {BOOK_PROMO['author']}!</p>
            <p><em>"{BOOK_PROMO['featured_review']['quote']}"</em></p>
            <p>- {BOOK_PROMO['featured_review']['reviewer']}</p>
            <a href="{BOOK_PROMO['amazon_url']}" style="display: inline-block; padding: 10px 20px; background: #ec4899; color: white; text-decoration: none; border-radius: 5px;">Get it on Amazon - {BOOK_PROMO['price']}</a>
            
            <h2 style="color: #10b981; margin-top: 30px;">✨ What's New</h2>
            <ul>
                <li>Interactive World Map with clickable markers</li>
                <li>Protocol Marketplace coming soon!</li>
                <li>Enhanced search with up to 99 pages of results</li>
            </ul>
            
            <p style="margin-top: 30px; color: #666;">Happy searching! 🔍</p>
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
    async def send_test_email(recipient: str) -> Dict[str, Any]:
        """Send a test newsletter email"""
        content = await EmailService.generate_newsletter_content()
        subject = f"📧 InfoPilot Test Newsletter - {datetime.now().strftime('%B %d, %Y')}"
        
        if not RESEND_API_KEY:
            return {"success": False, "error": "Resend API key not configured"}
        
        try:
            response = resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": recipient,
                "subject": subject,
                "html": content
            })
            return {"success": True, "id": response.get("id"), "preview": content[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}
