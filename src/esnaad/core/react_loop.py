"""ReAct (Reasoning + Acting) loop implementation."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

import structlog

from esnaad.llm.client import LLMClient, ChatResponse, ChatChunk
from esnaad.llm.streaming import StreamingHandler
from esnaad.models.tool_call import ToolCall, ToolResult
from esnaad.models.result import AgentResult, AgentStatus
from esnaad.exceptions import MaxIterationsError, AgentTimeoutError
from esnaad.tools.registry import ToolRegistry

logger = structlog.get_logger(__name__)


@dataclass
class ReActConfig:
    """Configuration for the ReAct loop."""

    max_iterations: int = 50
    timeout_seconds: int = 300
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False  # Enable streaming responses


@dataclass
class ReActState:
    """State of the ReAct loop."""

    messages: list[dict[str, Any]] = field(default_factory=list)
    iteration: int = 0
    tool_calls_count: int = 0
    start_time: float = field(default_factory=time.time)
    last_response: ChatResponse | None = None


class ReActLoop:
    """
    Generic ReAct loop implementation.

    Implements the Reason → Act → Observe cycle:
    1. Send messages to LLM
    2. If LLM returns tool calls, execute them
    3. Add tool results to messages
    4. Repeat until LLM returns final answer or limits reached
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: ReActConfig,
        tool_executor: Callable[[ToolCall], Awaitable[ToolResult]],
        tools_schema: list[dict[str, Any]],
        on_thinking: Callable[[str], Awaitable[None] | None] | None = None,
        on_tool_call: Callable[[ToolCall], Awaitable[None] | None] | None = None,
        on_tool_result: Callable[[ToolResult], Awaitable[None] | None] | None = None,
        on_content_delta: Callable[[str], Awaitable[None] | None] | None = None,
        on_thinking_start: Callable[[], Awaitable[None] | None] | None = None,
        on_thinking_end: Callable[[], Awaitable[None] | None] | None = None,
    ) -> None:
        """
        Initialize the ReAct loop.

        Args:
            llm_client: LLM client for completions
            config: Loop configuration
            tool_executor: Async function to execute tool calls
            tools_schema: OpenAI-format tool schemas
            on_thinking: Callback for thinking/reasoning output (complete)
            on_tool_call: Callback when a tool is called
            on_tool_result: Callback when a tool returns
            on_content_delta: Callback for streaming content deltas
            on_thinking_start: Callback when LLM request starts
            on_thinking_end: Callback when LLM request ends
        """
        self.llm = llm_client
        self.config = config
        self.tool_executor = tool_executor
        self.tools_schema = tools_schema
        self.on_thinking = on_thinking
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_content_delta = on_content_delta
        self.on_thinking_start = on_thinking_start
        self.on_thinking_end = on_thinking_end

    async def run(
        self,
        initial_messages: list[dict[str, Any]],
    ) -> AgentResult:
        """
        Run the ReAct loop.

        Args:
            initial_messages: Starting messages (system + user)

        Returns:
            Final agent result
        """
        state = ReActState(messages=list(initial_messages))

        logger.info(
            "Starting ReAct loop",
            max_iterations=self.config.max_iterations,
            timeout=self.config.timeout_seconds,
        )

        try:
            while state.iteration < self.config.max_iterations:
                # Check timeout
                elapsed = time.time() - state.start_time
                if elapsed > self.config.timeout_seconds:
                    raise AgentTimeoutError(
                        operation="ReAct loop",
                        timeout=self.config.timeout_seconds,
                    )

                # Execute one step
                result = await self._step(state)

                if result is not None:
                    # Loop complete
                    return result

                state.iteration += 1

            # Max iterations reached
            raise MaxIterationsError(
                iterations=state.iteration,
                max_iterations=self.config.max_iterations,
            )

        except MaxIterationsError:
            logger.warning(
                "Max iterations reached",
                iterations=state.iteration,
            )
            return AgentResult.max_iterations(
                iterations=state.iteration,
                max_iterations=self.config.max_iterations,
                partial_content=self._get_last_content(state),
                execution_time=time.time() - state.start_time,
                tool_calls_count=state.tool_calls_count,
            )

        except AgentTimeoutError as e:
            logger.warning(
                "Timeout reached",
                timeout=e.timeout,
            )
            return AgentResult.timeout(
                timeout=e.timeout,
                iterations=state.iteration,
                partial_content=self._get_last_content(state),
                tool_calls_count=state.tool_calls_count,
            )

        except Exception as e:
            logger.exception("ReAct loop error")
            return AgentResult.error(
                error=str(e),
                iterations=state.iteration,
                execution_time=time.time() - state.start_time,
                tool_calls_count=state.tool_calls_count,
            )

    async def _step(self, state: ReActState) -> AgentResult | None:
        """
        Execute one ReAct step.

        Returns AgentResult if complete, None to continue.
        """
        logger.debug(
            "ReAct step",
            iteration=state.iteration,
            message_count=len(state.messages),
        )

        # Signal thinking start
        if self.on_thinking_start:
            result = self.on_thinking_start()
            if hasattr(result, "__await__"):
                await result

        try:
            if self.config.stream:
                response = await self._step_streaming(state)
            else:
                response = await self._step_non_streaming(state)
        finally:
            # Signal thinking end
            if self.on_thinking_end:
                result = self.on_thinking_end()
                if hasattr(result, "__await__"):
                    await result

        state.last_response = response

        # Check for thinking/reasoning output (non-streaming only)
        if not self.config.stream and response.content and self.on_thinking:
            result = self.on_thinking(response.content)
            if hasattr(result, "__await__"):
                await result

        # Check if we're done (no tool calls)
        if not response.has_tool_calls:
            # Warn if model said tool_calls but didn't provide any
            if response.finish_reason == "tool_calls":
                logger.warning(
                    "Model indicated tool_calls but none were received. "
                    "This may indicate a model or API issue.",
                    finish_reason=response.finish_reason,
                    content_length=len(response.content) if response.content else 0,
                )

            # Retry if model returned empty response after tool calls
            # This handles cases where the model stops without providing output
            content_is_empty = not response.content or not response.content.strip()
            has_previous_tool_calls = state.tool_calls_count > 0
            retry_limit_not_reached = state.iteration < min(3, self.config.max_iterations - 1)

            if content_is_empty and has_previous_tool_calls and retry_limit_not_reached:
                logger.warning(
                    "Model returned empty response after tool calls, prompting to continue",
                    iteration=state.iteration,
                    tool_calls_count=state.tool_calls_count,
                )
                # Add a prompt to encourage the model to provide output
                state.messages.append({
                    "role": "user",
                    "content": "Please provide your analysis and response based on the tool results above.",
                })
                return None  # Continue loop

            logger.info(
                "ReAct loop complete",
                iterations=state.iteration,
                finish_reason=response.finish_reason,
            )
            return AgentResult.success(
                content=response.content or "",
                iterations=state.iteration,
                execution_time=time.time() - state.start_time,
                tool_calls_count=state.tool_calls_count,
            )

        # Add assistant message with tool calls
        assistant_msg = {"role": "assistant", "content": response.content}
        if response.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": str(tc.arguments),
                    },
                }
                for tc in response.tool_calls
            ]
        state.messages.append(assistant_msg)

        # Execute tool calls (skip callback for streaming since handler already called it)
        # Separate parallel-safe and sequential tools
        parallel_calls: list[ToolCall] = []
        sequential_calls: list[ToolCall] = []

        for tool_call in response.tool_calls:
            tool = ToolRegistry.get(tool_call.name)
            if tool and tool.parallel_safe and not tool.requires_lock:
                parallel_calls.append(tool_call)
            else:
                sequential_calls.append(tool_call)

        tool_results: dict[str, ToolResult] = {}

        # Execute parallel-safe tools concurrently
        if parallel_calls:
            logger.debug(
                "Executing tools in parallel",
                count=len(parallel_calls),
                tools=[tc.name for tc in parallel_calls],
            )

            # Fire callbacks for all parallel calls first
            for tool_call in parallel_calls:
                state.tool_calls_count += 1
                if not self.config.stream and self.on_tool_call:
                    result = self.on_tool_call(tool_call)
                    if hasattr(result, "__await__"):
                        await result

            # Execute all in parallel
            parallel_results = await asyncio.gather(
                *[self.tool_executor(tc) for tc in parallel_calls],
                return_exceptions=True,
            )

            # Process results
            for tool_call, tool_result in zip(parallel_calls, parallel_results):
                if isinstance(tool_result, Exception):
                    tool_result = ToolResult.create_error(
                        tool_call_id=tool_call.id,
                        tool_name=tool_call.name,
                        error=str(tool_result),
                    )
                tool_results[tool_call.id] = tool_result

                # Result callback
                if self.on_tool_result:
                    result = self.on_tool_result(tool_result)
                    if hasattr(result, "__await__"):
                        await result

        # Execute sequential tools one at a time
        for tool_call in sequential_calls:
            state.tool_calls_count += 1

            # Callback (only for non-streaming)
            if not self.config.stream and self.on_tool_call:
                result = self.on_tool_call(tool_call)
                if hasattr(result, "__await__"):
                    await result

            # Execute
            tool_result = await self.tool_executor(tool_call)
            tool_results[tool_call.id] = tool_result

            # Callback
            if self.on_tool_result:
                result = self.on_tool_result(tool_result)
                if hasattr(result, "__await__"):
                    await result

        # Add all results to messages (in original order)
        for tool_call in response.tool_calls:
            tool_result = tool_results[tool_call.id]
            state.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result.to_content(),
            })

        return None  # Continue loop

    async def _step_non_streaming(self, state: ReActState) -> ChatResponse:
        """Execute non-streaming LLM call."""
        return await self.llm.chat_completion(
            messages=state.messages,
            model=self.config.model,
            tools=self.tools_schema if self.tools_schema else None,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=False,
        )

    async def _step_streaming(self, state: ReActState) -> ChatResponse:
        """Execute streaming LLM call."""
        stream = await self.llm.chat_completion(
            messages=state.messages,
            model=self.config.model,
            tools=self.tools_schema if self.tools_schema else None,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )

        # Process stream with handler
        handler = StreamingHandler(
            on_content=self.on_content_delta,
            on_tool_call=self.on_tool_call,
        )
        return await handler.process(stream)

    def _get_last_content(self, state: ReActState) -> str | None:
        """Get the last assistant content from state."""
        if state.last_response and state.last_response.content:
            return state.last_response.content

        # Look through messages
        for msg in reversed(state.messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg["content"]

        return None
