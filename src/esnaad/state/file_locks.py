"""Async file locking mechanism."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Literal
from collections import defaultdict

import structlog

logger = structlog.get_logger(__name__)


class FileLockManager:
    """
    Async-compatible file lock manager with read/write distinction.

    Implements a readers-writer lock pattern:
    - Multiple readers can hold the lock simultaneously
    - A writer has exclusive access
    - Writers wait for all readers to release
    - New readers wait if a writer is waiting (to prevent writer starvation)
    """

    def __init__(self) -> None:
        self._meta_lock = asyncio.Lock()
        self._locks: dict[Path, asyncio.Lock] = {}
        self._readers: dict[Path, int] = defaultdict(int)
        self._writer_waiting: dict[Path, bool] = defaultdict(bool)
        self._write_lock: dict[Path, asyncio.Lock] = {}

    @asynccontextmanager
    async def acquire(
        self,
        path: Path | str,
        mode: Literal["read", "write"],
    ) -> AsyncGenerator[None, None]:
        """
        Acquire a file lock in the specified mode.

        Args:
            path: File path to lock
            mode: "read" for shared access, "write" for exclusive

        Yields:
            None (lock is held during context)
        """
        path = Path(path).resolve()

        if mode == "write":
            await self._acquire_write(path)
            try:
                yield
            finally:
                await self._release_write(path)
        else:
            await self._acquire_read(path)
            try:
                yield
            finally:
                await self._release_read(path)

    async def _ensure_lock(self, path: Path) -> None:
        """Ensure lock structures exist for a path."""
        async with self._meta_lock:
            if path not in self._locks:
                self._locks[path] = asyncio.Lock()
                self._write_lock[path] = asyncio.Lock()

    async def _acquire_write(self, path: Path) -> None:
        """Acquire exclusive write lock."""
        await self._ensure_lock(path)

        # Signal that a writer is waiting
        async with self._meta_lock:
            self._writer_waiting[path] = True

        # Acquire write lock (exclusive)
        await self._write_lock[path].acquire()

        # Wait for all readers to finish
        while True:
            async with self._meta_lock:
                if self._readers[path] == 0:
                    break
            await asyncio.sleep(0.01)

        logger.debug("Acquired write lock", path=str(path))

    async def _release_write(self, path: Path) -> None:
        """Release write lock."""
        async with self._meta_lock:
            self._writer_waiting[path] = False

        self._write_lock[path].release()
        logger.debug("Released write lock", path=str(path))

    async def _acquire_read(self, path: Path) -> None:
        """Acquire shared read lock."""
        await self._ensure_lock(path)

        # Wait if a writer is waiting or writing
        while True:
            async with self._meta_lock:
                if not self._writer_waiting[path] and not self._write_lock[path].locked():
                    self._readers[path] += 1
                    break
            await asyncio.sleep(0.01)

        logger.debug(
            "Acquired read lock",
            path=str(path),
            readers=self._readers[path],
        )

    async def _release_read(self, path: Path) -> None:
        """Release read lock."""
        async with self._meta_lock:
            self._readers[path] -= 1

        logger.debug(
            "Released read lock",
            path=str(path),
            readers=self._readers[path],
        )

    async def is_locked(self, path: Path | str) -> bool:
        """Check if a path is currently locked."""
        path = Path(path).resolve()

        async with self._meta_lock:
            if path not in self._locks:
                return False

            has_readers = self._readers[path] > 0
            has_writer = self._write_lock.get(path, asyncio.Lock()).locked()

            return has_readers or has_writer

    async def get_lock_status(self, path: Path | str) -> dict:
        """Get detailed lock status for a path."""
        path = Path(path).resolve()

        async with self._meta_lock:
            return {
                "path": str(path),
                "readers": self._readers.get(path, 0),
                "writer_waiting": self._writer_waiting.get(path, False),
                "write_locked": self._write_lock.get(path, asyncio.Lock()).locked(),
            }
