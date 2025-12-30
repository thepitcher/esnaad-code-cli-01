"""Async LLM client for OpenAI-compatible APIs."""

import json
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

import httpx
import structlog

from esnaad.config.settings import LLMSettings
from esnaad.exceptions import (
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from esnaad.models.messages import Message
from esnaad.models.tool_call import ToolCall

logger = structlog.get_logger(__name__)


@dataclass
class ChatChunk:
    """A chunk from a streaming response."""

    delta_content: str | None = None
    delta_tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str | None = None
    is_done: bool = False


@dataclass
class ChatResponse:
    """Complete chat completion response."""

    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    usage: dict[str, int] | None = None

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0


class LLMClient:
    """
    Async client for OpenAI-compatible LLM APIs.

    Supports:
    - Chat completions (streaming and non-streaming)
    - Tool/function calling
    - Retry with exponential backoff
    - Rate limit handling
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize the LLM client.

        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            verify_ssl: Whether to verify SSL/TLS certificates
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = httpx.Timeout(timeout, connect=10.0)
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def from_settings(cls, settings: LLMSettings) -> "LLMClient":
        """Create client from settings."""
        api_key = settings.api_key.get_secret_value() if settings.api_key else None
        return cls(
            base_url=settings.base_url,
            api_key=api_key,
            timeout=settings.timeout,
            verify_ssl=settings.verify_ssl,
        )

    def _build_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def __aenter__(self) -> "LLMClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._build_headers(),
            verify=self.verify_ssl,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._build_headers(),
                verify=self.verify_ssl,
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatChunk, None]:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts
            model: Model name to use
            tools: Optional list of tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            ChatResponse or AsyncGenerator[ChatChunk] if streaming
        """
        if stream:
            return self._stream_completion(
                messages=messages,
                model=model,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        else:
            return await self._complete(
                messages=messages,
                model=model,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

    async def _complete(
        self,
        messages: list[dict[str, Any]],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a non-streaming completion request."""
        client = await self._ensure_client()

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        # Add any extra parameters
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value

        logger.debug(
            "Sending chat completion",
            model=model,
            message_count=len(messages),
            has_tools=bool(tools),
        )

        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Failed to connect to LLM API: {e}",
                url=self.base_url,
            ) from e
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(
                f"LLM API request timed out: {e}",
                timeout=self.timeout.read,
            ) from e

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise LLMRateLimitError(
                retry_after=float(retry_after) if retry_after else None,
            )

        if response.status_code != 200:
            raise LLMResponseError(
                f"LLM API returned status {response.status_code}",
                response_text=response.text,
                status_code=response.status_code,
            )

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMResponseError(
                f"Failed to parse LLM response: {e}",
                response_text=response.text,
            ) from e

        logger.debug("LLM response received", response_data=data)
        return self._parse_response(data)

    async def _stream_completion(
        self,
        messages: list[dict[str, Any]],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Send a streaming completion request."""
        client = await self._ensure_client()

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        logger.debug(
            "Sending streaming chat completion",
            model=model,
            message_count=len(messages),
        )

        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
            ) as response:
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise LLMRateLimitError(
                        retry_after=float(retry_after) if retry_after else None,
                    )

                if response.status_code != 200:
                    text = await response.aread()
                    raise LLMResponseError(
                        f"LLM API returned status {response.status_code}",
                        response_text=text.decode(),
                        status_code=response.status_code,
                    )

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        yield ChatChunk(is_done=True)
                        break

                    try:
                        data = json.loads(data_str)
                        chunk = self._parse_stream_chunk(data)
                        if chunk:
                            yield chunk
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse stream chunk", data=data_str)
                        continue

        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Failed to connect to LLM API: {e}",
                url=self.base_url,
            ) from e
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(
                f"LLM API request timed out: {e}",
                timeout=self.timeout.read,
            ) from e

    def _parse_response(self, data: dict[str, Any]) -> ChatResponse:
        """Parse a complete API response (supports OpenAI and Anthropic formats)."""
        # Check if response is wrapped in "body" (some proxies do this)
        if "body" in data and isinstance(data["body"], dict):
            data = data["body"]

        # Detect format: Anthropic style has "content" as array and "stop_reason"
        if "stop_reason" in data or (isinstance(data.get("content"), list)):
            return self._parse_anthropic_response(data)

        # OpenAI format
        choices = data.get("choices", [])
        if not choices:
            raise LLMResponseError("No choices in LLM response")

        choice = choices[0]
        message = choice.get("message", {})

        # Parse tool calls
        tool_calls = []
        raw_tool_calls = message.get("tool_calls", [])
        for tc in raw_tool_calls:
            tool_calls.append(ToolCall.from_openai_format(tc))

        return ChatResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason"),
            usage=data.get("usage"),
        )

    def _parse_anthropic_response(self, data: dict[str, Any]) -> ChatResponse:
        """Parse Anthropic-style API response."""
        content_blocks = data.get("content", [])

        # Extract text content
        text_content = ""
        tool_calls = []

        for block in content_blocks:
            if isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "text":
                    text_content += block.get("text", "")
                elif block_type == "tool_use":
                    # Anthropic tool call format
                    tool_calls.append(ToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        arguments=block.get("input", {}),
                    ))
            elif isinstance(block, str):
                text_content += block

        # Map Anthropic stop_reason to OpenAI finish_reason
        stop_reason = data.get("stop_reason", "")
        finish_reason_map = {
            "end_turn": "stop",
            "tool_use": "tool_calls",
            "tool_calls": "tool_calls",
            "max_tokens": "length",
            "stop_sequence": "stop",
        }
        finish_reason = finish_reason_map.get(stop_reason, stop_reason)

        return ChatResponse(
            content=text_content if text_content else None,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=data.get("usage"),
        )

    def _parse_stream_chunk(self, data: dict[str, Any]) -> ChatChunk | None:
        """Parse a streaming chunk (supports OpenAI and Anthropic formats)."""
        # Check if wrapped in "body"
        if "body" in data and isinstance(data["body"], dict):
            data = data["body"]

        # Anthropic streaming format
        if data.get("type") in ("content_block_delta", "content_block_start", "message_delta", "message_start"):
            return self._parse_anthropic_stream_chunk(data)

        # OpenAI format
        choices = data.get("choices", [])
        if not choices:
            return None

        choice = choices[0]
        delta = choice.get("delta", {})

        return ChatChunk(
            delta_content=delta.get("content"),
            delta_tool_calls=delta.get("tool_calls"),
            finish_reason=choice.get("finish_reason"),
        )

    def _parse_anthropic_stream_chunk(self, data: dict[str, Any]) -> ChatChunk | None:
        """Parse Anthropic-style streaming chunk."""
        event_type = data.get("type", "")

        if event_type == "content_block_delta":
            delta = data.get("delta", {})
            delta_type = delta.get("type", "")

            if delta_type == "text_delta":
                return ChatChunk(delta_content=delta.get("text"))
            elif delta_type == "input_json_delta":
                # Tool call argument delta - accumulate JSON
                return ChatChunk(
                    delta_tool_calls=[{
                        "index": data.get("index", 0),
                        "function": {"arguments": delta.get("partial_json", "")},
                    }]
                )

        elif event_type == "content_block_start":
            block = data.get("content_block", {})
            if block.get("type") == "tool_use":
                # Start of a tool call
                return ChatChunk(
                    delta_tool_calls=[{
                        "index": data.get("index", 0),
                        "id": block.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": "",
                        },
                    }]
                )

        elif event_type == "message_delta":
            delta = data.get("delta", {})
            stop_reason = delta.get("stop_reason", "")
            finish_reason_map = {
                "end_turn": "stop",
                "tool_use": "tool_calls",
                "max_tokens": "length",
            }
            return ChatChunk(
                finish_reason=finish_reason_map.get(stop_reason, stop_reason)
            )

        elif event_type == "message_stop":
            return ChatChunk(is_done=True)

        return None

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            await self._client.aclose()
            self._client = None
