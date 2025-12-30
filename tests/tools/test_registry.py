"""Tests for tool registry."""

import pytest

from esnaad.tools.registry import ToolRegistry, register_tool, get_all_tools
from esnaad.tools.base import BaseTool, ToolContext
from pydantic import BaseModel, Field


class DummyInput(BaseModel):
    """Dummy input for test tool."""
    value: str = Field(description="Test value")


class DummyOutput(BaseModel):
    """Dummy output for test tool."""
    result: str


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        ToolRegistry.clear()

    def teardown_method(self) -> None:
        """Reinitialize registry after tests."""
        ToolRegistry.clear()

    def test_register_tool(self) -> None:
        """Test registering a tool."""
        @register_tool
        class TestTool(BaseTool[DummyInput, DummyOutput]):
            name = "test_tool"
            description = "A test tool"

            @property
            def input_schema(self):
                return DummyInput

            async def execute(self, input_data, context):
                return DummyOutput(result=input_data.value)

        tool = ToolRegistry.get("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"

    def test_get_nonexistent_tool(self) -> None:
        """Test getting a nonexistent tool."""
        tool = ToolRegistry.get("nonexistent")
        assert tool is None

    def test_get_or_raise(self) -> None:
        """Test get_or_raise with nonexistent tool."""
        from esnaad.exceptions import ToolNotFoundError

        with pytest.raises(ToolNotFoundError):
            ToolRegistry.get_or_raise("nonexistent")

    def test_get_all_tools(self) -> None:
        """Test getting all tools."""
        @register_tool
        class Tool1(BaseTool[DummyInput, DummyOutput]):
            name = "tool1"
            description = "Tool 1"

            @property
            def input_schema(self):
                return DummyInput

            async def execute(self, input_data, context):
                return DummyOutput(result="1")

        @register_tool
        class Tool2(BaseTool[DummyInput, DummyOutput]):
            name = "tool2"
            description = "Tool 2"

            @property
            def input_schema(self):
                return DummyInput

            async def execute(self, input_data, context):
                return DummyOutput(result="2")

        tools = ToolRegistry.get_all()
        assert len(tools) == 2
        names = [t.name for t in tools]
        assert "tool1" in names
        assert "tool2" in names

    def test_get_openai_schemas(self) -> None:
        """Test getting OpenAI schemas."""
        @register_tool
        class SchemaTool(BaseTool[DummyInput, DummyOutput]):
            name = "schema_tool"
            description = "A tool for testing schemas"

            @property
            def input_schema(self):
                return DummyInput

            async def execute(self, input_data, context):
                return DummyOutput(result=input_data.value)

        schemas = ToolRegistry.get_openai_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "schema_tool"

    def test_unregister_tool(self) -> None:
        """Test unregistering a tool."""
        @register_tool
        class TempTool(BaseTool[DummyInput, DummyOutput]):
            name = "temp_tool"
            description = "Temporary tool"

            @property
            def input_schema(self):
                return DummyInput

            async def execute(self, input_data, context):
                return DummyOutput(result="temp")

        assert ToolRegistry.get("temp_tool") is not None

        result = ToolRegistry.unregister("temp_tool")
        assert result is True
        assert ToolRegistry.get("temp_tool") is None

    def test_get_parallel_safe(self) -> None:
        """Test getting parallel-safe tools."""
        @register_tool
        class SafeTool(BaseTool[DummyInput, DummyOutput]):
            name = "safe_tool"
            description = "Parallel safe"
            parallel_safe = True

            @property
            def input_schema(self):
                return DummyInput

            async def execute(self, input_data, context):
                return DummyOutput(result="safe")

        @register_tool
        class UnsafeTool(BaseTool[DummyInput, DummyOutput]):
            name = "unsafe_tool"
            description = "Not parallel safe"
            parallel_safe = False

            @property
            def input_schema(self):
                return DummyInput

            async def execute(self, input_data, context):
                return DummyOutput(result="unsafe")

        safe_tools = ToolRegistry.get_parallel_safe()
        assert len(safe_tools) == 1
        assert safe_tools[0].name == "safe_tool"

    def test_initialize(self) -> None:
        """Test registry initialization."""
        ToolRegistry.initialize()
        assert ToolRegistry.is_initialized()

        # Should have the built-in tools registered
        tools = ToolRegistry.get_all()
        assert len(tools) > 0

        # Should include read_file
        assert ToolRegistry.get("read_file") is not None
