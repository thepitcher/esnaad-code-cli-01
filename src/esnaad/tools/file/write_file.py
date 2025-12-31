"""Write file tool implementation."""

from pathlib import Path

import aiofiles
from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class WriteFileInput(BaseModel):
    """Input schema for write_file tool."""

    file_path: str = Field(
        description="Absolute or relative path to the file to write"
    )
    content: str = Field(
        description="Content to write to the file"
    )
    create_directories: bool = Field(
        default=True,
        description="Create parent directories if they don't exist",
    )


class WriteFileOutput(BaseModel):
    """Output schema for write_file tool."""

    success: bool = Field(description="Whether the write was successful")
    file_path: str = Field(description="Resolved file path")
    bytes_written: int = Field(description="Number of bytes written")
    created: bool = Field(description="Whether file was newly created")


@register_tool
class WriteFileTool(BaseTool[WriteFileInput, WriteFileOutput]):
    """
    Create or overwrite a file with the given content.

    Creates parent directories if needed. For modifying existing files,
    prefer the edit_file tool for precise changes.
    """

    name = "write_file"
    description = (
        "Create a new file or overwrite an existing file with content. "
        "For modifying existing files, prefer edit_file for precise changes. "
        "Parent directories are created automatically."
    )
    parallel_safe = False
    requires_lock = True
    requires_approval = True  # Destructive: modifies filesystem

    @property
    def input_schema(self) -> type[WriteFileInput]:
        return WriteFileInput

    @property
    def output_schema(self) -> type[WriteFileOutput]:
        return WriteFileOutput

    async def execute(
        self,
        input_data: WriteFileInput,
        context: ToolContext,
    ) -> WriteFileOutput:
        """Write content to file."""
        # Resolve path
        path = context.resolve_path(input_data.file_path)

        # Check if file exists (for reporting)
        created = not path.exists()

        # Create parent directories if needed
        if input_data.create_directories:
            path.parent.mkdir(parents=True, exist_ok=True)
        elif not path.parent.exists():
            from esnaad.exceptions import ToolExecutionError
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Parent directory does not exist: {path.parent}",
            )

        # Write file
        try:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(input_data.content)

            bytes_written = len(input_data.content.encode("utf-8"))

            return WriteFileOutput(
                success=True,
                file_path=str(path),
                bytes_written=bytes_written,
                created=created,
            )

        except Exception as e:
            from esnaad.exceptions import ToolExecutionError
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Failed to write file: {e}",
                original=e,
            ) from e
