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

# InfoJet 2.0 Protocol Parser - ENHANCED for abbreviations, locations, and complex names
def parse_protocol(protocol: str) -> Tuple[bool, str, List[str]]:
    """
    Parse InfoJet 2.0 protocol and return validity, error message, and search terms.
    Format: (word1 or word2) & (word3 or word4) & (word5)+ & (word6)^
    
    ENHANCED FEATURES:
    - Handles abbreviations with periods (e.g., "William C. Gamble", "U.S.", "Ph.D.", "etc.")
    - Handles location formats (e.g., "Heidelberg, GER", "Albuquerque, NM", "Baden Wuerttemberg, GER")
    - Handles multi-word phrases correctly
    - Case-insensitive matching for "or" keyword
    - Preserves capitalization in names and places
    - Properly splits on " or " not on partial matches
    """
    try:
        # Remove extra whitespace but preserve spaces within phrases
        protocol = ' '.join(protocol.split())
        
        # Check for balanced parentheses
        if protocol.count('(') != protocol.count(')'):
            return False, "Unbalanced parentheses in protocol", []
        
        # Find all groups: (words) with optional + or ^ modifiers
        # This regex handles content with periods, commas, apostrophes inside parentheses
        pattern = r'\(([^)]+)\)\s*([+^]?)'
        matches = re.findall(pattern, protocol)
        
        if not matches:
            return False, "Invalid protocol format. Use: (word1 or word2) & (word3)", []
        
        # Extract search terms
        search_terms = []
        for group_content, modifier in matches:
            # CRITICAL FIX: Split by ' or ' (with spaces) to avoid splitting words like "for" or "history"
            # Use case-insensitive split but preserve the original case of terms
            terms = split_on_or_keyword(group_content)
            
            # Clean up each term, preserving internal punctuation (periods, apostrophes, commas)
            cleaned_terms = []
            for term in terms:
                cleaned = normalize_term(term.strip())
                if cleaned:
                    cleaned_terms.append(cleaned)
            
            if cleaned_terms:
                search_terms.append({
                    'terms': cleaned_terms,
                    'modifier': modifier if modifier else 'normal'  # +, ^, or normal
                })
        
        # Check if groups are separated by &
        groups_text = re.sub(r'\([^)]+\)\s*[+^]?', 'GROUP', protocol)
        if '&' in protocol and 'GROUP' not in groups_text.replace('GROUP', '').replace('&', '').strip():
            pass  # Valid
        
        return True, "", search_terms
        
    except Exception as e:
        return False, f"Error parsing protocol: {str(e)}", []


def split_on_or_keyword(text: str) -> List[str]:
    """
    Split text on ' or ' keyword (case-insensitive) while preserving:
    - Abbreviations like "U.S." or "Ph.D."
    - Location names like "Heidelberg, GER" or "Albuquerque, NM"
    - Full names like "William C. Gamble" or "John J. Selman"
    
    The key is to only split on ' or ' that is surrounded by spaces
    and is NOT part of a word like "for", "history", "Oregon", etc.
    """
    # Pattern matches ' or ' with word boundaries
    # This ensures we don't split "Oregon" or "for" or "history"
    parts = re.split(r'(?<!\S)\s+[oO][rR]\s+(?!\S)', text)
    
    # If no split happened, try a simpler pattern
    if len(parts) == 1:
        parts = re.split(r'\s+[oO][rR]\s+', text)
    
    return [p.strip() for p in parts if p.strip()]


def normalize_term(term: str) -> str:
    """
    Normalize a search term while preserving:
    - Abbreviations with periods (e.g., "William C. Gamble", "U.S.", "Ph.D.")
    - Location formats (e.g., "Heidelberg, GER", "Albuquerque, NM")
    - Proper capitalization
    - Internal punctuation
    """
    if not term:
        return ""
    
    # Remove leading/trailing whitespace
    term = term.strip()
    
    # Don't modify terms that contain:
    # - Middle initials (e.g., "William C. Gamble")
    # - Abbreviations (e.g., "U.S.", "Ph.D.")
    # - Location formats (e.g., "Heidelberg, GER")
    
    # Check for common abbreviation patterns
    abbrev_patterns = [
        r'\b[A-Z]\.\s*[A-Z]',  # Middle initials like "C. G" or "J. S."
        r'\b[A-Z]\.[A-Z]\.',   # Abbreviations like "U.S." or "N.Y."
        r'\b[A-Z]{2,3}\b',     # Country/state codes like "GER", "NM", "USA"
        r'Ph\.D\.',            # PhD abbreviation
        r'etc\.',              # etc. abbreviation
        r',\s*[A-Z]{2,}',      # Location format like ", GER" or ", NM"
    ]
    
    # If any abbreviation pattern is found, preserve the term as-is
    for pattern in abbrev_patterns:
        if re.search(pattern, term):
            return term
    
    return term


def expand_name_variations(name: str) -> List[str]:
    """
    Generate common variations of a name for better search matching.
    E.g., "William C. Gamble" -> ["William C. Gamble", "William Gamble", "W. C. Gamble", "Bill Gamble", "General Gamble"]
    """
    variations = [name]
    
    # Common first name nicknames
    nickname_map = {
        'William': ['Bill', 'Will', 'Willy'],
        'Richard': ['Rich', 'Rick', 'Dick'],
        'Robert': ['Bob', 'Rob', 'Bobby'],
        'James': ['Jim', 'Jimmy', 'Jamie'],
        'John': ['Jack', 'Johnny'],
        'Joshua': ['Josh'],
        'Joseph': ['Joe', 'Joey'],
        'Michael': ['Mike', 'Mikey'],
        'Thomas': ['Tom', 'Tommy'],
        'Charles': ['Chuck', 'Charlie'],
        'George': ['Geo'],
    }
    
    # Extract parts of the name
    parts = name.split()
    if len(parts) >= 2:
        first_name = parts[0]
        
        # Add nickname variations
        if first_name in nickname_map:
            for nickname in nickname_map[first_name]:
                # Replace first name with nickname
                new_parts = [nickname] + parts[1:]
                variations.append(' '.join(new_parts))
        
        # If there's a middle initial, create version without it
        if len(parts) >= 3:
            # Check if middle part looks like an initial (e.g., "C." or "J.")
            middle = parts[1]
            if len(middle) <= 2 and (middle.endswith('.') or len(middle) == 1):
                # Version without middle initial
                variations.append(f"{parts[0]} {parts[-1]}")
    
    return variations


def expand_location_variations(location: str) -> List[str]:
    """
    Generate variations of location names for better matching.
    E.g., "Heidelberg, GER" -> ["Heidelberg, Germany", "Heidelberg Germany", "Heidelberg, GER"]
    """
    variations = [location]
    
    # Country code to full name mapping
    country_codes = {
        'GER': 'Germany',
        'USA': 'United States',
        'UK': 'United Kingdom',
        'FRA': 'France',
        'ITA': 'Italy',
        'ESP': 'Spain',
        'JPN': 'Japan',
        'CAN': 'Canada',
        'AUS': 'Australia',
        'BRA': 'Brazil',
        'MEX': 'Mexico',
        'CHN': 'China',
        'IND': 'India',
        'RUS': 'Russia',
    }
    
    # US state abbreviations
    us_states = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
    }
    
    # Check for comma-separated location format
    if ',' in location:
        parts = [p.strip() for p in location.split(',')]
        city = parts[0]
        region = parts[-1].upper() if len(parts) > 1 else ''
        
        # Expand country codes
        if region in country_codes:
            variations.append(f"{city}, {country_codes[region]}")
            variations.append(f"{city} {country_codes[region]}")
        
        # Expand state abbreviations
        if region in us_states:
            variations.append(f"{city}, {us_states[region]}")
            variations.append(f"{city} {us_states[region]}")
        
        # Also add lowercase state code variation
        if region.upper() in us_states:
            variations.append(f"{city}, {region.capitalize()}")
    
    return variations

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
