"""Autocomplete completers for Esnaad Code CLI."""

from prompt_toolkit.completion import WordCompleter


def create_slash_command_completer() -> WordCompleter:
    """
    Create a completer for slash commands.

    Returns:
        WordCompleter configured with all slash commands and their aliases
    """
    commands = [
        "/help",
        "/h",
        "/?",
        "/exit",
        "/quit",
        "/q",
        "/clear",
        "/config",
        "/model",
        "/tools",
        "/rules",
        "/mode",
        "/debug-last-messages",
    ]

    return WordCompleter(
        commands,
        ignore_case=True,
        sentence=True,  # Allows completing anywhere in the input
    )
