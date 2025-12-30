"""Tool call parsing utilities."""

import json
from typing import Any

import structlog

from esnaad.models.tool_call import ToolCall

logger = structlog.get_logger(__name__)


def parse_tool_calls(raw_tool_calls: list[dict[str, Any]]) -> list[ToolCall]:
    """
    Parse raw tool call data from API response.

    Args:
        raw_tool_calls: List of tool call dicts from API

    Returns:
        List of parsed ToolCall objects
    """
    tool_calls = []
    for raw in raw_tool_calls:
        try:
            tool_call = ToolCall.from_openai_format(raw)
            tool_calls.append(tool_call)
        except Exception as e:
            logger.warning(
                "Failed to parse tool call",
                raw=raw,
                error=str(e),
            )
            continue
    return tool_calls


def parse_tool_arguments(arguments_str: str) -> dict[str, Any]:
    """
    Parse tool arguments from JSON string.

    Args:
        arguments_str: JSON string of arguments

    Returns:
        Parsed arguments dict
    """
    if not arguments_str:
        return {}

    try:
        return json.loads(arguments_str)
    except json.JSONDecodeError as e:
        logger.warning(
            "Failed to parse tool arguments",
            arguments=arguments_str[:200],
            error=str(e),
        )
        return {}


def merge_streaming_tool_calls(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merge tool call chunks from streaming response.

    In streaming mode, tool calls come in pieces that need to be
    assembled into complete tool calls.

    Args:
        chunks: List of tool call delta chunks

    Returns:
        List of complete tool call dicts
    """
    # Group chunks by index
    by_index: dict[int, dict[str, Any]] = {}

    for chunk in chunks:
        index = chunk.get("index", 0)

        if index not in by_index:
            by_index[index] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }

        # Merge chunk data
        current = by_index[index]

        if "id" in chunk:
            current["id"] = chunk["id"]

        if "function" in chunk:
            func = chunk["function"]
            if "name" in func:
                current["function"]["name"] = func["name"]
            if "arguments" in func:
                current["function"]["arguments"] += func["arguments"]

    return list(by_index.values())


class StreamingToolCallAccumulator:
    """
    Accumulates streaming tool call chunks into complete tool calls.

    Usage:
        accumulator = StreamingToolCallAccumulator()
        for chunk in stream:
            if chunk.delta_tool_calls:
                for tc in chunk.delta_tool_calls:
                    accumulator.add_chunk(tc)
        tool_calls = accumulator.get_tool_calls()
    """

    def __init__(self) -> None:
        self._chunks: list[dict[str, Any]] = []
        self._by_index: dict[int, dict[str, Any]] = {}

    def add_chunk(self, chunk: dict[str, Any]) -> None:
        """Add a tool call chunk."""
        self._chunks.append(chunk)

        index = chunk.get("index", 0)

        if index not in self._by_index:
            self._by_index[index] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }

        current = self._by_index[index]

        if "id" in chunk:
            current["id"] = chunk["id"]

        if "function" in chunk:
            func = chunk["function"]
            if "name" in func:
                current["function"]["name"] = func["name"]
            if "arguments" in func:
                current["function"]["arguments"] += func["arguments"]

    def get_tool_calls(self) -> list[ToolCall]:
        """Get accumulated tool calls."""
        raw_calls = list(self._by_index.values())
        return parse_tool_calls(raw_calls)

    def clear(self) -> None:
        """Clear accumulated chunks."""
        self._chunks.clear()
        self._by_index.clear()

    @property
    def has_tool_calls(self) -> bool:
        """Check if any tool calls have been accumulated."""
        return len(self._by_index) > 0
