"""Streaming response handler for LLM API."""

from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable, Awaitable

import structlog

from esnaad.llm.client import ChatChunk, ChatResponse
from esnaad.llm.tool_calls import StreamingToolCallAccumulator
from esnaad.models.tool_call import ToolCall

logger = structlog.get_logger(__name__)


@dataclass
class StreamingState:
    """State accumulated during streaming."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    is_complete: bool = False


class StreamingHandler:
    """
    Handles streaming responses from the LLM API.

    Accumulates content and tool calls from streaming chunks,
    optionally calling callbacks for real-time updates.

    Usage:
        handler = StreamingHandler(
            on_content=lambda text: print(text, end=""),
            on_tool_call=lambda tc: print(f"Tool: {tc.name}"),
        )
        response = await handler.process(stream)
    """

    def __init__(
        self,
        on_content: Callable[[str], Awaitable[None] | None] | None = None,
        on_tool_call: Callable[[ToolCall], Awaitable[None] | None] | None = None,
        on_complete: Callable[[ChatResponse], Awaitable[None] | None] | None = None,
    ) -> None:
        """
        Initialize the streaming handler.

        Args:
            on_content: Callback for content delta (real-time text)
            on_tool_call: Callback for completed tool calls
            on_complete: Callback when streaming is complete
        """
        self.on_content = on_content
        self.on_tool_call = on_tool_call
        self.on_complete = on_complete
        self._tool_accumulator = StreamingToolCallAccumulator()
        self._state = StreamingState()

    async def process(
        self,
        stream: AsyncGenerator[ChatChunk, None],
    ) -> ChatResponse:
        """
        Process a streaming response.

        Args:
            stream: Async generator of ChatChunks

        Returns:
            Complete ChatResponse
        """
        self._reset()

        async for chunk in stream:
            await self._handle_chunk(chunk)

            if chunk.is_done:
                break

        # Finalize tool calls
        if self._tool_accumulator.has_tool_calls:
            self._state.tool_calls = self._tool_accumulator.get_tool_calls()

            # Call tool call callbacks
            if self.on_tool_call:
                for tc in self._state.tool_calls:
                    result = self.on_tool_call(tc)
                    if hasattr(result, "__await__"):
                        await result

        self._state.is_complete = True

        response = ChatResponse(
            content=self._state.content or None,
            tool_calls=self._state.tool_calls,
            finish_reason=self._state.finish_reason,
        )

        # Call completion callback
        if self.on_complete:
            result = self.on_complete(response)
            if hasattr(result, "__await__"):
                await result

        return response

    async def _handle_chunk(self, chunk: ChatChunk) -> None:
        """Handle a single chunk."""
        # Handle content delta
        if chunk.delta_content:
            self._state.content += chunk.delta_content

            if self.on_content:
                result = self.on_content(chunk.delta_content)
                if hasattr(result, "__await__"):
                    await result

        # Handle tool call deltas
        if chunk.delta_tool_calls:
            for tc_chunk in chunk.delta_tool_calls:
                self._tool_accumulator.add_chunk(tc_chunk)

        # Handle finish reason
        if chunk.finish_reason:
            self._state.finish_reason = chunk.finish_reason

    def _reset(self) -> None:
        """Reset state for new stream."""
        self._state = StreamingState()
        self._tool_accumulator.clear()

    @property
    def current_content(self) -> str:
        """Get currently accumulated content."""
        return self._state.content

    @property
    def is_complete(self) -> bool:
        """Check if streaming is complete."""
        return self._state.is_complete


async def collect_stream(
    stream: AsyncGenerator[ChatChunk, None],
) -> ChatResponse:
    """
    Simple utility to collect a stream into a ChatResponse.

    Args:
        stream: Async generator of ChatChunks

    Returns:
        Complete ChatResponse
    """
    handler = StreamingHandler()
    return await handler.process(stream)


async def stream_to_stdout(
    stream: AsyncGenerator[ChatChunk, None],
) -> ChatResponse:
    """
    Stream content to stdout and return complete response.

    Args:
        stream: Async generator of ChatChunks

    Returns:
        Complete ChatResponse
    """
    import sys

    def print_content(text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    handler = StreamingHandler(on_content=print_content)
    response = await handler.process(stream)
    sys.stdout.write("\n")
    return response
