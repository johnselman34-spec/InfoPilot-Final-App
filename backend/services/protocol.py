"""
Protocol parsing and document classification services
"""
import re
from typing import Dict

from models.enums import DocumentType


class ProtocolParser:
    """InfoJet 2.0 Protocol Language Parser"""
    
    @staticmethod
    def parse_protocol(protocol: str) -> Dict:
        """Parse a protocol string into structured search terms"""
        # Replace 'and' with '&' for consistency
        protocol = re.sub(r'\band\b', '&', protocol, flags=re.IGNORECASE)
        
        # Split by & to get groups
        groups = [g.strip() for g in protocol.split('&') if g.strip()]
        
        result = {
            "include_groups": [],
            "exclude_groups": [],
            "all_terms": []
        }
        
        for group in groups:
            is_exclude = False
            is_include = False
            
            # Check for modifiers
            if group.startswith('^') or group.endswith('^'):
                is_exclude = True
                group = group.replace('^', '').strip()
            elif group.startswith('+') or group.endswith('+'):
                is_include = True
                group = group.replace('+', '').strip()
            
            # Extract terms from parentheses
            match = re.search(r'\(([^)]+)\)', group)
            if match:
                terms_str = match.group(1)
                terms = [t.strip() for t in terms_str.split(' or ')]
                
                if is_exclude:
                    result["exclude_groups"].append(terms)
                else:
                    result["include_groups"].append(terms)
                    result["all_terms"].extend(terms)
        
        return result
    
    @staticmethod
    def matches_protocol(text: str, protocol: str) -> bool:
        """Check if text matches the given protocol"""
        if not text or not protocol:
            return False
            
        text_lower = text.lower()
        parsed = ProtocolParser.parse_protocol(protocol)
        
        # Check exclusions first
        for exclude_group in parsed["exclude_groups"]:
            for term in exclude_group:
                if term.lower() in text_lower:
                    return False
        
        # Check inclusions - all groups must have at least one match
        for include_group in parsed["include_groups"]:
            group_matched = False
            for term in include_group:
                if term.lower() in text_lower:
                    group_matched = True
                    break
            if not group_matched:
                return False
        
        return True


class DocumentClassifier:
    """Classify documents based on content"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_settings(self):
        """Get classification settings from admin"""
        settings = await self.db.settings.find_one({"key": "doc_classification"}, {"_id": 0})
        return settings.get("value", {}) if settings else {}
    
    async def classify(self, content: str, title: str = "", url: str = "") -> DocumentType:
        """Classify document type based on content and rules"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        settings = await self.get_settings()
        
        # Check for Ph.D indicators
        phd_count = sum([
            content_lower.count(term) for term in ['ph.d.', 'phd', 'd.phil.', 'dr.']
        ])
        word_count = len(content.split())
        min_phd_words = settings.get("phd_min_words", 1500)
        min_phd_mentions = settings.get("phd_min_mentions", 3)
        
        if phd_count >= min_phd_mentions and word_count >= min_phd_words:
            return DocumentType.INFORMATIVE_PHD
        
        # Check for Forum
        if 'forum' in title_lower:
            return DocumentType.FORUM
        
        # Check for Blog
        blog_count = content_lower.count('blog')
        if blog_count >= 3 and 'blog' in title_lower:
            return DocumentType.BLOG
        
        # Check for News Article
        news_terms = ['news', 'story', 'news story']
        news_count = sum([content_lower.count(term) for term in news_terms])
        if news_count > 3:
            return DocumentType.NEWS_ARTICLE
        
        # Check for Personal Report (Collected)
        # Count 'I' outside of quotes
        i_count = len(re.findall(r'\bI\b(?!["\'])', content))
        if i_count >= 3:
            # Check paragraph length
            paragraphs = content.split('\n\n')
            for p in paragraphs:
                if len(p.split()) >= 75 and p.count('I ') >= 3:
                    return DocumentType.PERSONAL_REPORT_COLLECTED
        
        # Check for Informative content
        informative_protocol = settings.get("informative_protocol", 
            "(there are or there is) & (may have or might have or that are)")
        if ProtocolParser.matches_protocol(content, informative_protocol):
            return DocumentType.INFORMATIVE
        
        return DocumentType.NEWS_ARTICLE
