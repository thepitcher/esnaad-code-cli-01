"""Rich console singleton and utilities."""

from functools import lru_cache

from rich.console import Console
from rich.theme import Theme

# Custom theme for Esnaad Code
ESNAAD_THEME = Theme(
    {
        "info": "dim cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "user": "bold blue",
        "assistant": "green",
        "tool": "yellow",
        "thinking": "dim italic",
        "code": "cyan",
    }
)


@lru_cache
def get_console() -> Console:
    """Get the singleton Rich console instance."""
    return Console(theme=ESNAAD_THEME)


def create_console(**kwargs) -> Console:
    """Create a new console with the Esnaad theme."""
    return Console(theme=ESNAAD_THEME, **kwargs)
