"""
InfoPilot Explorer - Search Utilities
DuckDuckGo + Brave Search integration, protocol parsing, document classification
"""
import re
import os
import logging
import requests
from typing import List, Dict, Optional, Tuple

# Brave Search API Configuration
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")
BRAVE_SEARCH_BASE_URL = "https://api.search.brave.com/res/v1/web/search"

# Location patterns for geo-extraction
LOCATION_PATTERNS = {
    "New York": {"lat": 40.7128, "lng": -74.0060},
    "Los Angeles": {"lat": 34.0522, "lng": -118.2437},
    "Chicago": {"lat": 41.8781, "lng": -87.6298},
    "Houston": {"lat": 29.7604, "lng": -95.3698},
    "Phoenix": {"lat": 33.4484, "lng": -112.0740},
    "Philadelphia": {"lat": 39.9526, "lng": -75.1652},
    "San Antonio": {"lat": 29.4241, "lng": -98.4936},
    "San Diego": {"lat": 32.7157, "lng": -117.1611},
    "Dallas": {"lat": 32.7767, "lng": -96.7970},
    "San Francisco": {"lat": 37.7749, "lng": -122.4194},
    "Washington": {"lat": 38.9072, "lng": -77.0369},
    "Boston": {"lat": 42.3601, "lng": -71.0589},
    "Seattle": {"lat": 47.6062, "lng": -122.3321},
    "Denver": {"lat": 39.7392, "lng": -104.9903},
    "Atlanta": {"lat": 33.7490, "lng": -84.3880},
    "Miami": {"lat": 25.7617, "lng": -80.1918},
    "Brunswick": {"lat": 43.9145, "lng": -69.9653},
    "Portland": {"lat": 43.6591, "lng": -70.2568},
    "London": {"lat": 51.5074, "lng": -0.1278},
    "Paris": {"lat": 48.8566, "lng": 2.3522},
    "Tokyo": {"lat": 35.6762, "lng": 139.6503},
    "Sydney": {"lat": -33.8688, "lng": 151.2093},
    "Berlin": {"lat": 52.5200, "lng": 13.4050},
}


async def search_duckduckgo(query: str, max_results: int = 20) -> List[Dict]:
    """Search using DuckDuckGo via ddgs package."""
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "source": "DuckDuckGo"
                })
        logging.info(f"DuckDuckGo returned {len(results)} results for '{query}'")
        return results
    except Exception as e:
        logging.error(f"DuckDuckGo search error: {e}")
        return []


async def search_brave(query: str, max_results: int = 20) -> List[Dict]:
    """Search using Brave Search API (free tier: 2000 queries/month)."""
    if not BRAVE_SEARCH_API_KEY:
        logging.warning("Brave Search API key not configured, skipping Brave search")
        return []
    
    try:
        headers = {
            "X-Subscription-Token": BRAVE_SEARCH_API_KEY,
            "Accept": "application/json"
        }
        params = {
            "q": query,
            "count": min(max_results, 20),  # Brave API max is 20
            "country": "us",
            "search_lang": "en"
        }
        
        response = requests.get(
            BRAVE_SEARCH_BASE_URL,
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        web_results = data.get("web", {}).get("results", [])
        for r in web_results:
            results.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("description", ""),
                "source": "Brave"
            })
        
        logging.info(f"Brave Search returned {len(results)} results for '{query}'")
        return results
    except requests.exceptions.RequestException as e:
        logging.error(f"Brave Search API error: {e}")
        return []
    except Exception as e:
        logging.error(f"Brave Search error: {e}")
        return []


async def search_all_engines(query: str, max_results: int = 40, engine: str = "all") -> List[Dict]:
    """Search across all available search engines."""
    all_results = []
    
    # DuckDuckGo (free, no API key needed)
    ddg_results = await search_duckduckgo(query, max_results)
    all_results.extend(ddg_results)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r["url"] and r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_results.append(r)
    
    return unique_results[:max_results]


def parse_infojet_protocol(protocol: str) -> Dict:
    """Parse an InfoJet 2.0 protocol string into structured format."""
    protocol = protocol.replace(" and ", " & ")
    groups = []
    
    # Find groups in parentheses
    group_pattern = r'\(([^)]+)\)'
    matches = re.findall(group_pattern, protocol)
    
    for match in matches:
        words = [w.strip().lower() for w in re.split(r'\s+or\s+', match)]
        groups.append({
            "words": words,
            "operator": "or"
        })
    
    # Check for modifiers
    include_all = "+" in protocol
    exclude = "^" in protocol
    
    # Find total groups (for determining match logic)
    total_groups = len(groups)
    
    return {
        "groups": groups,
        "include_all": include_all,
        "exclude": exclude,
        "total_groups": total_groups,
        "raw": protocol
    }


def content_matches_protocol(content: str, protocol: str) -> Tuple[bool, int]:
    """Check if content matches a protocol. Returns (matches, score)."""
    parsed = parse_infojet_protocol(protocol)
    content_lower = content.lower()
    
    total_groups = len(parsed["groups"])
    matched_groups = 0
    total_score = 0
    
    for group in parsed["groups"]:
        group_matched = False
        for word in group["words"]:
            if word in content_lower:
                group_matched = True
                total_score += content_lower.count(word)
                break
        if group_matched:
            matched_groups += 1
    
    # Include all modifier (+): require all groups to match
    if parsed["include_all"]:
        if matched_groups == total_groups and total_groups > 0:
            return True, total_score
        return False, 0
    
    # Standard matching: at least one group must match
    if matched_groups == total_groups and total_groups > 0:
        return True, total_score
    elif matched_groups > 0:
        return True, total_score // 2
    
    return False, 0


def classify_document_type(content: str, title: str, admin_settings: Dict) -> str:
    """Classify document type based on content analysis."""
    content_lower = content.lower()
    title_lower = title.lower()
    full_text = f"{title_lower} {content_lower}"
    word_count = len(content.split())
    
    # PhD Informative
    phd_terms = ["ph.d", "phd", "d.phil", "dr.", "dissertation", "thesis", "peer-reviewed"]
    phd_count = sum(1 for term in phd_terms if term in content_lower)
    if phd_count >= admin_settings.get("phd_min_occurrences", 3) and word_count >= admin_settings.get("phd_min_words", 1500):
        return "PhD Informative"
    
    # News Article
    news_terms = ["breaking", "reported", "according to", "officials said", "news"]
    if any(term in content_lower for term in news_terms):
        return "News Article"
    
    # Blog
    blog_terms = ["posted by", "comment", "subscribe", "blog", "my opinion"]
    if any(term in content_lower for term in blog_terms):
        return "Blog"
    
    # Forum
    forum_terms = ["replied", "thread", "forum", "discussion", "member since"]
    if any(term in content_lower for term in forum_terms):
        return "Forum"
    
    # Personal Report detection
    i_count = content_lower.count(" i ") + content_lower.count("i'm") + content_lower.count("i've")
    if i_count >= admin_settings.get("personal_report_min_i", 3) and word_count >= admin_settings.get("personal_report_min_words", 75):
        return "Personal Report (Collected)"
    
    # Default to Informative
    return "Informative"


def extract_location(content: str) -> Optional[Dict[str, float]]:
    """Extract location from content."""
    content_lower = content.lower()
    for city, coords in LOCATION_PATTERNS.items():
        if city.lower() in content_lower:
            return {"lat": coords["lat"], "lng": coords["lng"], "city": city}
    return None
