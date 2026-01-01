"""Write todo tool for task tracking."""

from typing import Any

from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class TodoItemInput(BaseModel):
    """A single todo item for input."""

    content: str = Field(
        description="Task description in imperative form (e.g., 'Run tests')",
        min_length=1,
    )
    activeForm: str = Field(
        description="Present continuous form shown while in progress (e.g., 'Running tests')",
        min_length=1,
    )
    status: str = Field(
        default="pending",
        description="Status: pending, in_progress, or completed",
    )


class WriteTodoInput(BaseModel):
    """Input schema for write_todo tool."""

    todos: list[TodoItemInput] = Field(
        description="The complete updated todo list",
    )


class WriteTodoOutput(BaseModel):
    """Output schema for write_todo tool."""

    success: bool = Field(description="Whether the update succeeded")
    total: int = Field(description="Total number of todos")
    completed: int = Field(description="Number of completed todos")
    in_progress: int = Field(description="Number of in-progress todos")
    pending: int = Field(description="Number of pending todos")
    current_task: str | None = Field(
        default=None,
        description="The currently in-progress task",
    )


@register_tool
class WriteTodoTool(BaseTool[WriteTodoInput, WriteTodoOutput]):
    """
    Update the todo list to track task progress.

    Use this tool to:
    - Create a structured task list for complex multi-step tasks
    - Track progress as you work through tasks
    - Mark tasks as in_progress when starting work
    - Mark tasks as completed when finished

    Best practices:
    - Only one task should be in_progress at a time
    - Update the list each time you start or complete a task
    - Use clear, actionable task descriptions
    """

    name = "write_todo"
    description = (
        "Update the todo list for tracking task progress. "
        "Use this to organize complex tasks, track what you're working on, "
        "and show progress to the user. Each item needs content (imperative form like 'Fix bug'), "
        "activeForm (present continuous like 'Fixing bug'), and status (pending/in_progress/completed)."
    )
    parallel_safe = False  # State mutation
    requires_lock = False

    @property
    def input_schema(self) -> type[WriteTodoInput]:
        return WriteTodoInput

    @property
    def output_schema(self) -> type[WriteTodoOutput]:
        return WriteTodoOutput

    async def execute(
        self,
        input_data: WriteTodoInput,
        context: ToolContext,
    ) -> WriteTodoOutput:
        """Update the todo list."""
        # Get todo manager from metadata (injected by orchestrator)
        todo_manager = context.metadata.get("todo_manager")

        if todo_manager is None:
            # Create standalone manager if not provided
            from esnaad.state.todo_manager import TodoManager

            todo_manager = TodoManager(state_manager=context.state_manager)

        # Convert input to dict format
        items = [
            {
                "content": item.content,
                "activeForm": item.activeForm,
                "status": item.status,
            }
            for item in input_data.todos
        ]

        # Update the todo list
        todo_list = await todo_manager.set_todos(items)

        # Get current task
        current = todo_list.current_task
        current_task = current.active_form if current else None

        return WriteTodoOutput(
            success=True,
            total=todo_list.total_count,
            completed=todo_list.completed_count,
            in_progress=todo_list.in_progress_count,
            pending=todo_list.pending_count,
            current_task=current_task,
        )
