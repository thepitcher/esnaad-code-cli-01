"""Subtask models for parallel execution."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SubtaskStatus(str, Enum):
    """Status of a subtask."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Subtask(BaseModel):
    """
    Definition of a subtask to be executed by a sub-agent.

    Attributes:
        id: Unique identifier for the subtask
        description: Brief description of what the subtask does
        prompt: Full prompt to send to the sub-agent
        tools: List of tool names the sub-agent can use
        depends_on: IDs of subtasks this one depends on
        priority: Execution priority (lower = higher priority)
    """

    id: str = Field(description="Unique identifier")
    description: str = Field(description="Brief description")
    prompt: str = Field(description="Full prompt for the sub-agent")
    tools: list[str] = Field(
        default_factory=list,
        description="Allowed tool names",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of dependent subtasks",
    )
    priority: int = Field(default=0, description="Execution priority")

    @property
    def is_independent(self) -> bool:
        """Check if this subtask has no dependencies."""
        return len(self.depends_on) == 0


class SubtaskResult(BaseModel):
    """
    Result of a subtask execution.

    Attributes:
        id: ID of the subtask
        status: Execution status
        result: Final result content (if complete)
        error: Error message (if failed)
        iterations: Number of iterations used
        execution_time: Total execution time in seconds
        partial_output: Partial output if incomplete/failed
    """

    id: str = Field(description="Subtask ID")
    status: SubtaskStatus = Field(description="Execution status")
    result: str | None = Field(default=None, description="Final result")
    error: str | None = Field(default=None, description="Error message")
    iterations: int = Field(default=0, description="Iterations used")
    execution_time: float | None = Field(
        default=None,
        description="Execution time in seconds",
    )
    partial_output: str | None = Field(
        default=None,
        description="Partial output if incomplete",
    )

    @property
    def is_success(self) -> bool:
        """Check if the subtask completed successfully."""
        return self.status == SubtaskStatus.COMPLETE

    @property
    def is_failed(self) -> bool:
        """Check if the subtask failed."""
        return self.status in (
            SubtaskStatus.FAILED,
            SubtaskStatus.TIMEOUT,
        )

    @property
    def output(self) -> str:
        """Get the best available output."""
        return self.result or self.partial_output or self.error or "No output"

    @classmethod
    def complete(
        cls,
        id: str,
        result: str,
        iterations: int = 0,
        execution_time: float | None = None,
    ) -> "SubtaskResult":
        """Create a complete result."""
        return cls(
            id=id,
            status=SubtaskStatus.COMPLETE,
            result=result,
            iterations=iterations,
            execution_time=execution_time,
        )

    @classmethod
    def failed(
        cls,
        id: str,
        error: str,
        partial_output: str | None = None,
        iterations: int = 0,
        execution_time: float | None = None,
    ) -> "SubtaskResult":
        """Create a failed result."""
        return cls(
            id=id,
            status=SubtaskStatus.FAILED,
            error=error,
            partial_output=partial_output,
            iterations=iterations,
            execution_time=execution_time,
        )

    @classmethod
    def timeout(
        cls,
        id: str,
        timeout: float,
        partial_output: str | None = None,
        iterations: int = 0,
    ) -> "SubtaskResult":
        """Create a timeout result."""
        return cls(
            id=id,
            status=SubtaskStatus.TIMEOUT,
            error=f"Subtask timed out after {timeout}s",
            partial_output=partial_output,
            iterations=iterations,
            execution_time=timeout,
        )

    @classmethod
    def incomplete(
        cls,
        id: str,
        partial_output: str,
        iterations: int = 0,
        execution_time: float | None = None,
    ) -> "SubtaskResult":
        """Create an incomplete result."""
        return cls(
            id=id,
            status=SubtaskStatus.INCOMPLETE,
            partial_output=partial_output,
            iterations=iterations,
            execution_time=execution_time,
        )
