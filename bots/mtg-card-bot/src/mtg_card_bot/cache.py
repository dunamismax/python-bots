"""Card cache implementation for the MTG Card Bot."""

import asyncio
import time
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar('T')


class CacheStats:
    """Statistics for cache performance."""

    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self.size = 0
        self.max_size = 0
        self.evictions = 0
        self.ttl_seconds = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class CacheItem:
    """A single item in the cache with expiration."""

    def __init__(self, value: Any, ttl_seconds: float) -> None:
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 1
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if this cache item has expired."""
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()


class CardCache:
    """LRU cache with TTL for card data."""

    def __init__(self, ttl_seconds: float = 3600.0, max_size: int = 1000) -> None:
        self._cache: Dict[str, CacheItem] = {}
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._stats = CacheStats()
        self._stats.max_size = max_size
        self._stats.ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get an item from the cache."""
        async with self._lock:
            # Clean expired items first
            await self._cleanup_expired()
            
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            item = self._cache[key]
            if item.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                return None
            
            item.touch()
            self._stats.hits += 1
            return item.value

    async def set(self, key: str, value: Any) -> None:
        """Set an item in the cache."""
        async with self._lock:
            # Clean expired items first
            await self._cleanup_expired()
            
            # If at capacity, evict least recently used item
            if len(self._cache) >= self._max_size and key not in self._cache:
                await self._evict_lru()
            
            self._cache[key] = CacheItem(value, self._ttl_seconds)
            self._stats.size = len(self._cache)

    async def get_or_set(self, key: str, factory: Callable[[str], Any]) -> Any:
        """Get an item from cache, or set it using the factory function if not found."""
        # First try to get from cache
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Not in cache, use factory to create the value
        value = await factory(key) if asyncio.iscoroutinefunction(factory) else factory(key)
        await self.set(key, value)
        return value

    async def clear(self) -> None:
        """Clear all items from the cache."""
        async with self._lock:
            self._cache.clear()
            self._stats.size = 0

    def stats(self) -> CacheStats:
        """Get current cache statistics."""
        self._stats.size = len(self._cache)
        return self._stats

    async def _cleanup_expired(self) -> None:
        """Remove expired items from the cache."""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items()
            if current_time - item.created_at > self._ttl_seconds
        ]
        
        for key in expired_keys:
            del self._cache[key]

    async def _evict_lru(self) -> None:
        """Evict the least recently used item."""
        if not self._cache:
            return
        
        # Find the item with the oldest last_accessed time
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self._stats.evictions += 1