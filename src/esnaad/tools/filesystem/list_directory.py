"""List directory tool implementation."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class ListDirectoryInput(BaseModel):
    """Input schema for list_directory tool."""

    path: str = Field(
        default=".",
        description="Directory path to list (default: current directory)",
    )
    recursive: bool = Field(
        default=False,
        description="List recursively (use with caution on large directories)",
    )
    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum depth for recursive listing",
    )
    show_hidden: bool = Field(
        default=False,
        description="Include hidden files (starting with .)",
    )
    pattern: str | None = Field(
        default=None,
        description="Filter files by glob pattern (e.g., '*.py')",
    )


class FileInfo(BaseModel):
    """Information about a file or directory."""

    name: str
    path: str
    type: Literal["file", "directory", "symlink"]
    size: int | None = None


class ListDirectoryOutput(BaseModel):
    """Output schema for list_directory tool."""

    path: str = Field(description="Listed directory path")
    entries: list[FileInfo] = Field(description="Directory entries")
    total_files: int = Field(description="Total number of files")
    total_directories: int = Field(description="Total number of directories")
    truncated: bool = Field(description="Whether results were truncated")


@register_tool
class ListDirectoryTool(BaseTool[ListDirectoryInput, ListDirectoryOutput]):
    """
    List files and directories in a path.

    Returns file names, types, and sizes. Use pattern to filter results.
    """

    name = "list_directory"
    description = (
        "List files and directories in a path. "
        "Use pattern parameter to filter by glob pattern (e.g., '*.py'). "
        "Use recursive=true for subdirectories (limited by max_depth)."
    )
    parallel_safe = True
    requires_lock = False

    MAX_ENTRIES = 500

    @property
    def input_schema(self) -> type[ListDirectoryInput]:
        return ListDirectoryInput

    @property
    def output_schema(self) -> type[ListDirectoryOutput]:
        return ListDirectoryOutput

    async def execute(
        self,
        input_data: ListDirectoryInput,
        context: ToolContext,
    ) -> ListDirectoryOutput:
        """List directory contents."""
        from esnaad.exceptions import ToolExecutionError

        # Resolve path
        path = context.resolve_path(input_data.path)

        if not path.exists():
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Path not found: {path}",
            )

        if not path.is_dir():
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Not a directory: {path}",
            )

        entries: list[FileInfo] = []
        total_files = 0
        total_directories = 0
        truncated = False

        if input_data.recursive:
            # Recursive listing
            entries, total_files, total_directories, truncated = (
                self._list_recursive(
                    path,
                    input_data.max_depth,
                    input_data.show_hidden,
                    input_data.pattern,
                )
            )
        else:
            # Simple listing
            entries, total_files, total_directories, truncated = (
                self._list_simple(
                    path,
                    input_data.show_hidden,
                    input_data.pattern,
                )
            )

        return ListDirectoryOutput(
            path=str(path),
            entries=entries,
            total_files=total_files,
            total_directories=total_directories,
            truncated=truncated,
        )

    def _list_simple(
        self,
        path: Path,
        show_hidden: bool,
        pattern: str | None,
    ) -> tuple[list[FileInfo], int, int, bool]:
        """List a single directory."""
        entries = []
        total_files = 0
        total_directories = 0
        truncated = False

        try:
            items = list(path.iterdir())
        except PermissionError:
            return [], 0, 0, False

        for item in sorted(items, key=lambda x: (not x.is_dir(), x.name.lower())):
            # Filter hidden files
            if not show_hidden and item.name.startswith("."):
                continue

            # Filter by pattern
            if pattern and not item.match(pattern):
                continue

            # Check limit
            if len(entries) >= self.MAX_ENTRIES:
                truncated = True
                break

            # Get file info
            try:
                if item.is_symlink():
                    file_type = "symlink"
                    size = None
                elif item.is_dir():
                    file_type = "directory"
                    size = None
                    total_directories += 1
                else:
                    file_type = "file"
                    size = item.stat().st_size
                    total_files += 1

                entries.append(FileInfo(
                    name=item.name,
                    path=str(item),
                    type=file_type,
                    size=size,
                ))
            except (PermissionError, OSError):
                continue

        return entries, total_files, total_directories, truncated

    def _list_recursive(
        self,
        path: Path,
        max_depth: int,
        show_hidden: bool,
        pattern: str | None,
    ) -> tuple[list[FileInfo], int, int, bool]:
        """List directory recursively."""
        entries = []
        total_files = 0
        total_directories = 0
        truncated = False

        def walk(current: Path, depth: int) -> None:
            nonlocal total_files, total_directories, truncated

            if depth > max_depth or truncated:
                return

            try:
                items = list(current.iterdir())
            except PermissionError:
                return

            for item in sorted(items, key=lambda x: (not x.is_dir(), x.name.lower())):
                if truncated:
                    return

                # Filter hidden files
                if not show_hidden and item.name.startswith("."):
                    continue

                # Check limit
                if len(entries) >= self.MAX_ENTRIES:
                    truncated = True
                    return

                try:
                    if item.is_symlink():
                        file_type = "symlink"
                        size = None
                    elif item.is_dir():
                        file_type = "directory"
                        size = None
                        total_directories += 1

                        # Recurse into directory
                        walk(item, depth + 1)
                    else:
                        # Check pattern for files
                        if pattern and not item.match(pattern):
                            continue

                        file_type = "file"
                        size = item.stat().st_size
                        total_files += 1

                    entries.append(FileInfo(
                        name=item.name,
                        path=str(item.relative_to(path)),
                        type=file_type,
                        size=size,
                    ))
                except (PermissionError, OSError):
                    continue

        walk(path, 1)
        return entries, total_files, total_directories, truncated
