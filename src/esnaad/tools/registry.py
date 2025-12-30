"""Tool registry for managing available tools."""

from typing import Any, Callable, TypeVar

import structlog

from esnaad.tools.base import BaseTool

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseTool)


class ToolRegistry:
    """
    Registry for all available tools.

    Provides methods to register, retrieve, and manage tools.
    """

    _tools: dict[str, BaseTool] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """
        Register a tool instance.

        Args:
            tool: Tool instance to register
        """
        if tool.name in cls._tools:
            logger.warning(
                "Overwriting existing tool",
                tool_name=tool.name,
            )
        cls._tools[tool.name] = tool
        logger.debug("Registered tool", tool_name=tool.name)

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a tool by name.

        Args:
            name: Tool name

        Returns:
            True if tool was removed, False if not found
        """
        if name in cls._tools:
            del cls._tools[name]
            return True
        return False

    @classmethod
    def get(cls, name: str) -> BaseTool | None:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return cls._tools.get(name)

    @classmethod
    def get_or_raise(cls, name: str) -> BaseTool:
        """
        Get a tool by name, raising if not found.

        Args:
            name: Tool name

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool not found
        """
        from esnaad.exceptions import ToolNotFoundError

        tool = cls.get(name)
        if tool is None:
            raise ToolNotFoundError(name)
        return tool

    @classmethod
    def get_all(cls) -> list[BaseTool]:
        """Get all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def get_names(cls) -> list[str]:
        """Get all registered tool names."""
        return list(cls._tools.keys())

    @classmethod
    def get_scoped(cls, names: list[str]) -> list[BaseTool]:
        """
        Get a subset of tools by name.

        Args:
            names: List of tool names to include

        Returns:
            List of matching tools
        """
        return [
            cls._tools[name]
            for name in names
            if name in cls._tools
        ]

    @classmethod
    def get_openai_schemas(
        cls,
        names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get OpenAI function schemas for tools.

        Args:
            names: Optional list of tool names (all if None)

        Returns:
            List of OpenAI function schemas
        """
        if names:
            tools = cls.get_scoped(names)
        else:
            tools = cls.get_all()

        return [tool.to_openai_schema() for tool in tools]

    @classmethod
    def get_parallel_safe(cls) -> list[BaseTool]:
        """Get all parallel-safe tools."""
        return [t for t in cls._tools.values() if t.parallel_safe]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools."""
        cls._tools.clear()
        cls._initialized = False

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the registry with default tools.

        This imports all tool modules to trigger registration.
        """
        if cls._initialized:
            return

        # Import tool modules to trigger @register_tool decorators
        from esnaad.tools import file  # noqa: F401
        from esnaad.tools import filesystem  # noqa: F401
        from esnaad.tools import shell  # noqa: F401
        from esnaad.tools import orchestration  # noqa: F401
        from esnaad.tools import web  # noqa: F401

        cls._initialized = True
        logger.info(
            "Tool registry initialized",
            tool_count=len(cls._tools),
        )

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if registry has been initialized."""
        return cls._initialized


def register_tool(cls: type[T]) -> type[T]:
    """
    Decorator to auto-register a tool class.

    Usage:
        @register_tool
        class MyTool(BaseTool[MyInput, MyOutput]):
            name = "my_tool"
            ...
    """
    # Create instance and register
    tool = cls()
    ToolRegistry.register(tool)
    return cls


def get_all_tools() -> list[BaseTool]:
    """
    Get all registered tools, initializing if needed.

    Returns:
        List of all tools
    """
    if not ToolRegistry.is_initialized():
        ToolRegistry.initialize()
    return ToolRegistry.get_all()
