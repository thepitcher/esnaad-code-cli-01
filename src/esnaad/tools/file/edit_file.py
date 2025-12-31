"""Edit file tool implementation."""

from pathlib import Path

import aiofiles
from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class EditFileInput(BaseModel):
    """Input schema for edit_file tool."""

    file_path: str = Field(
        description="Absolute or relative path to the file to edit"
    )
    old_string: str = Field(
        description="The exact text to find and replace"
    )
    new_string: str = Field(
        description="The text to replace it with"
    )
    replace_all: bool = Field(
        default=False,
        description="Replace all occurrences (default: first only)",
    )


class EditFileOutput(BaseModel):
    """Output schema for edit_file tool."""

    success: bool = Field(description="Whether the edit was successful")
    file_path: str = Field(description="Resolved file path")
    replacements: int = Field(description="Number of replacements made")
    old_preview: str = Field(description="Preview of replaced text")
    new_preview: str = Field(description="Preview of new text")


@register_tool
class EditFileTool(BaseTool[EditFileInput, EditFileOutput]):
    """
    Make precise edits to a file by replacing text.

    Finds an exact string match and replaces it. Use this for surgical
    modifications to existing files rather than write_file.
    """

    name = "edit_file"
    description = (
        "Make precise edits to a file by replacing exact text matches. "
        "The old_string must match exactly (including whitespace and indentation). "
        "Always read the file first to ensure correct matching. "
        "Use replace_all=true to replace all occurrences."
    )
    parallel_safe = False
    requires_lock = True
    requires_approval = True  # Destructive: modifies files

    @property
    def input_schema(self) -> type[EditFileInput]:
        return EditFileInput

    @property
    def output_schema(self) -> type[EditFileOutput]:
        return EditFileOutput

    async def execute(
        self,
        input_data: EditFileInput,
        context: ToolContext,
    ) -> EditFileOutput:
        """Edit file by replacing text."""
        from esnaad.exceptions import ToolExecutionError

        # Resolve path
        path = context.resolve_path(input_data.file_path)

        # Check file exists
        if not path.exists():
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"File not found: {path}",
            )

        if not path.is_file():
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Not a file: {path}",
            )

        # Read current content
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
        except UnicodeDecodeError:
            async with aiofiles.open(path, "r", encoding="latin-1") as f:
                content = await f.read()

        # Check if old_string exists
        if input_data.old_string not in content:
            raise ToolExecutionError(
                tool_name=self.name,
                message=(
                    f"String not found in file: {repr(input_data.old_string[:100])}... "
                    "Make sure the string matches exactly including whitespace."
                ),
            )

        # Check for uniqueness if not replace_all
        if not input_data.replace_all:
            count = content.count(input_data.old_string)
            if count > 1:
                raise ToolExecutionError(
                    tool_name=self.name,
                    message=(
                        f"String found {count} times. Either use replace_all=true "
                        "or provide a more specific string to match uniquely."
                    ),
                )

        # Perform replacement
        if input_data.replace_all:
            new_content = content.replace(
                input_data.old_string,
                input_data.new_string,
            )
            replacements = content.count(input_data.old_string)
        else:
            new_content = content.replace(
                input_data.old_string,
                input_data.new_string,
                1,  # Only first occurrence
            )
            replacements = 1

        # Write updated content
        try:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(new_content)
        except Exception as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Failed to write file: {e}",
                original=e,
            ) from e

        # Create previews (truncated)
        def truncate(s: str, max_len: int = 100) -> str:
            if len(s) > max_len:
                return s[:max_len] + "..."
            return s

        return EditFileOutput(
            success=True,
            file_path=str(path),
            replacements=replacements,
            old_preview=truncate(input_data.old_string),
            new_preview=truncate(input_data.new_string),
        )
