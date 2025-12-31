"""Plan mode state management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class ExecutionMode(Enum):
    """Execution mode for the agent."""

    AUTO_EDIT = "auto_edit"
    """Execute tools automatically without approval."""

    PLAN = "plan"
    """Request user approval before executing destructive tools."""


@dataclass
class PlanModeState:
    """
    Mutable state for plan mode.

    Tracks the current execution mode and notifies listeners on change.
    """

    mode: ExecutionMode = ExecutionMode.AUTO_EDIT
    """Current execution mode."""

    on_mode_change: Callable[[ExecutionMode], None] | None = None
    """Callback invoked when mode changes."""

    def toggle(self) -> ExecutionMode:
        """
        Toggle between Plan and Auto Edit modes.

        Returns:
            The new mode after toggling.
        """
        if self.mode == ExecutionMode.AUTO_EDIT:
            self.mode = ExecutionMode.PLAN
        else:
            self.mode = ExecutionMode.AUTO_EDIT

        if self.on_mode_change:
            self.on_mode_change(self.mode)

        return self.mode

    def set_mode(self, mode: ExecutionMode) -> None:
        """
        Set the execution mode explicitly.

        Args:
            mode: The mode to set.
        """
        if self.mode != mode:
            self.mode = mode
            if self.on_mode_change:
                self.on_mode_change(self.mode)

    @property
    def is_plan_mode(self) -> bool:
        """Check if currently in plan mode."""
        return self.mode == ExecutionMode.PLAN

    @property
    def is_auto_edit(self) -> bool:
        """Check if currently in auto edit mode."""
        return self.mode == ExecutionMode.AUTO_EDIT

    @property
    def mode_name(self) -> str:
        """Get human-readable mode name."""
        return "Plan Mode" if self.is_plan_mode else "Auto Edit"
