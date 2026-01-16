"""
InfoPilot Explorer - Web Search Service
Handles web searching across multiple sources
"""
import asyncio
import httpx
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config import logger

# User agent for web requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class WebSearchService:
    """Web search aggregation service"""
    
    @staticmethod
    async def search_duckduckgo(query: str, num_results: int = 100) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo HTML scraping"""
        results = []
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                url = f"https://html.duckduckgo.com/html/?q={query}"
                response = await client.get(url, headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml"
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for result in soup.select('.result'):
                        title_elem = result.select_one('.result__title a')
                        snippet_elem = result.select_one('.result__snippet')
                        
                        if title_elem:
                            href = title_elem.get('href', '')
                            if 'uddg=' in href:
                                import urllib.parse
                                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                                actual_url = parsed.get('uddg', [href])[0]
                            else:
                                actual_url = href
                            
                            if actual_url and actual_url.startswith('http'):
                                results.append({
                                    "title": title_elem.get_text(strip=True),
                                    "url": actual_url,
                                    "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                                    "source": "duckduckgo"
                                })
                        
                        if len(results) >= num_results:
                            break
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        return results
    
    @staticmethod
    async def search_bing_scrape(query: str, num_results: int = 80) -> List[Dict[str, Any]]:
        """Search using Bing HTML scraping"""
        results = []
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                url = f"https://www.bing.com/search?q={query}&count={min(50, num_results)}"
                response = await client.get(url, headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml"
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for li in soup.select('li.b_algo'):
                        title_elem = li.select_one('h2 a')
                        snippet_elem = li.select_one('.b_caption p')
                        
                        if title_elem:
                            href = title_elem.get('href', '')
                            if href.startswith('http'):
                                results.append({
                                    "title": title_elem.get_text(strip=True),
                                    "url": href,
                                    "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                                    "source": "bing"
                                })
                        
                        if len(results) >= num_results:
                            break
        except Exception as e:
            logger.error(f"Bing search error: {e}")
        
        return results
    
    @staticmethod
    async def fetch_page_content(url: str) -> Dict[str, Any]:
        """Fetch and extract content from a webpage"""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": USER_AGENT})
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # Extract title
                    title = soup.title.string if soup.title else ""
                    
                    # Extract meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    description = meta_desc['content'] if meta_desc else ""
                    
                    # Extract main content
                    content = soup.get_text(separator=' ', strip=True)[:5000]
                    
                    return {
                        "title": title,
                        "description": description,
                        "content": content
                    }
        except Exception as e:
            logger.debug(f"Content fetch error for {url}: {e}")
        
        return {"title": "", "description": "", "content": ""}
    
    @staticmethod
    async def search(query: str, num_results: int = 200, max_pages: int = 99) -> List[Dict[str, Any]]:
        """
        Perform web search using multiple sources
        Returns deduplicated results with content enrichment
        Supports up to 99 pages of results (configurable via admin panel)
        """
        all_results = []
        seen_urls = set()
        
        try:
            # Run primary searches in parallel with increased limits
            ddg_task = WebSearchService.search_duckduckgo(query, min(100, num_results))
            bing_task = WebSearchService.search_bing_scrape(query, min(80, num_results))
            
            ddg_results, bing_results = await asyncio.gather(
                ddg_task, 
                bing_task,
                return_exceptions=True
            )
            
            # Process DuckDuckGo results
            if isinstance(ddg_results, list):
                for result in ddg_results:
                    if result["url"] not in seen_urls:
                        seen_urls.add(result["url"])
                        all_results.append(result)
                logger.info(f"DuckDuckGo returned {len(ddg_results)} results")
            else:
                logger.error(f"DuckDuckGo error: {ddg_results}")
            
            # Process Bing results
            if isinstance(bing_results, list):
                for result in bing_results:
                    if result["url"] not in seen_urls:
                        seen_urls.add(result["url"])
                        all_results.append(result)
                logger.info(f"Bing returned {len(bing_results)} results")
            else:
                logger.error(f"Bing error: {bing_results}")
            
        except Exception as e:
            logger.error(f"Search aggregation error: {e}")
        
        # Fetch content for results to improve protocol matching
        if all_results:
            batch_size = 15
            max_content_fetch = min(len(all_results), 50)
            for i in range(0, max_content_fetch, batch_size):
                batch = all_results[i:i+batch_size]
                tasks = [WebSearchService.fetch_page_content(r["url"]) for r in batch]
                
                try:
                    contents = await asyncio.gather(*tasks, return_exceptions=True)
                    for j, content in enumerate(contents):
                        idx = i + j
                        if isinstance(content, dict) and idx < len(all_results):
                            if content.get("title"):
                                all_results[idx]["title"] = content["title"]
                            if content.get("content"):
                                all_results[idx]["content"] = content["content"]
                            if content.get("description"):
                                all_results[idx]["snippet"] = content["description"]
                except Exception as e:
                    logger.debug(f"Content enrichment error: {e}")
        
        logger.info(f"Search for '{query}' returned {len(all_results)} results")
        return all_results[:num_results]
    
    @staticmethod
    def classify_article_type(url: str, title: str, content: str = "") -> str:
        """
        Classify the type of article based on URL and content.
        
        Document Types:
        - PhD Informative: Academic content written/reviewed by PhD holders
        - Personal Report (Organic): First-hand accounts and personal experiences
        - Personal Report (Collected): Aggregated/curated personal reports
        - News Article: Current events and journalism
        - Academic Paper: Scholarly research and publications
        - Government: Official government documents
        - Wiki: Wikipedia and wiki-based content
        - Blog Post: Personal blogs and opinion pieces
        - Forum: Discussion boards and Q&A sites
        - Video: Video content
        - Webpage: General web pages
        """
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:1000] if content else ""
        combined = f"{url_lower} {title_lower} {content_lower}"
        
        # PhD Informative detection - academic credentialed content
        phd_indicators = ['ph.d.', 'phd', 'd.phil.', 'dr.', 'professor', 'research by', 
                         'peer-reviewed', 'peer reviewed', 'published in', 'journal of',
                         'university study', 'clinical study', 'scientific study']
        phd_count = sum(1 for ind in phd_indicators if ind in combined)
        if phd_count >= 2:
            return 'PhD Informative'
        
        # Personal Report detection
        personal_indicators = ['my experience', 'i personally', 'in my opinion', 'my story',
                              'first-hand', 'firsthand', 'personal account', 'i found that',
                              'i discovered', 'my journey', 'my review', 'personal report']
        personal_count = sum(1 for ind in personal_indicators if ind in combined)
        
        # Collected/Aggregated report detection
        collected_indicators = ['collected', 'compilation', 'aggregated', 'curated',
                               'testimonials', 'user reports', 'customer experiences',
                               'reviews collected', 'gathered from', 'roundup']
        collected_count = sum(1 for ind in collected_indicators if ind in combined)
        
        if collected_count >= 2 or (collected_count >= 1 and personal_count >= 1):
            return 'Personal Report (Collected)'
        if personal_count >= 2:
            return 'Personal Report (Organic)'
        
        # Standard classifications
        if any(x in url_lower for x in ['wikipedia.org', 'wiki']):
            return 'Wiki'
        elif any(x in url_lower for x in ['youtube.com', 'vimeo.com', 'video', 'dailymotion']):
            return 'Video'
        elif any(x in url_lower for x in ['.gov', 'government']):
            return 'Government'
        elif any(x in url_lower for x in ['.edu', 'academic', 'journal', 'research', 'scholar', 'arxiv', 'pubmed']):
            return 'Academic Paper'
        elif any(x in url_lower for x in ['forum', 'reddit.com', 'quora.com', 'stackexchange', 'stackoverflow']):
            return 'Forum'
        elif any(x in url_lower for x in ['blog', 'medium.com', 'wordpress', 'substack']):
            return 'Blog Post'
        elif any(x in combined for x in ['breaking news', 'latest news', 'news article', 'reported today']):
            return 'News Article'
        elif any(x in url_lower for x in ['.pdf']):
            return 'PDF Document'
        elif any(x in url_lower for x in ['.doc', '.docx']):
            return 'MS Word Document'
        elif any(x in combined for x in ['news', 'article', 'report']):
            return 'News Article'
        else:
            return 'Webpage'
    
    @staticmethod
    def extract_root_domain(url: str) -> str:
        """Extract the root domain from a URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
