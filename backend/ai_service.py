from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from dotenv import load_dotenv
import asyncio
import re

load_dotenv()

class AIService:
    def __init__(self):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        
    async def classify_article(self, title: str, snippet: str, url: str) -> dict:
        """
        Classify article type using AI.
        Returns: {
            'article_type': str,
            'contains_banned': bool,
            'confidence': str
        }
        """
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"classify-{url[:50]}",
                system_message="""You are an article classifier. Analyze the given article information and determine its type.

Article Types:
1. Informative PhD - Contains (Ph.D. or PhD or D.Phil. or Dr.) AND has academic/research content with 1500+ words equivalent
2. Informative - Educational content that explains concepts, contains phrases like "there are", "may have", "this type", "is more than"
3. News Article - Current events, contains "news", "story", "breaking"
4. Blog - Personal blog content, contains "blog" in title or mentions blogging
5. Forum - Discussion forum, contains "forum" in title or URL
6. Personal Report (organic) - First-person narrative written by author
7. Personal Report (collected) - Contains multiple "I" statements outside quotes

You must also check for:
- Inappropriate content (pornography, explicit material)
- Child-related content (any words related to children, minors, kids)
- Profanity or cuss words

Respond in this exact format:
ARTICLE_TYPE: [type]
BANNED_CONTENT: [yes/no]
CONFIDENCE: [high/medium/low]
REASON: [brief explanation]"""
            ).with_model("openai", "gpt-4")
            
            user_message = UserMessage(
                text=f"""Analyze this article:

Title: {title}
Snippet: {snippet}
URL: {url}

Classify the article type and check for banned content."""
            )
            
            response = await chat.send_message(user_message)
            
            # Parse response
            article_type = "News Article"  # default
            contains_banned = False
            confidence = "medium"
            
            if "ARTICLE_TYPE:" in response:
                type_match = re.search(r'ARTICLE_TYPE:\s*(.+)', response)
                if type_match:
                    article_type = type_match.group(1).strip()
            
            if "BANNED_CONTENT:" in response:
                banned_match = re.search(r'BANNED_CONTENT:\s*(.+)', response)
                if banned_match:
                    contains_banned = "yes" in banned_match.group(1).lower()
            
            if "CONFIDENCE:" in response:
                conf_match = re.search(r'CONFIDENCE:\s*(.+)', response)
                if conf_match:
                    confidence = conf_match.group(1).strip().lower()
            
            return {
                'article_type': article_type,
                'contains_banned': contains_banned,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"AI Classification error: {str(e)}")
            # Fallback to basic classification
            return {
                'article_type': 'News Article',
                'contains_banned': False,
                'confidence': 'low'
            }
    
    async def check_protocol_matches_result(self, protocol_terms: list, title: str, snippet: str) -> bool:
        """
        Check if search result matches the protocol requirements.
        Uses AI to understand semantic matching.
        """
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id="protocol-matcher",
                system_message="""You are a protocol matcher. Given a set of search term groups and an article, determine if the article matches the protocol requirements.

Rules:
- Each group separated by & must have at least one matching term (unless it's an exclusion group with ^)
- Groups with + modifier must have ALL terms present
- Groups with ^ modifier must have NONE of the terms present
- Use semantic understanding to match concepts, not just exact words

Respond with only: MATCH or NO_MATCH"""
            ).with_model("openai", "gpt-4")
            
            terms_str = "\n".join([f"Group {i+1} ({g.get('modifier', 'normal')}): {', '.join(g['terms'])}" 
                                   for i, g in enumerate(protocol_terms)])
            
            user_message = UserMessage(
                text=f"""Protocol Terms:
{terms_str}

Article:
Title: {title}
Snippet: {snippet}

Does this article match the protocol?"""
            )
            
            response = await chat.send_message(user_message)
            return "MATCH" in response.upper()
            
        except Exception as e:
            print(f"Protocol matching error: {str(e)}")
            # Fallback to simple keyword matching
            combined_text = f"{title} {snippet}".lower()
            for group in protocol_terms:
                if group.get('modifier') == '^':
                    # Exclusion: if any term found, reject
                    if any(term.lower() in combined_text for term in group['terms']):
                        return False
                else:
                    # Must find at least one term
                    if not any(term.lower() in combined_text for term in group['terms']):
                        return False
            return True

# Singleton instance
ai_service = AIService()
