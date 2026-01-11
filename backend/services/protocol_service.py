"""
InfoPilot Explorer - Protocol Parser Service
Handles parsing and matching of search protocols
"""
import re
from typing import List, Dict, Any, Tuple
from fuzzywuzzy import fuzz
from config import logger


class ProtocolParser:
    """
    Parser for InfoPilot search protocols
    Protocol format: (word1 or word2) & (word3)+ means:
    - (word1 or word2) - Match either word1 OR word2
    - & - AND operator
    - + - Boost indicator (higher relevance)
    """
    
    @staticmethod
    def validate_protocol(protocol: str) -> Tuple[bool, str]:
        """Validate a protocol string and return (is_valid, error_message)"""
        if not protocol or not protocol.strip():
            return False, "Protocol cannot be empty"
        
        # Check for basic structure
        protocol = protocol.strip()
        
        # Check for matching parentheses
        open_count = protocol.count('(')
        close_count = protocol.count(')')
        if open_count != close_count:
            return False, f"Mismatched parentheses: {open_count} open, {close_count} close"
        
        # Check for at least one group
        if '(' not in protocol or ')' not in protocol:
            return False, "Protocol must contain at least one group: (word1 or word2)"
        
        # Check for operators
        has_and = '&' in protocol
        has_or = ' or ' in protocol.lower()
        
        if not has_or:
            return False, "Protocol must contain 'or' operators within groups"
        
        return True, "Valid protocol"
    
    @staticmethod
    def parse_protocol(protocol: str) -> List[Dict[str, Any]]:
        """
        Parse a protocol string into structured groups
        Returns list of groups, each with terms and modifiers
        """
        groups = []
        
        # Split by & operator
        parts = re.split(r'\s*&\s*', protocol)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check for boost modifier
            is_boosted = part.endswith('+')
            if is_boosted:
                part = part[:-1].strip()
            
            # Extract terms from parentheses
            match = re.search(r'\((.*?)\)', part)
            if match:
                terms_str = match.group(1)
                # Split by 'or' (case insensitive)
                terms = [t.strip() for t in re.split(r'\s+or\s+', terms_str, flags=re.IGNORECASE)]
                terms = [t for t in terms if t]  # Remove empty strings
                
                if terms:
                    groups.append({
                        "terms": terms,
                        "boosted": is_boosted,
                        "required": True
                    })
        
        return groups
    
    @staticmethod
    def fuzzy_match(text: str, term: str, threshold: int = 60) -> bool:
        """Check if term fuzzy matches anywhere in text"""
        if not text or not term:
            return False
        
        text_lower = text.lower()
        term_lower = term.lower()
        
        # Direct substring match (most common)
        if term_lower in text_lower:
            return True
        
        # Fuzzy match for typos and variations
        words = text_lower.split()
        for word in words:
            if len(word) >= 3 and len(term_lower) >= 3:
                ratio = fuzz.ratio(word, term_lower)
                if ratio >= threshold:
                    return True
                
                # Partial ratio for longer terms
                if len(term_lower) > 5:
                    partial = fuzz.partial_ratio(term_lower, word)
                    if partial >= threshold + 10:
                        return True
        
        # Check for partial matches in phrases
        if len(term_lower) > 3:
            partial = fuzz.partial_ratio(term_lower, text_lower)
            if partial >= threshold + 15:
                return True
        
        return False
    
    @staticmethod
    def match_result(result: Dict[str, Any], groups: List[Dict[str, Any]], 
                     threshold: int = 55) -> Tuple[bool, float]:
        """
        Check if a search result matches the protocol groups
        Returns (matches, score)
        """
        if not groups:
            return False, 0.0
        
        # Combine all text from result
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        content = result.get("content", "")
        combined_text = f"{title} {snippet} {content}"
        
        if not combined_text.strip():
            return False, 0.0
        
        matched_groups = 0
        total_score = 0.0
        
        for group in groups:
            group_matched = False
            group_score = 0.0
            
            for term in group["terms"]:
                if ProtocolParser.fuzzy_match(combined_text, term, threshold):
                    group_matched = True
                    # Calculate match quality
                    if term.lower() in combined_text.lower():
                        group_score = 1.0  # Exact match
                    else:
                        group_score = 0.8  # Fuzzy match
                    break
            
            if group_matched:
                matched_groups += 1
                if group["boosted"]:
                    group_score *= 1.5  # Boost score
                total_score += group_score
        
        # Must match at least 50% of groups (more lenient)
        min_required = max(1, len(groups) // 2)
        matches = matched_groups >= min_required
        
        # Normalize score
        if len(groups) > 0:
            normalized_score = (total_score / len(groups)) * (matched_groups / len(groups))
        else:
            normalized_score = 0.0
        
        return matches, normalized_score
    
    @staticmethod
    def extract_search_query(protocol: str) -> str:
        """Extract a web search query from a protocol"""
        # Parse groups
        groups = ProtocolParser.parse_protocol(protocol)
        
        # Get first term from each group (up to 4 groups)
        query_terms = []
        for group in groups[:4]:
            if group["terms"]:
                # Prefer shorter terms for search
                best_term = min(group["terms"], key=len)
                query_terms.append(best_term)
        
        return " ".join(query_terms)
    
    @staticmethod
    def debug_protocol(protocol: str) -> Dict[str, Any]:
        """Return debugging info about a protocol"""
        is_valid, message = ProtocolParser.validate_protocol(protocol)
        groups = ProtocolParser.parse_protocol(protocol) if is_valid else []
        search_query = ProtocolParser.extract_search_query(protocol) if is_valid else ""
        
        return {
            "valid": is_valid,
            "validation_message": message,
            "groups": groups,
            "group_count": len(groups),
            "extracted_search_query": search_query,
            "terms_per_group": [len(g["terms"]) for g in groups]
        }
