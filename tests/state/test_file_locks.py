"""Tests for file lock manager."""

import pytest
import asyncio
from pathlib import Path

from esnaad.state.file_locks import FileLockManager


class TestFileLockManager:
    """Tests for FileLockManager."""

    @pytest.fixture
    def manager(self) -> FileLockManager:
        """Create a file lock manager."""
        return FileLockManager()

    async def test_read_lock(
        self,
        manager: FileLockManager,
        temp_dir: Path,
    ) -> None:
        """Test acquiring read lock."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("content")

        async with manager.read_lock(str(file_path)):
            # Should be able to read
            content = file_path.read_text()
            assert content == "content"

    async def test_write_lock(
        self,
        manager: FileLockManager,
        temp_dir: Path,
    ) -> None:
        """Test acquiring write lock."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("original")

        async with manager.write_lock(str(file_path)):
            file_path.write_text("modified")

        assert file_path.read_text() == "modified"

    async def test_multiple_readers(
        self,
        manager: FileLockManager,
        temp_dir: Path,
    ) -> None:
        """Test that multiple readers can access simultaneously."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("content")

        read_count = 0

        async def reader():
            nonlocal read_count
            async with manager.read_lock(str(file_path)):
                read_count += 1
                await asyncio.sleep(0.1)
                return file_path.read_text()

        # Start multiple readers concurrently
        results = await asyncio.gather(reader(), reader(), reader())

        assert all(r == "content" for r in results)
        assert read_count == 3

    async def test_writer_blocks_readers(
        self,
        manager: FileLockManager,
        temp_dir: Path,
    ) -> None:
        """Test that writer blocks readers."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("original")

        events = []

        async def writer():
            async with manager.write_lock(str(file_path)):
                events.append("write_start")
                await asyncio.sleep(0.1)
                file_path.write_text("modified")
                events.append("write_end")

        async def reader():
            await asyncio.sleep(0.05)  # Small delay to ensure writer starts first
            async with manager.read_lock(str(file_path)):
                events.append("read")
                return file_path.read_text()

        # Writer should complete before reader gets access
        await asyncio.gather(writer(), reader())

        # Read should happen after write completes
        assert events.index("write_end") < events.index("read")

    async def test_is_locked(
        self,
        manager: FileLockManager,
        temp_dir: Path,
    ) -> None:
        """Test checking if file is locked."""
        file_path = str(temp_dir / "test.txt")

        assert not manager.is_locked(file_path)

        async with manager.write_lock(file_path):
            assert manager.is_locked(file_path)

        assert not manager.is_locked(file_path)

    async def test_release_all(
        self,
        manager: FileLockManager,
        temp_dir: Path,
    ) -> None:
        """Test releasing all locks."""
        file1 = str(temp_dir / "file1.txt")
        file2 = str(temp_dir / "file2.txt")

        # Acquire locks (but don't release through context manager for this test)
        lock1 = manager._get_or_create_lock(file1)
        lock2 = manager._get_or_create_lock(file2)

        await lock1.acquire()
        await lock2.acquire()

        assert manager.is_locked(file1)
        assert manager.is_locked(file2)

        # Release all
        await manager.release_all()

        # Locks should be cleared
        assert len(manager._locks) == 0
