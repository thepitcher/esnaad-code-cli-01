"""Panel and status display components."""

from contextlib import contextmanager
from typing import Generator

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


def print_tool_call(
    console: Console,
    tool_name: str,
    arguments: dict | None = None,
) -> None:
    """Print a tool call indicator."""
    args_str = ""
    if arguments:
        args_str = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
        if len(args_str) > 80:
            args_str = args_str[:80] + "..."

    console.print(f"[tool]→ {tool_name}[/tool]({args_str})")


def print_tool_result(
    console: Console,
    tool_name: str,
    success: bool,
    output: str | None = None,
    error: str | None = None,
) -> None:
    """Print a tool result."""
    if success:
        status = "[success]✓[/success]"
        message = output[:200] + "..." if output and len(output) > 200 else output
    else:
        status = "[error]✗[/error]"
        message = error

    console.print(f"  {status} {tool_name}: {message}")


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
