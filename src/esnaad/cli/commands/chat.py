"""Chat command implementation."""

import asyncio
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.status import Status

from esnaad.config.settings import Settings
from esnaad.cli.ui.console import get_console
from esnaad.cli.ui.panels import (
    print_welcome,
    print_thinking,
    print_error,
    print_assistant_message,
    print_tool_call,
    print_tool_result,
    print_mode_indicator,
    print_mode_toggle,
)
from esnaad.cli.ui.prompt import get_user_input, get_user_input_with_mode
from esnaad.cli.ui.clarification import create_clarification_handler
from esnaad.cli.ui.tool_approval import ToolApprovalUI, ApprovalDecision
from esnaad.llm.client import LLMClient
from esnaad.core.orchestrator import Orchestrator, OrchestratorConfig
from esnaad.models.tool_call import ToolCall, ToolResult
from esnaad.state.plan_mode import PlanModeState, ExecutionMode
from esnaad.tools.registry import ToolRegistry
from esnaad.utils.logging import setup_logging


async def run_chat(
    settings: Settings,
    initial_message: str | None = None,
    plan_mode: bool = False,
    stream: bool = True,
    preset_rules: str | None = None,
) -> None:
    """
    Run the chat interface.

    Args:
        settings: Application settings
        initial_message: Optional initial message to send
        plan_mode: Whether to enable plan mode
        stream: Whether to enable streaming responses
        preset_rules: Pre-loaded rules content (skips loading from working dir)
    """
    from esnaad.config.rules import RulesLoader

    console = get_console()

    # Load rules eagerly (either preset or from working directory)
    if preset_rules is None:
        # Load from working directory
        preset_rules = await RulesLoader.load_rules(settings.working_directory)

    # Setup logging - only show logs in debug mode
    if settings.debug:
        setup_logging(level=settings.log_level)
    else:
        setup_logging(level="ERROR")  # Suppress info/warning logs

    # Print welcome message
    print_welcome(console, settings)

    # Initialize plan mode state
    plan_mode_state = PlanModeState(
        mode=ExecutionMode.PLAN if plan_mode else ExecutionMode.AUTO_EDIT
    )

    # Create tool approval UI
    approval_ui = ToolApprovalUI(console)

    # Initialize LLM client
    async with LLMClient.from_settings(settings.llm) as client:
        # Create clarification handler
        clarification_handler = await create_clarification_handler(console)

        # Tool approval handler for plan mode
        async def handle_tool_approval(tool_call: ToolCall) -> bool:
            """Handle tool approval request in plan mode."""
            tool = ToolRegistry.get(tool_call.name)
            result = await approval_ui.request_approval(
                tool_call=tool_call,
                tool_description=tool.description if tool else "",
            )

            # Handle switch to Auto Edit mode
            if result.decision == ApprovalDecision.SWITCH_TO_AUTO_EDIT:
                # Switch to Auto Edit mode
                plan_mode_state.mode = ExecutionMode.AUTO_EDIT
                if plan_mode_state.on_mode_change:
                    plan_mode_state.on_mode_change(ExecutionMode.AUTO_EDIT)
                # Approve this tool and all future tools (since we're now in Auto Edit)
                return True

            return result.decision in (
                ApprovalDecision.APPROVE,
                ApprovalDecision.APPROVE_ALL,
            )

        # Mode change callback
        def on_mode_change(new_mode: ExecutionMode) -> None:
            """Handle mode change from Shift+Tab."""
            print_mode_toggle(console, new_mode)
            orchestrator.set_plan_mode(new_mode == ExecutionMode.PLAN)

        plan_mode_state.on_mode_change = on_mode_change

        # Create orchestrator config with streaming and plan_mode
        config = OrchestratorConfig(
            max_iterations=settings.orchestrator.max_iterations,
            timeout_seconds=settings.orchestrator.timeout_seconds,
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            enable_clarifications=settings.orchestrator.enable_clarifications,
            stream=stream,
            plan_mode=plan_mode_state.is_plan_mode,
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
            on_thinking_start=lambda: _on_thinking_start(console),
            on_thinking_end=lambda: _on_thinking_end(console),
            on_tool_approval=handle_tool_approval,
            preset_rules=preset_rules,
        )

        # Show initial mode indicator
        print_mode_indicator(console, plan_mode_state.mode)

        # Handle initial message if provided
        if initial_message:
            approval_ui.reset_session()
            await process_with_orchestrator(
                orchestrator=orchestrator,
                user_input=initial_message,
                console=console,
            )

        # Interactive loop
        while True:
            try:
                # Get user input with mode toggle support
                user_input = await get_user_input_with_mode(
                    console,
                    plan_mode_state,
                    on_mode_toggle=on_mode_change,
                )

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
                        plan_mode_state,
                    )
                    if not should_continue:
                        break
                    continue

                # Reset approval session for new message
                approval_ui.reset_session()

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

# Track the thinking spinner
_thinking_spinner: Status | None = None


def _on_content(console: Console, content: str) -> None:
    """Callback for complete content (non-streaming)."""
    # Only used in non-streaming mode
    pass


def _on_content_delta(console: Console, delta: str) -> None:
    """Callback for streaming content deltas."""
    global _streaming_in_progress, _thinking_spinner
    # Stop spinner if still running (first content received)
    if _thinking_spinner is not None:
        _thinking_spinner.stop()
        _thinking_spinner = None
    if not _streaming_in_progress:
        _streaming_in_progress = True
        console.print()  # Start new line before streaming
    console.print(delta, end="", markup=False)


def _reset_streaming_state() -> None:
    """Reset streaming state after response completes."""
    global _streaming_in_progress
    if _streaming_in_progress:
        _streaming_in_progress = False


def _on_thinking_start(console: Console) -> None:
    """Callback when LLM request starts - show spinner."""
    global _thinking_spinner
    _thinking_spinner = console.status(
        "[thinking]Esnaad Code is thinking...[/thinking]",
        spinner="dots",
    )
    _thinking_spinner.start()


def _on_thinking_end(console: Console) -> None:
    """Callback when LLM request ends - hide spinner."""
    global _thinking_spinner
    if _thinking_spinner is not None:
        _thinking_spinner.stop()
        _thinking_spinner = None


def _on_tool_call(console: Console, tool_call: ToolCall) -> None:
    """Callback when a tool is called."""
    global _thinking_spinner
    # Stop spinner if still running
    if _thinking_spinner is not None:
        _thinking_spinner.stop()
        _thinking_spinner = None
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
    plan_mode_state: PlanModeState | None = None,
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
/rules        - Show currently active rules
/mode         - Toggle Plan Mode / Auto Edit
""",
                title="[bold #E57B3A]Help[/bold #E57B3A]",
                border_style="#E57B3A",
            )
        )

    elif cmd == "/clear":
        orchestrator.clear_history()
        console.print("[green]Conversation cleared[/green]")

    elif cmd == "/config":
        from esnaad.config.settings import CONFIG_FILE
        console.print(
            Panel(
                f"""[bold]Current Configuration:[/bold]

Config File: {CONFIG_FILE}

Model: {settings.llm.model}
Base URL: {settings.llm.base_url}
Working Dir: {settings.working_directory}
Max Iterations: {settings.orchestrator.max_iterations}
Timeout: {settings.orchestrator.timeout_seconds}s
""",
                title="[bold #E57B3A]Configuration[/bold #E57B3A]",
                border_style="#E57B3A",
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
                title="[bold #E57B3A]Tools[/bold #E57B3A]",
                border_style="#E57B3A",
            )
        )

    elif cmd == "/rules":
        rules_content = orchestrator._rules
        if rules_content:
            # Truncate if too long for display
            if len(rules_content) > 2000:
                display_content = rules_content[:2000] + "\n\n[dim]... (truncated)[/dim]"
            else:
                display_content = rules_content
            console.print(
                Panel(
                    Markdown(display_content),
                    title="[bold #E57B3A]Active Rules[/bold #E57B3A]",
                    border_style="#E57B3A",
                )
            )
        else:
            console.print("[dim]No rules loaded[/dim]")

    elif cmd == "/mode":
        if plan_mode_state is not None:
            new_mode = plan_mode_state.toggle()
            # Note: toggle() already calls the on_mode_change callback
            # which prints the toggle message and updates orchestrator
        else:
            console.print("[dim]Mode toggle not available[/dim]")

    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")
        console.print("[dim]Type /help for available commands[/dim]")

    return True
