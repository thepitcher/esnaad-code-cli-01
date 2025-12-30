"""Custom exceptions for Esnaad Code."""

from esnaad.exceptions.base import (
    EsnaadError,
    ConfigurationError,
)
from esnaad.exceptions.llm import (
    LLMError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from esnaad.exceptions.tool import (
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolValidationError,
)
from esnaad.exceptions.agent import (
    AgentError,
    MaxIterationsError,
    AgentTimeoutError,
    SubtaskError,
)

__all__ = [
    # Base
    "EsnaadError",
    "ConfigurationError",
    # LLM
    "LLMError",
    "LLMConnectionError",
    "LLMRateLimitError",
    "LLMResponseError",
    "LLMTimeoutError",
    # Tool
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolValidationError",
    # Agent
    "AgentError",
    "MaxIterationsError",
    "AgentTimeoutError",
    "SubtaskError",
]
