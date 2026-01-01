"""Todo state management for the current session."""

from datetime import datetime
from typing import Any, Callable

import structlog

from esnaad.models.todo import TodoItem, TodoList, TodoStatus

logger = structlog.get_logger(__name__)


class TodoManager:
    """
    Manages todo state for a single conversation session.

    This class stores todos in memory during the conversation.
    Each orchestrator session has its own TodoManager instance.
    """

    # Memory store key for todos
    MEMORY_KEY = "todo_list"

    def __init__(
        self,
        state_manager: Any | None = None,
        on_change: Callable[[TodoList], None] | None = None,
    ) -> None:
        """
        Initialize the todo manager.

        Args:
            state_manager: Optional StateManager for memory storage
            on_change: Optional callback when todos change
        """
        self._state_manager = state_manager
        self._on_change = on_change
        self._todo_list: TodoList = TodoList()

    @property
    def todos(self) -> TodoList:
        """Get the current todo list."""
        return self._todo_list

    async def get_todos(self) -> TodoList:
        """
        Get the current todo list (async for memory store compatibility).
        """
        if self._state_manager:
            stored = await self._state_manager.get_memory(self.MEMORY_KEY)
            if stored:
                self._todo_list = TodoList.model_validate(stored)
        return self._todo_list

    async def set_todos(self, items: list[dict[str, Any]]) -> TodoList:
        """
        Replace the entire todo list with new items.

        Args:
            items: List of todo item dicts with content, activeForm, status

        Returns:
            The updated TodoList
        """
        now = datetime.now()

        # Convert input dicts to TodoItem models
        todo_items = []
        for item_data in items:
            # Parse status
            status_str = item_data.get("status", "pending")
            try:
                status = TodoStatus(status_str)
            except ValueError:
                status = TodoStatus.PENDING

            # Use activeForm or active_form (handle both cases)
            active_form = item_data.get("activeForm") or item_data.get(
                "active_form", item_data["content"]
            )

            todo_items.append(
                TodoItem(
                    content=item_data["content"],
                    active_form=active_form,
                    status=status,
                    created_at=now,
                    updated_at=now,
                )
            )

        # Create new list
        self._todo_list = TodoList(
            items=todo_items,
            last_updated=now,
        )

        # Persist to memory store
        if self._state_manager:
            await self._state_manager.set_memory(
                self.MEMORY_KEY,
                self._todo_list.model_dump(mode="json"),
            )

        # Trigger callback
        if self._on_change:
            self._on_change(self._todo_list)

        logger.debug(
            "Todo list updated",
            total=self._todo_list.total_count,
            completed=self._todo_list.completed_count,
            in_progress=self._todo_list.in_progress_count,
        )

        return self._todo_list

    async def clear(self) -> None:
        """Clear all todos."""
        self._todo_list = TodoList()

        if self._state_manager:
            await self._state_manager.delete_memory(self.MEMORY_KEY)

        if self._on_change:
            self._on_change(self._todo_list)

    def format_for_display(self) -> str:
        """Format the todo list for CLI display with Rich markup."""
        if self._todo_list.is_empty:
            return ""

        lines = []
        for item in self._todo_list.items:
            if item.is_completed:
                lines.append(f"  [success]\u2713[/success] {item.content}")
            elif item.is_in_progress:
                lines.append(f"  [#E57B3A]\u2192[/#E57B3A] {item.active_form}")
            else:
                lines.append(f"  [dim]\u25cb[/dim] {item.content}")

        return "\n".join(lines)
