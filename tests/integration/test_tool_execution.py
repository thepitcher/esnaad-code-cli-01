"""Integration tests for tool execution."""

import pytest
from pathlib import Path

from esnaad.tools.registry import ToolRegistry
from esnaad.tools.base import ToolContext
from esnaad.config.settings import Settings


class TestToolExecution:
    """Integration tests for tool execution flow."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Initialize tool registry for tests."""
        ToolRegistry.clear()
        ToolRegistry.initialize()

    async def test_read_write_edit_flow(
        self,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test complete file operation flow."""
        # Get tools
        write_tool = ToolRegistry.get_or_raise("write_file")
        read_tool = ToolRegistry.get_or_raise("read_file")
        edit_tool = ToolRegistry.get_or_raise("edit_file")

        file_path = str(temp_dir / "test.py")

        # Write initial file
        write_result = await write_tool.validate_and_execute(
            {"file_path": file_path, "content": "def hello():\n    print('Hello')\n"},
            tool_context,
        )
        assert write_result.success

        # Read file
        read_result = await read_tool.validate_and_execute(
            {"file_path": file_path},
            tool_context,
        )
        assert "def hello" in read_result.content

        # Edit file
        edit_result = await edit_tool.validate_and_execute(
            {
                "file_path": file_path,
                "old_string": "print('Hello')",
                "new_string": "print('Hello, World!')",
            },
            tool_context,
        )
        assert edit_result.success

        # Verify edit
        read_result2 = await read_tool.validate_and_execute(
            {"file_path": file_path},
            tool_context,
        )
        assert "Hello, World!" in read_result2.content

    async def test_filesystem_search_flow(
        self,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test filesystem search operations."""
        list_tool = ToolRegistry.get_or_raise("list_directory")
        search_files_tool = ToolRegistry.get_or_raise("search_files")
        search_content_tool = ToolRegistry.get_or_raise("search_content")

        # List directory
        list_result = await list_tool.validate_and_execute(
            {"path": str(sample_directory)},
            tool_context,
        )
        assert list_result.total_items > 0

        # Search for Python files
        search_result = await search_files_tool.validate_and_execute(
            {"path": str(sample_directory), "pattern": "**/*.py"},
            tool_context,
        )
        assert search_result.total_matches > 0

        # Search for function definitions
        content_result = await search_content_tool.validate_and_execute(
            {"path": str(sample_directory), "pattern": "def "},
            tool_context,
        )
        assert content_result.total_matches > 0

    async def test_shell_command_execution(
        self,
        tool_context: ToolContext,
        temp_dir: Path,
    ) -> None:
        """Test shell command execution."""
        import sys

        shell_tool = ToolRegistry.get_or_raise("run_command")

        # Simple echo command
        if sys.platform == "win32":
            cmd = "echo test"
        else:
            cmd = "echo test"

        result = await shell_tool.validate_and_execute(
            {"command": cmd, "cwd": str(temp_dir)},
            tool_context,
        )
        assert result.exit_code == 0
        assert "test" in result.stdout


class TestToolValidation:
    """Tests for tool input validation."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Initialize tool registry for tests."""
        ToolRegistry.clear()
        ToolRegistry.initialize()

    async def test_read_file_validation(
        self,
        tool_context: ToolContext,
    ) -> None:
        """Test read_file input validation."""
        from esnaad.exceptions import ToolValidationError

        read_tool = ToolRegistry.get_or_raise("read_file")

        # Missing required field
        with pytest.raises(ToolValidationError):
            await read_tool.validate_and_execute({}, tool_context)

        # Invalid offset
        with pytest.raises(ToolValidationError):
            await read_tool.validate_and_execute(
                {"file_path": "/test.txt", "offset": -1},
                tool_context,
            )

    async def test_edit_file_validation(
        self,
        tool_context: ToolContext,
    ) -> None:
        """Test edit_file input validation."""
        from esnaad.exceptions import ToolValidationError

        edit_tool = ToolRegistry.get_or_raise("edit_file")

        # Missing required fields
        with pytest.raises(ToolValidationError):
            await edit_tool.validate_and_execute(
                {"file_path": "/test.txt"},
                tool_context,
            )


class TestToolSchemas:
    """Tests for tool OpenAI schema generation."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Initialize tool registry for tests."""
        ToolRegistry.clear()
        ToolRegistry.initialize()

    def test_all_tools_have_valid_schemas(self) -> None:
        """Test that all tools generate valid OpenAI schemas."""
        tools = ToolRegistry.get_all()
        assert len(tools) > 0

        for tool in tools:
            schema = tool.to_openai_schema()

            # Basic structure
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]

            # Parameters should be an object
            params = schema["function"]["parameters"]
            assert params["type"] == "object"

    def test_schemas_json_serializable(self) -> None:
        """Test that all schemas are JSON serializable."""
        import json

        schemas = ToolRegistry.get_openai_schemas()

        # Should not raise
        json_str = json.dumps(schemas)
        assert len(json_str) > 0

        # Should round-trip
        parsed = json.loads(json_str)
        assert len(parsed) == len(schemas)
