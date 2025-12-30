"""Sub-agent implementation for parallel task execution."""

import time
import uuid
from dataclasses import dataclass
from typing import Any

import structlog

from esnaad.llm.client import LLMClient
from esnaad.llm.messages import get_subagent_prompt
from esnaad.models.tool_call import ToolCall, ToolResult
from esnaad.models.subtask import Subtask, SubtaskResult, SubtaskStatus
from esnaad.core.react_loop import ReActLoop, ReActConfig
from esnaad.state.manager import StateManager
from esnaad.tools.base import ToolContext
from esnaad.tools.registry import ToolRegistry
from esnaad.config.settings import Settings

logger = structlog.get_logger(__name__)


@dataclass
class SubAgentConfig:
    """Configuration for sub-agents."""

    max_iterations: int = 20
    timeout_seconds: int = 120
    max_retries: int = 2
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096


class SubAgent:
    """
    Sub-agent for executing isolated subtasks.

    Sub-agents:
    - Are stateless (all context passed in)
    - Have scoped tool access
    - Return structured results
    - Have independent iteration limits
    """

    def __init__(
        self,
        agent_id: str,
        llm_client: LLMClient,
        allowed_tools: list[str],
        state_manager: StateManager,
        settings: Settings,
        config: SubAgentConfig | None = None,
        rules: str | None = None,
    ) -> None:
        """
        Initialize a sub-agent.

        Args:
            agent_id: Unique identifier for this sub-agent
            llm_client: LLM client for completions
            allowed_tools: List of tool names this agent can use
            state_manager: Shared state manager
            settings: Application settings
            config: Sub-agent configuration
            rules: Project rules inherited from orchestrator
        """
        self.agent_id = agent_id
        self.llm = llm_client
        self.allowed_tools = allowed_tools
        self.state = state_manager
        self.settings = settings
        self.rules = rules
        self.config = config or SubAgentConfig(
            max_iterations=settings.subagent.max_iterations,
            timeout_seconds=settings.subagent.timeout_seconds,
            max_retries=settings.subagent.max_retries,
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
        )

        logger.debug(
            "SubAgent created",
            agent_id=agent_id,
            tools=allowed_tools,
        )

    async def execute(self, subtask: Subtask) -> SubtaskResult:
        """
        Execute a subtask.

        Args:
            subtask: Subtask to execute

        Returns:
            Subtask result
        """
        start_time = time.time()

        logger.info(
            "SubAgent executing subtask",
            agent_id=self.agent_id,
            subtask_id=subtask.id,
            description=subtask.description,
        )

        # Build system prompt
        system_prompt = get_subagent_prompt(
            task_description=subtask.description,
            tools=subtask.tools,
            project_rules=self.rules,
        )

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": subtask.prompt},
        ]

        # Get tool schemas for allowed tools
        tools_schema = ToolRegistry.get_openai_schemas(subtask.tools)

        # Create ReAct loop
        react_config = ReActConfig(
            max_iterations=self.config.max_iterations,
            timeout_seconds=self.config.timeout_seconds,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        loop = ReActLoop(
            llm_client=self.llm,
            config=react_config,
            tool_executor=self._execute_tool,
            tools_schema=tools_schema,
        )

        # Run the loop
        result = await loop.run(messages)

        execution_time = time.time() - start_time

        # Convert to SubtaskResult
        if result.is_success:
            return SubtaskResult.complete(
                id=subtask.id,
                result=result.content or "",
                iterations=result.iterations,
                execution_time=execution_time,
            )
        elif result.status.value == "timeout":
            return SubtaskResult.timeout(
                id=subtask.id,
                timeout=self.config.timeout_seconds,
                partial_output=result.content,
                iterations=result.iterations,
            )
        elif result.status.value == "max_iterations":
            return SubtaskResult.incomplete(
                id=subtask.id,
                partial_output=result.content or result.error or "Max iterations reached",
                iterations=result.iterations,
                execution_time=execution_time,
            )
        else:
            return SubtaskResult.failed(
                id=subtask.id,
                error=result.error or "Unknown error",
                partial_output=result.content,
                iterations=result.iterations,
                execution_time=execution_time,
            )

    async def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call within the sub-agent's scope."""
        start_time = time.time()

        # Check if tool is allowed
        if tool_call.name not in self.allowed_tools:
            return ToolResult.error(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                error=f"Tool '{tool_call.name}' not allowed for this sub-agent",
            )

        # Get the tool
        tool = ToolRegistry.get(tool_call.name)
        if tool is None:
            return ToolResult.error(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                error=f"Unknown tool: {tool_call.name}",
            )

        # Create context
        context = ToolContext(
            working_directory=self.settings.working_directory,
            settings=self.settings,
            agent_id=self.agent_id,
            state_manager=self.state,
            is_subagent=True,
        )

        # Execute
        try:
            if tool.requires_lock:
                file_path = tool_call.arguments.get("file_path")
                if file_path:
                    async with self.state.acquire_file_lock(file_path, "write"):
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

            if hasattr(output, "model_dump"):
                output_value = output.model_dump()
            else:
                output_value = output

            return ToolResult.success(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                output=output_value,
                execution_time=time.time() - start_time,
            )

        except Exception as e:
            return ToolResult.error(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                error=str(e),
                execution_time=time.time() - start_time,
            )
