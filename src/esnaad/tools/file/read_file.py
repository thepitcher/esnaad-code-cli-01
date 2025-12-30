"""Read file tool implementation."""

from pathlib import Path
from typing import Any

import aiofiles
from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool
from esnaad.config.constants import DEFAULT_READ_LINES, MAX_LINE_LENGTH


class ReadFileInput(BaseModel):
    """Input schema for read_file tool."""

    file_path: str = Field(
        description="Absolute or relative path to the file to read"
    )
    offset: int | None = Field(
        default=None,
        ge=1,
        description="Line number to start reading from (1-based)",
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of lines to read",
    )


class ReadFileOutput(BaseModel):
    """Output schema for read_file tool."""

    content: str = Field(description="File content with line numbers")
    total_lines: int = Field(description="Total lines in the file")
    lines_read: int = Field(description="Number of lines returned")
    truncated: bool = Field(description="Whether content was truncated")
    file_path: str = Field(description="Resolved file path")


@register_tool
class ReadFileTool(BaseTool[ReadFileInput, ReadFileOutput]):
    """
    Read contents of a file with optional line range support.

    Returns file content with line numbers prepended for easy reference.
    Large files are automatically truncated.
    """

    name = "read_file"
    description = (
        "Read the contents of a file. Returns content with line numbers. "
        "Use offset and limit parameters for large files. "
        "Always read a file before attempting to edit it."
    )
    parallel_safe = True
    requires_lock = False

    @property
    def input_schema(self) -> type[ReadFileInput]:
        return ReadFileInput

    @property
    def output_schema(self) -> type[ReadFileOutput]:
        return ReadFileOutput

    async def execute(
        self,
        input_data: ReadFileInput,
        context: ToolContext,
    ) -> ReadFileOutput:
        """Read file contents with line numbers."""
        # Resolve path
        path = context.resolve_path(input_data.file_path)

        # Check file exists
        if not path.exists():
            from esnaad.exceptions import ToolExecutionError
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"File not found: {path}",
            )

        if not path.is_file():
            from esnaad.exceptions import ToolExecutionError
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Not a file: {path}",
            )

        # Check file size
        file_size = path.stat().st_size
        max_size = context.settings.tools.max_file_size_bytes

        if file_size > max_size:
            from esnaad.exceptions import ToolExecutionError
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"File too large: {file_size} bytes (max: {max_size})",
            )

        # Read file
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                all_lines = await f.readlines()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            async with aiofiles.open(path, "r", encoding="latin-1") as f:
                all_lines = await f.readlines()

        total_lines = len(all_lines)

        # Apply offset and limit
        offset = input_data.offset or 1
        limit = input_data.limit or DEFAULT_READ_LINES

        start_idx = offset - 1  # Convert to 0-based
        end_idx = start_idx + limit

        lines = all_lines[start_idx:end_idx]
        lines_read = len(lines)

        # Format with line numbers
        formatted_lines = []
        for i, line in enumerate(lines):
            line_num = start_idx + i + 1
            line_content = line.rstrip("\n\r")

            # Truncate long lines
            if len(line_content) > MAX_LINE_LENGTH:
                line_content = line_content[:MAX_LINE_LENGTH] + "..."

            formatted_lines.append(f"{line_num:6d}\t{line_content}")

        content = "\n".join(formatted_lines)

        # Check if truncated
        truncated = end_idx < total_lines

        return ReadFileOutput(
            content=content,
            total_lines=total_lines,
            lines_read=lines_read,
            truncated=truncated,
            file_path=str(path),
        )
