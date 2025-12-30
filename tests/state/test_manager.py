"""Tests for state manager."""

import pytest
from pathlib import Path

from esnaad.state.manager import StateManager


class TestStateManager:
    """Tests for StateManager."""

    @pytest.fixture
    async def manager(self, temp_dir: Path) -> StateManager:
        """Create a state manager."""
        return StateManager(working_directory=temp_dir)

    async def test_initialization(
        self,
        manager: StateManager,
        temp_dir: Path,
    ) -> None:
        """Test state manager initialization."""
        assert manager.working_directory == temp_dir

    async def test_memory_operations(
        self,
        manager: StateManager,
    ) -> None:
        """Test memory store operations through manager."""
        await manager.set_memory("key1", "value1")
        value = await manager.get_memory("key1")
        assert value == "value1"

    async def test_agent_memory(
        self,
        manager: StateManager,
    ) -> None:
        """Test agent-specific memory operations."""
        await manager.set_agent_memory("agent-001", "task_count", 5)
        value = await manager.get_agent_memory("agent-001", "task_count")
        assert value == 5

        await manager.clear_agent_memory("agent-001")
        value = await manager.get_agent_memory("agent-001", "task_count")
        assert value is None

    async def test_cache_operations(
        self,
        manager: StateManager,
    ) -> None:
        """Test cache operations through manager."""
        await manager.set_cached("tool1", {"arg": "val"}, "result")

        hit, value = await manager.get_cached("tool1", {"arg": "val"})
        assert hit is True
        assert value == "result"

    async def test_file_lock(
        self,
        manager: StateManager,
        temp_dir: Path,
    ) -> None:
        """Test file locking through manager."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("content")

        async with manager.acquire_file_lock(str(file_path), "write"):
            file_path.write_text("modified")

        assert file_path.read_text() == "modified"

    async def test_cleanup(
        self,
        manager: StateManager,
    ) -> None:
        """Test cleanup method."""
        await manager.set_memory("key", "value")
        await manager.cleanup()

        # Memory should be cleared
        value = await manager.get_memory("key")
        assert value is None

    async def test_shared_data(
        self,
        manager: StateManager,
    ) -> None:
        """Test shared data between agents."""
        # Set data from one "agent"
        await manager.set_memory("shared:result", {"status": "complete"})

        # Read from another "agent"
        data = await manager.get_memory("shared:result")
        assert data == {"status": "complete"}
