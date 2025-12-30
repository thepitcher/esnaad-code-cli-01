"""Tool-related exceptions for Esnaad Code."""

from esnaad.exceptions.base import EsnaadError


class ToolError(EsnaadError):
    """Base exception for tool-related errors."""

    def __init__(
        self,
        message: str,
        tool_name: str | None = None,
        recoverable: bool = True,
    ) -> None:
        super().__init__(message, recoverable=recoverable)
        self.tool_name = tool_name
        if tool_name:
            self.details["tool_name"] = tool_name


class ToolNotFoundError(ToolError):
    """
    Tool not found in registry.

    Raised when attempting to use a tool that doesn't exist.
    """

    def __init__(self, tool_name: str) -> None:
        super().__init__(
            f"Tool '{tool_name}' not found in registry",
            tool_name=tool_name,
            recoverable=False,
        )


class ToolExecutionError(ToolError):
    """
    Error during tool execution.

    Raised when a tool fails to execute properly.
    """

    def __init__(
        self,
        tool_name: str,
        message: str,
        original: Exception | None = None,
    ) -> None:
        super().__init__(
            f"Tool '{tool_name}' failed: {message}",
            tool_name=tool_name,
            recoverable=True,
        )
        self.original = original
        if original:
            self.details["original_error"] = str(original)
            self.details["original_type"] = type(original).__name__


class ToolValidationError(ToolError):
    """
    Tool input validation failed.

    Raised when tool input doesn't match the expected schema.
    """

    def __init__(
        self,
        tool_name: str,
        message: str,
        validation_errors: list[dict] | None = None,
    ) -> None:
        super().__init__(
            f"Invalid input for tool '{tool_name}': {message}",
            tool_name=tool_name,
            recoverable=False,
        )
        self.validation_errors = validation_errors or []
        if validation_errors:
            self.details["validation_errors"] = validation_errors
