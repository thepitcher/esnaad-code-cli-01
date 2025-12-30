"""Agent-related exceptions for Esnaad Code."""

from esnaad.exceptions.base import EsnaadError


class AgentError(EsnaadError):
    """Base exception for agent-related errors."""

    def __init__(
        self,
        message: str,
        agent_id: str | None = None,
        recoverable: bool = False,
    ) -> None:
        super().__init__(message, recoverable=recoverable)
        self.agent_id = agent_id
        if agent_id:
            self.details["agent_id"] = agent_id


class MaxIterationsError(AgentError):
    """
    Maximum iterations exceeded.

    Raised when the agent loop exceeds the configured maximum iterations.
    """

    def __init__(
        self,
        iterations: int,
        max_iterations: int,
        agent_id: str | None = None,
    ) -> None:
        super().__init__(
            f"Maximum iterations ({max_iterations}) exceeded after {iterations} iterations",
            agent_id=agent_id,
            recoverable=False,
        )
        self.iterations = iterations
        self.max_iterations = max_iterations
        self.details["iterations"] = iterations
        self.details["max_iterations"] = max_iterations


class AgentTimeoutError(AgentError):
    """
    Agent operation timed out.

    Raised when the agent exceeds the configured timeout.
    """

    def __init__(
        self,
        operation: str,
        timeout: float,
        agent_id: str | None = None,
    ) -> None:
        super().__init__(
            f"Agent operation '{operation}' timed out after {timeout}s",
            agent_id=agent_id,
            recoverable=True,
        )
        self.operation = operation
        self.timeout = timeout
        self.details["operation"] = operation
        self.details["timeout"] = timeout


class SubtaskError(AgentError):
    """
    Error in subtask execution.

    Raised when a sub-agent fails to complete its task.
    """

    def __init__(
        self,
        subtask_id: str,
        message: str,
        partial_result: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        super().__init__(
            f"Subtask '{subtask_id}' failed: {message}",
            agent_id=agent_id,
            recoverable=True,
        )
        self.subtask_id = subtask_id
        self.partial_result = partial_result
        self.details["subtask_id"] = subtask_id
        if partial_result:
            self.details["partial_result"] = partial_result[:500]  # Truncate
