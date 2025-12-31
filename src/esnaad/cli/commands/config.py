"""Config command implementation."""

from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from esnaad.config.settings import get_settings, CONFIG_FILE, save_config
from esnaad.cli.ui.console import get_console


def run_config(
    key: str | None = None,
    value: str | None = None,
    list_all: bool = False,
    show_env: bool = False,
) -> None:
    """
    View or modify configuration.

    Args:
        key: Configuration key to get/set
        value: Value to set
        list_all: Show all configuration
        show_env: Show environment variable names
    """
    console = get_console()
    settings = get_settings()

    if show_env:
        _show_env_vars(console)
        return

    if list_all or (key is None and value is None):
        _show_all_config(console, settings)
        return

    if key and value is None:
        _show_config_key(console, settings, key)
        return

    if key and value:
        _set_config_key(console, key, value)
        return


def _show_all_config(console: Console, settings) -> None:
    """Show all configuration values."""
    # Show config file location
    console.print(f"[dim]Config file:[/dim] {CONFIG_FILE}\n")

    table = Table(title="Configuration", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    # LLM settings
    table.add_row("llm.base_url", settings.llm.base_url)
    table.add_row("llm.model", settings.llm.model)
    table.add_row("llm.temperature", str(settings.llm.temperature))
    table.add_row("llm.max_tokens", str(settings.llm.max_tokens))
    table.add_row("llm.timeout", str(settings.llm.timeout))
    table.add_row(
        "llm.api_key",
        "***" if settings.llm.api_key else "(not set)",
    )

    # Orchestrator settings
    table.add_row("orchestrator.max_iterations", str(settings.orchestrator.max_iterations))
    table.add_row("orchestrator.timeout_seconds", str(settings.orchestrator.timeout_seconds))
    table.add_row(
        "orchestrator.enable_clarifications",
        str(settings.orchestrator.enable_clarifications),
    )

    # Sub-agent settings
    table.add_row("subagent.max_iterations", str(settings.subagent.max_iterations))
    table.add_row("subagent.timeout_seconds", str(settings.subagent.timeout_seconds))
    table.add_row("subagent.max_retries", str(settings.subagent.max_retries))

    # Core settings
    table.add_row("working_directory", str(settings.working_directory))
    table.add_row("config_dir", str(settings.config_dir))
    table.add_row("debug", str(settings.debug))
    table.add_row("log_level", settings.log_level)

    console.print(table)


def _show_config_key(console: Console, settings, key: str) -> None:
    """Show a specific configuration value."""
    parts = key.split(".")

    try:
        value = settings
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                console.print(f"[red]Unknown configuration key: {key}[/red]")
                return

        # Handle secret values
        if "api_key" in key.lower() and value:
            display_value = "***"
        else:
            display_value = str(value)

        console.print(f"[cyan]{key}[/cyan] = [green]{display_value}[/green]")

    except Exception as e:
        console.print(f"[red]Error reading configuration: {e}[/red]")


def _set_config_key(console: Console, key: str, value: str) -> None:
    """Set a configuration value."""
    # Parse the key to build nested dict
    parts = key.split(".")
    config = {}
    current = config

    for i, part in enumerate(parts[:-1]):
        current[part] = {}
        current = current[part]

    # Convert value to appropriate type
    if value.lower() in ("true", "false"):
        current[parts[-1]] = value.lower() == "true"
    elif value.isdigit():
        current[parts[-1]] = int(value)
    else:
        try:
            current[parts[-1]] = float(value)
        except ValueError:
            current[parts[-1]] = value

    # Save to config file
    save_config(config)
    console.print(f"[green]Saved:[/green] {key} = {value}")
    console.print(f"[dim]Config file: {CONFIG_FILE}[/dim]")


def _show_env_vars(console: Console) -> None:
    """Show environment variable names."""
    table = Table(title="Environment Variables", show_header=True)
    table.add_column("Variable", style="cyan")
    table.add_column("Description", style="dim")

    env_vars = [
        ("ESNAAD_DEBUG", "Enable debug mode"),
        ("ESNAAD_LOG_LEVEL", "Logging level (DEBUG, INFO, WARNING, ERROR)"),
        ("ESNAAD_LLM__BASE_URL", "LLM API base URL"),
        ("ESNAAD_LLM__API_KEY", "LLM API key"),
        ("ESNAAD_LLM__MODEL", "Model name"),
        ("ESNAAD_LLM__TEMPERATURE", "Generation temperature"),
        ("ESNAAD_LLM__MAX_TOKENS", "Maximum tokens"),
        ("ESNAAD_LLM__TIMEOUT", "Request timeout"),
        ("ESNAAD_ORCHESTRATOR__MAX_ITERATIONS", "Max orchestrator iterations"),
        ("ESNAAD_ORCHESTRATOR__TIMEOUT_SECONDS", "Orchestrator timeout"),
        ("ESNAAD_ORCHESTRATOR__ENABLE_CLARIFICATIONS", "Enable clarifications"),
        ("ESNAAD_SUBAGENT__MAX_ITERATIONS", "Max sub-agent iterations"),
        ("ESNAAD_SUBAGENT__TIMEOUT_SECONDS", "Sub-agent timeout"),
        ("ESNAAD_SUBAGENT__MAX_RETRIES", "Max sub-agent retries"),
        ("ESNAAD_TOOLS__MAX_FILE_SIZE_BYTES", "Max file size to read"),
        ("ESNAAD_TOOLS__COMMAND_TIMEOUT", "Command execution timeout"),
    ]

    for var, desc in env_vars:
        table.add_row(var, desc)

    console.print(table)
    console.print(
        f"\n[dim]Configuration priority (later overrides earlier):[/dim]\n"
        f"  1. Default values\n"
        f"  2. {CONFIG_FILE}\n"
        f"  3. Environment variables (ESNAAD_*)\n"
    )
