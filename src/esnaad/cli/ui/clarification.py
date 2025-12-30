"""Clarification UI for interactive questionnaire."""

import asyncio
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from esnaad.models.clarification import (
    QuestionType,
    ClarificationQuestion,
    ClarificationRequest,
    ClarificationResponse,
)
from esnaad.state.preferences import get_preference_manager


PROMPT_STYLE = Style.from_dict({
    "prompt": "bold cyan",
    "selection": "yellow",
})


class ClarificationUI:
    """
    Interactive UI for handling clarification requests.

    Renders questions using Rich and collects responses
    using prompt_toolkit for a smooth user experience.
    """

    def __init__(self, console: Console) -> None:
        """
        Initialize the clarification UI.

        Args:
            console: Rich console for output
        """
        self.console = console

    async def handle_request(
        self,
        request: ClarificationRequest,
    ) -> ClarificationResponse:
        """
        Handle a clarification request, collecting user responses.

        Args:
            request: The clarification request with questions

        Returns:
            User's responses to the questions
        """
        response = ClarificationResponse()

        # Show context panel
        self._show_context(request.context)

        # Process each question
        for i, question in enumerate(request.questions, 1):
            self.console.print(f"\n[bold]Question {i}/{len(request.questions)}[/bold]")

            try:
                answer = await self._ask_question(question, request.allow_skip)

                if answer is None and question.default is not None:
                    # User skipped, use default
                    response.responses[question.id] = question.default
                    response.used_defaults.append(question.id)
                elif answer is not None:
                    response.responses[question.id] = answer

            except KeyboardInterrupt:
                # User wants to skip everything
                response.skipped = True
                self._fill_defaults(request, response)
                break

        # Show summary
        self._show_summary(request, response)

        # Learn from responses (store preferences)
        await self._learn_preferences(request, response)

        return response

    async def _learn_preferences(
        self,
        request: ClarificationRequest,
        response: ClarificationResponse,
    ) -> None:
        """Learn preferences from user responses."""
        if response.skipped:
            return  # Don't learn from skipped responses

        pref_manager = get_preference_manager()

        for question in request.questions:
            if question.id in response.responses:
                value = response.responses[question.id]
                # Don't learn default values as explicit preferences
                if question.id not in response.used_defaults:
                    await pref_manager.learn_from_clarification(
                        question_id=question.id,
                        response=value,
                        context=request.context[:50],  # Truncate context
                    )

    def _show_context(self, context: str) -> None:
        """Show the context panel."""
        panel = Panel(
            context,
            title="[bold yellow]Clarification Needed[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
        self.console.print("\n", panel)

    async def _ask_question(
        self,
        question: ClarificationQuestion,
        allow_skip: bool,
    ) -> Any:
        """Ask a single question and get response."""
        # Show question text
        self.console.print(f"\n[cyan]{question.question}[/cyan]")

        if question.help_text:
            self.console.print(f"[dim]{question.help_text}[/dim]")

        # Handle based on question type
        if question.type == QuestionType.YES_NO:
            return await self._ask_yes_no(question, allow_skip)
        elif question.type == QuestionType.CONFIRM:
            return await self._ask_confirm(question, allow_skip)
        elif question.type == QuestionType.SINGLE_SELECT:
            return await self._ask_single_select(question, allow_skip)
        elif question.type == QuestionType.MULTI_SELECT:
            return await self._ask_multi_select(question, allow_skip)
        elif question.type == QuestionType.TEXT_INPUT:
            return await self._ask_text_input(question, allow_skip)
        elif question.type == QuestionType.SCALE:
            return await self._ask_scale(question, allow_skip)
        else:
            # Fallback to text input
            return await self._ask_text_input(question, allow_skip)

    async def _ask_yes_no(
        self,
        question: ClarificationQuestion,
        allow_skip: bool,
    ) -> bool | None:
        """Ask a yes/no question."""
        default = question.default if isinstance(question.default, bool) else True
        default_str = "Y/n" if default else "y/N"

        skip_hint = " (press Enter to skip)" if allow_skip and not question.required else ""
        prompt = f"[{default_str}]{skip_hint}: "

        result = await self._prompt(prompt)

        if not result.strip():
            if allow_skip and not question.required:
                return None
            return default

        return result.strip().lower() in ("y", "yes", "true", "1")

    async def _ask_confirm(
        self,
        question: ClarificationQuestion,
        allow_skip: bool,
    ) -> bool | None:
        """Ask for confirmation."""
        prompt = "[y/N]: "
        result = await self._prompt(prompt)

        if not result.strip():
            if allow_skip and not question.required:
                return None
            return False

        return result.strip().lower() in ("y", "yes", "confirm", "ok")

    async def _ask_single_select(
        self,
        question: ClarificationQuestion,
        allow_skip: bool,
    ) -> str | None:
        """Ask a single-select question."""
        if not question.options:
            return await self._ask_text_input(question, allow_skip)

        # Show options
        self.console.print()
        for i, opt in enumerate(question.options, 1):
            desc = f" - [dim]{opt.description}[/dim]" if opt.description else ""
            self.console.print(f"  [{i}] {opt.label}{desc}")

        # Get default index
        default_idx = 0
        if question.default:
            for i, opt in enumerate(question.options):
                if opt.value == question.default:
                    default_idx = i + 1
                    break

        skip_hint = " (Enter to skip)" if allow_skip and not question.required else ""
        prompt = f"\nSelection [1-{len(question.options)}] (default: {default_idx}){skip_hint}: "

        result = await self._prompt(prompt)

        if not result.strip():
            if allow_skip and not question.required:
                return None
            if default_idx > 0:
                return question.options[default_idx - 1].value
            return question.options[0].value

        try:
            idx = int(result.strip()) - 1
            if 0 <= idx < len(question.options):
                return question.options[idx].value
        except ValueError:
            pass

        self.console.print("[warning]Invalid selection, using default[/warning]")
        return question.options[default_idx - 1].value if default_idx > 0 else question.options[0].value

    async def _ask_multi_select(
        self,
        question: ClarificationQuestion,
        allow_skip: bool,
    ) -> list[str] | None:
        """Ask a multi-select question."""
        if not question.options:
            return await self._ask_text_input(question, allow_skip)

        # Show options
        self.console.print()
        for i, opt in enumerate(question.options, 1):
            desc = f" - [dim]{opt.description}[/dim]" if opt.description else ""
            self.console.print(f"  [{i}] {opt.label}{desc}")

        skip_hint = " (Enter to skip)" if allow_skip and not question.required else ""
        prompt = f"\nSelections (comma-separated, e.g., 1,3,4){skip_hint}: "

        result = await self._prompt(prompt)

        if not result.strip():
            if allow_skip and not question.required:
                return None
            if isinstance(question.default, list):
                return question.default
            return []

        # Parse selections
        selected = []
        for part in result.split(","):
            try:
                idx = int(part.strip()) - 1
                if 0 <= idx < len(question.options):
                    selected.append(question.options[idx].value)
            except ValueError:
                continue

        return selected if selected else None

    async def _ask_text_input(
        self,
        question: ClarificationQuestion,
        allow_skip: bool,
    ) -> str | None:
        """Ask for text input."""
        default = question.default if isinstance(question.default, str) else ""

        skip_hint = " (Enter to skip)" if allow_skip and not question.required else ""
        if default:
            prompt = f"[default: {default}]{skip_hint}: "
        else:
            prompt = f"Enter text{skip_hint}: "

        result = await self._prompt(prompt)

        if not result.strip():
            if allow_skip and not question.required:
                return None
            return default

        return result.strip()

    async def _ask_scale(
        self,
        question: ClarificationQuestion,
        allow_skip: bool,
    ) -> int | None:
        """Ask for a scale value (1-10)."""
        default = question.default if isinstance(question.default, int) else 5

        skip_hint = " (Enter to skip)" if allow_skip and not question.required else ""
        prompt = f"[1-10, default: {default}]{skip_hint}: "

        result = await self._prompt(prompt)

        if not result.strip():
            if allow_skip and not question.required:
                return None
            return default

        try:
            value = int(result.strip())
            return max(1, min(10, value))
        except ValueError:
            return default

    async def _prompt(self, prompt_text: str) -> str:
        """Get input from user."""
        session = PromptSession(style=PROMPT_STYLE)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: session.prompt(prompt_text),
            )
            return result
        except EOFError:
            return ""

    def _fill_defaults(
        self,
        request: ClarificationRequest,
        response: ClarificationResponse,
    ) -> None:
        """Fill remaining questions with defaults."""
        for question in request.questions:
            if question.id not in response.responses:
                if question.default is not None:
                    response.responses[question.id] = question.default
                    response.used_defaults.append(question.id)

    def _show_summary(
        self,
        request: ClarificationRequest,
        response: ClarificationResponse,
    ) -> None:
        """Show a summary of responses."""
        if response.skipped:
            self.console.print("\n[dim]Skipped - using default values[/dim]")
            return

        table = Table(title="Your Responses", show_header=True, header_style="bold")
        table.add_column("Question", style="cyan")
        table.add_column("Response", style="green")
        table.add_column("", style="dim")  # For default indicator

        for question in request.questions:
            q_text = question.question[:40] + "..." if len(question.question) > 40 else question.question

            resp = response.responses.get(question.id, "(no response)")
            if isinstance(resp, list):
                resp = ", ".join(str(v) for v in resp)
            else:
                resp = str(resp)

            default_marker = "(default)" if question.id in response.used_defaults else ""

            table.add_row(q_text, resp, default_marker)

        self.console.print("\n", table)


async def create_clarification_handler(console: Console):
    """
    Create a clarification handler function for the orchestrator.

    Args:
        console: Rich console for output

    Returns:
        Async handler function
    """
    ui = ClarificationUI(console)

    async def handler(request: ClarificationRequest) -> ClarificationResponse:
        return await ui.handle_request(request)

    return handler
