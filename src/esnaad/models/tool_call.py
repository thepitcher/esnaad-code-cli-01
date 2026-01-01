"""Tool call models for Esnaad Code."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolCallStatus(str, Enum):
    """Status of a tool call execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class ToolCall(BaseModel):
    """
    Represents a tool call from the LLM.

    Attributes:
        id: Unique identifier for the tool call
        name: Name of the tool to call
        arguments: Tool arguments as a dictionary
    """

    id: str = Field(description="Unique identifier for the tool call")
    name: str = Field(description="Name of the tool to call")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool arguments",
    )

    @classmethod
    def from_openai_format(cls, data: dict[str, Any]) -> "ToolCall":
        """Create from OpenAI API format."""
        import ast
        import json
        import uuid

        function = data.get("function", {})
        arguments_str = function.get("arguments", "{}")

        # Parse arguments - try JSON first, then Python literal syntax
        arguments = {}
        if arguments_str:
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                # Some models send Python dict syntax with single quotes
                try:
                    arguments = ast.literal_eval(arguments_str)
                    if not isinstance(arguments, dict):
                        arguments = {}
                except (ValueError, SyntaxError):
                    arguments = {}

        # Handle None or missing ID by generating a fallback
        tool_id = data.get("id")
        if not tool_id:
            tool_id = f"call_{uuid.uuid4().hex[:12]}"

        return cls(
            id=tool_id,
            name=function.get("name", ""),
            arguments=arguments,
        )


class ToolResult(BaseModel):
    """
    Result of a tool execution.

    Attributes:
        tool_call_id: ID of the tool call this is responding to
        tool_name: Name of the tool that was called
        status: Execution status
        output: Tool output (success case)
        error: Error message (error case)
        execution_time: Time taken to execute in seconds
    """

    tool_call_id: str = Field(description="ID of the tool call")
    tool_name: str = Field(description="Name of the tool")
    status: ToolCallStatus = Field(description="Execution status")
    output: Any | None = Field(default=None, description="Tool output")
    error: str | None = Field(default=None, description="Error message")
    execution_time: float | None = Field(
        default=None,
        description="Execution time in seconds",
    )

    @property
    def is_success(self) -> bool:
        """Check if the tool execution was successful."""
        return self.status == ToolCallStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if the tool execution failed."""
        return self.status in (ToolCallStatus.ERROR, ToolCallStatus.TIMEOUT)

    def to_content(self) -> str:
        """Convert to content string for tool message."""
        if self.is_success:
            if isinstance(self.output, str):
                return self.output
            import json

            return json.dumps(self.output, indent=2, default=str)
        else:
            return f"Error: {self.error or 'Unknown error'}"

    @classmethod
    def create_success(
        cls,
        tool_call_id: str,
        tool_name: str,
        output: Any,
        execution_time: float | None = None,
    ) -> "ToolResult":
        """Create a success result."""
        return cls(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            status=ToolCallStatus.SUCCESS,
            output=output,
            execution_time=execution_time,
        )

    @classmethod
    def create_error(
        cls,
        tool_call_id: str,
        tool_name: str,
        error: str,
        execution_time: float | None = None,
    ) -> "ToolResult":
        """Create an error result."""
        return cls(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            status=ToolCallStatus.ERROR,
            error=error,
            execution_time=execution_time,
        )

    @classmethod
    def create_timeout(
        cls,
        tool_call_id: str,
        tool_name: str,
        timeout: float,
    ) -> "ToolResult":
        """Create a timeout result."""
        return cls(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            status=ToolCallStatus.TIMEOUT,
            error=f"Tool execution timed out after {timeout}s",
            execution_time=timeout,
        )
