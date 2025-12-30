"""Tests for memory store."""

import pytest

from esnaad.state.memory import MemoryStore


class TestMemoryStore:
    """Tests for MemoryStore."""

    @pytest.fixture
    def store(self) -> MemoryStore:
        """Create a memory store."""
        return MemoryStore()

    async def test_set_and_get(self, store: MemoryStore) -> None:
        """Test setting and getting values."""
        await store.set("key1", "value1")
        value = await store.get("key1")
        assert value == "value1"

    async def test_get_nonexistent(self, store: MemoryStore) -> None:
        """Test getting nonexistent key."""
        value = await store.get("nonexistent")
        assert value is None

    async def test_get_with_default(self, store: MemoryStore) -> None:
        """Test getting with default value."""
        value = await store.get("nonexistent", default="default")
        assert value == "default"

    async def test_delete(self, store: MemoryStore) -> None:
        """Test deleting values."""
        await store.set("key1", "value1")
        result = await store.delete("key1")
        assert result is True
        assert await store.get("key1") is None

    async def test_delete_nonexistent(self, store: MemoryStore) -> None:
        """Test deleting nonexistent key."""
        result = await store.delete("nonexistent")
        assert result is False

    async def test_exists(self, store: MemoryStore) -> None:
        """Test checking existence."""
        await store.set("key1", "value1")
        assert await store.exists("key1") is True
        assert await store.exists("nonexistent") is False

    async def test_clear(self, store: MemoryStore) -> None:
        """Test clearing all values."""
        await store.set("key1", "value1")
        await store.set("key2", "value2")
        await store.clear()
        assert await store.get("key1") is None
        assert await store.get("key2") is None

    async def test_keys(self, store: MemoryStore) -> None:
        """Test getting all keys."""
        await store.set("key1", "value1")
        await store.set("key2", "value2")
        keys = await store.keys()
        assert "key1" in keys
        assert "key2" in keys

    async def test_namespaced_keys(self, store: MemoryStore) -> None:
        """Test namespace prefix."""
        await store.set("agent:001:key1", "value1")
        await store.set("agent:001:key2", "value2")
        await store.set("agent:002:key1", "value3")

        keys = await store.keys(prefix="agent:001:")
        assert len(keys) == 2
        assert "agent:001:key1" in keys
        assert "agent:001:key2" in keys

    async def test_complex_values(self, store: MemoryStore) -> None:
        """Test storing complex values."""
        await store.set("dict", {"nested": {"value": 42}})
        await store.set("list", [1, 2, 3])

        dict_val = await store.get("dict")
        list_val = await store.get("list")

        assert dict_val == {"nested": {"value": 42}}
        assert list_val == [1, 2, 3]
