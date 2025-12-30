"""Tests for RulesLoader."""

import pytest
from pathlib import Path

from esnaad.config.rules import RulesLoader
from esnaad.config.constants import RULES_FILE_NAME


class TestRulesLoader:
    """Tests for RulesLoader class."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before and after each test."""
        RulesLoader.clear_cache()
        yield
        RulesLoader.clear_cache()

    @pytest.fixture
    def rules_content(self) -> str:
        """Sample rules content."""
        return """# Project Rules

## Guidelines

- Always write tests
- Use type hints
- Follow PEP 8
"""

    @pytest.fixture
    def rules_file(self, temp_dir: Path, rules_content: str) -> Path:
        """Create a rules file with content."""
        rules_path = temp_dir / RULES_FILE_NAME
        rules_path.write_text(rules_content, encoding="utf-8")
        return rules_path

    @pytest.mark.asyncio
    async def test_load_rules_success(self, temp_dir: Path, rules_file: Path, rules_content: str):
        """Test loading rules from existing file."""
        rules = await RulesLoader.load_rules(temp_dir)

        assert rules is not None
        assert "Project Rules" in rules
        assert "Always write tests" in rules
        assert rules == rules_content.strip()

    @pytest.mark.asyncio
    async def test_load_rules_missing_file(self, temp_dir: Path):
        """Test loading rules when file doesn't exist."""
        rules = await RulesLoader.load_rules(temp_dir)

        assert rules is None

    @pytest.mark.asyncio
    async def test_load_rules_empty_file(self, temp_dir: Path):
        """Test loading rules from empty file."""
        rules_path = temp_dir / RULES_FILE_NAME
        rules_path.write_text("", encoding="utf-8")

        rules = await RulesLoader.load_rules(temp_dir)

        assert rules is None

    @pytest.mark.asyncio
    async def test_load_rules_whitespace_only(self, temp_dir: Path):
        """Test loading rules from file with only whitespace."""
        rules_path = temp_dir / RULES_FILE_NAME
        rules_path.write_text("   \n\n\t  \n", encoding="utf-8")

        rules = await RulesLoader.load_rules(temp_dir)

        assert rules is None

    @pytest.mark.asyncio
    async def test_load_rules_caching(self, temp_dir: Path, rules_file: Path):
        """Test that rules are cached."""
        # First load
        rules1 = await RulesLoader.load_rules(temp_dir)

        # Modify file
        rules_file.write_text("Modified content", encoding="utf-8")

        # Second load should return cached version
        rules2 = await RulesLoader.load_rules(temp_dir)

        assert rules1 == rules2
        assert "Project Rules" in rules2  # Original content

    @pytest.mark.asyncio
    async def test_load_rules_force_reload(self, temp_dir: Path, rules_file: Path):
        """Test force reload bypasses cache."""
        # First load
        await RulesLoader.load_rules(temp_dir)

        # Modify file
        rules_file.write_text("Modified content", encoding="utf-8")

        # Force reload
        rules = await RulesLoader.load_rules(temp_dir, force_reload=True)

        assert "Modified content" in rules

    def test_load_rules_sync(self, temp_dir: Path, rules_file: Path, rules_content: str):
        """Test synchronous rules loading."""
        rules = RulesLoader.load_rules_sync(temp_dir)

        assert rules is not None
        assert "Project Rules" in rules
        assert rules == rules_content.strip()

    def test_load_rules_sync_missing_file(self, temp_dir: Path):
        """Test sync loading when file doesn't exist."""
        rules = RulesLoader.load_rules_sync(temp_dir)

        assert rules is None

    def test_load_rules_sync_caching(self, temp_dir: Path, rules_file: Path):
        """Test sync loading uses cache."""
        # First load
        rules1 = RulesLoader.load_rules_sync(temp_dir)

        # Modify file
        rules_file.write_text("New content", encoding="utf-8")

        # Second load should return cached version
        rules2 = RulesLoader.load_rules_sync(temp_dir)

        assert rules1 == rules2

    def test_clear_cache_specific(self, temp_dir: Path, rules_file: Path):
        """Test clearing cache for specific directory."""
        # Load to cache
        RulesLoader.load_rules_sync(temp_dir)
        assert RulesLoader.is_cached(temp_dir)

        # Clear specific
        RulesLoader.clear_cache(temp_dir)
        assert not RulesLoader.is_cached(temp_dir)

    def test_clear_cache_all(self, temp_dir: Path, rules_file: Path):
        """Test clearing entire cache."""
        # Load to cache
        RulesLoader.load_rules_sync(temp_dir)
        assert RulesLoader.is_cached(temp_dir)

        # Clear all
        RulesLoader.clear_cache()
        assert not RulesLoader.is_cached(temp_dir)

    def test_is_cached_false_initially(self, temp_dir: Path):
        """Test is_cached returns False before loading."""
        assert not RulesLoader.is_cached(temp_dir)

    def test_is_cached_true_after_load(self, temp_dir: Path, rules_file: Path):
        """Test is_cached returns True after loading."""
        RulesLoader.load_rules_sync(temp_dir)
        assert RulesLoader.is_cached(temp_dir)

    def test_is_cached_true_for_missing_file(self, temp_dir: Path):
        """Test is_cached returns True even when file was missing (None cached)."""
        RulesLoader.load_rules_sync(temp_dir)
        assert RulesLoader.is_cached(temp_dir)

    def test_get_rules_path(self, temp_dir: Path):
        """Test get_rules_path returns correct path."""
        path = RulesLoader.get_rules_path(temp_dir)
        assert path == temp_dir / RULES_FILE_NAME

    @pytest.mark.asyncio
    async def test_cache_stores_none_for_missing(self, temp_dir: Path):
        """Test that cache stores None for missing files."""
        # Load (file doesn't exist)
        rules1 = await RulesLoader.load_rules(temp_dir)
        assert rules1 is None
        assert RulesLoader.is_cached(temp_dir)

        # Create file
        (temp_dir / RULES_FILE_NAME).write_text("New rules", encoding="utf-8")

        # Should still return None from cache
        rules2 = await RulesLoader.load_rules(temp_dir)
        assert rules2 is None

        # Force reload should find the new file
        rules3 = await RulesLoader.load_rules(temp_dir, force_reload=True)
        assert rules3 == "New rules"
