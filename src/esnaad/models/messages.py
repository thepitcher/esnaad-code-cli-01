"""Message models for LLM conversation."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in the conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """Base message model."""

    role: MessageRole
    content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {"role": self.role.value, "content": self.content}


class SystemMessage(Message):
    """System message for setting context."""

    role: MessageRole = MessageRole.SYSTEM
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {"role": "system", "content": self.content}


class UserMessage(Message):
    """User message."""

    role: MessageRole = MessageRole.USER
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {"role": "user", "content": self.content}


class AssistantMessage(Message):
    """Assistant message, may include tool calls."""

    role: MessageRole = MessageRole.ASSISTANT
    content: str | None = None
    tool_calls: list["ToolCallData"] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": "assistant"}
        if self.content:
            result["content"] = self.content
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        return result


class ToolCallData(BaseModel):
    """Tool call data in assistant message."""

    id: str
    type: str = "function"
    function: "FunctionCallData"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "function": self.function.to_dict(),
        }


class FunctionCallData(BaseModel):
    """Function call data."""

    name: str
    arguments: str  # JSON string

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "arguments": self.arguments}


class ToolMessage(Message):
    """Tool result message."""

    role: MessageRole = MessageRole.TOOL
    content: str
    tool_call_id: str
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "role": "tool",
            "content": self.content,
            "tool_call_id": self.tool_call_id,
        }
        if self.name:
            result["name"] = self.name
        return result


# Update forward references
AssistantMessage.model_rebuild()
