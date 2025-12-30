"""Parallel coordinator for sub-agent execution."""

import asyncio
import uuid
from typing import Any

import structlog

from esnaad.llm.client import LLMClient
from esnaad.models.subtask import Subtask, SubtaskResult
from esnaad.core.subagent import SubAgent, SubAgentConfig
from esnaad.state.manager import StateManager
from esnaad.config.settings import Settings
from esnaad.parallel.executor import ParallelExecutor

logger = structlog.get_logger(__name__)


class ParallelCoordinator:
    """
    Coordinates parallel execution of sub-agents.

    Handles:
    - Fan-out: Dispatch subtasks to sub-agents
    - Fan-in: Aggregate results
    - Dependency resolution
    - Failure handling
    """

    def __init__(
        self,
        llm_client: LLMClient,
        state_manager: StateManager,
        settings: Settings,
        config: SubAgentConfig | None = None,
        rules: str | None = None,
    ) -> None:
        """
        Initialize the coordinator.

        Args:
            llm_client: LLM client for sub-agents
            state_manager: Shared state manager
            settings: Application settings
            config: Sub-agent configuration
            rules: Project rules to pass to sub-agents
        """
        self.llm = llm_client
        self.state = state_manager
        self.settings = settings
        self.rules = rules
        self.config = config or SubAgentConfig(
            max_iterations=settings.subagent.max_iterations,
            timeout_seconds=settings.subagent.timeout_seconds,
            max_retries=settings.subagent.max_retries,
            model=settings.llm.model,
        )

        self.executor = ParallelExecutor(
            timeout=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
        )

    async def execute_subtasks(
        self,
        subtasks: list[Subtask],
    ) -> list[SubtaskResult]:
        """
        Execute multiple subtasks in parallel.

        Handles dependencies by executing in waves:
        1. Execute all independent subtasks
        2. For dependent subtasks, wait for dependencies
        3. Pass dependency results as context

        Args:
            subtasks: List of subtasks to execute

        Returns:
            List of subtask results
        """
        logger.info(
            "Executing subtasks",
            count=len(subtasks),
        )

        # Separate independent and dependent subtasks
        independent = [s for s in subtasks if s.is_independent]
        dependent = [s for s in subtasks if not s.is_independent]

        results: dict[str, SubtaskResult] = {}

        # Phase 1: Execute independent subtasks in parallel
        if independent:
            logger.debug(
                "Executing independent subtasks",
                count=len(independent),
            )

            async def create_executor(subtask: Subtask):
                return await self._execute_single(subtask)

            tasks = [
                (s.id, lambda s=s: self._execute_single(s))
                for s in independent
            ]

            phase1_results = await self.executor.execute_all(tasks)

            for task_id, result in phase1_results.items():
                if isinstance(result, Exception):
                    results[task_id] = SubtaskResult.failed(
                        id=task_id,
                        error=str(result),
                    )
                else:
                    results[task_id] = result

        # Phase 2: Execute dependent subtasks
        # (simplified - sequential execution of remaining)
        for subtask in dependent:
            # Check if dependencies are complete
            missing_deps = [
                dep for dep in subtask.depends_on
                if dep not in results
            ]

            if missing_deps:
                results[subtask.id] = SubtaskResult.failed(
                    id=subtask.id,
                    error=f"Missing dependencies: {missing_deps}",
                )
                continue

            # Check if any dependency failed
            failed_deps = [
                dep for dep in subtask.depends_on
                if results[dep].is_failed
            ]

            if failed_deps:
                results[subtask.id] = SubtaskResult.failed(
                    id=subtask.id,
                    error=f"Dependencies failed: {failed_deps}",
                )
                continue

            # Build context from dependencies
            dep_context = self._build_dependency_context(
                subtask.depends_on,
                results,
            )

            # Modify prompt with dependency context
            enriched_subtask = Subtask(
                id=subtask.id,
                description=subtask.description,
                prompt=f"{subtask.prompt}\n\n## Results from dependent tasks:\n{dep_context}",
                tools=subtask.tools,
                depends_on=[],  # Clear dependencies as we've resolved them
            )

            # Execute
            result = await self._execute_single(enriched_subtask)
            results[subtask.id] = result

        # Return in original order
        return [results[s.id] for s in subtasks]

    async def _execute_single(self, subtask: Subtask) -> SubtaskResult:
        """Execute a single subtask."""
        agent_id = f"subagent-{subtask.id}-{uuid.uuid4().hex[:6]}"

        logger.debug(
            "Creating sub-agent",
            agent_id=agent_id,
            subtask_id=subtask.id,
        )

        agent = SubAgent(
            agent_id=agent_id,
            llm_client=self.llm,
            allowed_tools=subtask.tools,
            state_manager=self.state,
            settings=self.settings,
            config=self.config,
            rules=self.rules,
        )

        try:
            return await agent.execute(subtask)
        except Exception as e:
            logger.exception(
                "Sub-agent execution failed",
                agent_id=agent_id,
                subtask_id=subtask.id,
            )
            return SubtaskResult.failed(
                id=subtask.id,
                error=str(e),
            )

    def _build_dependency_context(
        self,
        dependency_ids: list[str],
        results: dict[str, SubtaskResult],
    ) -> str:
        """Build context string from dependency results."""
        parts = []
        for dep_id in dependency_ids:
            if dep_id in results:
                result = results[dep_id]
                parts.append(f"### {dep_id}\n{result.output}")
        return "\n\n".join(parts)


async def spawn_and_execute(
    subtasks: list[Subtask],
    llm_client: LLMClient,
    state_manager: StateManager,
    settings: Settings,
    rules: str | None = None,
) -> list[SubtaskResult]:
    """
    Helper function to spawn and execute subtasks.

    Args:
        subtasks: Subtasks to execute
        llm_client: LLM client
        state_manager: State manager
        settings: Settings
        rules: Project rules to pass to sub-agents

    Returns:
        List of subtask results
    """
    coordinator = ParallelCoordinator(
        llm_client=llm_client,
        state_manager=state_manager,
        settings=settings,
        rules=rules,
    )
    return await coordinator.execute_subtasks(subtasks)
