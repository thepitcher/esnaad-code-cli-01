"""Test script for subtask spawning functionality."""

import asyncio
from pathlib import Path

from esnaad.config.settings import get_settings
from esnaad.llm.client import LLMClient
from esnaad.state.manager import StateManager
from esnaad.models.subtask import Subtask
from esnaad.parallel.coordinator import ParallelCoordinator


async def test_parallel_subtasks():
    """Test spawning parallel subtasks."""
    settings = get_settings()

    print("=" * 60)
    print("Testing Parallel Subtask Execution")
    print("=" * 60)

    # Create LLM client
    async with LLMClient.from_settings(settings.llm) as client:
        # Create state manager
        state_manager = StateManager(settings.working_directory)

        # Define test subtasks
        subtasks = [
            Subtask(
                id="task-1",
                description="List files in current directory",
                prompt="List the files in the current directory using the list_directory tool. Return a summary of what you find.",
                tools=["list_directory"],
                depends_on=[],
            ),
            Subtask(
                id="task-2",
                description="Read pyproject.toml",
                prompt="Read the pyproject.toml file and summarize the project name and dependencies.",
                tools=["read_file"],
                depends_on=[],
            ),
            Subtask(
                id="task-3",
                description="Search for Python files",
                prompt="Search for all .py files in the src directory. Report how many you find.",
                tools=["search_files"],
                depends_on=[],
            ),
        ]

        print(f"\nSpawning {len(subtasks)} subtasks in parallel...")
        print("-" * 60)

        for st in subtasks:
            print(f"  [{st.id}] {st.description}")

        print("-" * 60)
        print("\nExecuting...\n")

        # Create coordinator and execute
        coordinator = ParallelCoordinator(
            llm_client=client,
            state_manager=state_manager,
            settings=settings,
        )

        results = await coordinator.execute_subtasks(subtasks)

        # Display results
        print("=" * 60)
        print("Results")
        print("=" * 60)

        for result in results:
            status_icon = "✓" if result.is_success else "✗"
            print(f"\n[{status_icon}] {result.id} ({result.status.value})")
            print(f"    Time: {result.execution_time:.2f}s" if result.execution_time else "    Time: N/A")

            if result.is_success:
                # Truncate long output
                output = result.result or ""
                if len(output) > 200:
                    output = output[:200] + "..."
                print(f"    Result: {output}")
            else:
                print(f"    Error: {result.error}")

        # Summary
        completed = sum(1 for r in results if r.is_success)
        failed = sum(1 for r in results if r.is_failed)

        print("\n" + "=" * 60)
        print(f"Summary: {completed} completed, {failed} failed, {len(results)} total")
        print("=" * 60)

        # Cleanup
        await state_manager.cleanup()


async def test_dependent_subtasks():
    """Test subtasks with dependencies."""
    settings = get_settings()

    print("\n" + "=" * 60)
    print("Testing Dependent Subtask Execution")
    print("=" * 60)

    async with LLMClient.from_settings(settings.llm) as client:
        state_manager = StateManager(settings.working_directory)

        # Define subtasks with dependencies
        subtasks = [
            Subtask(
                id="find-files",
                description="Find Python files",
                prompt="Search for .py files in the src directory. List them.",
                tools=["search_files"],
                depends_on=[],
            ),
            Subtask(
                id="analyze-results",
                description="Analyze the file list",
                prompt="Based on the file list from the previous task, summarize what components exist in this project.",
                tools=[],  # No tools needed, just analysis
                depends_on=["find-files"],  # Depends on first task
            ),
        ]

        print(f"\nSpawning {len(subtasks)} subtasks (with dependencies)...")
        print("-" * 60)

        for st in subtasks:
            deps = f" (depends on: {st.depends_on})" if st.depends_on else " (independent)"
            print(f"  [{st.id}] {st.description}{deps}")

        print("-" * 60)
        print("\nExecuting...\n")

        coordinator = ParallelCoordinator(
            llm_client=client,
            state_manager=state_manager,
            settings=settings,
        )

        results = await coordinator.execute_subtasks(subtasks)

        print("=" * 60)
        print("Results")
        print("=" * 60)

        for result in results:
            status_icon = "✓" if result.is_success else "✗"
            print(f"\n[{status_icon}] {result.id} ({result.status.value})")

            if result.is_success:
                output = result.result or ""
                if len(output) > 300:
                    output = output[:300] + "..."
                print(f"    Result: {output}")
            else:
                print(f"    Error: {result.error}")

        await state_manager.cleanup()


if __name__ == "__main__":
    print("\n🚀 Esnaad Code - Subtask Spawning Test\n")

    # Run tests
    asyncio.run(test_parallel_subtasks())
    asyncio.run(test_dependent_subtasks())

    print("\n✅ Test complete!")
