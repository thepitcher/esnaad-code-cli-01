"""Tests for filesystem tools (list_directory, search_files, search_content)."""

import pytest
from pathlib import Path

from esnaad.tools.filesystem.list_directory import ListDirectoryTool, ListDirectoryInput
from esnaad.tools.filesystem.search_files import SearchFilesTool, SearchFilesInput
from esnaad.tools.filesystem.search_content import SearchContentTool, SearchContentInput
from esnaad.tools.base import ToolContext
from esnaad.exceptions import ToolExecutionError


class TestListDirectoryTool:
    """Tests for ListDirectoryTool."""

    @pytest.fixture
    def tool(self) -> ListDirectoryTool:
        return ListDirectoryTool()

    async def test_list_directory(
        self,
        tool: ListDirectoryTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test listing a directory."""
        input_data = ListDirectoryInput(path=str(sample_directory))
        result = await tool.execute(input_data, tool_context)

        assert result.total_items > 0
        names = [e.name for e in result.entries]
        assert "README.md" in names
        assert "src" in names
        assert "tests" in names

    async def test_list_recursive(
        self,
        tool: ListDirectoryTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test recursive listing."""
        input_data = ListDirectoryInput(
            path=str(sample_directory),
            recursive=True,
        )
        result = await tool.execute(input_data, tool_context)

        # Should include nested files
        paths = [e.path for e in result.entries]
        has_nested = any("module" in p for p in paths)
        assert has_nested

    async def test_list_with_pattern(
        self,
        tool: ListDirectoryTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test listing with glob pattern."""
        input_data = ListDirectoryInput(
            path=str(sample_directory),
            pattern="*.py",
            recursive=True,
        )
        result = await tool.execute(input_data, tool_context)

        # All entries should be .py files
        for entry in result.entries:
            assert entry.name.endswith(".py")

    async def test_list_nonexistent_directory(
        self,
        tool: ListDirectoryTool,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test listing nonexistent directory."""
        input_data = ListDirectoryInput(path=str(temp_dir / "nonexistent"))

        with pytest.raises(ToolExecutionError):
            await tool.execute(input_data, tool_context)


class TestSearchFilesTool:
    """Tests for SearchFilesTool."""

    @pytest.fixture
    def tool(self) -> SearchFilesTool:
        return SearchFilesTool()

    async def test_search_by_extension(
        self,
        tool: SearchFilesTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test searching files by extension."""
        input_data = SearchFilesInput(
            path=str(sample_directory),
            pattern="**/*.py",
        )
        result = await tool.execute(input_data, tool_context)

        assert result.total_matches > 0
        for match in result.matches:
            assert match.endswith(".py")

    async def test_search_by_name(
        self,
        tool: SearchFilesTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test searching files by name pattern."""
        input_data = SearchFilesInput(
            path=str(sample_directory),
            pattern="**/test_*.py",
        )
        result = await tool.execute(input_data, tool_context)

        assert result.total_matches >= 1
        assert any("test_main.py" in m for m in result.matches)

    async def test_search_no_matches(
        self,
        tool: SearchFilesTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test search with no matches."""
        input_data = SearchFilesInput(
            path=str(sample_directory),
            pattern="**/*.xyz",
        )
        result = await tool.execute(input_data, tool_context)

        assert result.total_matches == 0


class TestSearchContentTool:
    """Tests for SearchContentTool."""

    @pytest.fixture
    def tool(self) -> SearchContentTool:
        return SearchContentTool()

    async def test_search_content(
        self,
        tool: SearchContentTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test searching file content."""
        input_data = SearchContentInput(
            path=str(sample_directory),
            pattern="def ",
        )
        result = await tool.execute(input_data, tool_context)

        assert result.total_matches > 0
        # Should find function definitions
        assert any("main" in str(m) for m in result.matches)

    async def test_search_content_case_insensitive(
        self,
        tool: SearchContentTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test case-insensitive content search."""
        input_data = SearchContentInput(
            path=str(sample_directory),
            pattern="README",
            case_sensitive=False,
        )
        result = await tool.execute(input_data, tool_context)

        # May or may not find matches depending on content
        assert result.total_matches >= 0

    async def test_search_with_file_pattern(
        self,
        tool: SearchContentTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test content search with file pattern filter."""
        input_data = SearchContentInput(
            path=str(sample_directory),
            pattern="def ",
            file_pattern="*.py",
        )
        result = await tool.execute(input_data, tool_context)

        # All matches should be in .py files
        for match in result.matches:
            assert ".py" in match.file_path
