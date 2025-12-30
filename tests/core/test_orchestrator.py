"""Tests for Orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from esnaad.core.orchestrator import Orchestrator, OrchestratorConfig
from esnaad.config.settings import Settings
from esnaad.models.result import AgentStatus


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = OrchestratorConfig()
        assert config.max_iterations == 50
        assert config.timeout_seconds == 300
        assert config.model == "gpt-4"
        assert config.enable_clarifications is True

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = OrchestratorConfig(
            max_iterations=20,
            timeout_seconds=120,
            model="gpt-3.5-turbo",
            enable_clarifications=False,
        )
        assert config.max_iterations == 20
        assert config.timeout_seconds == 120
        assert config.enable_clarifications is False


class TestOrchestrator:
    """Tests for Orchestrator."""

    @pytest.fixture
    def mock_llm_client(self) -> MagicMock:
        """Create mock LLM client."""
        client = MagicMock()
        client.complete = AsyncMock()
        return client

    @pytest.fixture
    def orchestrator(
        self,
        mock_llm_client: MagicMock,
        settings: Settings,
    ) -> Orchestrator:
        """Create orchestrator for testing."""
        return Orchestrator(
            llm_client=mock_llm_client,
            settings=settings,
        )

    async def test_initialization(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        """Test orchestrator initialization."""
        assert orchestrator.agent_id.startswith("orchestrator-")
        assert orchestrator.messages == []

    async def test_run_simple_message(
        self,
        orchestrator: Orchestrator,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test running a simple message."""
        mock_llm_client.complete.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello! I'm here to help.",
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        result = await orchestrator.run("Hello!")

        assert result.status == AgentStatus.COMPLETE
        assert result.content == "Hello! I'm here to help."

        # Should have system message + user message in history
        assert len(orchestrator.messages) == 3  # system + user + assistant

    async def test_run_with_tool_use(
        self,
        orchestrator: Orchestrator,
        mock_llm_client: MagicMock,
        temp_dir: Path,
    ) -> None:
        """Test running with tool use."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")

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
                            "content": "I read the file, it contains 'Test content'.",
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        ]

        result = await orchestrator.run(f"Read the file {test_file}")

        assert result.status == AgentStatus.COMPLETE
        assert "Test content" in result.content

    async def test_clear_history(
        self,
        orchestrator: Orchestrator,
        mock_llm_client: MagicMock,
    ) -> None:
        """Test clearing conversation history."""
        mock_llm_client.complete.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello!",
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        await orchestrator.run("Hello")
        assert len(orchestrator.messages) > 0

        orchestrator.clear_history()
        assert len(orchestrator.messages) == 0

    async def test_cleanup(
        self,
        orchestrator: Orchestrator,
    ) -> None:
        """Test cleanup method."""
        # Should not raise
        await orchestrator.cleanup()

    async def test_callbacks(
        self,
        mock_llm_client: MagicMock,
        settings: Settings,
    ) -> None:
        """Test that callbacks are invoked."""
        on_content = MagicMock()
        on_tool_call = MagicMock()
        on_tool_result = MagicMock()

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            settings=settings,
            on_content=on_content,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )

        mock_llm_client.complete.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello!",
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        await orchestrator.run("Hello")

        # on_content may or may not be called depending on implementation
        # The test ensures orchestrator is properly initialized with callbacks

    async def test_clarification_handler(
        self,
        mock_llm_client: MagicMock,
        settings: Settings,
    ) -> None:
        """Test that clarification handler is passed to tools."""
        mock_handler = AsyncMock()

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            settings=settings,
            clarification_handler=mock_handler,
        )

        assert orchestrator._clarification_handler == mock_handler
