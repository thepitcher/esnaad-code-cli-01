"""Spawn subtasks tool for parallel sub-agent execution."""

from typing import Any

from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool
from esnaad.models.subtask import Subtask, SubtaskResult


class SubtaskDefinition(BaseModel):
    """Definition of a subtask to spawn."""

    id: str = Field(description="Unique identifier for the subtask")
    description: str = Field(description="Brief description of what the subtask does")
    prompt: str = Field(description="Full prompt/instructions for the sub-agent")
    tools: list[str] = Field(
        default_factory=list,
        description="List of tool names the sub-agent can use (empty = all tools)",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of subtasks this one depends on (for sequential execution)",
    )


class SpawnSubtasksInput(BaseModel):
    """Input schema for spawn_subtasks tool."""

    subtasks: list[SubtaskDefinition] = Field(
        min_length=1,
        max_length=10,
        description="List of subtasks to execute (1-10 subtasks)",
    )
    wait_for_completion: bool = Field(
        default=True,
        description="Whether to wait for all subtasks to complete",
    )


class SubtaskResultOutput(BaseModel):
    """Output for a single subtask result."""

    id: str = Field(description="Subtask ID")
    status: str = Field(description="Execution status")
    result: str | None = Field(default=None, description="Final result content")
    error: str | None = Field(default=None, description="Error message if failed")
    execution_time: float | None = Field(default=None, description="Time in seconds")


class SpawnSubtasksOutput(BaseModel):
    """Output schema for spawn_subtasks tool."""

    total: int = Field(description="Total number of subtasks")
    completed: int = Field(description="Number of completed subtasks")
    failed: int = Field(description="Number of failed subtasks")
    results: list[SubtaskResultOutput] = Field(description="Individual results")


@register_tool
class SpawnSubtasksTool(BaseTool[SpawnSubtasksInput, SpawnSubtasksOutput]):
    """
    Spawn multiple sub-agents to execute subtasks in parallel.

    Use this tool when you have independent subtasks that can run concurrently.
    Sub-agents operate with their own context and can use specified tools.
    Results are aggregated and returned once all subtasks complete.

    Example use cases:
    - Reading multiple files simultaneously
    - Running independent searches
    - Performing parallel analysis of different components
    """

    name = "spawn_subtasks"
    description = (
        "Execute multiple subtasks in parallel using sub-agents. "
        "Use this when you have independent tasks that can run concurrently. "
        "Each subtask gets its own sub-agent with specified tools. "
        "Subtasks can have dependencies for sequential execution within the parallel batch."
    )
    parallel_safe = False  # This tool manages parallelism internally
    requires_lock = False

    @property
    def input_schema(self) -> type[SpawnSubtasksInput]:
        return SpawnSubtasksInput

    @property
    def output_schema(self) -> type[SpawnSubtasksOutput]:
        return SpawnSubtasksOutput

    async def execute(
        self,
        input_data: SpawnSubtasksInput,
        context: ToolContext,
    ) -> SpawnSubtasksOutput:
        """Execute subtasks using the parallel coordinator."""
        from esnaad.parallel.coordinator import ParallelCoordinator
        from esnaad.exceptions import ToolExecutionError

        # Get LLM client from metadata (injected by orchestrator)
        llm_client = context.metadata.get("llm_client")
        if llm_client is None:
            raise ToolExecutionError(
                tool_name=self.name,
                message="LLM client not available in tool context",
            )

        # Get rules from context (for sub-agent inheritance)
        rules = context.metadata.get("rules")

        # Convert input subtasks to Subtask models
        subtasks = [
            Subtask(
                id=s.id,
                description=s.description,
                prompt=s.prompt,
                tools=s.tools,
                depends_on=s.depends_on,
            )
            for s in input_data.subtasks
        ]

        # Create coordinator
        coordinator = ParallelCoordinator(
            llm_client=llm_client,
            state_manager=context.state_manager,
            settings=context.settings,
            rules=rules,
        )

        # Execute subtasks
        results: list[SubtaskResult] = await coordinator.execute_subtasks(subtasks)

        # Convert to output format
        result_outputs = [
            SubtaskResultOutput(
                id=r.id,
                status=r.status.value,
                result=r.result,
                error=r.error,
                execution_time=r.execution_time,
            )
            for r in results
        ]

        completed = sum(1 for r in results if r.is_success)
        failed = sum(1 for r in results if r.is_failed)

        return SpawnSubtasksOutput(
            total=len(results),
            completed=completed,
            failed=failed,
            results=result_outputs,
        )
