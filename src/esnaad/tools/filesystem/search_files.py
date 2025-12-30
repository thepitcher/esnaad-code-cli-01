"""Search files tool implementation."""

from pathlib import Path
import fnmatch

from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class SearchFilesInput(BaseModel):
    """Input schema for search_files tool."""

    pattern: str = Field(
        description="Glob pattern to match files (e.g., '*.py', '**/*.ts')",
    )
    path: str = Field(
        default=".",
        description="Directory to search in (default: current directory)",
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of results to return",
    )


class SearchFilesOutput(BaseModel):
    """Output schema for search_files tool."""

    matches: list[str] = Field(description="Matching file paths")
    total_matches: int = Field(description="Total number of matches found")
    truncated: bool = Field(description="Whether results were truncated")
    search_path: str = Field(description="Directory that was searched")


@register_tool
class SearchFilesTool(BaseTool[SearchFilesInput, SearchFilesOutput]):
    """
    Find files by name pattern.

    Uses glob patterns to find matching files recursively.
    """

    name = "search_files"
    description = (
        "Find files by name pattern using glob syntax. "
        "Examples: '*.py' for Python files, '**/*.ts' for TypeScript files recursively, "
        "'test_*.py' for test files. Use for locating files by name."
    )
    parallel_safe = True
    requires_lock = False

    @property
    def input_schema(self) -> type[SearchFilesInput]:
        return SearchFilesInput

    @property
    def output_schema(self) -> type[SearchFilesOutput]:
        return SearchFilesOutput

    async def execute(
        self,
        input_data: SearchFilesInput,
        context: ToolContext,
    ) -> SearchFilesOutput:
        """Search for files matching pattern."""
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

        # Normalize pattern for recursive search
        pattern = input_data.pattern
        if not pattern.startswith("**"):
            pattern = f"**/{pattern}"

        matches: list[str] = []
        truncated = False

        try:
            for match in path.glob(pattern):
                if match.is_file():
                    # Get relative path
                    try:
                        rel_path = str(match.relative_to(path))
                    except ValueError:
                        rel_path = str(match)

                    matches.append(rel_path)

                    if len(matches) >= input_data.max_results:
                        truncated = True
                        break

        except Exception as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Search failed: {e}",
                original=e,
            ) from e

        return SearchFilesOutput(
            matches=matches,
            total_matches=len(matches),
            truncated=truncated,
            search_path=str(path),
        )
