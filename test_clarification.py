"""Quick test script for the clarification system."""

import asyncio
from rich.console import Console

from esnaad.cli.ui.clarification import ClarificationUI
from esnaad.models.clarification import (
    QuestionType,
    QuestionOption,
    ClarificationQuestion,
    ClarificationRequest,
)


async def test_clarification_ui():
    """Test the clarification UI directly."""
    console = Console()
    ui = ClarificationUI(console)

    # Create a sample clarification request
    request = ClarificationRequest(
        context="I need some information to proceed with your request.",
        questions=[
            ClarificationQuestion(
                id="language",
                question="Which programming language do you prefer?",
                type=QuestionType.SINGLE_SELECT,
                options=[
                    QuestionOption(value="python", label="Python", description="Great for scripting and data science"),
                    QuestionOption(value="typescript", label="TypeScript", description="Type-safe JavaScript"),
                    QuestionOption(value="rust", label="Rust", description="Systems programming with safety"),
                ],
                default="python",
            ),
            ClarificationQuestion(
                id="features",
                question="Which features do you want to include?",
                type=QuestionType.MULTI_SELECT,
                options=[
                    QuestionOption(value="tests", label="Unit Tests"),
                    QuestionOption(value="docs", label="Documentation"),
                    QuestionOption(value="ci", label="CI/CD Pipeline"),
                ],
                default=["tests"],
            ),
            ClarificationQuestion(
                id="confirm_overwrite",
                question="Do you want to overwrite existing files?",
                type=QuestionType.YES_NO,
                default=False,
            ),
            ClarificationQuestion(
                id="project_name",
                question="What should the project be named?",
                type=QuestionType.TEXT_INPUT,
                default="my-project",
                help_text="Use lowercase letters and hyphens only",
            ),
        ],
        allow_skip=True,
    )

    console.print("\n[bold cyan]Testing Clarification UI[/bold cyan]\n")
    console.print("This will simulate the LLM asking for clarifications.\n")

    # Run the UI
    response = await ui.handle_request(request)

    # Show the result
    console.print("\n[bold green]Response received:[/bold green]")
    console.print(f"  Skipped: {response.skipped}")
    console.print(f"  Responses: {response.responses}")
    console.print(f"  Used defaults: {response.used_defaults}")
    console.print(f"\n[dim]Formatted for prompt:[/dim]")
    console.print(response.format_for_prompt())


if __name__ == "__main__":
    asyncio.run(test_clarification_ui())
