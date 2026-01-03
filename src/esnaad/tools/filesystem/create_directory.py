"""Create directory tool implementation."""

from pathlib import Path

from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class CreateDirectoryInput(BaseModel):
    """Input schema for create_directory tool."""

    path: str = Field(
        description="Directory path to create (can be nested path)"
    )
    parents: bool = Field(
        default=True,
        description="Create parent directories if they don't exist (like mkdir -p)",
    )
    exist_ok: bool = Field(
        default=True,
        description="Don't raise error if directory already exists",
    )


class CreateDirectoryOutput(BaseModel):
    """Output schema for create_directory tool."""

    success: bool = Field(description="Whether directory was created successfully")
    path: str = Field(description="Resolved directory path")
    created: bool = Field(description="True if directory was created, False if already existed")
    parent_created: bool = Field(description="True if parent directories were created")


@register_tool
class CreateDirectoryTool(BaseTool[CreateDirectoryInput, CreateDirectoryOutput]):
    """
    Create a directory with optional parent directory creation.

    Platform-agnostic directory creation using Python's pathlib.
    Safer and faster than using shell commands.
    """

    name = "create_directory"
    description = (
        "Create a directory at the specified path. "
        "Can create nested directories (parent directories) automatically. "
        "Safe operation - does not require approval. "
        "Use this instead of run_command with mkdir."
    )
    parallel_safe = False  # Multiple creates to same path could race
    requires_lock = False
    requires_approval = False  # Safe operation, no approval needed

    @property
    def input_schema(self) -> type[CreateDirectoryInput]:
        return CreateDirectoryInput

    @property
    def output_schema(self) -> type[CreateDirectoryOutput]:
        return CreateDirectoryOutput

    async def execute(
        self,
        input_data: CreateDirectoryInput,
        context: ToolContext,
    ) -> CreateDirectoryOutput:
        """Create directory."""
        from esnaad.exceptions import ToolExecutionError

        # Resolve path
        path = context.resolve_path(input_data.path)

        # Check if directory already exists
        already_existed = path.exists()
        parent_created = False

        try:
            if already_existed:
                if path.is_dir():
                    if not input_data.exist_ok:
                        raise ToolExecutionError(
                            tool_name=self.name,
                            message=f"Directory already exists: {path}",
                        )
                    # Directory exists, nothing to do
                    return CreateDirectoryOutput(
                        success=True,
                        path=str(path),
                        created=False,
                        parent_created=False,
                    )
                else:
                    raise ToolExecutionError(
                        tool_name=self.name,
                        message=f"Path exists but is not a directory: {path}",
                    )

            # Check if parent needs to be created
            if not path.parent.exists() and input_data.parents:
                parent_created = True

            # Create directory
            path.mkdir(parents=input_data.parents, exist_ok=input_data.exist_ok)

            return CreateDirectoryOutput(
                success=True,
                path=str(path),
                created=True,
                parent_created=parent_created,
            )

        except PermissionError as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Permission denied creating directory: {path}",
                original=e,
            ) from e

        except OSError as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Failed to create directory: {e}",
                original=e,
            ) from e

        except Exception as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Unexpected error creating directory: {e}",
                original=e,
            ) from e
