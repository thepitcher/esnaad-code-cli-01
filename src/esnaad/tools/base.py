"""Base tool class and context for all tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from esnaad.config.settings import Settings

# Type variables for input/output
TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput")


@dataclass
class ToolContext:
    """
    Context passed to every tool execution.

    Provides tools with access to shared resources and configuration.
    """

    working_directory: Path
    """Current working directory for file operations."""

    settings: Settings
    """Application settings."""

    agent_id: str
    """ID of the agent executing the tool."""

    is_subagent: bool = False
    """Whether this is a sub-agent execution."""

    state_manager: Any = None
    """Shared state manager (injected at runtime)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for the execution."""

    def resolve_path(self, path: str | Path) -> Path:
        """
        Resolve a path relative to the working directory.

        Args:
            path: Absolute or relative path

        Returns:
            Resolved absolute path
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return self.working_directory / p


class BaseTool(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for all tools.

    Tools must implement:
    - name: Unique tool name
    - description: Tool description for the LLM
    - input_schema: Pydantic model for input validation
    - execute: Async execution method

    Example:
        class MyTool(BaseTool[MyInput, MyOutput]):
            name = "my_tool"
            description = "Does something useful"

            @property
            def input_schema(self) -> type[MyInput]:
                return MyInput

            async def execute(
                self,
                input_data: MyInput,
                context: ToolContext,
            ) -> MyOutput:
                return MyOutput(...)
    """

    name: str
    """Unique name for the tool."""

    description: str
    """Description of what the tool does (shown to LLM)."""

    parallel_safe: bool = True
    """Whether the tool can be run in parallel with others."""

    requires_lock: bool = False
    """Whether the tool requires file locking."""

    requires_approval: bool = False
    """Whether the tool requires user approval in Plan Mode."""

    @property
    @abstractmethod
    def input_schema(self) -> type[TInput]:
        """Return the Pydantic model for input validation."""
        ...

    @property
    def output_schema(self) -> type[TOutput] | None:
        """Optional output schema for structured results."""
        return None

    @abstractmethod
    async def execute(
        self,
        input_data: TInput,
        context: ToolContext,
    ) -> TOutput:
        """
        Execute the tool with validated input.

        Args:
            input_data: Validated input data
            context: Tool execution context

        Returns:
            Tool output
        """
        ...

    def to_openai_schema(self) -> dict[str, Any]:
        """
        Convert to OpenAI function calling format.

        Returns:
            Tool definition in OpenAI format
        """
        schema = self.input_schema.model_json_schema()

        # Remove title if present (OpenAI doesn't like it)
        schema.pop("title", None)

        # Handle nested $defs
        if "$defs" in schema:
            # Inline definitions
            defs = schema.pop("$defs")
            schema = self._inline_refs(schema, defs)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }

    def _inline_refs(
        self,
        obj: Any,
        defs: dict[str, Any],
    ) -> Any:
        """Recursively inline $ref references."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                # Extract definition name from #/$defs/Name
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path[8:]
                    if def_name in defs:
                        return self._inline_refs(defs[def_name], defs)
                return obj

            return {
                k: self._inline_refs(v, defs)
                for k, v in obj.items()
            }

        elif isinstance(obj, list):
            return [self._inline_refs(item, defs) for item in obj]

        return obj

    async def validate_and_execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> TOutput:
        """
        Validate arguments and execute the tool.

        Args:
            arguments: Raw arguments dict
            context: Tool execution context

        Returns:
            Tool output

        Raises:
            ToolValidationError: If validation fails
            ToolExecutionError: If execution fails
        """
        from esnaad.exceptions import ToolValidationError, ToolExecutionError
        from pydantic import ValidationError

        # Validate input
        try:
            input_data = self.input_schema.model_validate(arguments)
        except ValidationError as e:
            raise ToolValidationError(
                tool_name=self.name,
                message=str(e),
                validation_errors=e.errors(),
            ) from e

        # Execute
        try:
            return await self.execute(input_data, context)
        except Exception as e:
            if isinstance(e, (ToolValidationError, ToolExecutionError)):
                raise
            raise ToolExecutionError(
                tool_name=self.name,
                message=str(e),
                original=e,
            ) from e

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
