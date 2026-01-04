import re
from typing import List, Tuple, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# InfoJet 2.0 Protocol Parser
def parse_protocol(protocol: str) -> Tuple[bool, str, List[str]]:
    """
    Parse InfoJet 2.0 protocol and return validity, error message, and search terms.
    Format: (word1 or word2) & (word3 or word4) & (word5)+ & (word6)^
    """
    try:
        # Remove extra whitespace
        protocol = ' '.join(protocol.split())
        
        # Check for balanced parentheses
        if protocol.count('(') != protocol.count(')'):
            return False, "Unbalanced parentheses in protocol", []
        
        # Find all groups: (words) with optional + or ^ modifiers
        pattern = r'\(([^)]+)\)\s*([+^]?)'
        matches = re.findall(pattern, protocol)
        
        if not matches:
            return False, "Invalid protocol format. Use: (word1 or word2) & (word3)", []
        
        # Extract search terms
        search_terms = []
        for group_content, modifier in matches:
            # Split by 'or' and clean up
            terms = [term.strip() for term in group_content.split(' or ')]
            search_terms.append({
                'terms': terms,
                'modifier': modifier if modifier else 'normal'  # +, ^, or normal
            })
        
        # Check if groups are separated by &
        groups_text = re.sub(r'\([^)]+\)\s*[+^]?', 'GROUP', protocol)
        if '&' in protocol and 'GROUP' not in groups_text.replace('GROUP', '').replace('&', '').strip():
            pass  # Valid
        
        return True, "", search_terms
        
    except Exception as e:
        return False, f"Error parsing protocol: {str(e)}", []

def protocol_to_search_query(protocol: str) -> str:
    """
    Convert InfoJet 2.0 protocol to Google search query.
    """
    valid, error, search_terms = parse_protocol(protocol)
    
    if not valid:
        return ""
    
    query_parts = []
    
    for group in search_terms:
        terms = group['terms']
        modifier = group['modifier']
        
        if modifier == '^':  # Exclusion
            for term in terms:
                query_parts.append(f'-"{term}"')
        elif modifier == '+':  # Inclusion (all must appear)
            for term in terms:
                query_parts.append(f'"{term}"')
        else:  # Normal OR
            if len(terms) == 1:
                query_parts.append(f'"{terms[0]}"')
            else:
                or_group = ' OR '.join([f'"{term}"' for term in terms])
                query_parts.append(f'({or_group})')
    
    return ' '.join(query_parts)

# Content Filtering
BANNED_CATEGORIES = [
    # Pornographic words (add more as needed)
    "porn", "xxx", "sex", "adult", "nude", "naked",
    # Child-related words in various languages
    "child", "children", "kid", "kids", "boy", "girl", "young", "teen", "teenager",
    "minor", "youth", "juvenile", "infant", "toddler", "baby",
    # Spanish
    "niño", "niña", "niños", "niñas", "menor", "joven",
    # French
    "enfant", "enfants", "garçon", "fille", "jeune", "mineur",
    # German
    "kind", "kinder", "junge", "mädchen", "jugend",
    # Nuclear weapons
    "nuclear weapon", "nuclear bomb", "atomic bomb", "hydrogen bomb", "thermonuclear",
    "nuclear warhead", "nuclear missile", "nuclear arsenal", "nuke", "nukes",
    "nuclear strike", "nuclear attack", "nuclear warfare",
    # Chemical weapons
    "chemical weapon", "chemical warfare", "nerve agent", "sarin", "vx gas",
    "mustard gas", "chlorine gas", "phosgene", "chemical attack", "toxic agent",
    "biological weapon", "bioweapon", "anthrax weapon",
    # Psychological warfare and interrogation
    "psychological warfare", "psyops", "psychological operations", "mind control",
    "interrogation technique", "torture method", "enhanced interrogation",
    "waterboarding", "psychological torture", "brainwashing", "coercive interrogation",
    "torture technique", "interrogation technology",
    # Add more languages as needed
]

def contains_banned_content(text: str) -> bool:
    """
    Check if text contains banned words or phrases.
    """
    text_lower = text.lower()
    for banned_word in BANNED_CATEGORIES:
        if banned_word in text_lower:
            return True
    return False

def extract_root_domain(url: str) -> str:
    """
    Extract root domain from URL.
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www.
        domain = domain.replace('www.', '')
        return domain
    except:
        return url

def extract_year_from_text(text: str) -> int:
    """
    Extract year from text (snippet or title).
    """
    try:
        # Look for 4-digit years between 1900-2099
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        if years:
            return int(years[0])
    except:
        pass
    return None
