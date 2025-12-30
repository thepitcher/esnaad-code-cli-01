"""Init command implementation."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from esnaad.cli.ui.console import get_console


def run_init(force: bool = False) -> None:
    """
    Initialize Esnaad Code in the current directory.

    Args:
        force: Overwrite existing configuration
    """
    console = get_console()
    cwd = Path.cwd()

    console.print(f"\n[bold]Initializing Esnaad Code in:[/bold] {cwd}\n")

    # Check for existing .env file
    env_file = cwd / ".env"
    if env_file.exists() and not force:
        console.print(
            "[yellow]Warning:[/yellow] .env file already exists. "
            "Use --force to overwrite."
        )
    else:
        _create_env_file(env_file, console)

    # Check for existing AGENT.md file
    agent_file = cwd / "AGENT.md"
    if agent_file.exists() and not force:
        console.print(
            "[yellow]Warning:[/yellow] AGENT.md file already exists. "
            "Use --force to overwrite."
        )
    else:
        _create_agent_file(agent_file, console)

    # Create .esnaad directory
    esnaad_dir = cwd / ".esnaad"
    esnaad_dir.mkdir(exist_ok=True)
    console.print(f"[green]Created:[/green] {esnaad_dir}")

    console.print(
        Panel(
            "[bold green]Initialization complete![/bold green]\n\n"
            "Next steps:\n"
            "1. Edit .env to configure your LLM provider\n"
            "2. Edit AGENT.md to describe your project\n"
            "3. Run [cyan]esnaad chat[/cyan] to start coding!",
            title="[bold]Success[/bold]",
            border_style="green",
        )
    )


def _create_env_file(path: Path, console: Console) -> None:
    """Create a default .env file."""
    content = """# Esnaad Code Configuration
# See: esnaad config --env for all options

# LLM Settings
ESNAAD_LLM__BASE_URL=http://localhost:3000/api
ESNAAD_LLM__MODEL=gpt-4
# ESNAAD_LLM__API_KEY=your-api-key

# Orchestrator Settings
ESNAAD_ORCHESTRATOR__MAX_ITERATIONS=50
ESNAAD_ORCHESTRATOR__ENABLE_CLARIFICATIONS=true

# Debug (set to true for verbose output)
ESNAAD_DEBUG=false
"""
    path.write_text(content)
    console.print(f"[green]Created:[/green] {path}")


def _create_agent_file(path: Path, console: Console) -> None:
    """Create a default AGENT.md file."""
    content = """# AGENT.md - Project Context for Esnaad Code

## Project Overview

<!-- Describe your project here -->

This project is...

## Technology Stack

- Language:
- Framework:
- Database:

## Code Style

- Formatting:
- Naming conventions:
- Testing approach:

## Important Files

- Entry point:
- Configuration:
- Main modules:

## Common Tasks

### Running the project

```bash
# Add your run commands here
```

### Running tests

```bash
# Add your test commands here
```

## Notes for the AI

<!-- Any special instructions or context for the AI assistant -->

- Prefer X over Y when...
- Always check Z before...
"""
    path.write_text(content)
    console.print(f"[green]Created:[/green] {path}")
