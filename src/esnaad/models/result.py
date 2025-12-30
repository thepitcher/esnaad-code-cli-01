"""Agent result models for Esnaad Code."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from esnaad.models.subtask import SubtaskResult


class AgentStatus(str, Enum):
    """Status of agent execution."""

    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"
    TIMEOUT = "timeout"
    MAX_ITERATIONS = "max_iterations"
    CANCELLED = "cancelled"


class AgentResult(BaseModel):
    """
    Final result from an agent execution.

    Attributes:
        status: Execution status
        content: Final response content
        error: Error message if failed
        iterations: Number of iterations used
        execution_time: Total execution time in seconds
        tool_calls_count: Number of tool calls made
        subtask_results: Results from any spawned subtasks
        metadata: Additional metadata about the execution
    """

    status: AgentStatus = Field(description="Execution status")
    content: str | None = Field(default=None, description="Final response")
    error: str | None = Field(default=None, description="Error message")
    iterations: int = Field(default=0, description="Iterations used")
    execution_time: float | None = Field(
        default=None,
        description="Execution time in seconds",
    )
    tool_calls_count: int = Field(default=0, description="Tool calls made")
    subtask_results: list[SubtaskResult] = Field(
        default_factory=list,
        description="Subtask results",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == AgentStatus.COMPLETE

    @property
    def is_error(self) -> bool:
        """Check if execution failed."""
        return self.status in (
            AgentStatus.ERROR,
            AgentStatus.TIMEOUT,
            AgentStatus.MAX_ITERATIONS,
        )

    @property
    def output(self) -> str:
        """Get the best available output."""
        if self.content:
            return self.content
        if self.error:
            return f"Error: {self.error}"
        return "No output"

    @classmethod
    def success(
        cls,
        content: str,
        iterations: int = 0,
        execution_time: float | None = None,
        tool_calls_count: int = 0,
        subtask_results: list[SubtaskResult] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "AgentResult":
        """Create a success result."""
        return cls(
            status=AgentStatus.COMPLETE,
            content=content,
            iterations=iterations,
            execution_time=execution_time,
            tool_calls_count=tool_calls_count,
            subtask_results=subtask_results or [],
            metadata=metadata or {},
        )

    @classmethod
    def error(
        cls,
        error: str,
        iterations: int = 0,
        execution_time: float | None = None,
        tool_calls_count: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> "AgentResult":
        """Create an error result."""
        return cls(
            status=AgentStatus.ERROR,
            error=error,
            iterations=iterations,
            execution_time=execution_time,
            tool_calls_count=tool_calls_count,
            metadata=metadata or {},
        )

    @classmethod
    def timeout(
        cls,
        timeout: float,
        iterations: int = 0,
        partial_content: str | None = None,
        tool_calls_count: int = 0,
    ) -> "AgentResult":
        """Create a timeout result."""
        return cls(
            status=AgentStatus.TIMEOUT,
            error=f"Execution timed out after {timeout}s",
            content=partial_content,
            iterations=iterations,
            execution_time=timeout,
            tool_calls_count=tool_calls_count,
        )

    @classmethod
    def max_iterations(
        cls,
        iterations: int,
        max_iterations: int,
        partial_content: str | None = None,
        execution_time: float | None = None,
        tool_calls_count: int = 0,
    ) -> "AgentResult":
        """Create a max iterations result."""
        return cls(
            status=AgentStatus.MAX_ITERATIONS,
            error=f"Maximum iterations ({max_iterations}) exceeded",
            content=partial_content,
            iterations=iterations,
            execution_time=execution_time,
            tool_calls_count=tool_calls_count,
        )
