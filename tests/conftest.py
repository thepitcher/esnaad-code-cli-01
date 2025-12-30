"""Shared pytest fixtures for Esnaad Code tests."""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from esnaad.config.settings import Settings, LLMSettings, OrchestratorSettings, SubAgentSettings, ToolSettings
from esnaad.tools.base import ToolContext
from esnaad.state.manager import StateManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def settings(temp_dir: Path) -> Settings:
    """Create test settings."""
    return Settings(
        debug=True,
        log_level="DEBUG",
        working_directory=temp_dir,
        config_dir=temp_dir / ".esnaad",
        llm=LLMSettings(
            base_url="http://localhost:3000/api",
            api_key="test-key",
            model="test-model",
        ),
        orchestrator=OrchestratorSettings(
            max_iterations=10,
            timeout_seconds=30,
        ),
        subagent=SubAgentSettings(
            max_iterations=5,
            timeout_seconds=15,
        ),
        tools=ToolSettings(),
    )


@pytest.fixture
def tool_context(settings: Settings, temp_dir: Path) -> ToolContext:
    """Create a tool context for testing."""
    return ToolContext(
        working_directory=temp_dir,
        settings=settings,
        agent_id="test-agent",
        is_subagent=False,
        state_manager=None,
        metadata={},
    )


@pytest.fixture
async def state_manager(temp_dir: Path) -> AsyncGenerator[StateManager, None]:
    """Create a state manager for testing."""
    manager = StateManager(temp_dir)
    yield manager
    await manager.cleanup()


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    client = MagicMock()
    client.complete = AsyncMock()
    client.stream = AsyncMock()
    return client


@pytest.fixture
def sample_file(temp_dir: Path) -> Path:
    """Create a sample file for testing."""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
    return file_path


@pytest.fixture
def sample_directory(temp_dir: Path) -> Path:
    """Create a sample directory structure for testing."""
    # Create subdirectories
    (temp_dir / "src").mkdir()
    (temp_dir / "src" / "module").mkdir()
    (temp_dir / "tests").mkdir()

    # Create files
    (temp_dir / "README.md").write_text("# Test Project\n")
    (temp_dir / "src" / "__init__.py").write_text("")
    (temp_dir / "src" / "main.py").write_text("def main():\n    pass\n")
    (temp_dir / "src" / "module" / "__init__.py").write_text("")
    (temp_dir / "src" / "module" / "utils.py").write_text("def helper():\n    return 42\n")
    (temp_dir / "tests" / "test_main.py").write_text("def test_main():\n    pass\n")

    return temp_dir
