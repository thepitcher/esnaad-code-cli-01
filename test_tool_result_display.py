"""Test script to demonstrate user-friendly tool result display."""

from rich.console import Console
from esnaad.cli.ui.panels import print_tool_call, print_tool_result
import json

console = Console()

console.print("\n[bold #E57B3A]User-Friendly Tool Result Display Examples:[/bold #E57B3A]\n")

# Example 1: Write File (Success)
console.print("[bold]Example 1: Write File[/bold]")
print_tool_call(console, "write_file", {"file_path": "test001.txt", "content": "Hello World"})
output = json.dumps({
    "success": True,
    "file_path": "c:/workspace/test001.txt",
    "bytes_written": 11,
    "created": True
})
print_tool_result(console, "write_file", True, {"file_path": "test001.txt", "content": "Hello World"}, output, None)
console.print()

# Example 2: Read File (Success)
console.print("[bold]Example 2: Read File[/bold]")
print_tool_call(console, "read_file", {"file_path": "config.py", "offset": 0, "limit": 100})
output = json.dumps({
    "success": True,
    "file_path": "c:/workspace/config.py",
    "content": "import os\nimport sys\nfrom pathlib import Path\n\nBASE_DIR = Path(__file__).parent\nDEBUG = True"
})
print_tool_result(console, "read_file", True, {"file_path": "config.py"}, output, None)
console.print()

# Example 3: Run Command (Success)
console.print("[bold]Example 3: Run Command[/bold]")
print_tool_call(console, "run_command", {"command": "dir /b"})
output = json.dumps({
    "success": True,
    "command": "dir /b",
    "stdout": "test001.txt\nconfig.py\nREADME.md\nsrc",
    "stderr": "",
    "exit_code": 0
})
print_tool_result(console, "run_command", True, {"command": "dir /b"}, output, None)
console.print()

# Example 4: List Directory (Success)
console.print("[bold]Example 4: List Directory[/bold]")
print_tool_call(console, "list_directory", {"path": "src/esnaad"})
output = json.dumps({
    "path": "src/esnaad",
    "items": [
        {"name": "core", "type": "directory"},
        {"name": "tools", "type": "directory"},
        {"name": "cli", "type": "directory"},
        {"name": "__init__.py", "type": "file"},
        {"name": "config.py", "type": "file"},
    ]
})
print_tool_result(console, "list_directory", True, {"path": "src/esnaad"}, output, None)
console.print()

# Example 5: Write File (Error)
console.print("[bold]Example 5: Write File (Error)[/bold]")
print_tool_call(console, "write_file", {"file_path": "/readonly/file.txt", "content": "Test"})
print_tool_result(console, "write_file", False, {"file_path": "/readonly/file.txt"}, None, "Permission denied: /readonly/file.txt")
console.print()

# Example 6: Edit File (Success)
console.print("[bold]Example 6: Edit File[/bold]")
print_tool_call(console, "edit_file", {"file_path": "config.py", "old_string": "DEBUG = True", "new_string": "DEBUG = False"})
output = json.dumps({
    "success": True,
    "file_path": "c:/workspace/config.py",
    "replacements_made": 1
})
print_tool_result(console, "edit_file", True, {"file_path": "config.py"}, output, None)
console.print()

console.print("\n[bold green]Tool results now display in Claude Code style![/bold green]")
console.print("[dim]* Green asterisk for success, red X for errors[/dim]")
console.print("[dim]* Friendly summaries with relevant information[/dim]")
console.print("[dim]* Content previews when applicable[/dim]")
console.print("[dim]* Technical details in debug mode only[/dim]\n")
