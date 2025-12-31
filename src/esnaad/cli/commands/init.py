"""Init command implementation."""

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from esnaad.cli.ui.console import get_console
from esnaad.config.settings import CONFIG_DIR, CONFIG_FILE, save_config


def run_init(force: bool = False) -> None:
    """
    Initialize Esnaad Code configuration.

    Creates config.json in ~/.esnaad/ and optionally ESNAAD.md in current directory.

    Args:
        force: Overwrite existing configuration
    """
    console = get_console()

    console.print("\n[bold #E57B3A]Esnaad Code Initialization[/bold #E57B3A]\n")

    # Create config directory
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"[dim]Config directory:[/dim] {CONFIG_DIR}")

    # Check for existing config file
    if CONFIG_FILE.exists() and not force:
        console.print(
            f"\n[yellow]Config file already exists:[/yellow] {CONFIG_FILE}\n"
            "Use --force to overwrite, or edit manually."
        )
        _show_current_config(console)
    else:
        _create_config_file(console)

    # Ask about project rules file
    cwd = Path.cwd()
    rules_file = cwd / "ESNAAD.md"

    console.print()
    if rules_file.exists() and not force:
        console.print(f"[dim]Project rules file exists:[/dim] {rules_file}")
    else:
        create_rules = Prompt.ask(
            "Create ESNAAD.md rules file in current directory?",
            choices=["y", "n"],
            default="y",
        )
        if create_rules.lower() == "y":
            _create_rules_file(rules_file, console)

    console.print(
        Panel(
            "[bold green]Initialization complete![/bold green]\n\n"
            f"[bold]Config location:[/bold] {CONFIG_FILE}\n\n"
            "Next steps:\n"
            f"1. Edit {CONFIG_FILE} to configure your LLM provider\n"
            "2. Create/edit ESNAAD.md in your project for project-specific rules\n"
            "3. Run [cyan]esnaad chat[/cyan] to start coding!\n\n"
            "[dim]Or use presets: esnaad core, esnaad ui[/dim]",
            title="[bold #E57B3A]Success[/bold #E57B3A]",
            border_style="#E57B3A",
        )
    )


def _create_config_file(console: Console) -> None:
    """Create the config.json file with user input."""
    console.print("\n[bold]LLM Configuration[/bold]\n")

    # Get LLM settings from user
    base_url = Prompt.ask(
        "LLM API Base URL",
        default="http://localhost:3000/api",
    )

    model = Prompt.ask(
        "Model name",
        default="gpt-4",
    )

    api_key = Prompt.ask(
        "API Key (leave empty if not required)",
        default="",
        password=True,
    )

    verify_ssl = Prompt.ask(
        "Verify SSL certificates?",
        choices=["y", "n"],
        default="y",
    )

    # Build config
    config = {
        "llm": {
            "base_url": base_url,
            "model": model,
            "verify_ssl": verify_ssl.lower() == "y",
        }
    }

    if api_key:
        config["llm"]["api_key"] = api_key

    # Save config
    save_config(config)
    console.print(f"\n[green]Created:[/green] {CONFIG_FILE}")


def _show_current_config(console: Console) -> None:
    """Show current configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Hide API key
            if "llm" in config and "api_key" in config["llm"]:
                config["llm"]["api_key"] = "***hidden***"

            console.print("\n[bold]Current configuration:[/bold]")
            console.print_json(data=config)
        except (json.JSONDecodeError, IOError):
            console.print("[red]Error reading config file[/red]")


def _create_rules_file(path: Path, console: Console) -> None:
    """Create a default ESNAAD.md rules file."""
    content = """# Esnaad Code Project Rules

## Build Verification

After ANY file modification (create, update, or delete), you MUST:

1. Run the build command to verify compilation succeeds
2. If the build fails, fix the errors before proceeding
3. Do not consider a task complete until the build passes

### Build Command

Run from the working directory root:

```bash
# Add your build command here, e.g.:
# npm run build
# dotnet build
# .\\tools\\nant\\NAnt.exe build
```

### When to Skip Build

You may skip build verification only when:
- Modifying documentation files (.md, .txt, .rst)
- Modifying configuration files (.env, .gitignore)
- The user explicitly says to skip verification

## Code Quality

- All code files must have valid syntax
- Follow existing code patterns and conventions
- Write clear, maintainable code

## Project-Specific Guidelines

<!-- Add your project-specific rules here -->

"""
    path.write_text(content, encoding="utf-8")
    console.print(f"[green]Created:[/green] {path}")
