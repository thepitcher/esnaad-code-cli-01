"""Tests for preference manager."""

import pytest
from pathlib import Path

from esnaad.state.preferences import PreferenceManager


class TestPreferenceManager:
    """Tests for PreferenceManager."""

    @pytest.fixture
    def manager(self, temp_dir: Path) -> PreferenceManager:
        """Create a preference manager."""
        return PreferenceManager(config_dir=temp_dir)

    async def test_set_and_get_preference(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test setting and getting preferences."""
        await manager.set_preference(
            category="coding_style",
            key="indent_size",
            value=4,
        )

        value = await manager.get_preference("coding_style", "indent_size")
        assert value == 4

    async def test_get_nonexistent_preference(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test getting nonexistent preference."""
        value = await manager.get_preference("nonexistent", "key")
        assert value is None

    async def test_get_with_default(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test getting with default value."""
        value = await manager.get_preference("nonexistent", "key", default="default")
        assert value == "default"

    async def test_persistence(
        self,
        temp_dir: Path,
    ) -> None:
        """Test that preferences persist to disk."""
        # Create manager and set preference
        manager1 = PreferenceManager(config_dir=temp_dir)
        await manager1.set_preference("test", "key", "value")

        # Create new manager instance
        manager2 = PreferenceManager(config_dir=temp_dir)
        value = await manager2.get_preference("test", "key")

        assert value == "value"

    async def test_learn_from_clarification(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test learning from clarification responses."""
        await manager.learn_from_clarification(
            question_id="prefer_typescript",
            response=True,
            context="language preference",
        )

        value = await manager.get_preference("clarifications", "prefer_typescript")
        assert value is True

    async def test_confidence_tracking(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test confidence tracking."""
        await manager.set_preference(
            category="test",
            key="key",
            value="value",
            confidence=0.8,
        )

        result = await manager.get_preference_with_confidence("test", "key")
        assert result is not None
        value, confidence = result
        assert value == "value"
        assert confidence == 0.8

    async def test_suggest_default(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test suggesting default values."""
        # High confidence preference
        await manager.set_preference("test", "high", "value1", confidence=0.9)
        # Low confidence preference
        await manager.set_preference("test", "low", "value2", confidence=0.3)

        # Should suggest high confidence
        high_suggestion = await manager.suggest_default("test", "high", min_confidence=0.5)
        assert high_suggestion == "value1"

        # Should not suggest low confidence
        low_suggestion = await manager.suggest_default("test", "low", min_confidence=0.5)
        assert low_suggestion is None

    async def test_get_category(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test getting all preferences in a category."""
        await manager.set_preference("category1", "key1", "value1")
        await manager.set_preference("category1", "key2", "value2")
        await manager.set_preference("category2", "key3", "value3")

        cat1 = await manager.get_category("category1")
        assert cat1 == {"key1": "value1", "key2": "value2"}

    async def test_clear_category(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test clearing a category."""
        await manager.set_preference("test", "key1", "value1")
        await manager.set_preference("test", "key2", "value2")

        await manager.clear_category("test")

        cat = await manager.get_category("test")
        assert cat == {}

    async def test_clear_all(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test clearing all preferences."""
        await manager.set_preference("cat1", "key1", "value1")
        await manager.set_preference("cat2", "key2", "value2")

        await manager.clear_all()

        assert await manager.get_preference("cat1", "key1") is None
        assert await manager.get_preference("cat2", "key2") is None

    async def test_export_import(
        self,
        manager: PreferenceManager,
    ) -> None:
        """Test exporting and importing preferences."""
        await manager.set_preference("test", "key", "value")

        exported = await manager.export_preferences()

        # Clear and reimport
        await manager.clear_all()
        await manager.import_preferences(exported)

        value = await manager.get_preference("test", "key")
        assert value == "value"
