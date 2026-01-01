"""Todo models for task tracking."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    """Status of a todo item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoItem(BaseModel):
    """
    A single todo item for task tracking.

    Attributes:
        content: Task description in imperative form (e.g., "Fix the bug")
        active_form: Present continuous form (e.g., "Fixing the bug")
        status: Current status of the item
        created_at: When the item was created
        updated_at: When the item was last updated
    """

    content: str = Field(
        description="Task description in imperative form (e.g., 'Run tests')",
        min_length=1,
    )
    active_form: str = Field(
        description="Present continuous form shown while in progress (e.g., 'Running tests')",
        min_length=1,
    )
    status: TodoStatus = Field(
        default=TodoStatus.PENDING,
        description="Current status: pending, in_progress, or completed",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_pending(self) -> bool:
        """Check if item is pending."""
        return self.status == TodoStatus.PENDING

    @property
    def is_in_progress(self) -> bool:
        """Check if item is in progress."""
        return self.status == TodoStatus.IN_PROGRESS

    @property
    def is_completed(self) -> bool:
        """Check if item is completed."""
        return self.status == TodoStatus.COMPLETED

    @property
    def display_text(self) -> str:
        """Get the appropriate display text based on status."""
        if self.is_in_progress:
            return self.active_form
        return self.content


class TodoList(BaseModel):
    """
    A complete todo list with items.

    Attributes:
        items: List of todo items
        last_updated: When the list was last modified
    """

    items: list[TodoItem] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

    @property
    def total_count(self) -> int:
        """Total number of items."""
        return len(self.items)

    @property
    def pending_count(self) -> int:
        """Number of pending items."""
        return sum(1 for item in self.items if item.is_pending)

    @property
    def in_progress_count(self) -> int:
        """Number of in-progress items."""
        return sum(1 for item in self.items if item.is_in_progress)

    @property
    def completed_count(self) -> int:
        """Number of completed items."""
        return sum(1 for item in self.items if item.is_completed)

    @property
    def current_task(self) -> TodoItem | None:
        """Get the currently in-progress task (should be at most one)."""
        for item in self.items:
            if item.is_in_progress:
                return item
        return None

    @property
    def is_empty(self) -> bool:
        """Check if the list is empty."""
        return len(self.items) == 0

    @property
    def is_all_completed(self) -> bool:
        """Check if all items are completed."""
        return all(item.is_completed for item in self.items) if self.items else True

    def get_summary(self) -> str:
        """Get a summary string."""
        if self.is_empty:
            return "No tasks"
        return f"{self.completed_count}/{self.total_count} completed"
