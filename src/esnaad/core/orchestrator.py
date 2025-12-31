"""Main orchestrator agent implementation."""

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Awaitable

import structlog

from esnaad.config.settings import Settings
from esnaad.config.rules import RulesLoader
from esnaad.llm.client import LLMClient
from esnaad.llm.messages import get_orchestrator_prompt
from esnaad.models.tool_call import ToolCall, ToolResult
from esnaad.models.result import AgentResult
from esnaad.core.react_loop import ReActLoop, ReActConfig
from esnaad.state.manager import StateManager
from esnaad.tools.base import ToolContext
from esnaad.tools.registry import ToolRegistry

logger = structlog.get_logger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""

    max_iterations: int = 50
    timeout_seconds: int = 300
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    enable_clarifications: bool = True
    stream: bool = False  # Enable streaming responses


class Orchestrator:
    """
    Main orchestrator agent.

    Manages the conversation, executes tools, and can spawn sub-agents
    for parallel execution of independent subtasks.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        settings: Settings,
        config: OrchestratorConfig | None = None,
        on_content: Callable[[str], Awaitable[None] | None] | None = None,
        on_tool_call: Callable[[ToolCall], Awaitable[None] | None] | None = None,
        on_tool_result: Callable[[ToolResult], Awaitable[None] | None] | None = None,
        clarification_handler: Callable[[Any], Awaitable[Any]] | None = None,
        on_content_delta: Callable[[str], Awaitable[None] | None] | None = None,
        on_thinking_start: Callable[[], Awaitable[None] | None] | None = None,
        on_thinking_end: Callable[[], Awaitable[None] | None] | None = None,
        preset_rules: str | None = None,
        skip_working_dir_rules: bool = False,
    ) -> None:
        """
        Initialize the orchestrator.

        Args:
            llm_client: LLM client for completions
            settings: Application settings
            config: Orchestrator configuration
            on_content: Callback for complete content output
            on_tool_call: Callback when a tool is called
            on_tool_result: Callback when a tool returns
            clarification_handler: Callback for user clarifications
            on_content_delta: Callback for streaming content deltas
            on_thinking_start: Callback when LLM request starts
            on_thinking_end: Callback when LLM request ends
            preset_rules: Pre-loaded rules content (skips loading from working dir)
            skip_working_dir_rules: If True, don't load ESNAAD.md from working dir
        """
        self.llm = llm_client
        self.settings = settings
        self.config = config or OrchestratorConfig(
            max_iterations=settings.orchestrator.max_iterations,
            timeout_seconds=settings.orchestrator.timeout_seconds,
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            enable_clarifications=settings.orchestrator.enable_clarifications,
        )

        self.on_content = on_content
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self._clarification_handler = clarification_handler
        self.on_content_delta = on_content_delta
        self.on_thinking_start = on_thinking_start
        self.on_thinking_end = on_thinking_end

        # Initialize state manager
        self.state_manager = StateManager(settings.working_directory)

        # Initialize tool registry
        if not ToolRegistry.is_initialized():
            ToolRegistry.initialize()

        # Agent ID for this session
        self.agent_id = f"orchestrator-{uuid.uuid4().hex[:8]}"

        # Conversation history
        self.messages: list[dict[str, Any]] = []

        # Rules (loaded lazily or from preset)
        self._rules: str | None = preset_rules
        self._rules_loaded: bool = preset_rules is not None
        self._skip_working_dir_rules: bool = skip_working_dir_rules or preset_rules is not None

        logger.info(
            "Orchestrator initialized",
            agent_id=self.agent_id,
            model=self.config.model,
        )

    async def _ensure_rules_loaded(self) -> None:
        """Ensure rules are loaded (lazy loading)."""
        if not self._rules_loaded:
            if self._skip_working_dir_rules:
                # Skip loading from working directory (preset rules already set or disabled)
                self._rules_loaded = True
            else:
                self._rules = await RulesLoader.load_rules(
                    self.settings.working_directory
                )
                self._rules_loaded = True

    async def run(self, user_message: str) -> AgentResult:
        """
        Process a user message and return the result.

        Args:
            user_message: User's input message

        Returns:
            Agent result with response
        """
        start_time = time.time()

        # Ensure rules are loaded
        await self._ensure_rules_loaded()

        # Build system prompt if needed
        if not self.messages:
            tools = ToolRegistry.get_names()
            system_prompt = get_orchestrator_prompt(
                working_directory=str(self.settings.working_directory),
                tools=tools,
                project_rules=self._rules,
            )
            self.messages.append({"role": "system", "content": system_prompt})

        # Add user message
        self.messages.append({"role": "user", "content": user_message})

        # Get tool schemas
        tools_schema = ToolRegistry.get_openai_schemas()

        # Create ReAct loop
        react_config = ReActConfig(
            max_iterations=self.config.max_iterations,
            timeout_seconds=self.config.timeout_seconds,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=self.config.stream,
        )

        loop = ReActLoop(
            llm_client=self.llm,
            config=react_config,
            tool_executor=self._execute_tool,
            tools_schema=tools_schema,
            on_thinking=self.on_content,
            on_tool_call=self.on_tool_call,
            on_tool_result=self.on_tool_result,
            on_content_delta=self.on_content_delta,
            on_thinking_start=self.on_thinking_start,
            on_thinking_end=self.on_thinking_end,
        )

        # Run the loop
        result = await loop.run(self.messages)

        # Update conversation history
        if result.content:
            self.messages.append({
                "role": "assistant",
                "content": result.content,
            })

        logger.info(
            "Orchestrator run complete",
            status=result.status,
            iterations=result.iterations,
            execution_time=time.time() - start_time,
        )

        return result

    async def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call."""
        start_time = time.time()

        logger.debug(
            "Executing tool",
            tool=tool_call.name,
            arguments=tool_call.arguments,
        )

        # Get the tool
        tool = ToolRegistry.get(tool_call.name)
        if tool is None:
            return ToolResult.create_error(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                error=f"Unknown tool: {tool_call.name}",
            )

        # Create context with metadata for orchestration tools
        context = ToolContext(
            working_directory=self.settings.working_directory,
            settings=self.settings,
            agent_id=self.agent_id,
            state_manager=self.state_manager,
            is_subagent=False,
            metadata={
                "llm_client": self.llm,
                "clarification_handler": self._clarification_handler,
                "rules": self._rules,
            },
        )

        # Check cache for read-only tools
        if tool.parallel_safe and not tool.requires_lock:
            hit, cached_value = await self.state_manager.get_cached(
                tool_call.name,
                tool_call.arguments,
            )
            if hit:
                logger.debug("Cache hit", tool=tool_call.name)
                return ToolResult.create_success(
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.name,
                    output=cached_value,
                    execution_time=time.time() - start_time,
                )

        # Execute with lock if needed
        try:
            if tool.requires_lock:
                # Get file path from arguments if available
                file_path = tool_call.arguments.get("file_path")
                if file_path:
                    async with self.state_manager.acquire_file_lock(
                        file_path,
                        "write",
                    ):
                        output = await tool.validate_and_execute(
                            tool_call.arguments,
                            context,
                        )
                else:
                    output = await tool.validate_and_execute(
                        tool_call.arguments,
                        context,
                    )
            else:
                output = await tool.validate_and_execute(
                    tool_call.arguments,
                    context,
                )

            execution_time = time.time() - start_time

            # Cache result for read-only tools
            if tool.parallel_safe and not tool.requires_lock:
                await self.state_manager.set_cached(
                    tool_call.name,
                    tool_call.arguments,
                    output,
                )

            # Convert output to string/dict
            if hasattr(output, "model_dump"):
                output_value = output.model_dump()
            else:
                output_value = output

            return ToolResult.create_success(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                output=output_value,
                execution_time=execution_time,
            )

        except Exception as e:
            logger.warning(
                "Tool execution failed",
                tool=tool_call.name,
                error=str(e),
            )
            return ToolResult.create_error(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
        logger.info("Conversation history cleared")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.state_manager.cleanup()
        await self.state_manager.clear_agent_memory(self.agent_id)
