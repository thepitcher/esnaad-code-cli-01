"""Panel and status display components."""

from contextlib import contextmanager
from typing import Any, Generator

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status

from esnaad import __version__
from esnaad.config.settings import Settings
from esnaad.state.plan_mode import ExecutionMode


# ASCII art banner for Esnaad Code
BANNER = r"""
[#E57B3A]
 ███████╗███████╗███╗   ██╗ █████╗  █████╗ ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
 ██╔════╝██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
 █████╗  ███████╗██╔██╗ ██║███████║███████║██║  ██║    ██║     ██║   ██║██║  ██║█████╗
 ██╔══╝  ╚════██║██║╚██╗██║██╔══██║██╔══██║██║  ██║    ██║     ██║   ██║██║  ██║██╔══╝
 ███████╗███████║██║ ╚████║██║  ██║██║  ██║██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
 ╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
[/#E57B3A]
"""


def print_welcome(console: Console, settings: Settings) -> None:
    """Print the welcome message with banner."""
    # Print ASCII banner
    console.print(BANNER)

    # Print info panel
    console.print(
        Panel(
            f"[bold]v{__version__}[/bold] - ASKMAI-powered agentic coding assistant\n\n"
            f"Model: [#E57B3A]{settings.llm.model}[/#E57B3A]\n"
            f"Working Directory: [#E57B3A]{settings.working_directory}[/#E57B3A]\n\n"
            "[dim]Type /help for commands, /exit to quit[/dim]\n"
            "[dim]Press [bold]Shift+Tab[/bold] or type [bold]/mode[/bold] to toggle Plan Mode[/dim]",
            border_style="#E57B3A",
        )
    )
    console.print()


@contextmanager
def print_thinking(console: Console) -> Generator[Status, None, None]:
    """Show a thinking status indicator."""
    with console.status(
        "[thinking]Thinking...[/thinking]",
        spinner="dots",
    ) as status:
        yield status


def print_error(console: Console, message: str) -> None:
    """Print an error message."""
    console.print(
        Panel(
            f"[error]{message}[/error]",
            title="[bold red]Error[/bold red]",
            border_style="red",
        )
    )


def print_warning(console: Console, message: str) -> None:
    """Print a warning message."""
    console.print(
        Panel(
            f"[warning]{message}[/warning]",
            title="[bold yellow]Warning[/bold yellow]",
            border_style="yellow",
        )
    )


def print_success(console: Console, message: str) -> None:
    """Print a success message."""
    console.print(
        Panel(
            f"[success]{message}[/success]",
            title="[bold green]Success[/bold green]",
            border_style="green",
        )
    )


def print_assistant_message(console: Console, content: str) -> None:
    """Print an assistant message with markdown rendering."""
    console.print()
    console.print(Markdown(content))
    console.print()


def print_user_message(console: Console, content: str) -> None:
    """Print a user message."""
    console.print(f"[user]You:[/user] {content}")


def _format_friendly_tool_call(tool_name: str, arguments: dict | None = None) -> str:
    """
    Format a tool call in a user-friendly way like Claude Code.

    Examples:
        write_file(file_path='test.txt') -> "Write(test.txt)"
        read_file(file_path='foo.py') -> "Read(foo.py)"
        run_command(command='dir') -> "Bash(dir)"
    """
    if not arguments:
        return tool_name

    # Map tool names to friendly display names and primary parameters
    tool_mappings = {
        "write_file": ("Write", "file_path"),
        "read_file": ("Read", "file_path"),
        "edit_file": ("Edit", "file_path"),
        "create_directory": ("CreateDirectory", "path"),
        "list_directory": ("List", "path"),
        "search_files": ("SearchFiles", "pattern"),
        "search_content": ("SearchContent", "pattern"),
        "run_command": ("Bash", "command"),
        "spawn_subtasks": ("Task", None),  # Special handling
        "request_clarifications": ("AskUserQuestion", None),  # Special handling
        "write_todo": ("TodoWrite", None),  # Special handling
        "web_search": ("WebSearch", "query"),
        "web_fetch": ("WebFetch", "url"),
    }

    friendly_name, primary_param = tool_mappings.get(tool_name, (tool_name, None))

    # Special handling for specific tools
    if tool_name == "spawn_subtasks":
        subtasks = arguments.get("subtasks", [])
        count = len(subtasks) if isinstance(subtasks, list) else "?"
        return f"{friendly_name}(spawn {count} subtask{'s' if count != 1 else ''})"

    elif tool_name == "request_clarifications":
        questions = arguments.get("questions", [])
        count = len(questions) if isinstance(questions, list) else "?"
        return f"{friendly_name}({count} question{'s' if count != 1 else ''})"

    elif tool_name == "write_todo":
        todos = arguments.get("todos", [])
        count = len(todos) if isinstance(todos, list) else "?"
        return f"{friendly_name}({count} task{'s' if count != 1 else ''})"

    # Standard handling: show primary parameter
    if primary_param and primary_param in arguments:
        param_value = arguments[primary_param]
        # Truncate long values
        if isinstance(param_value, str) and len(param_value) > 50:
            param_value = param_value[:47] + "..."
        return f"{friendly_name}({param_value})"

    # Fallback: just show the friendly name
    return friendly_name


def print_tool_call(
    console: Console,
    tool_name: str,
    arguments: dict | None = None,
) -> None:
    """Print a tool call indicator in user-friendly format."""
    from esnaad.config.settings import get_settings

    settings = get_settings()

    # User-friendly display (always shown)
    friendly_display = _format_friendly_tool_call(tool_name, arguments)
    console.print(f"[tool]> {friendly_display}[/tool]")

    # Technical details (only in debug mode)
    if settings.debug and arguments:
        args_str = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
        if len(args_str) > 100:
            args_str = args_str[:100] + "..."
        console.print(f"[dim]  Debug: {tool_name}({args_str})[/dim]")


def _format_friendly_tool_result(
    tool_name: str,
    output: Any,
    error: str | None = None,
) -> tuple[str, str | None]:
    """
    Format tool result in a user-friendly way like Claude Code.

    Returns:
        Tuple of (summary_line, content_preview)

    Examples:
        write_file -> ("Wrote 11 bytes to test.txt", "Hello World")
        read_file -> ("Read 50 lines from config.py", "import os\n...")
        run_command -> ("Ran: dir", "file1.txt\nfile2.txt")
    """
    import json

    if error:
        # Error case - show error message
        return (f"Error: {error}", None)

    # Parse output if it's JSON string
    parsed_output = output
    if isinstance(output, str):
        try:
            parsed_output = json.loads(output)
        except (json.JSONDecodeError, ValueError):
            # Not JSON, use as-is
            parsed_output = output

    # Format based on tool type
    if tool_name == "write_file":
        if isinstance(parsed_output, dict):
            file_path = parsed_output.get("file_path", "")
            bytes_written = parsed_output.get("bytes_written", 0)
            created = parsed_output.get("created", False)

            # Count approximate lines
            lines = bytes_written // 50 if bytes_written > 0 else 0
            action = "Created" if created else "Wrote"

            # Get filename only
            import os
            filename = os.path.basename(file_path)

            return (f"{action} {bytes_written} bytes to {filename}", None)
        return ("File written", None)

    elif tool_name == "read_file":
        if isinstance(parsed_output, dict):
            file_path = parsed_output.get("file_path", "")
            content = parsed_output.get("content", "")

            # Count lines
            lines = len(content.split("\n")) if content else 0

            # Get filename only
            import os
            filename = os.path.basename(file_path)

            # Preview first few lines
            preview_lines = content.split("\n")[:3] if content else []
            preview = "\n".join(preview_lines)
            if len(content.split("\n")) > 3:
                preview += "\n..."

            return (f"Read {lines} lines from {filename}", preview if preview else None)
        return ("File read", None)

    elif tool_name == "edit_file":
        if isinstance(parsed_output, dict):
            file_path = parsed_output.get("file_path", "")
            replacements = parsed_output.get("replacements_made", 0)

            import os
            filename = os.path.basename(file_path)

            return (f"Made {replacements} replacement(s) in {filename}", None)
        return ("File edited", None)

    elif tool_name == "create_directory":
        if isinstance(parsed_output, dict):
            path = parsed_output.get("path", "")
            created = parsed_output.get("created", False)
            parent_created = parsed_output.get("parent_created", False)

            import os
            dirname = os.path.basename(path)

            if created:
                action = "Created directory"
                if parent_created:
                    action = "Created directory (with parents)"
            else:
                action = "Directory already exists:"

            return (f"{action} {dirname}", None)
        return ("Directory created", None)

    elif tool_name == "list_directory":
        if isinstance(parsed_output, dict):
            path = parsed_output.get("path", "")
            items = parsed_output.get("items", [])

            import os
            dirname = os.path.basename(path) or path

            # Group by type
            files = [item for item in items if item.get("type") == "file"]
            dirs = [item for item in items if item.get("type") == "directory"]

            summary = f"Found {len(files)} file(s), {len(dirs)} dir(s) in {dirname}"

            # Preview first few items
            preview_items = items[:5]
            preview_lines = []
            for item in preview_items:
                name = item.get("name", "")
                item_type = "[D]" if item.get("type") == "directory" else "[F]"
                preview_lines.append(f"{item_type} {name}")

            if len(items) > 5:
                preview_lines.append("...")

            preview = "\n".join(preview_lines) if preview_lines else None

            return (summary, preview)
        return ("Directory listed", None)

    elif tool_name == "search_files":
        if isinstance(parsed_output, dict):
            pattern = parsed_output.get("pattern", "")
            matches = parsed_output.get("matches", [])

            summary = f"Found {len(matches)} file(s) matching '{pattern}'"

            # Preview first few matches
            preview_lines = matches[:5]
            if len(matches) > 5:
                preview_lines.append("...")

            preview = "\n".join(preview_lines) if preview_lines else None

            return (summary, preview)
        return ("Files found", None)

    elif tool_name == "search_content":
        if isinstance(parsed_output, dict):
            pattern = parsed_output.get("pattern", "")
            matches = parsed_output.get("matches", [])

            summary = f"Found {len(matches)} match(es) for '{pattern}'"

            # Preview first few matches
            preview_lines = []
            for match in matches[:3]:
                file_path = match.get("file", "")
                line_num = match.get("line_number", "")
                import os
                filename = os.path.basename(file_path)
                preview_lines.append(f"{filename}:{line_num}")

            if len(matches) > 3:
                preview_lines.append("...")

            preview = "\n".join(preview_lines) if preview_lines else None

            return (summary, preview)
        return ("Content found", None)

    elif tool_name == "run_command":
        if isinstance(parsed_output, dict):
            command = parsed_output.get("command", "")
            stdout = parsed_output.get("stdout", "")
            stderr = parsed_output.get("stderr", "")
            exit_code = parsed_output.get("exit_code", 0)

            # Truncate command for display
            cmd_display = command[:50] + "..." if len(command) > 50 else command

            if exit_code == 0:
                summary = f"Ran: {cmd_display}"
            else:
                summary = f"Command failed (exit {exit_code}): {cmd_display}"

            # Show stdout/stderr preview
            output_text = stdout or stderr
            if output_text:
                lines = output_text.strip().split("\n")[:5]
                preview = "\n".join(lines)
                if len(output_text.strip().split("\n")) > 5:
                    preview += "\n..."
            else:
                preview = None

            return (summary, preview)
        return ("Command executed", None)

    elif tool_name == "write_todo":
        if isinstance(parsed_output, dict):
            todos = parsed_output.get("todos", [])
            return (f"Updated todo list ({len(todos)} tasks)", None)
        return ("Todo list updated", None)

    elif tool_name == "spawn_subtasks":
        if isinstance(parsed_output, dict):
            results = parsed_output.get("results", [])
            completed = len([r for r in results if r.get("success")])
            total = len(results)
            return (f"Completed {completed}/{total} subtasks", None)
        return ("Subtasks spawned", None)

    elif tool_name == "request_clarifications":
        if isinstance(parsed_output, dict):
            answers = parsed_output.get("answers", {})
            return (f"Received {len(answers)} answer(s)", None)
        return ("Clarifications received", None)

    elif tool_name == "web_search":
        if isinstance(parsed_output, dict):
            results = parsed_output.get("results", [])
            query = parsed_output.get("query", "")
            return (f"Found {len(results)} results for '{query}'", None)
        return ("Search completed", None)

    elif tool_name == "web_fetch":
        if isinstance(parsed_output, dict):
            url = parsed_output.get("url", "")
            content = parsed_output.get("content", "")

            # Get domain from URL
            from urllib.parse import urlparse
            domain = urlparse(url).netloc or url

            # Preview first few lines
            if content:
                lines = content.strip().split("\n")[:3]
                preview = "\n".join(lines)
                if len(content.strip().split("\n")) > 3:
                    preview += "\n..."
            else:
                preview = None

            return (f"Fetched content from {domain}", preview)
        return ("Content fetched", None)

    # Fallback for unknown tools
    if isinstance(parsed_output, dict):
        # Try to show a generic summary
        return (f"Completed successfully", None)
    elif isinstance(parsed_output, str):
        # Show string output truncated
        preview = parsed_output[:200]
        if len(parsed_output) > 200:
            preview += "..."
        return ("Completed", preview)
    else:
        return ("Completed successfully", None)


def print_tool_result(
    console: Console,
    tool_name: str,
    success: bool,
    arguments: dict[str, Any] | None = None,
    output: str | None = None,
    error: str | None = None,
) -> None:
    """Print a tool result in user-friendly format like Claude Code."""
    from esnaad.config.settings import get_settings

    settings = get_settings()

    # Get friendly name for display (with original arguments)
    friendly_name = _format_friendly_tool_call(tool_name, arguments)

    # Colored indicator (use simple ASCII for Windows console compatibility)
    if success:
        indicator = "[green]*[/green]"
        # Format friendly result
        summary, preview = _format_friendly_tool_result(tool_name, output, None)
    else:
        indicator = "[red]X[/red]"
        summary, preview = _format_friendly_tool_result(tool_name, None, error)

    # Print: ● ToolName(args)
    console.print(f"{indicator} {friendly_name}")

    # Print:   └ Summary line
    console.print(f"  [dim]L[/dim] {summary}")

    # Print preview if available (indented)
    if preview:
        # Indent each line of preview
        preview_lines = preview.split("\n")
        for line in preview_lines:
            console.print(f"     [dim]{line}[/dim]")

    # Debug mode: show technical details
    if settings.debug:
        console.print(f"     [dim italic]Debug: {tool_name} -> {output if success else error}[/dim italic]")


def print_subtask_start(console: Console, subtask_id: str, description: str) -> None:
    """Print subtask start indicator."""
    console.print(f"[dim]├─ Starting:[/dim] {description}")


def print_subtask_complete(
    console: Console,
    subtask_id: str,
    success: bool,
) -> None:
    """Print subtask completion indicator."""
    if success:
        console.print(f"[success]├─ ✓[/success] Subtask {subtask_id} complete")
    else:
        console.print(f"[error]├─ ✗[/error] Subtask {subtask_id} failed")


def print_mode_indicator(console: Console, mode: ExecutionMode) -> None:
    """
    Print the current mode indicator.

    Args:
        console: Rich console for output.
        mode: Current execution mode.
    """
    if mode == ExecutionMode.PLAN:
        console.print(
            "[bold #E57B3A][[/bold #E57B3A]"
            "[bold yellow]PLAN MODE[/bold yellow]"
            "[bold #E57B3A]][/bold #E57B3A] "
            "[dim]Tools will pause for approval[/dim]"
        )
    else:
        console.print(
            "[bold #E57B3A][[/bold #E57B3A]"
            "[bold #E57B3A]AUTO EDIT[/bold #E57B3A]"
            "[bold #E57B3A]][/bold #E57B3A] "
            "[dim]Tools execute automatically[/dim]"
        )


def print_mode_toggle(console: Console, mode: ExecutionMode) -> None:
    """
    Print mode toggle notification.

    Args:
        console: Rich console for output.
        mode: New execution mode after toggle.
    """
    if mode == ExecutionMode.PLAN:
        console.print(
            "\n[bold yellow]Switched to Plan Mode[/bold yellow] - "
            "[dim]Destructive tools will require approval[/dim]"
        )
    else:
        console.print(
            "\n[bold #E57B3A]Switched to Auto Edit[/bold #E57B3A] - "
            "[dim]All tools will execute automatically[/dim]"
        )
