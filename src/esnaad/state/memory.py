"""Key-value memory store for cross-agent communication."""

import asyncio
from collections import OrderedDict
from typing import Any
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class MemoryStore:
    """
    Thread-safe async key-value store for cross-agent memory.

    Supports:
    - Basic get/set operations
    - LRU eviction when max size reached
    - Namespaced keys for agent isolation
    """

    def __init__(self, max_size: int = 1000) -> None:
        """
        Initialize the memory store.

        Args:
            max_size: Maximum number of entries before eviction
        """
        self._store: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._max_size = max_size

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the store.

        Args:
            key: Key to retrieve
            default: Default value if not found

        Returns:
            Stored value or default
        """
        async with self._lock:
            if key in self._store:
                value, _ = self._store[key]
                # Move to end (most recently accessed)
                self._store.move_to_end(key)
                return value
            return default

    async def set(self, key: str, value: Any) -> None:
        """
        Set a value in the store.

        Args:
            key: Key to set
            value: Value to store
        """
        async with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, datetime.now())

            # Evict oldest if over capacity
            while len(self._store) > self._max_size:
                evicted_key, _ = self._store.popitem(last=False)
                logger.debug("Evicted memory entry", key=evicted_key)

    async def delete(self, key: str) -> bool:
        """
        Delete a key from the store.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def has(self, key: str) -> bool:
        """Check if a key exists."""
        async with self._lock:
            return key in self._store

    async def keys(self, prefix: str | None = None) -> list[str]:
        """
        Get all keys, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of matching keys
        """
        async with self._lock:
            all_keys = list(self._store.keys())
            if prefix:
                return [k for k in all_keys if k.startswith(prefix)]
            return all_keys

    async def clear(self, prefix: str | None = None) -> int:
        """
        Clear entries, optionally only those with a prefix.

        Args:
            prefix: Optional prefix to filter deletion

        Returns:
            Number of entries deleted
        """
        async with self._lock:
            if prefix:
                keys_to_delete = [k for k in self._store.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self._store[key]
                return len(keys_to_delete)
            else:
                count = len(self._store)
                self._store.clear()
                return count

    async def size(self) -> int:
        """Get the number of entries in the store."""
        async with self._lock:
            return len(self._store)

    # Namespace helpers for agent isolation

    @staticmethod
    def namespaced_key(namespace: str, key: str) -> str:
        """Create a namespaced key."""
        return f"{namespace}:{key}"

    async def get_namespaced(
        self,
        namespace: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a value with namespace."""
        full_key = self.namespaced_key(namespace, key)
        return await self.get(full_key, default)

    async def set_namespaced(
        self,
        namespace: str,
        key: str,
        value: Any,
    ) -> None:
        """Set a value with namespace."""
        full_key = self.namespaced_key(namespace, key)
        await self.set(full_key, value)

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all entries in a namespace."""
        return await self.clear(prefix=f"{namespace}:")
