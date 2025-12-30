"""Web search tool implementation using DuckDuckGo."""

import re
from typing import Any
from urllib.parse import quote_plus

import httpx
from pydantic import BaseModel, Field

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class WebSearchInput(BaseModel):
    """Input schema for web_search tool."""

    query: str = Field(
        description="The search query",
        min_length=1,
        max_length=500,
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return (1-20)",
    )


class SearchResult(BaseModel):
    """A single search result."""

    title: str = Field(description="Result title")
    url: str = Field(description="Result URL")
    snippet: str = Field(description="Result snippet/description")


class WebSearchOutput(BaseModel):
    """Output schema for web_search tool."""

    query: str = Field(description="Original search query")
    results: list[SearchResult] = Field(description="Search results")
    total_results: int = Field(description="Number of results returned")


@register_tool
class WebSearchTool(BaseTool[WebSearchInput, WebSearchOutput]):
    """
    Search the web using DuckDuckGo.

    Returns a list of search results with titles, URLs, and snippets.
    Use this when you need current information from the internet.
    """

    name = "web_search"
    description = (
        "Search the web for information. Returns titles, URLs, and snippets. "
        "Use this when you need current/up-to-date information, "
        "documentation, or resources that may not be in your knowledge base."
    )
    parallel_safe = True
    requires_lock = False

    @property
    def input_schema(self) -> type[WebSearchInput]:
        return WebSearchInput

    @property
    def output_schema(self) -> type[WebSearchOutput]:
        return WebSearchOutput

    async def execute(
        self,
        input_data: WebSearchInput,
        context: ToolContext,
    ) -> WebSearchOutput:
        """Execute web search using DuckDuckGo HTML."""
        from esnaad.exceptions import ToolExecutionError

        # Build search URL
        query_encoded = quote_plus(input_data.query)
        url = f"https://html.duckduckgo.com/html/?q={query_encoded}"

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                )
                response.raise_for_status()

        except httpx.TimeoutException:
            raise ToolExecutionError(
                tool_name=self.name,
                message="Search request timed out",
            )
        except httpx.HTTPError as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Search request failed: {e}",
            )

        # Parse results from HTML
        html = response.text
        results = self._parse_duckduckgo_html(html, input_data.max_results)

        return WebSearchOutput(
            query=input_data.query,
            results=results,
            total_results=len(results),
        )

    def _parse_duckduckgo_html(
        self,
        html: str,
        max_results: int,
    ) -> list[SearchResult]:
        """Parse search results from DuckDuckGo HTML response."""
        results = []

        # Pattern to match result divs
        # DuckDuckGo HTML uses class="result" for each result
        result_pattern = re.compile(
            r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?'
            r'<a class="result__snippet"[^>]*>([^<]*(?:<[^>]+>[^<]*)*)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        # Alternative pattern for different HTML structure
        alt_pattern = re.compile(
            r'class="result__url"[^>]*href="([^"]+)"[^>]*>.*?'
            r'class="result__title"[^>]*>([^<]+)</.*?'
            r'class="result__snippet"[^>]*>([^<]*(?:<[^>]+>[^<]*)*)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        # Try to find result blocks
        for match in result_pattern.finditer(html):
            if len(results) >= max_results:
                break

            url = match.group(1)
            title = self._clean_html(match.group(2))
            snippet = self._clean_html(match.group(3))

            # Skip ad results
            if "duckduckgo.com/y.js" in url:
                continue

            if title and url:
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                ))

        # If primary pattern didn't find results, try alternative
        if not results:
            for match in alt_pattern.finditer(html):
                if len(results) >= max_results:
                    break

                url = match.group(1)
                title = self._clean_html(match.group(2))
                snippet = self._clean_html(match.group(3))

                if "duckduckgo.com/y.js" in url:
                    continue

                if title and url:
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                    ))

        # Fallback: simple link extraction
        if not results:
            link_pattern = re.compile(
                r'<a[^>]+class="[^"]*result[^"]*"[^>]+href="(https?://[^"]+)"[^>]*>([^<]+)</a>',
                re.IGNORECASE,
            )
            for match in link_pattern.finditer(html):
                if len(results) >= max_results:
                    break

                url = match.group(1)
                title = self._clean_html(match.group(2))

                if "duckduckgo.com" not in url:
                    results.append(SearchResult(
                        title=title or url,
                        url=url,
                        snippet="",
                    ))

        return results

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Decode common HTML entities
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")
        # Clean whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
