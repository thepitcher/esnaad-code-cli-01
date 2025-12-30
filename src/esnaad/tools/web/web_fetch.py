"""Web fetch tool for retrieving URL content."""

import re
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, field_validator

from esnaad.tools.base import BaseTool, ToolContext
from esnaad.tools.registry import register_tool


class WebFetchInput(BaseModel):
    """Input schema for web_fetch tool."""

    url: str = Field(
        description="The URL to fetch",
    )
    extract_text: bool = Field(
        default=True,
        description="Whether to extract text from HTML (removes tags)",
    )
    max_length: int = Field(
        default=50000,
        ge=100,
        le=200000,
        description="Maximum content length to return",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            v = "https://" + v

        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("Invalid URL: missing domain")

        return v


class WebFetchOutput(BaseModel):
    """Output schema for web_fetch tool."""

    url: str = Field(description="Fetched URL")
    status_code: int = Field(description="HTTP status code")
    content_type: str = Field(description="Response content type")
    content: str = Field(description="Page content (text or HTML)")
    title: str | None = Field(default=None, description="Page title if HTML")
    truncated: bool = Field(description="Whether content was truncated")
    content_length: int = Field(description="Original content length")


@register_tool
class WebFetchTool(BaseTool[WebFetchInput, WebFetchOutput]):
    """
    Fetch content from a URL.

    Can extract text from HTML pages or return raw content.
    Useful for reading documentation, articles, or API responses.
    """

    name = "web_fetch"
    description = (
        "Fetch content from a URL. Extracts readable text from HTML by default. "
        "Use this to read web pages, documentation, or download content. "
        "Returns the page content, title, and metadata."
    )
    parallel_safe = True
    requires_lock = False

    @property
    def input_schema(self) -> type[WebFetchInput]:
        return WebFetchInput

    @property
    def output_schema(self) -> type[WebFetchOutput]:
        return WebFetchOutput

    async def execute(
        self,
        input_data: WebFetchInput,
        context: ToolContext,
    ) -> WebFetchOutput:
        """Fetch URL content."""
        from esnaad.exceptions import ToolExecutionError

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                response = await client.get(
                    input_data.url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                    },
                )
                response.raise_for_status()

        except httpx.TimeoutException:
            raise ToolExecutionError(
                tool_name=self.name,
                message="Request timed out",
            )
        except httpx.HTTPStatusError as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
            )
        except httpx.HTTPError as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Request failed: {e}",
            )

        # Get content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()

        # Get raw content
        try:
            raw_content = response.text
        except UnicodeDecodeError:
            raw_content = response.content.decode("latin-1")

        original_length = len(raw_content)

        # Extract title if HTML
        title = None
        if "html" in content_type.lower():
            title = self._extract_title(raw_content)

        # Process content
        if input_data.extract_text and "html" in content_type.lower():
            content = self._extract_text(raw_content)
        else:
            content = raw_content

        # Truncate if needed
        truncated = len(content) > input_data.max_length
        if truncated:
            content = content[: input_data.max_length] + "\n\n[Content truncated...]"

        return WebFetchOutput(
            url=str(response.url),
            status_code=response.status_code,
            content_type=content_type,
            content=content,
            title=title,
            truncated=truncated,
            content_length=original_length,
        )

    def _extract_title(self, html: str) -> str | None:
        """Extract title from HTML."""
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))
        return None

    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML."""
        # Remove script and style elements
        html = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        html = re.sub(
            r"<style[^>]*>.*?</style>",
            "",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # Remove navigation, header, footer if marked
        for tag in ["nav", "header", "footer", "aside"]:
            html = re.sub(
                rf"<{tag}[^>]*>.*?</{tag}>",
                "",
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )

        # Convert block elements to newlines
        for tag in ["p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"]:
            html = re.sub(rf"<{tag}[^>]*>", "\n", html, flags=re.IGNORECASE)
            html = re.sub(rf"</{tag}>", "\n", html, flags=re.IGNORECASE)

        # Remove remaining HTML tags
        html = re.sub(r"<[^>]+>", "", html)

        # Clean up text
        text = self._clean_text(html)

        # Remove excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _clean_text(self, text: str) -> str:
        """Clean up text content."""
        # Decode HTML entities
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")
        text = text.replace("&mdash;", "-")
        text = text.replace("&ndash;", "-")
        text = text.replace("&copy;", "(c)")
        text = text.replace("&reg;", "(R)")
        text = text.replace("&trade;", "(TM)")

        # Decode numeric entities
        text = re.sub(
            r"&#(\d+);",
            lambda m: chr(int(m.group(1))) if int(m.group(1)) < 65536 else "",
            text,
        )
        text = re.sub(
            r"&#x([0-9a-fA-F]+);",
            lambda m: chr(int(m.group(1), 16)) if int(m.group(1), 16) < 65536 else "",
            text,
        )

        # Normalize whitespace (but preserve newlines)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)

        return text.strip()
