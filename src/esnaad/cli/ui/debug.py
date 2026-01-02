"""Debug display utilities for LLM message inspection."""

import json
from typing import Any

from rich.console import Group
from rich.text import Text


def format_debug_messages(messages: list[dict[str, Any]]) -> Group:
    """
    Format messages for debug display.

    Shows all message details including:
    - Role and full content
    - Tool call properties (ID, type, name)
    - Tool call arguments (formatted JSON, full content)
    - Tool results (full content)
    - Message count and summary stats

    Args:
        messages: List of message dictionaries from orchestrator

    Returns:
        Rich Group containing formatted debug output
    """
    output_elements = []

    # Summary header
    summary = Text()
    summary.append(f"Total Messages: {len(messages)}\n", style="bold")
    summary.append("Message Types: ", style="dim")

    role_counts: dict[str, int] = {}
    for msg in messages:
        role = msg.get("role", "unknown")
        role_counts[role] = role_counts.get(role, 0) + 1

    summary.append(
        ", ".join([f"{role}={count}" for role, count in role_counts.items()]),
        style="cyan",
    )
    summary.append("\n" + "=" * 60 + "\n", style="dim")

    output_elements.append(summary)

    # Format each message
    for idx, msg in enumerate(messages, 1):
        output_elements.append(_format_single_message(idx, msg))
        output_elements.append(Text("─" * 60 + "\n", style="dim"))

    return Group(*output_elements)


def _format_single_message(idx: int, msg: dict[str, Any]) -> Text:
    """Format a single message for display."""
    text = Text()
    role = msg.get("role", "unknown")

    # Message header with index and role
    header_color = {
        "user": "green",
        "assistant": "#E57B3A",
        "tool": "cyan",
        "system": "yellow",
    }.get(role, "white")

    text.append(f"[{idx}] ", style="bold dim")
    text.append(f"{role.upper()}", style=f"bold {header_color}")
    text.append("\n")

    # Content
    if "content" in msg and msg["content"]:
        content = msg["content"]
        text.append("  Content: ", style="dim")
        text.append(f"{content}\n", style="white")
    elif "content" in msg and msg["content"] is None:
        text.append("  Content: ", style="dim")
        text.append("[None]\n", style="dim italic")

    # Tool calls (assistant messages)
    if "tool_calls" in msg and msg["tool_calls"]:
        text.append("  Tool Calls:\n", style="dim")
        for tc_idx, tc in enumerate(msg["tool_calls"], 1):
            tool_name = tc.get("function", {}).get("name", "unknown")
            tool_args_str = tc.get("function", {}).get("arguments", "{}")
            tool_type = tc.get("type", "function")
            tool_id = tc.get("id", "N/A")

            # Parse and format arguments (no truncation)
            try:
                tool_args = (
                    json.loads(tool_args_str)
                    if isinstance(tool_args_str, str)
                    else tool_args_str
                )
                args_formatted = json.dumps(tool_args, indent=2)
            except Exception:
                args_formatted = str(tool_args_str)

            text.append(f"    [{tc_idx}] ", style="cyan bold")
            text.append(f"{tool_name}", style="bold cyan")
            text.append("\n")
            text.append(f"      ID: ", style="dim")
            text.append(f"{tool_id}\n", style="white")
            text.append(f"      Type: ", style="dim")
            text.append(f"{tool_type}\n", style="white")
            text.append(f"      Args: ", style="dim")
            text.append(f"{args_formatted}\n", style="white")

            # Show any additional properties in the tool call object
            known_tc_fields = {"id", "type", "function"}
            extra_tc_fields = {k: v for k, v in tc.items() if k not in known_tc_fields}
            if extra_tc_fields:
                text.append(f"      Additional Properties: ", style="dim")
                text.append(f"{json.dumps(extra_tc_fields, indent=2)}\n", style="yellow")

    # Tool call ID (tool result messages)
    if "tool_call_id" in msg:
        text.append("  Tool Call ID: ", style="dim")
        text.append(f"{msg['tool_call_id']}\n", style="cyan")

    # Additional server properties (any extra fields not covered above)
    known_fields = {"role", "content", "tool_calls", "tool_call_id"}
    extra_fields = {k: v for k, v in msg.items() if k not in known_fields}

    if extra_fields:
        text.append("  Additional Server Properties:\n", style="dim")
        for key, value in extra_fields.items():
            text.append(f"    {key}: ", style="dim")
            # Format complex values as JSON
            if isinstance(value, (dict, list)):
                try:
                    formatted_value = json.dumps(value, indent=2)
                    text.append(f"{formatted_value}\n", style="yellow")
                except Exception:
                    text.append(f"{str(value)}\n", style="yellow")
            else:
                text.append(f"{value}\n", style="yellow")

    # Raw message object (for complete visibility)
    text.append("  Raw Message Object:\n", style="dim")
    try:
        raw_msg = json.dumps(msg, indent=2)
        text.append(f"{raw_msg}\n", style="dim white")
    except Exception:
        text.append(f"{str(msg)}\n", style="dim white")

    return text
