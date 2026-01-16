"""
InfoPilot Explorer - Protocol Parser Service
Handles parsing and matching of search protocols
Enhanced to handle:
- Abbreviated names: "William C. Gamble", "John F. Kennedy", "John J S"
- Location abbreviations: "Heidelberg, GER", "Albuquerque, NM", "Nm", "Baden Wuerttemberg"
- Common abbreviations: "etc.", "U.S.", "Dr.", "Mr.", "Jr.", "Sr."
- Case-insensitive OR operators
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
    
    Supports:
    - Abbreviated names: "William C. Gamble", "John F. Kennedy", "John J S", "John S."
    - Location abbreviations: "Heidelberg, GER", "Albuquerque, NM", "Brunswick, ME"
    - German/European locations: "Baden Wuerttemberg, GER", "München, DEU"
    - Common abbreviations: "etc.", "U.S.", "Dr.", "Mr.", "Jr.", "Sr."
    - Case-insensitive OR: "or", "Or", "OR" all work
    - Quoted phrases: "exact phrase match"
    """
    
    # Common abbreviations that should be preserved
    COMMON_ABBREVIATIONS = [
        'etc.', 'e.g.', 'i.e.', 'vs.', 'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Jr.', 'Sr.',
        'Prof.', 'Rev.', 'Gen.', 'Col.', 'Lt.', 'Sgt.', 'Capt.', 'Maj.', 'Gov.',
        'St.', 'Ave.', 'Blvd.', 'Rd.', 'Inc.', 'Corp.', 'Co.', 'Ltd.', 'LLC.',
        'U.S.', 'U.S.A.', 'U.K.', 'D.C.', 'N.Y.', 'L.A.', 'a.m.', 'p.m.',
        'Ph.D.', 'M.D.', 'B.A.', 'M.A.', 'B.S.', 'M.S.', 'J.D.', 'M.B.A.',
        'ft.', 'in.', 'lb.', 'oz.', 'qt.', 'pt.', 'gal.', 'mi.', 'yd.',
        'Jan.', 'Feb.', 'Mar.', 'Apr.', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Sept.',
        'Oct.', 'Nov.', 'Dec.', 'Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.'
    ]
    
    # US State abbreviations (both upper and mixed case)
    US_STATE_ABBREVIATIONS = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID',
        'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
        'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK',
        'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV',
        'WI', 'WY', 'DC', 'PR', 'VI', 'GU', 'AS', 'MP'
    ]
    
    # Country abbreviations
    COUNTRY_ABBREVIATIONS = [
        'USA', 'US', 'UK', 'GB', 'GBR', 'GER', 'DEU', 'FRA', 'ESP', 'ITA', 'CAN',
        'AUS', 'NZL', 'JPN', 'CHN', 'KOR', 'IND', 'BRA', 'MEX', 'ARG', 'RUS',
        'NLD', 'BEL', 'CHE', 'AUT', 'POL', 'SWE', 'NOR', 'DNK', 'FIN', 'PRT'
    ]
    
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
        
        # Check for operators (case-insensitive OR)
        # Accept both "&" and "and" (case-insensitive) as group separators
        has_and = '&' in protocol or bool(re.search(r'\s+and\s+', protocol, re.IGNORECASE))
        has_or = bool(re.search(r'\bor\b', protocol, re.IGNORECASE))
        
        if not has_or:
            return False, "Protocol must contain 'or' operators within groups"
        
        return True, "Valid protocol"
    
    @staticmethod
    def _normalize_term(term: str) -> str:
        """Normalize a term while preserving abbreviations and punctuation"""
        term = term.strip()
        
        # Remove surrounding quotes if present (but keep the content)
        if (term.startswith('"') and term.endswith('"')) or \
           (term.startswith("'") and term.endswith("'")):
            term = term[1:-1]
        
        return term
    
    @staticmethod
    def _is_abbreviation_or_location(term: str) -> bool:
        """
        Check if a term is an abbreviation or location format
        Examples: "William C. Gamble", "John J S", "Heidelberg, GER", "NM"
        """
        # Check for single/double letter with period (C. G. J.)
        if re.match(r'^[A-Za-z]\.$', term):
            return True
        
        # Check for initials without periods (J S, J J S)
        if re.match(r'^[A-Za-z](\s+[A-Za-z])*$', term):
            return True
        
        # Check for US state abbreviation
        if term.upper() in ProtocolParser.US_STATE_ABBREVIATIONS:
            return True
        
        # Check for country abbreviation
        if term.upper() in ProtocolParser.COUNTRY_ABBREVIATIONS:
            return True
        
        # Check for location format (City, STATE/COUNTRY)
        if re.match(r'^[A-Za-z\s]+,\s*[A-Za-z]{2,3}$', term):
            return True
        
        return False
    
    @staticmethod
    def _split_terms_by_or(terms_str: str) -> List[str]:
        """
        Split terms by 'or' (case-insensitive) while preserving quoted phrases and abbreviations
        Handles: 
        - "William C. Gamble or John F. Kennedy or etc."
        - "Heidelberg, GER or Albuquerque, NM"
        - "John J S or John S."
        - Case variations: "or", "Or", "OR"
        """
        terms = []
        current_term = ""
        in_quotes = False
        quote_char = None
        i = 0
        
        while i < len(terms_str):
            char = terms_str[i]
            
            # Handle quotes
            if char in '"\'':
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                    current_term += char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                    current_term += char
                else:
                    current_term += char
                i += 1
                continue
            
            # Check for ' or ' (case insensitive) when not in quotes
            if not in_quotes and i + 4 <= len(terms_str):
                potential_or = terms_str[i:i+4]
                # Case-insensitive check for " or "
                if potential_or.lower() == ' or ':
                    # Save current term if not empty
                    if current_term.strip():
                        terms.append(ProtocolParser._normalize_term(current_term))
                    current_term = ""
                    i += 4  # Skip ' or '
                    continue
            
            current_term += char
            i += 1
        
        # Add final term
        if current_term.strip():
            terms.append(ProtocolParser._normalize_term(current_term))
        
        return terms
    
    @staticmethod
    def parse_protocol(protocol: str) -> List[Dict[str, Any]]:
        """
        Parse a protocol string into structured groups
        Returns list of groups, each with terms and modifiers
        
        Handles abbreviated names like "William C. Gamble" and
        abbreviations like "etc.", "U.S.", etc.
        
        NOW ACCEPTS: Both "&" and "and" (case-insensitive) as group separators
        Examples: 
          - (word1 or word2) & (word3) 
          - (word1 or word2) and (word3)
          - (word1 or word2) AND (word3)
        """
        groups = []
        
        # Normalize "and" to "&" (case-insensitive, with word boundaries)
        # Match " and " surrounded by spaces to avoid matching "and" within words
        normalized_protocol = re.sub(r'\s+and\s+', ' & ', protocol, flags=re.IGNORECASE)
        
        # Split by & operator
        parts = re.split(r'\s*&\s*', normalized_protocol)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check for modifiers
            is_boosted = part.endswith('+')
            is_excluded = part.endswith('^')
            is_include_all = part.endswith('+')
            
            # Remove modifier
            if is_boosted or is_excluded:
                part = part[:-1].strip()
            
            # Extract terms from parentheses - use a more robust regex
            # This handles nested content and preserves periods/abbreviations
            match = re.search(r'\(([^)]+)\)', part)
            if match:
                terms_str = match.group(1)
                
                # Use custom splitter that handles abbreviations
                terms = ProtocolParser._split_terms_by_or(terms_str)
                terms = [t for t in terms if t]  # Remove empty strings
                
                if terms:
                    groups.append({
                        "terms": terms,
                        "boosted": is_boosted,
                        "excluded": is_excluded,
                        "include_all": is_include_all,
                        "required": True
                    })
        
        return groups
    
    @staticmethod
    def _prepare_term_for_matching(term: str) -> str:
        """Prepare a term for matching by normalizing it"""
        # Remove quotes
        term = term.strip().strip('"\'')
        return term.lower()
    
    @staticmethod
    def fuzzy_match(text: str, term: str, threshold: int = 60) -> bool:
        """Check if term fuzzy matches anywhere in text"""
        if not text or not term:
            return False
        
        text_lower = text.lower()
        term_lower = ProtocolParser._prepare_term_for_matching(term)
        
        # Direct substring match (most common) - handles abbreviations
        if term_lower in text_lower:
            return True
        
        # Check for term with different punctuation variations
        # Handle cases like "U.S." matching "US" or "U.S.A"
        term_no_periods = term_lower.replace('.', '')
        text_no_periods = text_lower.replace('.', '')
        if term_no_periods and term_no_periods in text_no_periods:
            return True
        
        # For multi-word terms (like "William C. Gamble"), check as phrase
        if ' ' in term_lower or '.' in term_lower:
            # Try exact phrase match
            if term_lower in text_lower:
                return True
            
            # Try without periods
            if term_no_periods in text_no_periods:
                return True
            
            # Try partial phrase matching for names with initials
            # "William C. Gamble" should match "William Gamble" or "W. C. Gamble"
            words = term_lower.replace('.', ' ').split()
            words = [w for w in words if w]
            if len(words) >= 2:
                # Check if all significant words appear in text
                significant_words = [w for w in words if len(w) > 1]
                if significant_words:
                    matches = sum(1 for w in significant_words if w in text_lower)
                    if matches >= len(significant_words) * 0.7:  # 70% match threshold
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
        excluded_groups = 0
        total_score = 0.0
        
        for group in groups:
            group_matched = False
            group_score = 0.0
            
            for term in group["terms"]:
                if ProtocolParser.fuzzy_match(combined_text, term, threshold):
                    group_matched = True
                    # Calculate match quality
                    term_lower = ProtocolParser._prepare_term_for_matching(term)
                    if term_lower in combined_text.lower():
                        group_score = 1.0  # Exact match
                    else:
                        group_score = 0.8  # Fuzzy match
                    break
            
            if group_matched:
                if group.get("excluded"):
                    excluded_groups += 1
                else:
                    matched_groups += 1
                    if group["boosted"]:
                        group_score *= 1.5  # Boost score
                    total_score += group_score
        
        # If any excluded groups matched, reject
        if excluded_groups > 0:
            return False, 0.0
        
        # Must match at least 50% of non-excluded groups (more lenient)
        non_excluded_groups = [g for g in groups if not g.get("excluded")]
        min_required = max(1, len(non_excluded_groups) // 2)
        matches = matched_groups >= min_required
        
        # Normalize score
        if len(non_excluded_groups) > 0:
            normalized_score = (total_score / len(non_excluded_groups)) * (matched_groups / len(non_excluded_groups))
        else:
            normalized_score = 0.0
        
        return matches, normalized_score
    
    @staticmethod
    def extract_search_query(protocol: str) -> str:
        """Extract a web search query from a protocol"""
        # Parse groups
        groups = ProtocolParser.parse_protocol(protocol)
        
        # Get first term from each non-excluded group (up to 4 groups)
        query_terms = []
        for group in groups[:4]:
            if group.get("excluded"):
                continue
            if group["terms"]:
                # Prefer shorter terms for search, but keep full names
                best_term = min(group["terms"], key=len)
                # Keep the full term including abbreviations
                query_terms.append(best_term)
        
        return " ".join(query_terms)
    
    @staticmethod
    def generate_deep_search_queries(protocol: str, max_queries: int = 10) -> List[str]:
        """
        Generate multiple search query variations from a protocol for DEEP searching.
        This ensures we search with different term combinations to find results
        that truly match the protocol, not just top-ranked generic results.
        
        Returns list of unique search queries to execute.
        """
        groups = ProtocolParser.parse_protocol(protocol)
        non_excluded = [g for g in groups if not g.get("excluded")]
        
        if not non_excluded:
            return []
        
        queries = set()
        
        # Strategy 1: All combinations of first terms from each group
        first_terms = [g["terms"][0] if g["terms"] else "" for g in non_excluded]
        first_terms = [t for t in first_terms if t]
        if first_terms:
            queries.add(" ".join(first_terms))
        
        # Strategy 2: Boosted groups get priority - search with each boosted term individually
        for group in non_excluded:
            if group.get("boosted") and group["terms"]:
                for term in group["terms"][:3]:  # Top 3 terms from boosted groups
                    queries.add(term)
                    # Combine with terms from other groups
                    for other_group in non_excluded:
                        if other_group != group and other_group["terms"]:
                            queries.add(f"{term} {other_group['terms'][0]}")
        
        # Strategy 3: Generate queries using different terms from each group
        import itertools
        
        # Get up to 3 terms from each group
        term_lists = []
        for group in non_excluded[:4]:  # Limit to 4 groups
            terms = group["terms"][:3] if group["terms"] else [""]
            term_lists.append(terms)
        
        # Generate combinations (limit to avoid explosion)
        if term_lists:
            for combo in itertools.product(*term_lists):
                query = " ".join([t for t in combo if t])
                if query:
                    queries.add(query)
                if len(queries) >= max_queries * 2:
                    break
        
        # Strategy 4: Quoted exact phrases for multi-word terms
        for group in non_excluded:
            for term in group["terms"]:
                if " " in term or "." in term:  # Multi-word or abbreviated
                    queries.add(f'"{term}"')
        
        # Strategy 5: Combine longest terms (most specific)
        longest_terms = []
        for group in non_excluded:
            if group["terms"]:
                longest = max(group["terms"], key=len)
                longest_terms.append(longest)
        if len(longest_terms) >= 2:
            queries.add(" ".join(longest_terms[:3]))
        
        # Convert to list and limit
        query_list = list(queries)[:max_queries]
        
        # Ensure we have at least one query
        if not query_list and non_excluded and non_excluded[0]["terms"]:
            query_list = [non_excluded[0]["terms"][0]]
        
        return query_list
    
    @staticmethod
    def strict_match_result(result: Dict[str, Any], groups: List[Dict[str, Any]], 
                           min_group_match_percent: float = 0.7,
                           fuzzy_threshold: int = 70) -> Tuple[bool, float, Dict[str, Any]]:
        """
        STRICT protocol matching - only accepts results that truly fulfill requirements.
        
        Args:
            result: Search result to match
            groups: Parsed protocol groups
            min_group_match_percent: Minimum percentage of groups that must match (0.0-1.0)
            fuzzy_threshold: Minimum fuzzy match score (higher = stricter)
        
        Returns:
            (matches, score, match_details)
        """
        if not groups:
            return False, 0.0, {}
        
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        content = result.get("content", "")
        combined_text = f"{title} {snippet} {content}"
        
        if not combined_text.strip():
            return False, 0.0, {}
        
        non_excluded = [g for g in groups if not g.get("excluded")]
        excluded = [g for g in groups if g.get("excluded")]
        
        # Check excluded groups first - any match = reject
        for group in excluded:
            for term in group["terms"]:
                if ProtocolParser.fuzzy_match(combined_text, term, fuzzy_threshold - 10):
                    return False, 0.0, {"rejected_by": term}
        
        # Match non-excluded groups
        matched_groups = []
        unmatched_groups = []
        total_score = 0.0
        
        for i, group in enumerate(non_excluded):
            group_matched = False
            best_match_score = 0.0
            matched_term = None
            
            for term in group["terms"]:
                term_lower = ProtocolParser._prepare_term_for_matching(term)
                
                # Check for exact match first (highest score)
                if term_lower in combined_text.lower():
                    group_matched = True
                    best_match_score = 1.0
                    matched_term = term
                    
                    # Bonus if in title
                    if term_lower in title.lower():
                        best_match_score = 1.2
                    break
                
                # Check fuzzy match
                elif ProtocolParser.fuzzy_match(combined_text, term, fuzzy_threshold):
                    group_matched = True
                    best_match_score = 0.75
                    matched_term = term
            
            if group_matched:
                if group.get("boosted"):
                    best_match_score *= 1.5
                total_score += best_match_score
                matched_groups.append({
                    "group_index": i,
                    "matched_term": matched_term,
                    "score": best_match_score
                })
            else:
                unmatched_groups.append({
                    "group_index": i,
                    "required_terms": group["terms"][:3]
                })
        
        # Calculate match percentage
        if len(non_excluded) == 0:
            return False, 0.0, {}
        
        match_percent = len(matched_groups) / len(non_excluded)
        
        # STRICT: Must match minimum percentage of groups
        if match_percent < min_group_match_percent:
            return False, 0.0, {
                "match_percent": match_percent,
                "required_percent": min_group_match_percent,
                "unmatched_groups": unmatched_groups
            }
        
        # Normalize score (0.0 - 1.0 range, can exceed with bonuses)
        normalized_score = (total_score / len(non_excluded)) * match_percent
        
        match_details = {
            "match_percent": match_percent,
            "matched_groups": matched_groups,
            "unmatched_groups": unmatched_groups,
            "total_groups": len(non_excluded),
            "groups_matched": len(matched_groups)
        }
        
        return True, normalized_score, match_details
    
    @staticmethod
    def debug_protocol(protocol: str) -> Dict[str, Any]:
        """Return debugging info about a protocol"""
        is_valid, message = ProtocolParser.validate_protocol(protocol)
        groups = ProtocolParser.parse_protocol(protocol) if is_valid else []
        search_query = ProtocolParser.extract_search_query(protocol) if is_valid else ""
        
        # Include term details for debugging
        term_details = []
        for i, group in enumerate(groups):
            term_details.append({
                "group": i + 1,
                "terms": group["terms"],
                "boosted": group.get("boosted", False),
                "excluded": group.get("excluded", False)
            })
        
        return {
            "valid": is_valid,
            "validation_message": message,
            "groups": groups,
            "group_count": len(groups),
            "extracted_search_query": search_query,
            "terms_per_group": [len(g["terms"]) for g in groups],
            "term_details": term_details
        }
