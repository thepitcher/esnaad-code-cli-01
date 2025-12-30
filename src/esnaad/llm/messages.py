"""Message formatting utilities for LLM conversations."""

from typing import Any

from esnaad.models.messages import Message


def format_messages(messages: list[Message]) -> list[dict[str, Any]]:
    """
    Convert a list of Message objects to API format.

    Args:
        messages: List of Message objects

    Returns:
        List of dicts suitable for API calls
    """
    return [msg.to_dict() for msg in messages]


def build_system_prompt(
    base_prompt: str,
    working_directory: str | None = None,
    tools_available: list[str] | None = None,
    additional_context: str | None = None,
    project_rules: str | None = None,
) -> str:
    """
    Build a comprehensive system prompt for the agent.

    Args:
        base_prompt: Base system prompt
        working_directory: Current working directory
        tools_available: List of available tool names
        additional_context: Any additional context to include
        project_rules: Project-specific rules from ESNAAD.md

    Returns:
        Complete system prompt
    """
    parts = [base_prompt]

    if working_directory:
        parts.append(f"\n## Working Directory\n{working_directory}")

    if tools_available:
        tools_str = ", ".join(tools_available)
        parts.append(f"\n## Available Tools\n{tools_str}")

    # Insert project rules before additional context
    if project_rules:
        parts.append(
            f"\n## Project Rules\n\n"
            f"The following rules from ESNAAD.md MUST be followed:\n\n"
            f"{project_rules}"
        )

    if additional_context:
        parts.append(f"\n## Additional Context\n{additional_context}")

    return "\n".join(parts)


# Default system prompts
ORCHESTRATOR_SYSTEM_PROMPT = """You are Esnaad Code, an AI-powered coding assistant.

You help users with software engineering tasks by using available tools to read, write, and modify files, search code, run commands, and more.

## Guidelines

1. **Think step by step** - Break down complex tasks into smaller steps
2. **Use tools appropriately** - Choose the right tool for each task
3. **Be precise** - When editing files, make surgical changes
4. **Handle errors gracefully** - If a tool fails, try alternative approaches
5. **Keep the user informed** - Explain what you're doing and why

## Tool Usage

- Use `read_file` to examine file contents before making changes
- Use `search_files` and `search_content` to find relevant code
- Use `edit_file` for precise modifications (preferred over `write_file` for existing files)
- Use `run_command` for shell operations
- Use `spawn_subtasks` to parallelize independent work

## Important

- Always read a file before attempting to edit it
- Don't make changes you weren't asked to make
- Ask for clarification if the task is ambiguous
- Report any errors or issues clearly"""


SUBAGENT_SYSTEM_PROMPT = """You are a sub-agent of Esnaad Code, handling a specific subtask.

Focus on completing your assigned task efficiently using the available tools.

## Guidelines

1. Stay focused on your specific task
2. Use only the tools provided to you
3. Return a clear, structured result
4. Report any errors or blockers

Your output will be aggregated with other subtasks by the main agent."""


def get_orchestrator_prompt(
    working_directory: str | None = None,
    tools: list[str] | None = None,
    project_rules: str | None = None,
) -> str:
    """Get the complete orchestrator system prompt."""
    return build_system_prompt(
        ORCHESTRATOR_SYSTEM_PROMPT,
        working_directory=working_directory,
        tools_available=tools,
        project_rules=project_rules,
    )


def get_subagent_prompt(
    task_description: str,
    tools: list[str] | None = None,
    project_rules: str | None = None,
) -> str:
    """Get the complete sub-agent system prompt."""
    return build_system_prompt(
        SUBAGENT_SYSTEM_PROMPT,
        tools_available=tools,
        additional_context=f"## Your Task\n{task_description}",
        project_rules=project_rules,
    )
