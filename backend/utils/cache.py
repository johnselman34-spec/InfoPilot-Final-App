"""
InfoPilot Explorer - Simple In-Memory Cache
Lightweight caching for frequently accessed data
"""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache with default TTL in seconds."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if datetime.now() > entry["expires_at"]:
                del self._cache[key]
                return None
            
            return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        async with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl or self._default_ttl)
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now()
            }
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cached data."""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "total_entries": len(self._cache),
            "default_ttl": self._default_ttl
        }


# Global cache instances
search_cache = SimpleCache(default_ttl=600)      # 10 minutes for search results
leaderboard_cache = SimpleCache(default_ttl=300) # 5 minutes for leaderboards
marketplace_cache = SimpleCache(default_ttl=180) # 3 minutes for marketplace
engine_status_cache = SimpleCache(default_ttl=60) # 1 minute for engine status


async def cached_leaderboard():
    """Get leaderboard with caching."""
    cache_key = "leaderboard_global"
    
    cached = await leaderboard_cache.get(cache_key)
    if cached:
        logger.debug("Leaderboard served from cache")
        return cached
    
    from utils.db_optimization import get_leaderboard_optimized
    result = await get_leaderboard_optimized()
    
    await leaderboard_cache.set(cache_key, result)
    return result


async def cached_marketplace(category: str = None):
    """Get marketplace protocols with caching."""
    cache_key = f"marketplace_{category or 'all'}"
    
    cached = await marketplace_cache.get(cache_key)
    if cached:
        logger.debug(f"Marketplace served from cache: {cache_key}")
        return cached
    
    from utils.db_optimization import get_marketplace_protocols_optimized
    result = await get_marketplace_protocols_optimized(category)
    
    await marketplace_cache.set(cache_key, result)
    return result


async def invalidate_marketplace_cache():
    """Invalidate marketplace cache when data changes."""
    await marketplace_cache.clear()


async def invalidate_leaderboard_cache():
    """Invalidate leaderboard cache when data changes."""
    await leaderboard_cache.clear()
