"""Todo display components for CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from esnaad.models.todo import TodoList, TodoStatus


# Status symbols consistent with existing codebase
SYMBOLS = {
    TodoStatus.COMPLETED: ("\u2713", "green"),  # checkmark
    TodoStatus.IN_PROGRESS: ("\u2192", "#E57B3A"),  # arrow
    TodoStatus.PENDING: ("\u25cb", "dim"),  # circle
}


def print_todo_list(console: Console, todo_list: TodoList) -> None:
    """
    Print the todo list to the console as a panel.

    Args:
        console: Rich console for output
        todo_list: The todo list to display
    """
    if todo_list.is_empty:
        return

    # Build lines
    lines = []
    for item in todo_list.items:
        symbol, color = SYMBOLS.get(item.status, ("\u25cb", "dim"))
        text = item.active_form if item.is_in_progress else item.content

        if item.is_completed:
            lines.append(f"  [green]{symbol}[/green] [dim]{text}[/dim]")
        elif item.is_in_progress:
            lines.append(f"  [{color}]{symbol}[/{color}] {text}")
        else:
            lines.append(f"  [{color}]{symbol}[/{color}] {text}")

    # Add summary line
    summary = f"{todo_list.completed_count}/{todo_list.total_count} completed"
    lines.append(f"\n  [dim]{summary}[/dim]")

    # Print as panel
    content = "\n".join(lines)
    console.print(
        Panel(
            content,
            title="[bold #E57B3A]Tasks[/bold #E57B3A]",
            border_style="#E57B3A",
            padding=(0, 1),
        )
    )


def print_todo_inline(console: Console, todo_list: TodoList) -> None:
    """
    Print a compact inline todo status.

    Args:
        console: Rich console for output
        todo_list: The todo list to display
    """
    if todo_list.is_empty:
        return

    # Just show the current task if any
    current = todo_list.current_task
    if current:
        console.print(
            f"[dim]Working on:[/dim] [#E57B3A]{current.active_form}[/#E57B3A]"
        )

    # Show progress
    console.print(
        f"[dim]Progress: {todo_list.completed_count}/{todo_list.total_count} tasks[/dim]"
    )


def print_todo_table(console: Console, todo_list: TodoList) -> None:
    """
    Print the todo list as a table.

    Args:
        console: Rich console for output
        todo_list: The todo list to display
    """
    if todo_list.is_empty:
        console.print("[dim]No tasks[/dim]")
        return

    table = Table(title="Tasks", show_header=True, header_style="bold #E57B3A")
    table.add_column("#", style="dim", width=3)
    table.add_column("Task", style="cyan")
    table.add_column("Status", justify="center")

    for i, item in enumerate(todo_list.items, 1):
        symbol, color = SYMBOLS.get(item.status, ("\u25cb", "dim"))
        text = item.active_form if item.is_in_progress else item.content

        if item.is_completed:
            status_str = f"[green]{symbol} Done[/green]"
            text = f"[dim]{text}[/dim]"
        elif item.is_in_progress:
            status_str = f"[{color}]{symbol} Working[/{color}]"
        else:
            status_str = f"[dim]{symbol} Pending[/dim]"

        table.add_row(str(i), text, status_str)

    console.print(table)


def format_todo_for_callback(todo_list: TodoList) -> str:
    """
    Format todo list for callback/logging.

    Args:
        todo_list: The todo list

    Returns:
        Formatted string representation
    """
    if todo_list.is_empty:
        return "No tasks"

    parts = []
    for item in todo_list.items:
        if item.is_completed:
            parts.append(f"[DONE] {item.content}")
        elif item.is_in_progress:
            parts.append(f"[WORKING] {item.active_form}")
        else:
            parts.append(f"[TODO] {item.content}")

    return "\n".join(parts)
