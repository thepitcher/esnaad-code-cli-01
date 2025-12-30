"""Main CLI application entry point."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from esnaad import __version__
from esnaad.config.settings import get_settings, Settings

# Create the main Typer app
app = typer.Typer(
    name="esnaad",
    help="Esnaad Code - AI-powered agentic coding assistant",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold]Esnaad Code[/bold] version [cyan]{__version__}[/cyan]")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Esnaad Code - AI-powered agentic coding assistant."""
    pass


@app.command()
def chat(
    message: Optional[str] = typer.Argument(
        None,
        help="Initial message to send (starts interactive mode if not provided)",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Model to use (overrides config)",
    ),
    plan_mode: bool = typer.Option(
        False,
        "--plan",
        "-p",
        help="Enable plan mode (ask before executing)",
    ),
    no_clarify: bool = typer.Option(
        False,
        "--no-clarify",
        help="Skip clarification questions",
    ),
    working_dir: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Working directory (defaults to current)",
    ),
    no_stream: bool = typer.Option(
        False,
        "--no-stream",
        help="Disable streaming (useful for debugging)",
    ),
) -> None:
    """
    Start an interactive chat session or send a single message.

    Examples:

        esnaad chat "What files are in this project?"

        esnaad chat --plan "Add a new feature"

        esnaad chat  # Starts interactive mode
    """
    from esnaad.cli.commands.chat import run_chat

    settings = get_settings()

    # Override settings if options provided
    if model:
        settings.llm.model = model
    if working_dir:
        settings.working_directory = working_dir.resolve()
    if no_clarify:
        settings.orchestrator.enable_clarifications = False

    asyncio.run(
        run_chat(
            settings=settings,
            initial_message=message,
            plan_mode=plan_mode,
            stream=not no_stream,
        )
    )


@app.command()
def config(
    key: Optional[str] = typer.Argument(
        None,
        help="Configuration key to get/set",
    ),
    value: Optional[str] = typer.Argument(
        None,
        help="Value to set",
    ),
    list_all: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all configuration",
    ),
    show_env: bool = typer.Option(
        False,
        "--env",
        help="Show environment variable names",
    ),
) -> None:
    """
    View or modify configuration.

    Examples:

        esnaad config --list

        esnaad config llm.model

        esnaad config --env
    """
    from esnaad.cli.commands.config import run_config

    run_config(
        key=key,
        value=value,
        list_all=list_all,
        show_env=show_env,
    )


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration",
    ),
) -> None:
    """
    Initialize Esnaad Code in the current directory.

    Creates configuration files and sets up the project.
    """
    from esnaad.cli.commands.init import run_init

    run_init(force=force)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
