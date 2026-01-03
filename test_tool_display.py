"""Test script to demonstrate user-friendly tool call display."""

from rich.console import Console
from esnaad.cli.ui.panels import _format_friendly_tool_call

console = Console()

# Test cases
test_cases = [
    ("write_file", {"file_path": "test001.txt", "content": "Hello", "create_directories": True}),
    ("read_file", {"file_path": "src/esnaad/core/orchestrator.py", "offset": 0, "limit": 100}),
    ("edit_file", {"file_path": "config.py", "old_string": "foo", "new_string": "bar"}),
    ("create_directory", {"path": "src/new_module", "parents": True}),
    ("list_directory", {"path": "src/esnaad", "recursive": False}),
    ("search_files", {"pattern": "*.py", "path": "src"}),
    ("search_content", {"pattern": "TODO", "path": "src"}),
    ("run_command", {"command": "dir /b", "timeout": 10}),
    ("spawn_subtasks", {"subtasks": [{"id": "1", "description": "Task 1"}, {"id": "2", "description": "Task 2"}]}),
    ("request_clarifications", {"questions": [{"question": "Which library?", "options": ["A", "B"]}]}),
    ("write_todo", {"todos": [{"content": "Fix bug", "status": "pending"}, {"content": "Add test", "status": "pending"}]}),
    ("web_search", {"query": "Python async best practices"}),
    ("web_fetch", {"url": "https://example.com/api/docs"}),
]

console.print("\n[bold #E57B3A]User-Friendly Tool Call Display Examples:[/bold #E57B3A]\n")

for tool_name, arguments in test_cases:
    friendly = _format_friendly_tool_call(tool_name, arguments)

    # Show comparison
    console.print(f"[dim]Tool:[/dim] {tool_name}")
    console.print(f"[tool]> {friendly}[/tool]")
    console.print()

console.print("\n[bold green]All tool calls now display in user-friendly format![/bold green]")
console.print("[dim]Technical details available in debug mode (ESNAAD_DEBUG=true)[/dim]\n")
