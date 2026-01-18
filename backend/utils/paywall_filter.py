"""
InfoPilot Explorer - Paywall Filter
Filters out websites that require subscriptions or paywalls
"""
import re
from urllib.parse import urlparse
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

# Known paywall/subscription domains
# This list includes major news sites with paywalls, academic journals, and premium content sites
PAYWALL_DOMAINS: Set[str] = {
    # Major News Sites with Hard Paywalls
    "nytimes.com",
    "wsj.com",
    "washingtonpost.com",
    "ft.com",
    "economist.com",
    "newyorker.com",
    "theatlantic.com",
    "bloomberg.com",
    "barrons.com",
    "thetimes.co.uk",
    "telegraph.co.uk",
    "theinformation.com",
    "businessinsider.com",
    "seekingalpha.com",
    "hbr.org",
    "harvardbuinessreview.org",
    "foreignpolicy.com",
    "foreignaffairs.com",
    "stratfor.com",
    "thedailybeast.com",
    "bostonglobe.com",
    "latimes.com",
    "chicagotribune.com",
    "sfchronicle.com",
    "denverpost.com",
    "dallasnews.com",
    "seattletimes.com",
    "miamiherald.com",
    "baltimoresun.com",
    "startribune.com",
    "inquirer.com",
    "newsday.com",
    "theathletic.com",
    "sportico.com",
    
    # Academic/Research Journals
    "nature.com",
    "science.org",
    "sciencemag.org",
    "cell.com",
    "thelancet.com",
    "nejm.org",
    "bmj.com",
    "jamanetwork.com",
    "annals.org",
    "pnas.org",
    "aaas.org",
    "ieee.org",
    "acm.org",
    "springer.com",
    "link.springer.com",
    "wiley.com",
    "onlinelibrary.wiley.com",
    "tandfonline.com",
    "sagepub.com",
    "journals.sagepub.com",
    "elsevier.com",
    "sciencedirect.com",
    "jstor.org",
    "oxfordacademics.com",
    "academic.oup.com",
    "cambridge.org",
    "journals.cambridge.org",
    "annualreviews.org",
    "iopscience.iop.org",
    "aps.org",
    "journals.aps.org",
    "aip.org",
    "pubs.acs.org",
    "rsc.org",
    "pubs.rsc.org",
    
    # Financial/Business Premium
    "morningstar.com",
    "fool.com",
    "investopedia.com",  # Some premium content
    "marketwatch.com",
    "investors.com",
    "kiplinger.com",
    "forbes.com",  # Some premium content
    "fortune.com",
    "inc.com",
    "fastcompany.com",
    
    # Tech News with Paywalls
    "wired.com",
    "arstechnica.com",
    "theverge.com",  # Some premium content
    "protocol.com",
    "techcrunch.com",  # Some premium
    "venturebeat.com",
    "zdnet.com",
    
    # Magazine/Premium Content
    "vanityfair.com",
    "vogue.com",
    "gq.com",
    "esquire.com",
    "rollingstone.com",
    "billboard.com",
    "variety.com",
    "hollywoodreporter.com",
    "deadline.com",
    "vulture.com",
    "slate.com",
    "salon.com",
    "thedailybeast.com",
    "nationalgeographic.com",
    "smithsonianmag.com",
    "scientificamerican.com",
    "newscientist.com",
    "discovermagazine.com",
    
    # Cooking/Lifestyle Paywalls
    "bonappetit.com",
    "epicurious.com",
    "foodandwine.com",
    "saveur.com",
    "cooksillustrated.com",
    "americastestkitchen.com",
    
    # International Paywalls
    "spiegel.de",
    "zeit.de",
    "sueddeutsche.de",
    "faz.net",
    "lemonde.fr",
    "lefigaro.fr",
    "liberation.fr",
    "elpais.com",
    "elmundo.es",
    "corriere.it",
    "repubblica.it",
    "nikkei.com",
    "asahi.com",
    "yomiuri.co.jp",
    "scmp.com",
    "straitstimes.com",
    "theaustralian.com.au",
    "afr.com",
    "smh.com.au",
    "theage.com.au",
    "globeandmail.com",
    "nationalpost.com",
    "torstar.com",
    
    # Legal/Professional
    "law360.com",
    "lexisnexis.com",
    "westlaw.com",
    "courtlistener.com",
    "pacer.gov",
    
    # Stock/Trading (Premium)
    "tradingview.com",
    "benzinga.com",
    "zacks.com",
    "tipranks.com",
    "stockcharts.com",
    "finviz.com",
    
    # Data/Statistics (Premium)
    "statista.com",
    "ibisworld.com",
    "euromonitor.com",
    "mintel.com",
    "gartner.com",
    "forrester.com",
    "mckinsey.com",
    "bcg.com",
    "bain.com",
    "deloitte.com",
    "pwc.com",
    "ey.com",
    "kpmg.com",
}

# Patterns that indicate paywalled content in URLs
PAYWALL_URL_PATTERNS = [
    r"/subscribe",
    r"/subscription",
    r"/premium",
    r"/member-only",
    r"/members-only",
    r"/exclusive",
    r"/paid-content",
    r"/paywalled",
    r"/restricted",
    r"/login-required",
    r"/register-to-read",
    r"/unlock",
    r"/full-access",
]

# Patterns in titles that indicate paywall
PAYWALL_TITLE_PATTERNS = [
    r"subscribe to read",
    r"subscription required",
    r"premium content",
    r"members only",
    r"sign in to continue",
    r"login to read",
    r"unlock this article",
    r"exclusive for subscribers",
    r"register to read",
    r"full article available to",
]


def extract_domain(url: str) -> str:
    """Extract the base domain from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    except Exception:
        return ""


def is_paywall_domain(url: str) -> bool:
    """Check if a URL belongs to a known paywall domain."""
    domain = extract_domain(url)
    if not domain:
        return False
    
    # Check exact match
    if domain in PAYWALL_DOMAINS:
        return True
    
    # Check if it's a subdomain of a paywall domain
    for paywall_domain in PAYWALL_DOMAINS:
        if domain.endswith("." + paywall_domain):
            return True
    
    return False


def has_paywall_url_pattern(url: str) -> bool:
    """Check if URL contains patterns indicating paywalled content."""
    url_lower = url.lower()
    for pattern in PAYWALL_URL_PATTERNS:
        if re.search(pattern, url_lower):
            return True
    return False


def has_paywall_title_pattern(title: str) -> bool:
    """Check if title contains patterns indicating paywalled content."""
    if not title:
        return False
    
    title_lower = title.lower()
    for pattern in PAYWALL_TITLE_PATTERNS:
        if re.search(pattern, title_lower):
            return True
    return False


def is_paywalled(url: str, title: str = "", snippet: str = "") -> bool:
    """
    Comprehensive check if content is behind a paywall.
    
    Args:
        url: The URL to check
        title: Optional title of the content
        snippet: Optional snippet/description
    
    Returns:
        True if content appears to be paywalled, False otherwise
    """
    # Check domain
    if is_paywall_domain(url):
        return True
    
    # Check URL patterns
    if has_paywall_url_pattern(url):
        return True
    
    # Check title patterns
    if has_paywall_title_pattern(title):
        return True
    
    # Check snippet for paywall indicators
    if snippet and has_paywall_title_pattern(snippet):
        return True
    
    return False


def filter_paywalled_results(results: List[Dict]) -> List[Dict]:
    """
    Filter out paywalled results from a list of search results.
    
    Args:
        results: List of search result dictionaries with 'url', 'title', 'snippet' keys
    
    Returns:
        Filtered list with paywalled content removed
    """
    filtered = []
    removed_count = 0
    
    for result in results:
        url = result.get("url", "")
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        
        if is_paywalled(url, title, snippet):
            removed_count += 1
            logger.debug(f"Filtered paywalled content: {url}")
        else:
            filtered.append(result)
    
    if removed_count > 0:
        logger.info(f"Filtered {removed_count} paywalled results from {len(results)} total")
    
    return filtered


def get_paywall_stats() -> Dict:
    """Get statistics about paywall filtering."""
    return {
        "total_blocked_domains": len(PAYWALL_DOMAINS),
        "url_patterns_count": len(PAYWALL_URL_PATTERNS),
        "title_patterns_count": len(PAYWALL_TITLE_PATTERNS),
        "sample_domains": list(PAYWALL_DOMAINS)[:10]
    }
