"""User input prompt handling."""

import asyncio
from typing import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from rich.console import Console

from esnaad.config.settings import get_settings
from esnaad.state.plan_mode import ExecutionMode, PlanModeState


# Prompt style (Claude Code orange)
PROMPT_STYLE = Style.from_dict(
    {
        "prompt": "bold #E57B3A",
        "continuation": "dim",
    }
)


def create_prompt_session() -> PromptSession:
    """Create a prompt session with history."""
    settings = get_settings()
    history_file = settings.config_dir / "history.txt"

    return PromptSession(
        history=FileHistory(str(history_file)),
        style=PROMPT_STYLE,
        enable_history_search=True,
        multiline=False,
    )


async def get_user_input(
    console: Console,
    prompt_text: str = "> ",
) -> str | None:
    """
    Get input from the user.

    Args:
        console: Rich console instance
        prompt_text: Prompt text to display

    Returns:
        User input string, or None if user wants to exit
    """
    session = create_prompt_session()

    try:
        # Run prompt_toolkit in a thread since it's blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: session.prompt(prompt_text),
        )
        return result

    except EOFError:
        # Ctrl+D pressed
        return None

    except KeyboardInterrupt:
        # Ctrl+C pressed - don't exit, just return empty
        return ""


async def get_confirmation(
    console: Console,
    message: str,
    default: bool = True,
) -> bool:
    """
    Get a yes/no confirmation from the user.

    Args:
        console: Rich console instance
        message: Message to display
        default: Default value if user just presses Enter

    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    prompt = f"{message} [{default_str}]: "

    session = create_prompt_session()

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: session.prompt(prompt),
        )

        result = result.strip().lower()

        if not result:
            return default

        return result in ("y", "yes", "true", "1")

    except (EOFError, KeyboardInterrupt):
        return False


async def get_selection(
    console: Console,
    message: str,
    options: list[str],
    default: int = 0,
) -> int | None:
    """
    Get a selection from a list of options.

    Args:
        console: Rich console instance
        message: Message to display
        options: List of options
        default: Default option index

    Returns:
        Selected option index, or None if cancelled
    """
    console.print(f"\n{message}\n")

    for i, option in enumerate(options):
        marker = ">" if i == default else " "
        console.print(f"  {marker} [{i + 1}] {option}")

    console.print()

    session = create_prompt_session()
    prompt = f"Selection [1-{len(options)}] (default: {default + 1}): "

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: session.prompt(prompt),
        )

        result = result.strip()

        if not result:
            return default

        try:
            index = int(result) - 1
            if 0 <= index < len(options):
                return index
            else:
                console.print("[error]Invalid selection[/error]")
                return None
        except ValueError:
            console.print("[error]Invalid selection[/error]")
            return None

    except (EOFError, KeyboardInterrupt):
        return None


async def get_multiline_input(
    console: Console,
    prompt_text: str = "Enter text (Ctrl+D to finish):\n",
) -> str | None:
    """
    Get multiline input from the user.

    Args:
        console: Rich console instance
        prompt_text: Initial prompt text

    Returns:
        Multiline string, or None if cancelled
    """
    console.print(f"[dim]{prompt_text}[/dim]")

    session = PromptSession(
        multiline=True,
        prompt_continuation="... ",
        style=PROMPT_STYLE,
    )

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: session.prompt(""),
        )
        return result

    except (EOFError, KeyboardInterrupt):
        return None


def create_prompt_session_with_mode(
    plan_mode_state: PlanModeState,
    on_mode_toggle: Callable[[ExecutionMode], None] | None = None,
) -> PromptSession:
    """
    Create a prompt session with Shift+Tab mode toggle support.

    Args:
        plan_mode_state: The plan mode state to toggle.
        on_mode_toggle: Callback invoked when mode is toggled.

    Returns:
        A PromptSession with custom key bindings.
    """
    settings = get_settings()
    history_file = settings.config_dir / "history.txt"

    # Create key bindings
    kb = KeyBindings()

    @kb.add(Keys.BackTab)  # Shift+Tab
    def toggle_mode(event):
        """Toggle between Plan and Auto Edit modes."""
        # toggle() already calls plan_mode_state.on_mode_change internally
        # so we don't need to call on_mode_toggle here (would cause duplicate)
        plan_mode_state.toggle()
        # Invalidate the app to redraw prompt with new mode prefix
        event.app.invalidate()

    return PromptSession(
        history=FileHistory(str(history_file)),
        style=PROMPT_STYLE,
        enable_history_search=True,
        multiline=False,
        key_bindings=kb,
    )


async def get_user_input_with_mode(
    console: Console,
    plan_mode_state: PlanModeState,
    on_mode_toggle: Callable[[ExecutionMode], None] | None = None,
    prompt_text: str = "> ",
) -> str | None:
    """
    Get input from the user with mode toggle support.

    Pressing Shift+Tab toggles between Plan Mode and Auto Edit.
    The prompt updates dynamically to show [PLAN] prefix when in plan mode.

    Args:
        console: Rich console instance.
        plan_mode_state: The plan mode state.
        on_mode_toggle: Callback invoked when mode is toggled.
        prompt_text: Prompt text to display.

    Returns:
        User input string, or None if user wants to exit.
    """
    session = create_prompt_session_with_mode(
        plan_mode_state=plan_mode_state,
        on_mode_toggle=on_mode_toggle,
    )

    # Dynamic prompt function - called each time prompt is rendered
    def get_prompt():
        mode_prefix = "[PLAN] " if plan_mode_state.is_plan_mode else ""
        return f"{mode_prefix}{prompt_text}"

    try:
        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            lambda: session.prompt(get_prompt),
        )
        return result

    except EOFError:
        # Ctrl+D pressed
        return None

    except KeyboardInterrupt:
        # Ctrl+C pressed - don't exit, just return empty
        return ""
