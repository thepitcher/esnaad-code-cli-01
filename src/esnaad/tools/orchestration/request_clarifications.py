"""Request clarifications tool for interactive user queries."""

from typing import Any

from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool
from esnaad.models.clarification import (
    QuestionType,
    QuestionOption,
    ClarificationQuestion,
    ClarificationRequest,
    ClarificationResponse,
)


class OptionInput(BaseModel):
    """An option for select-type questions."""

    value: str = Field(description="Value to store if selected")
    label: str = Field(description="Display label shown to user")
    description: str | None = Field(
        default=None,
        description="Additional description for the option",
    )


class QuestionInput(BaseModel):
    """A single clarification question."""

    id: str = Field(description="Unique identifier for the question")
    question: str = Field(description="The question text to show the user")
    type: str = Field(
        default="single_select",
        description="Question type: single_select, multi_select, yes_no, text_input, confirm",
    )
    options: list[OptionInput] | None = Field(
        default=None,
        description="Options for select-type questions",
    )
    default: str | list[str] | bool | None = Field(
        default=None,
        description="Default value if user skips",
    )
    required: bool = Field(
        default=False,
        description="Whether the question must be answered",
    )
    help_text: str | None = Field(
        default=None,
        description="Additional help text shown below the question",
    )


class RequestClarificationsInput(BaseModel):
    """Input schema for request_clarifications tool."""

    context: str = Field(
        description="Brief explanation of why clarification is needed",
    )
    questions: list[QuestionInput] = Field(
        min_length=1,
        max_length=5,
        description="List of questions to ask (1-5 questions)",
    )
    allow_skip: bool = Field(
        default=True,
        description="Whether user can skip with default values",
    )


class ResponseOutput(BaseModel):
    """Output for user responses."""

    question_id: str = Field(description="Question ID")
    response: str | list[str] | bool = Field(description="User's response")
    used_default: bool = Field(description="Whether default value was used")


class RequestClarificationsOutput(BaseModel):
    """Output schema for request_clarifications tool."""

    skipped: bool = Field(description="Whether user skipped all questions")
    responses: list[ResponseOutput] = Field(description="Individual responses")
    formatted_summary: str = Field(description="Human-readable summary of responses")


@register_tool
class RequestClarificationsTool(BaseTool[RequestClarificationsInput, RequestClarificationsOutput]):
    """
    Request clarification from the user when information is ambiguous or missing.

    Use this tool when you need user input to proceed, such as:
    - Choosing between multiple valid approaches
    - Confirming a potentially destructive action
    - Getting preferences for implementation details
    - Resolving ambiguity in user requirements
    """

    name = "request_clarifications"
    description = (
        "Ask the user clarifying questions when you need more information. "
        "Use this when requirements are ambiguous, when choosing between approaches, "
        "or when confirming important decisions. Supports various question types: "
        "single_select, multi_select, yes_no, text_input, confirm."
    )
    parallel_safe = False  # Requires user interaction
    requires_lock = False

    @property
    def input_schema(self) -> type[RequestClarificationsInput]:
        return RequestClarificationsInput

    @property
    def output_schema(self) -> type[RequestClarificationsOutput]:
        return RequestClarificationsOutput

    async def execute(
        self,
        input_data: RequestClarificationsInput,
        context: ToolContext,
    ) -> RequestClarificationsOutput:
        """Request clarifications from the user."""
        from esnaad.exceptions import ToolExecutionError

        # Get clarification handler from metadata (injected by CLI)
        clarification_handler = context.metadata.get("clarification_handler")
        if clarification_handler is None:
            # Fallback: return defaults if no handler available
            return self._use_defaults(input_data)

        # Build clarification request
        questions = []
        for q in input_data.questions:
            # Parse question type
            try:
                q_type = QuestionType(q.type)
            except ValueError:
                q_type = QuestionType.SINGLE_SELECT

            # Build options
            options = None
            if q.options:
                options = [
                    QuestionOption(
                        value=opt.value,
                        label=opt.label,
                        description=opt.description,
                    )
                    for opt in q.options
                ]

            questions.append(
                ClarificationQuestion(
                    id=q.id,
                    question=q.question,
                    type=q_type,
                    options=options,
                    default=q.default,
                    required=q.required,
                    help_text=q.help_text,
                )
            )

        request = ClarificationRequest(
            context=input_data.context,
            questions=questions,
            allow_skip=input_data.allow_skip,
        )

        # Call the handler to get user input
        try:
            response: ClarificationResponse = await clarification_handler(request)
        except Exception as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Failed to get user clarification: {e}",
            )

        # Convert to output format
        response_outputs = []
        for q in input_data.questions:
            value = response.responses.get(q.id, q.default)
            used_default = q.id in response.used_defaults or response.skipped

            response_outputs.append(
                ResponseOutput(
                    question_id=q.id,
                    response=value if value is not None else "",
                    used_default=used_default,
                )
            )

        return RequestClarificationsOutput(
            skipped=response.skipped,
            responses=response_outputs,
            formatted_summary=response.format_for_prompt(),
        )

    def _use_defaults(
        self,
        input_data: RequestClarificationsInput,
    ) -> RequestClarificationsOutput:
        """Return defaults when no handler is available."""
        response_outputs = []
        for q in input_data.questions:
            response_outputs.append(
                ResponseOutput(
                    question_id=q.id,
                    response=q.default if q.default is not None else "",
                    used_default=True,
                )
            )

        summary_lines = ["(Using default values - no clarification handler available)"]
        for q in input_data.questions:
            default_str = str(q.default) if q.default is not None else "(none)"
            summary_lines.append(f"- {q.id}: {default_str}")

        return RequestClarificationsOutput(
            skipped=True,
            responses=response_outputs,
            formatted_summary="\n".join(summary_lines),
        )
