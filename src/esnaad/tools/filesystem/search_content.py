"""Search content tool implementation."""

import re
from pathlib import Path

import aiofiles
from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class SearchContentInput(BaseModel):
    """Input schema for search_content tool."""

    pattern: str = Field(
        description="Text or regex pattern to search for",
    )
    path: str = Field(
        default=".",
        description="Directory or file to search in",
    )
    file_pattern: str | None = Field(
        default=None,
        description="Glob pattern to filter files (e.g., '*.py')",
    )
    regex: bool = Field(
        default=False,
        description="Treat pattern as regex",
    )
    case_sensitive: bool = Field(
        default=True,
        description="Case-sensitive search",
    )
    max_results: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of matches to return",
    )
    context_lines: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Lines of context around each match",
    )


class ContentMatch(BaseModel):
    """A single content match."""

    file: str
    line_number: int
    line_content: str
    context_before: list[str] = []
    context_after: list[str] = []


class SearchContentOutput(BaseModel):
    """Output schema for search_content tool."""

    matches: list[ContentMatch] = Field(description="Matching lines")
    total_matches: int = Field(description="Total matches found")
    files_searched: int = Field(description="Number of files searched")
    truncated: bool = Field(description="Whether results were truncated")


@register_tool
class SearchContentTool(BaseTool[SearchContentInput, SearchContentOutput]):
    """
    Search for text or patterns inside files.

    Similar to grep - searches file contents for matching text or patterns.
    """

    name = "search_content"
    description = (
        "Search for text or patterns inside files (like grep). "
        "Use file_pattern to limit which files are searched. "
        "Set regex=true for regular expression patterns. "
        "Returns matching lines with file paths and line numbers."
    )
    parallel_safe = True
    requires_lock = False

    @property
    def input_schema(self) -> type[SearchContentInput]:
        return SearchContentInput

    @property
    def output_schema(self) -> type[SearchContentOutput]:
        return SearchContentOutput

    async def execute(
        self,
        input_data: SearchContentInput,
        context: ToolContext,
    ) -> SearchContentOutput:
        """Search file contents."""
        from esnaad.exceptions import ToolExecutionError

        # Resolve path
        path = context.resolve_path(input_data.path)

        if not path.exists():
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Path not found: {path}",
            )

        # Compile pattern
        try:
            if input_data.regex:
                flags = 0 if input_data.case_sensitive else re.IGNORECASE
                compiled = re.compile(input_data.pattern, flags)
            else:
                pattern = input_data.pattern
                if not input_data.case_sensitive:
                    pattern = pattern.lower()
                compiled = None
        except re.error as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Invalid regex pattern: {e}",
            ) from e

        # Collect files to search
        if path.is_file():
            files = [path]
        else:
            file_pattern = input_data.file_pattern or "**/*"
            if not file_pattern.startswith("**"):
                file_pattern = f"**/{file_pattern}"
            files = [f for f in path.glob(file_pattern) if f.is_file()]

        matches: list[ContentMatch] = []
        files_searched = 0
        truncated = False

        for file_path in files:
            if truncated:
                break

            # Skip binary files and large files
            try:
                if file_path.stat().st_size > 1_000_000:  # 1MB
                    continue
            except OSError:
                continue

            files_searched += 1

            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    lines = await f.readlines()
            except (UnicodeDecodeError, PermissionError):
                continue

            for i, line in enumerate(lines):
                if truncated:
                    break

                line_content = line.rstrip("\n\r")

                # Check for match
                if compiled:
                    if compiled.search(line_content):
                        is_match = True
                    else:
                        is_match = False
                else:
                    search_line = line_content if input_data.case_sensitive else line_content.lower()
                    is_match = pattern in search_line

                if is_match:
                    # Get context
                    context_before = []
                    context_after = []

                    if input_data.context_lines > 0:
                        start = max(0, i - input_data.context_lines)
                        end = min(len(lines), i + input_data.context_lines + 1)

                        context_before = [
                            lines[j].rstrip("\n\r")
                            for j in range(start, i)
                        ]
                        context_after = [
                            lines[j].rstrip("\n\r")
                            for j in range(i + 1, end)
                        ]

                    try:
                        rel_path = str(file_path.relative_to(path))
                    except ValueError:
                        rel_path = str(file_path)

                    matches.append(ContentMatch(
                        file=rel_path,
                        line_number=i + 1,
                        line_content=line_content[:500],  # Truncate long lines
                        context_before=context_before,
                        context_after=context_after,
                    ))

                    if len(matches) >= input_data.max_results:
                        truncated = True
                        break

        return SearchContentOutput(
            matches=matches,
            total_matches=len(matches),
            files_searched=files_searched,
            truncated=truncated,
        )
