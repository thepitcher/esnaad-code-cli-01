"""Parallel task executor with timeout and retry logic."""

import asyncio
from typing import TypeVar, Callable, Awaitable, Any

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class ParallelExecutor:
    """
    Execute multiple async tasks with timeout and retry logic.

    Features:
    - Concurrent execution with asyncio.gather
    - Per-task timeout
    - Retry with exponential backoff
    - Partial results on failure
    """

    def __init__(
        self,
        timeout: float = 120.0,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ) -> None:
        """
        Initialize the executor.

        Args:
            timeout: Timeout per task in seconds
            max_retries: Maximum retry attempts
            retry_delay: Base delay between retries
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def execute_all(
        self,
        tasks: list[tuple[str, Callable[[], Awaitable[T]]]],
        return_partial: bool = True,
    ) -> dict[str, T | Exception]:
        """
        Execute all tasks in parallel.

        Args:
            tasks: List of (id, async_callable) tuples
            return_partial: If True, return partial results on failure

        Returns:
            Dict of task_id -> result or exception
        """
        logger.info(
            "Executing tasks in parallel",
            task_count=len(tasks),
            timeout=self.timeout,
        )

        async def execute_one(task_id: str, task: Callable[[], Awaitable[T]]) -> T:
            return await self._execute_with_retry(task, task_id)

        # Create coroutines
        coros = [
            execute_one(task_id, task_fn)
            for task_id, task_fn in tasks
        ]
        task_ids = [task_id for task_id, _ in tasks]

        # Execute with exception handling
        results = await asyncio.gather(
            *coros,
            return_exceptions=True,
        )

        # Map results to task IDs
        return dict(zip(task_ids, results))

    async def _execute_with_retry(
        self,
        task: Callable[[], Awaitable[T]],
        task_id: str,
    ) -> T:
        """Execute a single task with retry logic."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    task(),
                    timeout=self.timeout,
                )
                logger.debug(
                    "Task completed",
                    task_id=task_id,
                    attempt=attempt + 1,
                )
                return result

            except asyncio.TimeoutError:
                last_error = asyncio.TimeoutError(
                    f"Task '{task_id}' timed out after {self.timeout}s"
                )
                logger.warning(
                    "Task timed out",
                    task_id=task_id,
                    attempt=attempt + 1,
                    timeout=self.timeout,
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    "Task failed",
                    task_id=task_id,
                    attempt=attempt + 1,
                    error=str(e),
                )

            # Retry with exponential backoff
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)
                logger.debug(
                    "Retrying task",
                    task_id=task_id,
                    delay=delay,
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        raise last_error or Exception(f"Task '{task_id}' failed after {self.max_retries + 1} attempts")


async def run_parallel(
    *tasks: Callable[[], Awaitable[T]],
    timeout: float = 120.0,
) -> list[T | Exception]:
    """
    Simple helper to run multiple tasks in parallel.

    Args:
        *tasks: Async callables to execute
        timeout: Timeout per task

    Returns:
        List of results or exceptions
    """
    async def with_timeout(task: Callable[[], Awaitable[T]]) -> T:
        return await asyncio.wait_for(task(), timeout=timeout)

    return await asyncio.gather(
        *[with_timeout(t) for t in tasks],
        return_exceptions=True,
    )
