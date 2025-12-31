"""Tool approval UI for Plan Mode."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from esnaad.models.tool_call import ToolCall


class ApprovalDecision(Enum):
    """User's decision on tool approval."""

    APPROVE = "approve"
    """Approve and execute this tool."""

    REJECT = "reject"
    """Reject and skip this tool."""

    APPROVE_ALL = "approve_all"
    """Approve all remaining tools for this message."""

    SWITCH_TO_AUTO_EDIT = "switch_to_auto_edit"
    """Switch to Auto Edit mode and execute this tool."""


@dataclass
class ApprovalResult:
    """Result of an approval request."""

    decision: ApprovalDecision
    """The user's decision."""

    modified_args: dict[str, Any] | None = None
    """Optional: modified arguments (for future use)."""


class ToolApprovalUI:
    """
    UI for approving tool executions in Plan Mode.

    Displays tool details and prompts the user for approval
    before executing destructive tools.
    """

    def __init__(self, console: Console) -> None:
        """
        Initialize the approval UI.

        Args:
            console: Rich console for output.
        """
        self.console = console
        self._approve_all_session = False

    def reset_session(self) -> None:
        """
        Reset session state.

        Call this at the start of each new user message to reset
        the "approve all" state.
        """
        self._approve_all_session = False

    async def request_approval(
        self,
        tool_call: ToolCall,
        tool_description: str,
    ) -> ApprovalResult:
        """
        Request user approval for a tool execution.

        Args:
            tool_call: The tool call to approve.
            tool_description: Description of the tool.

        Returns:
            The user's approval decision.
        """
        # Auto-approve if user previously selected "approve all"
        if self._approve_all_session:
            return ApprovalResult(decision=ApprovalDecision.APPROVE)

        # Display tool call details
        self._display_tool_call(tool_call, tool_description)

        # Get user decision
        decision = await self._get_decision()

        if decision == ApprovalDecision.APPROVE_ALL:
            self._approve_all_session = True
            return ApprovalResult(decision=ApprovalDecision.APPROVE)

        return ApprovalResult(decision=decision)

    def _display_tool_call(
        self,
        tool_call: ToolCall,
        tool_description: str,
    ) -> None:
        """Display the tool call details for review."""
        self.console.print()

        # Create panel with tool info
        panel_content = (
            f"[bold #E57B3A]{tool_call.name}[/bold #E57B3A]\n\n"
            f"[dim]{tool_description}[/dim]"
        )

        self.console.print(
            Panel(
                panel_content,
                title="[bold yellow]Tool Requires Approval[/bold yellow]",
                border_style="yellow",
            )
        )

        # Create arguments table
        if tool_call.arguments:
            table = Table(
                show_header=True,
                header_style="bold cyan",
                border_style="dim",
            )
            table.add_column("Parameter", style="cyan")
            table.add_column("Value")

            for key, value in tool_call.arguments.items():
                # Truncate long values for table display
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                table.add_row(key, value_str)

            self.console.print(table)

        # For write/edit operations, show content preview
        if tool_call.name in ("write_file", "edit_file"):
            content = (
                tool_call.arguments.get("content")
                or tool_call.arguments.get("new_string")
            )
            if content and len(content) > 0:
                self.console.print("\n[bold]Content Preview:[/bold]")

                # Try to detect language for syntax highlighting
                file_path = tool_call.arguments.get("file_path", "")
                lang = self._detect_language(file_path)

                # Truncate for display
                preview = content[:500]
                if len(content) > 500:
                    preview += "\n... [content truncated]"

                try:
                    syntax = Syntax(
                        preview,
                        lang,
                        theme="monokai",
                        line_numbers=True,
                    )
                    self.console.print(syntax)
                except Exception:
                    # Fallback to plain text
                    self.console.print(f"[dim]{preview}[/dim]")

        # For shell commands, show the command prominently
        if tool_call.name == "run_command":
            command = tool_call.arguments.get("command", "")
            if command:
                self.console.print("\n[bold]Command:[/bold]")
                try:
                    syntax = Syntax(
                        command,
                        "bash",
                        theme="monokai",
                    )
                    self.console.print(syntax)
                except Exception:
                    self.console.print(f"[bold red]{command}[/bold red]")

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".jsx": "jsx",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sh": "bash",
            ".bash": "bash",
            ".sql": "sql",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".toml": "toml",
            ".xml": "xml",
        }

        for ext, lang in ext_map.items():
            if file_path.lower().endswith(ext):
                return lang

        return "text"

    async def _get_decision(self) -> ApprovalDecision:
        """Get user's approval decision."""
        from esnaad.cli.ui.prompt import get_user_input

        self.console.print("\n[bold]Options:[/bold]")
        self.console.print("  [green]y[/green] - Approve and execute")
        self.console.print("  [red]n[/red] - Reject (skip this tool)")
        self.console.print("  [cyan]a[/cyan] - Approve all remaining tools")
        self.console.print("  [yellow]e[/yellow] - Switch to Auto Edit mode and execute")
        self.console.print()

        while True:
            response = await get_user_input(
                self.console,
                prompt_text="Approve? [y/n/a/e]: ",
            )

            if response is None:
                # Ctrl+D - treat as reject
                return ApprovalDecision.REJECT

            response = response.strip().lower()

            if response in ("y", "yes", "approve"):
                return ApprovalDecision.APPROVE
            elif response in ("n", "no", "reject", "skip"):
                return ApprovalDecision.REJECT
            elif response in ("a", "all", "approve all"):
                return ApprovalDecision.APPROVE_ALL
            elif response in ("e", "edit", "auto", "auto edit"):
                return ApprovalDecision.SWITCH_TO_AUTO_EDIT
            elif response == "":
                # Empty input - default to approve
                return ApprovalDecision.APPROVE
            else:
                self.console.print(
                    "[red]Invalid choice. Enter y, n, a, or e[/red]"
                )
