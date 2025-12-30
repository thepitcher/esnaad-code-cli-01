"""Tests for file tools (read, write, edit)."""

import pytest
from pathlib import Path

from esnaad.tools.file.read_file import ReadFileTool, ReadFileInput
from esnaad.tools.file.write_file import WriteFileTool, WriteFileInput
from esnaad.tools.file.edit_file import EditFileTool, EditFileInput
from esnaad.tools.base import ToolContext
from esnaad.exceptions import ToolExecutionError


class TestReadFileTool:
    """Tests for ReadFileTool."""

    @pytest.fixture
    def tool(self) -> ReadFileTool:
        return ReadFileTool()

    async def test_read_entire_file(
        self,
        tool: ReadFileTool,
        tool_context: ToolContext,
        sample_file: Path,
    ) -> None:
        """Test reading an entire file."""
        input_data = ReadFileInput(file_path=str(sample_file))
        result = await tool.execute(input_data, tool_context)

        assert result.total_lines == 5
        assert result.lines_read == 5
        assert not result.truncated
        assert "Line 1" in result.content
        assert "Line 5" in result.content

    async def test_read_with_offset(
        self,
        tool: ReadFileTool,
        tool_context: ToolContext,
        sample_file: Path,
    ) -> None:
        """Test reading with offset."""
        input_data = ReadFileInput(file_path=str(sample_file), offset=3, limit=2)
        result = await tool.execute(input_data, tool_context)

        assert result.lines_read == 2
        assert "Line 3" in result.content
        assert "Line 4" in result.content
        assert "Line 1" not in result.content

    async def test_read_nonexistent_file(
        self,
        tool: ReadFileTool,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test reading a nonexistent file."""
        input_data = ReadFileInput(file_path=str(temp_dir / "nonexistent.txt"))

        with pytest.raises(ToolExecutionError) as exc_info:
            await tool.execute(input_data, tool_context)

        assert "not found" in str(exc_info.value).lower()

    async def test_read_directory_fails(
        self,
        tool: ReadFileTool,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test that reading a directory fails."""
        input_data = ReadFileInput(file_path=str(temp_dir))

        with pytest.raises(ToolExecutionError) as exc_info:
            await tool.execute(input_data, tool_context)

        assert "not a file" in str(exc_info.value).lower()

    def test_openai_schema(self, tool: ReadFileTool) -> None:
        """Test OpenAI schema generation."""
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "read_file"
        assert "parameters" in schema["function"]
        assert "file_path" in schema["function"]["parameters"]["properties"]


class TestWriteFileTool:
    """Tests for WriteFileTool."""

    @pytest.fixture
    def tool(self) -> WriteFileTool:
        return WriteFileTool()

    async def test_write_new_file(
        self,
        tool: WriteFileTool,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test writing a new file."""
        file_path = temp_dir / "new_file.txt"
        input_data = WriteFileInput(
            file_path=str(file_path),
            content="Hello, World!",
        )

        result = await tool.execute(input_data, tool_context)

        assert result.success
        assert file_path.exists()
        assert file_path.read_text() == "Hello, World!"

    async def test_overwrite_existing_file(
        self,
        tool: WriteFileTool,
        tool_context: ToolContext,
        sample_file: Path,
    ) -> None:
        """Test overwriting an existing file."""
        input_data = WriteFileInput(
            file_path=str(sample_file),
            content="New content",
        )

        result = await tool.execute(input_data, tool_context)

        assert result.success
        assert sample_file.read_text() == "New content"

    async def test_write_creates_directories(
        self,
        tool: WriteFileTool,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test that write creates parent directories."""
        file_path = temp_dir / "new_dir" / "subdir" / "file.txt"
        input_data = WriteFileInput(
            file_path=str(file_path),
            content="Nested content",
        )

        result = await tool.execute(input_data, tool_context)

        assert result.success
        assert file_path.exists()
        assert file_path.read_text() == "Nested content"


class TestEditFileTool:
    """Tests for EditFileTool."""

    @pytest.fixture
    def tool(self) -> EditFileTool:
        return EditFileTool()

    async def test_simple_replacement(
        self,
        tool: EditFileTool,
        tool_context: ToolContext,
        sample_file: Path,
    ) -> None:
        """Test simple text replacement."""
        input_data = EditFileInput(
            file_path=str(sample_file),
            old_string="Line 2",
            new_string="Modified Line 2",
        )

        result = await tool.execute(input_data, tool_context)

        assert result.success
        content = sample_file.read_text()
        assert "Modified Line 2" in content
        assert "Line 2\n" not in content

    async def test_replace_all(
        self,
        tool: EditFileTool,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test replace_all option."""
        file_path = temp_dir / "repeat.txt"
        file_path.write_text("foo bar foo baz foo")

        input_data = EditFileInput(
            file_path=str(file_path),
            old_string="foo",
            new_string="qux",
            replace_all=True,
        )

        result = await tool.execute(input_data, tool_context)

        assert result.success
        assert result.replacements == 3
        assert file_path.read_text() == "qux bar qux baz qux"

    async def test_nonexistent_string_fails(
        self,
        tool: EditFileTool,
        tool_context: ToolContext,
        sample_file: Path,
    ) -> None:
        """Test that editing nonexistent string fails."""
        input_data = EditFileInput(
            file_path=str(sample_file),
            old_string="Nonexistent text",
            new_string="New text",
        )

        with pytest.raises(ToolExecutionError) as exc_info:
            await tool.execute(input_data, tool_context)

        assert "not found" in str(exc_info.value).lower()

    async def test_ambiguous_replacement_fails(
        self,
        tool: EditFileTool,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test that ambiguous replacement fails without replace_all."""
        file_path = temp_dir / "repeat.txt"
        file_path.write_text("foo bar foo baz foo")

        input_data = EditFileInput(
            file_path=str(file_path),
            old_string="foo",
            new_string="qux",
            replace_all=False,
        )

        with pytest.raises(ToolExecutionError) as exc_info:
            await tool.execute(input_data, tool_context)

        assert "ambiguous" in str(exc_info.value).lower() or "multiple" in str(exc_info.value).lower()
