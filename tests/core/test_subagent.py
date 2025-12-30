"""Tests for SubAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from esnaad.core.subagent import SubAgent, SubAgentConfig
from esnaad.models.subtask import Subtask, SubtaskStatus
from esnaad.config.settings import Settings


class TestSubAgentConfig:
    """Tests for SubAgentConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = SubAgentConfig()
        assert config.max_iterations == 20
        assert config.timeout_seconds == 120
        assert config.max_retries == 2

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = SubAgentConfig(
            max_iterations=10,
            timeout_seconds=60,
            max_retries=3,
            model="gpt-3.5-turbo",
        )
        assert config.max_iterations == 10
        assert config.timeout_seconds == 60
        assert config.max_retries == 3


class TestSubAgent:
    """Tests for SubAgent."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create mock LLM client."""
        client = MagicMock()
        client.complete = AsyncMock()
        return client

    @pytest.fixture
    def subagent(
        self,
        mock_llm_client: MagicMock,
        settings: Settings,
        state_manager,
    ) -> SubAgent:
        """Create subagent for testing."""
        return SubAgent(
            agent_id="test-subagent-001",
            llm_client=mock_llm_client,
            allowed_tools=["read_file"],
            state_manager=state_manager,
            settings=settings,
        )

    async def test_initialization(
        self,
        subagent: SubAgent,
    ) -> None:
        """Test subagent initialization."""
        assert subagent.agent_id == "test-subagent-001"
        assert "read_file" in subagent.allowed_tools

    async def test_execute_subtask(
        self,
        subagent: SubAgent,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test executing a subtask."""
        mock_llm_client.complete.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Task completed successfully!",
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        subtask = Subtask(
            id="subtask-001",
            description="Test subtask",
            prompt="Do something simple",
            tools=["read_file"],
        )

        result = await subagent.execute(subtask)

        assert result.id == "subtask-001"
        assert result.status == SubtaskStatus.COMPLETE
        assert result.result == "Task completed successfully!"

    async def test_execute_with_tool_use(
        self,
        subagent: SubAgent,
        mock_llm_client: MagicMock,
        temp_dir,
    ) -> None:
        """Test executing subtask that uses tools."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("File content")

        mock_llm_client.complete.side_effect = [
            # First call: use read_file tool
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": f'{{"file_path": "{test_file}"}}',
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
            # Second call: final response
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Read the file successfully.",
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        ]

        subtask = Subtask(
            id="subtask-002",
            description="Read a file",
            prompt=f"Read {test_file}",
            tools=["read_file"],
        )

        result = await subagent.execute(subtask)

        assert result.status == SubtaskStatus.COMPLETE
        assert result.iterations == 2

    async def test_independent_subtask(self) -> None:
        """Test subtask independence check."""
        independent = Subtask(
            id="independent",
            description="No dependencies",
            prompt="Do something",
        )
        assert independent.is_independent is True

        dependent = Subtask(
            id="dependent",
            description="Has dependencies",
            prompt="Do something else",
            depends_on=["independent"],
        )
        assert dependent.is_independent is False
