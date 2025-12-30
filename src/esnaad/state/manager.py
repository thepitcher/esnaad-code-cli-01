"""Central state manager for Esnaad Code."""

from pathlib import Path
from typing import Any, Literal
from contextlib import asynccontextmanager

import structlog

from esnaad.state.file_locks import FileLockManager
from esnaad.state.memory import MemoryStore
from esnaad.state.cache import ResultCache

logger = structlog.get_logger(__name__)


class StateManager:
    """
    Central coordinator for shared state across agents.

    Provides:
    - File locking for concurrent access
    - Key-value memory store
    - Result caching
    """

    def __init__(
        self,
        working_directory: Path,
        cache_max_size: int = 1000,
        memory_max_size: int = 1000,
    ) -> None:
        """
        Initialize the state manager.

        Args:
            working_directory: Base directory for file operations
            cache_max_size: Maximum cache entries
            memory_max_size: Maximum memory entries
        """
        self.cwd = working_directory
        self.file_locks = FileLockManager()
        self.memory = MemoryStore(max_size=memory_max_size)
        self.cache = ResultCache(max_size=cache_max_size)

        logger.info(
            "State manager initialized",
            working_directory=str(working_directory),
        )

    @asynccontextmanager
    async def acquire_file_lock(
        self,
        path: Path | str,
        mode: Literal["read", "write"],
    ):
        """
        Acquire a file lock.

        Args:
            path: File path to lock
            mode: "read" for shared, "write" for exclusive

        Yields:
            None (lock is held during context)
        """
        async with self.file_locks.acquire(path, mode):
            yield

    async def get_memory(self, key: str, default: Any = None) -> Any:
        """Get a value from memory store."""
        return await self.memory.get(key, default)

    async def set_memory(self, key: str, value: Any) -> None:
        """Set a value in memory store."""
        await self.memory.set(key, value)

    async def delete_memory(self, key: str) -> bool:
        """Delete a value from memory store."""
        return await self.memory.delete(key)

    async def get_cached(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[bool, Any]:
        """
        Get a cached tool result.

        Returns:
            Tuple of (hit, value)
        """
        return await self.cache.get(tool_name, arguments)

    async def set_cached(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Cache a tool result."""
        await self.cache.set(tool_name, arguments, value, ttl)

    async def invalidate_cache(
        self,
        tool_name: str | None = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            tool_name: Optional tool name to invalidate (all if None)

        Returns:
            Number of entries invalidated
        """
        if tool_name:
            return await self.cache.invalidate(tool_name)
        else:
            return await self.cache.clear()

    async def cleanup(self) -> dict[str, int]:
        """
        Cleanup expired cache entries.

        Returns:
            Dict with cleanup statistics
        """
        expired = await self.cache.cleanup_expired()
        return {"cache_expired": expired}

    async def stats(self) -> dict[str, Any]:
        """Get state manager statistics."""
        cache_stats = await self.cache.stats()
        memory_size = await self.memory.size()

        return {
            "working_directory": str(self.cwd),
            "cache": cache_stats,
            "memory_size": memory_size,
        }

    # Agent namespace helpers

    async def get_agent_memory(
        self,
        agent_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a value from agent-specific memory."""
        return await self.memory.get_namespaced(f"agent:{agent_id}", key, default)

    async def set_agent_memory(
        self,
        agent_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Set a value in agent-specific memory."""
        await self.memory.set_namespaced(f"agent:{agent_id}", key, value)

    async def clear_agent_memory(self, agent_id: str) -> int:
        """Clear all memory for an agent."""
        return await self.memory.clear_namespace(f"agent:{agent_id}")
