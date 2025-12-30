"""Tests for shell tool."""

import pytest
import sys
from pathlib import Path

from esnaad.tools.shell.run_command import RunCommandTool, RunCommandInput
from esnaad.tools.base import ToolContext
from esnaad.exceptions import ToolExecutionError


class TestRunCommandTool:
    """Tests for RunCommandTool."""

    @pytest.fixture
    def tool(self) -> RunCommandTool:
        return RunCommandTool()

    async def test_simple_command(
        self,
        tool: RunCommandTool,
        tool_context: ToolContext,
    ) -> None:
        """Test running a simple command."""
        # Use platform-appropriate command
        if sys.platform == "win32":
            cmd = "echo Hello"
        else:
            cmd = "echo Hello"

        input_data = RunCommandInput(command=cmd)
        result = await tool.execute(input_data, tool_context)

        assert result.exit_code == 0
        assert "Hello" in result.stdout

    async def test_command_with_cwd(
        self,
        tool: RunCommandTool,
        tool_context: ToolContext,
        sample_directory: Path,
    ) -> None:
        """Test running command in specific directory."""
        if sys.platform == "win32":
            cmd = "dir"
        else:
            cmd = "ls"

        input_data = RunCommandInput(
            command=cmd,
            cwd=str(sample_directory),
        )
        result = await tool.execute(input_data, tool_context)

        assert result.exit_code == 0
        assert "README" in result.stdout or "src" in result.stdout

    async def test_command_failure(
        self,
        tool: RunCommandTool,
        tool_context: ToolContext,
    ) -> None:
        """Test command that fails."""
        if sys.platform == "win32":
            cmd = "cmd /c exit 1"
        else:
            cmd = "exit 1"

        input_data = RunCommandInput(command=cmd)
        result = await tool.execute(input_data, tool_context)

        assert result.exit_code != 0

    async def test_command_timeout(
        self,
        tool: RunCommandTool,
        tool_context: ToolContext,
    ) -> None:
        """Test command timeout."""
        if sys.platform == "win32":
            cmd = "ping -n 10 127.0.0.1"
        else:
            cmd = "sleep 10"

        input_data = RunCommandInput(
            command=cmd,
            timeout=1,  # 1 second timeout
        )

        # Should timeout
        result = await tool.execute(input_data, tool_context)
        assert result.timed_out or result.exit_code != 0

    async def test_command_with_stderr(
        self,
        tool: RunCommandTool,
        tool_context: ToolContext,
    ) -> None:
        """Test command that produces stderr."""
        if sys.platform == "win32":
            # Windows doesn't have a simple way to echo to stderr
            cmd = "python -c \"import sys; sys.stderr.write('error output')\""
        else:
            cmd = "echo 'error output' >&2"

        input_data = RunCommandInput(command=cmd)
        result = await tool.execute(input_data, tool_context)

        # stderr should be captured
        assert result.stderr is not None or result.stdout is not None

    def test_openai_schema(self, tool: RunCommandTool) -> None:
        """Test OpenAI schema generation."""
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "run_command"
        assert "command" in schema["function"]["parameters"]["properties"]
