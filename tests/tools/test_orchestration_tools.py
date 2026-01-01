"""Tests for orchestration tools (spawn_subtasks, request_clarifications, write_todo)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from esnaad.tools.orchestration.spawn_subtasks import (
    SpawnSubtasksTool,
    SpawnSubtasksInput,
    SubtaskDefinition,
)
from esnaad.tools.orchestration.request_clarifications import (
    RequestClarificationsTool,
    RequestClarificationsInput,
    QuestionInput,
    OptionInput,
)
from esnaad.tools.orchestration.write_todo import (
    WriteTodoTool,
    WriteTodoInput,
    TodoItemInput,
)
from esnaad.tools.base import ToolContext
from esnaad.models.subtask import SubtaskResult, SubtaskStatus
from esnaad.models.clarification import ClarificationResponse
from esnaad.models.todo import TodoList, TodoStatus
from esnaad.state.todo_manager import TodoManager
from esnaad.exceptions import ToolExecutionError


class TestSpawnSubtasksTool:
    """Tests for SpawnSubtasksTool."""

    @pytest.fixture
    def tool(self) -> SpawnSubtasksTool:
        return SpawnSubtasksTool()

    @pytest.fixture
    def tool_context_with_llm(self, tool_context: ToolContext) -> ToolContext:
        """Create context with mock LLM client."""
        mock_llm = MagicMock()
        tool_context.metadata["llm_client"] = mock_llm
        return tool_context

    async def test_spawn_requires_llm_client(
        self,
        tool: SpawnSubtasksTool,
        tool_context: ToolContext,
    ) -> None:
        """Test that spawn fails without LLM client."""
        input_data = SpawnSubtasksInput(
            subtasks=[
                SubtaskDefinition(
                    id="task1",
                    description="Test task",
                    prompt="Do something",
                ),
            ],
        )

        with pytest.raises(ToolExecutionError) as exc_info:
            await tool.execute(input_data, tool_context)

        assert "llm client" in str(exc_info.value).lower()

    def test_input_validation(self) -> None:
        """Test input validation."""
        # Valid input
        input_data = SpawnSubtasksInput(
            subtasks=[
                SubtaskDefinition(
                    id="task1",
                    description="Test task",
                    prompt="Do something",
                    tools=["read_file"],
                ),
            ],
        )
        assert len(input_data.subtasks) == 1

        # Empty subtasks should fail
        with pytest.raises(ValueError):
            SpawnSubtasksInput(subtasks=[])

    def test_subtask_with_dependencies(self) -> None:
        """Test subtask with dependencies."""
        input_data = SpawnSubtasksInput(
            subtasks=[
                SubtaskDefinition(
                    id="task1",
                    description="First task",
                    prompt="Do first thing",
                ),
                SubtaskDefinition(
                    id="task2",
                    description="Second task",
                    prompt="Do second thing",
                    depends_on=["task1"],
                ),
            ],
        )

        assert input_data.subtasks[1].depends_on == ["task1"]

    def test_openai_schema(self, tool: SpawnSubtasksTool) -> None:
        """Test OpenAI schema generation."""
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "spawn_subtasks"
        assert "subtasks" in schema["function"]["parameters"]["properties"]


class TestRequestClarificationsTool:
    """Tests for RequestClarificationsTool."""

    @pytest.fixture
    def tool(self) -> RequestClarificationsTool:
        return RequestClarificationsTool()

    async def test_uses_defaults_without_handler(
        self,
        tool: RequestClarificationsTool,
        tool_context: ToolContext,
    ) -> None:
        """Test that defaults are used without clarification handler."""
        input_data = RequestClarificationsInput(
            context="Need to clarify something",
            questions=[
                QuestionInput(
                    id="q1",
                    question="What is your preference?",
                    type="single_select",
                    options=[
                        OptionInput(value="opt1", label="Option 1"),
                        OptionInput(value="opt2", label="Option 2"),
                    ],
                    default="opt1",
                ),
            ],
        )

        result = await tool.execute(input_data, tool_context)

        assert result.skipped  # Uses defaults, so skipped is True
        assert len(result.responses) == 1
        assert result.responses[0].question_id == "q1"
        assert result.responses[0].used_default

    async def test_calls_handler_when_available(
        self,
        tool: RequestClarificationsTool,
        tool_context: ToolContext,
    ) -> None:
        """Test that handler is called when available."""
        # Create mock handler
        mock_response = ClarificationResponse(
            responses={"q1": "user_choice"},
            skipped=False,
            used_defaults=[],
        )
        mock_handler = AsyncMock(return_value=mock_response)
        tool_context.metadata["clarification_handler"] = mock_handler

        input_data = RequestClarificationsInput(
            context="Need to clarify something",
            questions=[
                QuestionInput(
                    id="q1",
                    question="What is your preference?",
                    type="text_input",
                    default="default_value",
                ),
            ],
        )

        result = await tool.execute(input_data, tool_context)

        mock_handler.assert_called_once()
        assert not result.skipped
        assert result.responses[0].response == "user_choice"

    def test_question_types(self) -> None:
        """Test different question types."""
        # Single select
        q1 = QuestionInput(
            id="q1",
            question="Choose one",
            type="single_select",
            options=[
                OptionInput(value="a", label="A"),
                OptionInput(value="b", label="B"),
            ],
        )
        assert q1.type == "single_select"

        # Multi select
        q2 = QuestionInput(
            id="q2",
            question="Choose multiple",
            type="multi_select",
            options=[
                OptionInput(value="x", label="X"),
                OptionInput(value="y", label="Y"),
            ],
        )
        assert q2.type == "multi_select"

        # Yes/No
        q3 = QuestionInput(
            id="q3",
            question="Do you agree?",
            type="yes_no",
            default=True,
        )
        assert q3.type == "yes_no"

        # Text input
        q4 = QuestionInput(
            id="q4",
            question="Enter text",
            type="text_input",
        )
        assert q4.type == "text_input"

    def test_input_validation(self) -> None:
        """Test input validation."""
        # Valid input
        input_data = RequestClarificationsInput(
            context="Test context",
            questions=[
                QuestionInput(
                    id="q1",
                    question="Test question?",
                    type="yes_no",
                ),
            ],
        )
        assert len(input_data.questions) == 1

        # Too many questions (max 5)
        with pytest.raises(ValueError):
            RequestClarificationsInput(
                context="Test",
                questions=[
                    QuestionInput(id=f"q{i}", question=f"Q{i}?", type="yes_no")
                    for i in range(6)
                ],
            )

    def test_openai_schema(self, tool: RequestClarificationsTool) -> None:
        """Test OpenAI schema generation."""
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "request_clarifications"
        assert "questions" in schema["function"]["parameters"]["properties"]
        assert "context" in schema["function"]["parameters"]["properties"]


class TestWriteTodoTool:
    """Tests for WriteTodoTool."""

    @pytest.fixture
    def tool(self) -> WriteTodoTool:
        return WriteTodoTool()

    @pytest.fixture
    def todo_manager(self) -> TodoManager:
        return TodoManager()

    @pytest.fixture
    def tool_context_with_todo(
        self,
        tool_context: ToolContext,
        todo_manager: TodoManager,
    ) -> ToolContext:
        """Create context with todo manager."""
        tool_context.metadata["todo_manager"] = todo_manager
        return tool_context

    async def test_create_todo_list(
        self,
        tool: WriteTodoTool,
        tool_context_with_todo: ToolContext,
    ) -> None:
        """Test creating a todo list."""
        input_data = WriteTodoInput(
            todos=[
                TodoItemInput(
                    content="Task 1",
                    activeForm="Working on task 1",
                    status="pending",
                ),
                TodoItemInput(
                    content="Task 2",
                    activeForm="Working on task 2",
                    status="in_progress",
                ),
                TodoItemInput(
                    content="Task 3",
                    activeForm="Working on task 3",
                    status="completed",
                ),
            ],
        )

        result = await tool.execute(input_data, tool_context_with_todo)

        assert result.success
        assert result.total == 3
        assert result.pending == 1
        assert result.in_progress == 1
        assert result.completed == 1
        assert result.current_task == "Working on task 2"

    async def test_update_todo_status(
        self,
        tool: WriteTodoTool,
        tool_context_with_todo: ToolContext,
    ) -> None:
        """Test updating todo status."""
        # First create a pending task
        await tool.execute(
            WriteTodoInput(
                todos=[
                    TodoItemInput(
                        content="Task 1",
                        activeForm="Working on task 1",
                        status="pending",
                    ),
                ],
            ),
            tool_context_with_todo,
        )

        # Then mark it completed
        result = await tool.execute(
            WriteTodoInput(
                todos=[
                    TodoItemInput(
                        content="Task 1",
                        activeForm="Working on task 1",
                        status="completed",
                    ),
                ],
            ),
            tool_context_with_todo,
        )

        assert result.completed == 1
        assert result.pending == 0
        assert result.current_task is None

    async def test_empty_todo_list(
        self,
        tool: WriteTodoTool,
        tool_context_with_todo: ToolContext,
    ) -> None:
        """Test creating empty todo list."""
        input_data = WriteTodoInput(todos=[])

        result = await tool.execute(input_data, tool_context_with_todo)

        assert result.success
        assert result.total == 0
        assert result.current_task is None

    async def test_without_todo_manager(
        self,
        tool: WriteTodoTool,
        tool_context: ToolContext,
    ) -> None:
        """Test that tool works without pre-injected todo manager."""
        input_data = WriteTodoInput(
            todos=[
                TodoItemInput(
                    content="Task 1",
                    activeForm="Working on task 1",
                    status="pending",
                ),
            ],
        )

        # Should create its own TodoManager
        result = await tool.execute(input_data, tool_context)

        assert result.success
        assert result.total == 1

    def test_input_validation(self) -> None:
        """Test input validation."""
        # Valid input
        input_data = WriteTodoInput(
            todos=[
                TodoItemInput(
                    content="Task",
                    activeForm="Tasking",
                    status="pending",
                ),
            ],
        )
        assert len(input_data.todos) == 1

        # Invalid status should default to pending
        item = TodoItemInput(
            content="Task",
            activeForm="Tasking",
            status="invalid_status",
        )
        assert item.status == "invalid_status"  # Raw value

    def test_openai_schema(self, tool: WriteTodoTool) -> None:
        """Test OpenAI schema generation."""
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "write_todo"
        assert "todos" in schema["function"]["parameters"]["properties"]

    async def test_callback_triggered(
        self,
        tool: WriteTodoTool,
        tool_context: ToolContext,
    ) -> None:
        """Test that callback is triggered on todo change."""
        callback_called = False
        received_list: TodoList | None = None

        def on_change(todo_list: TodoList) -> None:
            nonlocal callback_called, received_list
            callback_called = True
            received_list = todo_list

        todo_manager = TodoManager(on_change=on_change)
        tool_context.metadata["todo_manager"] = todo_manager

        input_data = WriteTodoInput(
            todos=[
                TodoItemInput(
                    content="Task 1",
                    activeForm="Working on task 1",
                    status="in_progress",
                ),
            ],
        )

        await tool.execute(input_data, tool_context)

        assert callback_called
        assert received_list is not None
        assert received_list.total_count == 1
        assert received_list.current_task is not None
        assert received_list.current_task.active_form == "Working on task 1"
