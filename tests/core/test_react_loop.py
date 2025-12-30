"""Tests for ReAct loop."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from esnaad.core.react_loop import ReActLoop, ReActConfig
from esnaad.models.tool_call import ToolCall, ToolResult
from esnaad.models.result import AgentStatus


class TestReActConfig:
    """Tests for ReActConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = ReActConfig()
        assert config.max_iterations == 50
        assert config.timeout_seconds == 300
        assert config.model == "gpt-4"

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = ReActConfig(
            max_iterations=10,
            timeout_seconds=60,
            model="gpt-3.5-turbo",
            temperature=0.5,
        )
        assert config.max_iterations == 10
        assert config.timeout_seconds == 60
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5


class TestReActLoop:
    """Tests for ReActLoop."""

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create mock LLM client."""
        llm = MagicMock()
        llm.complete = AsyncMock()
        return llm

    @pytest.fixture
    def mock_tool_executor(self) -> AsyncMock:
        """Create mock tool executor."""
        return AsyncMock()

    @pytest.fixture
    def config(self) -> ReActConfig:
        """Create test config."""
        return ReActConfig(max_iterations=5, timeout_seconds=10)

    @pytest.fixture
    def loop(
        self,
        mock_llm: MagicMock,
        mock_tool_executor: AsyncMock,
        config: ReActConfig,
    ) -> ReActLoop:
        """Create ReAct loop for testing."""
        return ReActLoop(
            llm_client=mock_llm,
            config=config,
            tool_executor=mock_tool_executor,
            tools_schema=[],
        )

    async def test_simple_response(
        self,
        loop: ReActLoop,
        mock_llm: MagicMock,
    ) -> None:
        """Test simple response without tool calls."""
        # Mock LLM to return simple response
        mock_llm.complete.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help?",
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        messages = [{"role": "user", "content": "Hello"}]
        result = await loop.run(messages)

        assert result.status == AgentStatus.COMPLETE
        assert result.content == "Hello! How can I help?"
        assert result.iterations == 1

    async def test_with_tool_call(
        self,
        loop: ReActLoop,
        mock_llm: MagicMock,
        mock_tool_executor: AsyncMock,
    ) -> None:
        """Test response with tool call."""
        # First call returns tool call
        mock_llm.complete.side_effect = [
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
                                        "name": "test_tool",
                                        "arguments": '{"arg": "value"}',
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
            # Second call returns final response
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Done! I used the tool.",
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        ]

        # Mock tool execution
        mock_tool_executor.return_value = ToolResult.success(
            tool_call_id="call_123",
            tool_name="test_tool",
            output={"result": "success"},
        )

        messages = [{"role": "user", "content": "Use the tool"}]
        result = await loop.run(messages)

        assert result.status == AgentStatus.COMPLETE
        assert result.content == "Done! I used the tool."
        assert result.iterations == 2
        mock_tool_executor.assert_called_once()

    async def test_max_iterations(
        self,
        loop: ReActLoop,
        mock_llm: MagicMock,
        mock_tool_executor: AsyncMock,
    ) -> None:
        """Test hitting max iterations."""
        # Always return tool calls
        mock_llm.complete.return_value = {
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
                                    "name": "test_tool",
                                    "arguments": "{}",
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }

        mock_tool_executor.return_value = ToolResult.success(
            tool_call_id="call_123",
            tool_name="test_tool",
            output="result",
        )

        messages = [{"role": "user", "content": "Loop forever"}]
        result = await loop.run(messages)

        # Should hit max iterations (5)
        assert result.status == AgentStatus.INCOMPLETE
        assert result.iterations == 5

    async def test_callbacks(
        self,
        mock_llm: MagicMock,
        mock_tool_executor: AsyncMock,
        config: ReActConfig,
    ) -> None:
        """Test that callbacks are called."""
        on_thinking = AsyncMock()
        on_tool_call = AsyncMock()
        on_tool_result = AsyncMock()

        loop = ReActLoop(
            llm_client=mock_llm,
            config=config,
            tool_executor=mock_tool_executor,
            tools_schema=[],
            on_thinking=on_thinking,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )

        mock_llm.complete.side_effect = [
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Thinking...",
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "type": "function",
                                    "function": {
                                        "name": "test_tool",
                                        "arguments": "{}",
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Done!",
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        ]

        mock_tool_executor.return_value = ToolResult.success(
            tool_call_id="call_123",
            tool_name="test_tool",
            output="result",
        )

        messages = [{"role": "user", "content": "Test"}]
        await loop.run(messages)

        # Callbacks should have been called
        on_tool_call.assert_called_once()
        on_tool_result.assert_called_once()
