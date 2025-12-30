"""Tests for result cache."""

import pytest
import asyncio

from esnaad.state.cache import ResultCache


class TestResultCache:
    """Tests for ResultCache."""

    @pytest.fixture
    def cache(self) -> ResultCache:
        """Create a result cache."""
        return ResultCache(max_size=100, ttl_seconds=60)

    async def test_set_and_get(self, cache: ResultCache) -> None:
        """Test setting and getting cached values."""
        await cache.set("tool1", {"arg": "value"}, "result1")

        hit, value = await cache.get("tool1", {"arg": "value"})
        assert hit is True
        assert value == "result1"

    async def test_cache_miss(self, cache: ResultCache) -> None:
        """Test cache miss."""
        hit, value = await cache.get("nonexistent", {})
        assert hit is False
        assert value is None

    async def test_different_args_different_results(
        self,
        cache: ResultCache,
    ) -> None:
        """Test that different arguments produce different cache entries."""
        await cache.set("tool1", {"arg": "value1"}, "result1")
        await cache.set("tool1", {"arg": "value2"}, "result2")

        hit1, value1 = await cache.get("tool1", {"arg": "value1"})
        hit2, value2 = await cache.get("tool1", {"arg": "value2"})

        assert hit1 is True
        assert value1 == "result1"
        assert hit2 is True
        assert value2 == "result2"

    async def test_invalidate(self, cache: ResultCache) -> None:
        """Test invalidating cache entries."""
        await cache.set("tool1", {"arg": "value"}, "result1")
        await cache.invalidate("tool1", {"arg": "value"})

        hit, value = await cache.get("tool1", {"arg": "value"})
        assert hit is False

    async def test_clear(self, cache: ResultCache) -> None:
        """Test clearing the cache."""
        await cache.set("tool1", {"arg": "value1"}, "result1")
        await cache.set("tool2", {"arg": "value2"}, "result2")
        await cache.clear()

        hit1, _ = await cache.get("tool1", {"arg": "value1"})
        hit2, _ = await cache.get("tool2", {"arg": "value2"})

        assert hit1 is False
        assert hit2 is False

    async def test_max_size(self) -> None:
        """Test that cache respects max size."""
        cache = ResultCache(max_size=3, ttl_seconds=60)

        await cache.set("tool1", {}, "result1")
        await cache.set("tool2", {}, "result2")
        await cache.set("tool3", {}, "result3")
        await cache.set("tool4", {}, "result4")  # Should evict oldest

        # One of the first entries should be evicted
        size = await cache.size()
        assert size <= 3

    async def test_stats(self, cache: ResultCache) -> None:
        """Test cache statistics."""
        await cache.set("tool1", {}, "result1")

        # Cache hit
        await cache.get("tool1", {})
        # Cache miss
        await cache.get("tool2", {})

        stats = await cache.stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1


class TestResultCacheTTL:
    """Tests for cache TTL."""

    async def test_expired_entry(self) -> None:
        """Test that expired entries are not returned."""
        cache = ResultCache(max_size=100, ttl_seconds=0.1)  # 100ms TTL

        await cache.set("tool1", {}, "result1")

        # Should hit immediately
        hit1, _ = await cache.get("tool1", {})
        assert hit1 is True

        # Wait for expiry
        await asyncio.sleep(0.2)

        # Should miss after expiry
        hit2, _ = await cache.get("tool1", {})
        assert hit2 is False
