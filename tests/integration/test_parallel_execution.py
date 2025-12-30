"""Integration tests for parallel execution."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from esnaad.parallel.coordinator import ParallelCoordinator
from esnaad.parallel.executor import ParallelExecutor
from esnaad.models.subtask import Subtask, SubtaskStatus
from esnaad.state.manager import StateManager
from esnaad.config.settings import Settings


class TestParallelExecutor:
    """Tests for ParallelExecutor."""

    @pytest.fixture
    def executor(self) -> ParallelExecutor:
        """Create parallel executor."""
        return ParallelExecutor(timeout=5.0, max_retries=2)

    async def test_execute_single_task(
        self,
        executor: ParallelExecutor,
    ) -> None:
        """Test executing a single task."""
        async def task():
            return "result"

        tasks = [("task1", task)]
        results = await executor.execute_all(tasks)

        assert "task1" in results
        assert results["task1"] == "result"

    async def test_execute_multiple_tasks(
        self,
        executor: ParallelExecutor,
    ) -> None:
        """Test executing multiple tasks in parallel."""
        results_order = []

        async def task1():
            await asyncio.sleep(0.1)
            results_order.append("task1")
            return "result1"

        async def task2():
            await asyncio.sleep(0.05)
            results_order.append("task2")
            return "result2"

        tasks = [("task1", task1), ("task2", task2)]
        results = await executor.execute_all(tasks)

        assert results["task1"] == "result1"
        assert results["task2"] == "result2"

        # Task2 should complete first (shorter sleep)
        assert results_order[0] == "task2"

    async def test_task_timeout(self) -> None:
        """Test task timeout handling."""
        executor = ParallelExecutor(timeout=0.1, max_retries=0)

        async def slow_task():
            await asyncio.sleep(10)
            return "result"

        tasks = [("slow", slow_task)]
        results = await executor.execute_all(tasks)

        # Should be an exception due to timeout
        assert isinstance(results["slow"], Exception)

    async def test_task_retry(self) -> None:
        """Test task retry on failure."""
        executor = ParallelExecutor(timeout=5.0, max_retries=2)

        attempt_count = 0

        async def flaky_task():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Temporary error")
            return "success"

        tasks = [("flaky", flaky_task)]
        results = await executor.execute_all(tasks)

        assert results["flaky"] == "success"
        assert attempt_count == 2


class TestParallelCoordinator:
    """Tests for ParallelCoordinator."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create mock LLM client."""
        llm = MagicMock()
        llm.complete = AsyncMock(return_value={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Task completed!",
                    },
                    "finish_reason": "stop",
                }
            ]
        })
        return llm

    @pytest.fixture
    async def coordinator(
        self,
        mock_llm: MagicMock,
        state_manager: StateManager,
        settings: Settings,
    ) -> ParallelCoordinator:
        """Create parallel coordinator."""
        return ParallelCoordinator(
            llm_client=mock_llm,
            state_manager=state_manager,
            settings=settings,
        )

    async def test_execute_independent_subtasks(
        self,
        coordinator: ParallelCoordinator,
    ) -> None:
        """Test executing independent subtasks."""
        subtasks = [
            Subtask(
                id="task1",
                description="First task",
                prompt="Do task 1",
            ),
            Subtask(
                id="task2",
                description="Second task",
                prompt="Do task 2",
            ),
        ]

        results = await coordinator.execute_subtasks(subtasks)

        assert len(results) == 2
        assert results[0].id == "task1"
        assert results[1].id == "task2"

    async def test_execute_dependent_subtasks(
        self,
        coordinator: ParallelCoordinator,
    ) -> None:
        """Test executing subtasks with dependencies."""
        subtasks = [
            Subtask(
                id="task1",
                description="First task",
                prompt="Do task 1",
            ),
            Subtask(
                id="task2",
                description="Second task",
                prompt="Do task 2",
                depends_on=["task1"],
            ),
        ]

        results = await coordinator.execute_subtasks(subtasks)

        assert len(results) == 2
        # Task1 should complete before task2
        assert results[0].id == "task1"
        assert results[1].id == "task2"

    async def test_missing_dependency_fails(
        self,
        coordinator: ParallelCoordinator,
    ) -> None:
        """Test that missing dependencies cause failure."""
        subtasks = [
            Subtask(
                id="task2",
                description="Task with missing dependency",
                prompt="Do task 2",
                depends_on=["nonexistent"],
            ),
        ]

        results = await coordinator.execute_subtasks(subtasks)

        assert len(results) == 1
        assert results[0].status == SubtaskStatus.FAILED
        assert "missing" in results[0].error.lower()
