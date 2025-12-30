"""Clarification models for interactive questionnaire system."""

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Type of clarification question."""

    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    YES_NO = "yes_no"
    TEXT_INPUT = "text_input"
    SCALE = "scale"
    CONFIRM = "confirm"


class QuestionOption(BaseModel):
    """An option for select-type questions."""

    value: str = Field(description="Value to store if selected")
    label: str = Field(description="Display label")
    description: str | None = Field(
        default=None,
        description="Additional description",
    )


class ClarificationQuestion(BaseModel):
    """
    A single clarification question.

    Attributes:
        id: Unique identifier for the question
        question: The question text
        type: Type of question (affects UI rendering)
        options: Available options (for select types)
        default: Default value if user skips
        required: Whether the question must be answered
        help_text: Additional context shown below the question
    """

    id: str = Field(description="Unique identifier")
    question: str = Field(description="The question text")
    type: QuestionType = Field(description="Question type")
    options: list[QuestionOption] | None = Field(
        default=None,
        description="Options for select types",
    )
    default: str | list[str] | bool | int | None = Field(
        default=None,
        description="Default value",
    )
    required: bool = Field(default=False, description="Is required")
    help_text: str | None = Field(
        default=None,
        description="Additional help text",
    )

    @property
    def has_options(self) -> bool:
        """Check if question has selectable options."""
        return self.type in (
            QuestionType.SINGLE_SELECT,
            QuestionType.MULTI_SELECT,
        )

    def get_option_labels(self) -> list[str]:
        """Get list of option labels."""
        if self.options:
            return [opt.label for opt in self.options]
        return []

    def get_option_values(self) -> list[str]:
        """Get list of option values."""
        if self.options:
            return [opt.value for opt in self.options]
        return []


class ClarificationRequest(BaseModel):
    """
    Request for clarification with multiple questions.

    Attributes:
        context: Brief explanation of why clarification is needed
        questions: List of questions (max 5)
        allow_skip: Whether user can skip with defaults
    """

    context: str = Field(description="Why clarification is needed")
    questions: list[ClarificationQuestion] = Field(
        max_length=5,
        description="Questions to ask (max 5)",
    )
    allow_skip: bool = Field(
        default=True,
        description="Allow skipping with defaults",
    )

    def get_question_by_id(self, question_id: str) -> ClarificationQuestion | None:
        """Get a question by its ID."""
        for q in self.questions:
            if q.id == question_id:
                return q
        return None

    def get_defaults(self) -> dict[str, Any]:
        """Get all default values."""
        return {q.id: q.default for q in self.questions if q.default is not None}


class ClarificationResponse(BaseModel):
    """
    User's response to a clarification request.

    Attributes:
        clarification_id: Unique ID for this clarification session
        responses: Map of question ID to user's response
        skipped: Whether user skipped the entire clarification
        used_defaults: List of question IDs where default was used
    """

    clarification_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique clarification ID",
    )
    responses: dict[str, str | list[str] | bool | int] = Field(
        default_factory=dict,
        description="User responses by question ID",
    )
    skipped: bool = Field(
        default=False,
        description="Whether user skipped entirely",
    )
    used_defaults: list[str] = Field(
        default_factory=list,
        description="Question IDs where default was used",
    )

    def get_response(
        self,
        question_id: str,
        default: Any = None,
    ) -> Any:
        """Get response for a question, with fallback default."""
        return self.responses.get(question_id, default)

    def format_for_prompt(self) -> str:
        """Format responses as text for including in prompts."""
        if self.skipped:
            return "(User skipped clarification, using defaults)"

        lines = []
        for qid, response in self.responses.items():
            if isinstance(response, list):
                response_str = ", ".join(response)
            else:
                response_str = str(response)
            lines.append(f"- {qid}: {response_str}")

        return "\n".join(lines)
