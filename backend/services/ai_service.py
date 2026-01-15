"""
AI Service - GPT-5.2 Integration for Newsletter Generation and Content
Uses Emergent LLM Key for OpenAI GPT-5.2
"""
import os
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class AIService:
    """AI Service for generating funny marketing content"""
    
    @staticmethod
    async def generate_newsletter_content(topic: str = "weekly update", context: dict = None) -> dict:
        """Generate extremely funny and convincing newsletter content using GPT-5.2"""
        try:
            api_key = os.getenv("EMERGENT_LLM_KEY")
            if not api_key:
                raise ValueError("EMERGENT_LLM_KEY not found in environment")
            
            # Initialize chat with GPT-5.2
            chat = LlmChat(
                api_key=api_key,
                session_id=f"newsletter-{topic}",
                system_message="""You are a hilariously witty marketing copywriter for InfoPilot Explorer and Top Pilot Enterprises, Inc.
Your job is to write EXTREMELY FUNNY and EXTREMELY CONVINCING marketing content.
You promote three ventures:
1. Letters to Evelyn - A supernatural thriller comedy memoir by John Selman (Navy pilot, 19 five-star reviews, OPTIONED FOR FILM!)
2. InfoPilot Explorer - World Wide Information Exchange with InfoJet 2.0™ search technology
3. Maestro Bistro - Brunswick, Maine restaurant famous for deLectaBLe Beef Rouladen (German Cuisine!)

Your tone should be:
- Absurdly funny but professional
- Self-aware and playful
- Creates FOMO (fear of missing out)
- Makes readers laugh AND want to buy/subscribe
- Uses wordplay, puns, and unexpected humor

Remember: "Three ventures. One mission. Zero turbulence." (Okay, maybe a little during lunch rush at the bistro.)"""
            ).with_model("openai", "gpt-5.2")
            
            # Build context message
            stats_info = ""
            if context:
                default_users = "growing faster than expected"
                default_protocols = "several mind-blowing ones"
                default_seller = "someone absolutely crushing it"
                default_sales = "enough to make my accountant smile"
                stats_info = f"""
Here are some stats to include humorously:
- Total Users: {context.get('total_users', default_users)}
- New Protocols: {context.get('new_protocols', default_protocols)}
- Top Seller: {context.get('top_seller', default_seller)}
- Book Sales: {context.get('book_sales', default_sales)}
"""
            
            user_message = UserMessage(
                text=f"""Write a hilarious weekly newsletter for InfoPilot Explorer subscribers.
Topic: {topic}
{stats_info}

Include these sections:
1. A catchy, funny subject line (make it irresistible to open)
2. Opening paragraph that hooks readers with humor
3. Featured Protocol of the Week (make up something absurd but useful)
4. Letters to Evelyn promotion (supernatural comedy memoir, $2.99 eBook)
5. InfoPilot tip of the week (search protocol trick)
6. Maestro Bistro mention (the chowder is legendary)
7. A hilarious sign-off

Make it sound like a friend who happens to be a comedy writer AND a marketing genius wrote it.
Format as JSON with keys: subject_line, opening, featured_protocol, book_promo, tip, bistro_mention, signoff, full_html"""
            )
            
            response = await chat.send_message(user_message)
            
            # Try to parse as JSON, otherwise return raw
            import json
            try:
                # Find JSON in response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
            except:
                pass
            
            return {
                "subject_line": "🚀 Your Weekly Dose of InfoPilot Awesomeness!",
                "full_html": response,
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"Newsletter generation failed: {e}")
            return {
                "error": str(e),
                "subject_line": "InfoPilot Weekly Update",
                "full_html": f"<p>Newsletter generation encountered an issue. Please try again.</p><p>Error: {e}</p>"
            }
    
    @staticmethod
    async def generate_hashtags(title: str, snippet: str, article_type: str) -> list:
        """Generate relevant hashtags for a search result"""
        try:
            api_key = os.getenv("EMERGENT_LLM_KEY")
            if not api_key:
                return []
            
            chat = LlmChat(
                api_key=api_key,
                session_id="hashtag-gen",
                system_message="You generate 4-6 relevant hashtags. Return ONLY the hashtags separated by spaces, nothing else."
            ).with_model("openai", "gpt-5.2")
            
            user_message = UserMessage(
                text=f"Generate 4-6 hashtags for: Title: {title}, Snippet: {snippet[:200]}, Type: {article_type}"
            )
            
            response = await chat.send_message(user_message)
            
            # Parse hashtags from response
            hashtags = [tag.strip() for tag in response.split() if tag.startswith('#')]
            if not hashtags:
                hashtags = ['#' + word.strip('#') for word in response.split()[:6]]
            
            return hashtags[:6]
            
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            return []
    
    @staticmethod
    async def generate_funny_title(original_title: str) -> str:
        """Generate a funnier version of a title for sharing"""
        try:
            api_key = os.getenv("EMERGENT_LLM_KEY")
            if not api_key:
                return original_title
            
            chat = LlmChat(
                api_key=api_key,
                session_id="title-gen",
                system_message="You make titles funnier while keeping them accurate. Return ONLY the new title, nothing else."
            ).with_model("openai", "gpt-5.2")
            
            user_message = UserMessage(
                text=f"Make this title funnier (keep it short): {original_title}"
            )
            
            response = await chat.send_message(user_message)
            return response.strip('"\'')
            
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return original_title
