"""Run command tool implementation."""

import asyncio
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class RunCommandInput(BaseModel):
    """Input schema for run_command tool."""

    command: str = Field(
        description="Shell command to execute",
    )
    working_directory: str | None = Field(
        default=None,
        description="Directory to run the command in (default: current)",
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Command timeout in seconds",
    )
    capture_stderr: bool = Field(
        default=True,
        description="Include stderr in output",
    )


class RunCommandOutput(BaseModel):
    """Output schema for run_command tool."""

    stdout: str = Field(description="Command stdout output")
    stderr: str = Field(description="Command stderr output")
    exit_code: int = Field(description="Command exit code")
    success: bool = Field(description="Whether command succeeded (exit code 0)")
    timed_out: bool = Field(description="Whether command timed out")


@register_tool
class RunCommandTool(BaseTool[RunCommandInput, RunCommandOutput]):
    """
    Execute a shell command.

    Runs commands with timeout and captures output.
    Use with caution - commands can modify the system.
    """

    name = "run_command"
    description = (
        "Execute a shell command and return its output. "
        "Commands run in the working directory with a configurable timeout. "
        "Use for running builds, tests, git commands, etc. "
        "Avoid long-running or interactive commands."
    )
    parallel_safe = False  # Depends on the command
    requires_lock = False

    @property
    def input_schema(self) -> type[RunCommandInput]:
        return RunCommandInput

    @property
    def output_schema(self) -> type[RunCommandOutput]:
        return RunCommandOutput

    async def execute(
        self,
        input_data: RunCommandInput,
        context: ToolContext,
    ) -> RunCommandOutput:
        """Execute shell command."""
        # Determine working directory
        if input_data.working_directory:
            cwd = context.resolve_path(input_data.working_directory)
        else:
            cwd = context.working_directory

        # Validate working directory
        if not cwd.exists():
            from esnaad.exceptions import ToolExecutionError
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Working directory not found: {cwd}",
            )

        # Determine shell
        if sys.platform == "win32":
            shell = True
            command = input_data.command
        else:
            shell = True
            command = input_data.command

        # Create subprocess
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=input_data.timeout,
                )
                timed_out = False

            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                stdout, stderr = await process.communicate()
                timed_out = True

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Truncate if too long
            max_output = context.settings.tools.max_output_chars
            if len(stdout_str) > max_output:
                stdout_str = stdout_str[:max_output] + "\n... [output truncated]"
            if len(stderr_str) > max_output:
                stderr_str = stderr_str[:max_output] + "\n... [output truncated]"

            return RunCommandOutput(
                stdout=stdout_str,
                stderr=stderr_str,
                exit_code=process.returncode or -1,
                success=process.returncode == 0 and not timed_out,
                timed_out=timed_out,
            )

        except Exception as e:
            from esnaad.exceptions import ToolExecutionError
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Failed to execute command: {e}",
                original=e,
            ) from e
