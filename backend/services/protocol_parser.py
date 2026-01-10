"""Protocol parser and content matching"""
import re
from typing import Dict, Any

class InfoPilot2Parser:
    """
    InfoPilot 2.0 Boolean Protocol Parser
    
    Syntax:
    - (word1 or word2 or word3) - Match ANY word in the group
    - & - AND operator between groups
    - + suffix - INCLUDE ALL words in the group (all must be present)
    - ^ suffix - EXCLUDE ALL words in the group (none should be present)
    """
    
    @staticmethod
    def parse_protocol(protocol_string: str) -> Dict[str, Any]:
        """Parse InfoPilot 2.0 protocol string into structured format"""
        result = {
            "groups": [],
            "valid": True,
            "error": None
        }
        
        try:
            groups = re.split(r'\s*&\s*', protocol_string.strip())
            
            for group in groups:
                group = group.strip()
                if not group:
                    continue
                
                include_all = False
                exclude_all = False
                
                if group.startswith('+') or group.endswith('+'):
                    include_all = True
                    group = group.strip('+').strip()
                elif group.startswith('^') or group.endswith('^'):
                    exclude_all = True
                    group = group.strip('^').strip()
                
                match = re.match(r'\(([^)]+)\)', group)
                if match:
                    words_str = match.group(1)
                    words = [w.strip() for w in re.split(r'\s+or\s+', words_str, flags=re.IGNORECASE)]
                    
                    result["groups"].append({
                        "words": words,
                        "include_all": include_all,
                        "exclude_all": exclude_all,
                        "operator": "OR"
                    })
                else:
                    result["groups"].append({
                        "words": [group],
                        "include_all": include_all,
                        "exclude_all": exclude_all,
                        "operator": "OR"
                    })
            
            if not result["groups"]:
                result["valid"] = False
                result["error"] = "No valid groups found in protocol"
                
        except Exception as e:
            result["valid"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def match_content(content: str, parsed_protocol: Dict[str, Any]) -> bool:
        """Check if content matches the parsed protocol using word boundary matching"""
        if not parsed_protocol["valid"]:
            return False
        
        content_lower = content.lower()
        
        def phrase_matches(phrase: str, text: str) -> bool:
            """Check if a phrase/word matches in text using word boundaries.
            Handles multi-word phrases like 'William C. Gamble' as complete phrases.
            Uses simple string operations first for speed, then regex for edge cases.
            """
            phrase_lower = phrase.lower().strip()
            
            # Quick check: if phrase not in text at all, skip regex
            if phrase_lower not in text:
                return False
            
            # For single words without special chars, use simple word boundary check
            if ' ' not in phrase_lower and '.' not in phrase_lower:
                # Check if it's a whole word match using split
                words_in_text = set(re.findall(r'\b\w+\b', text))
                return phrase_lower in words_in_text
            
            # For multi-word phrases or phrases with punctuation, use regex
            escaped_phrase = re.escape(phrase_lower)
            pattern = r'(?:^|[\s\.,;:!?\-\(\)\[\]"])' + escaped_phrase + r'(?:[\s\.,;:!?\-\(\)\[\]"]|$)'
            return bool(re.search(pattern, text))
        
        for group in parsed_protocol["groups"]:
            words = group["words"]
            include_all = group["include_all"]
            exclude_all = group["exclude_all"]
            
            if exclude_all:
                # None of these phrases should be present
                for word in words:
                    if phrase_matches(word, content_lower):
                        return False
            elif include_all:
                # ALL of these phrases must be present
                for word in words:
                    if not phrase_matches(word, content_lower):
                        return False
            else:
                # ANY of these phrases must be present (OR logic)
                found = False
                for word in words:
                    if phrase_matches(word, content_lower):
                        found = True
                        break
                if not found:
                    return False
        
        return True
    
    @staticmethod
    def validate_protocol(protocol_string: str) -> tuple:
        """Validate protocol syntax"""
        parsed = InfoPilot2Parser.parse_protocol(protocol_string)
        if not parsed["valid"]:
            return False, parsed["error"]
        if len(parsed["groups"]) == 0:
            return False, "Protocol must contain at least one group"
        return True, "Valid protocol"
