"""Chat command implementation."""

import asyncio
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from esnaad.config.settings import Settings
from esnaad.cli.ui.console import get_console
from esnaad.cli.ui.panels import (
    print_welcome,
    print_thinking,
    print_error,
    print_assistant_message,
    print_tool_call,
    print_tool_result,
)
from esnaad.cli.ui.prompt import get_user_input
from esnaad.cli.ui.clarification import create_clarification_handler
from esnaad.llm.client import LLMClient
from esnaad.core.orchestrator import Orchestrator, OrchestratorConfig
from esnaad.models.tool_call import ToolCall, ToolResult
from esnaad.utils.logging import setup_logging


async def run_chat(
    settings: Settings,
    initial_message: str | None = None,
    plan_mode: bool = False,
    stream: bool = True,
) -> None:
    """
    Run the chat interface.

    Args:
        settings: Application settings
        initial_message: Optional initial message to send
        plan_mode: Whether to enable plan mode
        stream: Whether to enable streaming responses
    """
    console = get_console()

    # Setup logging - only show logs in debug mode
    if settings.debug:
        setup_logging(level=settings.log_level)
    else:
        setup_logging(level="ERROR")  # Suppress info/warning logs

    # Print welcome message
    print_welcome(console, settings)

    # Initialize LLM client
    async with LLMClient.from_settings(settings.llm) as client:
        # Create clarification handler
        clarification_handler = await create_clarification_handler(console)

        # Create orchestrator config with streaming
        from esnaad.core.orchestrator import OrchestratorConfig
        config = OrchestratorConfig(
            max_iterations=settings.orchestrator.max_iterations,
            timeout_seconds=settings.orchestrator.timeout_seconds,
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            enable_clarifications=settings.orchestrator.enable_clarifications,
            stream=stream,
        )

        # Create orchestrator with callbacks
        orchestrator = Orchestrator(
            llm_client=client,
            settings=settings,
            config=config,
            on_content=lambda content: _on_content(console, content),
            on_tool_call=lambda tc: _on_tool_call(console, tc),
            on_tool_result=lambda tr: _on_tool_result(console, tr),
            clarification_handler=clarification_handler,
            on_content_delta=lambda delta: _on_content_delta(console, delta) if stream else None,
        )

        # Handle initial message if provided
        if initial_message:
            await process_with_orchestrator(
                orchestrator=orchestrator,
                user_input=initial_message,
                console=console,
            )

        # Interactive loop
        while True:
            try:
                # Get user input
                user_input = await get_user_input(console)

                if user_input is None:
                    # User wants to exit
                    console.print("\n[dim]Goodbye![/dim]")
                    break

                if not user_input.strip():
                    continue

                # Handle special commands
                if user_input.startswith("/"):
                    should_continue = await handle_command(
                        user_input,
                        console,
                        settings,
                        orchestrator,
                    )
                    if not should_continue:
                        break
                    continue

                # Process the message
                await process_with_orchestrator(
                    orchestrator=orchestrator,
                    user_input=user_input,
                    console=console,
                )

            except KeyboardInterrupt:
                console.print("\n[dim]Use /exit or Ctrl+D to quit[/dim]")
                continue

        # Cleanup
        await orchestrator.cleanup()


async def process_with_orchestrator(
    orchestrator: Orchestrator,
    user_input: str,
    console: Console,
) -> None:
    """Process a user message using the orchestrator."""
    global _streaming_in_progress

    try:
        # Run orchestrator
        result = await orchestrator.run(user_input)

        # End streaming line if needed
        if _streaming_in_progress:
            console.print()  # Newline after streaming content
            _reset_streaming_state()

        # Display final response (only if not streaming - streaming already printed)
        if result.content and not orchestrator.config.stream:
            print_assistant_message(console, result.content)

        # Show status for non-success
        if not result.is_success:
            if result.error:
                print_error(console, result.error)

    except Exception as e:
        _reset_streaming_state()
        print_error(console, f"Error: {e}")


# Track if we're currently streaming (to avoid duplicate output)
_streaming_in_progress = False


def _on_content(console: Console, content: str) -> None:
    """Callback for complete content (non-streaming)."""
    # Only used in non-streaming mode
    pass


def _on_content_delta(console: Console, delta: str) -> None:
    """Callback for streaming content deltas."""
    global _streaming_in_progress
    if not _streaming_in_progress:
        _streaming_in_progress = True
        console.print()  # Start new line before streaming
    console.print(delta, end="", markup=False)


def _reset_streaming_state() -> None:
    """Reset streaming state after response completes."""
    global _streaming_in_progress
    if _streaming_in_progress:
        _streaming_in_progress = False


def _on_tool_call(console: Console, tool_call: ToolCall) -> None:
    """Callback when a tool is called."""
    _reset_streaming_state()  # End any streaming before tool output
    print_tool_call(console, tool_call.name, tool_call.arguments)


def _on_tool_result(console: Console, result: ToolResult) -> None:
    """Callback when a tool returns."""
    print_tool_result(
        console,
        result.tool_name,
        result.is_success,
        output=result.to_content()[:100] if result.is_success else None,
        error=result.error,
    )


async def handle_command(
    command: str,
    console: Console,
    settings: Settings,
    orchestrator: Orchestrator,
) -> bool:
    """
    Handle a slash command.

    Returns True to continue, False to exit.
    """
    cmd = command.lower().strip()

    if cmd in ("/exit", "/quit", "/q"):
        console.print("[dim]Goodbye![/dim]")
        return False

    elif cmd in ("/help", "/h", "/?"):
        console.print(
            Panel(
                """[bold]Available Commands:[/bold]

/help, /h     - Show this help message
/exit, /quit  - Exit the chat
/clear        - Clear conversation history
/config       - Show current configuration
/model <name> - Change the model
/tools        - List available tools
""",
                title="[bold]Help[/bold]",
                border_style="blue",
            )
        )

    elif cmd == "/clear":
        orchestrator.clear_history()
        console.print("[green]Conversation cleared[/green]")

    elif cmd == "/config":
        console.print(
            Panel(
                f"""[bold]Current Configuration:[/bold]

Model: {settings.llm.model}
Base URL: {settings.llm.base_url}
Working Dir: {settings.working_directory}
Max Iterations: {settings.orchestrator.max_iterations}
Timeout: {settings.orchestrator.timeout_seconds}s
""",
                title="[bold]Configuration[/bold]",
                border_style="blue",
            )
        )

    elif cmd.startswith("/model "):
        new_model = cmd[7:].strip()
        if new_model:
            settings.llm.model = new_model
            orchestrator.config.model = new_model
            console.print(f"[green]Model changed to: {new_model}[/green]")
        else:
            console.print("[red]Usage: /model <model_name>[/red]")

    elif cmd == "/tools":
        from esnaad.tools.registry import ToolRegistry

        tools = ToolRegistry.get_all()
        tool_list = "\n".join(
            f"  [cyan]{t.name}[/cyan]: {t.description[:60]}..."
            for t in tools
        )
        console.print(
            Panel(
                f"[bold]Available Tools ({len(tools)}):[/bold]\n\n{tool_list}",
                title="[bold]Tools[/bold]",
                border_style="blue",
            )
        )

    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")
        console.print("[dim]Type /help for available commands[/dim]")

    return True
