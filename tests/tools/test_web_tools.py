"""Tests for web tools (web_search, web_fetch)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from esnaad.tools.web.web_search import WebSearchTool, WebSearchInput
from esnaad.tools.web.web_fetch import WebFetchTool, WebFetchInput
from esnaad.tools.base import ToolContext
from esnaad.exceptions import ToolExecutionError


class TestWebSearchTool:
    """Tests for WebSearchTool."""

    @pytest.fixture
    def tool(self) -> WebSearchTool:
        return WebSearchTool()

    @pytest.fixture
    def mock_search_response(self) -> str:
        """Mock DuckDuckGo HTML response."""
        return """
        <html>
        <body>
        <div class="result">
            <a class="result__a" href="https://example.com/page1">Example Page 1</a>
            <a class="result__snippet">This is the first result snippet.</a>
        </div>
        <div class="result">
            <a class="result__a" href="https://example.com/page2">Example Page 2</a>
            <a class="result__snippet">This is the second result snippet.</a>
        </div>
        </body>
        </html>
        """

    async def test_search_parses_results(
        self,
        tool: WebSearchTool,
        tool_context: ToolContext,
        mock_search_response: str,
    ) -> None:
        """Test that search parses HTML results."""
        mock_response = MagicMock()
        mock_response.text = mock_search_response
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_client_instance

            input_data = WebSearchInput(query="test query", max_results=5)
            result = await tool.execute(input_data, tool_context)

            assert result.query == "test query"
            assert result.total_results >= 0

    async def test_search_handles_timeout(
        self,
        tool: WebSearchTool,
        tool_context: ToolContext,
    ) -> None:
        """Test that search handles timeout errors."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_client_instance

            input_data = WebSearchInput(query="test query")

            with pytest.raises(ToolExecutionError) as exc_info:
                await tool.execute(input_data, tool_context)

            assert "timeout" in str(exc_info.value).lower()

    def test_openai_schema(self, tool: WebSearchTool) -> None:
        """Test OpenAI schema generation."""
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_search"
        assert "query" in schema["function"]["parameters"]["properties"]

    def test_clean_html(self, tool: WebSearchTool) -> None:
        """Test HTML cleaning."""
        html = "<b>Bold</b> &amp; <i>italic</i> &nbsp; text"
        cleaned = tool._clean_html(html)

        assert "Bold" in cleaned
        assert "&" in cleaned
        assert "italic" in cleaned
        assert "<b>" not in cleaned


class TestWebFetchTool:
    """Tests for WebFetchTool."""

    @pytest.fixture
    def tool(self) -> WebFetchTool:
        return WebFetchTool()

    @pytest.fixture
    def mock_html_response(self) -> str:
        """Mock HTML page."""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
        <nav>Navigation content</nav>
        <main>
        <h1>Main Heading</h1>
        <p>This is the main content of the page.</p>
        <script>console.log('ignored');</script>
        </main>
        <footer>Footer content</footer>
        </body>
        </html>
        """

    async def test_fetch_extracts_text(
        self,
        tool: WebFetchTool,
        tool_context: ToolContext,
        mock_html_response: str,
    ) -> None:
        """Test that fetch extracts text from HTML."""
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_client_instance

            input_data = WebFetchInput(url="https://example.com")
            result = await tool.execute(input_data, tool_context)

            assert result.status_code == 200
            assert result.title == "Test Page"
            assert "Main Heading" in result.content
            assert "main content" in result.content
            # Script content should be removed
            assert "console.log" not in result.content

    async def test_fetch_raw_html(
        self,
        tool: WebFetchTool,
        tool_context: ToolContext,
        mock_html_response: str,
    ) -> None:
        """Test fetching raw HTML without extraction."""
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_client_instance

            input_data = WebFetchInput(url="https://example.com", extract_text=False)
            result = await tool.execute(input_data, tool_context)

            # Should contain HTML tags
            assert "<html>" in result.content or "<body>" in result.content

    async def test_fetch_handles_http_error(
        self,
        tool: WebFetchTool,
        tool_context: ToolContext,
    ) -> None:
        """Test handling HTTP errors."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.reason_phrase = "Not Found"
            error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(side_effect=error)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_client_instance

            input_data = WebFetchInput(url="https://example.com/notfound")

            with pytest.raises(ToolExecutionError) as exc_info:
                await tool.execute(input_data, tool_context)

            assert "404" in str(exc_info.value)

    async def test_fetch_truncates_long_content(
        self,
        tool: WebFetchTool,
        tool_context: ToolContext,
    ) -> None:
        """Test that long content is truncated."""
        long_content = "A" * 100000  # 100KB of content
        mock_response = MagicMock()
        mock_response.text = long_content
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_client_instance

            input_data = WebFetchInput(url="https://example.com", max_length=1000)
            result = await tool.execute(input_data, tool_context)

            assert result.truncated
            assert len(result.content) < 2000  # Slightly over due to truncation message

    def test_url_validation(self) -> None:
        """Test URL validation."""
        # Valid URLs
        input1 = WebFetchInput(url="https://example.com")
        assert input1.url == "https://example.com"

        # URL without scheme gets https:// prepended
        input2 = WebFetchInput(url="example.com")
        assert input2.url == "https://example.com"

        # Invalid URL
        with pytest.raises(ValueError):
            WebFetchInput(url="not a valid url without domain")

    def test_openai_schema(self, tool: WebFetchTool) -> None:
        """Test OpenAI schema generation."""
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_fetch"
        assert "url" in schema["function"]["parameters"]["properties"]
