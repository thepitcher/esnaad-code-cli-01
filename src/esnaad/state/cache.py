"""Result caching for tool outputs."""

import asyncio
import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class CacheEntry:
    """A single cache entry with expiration."""

    def __init__(self, value: Any, ttl: int = 300) -> None:
        """
        Create a cache entry.

        Args:
            value: Value to cache
            ttl: Time to live in seconds
        """
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.hits = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.expires_at

    def touch(self) -> None:
        """Record a cache hit."""
        self.hits += 1


class ResultCache:
    """
    LRU cache for tool results with TTL support.

    Caches tool outputs to avoid repeated expensive operations.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,
    ) -> None:
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(tool_name: str, arguments: dict[str, Any]) -> str:
        """Create a cache key from tool name and arguments."""
        # Sort arguments for consistent hashing
        args_str = json.dumps(arguments, sort_keys=True, default=str)
        content = f"{tool_name}:{args_str}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    async def get(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[bool, Any]:
        """
        Get a cached result.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tuple of (hit, value) - hit is True if found and valid
        """
        key = self._make_key(tool_name, arguments)

        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                if entry.is_expired():
                    # Remove expired entry
                    del self._cache[key]
                    self._misses += 1
                    return False, None

                # Move to end (most recently used)
                self._cache.move_to_end(key)
                entry.touch()
                self._hits += 1
                return True, entry.value

            self._misses += 1
            return False, None

    async def set(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """
        Cache a result.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            value: Result to cache
            ttl: Optional custom TTL in seconds
        """
        key = self._make_key(tool_name, arguments)
        ttl = ttl or self._default_ttl

        async with self._lock:
            # Add or update entry
            self._cache[key] = CacheEntry(value, ttl)
            self._cache.move_to_end(key)

            # Evict oldest if over capacity
            while len(self._cache) > self._max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug("Evicted cache entry", key=evicted_key[:8])

    async def invalidate(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            tool_name: Tool name to invalidate
            arguments: Optional specific arguments (invalidates all if None)

        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            if arguments:
                key = self._make_key(tool_name, arguments)
                if key in self._cache:
                    del self._cache[key]
                    return 1
                return 0
            else:
                # Invalidate all entries for this tool
                # Note: This is O(n) but rarely called
                keys_to_delete = [
                    k for k in self._cache.keys()
                    # We can't easily filter by tool name with hashed keys
                    # So this invalidates everything
                ]
                for key in keys_to_delete:
                    del self._cache[key]
                return len(keys_to_delete)

    async def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            return count

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired = [
                k for k, v in self._cache.items()
                if v.is_expired()
            ]
            for key in expired:
                del self._cache[key]
            return len(expired)

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_hits = sum(e.hits for e in self._cache.values())
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
                "total_entry_hits": total_hits,
            }
